#!/usr/bin/env python3
"""Sheet C-3.0 "GRADING, DRAINAGE AND STORMWATER CONCEPT" — The Cottages at Arcado Springs.

    python3 tools/grading.py        ->  drawings/grading-drainage.svg + .png

ARCH D 36 x 24 in at 1" = 60', drawn on tools/sitebase.py in the site-local (u, v) system so
that it overlays Sheet C-0 (existing conditions) and Sheet C-2.0 (master concept plan) exactly.

WHY THIS SHEET EXISTS
The 2026 Lilburn "Application Instructions" item 8 requires "existing AND PROPOSED topography ...
and drainage (approximate location of ponds and structures)"; the 2026-09-03 completeness audit
records the whole of it as missing (item M10), and the drawing-standards audit section 3.1 sets
the content of the C-3.0 row.  This sheet carries:

  * proposed 2-ft contours over screened existing 2-ft contours, tying to existing at the
    limits of disturbance;
  * a drainage-area map with the pre- and the post-development basins and their divides;
  * both detention basins with top of bank (= the 100-year ponding limit), basin bottom, the
    100-year ponding elevation, a forebay, an outlet control structure, an 8'-0" minimum
    earthen-dam top width, an emergency spillway, a 10-ft drainage easement outside the
    100-year ponding limit and a 30-ft BMP access easement carrying a 15-ft access road at
    not more than 20 % (City of Lilburn Site Development Plan Review Checklist section 11.i);
  * storm structures, pipe runs, headwalls and outfalls with a pipe chart (checklist 10.c);
  * limits of disturbance with the disturbed acreage stated (checklist 4.e);
  * the receiving-water note (Jackson Creek headwaters, GAR030701030315, Georgia 2024 303(d)
    list) with the runoff-reduction and water-quality approach; and
  * a LANE PROFILE band at 1" = 60' horizontal / 1" = 10' vertical showing the proposed grade
    line against existing ground, because existing ground on the lane centreline reaches
    11.00 % and the package claims street grades of 12 % or less
    (checklist 7.k; audit-2026-09-03/site-geometry.md item SG-20).

WHAT IS COMPUTED HERE AND WHAT IS READ
Read, never re-derived: the basin volumes, the disturbed area, the impervious area, the water
quality volume and every plan geometry come from data/layout.json as it stands at run time
(regenerated 2026-09-03 — older numbers in docs/ and in the audits are stale).  Computed here,
and only here: the proposed vertical alignment of the lane, the proposed ground surface and its
2-ft contours, the earthwork balance, the drainage-area split and the storm-pipe chart.  The
existing surface is the same bilinear interpolation of the USGS 3DEP samples in
data/topo-samples.json that tools/siteplan.py used to build the existing contours, so the
proposed contours tie to the existing ones by construction.

DRAFT — NOT SEALED.  Grading and drainage design must be sealed by a Georgia registered
professional engineer; topography is approximate until a topographic survey is performed.
"""
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitebase as sb                                       # noqa: E402

L = sb.LAYOUT
M = L['metrics']
SW_ORD = L['stormwater']

# =========================================================================== 1. existing surface
_TS = sb.TOPO['samples']
_TU = sorted(set(t['u'] for t in _TS))
_TV = sorted(set(t['v'] for t in _TS))
_ZG = {(t['u'], t['v']): t['z_ft'] for t in _TS}


def ground(u, v):
    """Existing ground, NAVD88 ft — bilinear over the 100 x 50-ft USGS 3DEP grid.
    Identical to the interpolation tools/siteplan.py used for the existing 2-ft contours."""
    u = min(max(u, _TU[0]), _TU[-1])
    v = min(max(v, _TV[0]), _TV[-1])
    i = min(max(int((u - _TU[0]) // 100), 0), len(_TU) - 2)
    j = min(max(int((v - _TV[0]) // 50), 0), len(_TV) - 2)
    u0, u1, v0, v1 = _TU[i], _TU[i + 1], _TV[j], _TV[j + 1]
    fu, fv = (u - u0) / (u1 - u0), (v - v0) / (v1 - v0)
    return ((1 - fu) * (1 - fv) * _ZG[(u0, v0)] + fu * (1 - fv) * _ZG[(u1, v0)]
            + (1 - fu) * fv * _ZG[(u0, v1)] + fu * fv * _ZG[(u1, v1)])


# =========================================================================== 2. proposed lane profile
LANE_CL = [tuple(p) for p in L['lane']['centerline']]
ENTRY_CL = [tuple(p) for p in L['lane']['entry_drive']['centerline']]
GP = [(float(u), float(z)) for u, z in L['lane']['ground_profile']]     # existing ground, lane C/L
U_PROF0, U_PROF1 = GP[0][0], GP[-1][0]                                  # 149 .. 1699


def vc(u):
    return sb.interp_v(LANE_CL, u)


def ex_prof(u):
    return sb.interp_v(GP, u)


# Vertical alignment.  Four tangents and three parabolic vertical curves, chosen so that the
# proposed grade line balances cut against fill on the lane centreline (mean deviation 0.00 ft)
# while holding every grade under 6 % — against existing ground that reaches 11.00 %.
PVI = [(149.5, 944.20), (830.0, 939.80), (1160.0, 951.00), (1470.0, 934.00), (1700.0, 945.00)]
VC_LEN = [150.0, 150.0, 150.0]                       # vertical-curve lengths at PVI 2, 3, 4
GRADE = [(PVI[i + 1][1] - PVI[i][1]) / (PVI[i + 1][0] - PVI[i][0]) for i in range(len(PVI) - 1)]


def prof(u):
    """Proposed lane centreline elevation (NAVD88 ft)."""
    for i in range(1, len(PVI) - 1):
        Lv, (pu, pz) = VC_LEN[i - 1], PVI[i]
        if abs(u - pu) <= Lv / 2.0:
            g1, g2 = GRADE[i - 1], GRADE[i]
            x = u - (pu - Lv / 2.0)
            return pz + g1 * (x - Lv / 2.0) + (g2 - g1) / (2.0 * Lv) * x * x
    for i in range(len(PVI) - 1):
        if PVI[i][0] <= u <= PVI[i + 1][0]:
            return PVI[i][1] + GRADE[i] * (u - PVI[i][0])
    return PVI[0][1] if u < PVI[0][0] else PVI[-1][1]


def grade_pct(u, dx=1.0):
    return (prof(u + dx) - prof(u - dx)) / (2.0 * dx) * 100.0


def _max_run(fn, u0, u1, step):
    best, at = 0.0, u0
    u = u0
    while u <= u1 - step:
        g = (fn(u + step) - fn(u)) / step * 100.0
        if abs(g) > abs(best):
            best, at = g, u
        u += 10.0
    return best, at


EX_GMAX, EX_GMAX_U = _max_run(ex_prof, U_PROF0, U_PROF1, 10.0)          # 11.00 % at u = 999
EX_GMAX50, EX_GMAX50_U = _max_run(ex_prof, U_PROF0, U_PROF1, 50.0)
PR_GMAX, PR_GMAX_U = _max_run(prof, PVI[0][0], PVI[-1][0], 10.0)
DEV = [(u, prof(u) - ex_prof(u)) for u in [U_PROF0 + 5 * k for k in range(int((U_PROF1 - U_PROF0) / 5) + 1)]]
DEV_MAX = max(DEV, key=lambda t: abs(t[1]))
DEV_MEAN = sum(d for _, d in DEV) / len(DEV)

# Entry drive: a uniform grade from the Arcado Rd right-of-way (existing pavement edge) up to
# the lane crest at u = 149.5.  The drive fills the shallow front swale at u ~ 84.
ENTRY_RW = ENTRY_CL[0]
ENTRY_Z0 = round(ground(ENTRY_RW[0], ENTRY_RW[1]), 1)
ENTRY_LEN = sum(sb.dist(ENTRY_CL[i], ENTRY_CL[i + 1]) for i in range(len(ENTRY_CL) - 1))
ENTRY_GRADE = (PVI[0][1] - ENTRY_Z0) / ENTRY_LEN * 100.0

# =========================================================================== 3. corridor + LOD
BND = sb.BOUNDARY
BUF = 20.0                                            # 20-ft perimeter buffer = limit of grading
CREEK_U0, CREEK_U1 = 1280.0, 1480.0                   # preserved creek-woods tract (SW side)
CREEK_V = -135.0


def lod_polygon():
    """Limits of disturbance: the Arcado Rd right-of-way on the front, the 20-ft undisturbed
    perimeter buffer on the two long lines and the rear line, and the preserved creek-woods
    tract notched out of the southwest side."""
    us = [0.0] + [float(u) for u in range(20, int(sb.U_REAR - BUF), 20)] + [sb.U_REAR - BUF]
    ne = [(u, sb.NE(u) - BUF) for u in us]
    sw = []
    for u in reversed(us):
        if CREEK_U0 <= u <= CREEK_U1:
            sw.append((u, CREEK_V))
        else:
            sw.append((u, sb.SW(u) + BUF))
    # square the notch off at its two ends
    out, prev = [], None
    for p in sw:
        if prev is not None and abs(p[1] - prev[1]) > 20:
            out.append((prev[0], p[1]) if prev[0] < p[0] else (p[0], prev[1]))
        out.append(p)
        prev = p
    front = [tuple(p) for p in sb.FRONT_LINE]
    return ne + out + list(reversed(front))[1:-1]


LOD = lod_polygon()

# design centreline: the entry drive then the lane, at 10-ft stations, each with a design elevation
CORRIDOR = []
for i in range(0, int(ENTRY_LEN) + 1, 10):
    t = i / ENTRY_LEN
    k = t * (len(ENTRY_CL) - 1)
    a, b = ENTRY_CL[int(k)], ENTRY_CL[min(int(k) + 1, len(ENTRY_CL) - 1)]
    f = k - int(k)
    p = (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]))
    CORRIDOR.append((p[0], p[1], ENTRY_Z0 + (PVI[0][1] - ENTRY_Z0) * t))
for u in range(150, int(PVI[-1][0]) + 1, 10):
    CORRIDOR.append((float(u), vc(u), prof(float(u))))

PAVE_HALF = 11.0                                      # 22-ft pavement, crowned at 2 %
CROWN = 0.02


def _taper(u, side):
    """Distance from the pavement edge out to the limit of disturbance, on one side."""
    uu = min(max(u, 0.0), sb.U_REAR - BUF)
    if side > 0:
        t = (sb.NE(uu) - BUF) - vc(max(uu, 150.0)) - PAVE_HALF
    else:
        t = vc(max(uu, 150.0)) - (sb.SW(uu) + BUF) - PAVE_HALF
    return max(t, 25.0)


def corridor_z(u, v):
    """Proposed ground before the basins are cut: the existing surface shifted vertically by
    the lane's cut or fill, the shift decaying to zero at the limit of disturbance, with the
    22-ft crowned pavement modelled inside the pavement edges."""
    best, bd = None, 1e18
    for c in CORRIDOR:
        d = (c[0] - u) ** 2 + (c[1] - v) ** 2
        if d < bd:
            bd, best = d, c
    a = math.sqrt(bd)
    zc = best[2]
    if a <= PAVE_HALF:
        return zc - CROWN * a
    z_edge = zc - CROWN * PAVE_HALF
    side = 1 if v > best[1] else -1
    d_edge = z_edge - ground(best[0], best[1] + side * PAVE_HALF)
    T = _taper(best[0], side)
    w = max(0.0, 1.0 - (a - PAVE_HALF) / T)
    return ground(u, v) + d_edge * w


# =========================================================================== 4. detention basins
def _rect_bounds(poly):
    us = [p[0] for p in poly]
    vs = [p[1] for p in poly]
    return min(us), max(us), min(vs), max(vs)


PONDS = []
for i, p in enumerate(L['ponds'], 1):
    u0, u1, v0, v1 = _rect_bounds([tuple(q) for q in p['polygon']])
    t0, t1, tv0, tv1 = _rect_bounds([tuple(q) for q in p['tract_polygon']])
    PONDS.append({
        'n': i, 'name': 'POND %d' % i, 'u0': u0, 'u1': u1, 'v0': v0, 'v1': v1,
        'tract': (t0, t1, tv0, tv1), 'tract_poly': [tuple(q) for q in p['tract_polygon']],
        'tract_sf': int(round(abs(sb.poly_area([tuple(q) for q in p['tract_polygon']])))),
        'tob_dims': p['top_of_bank_ft'], 'storage_cf': p['est_storage_cf'], 'depth': 6.0,
        'area_sf': p['area_sf'],
    })
# Design elevations.  Top of bank is set at the 100-year ponding limit so that the storage read
# from data/layout.json (top of bank to basin bottom, 6-ft depth, 3:1 side slopes) is the volume
# available below the 100-year water surface; the earthen embankment crest is carried 1'-6"
# higher for the freeboard the checklist requires at section 11.i.8.
PONDS[0].update({'tob': 936.50, 'bottom': 930.50, 'dam': 938.00, 'spillway': 937.00,
                 'ocs': (812.0, -186.0), 'fb': (794.0, 828.0, -166.0, -146.0), 'fb_depth': 2.0,
                 'hw': (805.0, -206.0), 'apron': (800.0, -212.0), 'spread': (796.0, -214.0),
                 'acc': [(965.0, -128.0), (965.0, -150.0), (862.0, -170.0), (816.0, -184.0)],
                 'acc_from_u': 965.0, 'baffle': [(800.0, -168.0), (918.0, -172.0)],
                 'dam_path': [(790.0, -141.0), (790.0, -193.0), (970.0, -193.0)],
                 'spill': [(928.0, -193.0), (948.0, -193.0)],
                 'flow': 'INLET AND OUTLET BOTH AT THE SE (LOW) END; BAFFLE BERM LENGTHENS THE '
                         'PATH (§11.i.13)'})
PONDS[1].update({'tob': 938.00, 'bottom': 932.00, 'dam': 939.50, 'spillway': 938.50,
                 'ocs': (1508.0, -198.0), 'fb': (1500.0, 1526.0, -160.0, -142.0), 'fb_depth': 2.0,
                 'hw': (1496.0, -208.0), 'apron': (1490.0, -212.0), 'spread': (1484.0, -214.0),
                 'acc': [(1560.0, -128.0), (1560.0, -152.0), (1538.0, -186.0), (1512.0, -196.0)],
                 'acc_from_u': 1560.0, 'baffle': [(1498.0, -172.0), (1604.0, -176.0)],
                 'dam_path': [(1490.0, -142.0), (1490.0, -206.0), (1546.0, -206.0)],
                 'spill': [(1490.0, -186.0), (1490.0, -166.0)],
                 'flow': 'INLET AND OUTLET BOTH AT THE SE (LOW) END; BAFFLE BERM LENGTHENS THE '
                         'PATH (§11.i.13)'})
for p in PONDS:
    p['fb_area'] = (p['fb'][1] - p['fb'][0]) * (p['fb'][3] - p['fb'][2])
    p['fb_vol'] = p['fb_area'] * p['fb_depth']          # forebay below the basin bottom
    p['pond_poly'] = sb.rect(p['u0'], p['u1'], p['v0'], p['v1'])
    inset = 3.0 * p['depth']                            # 3:1 side slopes, full depth
    p['bottom_poly'] = sb.rect(p['u0'] + inset, p['u1'] - inset, p['v0'] + inset, p['v1'] - inset)
    p['esmt_poly'] = sb.rect(p['u0'] - 10.0, p['u1'] + 10.0, p['v0'] - 10.0, p['v1'] + 10.0)


def _inside_rect_dist(u, v, u0, u1, v0, v1):
    if not (u0 <= u <= u1 and v0 <= v <= v1):
        return None
    return min(u - u0, u1 - u, v - v0, v1 - v)


def _outside_rect_dist(u, v, u0, u1, v0, v1):
    du = max(u0 - u, 0.0, u - u1)
    dv = max(v0 - v, 0.0, v - v1)
    return math.hypot(du, dv)


def z_prop(u, v):
    """Proposed ground surface (NAVD88 ft) = graded corridor, then the two basins cut in."""
    z = corridor_z(u, v)
    for p in PONDS:
        din = _inside_rect_dist(u, v, p['u0'], p['u1'], p['v0'], p['v1'])
        if din is not None:
            return p['tob'] - min(din / 3.0, p['depth'])
        dout = _outside_rect_dist(u, v, p['u0'], p['u1'], p['v0'], p['v1'])
        if dout < 3.0 * abs(z - p['tob']):
            return p['tob'] + math.copysign(min(dout / 3.0, abs(z - p['tob'])), z - p['tob'])
    return z


# =========================================================================== 5. proposed contours
def marching_squares(xs, ys, Z, level):
    """Z[j][i] at (xs[i], ys[j]); returns chained polylines at `level` (same routine as
    tools/siteplan.py so the proposed contours chain exactly like the existing ones)."""
    segs = []

    def lerp(p, q, zp, zq):
        t = 0.5 if zq == zp else (level - zp) / (zq - zp)
        return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))

    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            c = [(xs[i], ys[j]), (xs[i + 1], ys[j]), (xs[i + 1], ys[j + 1]), (xs[i], ys[j + 1])]
            z = [Z[j][i], Z[j][i + 1], Z[j + 1][i + 1], Z[j + 1][i]]
            idx = sum(1 << k for k in range(4) if z[k] >= level)
            if idx in (0, 15):
                continue
            e = {0: lerp(c[0], c[1], z[0], z[1]), 1: lerp(c[1], c[2], z[1], z[2]),
                 2: lerp(c[2], c[3], z[2], z[3]), 3: lerp(c[3], c[0], z[3], z[0])}
            table = {1: [(3, 0)], 2: [(0, 1)], 3: [(3, 1)], 4: [(1, 2)], 6: [(0, 2)], 7: [(3, 2)],
                     8: [(2, 3)], 9: [(0, 2)], 11: [(1, 2)], 12: [(1, 3)], 13: [(0, 1)], 14: [(3, 0)],
                     5: [(3, 0), (1, 2)] if sum(z) / 4 < level else [(0, 1), (2, 3)],
                     10: [(0, 1), (2, 3)] if sum(z) / 4 < level else [(3, 0), (1, 2)]}
            for a, b in table[idx]:
                segs.append((e[a], e[b]))
    key = lambda p: (round(p[0], 3), round(p[1], 3))                              # noqa: E731
    adj = defaultdict(list)
    for k, (a, b) in enumerate(segs):
        adj[key(a)].append(k)
        adj[key(b)].append(k)
    used = [False] * len(segs)
    lines = []
    for k in range(len(segs)):
        if used[k]:
            continue
        used[k] = True
        line = [segs[k][0], segs[k][1]]
        for end in (1, 0):
            while True:
                cur = key(line[-1] if end else line[0])
                nxt = None
                for m in adj[cur]:
                    if not used[m]:
                        nxt = m
                        break
                if nxt is None:
                    break
                used[nxt] = True
                a, b = segs[nxt]
                other = b if key(a) == cur else a
                if end:
                    line.append(other)
                else:
                    line.insert(0, other)
        lines.append(line)
    return lines


GX = [float(x) for x in range(-40, 1740, 8)]
GY = [float(y) for y in range(-244, 20, 4)]
ZP = [[z_prop(x, y) for x in GX] for y in GY]
ZE = [[ground(x, y) for x in GX] for y in GY]


def _split_inside(line, poly):
    out, cur = [], []
    for p in line:
        if sb.point_in_poly(p, poly):
            cur.append(p)
        else:
            if len(cur) > 1:
                out.append(cur)
            cur = []
    if len(cur) > 1:
        out.append(cur)
    return out


PROP_CONTOURS = {}
for lev in range(922, 960, 2):
    runs = []
    for ln in marching_squares(GX, GY, ZP, lev):
        runs += _split_inside(ln, LOD)
    if runs:
        PROP_CONTOURS[str(lev)] = runs

# ------------------------------------------------------------------ earthwork and disturbed area
CELL = (GX[1] - GX[0]) * (GY[1] - GY[0])
CUT_CF = FILL_CF = 0.0
DIST_SF = 0.0
BASIN_SF = {1: 0.0, 2: 0.0, 0: 0.0}                 # 0 = to the Arcado Rd right-of-way
U_DIVIDE = 1160.0                                    # proposed crest = the post-development divide
U_FRONT_DIV = 25.0
for j, y in enumerate(GY):
    for i, x in enumerate(GX):
        if not sb.point_in_poly((x, y), BND):
            continue
        d = ZP[j][i] - ZE[j][i]
        if sb.point_in_poly((x, y), LOD):
            DIST_SF += CELL
            key = 0 if x < U_FRONT_DIV else (1 if x < U_DIVIDE else 2)
            BASIN_SF[key] += CELL
            if d > 0.05:
                FILL_CF += d * CELL
            elif d < -0.05:
                CUT_CF += -d * CELL
CUT_CY, FILL_CY = CUT_CF / 27.0, FILL_CF / 27.0
DIST_AC_DRAWN = DIST_SF / 43560.0

# The disturbed acreage the package publishes (data/layout.json, re-derived 2026-09-03)
DIST_SF_PUB = SW_ORD['disturbed_area']['disturbed_sf']
DIST_AC_PUB = SW_ORD['disturbed_area']['disturbed_ac']
DET_REQ = SW_ORD['detention_required_cf']
DET_PROV = SW_ORD['detention_provided_cf']
DET_RATE = SW_ORD['detention_rate_cf_per_disturbed_ac']
WQV = SW_ORD['wqv_cf']
IMP_SF = L['impervious_summary']['total_sf']
IMP_PCT = L['impervious_summary']['pct_of_gis_area']
RV = 0.05 + 0.009 * IMP_PCT
RRV = RV * 1.0 / 12.0 * sb.BOUNDARY_SF

# forebay requirement: 10 % of each basin's share of the water quality volume (§11.i.15)
# (filled in after BASIN_AC is known, below)

# per-basin disturbed acreage, scaled so the three sub-basins sum to the published figure
_scale = DIST_SF_PUB / max(DIST_SF, 1.0)
BASIN_AC = {k: BASIN_SF[k] * _scale / 43560.0 for k in BASIN_SF}
BASIN_REQ = {k: BASIN_AC[k] * DET_RATE for k in BASIN_AC}
for _p in PONDS:
    _p['wqv_share'] = WQV * BASIN_AC[_p['n']] / DIST_AC_PUB
    _p['fb_req'] = 0.10 * _p['wqv_share']

# ------------------------------------------------------------------ impervious by drainage basin
_per_lot = L['impervious_summary']['per_lot_sf']
LOT_IMP = {0: 0.0, 1: 0.0, 2: 0.0}
for lot in L['lots']:
    umid = sum(p[0] for p in lot['polygon']) / len(lot['polygon'])
    k = 0 if umid < U_FRONT_DIV else (1 if umid < U_DIVIDE else 2)
    LOT_IMP[k] += _per_lot[lot['plan']]['total'] if isinstance(_per_lot[lot['plan']], dict) \
        and 'total' in _per_lot[lot['plan']] else sum(v for v in _per_lot[lot['plan']].values()
                                                      if isinstance(v, (int, float)))
_comp = M['impervious_components_sf']
_lane_imp = (_comp['Private lane pavement'] + _comp['Sidewalks'] + _comp['Hammerhead turnaround legs'])
_front_imp = (_comp['Entry drive pavement'] + _comp['Entrance curb returns']
              + _comp['Guest and mail-kiosk parking bays']
              + _comp['Clubhouse roof, court pads, mail kiosk and amenity walks'])
_f1 = (U_DIVIDE - 150.0) / (1700.0 - 150.0)
IMP_BY = {0: _front_imp * 0.25 + LOT_IMP[0],
          1: _front_imp * 0.75 + _lane_imp * _f1 + LOT_IMP[1],
          2: _lane_imp * (1.0 - _f1) + LOT_IMP[2]}
_tot = sum(IMP_BY.values())
IMP_BY = {k: v * IMP_SF / _tot for k, v in IMP_BY.items()}

# pre-development impervious: the two mapped dwellings and the 4541 drive (aerial-imagery
# footprints carried by tools/sitebase.py) — everything else on the site is woodland or lawn
PRE_IMP = []
for _rec, _poly, _area in sb.existing_polys():
    PRE_IMP.append((sb.poly_centroid(_poly)[0], _area))
_dpath, _dband = sb.existing_drive_poly()
PRE_IMP.append((sb.poly_centroid(_dband)[0], abs(sb.poly_area(_dband))))


def pre_impervious_sf(ua, ub):
    return sum(a for u, a in PRE_IMP if ua <= u < ub)

# =========================================================================== 6. storm network
def _rim(u, v):
    return round(z_prop(u, v), 2)


STRUCT = [
    # id, type, u, v, note
    ('A-1', 'DOUBLE CURB INLET', 95.0, -168.0, 'entry drive at the existing front swale'),
    ('A-1B', 'JUNCTION BOX', 150.0, -122.0, 'entry drive / lane junction — bend'),
    ('A-2', 'CURB INLET', 300.0, -128.0, 'lane, southwest edge of pavement'),
    ('A-3', 'CURB INLET', 500.0, -127.0, 'lane, southwest edge of pavement'),
    ('A-4', 'CURB INLET', 680.0, -126.0, 'lane, southwest edge of pavement'),
    ('A-5', 'DOUBLE CURB INLET', 830.0, -126.0, 'lane sag at PVI 2'),
    ('A-6', 'JUNCTION BOX', 800.0, -134.0, 'Pond 1 tract; also receives Line B'),
    ('A-7', 'FLARED END SECTION', 806.0, -142.0, 'into the Pond 1 forebay'),
    ('B-1', 'CURB INLET', 1140.0, -125.5, 'lane, southeast of the crest at PVI 3'),
    ('B-2', 'CURB INLET', 1040.0, -125.8, 'lane, southwest edge of pavement'),
    ('B-3', 'CURB INLET', 930.0, -126.0, 'lane, southwest edge of pavement'),
    ('C-1', 'CURB INLET', 1190.0, -125.0, 'lane, northwest of the crest at PVI 3'),
    ('C-2', 'CURB INLET', 1330.0, -125.0, 'lane, southwest edge of pavement'),
    ('C-3', 'DOUBLE CURB INLET', 1470.0, -125.0, 'lane sag at PVI 4'),
    ('C-4', 'JUNCTION BOX', 1500.0, -132.0, 'lane tract at the Pond 2 access'),
    ('C-5', 'FLARED END SECTION', 1512.0, -140.0, 'into the Pond 2 forebay'),
    ('OF-1', 'HEADWALL + RIPRAP APRON', 805.0, -206.0, 'Pond 1 outlet, thence level spreader'),
    ('OF-2', 'HEADWALL + RIPRAP APRON', 1496.0, -208.0, 'Pond 2 outlet, thence level spreader'),
]
S_XY = {s[0]: (s[2], s[3]) for s in STRUCT}

# reaches: from, to, diameter (in), material, slope (%), and the invert at the upstream end
REACH = [
    ('A-1', 'A-1B', 24, 'RCP', 0.35, 936.20),
    ('A-1B', 'A-2', 24, 'RCP', 0.35, None),
    ('A-2', 'A-3', 24, 'RCP', 0.35, None),
    ('A-3', 'A-4', 24, 'RCP', 0.35, None),
    ('A-4', 'A-5', 24, 'RCP', 0.35, None),
    ('A-5', 'A-6', 24, 'RCP', 0.50, None),
    ('A-6', 'A-7', 24, 'RCP', 0.50, None),
    ('B-1', 'B-2', 18, 'RCP', 2.50, 945.20),
    ('B-2', 'B-3', 18, 'RCP', 4.80, None),
    ('B-3', 'A-6', 18, 'RCP', 3.00, None),
    ('C-1', 'C-2', 18, 'RCP', 5.10, 944.20),
    ('C-2', 'C-3', 18, 'RCP', 4.20, None),
    ('C-3', 'C-4', 24, 'RCP', 0.50, None),
    ('C-4', 'C-5', 24, 'RCP', 0.50, None),
]
OUTLETS = [                        # OCS -> headwall, through the earthen embankment
    ('POND 1 OCS', 'OF-1', 24, 'RCP', 1.40, PONDS[0]['bottom'], PONDS[0]['ocs'], S_XY['OF-1']),
    ('POND 2 OCS', 'OF-2', 24, 'RCP', 1.40, PONDS[1]['bottom'], PONDS[1]['ocs'], S_XY['OF-2']),
]

PIPES = []
_inv_out = {}
for a, b, dia, mat, slope, inv0 in REACH:
    pa, pb = S_XY[a], S_XY[b]
    ln = sb.dist(pa, pb)
    iv_up = inv0 if inv0 is not None else _inv_out[a]
    iv_dn = iv_up - slope / 100.0 * ln
    if b not in _inv_out or iv_dn < _inv_out[b]:
        _inv_out[b] = iv_dn
    PIPES.append({'from': a, 'to': b, 'dia': dia, 'mat': mat, 'len': ln, 'slope': slope,
                  'inv_up': iv_up, 'inv_dn': iv_dn, 'a': pa, 'b': pb})
for name, b, dia, mat, slope, inv0, pa, pb in OUTLETS:
    ln = sb.dist(pa, pb)
    PIPES.append({'from': name, 'to': b, 'dia': dia, 'mat': mat, 'len': ln, 'slope': slope,
                  'inv_up': inv0, 'inv_dn': inv0 - slope / 100.0 * ln, 'a': pa, 'b': pb})

STR_RIM, STR_TYPE = {}, {}
for sid, typ, u, v, note in STRUCT:
    STR_RIM[sid] = _rim(u, v)
    STR_TYPE[sid] = typ


def pipe_rows():
    rows = []
    for p in PIPES:
        cov = None
        typ = STR_TYPE.get(p['from'], '')
        if p['from'] in STR_RIM and 'FLARED' not in typ and 'HEADWALL' not in typ:
            cov = STR_RIM[p['from']] - p['inv_up'] - p['dia'] / 12.0
        rows.append([
            '%s → %s' % (p['from'], p['to']),
            '%d" %s' % (p['dia'], p['mat']),
            "%.0f'" % p['len'],
            '%.2f' % p['slope'],
            '%.2f' % p['inv_up'],
            '%.2f' % p['inv_dn'],
            ('%.1f' % cov) if cov is not None else '—',
        ])
    return rows


def struct_rows():
    rows = []
    for sid, typ, u, v, note in STRUCT:
        rows.append([sid, typ, '(%.0f, %+.0f)' % (u, v), '%.2f' % STR_RIM[sid], note])
    return rows


# =========================================================================== 7. drainage areas
def band_poly(ua, ub, front=False):
    us = [float(u) for u in range(int(max(ua, 0.0)), int(ub) + 1, 20)] + [float(ub)]
    top = [(u, sb.NE(u)) for u in us]
    bot = [(u, sb.SW(u)) for u in reversed(us)]
    poly = top + bot
    if front:
        poly = poly + list(reversed([tuple(p) for p in sb.FRONT_LINE]))
    return poly


PRE = [
    ('PRE-A', 0.0, 250.0, True, '#8e24aa',
     'Front slope and the existing swale at u ≈ 84 — southwest, off site, to the branch of the '
     'Jackson Creek headwaters that runs 38–58 ft outside the southwest line'),
    ('PRE-B', 250.0, 1160.0, False, '#00838f',
     'Mid-strip swale (existing sag at u ≈ 800) — southwest, off site, to the same branch'),
    ('PRE-C', 1160.0, sb.U_REAR, False, '#ef6c00',
     'Rear low pocket — southwest to the on-site headwater channel at (u 1,392, v −210)'),
]
POST = [
    ('POST-0', 0.0, U_FRONT_DIV, True, '#8e24aa', 0,
     'Arcado Rd frontage strip and the entrance apron — sheet flow to the existing Arcado Rd '
     'right-of-way as today (no change in outfall)'),
    ('POST-1', U_FRONT_DIV, U_DIVIDE, False, '#0277bd', 1,
     'Lines A and B → POND 1 forebay → OCS → OF-1 headwall, riprap apron and level spreader → '
     'sheet flow through the undisturbed buffer to the existing southwest swale'),
    ('POST-2', U_DIVIDE, sb.U_REAR, False, '#2e7d32', 2,
     'Line C → POND 2 forebay → OCS → OF-2 headwall, riprap apron and level spreader → sheet '
     'flow through the creek woods to the headwater channel'),
]

# =========================================================================== 8. sheet content
G = {'prop': '#6d4c2f', 'lod': '#c62828', 'storm': '#00695c', 'pond': '#0d47a1',
     'esmt': '#7b1fa2', 'acc': '#a1450a', 'pre': '#8e24aa', 'ctx': '#b5b5b5'}

LEGEND = [
    ('line', sb.C['bnd'], 1.8, '', 'Assemblage boundary (Gwinnett GIS — DRAFT)'),
    ('rect', sb.C['adj_fill'], 0, '', 'Adjoining tax parcel (all zoned R-1, Lilburn)'),
    ('line', sb.C['rw'], 0.9, '', 'Arcado Rd right-of-way line'),
    ('line', '#333', 0.6, '14 3 3 3', 'Existing road centreline'),
    ('line', sb.C['contour'], 0.45, '2 2', 'EXISTING 2-ft contour (3DEP, screened)'),
    ('line', sb.C['contour_txt'], 0.9, '7 3', 'EXISTING 10-ft index contour (screened)'),
    ('line', G['prop'], 0.8, '', 'PROPOSED 2-ft contour'),
    ('line', G['prop'], 1.9, '', 'PROPOSED 10-ft index contour'),
    ('plus', G['prop'], 0, '', 'Proposed spot elevation (checklist §10.b)'),
    ('line', G['lod'], 1.6, '18 4 3 4', 'LIMITS OF DISTURBANCE (§4.e)'),
    ('line', sb.C['stream'], 1.6, '', 'Stream — state waters (top of bank approx.)'),
    ('line', sb.C['buf_line'], 0.5, '3 2', "25' state (GA EPD) buffer"),
    ('line', sb.C['buf_line'], 0.8, '6 2', "50' undisturbed stream buffer (Lilburn)"),
    ('line', sb.C['buf_line'], 0.8, '8 2 2 2', "75' impervious setback"),
    ('line', G['pre'], 1.2, '9 3 2 3', 'Pre-development drainage divide'),
    ('rect', '#cfe0f0', 0, '', 'Post-development drainage area (tinted, labelled)'),
    ('line', G['storm'], 1.8, '', 'Proposed storm sewer (RCP) — see pipe chart'),
    ('sq', G['storm'], 0, '', 'Proposed curb inlet / double curb inlet'),
    ('dot', G['storm'], 0, '', 'Proposed junction box'),
    ('tri', G['storm'], 0, '', 'Flared end section / headwall + riprap apron'),
    ('rect', 'url(#rip)', 0, '', 'Riprap outlet protection and level spreader'),
    ('line', G['pond'], 1.4, '', 'Basin top of bank = 100-yr ponding limit'),
    ('line', G['pond'], 0.7, '5 3', 'Basin bottom (3:1 side slopes)'),
    ('line', '#5d4037', 2.2, '', "Earthen embankment crest — 8'-0\" min. top width"),
    ('line', '#2e7d32', 1.4, '3 2', 'Emergency spillway (grassed, 20 ft wide)'),
    ('line', '#5d4037', 1.4, '6 3', 'Internal baffle berm (flow path, §11.i.13)'),
    ('rect', '#bcd7c2', 0, '', 'Sediment forebay (10 % of WQv per inlet)'),
    ('ocs', G['pond'], 0, '', 'Outlet control structure (OCS)'),
    ('line', G['esmt'], 1.0, '7 3', "10' drainage easement outside the 100-yr limit"),
    ('line', G['acc'], 1.0, '12 4', "30' BMP access easement (cleared and grubbed)"),
    ('line', G['acc'], 3.2, '2 3', "15' BMP access road at ≤ 20 % to the OCS"),
    ('line', sb.C['sewer'], 0.9, '', 'Existing 8-in sanitary sewer and manhole'),
    ('rect', 'url(#exhatch)', 0, '', 'Existing building — to be removed'),
    ('rect', '#efe6dc', 0, '', 'Existing drive — to be removed'),
    ('line', G['ctx'], 0.5, '', 'Proposed lot, tract and structure line (Sheet C-2.0)'),
    ('rect', '#e6e6e6', 0, '', 'Proposed pavement (lane, drive, turnarounds)'),
    ('rect', sb.C['green'], 0, '', 'Common open-space tract (HOA)'),
]


def basin_rows():
    rows = []
    for p in PONDS:
        rows.append([p['name'], '%s ft' % p['tob_dims'].replace('x', '×'),
                     '%.2f' % p['bottom'], '%.2f' % p['tob'], '%.2f' % p['dam'],
                     '%.2f' % p['spillway'],
                     '%s' % format(p['storage_cf'], ','),
                     '%s' % format(int(round(BASIN_REQ[p['n']])), ','),
                     '%.2f' % BASIN_AC[p['n']],
                     '%s / %s' % (format(int(p['fb_vol']), ','),
                                  format(int(round(p['fb_req'])), ','))])
    return rows


def da_rows():
    rows = []
    for tag, ua, ub, front, col, txt in PRE:
        gross = _band_area(ua, ub, front)
        imp = pre_impervious_sf(ua, ub)
        rows.append([tag, 'PRE', "u %.0f – %.0f" % (ua, ub), '%.2f' % (gross / 43560.0), '—',
                     '%.2f ac (%.1f %%)' % (imp / 43560.0, 100.0 * imp / max(gross, 1.0)), txt])
    for tag, ua, ub, front, col, key, txt in POST:
        gross = _band_area(ua, ub, front)
        rows.append([tag, 'POST', "u %.0f – %.0f" % (ua, ub), '%.2f' % (gross / 43560.0),
                     '%.2f' % BASIN_AC[key],
                     '%.2f ac (%.0f %%)' % (IMP_BY[key] / 43560.0, 100.0 * IMP_BY[key] / max(gross, 1.0)),
                     txt])
    return rows


_AREA_CACHE = {}


def _band_area(ua, ub, front):
    k = (ua, ub, front)
    if k in _AREA_CACHE:
        return _AREA_CACHE[k]
    a = 0.0
    for j, y in enumerate(GY):
        for i, x in enumerate(GX):
            if ua - (25.0 if front else 0.0) <= x < ub and sb.point_in_poly((x, y), BND):
                a += CELL
    _AREA_CACHE[k] = a
    return a


SW_ROWS = [
    ['Regulatory basis', 'Gwinnett County Stormwater Management Manual (GCSWMM) as applied by the City '
                         'of Lilburn; City of Lilburn Development Regulations, Post-Development Stormwater '
                         'Ordinance; Site Development Plan Review Checklist §11'],
    ['Gross site area', '%s SF = %.3f ac (GIS ring); 9.44 ac deeded — RLS survey governs'
     % (format(int(round(sb.BOUNDARY_SF)), ','), sb.BOUNDARY_SF / 43560.0)],
    ['Disturbed area', '%s SF = %.3f ac (data/layout.json, re-derived 2026-09-03: site raster less the '
                       '20-ft perimeter buffer bands and the creek-woods tract). Limits of disturbance as '
                       'drawn on this sheet enclose %s SF = %.2f ac. No off-site disturbance is proposed '
                       'except the outfall aprons shown.'
     % (format(DIST_SF_PUB, ','), DIST_AC_PUB, format(int(round(DIST_SF)), ','), DIST_AC_DRAWN)],
    ['Impervious area', '%s SF = %.1f %% of the GIS area (data/layout.json)'
     % (format(IMP_SF, ','), IMP_PCT)],
    ['Rv', 'Rv = 0.05 + 0.009 · I = 0.05 + 0.009 × %.1f = %.4f' % (IMP_PCT, RV)],
    ['Water quality volume', 'WQv = 1.2 · (0.05 + 0.009 · I) ÷ 12 · A = %s CF (data/layout.json)'
     % format(WQV, ',')],
    ['Runoff reduction volume', 'RRv = Rv · 1.0 in ÷ 12 · A = %s CF if credited. Taken as ZERO in the '
                                'detention sizing below (conservative); any RRv credit reduces the '
                                'required detention one-for-one.' % format(int(round(RRV)), ',')],
    ['Detention required', '%s CF/disturbed ac × %.3f ac = %s CF (screening rate, RRv = 0)'
     % (format(int(DET_RATE), ','), DIST_AC_PUB, format(DET_REQ, ','))],
    ['Detention provided', '%s CF = POND 1 %s CF + POND 2 %s CF, measured between top of bank and basin '
                           'bottom (6-ft depth, 3:1 side slopes, prismoidal) — data/layout.json'
     % (format(DET_PROV, ','), format(PONDS[0]['storage_cf'], ','), format(PONDS[1]['storage_cf'], ','))],
    ['Adequacy', 'Provided ÷ required = %.1f %% of the site total. The split between the two basins does '
                 'not yet match the tributary split — see general note 9.' % (100.0 * DET_PROV / DET_REQ)],
    ['Receiving water', 'Jackson Creek headwaters, GAR030701030315 — Georgia 2024 Integrated 305(b)/303(d) '
                        'list, NOT SUPPORTING (bacteria, biota; urban runoff)'],
    ['Floodplain', 'FEMA Zone X, FIRM panel 13135C0114F eff. 2006-09-29 — no SFHA, floodway or BFE on '
                   'site (checklist §7.c, §9.a)'],
    ['Earthwork (concept)', 'Cut ≈ %s CY, fill ≈ %s CY inside the limits of disturbance — a net surplus of '
                            '≈ %s CY of excavation, most of it the two basins. The lane centreline itself '
                            'balances (mean deviation %+.2f ft). Shrinkage, topsoil stripping, rock and '
                            'undercut are NOT included; rock probes required (NRCS ARE: gneiss at 22–40 in).'
     % (format(int(round(CUT_CY)), ','), format(int(round(FILL_CY)), ','),
        format(int(round(CUT_CY - FILL_CY)), ','), DEV_MEAN)],
]

OF1_TO_SW = abs(S_XY['OF-1'][1] - sb.SW(S_XY['OF-1'][0]))
OF2_TO_SW = abs(S_XY['OF-2'][1] - sb.SW(S_XY['OF-2'][0]))
CUT_MAX_CL = -min(d for _, d in DEV)
FILL_MAX_CL = max(d for _, d in DEV)
GRADE_STR = ' / '.join('%+.2f %%' % (g * 100.0) for g in GRADE)

NOTES = [
    'BASIS AND STATUS. This is a CONCEPT grading and drainage exhibit prepared by the owner for a '
    'rezoning application; it is DRAFT and NOT SEALED. Grading, drainage, hydrology and hydraulics must '
    'be designed and sealed by a Georgia registered professional engineer, and topography must be '
    'established by a topographic survey, before any land disturbance permit. Every statement of '
    'conformity on this sheet reads "appears consistent with" and none is a compliance certification.',

    'DATUM AND TOPOGRAPHY (checklist §7.b, §7.d). Vertical datum NAVD88; horizontal SR 2240 GA West, '
    'US survey feet, shown in the site-local (u, v) system of FACTS §1. EXISTING contours (screened) are '
    '2-ft contours interpolated from the USGS 3DEP 1-metre digital elevation model sampled on a '
    '100 × 50-ft grid — APPROXIMATE. PROPOSED contours are 2-ft contours generated from the design '
    'surface described in note 3. NO BENCHMARK HAS BEEN SET: a benchmark and a field topographic survey '
    'are required and govern over this sheet.',

    'PROPOSED SURFACE. The proposed surface is the existing surface displaced vertically by the cut or '
    'fill on the private-lane centreline, the displacement decaying to zero at the limits of '
    'disturbance, with the 22-ft crowned pavement (2 %) modelled between the pavement edges and the two '
    'detention basins cut in at 3:1 side slopes. Individual lot and driveway grading, finished floor '
    'elevations, retaining structures if any, and the erosion and sedimentation control plan are NOT '
    'part of this exhibit and are to be designed by the PE at the land disturbance permit stage.',

    'LANE PROFILE AND STREET GRADES (checklist §7.k). The profile band at the bottom of this sheet plots '
    'the proposed grade line against existing ground on the lane centreline from u = %.0f to u = %.0f. '
    'EXISTING ground reaches %.2f %% over the 10-ft station interval at u ≈ %.0f and %.2f %% over a '
    '50-ft interval at u ≈ %.0f. The PROPOSED alignment — four tangents at %s and three %.0f-ft '
    'vertical curves — holds a maximum grade of %.2f %% at u ≈ %.0f, inside the 12 %% maximum street '
    'grade the package cites and below the 12 %%–15 %% band that triggers the checklist note "12%% to '
    '15%% street grades require an ‘As Graded’ survey before installation of the curb". That note is '
    'carried on this sheet for completeness. Maximum deviation from existing ground on the centreline '
    'is %.1f ft at u ≈ %.0f; the mean deviation is %+.2f ft, so the centreline earthwork balances.'
    % (U_PROF0, U_PROF1, EX_GMAX, EX_GMAX_U + 5, EX_GMAX50, EX_GMAX50_U + 25, GRADE_STR, VC_LEN[0],
       abs(PR_GMAX), PR_GMAX_U + 5, abs(DEV_MAX[1]), DEV_MAX[0], DEV_MEAN),

    'ENTRY DRIVE. The 24-ft entry drive rises from the Arcado Rd right-of-way at approximately %.1f '
    '(existing ground) to the lane crest at %.2f over %.0f ft, a uniform %.2f %%. It fills the shallow '
    'front swale at u ≈ 84; cross-drain STR A-1 picks that swale up and carries it to POND 1 (Line A) so '
    'the front of the site is detained rather than discharged untreated. The tie-in elevation at the '
    'right-of-way must be confirmed against a field survey of the Arcado Rd pavement edge and against '
    'the Gwinnett County DOT driveway permit.'
    % (ENTRY_Z0, PVI[0][1], ENTRY_LEN, ENTRY_GRADE),

    'LIMITS OF DISTURBANCE (checklist §4.e). Total site %.3f ac (GIS) / 9.44 ac (deeded). DISTURBED AREA '
    '= %s SF = %.3f ac, being the site less the 20-ft undisturbed perimeter buffer bands and the '
    'preserved creek-woods tract (data/layout.json, re-derived 2026-09-03; this supersedes the '
    '"≈ 4.4 disturbed acres" figure carried in earlier revisions of docs/03 and the "≈ 7.9 ac" '
    'estimate in docs/08). The limits of disturbance as drawn enclose %s SF = %.2f ac. NO OFF-SITE '
    'DISTURBANCE is proposed. Land disturbance exceeds one acre: an NPDES permit (GAR100001), the '
    '$40/disturbed-acre Lilburn NPDES fee, the EPD fee and an erosion control bond apply '
    '(checklist §3.e, §3.f).'
    % (sb.BOUNDARY_SF / 43560.0, format(DIST_SF_PUB, ','), DIST_AC_PUB,
       format(int(round(DIST_SF)), ','), DIST_AC_DRAWN),

    'STREAM BUFFERS. STREAM BUFFERS ARE TO REMAIN IN A NATURAL AND UNDISTURBED CONDITION. STREAM BUFFER '
    'SHALL BE STAKED AND PROTECTED PRIOR TO LAND DISTURBANCE (checklist §9.e, §9.f). The 25-ft state '
    'buffer (O.C.G.A. §12-7-6(b)(15)), the 50-ft undisturbed city buffer and the 75-ft impervious '
    'setback (Lilburn Code Ch. 109 Art. VII) are drawn from the digitised channel centreline of all '
    'three mapped reaches and are APPROXIMATE — the top of bank must be field-delineated by a qualified '
    'professional and governs. No grading, no basin and no impervious surface is proposed inside the '
    '75-ft setback; both outfall aprons and level spreaders are held outside it.',

    'RECEIVING WATER AND WATER QUALITY. All runoff from this site discharges to the headwaters of '
    'JACKSON CREEK, GA EPD reach GAR030701030315, which is on GEORGIA’S 2024 303(d) LIST as NOT '
    'SUPPORTING for bacteria and biota with urban runoff cited as the cause. There is no direct '
    'discharge to the buffer or to any adjoining yard: every outfall terminates in a riprap apron and a '
    'level spreader, and the last reach to the channel is sheet flow across undisturbed woodland. '
    'WQv = %s CF, treated in the two dry extended-detention / water-quality basins. RUNOFF REDUCTION: '
    'RRv = %s CF if credited — to be met by bioretention with underdrains in the two pocket greens and '
    'the terminus green, roof-drain disconnection to HOA-maintained yards, pervious pavers in the guest '
    'and mail-kiosk bays (permitted by Zoning Ordinance 2023-603 Table 4.2), and credit for the '
    'preserved buffers and creek woods. Infiltration will test poorly on the eroded Appling / Madison / '
    'Pacolet clays, so no infiltration credit is assumed at this stage.'
    % (format(WQV, ','), format(int(round(RRV)), ',')),

    'DETENTION SIZING AND THE SPLIT BETWEEN THE TWO BASINS. At the hydrology basis the City accepted for '
    'this site — %s CF of detention per disturbed acre, less any runoff-reduction volume — %.3f '
    'disturbed acres require %s CF with RRv taken as zero. The two basins as drawn provide %s CF '
    '(POND 1 %s + POND 2 %s, from data/layout.json), which clears the SITE TOTAL at %.1f %%. The '
    'DISTRIBUTION does not yet match the tributary split: POND 1 drains %.2f disturbed acres '
    '(%s CF required at the screening rate) against %s CF drawn, and POND 2 drains %.2f acres '
    '(%s CF required) against %s CF drawn. POND 1 sits in a %s SF HOA tract against a %s SF basin '
    'footprint and can be widened within that tract to about 90 ft × 190 ft at top of bank without '
    'moving a lot line; the basins are to be re-proportioned, and the true tributary areas established, '
    'by the design PE. THIS SHEET DOES NOT CERTIFY DETENTION ADEQUACY.'
    % (format(int(DET_RATE), ','), DIST_AC_PUB, format(DET_REQ, ','), format(DET_PROV, ','),
       format(PONDS[0]['storage_cf'], ','), format(PONDS[1]['storage_cf'], ','),
       100.0 * DET_PROV / DET_REQ,
       BASIN_AC[1], format(int(round(BASIN_REQ[1])), ','), format(PONDS[0]['storage_cf'], ','),
       BASIN_AC[2], format(int(round(BASIN_REQ[2])), ','), format(PONDS[1]['storage_cf'], ','),
       format(int(PONDS[0]['tract_sf']), ','), format(PONDS[0]['area_sf'], ',')),

    'DETENTION BASINS — GENERAL (checklist §11.i). Each basin is a DRY extended-detention / '
    'water-quality basin on its own HOA-owned tract (§11.i.1). TOP OF BANK IS SET AT THE 100-YEAR '
    'PONDING LIMIT, and the earthen embankment crest is carried 1′-6″ above it to provide the minimum '
    'freeboard of §11.i.8; the volumes tabulated are therefore the volumes available below the 100-year '
    'water surface. Minimum earthen dam top width 8′-0″ (§11.i.5; Development Regulations 9.8.2.d(5)). '
    'Maximum cut or fill slope 2H:1V; basin side slopes 3H:1V. A sediment forebay equal to 10 % of the '
    'water quality volume is provided at each inlet (§11.i.15) and is sized against that basin’s share '
    'of the water quality volume in the DETENTION BASIN DATA table. FLOW PATH (§11.i.13): in BOTH basins '
    'the inlet and the outlet are at the SOUTHEAST (low) end. Existing ground rises to the northwest '
    'across each basin site — about 6 ft at POND 1 and about 10 ft at POND 2 — so the lane sag that feeds '
    'the basin and the only corner at which it can discharge by gravity are the same end, and the inlet '
    'and outlet cannot be put at opposite ends. An INTERNAL BAFFLE BERM is therefore shown in each basin, '
    'as §11.i.13 expressly permits ("baffles or islands may be installed to increase the flow path '
    'length"). Toe of slope is more than 10 ft from every '
    'adjoining property line (§11.i.6; §8.f). Outlet control structure details, the trash rack, the '
    'anti-clog orifice, the embankment cross-section, benches, the emergency spillway section and the '
    'WQ / CPv / 100-year elevations and volumes tabulated on the OCS detail belong on Sheet C-3.1 and '
    'are NOT on this sheet.',

    'BMP ACCESS AND DRAINAGE EASEMENTS. A 30-FT BMP ACCESS EASEMENT is provided from the private lane to '
    'each basin (residential projects, §11.i.2), carrying a 15-FT WIDE GRASSED ACCESS ROAD GRADED AT NOT '
    'MORE THAN 20 %. Both basins exceed 50 ft in width, so the access road extends to the bottom of the '
    'basin at the outlet control structure (§11.i.3). ACCESS EASEMENT TO BE CLEARED AND GRUBBED '
    '(§11.i.4). A 10-FT DRAINAGE EASEMENT is provided around each basin outside the 100-year ponding '
    'limit (§11.i.12); both lie wholly within the HOA-owned pond and private-lane tracts. All drainage, '
    'access and maintenance easements for storm and sanitary pipes and for the stormwater facilities '
    'will be shown and recorded with the final plat (§10.h). A Stormwater BMP Maintenance Agreement with '
    'as-built hydrology, volume certification, maintenance schedule, access easement, inspection report '
    'and an 18-month BMP inspection is required of the HOA (checklist §3.f.3).',

    'STORM SEWER. Structure and pipe data are tabulated in the STORM STRUCTURE SCHEDULE and PIPE CHART. '
    'Rim elevations are read from the proposed surface of this sheet; inverts are set at the slopes '
    'tabulated and are CONCEPT values for feasibility only — final sizes, slopes, inverts, inlet '
    'spacing, spread and hydraulic grade line are the design PE’s. Minimum cover over the pipe barrel '
    'is tabulated in the pipe chart. All pipe is reinforced concrete pipe to Gwinnett County standards. '
    'OUTLET DISCHARGE PIPES ARE HELD MORE THAN SIX PIPE DIAMETERS FROM EVERY ADJOINING PROPERTY LINE '
    '(§10.e): OF-1 is %.0f ft and OF-2 is %.0f ft from the southwest line against a 12-ft requirement '
    'for the 24-in outlets. Energy-dissipation calculations for every outfall are required with the '
    'erosion control plan (§12.c).'
    % (OF1_TO_SW, OF2_TO_SW),

    'GRADING NOTES, VERBATIM (checklist §10.a — to appear on all SESPC sheets if clearing/grubbing or '
    'grading are permitted separately). 1. MAXIMUM CUT OR FILL SLOPES IS 2H:1V. 2. CITY OF LILBURN / '
    'GWINNETT COUNTY ASSUMES NO RESPONSIBILITY FOR OVERFLOW OR EROSION OF NATURAL OR ARTIFICIAL DRAINS '
    'BEYOND THE EXTENT OF THE STREET RIGHT-OF-WAY, OR FOR THE EXTENSION OF CULVERTS BEYOND THE POINT '
    'SHOWN ON THE APPROVED AND RECORDED PLAN. THE CITY OF LILBURN / GWINNETT COUNTY DOES NOT ASSUME THE '
    'RESPONSIBILITY FOR THE MAINTENANCE OF PIPES IN DRAINAGE EASEMENTS BEYOND THE CITY / COUNTY '
    'RIGHT-OF-WAY. 3. STRUCTURES ARE NOT ALLOWED IN DRAINAGE EASEMENTS. 4. 12% TO 15% STREET GRADES '
    'REQUIRE AN "AS GRADED" SURVEY BEFORE INSTALLATION OF THE CURB (§7.k).',

    'RETAINING WALLS. NO RETAINING WALL IS PROPOSED. Maximum cut on the lane centreline is %.1f ft and '
    'maximum fill %.1f ft, and every graded slope daylights at 2H:1V or flatter inside the limits of '
    'disturbance, so no wall envelope, hydrostatic design, wall easement or as-built wall certification '
    '(checklist §8) is triggered by this concept. If lot grading at the land disturbance permit stage '
    'introduces a wall, top, bottom and ground elevations must be shown (§10.f) and any wall over 4 ft '
    'must be designed by a Georgia registered professional engineer.'
    % (CUT_MAX_CL, FILL_MAX_CL),

    'SOILS AND ROCK. NRCS SSURGO GA135 maps ARE (Ashlar–Rion–Wateree, gneiss bedrock at 22–40 in) under '
    'BOTH basin sites and the mid-strip swale, and HYB (Helena sandy loam, hydrologic soil group D, '
    'seasonal high water table ≈ 24 in) at the front southwest corner. ROCK PROBES AND TEST PITS AT BOTH '
    'BASINS AND ALONG THE STORM TRUNK ARE REQUIRED BEFORE THE HYDROLOGY BASIS OR THE EARTHWORK BALANCE '
    'IS TRUSTED; an undercut allowance should be carried. Shallow rock at either basin changes the '
    'volume, the depth and the cost, and the alternatives are a third facility at the terminus green or '
    'shallower, longer basins.',

    'EARTHWORK. Cut ≈ %s CY and fill ≈ %s CY inside the limits of disturbance, a net surplus of '
    '≈ %s CY of excavation — most of it the two basins. The centreline itself balances (mean '
    'deviation %+.2f ft); the surplus is to be placed on site in lot pads, buffer berms and topsoil, or '
    'exported. Shrinkage, topsoil stripping, rock and undercut are NOT included, and the quantity is a '
    'concept estimate from an approximate digital elevation model, not a survey.'
    % (format(int(round(CUT_CY)), ','), format(int(round(FILL_CY)), ','),
       format(int(round(CUT_CY - FILL_CY)), ','), DEV_MEAN),

    'PHASING. The phase line is at u = %.0f (data/layout.json). POND 1 and Lines A and B serve Phase 1; '
    'POND 2 and Line C serve Phase 2. Each phase must stand alone hydrologically: the Phase 1 basin, its '
    'outfall and its erosion control must be built and stabilised with Phase 1, and the Phase 2 area '
    'remains undisturbed woodland until Phase 2 begins. Phasing is permitted only if platted in blocks '
    '(checklist §4.i).'
    % (L['phase_line_u'],),

    'RECORD DRAWINGS (checklist §4.a, verbatim). DEVELOPER TO PROVIDE TO CITY CERTIFIED DETENTION '
    'POST-CONSTRUCTION (RECORD) DRAWINGS WITH THE SUBMITTAL OF THE FINAL PLAT OR ONE WEEK PRIOR TO '
    'REQUESTING A CERTIFICATE OF OCCUPANCY, SO THAT THE POST-CONSTRUCTION CONDITIONS MAY BE VERIFIED AND '
    'APPROVED. CERTIFIED RECORD DRAWINGS SHALL INCLUDE TOPOGRAPHY OF POND AND OUTLET STRUCTURE DETAIL '
    'USING POST-CONSTRUCTION SURVEY DATA. USING RECORD DRAWINGS, PROVIDE A CERTIFIED HYDROLOGY REPORT '
    'VERIFYING POND VOLUMES AND PEAK OUTFLOWS FROM REGULATED STORM EVENTS.',

    'PROFILE STATIONS. Existing ground on the profile is data/layout.json lane.ground_profile — '
    '156 stations at 10 ft from u = %.0f to u = %.0f interpolated from the USGS 3DEP model, '
    'APPROXIMATE. The three hammerhead turnarounds at u = 540, 1,110 and 1,690 fall on proposed '
    'grades of %.2f %%, %.2f %% and %.2f %%. Vertical curves are %.0f ft long at each of the three '
    'interior PVIs; sight distance and K-values at the 15-mph design speed, together with the '
    'horizontal alignment and its curve data, belong on Sheet C-5.0.'
    % (U_PROF0, U_PROF1, grade_pct(540.0), grade_pct(1110.0), grade_pct(1690.0), VC_LEN[0]),

    'WHAT IS NOT ON THIS SHEET. Storm sewer profiles and stormwater construction details (Sheet C-3.1); '
    'the soil erosion, sedimentation and pollution control plan and its GSWCC checklist and '
    'certifications; the tree protection plan; sanitary sewer and water (Sheet C-4.0); the private lane '
    'plan and profile with horizontal curve data (Sheet C-5.0). Utility locates through Georgia 811 '
    '(O.C.G.A. §25-9) are required before any field work.',
]


# Two note frames: a four-column block in the empty top band of the plan window, and a tall
# single column at the right of the data band.  flow_notes() picks the largest type size that
# holds the whole note set and never clips.
NOTE_FRAMES = [(840.0, 82.0, 1650.0, 242.0, 4), (1982.0, 900.0, 558.0, 626.0, 1)]


def flow_notes(D, frames, blocks_text):
    for size, lead in ((6.5, 7.6), (6.4, 7.45), (6.3, 7.3), (6.2, 7.15), (6.1, 7.0)):
        cols = []
        for (fx, fy, fw, fh, nc) in frames:
            cw = fw / nc
            for k in range(nc):
                cols.append((fx + k * cw, fy, int((cw - 12) / (0.56 * size)), int(fh / lead)))
        placed, ci, used, ok = [], 0, 0, True
        for t in blocks_text:
            lines = sb.wrap(t, cols[ci][2])
            if used + len(lines) > cols[ci][3]:
                ci += 1
                used = 0
                if ci >= len(cols):
                    ok = False
                    break
                lines = sb.wrap(t, cols[ci][2])
            placed.append((ci, used, lines))
            used += len(lines) + 1
        if ok:
            for ci, row, lines in placed:
                cx, cy, _, _ = cols[ci]
                for j, ln in enumerate(lines):
                    D.stext(cx + (0 if j == 0 else 7), cy + (row + j) * lead, ln, size=size)
            print('  notes     : %d notes flowed into %d columns at %.1f pt'
                  % (len(blocks_text), ci + 1, size))
            return size
    raise RuntimeError('general notes do not fit the note frames')


# =========================================================================== 9. plan layers
def context(c):
    """Screened proposed layout from Sheet C-2.0 — lots, pavement, structures, open space."""
    c.add('<g id="context">')
    for g in L['greens']:
        for p in g['polygons']:
            c.poly([tuple(q) for q in p], fill=sb.C['green'], stroke='#c8d8c0', stroke_width=0.3)
    for p in L['amenity']['tract_polygons']:
        c.poly([tuple(q) for q in p], fill='#eef4e6', stroke='#c8d8c0', stroke_width=0.3)
    ln = L['lane']
    for key in (ln['tract_polygon'], ln['entry_drive']['tract_polygon']):
        c.poly([tuple(p) for p in key], fill='#f4f4f4', stroke=G['ctx'], stroke_width=0.35,
               stroke_dasharray='4 2')
    for key in (ln['pavement_polygon'], ln['entry_drive']['pavement_polygon']):
        c.poly([tuple(p) for p in key], fill='#e6e6e6', stroke='#9a9a9a', stroke_width=0.5)
    for h in L['hammerheads']:
        for leg in h['legs']:
            c.poly([tuple(p) for p in leg], fill='#e6e6e6', stroke='#9a9a9a', stroke_width=0.5)
    for lot in L['lots']:
        c.poly([tuple(p) for p in lot['polygon']], fill='none', stroke=G['ctx'], stroke_width=0.5)
        for k in ('house_rect', 'garage_rect'):
            c.poly([tuple(p) for p in lot[k]], fill='#f0f0f0', stroke=G['ctx'], stroke_width=0.35)
    c.poly([tuple(p) for p in L['amenity']['clubhouse']], fill='#f0f0f0', stroke=G['ctx'],
           stroke_width=0.5)
    c.add('</g>')


def screened_existing(c, labels=True):
    """sitebase's existing 2-ft contours, screened back so the proposed contours read over them."""
    c.add('<g opacity="0.30">')
    sb.contours(c, existing=True, labels=labels)
    c.add('</g>')


def proposed_contours(c, labels=True):
    c.add('<g id="contours-proposed">')
    for lev, lines in sorted(PROP_CONTOURS.items(), key=lambda kv: int(kv[0])):
        idx = int(lev) % 10 == 0
        for lnn in lines:
            c.pline(lnn, fill='none', stroke=G['prop'], stroke_width=(1.9 if idx else 0.8))
    c.add('</g>')
    if not labels:
        return
    for lev, lines in sorted(PROP_CONTOURS.items(), key=lambda kv: int(kv[0])):
        if int(lev) % 10:
            continue
        for lnn in lines:
            if len(lnn) < 8:
                continue
            p = lnn[len(lnn) // 2]
            c.text(p[0], p[1], str(lev), size=6.2, bold=True, fill=G['prop'], halo=True, avoid=True)


def drainage_areas(c):
    c.add('<g id="drainage-areas">')
    for tag, ua, ub, front, col, key, txt in POST:
        poly = band_poly(ua, ub, front)
        c.poly(poly, fill=col, fill_opacity='0.13', stroke=col, stroke_width=1.2,
               stroke_dasharray='14 4 3 4')
    for tag, ua, ub, front, col, txt in PRE:
        if ua > 0:
            c.line((ua, sb.NE(ua)), (ua, sb.SW(ua)), stroke=G['pre'], stroke_width=1.2,
                   stroke_dasharray='9 3 2 3')
    c.add('</g>')


def lod_layer(c):
    c.poly(LOD, fill='none', stroke=G['lod'], stroke_width=1.6, stroke_dasharray='18 4 3 4')


def basins(c):
    c.add('<g id="basins">')
    for p in PONDS:
        c.poly(p['tract_poly'], fill='#eaf1e6', fill_opacity='0.55', stroke=sb.C['green_line'],
               stroke_width=0.4)
        c.poly(p['esmt_poly'], fill='none', stroke=G['esmt'], stroke_width=1.0, stroke_dasharray='7 3')
        c.poly(p['pond_poly'], fill='#dceaf6', stroke=G['pond'], stroke_width=1.4)
        c.poly(p['bottom_poly'], fill='#cfe3f3', stroke=G['pond'], stroke_width=0.7,
               stroke_dasharray='5 3')
        # forebay
        f = p['fb']
        c.poly(sb.rect(f[0], f[1], f[2], f[3]), fill='#bcd7c2', stroke=G['pond'], stroke_width=0.6)
        # earthen embankment crest along the downhill sides (8'-0" minimum top width)
        c.pline(p['dam_path'], fill='none', stroke='#5d4037', stroke_width=2.4)
        # emergency spillway: a 20-ft grassed notch in the embankment away from the OCS
        c.pline(p['spill'], fill='none', stroke='#2e7d32', stroke_width=3.4, stroke_dasharray='3 2')
        # internal baffle berm where the inlet and the outlet share an end
        if p['baffle']:
            c.pline(p['baffle'], fill='none', stroke='#5d4037', stroke_width=1.4,
                    stroke_dasharray='6 3')
        # OCS
        o = p['ocs']
        c.poly(sb.rect(o[0] - 3, o[0] + 3, o[1] - 3, o[1] + 3), fill='#fff', stroke=G['pond'],
               stroke_width=1.2)
        # BMP access easement + 15-ft road
        c.poly(sb.offset_band(p['acc'], 15.0), fill='none', stroke=G['acc'], stroke_width=1.0,
               stroke_dasharray='12 4')
        c.pline(p['acc'], fill='none', stroke=G['acc'], stroke_width=3.2, stroke_dasharray='2 3')
        # outfall: headwall, riprap apron, level spreader
        hw, ap, sp2 = p['hw'], p['apron'], p['spread']
        c.pline([o, hw, ap, sp2], fill='none', stroke=G['storm'], stroke_width=1.8)
        c.poly(sb.rect(ap[0] - 10, ap[0] + 10, ap[1] - 7, ap[1] + 7), fill='url(#rip)',
               stroke=G['storm'], stroke_width=0.5)
        c.line((sp2[0] - 14, sp2[1]), (sp2[0] + 14, sp2[1]), stroke=G['storm'], stroke_width=2.4)
    c.add('</g>')


def storm(c):
    c.add('<g id="storm">')
    for p in PIPES:
        c.line(p['a'], p['b'], stroke=G['storm'], stroke_width=1.8)
    for sid, typ, u, v, note in STRUCT:
        if 'CURB INLET' in typ:
            c.poly(sb.rect(u - 4, u + 4, v - 2.5, v + 2.5), fill=G['storm'], stroke='#fff',
                   stroke_width=0.4)
        elif 'JUNCTION' in typ:
            c.circle((u, v), 3.0, fill='#fff', stroke=G['storm'], stroke_width=1.1)
        else:
            c.poly([(u - 4, v - 4), (u + 4, v - 4), (u, v + 4)], fill=G['storm'], stroke='#fff',
                   stroke_width=0.4)
    c.add('</g>')


def spot_elevs(c, picks):
    for u, v, z, anc in picks:
        c.line((u - 3.5, v), (u + 3.5, v), stroke=G['prop'], stroke_width=0.7)
        c.line((u, v - 3.5), (u, v + 3.5), stroke=G['prop'], stroke_width=0.7)
        c.text(u + (6 if anc == 'start' else -6), v + 8.0, '%.2f' % z, size=6.0, anchor=anc,
               fill=G['prop'], bold=True, halo=True)


# =========================================================================== 10. profile band
def profile_band(D, x0, y0, w, h):
    """Lane profile: 1" = 60' horizontal, 1" = 10' vertical (6:1 exaggeration)."""
    hs = sb.SCALE60
    vs = 72.0 / 10.0
    zlo, zhi = 930.0, 954.0
    px0 = x0 + 46
    py1 = y0 + (zhi - zlo) * vs                    # datum line (z = zlo)

    def X(u):
        return px0 + (u - U_PROF0) * hs

    def Y(z):
        return py1 - (z - zlo) * vs

    D.stext(x0, y0 - 24, 'LANE PROFILE — PRIVATE LANE CENTRELINE, u = %.0f TO u = %.0f'
            % (U_PROF0, U_PROF1), size=12, bold=True)
    D.stext(x0, y0 - 12, 'HORIZONTAL 1" = 60\'   ·   VERTICAL 1" = 10\'   ·   EXAGGERATION 6:1   ·   '
                         'DATUM ELEV. %.0f   ·   NAVD88   ·   DRAFT — NOT SEALED — grading and profile '
                         'design must be sealed by a Georgia PE' % zlo, size=8, fill='#444')
    D.srect(px0, Y(zhi), (U_PROF1 - U_PROF0) * hs, (zhi - zlo) * vs, fill='#fff', stroke='#000',
            stroke_width=1.0)
    z = int(zlo)
    while z <= zhi:
        idx = z % 10 == 0
        D.sline(px0, Y(z), X(U_PROF1), Y(z), stroke='#999' if idx else '#ddd',
                stroke_width=0.6 if idx else 0.25)
        D.stext(px0 - 5, Y(z) + 2.5, str(z), size=6.6, anchor='end', bold=idx)
        D.stext(X(U_PROF1) + 5, Y(z) + 2.5, str(z), size=6.6, anchor='start', bold=idx)
        z += 2
    u = 200.0
    while u <= U_PROF1:
        idx = int(u) % 500 == 0
        D.sline(X(u), Y(zlo), X(u), Y(zhi), stroke='#666' if idx else '#ddd',
                stroke_width=0.6 if idx else 0.25)
        D.stext(X(u), py1 + 12, '%d' % u, size=6.6, anchor='middle', bold=idx)
        u += 100.0
    D.stext(X((U_PROF0 + U_PROF1) / 2.0), py1 + 24, 'u — DISTANCE ALONG THE STRIP FROM THE ARCADO ROAD '
                                                    'RIGHT-OF-WAY CORNER (ft)', size=8,
            anchor='middle', bold=True)
    # existing ground and proposed grade
    us = [U_PROF0 + 5.0 * k for k in range(int((U_PROF1 - U_PROF0) / 5) + 1)]
    D.add('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.6" stroke-dasharray="9 4"/>'
          % (' '.join('%.2f,%.2f' % (X(u), Y(ex_prof(u))) for u in us), sb.C['contour_txt']))
    D.add('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.8"/>'
          % (' '.join('%.2f,%.2f' % (X(u), Y(prof(u))) for u in us), G['prop']))
    # PVI markers, tangent grades, vertical curves
    for i, (pu, pz) in enumerate(PVI):
        D.sline(X(pu), Y(zlo), X(pu), Y(zhi), stroke=G['prop'], stroke_width=0.5,
                stroke_dasharray='4 3')
        D.scircle(X(pu), Y(prof(pu)), 2.8, fill='#fff', stroke=G['prop'], stroke_width=1.3)
        lab = ['PVI %d' % (i + 1), 'u = %.0f' % pu, 'ELEV %.2f' % pz]
        if 0 < i < len(PVI) - 1:
            lab.append('VC = %.0f ft' % VC_LEN[i - 1])
        anc = 'end' if i == len(PVI) - 1 else 'start'
        dx = -5 if anc == 'end' else 5
        yb = Y(zhi) + 10
        D.srect(X(pu) + (dx - 3 if anc == 'start' else dx - 55), yb - 8, 58, 8 + len(lab) * 7.8,
                fill='#fff', fill_opacity='0.9', stroke='none')
        for k, t in enumerate(lab):
            D.stext(X(pu) + dx, yb + k * 7.8, t, size=6.3, bold=(k == 0), fill=G['prop'], anchor=anc)
    for i, g in enumerate(GRADE):
        um = (PVI[i][0] + PVI[i + 1][0]) / 2.0
        D.srect(X(um) - 24, Y(prof(um)) - 18, 48, 12, fill='#fff', fill_opacity='0.85', stroke='none')
        D.stext(X(um), Y(prof(um)) - 9, '%+.2f %%' % (g * 100.0), size=9, bold=True,
                anchor='middle', fill=G['prop'])
    # cut / fill call-outs
    for u in (300.0, 620.0, 830.0, 1160.0, 1470.0, 1650.0):
        d = prof(u) - ex_prof(u)
        if abs(d) < 0.4:
            continue
        D.sline(X(u), Y(ex_prof(u)), X(u), Y(prof(u)), stroke='#555', stroke_width=0.8)
        yy = Y(min(prof(u), ex_prof(u))) + 11
        D.srect(X(u) - 20, yy - 7, 40, 9, fill='#fff', fill_opacity='0.85', stroke='none')
        D.stext(X(u), yy, '%s %.1f\'' % ('FILL' if d > 0 else 'CUT', abs(d)), size=7,
                anchor='middle', fill='#333', bold=True)
    # hammerheads
    for h in L['hammerheads']:
        u = float(h['u'])
        if U_PROF0 <= u <= U_PROF1:
            D.spoly([(X(u), py1), (X(u) - 4.5, py1 + 7), (X(u) + 4.5, py1 + 7)], fill='#555')
    # the existing 11 % reach, called out clear of the lines
    ux = EX_GMAX_U + 5
    D.scircle(X(ux), Y(ex_prof(ux)), 4.2, fill='none', stroke=sb.C['red'], stroke_width=1.4)
    lx, ly = X(ux) - 40, Y(zhi) + 74
    D.sline(X(ux) - 4, Y(ex_prof(ux)) - 4, lx + 6, ly + 3, stroke=sb.C['red'], stroke_width=0.7)
    D.srect(lx - 178, ly - 9, 186, 22, fill='#fff', fill_opacity='0.9', stroke=sb.C['red'],
            stroke_width=0.6)
    D.stext(lx - 6, ly, 'EXISTING GROUND REACHES %.2f %% AT u ≈ %.0f' % (EX_GMAX, ux), size=7.4,
            bold=True, anchor='end', fill=sb.C['red'])
    D.stext(lx - 6, ly + 9, 'PROPOSED GRADE HERE %+.2f %% — MAX. %.2f %% ON THE WHOLE LANE'
            % (grade_pct(ux), abs(PR_GMAX)), size=7.0, anchor='end', fill=sb.C['red'])
    # key, in the empty lower-left of the plot
    kx, ky = px0 + 14, Y(936.4)
    D.srect(kx - 8, ky - 10, 300, 42, fill='#fff', fill_opacity='0.92', stroke='#999',
            stroke_width=0.5)
    D.sline(kx, ky - 3, kx + 26, ky - 3, stroke=sb.C['contour_txt'], stroke_width=1.6,
            stroke_dasharray='9 4')
    D.stext(kx + 31, ky, 'EXISTING GROUND ON THE LANE CENTRELINE (3DEP — approximate)', size=6.8)
    D.sline(kx, ky + 8, kx + 26, ky + 8, stroke=G['prop'], stroke_width=2.8)
    D.stext(kx + 31, ky + 11, 'PROPOSED FINISHED GRADE — lane centreline', size=6.8)
    D.spoly([(kx + 13, ky + 17), (kx + 9, ky + 24), (kx + 17, ky + 24)], fill='#555')
    D.stext(kx + 31, ky + 23, 'Hammerhead turnaround (u = 540 / 1,110 / 1,690)', size=6.8)
    return py1 + 30


# =========================================================================== 11. build
def build():
    scale_note = 'Scale 1" = 60\' (ARCH D 36 × 24 in); profile 1" = 60\' H / 1" = 10\' V'
    D, F = sb.sheet(
        'GRADING, DRAINAGE AND STORMWATER CONCEPT', 'C-3.0',
        'Proposed grading, drainage-area map, detention concept and lane profile — 2026 Application '
        'Instructions item 8; City of Lilburn Site Development Plan Review Checklist §4.e, §7, §10, §11',
        scale_note, generator='tools/sitebase.py + tools/grading.py',
        north_at=(F0 := (2400.0, 780.0)), scale_at=(1470.0, 812.0),
        status_lines=[
            'Concept grading and drainage for pre-application review. Existing',
            'topography is USGS 3DEP (approximate) — a topographic survey is',
            'required and governs. Grading, hydrology, hydraulics and the',
            'detention design must be sealed by a Georgia PE. NOT FOR CONSTRUCTION.'])
    del F0
    # sitebase queues an "EXISTING CONDITIONS OF RECORD" watermark for Sheet C-0; this sheet
    # shows proposed work, so that queued layer is replaced (sitebase itself is not modified).
    D.late.pop(1)
    px, py, pw, ph = F['plan']
    D.later(lambda: D.add('<text x="%.1f" y="%.1f" font-size="34" fill="#c00" fill-opacity="0.10" '
                          'font-weight="bold" text-anchor="middle" transform="rotate(-8 %.1f %.1f)">'
                          'DRAFT — NOT SEALED — CONCEPT GRADING AND DRAINAGE, NOT FOR CONSTRUCTION</text>'
                          % (px + pw / 2, py + ph - 38, px + pw / 2, py + ph - 38)))
    D.add('<defs><pattern id="rip" patternUnits="userSpaceOnUse" width="7" height="7">'
          '<rect width="7" height="7" fill="#eceff1"/>'
          '<circle cx="2" cy="2" r="1.1" fill="none" stroke="#00695c" stroke-width="0.4"/>'
          '<circle cx="5.5" cy="5" r="1.1" fill="none" stroke="#00695c" stroke-width="0.4"/>'
          '</pattern></defs>')

    # ---------------------------------------------------------------- plan
    D.clip_open(fill='#fff')
    sb.adjoiners(D, labels=False, zoning=False)
    sb.arcado_row(D, labels=False)
    context(D)
    drainage_areas(D)
    screened_existing(D, labels=True)
    proposed_contours(D, labels=True)
    sb.streams_and_buffers(D, labels=False)
    sb.sewer_existing(D, labels=False, easement=False)
    sb.existing_structures(D, labels=False)
    basins(D)
    storm(D)
    lod_layer(D)
    sb.boundary(D, bearings=False, label=False)

    spot_elevs(D, [
        (ENTRY_RW[0] + 16, ENTRY_RW[1], ENTRY_Z0, 'start'),
        (150.0, vc(150.0), prof(150.0), 'start'),
        (830.0, vc(830.0), prof(830.0), 'start'),
        (1160.0, vc(1160.0), prof(1160.0), 'start'),
        (1470.0, vc(1470.0), prof(1470.0), 'start'),
        (1699.0, vc(1699.0), prof(1699.0), 'end'),
        (PONDS[0]['u0'] + 22, PONDS[0]['v0'] + 26, PONDS[0]['bottom'], 'start'),
        (PONDS[1]['u0'] + 22, PONDS[1]['v0'] + 26, PONDS[1]['bottom'], 'start'),
    ])

    # --- plan annotation: drainage areas, basins, outfalls, structures
    for tag, ua, ub, front, col, key, txt in POST:
        um = (max(ua, 0) + ub) / 2.0
        D.textlines(um, sb.NE(um) - 26, ['%s → %s' % (tag, 'ARCADO RD R/W' if key == 0 else 'POND %d' % key),
                                         '%.2f ac gross / %.2f ac disturbed'
                                         % (_band_area(ua, ub, front) / 43560.0, BASIN_AC[key])],
                    size=7, gap=1.2, bold_first=True, fill=col, halo=True)
    for tag, ua, ub, front, col, txt in PRE:
        if ua > 0:
            D.text(ua, sb.SW(ua) + 30, 'PRE-DEVELOPMENT DIVIDE  u = %.0f' % ua, size=6.4, rot=-81,
                   fill=G['pre'], halo=True)
    D.text(60, -294, 'PRE-DEVELOPMENT DRAINAGE: the strip falls northeast to southwest across its whole '
                     'length; PRE-A, PRE-B and PRE-C all leave the site on the southwest line, PRE-A and '
                     'PRE-B to the off-site branch 38–58 ft outside that line and PRE-C to the on-site '
                     'headwater channel.', size=7.5, bold=True, fill=G['pre'], halo=True, anchor='start')

    for p in PONDS:
        u0, u1, v0, v1 = p['u0'], p['u1'], p['v0'], p['v1']
        lines = ['%s — DRY EXTENDED-DETENTION / WATER-QUALITY BASIN' % p['name'],
                 'TOP OF BANK = 100-YR PONDING ELEV. %.2f   ·   BOTTOM %.2f   ·   6.0 ft, 3:1'
                 % (p['tob'], p['bottom']),
                 'EMBANKMENT CREST %.2f (8\'-0" MIN. TOP WIDTH)   ·   FREEBOARD 1\'-6"' % p['dam'],
                 'EMERG. SPILLWAY CREST %.2f, 20 ft WIDE, GRASSED' % p['spillway'],
                 'STORAGE %s CF TO THE 100-YR LIMIT (data/layout.json)' % format(p['storage_cf'], ','),
                 'TOP OF BANK %s ft   ·   FOREBAY %.0f × %.0f ft, %.0f ft DEEP = %s CF PROVIDED '
                 'vs %s CF REQUIRED (10 %% OF WQv, §11.i.15)'
                 % (p['tob_dims'], p['fb'][1] - p['fb'][0], p['fb'][3] - p['fb'][2], p['fb_depth'],
                    format(int(p['fb_vol']), ','), format(int(round(p['fb_req'])), ',')),
                 "30' BMP ACCESS EASEMENT, 15' ROAD AT ≤ 20 % TO THE BASIN BOTTOM AT THE OCS",
                 '(§11.i.2, §11.i.3) — ACCESS EASEMENT TO BE CLEARED AND GRUBBED (§11.i.4)',
                 "10' DRAINAGE EASEMENT OUTSIDE THE 100-YR PONDING LIMIT (§11.i.12)",
                 'FLOW PATH: %s' % p['flow']]
        D.textlines(u0 - 6, v0 - 46, lines, size=6.6, gap=1.24,
                    bold_first=True, fill=G['pond'], halo=True, anchor='start')
        D.line((u0 + 40, v0 - 44), (u0 + 40, v0 - 4), stroke=G['pond'], stroke_width=0.5)

        D.text((u0 + u1) / 2.0 + 34, v0 + 13, p['name'], size=9, bold=True, fill=G['pond'],
               halo=True)
        D.text(p['ocs'][0] + 7, p['ocs'][1] + 1, 'OCS', size=6.2, bold=True, fill=G['pond'],
               anchor='start', halo=True)
        D.text((p['fb'][0] + p['fb'][1]) / 2.0, (p['fb'][2] + p['fb'][3]) / 2.0 + 2, 'FOREBAY',
               size=6.0, bold=True, fill='#1b5e20', halo=True)
        am = p['acc'][1]
        anc = 'start' if p['n'] == 1 else 'end'
        sgn = 1 if p['n'] == 1 else -1
        D.line((am[0] + sgn * 6, am[1] + 3), (am[0] + sgn * 26, am[1] + 3), stroke=G['acc'],
               stroke_width=0.6)
        D.poly([(am[0] + sgn * 5, am[1] + 3), (am[0] + sgn * 13, am[1] - 1),
                (am[0] + sgn * 13, am[1] + 7)], fill=G['acc'], stroke='none')
        D.textlines(am[0] + sgn * 28, am[1] + 1,
                    ["30' BMP ACCESS EASEMENT — 15' ROAD AT ≤ 20 %",
                     'ACCESS EASEMENT TO BE CLEARED AND GRUBBED'],
                    size=6.3, gap=1.24, fill=G['acc'], anchor=anc, halo=True, bold_first=True)
        D.text(u0 - 12, v0 - 6, "10' DRAIN. ESMT (§11.i.12)", size=6.2, fill=G['esmt'],
               anchor='end', halo=True)
        dm = p['dam_path'][1]
        D.line((dm[0], dm[1] + 12), (dm[0] - 14, dm[1] + 16), stroke='#5d4037', stroke_width=0.5)
        D.text(dm[0] - 16, dm[1] + 18, 'EARTHEN EMBANKMENT — CREST %.2f, 8\'-0" MIN. TOP WIDTH'
               % p['dam'], size=6.3, bold=True, fill='#5d4037', anchor='end', halo=True)
        sp = p['spill']
        spm = ((sp[0][0] + sp[1][0]) / 2.0, (sp[0][1] + sp[1][1]) / 2.0)
        lt = (spm[0], spm[1] - 16) if p['n'] == 1 else (spm[0] - 18, spm[1] - 46)
        D.line(spm, lt, stroke='#1b5e20', stroke_width=0.5)
        D.text(lt[0], lt[1] - 2, 'EMERG. SPILLWAY %.2f' % p['spillway'], size=6.2, bold=True,
               fill='#1b5e20', anchor='middle' if p['n'] == 1 else 'end', halo=True)
        if p['baffle']:
            D.text((p['baffle'][0][0] + p['baffle'][1][0]) / 2.0,
                   (p['baffle'][0][1] + p['baffle'][1][1]) / 2.0 + 5,
                   'BAFFLE BERM — FLOW PATH (§11.i.13)', size=6.0, bold=True, fill='#5d4037',
                   halo=True)
        D.text(p['spread'][0] - 26, p['spread'][1] - 32,
               'OF-%d HEADWALL, RIPRAP APRON AND LEVEL SPREADER — NO DIRECT DISCHARGE TO THE BUFFER '
               'OR TO ANY ADJOINING YARD' % p['n'], size=6.3, bold=True, fill=G['storm'],
               anchor='end', halo=True)

    LAB_DX = {'C-5': (16, -2), 'C-4': (-9, 11), 'A-7': (16, -2), 'A-1': (0, 10), 'A-1B': (0, 10)}
    for sid, typ, u, v, note in STRUCT:
        if sid.startswith('OF'):
            continue
        dx, dv = LAB_DX.get(sid, (0, -9))
        D.text(u + dx, v + dv, sid, size=6.3, bold=True, fill=G['storm'], halo=True,
               anchor='start' if dx > 0 else ('end' if dx < 0 else 'middle'))
    D.text(430, -182, 'STORM LINE A — 24" RCP TRUNK, ENTRANCE TO POND 1', size=6.6, bold=True,
           fill=G['storm'], halo=True)
    D.text(1075, -182, 'LINE B — 18" RCP', size=6.6, bold=True, fill=G['storm'], halo=True)
    D.text(1310, -182, 'LINE C — 18"/24" RCP', size=6.6, bold=True, fill=G['storm'], halo=True)
    D.text(60, -278, 'LIMITS OF DISTURBANCE — %s SF = %.3f ac (data/layout.json, 2026-09-03). '
                     'NO OFF-SITE DISTURBANCE IS PROPOSED.' % (format(DIST_SF_PUB, ','), DIST_AC_PUB),
           size=7.5, bold=True, fill=G['lod'], halo=True, anchor='start')
    D.text(1470, -258, 'PRESERVED CREEK WOODS AND STREAM BUFFERS — NO GRADING, NO IMPERVIOUS SURFACE',
           size=7, bold=True, fill=sb.C['stream'], halo=True, anchor='end')
    D.line((1392.0, -212.0), (1436.0, -268.0), stroke=sb.C['stream'], stroke_width=0.5)
    D.text(1470, -272, 'STREAM HEAD (u 1,392, v −210) — FIELD DELINEATION REQUIRED', size=6.6,
           fill=sb.C['stream'], halo=True, anchor='end')
    D.text(60, -262, 'ALL RUNOFF DISCHARGES TO THE HEADWATERS OF JACKSON CREEK — GAR030701030315, '
                     "GEORGIA'S 2024 303(d) LIST, NOT SUPPORTING (BACTERIA, BIOTA; URBAN RUNOFF)",
           size=8, bold=True, fill=sb.C['stream'], halo=True, anchor='start')
    D.clip_close()

    # ------------------------------------------------- grading-plan notes, verbatim (checklist §10.a)
    gx, gy, gw = 318.0, 706.0, 884.0
    D.srect(gx - 8, gy - 8, gw + 16, 112, fill='#fff', fill_opacity='0.95', stroke='#000',
            stroke_width=0.8)
    D.stext(gx, gy + 5, 'GRADING PLAN NOTES — City of Lilburn Site Development Plan Review Checklist '
                        '§10.a and §7.k, VERBATIM', size=8.5, bold=True)
    yy = gy + 18
    for t in [
        '1.  MAXIMUM CUT OR FILL SLOPES IS 2H:1V.',
        '2.  CITY OF LILBURN / GWINNETT COUNTY ASSUMES NO RESPONSIBILITY FOR OVERFLOW OR EROSION OF '
        'NATURAL OR ARTIFICIAL DRAINS BEYOND THE EXTENT OF THE STREET RIGHT-OF-WAY, OR FOR THE '
        'EXTENSION OF CULVERTS BEYOND THE POINT SHOWN ON THE APPROVED AND RECORDED PLAN. THE CITY OF '
        'LILBURN / GWINNETT COUNTY DOES NOT ASSUME THE RESPONSIBILITY FOR THE MAINTENANCE OF PIPES IN '
        'DRAINAGE EASEMENTS BEYOND THE CITY / COUNTY RIGHT-OF-WAY.',
        '3.  STRUCTURES ARE NOT ALLOWED IN DRAINAGE EASEMENTS.',
        '4.  12% TO 15% STREET GRADES REQUIRE AN "AS GRADED" SURVEY BEFORE INSTALLATION OF THE CURB.',
        'These notes are to appear on all soil erosion, sedimentation and pollution control sheets if '
        'clearing / grubbing or grading are permitted separately.',
    ]:
        yy = D.stextblock(gx, yy, t, size=6.8, chars=int((gw - 8) / (0.56 * 6.8)), lead=8.4,
                          indent=13, bold=not t.startswith('These'))
        yy += 1.6

    # ---------------------------------------------------------------- legend (in the plan window)
    lx, ly, lw, lh = 116.0, 62.0, 700.0, 262.0
    D.srect(lx - 8, ly - 8, lw + 16, lh + 12, fill='#fff', fill_opacity='0.95', stroke='#000',
            stroke_width=0.8)
    D.stext(lx, ly + 6, 'LEGEND — every symbol drawn on this sheet appears here; no unused entry',
            size=8.5, bold=True)
    half = (len(LEGEND) + 1) // 2
    for i, (kind, col, wdt, dash, txt) in enumerate(LEGEND):
        cx = lx + (0 if i < half else lw / 2.0)
        yy = ly + 22 + (i % half) * 14.0
        if kind == 'line':
            D.sline(cx, yy - 3, cx + 30, yy - 3, stroke=col, stroke_width=wdt, stroke_dasharray=dash)
        elif kind == 'dot':
            D.scircle(cx + 15, yy - 3, 3.0, fill='#fff', stroke=col, stroke_width=1.1)
        elif kind == 'sq':
            D.srect(cx + 7, yy - 6, 16, 6, fill=col, stroke='#fff', stroke_width=0.4)
        elif kind == 'ocs':
            D.srect(cx + 10, yy - 8, 10, 10, fill='#fff', stroke=col, stroke_width=1.2)
        elif kind == 'tri':
            D.spoly([(cx + 8, yy), (cx + 22, yy), (cx + 15, yy - 8)], fill=col)
        elif kind == 'plus':
            D.sline(cx + 10, yy - 3, cx + 20, yy - 3, stroke=col, stroke_width=0.8)
            D.sline(cx + 15, yy - 8, cx + 15, yy + 2, stroke=col, stroke_width=0.8)
        else:
            D.srect(cx, yy - 9.5, 30, 12, fill=col, stroke='#555', stroke_width=0.4)
        D.stext(cx + 36, yy, txt, size=6.7)

    f1 = NOTE_FRAMES[0]
    D.srect(f1[0] - 10, 54.0, f1[2] + 18, f1[3] + 34, fill='#fff', fill_opacity='0.95',
            stroke='#000', stroke_width=0.8)

    # ---------------------------------------------------------------- band: tables
    y0 = sb.BAND_Y0
    x = F['inner_l']
    ya = sb.table(D, x, y0, ['STR.', 'TYPE', 'LOCATION (u, v)', 'RIM / GRADE', 'DESCRIPTION / LOCATION'],
                  struct_rows(), size=6.5, widths=[38, 116, 74, 58, 242],
                  title='STORM STRUCTURE SCHEDULE — concept, checklist §10.c (rim elevations read from '
                        'the proposed surface of this sheet)')
    y1 = sb.table(D, x, ya + 20, ['REACH', 'PIPE', 'LENGTH', 'SLOPE %', 'INV. UP', 'INV. DN', 'COVER ft'],
                  pipe_rows(), size=6.5, widths=[84, 60, 46, 46, 52, 52, 52],
                  title='PIPE CHART — concept sizes and slopes; final design by the PE')
    D.stext(x, y1 + 11, 'Cover is measured from the structure rim to the top of the pipe barrel. All '
                        'pipe reinforced concrete to Gwinnett County standards.', size=6.2, fill='#444')

    x2 = x + 570
    yb = sb.table(D, x2, y0, ['AREA', 'COND.', 'EXTENT (u, ft)', 'GROSS ac', 'DISTURBED ac',
                              'IMPERVIOUS', 'RECEIVING SYSTEM / FACILITY'],
                  da_rows(), size=6.5, widths=[46, 40, 78, 50, 62, 90, 336],
                  title='DRAINAGE AREA SUMMARY — PRE- AND POST-DEVELOPMENT (divides interpreted from '
                        'the 3DEP model; confirm against the topographic survey)')
    D.stext(x2, yb + 11, 'Gross areas are measured inside the boundary between the u-limits shown; '
                         'disturbed areas are the part of each inside the limits of disturbance, scaled '
                         'so the three post-development areas', size=6.2, fill='#444')
    D.stext(x2, yb + 20, 'sum to the published %s SF. PRE-A, PRE-B and PRE-C are the three existing '
                         'sub-basins; the strip falls northeast to southwest along its whole length and '
                         'all three leave the site on the southwest line.'
            % format(DIST_SF_PUB, ','), size=6.2, fill='#444')
    yc = sb.table(D, x2, yb + 40, ['BASIN', 'TOP OF BANK', 'BOTTOM', 'TOB / 100-YR', 'DAM',
                                   'SPILLWAY', 'STORAGE CF', 'REQ. CF', 'TRIB. ac',
                                   'FOREBAY CF prov/req'],
                  basin_rows(), size=6.5, widths=[44, 66, 44, 62, 40, 50, 58, 52, 46, 84],
                  title='DETENTION BASIN DATA — checklist §11.i')
    D.stext(x2, yc + 12, 'Storage is the prismoidal volume between top of bank and basin bottom at 6-ft '
                         'depth and 3:1 side slopes, read from data/layout.json. Top of bank is set at '
                         'the 100-year ponding limit and the', size=6.3, fill='#444')
    D.stext(x2, yc + 21, 'embankment crest 1\'-6" above it (checklist §11.i.8). REQ. CF = %s CF per '
                         'disturbed acre × the basin\'s tributary disturbed acreage — see general note 9 '
                         'on the split between the two basins.' % format(int(DET_RATE), ','),
            size=6.3, fill='#444')

    x3 = x + 1290
    sb.table(D, x3, y0, ['ITEM', 'VALUE / BASIS'], SW_ROWS, size=6.5, widths=[126, 496],
             title='STORMWATER MANAGEMENT SUMMARY — GCSWMM basis (checklist §11)')

    # ---------------------------------------------------------------- band: profile
    profile_band(D, x, 1312.0, 1900.0, 0.0)

    # ---------------------------------------------------------------- general notes (two frames)
    D.stext(NOTE_FRAMES[0][0], 68.0,
            'GENERAL NOTES — GRADING, DRAINAGE AND STORMWATER  (the checklist cited throughout is the '
            'City of Lilburn Site Development Plan Review Checklist; notes continue at the right of '
            'the sheet)', size=8.5, bold=True)
    D.stext(NOTE_FRAMES[1][0], 890.0, 'GENERAL NOTES (CONTINUED)', size=8.5, bold=True)
    flow_notes(D, NOTE_FRAMES, ['%d. %s' % (i, _fill(n)) for i, n in enumerate(NOTES, 1)])
    return D


def _fill(t):
    return ' '.join(str(t).split())


if __name__ == '__main__':
    D = build()
    svg, png = sb.save(D, 'grading-drainage', dpi=150)
    print('wrote %s\n      %s' % (svg, png))
    print('  profile   : existing max %.2f%% at u=%.0f; proposed max %.2f%% at u=%.0f; '
          'max deviation %.2f ft at u=%.0f; mean %+.3f ft'
          % (EX_GMAX, EX_GMAX_U + 5, PR_GMAX, PR_GMAX_U + 5, DEV_MAX[1], DEV_MAX[0], DEV_MEAN))
    print('  grades    : ' + ', '.join('%+.2f%%' % (g * 100) for g in GRADE))
    print('  earthwork : cut %.0f CY, fill %.0f CY (grid %d x %d at %.0f x %.0f ft)'
          % (CUT_CY, FILL_CY, len(GX), len(GY), GX[1] - GX[0], GY[1] - GY[0]))
    print('  disturbed : drawn LOD %.0f SF = %.3f ac; published %d SF = %.3f ac'
          % (DIST_SF, DIST_AC_DRAWN, DIST_SF_PUB, DIST_AC_PUB))
    print('  detention : required %d CF, provided %d CF (%.1f%%)'
          % (DET_REQ, DET_PROV, 100.0 * DET_PROV / DET_REQ))
    for p in PONDS:
        print('  pond %d    : trib %.2f ac -> %d CF required, %d CF provided'
              % (p['n'], BASIN_AC[p['n']], BASIN_REQ[p['n']], p['storage_cf']))
    print('  contours  : %d proposed levels, %d polylines'
          % (len(PROP_CONTOURS), sum(len(v) for v in PROP_CONTOURS.values())))
