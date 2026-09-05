#!/usr/bin/env python3
"""Sheets C-2.1 and C-2.2 — MASTER CONCEPT PLAN ENLARGEMENTS, BLOCK A and BLOCK B.

    python3 tools/enlargements.py   ->  drawings/mcp-enlargement-a.svg + .png
                                        drawings/mcp-enlargement-b.svg + .png

Two ARCH D 36 x 24 in sheets at 1" = 30', built on tools/sitebase.py in the same site-local
(u, v) system as Sheet C-0 (tools/existing_conditions.py) and Sheet C-2.0, so the three
overlay each other exactly.  Sheet C-2.1 covers u -40 to +1,000 (Block A / Phase 1) and
Sheet C-2.2 covers u 960 to 1,760 (Block B / Phase 2); the two share a match line at
u = 980, which is also the block line and the phase line and which falls on lot lines
(City of Lilburn Site Development Plan Review Checklist section 4.i, "Phasing is not
permitted unless platted in Blocks").

WHY THESE SHEETS EXIST
The 2026-09-03 drawing-standards audit (audit-2026-09-03/drawing-standards.md section 3.1)
records that at 1" = 60' a planner cannot check a 5-ft side yard, a 5-ft garage recess or a
20-ft buffer easement, and prescribes C-2.1 / C-2.2 as the lot-level review sheets: every lot
dimensioned 50'-0" x 100'-0" with its block and lot number, the setback envelope dimensioned
15 / 5 / 20, the 20-ft buffer easement dimensioned, the driveway dimensioned and its material
labelled, the garage-door setback and the 5'-0" recess called out, the lane tract dimensioned
with its pavement, strip and sidewalk widths, hydrants, and a match line with a key plan on
each sheet.  C-2.2 additionally carries the creek-woods tract, the stream buffers with the
75-ft impervious setback dimensioned, the rear basin with its easements, and the terminus
green and hammerhead.

EVERY DIMENSION ON BOTH SHEETS IS READ OUT OF data/layout.json AT RUN TIME.  Nothing is
transcribed from an older document, and nothing in data/, docs/ or tools/sitebase.py is
written by this script.

Two things this file does not take from tools/sitebase.py, and why:
  * sitebase.lots() is written against an older data/layout.json schema (it reads
    L['porch_rect'] / L['rear_rect'], which the 2026-09-03 regeneration replaced with
    house.porch_rects / house.rear_porch_rects / house.patio_rects) and raises KeyError on
    the current file.  lots_layer() below draws the current schema.
  * data/layout.json still carries a `lift_station_symbol` and a `sewer.phase2_primary`
    string describing an in-tract lift station / grinder system.  That position was
    CORRECTED on 2026-09-03 (audit-2026-09-03/external-facts.md section 4.1): Gwinnett DWR's
    Standard Policy for Private Developments (Condominiums, Townhomes and Subdivisions,
    rev. 9/2018) allows private pump stations, force mains and gravity sewers "only ... for
    commercial properties under single ownership within a development", and WSR-24
    section 1.3.1(A) allows a county station only where gravity is "more than 5,000 feet
    down gradient" against an actual 178 ft.  Neither symbol nor string is drawn.

Lettering: every text element placed by this file is at least 13.1 pt, i.e. a cap height of
0.125 in (1/8 in) at full size in Liberation Sans (cap height 1409/2048 em = 0.688), so an
11 x 17 reduction still reads at 0.059 in.

DRAFT - NOT SEALED.  Lot geometry, setbacks, buffers, basins and easements are concept
information for a rezoning application; a Georgia RLS boundary survey, a PE civil design and
a registered landscape architect's buffer and landscape plan are required and govern.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitebase as sb                                       # noqa: E402

L = sb.LAYOUT
M = L['metrics']
LANE = L['lane']
FS = 13.1                       # 1/8-in cap height at full size — the floor for every label
FS_S = 13.1
FS_H = 17.0                     # column headings
DIMC = '#b0003a'                # dimension colour (red-violet, reads over every fill)
PHC = '#7b1fa2'                 # phase / block / match line
BUF_LINE = '#4f7a2a'

SCALE = sb.SCALE30              # 1" = 30' -> 2.4 pt / ft
DATE = sb.DATE


# ============================================================================ small helpers
def ft(x):
    """Architectural notation:  50.0 -> 50'-0" ,  26.667 -> 26'-8" ."""
    neg = x < 0
    x = abs(x)
    f = int(math.floor(x + 1e-7))
    i = int(round((x - f) * 12.0))
    if i == 12:
        f += 1
        i = 0
    return ('-' if neg else '') + '%d\'-%d"' % (f, i)


def interp(path, u):
    if u <= path[0][0]:
        return path[0][1]
    for i in range(len(path) - 1):
        (u0, v0), (u1, v1) = path[i], path[i + 1]
        if u0 <= u <= u1 and u1 > u0:
            return v0 + (v1 - v0) * (u - u0) / (u1 - u0)
    return path[-1][1]


def band_edges(poly, u):
    """A band polygon written as N points along one side then N along the other, reversed.
    Returns (v_low_side, v_high_side) at station u, or (None, None) outside the band."""
    n = len(poly) // 2
    a = [tuple(p) for p in poly[:n]]
    b = [tuple(p) for p in poly[n:]][::-1]
    if u < min(a[0][0], b[0][0]) - 1e-6 or u > max(a[-1][0], b[-1][0]) + 1e-6:
        return (None, None)
    return (interp(a, u), interp(b, u))


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / l2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def dist_to_streams(p):
    """Minimum distance from a plan point to any digitised stream reach (all three)."""
    best = 1e9
    for s in L['stream_setbacks']:
        st = [tuple(q) for q in s['stream']]
        for i in range(len(st) - 1):
            best = min(best, seg_dist(p, st[i], st[i + 1]))
    return best


def eg_at(u, v):
    """Existing ground (NAVD88 ft) by inverse-distance weighting of the four nearest
    USGS 3DEP samples in data/topo-samples.json.  APPROXIMATE — no topographic survey."""
    S = sorted(sb.TOPO['samples'], key=lambda s: (s['u'] - u) ** 2 + (s['v'] - v) ** 2)[:4]
    num = den = 0.0
    for s in S:
        d = math.hypot(s['u'] - u, s['v'] - v)
        if d < 0.5:
            return s['z_ft']
        w = 1.0 / (d * d)
        num += w * s['z_ft']
        den += w
    return num / den


# ============================================================================ derived geometry
CL = [tuple(p) for p in LANE['centerline']]
TRACT = LANE['tract_polygon']
PAVE = LANE['pavement_polygon']
WALKS = [(s['side'], s['polygon']) for s in LANE['sidewalks'] if 'entry' not in s['side']]
U_MATCH = float(L['phase_line_u'])                          # 980.0 — block, phase and match line
U_REAR = sb.U_REAR


def cl_v(u):
    return interp(CL, u)


def station(u):
    """Travelled-way station from the Arcado Rd right-of-way (entry drive + lane)."""
    return LANE['entry_drive']['length_ft'] + max(0.0, u - CL[0][0])


def lane_section(u):
    """The cross-section chain at station u as [(v0, v1, label), ...] from SW to NE."""
    t0, t1 = band_edges(TRACT, u)
    p0, p1 = band_edges(PAVE, u)
    if t0 is None or p0 is None:
        return []
    cuts = [(min(t0, t1), 'tract'), (max(t0, t1), 'tract'),
            (min(p0, p1), 'pave'), (max(p0, p1), 'pave')]
    for side, poly in WALKS:
        w0, w1 = band_edges(poly, u)
        if w0 is not None:
            cuts += [(min(w0, w1), 'walk'), (max(w0, w1), 'walk')]
    vs = sorted(set(round(c[0], 3) for c in cuts))
    out = []
    for i in range(len(vs) - 1):
        a, b = vs[i], vs[i + 1]
        mid = (a + b) / 2.0
        if min(p0, p1) < mid < max(p0, p1):
            lab = 'PVMT'
        else:
            lab = 'STRIP'
            for side, poly in WALKS:
                w0, w1 = band_edges(poly, u)
                if w0 is not None and min(w0, w1) < mid < max(w0, w1):
                    lab = 'WALK'
        out.append((a, b, lab))
    return out


def buffer_bands():
    """The continuous 20-ft undisturbed perimeter buffer along the SW, NE and NW lines."""
    us = [u for u in range(-30, int(U_REAR) + 1, 10)] + [U_REAR - 0.5]
    sw = [(u, sb.SW(u)) for u in us if u >= 0]
    ne = [(u, sb.NE(u)) for u in us if u >= 0]
    b_sw = sw + [(u, v + 20.0) for u, v in sw][::-1]
    b_ne = ne + [(u, v - 20.0) for u, v in ne][::-1]
    rear = [tuple(p) for p in sb.REAR_LINE]
    b_rear = rear + [(u - 20.0, v) for u, v in rear][::-1]
    return b_sw, b_ne, b_rear


def sw_tract(u0, u1):
    """A common-open-space tract on the SW side, boundary line to the lane tract line."""
    return [(u0, sb.SW(u0)), (u1, sb.SW(u1)), (u1, sb.SW(u1) + 100.0), (u0, sb.SW(u0) + 100.0)]


CREEK_WOODS = sw_tract(1280.0, 1480.0)                      # 20,000 SF tract in open_space_tracts
STREAM_TRACT = sw_tract(1230.0, 1280.0)                     # 5,000 SF tract in open_space_tracts

# --- proposed fire hydrants ------------------------------------------------------------
# Gwinnett DWR Water and Sewer Standards (April 2016) section 2.2.15(b): hydrants "generally
# located every 400 feet ... spaced from a minimum of 350 feet to an absolute maximum of
# 450 feet", with "a fire hydrant near the end of each main".  docs/08 Memo C adds that a
# hydrant standing on a fire-apparatus access road wants 26 ft of road width (IFC 2024 (GA)
# Appendix D103.1), so every hydrant below is placed in a common tract where the lane
# locally widens rather than in the 2-ft strip.  Positions are checked against the 75-ft
# stream impervious setback at run time by _selfcheck().
HYDRANTS = [('FH-1', 205.0, -152.0, 'front amenity tract'),
            ('FH-2', 565.0, -139.0, 'pocket green, hammerhead 1'),
            ('FH-3', 975.0, -142.0, 'Pond 1 tract'),
            ('FH-4', 1330.0, -142.0, 'creek-woods tract'),
            ('FH-5', 1706.0, -140.0, 'terminus green, hammerhead 3')]
WATER_MAIN = [(u, cl_v(u) + 12.0) for u in [CL[0][0]] + list(range(160, int(CL[-1][0]) + 1, 20))]

# --- Pond 2 concept easements (Sheet C-2.2) ---------------------------------------------
P2 = [tuple(p) for p in L['ponds'][1]['polygon']]
P2_U0, P2_U1 = min(p[0] for p in P2), max(p[0] for p in P2)
P2_V0, P2_V1 = min(p[1] for p in P2), max(p[1] for p in P2)
P2_TRACT = [tuple(p) for p in L['ponds'][1]['tract_polygon']]
DRAIN_ESMT = [(P2_U0 - 10, P2_V0 - 10), (P2_U1 + 10, P2_V0 - 10),
              (P2_U1 + 10, P2_V1 + 10), (P2_U0 - 10, P2_V1 + 10)]
BMP_ESMT = [(1630.0, P2_V1), (1660.0, P2_V1), (1660.0, sb.SW(1660) + 100.0), (1630.0, sb.SW(1630) + 100.0)]
BMP_ROAD = [(1637.5, P2_V1), (1652.5, P2_V1), (1652.5, sb.SW(1652.5) + 100.0), (1637.5, sb.SW(1637.5) + 100.0)]


def lots_of(block):
    return [x for x in L['lots'] if x['block'] == block]


def lots_in(u0, u1):
    return [x for x in L['lots']
            if max(p[0] for p in x['polygon']) > u0 and min(p[0] for p in x['polygon']) < u1]


def runs_of(side, u0, u1):
    """Contiguous 50-ft lot runs on one side inside [u0, u1] -> [[lot, ...], ...]."""
    got = sorted([x for x in lots_in(u0, u1) if x['side'] == side],
                 key=lambda x: min(p[0] for p in x['polygon']))
    runs, cur = [], []
    for x in got:
        a = min(p[0] for p in x['polygon'])
        if cur and abs(a - max(p[0] for p in cur[-1]['polygon'])) > 0.01:
            runs.append(cur)
            cur = []
        cur.append(x)
    if cur:
        runs.append(cur)
    return runs


# ============================================================================ drawing helpers
def dim(c, p0, p1, text, off=0.0, size=FS, color=DIMC, textoff=None, witness=True,
        lw=0.6, tick=2.0, halo=True):
    """A dimension between two plan points, offset `off` ft to the left of p0 -> p1."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    Lg = math.hypot(dx, dy) or 1.0
    ux, uy = dx / Lg, dy / Lg
    nx, ny = -uy, ux
    a = (p0[0] + nx * off, p0[1] + ny * off)
    b = (p1[0] + nx * off, p1[1] + ny * off)
    c.line(a, b, stroke=color, stroke_width=lw)
    if witness and abs(off) > 0.01:
        e = 2.0 if off > 0 else -2.0
        c.line(p0, (p0[0] + nx * (off + e), p0[1] + ny * (off + e)), stroke=color, stroke_width=0.35)
        c.line(p1, (p1[0] + nx * (off + e), p1[1] + ny * (off + e)), stroke=color, stroke_width=0.35)
    for q in (a, b):
        c.line((q[0] - (ux + nx) * tick, q[1] - (uy + ny) * tick),
               (q[0] + (ux + nx) * tick, q[1] + (uy + ny) * tick), stroke=color, stroke_width=0.9)
    if text is None:
        return
    m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
    to = textoff if textoff is not None else (size / c.s) * 0.40
    rot = c.rot_of(a, b)
    if rot > 89.0:                    # vertical dimensions always read bottom-to-top
        rot -= 180.0
    c.text(m[0] + nx * to, m[1] + ny * to, text, size=size, rot=rot, fill=color, halo=halo)


def dimchain(c, pts, labels, off, size=FS, color=DIMC, textoff=None, textoffs=None):
    for i in range(len(pts) - 1):
        dim(c, pts[i], pts[i + 1], labels[i], off=off, size=size, color=color,
            textoff=(textoffs[i] if textoffs else textoff), witness=(i == 0 or i == len(pts) - 2))


def leader(c, at, to, lines, size=FS, color=DIMC, anchor='start', bold_first=False):
    c.line(at, to, stroke=color, stroke_width=0.6)
    c.circle(at, 2.0, fill=color, stroke='none')
    dv = -(size / c.s) * (0.35 + 1.15 * (len(lines) - 1)) if to[1] > at[1] else (size / c.s) * 1.0
    c.textlines(to[0] + (2.0 if anchor == 'start' else -2.0), to[1] + dv, lines, size=size,
                anchor=anchor, gap=1.15, fill=color, halo=True, bold_first=bold_first)


def north(c, x, y, r=42.0):
    a = math.radians(sb.NORTH_DEG)
    dx, dy = math.cos(a), -math.sin(a)
    px, py = -dy, dx
    c.scircle(x, y, r, fill='#fff', stroke='#000', stroke_width=1.0)
    tip = (x + dx * r * 0.84, y + dy * r * 0.84)
    tail = (x - dx * r * 0.76, y - dy * r * 0.76)
    c.sline(tail[0], tail[1], tip[0], tip[1], stroke='#000', stroke_width=2.6)
    c.spoly([tip, (tip[0] - 22 * dx + 8.0 * px, tip[1] - 22 * dy + 8.0 * py),
             (tip[0] - 22 * dx - 8.0 * px, tip[1] - 22 * dy - 8.0 * py)], fill='#000')
    c.stext(tip[0] + 14 * dx, tip[1] + 14 * dy + 6, 'N', size=20, bold=True, anchor='middle')
    c.stext(x, y + r + 16, 'GRID NORTH (SR 2240 GA WEST)', size=FS, anchor='middle')
    c.stext(x, y + r + 32, "= 28°43' ABOVE THE +u AXIS", size=FS, anchor='middle')


def gscale(c, x, y, scale=SCALE, step=30, steps=6):
    h = 11.0
    for k in range(steps):
        c.srect(x + step * scale * k, y, step * scale, h,
                fill='#000' if k % 2 == 0 else '#fff', stroke='#000', stroke_width=0.8)
        c.stext(x + step * scale * k, y - 6, str(step * k), size=FS, anchor='middle')
    c.stext(x + step * scale * steps, y - 6, '%d ft' % (step * steps), size=FS, anchor='middle')
    c.stext(x + step * scale * steps / 2.0, y + h + 18, 'GRAPHIC SCALE  1" = %d\'' % round(72.0 / scale),
            size=FS + 2, bold=True, anchor='middle')


def watermark(c, px, py, pw, ph, text):
    c.add('<text x="%.1f" y="%.1f" font-size="46" fill="#c00" fill-opacity="0.085" font-weight="bold" '
          'text-anchor="middle" transform="rotate(-6 %.1f %.1f)">%s</text>'
          % (px + pw / 2, py + ph * 0.52, px + pw / 2, py + ph * 0.52, sb.esc(text)))


def block(c, x, y, title, lines, w=690, size=FS, lead=16.4, gap=6.0):
    """A numbered-note column.  Returns the bottom y."""
    c.stext(x, y, title, size=FS_H, bold=True)
    y += FS_H + 6
    chars = max(int(w / (0.56 * size)), 10)
    for i, t in enumerate(lines, 1):
        y = c.stextblock(x, y, '%d.  %s' % (i, t), size=size, chars=chars, lead=lead, indent=15)
        y += gap
    return y


# ============================================================================ plan layers
def lots_layer(c, lots, labels=True, dim_lots=True, key_lots=()):
    """Lots, buffer easements, setback envelopes, driveways and the two house plans."""
    c.add('<g id="lots">')
    for x in lots:
        c.poly([tuple(p) for p in x['polygon']], fill='#fff', stroke='#111', stroke_width=1.1)
    for x in lots:
        h = x['house']
        c.poly([tuple(p) for p in x['buffer_easement']], fill='none', stroke=BUF_LINE,
               stroke_width=0.7, stroke_dasharray='7 3')
        c.poly([tuple(p) for p in x['setback_envelope']], fill='none', stroke='#888',
               stroke_width=0.6, stroke_dasharray='5 3')
        c.poly([tuple(p) for p in x['driveway_rect']], fill='#e3e3e3', stroke='#666', stroke_width=0.5)
        for r in h['patio_rects'] + h['rear_porch_rects'] + h['porch_rects']:
            c.poly([tuple(p) for p in r], fill='#fdf1de', stroke='#333', stroke_width=0.5)
        c.poly([tuple(p) for p in h['body_polygon']], fill=sb.C['house'], stroke='#111', stroke_width=1.0)
        c.poly([tuple(p) for p in h['garage_rect']], fill='#efd2ad', stroke='#111', stroke_width=0.7)
    c.add('</g>')
    if not labels:
        return
    for x in lots:
        poly = [tuple(p) for p in x['polygon']]
        uc = sum(p[0] for p in poly) / 4.0
        hv = [p[1] for p in x['house']['body_polygon']]
        vc = (min(hv) + 12.5) if x['side'] == 'SW' else (max(hv) - 12.5)
        c.textlines(uc, vc - 6.0, ['LOT %s-%d' % (x['block'], x['block_lot']),
                                   'PLAN %s' % x['plan'],
                                   'EG ±%.0f' % eg_at(uc, vc)],
                    size=FS, gap=1.16, bold_first=True, halo=True)
    if not dim_lots:
        return
    # 100'-0" depth dimension on every lot side line, in the side-yard gap
    for x in lots:
        poly = [tuple(p) for p in x['polygon']]
        u0 = min(p[0] for p in poly)
        u1 = max(p[0] for p in poly)
        for u in ([u0, u1] if x is lots[-1] else [u0]):
            va = interp(sorted([(p[0], p[1]) for p in poly if p[1] < (min(q[1] for q in poly) + 50)]), u)
            vs = sorted(p[1] for p in poly)
            lo = (vs[0] + vs[1]) / 2.0
            hi = (vs[2] + vs[3]) / 2.0
            c.line((u - 3.0, lo), (u + 3.0, lo), stroke=DIMC, stroke_width=0.8)
            c.line((u - 3.0, hi), (u + 3.0, hi), stroke=DIMC, stroke_width=0.8)
            c.text(u + (FS / c.s) * 0.36, (lo + hi) / 2.0, ft(100.0), size=FS, rot=-90,
                   fill=DIMC, halo=True)


def lot_width_chains(c, u0, u1, size=FS):
    """A 50'-0" dimension chain outside each property line, one bay per lot."""
    for side in ('SW', 'NE'):
        for run in runs_of(side, u0, u1):
            us = [min(p[0] for p in run[0]['polygon'])] + [max(p[0] for p in x['polygon']) for x in run]
            line = sb.SW if side == 'SW' else sb.NE
            pts = [(u, line(u)) for u in us]
            off = -5.0 if side == 'SW' else 5.0
            toff = -(size / c.s) * 1.05 if side == 'SW' else (size / c.s) * 0.38
            dimchain(c, pts, [ft(50.0)] * (len(pts) - 1), off=off, size=size, textoff=toff)


def buffers_layer(c, labels=True, at=()):
    b_sw, b_ne, b_rear = buffer_bands()
    c.add('<g id="buffer">')
    for b in (b_sw, b_ne, b_rear):
        c.poly(b, fill='url(#bufhatch)', stroke=BUF_LINE, stroke_width=0.8)
    c.add('</g>')
    if not labels:
        return
    for (u, side) in at:
        if side == 'SW':
            p0, p1 = (u, sb.SW(u)), (u, sb.SW(u) + 20.0)
        else:
            p0, p1 = (u, sb.NE(u) - 20.0), (u, sb.NE(u))
        dim(c, p0, p1, ft(20.0), off=0.0, size=FS, color=BUF_LINE,
            textoff=(FS / c.s) * 0.36, witness=False)


def lane_layer(c, labels=True):
    c.add('<g id="lane">')
    c.poly([tuple(p) for p in LANE['tract_polygon']], fill='#f3f3f0', stroke='#555',
           stroke_width=0.8, stroke_dasharray='9 4')
    c.poly([tuple(p) for p in LANE['entry_drive']['tract_polygon']], fill='#f3f3f0', stroke='#555',
           stroke_width=0.8, stroke_dasharray='9 4')
    for h in L['hammerheads']:
        for leg in h['legs']:
            c.poly([tuple(p) for p in leg], fill=sb.C['pave'], stroke='#333', stroke_width=0.9)
    c.poly([tuple(p) for p in LANE['entry_drive']['pavement_polygon']], fill=sb.C['pave'],
           stroke='#333', stroke_width=0.9)
    c.poly([tuple(p) for p in LANE['pavement_polygon']], fill=sb.C['pave'], stroke='#333', stroke_width=0.9)
    for s in LANE['sidewalks']:
        c.poly([tuple(p) for p in s['polygon']], fill='#fafafa', stroke='#777', stroke_width=0.5)
    c.pline(CL, fill='none', stroke='#555', stroke_width=0.5, stroke_dasharray='18 4 3 4')
    c.add('</g>')


def lane_section_dim(c, u, side=1, size=FS):
    """Dimension the lane tract across station u.  Each component is dimensioned on its own
    offset station so that a 2-ft strip and a 5-ft walk never share a label position, and the
    full breakdown is written along the lane."""
    sec = lane_section(u)
    if not sec:
        return
    names = {'PVMT': 'ASPHALT PAVEMENT', 'WALK': 'CONCRETE SIDEWALK', 'STRIP': 'STRIP'}
    pav = [x for x in sec if x[2] == 'PVMT'][0]
    tot = sec[-1][1] - sec[0][0]
    step = (size / c.s) * 0.36
    c.line((u - 30.0, sec[0][0]), (u + 26.0, sec[0][0]), stroke=DIMC, stroke_width=0.35)
    c.line((u - 30.0, sec[-1][1]), (u + 26.0, sec[-1][1]), stroke=DIMC, stroke_width=0.35)
    dim(c, (u, pav[0]), (u, pav[1]), ft(pav[1] - pav[0]), off=0.0, size=size, textoff=step)
    k = 0
    for x in sec:
        if x[2] == 'PVMT' or (x[1] - x[0]) < 1.5:
            continue
        k += 1
        uu = u + 9.0 * k if x[0] >= pav[1] else u - 9.0 * k
        c.line((u, x[0]), (uu, x[0]), stroke=DIMC, stroke_width=0.3)
        c.line((u, x[1]), (uu, x[1]), stroke=DIMC, stroke_width=0.3)
        dim(c, (uu, x[0]), (uu, x[1]), ft(x[1] - x[0]), off=0.0, size=size, textoff=step,
            witness=False)
    dim(c, (u - 30.0, sec[0][0]), (u - 30.0, sec[-1][1]), '%s PRIVATE LANE TRACT (HOA)' % ft(tot),
        off=0.0, size=size, textoff=step, witness=False)
    txt = ('LANE SECTION AT STA. %d+%02d — ' % (int(station(u)) // 100, int(station(u)) % 100)
           + ' + '.join('%s %s' % (ft(x[1] - x[0]), names[x[2]]) for x in sec if (x[1] - x[0]) > 1.0)
           + ' IN A %s HOA TRACT' % ft(tot))
    cv = cl_v(u)
    c.text(u + 34.0 * side, cv + (4.5 if side > 0 else -8.5), txt, size=size,
           anchor=('start' if side > 0 else 'end'), fill=DIMC, halo=True)


def hydrants_layer(c, u0, u1, labels=True):
    c.add('<g id="water">')
    c.pline([p for p in WATER_MAIN], fill='none', stroke=sb.C['water'], stroke_width=1.1,
            stroke_dasharray='14 4 3 4')
    for tag, u, v, where in HYDRANTS:
        if not (u0 - 30 < u < u1 + 30):
            continue
        c.circle((u, v), 4.6, fill=sb.C['hydrant'], stroke='#fff', stroke_width=1.0)
        c.line((u, v), (u, v + 9.0), stroke=sb.C['hydrant'], stroke_width=0.7)
        if labels and u0 + 70 < u < u1 - 70:
            c.textlines(u, v + 12.0 + (FS / c.s) * 0.4,
                        ['%s  STA. %d+%02d' % (tag, int(station(u)) // 100, int(station(u)) % 100),
                         'PROPOSED FIRE HYDRANT'],
                        size=FS, gap=1.15, bold_first=True, fill=sb.C['hydrant'], halo=True, anchor='middle')
    c.add('</g>')


def matchline(c, v0, v1, other, note=True):
    c.line((U_MATCH, v0), (U_MATCH, v1), stroke=sb.C['match'], stroke_width=3.0,
           stroke_dasharray='26 8 6 8')
    c.text(U_MATCH - 5.0, (v0 + v1) / 2.0 + 40, 'MATCH LINE  u = 980  —  SEE SHEET %s' % other,
           size=FS + 2, rot=-90, bold=True, fill=sb.C['match'], halo=True)
    if note:
        c.text(U_MATCH + 5.0, (v0 + v1) / 2.0 - 60,
               'BLOCK A / BLOCK B AND PHASE 1 / PHASE 2 LINE — ON LOT LINES (CHECKLIST §4.i)',
               size=FS, rot=-90, bold=True, fill=PHC, halo=True)


# ============================================================================ key plan
def key_plan(c, x, y, this_tag, w=340.0):
    ku0, ku1, kv0, kv1 = -70.0, 1780.0, -300.0, 60.0
    ks = w / (ku1 - ku0)
    K = sb.Drawing(ks, x, y, fs=1.0, win=(ku0, ku1, kv0, kv1))
    K.clip_open(fill='#fff')
    K.poly(sb.BOUNDARY, fill='#fbfbf8', stroke='#000', stroke_width=1.2)
    for g in L['greens']:
        for p in g['polygons']:
            K.poly([tuple(q) for q in p], fill=sb.C['green'], stroke='none')
    for p in L['ponds']:
        K.poly([tuple(q) for q in p['polygon']], fill=sb.C['pond'], stroke='none')
    K.poly(CREEK_WOODS, fill='#dfeed6', stroke='none')
    for a in L['amenity']['tract_polygons']:
        K.poly([tuple(q) for q in a], fill='#eef4e6', stroke='none')
    for lot in L['lots']:
        K.poly([tuple(p) for p in lot['polygon']], fill='#fff', stroke='#666', stroke_width=0.35)
    K.poly([tuple(p) for p in LANE['pavement_polygon']], fill='#c9c9c9', stroke='none')
    K.poly([tuple(p) for p in LANE['entry_drive']['pavement_polygon']], fill='#c9c9c9', stroke='none')
    for tag, u0, u1 in (('A', -40.0, U_MATCH), ('B', U_MATCH, 1760.0)):
        K.poly(sb.rect(u0, u1, -280.0, 40.0), fill='#c62828' if tag == this_tag else 'none',
               fill_opacity='0.14' if tag == this_tag else '0',
               stroke=sb.C['match'], stroke_width=1.4, stroke_dasharray='9 3 2 3')
    K.line((U_MATCH, -280.0), (U_MATCH, 40.0), stroke=sb.C['match'], stroke_width=2.0)
    K.clip_close()
    c.add(K.render())
    bx, by, bw, bh = K.box()
    c.srect(bx, by, bw, bh, fill='none', stroke='#000', stroke_width=1.0)
    c.stext(bx, by - 8, 'KEY PLAN — 1" ≈ %d\'  (SHEET C-2.0 COVERS THE WHOLE SITE AT 1" = 60\')'
            % round(72.0 / ks), size=FS, bold=True)
    c.stext(bx, by + bh + 17, 'BLOCK A = SHEET C-2.1   ·   BLOCK B = SHEET C-2.2', size=FS)
    c.stext(bx, by + bh + 33, 'THIS SHEET IS SHADED   ·   MATCH LINE u = 980', size=FS)
    return by + bh + 38


# ============================================================================ legend
LEGEND = [
    ('AB', 'line', sb.C['bnd'], 1.8, '', 'Assemblage boundary — Gwinnett GIS, DRAFT (RLS survey governs)'),
    ('AB', 'line', '#111', 1.1, '', 'Proposed lot line (fee-simple lot)'),
    ('AB', 'line', '#888', 0.8, '5 3', 'Building setback line — 15\' front / 5\' side / 20\' rear'),
    ('AB', 'rect', 'url(#bufhatch)', 0, '', "20'-0\" undisturbed buffer, recorded buffer easement"),
    ('AB', 'line', BUF_LINE, 0.9, '7 3', 'Limit of buffer easement on a lot (§313(1))'),
    ('AB', 'rect', sb.C['house'], 0, '', 'Proposed 1-story cottage — Plan A / Plan B body'),
    ('AB', 'rect', '#efd2ad', 0, '', 'Attached 2-car garage (recessed 5\'-0")'),
    ('AB', 'rect', '#fdf1de', 0, '', 'Covered front porch, rear porch or patio'),
    ('AB', 'rect', '#e3e3e3', 0, '', 'Concrete driveway, 20\'-0" × 26\'-8"'),
    ('A', 'rect', sb.C['pave'], 0, '', 'Asphalt pavement — lane, turnarounds, parking bays'),
    ('B', 'rect', sb.C['pave'], 0, '', 'Asphalt pavement — private lane and turnarounds'),
    ('AB', 'rect', '#fafafa', 0, '', '5\'-0" concrete sidewalk'),
    ('AB', 'line', '#555', 0.9, '9 4', 'Private lane tract line (HOA-owned and maintained)'),
    ('AB', 'line', '#555', 0.8, '18 4 3 4', 'Lane centreline'),
    ('AB', 'rect', sb.C['green'], 0, '', 'Common open space — pocket / terminus green (HOA)'),
    ('A', 'rect', '#eef4e6', 0, '', 'Front amenity tract (HOA)'),
    ('A', 'rect', '#cfe8bd', 0, '', 'Village green'),
    ('A', 'rect', '#f2c58a', 0, '', 'Clubhouse and mail kiosk (CBU)'),
    ('A', 'rect', '#e9e2d0', 0, '', 'Pickleball pad and court'),
    ('A', 'line', '#555', 0.5, '', 'Guest / mail-kiosk parking stall, 9\' × 18\''),
    ('A', 'rect', '#333', 0, '', 'Monument entry sign — see Sheet C-2.3'),
    ('AB', 'rect', sb.C['pond'], 0, '', 'Dry detention / water-quality basin, top of bank'),
    ('AB', 'rect', '#e4efdc', 0, '', 'Basin tract (HOA)'),
    ('B', 'rect', 'url(#woods)', 0, '', 'Creek-woods and stream-setback tracts — preserved'),
    ('B', 'line', '#0d47a1', 0.9, '8 3', 'Drainage / BMP access easement (concept — Sheet C-3.0)'),
    ('AB', 'dot', sb.C['hydrant'], 0, '', 'Proposed fire hydrant'),
    ('AB', 'line', sb.C['water'], 1.1, '14 4 3 4', 'Proposed 8-in water main (see Sheet C-4.0)'),
    ('A', 'line', sb.C['sewer'], 1.0, '', 'Existing 8-in sanitary sewer and manhole'),
    ('A', 'rect', 'url(#ssehatch)', 0, '', "Existing 20' sanitary sewer easement (VERIFY)"),
    ('B', 'line', sb.C['stream'], 1.6, '', 'Stream — state waters, top of bank approximate'),
    ('AB', 'line', sb.C['buf_line'], 0.8, '3 2', "25' state (GA EPD) stream buffer"),
    ('AB', 'line', sb.C['buf_line'], 1.0, '6 2', "50' undisturbed stream buffer (Lilburn)"),
    ('AB', 'line', sb.C['buf_line'], 1.0, '8 2 2 2', "75' impervious setback"),
    ('A', 'line', '#c8791a', 1.0, '12 4', "50' Arcado Rd building setback line (Table 4.1)"),
    ('A', 'line', '#5a8a4a', 0.9, '6 3', "10' landscape strip along the Arcado Rd R/W"),
    ('AB', 'rect', sb.C['adj_fill'], 0, '', 'Adjoining tax parcel — all zoned R-1, City of Lilburn'),
    ('AB', 'line', DIMC, 0.8, '', 'Dimension line and witness line (US survey feet)'),
    ('AB', 'line', sb.C['match'], 3.0, '26 8 6 8', 'Match line = block line = phase line, u = 980'),
]


def legend(c, x, y, tag, w=520.0, rowh=17.6, split=None, gap=500.0):
    c.stext(x, y, 'LEGEND', size=FS_H, bold=True)
    c.stext(x + 76, y, '— every symbol drawn appears below; no unused entry',
            size=FS, fill='#444')
    y0 = y + FS_H + 8
    y = y0
    rows = [e for e in LEGEND if tag in e[0]]
    for k, e in enumerate(rows):
        if split and k == split:
            x += gap
            y = y0
        kind, col, lw, dash, txt = e[1], e[2], e[3], e[4], e[5]
        if kind == 'line':
            c.sline(x, y - 4, x + 50, y - 4, stroke=col, stroke_width=max(lw, 0.9), stroke_dasharray=dash)
        elif kind == 'dot':
            c.scircle(x + 25, y - 4, 5.2, fill=col, stroke='#fff', stroke_width=0.8)
        else:
            c.srect(x, y - 12, 50, 14, fill=col, stroke='#555', stroke_width=0.5)
        c.stext(x + 60, y, txt, size=FS)
        y += rowh
    return y


# ============================================================================ general notes
def note_no(tag, prefix):
    for i, t in enumerate(notes_for(tag), 1):
        if t.startswith(prefix):
            return i
    return 0


def notes_for(tag):
    lots = lots_of(tag)
    nsw = len([x for x in lots if x['side'] == 'SW'])
    nne = len([x for x in lots if x['side'] == 'NE'])
    sec = lane_section(1050.0 if tag == 'B' else 900.0)
    hyd = [h for h in HYDRANTS if (h[1] < U_MATCH) == (tag == 'A')]
    sew = [p for r in sb.CTX['sewer'] if 'ARCADO ROAD TOWNHOMES' in r['project']
           for path in r['paths_local'] for p in path]
    inbuf = sorted(set('%s-%d' % (x['block'], x['block_lot']) for x in L['lots']
                       if any(sb.point_in_poly(tuple(p), [tuple(q) for q in x['buffer_easement']])
                              for p in sew)))
    N = [
        'SCALE AND MATCH LINE. Enlargement of Sheet C-2.0 (1" = 60\') at 1" = 30\' on ARCH D 36 x 24 in, in the '
        'site-local system of Sheet C-0 (+u along the strip to the north-west from the Arcado Rd R/W corner, +v '
        'across toward the north-east line). C-2.1 = BLOCK A / PHASE 1, u -40 to +1,000; C-2.2 = BLOCK B / PHASE 2, '
        'u 960 to 1,760. THE MATCH LINE AT u = 980 IS ALSO THE BLOCK LINE AND THE PHASE LINE AND FALLS ON LOT LINES, '
        'so the work can be platted in blocks (Checklist §4.i). See the key plan.',

        'DIMENSION BASIS. Every dimension is computed at run time from data/layout.json; none is transcribed. US '
        'survey feet, architectural notation, measured to property lines and to the face of the element dimensioned. '
        'CONCEPT information on a Gwinnett County GIS boundary: a boundary survey plat and metes-and-bounds '
        'description sealed by a Georgia RLS (Ord. 2023-603 §1003-4.3, §1003-4.4) are required and GOVERN. Every '
        'statement of conformity reads "appears consistent with".',

        'LOTS AND BLOCKS (Checklist §4.i). %d lots — BLOCK A %d (Phase 1), BLOCK B %d (Phase 2). This sheet shows '
        'BLOCK %s: %d lots, %d south-west and %d north-east. Every lot is %s x %s = %s SF and is dimensioned on the '
        'plan; designations read BLOCK-LOT. Table 4.1 (R-2) requires 3,000 SF, 50 ft width and 100 ft depth for a '
        'cottage home — the layout appears consistent with all three. Density %.2f du/ac deeded (%.2f GIS) against '
        'the 8 du/ac maximum. The use is P in R-2 (§602 Use Table).'
        % (M['lots'], len(lots_of('A')), len(lots_of('B')), tag, len(lots), nsw, nne,
           ft(50.0), ft(100.0), format(5000, ','), M['density_du_ac_deeded'], M['density_du_ac_gis']),

        'SETBACK ENVELOPE (Table 4.1 R-2; Checklist §4.j, §4.k). The dashed envelope on every lot is FRONT %s from '
        'the front lot line (= the lane tract line), SIDE %s, REAR %s. Houses sit inside it with margin: porch face '
        '%s, side yard %s on both plans, rearmost element %s (Plan A patio) / %s (Plan B rear porch). Accessory '
        'buildings and ground equipment keep %s (Checklist §4.l). One lot of each row is dimensioned as TYPICAL; '
        'all lots are identical.'
        % (ft(15.0), ft(5.0), ft(20.0), ft(L['lots'][0]['house']['porch_face_from_lot_line_ft']),
           ft(min(x['house']['side_yard_ft'] for x in L['lots'])),
           ft(L['lots'][0]['house']['rear_element_from_rear_line_ft']),
           ft(L['lots'][1]['house']['rear_element_from_rear_line_ft']), ft(5.0)),

        'PERIMETER BUFFER (Table 4.1; §313(1); Checklist §4.j, §6.b). A %s UNDISTURBED buffer runs the entire '
        'south-west, north-east and north-west lines — every line abutting R-1 — and is dimensioned on the plan. '
        'Table 4.1 gives 0 ft for detached single-family in R-2 and 20 ft for "all other allowed dwelling types"; '
        'cottage homes are listed separately, so the plan is designed to 20 ft. The buffer lies in the rear 20 ft of '
        'each perimeter lot in a RECORDED BUFFER EASEMENT, on the reading that §313(1) lets a buffer supersede and '
        'coincide with the 20-ft rear yard. THIS SINGLE READING CARRIES THE LOT MODULE — CONFIRM IT AT THE '
        'PRE-APPLICATION CONFERENCE. Fallback (buffer in a separate tract, 50\' x 82\' '
        'lots, §1005 variance): Sheet C-2.4.' % ft(L['buffers']['perimeter_buffer_ft']),

        'GARAGES AND DRIVEWAYS (Table 4.2 R-2 "A"; Checklist §4.p, §4.t, §7.i). Front-loaded garages are '
        'RECESSED %s BEHIND THE FRONT WALL as Table 4.2 requires; the porch projects a further 6\'-0". The '
        'garage door stands %s from the front lot line, so the driveway holds two cars clear of the sidewalk. '
        'Driveways are %s x %s, 4-in concrete on min. 4-in compacted GAB (asphalt alternate 2-in GDOT Type E or F on '
        '4-in GAB, §7.i). 2 garage + 2 driveway spaces per dwelling = %d on-lot against Table 8.1\'s 2 per '
        'unit; the sidewalk crosses every apron with curb ramps to PROWAG / 2010 ADA Standards.'
        % (ft(L['lots'][0]['house']['garage_recess_ft']),
           ft(L['lots'][0]['house']['garage_door_from_lot_line_ft']), ft(20.0), ft(26.667), 4 * M['lots']),

        'PRIVATE LANE (§319; Checklist §4.s). One private lane in an HOA tract %s to %s wide serves every lot; '
        'the tract is dimensioned at two stations. Typical section %s. Each lot has %s of frontage against the 30-ft '
        'minimum of §319. Labelled PRIVATE: "all components of private streets and alleys must meet minimum '
        'standards for public street" (§4.s). Pavement 2-in GDOT Type E or F on min. 4-in GAB; section on Sheet '
        'C-8.0. South-west walk from u = %.0f; travelled way %s. The 5-ft sidewalk and the 10-ft Arcado Rd '
        'landscape strip appear in the Checklist only under the Highway 29 Overlay comments (§5.b, §5.g) and are '
        'therefore provided VOLUNTARILY — confirm applicability at the pre-application conference.'
        % (ft(M['lane_tract_width_ft_min']), ft(M['lane_tract_width_ft_max']),
           ' + '.join('%s %s' % (ft(s[1] - s[0]), {'PVMT': 'asphalt', 'WALK': 'walk',
                                                   'STRIP': 'strip'}[s[2]]) for s in sec if (s[1] - s[0]) > 1.0),
           ft(50.0), LANE['sidewalks'][2]['from_u'], ft(M['lane_length_ft'])),

        'FIRE HYDRANTS AND WATER. %d hydrants on a new 8-in DIP main in the lane tract, %d on this sheet at '
        'the stations shown; spacing %s ft against Gwinnett DWR Water and Sewer Standards (April 2016) §2.2.15(b), '
        '"350 feet to an absolute maximum of 450 feet", with "a fire hydrant near the end of each main". Each stands '
        'in a common tract where the lane widens, so IFC 2024 (GA) App. D103.1 (26 ft of width where a hydrant is on '
        'the access road) can be met. Existing hydrant at (u -45, v +41), 61 ft from the front corner — Sheet C-0. '
        'Fire flow 1,000 gpm / 1 hr (App. B Table B105.1(1)), 500 gpm with the voluntary NFPA 13D sprinklers. '
        'Main size, valving and the DWR flow test: Sheet C-4.0.'
        % (len(HYDRANTS), len(hyd),
           ' / '.join('%.0f' % (station(HYDRANTS[i + 1][1]) - station(HYDRANTS[i][1]))
                      for i in range(len(HYDRANTS) - 1))),

        'FIRE APPARATUS ACCESS. The lane is a %s dead end; IFC 2024 (GA) App. D103.4 SPECIAL APPROVAL of a dead end '
        'over 750 ft is requested of the Gwinnett County Fire Marshal. Three %s x %s hammerheads at u = %s, no '
        'interval over %.0f ft, and no circular cul-de-sac (Table 4.2 R-2 "A"). A SECOND ACCESS IS NOT REQUIRED: Ga. '
        'Comp. R. & Regs. 120-3-3-.04 replaces App. D107.1 and sets the trigger at MORE THAN 120 DWELLING UNITS, not '
        'the model code\'s 30; this development has %d. NFPA 13D sprinklers are offered VOLUNTARILY, not as required '
        'mitigation. No on-lane parking; 22\'-0" is kept clear.'
        % (ft(M['longest_dead_end_ft']), ft(20.0), ft(60.0),
           ', '.join('%.0f' % h['u'] for h in L['hammerheads']),
           M['hammerhead_spacing_max_ft'], M['lots']),

        'FINISHED FLOOR ELEVATIONS (Checklist §4.g). FFE IS NOT SET AT THE REZONING STAGE. "EG ±" in each lot is the '
        'EXISTING ground at the centre of the pad (NAVD88), interpolated from the USGS 3DEP 1-m DEM on a 100 x 50-ft '
        'grid — APPROXIMATE, for reference only, NOT a proposed elevation; on this sheet it ranges %.0f to %.0f ft. '
        'Finished floors, proposed contours, pad grading, walls and the lane profile are set by the PE on Sheets '
        'C-3.0 and C-5.0 after a topographic survey. Each dwelling is 1 story, ridge %s (Plan A) / %s (Plan B) above '
        'finished floor against the 40-ft Table 4.1 maximum.'
        % (min(eg_at(sum(p[0] for p in x['polygon']) / 4.0, sum(p[1] for p in x['polygon']) / 4.0) for x in lots),
           max(eg_at(sum(p[0] for p in x['polygon']) / 4.0, sum(p[1] for p in x['polygon']) / 4.0) for x in lots),
           ft(17.83), ft(19.33)),

        'OPEN SPACE AND MAINTENANCE (Checklist §4.o). Every tract other than a numbered lot is common open space or '
        'private street tract, conveyed to and maintained by the HOA; none is offered for public dedication. Common open space %s SF = %.2f ac = %.1f%% of the GIS area / %.1f%% of 9.44 '
        'deeded ac, of which %s SF is built or paved; green-only %s SF = %.1f%%. The %s SF of buffer easement on '
        'lots is reported separately and is NOT counted. Development Regulations §5.9 "Recreation Areas" applies '
        'only at 50 acres or more, so all of this open space is voluntary.'
        % (format(M['open_space_sf'], ','), M['open_space_ac'], M['open_space_pct_gis'],
           M['open_space_pct_deeded'], format(M['open_space_built_paved_sf'], ','),
           format(M['open_space_green_only_sf'], ','), M['open_space_green_only_pct_gis'],
           format(M['buffer_easement_on_lots_sf'], ',')),

        'UTILITIES NOT DRAWN HERE. Storm drainage, sanitary sewer, gas, electric and telecommunications are on '
        'Sheets C-3.0 and C-4.0. PHASE 1 NEEDS NO SEWER EXTENSION — the existing 8-in Arcado Road Townhomes outfall '
        'crosses the property; the point of connection is the existing manhole at invert 927.13. Phase 2 is a '
        'roughly 178-ft OFF-SITE GRAVITY TIE to the Legends at Parkview 8-in main at invert 919.58. AN IN-TRACT PUMP '
        'STATION, PRIVATE FORCE MAIN, PRIVATE GRAVITY SEWER OR GRINDER SYSTEM IS NOT AVAILABLE: Gwinnett DWR\'s '
        'Standard Policy for Private Developments (rev. 9/2018) allows private facilities "only ... for commercial '
        'properties under single ownership", and WSR-24 §1.3.1(A) allows a county station only where gravity is '
        '"more than 5,000 feet down gradient" against an actual 178 ft. DWR capacity certification required; '
        'Georgia 811 locates (O.C.G.A. §25-9) precede field work.',

        'ADJOINING PROPERTY. Every parcel adjoining this sheet is zoned R-1, City of Lilburn, in single-family use — '
        'King David Manor (plat S/159) north-east, Legends at Parkview (plat 118/187) south-west, Nantucket at the '
        'north-west end. PINs, addresses, owners and zoning for all 31 adjoining parcels and the county '
        'right-of-way are labelled on Sheet C-0 and are not repeated here, so the lot dimensions stay legible.',

        'STATUS, SIGNS AND MAIL. DRAFT — NOT SEALED. Concept information prepared by the owner for a rezoning '
        'application under Ord. 2023-603 §1003; not a survey, not a construction document, not a plat. SIGNS: the only sign proposed is one ground-mounted monument entry sign at the Arcado Rd '
        'entrance, face not over 32 SF and height not over 6\'-0" above grade (VERIFY against the Lilburn sign '
        'regulations); NO WALL SIGNS ARE PROPOSED on any dwelling, the clubhouse or any accessory structure. ALL '
        'SIGNS SHALL BE PERMITTED SEPARATELY (§4.q). MAIL: cluster box units at the amenity tract; contact the '
        'Lilburn Post Office Growth Manager (§4.r).',
    ]
    if tag == 'A':
        N.insert(9, 'EXISTING SANITARY SEWER IN THE BUFFER EASEMENT. The existing 8-in Arcado Road Townhomes outfall '
                    'and its 20-ft easement run inside the south-west line from u = -42 to the existing manhole at '
                    '(u 272, v -224), so they fall within the rear buffer easement of LOT%s %s. The buffer stays '
                    'undisturbed except for the existing sewer, which pre-dates it; Checklist §6.f allows sanitary '
                    'sewer conveyance to encroach a buffer "as near perpendicular as possible, up to max 50\' '
                    'width", and this run is parallel — CONFIRM the reading at the pre-application conference. The '
                    '20-ft width is from the 2025 hydrology sheet, NOT a surveyed plat dimension; confirm width and '
                    'holder by title examination. Inverts elsewhere in this set are unsurveyed DWR GIS attributes.'
                    % ('' if len(inbuf) == 1 else 'S', ' AND '.join(inbuf) or 'A-1'))
        N.insert(10, 'FRONT AMENITY TRACT AND ENTRANCE. The clubhouse, village green, two pickleball courts, guest '
                     'and mail-kiosk parking, the monument entry sign, the 10-ft landscape strip and the 50-ft '
                     'Arcado Rd building setback line are shown for continuity and are drawn and dimensioned at '
                     '1" = 20\' on Sheet C-2.3, which also carries the entrance geometry, the intersection sight '
                     'distance and sight triangles, and the south-west curb return\'s encroachment into the 20-ft '
                     'buffer — a buffer reduction the Letter of Intent requests expressly. No lot fronts Arcado Rd '
                     'and no lot has direct access to it.')
    else:
        N.insert(4, 'STREAM AND STREAM BUFFERS (Checklist §9, Buffered State Waters (b)-(g)). An unnamed order-0 headwater of Jackson Creek '
                    '(GAR030701030315; Georgia 2024 §303(d) list) reaches about 30 ft inside the south-west line and '
                    'ends at (u 1,392, v -210); two more branches run outside it. TOP OF BANK IS APPROXIMATE — the '
                    'state waters must be field located and that delineation governs. Buffers are dimensioned and labelled at 25 ft '
                    '(GA EPD, O.C.G.A. §12-7-6(b)(15)), 50 ft (undisturbed, Lilburn Code Ch. 109 Art. VII) and '
                    '75 ft (impervious setback) from top of bank (§9, BSW (d)). REQUIRED NOTES (§9, BSW (e) and (f)): STREAM BUFFERS ARE TO REMAIN IN A NATURAL AND UNDISTURBED CONDITION. STREAM BUFFER SHALL '
                    'BE STAKED AND PROTECTED PRIOR TO LAND DISTURBANCE. No lot, dwelling, driveway, basin or pavement '
                    'is proposed within the 75-ft setback; the pocket between the buffers and the lane is the '
                    'preserved CREEK-WOODS TRACT. No stream-buffer variance is requested (§9, BSW (g)).')
        N.insert(5, 'POND 2 — DRY DETENTION / WATER QUALITY. Concept basin, top of bank %s x %s, 6-ft depth, 3:1 '
                    'slopes, about %s cf. The two basins provide %s cf against %s cf required at the Gwinnett County '
                    'Stormwater Management Manual rate of 10,000 cf per disturbed acre on %.2f disturbed acres '
                    '(RRv zero at concept). WQv = %s cf at %.1f%% impervious. The top of bank stands '
                    '%.1f ft from the south-west line — %.1f ft clear of the 20-ft buffer — and %.0f ft from the '
                    'nearest stream reach, outside the 75-ft setback. The 10-ft drainage easement and the 30-ft BMP '
                    'access easement with its 15-ft road at <= 20%% are CONCEPT, to be set outside the 100-year '
                    'ponding limit by the PE on Sheet C-3.0 with forebay, outlet structure, spillway and the note '
                    'ACCESS EASEMENT TO BE CLEARED AND GRUBBED. Ashlar (ARE) soils map gneiss bedrock at 22-40 in '
                    'here: rock probes and an undercut allowance are required before the hydrology is trusted.'
                    % (ft(P2_V1 - P2_V0), ft(P2_U1 - P2_U0), format(L['ponds'][1]['est_storage_cf'], ','),
                       format(M['detention_provided_cf'], ','), format(M['detention_required_cf'], ','),
                       M['disturbed_area']['disturbed_ac'], format(M['wqv_cf'], ','), M['impervious_pct_gis'],
                       min(abs(p[1] - sb.SW(p[0])) for p in P2),
                       min(abs(p[1] - sb.SW(p[0])) for p in P2) - 20.0,
                       min(dist_to_streams(p) for p in P2)))
    return N


def flow_notes(c, boxes, title, notes, size=FS, lead=15.2, gap=6.0):
    """Flow numbered notes down `boxes` = [(x, y, w, h), ...], line by line, so no column
    ends short.  A note may continue in the next column; continuation lines are indented.
    Returns the number of lines that did not fit anywhere (0 on a good sheet)."""
    w0 = min(b[2] for b in boxes)
    chars = max(int(w0 / (0.56 * size)), 10)
    lines = []
    for i, t in enumerate(notes, 1):
        ls = sb.wrap('%d.  %s' % (i, t), chars)
        lines += [(j > 0, ln) for j, ln in enumerate(ls)]
        lines.append((False, None))                      # blank spacer between notes
    bi = 0
    x, y, w, h = boxes[0]
    ybot = y + h
    c.stext(x, y, title, size=FS_H, bold=True)
    y += FS_H + 8
    over = 0
    for ind, ln in lines:
        if ln is None:
            y += gap
            continue
        if y > ybot:
            if bi + 1 < len(boxes):
                bi += 1
                x, y, w, h = boxes[bi]
                ybot = y + h
                c.stext(x, y, title + '  (CONT.)', size=FS_H, bold=True)
                y += FS_H + 8
            else:
                over += 1
                continue
        c.stext(x + (15 if ind else 0), y, ln, size=size)
        y += lead
    return over


# ============================================================================ keyed-lot dimensions
def front_v(x):
    vs = [p[1] for p in x['polygon']]
    return max(vs) if x['side'] == 'SW' else min(vs)


def rear_v(x):
    vs = [p[1] for p in x['polygon']]
    return min(vs) if x['side'] == 'SW' else max(vs)


def fdir(x):
    return 1.0 if x['side'] == 'SW' else -1.0


def extreme(poly, x):
    vs = [p[1] for p in poly]
    return max(vs) if x['side'] == 'SW' else min(vs)


def typ_tag(c, x, text):
    """A TYPICAL-lot tag written inside the 20-ft buffer band behind the keyed lot."""
    u = sum(p[0] for p in x['polygon']) / 4.0
    v = (sb.SW(u) + 10.0) if x['side'] == 'SW' else (sb.NE(u) - 10.0)
    c.text(u, v, text, size=FS, bold=True, fill=DIMC, halo=True)


def key_lot_setbacks(c, x, nn):
    """Dimension the 15 / 5 / 20 setback envelope on one typical lot of the row."""
    poly = [tuple(p) for p in x['polygon']]
    u0 = min(p[0] for p in poly)
    env = [tuple(p) for p in x['setback_envelope']]
    ev = sorted(p[1] for p in env)
    fl, rl = front_v(x), rear_v(x)
    ef = max(ev) if x['side'] == 'SW' else min(ev)
    er = min(ev) if x['side'] == 'SW' else max(ev)
    dimchain(c, [(u0 + 3.0, fl), (u0 + 3.0, ef), (u0 + 3.0, er), (u0 + 3.0, rl)],
             [ft(15.0), ft(abs(ef - er)), ft(20.0)], off=0.0, textoff=(FS / c.s) * 0.36)
    vmid = fl - fdir(x) * 7.6
    eu = sorted(p[0] for p in env)
    dimchain(c, [(u0, vmid), (min(eu), vmid), (max(eu), vmid), (u0 + 50.0, vmid)],
             [ft(5.0), ft(max(eu) - min(eu)), ft(5.0)], off=0.0, textoff=(FS / c.s) * 0.36)
    typ_tag(c, x, 'TYPICAL LOT — SETBACK ENVELOPE DIMENSIONED 15 / 5 / 20 (NOTE %d)' % nn)


def key_lot_drive(c, x, nn):
    """Dimension the driveway, the garage-door setback and the 5'-0" garage recess."""
    poly = [tuple(p) for p in x['polygon']]
    u0 = min(p[0] for p in poly)
    h = x['house']
    fl = front_v(x)
    gv = extreme([tuple(p) for p in h['garage_rect']], x)
    bv = extreme([tuple(p) for p in h['body_polygon']], x)
    dw = [tuple(p) for p in x['driveway_rect']]
    du0, du1 = min(p[0] for p in dw), max(p[0] for p in dw)
    dim(c, (du0, gv), (du1, gv), ft(du1 - du0), off=fdir(x) * 3.0,
        textoff=(FS / c.s) * (0.38 if x['side'] == 'SW' else -1.05))
    dim(c, (du0 + 10.0, fl), (du0 + 10.0, gv), ft(abs(fl - gv)), off=0.0, textoff=(FS / c.s) * 0.36)
    dim(c, (u0 + 3.0, gv), (u0 + 3.0, bv), ft(abs(gv - bv)), off=0.0, textoff=(FS / c.s) * 0.36)
    typ_tag(c, x, 'TYPICAL LOT — DRIVEWAY %s × %s TO THE GARAGE DOOR, GARAGE RECESS %s (NOTE %d)'
            % (ft(du1 - du0), ft(abs(fl - gv)), ft(abs(gv - bv)), nn))


# ============================================================================ sheets
SHEETS = {
    'A': dict(no='C-2.1', title='MASTER CONCEPT PLAN — ENLARGEMENT, BLOCK A',
              win=(-40.0, 1000.0, -258.0, 24.0), x0=48.0, other='C-2.2',
              sub='Lot-level enlargement of Sheet C-2.0 — Block A / Phase 1, u −40 to +1,000 · every lot, setback '
                  'envelope, buffer easement, driveway, garage recess, lane tract and hydrants dimensioned',
              key_sw=5, key_ne=20,
              buf=((300.0, 'SW'), (660.0, 'SW'), (930.0, 'SW'), (450.0, 'NE'), (760.0, 'NE'), (930.0, 'NE')),
              sect=(300.0, 900.0)),
    'B': dict(no='C-2.2', title='MASTER CONCEPT PLAN — ENLARGEMENT, BLOCK B',
              win=(960.0, 1760.0, -292.0, 24.0), x0=48.0, other='C-2.1',
              sub='Lot-level enlargement of Sheet C-2.0 — Block B / Phase 2, u 960 to the north-west end · lots, '
                  'creek-woods tract, stream buffers, Pond 2 and its easements, terminus green and hammerhead',
              key_sw=3, key_ne=9,
              buf=((1010.0, 'SW'), (1200.0, 'SW'), (1560.0, 'SW'), (1060.0, 'NE'), (1300.0, 'NE'), (1600.0, 'NE')),
              sect=(1050.0, 1620.0)),
}


def build(tag):
    S = SHEETS[tag]
    u0, u1, v0, v1 = S['win']
    lots = lots_of(tag)
    D, F = sb.sheet(S['title'], S['no'], S['sub'], 'Scale 1" = 30\' (ARCH D 36 × 24 in)',
                    status_lines=['Concept lot layout for a rezoning application. Lot lines, setbacks,',
                                  'buffers, basins and easements are DRAFT. A sealed Georgia RLS boundary',
                                  'survey, PE civil design and a registered landscape architect\'s buffer',
                                  'and landscape plan are required and govern. Not a plat, not a survey.'],
                    generator='tools/sitebase.py + tools/enlargements.py',
                    win=S['win'], scale=SCALE, x0=S['x0'], y0=52.0)
    px, py, pw, ph = F['plan']
    strip = py + ph + 6

    # the sitebase overlays are re-pointed: no watermark inside the plan window (audit D-?), and a
    # north arrow and graphic scale lettered to the 1/8-in minimum, below the plan.
    D.late[1] = (lambda: None)
    D.late[2] = (lambda: north(D, px + pw - 104, strip + 30, r=26) if tag == 'A'
                 else north(D, 2274, 762, r=26))
    D.late[3] = (lambda: gscale(D, px + 16, strip + 40))

    # ---------------------------------------------------------------- plan
    D.clip_open(fill='#fff')
    sb.adjoiners(D, labels=False, zoning=False)
    sb.arcado_row(D, labels=False)
    for x in lots_in(u0, u1):
        D.poly([tuple(p) for p in x['polygon']], fill='#fff', stroke='#111', stroke_width=1.1)
    for g in L['greens']:
        for p in g['polygons']:
            D.poly([tuple(q) for q in p], fill=sb.C['green'], stroke=sb.C['green_line'], stroke_width=0.7)
    if tag == 'B':
        for t in (CREEK_WOODS, STREAM_TRACT):
            D.poly(t, fill='url(#woods)', stroke=sb.C['green_line'], stroke_width=1.0)
    for p in L['ponds']:
        D.poly([tuple(q) for q in p['tract_polygon']], fill='#e4efdc', stroke=sb.C['green_line'], stroke_width=0.7)
        D.poly([tuple(q) for q in p['polygon']], fill=sb.C['pond'], stroke=sb.C['buf_line'],
               stroke_width=1.1, stroke_dasharray='7 3')
    if tag == 'A':
        sb.amenity(D, labels=False)
        D.pline([tuple(p) for p in L['buffers']['arcado_setback_line']], fill='none', stroke='#c8791a',
                stroke_width=1.1, stroke_dasharray='12 4')
        D.poly([tuple(p) for p in L['buffers']['landscape_strip']], fill='none', stroke='#5a8a4a',
               stroke_width=1.0, stroke_dasharray='6 3')
    else:
        D.poly(DRAIN_ESMT, fill='none', stroke='#0d47a1', stroke_width=1.0, stroke_dasharray='8 3')
        D.poly(BMP_ESMT, fill='none', stroke='#0d47a1', stroke_width=1.0, stroke_dasharray='8 3')
        D.poly(BMP_ROAD, fill=sb.C['pave'], stroke='#333', stroke_width=0.7)
    buffers_layer(D, labels=False)
    lane_layer(D)
    lots_layer(D, lots_in(u0, u1), labels=True, dim_lots=True)
    sb.streams_and_buffers(D, labels=False)
    if tag == 'A':
        sb.sewer_existing(D, labels=False)
    hydrants_layer(D, u0, u1)
    sb.boundary(D, bearings=False, label=False)

    # ---- dimensions -------------------------------------------------------------------
    lot_width_chains(D, u0, u1)
    buffers_layer(D, labels=True, at=S['buf'])
    for k, u in enumerate(S['sect']):
        lane_section_dim(D, u, side=1 if k == 0 else -1)
    ksw = [x for x in lots if x['side'] == 'SW' and x['block_lot'] == S['key_sw']]
    kne = [x for x in lots if x['side'] == 'NE' and x['block_lot'] == S['key_ne']]
    if ksw:
        key_lot_setbacks(D, ksw[0], note_no(tag, 'SETBACK ENVELOPE'))
    if kne:
        key_lot_drive(D, kne[0], note_no(tag, 'GARAGES AND DRIVEWAYS'))

    # ---- hammerheads, basins, tract callouts ------------------------------------------
    for h in L['hammerheads']:
        if not (u0 + 20 < h['u'] < u1 - 20):
            continue
        leg = [tuple(p) for p in h['legs'][0]]
        lu0, lu1 = min(p[0] for p in leg), max(p[0] for p in leg)
        lv0, lv1 = min(p[1] for p in leg), max(p[1] for p in leg)
        dim(D, (lu0, lv0), (lu1, lv0), ft(h['width_ft']), off=-3.0, textoff=-(FS / D.s) * 1.05)
        dim(D, (lu1, lv0), (lu1, lv1), ft(h['leg_ft']), off=0.0, textoff=(FS / D.s) * 0.36)
        far = h['u'] + 330.0 > u1
        D.textlines(h['u'] + (-30.0 if far else 30.0), lv0 + (-22.0 if far else 8.0),
                    ['HAMMERHEAD TURNAROUND %s × %s' % (ft(h['width_ft']), ft(h['leg_ft'])),
                     'STA. %d+%02d — IFC 2024 (GA) APP. D103.4' % (int(station(h['u'])) // 100,
                                                                   int(station(h['u'])) % 100),
                     'NO CIRCULAR CUL-DE-SAC (TABLE 4.2 R-2 "A")'],
                    size=FS, gap=1.16, bold_first=True, fill=DIMC, halo=True,
                    anchor='end' if far else 'start')
    for i, p in enumerate(L['ponds'], 1):
        q = [tuple(x) for x in p['polygon']]
        cu = sum(x[0] for x in q) / 4.0
        if not (u0 + 20 < cu < u1 - 20):
            continue
        lng, wid = sb.dist(q[0], q[1]), sb.dist(q[1], q[2])
        dim(D, q[3], q[2], ft(lng), off=4.0, textoff=(FS / D.s) * 0.38)
        dim(D, q[1], q[2], ft(wid), off=-5.0, textoff=(FS / D.s) * 0.36)
        D.textlines(cu, sum(x[1] for x in q) / 4.0 + 6.0,
                    ['POND %d — DRY DETENTION / WATER QUALITY' % i,
                     'TOP OF BANK %s × %s, 6 ft DEEP, 3:1 SLOPES' % (ft(wid), ft(lng)),
                     '≈%s cf PROVIDED — CONCEPT, SEE SHEET C-3.0' % format(p['est_storage_cf'], ',')],
                    size=FS, gap=1.16, bold_first=True, fill='#0d47a1', halo=True)

    # ---- sheet-specific annotation ----------------------------------------------------
    if tag == 'A':
        A = L['amenity']
        D.textlines(6.0, -4.0, ['FRONT AMENITY TRACT — %s SF (HOA): CLUBHOUSE %s SF (%s × %s),'
                                % (format(A['tract_sf'], ','), format(A['clubhouse_sf'], ','), ft(40.0), ft(60.0)),
                                'VILLAGE GREEN, 2 PICKLEBALL COURTS, GUEST AND MAIL-KIOSK PARKING,',
                                'MONUMENT ENTRY SIGN — ALL DIMENSIONED ON SHEET C-2.3 AT 1" = 20\''],
                    size=FS, gap=1.20, bold_first=True, fill='#2e5e1e', halo=True, anchor='start')
        D.text(10.0, -226.0, "EXISTING 8-in SANITARY SEWER IN A 20' EASEMENT — SEE NOTE %d"
               % note_no(tag, 'EXISTING SANITARY SEWER'), size=FS,
               anchor='start', fill=sb.C['sewer_txt'], halo=True)
        D.textlines(700.0, -244.0, ["50' AND 75' BUFFERS OF THE OFF-SITE STREAM BRANCH — THE BRANCH ITSELF LIES",
                                    'BEYOND THIS ENLARGEMENT; SEE SHEETS C-0 AND C-2.2'],
                    size=FS, gap=1.20, fill=sb.C['buf_line'], halo=True, anchor='start')
        D.text(30.0, -140.0, "50'-0\" ARCADO RD BUILDING SETBACK (TABLE 4.1)", size=FS, rot=-81,
               fill='#c8791a', halo=True)
        D.text(14.0, -150.0, "10'-0\" LANDSCAPE STRIP ALONG THE ARCADO RD R/W (VOLUNTARY)", size=FS,
               rot=-81, fill='#5a8a4a', halo=True)
    else:
        D.textlines(1284.0, -206.0, ['CREEK-WOODS TRACT — PRESERVED COMMON OPEN SPACE',
                                     '%s SF · STREAM HEAD AND ITS 50 / 75-ft BUFFERS' % format(20000, ','),
                                     'NO LOT, DWELLING, DRIVE, BASIN OR PAVEMENT PROPOSED'],
                    size=FS, gap=1.20, bold_first=True, fill='#2e5e1e', halo=True, anchor='start')
        D.textlines(1255.0, -146.0, ['STREAM-SETBACK', 'TRACT — %s SF' % format(5000, ','),
                                     'NO IMPERVIOUS'],
                    size=FS, gap=1.20, bold_first=True, fill='#2e5e1e', halo=True, anchor='middle')
        D.textlines(1236.0, -244.0, ['UNNAMED STREAM (STATE WATERS) — ORDER-0 HEADWATER OF',
                                     'JACKSON CREEK, GAR030701030315.  TOP OF BANK APPROXIMATE —',
                                     'FIELD DELINEATION REQUIRED (CHECKLIST §9, BSW (b), (c)).',
                                     'STREAM BUFFERS ARE TO REMAIN IN A NATURAL AND UNDISTURBED',
                                     'CONDITION.  STREAM BUFFER SHALL BE STAKED AND PROTECTED',
                                     'PRIOR TO LAND DISTURBANCE.'],
                    size=FS, gap=1.20, bold_first=True, fill=sb.C['stream'], halo=True, anchor='start')
        D.textlines(986.0, -250.0, ["25'-0\" STATE (GA EPD) BUFFER",
                                    "50'-0\" UNDISTURBED CITY BUFFER (CH. 109 ART. VII)",
                                    "75'-0\" IMPERVIOUS SETBACK",
                                    'ALL LABELLED ON EVERY SHEET (CHECKLIST §9, BSW (d))'],
                    size=FS, gap=1.20, fill=sb.C['buf_line'], halo=True, anchor='start')
        st = [tuple(p) for p in L['stream_setbacks'][0]['stream']]
        a, b = st[-3], st[-1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        if ny < 0:
            nx, ny = -nx, -ny
        p0 = st[-2]
        dimchain(D, [p0, (p0[0] + nx * 25, p0[1] + ny * 25), (p0[0] + nx * 50, p0[1] + ny * 50),
                     (p0[0] + nx * 75, p0[1] + ny * 75)],
                 [ft(25.0), ft(25.0), ft(25.0)], off=0.0, textoff=(FS / D.s) * 0.36)
        dim(D, p0, (p0[0] + nx * 75, p0[1] + ny * 75),
            ft(75.0),
            off=-15.0, textoff=(FS / D.s) * 0.38, color=sb.C['buf_line'])
        leader(D, (1655.0, P2_V1 + 10.0), (1496.0, -250.0),
               ["10'-0\" DRAINAGE EASEMENT OUTSIDE THE BASIN TOP OF BANK and",
                "30'-0\" BMP ACCESS EASEMENT WITH A 15'-0\" ACCESS ROAD AT ≤ 20%",
                'CONCEPT — TO BE SET OUTSIDE THE 100-YR PONDING LIMIT, SHEET C-3.0',
                'ACCESS EASEMENT TO BE CLEARED AND GRUBBED'],
               anchor='start', bold_first=True, color='#0d47a1')
        D.text(1690.0, -232.0, 'TERMINUS GREEN — %s SF (HOA)' % format(L['greens'][2]['area_sf'], ','),
               size=FS, bold=True, fill='#2e5e1e', halo=True, anchor='middle')
        D.text(1752.0, -150.0, 'ADJOINING: NANTUCKET — ZONED R-1, CITY OF LILBURN', size=FS, rot=-90,
               bold=True, fill='#555', halo=True)

    matchline(D, v0 + 26, v1 - 26, S['other'])
    D.text((u0 + u1) / 2.0, v1 - 6.0,
           'ADJOINING: KING DAVID MANOR (PLAT S/159) — ALL LOTS ZONED R-1, CITY OF LILBURN, SINGLE-FAMILY '
           '(PIN, OWNER AND ZONING ON SHEET C-0)', size=FS, bold=True, fill='#555', halo=True)
    D.text((u0 + u1) / 2.0, v0 + 5.0,
           'ADJOINING: LEGENDS AT PARKVIEW (PLAT 118/187) — ALL LOTS ZONED R-1, CITY OF LILBURN, SINGLE-FAMILY '
           '(PIN, OWNER AND ZONING ON SHEET C-0)', size=FS, bold=True, fill='#555', halo=True)
    D.clip_close()

    # ---------------------------------------------------------------- strip below the plan
    tx = px + 560
    D.stext(tx, strip + 32, 'DRAFT — NOT SEALED — CONCEPT PLAN FOR PRE-APPLICATION REVIEW',
            size=FS + 4, bold=True, fill='#c00')
    D.stext(tx, strip + 54, 'MATCH LINE u = 980 IS ALSO THE BLOCK LINE AND THE PHASE LINE — SEE THE KEY PLAN '
                            'AND SHEET %s' % S['other'], size=FS, fill=sb.C['match'])
    D.stext(tx, strip + 72, 'Every dimension is computed from data/layout.json at run time and is DRAFT — the '
                            'sealed RLS survey and the PE design govern.', size=FS, fill='#444')
    D.stext(tx, strip + 90, 'Lot designations read BLOCK–LOT.  EG ± is EXISTING ground from the USGS 3DEP DEM, '
                            'approximate; FFE is set on Sheet C-3.0.  Boundary and adjoining parcels: Gwinnett '
                            'County GIS parcel fabric.', size=FS, fill='#444')
    if tag == 'A':
        key_plan(D, px + pw - 700, strip + 16, tag)

    # ---------------------------------------------------------------- band
    by0 = strip + 112
    by1 = 1524.0
    bh = by1 - by0
    if tag == 'A':
        legend(D, 1958, by0 + 24, tag, w=580, rowh=17.4)
        boxes = [(56, by0, 618, bh), (694, by0, 618, bh), (1332, by0, 618, bh)]
    else:
        legend(D, 2000, 76, tag, w=546, rowh=17.6)
        key_plan(D, 2000, 606, tag)
        boxes = [(56, by0, 600, bh), (682, by0, 600, bh), (1308, by0, 600, bh), (1934, by0, 600, bh)]
    over = flow_notes(D, boxes, 'GENERAL NOTES — SHEET %s' % S['no'], notes_for(tag),
                      lead=14.6, gap=5.5)
    return D, over


# ============================================================================ self-check / main
def _report():
    print('enlargements.py — Sheets C-2.1 / C-2.2 —', DATE)
    print('  layout    : %d lots (Block A %d, Block B %d); match = block = phase line at u = %.0f'
          % (M['lots'], len(lots_of('A')), len(lots_of('B')), U_MATCH))
    for u in (300.0, 900.0, 1050.0, 1620.0):
        sec = lane_section(u)
        print('  lane u=%-6.0f %s = %s'
              % (u, ' + '.join('%s %s' % (ft(s[1] - s[0]), s[2]) for s in sec), ft(sec[-1][1] - sec[0][0])))
    for t, u, v, w in HYDRANTS:
        print('  hydrant   : %s at u=%.0f (sta %d+%02d) in the %s — %.0f ft to the nearest stream reach'
              % (t, u, int(station(u)) // 100, int(station(u)) % 100, w, dist_to_streams((u, v))))
    print('  spacing   : %s ft (Gwinnett DWR 2016 §2.2.15(b): 350 min / 400 typical / 450 max)'
          % ', '.join('%.0f' % (station(HYDRANTS[i + 1][1]) - station(HYDRANTS[i][1]))
                      for i in range(len(HYDRANTS) - 1)))
    print('  pond 2    : top of bank %.1f ft from the SW line (20-ft buffer clear by %.1f ft), %.0f ft to the stream'
          % (min(abs(p[1] - sb.SW(p[0])) for p in P2), min(abs(p[1] - sb.SW(p[0])) for p in P2) - 20.0,
             min(dist_to_streams(p) for p in P2)))
    print('  tracts    : creek woods %s SF, stream-setback tract %s SF'
          % (format(round(abs(sb.poly_area(CREEK_WOODS))), ','),
             format(round(abs(sb.poly_area(STREAM_TRACT))), ',')))
    sew = [p for r in sb.CTX['sewer'] if 'ARCADO ROAD TOWNHOMES' in r['project']
           for path in r['paths_local'] for p in path]
    inb = sorted(set('%s-%d' % (x['block'], x['block_lot']) for x in L['lots']
                     if any(sb.point_in_poly(tuple(p), [tuple(q) for q in x['buffer_easement']]) for p in sew)))
    print('  ex. sewer : inside the buffer easement of lot(s) %s' % (', '.join(inb) or 'none'))


if __name__ == '__main__':
    _report()
    for tag in ('A', 'B'):
        D, over = build(tag)
        svg, png = sb.save(D, 'mcp-enlargement-%s' % tag.lower(), dpi=150)
        print('  wrote %s' % svg)
        print('        %s   (general-note overflow: %d lines)' % (png, over))
