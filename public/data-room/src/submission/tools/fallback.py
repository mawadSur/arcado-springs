#!/usr/bin/env python3
"""Sheet C-2.4 "FALLBACK LOT-DEPTH LAYOUT EXHIBIT" — The Cottages at Arcado Springs.

    python3 tools/fallback.py     ->  drawings/fallback-layout.svg + .png   (ARCH D 36 x 24, 1" = 60')

WHY THIS SHEET EXISTS
Sheet C-2.0 (master concept plan) fits two facing rows of 50'-0" x 100'-0" cottage lots on a
234.70-246.38-ft-wide strip only because the 20-ft buffer required against the abutting R-1
property is held INSIDE the rear 20 ft of each perimeter lot, in a recorded buffer easement,
on the strength of Lilburn Zoning Ordinance 2023-603 section 313(1) ("Buffer requirements ...
supersede these minimum required yards").

The 2026-09-03 external-fact review (audit-2026-09-03/external-facts.md, item P1) found that
reading weaker than the package had assumed: section 313(1) speaks of "buffer requirements
established by this article" - Article 3 - and Article 3 sets no buffer widths at all; the
20-ft R-1 buffer comes from Table 4.1 in Article 4. Nothing in the ordinance expressly
authorises holding a required buffer inside a private lot. Independently, the City of Lilburn
Site Development Plan Review Checklist section 6.c reads "If a portion of required buffer is
within an easement, provide 25' additional buffer outside easement."

So the application must be able to answer the unfavourable reading with a drawing, not a
sentence. This sheet is that drawing: the same boundary, the same entrance, the same lane, the
same amenity block, ponds, greens and phasing, with the 20-ft buffer moved into separate
HOA-owned tracts, the lots shortened to 50'-0" x 82'-0" (4,100 SF), a concurrent variance
under section 1005 from the 100-ft minimum lot depth of Table 4.1, and a third, shallower house
plan - because the body depth left on an 82-ft lot is 82 - 15 - 20 = 47'-0" less the 6'-0"
porch = 41'-0", and neither Plan A (51'-10") nor Plan B (57'-6") fits it.

WHAT IS COMPUTED HERE (nothing is transcribed from an older document)
  * every fallback lot polygon, from data/layout.json's boundary and lot stationing;
  * the 20-ft perimeter buffer tract, as a true mitred inward offset of the side and rear
    property lines;
  * the fallback lane tract and its asymmetric section, and the station at which the second
    (SW) sidewalk can begin;
  * lot count, density, lot and open-space areas, impervious area and WQv;
  * the Plan C schematic footprint and its areas.
Sheet furniture, palette, title block, north arrow, graphic scale and disclaimer come from
tools/sitebase.py, exactly as on Sheet C-0.

DRAFT - NOT SEALED. This sheet is an ALTERNATIVE, not the proposed plan. It is to be
superseded by a sealed Georgia RLS boundary survey and PE civil design, and Plan C is a
schematic block plan that must be replaced by a Georgia-registered architect's drawings.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitebase as sb                                       # noqa: E402

fti = sb.fp.fti
LAYOUT = sb.LAYOUT
M = LAYOUT['metrics']

# ============================================================================ design constants
BUF_W = 20.0                     # Table 4.1 buffer abutting R-1 for "all other allowed dwelling types"
LOT_W, LOT_D = 50.0, 82.0        # the fallback lot module
LOT_SF = LOT_W * LOT_D
PAVE_W, STRIP, WALK = 22.0, 2.0, 5.0
HALF_SECTION = PAVE_W / 2 + STRIP + WALK          # 18.0 ft of half-tract where a sidewalk is carried
MIN_TRACT = PAVE_W + STRIP + WALK + STRIP         # 31.0 ft - the minimum private-lane tract
FRONT_SB, SIDE_SB, REAR_SB = 15.0, 5.0, 20.0      # Table 4.1 R-2 (local street / interior lot)
PORCH_D = 6.0
BODY_W, BODY_D = 38.0, LOT_D - FRONT_SB - REAR_SB - PORCH_D      # 38'-0" x 41'-0"
GAR_W, GAR_D, GAR_RECESS = 21.0, 21.0, 5.0
FRONT_WING_W = BODY_W - GAR_W                                     # 17'-0"
REAR_BLOCK_D = BODY_D - (GAR_RECESS + GAR_D)                      # 15'-0"
DRIVE_W = 20.0
U_JOIN, U_LOT0, U_PAVE_END = 149.5, 230.0, 1700.0
BAY = (149.5, 154.5, 225.0, 230.0)               # the amenity-block tract widening of Sheet C-2.0
BAY_HALF = 30.0

TABLE41_MIN_SF, TABLE41_MIN_W, TABLE41_MIN_D, TABLE41_MIN_HEATED = 3000.0, 50.0, 100.0, 1000.0


# ============================================================================ geometry helpers
def _lnorm(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    return (-dy / L, dx / L)


def _ll_int(p, d1, q, d2):
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-12:
        return None
    t = ((q[0] - p[0]) * d2[1] - (q[1] - p[1]) * d2[0]) / den
    return (p[0] + d1[0] * t, p[1] + d1[1] * t)


def offset_left(path, d):
    """Offset an open polyline by d to its left, with mitred joins (exact for straight courses)."""
    n, out = len(path), []
    for i in range(n):
        if i == 0 or i == n - 1:
            a, b = (path[0], path[1]) if i == 0 else (path[-2], path[-1])
            nx, ny = _lnorm(a, b)
            out.append((path[i][0] + nx * d, path[i][1] + ny * d))
            continue
        n1, n2 = _lnorm(path[i - 1], path[i]), _lnorm(path[i], path[i + 1])
        p1 = (path[i][0] + n1[0] * d, path[i][1] + n1[1] * d)
        p2 = (path[i][0] + n2[0] * d, path[i][1] + n2[1] * d)
        d1 = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        d2 = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
        out.append(_ll_int(p1, d1, p2, d2) or p1)
    return out


def seg_seg_dist(a, b, c, d):
    return min(sb._seg_pt(a, c, d), sb._seg_pt(b, c, d), sb._seg_pt(c, a, b), sb._seg_pt(d, a, b))


def poly_path_dist(poly, path):
    best = 1e9
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        for j in range(len(path) - 1):
            best = min(best, seg_seg_dist(a, b, path[j], path[j + 1]))
    return best


def frange(a, b, step):
    us, u = [], a
    while u < b - 1e-9:
        us.append(u)
        u += step
    us.append(b)
    return us


def band(u0, u1, f_lo, f_hi, step=10.0):
    us = frange(u0, u1, step)
    return [(u, f_lo(u)) for u in us] + [(u, f_hi(u)) for u in reversed(us)]


# ============================================================================ the 20-ft buffer tract
# The perimeter of the assemblage less the Arcado Rd frontage: courses 6 through 47 of
# data/layout.json "bearings" run from the SW front corner (u -36) NW along the SW line, NE
# across the rear line and SE down the NE line to the NE front corner (0, 0).  The interior lies
# to the LEFT of that direction of travel, so the inward offset is offset_left(+20).
PERIM = [tuple(sb.BEARINGS[6]['from'])] + [tuple(b['to']) for b in sb.BEARINGS[6:48]]
I_REAR0, I_REAR1 = 22, 26                                  # PERIM indices of the two rear corners
BUF_INNER = offset_left(PERIM, BUF_W)
BUFFER_TRACT = PERIM + BUF_INNER[::-1]
BUFFER_SF = abs(sb.poly_area(BUFFER_TRACT))
INNER_SW = BUF_INNER[:I_REAR0 + 1]                         # ascending u
INNER_REAR = BUF_INNER[I_REAR0:I_REAR1 + 1]
INNER_NE = sorted(BUF_INNER[I_REAR1:], key=lambda p: p[0])  # ascending u
LEG_SW_FT = sum(sb.dist(PERIM[i], PERIM[i + 1]) for i in range(I_REAR0))
LEG_REAR_FT = sum(sb.dist(PERIM[i], PERIM[i + 1]) for i in range(I_REAR0, I_REAR1))
LEG_NE_FT = sum(sb.dist(PERIM[i], PERIM[i + 1]) for i in range(I_REAR1, len(PERIM) - 1))


def buf_sw(u):
    return sb.interp_v(INNER_SW, u)


def buf_ne(u):
    return sb.interp_v(INNER_NE, u)


# ============================================================================ lots and lane
def lot_line_sw(u):
    """Lane-side (front) line of the SW lot row = buffer tract line + 82 ft."""
    return buf_sw(u) + LOT_D


def lot_line_ne(u):
    return buf_ne(u) - LOT_D


def tract_w(u):
    return lot_line_ne(u) - lot_line_sw(u)


CLM = [tuple(p) for p in LAYOUT['lane']['centerline']]      # the Sheet C-2.0 lane centreline


def clm(u):
    return sb.interp_v(CLM, u)


def mid(u):
    return (sb.SW(u) + sb.NE(u)) / 2.0


def _need(u):
    """SW offset of the travelled way from the tract midline so the NE half-section still fits."""
    return max(0.0, HALF_SECTION - tract_w(u) / 2.0)


_EXTRA0 = max(0.0, _need(U_LOT0) - (mid(U_LOT0) - clm(U_LOT0)))


def extra(u):
    """Extra SW shift of the lane centreline over the Sheet C-2.0 alignment (tapered at the front)."""
    if u <= U_JOIN:
        return 0.0
    if u < U_LOT0:
        return _EXTRA0 * (u - U_JOIN) / (U_LOT0 - U_JOIN)
    return max(0.0, _need(u) - (mid(u) - clm(u)))


def cl(u):
    return clm(u) - extra(u)


def bayf(u):
    a0, a1, b1, b0 = BAY
    if u <= a0 or u >= b0:
        return 0.0
    if u < a1:
        return (u - a0) / (a1 - a0)
    if u > b1:
        return (b0 - u) / (b0 - b1)
    return 1.0


def tr_sw(u):
    e, f = lot_line_sw(u), bayf(u)
    return e + (cl(u) - BAY_HALF - e) * f if f > 0 else e


def tr_ne(u):
    e, f = lot_line_ne(u), bayf(u)
    return e + (cl(u) + BAY_HALF - e) * f if f > 0 else e


def _sw_walk_start():
    """First 10-ft station from which the SW half-section keeps fitting to the terminus."""
    ok = U_PAVE_END
    for u in range(int(U_PAVE_END), int(U_LOT0) - 1, -10):
        if cl(u) - lot_line_sw(u) >= HALF_SECTION + 0.25:
            ok = float(u)
        else:
            break
    return ok


U_SWWALK = _sw_walk_start()

# --- lot slots: the same stationing and the same side as the 41 lots of Sheet C-2.0, so that the
#     entrance, the greens, the hammerheads, the ponds, the creek woods and the stream setback are
#     honoured exactly as they are there.  Only the depth changes.
SLOTS = []
for L in LAYOUT['lots']:
    p = [tuple(q) for q in L['polygon']]
    SLOTS.append({'id': L['id'], 'side': L['side'], 'block': L['block'], 'block_lot': L['block_lot'],
                  'phase': L['phase'], 'u0': min(q[0] for q in p), 'u1': max(q[0] for q in p)})


def lot_poly(s):
    u0, u1 = s['u0'], s['u1']
    if s['side'] == 'SW':
        return [(u0, buf_sw(u0)), (u1, buf_sw(u1)), (u1, lot_line_sw(u1)), (u0, lot_line_sw(u0))]
    return [(u0, lot_line_ne(u0)), (u1, lot_line_ne(u1)), (u1, buf_ne(u1)), (u0, buf_ne(u0))]


def lot_xy(s, x, y):
    """(x along the lot frontage from its low-u corner, y into the lot from the front line) -> (u, v)."""
    u = s['u0'] + (x if s['side'] == 'NE' else (LOT_W - x))
    front = lot_line_ne(u) if s['side'] == 'NE' else lot_line_sw(u)
    sgn = 1.0 if s['side'] == 'NE' else -1.0
    return (u, front + sgn * y)


def lot_rect(s, x0, y0, x1, y1):
    return [lot_xy(s, x0, y0), lot_xy(s, x1, y0), lot_xy(s, x1, y1), lot_xy(s, x0, y1)]


# --- Plan C, in the lot's own coordinates (y measured from the front lot line)
Y_PORCH, Y_BODY = FRONT_SB, FRONT_SB + PORCH_D                     # 15'-0" and 21'-0"
Y_GAR = Y_BODY + GAR_RECESS                                        # 26'-0"
Y_REAR_BLOCK = Y_GAR + GAR_D                                       # 47'-0"
Y_BACK = Y_BODY + BODY_D                                           # 62'-0"
X0 = (LOT_W - BODY_W) / 2.0                                        # 6'-0" side yard
X_GAR1 = X0 + GAR_W                                                # 27'-0"
X1 = X0 + BODY_W                                                   # 44'-0"
COND_L = [(X_GAR1, Y_BODY), (X1, Y_BODY), (X1, Y_BACK), (X0, Y_BACK), (X0, Y_REAR_BLOCK), (X_GAR1, Y_REAR_BLOCK)]
COND_SF = FRONT_WING_W * (Y_REAR_BLOCK - Y_BODY) + BODY_W * REAR_BLOCK_D
GAR_SF = GAR_W * GAR_D
PORCH_SF = FRONT_WING_W * PORCH_D
ROOF_SF = COND_SF + GAR_SF + PORCH_SF
PATIO_W, PATIO_D = 12.0, 6.0
WALK_SF = 60.0
DRIVE_IN_LOT_SF = DRIVE_W * Y_GAR


# ============================================================================ areas
U_TRACT_END = 1701.0                              # the lane tract ends 1 ft beyond the pavement, as on C-2.0


def lane_tract_poly():
    return band(U_JOIN, U_TRACT_END, tr_sw, tr_ne, step=5.0)


def pav_poly():
    return band(U_JOIN, U_PAVE_END, lambda u: cl(u) - PAVE_W / 2, lambda u: cl(u) + PAVE_W / 2, step=5.0)


def walk_ne_poly():
    return band(U_JOIN, U_PAVE_END, lambda u: cl(u) + PAVE_W / 2 + STRIP,
                lambda u: cl(u) + PAVE_W / 2 + STRIP + WALK, step=5.0)


def walk_sw_poly():
    return band(U_SWWALK, U_PAVE_END, lambda u: cl(u) - PAVE_W / 2 - STRIP - WALK,
                lambda u: cl(u) - PAVE_W / 2 - STRIP, step=5.0)


def hammerhead_legs():
    out = []
    for h in LAYOUT['hammerheads']:
        u0 = min(p[0] for p in h['legs'][0])
        u1 = max(p[0] for p in h['legs'][0])
        for sgn in (-1.0, 1.0):
            e0 = cl(u0) + sgn * PAVE_W / 2
            e1 = cl(u1) + sgn * PAVE_W / 2
            out.append([(u0, e0), (u1, e1), (u1, e1 + sgn * h['leg_ft']), (u0, e0 + sgn * h['leg_ft'])])
    return out


LANE_TRACT = lane_tract_poly()
PAVEMENT = pav_poly()
WALK_NE = walk_ne_poly()
WALK_SW = walk_sw_poly()
HH_LEGS = hammerhead_legs()
ENTRY = LAYOUT['lane']['entry_drive']
ENTRY_TRACT_SF = abs(sb.poly_area([tuple(p) for p in ENTRY['tract_polygon']]))
LANE_TRACT_SF = abs(sb.poly_area(LANE_TRACT))
PAVE_SF = abs(sb.poly_area(PAVEMENT))
ENTRY_PAVE_SF = abs(sb.poly_area([tuple(p) for p in ENTRY['pavement_polygon']]))
ENTRY_WALK_SF = abs(sb.poly_area([tuple(p) for p in ENTRY['sidewalk_polygon']]))
WALK_SF_TOTAL = abs(sb.poly_area(WALK_NE)) + abs(sb.poly_area(WALK_SW)) + ENTRY_WALK_SF
HH_SF = sum(abs(sb.poly_area(p)) for p in HH_LEGS)

N_LOTS = len(SLOTS)
LOTS_SF = N_LOTS * LOT_SF
GIS_SF = sb.BOUNDARY_SF
DEEDED_SF = 411206.0
OPEN_SF = GIS_SF - LOTS_SF - LANE_TRACT_SF - ENTRY_TRACT_SF
DENS_DEEDED = N_LOTS / 9.44
DENS_GIS = N_LOTS / (GIS_SF / 43560.0)

# --- driveways: 20'-0" from the garage door out to the edge of pavement; the reach that crosses the
#     5-ft sidewalk is counted once (with the sidewalk), not twice.
APRON_SF, OVERLAP_SF = 0.0, 0.0
for s in SLOTS:
    um = (s['u0'] + s['u1']) / 2.0
    half = (cl(um) - lot_line_sw(um)) if s['side'] == 'SW' else (lot_line_ne(um) - cl(um))
    APRON_SF += DRIVE_W * max(0.0, half - PAVE_W / 2)
    if s['side'] == 'NE' or um >= U_SWWALK:
        OVERLAP_SF += DRIVE_W * WALK

IMP = [
    ('Dwellings, garages and covered porches (Plan C on every lot)', N_LOTS * ROOF_SF),
    ('Lot driveways, aprons and entry walks', N_LOTS * (DRIVE_IN_LOT_SF + WALK_SF) + APRON_SF),
    ('Private lane pavement (22\'-0", unchanged)', PAVE_SF),
    ('Entry drive pavement and curb returns (unchanged)', ENTRY_PAVE_SF + 184.0),   # 184 SF of returns, layout.json
    ('Hammerhead turnaround legs (unchanged)', HH_SF),
    ('Guest and mail-kiosk parking bays (unchanged)', 2070.0),
    ('Sidewalks (5\'-0"; the SW walk begins at u = %d)' % round(U_SWWALK), WALK_SF_TOTAL),
    ('Clubhouse roof, court pads, mail kiosk and amenity walks (unchanged)', 6760.0),
    ('less driveway / sidewalk area counted twice', -OVERLAP_SF),
]
IMP_SF = sum(v for _, v in IMP)
IMP_PCT = 100.0 * IMP_SF / GIS_SF
WQV_CF = 1.2 * (0.05 + 0.009 * IMP_PCT) / 12.0 * GIS_SF

# --- validation of every fallback lot (re-derived, not asserted)
STREAMS = [[tuple(p) for p in s['stream']] for s in LAYOUT['stream_setbacks']]
CHK = {'area': [], 'width': [], 'depth': [], 'frontage': [], 'stream': [], 'inside': 0}
for s in SLOTS:
    P = lot_poly(s)
    CHK['area'].append(abs(sb.poly_area(P)))
    CHK['width'].append(sb.dist(P[0], P[1]))
    CHK['depth'].append(min(sb.dist(P[1], P[2]), sb.dist(P[3], P[0])))
    CHK['frontage'].append(sb.dist(P[2], P[3]))
    CHK['stream'].append(min(poly_path_dist(P, st) for st in STREAMS))
    CHK['inside'] += all(sb.point_in_poly(q, sb.BOUNDARY) for q in P)
LOT_MIN_SF, LOT_MAX_SF = min(CHK['area']), max(CHK['area'])
STREAM_MIN = min(CHK['stream'])

# --- how close do the unchanged amenity improvements come to the new buffer tract?
AMEN = LAYOUT['amenity']
AMEN_POLYS = ([AMEN['clubhouse'], AMEN['mail_kiosk'], AMEN['parking_bay'], AMEN['kiosk_bay'], AMEN['entry_sign']]
              + AMEN['pickleball'])
AMEN_TO_BUF = min(min(poly_path_dist([tuple(q) for q in p], INNER_SW),
                      poly_path_dist([tuple(q) for q in p], INNER_NE)) for p in AMEN_POLYS)

TRACT_MIN = min(tract_w(u) for u in frange(U_LOT0, U_PAVE_END, 5.0))
TRACT_MAX = max(tract_w(u) for u in frange(U_LOT0, U_PAVE_END, 5.0))
SHIFT_MAX = max(extra(u) for u in frange(U_LOT0, U_PAVE_END, 5.0))
NE_HALF_MIN = min(lot_line_ne(u) - cl(u) for u in frange(U_LOT0, U_PAVE_END, 5.0))
SW_HALF_MIN = min(cl(u) - lot_line_sw(u) for u in frange(U_LOT0, U_PAVE_END, 5.0))
W_AT_LOT0, W_AT_REAR = sb.width(U_LOT0), sb.width(sb.U_REAR - 1.0)
BASIS_82 = (W_AT_LOT0 - 2 * BUF_W - MIN_TRACT) / 2.0


# ============================================================================ plan layers
def buffer_tracts(c, labels=True):
    c.add('<g id="buffer-tracts">')
    c.poly(BUFFER_TRACT, fill='url(#bufhatch)', stroke='#4a7a2a', stroke_width=1.0)
    c.pline(BUF_INNER, fill='none', stroke='#4a7a2a', stroke_width=1.0)
    c.add('</g>')
    if not labels:
        return
    for u, v, t, rot in ((980.0, -224.0, "TRACT B-2 — 20'-0\" UNDISTURBED BUFFER (HOA) — %s LF" % format(round(LEG_SW_FT), ','), 0),
                         (700.0, -6.0, "TRACT B-1 — 20'-0\" UNDISTURBED BUFFER (HOA) — %s LF" % format(round(LEG_NE_FT), ','), 0),
                         (1712.0, -120.0, "TRACT B-3 — 20'-0\" BUFFER — %d LF" % round(LEG_REAR_FT), 90)):
        c.text(u, v, t, size=6.5, bold=True, fill='#2f5d17', halo=True, rot=rot)


def lane_fb(c, labels=True):
    c.add('<g id="lane-fallback">')
    c.poly(LANE_TRACT, fill=sb.C['tract'], stroke='#666', stroke_width=0.5, stroke_dasharray='4 2')
    c.poly([tuple(p) for p in ENTRY['tract_polygon']], fill=sb.C['tract'], stroke='#666',
           stroke_width=0.5, stroke_dasharray='4 2')
    c.poly([tuple(p) for p in ENTRY['pavement_polygon']], fill=sb.C['pave'], stroke='#333', stroke_width=0.7)
    c.poly([tuple(p) for p in ENTRY['sidewalk_polygon']], fill='#f7f7f7', stroke='#777', stroke_width=0.35)
    for leg in HH_LEGS:
        c.poly(leg, fill=sb.C['pave'], stroke='#333', stroke_width=0.7)
    c.poly(PAVEMENT, fill=sb.C['pave'], stroke='#333', stroke_width=0.7)
    c.poly(WALK_NE, fill='#f7f7f7', stroke='#777', stroke_width=0.35)
    c.poly(WALK_SW, fill='#f7f7f7', stroke='#777', stroke_width=0.35)
    c.pline([(u, cl(u)) for u in frange(U_JOIN, U_PAVE_END, 10.0)], fill='none', stroke='#444',
            stroke_width=0.4, stroke_dasharray='12 3 2 3')
    c.add('</g>')
    if labels:
        c.text(880.0, cl(880.0) + 4.0, "PRIVATE LANE — HOA TRACT %s–%s (SHEET C-2.0: 35'-11\"–46'-1\") — "
               "22'-0\" PVMT + 2'-0\" STRIP + 5'-0\" WALK" % (fti(TRACT_MIN), fti(TRACT_MAX)),
               size=6.5, bold=True, halo=True)
        c.text(1105.0, -55.0, 'POCKET GREEN', size=6.5, bold=True, fill='#2e5e1e', rot=-90, halo=True)
        c.text(574.0, -200.0, 'POCKET GREEN', size=6.5, bold=True, fill='#2e5e1e', rot=-90, halo=True)


def lots_fb(c, labels=True):
    c.add('<g id="lots-fallback">')
    for s in SLOTS:
        c.poly(lot_poly(s), fill='#fff', stroke='#222', stroke_width=0.6)
        c.poly(lot_rect(s, SIDE_SB, FRONT_SB, LOT_W - SIDE_SB, Y_BACK), fill='none', stroke='#999',
               stroke_width=0.3, stroke_dasharray='2 1.5')
        um = (s['u0'] + s['u1']) / 2.0
        apron = -max(0.0, ((cl(um) - lot_line_sw(um)) if s['side'] == 'SW' else (lot_line_ne(um) - cl(um)))
                     - PAVE_W / 2.0)
        c.poly(lot_rect(s, X0 + 0.5, apron, X0 + 0.5 + DRIVE_W, Y_GAR), fill='#e2e2e2', stroke='#777',
               stroke_width=0.35)
        c.poly([lot_xy(s, p[0], p[1]) for p in COND_L], fill=sb.C['house'], stroke='#222', stroke_width=0.6)
        c.poly(lot_rect(s, X0, Y_GAR, X_GAR1, Y_REAR_BLOCK), fill='#efd2ad', stroke='#222', stroke_width=0.45)
        c.poly(lot_rect(s, X_GAR1, Y_PORCH, X1, Y_BODY), fill='#fdf3e4', stroke='#222', stroke_width=0.4)
    c.add('</g>')
    if not labels:
        return
    for s in SLOTS:
        # three lines run down the sheet, so start them at the end of the rear block that is
        # uppermost on the sheet: the rear line for an NE lot, the front of the block for an SW lot
        y_anchor = (Y_BACK - 3.0) if s['side'] == 'NE' else (Y_REAR_BLOCK + 3.0)
        p = lot_xy(s, LOT_W / 2.0, y_anchor)
        c.textlines(p[0], p[1] + 2.0, ['LOT %d' % s['id'], 'PLAN C', '4,100 SF'],
                    size=6.5, gap=1.15, bold_first=True)


def dim_v(c, u, v0, v1, txt, dx=-7.0, size=6.5, tick=3.0, color='#000'):
    """Dimension across the strip at station u, label reading bottom-up."""
    c.line((u, v0), (u, v1), stroke=color, stroke_width=0.5)
    for v in (v0, v1):
        c.line((u - tick, v), (u + tick, v), stroke=color, stroke_width=0.7)
    c.text(u + dx, (v0 + v1) / 2.0, txt, size=size, rot=-90, fill=color, halo=True)


def dim_u(c, v, u0, u1, txt, dy=-4.0, size=6.5, tick=3.0, color='#000'):
    c.line((u0, v), (u1, v), stroke=color, stroke_width=0.5)
    for u in (u0, u1):
        c.line((u, v - tick), (u, v + tick), stroke=color, stroke_width=0.7)
    c.text((u0 + u1) / 2.0, v, txt, size=size, fill=color, halo=True, dy=dy)


U_SEC = 565.0                                    # the cross-section station (clear of every lot)
KEYS = [
    ('a', 645.0, 92.0, (U_SEC, sb.NE(U_SEC)), "EXCEPTIONAL NARROWNESS — 234.70' AT ARCADO RD, 246.38' AT THE "
     "REAR LINE, AGAINST 1,721.68'–1,757.01' OF DEPTH"),
    ('c', 100.0, 92.0, (300.0, sb.NE(300.0)), 'NOT SELF-CREATED — FOUR PARCELS OF RECORD, LAND LOT 123'),
    ('d', 1150.0, 92.0, (1210.0, sb.NE(1210.0) - 20.0), 'RIGHTS COMMONLY ENJOYED — WITHOUT DEPTH RELIEF THE R-2 '
     'COTTAGE STANDARD CANNOT BE USED HERE AT ANY DENSITY'),
    ('e', 100.0, 148.0, (330.0, sb.NE(330.0) - 20.0), 'MINIMUM RELIEF — 82\'-0" IS ARITHMETIC: '
     '(235.88 − 40.00 − 31.00) ÷ 2 = 82.44\' AT THE FIRST LOT ROW; NOTHING ELSE IS ASKED'),
    ('f', 1150.0, 148.0, (1290.0, sb.NE(1290.0) - 10.0), 'NO DETRIMENT — THE 20-FT BUFFER BECOMES AN HOA TRACT: '
     'WIDER PROTECTION FOR THE R-1 NEIGHBOURS, NOT LESS'),
    ('b', 1120.0, -300.0, (1330.0, -238.0), 'EXTRAORDINARY PHYSICAL CONDITIONS — STATE-WATERS HEADWATER 30 FT INSIDE '
     'THE SW LINE, WITH 50\'/75\' BUFFERS'),
    ('g', 290.0, -300.0, (430.0, sb.SW(430.0) + 10.0), 'NOT FOR GAIN — THE VARIANCE BUYS NO ADDITIONAL LOTS: '
     '41 LOTS AND 4.34 du/ac EITHER WAY'),
]


def annotations(c):
    v_sw, v_ne = sb.SW(U_SEC), sb.NE(U_SEC)
    stations = [v_sw, buf_sw(U_SEC), lot_line_sw(U_SEC), cl(U_SEC) - PAVE_W / 2,
                cl(U_SEC) + PAVE_W / 2, lot_line_ne(U_SEC), buf_ne(U_SEC), v_ne]
    labels = ["20'-0\" BUFFER TRACT", "82'-0\" LOT", "%s" % fti(cl(U_SEC) - PAVE_W / 2 - lot_line_sw(U_SEC)),
              "22'-0\"", "%s" % fti(lot_line_ne(U_SEC) - cl(U_SEC) - PAVE_W / 2), "82'-0\" LOT",
              "20'-0\" BUFFER TRACT"]
    c.line((U_SEC, v_sw), (U_SEC, v_ne), stroke='#000', stroke_width=0.5)
    for v in stations:
        c.line((U_SEC - 3.0, v), (U_SEC + 3.0, v), stroke='#000', stroke_width=0.7)
    for i, t in enumerate(labels):
        # the three lane segments are short: label them on the other side of the dimension line
        dx = 6.0 if 2 <= i <= 4 else -7.0
        c.text(U_SEC + dx, (stations[i] + stations[i + 1]) / 2.0, t, size=(5.8 if 2 <= i <= 4 else 6.5),
               rot=-90, halo=True, anchor='middle')
    c.text(U_SEC, 26.0, "TYPICAL CROSS-SECTION AT u = 565 — %s OVERALL" % fti(v_ne - v_sw),
           size=7, bold=True, halo=True)
    dim_v(c, U_LOT0 - 6.0, sb.SW(U_LOT0), sb.NE(U_LOT0),
          "%s AT THE FIRST LOT — NARROWEST" % fti(W_AT_LOT0), dx=-8.0, color='#b00')
    v_r0, v_r1 = sb.SW(sb.U_REAR - 1.0), sb.NE(sb.U_REAR - 1.0)
    for v in (v_r0, v_r1):                                     # extension lines out to the offset dimension
        c.line((sb.U_REAR + 2.0, v), (1744.0, v), stroke='#000', stroke_width=0.35)
    dim_v(c, 1746.0, v_r0, v_r1, "%s AT THE REAR LINE" % fti(W_AT_REAR), dx=-8.0)
    dim_u(c, sb.NE(900.0) + 44.0, U_JOIN, U_PAVE_END, "PRIVATE LANE — %s FT OF TRAVELLED WAY FROM THE ARCADO RD "
          "RIGHT-OF-WAY, ENDING IN A HAMMERHEAD TURNAROUND (UNCHANGED FROM SHEET C-2.0)"
          % format(M['longest_dead_end_ft'], ',.0f'), dy=-4.0)

    c.line((U_SWWALK, cl(U_SWWALK) - 13.0), (1080.0, -296.0), stroke='#333', stroke_width=0.5)
    c.text(1076.0, -300.0, "SECOND (SW) SIDEWALK BEGINS AT u = %d — WHERE THE LANE TRACT REACHES 36'-0\" "
           "(SHEET C-2.0: u = 530)" % round(U_SWWALK), size=6.5, fill='#333', halo=True, anchor='end')
    c.text(60.0, -254.0, "EXISTING 8-in SANITARY SEWER AND ITS 20' EASEMENT LIE INSIDE THE SW BUFFER TRACT FOR "
           "≈ 300 FT — SEE GENERAL NOTE 8", size=6.5, fill=sb.C['sewer_txt'], halo=True, anchor='start')
    c.text(900.0, 214.0, 'ADJOINING PROPERTY — 31 PARCELS, EVERY ONE ZONED R-1, CITY OF LILBURN. PINs, ADDRESSES AND '
           'OWNERS ARE SCHEDULED ON SHEET C-0 (EXISTING CONDITIONS).', size=8, bold=True, fill='#555')
    c.text(900.0, 202.0, 'THE ASSEMBLAGE BOUNDARY, THE FOUR PARCELS TO BE COMBINED AND THE EXISTING IMPROVEMENTS TO BE '
           'REMOVED ARE SHOWN ON SHEET C-0. ONLY THE FALLBACK LAYOUT IS SHOWN HERE.', size=6.5, fill='#555')
    c.text(1500.0, -404.0, 'THE ENTRANCE, THE ENTRY DRIVE, THE LANE ALIGNMENT AND LENGTH, THE HAMMERHEADS, THE AMENITY '
           'BLOCK, BOTH PONDS, THE GREENS, THE CREEK WOODS AND THE PHASE LINE ARE UNCHANGED FROM SHEET C-2.0.',
           size=7, bold=True, fill='#7b1fa2', anchor='end')
    c.text(1500.0, -416.0, 'ONLY THE LOT DEPTH, THE BUFFER TENURE, THE LANE-TRACT WIDTH, THE SECOND SIDEWALK AND THE '
           'HOUSE PLAN CHANGE. LOT COUNT AND DENSITY DO NOT CHANGE.', size=7, fill='#7b1fa2', anchor='end')

    for k, ku, kv, tgt, txt in KEYS:
        c.line((ku, kv), tgt, stroke='#b00', stroke_width=0.5)
        c.circle((ku, kv), 6.5, fill='#fff', stroke='#b00', stroke_width=0.9)
        c.text(ku, kv, k, size=8, bold=True, fill='#b00', dy=3.0)
        c.text(ku + 10.0, kv, '§1005-3.2(%s)  %s' % (k, txt), size=6.5, anchor='start', halo=True, fill='#b00', dy=2.5)


# ============================================================================ details
def _dimline(c, x, y0, y1, txt, size=6.2, tick=2.0, color='#000', bold=False, vertical=True, off=1.6):
    """A single dimension in detail coordinates: line + ticks + label reading along it."""
    if vertical:
        c.line((x, y0), (x, y1), stroke=color, stroke_width=0.5)
        for yv in (y0, y1):
            c.line((x - tick, yv), (x + tick, yv), stroke=color, stroke_width=0.7)
        c.text(x - off, (y0 + y1) / 2.0, txt, size=size, rot=-90, fill=color, bold=bold, halo=True)
    else:
        c.line((y0, x), (y1, x), stroke=color, stroke_width=0.5)
        for xv in (y0, y1):
            c.line((xv, x - tick), (xv, x + tick), stroke=color, stroke_width=0.7)
        c.text((y0 + y1) / 2.0, x, txt, size=size, fill=color, bold=bold, halo=True, dy=-2.4)


def detail_typical_lot(D, x, y, scale=72.0 / 20.0):
    """Typical fallback lot at 1" = 20': buffer tract, 82-ft lot, setbacks, Plan C, lane section.
    Detail coordinates: x across the lot frontage, y into the lot from the front (lane) lot line, so
    the lane is at the bottom of the detail and the adjoining R-1 property at the top."""
    win = (-11.0, 60.0, -21.0, 111.0)
    sub = sb.Drawing(scale, x, y, win=win)
    sub.srect(sub.X(win[0]), sub.Y(win[3]), (win[1] - win[0]) * scale, (win[3] - win[2]) * scale,
              fill='#fff', stroke='none')
    # lane section below the front lot line
    sub.poly(sb.rect(win[0], win[1], -18.0, -7.0), fill=sb.C['pave'], stroke='#333', stroke_width=0.7)
    sub.poly(sb.rect(win[0], win[1], -5.0, 0.0), fill='#f7f7f7', stroke='#777', stroke_width=0.4)
    sub.line((win[0], -18.0), (win[1], -18.0), stroke='#444', stroke_width=0.6, stroke_dasharray='10 3 2 3')
    # lot, buffer tract, property line
    sub.poly(sb.rect(0.0, LOT_W, 0.0, LOT_D), fill='#fff', stroke='#222', stroke_width=1.4)
    sub.poly(sb.rect(win[0], win[1], LOT_D, LOT_D + BUF_W), fill='url(#bufhatch)', stroke='#4a7a2a',
             stroke_width=1.0)
    sub.line((win[0], LOT_D + BUF_W), (win[1], LOT_D + BUF_W), stroke='#000', stroke_width=2.0)
    sub.poly(sb.rect(SIDE_SB, LOT_W - SIDE_SB, FRONT_SB, Y_BACK), fill='none', stroke='#999',
             stroke_width=0.6, stroke_dasharray='4 2')
    # Plan C on the lot
    sub.poly(sb.rect(X0 + 0.5, X0 + 0.5 + DRIVE_W, -7.0, Y_GAR), fill='#e2e2e2', stroke='#777', stroke_width=0.5)
    sub.poly(COND_L, fill=sb.C['house'], stroke='#222', stroke_width=1.0)
    sub.poly(sb.rect(X0, X_GAR1, Y_GAR, Y_REAR_BLOCK), fill='#efd2ad', stroke='#222', stroke_width=0.8)
    sub.poly(sb.rect(X_GAR1, X1, Y_PORCH, Y_BODY), fill='#fdf3e4', stroke='#222', stroke_width=0.7)
    sub.poly(sb.rect(19.0, 19.0 + PATIO_W, Y_BACK, Y_BACK + PATIO_D), fill='none', stroke='#888',
             stroke_width=0.6, stroke_dasharray='3 2')
    # labels
    sub.text(25.0, Y_BACK + 2.5, 'OPTIONAL UNCOVERED PATIO — VERIFY', size=5.8, fill='#666')
    sub.text(X_GAR1 + 8.5, Y_REAR_BLOCK + 8.0, 'PLAN C', size=8.0, bold=True)
    sub.text(X_GAR1 + 8.5, Y_REAR_BLOCK + 2.5, 'SCHEMATIC', size=6.2, fill='#b00')
    sub.text(X0 + 10.5, Y_GAR + 11.5, 'GARAGE', size=6.2)
    sub.text(X0 + 10.5, Y_GAR + 6.5, "21' × 21'", size=6.2)
    sub.text(X_GAR1 + 8.5, Y_PORCH + 2.0, 'PORCH', size=6.0)
    sub.text(X0 + 10.5, 7.0, 'DRIVEWAY', size=6.2)
    sub.text(X0 + 10.5, 2.0, "20' × 26'", size=6.0)
    sub.text(LOT_W / 2.0, LOT_D + 8.5, "TRACT B — 20'-0\" UNDISTURBED BUFFER (HOA)", size=6.5, bold=True,
             fill='#2f5d17')
    sub.text(LOT_W / 2.0, LOT_D + BUF_W + 4.5, 'ADJOINING PROPERTY — ZONED R-1', size=6.5, bold=True, fill='#444')
    sub.text(LOT_W / 2.0, -12.5, "22'-0\" PRIVATE LANE PAVEMENT", size=6.5, bold=True)
    sub.text(LOT_W / 2.0, -3.0, "5'-0\" WALK + 2'-0\" STRIP", size=6.0)
    # dimension strings — left: the depth chain; right: the 82-ft variance dimension
    for a, b, t in ((0.0, FRONT_SB, "15'-0\""), (FRONT_SB, Y_BACK, "47'-0\" BUILDABLE"),
                    (Y_BACK, LOT_D, "20'-0\""), (LOT_D, LOT_D + BUF_W, "20'-0\" BUFFER")):
        _dimline(sub, -4.0, a, b, t)
    _dimline(sub, 54.0, 0.0, LOT_D, "82'-0\" LOT DEPTH — §1005 VARIANCE (100'-0\" REQUIRED)",
             size=6.5, color='#b00', bold=True, off=-3.2)
    _dimline(sub, 74.0, 0.0, LOT_W, "50'-0\" LOT WIDTH — 4,100 SF", size=6.5, bold=True, vertical=False)
    _dimline(sub, 55.0, 0.0, X0, "6'", size=5.8, vertical=False)
    _dimline(sub, 55.0, X1, LOT_W, "6'", size=5.8, vertical=False)
    D.add(sub.render())
    return sub


def detail_plan_c(D, x, y, scale=72.0 * 3.0 / 32.0):
    """Plan C schematic footprint at 3/32" = 1'-0".  Detail coordinates follow data/plans.json:
    x across the front, y from the front wall of the dwelling toward the rear, so on the sheet the
    porch and the lane are at the bottom and the rear wall at the top."""
    win = (-9.0, 47.0, -15.0, 51.0)
    sub = sb.Drawing(scale, x, y, win=win)
    sub.srect(sub.X(win[0]), sub.Y(win[3]), (win[1] - win[0]) * scale, (win[3] - win[2]) * scale,
              fill='#fff', stroke='none')
    sub.poly(sb.rect(0.0, BODY_W, 0.0, BODY_D), fill='none', stroke='#bbb', stroke_width=0.5,
             stroke_dasharray='4 3')
    sub.poly([(GAR_W, 0.0), (BODY_W, 0.0), (BODY_W, BODY_D), (0.0, BODY_D), (0.0, GAR_RECESS + GAR_D),
              (GAR_W, GAR_RECESS + GAR_D)], fill=sb.C['house'], stroke='#222', stroke_width=1.6)
    sub.poly(sb.rect(0.0, GAR_W, GAR_RECESS, GAR_RECESS + GAR_D), fill='#efd2ad', stroke='#222', stroke_width=1.0)
    sub.poly(sb.rect(GAR_W, BODY_W, -PORCH_D, 0.0), fill='#fdf3e4', stroke='#222', stroke_width=0.9)
    for a, b in (((0.0, GAR_RECESS + GAR_D), (BODY_W, GAR_RECESS + GAR_D)),
                 ((22.0, GAR_RECESS + GAR_D), (22.0, BODY_D)), ((30.0, GAR_RECESS + GAR_D), (30.0, BODY_D)),
                 ((GAR_W, 12.0), (BODY_W, 12.0))):
        sub.line(a, b, stroke='#888', stroke_width=0.5, stroke_dasharray='4 2')
    for xv, yv, t, sz in ((10.5, 17.5, '2-CAR GARAGE', 7.0), (10.5, 13.5, "21'-0\" × 21'-0\"", 6.2),
                          (29.5, 20.5, 'KITCHEN /', 6.5), (29.5, 17.0, 'DINING', 6.5),
                          (29.5, 6.0, 'LIVING', 6.5), (11.0, 36.0, 'BEDROOM 1', 6.5), (11.0, 32.5, '+ BATH 1', 6.5),
                          (26.0, 36.0, 'BATH 2 /', 6.0), (26.0, 32.5, 'LAUNDRY', 6.0),
                          (34.0, 36.0, 'BED 2 /', 6.0), (34.0, 32.5, 'DEN', 6.0),
                          (29.5, -3.5, "COVERED PORCH 6'-0\"", 6.2)):
        sub.text(xv, yv, t, size=sz)
    sub.text(BODY_W / 2.0, -11.0, 'FRONT (LANE SIDE) — ZERO-STEP ENTRY', size=6.5, bold=True)
    sub.text(BODY_W / 2.0, 47.5, 'REAR — 20\'-0" REAR YARD BEYOND', size=6.2, fill='#444')
    _dimline(sub, -4.0, 0.0, BODY_D, "41'-0\" BODY DEPTH", size=6.5, bold=True)
    _dimline(sub, -4.0, -PORCH_D, 0.0, "6'-0\"", size=6.0)
    sub.line((0.0, 0.0), (GAR_W, 0.0), stroke='#b00', stroke_width=0.5, stroke_dasharray='4 2')
    _dimline(sub, 10.5, 0.0, GAR_RECESS, "5'-0\" GARAGE RECESS", size=5.8, color='#b00', off=-7.0)
    _dimline(sub, 44.0, 0.0, GAR_W, "21'-0\"", size=6.0, vertical=False)
    _dimline(sub, 44.0, GAR_W, BODY_W, "17'-0\"", size=6.0, vertical=False)
    _dimline(sub, -8.0, 0.0, BODY_W, "38'-0\" BODY WIDTH", size=6.5, bold=True, vertical=False)
    D.add(sub.render())
    return sub


# ============================================================================ band content
def comparison_rows():
    return [
        ['Buffer against R-1', "20'-0\" undisturbed buffer inside the rear 20 ft of every perimeter lot, in a "
         "recorded buffer easement (§313(1) reading)", "20'-0\" undisturbed buffer in separate HOA-owned Tracts "
         "B-1 / B-2 / B-3 — %s SF" % format(round(BUFFER_SF), ',')],
        ['Typical lot', "50'-0\" × 100'-0\" = 5,000 SF", "50'-0\" × 82'-0\" = 4,100 SF"],
        ['Table 4.1 lot area (3,000 SF min.)', '5,000 SF — appears consistent', '4,100 SF — appears consistent'],
        ['Table 4.1 lot width (50 ft min.)', "50'-0\" — appears consistent", "50'-0\" — appears consistent"],
        ['Table 4.1 lot depth (100 ft min.)', "100'-0\" — appears consistent", "82'-0\" — VARIANCE REQUIRED (§1005)"],
        ['Lots', '41 (14 SW + 27 NE)', '%d (14 SW + 27 NE) — unchanged' % N_LOTS],
        ['Density (8 du/ac max.)', '4.34 du/ac deeded / 4.28 GIS', '%.2f du/ac deeded / %.2f GIS — unchanged'
         % (DENS_DEEDED, DENS_GIS)],
        ['Buildable body depth', "100 − 15 − 20 = 65'-0\" less the 6-ft porch = 59'-0\"",
         "82 − 15 − 20 = 47'-0\" less the 6-ft porch = %s" % fti(BODY_D)],
        ['House plans that fit', "Plan A 38'-0\" × 51'-10\"; Plan B 38'-0\" × 57'-6\"",
         "NEITHER — a third plan is required: Plan C %s × %s" % (fti(BODY_W), fti(BODY_D))],
        ['Conditioned area', '1,406 SF (Plan A) / 1,492 SF (Plan B)', '≈ %s SF (Plan C) — %d SF above the 1,000-SF '
         'Table 4.1 minimum' % (format(round(COND_SF), ','), round(COND_SF - TABLE41_MIN_HEATED))],
        ['Total under roof', '1,966 SF / 2,182 SF', '%s SF' % format(round(ROOF_SF), ',')],
        ['Rear amenity', "Plan A 6'-0\" patio; Plan B 14'×6' covered rear porch",
         "None within the 20-ft rear yard; uncovered patio shown dashed — VERIFY"],
        ['Private lane tract', "35'-11\" – 46'-1\"; 22-ft pavement, symmetrical",
         "%s – %s; 22-ft pavement set %s from the NE tract line" % (fti(TRACT_MIN), fti(TRACT_MAX),
                                                                    fti(HALF_SECTION))],
        ['Second (SW) sidewalk', 'From u = 530 (≈ 1,170 ft)', 'From u = %d (≈ %d ft)'
         % (round(U_SWWALK), round(U_PAVE_END - U_SWWALK))],
        ['Common open space', '141,089 SF = 33.8% of GIS area, plus 41,000 SF of buffer easement on lots reported '
         'separately', '%s SF = %.1f%% of GIS area, including the %s-SF buffer tracts; no buffer easement on any lot'
         % (format(round(OPEN_SF), ','), 100.0 * OPEN_SF / GIS_SF, format(round(BUFFER_SF), ','))],
        ['Impervious area', '184,148 SF = 44.1% of GIS area', '%s SF = %.1f%% of GIS area (Plan C is smaller)'
         % (format(round(IMP_SF), ','), IMP_PCT)],
        ['Water-quality volume WQv', '18,659 cf', '%s cf' % format(round(WQV_CF), ',')],
        ['Disturbed area / detention', '7.54 ac; 75,410 cf required, 77,863 cf provided',
         'Unchanged — the preserved buffer bands and creek woods are identical'],
        ['Fire access', '41 units — under the 120-unit trigger of IFC 2024 (GA) App. D107.1 as amended by Ga. Comp. R. '
         '& Regs. 120-3-3-.04; D103.4 special approval for the dead end', 'Unchanged'],
        ['Sanitary sewer', 'Phase 1 to the existing on-site 8-in main; Phase 2 by the ≈ 178-ft off-site gravity tie',
         'Unchanged'],
        ['Approvals needed', 'Rezoning R-1 → R-2, plus a favourable §313(1) interpretation by the Planning Director',
         'Rezoning R-1 → R-2, plus a concurrent §1005 variance on lot depth decided by Mayor and Council with the '
         'companion application'],
        ['Filing cost', '$1,250 rezoning fee (City of Lilburn FY2026-2027 Fee Schedule, Res. 2026-08, 2026-08-31)',
         '$1,250 + $500 variance hearing fee (+$25 for each additional variance on the same property) — confirm the '
         'adopted amounts at filing'],
        ['Principal risk', 'The §313(1) reading may be rejected: Article 3 sets no buffer widths and the ordinance '
         'nowhere authorises a required buffer inside a private lot', 'A variance is discretionary; the applicant must '
         'carry every §1005-3.2 criterion at the hearing'],
    ]


def criteria_rows():
    return [
        ['a', 'Exceptional narrowness, shallowness, size or shape of the property',
         'The assemblage is a strip %s wide at the Arcado Rd right-of-way, %s at the first lot row (u = 230) and %s '
         'at the rear line, against %s of depth on the SW line and %s on the NE line — about 7.3 : 1. Take a 20-ft '
         'buffer tract off each side (40 ft) and the 31-ft minimum private-lane section that City of Lilburn Site '
         'Development Plan Review Checklist §4.s ("all components of private streets ... must meet minimum standards '
         'for public street") requires, and %s of width is left for two facing rows of lots — %s each. No arrangement '
         'of a 100-ft-deep lot fits.'
         % (fti(sb.width(0.0)), fti(W_AT_LOT0), fti(W_AT_REAR), "1,757'-0\"", "1,721'-8\"",
            fti(W_AT_LOT0 - 2 * BUF_W - MIN_TRACT), fti(BASIS_82))],
        ['b', 'Extraordinary and exceptional physical conditions',
         'An unnamed order-0 headwater of Jackson Creek (state waters) reaches about 30 ft inside the SW line and '
         'carries 25-ft state, 50-ft undisturbed and 75-ft impervious setbacks; a ridge at u 1,080–1,200 divides the '
         'sanitary basins; the only public frontage is 237.63 ft of Arcado Rd, a county collector on which no lot may '
         'be driveway-served. The developable envelope is fixed before any lot is drawn.'],
        ['c', 'The condition is not the result of any action by the applicant',
         'The four parcels (PINs R6123 033, 015, 014 and 162) and the strip geometry are of record in Land Lot 123, '
         '6th District; King David Manor (plat S/159) and Legends at Parkview (plat 118/187) were platted around them. '
         'The applicant has subdivided, conveyed or reconfigured nothing that created the narrowness.'],
        ['d', 'Strict application deprives the owner of rights commonly enjoyed by other property in the district',
         'R-2 lists "Single-family (cluster-cottage, creative lot configuration)" as a permitted use (§602) and sets a '
         '3,000-SF, 50-ft cottage lot in Table 4.1. If the buffer must sit in its own tract, the 100-ft depth rule '
         'makes that permitted use unbuildable here at any density — the district standard the property is being '
         'rezoned to use cannot be used.'],
        ['e', 'The variance requested is the minimum necessary',
         'Relief is 18 ft of depth (100 ft → 82 ft, 18%%), and 82 ft is arithmetic, not preference: '
         '(%.2f − 2 × 20.00 − 31.00) ÷ 2 = %.2f ft. Nothing else is asked: lot area 4,100 SF (min. 3,000), lot width '
         '50 ft (min. 50), density %.2f du/ac (max. 8), front 15 ft, side 5 ft, rear 20 ft, height one storey, buffer '
         '20 ft — every one met as drawn.' % (W_AT_LOT0, BASIS_82, DENS_DEEDED)],
        ['f', 'Relief may be granted without substantial detriment to the public good and without impairing the '
         'purposes and intent of the ordinance',
         'The variance moves protection outward, not inward: the 20-ft buffer stops being a private easement inside a '
         'back yard and becomes %s SF of HOA-owned undisturbed tract, shown on the plat with a no-disturbance '
         'restriction and a maintenance obligation (Checklist §4.o, §6.b). Common open space rises from 33.8%% to '
         '%.1f%% of the site and impervious area falls to %.1f%%. Density, use, height, setbacks and the 55+ (HOPA) '
         'condition are unchanged.' % (format(round(BUFFER_SF), ','), 100.0 * OPEN_SF / GIS_SF, IMP_PCT)],
        ['g', 'The relief sought is not merely for financial advantage',
         'The variance yields no additional lots and no additional density: %d lots and %.2f du/ac either way. Its '
         'only effect is to let the required buffer be held in the separate tract staff may require, at the cost of '
         '900 SF of private lot area per home and a smaller house. The applicant would prefer the §313(1) reading and '
         'no variance at all.' % (N_LOTS, DENS_DEEDED)],
    ]


def area_rows():
    return [
        ['Gross site area', '%s SF = %.3f ac (GIS); 9.44 ac deeded' % (format(round(GIS_SF), ','), GIS_SF / 43560.0),
         'data/layout.json boundary_ring; RLS survey governs'],
        ['Lots', '%d × 4,100 SF = %s SF (%.1f%%)' % (N_LOTS, format(round(LOTS_SF), ','), 100.0 * LOTS_SF / GIS_SF),
         "50'-0\" × 82'-0\", computed lot by lot (%s–%s SF)" % (format(round(LOT_MIN_SF), ','),
                                                                format(round(LOT_MAX_SF), ','))],
        ['Private lane tract', '%s SF' % format(round(LANE_TRACT_SF), ','),
         'Residual between the two lot rows, %s–%s' % (fti(TRACT_MIN), fti(TRACT_MAX))],
        ['Entry drive tract', '%s SF' % format(round(ENTRY_TRACT_SF), ','), 'Unchanged from Sheet C-2.0'],
        ['Common open space (all HOA tracts)', '%s SF = %.2f ac = %.1f%% of GIS / %.1f%% of deeded'
         % (format(round(OPEN_SF), ','), OPEN_SF / 43560.0, 100.0 * OPEN_SF / GIS_SF, 100.0 * OPEN_SF / DEEDED_SF),
         'Residual: site less lots less the lane and entry-drive tracts'],
        ['— of which perimeter buffer tracts', '%s SF (B-1 NE %s LF, B-2 SW %s LF, B-3 rear %d LF)'
         % (format(round(BUFFER_SF), ','), format(round(LEG_NE_FT), ','), format(round(LEG_SW_FT), ','),
            round(LEG_REAR_FT)), "20'-0\" mitred inward offset of the side and rear property lines"],
        ['— of which amenity, greens, ponds, creek woods', '%s SF' % format(round(OPEN_SF - BUFFER_SF), ','),
         'Unchanged tracts of Sheet C-2.0, less the area now inside the buffer tracts'],
        ['Buffer easement on lots', '0 SF (Sheet C-2.0: 41,000 SF)', 'The point of this sheet'],
        ['Impervious area', '%s SF = %.1f%% of GIS area' % (format(round(IMP_SF), ','), IMP_PCT),
         'Computed from the Plan C footprint and the drawn pavement — see the impervious schedule'],
        ['Water-quality volume WQv', '%s cf' % format(round(WQV_CF), ','),
         'GCSWMM: 1.2 × (0.05 + 0.009 × %.1f) ÷ 12 × %s SF' % (IMP_PCT, format(round(GIS_SF), ','))],
        ['Detention required / provided', '75,410 cf / 77,863 cf', 'Unchanged — 7.54 disturbed ac at 10,000 cf/ac '
         '(GCSWMM); both ponds unchanged'],
        ['Parking', '%d required, %d on lot + 12 guest' % (2 * N_LOTS, 4 * N_LOTS),
         'Table 8.1: 2 per dwelling unit; 2 garage + 2 driveway per lot'],
        ['Lot frontage on the lane', "50'-0\" every lot (30 ft required)", 'Ord. 2023-603 §319'],
        ['Clearance, lots to the stream centreline', '%.1f ft minimum (Sheet C-2.0: %.1f ft)'
         % (STREAM_MIN, M['stream_clearances_ft']['nearest_lot_ft']),
         'All three digitised reaches; top of bank not yet delineated'],
    ]


LEGEND = [
    ('line', sb.C['bnd'], 1.8, '', 'Assemblage boundary (GIS — DRAFT)'),
    ('rect', sb.C['adj_fill'], 0, '', 'Adjoining tax parcel — zoned R-1'),
    ('line', sb.C['rw'], 0.9, '', 'Arcado Rd right-of-way line'),
    ('line', '#333', 0.6, '14 3 3 3', 'Existing road centreline'),
    ('rect', 'url(#bufhatch)', 0, '', "20'-0\" perimeter buffer tract (HOA)"),
    ('line', '#222', 0.8, '', "Fallback lot line — 50' × 82' = 4,100 SF"),
    ('line', '#999', 0.5, '2 1.5', 'Building setback line 15 / 5 / 20'),
    ('rect', sb.C['house'], 0, '', 'Plan C dwelling — SCHEMATIC'),
    ('rect', '#efd2ad', 0, '', "2-car garage, recessed 5'-0\""),
    ('rect', '#fdf3e4', 0, '', "Covered front porch 6'-0\""),
    ('rect', '#e2e2e2', 0, '', "Driveway 20'-0\" × 26'-0\""),
    ('rect', sb.C['tract'], 0, '', 'Private lane / entry drive tract (HOA)'),
    ('rect', sb.C['pave'], 0, '', 'Pavement and hammerhead turnaround'),
    ('line', '#555', 0.4, '', "Guest / mail-kiosk parking stall 9' × 18'"),
    ('rect', '#f7f7f7', 0, '', "Sidewalk 5'-0\""),
    ('line', '#444', 0.4, '12 3 2 3', 'Lane centreline (fallback alignment)'),
    ('rect', sb.C['green'], 0, '', 'Pocket / terminus green (unchanged)'),
    ('rect', '#eef4e6', 0, '', 'Front amenity tract (unchanged)'),
    ('rect', '#cfe8bd', 0, '', 'Village green (unchanged)'),
    ('rect', '#f2c58a', 0, '', 'Clubhouse and mail kiosk (unchanged)'),
    ('rect', '#e9e2d0', 0, '', 'Pickleball pad (unchanged)'),
    ('rect', '#bcd7c2', 0, '', 'Pickleball court surface (unchanged)'),
    ('rect', '#333', 0, '', 'Monument entry sign (unchanged)'),
    ('rect', '#e4efdc', 0, '', 'Stormwater pond tract (unchanged)'),
    ('rect', sb.C['pond'], 0, '', 'Dry detention / WQ basin (unchanged)'),
    ('line', sb.C['stream'], 1.6, '', 'Stream — state waters (top of bank approx.)'),
    ('line', sb.C['buf_line'], 0.5, '3 2', "25' state (GA EPD) buffer"),
    ('line', sb.C['buf_line'], 0.8, '6 2', "50' undisturbed stream buffer"),
    ('line', sb.C['buf_line'], 0.8, '8 2 2 2', "75' impervious setback"),
    ('line', sb.C['sewer'], 0.9, '', 'Existing 8-in sanitary sewer and manhole'),
    ('rect', 'url(#ssehatch)', 0, '', "Existing 20' sanitary sewer easement"),
    ('key', '#b00', 0, '', '§1005-3.2 criterion key (a) – (g)'),
    ('line', '#000', 0.5, '', 'Dimension line and tick'),
]

NOTES = [
    'STATUS OF THIS SHEET — IT IS NOT THE PROPOSED PLAN. The proposed layout is Sheet C-2.0, on which the 20-ft buffer '
    'required against the abutting R-1 property is held inside the rear 20 ft of each perimeter lot in a recorded '
    'buffer easement, under Lilburn Zoning Ordinance 2023-603 §313(1) ("Buffer requirements ... supersede these '
    'minimum required yards"). This sheet is the alternative that is built if the Planning Director or the City '
    'Attorney reads §313(1) as not authorising a required buffer inside a private lot. Only one of the two layouts '
    'will be constructed; both are shown so the Commission and the Council can price the interpretation before it is '
    'made.',

    'WHY THE FALLBACK IS CARRIED. Two independent readings put the §313(1) basis in doubt. (1) §313(1) speaks of '
    '"buffer requirements established by this article" — Article 3 — and Article 3 fixes no buffer width; the 20-ft '
    'buffer abutting R-1 comes from Table 4.1 in Article 4, and nothing in Ord. 2023-603 expressly authorises holding '
    'a required buffer inside a private lot. (2) The City of Lilburn Site Development Plan Review Checklist §6.c reads '
    '"If a portion of required buffer is within an easement, provide 25\' additional buffer outside easement," which '
    'on its face would add 25 ft outside any buffer easement held on a lot. Both are questions for the '
    'pre-application conference (Planning Director, 340 Main St).',

    'WHAT CHANGES AND WHAT DOES NOT. Changed: lot depth 100\'-0" → 82\'-0"; buffer tenure (easement on lots → HOA '
    'tracts); house plan (Plans A and B → Plan C); private-lane tract width; the station at which the second sidewalk '
    'begins. Unchanged: the boundary, the entrance at v = −190 and its 24-ft entry drive, the lane alignment and its '
    '1,754-ft length, the 22-ft pavement, all three hammerhead turnarounds, the amenity block, both stormwater ponds, '
    'the pocket and terminus greens, the creek-woods tract, the stream setbacks, the phase line at u = 980, the '
    'perimeter buffer WIDTH (20 ft), every setback, the one-storey height, the use, and the 55+ (HOPA) condition. '
    'LOT COUNT AND DENSITY DO NOT CHANGE: %d lots at %.2f du/ac on 9.44 deeded acres, well under the 8 du/ac maximum '
    'of Table 4.1. Yield here is set by frontage on the single lane, not by lot depth — the same %d fifty-foot lots '
    'front the same travelled way in both layouts — so the shallower lot returns 900 SF per lot to common open space '
    'and takes nothing off the unit count.' % (N_LOTS, DENS_DEEDED, N_LOTS),

    'THE VARIANCE REQUESTED. Table 4.1 sets a minimum lot depth of 100 ft for ALL uses in R-2, with no cottage-home '
    'exception, so 82\'-0" requires a variance under Ord. 2023-603 §1005. It would be filed as a CONCURRENT variance '
    'with the rezoning and decided by Mayor and Council with the companion application (§1005-1); no variance may be '
    'approved before the Council\'s final action on the rezoning. NO OTHER RELIEF IS REQUESTED: lot area 4,100 SF '
    '(3,000 SF minimum), lot width 50\'-0" (50 ft minimum), density %.2f du/ac (8 maximum), front setback 15 ft, side '
    '5 ft, rear 20 ft, buffer 20 ft, height one storey — each appears consistent with Table 4.1 as drawn. The '
    'applicant\'s responses to the §1005-3.2 criteria are tabulated at the left and keyed (a) – (g) on the plan.'
    % DENS_DEEDED,

    'THE §1005-3.2 CRITERIA TEXT IS NOT REPRODUCED HERE — VERIFY. The excerpt set the package works from '
    '(data/ordinance-excerpts.md) ends inside §1005-3.1, so the adopted wording of the criteria at §1005-3.2(a) '
    'through (g) has not been transcribed from a primary source. The criterion subjects shown are the standard '
    'Georgia hardship-variance subjects and the letters are placeholders. Before filing, transcribe §1005-3.2(a)–(g) '
    'verbatim from Ord. 2023-603 and conform each response — and its letter — to the adopted text.',

    'THE 82\'-0" DIMENSION IS ARITHMETIC. Width available at the first lot (u = 230) = %.2f ft, less two 20\'-0" '
    'buffer tracts (40.00 ft), less the 31\'-0" minimum private-lane tract (22\'-0" pavement + 2\'-0" strip + 5\'-0" '
    'sidewalk + 2\'-0" strip) = %.2f ft for two facing rows, i.e. %.2f ft each. The lot module is set at 82\'-0" and '
    'the surplus width that the strip picks up toward the rear (it widens to %s) is carried in the lane tract, '
    'exactly as it is on Sheet C-2.0. Lot depth is measured perpendicular to the front lot line; lot area is '
    '4,100 SF on every lot (computed lot by lot: %s – %s SF).'
    % (W_AT_LOT0, W_AT_LOT0 - 2 * BUF_W - MIN_TRACT, BASIS_82, fti(W_AT_REAR),
       format(round(LOT_MIN_SF), ','), format(round(LOT_MAX_SF), ',')),

    'THE THIRD HOUSE PLAN. Body depth available on an 82-ft lot = 82 − 15 (front setback) − 20 (rear setback) = '
    '47\'-0", less the 6\'-0" covered porch = 41\'-0". Plan A "The Springbrook" has a 51\'-10" body and Plan B "The '
    'Laurel" 57\'-6" (data/plans.json), so NEITHER FITS. Plan C is drawn as a SCHEMATIC one-storey 38\'-0" × 41\'-0" '
    'body with the same front-facing gable, an integral 6\'-0" covered porch and a 2-car garage recessed 5\'-0" '
    'behind the front wall (Table 4.2 design criterion): ≈ %s SF conditioned, %s SF garage, %s SF covered porch, '
    '%s SF total under roof. That is %d SF above the 1,000-SF minimum heated floor area for a cottage home in Table '
    '4.1 — about 1%%. Plan C carries no covered rear porch; an at-grade uncovered patio is shown dashed in the 20-ft '
    'rear yard and its permissibility must be confirmed. PLAN C IS A BLOCK DIAGRAM, NOT A DESIGNED PLAN: it is drawn '
    'to prove that a compliant cottage fits, and must be replaced by a Georgia-registered architect\'s drawings.'
    % (format(round(COND_SF), ','), format(round(GAR_SF), ','), format(round(PORCH_SF), ','),
       format(round(ROOF_SF), ','), round(COND_SF - TABLE41_MIN_HEATED)),

    'THE PERIMETER BUFFER TRACTS. Tracts B-1 (NE line, %s LF), B-2 (SW line, %s LF) and B-3 (rear line, %d LF) total '
    '%s SF, are 20\'-0" wide measured perpendicular to the property line, are owned and maintained by the homeowners '
    'association, and are to be shown on the final plat labelled "20\' UNDISTURBED BUFFER" with a no-disturbance '
    'restriction and the HOA maintenance obligation (Checklist §4.o, §6.b). No dwelling, drive or accessory structure '
    'is drawn in them. Two encroachments carried over from Sheet C-2.0 must be disclosed: (i) the existing 8-in '
    'sanitary sewer and its 20-ft easement run inside Tract B-2 for about 300 ft from Arcado Rd to the manhole at '
    '(u 272, v −224) — Checklist §6.f permits sanitary sewer conveyance facilities and easements to encroach a buffer '
    '"as near as perpendicular as possible, up to max 50\' width", which this parallel run does not satisfy, and '
    '§6.c may require 25 ft of additional buffer outside the easement; (ii) the SW curb return at the entrance '
    'reaches %.1f ft into the buffer band (%.1f SF). Both need the Director\'s reading, and (i) exists on Sheet C-2.0 '
    'as well. The SW pickleball pad stands %.1f ft clear of Tract B-2 (%.1f ft from the property line); Checklist '
    '§6.l\'s 5-ft landscape strip around accessory structures would move it about 3 ft to the NE — an amenity-block '
    'item inherited unchanged from Sheet C-2.0.'
    % (format(round(LEG_NE_FT), ','), format(round(LEG_SW_FT), ','), round(LEG_REAR_FT),
       format(round(BUFFER_SF), ','), M['sw_curb_return_buffer_encroachment_ft'],
       M['sw_curb_return_buffer_encroachment_sf'], AMEN_TO_BUF, AMEN_TO_BUF + BUF_W),

    'THE LANE SECTION IS TIGHTER, AND THE SECOND SIDEWALK RETREATS. Holding 20 ft of buffer outside the lots takes '
    '4\'-0" of width off the lane tract: %s at the first lot against 35\'-11" on Sheet C-2.0, widening to %s at the '
    'terminus. The 31\'-0" section still fits, but the 22-ft pavement must sit asymmetrically in the tract — %s from '
    'the NE tract line to carry the 2\'-0" strip and the 5\'-0" sidewalk, %s to the SW — which moves the travelled '
    'way up to %s toward the SW line, tapering out by u ≈ 1,000. The second (SW) sidewalk can begin only where the '
    'tract reaches 36\'-0", at u = %d instead of u = 530. All private-street components must still meet minimum '
    'public-street standards (Checklist §4.s), and the section, pavement structure and profile are PE work.'
    % (fti(TRACT_MIN), fti(TRACT_MAX), fti(NE_HALF_MIN), fti(SW_HALF_MIN), fti(SHIFT_MAX), round(U_SWWALK)),

    'AREAS AND OPEN SPACE. Common open space rises to %s SF = %.2f ac = %.1f%% of the GIS area (%.1f%% of the 9.44 '
    'deeded acres) because 900 SF per lot moves out of private ownership; on Sheet C-2.0 the equivalent figures are '
    '141,089 SF and 33.8%% plus 41,000 SF of buffer easement held on lots. Development Regulations §5.9 (Recreation '
    'Areas) applies to single-family detached subdivisions of 50 acres or more and therefore does not apply to this '
    '9.44-acre site — all common open space shown is voluntary. Open space is computed as a residual: the GIS '
    'boundary area less the lot areas less the lane and entry-drive tracts.'
    % (format(round(OPEN_SF), ','), OPEN_SF / 43560.0, 100.0 * OPEN_SF / GIS_SF, 100.0 * OPEN_SF / DEEDED_SF),

    'IMPERVIOUS AREA AND STORMWATER. Impervious area falls to %s SF = %.1f%% of the GIS area (Sheet C-2.0: 184,148 SF '
    '= 44.1%%) because Plan C is a smaller house on a smaller lot; WQv falls to %s cf on the Gwinnett County '
    'Stormwater Management Manual formula. Disturbed area and detention are UNCHANGED at 7.54 ac and 75,410 cf '
    'required against 77,863 cf provided, because the preserved 20-ft perimeter bands and the creek-woods tract '
    'occupy exactly the same ground in both layouts. Both ponds, their tracts and their assumptions are unchanged; '
    'final volumes, outlet structures, forebays and the runoff-reduction credit are the design PE\'s.'
    % (format(round(IMP_SF), ','), IMP_PCT, format(round(WQV_CF), ',')),

    'EVERYTHING ELSE IN THE APPLICATION IS UNAFFECTED. At %d units the development stays below the 120-dwelling-unit '
    'two-access trigger of IFC 2024 (GA) Appendix D107.1 as amended by Ga. Comp. R. & Regs. 120-3-3-.04, so the only '
    'fire-access relief sought remains special approval of the 1,754-ft dead end under IFC 2024 (GA) Appendix Table '
    'D103.4; NFPA 13D sprinklers remain a VOLUNTARY offer, not a required mitigation. Sanitary sewer is unchanged: '
    'Phase 1 connects by gravity to the existing 8-in main on the property (no extension), and Phase 2 depends on the '
    '≈ 178-ft off-site gravity tie to the Legends at Parkview main at invert 919.58 — a private pump station, private '
    'force main or private gravity sewer is not available to a residential subdivision under the Gwinnett DWR '
    'Standard Policy for Private Developments (rev. 9/2018), and WSR-24 §1.3.1(A) does not reach a 178-ft gravity '
    'alternative. Trip generation, school impact and the HOPA condition are unchanged.' % N_LOTS,

    'DRAWING STATUS — DRAFT, NOT SEALED. The boundary, bearings and acreage are computed from the Gwinnett County GIS '
    'parcel fabric and are DRAFT; a boundary survey plat and metes-and-bounds description sealed by a Georgia '
    'registered land surveyor are required by Ord. 2023-603 §1003-4.3 and §1003-4.4 and govern. Lot lines, tract '
    'lines, the lane and the buffer offsets shown here are concept geometry to be replaced by PE civil design and an '
    'RLS plat; Plan C must be replaced by architect\'s drawings. Every statement of conformity on this sheet reads '
    '"appears consistent with" and none is a compliance certification. Dimensions are US survey feet in the '
    'site-local system (u along the strip to the NW, v across toward the NE line).',
]


# ============================================================================ the sheet
def build():
    scale_note = 'Scale 1" = 60\' (ARCH D 36 × 24 in); details 1" = 20\' and 3/32" = 1\'-0"'
    D, F = sb.sheet('FALLBACK LOT-DEPTH LAYOUT EXHIBIT', 'C-2.4',
                    'ALTERNATIVE LAYOUT — 50\'-0" × 82\'-0" lots, the 20-ft buffer in separate HOA tracts, and a '
                    'concurrent §1005 lot-depth variance (100 ft → 82 ft)',
                    scale_note, generator='tools/sitebase.py + tools/fallback.py',
                    status_lines=['ALTERNATIVE LAYOUT — NOT THE PROPOSED PLAN. The proposed plan is Sheet',
                                  'C-2.0 (Master Concept Plan). This exhibit applies only if staff require',
                                  'the 20-ft buffer in a separate tract; it then carries a concurrent §1005',
                                  'variance on lot depth (100 ft → 82 ft) and a third house plan, Plan C.'])
    # the sheet() watermark names Sheet C-0's subject; this sheet needs its own
    px, py, pw, ph = F['plan']
    if len(D.late) >= 2:
        D.late[1] = (lambda: D.add(
            '<text x="%.1f" y="%.1f" font-size="40" fill="#c00" fill-opacity="0.09" font-weight="bold" '
            'text-anchor="middle" transform="rotate(-8 %.1f %.1f)">DRAFT — NOT SEALED — FALLBACK EXHIBIT, '
            'NOT THE PROPOSED PLAN — SEE SHEET C-2.0</text>' % (px + pw / 2, py + ph / 2, px + pw / 2, py + ph / 2)))

    # ---------------------------------------------------------------- plan (1" = 60')
    D.clip_open(fill='#fff')
    sb.adjoiners(D, labels=False, zoning=False)
    sb.arcado_row(D, labels=False)
    sb.ponds(D)
    sb.open_space(D, labels=False)
    sb.amenity(D)
    buffer_tracts(D)
    lane_fb(D)
    lots_fb(D)
    sb.streams_and_buffers(D)
    sb.sewer_existing(D, labels=False)
    sb.boundary(D, bearings=False, label=False)
    annotations(D)
    D.clip_close()
    D.stext(px + pw, py - 8, 'FOR THE PROPOSED LAYOUT SEE SHEET C-2.0 — MASTER CONCEPT PLAN', size=11,
            bold=True, fill='#7b1fa2', anchor='end')

    # ---------------------------------------------------------------- band
    X1_, X2_, X3_, X4_, X5_ = 62.0, 632.0, 1162.0, 1806.0, 2176.0
    y0 = sb.BAND_Y0

    # column 1 — the side-by-side comparison, then the legend
    y = sb.table(D, X1_, y0, ['ITEM', 'SHEET C-2.0 — §313(1) BUFFER INSIDE THE LOT',
                              'THIS SHEET C-2.4 — BUFFER IN A SEPARATE TRACT'],
                 comparison_rows(), size=6.5, widths=[124, 198, 220],
                 title='SIDE-BY-SIDE COMPARISON — the two readings of Ord. 2023-603 §313(1), priced')
    D.stext(X1_, y + 11, 'Every figure in the right-hand column is computed by tools/fallback.py from the same '
                         'boundary, entrance and lane geometry as Sheet C-2.0.', size=6.5, fill='#444')

    ylg = y + 30
    D.stext(X1_, ylg, 'LEGEND — every symbol drawn on this sheet', size=9, bold=True)
    half = (len(LEGEND) + 1) // 2
    for i, (kind, col, wdt, dash, txt) in enumerate(LEGEND):
        lx = X1_ + (0 if i < half else 278)
        yy = ylg + 13 + (i % half) * 12.0
        if kind == 'line':
            D.sline(lx, yy - 3, lx + 30, yy - 3, stroke=col, stroke_width=wdt, stroke_dasharray=dash)
        elif kind == 'key':
            D.scircle(lx + 15, yy - 3.5, 5.2, fill='#fff', stroke=col, stroke_width=0.9)
            D.stext(lx + 15, yy - 1, 'a', size=7, bold=True, fill=col, anchor='middle')
        else:
            D.srect(lx, yy - 9.5, 30, 12, fill=col, stroke='#555', stroke_width=0.4)
        D.stext(lx + 36, yy, txt, size=6.5)
    D.stext(X1_, ylg + 13 + half * 12.0 + 6, 'Existing contours, vegetation, structures, utilities, soils and the '
            'adjoining-owner schedule are on Sheet C-0 and are not repeated here.', size=6.5, fill='#444')

    # column 2 — the variance criteria keyed to the plan, then the area tabulation
    y2 = sb.table(D, X2_, y0, ['KEY', 'CRITERION (SUBJECT — VERIFY)', "APPLICANT'S RESPONSE"],
                  criteria_rows(), size=6.5, widths=[24, 110, 372],
                  title='CONCURRENT VARIANCE — Ord. 2023-603 §1005, lot depth 100\'-0" → 82\'-0" '
                        '(criteria §1005-3.2 (a)–(g), keyed on the plan)')
    D.stext(X2_, y2 + 11, 'The letters (a) – (g) are keyed to the plan above in red. The adopted text of §1005-3.2 is '
                          'NOT reproduced on this sheet — see General Note 5.', size=6.5, fill='#b00')
    sb.table(D, X2_, y2 + 28, ['ITEM', 'THIS SHEET (COMPUTED)', 'BASIS'], area_rows(), size=6.5,
             widths=[124, 188, 194], title='FALLBACK SITE DATA AND AREA TABULATION')

    # column 3 — the two details
    D.stext(X3_, y0, 'TYPICAL FALLBACK LOT — 50\'-0" × 82\'-0" (4,100 SF)', size=9, bold=True)
    D.stext(X3_, y0 + 10, 'Scale 1" = 20\'.  Buffer in a separate HOA tract.', size=6.5, fill='#444')
    sub1 = detail_typical_lot(D, X3_, y0 + 20.0)
    bx, by, bw, bh = sub1.box()
    D.srect(bx, by, bw, bh, fill='none', stroke='#000', stroke_width=0.8)
    sb.scalebar(D, bx + 10, by + bh + 24, scale=72.0 / 20.0, step_ft=20, steps=3)

    xc = X3_ + 268.0
    D.stext(xc, y0, 'PLAN C — SCHEMATIC COTTAGE FOOTPRINT', size=9, bold=True)
    D.stext(xc, y0 + 10, 'Scale 3/32" = 1\'-0".  Block diagram only — SCHEMATIC, not a designed plan.',
            size=6.5, fill='#b00')
    sub2 = detail_plan_c(D, xc, y0 + 20.0)
    bx2, by2, bw2, bh2 = sub2.box()
    D.srect(bx2, by2, bw2, bh2, fill='none', stroke='#000', stroke_width=0.8)
    yy = sb.table(D, xc, by2 + bh2 + 18,
                  ['PLAN C — AREA TABULATION (SCHEMATIC)', 'AREA', 'BASIS'],
                  [['Conditioned — front wing 17\'-0" × 26\'-0"', '442 SF', 'Outside face of exterior walls'],
                   ['Conditioned — rear block 38\'-0" × 15\'-0"', '570 SF', 'Outside face of exterior walls'],
                   ['Total conditioned (heated) floor area', '%s SF' % format(round(COND_SF), ','),
                    '2 BR / 2 BA, one storey'],
                   ['Table 4.1 minimum, cottage home', '1,000 SF', 'Margin +%d SF (≈ 1%%)'
                    % round(COND_SF - TABLE41_MIN_HEATED)],
                   ['2-car garage 21\'-0" × 21\'-0"', '%s SF' % format(round(GAR_SF), ','),
                    'Recessed 5\'-0" (Table 4.2)'],
                   ['Covered front porch 17\'-0" × 6\'-0"', '%s SF' % format(round(PORCH_SF), ','), 'Integral'],
                   ['Total under roof', '%s SF' % format(round(ROOF_SF), ','), 'Conditioned + garage + porch'],
                   ['Building coverage on a 4,100-SF lot', '%.1f%%' % (100.0 * ROOF_SF / LOT_SF), 'Under roof ÷ lot'],
                   ['Impervious per lot', '%s SF' % format(round(ROOF_SF + DRIVE_IN_LOT_SF + WALK_SF), ','),
                    'Roof + 20\' × 26\' drive + entry walk'],
                   ['Ridge height (as Plans A and B)', '≤ 24\'-0"', 'One storey; Table 4.1 maximum 40 ft']],
                  size=6.5, widths=[176, 56, 126])
    D.stext(xc, yy + 11, 'Zero-step entry, 36-in doors, 5-ft turning circles and grab-bar blocking as Plans A and B.',
            size=6.5, fill='#444')

    # columns 4 and 5 — general notes, filled column by column
    D.stext(X4_, y0, 'GENERAL NOTES — FALLBACK LAYOUT', size=9, bold=True)
    D.stext(X5_, y0, '(GENERAL NOTES, CONTINUED)', size=9, bold=True)
    cols = [(X4_, 96), (X5_, 98)]
    ci, yy = 0, y0 + 13
    for i, n in enumerate(NOTES, 1):
        nx, chars = cols[ci]
        lines = len(sb.wrap('%d. %s' % (i, n), chars))
        if yy + lines * 8.0 > sb.BAND_Y1 and ci + 1 < len(cols):
            ci, yy = ci + 1, y0 + 13
            nx, chars = cols[ci]
        yy = D.stextblock(nx, yy, '%d. %s' % (i, n), size=6.5, chars=chars, lead=8.0, indent=9)
        yy += 3.0

    # the impervious schedule that the area tabulation refers to, under the last notes column
    sb.table(D, cols[ci][0], yy + 20, ['IMPERVIOUS SCHEDULE — FALLBACK LAYOUT', 'AREA (SF)'],
             [[n, format(round(v), ',')] for n, v in IMP]
             + [['TOTAL IMPERVIOUS — %.1f%% of the %s-SF GIS site area (Sheet C-2.0: 184,148 SF = 44.1%%)'
                 % (IMP_PCT, format(round(GIS_SF), ',')), format(round(IMP_SF), ',')]],
             size=6.5, widths=[286, 60])
    return D


if __name__ == '__main__':
    D = build()
    svg, png = sb.save(D, 'fallback-layout', dpi=150)
    print('wrote %s\n      %s' % (svg, png))
    print('  lots        : %d (%d SW + %d NE), %.0f SF each (%.1f–%.1f), %.2f du/ac deeded / %.2f GIS'
          % (N_LOTS, sum(1 for s in SLOTS if s['side'] == 'SW'), sum(1 for s in SLOTS if s['side'] == 'NE'),
             LOT_SF, LOT_MIN_SF, LOT_MAX_SF, DENS_DEEDED, DENS_GIS))
    print('  lot checks  : width %.2f–%.2f, depth %.2f–%.2f, lane frontage %.2f–%.2f, inside boundary %d/%d'
          % (min(CHK['width']), max(CHK['width']), min(CHK['depth']), max(CHK['depth']),
             min(CHK['frontage']), max(CHK['frontage']), CHK['inside'], N_LOTS))
    print('  buffer      : %s SF (NE %.0f + rear %.0f + SW %.0f LF)'
          % (format(round(BUFFER_SF), ','), LEG_NE_FT, LEG_REAR_FT, LEG_SW_FT))
    print('  lane tract  : %.2f–%.2f ft; NE half %.2f, SW half %.2f; extra CL shift %.2f ft; SW walk from u=%d'
          % (TRACT_MIN, TRACT_MAX, NE_HALF_MIN, SW_HALF_MIN, SHIFT_MAX, U_SWWALK))
    print('  areas       : lots %s, lane %s, entry %s, open space %s SF = %.1f%% GIS'
          % (format(round(LOTS_SF), ','), format(round(LANE_TRACT_SF), ','), format(round(ENTRY_TRACT_SF), ','),
             format(round(OPEN_SF), ','), 100.0 * OPEN_SF / GIS_SF))
    print('  impervious  : %s SF = %.1f%%; WQv %s cf' % (format(round(IMP_SF), ','), IMP_PCT,
                                                         format(round(WQV_CF), ',')))
    print('  Plan C      : %.0f SF conditioned, %.0f garage, %.0f porch, %.0f under roof (min heated 1,000 SF)'
          % (COND_SF, GAR_SF, PORCH_SF, ROOF_SF))
    print('  clearances  : nearest lot to a stream centreline %.1f ft; amenity to a buffer tract %.1f ft'
          % (STREAM_MIN, AMEN_TO_BUF))
