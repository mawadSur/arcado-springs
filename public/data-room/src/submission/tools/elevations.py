#!/usr/bin/env python3
"""Exterior ELEVATION engine — The Cottages at Arcado Springs (R-1 → R-2 rezoning, Lilburn GA).

Answers City of Lilburn 2026 Application Instructions item (11), "Architectural Renderings and Elevations":
    "An architectural rendering or elevation of each side of the structure visible from the street shall be
     submitted. The drawings shall be to scale or in proper perspective and shall include the color and
     materials of all structures and roofing and location and size of wall signs."

ILLUSTRATIVE — NOT FOR CONSTRUCTION. DRAFT — to be superseded by sealed drawings (GA-registered architect).

    python3 tools/elevations.py              # both plans, all sheets
    python3 tools/elevations.py A            # one plan

===================================================================================================
WHERE THE GEOMETRY COMES FROM  (nothing is drawn by hand; an elevation cannot disagree with its plan)
===================================================================================================
tools/floorplans.py holds the authoritative plan specs and generates data/plans.json. This module
imports it and re-derives:
  * the massing rectangles below are the plan's own room groups (checked against the footprint polygon
    by check_massing(), which fails the build if they drift);
  * eave height  = plate + heel;
  * ridge height = eave + (span / 2) x pitch, recomputed per block;
  * every opening is placed from spec['exterior_openings'] — 'at' is the plan coordinate, so a window
    that moves on the floor plan moves on the elevation.

PROJECTION. Each view has a plan view-direction d (the way the viewer looks) and a paper-horizontal
axis r = (d_y, -d_x), the standard right-handed elevation convention:
    front  d = (0, +1)  ->  paper right = +x   (lane side; x increases to the right, as on the plan)
    rear   d = (0, -1)  ->  paper right = -x
    left   d = (+1, 0)  ->  paper right = -y   (the front of the house appears on the RIGHT)
    right  d = (-1, 0)  ->  paper right = +y   (the front of the house appears on the LEFT)
Depth along d orders the masses (smaller p.d is nearer the viewer), and blocks are painted far-to-near.

ROOFS. A block's ridge axis a is (1,0) for 'x' or (0,1) for 'y'.
    a.d == 0   the ridge crosses the view -> the eave face is toward us: the wall stops at the eave and
               the roof projects as a rectangle from the eave to the ridge, widened by the RAKE overhang.
    |a.d| == 1 the ridge points at the viewer -> the gable end is toward us: the wall carries a gable
               triangle to the ridge and the roof projects as a rake band widened by the EAVE overhang.

FRONT PORCH (design decision, 2026-09-03 Rev B). The front porch is roofed by carrying the front-wing
gable forward over it — an integral gable porch — instead of the separate 4:12 shed the 2026-08-28
program assumed. A full-width shed cannot be built against a gable-end wall: at 4:12 over a 6'-0" porch
its high side lands 2'-0" above the plate, which is above the 8:12 rake for the outer 3'-0" at each end
of the wing. Carrying the gable forward keeps the porch its full programmed width and area (Plan A
17'-0" x 6'-0" = 102 SF; Plan B 19'-0" x 6'-0" = 114 SF — unchanged), keeps a flat 9'-0" porch ceiling,
and adds no height. The gable end above the porch is carried on a header between the outer posts.

WIDTH CHECK (the binding dimension). A 50'-0" lot less two 5'-0" side yards leaves 40'-0" buildable
(Lilburn Zoning Ordinance 2023-603 Table 4.1). Overhangs are therefore held to 8 in on the two side
(lot-line) walls and 12 in front and rear, and check_width() fails the build if roof-to-roof width
exceeds 40'-0".

FLOOR HEIGHT. Finished floor is 8 in above finished grade at the front porch, not the 18 in a slab
house usually carries, so that the entry walk from the lane can rise to a flush landing at no more than
1:20 and stay a zero-step entry (voluntary accessibility condition) without becoming a ramp under
IRC 2024 (GA 2026) R311.8. At 8 in the porch is also below the 30-in threshold at which R312.1.1 would
require a guard. Grade falls away at the sides and rear; the elevations show level grade with a note.
===================================================================================================
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import floorplans as fp                                   # noqa: E402

ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data')
DRAW = os.path.join(ROOT, 'drawings')
os.makedirs(DRAW, exist_ok=True)

DATE = '2026-09-03'
REVISION = 'Rev B — 2026-09-03'
fti, esc = fp.fti, fp.esc
DISCLAIMER, MARKER = fp.DISCLAIMER, fp.MARKER

# ----------------------------------------------------------------------------- standards
FF = 0.667                  # ft, finished floor above finished grade at the front (8 in — see FLOOR HEIGHT)
WATER_TABLE = 2.5           # ft, masonry water table above FF (30 in; 04 20 00 / 04 40 00)
OH_SIDE = 0.667             # ft, 8-in overhang on the two side (lot-line) walls
OH_FR = 0.667               # ft, 8-in overhang front and rear (held out of the required yards)
FASCIA = 0.67               # ft, fascia + sub-fascia shown on the roof edge
BEAM = 0.83                 # ft, porch header depth (10 in shown)
COL = 0.667                 # ft, 8x8 nominal cedar post
PIER_W, PIER_H = 1.67, 2.0  # ft, 20-in square masonry pier, 2'-0" tall
VENT = (2.0, 1.33)          # ft, louvered gable vent, 24 x 16 in
CAP_RIDGE = 24.0            # ft, voluntary condition 4: maximum ridge above finished grade
DISTRICT_MAX = 40.0         # ft, Ord. 2023-603 Table 4.1 R-2 maximum height
LOT_BUILDABLE = 40.0        # ft, 50-ft lot less two 5-ft side yards

VIEWS = [
    ('front', (0, 1),  'FRONT ELEVATION — FACES THE PRIVATE LANE'),
    ('right', (-1, 0), 'RIGHT SIDE ELEVATION'),
    ('rear',  (0, -1), 'REAR ELEVATION'),
    ('left',  (1, 0),  'LEFT SIDE ELEVATION'),
]
VD = {k: d for k, d, _ in VIEWS}
VT = {k: t for k, _, t in VIEWS}

SCHEMES = {
    '1': {'name': 'SCHEME 1 — WARM WHITE',
          'siding_kind': 'batten', 'siding': '#F1EDE3', 'siding_line': '#D6CFBE',
          'base_kind': 'stone', 'base': '#ABA495', 'base_line': '#8A8378',
          'roof': '#4A4E52', 'roof_line': '#383C40', 'trim': '#FFFFFF', 'trim_line': '#CBC5B8',
          'door': '#2E4A38', 'garage': '#F4F1E9', 'post': '#A9catch', 'sash': '#FFFFFF'},
    '2': {'name': 'SCHEME 2 — SAGE',
          'siding_kind': 'lap', 'siding': '#98A189', 'siding_line': '#7A8370',
          'base_kind': 'brick', 'base': '#8C5A4A', 'base_line': '#6C4438',
          'roof': '#6B6255', 'roof_line': '#524B41', 'trim': '#F7F5EF', 'trim_line': '#D5D0C2',
          'door': '#6E2B2B', 'garage': '#98A189', 'post': '#A98C5F', 'sash': '#FFFFFF'},
    '3': {'name': 'SCHEME 3 — CLAY',
          'siding_kind': 'lap', 'siding': '#D7C8AD', 'siding_line': '#B9A98C',
          'base_kind': 'stone', 'base': '#C4B594', 'base_line': '#9F9169',
          'roof': '#7A6E60', 'roof_line': '#5E5449', 'trim': '#F5EEDC', 'trim_line': '#D7CDB4',
          'door': '#23364F', 'garage': '#F5EEDC', 'post': '#A98C5F', 'sash': '#FFFFFF'},
}
SCHEMES['1']['post'] = '#A98C5F'
LINEWORK = {'name': 'LINE DRAWING', 'siding_kind': 'lap', 'base_kind': 'stone',
            'siding': '#FFFFFF', 'siding_line': '#B4B4B4', 'base': '#FFFFFF', 'base_line': '#8C8C8C',
            'roof': '#F2F2F2', 'roof_line': '#8E8E8E', 'trim': '#FFFFFF', 'trim_line': '#9A9A9A',
            'door': '#FFFFFF', 'garage': '#FFFFFF', 'post': '#FFFFFF', 'sash': '#FFFFFF'}

MATERIAL_KEYS = [
    ('ROOF', '07 31 00', 'Architectural asphalt shingle, 30-year, over synthetic underlayment; ridge vent; '
     '5-in K-style aluminium gutters and downspouts (07 71 00). Colour by scheme.'),
    ('WALL', '07 46 46', 'Fiber-cement siding: 7-1/4-in lap at 6-in exposure (schemes 2 and 3) or vertical '
     'panel with 12-in battens (scheme 1); factory finish. 5/4 cellular-PVC or fiber-cement trim, corner '
     'boards and frieze (06 20 00).'),
    ('BASE', '04 20 00 / 04 40 00', 'Masonry water table 30 in above finished floor and porch piers: modular '
     'brick veneer (scheme 2) or adhered ledge stone (schemes 1 and 3), cast-stone cap sloped with drip.'),
    ('PORCH', '06 20 00', '8x8 nominal Western Red Cedar posts on 20-in square masonry piers with cast-stone '
     'caps; cedar brackets at the gable; beadboard porch ceiling; 9\'-0" flat porch ceiling.'),
    ('WINDOWS', '08 53 13', 'Vinyl (fiberglass alternate) single-hung and fixed units, white; 4-in flat casing '
     'with a sloped sill; grilles at the front elevation only.'),
    ('DOORS', '08 14 00 / 08 36 13', 'Insulated fiberglass entry door 3\'-0" x 6\'-8" with a glazed upper '
     'panel; carriage-style sectional garage door 16\'-0" x 7\'-0" with a top row of lites.'),
]

# ----------------------------------------------------------------------------- massing
# Plan rectangles grouped into roofed masses. check_massing() proves these tile the plan footprint.
MASSING = {
    'A': {
        'blocks': [
            {'name': 'MAIN BLOCK', 'rect': (0.0, 26.83, 38.0, 51.83), 'ridge': 'x', 'pitch': (8, 12)},
            {'name': 'FRONT WING', 'rect': (21.0, -6.0, 38.0, 26.83), 'ridge': 'y', 'pitch': (8, 12),
             'porch': (21.0, -6.0, 38.0, 0.0), 'inner_wall_y': 0.0},
            {'name': 'GARAGE', 'rect': (0.0, 5.0, 21.0, 26.83), 'ridge': 'y', 'pitch': (6, 12)},
        ],
        'footprint_check': [(0, 26.83, 38, 51.83), (21, 0, 38, 26.83), (0, 5, 21, 26.83)],
        'porch_sf': 102.0,
        'rear': {'kind': 'PATIO (UNCOVERED)', 'rect': (21.0, 51.83, 33.0, 57.83)},
    },
    'B': {
        # conformed 2026-09-03 to the re-proportioned PLAN_B (38'-0" body x 58'-6" deep) in tools/floorplans.py
        'blocks': [
            {'name': 'MAIN BLOCK', 'rect': (0.0, 29.0, 38.0, 57.5), 'ridge': 'x', 'pitch': (8, 12),
             'rear_porch': (24.0, 51.5, 38.0, 57.5)},
            {'name': 'FRONT WING', 'rect': (21.0, -6.0, 38.0, 29.0), 'ridge': 'y', 'pitch': (8, 12),
             'porch': (21.0, -6.0, 38.0, 0.0), 'inner_wall_y': 0.0},
            {'name': 'GARAGE', 'rect': (0.0, 5.0, 21.0, 29.0), 'ridge': 'y', 'pitch': (6, 12)},
        ],
        'footprint_check': [(0, 29, 38, 57.5), (21, 0, 38, 29), (0, 5, 21, 29)],
        'footprint_deduct': [(24, 51.5, 38, 57.5)],          # covered rear porch, recessed under the main roof
        'porch_sf': 102.0,
        'rear': {'kind': 'COVERED REAR PORCH', 'rect': (24.0, 51.5, 38.0, 57.5)},
    },
}


def build_model(pid):
    spec = fp.PLANS[pid]
    an = fp.analyze(spec)
    m = json.loads(json.dumps({k: v for k, v in MASSING[pid].items()}))
    plate = an['roof']['plate_ft'] + an['roof'].get('heel_ft', 0.5)
    for b in m['blocks']:
        x0, y0, x1, y1 = b['rect']
        b['span'] = (x1 - x0) if b['ridge'] == 'y' else (y1 - y0)
        b['eave'] = plate
        b['ridge_h'] = plate + b['span'] / 2.0 * (b['pitch'][0] / float(b['pitch'][1]))
    m['id'] = pid
    m['spec'] = spec
    m['an'] = an
    m['plate'] = plate
    m['openings'] = spec_openings_list(pid, an)
    m['max_ridge'] = max(b['ridge_h'] for b in m['blocks'])
    m['max_ridge_grade'] = m['max_ridge'] + FF
    return m


def spec_openings_list(pid, an):
    """Exterior openings as floorplans.py computes them (same list that reaches data/plans.json)."""
    spec = fp.PLANS[pid]
    walls = fp.build_walls(spec)
    return fp.exterior_openings(spec, walls)


def check_massing(m):
    """The massing rectangles must tile the plan's conditioned + garage footprint exactly, and the roof
    spans declared in the plan spec must equal the spans the massing actually has — the two drifted once
    when a plan's depth changed and only the massing was updated, which put the drawn ridge 4 in below the
    published one."""
    fails = []
    decl = {e['name']: e['span_ft'] for e in m['an']['roof']['elements']}
    for b in m['blocks']:
        for nm, sp in decl.items():
            key = b['name'].split()[0].lower()
            if (key == 'main' and nm.startswith('main')) or (key == 'front' and nm.startswith('front')) \
                    or (key == 'garage' and nm.startswith('garage')):
                if abs(sp - b['span']) > 0.02:
                    fails.append('roof element "%s" declares span %s but the %s massing is %s'
                                 % (nm, fti(sp), b['name'], fti(b['span'])))
    an = m['an']
    got = sum((r[2] - r[0]) * (r[3] - r[1]) for r in m['footprint_check'])
    got -= sum((r[2] - r[0]) * (r[3] - r[1]) for r in m.get('footprint_deduct', []))
    want = an['areas']['conditioned_sf'] + an['areas']['garage_sf']
    if abs(got - want) > 12.0:
        fails.append('massing area %.1f SF vs plan conditioned+garage %.1f SF (>12 SF apart)' % (got, want))
    bb = an['body_bbox']
    mx0 = min(b['rect'][0] for b in m['blocks']); mx1 = max(b['rect'][2] for b in m['blocks'])
    if abs(mx0 - bb[0]) > 0.02 or abs(mx1 - bb[2]) > 0.02:
        fails.append('massing x-extent %.2f..%.2f vs plan body bbox %.2f..%.2f' % (mx0, mx1, bb[0], bb[2]))
    return fails


def check_width(m):
    """Roof-to-roof width across the lot-line walls must fit the 40'-0" buildable width."""
    left = min(b['rect'][0] - side_overhang(b, 'x0') for b in m['blocks'])
    right = max(b['rect'][2] + side_overhang(b, 'x1') for b in m['blocks'])
    w = right - left
    body = max(b['rect'][2] for b in m['blocks']) - min(b['rect'][0] for b in m['blocks'])
    fails = []
    if w > LOT_BUILDABLE + 1e-6:
        fails.append('roof-to-roof width %s exceeds the %s buildable width (50-ft lot less two 5-ft side yards)'
                     % (fti(w), fti(LOT_BUILDABLE)))
    return fails, w, body


def side_overhang(b, edge):
    """Overhang beyond a lot-line (x) wall: rake if the ridge runs in x, eave if it runs in y."""
    return OH_SIDE


# ----------------------------------------------------------------------------- projection
def rvec(view):
    d = VD[view]
    return (d[1], -d[0])


def Hh(view, p):
    r = rvec(view)
    return p[0] * r[0] + p[1] * r[1]


def Dd(view, p):
    d = VD[view]
    return p[0] * d[0] + p[1] * d[1]


def h_range(view, rect):
    x0, y0, x1, y1 = rect
    hs = [Hh(view, q) for q in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    return min(hs), max(hs)


def d_near(view, rect):
    x0, y0, x1, y1 = rect
    return min(Dd(view, q) for q in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)))


def gable_end_toward(view, b):
    a = (1, 0) if b['ridge'] == 'x' else (0, 1)
    d = VD[view]
    return abs(a[0] * d[0] + a[1] * d[1]) > 0.5


def gable_top(h0, h1, eave, ridge_h, h):
    hc = (h0 + h1) / 2.0
    half = (h1 - h0) / 2.0
    if half <= 0:
        return eave
    return eave + (ridge_h - eave) * max(0.0, 1.0 - abs(h - hc) / half)


# ----------------------------------------------------------------------------- texture / element painting
def _lap(c, x0, y0, x1, y1, col, exp=0.5):
    y = y0 + exp
    while y < y1 - 0.02:
        c.line(x0, y, x1, y, lw=0.016, color=col)
        y += exp


def _batten(c, x0, y0, x1, y1, col, sp=1.0):
    x = x0 + sp
    while x < x1 - 0.02:
        c.line(x, y0, x, y1, lw=0.028, color=col)
        x += sp


def _stone(c, x0, y0, x1, y1, col):
    n, y = 0, y0 + 0.42
    while y < y1 - 0.02:
        c.line(x0, y, x1, min(y, y1), lw=0.018, color=col)
        x = x0 + 0.3 + (0.0 if n % 2 == 0 else 0.6)
        while x < x1 - 0.12:
            c.line(x, max(y - 0.42, y0), x, min(y, y1), lw=0.014, color=col)
            x += 1.2
        n += 1
        y += 0.42


def _brick(c, x0, y0, x1, y1, col):
    n, y = 0, y0 + 0.23
    while y < y1 - 0.02:
        c.line(x0, y, x1, min(y, y1), lw=0.013, color=col)
        x = x0 + 0.16 + (0.0 if n % 2 == 0 else 0.33)
        while x < x1 - 0.06:
            c.line(x, max(y - 0.23, y0), x, min(y, y1), lw=0.011, color=col)
            x += 0.67
        n += 1
        y += 0.23


def base_tex(S):
    return _brick if S['base_kind'] == 'brick' else _stone


def wall_band(c, S, h0, h1, z0, z1, base=True):
    """A rectangular piece of wall: masonry water table below, siding above."""
    if h1 - h0 <= 1e-6 or z1 - z0 <= 1e-6:
        return
    wt = FF + WATER_TABLE
    if base and z0 < wt:
        top = min(wt, z1)
        c.rect((h0, z0, h1, top), fill=S['base'], stroke='none')
        base_tex(S)(c, h0, z0, h1, top, S['base_line'])
        if top >= wt - 1e-6:
            c.rect((h0, wt - 0.19, h1, wt), fill=S['trim'], stroke=S['trim_line'], lw=0.018)
    lo = max(z0, wt) if base else z0
    if z1 > lo:
        c.rect((h0, lo, h1, z1), fill=S['siding'], stroke='none')
        (_batten if S['siding_kind'] == 'batten' else _lap)(c, h0, lo, h1, z1, S['siding_line'])


def gable_wall(c, S, h0, h1, eave, ridge_h, vent=True, brackets=False):
    hc = (h0 + h1) / 2.0
    tri = [(h0, eave), (hc, ridge_h), (h1, eave)]
    c.poly(tri, fill=S['siding'], stroke='none')
    y = eave + 0.5
    while y < ridge_h - 0.04:
        ch = _chord(tri, y)
        if ch:
            if S['siding_kind'] == 'batten':
                x = ch[0] + 0.25
                while x < ch[1] - 0.05:
                    c.line(x, max(y - 0.5, eave), x, y, lw=0.028, color=S['siding_line'])
                    x += 1.0
            else:
                c.line(ch[0], y, ch[1], y, lw=0.016, color=S['siding_line'])
        y += 0.5
    if vent and ridge_h - eave > 3.2:
        vw, vh = VENT
        vy = eave + (ridge_h - eave) * 0.42
        c.rect((hc - vw / 2, vy, hc + vw / 2, vy + vh), fill=S['trim'], stroke='#111', lw=0.024)
        k = vy + 0.2
        while k < vy + vh - 0.04:
            c.line(hc - vw / 2 + 0.09, k, hc + vw / 2 - 0.09, k, lw=0.016, color=S['trim_line'])
            k += 0.2
    if brackets:
        # cedar knee brace: post leg on the wall, diagonal, and a horizontal top under the rake (06 20 00)
        for sx, sgn in ((h0, 1), (h1, -1)):
            by = eave + 0.15
            leg = 1.5
            x_in = sx + sgn * 0.28
            c.rect((min(sx, x_in), by, max(sx, x_in), by + leg), fill=S['post'], stroke='#111', lw=0.022)
            top_out = sx + sgn * 1.55
            c.poly([(sx + sgn * 0.28, by + leg), (top_out, by + leg), (top_out, by + leg + 0.28),
                    (sx + sgn * 0.28, by + leg + 0.28)], fill=S['post'], stroke='#111', lw=0.022)
            c.poly([(sx + sgn * 0.28, by + 0.15), (top_out, by + leg), (top_out, by + leg - 0.34),
                    (sx + sgn * 0.28, by - 0.2)], fill=S['post'], stroke='#111', lw=0.022)


def _chord(pts, y):
    xs = []
    n = len(pts)
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
        if (ya - y) * (yb - y) < 0:
            xs.append(xa + (xb - xa) * (y - ya) / (yb - ya))
        elif abs(ya - y) < 1e-9:
            xs.append(xa)
    return (min(xs), max(xs)) if len(xs) >= 2 else None


def gutter(c, S, h0, h1, z):
    """5-in K-style gutter along an eave, with a downspout at each end (07 71 00)."""
    c.rect((h0, z - 0.42, h1, z - 0.05), fill=S['trim'], stroke='#111', lw=0.024)
    for hx, sgn in ((h0, 1), (h1, -1)):
        c.rect((hx + sgn * 0.12, 0, hx + sgn * 0.42, z - 0.42), fill=S['trim'], stroke='#111', lw=0.02)


def corner_and_frieze(c, S, h0, h1, z0, z1, frieze=True):
    c.rect((h0, z0, h0 + 0.42, z1), fill=S['trim'], stroke='#111', lw=0.022)
    c.rect((h1 - 0.42, z0, h1, z1), fill=S['trim'], stroke='#111', lw=0.022)
    if frieze:
        c.rect((h0, z1 - 0.55, h1, z1), fill=S['trim'], stroke='#111', lw=0.022)


def roof_poly(c, S, pts):
    c.poly(pts, fill=S['roof'], stroke='none')
    ys = [p[1] for p in pts]
    y, n = min(ys) + 0.75, 0
    while y < max(ys) - 0.06:
        ch = _chord(pts, y)
        if ch:
            c.line(ch[0], y, ch[1], y, lw=0.014, color=S['roof_line'])
            x = ch[0] + (0.6 if n % 2 else 1.8)          # shingle tabs, staggered course to course
            while x < ch[1] - 0.05:
                c.line(x, y, x, max(y - 0.32, min(ys)), lw=0.012, color=S['roof_line'])
                x += 2.4
        n += 1
        y += 0.75
    c.poly(pts, fill='none', stroke='#111', lw=0.042)


def opening(c, S, o, hc, z0):
    w, ht, t = o['width_ft'], o['height_ft'], o['type']
    x0, x1, z1 = hc - w / 2.0, hc + w / 2.0, z0 + o['height_ft']
    if t == 'garage':
        c.rect((x0 - 0.31, z0, x1 + 0.31, z1 + 0.31), fill=S['trim'], stroke='#111', lw=0.028)
        c.rect((x0, z0, x1, z1), fill=S['garage'], stroke='#111', lw=0.034)
        for i in range(1, 4):
            c.line(x0, z0 + (z1 - z0) * i / 4.0, x1, z0 + (z1 - z0) * i / 4.0, lw=0.02, color='#9A9A9A')
        c.line(hc, z0, hc, z1, lw=0.02, color='#9A9A9A')
        for k in (0.22, 0.44, 0.56, 0.78):
            cx = x0 + (x1 - x0) * k
            c.rect((cx - 0.6, z1 - (z1 - z0) / 4.0 + 0.13, cx + 0.6, z1 - 0.13), fill='#DCE5EA', stroke='#111', lw=0.018)
        return
    c.rect((x0 - 0.29, z0 - (0.0 if t == 'window' else 0.29), x1 + 0.29, z1 + 0.4), fill=S['trim'], stroke='#111', lw=0.026)
    if t == 'door':
        c.rect((x0, z0, x1, z1), fill=S['door'], stroke='#111', lw=0.034)
        c.rect((x0 + 0.28, z1 - 2.2, x1 - 0.28, z1 - 0.32), fill='#DCE5EA', stroke='#111', lw=0.02)
        c.rect((x0 + 0.28, z0 + 0.32, x1 - 0.28, z1 - 2.55), fill='none', stroke='#111', lw=0.018)
        c.circle(x1 - 0.42, z0 + 2.9, 0.085, fill='#8A7A5A', stroke='#111', lw=0.014)
        return
    if t == 'french':
        c.rect((x0, z0, x1, z1), fill='#DCE5EA', stroke='#111', lw=0.034)
        c.line(hc, z0, hc, z1, lw=0.034)
        for k in (1, 2):
            c.line(x0, z0 + (z1 - z0) * k / 3.0, x1, z0 + (z1 - z0) * k / 3.0, lw=0.016, color='#7C8B92')
        return
    c.rect((x0, z0, x1, z1), fill=S['sash'], stroke='#111', lw=0.034)
    lites = 2 if w >= 5.0 else 1
    for k in range(lites):
        gx0 = x0 + 0.15 + (w - 0.3) * k / lites
        gx1 = x0 + 0.15 + (w - 0.3) * (k + 1) / lites
        c.rect((gx0, z0 + 0.15, gx1, z1 - 0.15), fill='#DCE5EA', stroke='#111', lw=0.022)
        c.line(gx0, (z0 + z1) / 2.0, gx1, (z0 + z1) / 2.0, lw=0.028)
    c.rect((x0 - 0.33, z0 - 0.19, x1 + 0.33, z0), fill=S['trim'], stroke='#111', lw=0.022)


# ----------------------------------------------------------------------------- one elevation
def draw_elevation(c, m, view, S, dims=True):
    """Draw one elevation into canvas c with grade at y = 0 and paper-horizontal h unshifted."""
    blocks = sorted(m['blocks'], key=lambda b: -d_near(view, b['rect']))
    for b in blocks:
        b['_h'] = h_range(view, b['rect'])

    hmin = min(b['_h'][0] for b in m['blocks']) - OH_SIDE
    hmax = max(b['_h'][1] for b in m['blocks']) + OH_SIDE

    plate_z = FF + m['plate']
    for b in blocks:
        h0, h1 = b['_h']
        # b['eave'] and b['ridge_h'] are above the FINISHED FLOOR; the drawing datum is finished GRADE,
        # so every structural height is raised by the floor height FF. (Openings already use FF + sill.)
        eave, ridge_h = FF + b['eave'], FF + b['ridge_h']
        pitch = b['pitch'][0] / float(b['pitch'][1])
        gable = gable_end_toward(view, b)
        # overhang beyond the two h-ends of this block in this view
        oh = OH_SIDE if _h_axis_is_lot_line(view) else OH_FR
        porch = b.get('porch')
        p_h = h_range(view, porch) if porch else None

        if gable:
            if porch and view == 'front':
                # gable end above the porch header; the recessed front wall shows below
                inner = b['inner_wall_y']
                ih0, ih1 = h_range(view, (b['rect'][0], inner, b['rect'][2], inner))
                c.rect((ih0, 0, ih1, plate_z), fill='#EDEAE3', stroke='none')             # porch recess (shade)
                wall_band(c, S, ih0, ih1, 0, plate_z)
                c.rect((ih0, 0, ih1, plate_z), fill='#2B2B2B', stroke='none', opacity=0.10)
                for o in _openings_on(m, view, b, at_y=inner):
                    opening(c, S, o, Hh(view, o['at']), FF + o['sill_ft'])
                gable_wall(c, S, h0, h1, plate_z, ridge_h, brackets=True)
                c.rect((h0, plate_z - BEAM, h1, plate_z), fill=S['trim'], stroke='#111', lw=0.04)
            else:
                bay = b.get('rear_porch')
                bh = _draw_bay(c, S, view, b, bay, plate_z, eave) if (bay and _bay_at_face(view, b, bay)) else None
                for a_, b_ in (_segments(h0, h1, bh)):
                    wall_band(c, S, a_, b_, 0, eave)
                corner_and_frieze(c, S, h0, h1, FF + WATER_TABLE, eave, frieze=False)
                gable_wall(c, S, h0, h1, eave, ridge_h, brackets=bool(porch))
                for o in _openings_on(m, view, b):
                    opening(c, S, o, Hh(view, o['at']), FF + o['sill_ft'])
                if bh:
                    _close_bay(c, S, bh[0], bh[1], plate_z)
            drop = oh * pitch
            roof_poly(c, S, [(h0 - oh, eave - drop - FASCIA), (h0 - oh, eave - drop),
                             ((h0 + h1) / 2.0, ridge_h), (h1 + oh, eave - drop),
                             (h1 + oh, eave - drop - FASCIA), ((h0 + h1) / 2.0, ridge_h - FASCIA)])
            c.line(h0, 0, h0, eave, lw=0.05)
            c.line(h1, 0, h1, eave, lw=0.05)
        else:
            if porch:
                # side view across an integral porch: wall only outside the porch run
                seg = [(h0, p_h[0]), (p_h[1], h1)]
                for a, bb in seg:
                    wall_band(c, S, a, bb, 0, eave)
                c.rect((p_h[0], 0, p_h[1], plate_z - BEAM), fill='#3A3A3A', stroke='none', opacity=0.16)
                c.rect((p_h[0], plate_z - BEAM, p_h[1], plate_z), fill=S['trim'], stroke='#111', lw=0.03)
                _porch_base(c, S, p_h[0], p_h[1], plate_z, corner_only=True)
            else:
                bay = b.get('rear_porch')
                bh = _draw_bay(c, S, view, b, bay, plate_z, eave) if (bay and _bay_at_face(view, b, bay)) else None
                for a_, b_ in _segments(h0, h1, bh):
                    wall_band(c, S, a_, b_, 0, eave)
                corner_and_frieze(c, S, h0, h1, FF + WATER_TABLE, eave)
            for o in _openings_on(m, view, b):
                opening(c, S, o, Hh(view, o['at']), FF + o['sill_ft'])
            if not porch and b.get('rear_porch') and _bay_at_face(view, b, b['rear_porch']):
                _bh = h_range(view, b['rear_porch'])
                _close_bay(c, S, _bh[0], _bh[1], plate_z)
            gutter(c, S, h0 - oh, h1 + oh, eave)
            roof_poly(c, S, [(h0 - oh, eave - FASCIA), (h0 - oh, ridge_h), (h1 + oh, ridge_h), (h1 + oh, eave - FASCIA)])
            c.line(h0 - oh, ridge_h, h1 + oh, ridge_h, lw=0.055)
            c.line(h0 - oh, eave, h1 + oh, eave, lw=0.03, color='#666')

        if porch and view == 'front':
            _porch_base(c, S, p_h[0], p_h[1], plate_z)

    # ground line last so it reads over the masonry
    c.line(hmin - 2.0, 0, hmax + 2.0, 0, lw=0.085)
    x = hmin - 2.0
    while x < hmax + 2.0:
        c.line(x, 0, x - 0.4, -0.4, lw=0.018, color='#777')
        x += 1.0
    return hmin, hmax, m['max_ridge']



def _segments(h0, h1, skip):
    if not skip:
        return [(h0, h1)]
    out = []
    if skip[0] - h0 > 0.02:
        out.append((h0, skip[0]))
    if h1 - skip[1] > 0.02:
        out.append((skip[1], h1))
    return out


def _bay_at_face(view, b, bay):
    """True when a recessed bay (e.g. a covered rear porch carved out of the block) opens toward this view."""
    dn = d_near(view, b['rect'])
    return abs(d_near(view, bay) - dn) < 0.02


def _draw_bay(c, S, view, b, bay, plate_z, eave):
    """Draw a recessed covered bay: the wall set back inside it, in shade, with its beam and corner posts.
    Returns the paper h-range the solid wall must skip."""
    bh0, bh1 = h_range(view, bay)
    c.rect((bh0, 0, bh1, plate_z), fill='#EDEAE3', stroke='none')
    wall_band(c, S, bh0, bh1, 0, plate_z)
    c.rect((bh0, 0, bh1, plate_z), fill='#2B2B2B', stroke='none', opacity=0.18)
    c.line(bh0, plate_z - BEAM, bh1, plate_z - BEAM, lw=0.03, color='#444')      # porch ceiling / soffit
    return bh0, bh1


def _close_bay(c, S, bh0, bh1, plate_z):
    c.rect((bh0, plate_z - BEAM, bh1, plate_z), fill=S['trim'], stroke='#111', lw=0.034)
    for cx in (bh0 + COL / 2, bh1 - COL / 2):
        c.rect((cx - PIER_W / 2, 0, cx + PIER_W / 2, FF + PIER_H), fill=S['base'], stroke='#111', lw=0.028)
        base_tex(S)(c, cx - PIER_W / 2, 0, cx + PIER_W / 2, FF + PIER_H, S['base_line'])
        c.rect((cx - PIER_W / 2 - 0.1, FF + PIER_H, cx + PIER_W / 2 + 0.1, FF + PIER_H + 0.17),
               fill=S['trim'], stroke='#111', lw=0.022)
        c.rect((cx - COL / 2, FF + PIER_H + 0.17, cx + COL / 2, plate_z - BEAM),
               fill=S['post'], stroke='#111', lw=0.028)


def _h_axis_is_lot_line(view):
    """True when the paper-horizontal axis runs across the lot (front/rear views), so the h-ends of a
    block are the side (lot-line) walls and carry the 8-in overhang."""
    return view in ('front', 'rear')


def _porch_base(c, S, h0, h1, plate_z, corner_only=False):
    c.rect((h0, 0, h1, FF), fill=S['base'], stroke='#111', lw=0.028)
    base_tex(S)(c, h0, 0, h1, FF, S['base_line'])
    xs = _col_x(h0, h1) if not corner_only else [h0 + COL / 2, h1 - COL / 2]
    for cx in xs:
        c.rect((cx - PIER_W / 2, FF, cx + PIER_W / 2, FF + PIER_H), fill=S['base'], stroke='#111', lw=0.028)
        base_tex(S)(c, cx - PIER_W / 2, FF, cx + PIER_W / 2, FF + PIER_H, S['base_line'])
        c.rect((cx - PIER_W / 2 - 0.1, FF + PIER_H, cx + PIER_W / 2 + 0.1, FF + PIER_H + 0.17),
               fill=S['trim'], stroke='#111', lw=0.022)
        c.rect((cx - COL / 2, FF + PIER_H + 0.17, cx + COL / 2, plate_z - BEAM), fill=S['post'], stroke='#111', lw=0.028)


def _col_x(h0, h1, spacing_max=9.0):
    n = max(2, int(math.ceil((h1 - h0 - COL) / spacing_max)) + 1)
    return [h0 + COL / 2 + (h1 - h0 - COL) * k / (n - 1) for k in range(n)]


def _openings_on(m, view, b, at_y=None):
    """Openings of this view that sit on this block (optionally on a specific wall line)."""
    x0, y0, x1, y1 = b['rect']
    out = []
    for o in m['openings']:
        if o['wall'] != view:
            continue
        ax, ay = o['at']
        if not (x0 - 0.03 <= ax <= x1 + 0.03 and y0 - 0.03 <= ay <= y1 + 0.03):
            continue
        if at_y is not None and abs(ay - at_y) > 0.03:
            continue
        if at_y is None and b.get('porch') and view == 'front' and abs(ay - b['inner_wall_y']) < 0.03:
            continue
        out.append(o)
    return out


SHEET_IN = (24.0, 18.0)               # ARCH C landscape
PT_PER_FT = 13.5                      # 3/16 in = 1 ft-0 in


def _levels(c, m, h0, h1, view):
    """Level datum lines, the voluntary 24-ft ridge cap and the vertical dimension chain."""
    plate = FF + m['plate']
    top = FF + max(b['ridge_h'] for b in m['blocks'])
    x0, x1 = h0 - 0.8, h1 + 0.6
    for z, tag in ((0.0, 'FIN. GRADE 0\'-0"'), (FF, ''),
                   (plate, 'EAVE %s' % fti(plate)), (top, 'RIDGE %s' % fti(top))):
        c.line(x0, z, x1, z, lw=0.016, dash='0.5,0.35', color='#8A8A8A')
        if tag:
            c.text(x1 + 0.4, z, tag, size=0.46, anchor='start', color='#333')
    c.line(x0, CAP_RIDGE, x1, CAP_RIDGE, lw=0.05, dash='1.1,0.5', color='#B03A2E')
    c.text((h0 + h1) / 2.0, CAP_RIDGE + 0.75,
           '%s MAXIMUM RIDGE ABOVE FINISHED GRADE — VOLUNTARY ZONING CONDITION (Ord. 2023-603 Table 4.1 R-2 allows %s)'
           % (fti(CAP_RIDGE), fti(DISTRICT_MAX)), size=0.44, color='#B03A2E')
    dim_v(c, h0 - 2.1, 0, FF, fti(FF))
    dim_v(c, h0 - 2.1, FF, plate, fti(plate - FF))
    dim_v(c, h0 - 2.1, plate, top, fti(top - plate))
    dim_v(c, h0 - 3.9, 0, top, fti(top))


def dim_v(c, x, z0, z1, label, size=0.46, tick=0.3):
    c.line(x, z0, x, z1, lw=0.022)
    for z in (z0, z1):
        c.line(x - tick, z - tick * 0.7, x + tick, z + tick * 0.7, lw=0.022)
    c.text(x - 0.34, (z0 + z1) / 2.0, label, size=size, anchor='middle', rot=-90)


def dim_h(c, z, h0, h1, label, size=0.46, tick=0.3):
    c.line(h0, z, h1, z, lw=0.022)
    for h in (h0, h1):
        c.line(h - tick * 0.7, z - tick, h + tick * 0.7, z + tick, lw=0.022)
    c.text((h0 + h1) / 2.0, z - 0.55, label, size=size, anchor='middle')


def elevation_group(m, view, S, with_levels=True):
    """Render one elevation into an SVG group string plus its extents."""
    c = fp.Canvas(ymax=0.0)               # ymax set by the caller's translate; use 0 and flip later
    c.ymax = 0.0
    h0, h1, ridge = draw_elevation(c, m, view, S)
    body_h = h_range(view, _body_rect(m, view))
    if with_levels:
        _levels(c, m, h0, h1, view)
        dim_h(c, -2.6, h0, h1, 'ROOF TO ROOF %s' % fti(h1 - h0))
        dim_h(c, -4.4, body_h[0], body_h[1], 'BUILDING %s' % fti(body_h[1] - body_h[0]))
    return c.svg(), (h0, h1, ridge)


def _body_rect(m, view):
    x0 = min(b['rect'][0] for b in m['blocks']); x1 = max(b['rect'][2] for b in m['blocks'])
    y0 = min(b['rect'][1] for b in m['blocks']); y1 = max(b['rect'][3] for b in m['blocks'])
    return (x0, y0, x1, y1)


def _sheet_frame(c, Wf, Hf, m, sheet_no, subtitle, scale_note):
    mg, tb = 2.0, 7.6
    c.rect((mg, mg, Wf - mg, Hf - mg), fill='none', lw=0.12)
    c.rect((mg + 0.4, mg + 0.4, Wf - mg - 0.4, Hf - mg - 0.4), fill='none', lw=0.04)
    c.line(mg + 0.4, mg + 0.4 + tb, Wf - mg - 0.4, mg + 0.4 + tb, lw=0.08)
    c.line(Wf - mg - 0.4 - 13.0, mg + 0.4, Wf - mg - 0.4 - 13.0, mg + 0.4 + tb, lw=0.06)
    y = mg + 0.4 + tb - 1.25
    c.text(mg + 1.2, y, 'THE COTTAGES AT ARCADO SPRINGS — %s' % subtitle, size=0.95, weight='bold', anchor='start')
    y -= 1.25
    c.text(mg + 1.2, y, 'R-1 → R-2 REZONING (Lilburn Zoning Ordinance 2023-603 §1003-4; 2026 Application '
           'Instructions item (11)) — 4535 / 4537 / 4539 / 4541 Arcado Rd SW, Lilburn GA 30047 — Land Lot 123, '
           '6th District, Gwinnett County', size=0.44, anchor='start')
    y -= 1.05
    c.text(mg + 1.2, y, '%s · %s · Prepared by the owner-applicant (Mohammed Awad) with AI drafting tools · '
           'ILLUSTRATIVE — NOT FOR CONSTRUCTION · DRAFT, to be superseded by sealed drawings by a '
           'Georgia-registered architect' % (scale_note, REVISION), size=0.42, anchor='start')
    y -= 1.05
    c.text(mg + 1.2, y, DISCLAIMER, size=0.4, anchor='start', color='#222')
    y -= 0.95
    c.text(mg + 1.2, y, '<!-- ' + MARKER + ' -->', size=0.34, anchor='start', color='#AAA')
    c.text(Wf - mg - 7.0, mg + 0.4 + tb - 2.6, sheet_no, size=2.6, weight='bold', anchor='middle')
    c.text(Wf - mg - 7.0, mg + 0.4 + tb - 4.6, subtitle.split(' — ')[0], size=0.42, anchor='middle', color='#444')
    c.text(Wf - mg - 7.0, mg + 0.4 + tb - 5.6, DATE, size=0.42, anchor='middle', color='#444')
    return mg, tb


def make_elev_sheet(m, path, scheme='linework'):
    S = LINEWORK if scheme == 'linework' else SCHEMES[scheme]
    W, H = SHEET_IN[0] * 72, SHEET_IN[1] * 72
    Wf, Hf = W / PT_PER_FT, H / PT_PER_FT              # 128 x 96 drawing-feet
    c = fp.Canvas(ymax=Hf)
    mg, tb = _sheet_frame(c, Wf, Hf, m, 'A-2.%s' % ('1' if m['id'] == 'A' else '2'),
                          'PLAN %s "%s" — EXTERIOR ELEVATIONS' % (m['id'], m['spec']['name'].title()),
                          'Scale 3/16" = 1\'-0" on ARCH C (24 x 18 in)')
    cells = [('right', 9.0, 68.0), ('front', 81.0, 68.0), ('left', 9.0, 34.0), ('rear', 81.0, 34.0)]
    for view, X0, Y0 in cells:
        g, (h0, h1, ridge) = elevation_group(m, view, S)
        c.add('<g transform="translate(%.3f %.3f)">%s</g>' % (X0 - h0, Hf - Y0, g))
        c.text(X0 - h0 + (h0 + h1) / 2.0, Y0 - 6.4, VT[view], size=0.72, weight='bold')
        c.text(X0 - h0 + (h0 + h1) / 2.0, Y0 - 7.5, 'SCALE 3/16" = 1\'-0"', size=0.44, color='#444')
    _material_key(c, mg + 1.4, 24.0, Wf - 2 * mg - 2.8, m)
    body = c.svg()
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%gin" height="%gin" viewBox="0 0 %.3f %.3f" '
           'font-family="Helvetica, Arial, sans-serif"><rect width="%.3f" height="%.3f" fill="#fff"/>\n%s\n</svg>'
           % (SHEET_IN[0], SHEET_IN[1], Wf, Hf, Wf, Hf, body))
    open(path, 'w').write(svg + '\n<!-- ' + MARKER + ' -->\n')
    return path


def _material_key(c, x, y, w, m):
    c.text(x, y, 'MATERIALS AND COLOURS — Application Instructions item (11)', size=0.62, weight='bold', anchor='start')
    yy = y - 1.15
    for i, (name, csi, txt) in enumerate(MATERIAL_KEYS, 1):
        c.circle(x + 0.45, yy + 0.05, 0.42, fill='#fff', stroke='#111', lw=0.035)
        c.text(x + 0.45, yy + 0.05, str(i), size=0.44, weight='bold')
        c.text(x + 1.3, yy + 0.05, '%s  (%s)' % (name, csi), size=0.44, weight='bold', anchor='start')
        import textwrap
        tx = x + 9.5
        for k, ln in enumerate(textwrap.wrap(txt, 150)):
            c.text(tx, yy + 0.05 - k * 0.62, ln, size=0.42, anchor='start', color='#333')
        yy -= 0.6 * max(1, len(textwrap.wrap(txt, 150))) + 0.24
    yy -= 0.3
    for ln in ('WALL SIGNS: none proposed on any dwelling, the clubhouse or an accessory structure. One '
               'ground-mounted monument entry sign not exceeding 32 SF is proposed at the Arcado Road entrance — '
               'see sheet A-4 for its elevation, dimensions, materials and colours.',
               'HEIGHT: maximum ridge %s above finished grade — within the %s voluntary condition and well '
               'below the %s maximum of Ord. 2023-603 Table 4.1 (R-2). One story throughout; no basement.'
               % (fti(m['max_ridge_grade']), fti(CAP_RIDGE), fti(DISTRICT_MAX)),
               'GRADE: elevations are drawn on level finished grade. Finished floor is %s above finished grade at '
               'the front porch so the entry walk stays at or under 1:20 (zero-step entry, voluntary accessibility '
               'condition); grade falls away at the sides and rear. Lot grading is shown on sheet C-3.' % fti(FF)):
        import textwrap
        for ln2 in textwrap.wrap(ln, 205):
            c.text(x, yy, ln2, size=0.42, anchor='start', color='#222')
            yy -= 0.62
        yy -= 0.2


def make_color_sheet(models, path):
    """Sheet A-2.3 — the three colour schemes on the front elevation of both plans, plus a materials board.
    Instruction item (11): 'shall include the color and materials of all structures and roofing'."""
    W, H = SHEET_IN[0] * 72, SHEET_IN[1] * 72
    Wf, Hf = W / PT_PER_FT, H / PT_PER_FT
    c = fp.Canvas(ymax=Hf)
    _sheet_frame(c, Wf, Hf, models[0], 'A-2.3', 'EXTERIOR COLOUR SCHEMES AND MATERIALS',
                 'Scale 3/16" = 1\'-0" on ARCH C (24 x 18 in)')
    cols = [5.5, 45.5, 85.5]
    rows = [(models[0], 66.0), (models[1] if len(models) > 1 else models[0], 42.0)]
    for ci, key in enumerate(('1', '2', '3')):
        S = SCHEMES[key]
        c.text(cols[ci] + 19.0, 88.0, S['name'], size=0.86, weight='bold')
        for m, Y0 in rows:
            g, (h0, h1, _r) = elevation_group(m, 'front', S, with_levels=False)
            c.add('<g transform="translate(%.3f %.3f)">%s</g>' % (cols[ci] - h0, Hf - Y0, g))
            c.text(cols[ci] + (h1 - h0) / 2.0, Y0 - 2.6,
                   'PLAN %s "%s" — FRONT ELEVATION' % (m['id'], m['spec']['name'].title()), size=0.56, weight='bold')
    _swatches(c, 6.0, 34.0)
    _color_notes(c, 6.0, 18.6, Wf - 12.0)
    body = c.svg()
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%gin" height="%gin" viewBox="0 0 %.3f %.3f" '
           'font-family="Helvetica, Arial, sans-serif"><rect width="%.3f" height="%.3f" fill="#fff"/>\n%s\n</svg>'
           % (SHEET_IN[0], SHEET_IN[1], Wf, Hf, Wf, Hf, body))
    open(path, 'w').write(svg + '\n<!-- ' + MARKER + ' -->\n')
    return path


SWATCH_ROWS = [
    ('SIDING (07 46 46)', 'siding', ('Board-and-batten, warm white', 'Lap 6-in exposure, sage',
                                     'Lap 6-in exposure, clay/beige')),
    ('WATER TABLE / PIERS (04 20 00, 04 40 00)', 'base', ('Ledge stone, gray-tan blend',
                                                          'Modular brick, red-brown blend', 'Ledge stone, buff blend')),
    ('ROOFING (07 31 00)', 'roof', ('Architectural shingle, charcoal', 'Architectural shingle, weathered wood',
                                    'Architectural shingle, driftwood')),
    ('TRIM / FASCIA / FRIEZE (06 20 00, 09 91 13)', 'trim', ('Warm white', 'Soft white', 'Cream')),
    ('FRONT DOOR (08 14 00)', 'door', ('Deep green', 'Oxblood', 'Navy')),
    ('GARAGE DOOR (08 36 13)', 'garage', ('Painted to match trim', 'Painted to match siding',
                                          'Painted to match trim')),
    ('PORCH POSTS (06 20 00)', 'post', ('Western Red Cedar, natural stain', 'Western Red Cedar, natural stain',
                                        'Western Red Cedar, natural stain')),
]


def _swatches(c, x, y):
    c.text(x, y + 1.6, 'MATERIAL AND COLOUR BOARD — basis of design per docs/12-outline-specifications.md; '
           'final selections by the Owner and Architect from the manufacturers\' full ranges',
           size=0.56, weight='bold', anchor='start')
    colw = 41.0
    for ci, key in enumerate(('1', '2', '3')):
        c.text(x + 21.0 + ci * colw, y + 0.4, SCHEMES[key]['name'], size=0.5, weight='bold')
    yy = y - 0.9
    for label, field, notes in SWATCH_ROWS:
        c.text(x, yy - 0.55, label, size=0.44, anchor='start', weight='bold')
        for ci, key in enumerate(('1', '2', '3')):
            S = SCHEMES[key]
            bx = x + 17.0 + ci * colw
            c.rect((bx, yy - 1.25, bx + 3.4, yy + 0.15), fill=S[field], stroke='#111', lw=0.03)
            c.text(bx + 3.9, yy - 0.55, notes[ci], size=0.42, anchor='start', color='#222')
        yy -= 1.85


def _color_notes(c, x, y, w):
    import textwrap
    lines = [
        'Every dwelling is one story. Colour schemes are distributed so that no scheme repeats on adjacent '
        'lots and no scheme exceeds 40 % of the 43 lots; the distribution is a voluntary condition and is '
        'administered by the homeowners association.',
        'Roofing is the same product on every dwelling, the clubhouse and the mail kiosk; only the colour '
        'changes with the scheme.',
        'WALL SIGNS: none are proposed on any dwelling, on the clubhouse or on any accessory structure. '
        'One ground-mounted monument entry sign not exceeding 32 SF in face area and 6\'-0" in height is '
        'proposed at the Arcado Road entrance; see sheet A-4 for its elevation, dimensions, materials, '
        'colours and sight-triangle clearance.',
        'These elevations are illustrative and are drawn to scale. They are DRAFT work by the '
        'owner-applicant and are to be superseded by sealed drawings by a Georgia-registered architect '
        'before any building permit.',
    ]
    yy = y
    for ln in lines:
        for k, seg in enumerate(textwrap.wrap(ln, 200)):
            c.text(x, yy, seg, size=0.44, anchor='start', color='#222')
            yy -= 0.62
        yy -= 0.25


def make_ref_image(m, view, scheme, path, px_per_ft=48.0, pad=3.0):
    """A tight, furniture-free coloured elevation — the structural reference handed to an image model so a
    photoreal rendering cannot contradict the drawn dimensions. No dimensions, no title block, no notes."""
    S = SCHEMES[scheme]
    probe = fp.Canvas(ymax=0.0)
    h0, h1, ridge = draw_elevation(probe, m, view, S)
    top = max(b['ridge_h'] for b in m['blocks']) + 1.2
    w, hgt = (h1 - h0) + 2 * pad, top + 2 * pad
    c = fp.Canvas(ymax=hgt - pad)
    draw_elevation(c, m, view, S)
    body = '<g transform="translate(%.3f 0)">%s</g>' % (pad - h0, c.svg())
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%.0f" height="%.0f" viewBox="0 0 %.3f %.3f" '
           'font-family="Helvetica, Arial, sans-serif"><rect width="%.3f" height="%.3f" fill="#FBFAF7"/>\n%s\n</svg>'
           % (w * px_per_ft, hgt * px_per_ft, w, hgt, w, hgt, body))
    open(path, 'w').write(svg)
    fp.render_png(path, path[:-4] + '.png', px_scale=1.0)
    return path[:-4] + '.png'


def build(pid):
    m = build_model(pid)
    fails = check_massing(m)
    f2, w, body = check_width(m)
    fails += f2
    p = os.path.join(DRAW, 'plan-%s-elev.svg' % pid.lower())
    make_elev_sheet(m, p)
    fp.render_png(p, p[:-4] + '.png', dpi=150)
    print('PLAN %s: body %s, roof-to-roof %s, ridge %s AFF / %s above grade -> %s'
          % (pid, fti(body), fti(w), fti(m['max_ridge']), fti(m['max_ridge_grade']), p))
    for f in fails:
        print('   FAIL:', f)
    return m, fails


if __name__ == '__main__':
    ids = sys.argv[1:] or list(fp.PLANS)
    models = []
    for pid in ids:
        m, _f = build(pid)
        models.append(m)
    REF = os.path.join(ROOT, 'renderings', 'reference')
    os.makedirs(REF, exist_ok=True)
    for m in models:
        for view in ('front', 'rear', 'right', 'left'):
            for sch in ('1', '2', '3'):
                if view != 'front' and sch != '2':
                    continue
                q = os.path.join(REF, 'ref-plan-%s-%s-scheme%s.svg' % (m['id'].lower(), view, sch))
                print('   ref ->', make_ref_image(m, view, sch, q))
    if len(models) >= 1:
        p = os.path.join(DRAW, 'plan-colors.svg')
        make_color_sheet(models, p)
        fp.render_png(p, p[:-4] + '.png', dpi=150)
        print('colour sheet ->', p)
