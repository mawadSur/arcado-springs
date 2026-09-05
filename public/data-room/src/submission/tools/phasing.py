#!/usr/bin/env python3
"""Sheet C-6.0 "PHASING, BLOCK AND OPEN SPACE EXHIBIT" — The Cottages at Arcado Springs.

    python3 tools/phasing.py     ->  drawings/phasing-openspace.svg + .png

ARCH D 36 x 24 in at 1" = 60', drawn by tools/sitebase.py in the same site-local (u, v)
system, at the same scale and off the same origin as Sheets C-0, C-2.0 and C-4.0.  Every
number on the sheet is read from data/layout.json (and data/plans.json for the two plan
names) at run time; nothing is transcribed.

WHY THIS SHEET EXISTS
`docs/03-letter-of-intent.md` offers voluntary condition 15 (phasing) and condition 16
(sanitary sewer) and cites THIS SHEET BY NUMBER for the phase line, so the filed set must
carry it.  The governing clause is the City of Lilburn Site Development Plan Review Checklist
section 4.i — "Subdivision — add number of lots/units by type, calculated site density, Unit
Numbers, Lot and Block Numbers if applicable.  **Phasing is not permitted unless platted in
Blocks.**" — with section 4.o, which requires the maintenance responsibility of every
dedicated or common area to be noted.  The 2026-09-03 drawing audit records both as open
defects (D-02: the old phase line at u = 1,000 bisected two lots and no Blocks were platted).

WHAT THE SHEET SETTLES
  * Block A (Phase 1) and Block B (Phase 2), their boundaries drawn ONLY on lot lines and
    tract lines, with the phase line called out at its station along the travelled way and at
    its local u station, and the lot count of each phase on the plan and in the schedules.
  * A lot schedule by block and phase — block-lot number, the Sheet C-2.0 lot number, side,
    station, area, width, depth and plan type.
  * An open-space tract table: every common tract with its area, its percentage of the GIS
    area AND of the deeded 9.44 ac, WHAT THE TRACT ACTUALLY CONTAINS (the built and paved area
    inside the amenity tract stated in plain figures rather than left for staff to find), its
    phase and its maintenance.
  * The 20-ft buffer easement held inside private lots reported SEPARATELY and never added
    into the common-tract total.
  * Maintenance responsibility — homeowners association versus public — for every tract, every
    easement and the right-of-way.

Dwelling footprints, driveways, setback envelopes, contours and boundary bearings are NOT
repeated here; they are on Sheets C-1.0, C-2.0, C-2.1, C-2.2 and C-3.0.  Omitting them is what
lets the block, phase and tract lines read at this scale.

DRAFT — NOT SEALED.  Not a plat.  A Georgia RLS must prepare the boundary survey, the block
and lot platting and every easement description; a Georgia PE the utility and stormwater
design.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitebase as sb                                      # noqa: E402

L = sb.LAYOUT
M = L['metrics']
GIS_SF = sb.BOUNDARY_SF                                    # 417,174 sf  (9.577 ac)
DEEDED_AC = M['acreage_deeded_ac']
DEEDED_SF = DEEDED_AC * 43560.0                            # 411,206 sf  (9.44 ac)
PLANS = json.load(open(os.path.join(sb.DATA, 'plans.json')))['plans']

# --------------------------------------------------------------------------- sheet geometry
# The plan window keeps the u-range, the scale, the origin and the plan-window position of
# Sheets C-0 / C-2.0, so those sheets still overlay this one.  It is cropped ACROSS the strip
# (v -440 to +40 instead of -430 to +240): this exhibit needs the schedules more than it needs
# the King David Manor lot labels, and the schedules have to be lettered at 1/8-in cap height.
WIN = (-150.0, 1840.0, -440.0, 40.0)
PLAN_H = (WIN[3] - WIN[2]) * sb.SCALE60                    # 576 pt
BAND_Y0 = sb.PLAN_Y0 + PLAN_H + 28                         # 656 pt
BAND_Y1 = sb.BAND_Y1                                       # 1530 pt

# House rule: minimum lettering 1/8 in (0.125 in) cap height at full size.  Liberation Sans /
# Arial cap height is 0.716 em, so 0.125 in x 72 pt/in / 0.716 = 12.57 pt is the smallest font
# size allowed on this sheet.  TXT is used for every table cell, note and legend entry, and
# nothing on the sheet is set smaller; plan labels and titles are larger.
TXT = 12.6
LEAD = 15.6
CAP_IN = TXT * 0.716 / 72.0

# --------------------------------------------------------------------------- palette
CA, CB = '#b26a00', '#5e35b1'                              # Block A / Block B
FILL_A, FILL_B = '#fdefd8', '#ece4f7'                      # Phase 1 / Phase 2 lot tint
C_OS, C_OSLINE = '#dff0d8', '#4a7c3a'                      # common open-space tract
C_BUILT = '#f2c58a'                                        # clubhouse / court pads / kiosk
C_GREEN = '#cfe8bd'                                        # village green


# --------------------------------------------------------------------------- small geometry
def clip_convex(subject, clipper):
    """Sutherland-Hodgman clip of `subject` by the CONVEX polygon `clipper`."""
    out = [tuple(p) for p in subject]
    cl = [tuple(p) for p in clipper]
    if sb.poly_area(cl) < 0:
        cl = cl[::-1]
    for i in range(len(cl)):
        a, b = cl[i], cl[(i + 1) % len(cl)]
        ex, ey = b[0] - a[0], b[1] - a[1]

        def inside(p):
            return ex * (p[1] - a[1]) - ey * (p[0] - a[0]) >= 0

        src, out = out, []
        for k in range(len(src)):
            p, q = src[k], src[(k + 1) % len(src)]
            ip, iq = inside(p), inside(q)
            if ip:
                out.append(p)
            if ip != iq:
                dx, dy = q[0] - p[0], q[1] - p[1]
                den = ex * dy - ey * dx
                if abs(den) > 1e-12:
                    t = (ex * (p[1] - a[1]) - ey * (p[0] - a[0])) / den
                    out.append((p[0] - t * dx, p[1] - t * dy))
        if not out:
            return []
    return out


def clip_area(subject, clipper):
    p = clip_convex(subject, clipper)
    return abs(sb.poly_area(p)) if len(p) > 2 else 0.0


def clip_halfplane(poly, u_cut, keep_low=True):
    """The part of a polygon on one side of the line u = u_cut — the phase gross areas."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        ip = (p[0] <= u_cut) if keep_low else (p[0] >= u_cut)
        iq = (q[0] <= u_cut) if keep_low else (q[0] >= u_cut)
        if ip:
            out.append(p)
        if ip != iq and abs(q[0] - p[0]) > 1e-12:
            t = (u_cut - p[0]) / (q[0] - p[0])
            out.append((u_cut, p[1] + t * (q[1] - p[1])))
    return out


def sw_band(a, b):
    """The 100-ft-deep lot band on the SW side between stations a and b — the geometry the two
    unlotted tracts (creek woods, stream setback) occupy (tools/siteplan.py `sw_tract`)."""
    return [(a, sb.SW(a)), (b, sb.SW(b)), (b, sb.SW(b) + 100.0), (a, sb.SW(a) + 100.0)]


def arclen(path, u0=-1e9, u1=1e9):
    s = 0.0
    for p, q in zip(path, path[1:]):
        if q[0] <= u0 or p[0] >= u1:
            continue
        s += math.hypot(q[0] - p[0], q[1] - p[1])
    return s


def sta(ft):
    return '%d+%05.2f' % (int(ft // 100), ft % 100)


def sf(x):
    return format(int(round(x)), ',')


# --------------------------------------------------------------------------- blocks and lots
LOTS = L['lots']
PHASE_U = float(L['phase_line_u'])
BLOCKS = sorted({l['block'] for l in LOTS})
PHASE_OF_BLOCK = {b: min(l['phase'] for l in LOTS if l['block'] == b) for b in BLOCKS}
BLOCK_OF_PHASE = {PHASE_OF_BLOCK[b]: b for b in BLOCKS}
BLOCK_LOTS = {b: sorted([l for l in LOTS if l['block'] == b], key=lambda l: l['block_lot']) for b in BLOCKS}
N_PHASE = {p: sum(1 for l in LOTS if l['phase'] == p) for p in sorted({l['phase'] for l in LOTS})}
B1, B2 = BLOCK_OF_PHASE[1], BLOCK_OF_PHASE[2]


def lot_u(l):
    us = [p[0] for p in l['polygon']]
    return min(us), max(us)


def block_runs(block, side):
    """Contiguous runs of lots (same block, same side), so the block boundary can be drawn as a
    heavy line ON LOT LINES and never across a lot."""
    ls = sorted([l for l in LOTS if l['block'] == block and l['side'] == side], key=lambda l: lot_u(l)[0])
    runs, cur = [], []
    for l in ls:
        if cur and abs(lot_u(l)[0] - lot_u(cur[-1])[1]) > 1e-6:
            runs.append(cur)
            cur = []
        cur.append(l)
    if cur:
        runs.append(cur)
    return runs


def run_polygon(run):
    """Outline of a run of lots, taken from the member lots' own corners."""
    u0, u1 = lot_u(run[0])[0], lot_u(run[-1])[1]
    a = sorted([p for p in run[0]['polygon'] if abs(p[0] - u0) < 1e-6], key=lambda p: p[1])
    b = sorted([p for p in run[-1]['polygon'] if abs(p[0] - u1) < 1e-6], key=lambda p: p[1])
    return [tuple(a[0]), tuple(b[0]), tuple(b[1]), tuple(a[1])]


# ---- the phase line, stationed along the travelled way from the Arcado Rd right-of-way
LANE_CL = [tuple(p) for p in L['lane']['centerline']]
ENTRY_CL = [tuple(p) for p in L['lane']['entry_drive']['centerline']]
ENTRY_LEN = arclen(ENTRY_CL)
STA_PHASE = ENTRY_LEN + arclen(LANE_CL, LANE_CL[0][0], PHASE_U)
STA_END = ENTRY_LEN + arclen(LANE_CL)

# ---- what the phase line actually runs between, and how many lots it divides (checked here,
#      not asserted: the count is printed on the sheet)
NE_PAIR = (max([l for l in LOTS if l['side'] == 'NE' and lot_u(l)[1] <= PHASE_U + 1e-6], key=lambda l: lot_u(l)[1]),
           min([l for l in LOTS if l['side'] == 'NE' and lot_u(l)[0] >= PHASE_U - 1e-6], key=lambda l: lot_u(l)[0]))
SW_NEXT = min([l for l in LOTS if l['side'] == 'SW' and lot_u(l)[0] >= PHASE_U - 1e-6], key=lambda l: lot_u(l)[0])
CROSSED = [l for l in LOTS if lot_u(l)[0] < PHASE_U < lot_u(l)[1]]

# ---- gross land area of each phase: the boundary cut at the phase line
GROSS = {1: abs(sb.poly_area(clip_halfplane(sb.BOUNDARY, PHASE_U, True))),
         2: abs(sb.poly_area(clip_halfplane(sb.BOUNDARY, PHASE_U, False)))}

# --------------------------------------------------------------------------- open-space tracts
AM = L['amenity']
HH = L['hammerheads']
GREENS = L['greens']
PONDS = L['ponds']
OS_SUM = L['open_space_summary']
BUILT_BD = OS_SUM['built_or_paved_breakdown_sf']
TRACT_AREA = {t['name']: t['area_sf'] for t in L['open_space_tracts']}


def named(key):
    for n, a in TRACT_AREA.items():
        if key.lower() in n.lower():
            return n, a
    raise KeyError(key)


CLUB_SF = AM['clubhouse_sf']
PAD_SF = sum(abs(sb.poly_area([tuple(q) for q in p])) for p in AM['pickleball'])
KIOSK_SF = abs(sb.poly_area([tuple(q) for q in AM['mail_kiosk']]))
WALKS_SF = BUILT_BD.get('amenity walks (allowance)', 0)
AM_BUILT = CLUB_SF + PAD_SF + KIOSK_SF + WALKS_SF
BAY_SF = (abs(sb.poly_area([tuple(q) for q in AM['parking_bay']]))
          + abs(sb.poly_area([tuple(q) for q in AM['kiosk_bay']])))
N_GUEST = AM['guest_spaces'] + AM['kiosk_spaces']
HH_LEG_SF = abs(sb.poly_area([tuple(p) for p in HH[0]['legs'][0]]))
HH_PER = 2 * HH_LEG_SF                                     # 2,400 sf per turnaround, as published


def _hh_in(polys):
    """How much of the turnaround legs really falls inside the greens.  The published breakdown
    counts the whole leg; the honest figure is quoted in general note 9."""
    return sum(clip_area([tuple(p) for p in leg], [tuple(q) for q in g])
               for h in HH for leg in h['legs'] for g in polys)


def _amenity_split():
    """The published 46,777 sf amenity tract is the tract polygon LESS the entry drive and the
    widened lane tract that cross it.  Measured on a 1-ft raster so the sheet can say so."""
    tract = [tuple(p) for p in AM['tract_polygons'][0]]
    lane = [tuple(p) for p in L['lane']['tract_polygon']]
    entry = [tuple(p) for p in L['lane']['entry_drive']['tract_polygon']]
    us = [p[0] for p in tract]
    vs = [p[1] for p in tract]
    gross = crossed = 0
    u = min(us) + 0.5
    while u < max(us):
        v = min(vs) + 0.5
        while v < max(vs):
            if sb.point_in_poly((u, v), tract):
                gross += 1
                if sb.point_in_poly((u, v), lane) or sb.point_in_poly((u, v), entry):
                    crossed += 1
            v += 1.0
        u += 1.0
    return float(gross), float(crossed)


AM_GROSS, AM_CROSSED = _amenity_split()

TRACTS = [
    {'id': 'A', 'key': 'amenity', 'phase': 1,
     'polys': [[tuple(q) for q in p] for p in AM['tract_polygons']],
     'where': 'Front amenity tract, Arcado Rd frontage to u 230',
     'maint': 'HOA'},
    {'id': 'B', 'key': 'Pocket green (u 530', 'phase': 1,
     'polys': [[tuple(q) for q in p] for p in GREENS[0]['polygons']],
     'where': 'Pocket green, both sides, u 530–580',
     'contains': 'Lawn and plantings. Hammerhead turnaround 1 — %s SF of pavement in two legs.' % sf(HH_PER),
     'maint': 'HOA'},
    {'id': 'C', 'key': 'Pocket green (u 1080', 'phase': 2,
     'polys': [[tuple(q) for q in p] for p in GREENS[1]['polygons']],
     'where': 'Pocket green, both sides, u 1,080–1,130',
     'contains': 'Lawn and plantings. Hammerhead turnaround 2 — %s SF of pavement in two legs.' % sf(HH_PER),
     'maint': 'HOA'},
    {'id': 'D', 'key': 'Terminus green', 'phase': 2,
     'polys': [[tuple(q) for q in p] for p in GREENS[2]['polygons']],
     'where': 'Terminus green + rear buffer, u 1,680–1,722',
     'contains': ('Lawn; rear 20-ft buffer in common ownership. Hammerhead turnaround 3 — %s SF of '
                  'pavement in two legs.' % sf(HH_PER)),
     'maint': 'HOA'},
    {'id': 'E', 'key': 'Pond 1', 'phase': 1,
     'polys': [[tuple(q) for q in PONDS[0]['tract_polygon']]],
     'where': 'Pond 1 tract, SW side, u 780–980',
     'contains': ('Dry detention / water-quality basin, %s SF at top of bank — earthen, NOT impervious. '
                  'Buffer, drainage and BMP access easements inside the tract.' % sf(PONDS[0]['area_sf'])),
     'maint': 'HOA'},
    {'id': 'F', 'key': 'Pond 2', 'phase': 2,
     'polys': [[tuple(q) for q in PONDS[1]['tract_polygon']]],
     'where': 'Pond 2 tract, SW side, u 1,480–1,680',
     'contains': ('Dry detention / water-quality basin, %s SF at top of bank — earthen, NOT impervious. '
                  'Buffer, drainage and BMP access easements inside the tract.' % sf(PONDS[1]['area_sf'])),
     'maint': 'HOA'},
    {'id': 'G', 'key': 'Creek woods', 'phase': 2,
     'polys': [sw_band(1280.0, 1480.0)],
     'where': 'Creek woods, SW side, u 1,280–1,480',
     'contains': ('Stream head, 50-ft undisturbed buffer and 75-ft impervious setback, preserved. '
                  'NOTHING BUILT OR PAVED.'),
     'maint': 'HOA'},
    {'id': 'H', 'key': 'Stream-setback', 'phase': 2,
     'polys': [sw_band(1230.0, 1280.0)],
     'where': 'Stream-setback tract, SW, u 1,230–1,280',
     'contains': ('The one 50 x 100-ft lot slot that fails the 75-ft screen, left unlotted. '
                  'NOTHING BUILT OR PAVED.'),
     'maint': 'HOA'},
]
for t in TRACTS:
    t['name'], t['area'] = named(t['key'])
    t['shoelace'] = sum(abs(sb.poly_area(p)) for p in t['polys'])
    t['built'] = (AM_BUILT if t['id'] == 'A' else (HH_PER if t['id'] in ('B', 'C', 'D') else 0.0))
TRACTS[0]['contains'] = (
    'Clubhouse %s SF + two court pads %s SF + mail kiosk %s SF + walks %s SF = %s SF BUILT OR PAVED, '
    '%.1f%% of the tract. Also the village green, landscape strip and monument sign. The %d guest and '
    'kiosk spaces (%s SF of bays) are NOT in it — note 8.'
    % (sf(CLUB_SF), sf(PAD_SF), sf(KIOSK_SF), sf(WALKS_SF), sf(AM_BUILT),
       100.0 * AM_BUILT / TRACTS[0]['area'], N_GUEST, sf(BAY_SF)))

OS_TOTAL = sum(t['area'] for t in TRACTS)
OS_BUILT = sum(t['built'] for t in TRACTS)
PHASE_OS = {p: sum(t['area'] for t in TRACTS if t['phase'] == p) for p in (1, 2)}
HH_REAL = _hh_in([g for t in TRACTS if t['id'] in ('B', 'C', 'D') for g in t['polys']])
BUF_SF = sum(abs(sb.poly_area([tuple(p) for p in l['buffer_easement']])) for l in LOTS)
PH1_SEWER_FT = arclen([tuple(p) for p in L['sewer']['proposed_phase1_gravity']])
OFFSITE_FT = L['sewer']['extension_offsite_ft']


# --------------------------------------------------------------------------- table rows
LOT_COLS = ['LOT', 'C-2.0', 'SIDE', 'STATION u, ft', 'AREA SF', 'WIDTH', 'DEPTH', 'PLAN']
LOT_W = [46, 42, 44, 106, 60, 56, 62, 34]


def lot_rows(block):
    out = []
    for l in BLOCK_LOTS[block]:
        u0, u1 = lot_u(l)
        out.append(['%s-%d' % (block, l['block_lot']), str(l['id']), l['side'],
                    '%s – %s' % (sf(u0), sf(u1)), sf(l['area_sf']),
                    '%d\'-0"' % round(l['width_ft']), '%d\'-0"' % round(l['depth_ft']), l['plan']])
    return out


def tract_rows():
    rows = []
    for t in TRACTS:
        rows.append([t['id'], t['where'], sf(t['area']),
                     '%.2f%%' % (100.0 * t['area'] / GIS_SF),
                     '%.2f%%' % (100.0 * t['area'] / DEEDED_SF),
                     '%d / %s' % (t['phase'], BLOCK_OF_PHASE[t['phase']]),
                     t['contains'], t['maint']])
    rows.append(['', 'TOTAL — EIGHT TRACTS', sf(OS_TOTAL),
                 '%.1f%%' % OS_SUM['pct_of_gis_area'], '%.1f%%' % OS_SUM['pct_of_deeded_area'], 'BOTH',
                 'Of which %s SF is built or paved (note 8); %s SF, %.1f%% of the GIS area, is green. '
                 'NO open space is required here — note 5.'
                 % (sf(OS_BUILT), sf(OS_SUM['green_only_sf']), OS_SUM['green_only_pct_of_gis_area']),
                 'HOA'])
    return rows


def easement_rows():
    return [
        ['Private lane tract, including the entry drive', '%s SF' % sf(M['lane_tract_sf']), '1 and 2',
         'HOA in fee', 'HOA — pavement, sidewalks, curb, drainage, lighting and street trees. '
         'Private street (§4.s), built to public-street standards.', 'NO'],
        ['20-ft buffer easement on the rear of all %d lots' % len(LOTS), '%s SF' % sf(BUF_SF), '1 and 2',
         'Lot owner in fee, subject to a recorded buffer easement (§313(1))',
         'HOA maintains and enforces it; the owner may not clear, grade, fence or build in it.',
         'NO — separate, note 7'],
        ['Existing 20-ft sanitary sewer easement (Arcado Rd Townhomes outfall)',
         "20' wide, u −42 to 272; width to be confirmed from the recorded plat", 'existing',
         'Gwinnett County (DWR)', 'PUBLIC — DWR maintains the main; HOA mows the surface.', 'NO'],
        ['Phase 1 sanitary sewer easement, on site, to MH inv 927.13',
         "20' wide, ≈ %d ft; area by survey" % round(PH1_SEWER_FT), '1',
         'To be dedicated to Gwinnett County (DWR)',
         'PUBLIC — DWR maintains the main after acceptance; HOA the surface.', 'NO'],
        ['Phase 2 sanitary sewer easement, off site, to the Legends at Parkview main (MH inv 919.58)',
         "20' wide, ≈ %.0f ft of it OFF SITE; to be acquired" % OFFSITE_FT, '2',
         'To be dedicated to Gwinnett County (DWR)',
         'PUBLIC — DWR maintains the main. MUST BE RECORDED BEFORE ANY PHASE 2 WORK '
         '(condition 16).', 'NO'],
        ['Drainage and 30-ft BMP access easements at each pond',
         'Within Tracts E and F; Sheet C-3.0', '1 and 2', 'HOA in fee',
         'HOA under a recorded Storm Water BMP Maintenance Agreement with the City (§9.g.3).', 'NO'],
        ['Arcado Road right-of-way', 'R/W width varies — Sheet C-1.0', 'existing', 'Gwinnett County',
         'PUBLIC — Gwinnett County DOT. Nothing here is offered for dedication to the City.', 'NO'],
    ]


def phase_rows():
    l1 = [l for l in LOTS if l['phase'] == 1]
    l2 = [l for l in LOTS if l['phase'] == 2]
    tr = {p: ', '.join(t['id'] for t in TRACTS if t['phase'] == p) for p in (1, 2)}

    def blk(b, ls):
        return '%s — %d lots (%d SW, %d NE), numbered %s-1 to %s-%d' % (
            b, len(ls), sum(1 for l in ls if l['side'] == 'SW'),
            sum(1 for l in ls if l['side'] == 'NE'), b, b, len(ls))

    return [
        ['Block and lots', blk(B1, l1), blk(B2, l2)],
        ['Station; gross area; density', 'STA %s–%s; %s SF = %.2f ac; %.2f du/ac'
         % (sta(0), sta(STA_PHASE), sf(GROSS[1]), GROSS[1] / 43560.0, len(l1) / (GROSS[1] / 43560.0)),
         'STA %s–%s; %s SF = %.2f ac; %.2f du/ac'
         % (sta(STA_PHASE), sta(STA_END), sf(GROSS[2]), GROSS[2] / 43560.0, len(l2) / (GROSS[2] / 43560.0))],
        ['Open space; turnarounds; pond', 'Tracts %s — %s SF; hammerhead 1; Pond 1, %s cf'
         % (tr[1], sf(PHASE_OS[1]), sf(PONDS[0]['est_storage_cf'])),
         'Tracts %s — %s SF; hammerheads 2 and 3; Pond 2, %s cf'
         % (tr[2], sf(PHASE_OS[2]), sf(PONDS[1]['est_storage_cf']))],
        ['Amenities', 'The whole amenity block — clubhouse, green, two courts, kiosk, guest parking, '
                      'monument sign', 'None deferred to Phase 2'],
        ['Sanitary sewer', 'Gravity to the existing 8-in county main already on the property (MH inv '
                           '927.13). NO EXTENSION.',
         'Gravity only, ≈ %.0f ft of it off site, to MH inv 919.58. Conditions 15 and 16.' % OFFSITE_FT],
        ['Demolition', 'Dwelling at 4541 Arcado Rd (u ≈ 203)',
         'Dwelling at 4535 Arcado Rd (u ≈ 1,202) — stands ON the lane; remove before any Phase 2 '
         'disturbance'],
        ['Does the phase stand alone?', 'YES — entrance, all amenities, Pond 1, a turnaround and gravity '
                                        'sewer; no off-site easement, no second access needed',
         'NO — needs a recorded off-site easement and a Gwinnett DWR capacity certification'],
    ]


# --------------------------------------------------------------------------- legend and notes
LEGEND = [
    ('line', '#000', 1.8, '', 'Assemblage boundary (Gwinnett GIS — DRAFT)'),
    ('rect', sb.C['adj_fill'], 0, '', 'Adjoining tax parcel — zoned R-1, Lilburn'),
    ('line', sb.C['rw'], 0.9, '', 'Arcado Rd right-of-way line (Gwinnett County)'),
    ('line', '#333', 0.6, '14 3 3 3', 'Existing street centreline'),
    ('rect', FILL_A, 0, '', 'Lot in Block A — Phase 1 (fee simple, private)'),
    ('rect', FILL_B, 0, '', 'Lot in Block B — Phase 2 (fee simple, private)'),
    ('line', CA, 2.8, '', 'Block A boundary — drawn on lot lines only'),
    ('line', CB, 2.8, '', 'Block B boundary — drawn on lot lines only'),
    ('line', sb.C['phase'], 3.4, '18 5 4 5', 'Phase line = Block A – Block B boundary'),
    ('rect', C_OS, 0, '', 'Common open-space tract, HOA-owned'),
    ('key', C_OS, 0, '', 'Open-space tract key — see the tract table'),
    ('rect', sb.C['tract'], 0, '', 'Private lane tract, HOA-owned — NOT open space'),
    ('rect', sb.C['pave'], 0, '', 'Pavement — lane, entry drive, turnarounds, bays'),
    ('rect', '#f7f7f7', 0, '', "Sidewalk, 5'-0\""),
    ('line', '#666', 0.35, '', 'Parking stall (12 guest and mail-kiosk spaces)'),
    ('line', '#444', 0.4, '12 3 2 3', 'Private lane centreline'),
    ('rect', 'url(#bufhatch)', 0, '', "20' buffer easement in a lot (reported separately)"),
    ('rect', C_GREEN, 0, '', 'Village green (within Tract A)'),
    ('rect', C_BUILT, 0, '', 'Clubhouse, court pads, kiosk — built, Tract A'),
    ('rect', '#333', 0, '', 'Monument entry sign (permitted separately)'),
    ('rect', sb.C['pond'], 0, '', 'Dry detention / water-quality basin (earthen)'),
    ('rect', 'url(#exhatch)', 0, '', 'Existing dwelling — to be removed'),
    ('rect', '#efe6dc', 0, '', 'Existing drive — to be removed'),
    ('line', sb.C['stream'], 1.6, '', 'Stream — state waters (top of bank approximate)'),
    ('line', sb.C['buf_line'], 0.5, '3 2', "25' state (GA EPD) stream buffer"),
    ('line', sb.C['buf_line'], 0.8, '6 2', "50' undisturbed stream buffer (Lilburn)"),
    ('line', sb.C['buf_line'], 0.8, '8 2 2 2', "75' impervious setback"),
    ('line', sb.C['sewer'], 1.0, '', 'Existing 8-in sanitary sewer and manhole'),
    ('line', sb.C['sewer'], 2.2, '9 4', 'Phase 2 gravity sewer — easement to be recorded'),
]


def notes():
    return [
        'BLOCKS. Site Development Plan Review Checklist §4.i: "Subdivision — add number of lots/units … '
        'Lot and Block Numbers if applicable. Phasing is not permitted unless platted in Blocks." Block '
        '%s (Phase 1, %d lots) and Block %s (Phase 2, %d lots) are platted as blocks, and every block '
        'boundary drawn here lies on a lot line or a tract line. Numbers %s-1…%s-%d and %s-1…%s-%d carry '
        'to the plat; column 2 of each schedule gives the C-2.0 lot number.'
        % (B1, N_PHASE[1], B2, N_PHASE[2], B1, B1, len(BLOCK_LOTS[B1]), B2, B2, len(BLOCK_LOTS[B2])),

        'PHASE LINE. STA %s along the travelled way from the Arcado Rd right-of-way (%.0f-ft entry drive '
        'plus lane) = local station u %.0f. NE side: the common lot line of Lots %s-%d and %s-%d. SW '
        'side: the tract line between Tract E (Pond 1) and Lot %s-%d. Between them it crosses only the '
        'private lane tract. IT DIVIDES %d LOTS.'
        % (sta(STA_PHASE), ENTRY_LEN, PHASE_U, NE_PAIR[0]['block'], NE_PAIR[0]['block_lot'],
           NE_PAIR[1]['block'], NE_PAIR[1]['block_lot'], SW_NEXT['block'], SW_NEXT['block_lot'],
           len(CROSSED)),

        'PHASE 1 IS DESIGNED TO STAND ALONE. Block %s carries the entrance, the entire amenity block '
        '(Tract A), Pond 1 (Tract E), the first turnaround (Tract B) and %d of the %d lots, served by '
        'gravity to the existing 8-in county main already crossing the property (MH inv 927.13). No '
        'sewer extension, no off-site easement, no second access; complete whether or not Phase 2 is '
        'built.' % (B1, N_PHASE[1], len(LOTS)),

        'PHASE 2 CONDITION. No Phase 2 work and no land-disturbance permit until (a) the off-site '
        'sewer easement for the ≈ %.0f-ft gravity tie to the Legends at Parkview main (MH inv 919.58) is '
        'RECORDED and (b) Gwinnett County DWR has issued its SEWER CAPACITY CERTIFICATION (condition '
        '16). Gravity only: no private pump station, force main, private gravity sewer, grinder pump or '
        'low-pressure system (Gwinnett DWR Standard Policy for Private Developments, rev. 9/2018; '
        'WSR-24 §1.3.1(A)). If either fails, Phase 2 is not built, and 4535 Arcado Rd — which stands on '
        'the lane alignment — comes down under permit first (condition 15).' % OFFSITE_FT,

        'OPEN SPACE IS VOLUNTARY. Table 4.1 refers the R-2 open-space requirement to §5.9 of the '
        'Development Regulations; §5.9.1 "Recreation Areas" reaches detached subdivisions "having a '
        'gross area of 50 acres or more." At %.2f ac it is not engaged: none of the %s SF is required.'
        % (DEEDED_AC, sf(OS_TOTAL)),

        'BUFFER EASEMENT — REPORTED SEPARATELY. The rear 20 ft of each of the %d lots is undisturbed '
        'buffer in a recorded easement inside the private lot (Ord. 2023-603 §313(1)): %s SF. It is not '
        'a common tract, is not in the %s SF total, and is in no percentage on this sheet.'
        % (len(LOTS), sf(BUF_SF), sf(OS_TOTAL)),

        'AREA BASIS. %s SF = %.3f ac GIS; %s SF = %.2f ac deeded; percentages given against both. Tract '
        'areas are the published residual — GIS area less lots less the lane and entry-drive tracts — so '
        'the eight sum exactly. Tract A is NET: its outline encloses ≈ %s SF, of which ≈ %s SF is entry '
        'drive and lane tract.'
        % (sf(GIS_SF), GIS_SF / 43560.0, sf(DEEDED_SF), DEEDED_AC, sf(AM_GROSS), sf(AM_CROSSED)),

        'BUILT AND PAVED INSIDE THE OPEN SPACE. %s SF of %s SF; the balance, %s SF (%.1f%% of the GIS '
        'area), is green. Turnaround legs are counted at the full %s SF each although only ≈ %s SF of '
        'the %s SF really falls inside the greens, so the figure is conservative. The %d guest and kiosk '
        'spaces (%s SF of bays) lie in the lane tract and are not counted at all.'
        % (sf(OS_BUILT), sf(OS_TOTAL), sf(OS_SUM['green_only_sf']), OS_SUM['green_only_pct_of_gis_area'],
           sf(HH_LEG_SF), sf(HH_REAL), sf(6 * HH_LEG_SF), N_GUEST, sf(BAY_SF)),

        'MAINTENANCE (§4.o). A mandatory HOA owns and maintains Tracts A–H, the lane tract and its '
        'sidewalks, both ponds, the buffers and buffer easements, the entry sign and the lighting, and '
        'provides yard maintenance to every lot (condition 10). NOTHING IS OFFERED FOR DEDICATION TO '
        'THE CITY; only the sanitary mains and their easements become public, to Gwinnett DWR.',

        'NOT SHOWN, AND SOURCES. Dwellings, driveways and setback envelopes — Sheets C-2.0/2.1/2.2; '
        'bearings and topography — C-1.0; grading — C-3.0; utilities — C-4.0/4.1. Only the sewer '
        'reaches on or adjoining the property are drawn. Every area, count and station here is read at '
        'run time from data/layout.json (%s) and data/plans.json.' % sb.DATE,
    ]


def flow_notes(D, x, y, w, ncols, hmax, texts, size=TXT, lead=LEAD, gap=18.0):
    """Balanced multi-column note block at a FIXED type size (the 1/8-in minimum is a house
    rule, so the block is never shrunk to fit — it reports overflow instead)."""
    cw = (w - gap * (ncols - 1)) / ncols
    chars = max(int((cw - 14) / (0.56 * size)), 8)
    blocks = [sb.wrap('%d. %s' % (i, t), chars) for i, t in enumerate(texts, 1)]
    total = sum(len(b) + 1 for b in blocks) - 1
    target = math.ceil(total / float(ncols))
    cols, cur, used = [], [], 0
    for b in blocks:
        if cur and used + len(b) > target and len(cols) < ncols - 1:
            cols.append(cur)
            cur, used = [], 0
        cur.append(b)
        used += len(b) + 1
    cols.append(cur)
    tallest = 0.0
    for ci, col in enumerate(cols):
        yy = y
        for b in col:
            for j, ln in enumerate(b):
                D.stext(x + ci * (cw + gap) + (0 if j == 0 else 13), yy, ln, size=size)
                yy += lead
            yy += lead * 0.35
        tallest = max(tallest, yy - y)
    return tallest, (y + tallest <= hmax), chars


# --------------------------------------------------------------------------- plan layers
def tract_layer(c):
    """Common open-space tract fills — drawn first, under the lane, amenity and ponds."""
    c.add('<g id="open-space-tracts">')
    for t in TRACTS:
        for p in t['polys']:
            c.poly(p, fill=C_OS, stroke=C_OSLINE, stroke_width=1.2, stroke_dasharray='9 3')
    c.add('</g>')


def tract_keys(c):
    """The keyed tract symbols A-H, drawn last so nothing buries them."""
    for t in TRACTS:
        for p in t['polys']:
            if abs(sb.poly_area(p)) < 1800:
                continue
            ctr = sb.poly_centroid(p)
            if t['id'] == 'A':
                ctr = (108.0, -60.0)
            c.circle(ctr, 13.0, fill='#fff', stroke=C_OSLINE, stroke_width=1.8)
            c.text(ctr[0], ctr[1], t['id'], size=16, bold=True, fill='#1b5e20', dy=6)


def amenity_layer(c):
    c.add('<g id="amenity">')
    c.poly([tuple(p) for p in AM['village_green']], fill=C_GREEN, stroke=C_OSLINE, stroke_width=0.5)
    for k in ('parking_bay', 'kiosk_bay'):
        c.poly([tuple(p) for p in AM[k]], fill=sb.C['pave'], stroke='#333', stroke_width=0.6)
    for st in AM['stalls'] + AM['kiosk_stalls']:
        c.poly([tuple(p) for p in st], fill='none', stroke='#666', stroke_width=0.35)
    for pad in AM['pickleball']:
        c.poly([tuple(p) for p in pad], fill=C_BUILT, stroke='#222', stroke_width=0.7)
    c.poly([tuple(p) for p in AM['clubhouse']], fill=C_BUILT, stroke='#222', stroke_width=1.0)
    c.poly([tuple(p) for p in AM['mail_kiosk']], fill=C_BUILT, stroke='#222', stroke_width=0.7)
    c.poly([tuple(p) for p in AM['entry_sign']], fill='#333', stroke='none')
    c.add('</g>')


def pond_layer(c):
    c.add('<g id="ponds">')
    for p in PONDS:
        c.poly([tuple(q) for q in p['polygon']], fill=sb.C['pond'], stroke=sb.C['buf_line'],
               stroke_width=0.9, stroke_dasharray='5 2')
    c.add('</g>')


def lot_layer(c, numbers=True):
    c.add('<g id="lots">')
    for l in LOTS:
        c.poly([tuple(p) for p in l['polygon']], fill=(FILL_A if l['phase'] == 1 else FILL_B),
               stroke='#333', stroke_width=0.7)
        c.poly([tuple(p) for p in l['buffer_easement']], fill='url(#bufhatch)', stroke='none')
    c.add('</g>')
    if numbers:
        lot_numbers(c)


def lot_numbers(c):
    """Block-lot numbers, drawn last so the existing-dwelling hatch cannot bury them."""
    for l in LOTS:
        u0, u1 = lot_u(l)
        ctr = sb.poly_centroid([tuple(p) for p in l['polygon']])
        v = ctr[1] + (24.0 if l['side'] == 'SW' else -24.0)   # toward the lane, clear of the hatch
        c.text((u0 + u1) / 2.0, v, '%s-%d' % (l['block'], l['block_lot']), size=13.5, bold=True,
               fill=(CA if l['block'] == 'A' else CB), halo=True, dy=4)


def block_layer(c):
    """Block boundaries — heavy, and every segment lies on a lot line."""
    c.add('<g id="blocks">')
    for b in BLOCKS:
        col = CA if b == B1 else CB
        for side in ('SW', 'NE'):
            for run in block_runs(b, side):
                c.poly(run_polygon(run), fill='none', stroke=col, stroke_width=2.8)
    c.add('</g>')


def phase_line(c, labels=True):
    c.line((PHASE_U, sb.SW(PHASE_U) - 16.0), (PHASE_U, sb.NE(PHASE_U) + 16.0),
           stroke=sb.C['phase'], stroke_width=3.4, stroke_dasharray='18 5 4 5')
    if labels:
        c.text(PHASE_U - 9, -248, 'PHASE LINE — STA %s (u = %.0f)' % (sta(STA_PHASE), PHASE_U),
               size=13, bold=True, rot=-90, fill=sb.C['phase'], halo=True, anchor='start')


def sewer_layer(c, labels=True):
    """Only the reaches on or adjoining the property; the off-site downstream leg of the Arcado
    outfall is not part of this exhibit and is omitted (general note 11)."""
    c.add('<g id="sewer">')
    for run in L['sewer']['existing_on_site']:
        path = [tuple(p) for p in run['path']]
        if (path[0][1] + path[-1][1]) / 2.0 < -260.0:
            continue
        c.pline(path, fill='none', stroke=sb.C['sewer'], stroke_width=1.0)
        for p in path:
            c.circle(p, 2.4, fill='#fff', stroke=sb.C['sewer'], stroke_width=0.8)
    ext = [tuple(p) for p in L['sewer']['phase2_alternative_extension']]
    c.pline(ext, fill='none', stroke=sb.C['sewer'], stroke_width=2.2, stroke_dasharray='9 4')
    for p in (ext[0], ext[-1]):
        c.circle(p, 2.8, fill='#fff', stroke=sb.C['sewer'], stroke_width=1.0)
    c.add('</g>')
    if not labels:
        return
    c.circle((271.7, -224.0), 6.0, fill='none', stroke=sb.C['sewer_txt'], stroke_width=1.2)
    c.text(950, -244, 'PHASE 1 POINT OF CONNECTION — EX. MH INV 927.13 (GIS ATTRIBUTE, UNSURVEYED) — '
           'NO SEWER EXTENSION IN PHASE 1', size=12.6, bold=True, fill=sb.C['sewer_txt'], halo=True,
           anchor='end')
    c.text(1372, -388, 'PHASE 2 — 8-in GRAVITY SEWER TO THE LEGENDS AT PARKVIEW MAIN, MH INV 919.58;',
           size=12.6, bold=True, fill=sb.C['sewer_txt'], halo=True, anchor='start')
    c.text(1372, -403, '≈ %.0f FT OF IT OFF SITE. EASEMENT TO BE RECORDED AND DWR CAPACITY'
           % OFFSITE_FT, size=12.6, fill=sb.C['sewer_txt'], halo=True, anchor='start')
    c.text(1372, -418, 'CERTIFICATION ISSUED BEFORE ANY PHASE 2 WORK (CONDITION 16)', size=12.6,
           fill=sb.C['sewer_txt'], halo=True, anchor='start')


def callout(D, x, y, w, lines, title, col='#000', lead=15.4, pad=9.0):
    h = pad * 2 + 17 + lead * len(lines)
    D.srect(x, y, w, h, fill='#fff', stroke=col, stroke_width=1.4)
    D.stext(x + pad, y + pad + 12, title, size=13.6, bold=True, fill=col)
    for i, ln in enumerate(lines):
        D.stext(x + pad, y + pad + 17 + lead * (i + 1) - 3, ln, size=TXT)
    return y + h


# --------------------------------------------------------------------------- build
def build():
    scale_note = 'Scale 1" = 60\' (ARCH D 36 × 24 in)'
    D, F = sb.sheet(
        'PHASING, BLOCK AND OPEN SPACE EXHIBIT', 'C-6.0',
        'Blocks, phases, common open-space tracts, easements and maintenance responsibility — Site '
        'Development Plan Review Checklist §4.i and §4.o; Ord. 2023-603 §313(1)',
        scale_note, generator='tools/sitebase.py + tools/phasing.py', win=WIN,
        north_at=(sb.PLAN_X0 + 2328.0, sb.PLAN_Y0 + 38.0),
        scale_at=(sb.PLAN_X0 + 1360.0, sb.PLAN_Y0 + PLAN_H - 62.0),
        status_lines=[
            'Phasing, block and open-space CONCEPT compiled from public records',
            'for pre-application review. NOT A PLAT. Block and lot platting, tract',
            'and easement descriptions and every area shown are to be prepared and',
            'sealed by a Georgia RLS; utilities and stormwater by a Georgia PE.'])
    px, py, pw, ph = F['plan']

    # the base sheet's watermark names existing conditions; this sheet needs its own
    D.late[1] = (lambda: D.add(
        '<text x="%.1f" y="%.1f" font-size="38" fill="#c00" fill-opacity="0.09" font-weight="bold" '
        'text-anchor="middle" transform="rotate(-6 %.1f %.1f)">DRAFT — NOT SEALED — PHASING, BLOCK AND '
        'OPEN-SPACE CONCEPT — NOT A PLAT</text>'
        % (px + pw / 2, py + ph * 0.24, px + pw / 2, py + ph * 0.24)))
    # a white backing for the graphic scale, painted before the scale bar itself
    D.late.insert(3, lambda: D.srect(px + 1342, py + ph - 84, 330, 52, fill='#fff', stroke='#888',
                                     stroke_width=0.8))

    # ---------------------------------------------------------------- plan
    D.clip_open(fill='#fff')
    sb.adjoiners(D, labels=False, zoning=False)
    sb.arcado_row(D, labels=False)
    tract_layer(D)
    sb.lane(D, labels=False)
    amenity_layer(D)
    pond_layer(D)
    lot_layer(D, numbers=False)
    sb.streams_and_buffers(D, labels=False)
    sewer_layer(D)
    sb.existing_structures(D, labels=False)
    lot_numbers(D)
    sb.boundary(D, bearings=False, label=False)
    tract_keys(D)
    block_layer(D)
    phase_line(D)

    D.text(600, 24, '◄  PHASE 1 — BLOCK %s — %d LOTS   (STA %s TO %s)'
           % (B1, N_PHASE[1], sta(0), sta(STA_PHASE)), size=17, bold=True, fill=CA, halo=True)
    D.text(1330, 24, 'PHASE 2 — BLOCK %s — %d LOTS   (STA %s TO %s)  ►'
           % (B2, N_PHASE[2], sta(STA_PHASE), sta(STA_END)), size=17, bold=True, fill=CB, halo=True)
    D.text(-104, -140, 'ARCADO ROAD — PUBLIC R/W', size=12.6, bold=True, rot=-81, fill='#444', halo=True)
    D.text(-126, -140, 'GWINNETT CO. MINOR COLLECTOR', size=12.6, rot=-81, fill='#444', halo=True)
    D.text(-64, 24, 'KING DAVID MANOR — ZONED R-1 (LILBURN)', size=12.6, bold=True, fill='#555',
           halo=True, anchor='start')
    D.text(0, -244, 'LEGENDS AT PARKVIEW — ZONED R-1 (LILBURN)', size=12.6, bold=True, fill='#555',
           halo=True, anchor='start')
    D.text(1790, -244, 'TRACTS G AND H — CREEK WOODS AND STREAM SETBACK, PRESERVED, NOTHING BUILT OR '
                       'PAVED', size=12.6, bold=True, fill='#1b5e20', halo=True, anchor='end')
    D.text(203, -104, 'EX. DWELLING 4541 — REMOVE IN PHASE 1', size=12.6, bold=True,
           fill=sb.C['exist'], halo=True)
    for k, ln in enumerate(['EX. DWELLING 4535 — STANDS ON THE LANE ALIGNMENT;',
                            'REMOVE UNDER PERMIT BEFORE ANY PHASE 2 LAND',
                            'DISTURBANCE (VOLUNTARY CONDITION 15)']):
        D.text(1256, -22 - 14 * k, ln, size=12.6, bold=True, fill=sb.C['exist'], halo=True,
               anchor='start')
    D.clip_close()

    # ---------------------------------------------------------------- legend, on the plan
    # Placed over the Legends at Parkview parcels at u 0-800, which carry nothing this sheet
    # needs; the stream, its buffers, the Phase 2 sewer tie and their notes stay clear to the
    # right of it.
    lx, ly, lw, lh = px + 180, py + ph - 230, 1140.0, 230.0
    D.srect(lx, ly, lw, lh, fill='#fff', stroke='#000', stroke_width=1.2)
    D.stext(lx + 10, ly + 18, 'LEGEND — every symbol drawn on this sheet appears here, and no entry is '
                              'unused', size=13.6, bold=True)
    ncol, per = 3, int(math.ceil(len(LEGEND) / 3.0))
    for i, (kind, col, wd, dash, txt) in enumerate(LEGEND):
        cx = lx + 10 + (i // per) * (lw - 20) / ncol
        yy = ly + 38 + (i % per) * 18.9
        if kind == 'line':
            D.sline(cx, yy - 4, cx + 34, yy - 4, stroke=col, stroke_width=wd, stroke_dasharray=dash)
        elif kind == 'key':
            D.scircle(cx + 17, yy - 4.5, 8.5, fill='#fff', stroke=C_OSLINE, stroke_width=1.5)
            D.stext(cx + 17, yy - 0.5, 'A', size=10.5, bold=True, fill='#1b5e20', anchor='middle')
        else:
            D.srect(cx, yy - 12, 34, 14, fill=col, stroke='#555', stroke_width=0.5)
        D.stext(cx + 41, yy, txt, size=TXT)

    # ---------------------------------------------------------------- band, column 1: lot schedules
    x1, w1 = F['inner_l'] + 20, float(sum(LOT_W))
    y = sb.table(D, x1, BAND_Y0, LOT_COLS, lot_rows(B1), size=TXT, widths=LOT_W,
                 title='LOT SCHEDULE — BLOCK %s (PHASE 1), %d LOTS' % (B1, N_PHASE[1]))
    y = sb.table(D, x1, y + 30, LOT_COLS, lot_rows(B2), size=TXT, widths=LOT_W,
                 title='LOT SCHEDULE — BLOCK %s (PHASE 2), %d LOTS' % (B2, N_PHASE[2]))
    ends = {1: y}

    # ---------------------------------------------------------------- band, column 2: general notes
    x2, w2 = x1 + w1 + 20, 692.0
    D.stext(x2, BAND_Y0 + 2, 'GENERAL NOTES — PHASING, BLOCKS AND OPEN SPACE', size=15, bold=True)
    nh, fits, nchars = flow_notes(D, x2, BAND_Y0 + 24, w2, 1, BAND_Y1, notes())
    tr = {p: ', '.join(t['id'] for t in TRACTS if t['phase'] == p) for p in (1, 2)}
    ends[2] = callout(
        D, x2, BAND_Y0 + 22 + nh, w2,
        ['PHASE 1 · BLOCK %s · STA %s–%s · %d lots · %s SF (%.2f ac) · %.2f du/ac'
         % (B1, sta(0), sta(STA_PHASE), N_PHASE[1], sf(GROSS[1]), GROSS[1] / 43560.0,
            N_PHASE[1] / (GROSS[1] / 43560.0)),
         'Tracts %s = %s SF · Pond 1, %s cf · turnaround 1 · gravity to the on-site main'
         % (tr[1], sf(PHASE_OS[1]), sf(PONDS[0]['est_storage_cf'])),
         'PHASE 2 · BLOCK %s · STA %s–%s · %d lots · %s SF (%.2f ac) · %.2f du/ac'
         % (B2, sta(STA_PHASE), sta(STA_END), N_PHASE[2], sf(GROSS[2]), GROSS[2] / 43560.0,
            N_PHASE[2] / (GROSS[2] / 43560.0)),
         'Tracts %s = %s SF · Pond 2, %s cf · turnarounds 2, 3 · ≈ %.0f ft off-site sewer tie'
         % (tr[2], sf(PHASE_OS[2]), sf(PONDS[1]['est_storage_cf']), OFFSITE_FT),
         'Every lot %s SF · %.0f ft × %.0f ft · %.0f ft of frontage on the private lane (§319 requires '
         '30 ft)' % (sf(M['lot_area_min_sf']), M['lot_width_min_ft'], M['lot_depth_min_ft'], 50.0),
         'PLAN A = "%s", %s SF conditioned · PLAN B = "%s", %s SF conditioned (data/plans.json)'
         % (PLANS['A']['name'].title(), sf(PLANS['A']['areas']['conditioned_sf']),
            PLANS['B']['name'].title(), sf(PLANS['B']['areas']['conditioned_sf']))],
        'PHASE DATA — %d LOTS IN TWO BLOCKS, %.2f DU/AC ON THE DEEDED %.2f AC'
        % (len(LOTS), M['density_du_ac_deeded'], DEEDED_AC), col=sb.C['phase'], lead=14.4, pad=7.0)

    # ------------------------------------------- band, column 3: tract table, easements, condition
    x3, w3 = x2 + w2 + 20, 1180.0
    y3 = sb.table(D, x3, BAND_Y0,
                  ['TR.', 'NAME AND LOCATION', 'AREA SF', '% GIS', '% 9.44 AC', 'PH./BLK',
                   'WHAT THE TRACT CONTAINS — BUILT AND PAVED AREA STATED', 'MAINT.'],
                  tract_rows(), size=TXT, widths=[36, 190, 72, 58, 72, 58, 548, 146],
                  title='COMMON OPEN-SPACE TRACT TABLE — %s SF = %.3f AC = %.1f%% OF THE %s-SF GIS AREA '
                        '/ %.1f%% OF THE DEEDED %.2f AC'
                        % (sf(OS_TOTAL), OS_SUM['total_ac'], OS_SUM['pct_of_gis_area'], sf(GIS_SF),
                           OS_SUM['pct_of_deeded_area'], DEEDED_AC))
    D.stext(x3, y3 + 13, 'TRACT A HOLDS %s SF OF BUILT AND PAVED AREA — %.1f%% OF THE TRACT — AND ITS '
            '%s SF IS NET OF THE ≈ %s SF OF ENTRY DRIVE AND LANE TRACT CROSSING IT;'
            % (sf(AM_BUILT), 100.0 * AM_BUILT / TRACTS[0]['area'], sf(TRACTS[0]['area']), sf(AM_CROSSED)),
            size=13.2, bold=True, fill=C_OSLINE)
    D.stext(x3, y3 + 30, 'THE %d GUEST AND MAIL-KIOSK PARKING SPACES (%s SF OF BAYS) ARE NOT IN IT — '
            'THEY LIE IN THE PRIVATE LANE TRACT. SEE NOTE 8.' % (N_GUEST, sf(BAY_SF)),
            size=13.2, bold=True, fill=C_OSLINE)
    y3 = sb.table(D, x3, y3 + 48,
                  ['ITEM', 'AREA / DIMENSION', 'PHASE', 'OWNERSHIP', 'MAINTENANCE — HOA OR PUBLIC'],
                  [r[:5] for r in easement_rows()], size=TXT, widths=[316, 186, 62, 228, 388],
                  title='OTHER COMMON PROPERTY AND EASEMENTS — MAINTENANCE RESPONSIBILITY (CHECKLIST '
                        '§4.o). NONE OF IT IS COUNTED AS COMMON OPEN SPACE')
    D.srect(x3, y3 + 10, w3, 42, fill='#f7f0fa', stroke=sb.C['phase'], stroke_width=1.4)
    D.stext(x3 + 9, y3 + 26, 'PHASE 1 STANDS ALONE. PHASE 2 SHALL NOT COMMENCE UNTIL THE OFF-SITE '
                             'SANITARY SEWER EASEMENT IS RECORDED AND GWINNETT COUNTY DWR HAS',
            size=13.2, bold=True, fill=sb.C['phase'])
    D.stext(x3 + 9, y3 + 43, 'ISSUED ITS SEWER CAPACITY CERTIFICATION (LETTER OF INTENT, VOLUNTARY '
                             'CONDITIONS 15 AND 16 — SEE NOTES 3 AND 4).',
            size=13.2, bold=True, fill=sb.C['phase'])
    ends[3] = y3 + 52
    return D, ends, fits, nchars


def _check_note_refs():
    """The tract table and the emphasis lines cross-reference general notes by number; keep the
    references honest if the note list is ever re-ordered."""
    want = {'PHASE 1 IS DESIGNED': 3, 'PHASE 2 CONDITION': 4, 'OPEN SPACE IS VOLUNTARY': 5,
            'BUFFER EASEMENT': 6, 'BUILT AND PAVED': 8}
    got = {}
    for i, t in enumerate(notes(), 1):
        for k in want:
            if t.startswith(k):
                got[k] = i
    bad = {k: (want[k], got.get(k)) for k in want if got.get(k) != want[k]}
    return bad


if __name__ == '__main__':
    bad = _check_note_refs()
    if bad:
        raise SystemExit('note cross-references are stale: %s' % bad)
    D, ends, fits, nchars = build()
    svg, png = sb.save(D, 'phasing-openspace', dpi=150)
    print('wrote %s\n      %s' % (svg, png))
    print('  lettering : %.1f pt minimum = %.4f in cap height at full size (%.4f in on 11 × 17)'
          % (TXT, CAP_IN, CAP_IN * 11.0 / 24.0))
    print('  blocks    : ' + '; '.join(
        '%s = phase %d, %d lots [%s]' % (b, PHASE_OF_BLOCK[b], len(BLOCK_LOTS[b]),
                                         ', '.join('%s %.0f–%.0f' % (r[0]['side'], lot_u(r[0])[0], lot_u(r[-1])[1])
                                                   for s in ('SW', 'NE') for r in block_runs(b, s)))
        for b in BLOCKS))
    print('  phase line: u = %.1f = STA %s of a %s travelled way; lots divided by it: %d'
          % (PHASE_U, sta(STA_PHASE), sta(STA_END), len(CROSSED)))
    print('  tracts    : ' + '; '.join('%s %s SF (shoelace %s)' % (t['id'], sf(t['area']), sf(t['shoelace']))
                                       for t in TRACTS))
    print('  open space: %s SF = %.3f ac = %.1f%% GIS / %.1f%% deeded; built or paved %s SF; '
          'buffer easement on lots %s SF (reported separately)'
          % (sf(OS_TOTAL), OS_SUM['total_ac'], OS_SUM['pct_of_gis_area'], OS_SUM['pct_of_deeded_area'],
             sf(OS_BUILT), sf(BUF_SF)))
    print('  amenity   : gross %s SF less %s SF of lane/entry = %s SF net (published %s SF)'
          % (sf(AM_GROSS), sf(AM_CROSSED), sf(AM_GROSS - AM_CROSSED), sf(TRACTS[0]['area'])))
    print('  turnaround: legs counted %s SF, actually inside the greens %s SF'
          % (sf(6 * HH_LEG_SF), sf(HH_REAL)))
    print('  gross area: phase 1 %s SF, phase 2 %s SF, sum %s SF vs boundary %s SF'
          % (sf(GROSS[1]), sf(GROSS[2]), sf(GROSS[1] + GROSS[2]), sf(GIS_SF)))
    print('  band fit  : columns end at %s (limit %.0f); notes %d chars/line, fits=%s'
          % (', '.join('%d:%.0f' % (k, v) for k, v in sorted(ends.items())), BAND_Y1, nchars, fits))
    print('  notes     : %d notes, cross-references checked (phase 1 = 3, phase 2 = 4, open space = 5, '
          'buffer = 6, built/paved = 8)' % len(notes()))
