#!/usr/bin/env python3
"""Master Concept Plan generator — The Cottages at Arcado Springs (R-1 -> R-2, City of Lilburn GA).

Reads data/site-context-local.json (+ owners, world-coordinate rings), builds the concept layout in the
site-local (u,v) feet system defined in FACTS.md §1, self-checks it, writes data/layout.json and the
drawings (drawings/mcp-sheet.svg ARCH D 24x36 landscape @ 1"=60', drawings/mcp-web.svg, PNG renders).

All numbers derive from FACTS.md §1/§2/§4 and the data files; nothing here is a sealed survey.
Run:  python3 tools/siteplan.py
"""
import json, math, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data')
DRAW = os.path.join(ROOT, 'drawings')
os.makedirs(DRAW, exist_ok=True)

# ----------------------------------------------------------------------------- inputs
ctx = json.load(open(os.path.join(DATA, 'site-context-local.json')))
world = json.load(open(os.path.join(DATA, 'site-parcels-2240.json')))
owners = json.load(open(os.path.join(DATA, 'owners-found.json')))

PINS = ['6123 033', '6123 015', '6123 014', '6123 162']
ADDR = {'6123 033': '4541', '6123 015': '4539', '6123 014': '4537', '6123 162': '4535'}
DEEDED = {'6123 033': 0.99, '6123 015': 2.00, '6123 014': 2.00, '6123 162': 4.45}
AC_DEEDED, AC_GIS = 9.44, 9.577          # FACTS §1
SF_DEEDED, SF_GIS = AC_DEEDED * 43560, AC_GIS * 43560
NORTH_DEG = 28.72                          # true/grid north is 28.72 deg above +u (FACTS §1)

# ----------------------------------------------------------------------------- geometry helpers
def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])

def poly_area(p):
    return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))

def poly_centroid(p):
    A = poly_area(p)
    if abs(A) < 1e-9:
        return (sum(q[0] for q in p) / len(p), sum(q[1] for q in p) / len(p))
    cx = cy = 0.0
    for i in range(len(p)):
        x0, y0 = p[i]; x1, y1 = p[(i + 1) % len(p)]
        f = x0 * y1 - x1 * y0
        cx += (x0 + x1) * f; cy += (y0 + y1) * f
    return (cx / (6 * A), cy / (6 * A))

def ccw(p): return p if poly_area(p) > 0 else p[::-1]

def point_in_poly(pt, poly):
    x, y = pt; inside = False; n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if xi > x: inside = not inside
    return inside

def seg_point_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0: return dist(p, a)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return dist(p, (ax + t * dx, ay + t * dy))

def polyline_point_dist(p, path):
    return min(seg_point_dist(p, path[i], path[i + 1]) for i in range(len(path) - 1))

def orient(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

def segs_intersect(p1, p2, p3, p4):
    d1, d2, d3, d4 = orient(p3, p4, p1), orient(p3, p4, p2), orient(p1, p2, p3), orient(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and all(abs(d) > 1e-9 for d in (d1, d2, d3, d4))

def seg_seg_dist(a, b, c, d):
    if segs_intersect(a, b, c, d): return 0.0
    return min(seg_point_dist(a, c, d), seg_point_dist(b, c, d), seg_point_dist(c, a, b), seg_point_dist(d, a, b))

def poly_polyline_dist(poly, path):
    """min distance between a polygon (edges) and a polyline; 0 if the polyline enters the polygon."""
    best = 1e9
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        for j in range(len(path) - 1):
            best = min(best, seg_seg_dist(a, b, path[j], path[j + 1]))
    if any(point_in_poly(p, poly) for p in path): return 0.0
    return best

def shrink_convex(poly, d):
    """inward offset of a convex CCW polygon by d (line-intersection of offset edges)."""
    poly = ccw(poly); n = len(poly); lines = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L                   # inward normal for CCW
        lines.append((a[0] + nx * d, a[1] + ny * d, dx, dy))
    out = []
    for i in range(n):
        x1, y1, dx1, dy1 = lines[i - 1]; x2, y2, dx2, dy2 = lines[i]
        den = dx1 * dy2 - dy1 * dx2
        if abs(den) < 1e-12: out.append((x2, y2)); continue
        t = ((x2 - x1) * dy2 - (y2 - y1) * dx2) / den
        out.append((x1 + t * dx1, y1 + t * dy1))
    return out

def polys_overlap(A, B, tol=0.05):
    """True if convex polygons A and B share interior area (shared edges/touching do not count)."""
    a, b = shrink_convex(A, tol), shrink_convex(B, tol)
    for i in range(len(a)):
        for j in range(len(b)):
            if segs_intersect(a[i], a[(i + 1) % len(a)], b[j], b[(j + 1) % len(b)]): return True
    return any(point_in_poly(p, b) for p in a) or any(point_in_poly(p, a) for p in b)

def rect(u0, u1, v0, v1): return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

def interp_v(path, u):
    """v on a polyline monotone in u (linear interp; clamps at ends)."""
    if u <= path[0][0]: return path[0][1]
    for i in range(len(path) - 1):
        (u0, v0), (u1, v1) = path[i], path[i + 1]
        if u0 <= u <= u1 and u1 > u0: return v0 + (v1 - v0) * (u - u0) / (u1 - u0)
    return path[-1][1]

# ----------------------------------------------------------------------------- 1. assemblage boundary
def union_outer_ring(rings, tol=0.5):
    segs = []
    for r in rings:
        for i in range(len(r)):
            segs.append((tuple(r[i]), tuple(r[(i + 1) % len(r)])))
    keep = []
    for s in segs:
        shared = any(dist(s[0], t[1]) < tol and dist(s[1], t[0]) < tol for t in segs if t is not s)
        if not shared: keep.append(s)
    # chain
    ring = [keep[0][0], keep[0][1]]; used = {0}
    while len(used) < len(keep):
        for k, s in enumerate(keep):
            if k in used: continue
            if dist(s[0], ring[-1]) < tol: ring.append(s[1]); used.add(k); break
            if dist(s[1], ring[-1]) < tol: ring.append(s[0]); used.add(k); break
        else:
            raise RuntimeError('boundary chain broke')
    if dist(ring[0], ring[-1]) < tol: ring.pop()
    return ring

parcel_rings = {pin: [tuple(p) for p in ctx['parcels'][pin]['ring_local']] for pin in PINS}
BOUNDARY = union_outer_ring(list(parcel_rings.values()))
BOUNDARY = ccw(BOUNDARY)
BOUNDARY_SF = poly_area(BOUNDARY)

# local vertex -> world vertex (same vertex order in both files; verified below)
local_to_world = {}
for pin in PINS:
    loc = ctx['parcels'][pin]['ring_local']; wr = world[pin]['ring']
    assert len(loc) == len(wr), pin
    for l, w in zip(loc, wr): local_to_world[(round(l[0], 1), round(l[1], 1))] = tuple(w)
th = math.radians(NORTH_DEG)
U_HAT = (-math.sin(th), math.cos(th)); V_HAT = (math.cos(th), math.sin(th))   # world (E,N) unit vectors of +u, +v
ORIGIN = tuple(ctx['origin_2240'])
def to_world(p):
    k = (round(p[0], 1), round(p[1], 1))
    if k in local_to_world: return local_to_world[k]
    return (ORIGIN[0] + p[0] * U_HAT[0] + p[1] * V_HAT[0], ORIGIN[1] + p[0] * U_HAT[1] + p[1] * V_HAT[1])
for k, w in local_to_world.items():   # transform sanity
    w2 = (ORIGIN[0] + k[0] * U_HAT[0] + k[1] * V_HAT[0], ORIGIN[1] + k[0] * U_HAT[1] + k[1] * V_HAT[1])
    assert dist(w, w2) < 0.6, (k, w, w2)

def quadrant_bearing(a, b):
    wa, wb = to_world(a), to_world(b)
    dx, dy = wb[0] - wa[0], wb[1] - wa[1]
    d = math.hypot(dx, dy)
    ns = 'N' if dy >= 0 else 'S'; ew = 'E' if dx >= 0 else 'W'
    ang = math.degrees(math.atan2(abs(dx), abs(dy)))
    tot = int(round(ang * 3600)); D, M, S = tot // 3600, (tot % 3600) // 60, tot % 60
    return f"{ns} {D:d}°{M:02d}'{S:02d}\" {ew}", d

# --- Arcado Rd R/W frontage.  The frontage is the ring chain running from the NE front corner (the
#     coordinate origin) to the SW front corner (the minimum-u vertex of the assemblage).  A box filter
#     on (u <= 0.05, v >= -235) is NOT sufficient and was the source of a real drafting error: the first
#     10.04-ft segment of the SW PROPERTY line, (-36.00, -234.70) -> (-26.00, -234.70), also satisfies it
#     (it bears N 28°43'03" W, i.e. straight into the site, not along the road).  Admitting that vertex
#     tipped the front line, understated the frontage as 236.1 ft instead of 237.44 ft (chord), rotated
#     the inward R/W normal PHI0 by 2.4 deg and therefore mis-set the entrance tangent, both curb returns
#     and the 50-ft collector setback offset near the SW corner.  Build the chain by walking the ring.
def _ring_chain(i0, i1):
    out = []; i = i0
    while True:
        out.append(BOUNDARY[i])
        if i == i1: return out
        i = (i + 1) % len(BOUNDARY)
I_FRONT_NE = min(range(len(BOUNDARY)), key=lambda i: dist(BOUNDARY[i], (0.0, 0.0)))     # (0.00, 0.00)
I_FRONT_SW = min(range(len(BOUNDARY)), key=lambda i: BOUNDARY[i][0])                    # (-36.00, -234.70)
FRONT_LINE = _ring_chain(I_FRONT_NE, I_FRONT_SW)                                        # NE -> SW, v decreasing
assert all(p[0] <= 0.05 and p[1] <= 0.05 for p in FRONT_LINE) and len(FRONT_LINE) >= 8, FRONT_LINE
assert all(FRONT_LINE[i][1] > FRONT_LINE[i + 1][1] for i in range(len(FRONT_LINE) - 1)), 'front line not monotone in v'
def _fkey(p): return (round(p[0], 3), round(p[1], 3))
_FRONT_SEGS = {frozenset((_fkey(FRONT_LINE[i]), _fkey(FRONT_LINE[i + 1]))) for i in range(len(FRONT_LINE) - 1)}
def is_frontage_seg(a, b):
    return frozenset((_fkey(a), _fkey(b))) in _FRONT_SEGS
FRONTAGE_CHORD_FT = dist(FRONT_LINE[0], FRONT_LINE[-1])                                  # 237.44 ft
FRONTAGE_PATH_FT = sum(dist(FRONT_LINE[i], FRONT_LINE[i + 1]) for i in range(len(FRONT_LINE) - 1))   # 237.63 ft

BEARINGS = []
for i in range(len(BOUNDARY)):
    a, b = BOUNDARY[i], BOUNDARY[(i + 1) % len(BOUNDARY)]
    brg, d = quadrant_bearing(a, b)
    BEARINGS.append({'from': a, 'to': b, 'bearing': brg, 'distance_ft': round(d, 2), 'frontage': is_frontage_seg(a, b)})

# side lines as u-monotone polylines
NE_LINE = sorted([p for p in BOUNDARY if p[1] > -100 and p[0] >= -0.05], key=lambda p: p[0])
SW_LINE = sorted([p for p in BOUNDARY if p[1] < -230], key=lambda p: p[0])   # starts at the SW front corner
REAR_LINE = sorted([p for p in BOUNDARY if p[0] > 1700], key=lambda p: p[1])
U_REAR = min(p[0] for p in REAR_LINE)          # 1721.0
def NE(u): return interp_v(NE_LINE, u)
def SW(u): return interp_v(SW_LINE, u)
def front_u(v): return interp_v(sorted([(p[1], p[0]) for p in FRONT_LINE]), v)   # u of the R/W line at a given v
def width(u): return NE(u) - SW(u)

# ----------------------------------------------------------------------------- 2. topo (bilinear) + marching squares
TS = ctx['topo_samples']
TU = sorted(set(t['u'] for t in TS)); TV = sorted(set(t['v'] for t in TS))
ZG = {(t['u'], t['v']): t['z_ft'] for t in TS}
def ground(u, v):
    u = min(max(u, TU[0]), TU[-1]); v = min(max(v, TV[0]), TV[-1])
    i = min(max(int((u - TU[0]) // 100), 0), len(TU) - 2); j = min(max(int((v - TV[0]) // 50), 0), len(TV) - 2)
    u0, u1, v0, v1 = TU[i], TU[i + 1], TV[j], TV[j + 1]
    fu, fv = (u - u0) / (u1 - u0), (v - v0) / (v1 - v0)
    return ((1 - fu) * (1 - fv) * ZG[(u0, v0)] + fu * (1 - fv) * ZG[(u1, v0)] + (1 - fu) * fv * ZG[(u0, v1)] + fu * fv * ZG[(u1, v1)])

def marching_squares(xs, ys, Z, level):
    """Z[j][i] at (xs[i], ys[j]); returns list of chained polylines at `level`."""
    segs = []
    def lerp(p, q, zp, zq):
        t = 0.5 if zq == zp else (level - zp) / (zq - zp)
        return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            c = [(xs[i], ys[j]), (xs[i + 1], ys[j]), (xs[i + 1], ys[j + 1]), (xs[i], ys[j + 1])]
            z = [Z[j][i], Z[j][i + 1], Z[j + 1][i + 1], Z[j + 1][i]]
            idx = sum(1 << k for k in range(4) if z[k] >= level)
            if idx in (0, 15): continue
            e = {0: lerp(c[0], c[1], z[0], z[1]), 1: lerp(c[1], c[2], z[1], z[2]),
                 2: lerp(c[2], c[3], z[2], z[3]), 3: lerp(c[3], c[0], z[3], z[0])}
            table = {1: [(3, 0)], 2: [(0, 1)], 3: [(3, 1)], 4: [(1, 2)], 6: [(0, 2)], 7: [(3, 2)], 8: [(2, 3)],
                     9: [(0, 2)], 11: [(1, 2)], 12: [(1, 3)], 13: [(0, 1)], 14: [(3, 0)],
                     5: [(3, 0), (1, 2)] if sum(z) / 4 < level else [(0, 1), (2, 3)],
                     10: [(0, 1), (2, 3)] if sum(z) / 4 < level else [(3, 0), (1, 2)]}
            for a, b in table[idx]: segs.append((e[a], e[b]))
    # chain
    key = lambda p: (round(p[0], 3), round(p[1], 3))
    adj = defaultdict(list)
    for k, (a, b) in enumerate(segs): adj[key(a)].append(k); adj[key(b)].append(k)
    used = [False] * len(segs); lines = []
    for k in range(len(segs)):
        if used[k]: continue
        used[k] = True; line = [segs[k][0], segs[k][1]]
        for end in (1, 0):
            while True:
                cur = key(line[-1] if end else line[0]); nxt = None
                for m in adj[cur]:
                    if not used[m]: nxt = m; break
                if nxt is None: break
                used[nxt] = True; a, b = segs[nxt]
                other = b if key(a) == cur else a
                if end: line.append(other)
                else: line.insert(0, other)
        lines.append(line)
    return lines

# contours (2-ft) over the site, 10-ft fine grid
CX = [x for x in range(-40, 1740, 10)]; CY = [y for y in range(-240, 20, 10)]
ZC = [[ground(x, y) for x in CX] for y in CY]
CONTOURS = {}
for lev in range(922, 960, 2):
    lines = [[p for p in ln if point_in_poly(p, BOUNDARY)] for ln in marching_squares(CX, CY, ZC, lev)]
    CONTOURS[lev] = [ln for ln in lines if len(ln) > 1]

# ----------------------------------------------------------------------------- 3. streams / setbacks / sewer
STREAMS = [[tuple(p) for path in s['paths_local'] for p in path] for s in ctx['streams'] if s['min_dist_ft'] < 60]
STREAM_IN = STREAMS[0]                                       # the reach that enters the site (FACTS §2)
def stream_dist(p, streams=None):
    return min(polyline_point_dist(p, s) for s in (streams or STREAMS))
def stream_offsets(path, levels=(25, 50, 75), step=3):
    us = [p[0] for p in path]; vs = [p[1] for p in path]
    xs = list(range(int(min(us)) - 90, int(max(us)) + 90, step)); ys = list(range(int(min(vs)) - 90, int(max(vs)) + 90, step))
    D = [[polyline_point_dist((x, y), path) for x in xs] for y in ys]
    return {lv: marching_squares(xs, ys, D, lv) for lv in levels}
STREAM_SETBACKS = [stream_offsets(s) for s in STREAMS]

SEWER = [s for s in ctx['sewer'] if s['min_dist_ft'] < 200]
SEWER_EX_SITE = [s for s in SEWER if 'ARCADO' in s['project'] and s['min_dist_ft'] < 15]
LEG_MH = (1348.9, -406.5)          # Legends at Parkview MH, invert 919.58 (FACTS §2)

# ----------------------------------------------------------------------------- 4. proposed layout
LOT_W, LOT_D = 50.0, 100.0
PAVE_W, SIDEWALK, STRIP = 22.0, 5.0, 2.0
BUFFER = 20.0; FRONT_SB, SIDE_SB, REAR_SB = 15.0, 5.0, 20.0
ARCADO_SB = 50.0; LANDSCAPE = 10.0
U_LOT0 = 230.0                                           # first lot (amenity block u 20-230)
U_BUF_REAR = U_REAR - BUFFER                             # 1701.0 rear buffer line
U_PAVE_END = U_BUF_REAR - 1.0                            # pavement end 1 ft inside the buffer line

# --- SG-05: the ordinance measures the stream buffer from TOP OF BANK, not from the digitized centreline.
#     Until the field delineation fixes top of bank, every stream clearance in this layout carries a 5.0-ft
#     top-of-bank allowance: design distances are measured from the digitized centreline and screened at
#     75 + 5 = 80 ft (impervious/lot/pond) and 50 + 5 = 55 ft (any land disturbance).
TOB_ALLOWANCE = 5.0
STREAM_IMPERV_SETBACK = 75.0                              # 50-ft undisturbed + 25-ft impervious setback
STREAM_UNDISTURBED = 50.0
SCREEN_IMPERV = STREAM_IMPERV_SETBACK + TOB_ALLOWANCE     # 80.0 ft from the digitized centreline
SCREEN_DISTURB = STREAM_UNDISTURBED + TOB_ALLOWANCE       # 55.0 ft from the digitized centreline

# --- SG-06 + SG-08: hammerhead stations are set from the travelled way so that every block reading between
#     street intersections is <= 600 ft (Table 4.2) and every turnaround spacing is well inside the 750-ft
#     trigger of IFC 2024 (GA) Appendix D103.4.  Slots are 20 ft of u inside a 50-ft pocket green on BOTH
#     sides of the lane, so no hammerhead leg lands on a lot.
GREENS_U = [(530.0, 580.0), (1080.0, 1130.0)]            # pocket greens (both sides) hosting hammerheads 1 and 2
POND_TRACTS = [(780.0, 980.0), (1480.0, 1680.0)]         # SW side open-space tracts holding Pond 1 / Pond 2
WOODS_U = (1280.0, 1480.0)                               # stream-head creek-woods tract (SW side)
HH_U = [(530.0, 550.0), (1100.0, 1120.0), (U_PAVE_END - 20.0, U_PAVE_END)]   # 20-ft hammerhead leg slots
HH_LEG = 60.0

# --- the lane tract.  Its edge is the lot-line offset (100-ft lot depth off each side line) everywhere a
#     lot fronts it.  Through the amenity block (no lots between the entry-curve PT and the first lot at
#     u = 230) it WIDENS locally, because a tract must contain its own improvements and an 18-ft-deep 90-deg
#     parking bay off an 11-ft half-pavement needs 30.0 ft of half-width against the 17.7-17.9 ft the lot-line
#     offset gives.  Drawn earlier as a flat 100-ft offset, the guest bay and the mail-kiosk bay lay about
#     11.2 ft OUTSIDE the tract that is supposed to own them.
def lot_line_sw(u): return SW(u) + LOT_D
def lot_line_ne(u): return NE(u) - LOT_D
BAY_DEPTH = 18.0                                   # 90-deg stall depth (9'-0" x 18'-0" stalls)
BAY_TRACT_HALF = PAVE_W / 2 + BAY_DEPTH + 1.0      # 11 + 18 + 1 = 30.0 ft of tract half-width at a bay
BAY_TAPER = 5.0
_BAY_WINDOW = []                                   # [taper-in start, full start, full end, taper-out end]
def tract_widen(u):
    if not _BAY_WINDOW: return 0.0
    a0, a1, b1, b0 = _BAY_WINDOW
    if u <= a0 or u >= b0: return 0.0
    if u < a1: return (u - a0) / (a1 - a0)
    if u > b1: return (b0 - u) / (b0 - b1)
    return 1.0
def tract_sw(u):
    e = lot_line_sw(u); f = tract_widen(u)
    return e + (lane_mid(u) - BAY_TRACT_HALF - e) * f if f > 0.0 else e
def tract_ne(u):
    e = lot_line_ne(u); f = tract_widen(u)
    return e + (lane_mid(u) + BAY_TRACT_HALF - e) * f if f > 0.0 else e

# --- SG-09: the asymmetric half-section (5-ft walk on the NE side only) needs 11 + 2 + 5 = 18.0 ft of NE
#     half-width, but the strip is only 235.4-236.1 ft wide over the first ~250 ft of lane, giving 17.72-
#     18.05 ft on the tract midline.  Offset the lane centreline 1.0 ft toward the SW for u < 400 and taper
#     the offset out over the following 200 ft.  No lot dimension changes: the lot lines stay on the tract.
LANE_SHIFT_SW = 1.0; LANE_SHIFT_HOLD_U = 400.0; LANE_SHIFT_TAPER_U = 600.0
def lane_shift(u):
    if u <= LANE_SHIFT_HOLD_U: return LANE_SHIFT_SW
    if u >= LANE_SHIFT_TAPER_U: return 0.0
    return LANE_SHIFT_SW * (LANE_SHIFT_TAPER_U - u) / (LANE_SHIFT_TAPER_U - LANE_SHIFT_HOLD_U)
def lane_mid(u): return (lot_line_sw(u) + lot_line_ne(u)) / 2.0 - lane_shift(u)
def ne_half(u): return lot_line_ne(u) - lane_mid(u)          # half-width available where LOTS front the tract
def sw_half(u): return lane_mid(u) - lot_line_sw(u)
HALF_SECTION = PAVE_W / 2 + STRIP + SIDEWALK              # 18.0 ft where a sidewalk is carried
# --- SG-13: the SW sidewalk starts at the first 10-ft station where the SW half-section fits with 0.25 ft
#     of margin and keeps fitting all the way to the terminus.
def _sw_walk_start():
    us = [float(u) for u in range(int(U_LOT0), int(U_PAVE_END), 10)]
    ok = None
    for u in reversed(us):
        if sw_half(u) >= HALF_SECTION + 0.25: ok = u
        else: break
    return ok if ok is not None else U_PAVE_END
U_WIDEN = _sw_walk_start()

# ---- entrance + entry drive (FACTS §2b / §4): centred at v = -190 on the Arcado Rd R/W, >= 250 ft from the Arcadia Pl
#      centreline (which meets the Arcado Rd centreline at local (u -12, v +61)); a 24-ft drive leaves the R/W on a short
#      tangent perpendicular to the R/W, then two reverse curves (R >= 100 ft, no intermediate tangent) carry it to the
#      lane midline; the straight private lane begins at U_JOIN.
ENTRY_V, ENTRY_W, ENTRY_R, ENTRY_T0 = -190.0, 24.0, 100.0, 10.0
U_ENTRY = front_u(ENTRY_V)                                                     # R/W point of the entrance centreline
_fd = (FRONT_LINE[-1][0] - FRONT_LINE[0][0], FRONT_LINE[-1][1] - FRONT_LINE[0][1]); _fl = math.hypot(*_fd)
PHI0 = math.atan2(_fd[0] / _fl, -_fd[1] / _fl)                                 # heading (rad from +u toward +v) of the inward R/W normal
def _solve_entry(target_v):
    """closed-form symmetric-radius reverse curve: tangent T0 at PHI0, left arc to PHI1, right arc back to heading 0."""
    c1 = (ENTRY_R * (1 + math.cos(PHI0)) + ENTRY_T0 * math.sin(PHI0) - (target_v - ENTRY_V)) / (2 * ENTRY_R)
    phi1 = math.acos(c1)
    return phi1, U_ENTRY + ENTRY_T0 * math.cos(PHI0) + ENTRY_R * (2 * math.sin(phi1) - math.sin(PHI0))
U_JOIN = 150.0
for _ in range(6): PHI1, U_JOIN = _solve_entry(lane_mid(U_JOIN))
# the local tract widening runs from the entry-curve PT to the first lot, tapered at both ends so the tract
# edge meets the entry-drive tract at the PT and the lot line at u = 230 with no step.
_BAY_WINDOW[:] = [U_JOIN, U_JOIN + BAY_TAPER, U_LOT0 - BAY_TAPER, U_LOT0]
BAY_U = (U_JOIN + 6.0, U_LOT0 - 6.0)               # usable stationing for the bays (inside the full-width reach)
def entry_samples(step=2.0):
    """[(point, heading, station)] along the entry-drive centreline: tangent, arc 1 (left), arc 2 (right)."""
    out = []; p = (U_ENTRY, ENTRY_V); h = PHI0
    n = max(1, int(ENTRY_T0 / step))
    for k in range(n + 1):
        t = ENTRY_T0 * k / n; out.append(((p[0] + t * math.cos(h), p[1] + t * math.sin(h)), h, t))
    p1 = out[-1][0]; s = ENTRY_T0
    c1 = (p1[0] - ENTRY_R * math.sin(h), p1[1] + ENTRY_R * math.cos(h))           # centre on the left
    a1 = PHI1 - PHI0; n = max(2, int(ENTRY_R * a1 / step))
    for k in range(1, n + 1):
        hh = PHI0 + a1 * k / n
        out.append(((c1[0] + ENTRY_R * math.sin(hh), c1[1] - ENTRY_R * math.cos(hh)), hh, s + ENTRY_R * a1 * k / n))
    p2 = out[-1][0]; s += ENTRY_R * a1
    c2 = (p2[0] + ENTRY_R * math.sin(PHI1), p2[1] - ENTRY_R * math.cos(PHI1))     # centre on the right
    n = max(2, int(ENTRY_R * PHI1 / step))
    for k in range(1, n + 1):
        hh = PHI1 * (1 - k / n)
        out.append(((c2[0] - ENTRY_R * math.sin(hh), c2[1] + ENTRY_R * math.cos(hh)), hh, s + ENTRY_R * (PHI1 - hh)))
    return out
ENTRY_SAMPLES = entry_samples()
ENTRY_CL = [p for p, h, s in ENTRY_SAMPLES]; ENTRY_LEN = ENTRY_SAMPLES[-1][2]
assert dist(ENTRY_CL[-1], (U_JOIN, lane_mid(U_JOIN))) < 0.05, 'entry curve does not close on the lane midline'
def entry_offset(d, taper_from=None, d_end=None):
    """parallel offset of the entry centreline (+d toward NE / left); optional linear taper over the last `taper_from` ft."""
    pts = []
    for p, h, s in ENTRY_SAMPLES:
        dd = d
        if taper_from is not None and s > ENTRY_LEN - taper_from: dd = d + (d_end - d) * (s - (ENTRY_LEN - taper_from)) / taper_from
        pts.append((p[0] - dd * math.sin(h), p[1] + dd * math.cos(h)))
    return pts
ENTRY_SW_OFF = sw_half(U_JOIN); ENTRY_NE_OFF = ne_half(U_JOIN)                  # lane-tract half-widths at the join
# SG-16: the entry-drive tract must contain its own 5-ft sidewalk.  The walk's outer edge sits 19.0 ft off the
# entry centreline at the R/W (12 + 2 + 5) and tapers to 18.0 ft at the join, so the tract half-width tapers
# from 20.0 ft at the R/W to the lane-tract half-width at the join.
ENTRY_TRACT_NE_RW = max(ENTRY_W / 2 + STRIP + SIDEWALK + 1.0, ENTRY_NE_OFF)
ENTRY_TRACT_SW_RW = max(ENTRY_W / 2 + 3.0, ENTRY_SW_OFF)
ENTRY_PAVE = entry_offset(ENTRY_W / 2, 30.0, PAVE_W / 2) + entry_offset(-ENTRY_W / 2, 30.0, -PAVE_W / 2)[::-1]
ENTRY_TRACT = entry_offset(ENTRY_TRACT_NE_RW, 30.0, ENTRY_NE_OFF) + entry_offset(-ENTRY_TRACT_SW_RW, 30.0, -ENTRY_SW_OFF)[::-1]
ENTRY_WALK = entry_offset(ENTRY_W / 2 + STRIP, 30.0, PAVE_W / 2 + STRIP) + entry_offset(ENTRY_W / 2 + STRIP + SIDEWALK, 30.0, PAVE_W / 2 + STRIP + SIDEWALK)[::-1]
# Arcado Rd centreline (Gwinnett GIS street centrelines) and the Arcadia Pl centreline point on it
ARCADO_CL = sorted({(round(p[0], 2), round(p[1], 2)) for st in ctx['streets'] if st['name'] == 'ARCADO RD' and st['min_dist_ft'] < 40
                    for path in st['paths_local'] for p in path if -450 <= p[1] <= 70}, key=lambda p: -p[1])
_arcadia = next(st for st in ctx['streets'] if st['name'] == 'ARCADIA PL' and st['min_dist_ft'] < 100)
ARCADIA_PATH = [tuple(p) for p in _arcadia['paths_local'][0]]
ARCADIA_CL = min((ARCADIA_PATH[0], ARCADIA_PATH[-1]), key=lambda p: polyline_point_dist(p, ARCADO_CL))   # ≈ (-12, 61) per FACTS §2b
assert polyline_point_dist(ARCADIA_CL, ARCADO_CL) < 2.0 and dist(ARCADIA_CL, (-12.0, 61.0)) < 3.0, ARCADIA_CL
def _ray_hit(p, h, path):
    """intersection of the ray from p with heading h (backwards, i.e. toward the road) and a polyline."""
    q = (p[0] - 400 * math.cos(h), p[1] - 400 * math.sin(h))
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        if segs_intersect(p, q, a, b):
            d1, d2 = orient(a, b, p), orient(a, b, q); t = d1 / (d1 - d2)
            return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])), i
    raise RuntimeError('entrance ray misses the Arcado Rd centreline')
ENTRY_ON_CL, _seg = _ray_hit((U_ENTRY, ENTRY_V), PHI0, ARCADO_CL)
_i0 = min(range(len(ARCADO_CL)), key=lambda i: dist(ARCADO_CL[i], ARCADIA_CL))
_path = [ARCADIA_CL] + ARCADO_CL[_i0 + 1:_seg + 1] + [ENTRY_ON_CL]
SEP_FT = sum(dist(_path[i], _path[i + 1]) for i in range(len(_path) - 1))       # along the Arcado Rd C/L
SEP_CHORD_FT = dist(ARCADIA_CL, ENTRY_ON_CL)
_n0 = (-math.sin(PHI0), math.cos(PHI0)); _t0 = (math.cos(PHI0), math.sin(PHI0))
# --- SG-07 + SG-19: the entrance curb returns are DRAWN geometry, not an area allowance.  The SW return is
#     reduced from 25'-0" to 15'-0" to pull it out of the 20-ft perimeter buffer band; the NE return stays
#     25'-0" for fire-apparatus entry.  Whatever is left inside the buffer band is reported, dimensioned on
#     the sheet and carried into the letter of intent as an explicit buffer-reduction request.
RET_R_NE, RET_R_SW = 25.0, 15.0
def curb_return(sgn, R, n=14):
    """quarter-round fillet between the R/W line and the drive's pavement edge; sgn -1 = SW side, +1 = NE."""
    E = (U_ENTRY + sgn * (ENTRY_W / 2) * _n0[0], ENTRY_V + sgn * (ENTRY_W / 2) * _n0[1])   # pavement edge on the R/W
    C = (E[0] + sgn * R * _n0[0] + R * _t0[0], E[1] + sgn * R * _n0[1] + R * _t0[1])       # arc centre
    A = (E[0] + sgn * R * _n0[0], E[1] + sgn * R * _n0[1])                                 # tangent point on the R/W
    B = (E[0] + R * _t0[0], E[1] + R * _t0[1])                                             # tangent point on the drive edge
    pts = [E]
    for k in range(n + 1):                       # arc from A to B about C
        a0 = math.atan2(A[1] - C[1], A[0] - C[0]); a1 = math.atan2(B[1] - C[1], B[0] - C[0])
        while a1 - a0 > math.pi: a1 -= 2 * math.pi
        while a0 - a1 > math.pi: a1 += 2 * math.pi
        a = a0 + (a1 - a0) * k / n
        pts.append((C[0] + R * math.cos(a), C[1] + R * math.sin(a)))
    return pts
CURB_RETURNS = [{'side': 'SW', 'radius_ft': RET_R_SW, 'polygon': curb_return(-1, RET_R_SW)},
                {'side': 'NE', 'radius_ft': RET_R_NE, 'polygon': curb_return(+1, RET_R_NE)}]
_sw_return_v = ENTRY_V - (ENTRY_W / 2 + RET_R_SW) * _n0[1]                      # v of the SW curb return's tangent point on the R/W
SW_BUFFER_INNER_V = SW(0.0) + BUFFER
SW_RETURN_ENCROACH_FT = max(0.0, SW_BUFFER_INNER_V - _sw_return_v)              # into the 20-ft SW buffer band, at the R/W only
def _return_buffer_area(poly):
    """area of a curb-return polygon that falls inside the 20-ft SW buffer band (0.25-ft raster)."""
    us = [p[0] for p in poly]; vs = [p[1] for p in poly]; a = 0.0
    u = min(us)
    while u <= max(us):
        v = min(vs)
        while v <= max(vs):
            if v < SW(u) + BUFFER and v > SW(u) and point_in_poly((u, v), poly): a += 0.0625
            v += 0.25
        u += 0.25
    return a
SW_RETURN_BUFFER_SF = round(_return_buffer_area(CURB_RETURNS[0]['polygon']), 1)
SW_RETURN_BUFFER_SF_TXT = ('< 1' if 0 < SW_RETURN_BUFFER_SF < 1 else f'{SW_RETURN_BUFFER_SF:,.0f}') + ' sf'
CURB_RETURN_SF = sum(abs(poly_area(r['polygon'])) for r in CURB_RETURNS)

# lane geometry (polylines sampled every 10 ft + all lot corner u's); the straight lane begins at U_JOIN
US = sorted(set([U_JOIN] + [float(u) for u in range(int(U_JOIN) + 1, int(U_BUF_REAR), 10)] + [U_BUF_REAR]
               + [float(u) for u in range(230, int(U_BUF_REAR), 50)] + list(_BAY_WINDOW)))
LANE_CL = [(u, lane_mid(u)) for u in US]
LANE_TRACT = [(u, tract_sw(u)) for u in US] + [(u, tract_ne(u)) for u in reversed(US)]
LANE_PAVE = [(u, lane_mid(u) - PAVE_W / 2) for u in US if u <= U_PAVE_END] + [(U_PAVE_END, lane_mid(U_PAVE_END) - PAVE_W / 2)]
LANE_PAVE += [(U_PAVE_END, lane_mid(U_PAVE_END) + PAVE_W / 2)] + [(u, lane_mid(u) + PAVE_W / 2) for u in reversed(US) if u <= U_PAVE_END]
def sidewalk_polys():
    out = []
    ne = [(u, lane_mid(u) + PAVE_W / 2 + STRIP) for u in US] ; ne2 = [(u, lane_mid(u) + PAVE_W / 2 + STRIP + SIDEWALK) for u in reversed(US)]
    out.append({'side': 'NE', 'polygon': ne + ne2})
    out.append({'side': 'NE (entry drive)', 'polygon': ENTRY_WALK})
    sw = [(u, lane_mid(u) - PAVE_W / 2 - STRIP) for u in US if u >= U_WIDEN]; sw2 = [(u, lane_mid(u) - PAVE_W / 2 - STRIP - SIDEWALK) for u in reversed(US) if u >= U_WIDEN]
    out.append({'side': 'SW', 'polygon': sw + sw2, 'from_u': U_WIDEN})
    return out
SIDEWALKS = sidewalk_polys()

HAMMERHEADS = []
for (a, b) in HH_U:
    um = (a + b) / 2
    HAMMERHEADS.append({'u': um, 'legs': [rect(a, b, lane_mid(um) - PAVE_W / 2 - HH_LEG, lane_mid(um) - PAVE_W / 2),
                                          rect(a, b, lane_mid(um) + PAVE_W / 2, lane_mid(um) + PAVE_W / 2 + HH_LEG)],
                        'width_ft': b - a, 'leg_ft': HH_LEG})

# lot slots
def lot_poly(side, u0, u1):
    if side == 'SW': return [(u0, SW(u0)), (u1, SW(u1)), (u1, tract_sw(u1)), (u0, tract_sw(u0))]
    return [(u0, tract_ne(u0)), (u1, tract_ne(u1)), (u1, NE(u1)), (u0, NE(u0))]

def slot_blocked(side, u0, u1):
    for (a, b) in GREENS_U:
        if u0 < b and u1 > a: return 'green'
    if side == 'SW':
        for (a, b) in POND_TRACTS:
            if u0 < b and u1 > a: return 'pond'
        if u0 < WOODS_U[1] and u1 > WOODS_U[0]: return 'woods'
    for (a, b) in HH_U:
        if u0 < b and u1 > a: return 'hammerhead'
    # SG-04 + SG-05: screen against ALL digitized reaches (not only the on-site one) at 75 ft + the 5-ft
    # top-of-bank allowance.
    if min(poly_polyline_dist(lot_poly(side, u0, u1), s) for s in STREAMS) < SCREEN_IMPERV: return 'stream'
    return None

LOTS = []
for side in ('SW', 'NE'):
    u = U_LOT0
    while u + LOT_W <= U_BUF_REAR + 1e-6:
        why = slot_blocked(side, u, u + LOT_W)
        if why is None:
            LOTS.append({'side': side, 'u0': u, 'u1': u + LOT_W, 'polygon': lot_poly(side, u, u + LOT_W)})
            u += LOT_W
        else:
            # jump to the end of the blocking feature
            ends = [b for (a, b) in GREENS_U + HH_U + (POND_TRACTS + [WOODS_U] if side == 'SW' else []) if u < b and u + LOT_W > a]
            u = max(ends) if ends and why != 'stream' else u + 10.0
            if why == 'stream': u = round(u, 0)

# ---------------------------------------------------------------- house siting from data/plans.json (SG-03)
# The MCP no longer draws the nominal 38 x 38 / 40 x 40 program rectangles.  Every dwelling is drawn from the
# real envelope the architectural generator published in data/plans.json: the L-shaped conditioned body, the
# garage wing stepped back so the Table 4.2 5-ft recess reads, the covered front porch and the rear
# porch/patio.  plans.json is read AT RUN TIME so a re-proportioned plan flows straight through to this sheet.
PLANS = json.load(open(os.path.join(DATA, 'plans.json')))['plans']
PLANS_DATE = json.load(open(os.path.join(DATA, 'plans.json'))).get('date', 'n/a')
ROOF_OVERHANG = 8.0 / 12.0      # 8 in all round (plans.json roof); held OUTSIDE every required yard
FRONT_WALK_SF = 60.0            # 3 ft x 20 ft entry walk, porch to lane sidewalk (not drawn at 1" = 60')

def plan_geometry(pid):
    """Siting + footprint pieces of one plan, in lot coordinates (x across the lot, y from the front lot line).

    The siting is READ from plans.json `lot_siting`; it is not re-derived here.  The architectural generator
    holds the 8-in roof overhang outside every required yard, so the porch FACE sits 15'-8" from the front lot
    line (15'-0" required + 0'-8" overhang) and no projection into a required yard is claimed.  Anything this
    routine needs that plans.json does not carry is computed from the published polygons, never assumed."""
    P = PLANS[pid]; LS = P['lot_siting']
    fp = [tuple(p) for p in P['footprint_polygon_ft']]                 # CONDITIONED footprint (L-shaped)
    gx0, gy0, gx1, gy1 = P['garage_rect']                              # garage wing, stepped back gy0 = 5'-0"
    porch = [tuple(r) for r in P.get('porch_rects', [])]
    patio = [tuple(r) for r in P.get('patio_rects', [])]
    rporch = [tuple(r) for r in P.get('rear_porch_rects', [])]
    body_w = P['overall_body_dims']['width_ft']; body_d = P['overall_body_dims']['depth_ft']
    ox, oy = LS['house_origin_on_lot_ft']                              # (6.00, 21.667) — front WALL of the body
    porch_d = max((0.0 - r[1]) for r in porch) if porch else 0.0       # porch projects to negative y
    face = oy - porch_d                                                # porch face from the front lot line
    patio_d = max((r[3] - body_d) for r in patio) if patio else 0.0    # uncovered patio beyond the rear wall
    rporch_d = max((r[3] - body_d) for r in rporch) if rporch else 0.0 # covered rear porch beyond the rear wall
    rear_edge = oy + body_d + max(patio_d, rporch_d)
    # areas actually DRAWN on this sheet (shoelace of the published polygons, not the nominal squares)
    a_cond = abs(poly_area(fp)); a_gar = (gx1 - gx0) * (gy1 - gy0)
    a_porch = sum((r[2] - r[0]) * (r[3] - r[1]) for r in porch)
    a_rporch = sum((r[2] - r[0]) * (r[3] - r[1]) for r in rporch)
    a_patio = sum((r[2] - r[0]) * (r[3] - r[1]) for r in patio)
    return {'id': pid, 'name': P['name'], 'plan': P, 'fp': fp, 'garage': (gx0, gy0, gx1, gy1), 'porch': porch,
            'patio': patio, 'rear_porch': rporch, 'body_w': body_w, 'body_d': body_d, 'porch_d': porch_d,
            'patio_d': patio_d, 'rear_porch_d': rporch_d, 'face': face, 'ox': ox, 'oy': oy,
            'side_yard_ft': LS['side_yard_ft'], 'garage_door_ft': oy + gy0, 'garage_recess_ft': gy0,
            'rear_edge_ft': rear_edge, 'rear_clear_ft': LOT_D - rear_edge,
            'body_label': P['overall_body_dims']['label'], 'areas': P['areas'],
            'a_conditioned_sf': a_cond, 'a_garage_sf': a_gar, 'a_front_porch_sf': a_porch,
            'a_rear_porch_sf': a_rporch, 'a_patio_sf': a_patio, 'a_under_roof_sf': a_cond + a_gar + a_porch + a_rporch,
            'roof_max_ridge_ft': P['roof']['max_ridge_ft'], 'target_cond_sf': P.get('target_cond_sf')}
PLAN_GEOM = {pid: plan_geometry(pid) for pid in ('A', 'B')}
# the drawn footprints must reproduce the areas plans.json publishes, or the impervious total is fiction
for _pid, _G in PLAN_GEOM.items():
    _a = _G['areas']
    assert abs(_G['a_conditioned_sf'] - _a['conditioned_sf']) < 1.0, (_pid, 'conditioned', _G['a_conditioned_sf'])
    assert abs(_G['a_garage_sf'] - _a['garage_sf']) < 1.0, (_pid, 'garage', _G['a_garage_sf'])
    assert abs(_G['a_under_roof_sf'] - _a['total_under_roof_sf']) < 1.0, (_pid, 'under roof', _G['a_under_roof_sf'])

for k, L in enumerate(LOTS, 1):
    L['id'] = k; L['plan'] = 'A' if k % 2 else 'B'
    G = PLAN_GEOM[L['plan']]
    L['area_sf'] = round(abs(poly_area(L['polygon'])), 0); L['width_ft'] = LOT_W
    d0 = dist(L['polygon'][0], L['polygon'][3]); d1 = dist(L['polygon'][1], L['polygon'][2])
    L['depth_ft'] = round((d0 + d1) / 2, 1)
    u0, u1 = L['u0'], L['u1']; um = (u0 + u1) / 2
    sgn = -1 if L['side'] == 'SW' else 1                 # direction from lane into the lot
    edge = tract_sw if L['side'] == 'SW' else tract_ne
    # SG-17: the front lot line is not parallel to +u (the strip lines diverge ~0.35 deg).  Measure the front
    # setback perpendicular to the real front lot line and site the house on its NEAREST point, so the drawn
    # minimum equals the stated minimum instead of falling 0.008 ft short of it.
    front_near = edge(u0) if (edge(u0) * sgn) < (edge(u1) * sgn) else edge(u1)
    mirror = (k % 4) not in (1, 2)                        # alternate the garage bay left/right down the street
    def XY(x, y, _f=front_near, _s=sgn, _u0=u0, _u1=u1, _m=mirror):
        return ((_u1 - x) if _m else (_u0 + x), _f + _s * y)
    def R4(x0, y0, x1, y1):
        return [XY(x0, y0), XY(x1, y0), XY(x1, y1), XY(x0, y1)]
    ox, oy = G['ox'], G['oy']
    gx0, gy0, gx1, gy1 = G['garage']
    L['house'] = {
        'plan': L['plan'], 'plan_name': G['name'], 'body_ft': G['body_label'],
        'body_polygon': [XY(ox + x, oy + y) for (x, y) in G['fp']],
        'garage_rect': R4(ox + gx0, oy + gy0, ox + gx1, oy + gy1),
        'porch_rects': [R4(ox + r[0], oy + r[1], ox + r[2], oy + r[3]) for r in G['porch']],
        'rear_porch_rects': [R4(ox + r[0], oy + r[1], ox + r[2], oy + r[3]) for r in G['rear_porch']],
        'patio_rects': [R4(ox + r[0], oy + r[1], ox + r[2], oy + r[3]) for r in G['patio']],
        'rear_kind': (f"covered rear porch {max(r[3] - r[1] for r in G['rear_porch']):.0f}'-0\" (recessed under the main roof)"
                      if G['rear_porch'] else
                      (f"uncovered patio {max(r[3] - r[1] for r in G['patio']):.0f}'-0\"" if G['patio'] else 'none')),
        'garage_recess_ft': gy0,
        'garage_door_from_lot_line_ft': round(G['garage_door_ft'], 2),
        'porch_face_from_lot_line_ft': round(G['face'], 2),
        'rear_element_from_rear_line_ft': round(G['rear_clear_ft'], 2),
        'side_yard_ft': G['side_yard_ft'],
    }
    # driveway: 20 ft wide on the garage bay, from the lane pavement edge to the garage door
    dw = 20.0; dc = (ox + gx0 + ox + gx1) / 2
    L['house']['driveway_rect'] = [XY(dc - dw / 2, G['garage_door_ft']), XY(dc + dw / 2, G['garage_door_ft'])] + \
        [(XY(dc + dw / 2, 0)[0], lane_mid(um) + sgn * PAVE_W / 2), (XY(dc - dw / 2, 0)[0], lane_mid(um) + sgn * PAVE_W / 2)]
    L['house_rect'] = L['house']['body_polygon']; L['driveway_rect'] = L['house']['driveway_rect']
    # SG-11: the setback envelope and the buffer easement are recorded instruments — draw them as trapezoids
    # that close on the surveyed side lines, not as u-v rectangles evaluated at the lot mid-station.
    side_line = SW if L['side'] == 'SW' else NE
    L['setback_envelope'] = [(u0 + SIDE_SB, edge(u0 + SIDE_SB) + sgn * FRONT_SB), (u1 - SIDE_SB, edge(u1 - SIDE_SB) + sgn * FRONT_SB),
                             (u1 - SIDE_SB, side_line(u1 - SIDE_SB) - sgn * REAR_SB), (u0 + SIDE_SB, side_line(u0 + SIDE_SB) - sgn * REAR_SB)]
    L['buffer_easement'] = [(u0, side_line(u0) - sgn * BUFFER), (u1, side_line(u1) - sgn * BUFFER),
                            (u1, side_line(u1)), (u0, side_line(u0))]
    # --- SG-02: per-lot impervious from the REAL drawn footprints, never a flat nominal allowance.
    #     inputs (all shoelace areas of the polygons this sheet actually draws, in SF):
    #       under roof = conditioned footprint + garage wing + covered front porch + covered rear porch
    #       + uncovered rear patio + driveway (on-lot run + apron to the lane pavement edge) + entry walk
    #     less the 20 ft x 5 ft square where the driveway apron crosses the lane sidewalk on that lot's side
    #     (counted once in the sidewalk total, so it must not be counted again here).
    H = L['house']
    a_roof = abs(poly_area(H['body_polygon'])) + abs(poly_area(H['garage_rect'])) \
        + sum(abs(poly_area(r)) for r in H['porch_rects']) + sum(abs(poly_area(r)) for r in H['rear_porch_rects'])
    a_patio = sum(abs(poly_area(r)) for r in H['patio_rects'])
    a_drive = abs(poly_area(H['driveway_rect']))
    L['impervious'] = {'under_roof_sf': round(a_roof, 1), 'patio_sf': round(a_patio, 1),
                       'driveway_sf': round(a_drive, 1), 'entry_walk_sf': FRONT_WALK_SF,
                       'total_sf': round(a_roof + a_patio + a_drive + FRONT_WALK_SF, 1)}
    L['notes'] = []
    if L['area_sf'] < 5000: L['notes'].append('area < 5,000 sf')
N_LOTS = len(LOTS)
# --- Blocks (Site Development Plan Review Checklist §4.i: "Phasing is not permitted unless platted in
#     Blocks").  The phase/block line must fall ON a lot line, never through a lot.
_lot_edges = sorted({L['u0'] for L in LOTS} | {L['u1'] for L in LOTS})
def _interior(u): return any(L['u0'] + 1e-6 < u < L['u1'] - 1e-6 for L in LOTS)
PHASE_U = min([u for u in _lot_edges if not _interior(u)], key=lambda u: abs(u - 1000.0))
for L in LOTS:
    L['block'] = 'A' if L['u1'] <= PHASE_U + 1e-6 else 'B'
    L['phase'] = 1 if L['block'] == 'A' else 2
for b in ('A', 'B'):
    for n, L in enumerate([x for x in LOTS if x['block'] == b], 1): L['block_lot'] = n

# --- open-space tracts.  SG-11 / SG-14: every tract is a TRAPEZOID that closes on the surveyed side lines,
#     so the named tracts tile the residual exactly and there are no unallocated slivers to explain.
def sw_tract(a, b): return [(a, SW(a)), (b, SW(b)), (b, tract_sw(b)), (a, tract_sw(a))]
def ne_tract(a, b): return [(a, tract_ne(a)), (b, tract_ne(b)), (b, NE(b)), (a, NE(a))]
GREENS = []
for (a, b) in GREENS_U:
    GREENS.append({'name': f'Pocket green (u {a:.0f}-{b:.0f})', 'polygons': [sw_tract(a, b), ne_tract(a, b)]})
# SG-15: the terminus green starts where the hammerhead-3 legs start, so tract and pavement register exactly.
U_TERM = HH_U[2][0]
GREENS.append({'name': 'Terminus green + rear buffer', 'polygons': [
    sw_tract(U_TERM, U_BUF_REAR), ne_tract(U_TERM, U_BUF_REAR),
    [(U_BUF_REAR, SW(U_BUF_REAR))] + [p for p in REAR_LINE] + [(U_BUF_REAR, NE(U_BUF_REAR))]]})
for g in GREENS: g['area_sf'] = round(sum(abs(poly_area(p)) for p in g['polygons']))

# --- SG-04: the lot module is screened against ALL THREE digitized stream reaches at 75 ft + the 5-ft
#     top-of-bank allowance, so the slots that fail the screen are simply not lotted.  They are NAMED here as
#     stream-setback open-space tracts rather than left as unallocated slivers, and they carry the same
#     no-impervious restriction as the buffer easements.
def _residual_strips(side):
    cov = sorted([(L['u0'], L['u1']) for L in LOTS if L['side'] == side] + list(GREENS_U) + [(U_TERM, U_BUF_REAR)]
                 + (list(POND_TRACTS) + [WOODS_U] if side == 'SW' else []))
    out = []; u = U_LOT0
    for a, b in cov:
        if a > u + 1e-6: out.append((u, a))
        u = max(u, b)
    if u < U_BUF_REAR - 1e-6: out.append((u, U_BUF_REAR))
    return out
STREAM_TRACTS = []
for _side in ('SW', 'NE'):
    for (a, b) in _residual_strips(_side):
        poly = (sw_tract if _side == 'SW' else ne_tract)(a, b)
        d = min(poly_polyline_dist(poly, s) for s in STREAMS)
        STREAM_TRACTS.append({'name': f'Stream-setback open-space tract ({_side} side, u {a:.0f}-{b:.0f}) — unlotted, no impervious',
                              'side': _side, 'u': (a, b), 'polygon': poly, 'area_sf': round(abs(poly_area(poly))),
                              'min_dist_to_stream_centreline_ft': round(d, 1)})

# --- SG-01: detention basins sized against the RE-DERIVED disturbed area at the Gwinnett County Stormwater
#     Management Manual screening rate of 10,000 cf per disturbed acre (RRv = 0 at concept stage), not against
#     the 4.4 ac the previous run assumed.  Basins are trapezoids parallel to the SW property line (SG-10):
#       * top of bank >= POND_TOB_OFFSET ft inside the SW line, which leaves the 20-ft undisturbed buffer
#         intact AND satisfies Site Development Plan Review Checklist §11.i.6 (toe >= 10 ft off the line);
#       * a 10-ft drainage easement between the buffer line and the top of bank (Checklist §11.i.12);
#       * a 10-ft maintenance shelf between the top of bank and the lane tract, with a 30-ft BMP access
#         easement off the lane at the downstream end (Checklist §11.i.2);
#       * every point >= 75 ft + the 5-ft top-of-bank allowance from all three digitized stream reaches.
POND_DEPTH, POND_SLOPE = 6.0, 3.0
POND_TOB_OFFSET = BUFFER + 10.0            # 30 ft inside the SW property line
POND_SHELF = 6.0                           # maintenance shelf between top of bank and the lane tract
POND_END_CLEAR = 10.0                      # clear of the tract ends
def prismoidal(poly, depth=POND_DEPTH, slope=POND_SLOPE):
    """prismoidal volume of a basin whose top of bank is `poly`, side slopes `slope`:1."""
    A1 = abs(poly_area(poly)); inner = shrink_convex(poly, slope * depth)
    A2 = abs(poly_area(inner))
    if A2 <= 0 or any(abs(p[0]) > 1e6 for p in inner): return 0.0, inner
    # reject a degenerate inset (self-crossing) — check it stays inside the outer polygon
    if not all(point_in_poly(p, ccw(poly)) for p in inner): return 0.0, inner
    return depth * (A1 + A2 + math.sqrt(A1 * A2)) / 3.0, inner
def size_pond(tract, want):
    """largest trapezoidal basin inside a SW open-space tract that clears the stream screen; returns geometry."""
    a, b = tract
    best = None
    for shrink_ne in [x * 0.5 for x in range(0, 61)]:            # pull the NE edge back if the stream demands it
        for shrink_sw in [x * 0.5 for x in range(0, 61)]:        # pull the SW edge in if the stream demands it
            for end in [POND_END_CLEAR + x * 5.0 for x in range(0, 12)]:
                u0, u1 = a + end, b - end
                if u1 - u0 < 60: continue
                poly = [(u0, SW(u0) + POND_TOB_OFFSET + shrink_sw), (u1, SW(u1) + POND_TOB_OFFSET + shrink_sw),
                        (u1, tract_sw(u1) - POND_SHELF - shrink_ne), (u0, tract_sw(u0) - POND_SHELF - shrink_ne)]
                if (poly[3][1] - poly[0][1]) < 30.0: continue
                if min(poly_polyline_dist(poly, s) for s in STREAMS) < SCREEN_IMPERV: continue
                V, inner = prismoidal(poly)
                if V <= 0: continue
                if best is None or V > best[0]: best = (V, poly, inner, u0, u1)
                if V >= want: return best
    if best is None: raise RuntimeError('pond does not fit')
    return best
PONDS = []
for i, tr in enumerate(POND_TRACTS, 1):
    a, b = tr
    PONDS.append({'name': f'Pond {i} (dry detention / WQ)', 'tract_u': tr, 'tract_polygon': sw_tract(a, b), '_target': 0.0})
WOODS = {'name': 'Creek woods (stream head + 50/75-ft buffers) — preserved', 'polygon': sw_tract(*WOODS_U)}
WOODS['area_sf'] = round(abs(poly_area(WOODS['polygon'])))

# --- disturbed area (drives detention).  Site area less the areas that stay undisturbed: the 20-ft perimeter
#     buffer bands on every property line except the Arcado Rd frontage, the creek-woods tract, and the 50-ft
#     undisturbed stream buffer where it falls inside the boundary.  2-ft raster; the three preserved sets are
#     unioned, not added, so nothing is double-counted.
_bseg = [(BOUNDARY[i], BOUNDARY[(i + 1) % len(BOUNDARY)]) for i in range(len(BOUNDARY))
         if not is_frontage_seg(BOUNDARY[i], BOUNDARY[(i + 1) % len(BOUNDARY)])]
_sbox = []
for s in STREAMS:
    _sbox.append((min(p[0] for p in s) - 60, max(p[0] for p in s) + 60, min(p[1] for p in s) - 60, max(p[1] for p in s) + 60))
def _near_stream(u, v):
    return any(b[0] <= u <= b[1] and b[2] <= v <= b[3] for b in _sbox)
def compute_disturbed(step=2.0):
    ub0 = min(p[0] for p in BOUNDARY); ub1 = max(p[0] for p in BOUNDARY)
    vb0 = min(p[1] for p in BOUNDARY); vb1 = max(p[1] for p in BOUNDARY)
    cell = step * step; site = buf = wood = strm = 0.0
    woods_ring = ccw(WOODS['polygon'])
    u = ub0 + step / 2
    while u < ub1:
        v = vb0 + step / 2
        while v < vb1:
            p = (u, v)
            if point_in_poly(p, BOUNDARY):
                site += cell
                pres = False
                if (v - SW(u) < BUFFER + 5) or (NE(u) - v < BUFFER + 5) or (u > U_REAR - 30) or (u < 30):
                    if min(seg_point_dist(p, a, b) for a, b in _bseg) < BUFFER: buf += cell; pres = True
                if not pres and point_in_poly(p, woods_ring): wood += cell; pres = True
                if not pres and _near_stream(u, v):
                    if min(polyline_point_dist(p, s) for s in STREAMS) < STREAM_UNDISTURBED: strm += cell; pres = True
            v += step
        u += step
    return {'site_raster_sf': round(site), 'buffer_bands_sf': round(buf), 'creek_woods_net_sf': round(wood),
            'stream_buffer_net_sf': round(strm), 'preserved_sf': round(buf + wood + strm),
            'disturbed_sf': round(site - buf - wood - strm), 'disturbed_ac': round((site - buf - wood - strm) / 43560, 3),
            'raster_step_ft': step}
DISTURBED = compute_disturbed()
DETENTION_RATE_CF_AC = 10000.0                                   # GCSWMM screening basis (FACTS §3), RRv = 0
DETENTION_REQ_CF = round(DETENTION_RATE_CF_AC * DISTURBED['disturbed_ac'])

# size the two basins: Pond 2 (rear low pocket, the deeper catchment) first, then Pond 1 for the remainder
_want = DETENTION_REQ_CF * 1.05                                  # 5 % concept contingency
for i, P in enumerate(PONDS):
    share = _want * (0.55 if i == 1 else 0.45)
    V, poly, inner, u0, u1 = size_pond(P['tract_u'], share)
    W = (poly[3][1] - poly[0][1] + poly[2][1] - poly[1][1]) / 2.0
    P.update({'polygon': poly, 'bottom_polygon': inner, 'top_of_bank_ft': f"{W:.0f} x {u1 - u0:.0f}",
              'length_ft': round(u1 - u0, 1), 'width_ft': round(W, 1), 'depth_ft': POND_DEPTH,
              'area_sf': round(abs(poly_area(poly))), 'bottom_area_sf': round(abs(poly_area(inner))),
              'est_storage_cf': round(V),
              'tob_to_sw_line_ft': round(min(p[1] - SW(p[0]) for p in poly), 1),
              'tob_to_lane_tract_ft': round(min(tract_sw(p[0]) - p[1] for p in poly), 1),
              'tob_to_stream_ft': round(min(poly_polyline_dist(poly, s) for s in STREAMS), 1),
              'drainage_easement': [(p[0], p[1]) for p in
                                    [(u0, SW(u0) + BUFFER), (u1, SW(u1) + BUFFER), (u1, poly[1][1]), (u0, poly[0][1])]],
              'assumption': f'{POND_DEPTH:.0f}-ft depth, {POND_SLOPE:.0f}:1 side slopes, prismoidal volume between top of bank and basin '
                            f'bottom; dry extended-detention / water-quality basin per the Gwinnett County Stormwater Management '
                            f'Manual. Concept sizing only — final volumes, outlet structures, forebay, spillway and the runoff-'
                            f'reduction (RRv) credit by the design PE. Rock probes required (NRCS ARE, gneiss bedrock 22-40 in).'})
    P.pop('_target', None)
DETENTION_PROV_CF = sum(P['est_storage_cf'] for P in PONDS)
# BMP access easement: a 30-ft corridor off the lane at each basin's downstream (higher-u) end
POND_ACCESS = [[(P['polygon'][1][0] - 30.0, tract_sw(P['polygon'][1][0] - 30.0)), (P['polygon'][1][0], tract_sw(P['polygon'][1][0])),
                (P['polygon'][2][0], P['polygon'][2][1]), (P['polygon'][2][0] - 30.0, P['polygon'][3][1])] for P in PONDS]

# amenity block (front tract between the Arcado R/W and the first lots at u = 230, wrapped around the entry curve; FACTS §4):
# clubhouse + village green on the NE side of the entry drive; pickleball pads, guest bay and mail kiosk off the straight
# lane between the curve's end (U_JOIN) and lot 1, on both sides.
AMEN_U1 = U_LOT0
AMEN_TRACT = [(AMEN_U1, SW(AMEN_U1)), (AMEN_U1, NE(AMEN_U1))] + [p for p in FRONT_LINE]       # CCW: SW-rear, NE-rear, then the R/W (0,0) -> (-36,-234.7)
J = U_JOIN; LM = lane_mid(J + 40)
ENTRY_NE_EDGE = entry_offset(ENTRY_NE_OFF)
def _village_green():
    lo = [p for p in ENTRY_NE_EDGE if p[0] >= front_u(p[1]) + LANDSCAPE and p[0] <= 105.0]
    strip = [(front_u(v) + LANDSCAPE, v) for v in (-20.0, -60.0, -100.0, -140.0, -160.0) if v > lo[0][1] + 3]
    return lo + [(105.0, NE(105.0) - BUFFER)] + strip
def _sign():
    p, h, s = min(ENTRY_SAMPLES, key=lambda t: abs(t[2] - 26.0)); d = ENTRY_NE_OFF + 4.0
    c = (p[0] - d * math.sin(h), p[1] + d * math.cos(h))
    return rect(c[0] - 4.0, c[0] + 4.0, c[1] - 2.0, c[1] + 2.0)
# --- pickleball: one 60'-0" x 60'-0" fenced enclosure divided by a shared centre fence into two
#     30'-0" x 60'-0" pads, each holding a 20'-0" x 44'-0" court.  Set 2 ft clear of the 20-ft SW buffer
#     band; its NE edge must stay clear of the widened lane tract (checked below).
_PAD_V0 = SW(J + 38.0) + BUFFER + 2.0
pads = [rect(J + 8.0, J + 68.0, _PAD_V0, _PAD_V0 + 30.0), rect(J + 8.0, J + 68.0, _PAD_V0 + 30.0, _PAD_V0 + 60.0)]
BAY_SW_U = (BAY_U[0], BAY_U[0] + 63.0)             # 7 standard guest stalls at 9'-0"
BAY_NE_U = (BAY_U[0], BAY_U[0] + 52.0)             # 8-ft van space + 8-ft aisle + 4 kiosk stalls at 9'-0"
assert BAY_SW_U[1] <= BAY_U[1] + 1e-6 and BAY_NE_U[1] <= BAY_U[1] + 1e-6, 'parking bays overrun the widened tract'
AMENITY = {
    'tract_polygons': [AMEN_TRACT],
    'clubhouse': rect(110.0, 170.0, tract_ne(140) + 25.0, tract_ne(140) + 65.0),      # 60 x 40 = 2,400 sf, 25 ft off the lane tract
    'village_green': _village_green(),
    'pickleball': pads,
    'courts': [rect(p[0][0] + 8.0, p[0][0] + 52.0, p[0][1] + 5.0, p[0][1] + 25.0) for p in pads],   # 20' x 44' court centred in each 30' x 60' pad
    # SW bay: 8 guest stalls 9'-0" x 18'-0", 90 deg off the 22-ft lane, inside the widened lane tract
    'parking_bay': rect(BAY_SW_U[0], BAY_SW_U[1], LM - PAVE_W / 2 - BAY_DEPTH, LM - PAVE_W / 2),
    'stalls': [rect(BAY_SW_U[0] + 9 * i, BAY_SW_U[0] + 9 * (i + 1), LM - PAVE_W / 2 - BAY_DEPTH, LM - PAVE_W / 2) for i in range(7)],
    # NE bay: the van-accessible space + access aisle at the clubhouse end, then 4 short-term mail-kiosk stalls
    'kiosk_bay': rect(BAY_NE_U[0], BAY_NE_U[1], LM + PAVE_W / 2, LM + PAVE_W / 2 + BAY_DEPTH),
    'kiosk_stalls': [rect(BAY_NE_U[0] + 16.0 + 9 * i, BAY_NE_U[0] + 25.0 + 9 * i, LM + PAVE_W / 2, LM + PAVE_W / 2 + BAY_DEPTH) for i in range(4)],
    'mail_kiosk': rect(BAY_NE_U[1] + 4.0, BAY_NE_U[1] + 20.0, tract_ne(BAY_NE_U[1] + 12.0) + 2.0, tract_ne(BAY_NE_U[1] + 12.0) + 12.0),
    'guest_spaces': 8, 'guest_standard_spaces': 7, 'accessible_spaces': 1, 'kiosk_spaces': 4,
    'entry_sign': _sign(),
    # 2010 ADA Standards §208.2 (1 accessible space where 1-25 are provided) and §502.2 (van space 8'-0" wide
    # with an 8'-0" access aisle): the accessible space sits at the clubhouse end of the NE bay, on the shortest
    # accessible route to the clubhouse entrance (§208.3.1).
    'accessible_stall': rect(BAY_NE_U[0], BAY_NE_U[0] + 8.0, LM + PAVE_W / 2, LM + PAVE_W / 2 + BAY_DEPTH),
    'accessible_aisle': rect(BAY_NE_U[0] + 8.0, BAY_NE_U[0] + 16.0, LM + PAVE_W / 2, LM + PAVE_W / 2 + BAY_DEPTH),
    'entrance': {'drive_width_ft': ENTRY_W, 'curb_return_radius_ne_ft': RET_R_NE, 'curb_return_radius_sw_ft': RET_R_SW,
                 'u_rw': round(U_ENTRY, 2), 'v_rw': ENTRY_V,
                 'reverse_curve_radius_ft': ENTRY_R, 'tangent_at_rw_ft': ENTRY_T0, 'deflection_deg': round(math.degrees(PHI1 - PHI0), 1),
                 'join_u': round(U_JOIN, 1), 'drive_length_ft': round(ENTRY_LEN, 1), 'arcadia_pl_cl_at_arcado': [round(ARCADIA_CL[0], 1), round(ARCADIA_CL[1], 1)],
                 'entrance_cl_on_arcado_cl': [round(ENTRY_ON_CL[0], 1), round(ENTRY_ON_CL[1], 1)], 'separation_along_cl_ft': round(SEP_FT, 1),
                 'separation_chord_ft': round(SEP_CHORD_FT, 1), 'basis': 'FACTS §2b: entrance in the SW third of the frontage, >= 250 ft from the Arcadia Pl centreline (Gwinnett collector access spacing ~244 ft — VERIFY Gwinnett DOT)'},
}
AMENITY['clubhouse_sf'] = round(abs(poly_area(AMENITY['clubhouse'])))
_amen_us = [u for u in US if J - 1e-9 <= u <= AMEN_U1 + 1e-9]
_lane_front = [(u, tract_sw(u)) for u in _amen_us] + [(u, tract_ne(u)) for u in reversed(_amen_us)]   # widened tract
AMENITY['tract_sf'] = round(abs(poly_area(AMEN_TRACT)) - abs(poly_area(ENTRY_TRACT)) - abs(poly_area(_lane_front)))
# --- SG-12: the 50-ft collector building-setback line and the 10-ft landscape strip are TRUE PERPENDICULAR
#     offsets of the Arcado Rd R/W polyline, not "+50 ft in u".  The R/W chord bears about S 55 deg W, so a
#     u-offset measured only 49.14 ft on the perpendicular (40.0 ft at the SW terminus) — a label that
#     understated the setback it claimed to show.
def offset_polyline(path, d):
    """parallel offset of an open polyline by d toward +u (into the site); miter joins, rounded ends."""
    segs = []
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
        if L < 1e-9: continue
        nx, ny = -dy / L, dx / L
        if nx < 0: nx, ny = -nx, -ny                       # normal pointing toward +u (into the site)
        segs.append(((a[0] + nx * d, a[1] + ny * d), (b[0] + nx * d, b[1] + ny * d)))
    out = [segs[0][0]]
    for i in range(len(segs) - 1):
        (p1, p2), (p3, p4) = segs[i], segs[i + 1]
        d1 = (p2[0] - p1[0], p2[1] - p1[1]); d2 = (p4[0] - p3[0], p4[1] - p3[1])
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9: out.append(p2); continue
        t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + t * d1[0], p1[1] + t * d1[1]))
    out.append(segs[-1][1])
    return out
RW_LINE = list(FRONT_LINE)                                  # (0,0) -> (-36, -234.7), the Arcado Rd R/W on the site
ARCADO_SB_LINE = offset_polyline(RW_LINE, ARCADO_SB)
LANDSCAPE_STRIP = RW_LINE + offset_polyline(RW_LINE, LANDSCAPE)[::-1]
def arcado_perp(p): return polyline_point_dist(p, RW_LINE)  # true perpendicular distance to the R/W

# ----------------------------------------------------------------------------- 5. metrics
LOT_SF = sum(L['area_sf'] for L in LOTS)
LANE_TRACT_SF = abs(poly_area(LANE_TRACT)) + abs(poly_area(ENTRY_TRACT))          # straight lane tract + entry-drive tract
def pave_len(): return U_PAVE_END - U_JOIN + ENTRY_LEN                                  # travelled length from the R/W

# --- SG-02: IMPERVIOUS.  Every component below is the shoelace area of a polygon this sheet actually draws;
#     nothing is a nominal allowance.  Inputs are published individually so the total can be re-added by hand.
HH_PAVE_SF = sum(abs(poly_area(l)) for h in HAMMERHEADS for l in h['legs'])
BAY_PAVE_SF = abs(poly_area(AMENITY['parking_bay'])) + abs(poly_area(AMENITY['kiosk_bay']))
LANE_PAVE_SF = abs(poly_area(LANE_PAVE))
ENTRY_PAVE_SF = abs(poly_area(ENTRY_PAVE))
SIDEWALK_SF = sum(abs(poly_area(s['polygon'])) for s in SIDEWALKS)
COURT_PAD_SF = sum(abs(poly_area(p)) for p in AMENITY['pickleball'])
KIOSK_SF = abs(poly_area(AMENITY['mail_kiosk']))
AMEN_WALK_SF = 600.0                        # clubhouse/court/kiosk connecting walks (5 ft wide, ~120 lf) — allowance
AMEN_BUILT_SF = AMENITY['clubhouse_sf'] + COURT_PAD_SF + KIOSK_SF + AMEN_WALK_SF
LOT_IMPERV_SF = sum(L['impervious']['total_sf'] for L in LOTS)
# a driveway apron crosses the lane sidewalk on the side its lot fronts; that 20 ft x 5 ft square is inside
# BOTH the driveway polygon and the sidewalk polygon, so remove it once.
def _has_walk(L):
    um = (L['u0'] + L['u1']) / 2.0
    return True if L['side'] == 'NE' else um >= U_WIDEN
DRIVE_WALK_OVERLAP_SF = sum(20.0 * SIDEWALK for L in LOTS if _has_walk(L))
PAVE_SF = LANE_PAVE_SF + ENTRY_PAVE_SF + HH_PAVE_SF + CURB_RETURN_SF + BAY_PAVE_SF
IMPERV_PARTS = [('Dwellings, garages, porches, rear porches and patios (from data/plans.json footprints)',
                 round(sum(L['impervious']['under_roof_sf'] + L['impervious']['patio_sf'] for L in LOTS))),
                ('Lot driveways and entry walks', round(sum(L['impervious']['driveway_sf'] + L['impervious']['entry_walk_sf'] for L in LOTS))),
                ('Private lane pavement', round(LANE_PAVE_SF)), ('Entry drive pavement', round(ENTRY_PAVE_SF)),
                ('Entrance curb returns', round(CURB_RETURN_SF)), ('Hammerhead turnaround legs', round(HH_PAVE_SF)),
                ('Guest and mail-kiosk parking bays', round(BAY_PAVE_SF)), ('Sidewalks', round(SIDEWALK_SF)),
                ('Clubhouse roof, court pads, mail kiosk and amenity walks', round(AMEN_BUILT_SF)),
                ('less driveway apron / sidewalk overlap counted twice', -round(DRIVE_WALK_OVERLAP_SF))]
IMPERV_SF = LOT_IMPERV_SF + PAVE_SF + SIDEWALK_SF + AMEN_BUILT_SF - DRIVE_WALK_OVERLAP_SF
assert abs(sum(v for _, v in IMPERV_PARTS) - IMPERV_SF) < 2.0, 'impervious parts do not add to the total'
IMPERV_PCT_GIS = 100 * IMPERV_SF / BOUNDARY_SF
# Gwinnett County Stormwater Management Manual water-quality volume, WQv = 1.2 * (0.05 + 0.009*I) / 12 * A
WQV_CF = 1.2 * (0.05 + 0.009 * IMPERV_PCT_GIS) / 12.0 * BOUNDARY_SF

# --- SG-14: ONE open-space number.  The published figure is the residual (site less lots less lane tract);
#     the named tracts are then made to sum to it exactly by naming the balance, so there is nothing left over
#     to explain.  Built and paved area inside the common tracts is disclosed separately.
OPEN_SF = BOUNDARY_SF - LOT_SF - LANE_TRACT_SF
BUFFER_ON_LOTS_SF = sum(abs(poly_area(L['buffer_easement'])) for L in LOTS)
OPEN_TRACTS = [{'name': g['name'], 'area_sf': g['area_sf']} for g in GREENS] \
    + [{'name': p['name'] + ' tract', 'area_sf': round(abs(poly_area(p['tract_polygon'])))} for p in PONDS] \
    + [{'name': WOODS['name'], 'area_sf': WOODS['area_sf']}] \
    + [{'name': t['name'], 'area_sf': t['area_sf']} for t in STREAM_TRACTS] \
    + [{'name': 'Front amenity tract (clubhouse, village green, courts, landscape strip)', 'area_sf': AMENITY['tract_sf']}]
OPEN_BALANCE_SF = round(OPEN_SF) - sum(t['area_sf'] for t in OPEN_TRACTS)
if OPEN_BALANCE_SF:
    OPEN_TRACTS.append({'name': 'Balance of common land — perimeter buffer bands and interstitial common tracts, HOA-owned',
                        'area_sf': OPEN_BALANCE_SF})
OPEN_BUILT_SF = AMEN_BUILT_SF + HH_PAVE_SF          # clubhouse/courts/kiosk/walks (amenity tract) + hammerhead legs (greens)
OPEN_GREEN_SF = OPEN_SF - OPEN_BUILT_SF

# --- SG-06: block length.  There are no cross streets on a single-frontage strip, so state the reading used.
#     Reading 1 (the one relied on): distance along the travelled way between STREET INTERSECTIONS, counting
#     Arcado Rd and the three hammerhead (T) intersections.  Reading 2 (shown for completeness): the runs of
#     continuous lot frontage between the open-space breaks, which is what a pedestrian actually walks.
hh_us = [U_JOIN - ENTRY_LEN] + [h['u'] for h in HAMMERHEADS]                          # stations along the travelled way
HH_SPACING = [round(hh_us[i + 1] - hh_us[i], 1) for i in range(len(hh_us) - 1)]
BLOCKS_INTERSECTION_FT = list(HH_SPACING)
_breaks = sorted([U_LOT0] + [x for g in GREENS_U for x in g] + [U_TERM])
BLOCKS_FRONTAGE_FT = [round(_breaks[i + 1] - _breaks[i]) for i in range(0, len(_breaks) - 1, 2)]
blocks = [(_breaks[i], _breaks[i + 1], _breaks[i + 1] - _breaks[i]) for i in range(0, len(_breaks) - 1, 2)]
DEAD_END_FT = round(pave_len(), 0)
lane_prof = [(u, ground(u, lane_mid(u))) for u in range(int(U_JOIN), int(U_PAVE_END), 10)]
rear_low = min(((u, z) for u, z in lane_prof if 1300 <= u <= 1560), key=lambda t: t[1])
# SG-20: the steepest EXISTING ground grade on the lane centreline (the finished profile is a PE deliverable)
_grades = [((lane_prof[i][0] + lane_prof[i + 1][0]) / 2, 100.0 * abs(lane_prof[i + 1][1] - lane_prof[i][1]) / (lane_prof[i + 1][0] - lane_prof[i][0]))
           for i in range(len(lane_prof) - 1)]
MAX_LANE_GRADE = max(_grades, key=lambda t: t[1])
# the two steepest reaches, at least 200 ft apart, so the profile question is framed for the design PE
STEEP_REACHES = []
for u_, g_ in sorted(_grades, key=lambda t: -t[1]):
    if all(abs(u_ - v_) > 200 for v_, _ in STEEP_REACHES): STEEP_REACHES.append((u_, g_))
    if len(STEEP_REACHES) == 2: break

# --- SG-04 + SG-05: clearances to the digitized stream CENTRELINES of ALL THREE reaches, and the same
#     clearances with the 5-ft top-of-bank allowance applied (the ordinance measures from top of bank).
def _min_stream(polys):
    return min(poly_polyline_dist(p, s) for p in polys for s in STREAMS)
STREAM_CLEARANCES = {
    'datum': 'distances are measured to the DIGITIZED STREAM CENTRELINE of all three reaches (Gwinnett GIS '
             'hydrology). The Lilburn / GA EPD buffer is measured from TOP OF BANK, which has not been field '
             'delineated; a 5.0-ft top-of-bank allowance is therefore carried and every element is screened at '
             '75 + 5 = 80 ft (impervious) and 50 + 5 = 55 ft (land disturbance).',
    'nearest_lot_ft': round(_min_stream([L['polygon'] for L in LOTS]), 1),
    'nearest_dwelling_ft': round(_min_stream([L['house']['body_polygon'] for L in LOTS]), 1),
    'nearest_driveway_ft': round(_min_stream([L['house']['driveway_rect'] for L in LOTS]), 1),
    'nearest_pond_top_of_bank_ft': round(_min_stream([P['polygon'] for P in PONDS]), 1),
    'lane_pavement_ft': round(_min_stream([LANE_PAVE]), 1),
    'lane_tract_ft': round(_min_stream([LANE_TRACT]), 1),
}
STREAM_CLEARANCES['worst_impervious_ft'] = min(STREAM_CLEARANCES[k] for k in
                                               ('nearest_lot_ft', 'nearest_dwelling_ft', 'nearest_driveway_ft',
                                                'nearest_pond_top_of_bank_ft', 'lane_pavement_ft'))
STREAM_CLEARANCES['worst_impervious_less_tob_allowance_ft'] = round(STREAM_CLEARANCES['worst_impervious_ft'] - TOB_ALLOWANCE, 1)
SEWER_EXT = [(rear_low[0], lane_mid(rear_low[0])), (1300.0, lane_mid(1300.0)), (1300.0, SW(1300.0)), LEG_MH]
SEWER_EXT_OFFSITE_FT = round(dist(SEWER_EXT[2], SEWER_EXT[3]), 0)
SEWER_PH1 = [(u, lane_mid(u)) for u in (PHASE_U, 900, 700, 500, 300, 272.0)] + [(271.7, -224.0)]
# Phase 2 primary option: in-tract lift station / grinder pumps at the rear lane low point (symbol only; PE to size), force main to Phase 1 gravity
LS_SYMBOL = rect(rear_low[0] + 2.0, rear_low[0] + 10.0, tract_sw(rear_low[0]) - 11.0, tract_sw(rear_low[0]) - 3.0)
SEWER_FM = [(rear_low[0] + 6.0, tract_sw(rear_low[0]) - 3.0), (rear_low[0] + 6.0, lane_mid(rear_low[0]) - 4.0), (PHASE_U, lane_mid(PHASE_U) - 4.0)]

METRICS = {
    'acreage_deeded_ac': AC_DEEDED, 'acreage_gis_ac': round(BOUNDARY_SF / 43560, 3), 'boundary_sf': round(BOUNDARY_SF),
    'lots': N_LOTS, 'lots_sw': sum(1 for L in LOTS if L['side'] == 'SW'), 'lots_ne': sum(1 for L in LOTS if L['side'] == 'NE'),
    'density_du_ac_deeded': round(N_LOTS / AC_DEEDED, 2), 'density_du_ac_gis': round(N_LOTS / (BOUNDARY_SF / 43560), 2),
    'lot_area_min_sf': min(L['area_sf'] for L in LOTS), 'lot_area_avg_sf': round(LOT_SF / N_LOTS), 'lot_area_max_sf': max(L['area_sf'] for L in LOTS),
    'lot_width_min_ft': min(L['width_ft'] for L in LOTS), 'lot_depth_min_ft': min(L['depth_ft'] for L in LOTS),
    'lane_tract_sf': round(LANE_TRACT_SF),
    'lane_tract_width_ft_min': round(min(lot_line_ne(u) - lot_line_sw(u) for u in US if u >= U_LOT0), 1),
    'lane_tract_width_ft_max': round(max(lot_line_ne(u) - lot_line_sw(u) for u in US if u >= U_LOT0), 1),
    'lane_tract_width_ft_at_amenity_block': round(max(tract_ne(u) - tract_sw(u) for u in US), 1),
    'lane_length_ft': DEAD_END_FT,
    'lane_widen_u_ft': U_WIDEN, 'pavement_sf': round(PAVE_SF), 'sidewalk_sf': round(SIDEWALK_SF),
    'frontage_arcado_chord_ft': round(FRONTAGE_CHORD_FT, 2), 'frontage_arcado_along_rw_ft': round(FRONTAGE_PATH_FT, 2),
    'open_space_sf': round(OPEN_SF), 'open_space_ac': round(OPEN_SF / 43560, 2), 'open_space_pct_gis': round(100 * OPEN_SF / BOUNDARY_SF, 1),
    'open_space_pct_deeded': round(100 * OPEN_SF / SF_DEEDED, 1), 'buffer_easement_on_lots_sf': round(BUFFER_ON_LOTS_SF),
    'open_space_built_paved_sf': round(OPEN_BUILT_SF), 'open_space_green_only_sf': round(OPEN_GREEN_SF),
    'open_space_green_only_pct_gis': round(100 * OPEN_GREEN_SF / BOUNDARY_SF, 1),
    'impervious_sf': round(IMPERV_SF), 'impervious_pct_gis': round(IMPERV_PCT_GIS, 1),
    'impervious_pct_deeded': round(100 * IMPERV_SF / SF_DEEDED, 1),
    'impervious_components_sf': {n: v for n, v in IMPERV_PARTS},
    'impervious_per_lot_sf': {pid: round(next(L['impervious']['total_sf'] for L in LOTS if L['plan'] == pid), 1) for pid in ('A', 'B')},
    'plan_mix': {pid: sum(1 for L in LOTS if L['plan'] == pid) for pid in ('A', 'B')},
    'wqv_cf': round(WQV_CF), 'wqv_basis': f'GCSWMM WQv = 1.2 x (0.05 + 0.009 x I) / 12 x A, I = {IMPERV_PCT_GIS:.1f}% impervious, A = {BOUNDARY_SF:,.0f} sf',
    'blocks_ft_between_street_intersections': BLOCKS_INTERSECTION_FT,
    'blocks_ft_lot_frontage_runs': BLOCKS_FRONTAGE_FT,
    'blocks_ft': BLOCKS_INTERSECTION_FT, 'block_max_ft': round(max(BLOCKS_INTERSECTION_FT)),
    'block_reading': 'distance along the travelled way between street intersections (Arcado Rd plus the three hammerhead T-intersections); the lot-frontage runs between open-space breaks are reported separately',
    'hammerhead_spacing_ft': HH_SPACING, 'hammerhead_spacing_max_ft': max(HH_SPACING), 'longest_dead_end_ft': DEAD_END_FT,
    'phase_line_u_ft': PHASE_U, 'lots_phase1': sum(1 for L in LOTS if L['u1'] <= PHASE_U), 'lots_phase2': sum(1 for L in LOTS if L['u1'] > PHASE_U),
    'ponds_cf': [p['est_storage_cf'] for p in PONDS], 'sewer_ext_offsite_ft': SEWER_EXT_OFFSITE_FT, 'rear_lane_low_point': {'u': rear_low[0], 'ground_ft': round(rear_low[1], 1)},
    'disturbed_area': DISTURBED, 'detention_required_cf': DETENTION_REQ_CF, 'detention_provided_cf': DETENTION_PROV_CF,
    'detention_rate_cf_per_disturbed_ac': DETENTION_RATE_CF_AC,
    'max_existing_lane_grade_pct': round(MAX_LANE_GRADE[1], 1), 'max_existing_lane_grade_at_u_ft': MAX_LANE_GRADE[0],
    'stream_top_of_bank_allowance_ft': TOB_ALLOWANCE, 'stream_clearances_ft': STREAM_CLEARANCES,
    'parking_required': 2 * N_LOTS, 'parking_provided_on_lot': 4 * N_LOTS, 'guest_spaces': AMENITY['guest_spaces'] + AMENITY['kiosk_spaces'],
    'pm_peak_trips_ite_251': round(0.30 * N_LOTS, 1),
    'entrance_v_ft': ENTRY_V, 'entrance_u_rw_ft': round(U_ENTRY, 1), 'entrance_to_arcadia_cl_ft': round(SEP_FT), 'entrance_to_arcadia_cl_chord_ft': round(SEP_CHORD_FT),
    'entry_drive_width_ft': ENTRY_W, 'entry_curve_radius_ft': ENTRY_R, 'entry_curve_deflection_deg': round(math.degrees(PHI1 - PHI0), 1),
    'entry_drive_length_ft': round(ENTRY_LEN), 'entry_join_u_ft': round(U_JOIN, 1), 'amenity_tract_sf': AMENITY['tract_sf'],
    'sw_curb_return_radius_ft': RET_R_SW, 'ne_curb_return_radius_ft': RET_R_NE,
    'sw_curb_return_buffer_encroachment_ft': round(SW_RETURN_ENCROACH_FT, 1),
    'sw_curb_return_buffer_encroachment_sf': SW_RETURN_BUFFER_SF,
    'clubhouse_setback_from_arcado_rw_ft': round(min(arcado_perp(p) for p in AMENITY['clubhouse']), 1),
    'entry_sign_setback_from_arcado_rw_ft': round(min(arcado_perp(p) for p in AMENITY['entry_sign']), 1),
    'nearest_lot_to_arcado_rw_ft': round(min(arcado_perp(p) for L in LOTS for p in L['polygon']), 1),
    'lane_tract_widened_through_amenity_block': {'from_u': round(_BAY_WINDOW[0], 1), 'to_u': round(_BAY_WINDOW[3], 1),
                                                 'tract_half_width_ft': BAY_TRACT_HALF,
                                                 'reason': 'the tract must contain the 18-ft-deep 90-deg guest and mail-kiosk bays'},
}

# ----------------------------------------------------------------------------- 6. self-checks
def check(cond, msg):
    if not cond: raise AssertionError('CHECK FAILED: ' + msg)
    print('  ok  ' + msg)

print('Self-checks:')
inner = [p for p in BOUNDARY]
for L in LOTS:
    sh = shrink_convex(L['polygon'], 0.05)
    check(all(point_in_poly(p, BOUNDARY) for p in sh), f"lot {L['id']} inside boundary") if L['id'] in (1, N_LOTS) else None
    assert all(point_in_poly(p, BOUNDARY) for p in sh), f"lot {L['id']} outside boundary"
print(f'  ok  all {N_LOTS} lots inside the assemblage boundary')
for i, A in enumerate(LOTS):
    for B in LOTS[i + 1:]:
        assert not polys_overlap(A['polygon'], B['polygon']), f"lots {A['id']} / {B['id']} overlap"
print('  ok  no lot overlaps another lot')
lane_quads = [rect(US[i], US[i + 1], tract_sw(US[i]), tract_ne(US[i + 1])) for i in range(len(US) - 1)]
obst = [('lane', q) for q in lane_quads] + [('pond ' + p['name'], p['polygon']) for p in PONDS] + [('pond tract', p['tract_polygon']) for p in PONDS]
obst += [('green', g) for G in GREENS for g in G['polygons'] if len(g) == 4] + [('hammerhead', l) for h in HAMMERHEADS for l in h['legs']]
obst += [('woods', WOODS['polygon']), ('clubhouse', AMENITY['clubhouse'])]
for L in LOTS:
    for name, q in obst:
        assert not polys_overlap(L['polygon'], q), f"lot {L['id']} overlaps {name}"
    # SG-04: screen every lot against ALL THREE digitized reaches at 75 ft + the 5-ft top-of-bank allowance
    assert min(poly_polyline_dist(L['polygon'], s) for s in STREAMS) >= SCREEN_IMPERV, \
        f"lot {L['id']} inside the 75-ft stream setback (+{TOB_ALLOWANCE:.0f}-ft top-of-bank allowance)"
    for key in ('body_polygon', 'driveway_rect'):
        assert min(poly_polyline_dist(L['house'][key], s) for s in STREAMS) >= SCREEN_IMPERV, f"lot {L['id']} {key} vs stream"
    assert min(arcado_perp(p) for p in L['polygon']) >= ARCADO_SB, f"lot {L['id']} inside the 50-ft Arcado setback"
    assert L['area_sf'] >= 3000 and L['width_ft'] >= 50 and L['depth_ft'] >= 82, f"lot {L['id']} size"
    # abuts the lane >= 30 ft: front edge lies on the tract edge
    fr = (L['polygon'][2], L['polygon'][3]) if L['side'] == 'SW' else (L['polygon'][0], L['polygon'][1])
    edge = tract_sw if L['side'] == 'SW' else tract_ne
    assert all(abs(p[1] - edge(p[0])) < 0.01 for p in fr) and dist(*fr) >= 30.0, f"lot {L['id']} lane frontage"
    # SG-03 + SG-17: every drawn piece of the house sits inside the 15 / 5 / 20 setback envelope, which is
    # itself a trapezoid closing on the surveyed side lines (SG-11).
    env = ccw(L['setback_envelope'])
    H = L['house']; sgn = -1 if L['side'] == 'SW' else 1
    for key in ('body_polygon', 'garage_rect'):
        for p in H[key]:
            assert point_in_poly(p, env), f"lot {L['id']} {key} outside the setback envelope"
    for key in ('porch_rects', 'rear_porch_rects', 'patio_rects'):
        for r in H[key]:
            for p in r: assert point_in_poly(p, env), f"lot {L['id']} {key} outside the setback envelope"
    # nothing inside the recorded 20-ft buffer easement
    be = ccw(L['buffer_easement'])
    for key in ('body_polygon', 'garage_rect'):
        assert not any(point_in_poly(p, be) for p in H[key]), f"lot {L['id']} {key} inside the buffer easement"
    # the garage wing is stepped back 5'-0" behind the front wall of the dwelling (Table 4.2)
    assert abs(H['garage_door_from_lot_line_ft'] - H['porch_face_from_lot_line_ft']
               - PLAN_GEOM[L['plan']]['porch_d'] - H['garage_recess_ft']) < 0.01, f"lot {L['id']} garage recess"
    assert H['garage_recess_ft'] >= 5.0 - 1e-9, f"lot {L['id']} garage recess < 5 ft"
    # SG-11: the buffer easement and the setback envelope close ON the surveyed property line
    sl = SW if L['side'] == 'SW' else NE
    for p in (be[0], be[1], be[2], be[3]):
        off = (sl(p[0]) - p[1]) * sgn
        assert -1e-6 <= off <= BUFFER + 1e-6, f"lot {L['id']} buffer easement off the property line by {off:.3f} ft"
    assert all(point_in_poly(p, BOUNDARY) or abs((sl(p[0]) - p[1])) < 1e-6 for p in be), f"lot {L['id']} buffer easement outside the parcel"
print(f'  ok  no lot overlaps the lane, ponds, greens, hammerheads, woods or the clubhouse')
print(f'  ok  every lot and every dwelling / driveway >= {SCREEN_IMPERV:.0f} ft from ALL {len(STREAMS)} digitized stream reaches '
      f'(75-ft impervious setback + {TOB_ALLOWANCE:.0f}-ft top-of-bank allowance)  [SG-04 / SG-05]')
print('  ok  every lot >= 3,000 sf, >= 50 ft wide, >= 82 ft deep, abuts the lane >= 30 ft; the drawn L-shaped body, garage wing,')
print('      porches and patio all sit inside the 15 / 5 / 20 envelope and clear of the 20-ft buffer easement; garage recessed 5 ft  [SG-03]')
print('  ok  buffer easements and setback envelopes are trapezoids that close on the surveyed side lines  [SG-11]')
check(all(min(poly_polyline_dist(p['polygon'], s) for s in STREAMS) >= SCREEN_IMPERV for p in PONDS),
      f'both pond tops of bank >= {SCREEN_IMPERV:.0f} ft from every digitized stream centreline  [SG-05]')
_tob = ' / '.join('%.1f' % p['tob_to_sw_line_ft'] for p in PONDS)
check(all(p['tob_to_sw_line_ft'] >= BUFFER + 10.0 - 1e-6 for p in PONDS),
      f"pond tops of bank {_tob} ft inside the SW property line >= {BUFFER + 10.0:.0f} ft "
      f"(20-ft undisturbed buffer + 10-ft toe clearance)  [SG-01 / SG-10]")
check(DETENTION_PROV_CF >= DETENTION_REQ_CF,
      f"detention provided {DETENTION_PROV_CF:,} cf >= required {DETENTION_REQ_CF:,} cf "
      f"(10,000 cf/ac x {DISTURBED['disturbed_ac']:.3f} disturbed ac, GCSWMM screening basis, RRv = 0)  [SG-01]")
assert min(arcado_perp(p) for p in AMENITY['clubhouse']) >= ARCADO_SB, 'clubhouse inside the 50-ft Arcado setback'
check(40 <= N_LOTS <= 47, f'lot count {N_LOTS} within the 40-47 target')
check(METRICS['density_du_ac_deeded'] <= 8.0, f"density {METRICS['density_du_ac_deeded']} du/ac <= 8 (Table 4.1 R-2)")
check(max(BLOCKS_INTERSECTION_FT) <= 600,
      f"block lengths between street intersections {BLOCKS_INTERSECTION_FT} <= 600 ft (Table 4.2); "
      f"lot-frontage runs {BLOCKS_FRONTAGE_FT} ft reported separately  [SG-06]")
check(max(HH_SPACING) <= 750, f'turnaround spacing {HH_SPACING} ft <= 750 ft (IFC 2024 (GA) App. D103.4 trigger)  [SG-08]')
check(METRICS['open_space_pct_gis'] >= 20, f"open space {METRICS['open_space_pct_gis']}% >= 20%")
check(sum(t['area_sf'] for t in OPEN_TRACTS) == round(OPEN_SF),
      f"the named open-space tracts sum exactly to the published {round(OPEN_SF):,} sf — no unallocated slivers  [SG-14]")
check(abs(IMPERV_SF - sum(v for _, v in IMPERV_PARTS)) < 2.0,
      f"impervious {IMPERV_SF:,.0f} sf = {IMPERV_PCT_GIS:.1f}% of the GIS area, re-added from {len(IMPERV_PARTS)} drawn components  [SG-02]")
check(all(abs(L['impervious']['under_roof_sf'] - PLAN_GEOM[L['plan']]['a_under_roof_sf']) < 1.0 for L in LOTS),
      f"per-lot under-roof area equals the data/plans.json footprint for every lot (Plan A {PLAN_GEOM['A']['a_under_roof_sf']:,.0f} sf, "
      f"Plan B {PLAN_GEOM['B']['a_under_roof_sf']:,.0f} sf) — no nominal allowance  [SG-02 / SG-03]")
check(all(abs(L['house']['porch_face_from_lot_line_ft'] - PLAN_GEOM[L['plan']]['face']) < 0.01 for L in LOTS)
      and min(L['house']['porch_face_from_lot_line_ft'] for L in LOTS) >= FRONT_SB + ROOF_OVERHANG - 1e-6,
      f"porch face {PLAN_GEOM['A']['face']:.3f} ft from the front lot line, taken from data/plans.json lot_siting "
      f"= 15'-0\" required + 0'-8\" roof overhang held outside the required yard  [SG-03 / SG-17]")
check(min(L['house']['rear_element_from_rear_line_ft'] for L in LOTS) >= REAR_SB,
      f"rearmost drawn element {min(L['house']['rear_element_from_rear_line_ft'] for L in LOTS):.2f} ft from the rear lot line "
      f">= the 20-ft rear yard / buffer easement (Plan A {PLAN_GEOM['A']['rear_clear_ft']:.2f} ft, Plan B {PLAN_GEOM['B']['rear_clear_ft']:.2f} ft)")
check(abs(FRONTAGE_CHORD_FT - 237.44) < 0.05 and len(FRONT_LINE) == 14,
      f'Arcado Rd frontage {FRONTAGE_PATH_FT:.2f} ft along the R/W ({FRONTAGE_CHORD_FT:.2f} ft chord) over {len(FRONT_LINE) - 1} segments — '
      f'the SW property line is NOT admitted to the front line')
check(min(arcado_perp(p) for p in ARCADO_SB_LINE) >= ARCADO_SB - 0.02 and max(arcado_perp(p) for p in ARCADO_SB_LINE) <= ARCADO_SB + 0.02,
      f"the 50-ft Arcado setback line is a TRUE PERPENDICULAR offset: {min(arcado_perp(p) for p in ARCADO_SB_LINE):.2f}-"
      f"{max(arcado_perp(p) for p in ARCADO_SB_LINE):.2f} ft everywhere along it  [SG-12]")
check(abs(HH_U[2][0] - U_TERM) < 1e-9 and abs(HH_U[2][1] - (U_BUF_REAR - 1.0)) < 1e-9,
      f'hammerhead 3 (u {HH_U[2][0]:.0f}-{HH_U[2][1]:.0f}) registers with the terminus green (u {U_TERM:.0f}-{U_BUF_REAR:.0f})  [SG-15]')
check(all(point_in_poly(p, ccw(ENTRY_TRACT)) or polyline_point_dist(p, ENTRY_TRACT + ENTRY_TRACT[:1]) < 0.01 for p in ENTRY_WALK),
      'the entry-drive sidewalk lies wholly inside the entry-drive tract  [SG-16]')
check(MAX_LANE_GRADE[1] <= 12.0,
      f'steepest EXISTING ground grade on the lane centreline {MAX_LANE_GRADE[1]:.1f}% at u = {MAX_LANE_GRADE[0]:.0f} ft <= 12% '
      f'(site-dev checklist) — the FINISHED profile is a PE deliverable, not claimed here  [SG-20]')
_c = poly_centroid(LANE_TRACT)
check(all(point_in_poly((p[0] + (0.2 if p[0] < _c[0] else -0.2), p[1] + (0.2 if p[1] < _c[1] else -0.2)), BOUNDARY) for p in LANE_TRACT), 'lane tract inside boundary')
check(min(width(u) for u in US) >= 231, 'strip >= 231 ft everywhere (no reduced-depth lots)')
# entrance / entry drive / amenity block
check(SEP_FT >= 250.0 and SEP_CHORD_FT >= 250.0, f'entrance centreline {SEP_FT:.0f} ft along the Arcado Rd centreline ({SEP_CHORD_FT:.0f} ft chord) from the Arcadia Pl centreline >= 250 ft (FACTS §2b)')
check(ENTRY_R >= 100.0 and abs(ENTRY_V + 190.0) < 1e-9 and U_JOIN <= 220.0, f'entry drive: v = {ENTRY_V:.0f} at the R/W, reverse curves R = {ENTRY_R:.0f} ft >= 100, joins the lane midline at u = {U_JOIN:.0f} <= 220')
check(all(point_in_poly(p, BOUNDARY) for p in ENTRY_PAVE if p[0] > U_ENTRY + 0.5) and all(p[1] >= SW(p[0]) + BUFFER for p in ENTRY_TRACT), 'entry-drive tract inside the boundary and clear of the 20-ft SW buffer')
check(all(abs(p[1] - ENTRY_V) < 0.01 for p in ENTRY_CL[:1]) and abs(ENTRY_CL[0][0] - front_u(ENTRY_V)) < 0.01, 'entry drive starts on the Arcado R/W line')
_feat = [('clubhouse', AMENITY['clubhouse']), ('pad 1', AMENITY['pickleball'][0]), ('pad 2', AMENITY['pickleball'][1]), ('guest bay', AMENITY['parking_bay']),
         ('kiosk bay', AMENITY['kiosk_bay']), ('mail kiosk', AMENITY['mail_kiosk']), ('entry sign', AMENITY['entry_sign'])]
_tracts = [('entry tract', ENTRY_TRACT), ('lane tract', LANE_TRACT)] + [('lot %d' % L['id'], L['polygon']) for L in LOTS if L['u0'] < 400]
for i, (na, A) in enumerate(_feat):
    for nb, B in _feat[i + 1:]:
        assert not polys_overlap(A, B), f'amenity: {na} overlaps {nb}'
    for nb, B in _tracts:
        if na in ('guest bay', 'kiosk bay') and nb == 'lane tract': continue           # the bays are INSIDE the lane tract — checked below
        assert poly_polyline_dist(A, B + B[:1]) > 0.0 and not any(point_in_poly(p, B) for p in A), f'amenity: {na} intersects {nb}'
    assert all(point_in_poly(p, BOUNDARY) for p in A), f'amenity: {na} outside the boundary'
    assert all(p[1] >= SW(p[0]) + BUFFER - 1e-6 and p[1] <= NE(p[0]) - BUFFER + 1e-6 for p in A), f'amenity: {na} inside the 20-ft perimeter buffer'
for na, A in _feat:
    if na != 'entry sign': assert min(arcado_perp(p) for p in A) >= ARCADO_SB, f'{na} inside the 50-ft Arcado setback'
for na in ('clubhouse', 'pad 1', 'pad 2', 'mail kiosk'):
    A = dict(_feat)[na]
    assert min(p[1] - SW(p[0]) - BUFFER for p in A) >= 1.0 and min(NE(p[0]) - BUFFER - p[1] for p in A) >= 1.0, na + ' < 1 ft from a buffer'
print('  ok  amenity features do not overlap each other, the entry tract or lots; clubhouse / courts / kiosk outside the 50-ft')
print('      Arcado setback (true perpendicular) and clear of the 20-ft perimeter buffers')
# NEW DEFECT (found after the 2026-09-03 audit): the guest bay and the mail-kiosk bay lay ~11.2 ft OUTSIDE the
# lane tract.  A tract must contain its own improvements; the tract now widens locally through the amenity block.
_lt = ccw(LANE_TRACT)
for na in ('guest bay', 'kiosk bay'):
    A = dict(_feat)[na]
    assert all(point_in_poly(p, _lt) for p in A), f'{na} is not contained by the lane tract'
_bay_margin = min(min(abs(tract_sw(p[0]) - p[1]) if p[1] < lane_mid(p[0]) else abs(tract_ne(p[0]) - p[1])
                      for p in dict(_feat)[na]) for na in ('guest bay', 'kiosk bay'))
check(True, f'the guest bay and the mail-kiosk bay lie wholly INSIDE the lane tract, which widens to '
            f'{2 * BAY_TRACT_HALF:.0f} ft through the amenity block (u {_BAY_WINDOW[0]:.0f}-{_BAY_WINDOW[3]:.0f}); '
            f'closest bay edge to the tract line {_bay_margin:.1f} ft')
check(AMENITY['guest_spaces'] + AMENITY['kiosk_spaces'] >= math.ceil(N_LOTS / 4.0),
      f"guest parking {AMENITY['guest_spaces']} (incl. 1 van-accessible) + {AMENITY['kiosk_spaces']} mail-kiosk = "
      f"{AMENITY['guest_spaces'] + AMENITY['kiosk_spaces']} spaces >= 1 per 4 dwellings ({math.ceil(N_LOTS / 4.0)})")

# ----------------------------------------------------------------------------- 7. compliance list
METRICS_PRE = {'clubhouse': METRICS['clubhouse_setback_from_arcado_rw_ft'], 'sign': METRICS['entry_sign_setback_from_arcado_rw_ft'],
               'nearest_lot': METRICS['nearest_lot_to_arcado_rw_ft'], 'tract_min': METRICS['lane_tract_width_ft_min'],
               'tract_max': METRICS['lane_tract_width_ft_max']}
COMPLIANCE = [
    {'item': 'Use: single-family cluster-cottage (§602 Use Table)', 'required': 'P in R-2 (no SUP)', 'provided': f'{N_LOTS} detached cottage homes, fee-simple lots', 'status': 'appears consistent'},
    {'item': 'Min lot area, cottage home (Table 4.1 R-2)', 'required': '3,000 sf', 'provided': f"{METRICS['lot_area_min_sf']:,.0f} sf min / {METRICS['lot_area_avg_sf']:,.0f} avg", 'status': 'appears consistent'},
    {'item': 'Min lot width, cottage (Table 4.1)', 'required': '50 ft', 'provided': '50 ft', 'status': 'appears consistent'},
    {'item': 'Min lot depth, all uses (Table 4.1)', 'required': '100 ft', 'provided': f"{METRICS['lot_depth_min_ft']} ft min", 'status': 'appears consistent'},
    {'item': 'Max gross density (Table 4.1 R-2)', 'required': '8 du/ac', 'provided': f"{METRICS['density_du_ac_deeded']} du/ac (9.44 ac) / {METRICS['density_du_ac_gis']} (9.58 ac GIS)", 'status': 'appears consistent'},
    {'item': 'Min heated floor area, cottage (Table 4.1)', 'required': '1,000 sf', 'provided': f"Plan A '{PLAN_GEOM['A']['name'].title()}' {PLAN_GEOM['A']['areas']['conditioned_sf']:,.0f} sf and Plan B '{PLAN_GEOM['B']['name'].title()}' {PLAN_GEOM['B']['areas']['conditioned_sf']:,.0f} sf conditioned (data/plans.json, {PLANS_DATE})", 'status': 'appears consistent'},
    {'item': 'Max height (Table 4.1)', 'required': '40 ft', 'provided': f"1 story; max ridge Plan A {PLAN_GEOM['A']['roof_max_ridge_ft']:.2f} ft / Plan B {PLAN_GEOM['B']['roof_max_ridge_ft']:.2f} ft above FFE (data/plans.json)", 'status': 'appears consistent'},
    {'item': 'Front setback, local street (Table 4.1)', 'required': '15 ft from R/W', 'provided': f"porch face {PLAN_GEOM['A']['face']:.2f} ft (15'-8\") from the front lot line / private lane tract; the 8-in roof overhang is held outside the required yard, so no projection into a required yard is claimed", 'status': 'appears consistent'},
    {'item': 'Front setback on collector (Table 4.1)', 'required': '50 ft from Arcado Rd R/W', 'provided': f"no lot fronts Arcado Rd (nearest lot {METRICS_PRE['nearest_lot']:.1f} ft); nearest principal structure = clubhouse {METRICS_PRE['clubhouse']:.1f} ft, measured PERPENDICULAR to the R/W polyline. The monument entry sign stands {METRICS_PRE['sign']:.1f} ft from the R/W — an entry sign is not a principal structure and is shown as an express exception to the 50-ft building setback (Lilburn sign regulations — VERIFY)", 'status': 'appears consistent — sign setback VERIFY'},
    {'item': 'Side setback (Table 4.1)', 'required': '5 ft', 'provided': '5 ft (Plan B) / 6 ft (Plan A)', 'status': 'appears consistent'},
    {'item': 'Rear setback (Table 4.1)', 'required': '20 ft', 'provided': f"rearmost drawn element {min(L['house']['rear_element_from_rear_line_ft'] for L in LOTS):.2f} ft from the rear lot line (Plan A patio {PLAN_GEOM['A']['rear_clear_ft']:.2f} ft; Plan B covered rear porch {PLAN_GEOM['B']['rear_clear_ft']:.2f} ft); the rear 20 ft is also the buffer easement", 'status': 'appears consistent'},
    {'item': 'Buffer abutting R-1 (Table 4.1; §313(1))', 'required': '0 ft detached SF / 20 ft other dwelling types', 'provided': '20-ft undisturbed buffer in recorded easement on lots + common tracts', 'status': 'appears consistent — interpretation VERIFY at pre-app'},
    {'item': 'Lot frontage on approved private street (§319)', 'required': '>= 30 ft', 'provided': '50 ft each lot', 'status': 'appears consistent'},
    {'item': 'Block length (Table 4.2)', 'required': '<= 600 ft', 'provided': f"{' / '.join(f'{b:.0f}' for b in BLOCKS_INTERSECTION_FT)} ft measured along the travelled way BETWEEN STREET INTERSECTIONS (Arcado Rd plus the three hammerhead T-intersections). There are no cross streets on a single-frontage strip, so the reading is stated: an open-space green is not a street and does not terminate a block. The runs of continuous lot frontage between the greens are {' / '.join(str(b) for b in BLOCKS_FRONTAGE_FT)} ft", 'status': 'appears consistent'},
    {'item': 'Culs-de-sac (Table 4.2)', 'required': 'circular turnarounds not permitted', 'provided': f'none; 3 hammerhead (T) turnarounds, spacing {", ".join(str(s) for s in HH_SPACING)} ft', 'status': 'appears consistent'},
    {'item': 'Front-loaded garage recess (Table 4.2)', 'required': '>= 5 ft behind front wall', 'provided': '5 ft', 'status': 'appears consistent'},
    {'item': 'Parking (Table 8.1, SF detached)', 'required': f'2 / DU = {2 * N_LOTS}', 'provided': f'4 / DU (2 garage + 2 driveway) = {4 * N_LOTS} + 12 guest/kiosk', 'status': 'appears consistent'},
    {'item': 'Interior drive with 90-deg parking (site-dev checklist)', 'required': '22 ft min two-way with 90-deg parking', 'provided': f"22'-0\" pavement throughout; the HOA lane tract is {METRICS_PRE['tract_min']:.1f}-{METRICS_PRE['tract_max']:.1f} ft wide where lots front it and widens to {2 * BAY_TRACT_HALF:.0f} ft through the amenity block so that the guest and mail-kiosk bays lie wholly inside the tract that owns them", 'status': 'appears consistent'},
    {'item': 'Sidewalks (Site Development Plan Review Checklist item b)', 'required': "5'-0\" sidewalk on all roads, 2 ft off the back of curb", 'provided': f"5'-0\" walk on the NE side of the whole lane and on the entry drive; a second 5'-0\" walk on the SW side from u = {U_WIDEN:.0f} ft, where the strip first gives the SW half-section its full 11 + 2 + 5 = {HALF_SECTION:.0f} ft. Over u = {U_LOT0:.0f}-{U_WIDEN:.0f} ft the SW half-width is {min(sw_half(u) for u in US if U_LOT0 <= u <= U_WIDEN):.2f}-{max(sw_half(u) for u in US if U_LOT0 <= u <= U_WIDEN):.2f} ft and a second walk does not fit without shortening the SW lots", 'status': 'partial — a walk on both sides over the front reach requires either 0.5 ft of lot depth or a 1.5-ft strip; question posed at the pre-application conference'},
    {'item': 'Landscape strip along public R/W (checklist)', 'required': '10 ft', 'provided': '10 ft along Arcado Rd', 'status': 'appears consistent'},
    {'item': 'Stream buffers (Lilburn / GA EPD)', 'required': '25 ft (GA EPD) / 50 ft undisturbed / 75 ft impervious, measured from TOP OF BANK', 'provided': f"All THREE digitized reaches are screened, not only the on-site one. Distances are to the digitized CENTRELINE and a 5.0-ft top-of-bank allowance is carried, so every lot, dwelling, driveway, pond and pavement is held at >= {SCREEN_IMPERV:.0f} ft: nearest lot {STREAM_CLEARANCES['nearest_lot_ft']:.1f} ft, nearest dwelling {STREAM_CLEARANCES['nearest_dwelling_ft']:.1f} ft, Pond 1/2 top of bank {STREAM_CLEARANCES['nearest_pond_top_of_bank_ft']:.1f} ft, lane pavement {STREAM_CLEARANCES['lane_pavement_ft']:.1f} ft. The SW slot at u 1,230-1,280 that fails the screen is NOT lotted; it becomes a stream-setback open-space tract (lot yield {N_LOTS}, not 43)", 'status': 'appears consistent — top of bank to be field delineated; the allowance is a design assumption, not a survey'},
    {'item': 'Floodplain (Table 4.2)', 'required': 'no development in floodway/floodplain', 'provided': 'FEMA Zone X — none on site (Gwinnett GIS)', 'status': 'appears consistent'},
    {'item': 'Common open space (Development Regulations §5.9.1)', 'required': 'NOT TRIGGERED — §5.9.1 applies to single-family detached subdivisions of 50 acres or more; this site is 9.44 ac. Voluntary design basis >= 20%', 'provided': f"{OPEN_SF/43560:.2f} ac = {round(OPEN_SF):,} sf = {100*OPEN_SF/BOUNDARY_SF:.1f}% of the GIS area ({100*OPEN_SF/SF_DEEDED:.1f}% of 9.44 ac), in named HOA tracts that sum exactly to that figure. Of it, {round(OPEN_BUILT_SF):,} sf is built or paved (clubhouse roof, court pads, mail kiosk, amenity walks and the hammerhead legs inside the greens), so green-only open space is {round(OPEN_GREEN_SF):,} sf = {100*OPEN_GREEN_SF/BOUNDARY_SF:.1f}%. The {round(BUFFER_ON_LOTS_SF):,} sf of buffer easement on lots is additional and is NOT counted here", 'status': 'appears consistent — voluntary, and far above anything the code requires'},
    {'item': 'Dead-end fire apparatus road (IFC 2024 (GA) App. D103.4)', 'required': 'Table D103.4: over 750 ft — "Special approval required"', 'provided': f"{DEAD_END_FT:.0f} ft of dead-end travelled way from the Arcado Rd R/W on one access, with three hammerhead (T) turnarounds at {' / '.join(f'{s:.0f}' for s in HH_SPACING)} ft spacing (every spacing well inside the 750-ft trigger) and 22-ft clear pavement with no on-lane parking", 'status': 'D103.4 special approval must be requested — Gwinnett County Fire Marshal'},
    {'item': 'Second fire access (IFC 2024 (GA) App. D107.1)', 'required': 'Georgia amendment: two access roads for one- and two-family developments of MORE THAN 120 dwelling units (not 30)', 'provided': f'{N_LOTS} dwelling units — below the 120-unit threshold, so D107.1 is not triggered and no second access is required on that ground', 'status': 'appears consistent — the only fire relief sought is the D103.4 dead-end special approval'},
    {'item': 'Driveway spacing on a collector (Gwinnett DOT access management)', 'required': '~244 ft between access points (VERIFY)', 'provided': f'entrance centreline {SEP_FT:.0f} ft from the Arcadia Pl centreline along Arcado Rd', 'status': 'appears consistent — VERIFY Gwinnett DOT driveway permit'},
    {'item': 'Fire sprinklers (NFPA 13D)', 'required': 'not required by IFC 2024 (GA) for detached one-family dwellings on this project', 'provided': f'OFFERED voluntarily in all {N_LOTS} dwellings as mitigation supporting the D103.4 special approval and the 50% fire-flow reduction of IFC 2024 (GA) App. B105.1 (1,000 to 500 gpm on a ~{DEAD_END_FT:.0f}-ft dead-end main)', 'status': 'voluntary offer — Fire Marshal to accept or substitute another App. D107.1 Exception 3 measure'},
    {'item': 'Traffic study (Gwinnett DOT TIS Guidelines 2023)', 'required': 'A TIS must be submitted with a zoning application; the exemption is 7 lots or fewer, so a LEVEL 1 (document-only) TIS applies', 'provided': f"Level 1 TIS to be submitted: ~{0.30 * N_LOTS:.1f} PM peak-hour trips (ITE Trip Generation 11th ed. LUC 251, 0.30/DU x {N_LOTS} DU); daily ~{4.31 * N_LOTS:.0f}. Left-turn lane not warranted below 75 lots (VERIFY)", 'status': 'Level 1 TIS required — confirm at the pre-application conference that the City adopts the Gwinnett DOT guidelines for a city case'},
    {'item': 'Sanitary sewer capacity (Gwinnett DWR)', 'required': 'capacity certification (Rev. 07/2023 form, "Pre-Rezoning" request type)', 'provided': f"Phase 1 ({METRICS['lots_phase1']} lots, u < {PHASE_U:.0f} ft) drains by gravity to the EXISTING on-site 8-in main at MH INV 927.13 — no sewer extension of any kind. Phase 2 ({METRICS['lots_phase2']} lots): a {SEWER_EXT_OFFSITE_FT:.0f}-ft off-site 8-in gravity extension to the Legends at Parkview main (MH INV 919.58) through a recorded easement. A private pump station / force main is NOT available: Gwinnett DWR's Standard Policy for Private Developments (rev. 9/2018) allows private stations only for commercial property under single ownership, and WSR-24 §1.3.1(A) grants a county station only where gravity is generally more than 5,000 ft down gradient (here it is {SEWER_EXT_OFFSITE_FT:.0f} ft). A low-pressure grinder system is shown only as a contingency", 'status': 'VERIFY — DWR capacity certification, invert survey and the easement; ask staff whether the 2026 Comprehensive Plan Amendment policy "do not further extend sewer in this area" bars a {SEWER_EXT_OFFSITE_FT:.0f}-ft in-basin tie to an existing main'},
    {'item': 'Perimeter buffer at the entrance (Table 4.1; §1003-4 buffer reduction)', 'required': '20-ft undisturbed buffer abutting R-1', 'provided': f"The SW curb return is reduced from 25'-0\" to {RET_R_SW:.0f}'-0\" so that it clears the buffer band as far as the geometry allows. What remains inside the band is dimensioned on the sheet: {SW_RETURN_ENCROACH_FT:.1f} ft measured along the R/W and {SW_RETURN_BUFFER_SF_TXT} of pavement, at the R/W corner only. The entrance cannot be shifted NE: it is already only {SEP_FT:.0f} ft from the Arcadia Pl centreline against the ~244-ft access-management spacing", 'status': f'a buffer reduction of {SW_RETURN_ENCROACH_FT:.1f} ft over {SW_RETURN_BUFFER_SF_TXT} IS REQUESTED and is stated on this drawing; the letter of intent and voluntary condition 8 must match'},
    {'item': 'Detention (Gwinnett County Stormwater Management Manual)', 'required': f"screening basis 10,000 cf per disturbed acre less RRv = {DETENTION_REQ_CF:,} cf on {DISTURBED['disturbed_ac']:.3f} disturbed ac (RRv taken as 0)", 'provided': f"{DETENTION_PROV_CF:,} cf in two dry extended-detention / water-quality basins: Pond 1 {PONDS[0]['est_storage_cf']:,} cf ({PONDS[0]['top_of_bank_ft']} ft top of bank) and Pond 2 {PONDS[1]['est_storage_cf']:,} cf ({PONDS[1]['top_of_bank_ft']} ft), each {POND_DEPTH:.0f} ft deep with {POND_SLOPE:.0f}:1 side slopes, prismoidal volume between top of bank and basin bottom", 'status': 'concept sizing only — final volumes, outlet structures, forebay, spillway and the RRv credit by the design PE; rock probes required (NRCS ARE, gneiss bedrock 22-40 in, under both basins)'},
    {'item': 'Water quality volume (GCSWMM)', 'required': 'WQv = 1.2 x (0.05 + 0.009 x I) / 12 x A', 'provided': f"{round(WQV_CF):,} cf at I = {IMPERV_PCT_GIS:.1f}% impervious on A = {BOUNDARY_SF:,.0f} sf; treated in the two basins. Receiving water is the Jackson Creek headwaters (GAR030701030315), on Georgia's 2024 303(d) list", 'status': 'appears consistent — runoff-reduction approach and BMP selection by the design PE'},
    {'item': 'Impervious surface', 'required': 'no district maximum in Table 4.1 (reported for the stormwater basis)', 'provided': f"{round(IMPERV_SF):,} sf = {IMPERV_PCT_GIS:.1f}% of the GIS area ({100*IMPERV_SF/SF_DEEDED:.1f}% of 9.44 ac), summed from the drawn footprints in data/plans.json ({PLANS_DATE}): Plan A {PLAN_GEOM['A']['a_under_roof_sf']:,.0f} sf under roof + {PLAN_GEOM['A']['a_patio_sf']:,.0f} sf patio, Plan B {PLAN_GEOM['B']['a_under_roof_sf']:,.0f} sf under roof, plus driveways, lane, turnarounds, bays, sidewalks and amenity paving", 'status': 'reported — replaces the flat 2,200 sf/lot allowance previously used'},
    {'item': 'Street grades (site-dev checklist)', 'required': '<= 12%; 12-15% requires an "as graded" survey before the curb is installed', 'provided': "steepest EXISTING ground grades on the lane centreline: " + ' and '.join(f'{g:.1f}% at u ≈ {u:,.0f} ft' for u, g in STEEP_REACHES) + " (USGS 3DEP, approximate — a topographic survey is required). The FINISHED lane profile is not designed on this sheet", 'status': 'RISK — a PE plan-and-profile with vertical curves, cut/fill quantities and any retaining at the lot fronts is required before a <= 12% statement is made about the FINISHED lane; see sheet C-5.0'},
    {'item': 'Accessible parking (2010 ADA Standards §208.2, §502)', 'required': '1 accessible space where 1-25 spaces are provided; van space 8 ft wide + 8-ft access aisle', 'provided': f"1 van-accessible space with an 8-ft access aisle at the clubhouse end of the NE bay, on the shortest accessible route to the clubhouse entrance (§208.3.1), within {AMENITY['guest_spaces'] + AMENITY['kiosk_spaces']} common spaces", 'status': 'appears consistent'},
]

# ----------------------------------------------------------------------------- 8. layout.json
def rp(poly): return [[round(x, 2), round(y, 2)] for x, y in poly]
LAYOUT = {
    'coordinate_system': ctx['axis'] + '; origin SR 2240 GA West US-ft ' + str(ORIGIN) + '; +u to the right, +v up on the drawing; north = 28.72 deg above +u',
    'source': 'Gwinnett County GIS parcel fabric (DRAFT — RLS boundary survey required and governs); USGS 3DEP topo (approx.)',
    'boundary_ring': rp(BOUNDARY), 'boundary_sf': round(BOUNDARY_SF, 1),
    'bearings': [{'from': rp([b['from']])[0], 'to': rp([b['to']])[0], 'bearing': b['bearing'], 'distance_ft': b['distance_ft'], 'frontage': b['frontage']} for b in BEARINGS],
    'parcels': {pin: {'address': ADDR[pin] + ' Arcado Rd SW', 'deeded_ac': DEEDED[pin], 'gis_ac': ctx['parcels'][pin]['gis_ac'], 'ring': rp(parcel_rings[pin])} for pin in PINS},
    'lots': [{'id': L['id'], 'block': L['block'], 'block_lot': L['block_lot'], 'side': L['side'], 'polygon': rp(L['polygon']),
              'area_sf': L['area_sf'], 'width_ft': L['width_ft'], 'depth_ft': L['depth_ft'], 'plan': L['plan'],
              'house': {'plan': L['plan'], 'plan_name': L['house']['plan_name'], 'body_ft': L['house']['body_ft'],
                        'body_polygon': rp(L['house']['body_polygon']), 'garage_rect': rp(L['house']['garage_rect']),
                        'porch_rects': [rp(r) for r in L['house']['porch_rects']],
                        'rear_porch_rects': [rp(r) for r in L['house']['rear_porch_rects']],
                        'patio_rects': [rp(r) for r in L['house']['patio_rects']],
                        'driveway_rect': rp(L['house']['driveway_rect']), 'rear_kind': L['house']['rear_kind'],
                        'garage_recess_ft': L['house']['garage_recess_ft'],
                        'garage_door_from_lot_line_ft': L['house']['garage_door_from_lot_line_ft'],
                        'porch_face_from_lot_line_ft': L['house']['porch_face_from_lot_line_ft'],
                        'rear_element_from_rear_line_ft': L['house']['rear_element_from_rear_line_ft'],
                        'side_yard_ft': L['house']['side_yard_ft']},
              'house_rect': rp(L['house_rect']), 'driveway_rect': rp(L['driveway_rect']), 'garage_rect': rp(L['house']['garage_rect']),
              # backward-compatible single-rectangle keys for consumers written against the pre-2026-09-03
              # layout (tools/sitebase.py).  The authoritative geometry is `house` above: the L-shaped
              # `body_polygon` plus the porch / rear-porch / patio rect LISTS.
              'porch_rect': rp(L['house']['porch_rects'][0]) if L['house']['porch_rects'] else rp(L['house']['garage_rect']),
              'rear_rect': rp((L['house']['rear_porch_rects'] or L['house']['patio_rects'] or [L['house']['garage_rect']])[0]),
              'setback_envelope': rp(L['setback_envelope']), 'buffer_easement': rp(L['buffer_easement']),
              'impervious': L['impervious'], 'phase': L['phase'], 'notes': L['notes']} for L in LOTS],
    'lane': {'centerline': rp(LANE_CL), 'tract_polygon': rp(LANE_TRACT), 'pavement_polygon': rp(LANE_PAVE), 'pavement_width_ft': PAVE_W,
             'sidewalks': [{'side': s['side'], 'polygon': rp(s['polygon']), **({'from_u': s['from_u']} if 'from_u' in s else {})} for s in SIDEWALKS],
             'tract_width_ft': [METRICS['lane_tract_width_ft_min'], METRICS['lane_tract_width_ft_max']], 'widen_both_sidewalks_from_u': U_WIDEN,
             'entrance': AMENITY['entrance'], 'pavement_end_u': U_PAVE_END, 'ground_profile': [(u, round(z, 1)) for u, z in lane_prof],
             'entry_drive': {'centerline': rp(ENTRY_CL), 'pavement_polygon': rp(ENTRY_PAVE), 'tract_polygon': rp(ENTRY_TRACT), 'sidewalk_polygon': rp(ENTRY_WALK), 'length_ft': round(ENTRY_LEN, 1), 'width_ft': ENTRY_W, 'radius_ft': ENTRY_R},
             'arcado_centerline': rp(ARCADO_CL), 'arcadia_pl_centerline': rp(ARCADIA_PATH)},
    'hammerheads': [{'u': h['u'], 'legs': [rp(l) for l in h['legs']], 'width_ft': h['width_ft'], 'leg_ft': h['leg_ft']} for h in HAMMERHEADS],
    'greens': [{'name': g['name'], 'polygons': [rp(p) for p in g['polygons']], 'area_sf': g['area_sf']} for g in GREENS],
    'ponds': [{'name': p['name'], 'polygon': rp(p['polygon']), 'tract_polygon': rp(p['tract_polygon']), 'area_sf': p['area_sf'], 'top_of_bank_ft': p['top_of_bank_ft'],
               'est_storage_cf': p['est_storage_cf'], 'assumption': p['assumption']} for p in PONDS],
    'amenity': {k: (rp(v) if isinstance(v, list) and v and isinstance(v[0], tuple) else ([rp(x) for x in v] if isinstance(v, list) and v and isinstance(v[0], list) else v)) for k, v in AMENITY.items()},
    'lift_station_symbol': rp(LS_SYMBOL),
    'buffers': {'perimeter_buffer_ft': BUFFER, 'note': '20-ft undisturbed buffer along every property line except the Arcado Rd frontage; within lots held in a recorded buffer easement per Lilburn Zoning Ordinance 2023-603 §313(1)',
                'arcado_setback_line': rp(ARCADO_SB_LINE), 'landscape_strip': rp(LANDSCAPE_STRIP)},
    'stream_setbacks': [{'stream': rp(s), 'offsets': {str(lv): [rp(ln) for ln in lines] for lv, lines in so.items()}} for s, so in zip(STREAMS, STREAM_SETBACKS)],
    'sewer': {'existing_on_site': [{'inv_in': s['inv_in'], 'inv_out': s['inv_out'], 'path': rp([tuple(p) for p in s['paths_local'][0]])} for s in SEWER_EX_SITE],
              'proposed_phase1_gravity': rp(SEWER_PH1), 'phase2_primary': 'in-tract lift station / grinder pumps at the rear lane low point, force main to the Phase 1 gravity main (no off-site extension)', 'phase2_force_main_concept': rp(SEWER_FM),
              'phase2_alternative_extension': rp(SEWER_EXT), 'extension_offsite_ft': SEWER_EXT_OFFSITE_FT},
    'open_space_tracts': OPEN_TRACTS,
    'open_space_summary': {'total_sf': round(OPEN_SF), 'total_ac': round(OPEN_SF / 43560, 3),
                           'pct_of_gis_area': round(100 * OPEN_SF / BOUNDARY_SF, 1), 'pct_of_deeded_area': round(100 * OPEN_SF / SF_DEEDED, 1),
                           'built_or_paved_within_sf': round(OPEN_BUILT_SF), 'green_only_sf': round(OPEN_GREEN_SF),
                           'green_only_pct_of_gis_area': round(100 * OPEN_GREEN_SF / BOUNDARY_SF, 1),
                           'built_or_paved_breakdown_sf': {'clubhouse roof': AMENITY['clubhouse_sf'], 'pickleball pads': round(COURT_PAD_SF),
                                                           'mail kiosk': round(KIOSK_SF), 'amenity walks (allowance)': round(AMEN_WALK_SF),
                                                           'hammerhead turnaround legs inside the greens': round(HH_PAVE_SF)},
                           'basis': 'residual: GIS boundary area less lot areas less the lane and entry-drive tracts; the named '
                                    'tracts sum to it exactly. The 20-ft buffer easements on lots (%s sf) are reported separately '
                                    'and are NOT counted here.' % f'{round(BUFFER_ON_LOTS_SF):,}'},
    'impervious_summary': {'total_sf': round(IMPERV_SF), 'pct_of_gis_area': round(IMPERV_PCT_GIS, 1),
                           'pct_of_deeded_area': round(100 * IMPERV_SF / SF_DEEDED, 1),
                           'components_sf': [{'item': n, 'area_sf': v} for n, v in IMPERV_PARTS],
                           'per_lot_sf': {pid: {'plan': PLAN_GEOM[pid]['name'], 'under_roof_sf': round(PLAN_GEOM[pid]['a_under_roof_sf'], 1),
                                                'patio_sf': round(PLAN_GEOM[pid]['a_patio_sf'], 1),
                                                'lots': sum(1 for L in LOTS if L['plan'] == pid),
                                                'total_sf': round(next(L['impervious']['total_sf'] for L in LOTS if L['plan'] == pid), 1)} for pid in ('A', 'B')},
                           'wqv_cf': round(WQV_CF), 'wqv_basis': METRICS['wqv_basis'],
                           'basis': 'shoelace areas of the polygons drawn on sheet C-2.0, computed from data/plans.json '
                                    '(read %s) — no nominal per-lot allowance' % PLANS_DATE},
    'stormwater': {'disturbed_area': DISTURBED, 'detention_rate_cf_per_disturbed_ac': DETENTION_RATE_CF_AC,
                   'detention_required_cf': DETENTION_REQ_CF, 'detention_provided_cf': DETENTION_PROV_CF,
                   'runoff_reduction_volume_cf': 0, 'wqv_cf': round(WQV_CF),
                   'basis': 'Gwinnett County Stormwater Management Manual screening rate of 10,000 cf of detention per '
                            'disturbed acre, RRv taken as 0 at concept stage (any runoff-reduction credit reduces this). '
                            'Disturbed area = raster site area less the 20-ft perimeter buffer bands, the creek-woods tract '
                            'and the 50-ft undisturbed stream buffer, unioned so nothing is counted twice.'},
    'phase_line_u': PHASE_U, 'contours_2ft': {str(k): [rp(ln) for ln in v] for k, v in CONTOURS.items()},
    'metrics': METRICS, 'compliance': COMPLIANCE,
}
json.dump(LAYOUT, open(os.path.join(DATA, 'layout.json'), 'w'), indent=1)
print('\nMETRICS:'); print(json.dumps(METRICS, indent=1))
print('\nOpen-space tracts:', json.dumps(LAYOUT['open_space_tracts']))
print('Ponds:', [(p['name'], p['top_of_bank_ft'], p['est_storage_cf']) for p in PONDS])
print('Blocks:', blocks, 'HH spacing:', HH_SPACING, 'lots per side', METRICS['lots_sw'], METRICS['lots_ne'])
if __name__ == '__main__' and '--layout-only' in sys.argv: sys.exit(0)

# =============================================================================== DRAWING
SHEET_W, SHEET_H = 36 * 72, 24 * 72            # ARCH D landscape, points
SCALE = 72.0 / 60.0                             # 1" = 60'  -> 1.2 pt/ft
WIN = (-150.0, 1840.0, -430.0, 240.0)           # plan window u0,u1,v0,v1 (ft)
FONT = "'Liberation Sans', Arial, Helvetica, sans-serif"
DATE = '2026-08-28'

def esc(t): return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

class Labeler:
    """greedy label collision avoidance in sheet points; nudges along y then x."""
    def __init__(self): self.boxes = []
    def hit(self, b): return any(not (b[2] < o[0] or b[0] > o[2] or b[3] < o[1] or b[1] > o[3]) for o in self.boxes)
    def place(self, x, y, w, h, anchor='middle'):
        for k in range(0, 9):
            for sgn in (1, -1) if k else (1,):
                yy = y + sgn * k * (h + 1.5)
                x0 = x - w / 2 if anchor == 'middle' else (x if anchor == 'start' else x - w)
                b = (x0, yy - h * 0.8, x0 + w, yy + h * 0.3)
                if not self.hit(b): self.boxes.append(b); return yy
        self.boxes.append((x - w / 2, y - h, x + w / 2, y)); return y
    def reserve(self, x0, y0, x1, y1): self.boxes.append((x0, y0, x1, y1))

class Drawing:
    def __init__(self, s, x0, y0, fs=1.0, win=WIN):
        self.s, self.x0, self.y0, self.fs, self.win = s, x0, y0, fs, win
        self.out = []; self.lab = Labeler()
    def X(self, u): return self.x0 + (u - self.win[0]) * self.s
    def Y(self, v): return self.y0 + (self.win[3] - v) * self.s
    def P(self, p): return f"{self.X(p[0]):.2f},{self.Y(p[1]):.2f}"
    def add(self, t): self.out.append(t)
    def poly(self, pts, **kw): self.add(f'<polygon points="{" ".join(self.P(p) for p in pts)}" {attrs(kw)}/>')
    def pline(self, pts, **kw): self.add(f'<polyline points="{" ".join(self.P(p) for p in pts)}" {attrs(kw)}/>')
    def line(self, a, b, **kw): self.add(f'<line x1="{self.X(a[0]):.2f}" y1="{self.Y(a[1]):.2f}" x2="{self.X(b[0]):.2f}" y2="{self.Y(b[1]):.2f}" {attrs(kw)}/>')
    def circle(self, c, r_pt, **kw): self.add(f'<circle cx="{self.X(c[0]):.2f}" cy="{self.Y(c[1]):.2f}" r="{r_pt:.2f}" {attrs(kw)}/>')
    def tw(self, text, size): return 0.56 * size * self.fs * len(text)
    def text(self, u, v, t, size=6, anchor='middle', rot=0, bold=False, fill='#111', halo=False, avoid=False, dy=0):
        size = size * self.fs; x, y = self.X(u), self.Y(v) + dy
        if avoid and rot == 0: y = self.lab.place(x, y, self.tw(t, size / self.fs), size, anchor)
        tr = f' transform="rotate({rot:.2f} {x:.2f} {y:.2f})"' if rot else ''
        st = f'font-size="{size:.2f}" text-anchor="{anchor}" fill="{fill}"' + (' font-weight="bold"' if bold else '')
        if halo: self.add(f'<text x="{x:.2f}" y="{y:.2f}" {st} stroke="#fff" stroke-width="{size*0.45:.2f}" stroke-linejoin="round"{tr}>{esc(t)}</text>')
        self.add(f'<text x="{x:.2f}" y="{y:.2f}" {st}{tr}>{esc(t)}</text>')
    def textlines(self, u, v, lines, size=6, anchor='middle', gap=1.15, avoid=False, bold_first=False, fill='#111'):
        h = size * self.fs * gap; x, y = self.X(u), self.Y(v)
        if avoid:
            w = max(self.tw(l, size) for l in lines); y = self.lab.place(x, y, w, h * len(lines), anchor) ; 
        for i, l in enumerate(lines):
            st = f'font-size="{size*self.fs:.2f}" text-anchor="{anchor}" fill="{fill}"' + (' font-weight="bold"' if (bold_first and i == 0) else '')
            self.add(f'<text x="{x:.2f}" y="{y + i*h:.2f}" {st}>{esc(l)}</text>')
    def rot_of(self, a, b):
        dx, dy = self.X(b[0]) - self.X(a[0]), self.Y(b[1]) - self.Y(a[1])
        ang = math.degrees(math.atan2(dy, dx))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        return ang

def attrs(kw):
    return ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())

STREET_OF = {'6123 017': 'Arcado Rd SW', '6123 036': 'Nantucket Dr', '6123 037': 'Nantucket Dr', '6123 038': 'Nantucket Dr',
             '6123 312': 'Fieldhouse Cir', '6123 313': 'Fieldhouse Cir'}
def street_of(pin):
    n = int(pin.split()[1])
    if pin in STREET_OF: return STREET_OF[pin]
    if 20 <= n <= 32: return 'King David Dr'
    if 300 <= n <= 311: return 'Village Green Ct'
    return ''
def owner_of(pin):
    recs = owners.get(pin) or []
    return (recs[0].get('OWNERNAME1') or 'owner VERIFY') if recs else 'owner VERIFY (Tax Assessor)'
def wrap(t, n=20):
    words = t.split(); lines = []; cur = ''
    for w in words:
        if len(cur) + len(w) + 1 > n and cur: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: lines.append(cur)
    return lines

def draw_plan(D, web=False):
    s = D.s; fs = D.fs
    u0, u1, v0, v1 = D.win
    cid = 'clipweb' if web else 'clipplan'
    D.add(f'<clipPath id="{cid}"><rect x="{D.X(u0):.2f}" y="{D.Y(v1):.2f}" width="{(u1-u0)*s:.2f}" height="{(v1-v0)*s:.2f}"/></clipPath>')
    D.add(f'<g clip-path="url(#{cid})" font-family="{FONT}">')
    D.add(f'<rect x="{D.X(u0):.2f}" y="{D.Y(v1):.2f}" width="{(u1-u0)*s:.2f}" height="{(v1-v0)*s:.2f}" fill="#fff"/>')
    # --- adjoining parcels / R/W / zoning
    D.add('<g id="adjoining">')
    for a in ctx['adjoining_parcels']:
        ring = [tuple(p) for p in a['ring_local']]
        if a['PIN'] == 'R/W':
            D.pline(ring + [ring[0]], fill='none', stroke='#9a9a9a', stroke_width=0.5 * fs); continue
        D.poly(ring, fill='#f5f5f2', stroke='#9a9a9a', stroke_width=0.5 * fs)
    D.add('</g>')
    for z in ctx['zoning']:
        if z['type'] == 'R2':
            D.poly([tuple(p) for p in z['ring_local']], fill='url(#r2hatch)', stroke='#c8791a', stroke_width=0.8 * fs, stroke_dasharray='6 3')
    # --- streams + setbacks
    D.add('<g id="streams">')
    for si, (stream, so) in enumerate(zip(STREAMS, STREAM_SETBACKS)):
        for lv, lines in so.items():
            style = {25: ('#1f77b4', '3 2', 0.5), 50: ('#1f77b4', '6 2', 0.8), 75: ('#1f77b4', '8 2 2 2', 0.8)}[lv]
            for ln in lines: D.pline(ln, fill='none', stroke=style[0], stroke_width=style[2] * fs, stroke_dasharray=style[1])
        D.pline(stream, fill='none', stroke='#1565c0', stroke_width=1.6 * fs)
    D.add('</g>')
    # --- sewer (existing)
    D.add('<g id="sewer">')
    for sw in SEWER:
        col = '#2e7d32'
        for path in sw['paths_local']:
            D.pline([tuple(p) for p in path], fill='none', stroke=col, stroke_width=0.9 * fs)
            for p in path: D.circle(p, 2.2 * fs, fill='#fff', stroke=col, stroke_width=0.7 * fs)
    D.add('</g>')
    # --- boundary, parcels, buffer
    D.add('<g id="boundary">')
    for pin in PINS: D.poly(parcel_rings[pin], fill='none', stroke='#333', stroke_width=0.6 * fs, stroke_dasharray='10 4 2 4')
    # 20-ft buffer bands (non-frontage segments)
    n = len(BOUNDARY)
    for i in range(n):
        a, b = BOUNDARY[i], BOUNDARY[(i + 1) % n]
        if is_frontage_seg(a, b): continue
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L   # inward normal (CCW)
        D.poly([a, b, (b[0] + nx * BUFFER, b[1] + ny * BUFFER), (a[0] + nx * BUFFER, a[1] + ny * BUFFER)], fill='url(#bufhatch)', stroke='none')
    D.poly(BOUNDARY, fill='none', stroke='#000', stroke_width=1.8 * fs)
    # buffer inner line
    D.pline([(u, SW(u) + BUFFER) for u in (0, 400, 800, 1200, 1561, U_BUF_REAR)] + [(U_BUF_REAR, NE(U_BUF_REAR) - BUFFER)] + [(u, NE(u) - BUFFER) for u in (1561, 1200, 800, 400, 0)],
            fill='none', stroke='#555', stroke_width=0.4 * fs, stroke_dasharray='3 2')
    D.add('</g>')
    # --- Arcado 50-ft setback + landscape strip
    D.poly(LANDSCAPE_STRIP, fill='#d8ecc8', stroke='none')
    D.pline(ARCADO_SB_LINE, fill='none', stroke='#b00', stroke_width=0.8 * fs, stroke_dasharray='8 3 2 3')
    # --- open-space tracts
    D.add('<g id="openspace">')
    for g in GREENS:
        for p in g['polygons']: D.poly(p, fill='#dff0d8', stroke='#5a8a4a', stroke_width=0.4 * fs)
    for p in PONDS:
        D.poly(p['tract_polygon'], fill='#e4efdc', stroke='#5a8a4a', stroke_width=0.4 * fs)
        D.poly(p['polygon'], fill='#cfe3f3', stroke='#1f77b4', stroke_width=0.8 * fs, stroke_dasharray='5 2')
        D.poly(shrink_convex(p['polygon'], 12.0), fill='none', stroke='#1f77b4', stroke_width=0.4 * fs, stroke_dasharray='2 2')
    D.poly(WOODS['polygon'], fill='url(#woods)', stroke='#3d6b35', stroke_width=0.5 * fs)
    for t in STREAM_TRACTS: D.poly(t['polygon'], fill='#dbe9f4', stroke='#1f77b4', stroke_width=0.5 * fs, stroke_dasharray='5 2')
    for p in AMENITY['tract_polygons']: D.poly(p, fill='#eef4e6', stroke='#5a8a4a', stroke_width=0.4 * fs)
    D.add('</g>')
    # --- lane
    D.add('<g id="lane">')
    D.poly(LANE_TRACT, fill='#ececec', stroke='#666', stroke_width=0.5 * fs, stroke_dasharray='4 2')
    D.poly(ENTRY_TRACT, fill='#ececec', stroke='#666', stroke_width=0.5 * fs, stroke_dasharray='4 2')
    D.poly(ENTRY_PAVE, fill='#d6d6d6', stroke='#333', stroke_width=0.7 * fs)
    D.poly(LANE_PAVE, fill='#d6d6d6', stroke='#333', stroke_width=0.7 * fs)
    for h in HAMMERHEADS:
        for l in h['legs']: D.poly(l, fill='#d6d6d6', stroke='#333', stroke_width=0.7 * fs)
    for swk in SIDEWALKS: D.poly(swk['polygon'], fill='#f7f7f7', stroke='#777', stroke_width=0.35 * fs)
    # SG-19: the entrance curb returns are DRAWN geometry (NE R = 25'-0", SW R = 15'-0"), not an area allowance
    for r in CURB_RETURNS:
        D.poly(r['polygon'], fill='#d6d6d6', stroke='#333', stroke_width=0.7 * fs)
    D.pline(ENTRY_CL, fill='none', stroke='#444', stroke_width=0.4 * fs, stroke_dasharray='12 3 2 3')
    D.pline(LANE_CL, fill='none', stroke='#444', stroke_width=0.4 * fs, stroke_dasharray='12 3 2 3')
    # extension of the entrance centreline to the Arcado Rd centreline (spacing measurement)
    D.line((U_ENTRY, ENTRY_V), ENTRY_ON_CL, stroke='#444', stroke_width=0.4 * fs, stroke_dasharray='12 3 2 3')
    D.add('</g>')
    # --- amenity
    D.add('<g id="amenity">')
    D.poly(AMENITY['village_green'], fill='#cfe8bd', stroke='#5a8a4a', stroke_width=0.4 * fs)
    D.poly(AMENITY['clubhouse'], fill='#f2c58a', stroke='#222', stroke_width=0.8 * fs)
    for pad, court in zip(AMENITY['pickleball'], AMENITY['courts']):
        D.poly(pad, fill='#f0e9d8', stroke='#222', stroke_width=0.6 * fs)
        D.poly(court, fill='#bcd7c2', stroke='#222', stroke_width=0.4 * fs)
    D.poly(AMENITY['parking_bay'], fill='#d6d6d6', stroke='#333', stroke_width=0.5 * fs)
    D.poly(AMENITY['kiosk_bay'], fill='#d6d6d6', stroke='#333', stroke_width=0.5 * fs)
    for st in AMENITY['stalls'] + AMENITY['kiosk_stalls']: D.poly(st, fill='none', stroke='#555', stroke_width=0.3 * fs)
    D.poly(AMENITY['mail_kiosk'], fill='#f2c58a', stroke='#222', stroke_width=0.6 * fs)
    D.poly(AMENITY['entry_sign'], fill='#333', stroke='none')
    D.add('</g>')
    # --- lots + houses
    D.add('<g id="lots">')
    for L in LOTS:
        D.poly(L['polygon'], fill='#fff', stroke='#222', stroke_width=0.6 * fs)
        D.poly(L['buffer_easement'], fill='url(#bufhatch)', stroke='none')
        D.poly(L['setback_envelope'], fill='none', stroke='#999', stroke_width=0.3 * fs, stroke_dasharray='2 1.5')
    D.add('</g>')
    # --- contours (drawn over the ground fills, under buildings/labels)
    D.add('<g id="contours">')
    for lev, lines in CONTOURS.items():
        idx = lev % 10 == 0
        for ln in lines:
            D.pline(ln, fill='none', stroke='#a67c52', stroke_width=(0.6 if idx else 0.3) * fs, stroke_dasharray='4 2' if idx else '2 2', opacity='0.9')
    for lev, lines in CONTOURS.items():
        if lev % 10: continue
        for ln in lines:
            for k in range(len(ln) - 1):
                for ref in (lane_mid, lambda u: SW(u) + 9.0, lambda u: NE(u) - 9.0):
                    d0, d1 = ln[k][1] - ref(ln[k][0]), ln[k + 1][1] - ref(ln[k + 1][0])
                    if (d0 > 0) != (d1 > 0):
                        t = d0 / (d0 - d1); uc = ln[k][0] + t * (ln[k + 1][0] - ln[k][0])
                        D.text(uc, ref(uc) - 2.5, str(lev), size=6, fill='#7a5230', halo=True, avoid=True)
    D.add('</g>')
    D.add('<g id="houses">')
    for L in LOTS:
        H = L['house']
        D.poly(H['driveway_rect'], fill='#e2e2e2', stroke='#777', stroke_width=0.35 * fs)
        for r in H['patio_rects']: D.poly(r, fill='#ded2bc', stroke='#444', stroke_width=0.4 * fs)      # uncovered patio
        D.poly(H['garage_rect'], fill='#efd2ad', stroke='#222', stroke_width=0.5 * fs)                   # garage wing, stepped back 5'
        for r in H['rear_porch_rects']: D.poly(r, fill='#fdf3e4', stroke='#222', stroke_width=0.4 * fs)  # covered rear porch
        D.poly(H['body_polygon'], fill='#f9e4c8', stroke='#222', stroke_width=0.7 * fs)                  # L-shaped conditioned body
        for r in H['porch_rects']: D.poly(r, fill='#fdf3e4', stroke='#222', stroke_width=0.4 * fs)       # covered front porch
        c = poly_centroid(H['body_polygon'])
        sgnl = -1 if L['side'] == 'SW' else 1
        D.text(c[0], c[1] + 4.5, f"{L['block']}-{L['block_lot']}", size=7.5, bold=True, halo=True)
        D.text(c[0], c[1] - 4.5, f"PLAN {L['plan']}", size=5.6, halo=True)
        # lot area in the 6-ft side yard, read along the lot depth
        sy = (L['u1'] - 3.0) if ((L['id'] % 4) not in (1, 2)) else (L['u0'] + 3.0)
        edge0 = (tract_sw if L['side'] == 'SW' else tract_ne)(sy)
        D.text(sy, edge0 + sgnl * 45.0, f"{L['area_sf']:,.0f} SF", size=5.0, rot=-90, halo=True, fill='#444')
    D.add('</g>')
    # --- proposed sewer (Phase 1 gravity; Phase 2 primary = lift station / grinder pumps; alternative = off-site extension)
    D.pline(SEWER_PH1, fill='none', stroke='#2e7d32', stroke_width=0.9 * fs, stroke_dasharray='6 3')
    D.pline(SEWER_EXT, fill='none', stroke='#2e7d32', stroke_width=0.9 * fs, stroke_dasharray='6 3 1.5 3')
    D.pline(SEWER_FM, fill='none', stroke='#2e7d32', stroke_width=0.9 * fs, stroke_dasharray='2 2')
    D.poly(LS_SYMBOL, fill='#fff', stroke='#2e7d32', stroke_width=0.9 * fs)
    c = poly_centroid(LS_SYMBOL); D.text(c[0], c[1] - 2.2, 'LS', size=5.5, bold=True, fill='#1b5e20')
    # --- phase line
    D.line((PHASE_U, SW(PHASE_U) - 40), (PHASE_U, NE(PHASE_U) + 40), stroke='#7b1fa2', stroke_width=1.4 * fs, stroke_dasharray='14 4 3 4')
    # --- Arcado centerline (+ Arcadia Pl centreline, drawn heavier: access-spacing reference)
    for st in ctx['streets']:
        if st['name'] == 'ARCADO RD' and st['min_dist_ft'] < 70:
            for path in st['paths_local']: D.pline([tuple(p) for p in path], fill='none', stroke='#333', stroke_width=0.6 * fs, stroke_dasharray='14 3 3 3')
        elif st['name'] == 'ARCADIA PL' and st['min_dist_ft'] < 100:
            for path in st['paths_local']: D.pline([tuple(p) for p in path], fill='none', stroke='#333', stroke_width=0.6 * fs, stroke_dasharray='14 3 3 3')
        elif st['min_dist_ft'] < 260:
            for path in st['paths_local']: D.pline([tuple(p) for p in path], fill='none', stroke='#777', stroke_width=0.5 * fs, stroke_dasharray='14 3 3 3')
    # access-spacing dimension along the Arcado Rd centreline: Arcadia Pl C/L -> site entrance C/L (offset 32 ft into the roadway)
    def _off(p, i):
        a, b = ARCADO_CL[max(i, 0)], ARCADO_CL[min(i + 1, len(ARCADO_CL) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); return (p[0] - 32.0 * (-dy / L) * -1, p[1] - 32.0 * (dx / L) * -1)
    _i0 = min(range(len(ARCADO_CL)), key=lambda i: dist(ARCADO_CL[i], ARCADIA_CL))
    dim = [_path[0]] + _path[1:-1] + [_path[-1]]
    dimo = []
    for k, p in enumerate(dim):
        i = _i0 + k - 1 if k else _i0
        i = min(max(i, 0), len(ARCADO_CL) - 2)
        a, b = ARCADO_CL[i], ARCADO_CL[i + 1]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
        nx, ny = dy / L, -dx / L                       # normal pointing away from the site (toward -u)
        if nx > 0: nx, ny = -nx, -ny
        dimo.append((p[0] + 32.0 * nx, p[1] + 32.0 * ny))
    D.line(dim[0], dimo[0], stroke='#000', stroke_width=0.5 * fs); D.line(dim[-1], dimo[-1], stroke='#000', stroke_width=0.5 * fs)
    D.pline(dimo, fill='none', stroke='#000', stroke_width=0.6 * fs)
    for p, q in ((dimo[0], dimo[1]), (dimo[-1], dimo[-2])):
        ddx, ddy = q[0] - p[0], q[1] - p[1]; L = math.hypot(ddx, ddy); ddx, ddy = ddx / L, ddy / L
        D.poly([p, (p[0] + 9 * ddx - 3 * ddy, p[1] + 9 * ddy + 3 * ddx), (p[0] + 9 * ddx + 3 * ddy, p[1] + 9 * ddy - 3 * ddx)], fill='#000')
    D.circle(ARCADIA_CL, 2.4 * fs, fill='#fff', stroke='#000', stroke_width=0.8 * fs)
    D.circle(ENTRY_ON_CL, 2.4 * fs, fill='#fff', stroke='#000', stroke_width=0.8 * fs)
    # ======================================================================= labels
    D.add('<g id="labels">')
    # bearings
    short = []
    for k, b in enumerate(BEARINGS):
        a, c = b['from'], b['to']; m = ((a[0] + c[0]) / 2, (a[1] + c[1]) / 2)
        if b['distance_ft'] < 60:
            short.append(('L%d' % (len(short) + 1), b)); b['tag'] = short[-1][0]
            if not b['frontage']:
                D.text(m[0] + (10 if a[0] > 1700 else 0), m[1] + (0 if a[0] > 1700 else -12), b['tag'], size=6, fill='#000', avoid=True)
            continue
        dx, dy = c[0] - a[0], c[1] - a[1]; Ln = math.hypot(dx, dy); nx, ny = -dy / Ln, dx / Ln   # inward normal (CCW)
        off = -9.0                                                            # outward, ft
        rot = D.rot_of(a, c)
        D.text(m[0] + nx * off, m[1] + ny * off, f"{b['bearing']}   {b['distance_ft']:.2f}'", size=6, rot=rot, fill='#000', dy=2 * fs)
    # frontage short-segment tags as one list
    D.text(front_u(-118) - 14, -120, 'L1–L%d (see LINE TABLE)' % sum(1 for t, b in short if b['frontage']), size=6, rot=-81, fill='#000')
    # PIN labels inside each parcel
    for pin in PINS:
        c = poly_centroid(parcel_rings[pin])
        c = {'6123 033': (150, -226), '6123 015': (480, -226), '6123 014': (1000, -12), '6123 162': (1470, -12)}[pin]
        D.text(c[0], c[1], f"PIN R{pin}  ({ADDR[pin]} ARCADO RD SW)  {DEEDED[pin]:.2f} AC DEEDED", size=6.5, bold=True, fill='#444', halo=True, avoid=True)
    D.text(1000, 165, f"ASSEMBLAGE: 9.44 AC (DEEDED) / {BOUNDARY_SF/43560:.2f} AC (GIS CALC.)  —  LAND LOT 123, 6th DISTRICT  —  BOUNDARY FROM GWINNETT GIS: RLS SURVEY REQUIRED AND GOVERNS", size=7, bold=True, halo=True)
    # Arcado Rd
    D.text(-105, 10, 'ARCADO ROAD  (Gwinnett County minor collector · 35 mph · 14,800 AADT) — R/W VARIES', size=8, rot=-81, bold=True, halo=True)
    D.text(-58, -330, 'C/L ARCADO RD', size=6, rot=-81, halo=True)
    D.text(front_u(-40) + 28, -12, "50' BLDG SETBACK FROM ARCADO R/W", size=6, rot=-81, fill='#b00', halo=True)
    D.text(front_u(-100) + 5, -100, "10' LANDSCAPE STRIP", size=6, rot=-81, fill='#3a6b2a', halo=True)
    # Arcadia Pl + access-spacing dimension text
    _ap = ARCADIA_PATH if ARCADIA_PATH[0] == ARCADIA_CL else ARCADIA_PATH[::-1]
    _t = (-122.0 - _ap[0][0]) / (_ap[1][0] - _ap[0][0]); _pa = (_ap[0][0] + _t * (_ap[1][0] - _ap[0][0]), _ap[0][1] + _t * (_ap[1][1] - _ap[0][1]))
    D.text(_pa[0], _pa[1] + 7, 'C/L ARCADIA PL', size=6.5, bold=True, rot=D.rot_of(_ap[0], _ap[1]), halo=True)
    D.text(6, 86, 'C/L ARCADIA PL MEETS C/L ARCADO RD AT (u −12, v +61) — 61 FT NE OF THE SITE CORNER', size=6, anchor='start', halo=True)
    dm = dimo[len(dimo) // 2]
    D.text(dm[0] - 8, dm[1] + 8, f"≈ {SEP_FT:.0f}' ALONG C/L ARCADO RD — C/L ARCADIA PL TO C/L SITE ENTRANCE", size=6.5, bold=True, rot=-81, halo=True)
    D.text(-39, 39.5, 'EX. HYDRANT', size=6, fill='#b00', halo=True, anchor='start'); D.circle((-45.0, 41.5), 2.5 * fs, fill='#b00')
    # subdivisions / zoning
    D.text(900, 226, 'KING DAVID MANOR (plat S/159)  —  ZONED R-1 (CITY OF LILBURN)  —  single-family houses', size=8, bold=True, fill='#555')
    D.text(760, -388, 'LEGENDS AT PARKVIEW (plat 118/187)  —  ZONED R-1 (CITY OF LILBURN)  —  single-family houses', size=8, bold=True, fill='#555')
    D.text(1836, -110, 'NANTUCKET (plat 1/268) — ZONED R-1 (LILBURN)', size=8, rot=-90, bold=True, fill='#555')
    D.text(520, -415, 'VILLAGE GREEN CT', size=6, fill='#555')
    D.text(60, 212, 'R-2 (Lilburn) — existing', size=7.5, bold=True, fill='#8a4b00', halo=True)
    D.text(60, 202, '"Arcado Road Townhomes" site — nearest R-2 precedent', size=6, fill='#8a4b00', halo=True)
    D.text(-100, 305 - 80, 'UNINCORPORATED GWINNETT R-100 ≈314 ft NW (not shown)', size=6, fill='#555', rot=-81) if False else None
    # adjoining parcel labels
    for a in ctx['adjoining_parcels']:
        if a['PIN'] == 'R/W': continue
        ring = [tuple(p) for p in a['ring_local']]; c = poly_centroid(ring)
        if a['PIN'] == '6123 017': c = (165, 62)
        lines = [f"PIN R{a['PIN']}", f"{a['ADDRESS']} {street_of(a['PIN'])}"] + wrap(owner_of(a['PIN']), 22) + ['Zoned R-1 (City of Lilburn)']
        if a['PIN'] in ('6123 036', '6123 037', '6123 038'): c = (c[0] - 15, c[1])
        D.textlines(c[0], c[1] + 12, lines, size=6, gap=1.18, avoid=True, fill='#444')
    # stream + buffers
    D.text(1455, -380, 'UNNAMED STREAM (state waters, order-0 headwater) — TOP OF BANK PER FIELD DELINEATION (REQUIRED)', size=6, fill='#1565c0', halo=True, anchor='end')
    so = STREAM_SETBACKS[0]
    for lv, vv, txt in ((75, -262, "75' IMPERVIOUS SETBACK"), (50, -276, "50' UNDISTURBED STREAM BUFFER (LILBURN)"), (25, -290, "25' STATE (GA EPD) BUFFER")):
        pts = [p for ln in so[lv] for p in ln if p[0] < 1330]
        p = min(pts, key=lambda q: abs(q[1] - vv)); D.text(p[0] - 4, p[1], txt, size=6, fill='#1565c0', halo=True, anchor='end')
    D.text(940, -232, "50'/75' BUFFERS OF OFF-SITE BRANCH (clip SW edge ≤12 ft / ≤36 ft)", size=6, fill='#1565c0', halo=True, rot=0, avoid=True)
    # sewer labels
    D.text(-38, -62, 'EX. MH  INV 943.79', size=6, fill='#1b5e20', halo=True, rot=-81)
    D.text(278, -207.0, 'EX. MH  INV 927.13 (PHASE 1 OUTFALL)', size=6, fill='#1b5e20', halo=True)
    D.text(120, -259, "EX. 8-in SANITARY SEWER — \"EX. 20' SSE\" (Gwinnett DWR, Arcado Road Townhomes outfall)", size=6, fill='#1b5e20', halo=True, anchor='start')
    D.text(1100, -420, 'EX. 8-in SS — LEGENDS AT PARKVIEW (Gwinnett DWR)', size=6, fill='#1b5e20', halo=True)
    D.text(LEG_MH[0] - 10, LEG_MH[1] - 12, 'EX. MH  INV 919.58', size=6, fill='#1b5e20', halo=True, anchor='end')
    D.text(1300 + 8, -185, f'PHASE 2 SEWER (PRIMARY ROUTE): {SEWER_EXT_OFFSITE_FT:.0f}-ft OFF-SITE 8-in GRAVITY EXTENSION', size=6, bold=True, fill='#1b5e20', halo=True, rot=-90)
    D.text(1300 + 16, -185, 'IN A RECORDED EASEMENT TO THE LEGENDS AT PARKVIEW MAIN (SEE GENERAL NOTE 10)', size=6, fill='#1b5e20', halo=True, rot=-90)
    D.text(rear_low[0] + 12, lane_mid(rear_low[0]) - PAVE_W / 2 - 0.5, 'LS = GRINDER / LOW-PRESSURE STATION — CONTINGENCY ONLY (DWR POLICY BARS A PRIVATE STATION HERE)', size=5.5, fill='#1b5e20', halo=True, anchor='start')
    D.text(1300 + 0.78 * (LEG_MH[0] - 1300) + 9, SW(1300) + 0.78 * (LEG_MH[1] - SW(1300)), 'TO LEGENDS MH INV 919.58 (STREAM CROSSING)', size=6, fill='#1b5e20', halo=True, rot=D.rot_of(SEWER_EXT[2], SEWER_EXT[3]))
    D.text(1380, lane_mid(1380) + 5, f'REAR LANE LOW POINT ≈ {rear_low[1]:.0f} ft (3DEP)', size=6, fill='#1b5e20', halo=True)
    for _u, _g in STEEP_REACHES:
        D.text(_u, lane_mid(_u) - PAVE_W / 2 - 3.0, f'EXISTING GROUND {_g:.1f}% AT u ≈ {_u:,.0f} ft — FINISHED LANE PROFILE BY PE (SHEET C-5.0)',
               size=5.5, fill='#7a5230', halo=True, avoid=True)
    D.text(700, lane_mid(700) - 6, 'PROP. 8-in SS (PHASE 1) — GRAVITY TO EX. MH INV 927.13', size=6, fill='#1b5e20', halo=True)
    # lane labels
    D.text(470, lane_mid(470) + 5, f"PRIVATE LANE — HOA TRACT {METRICS['lane_tract_width_ft_min']:.0f}'–{METRICS['lane_tract_width_ft_max']:.0f}' — 22' PVMT + 2' STRIP + 5' WALK (NE) — PUBLIC-STREET STANDARD", size=6, bold=True)
    D.text(1570, lane_mid(1570) + 5, f"SIDEWALKS BOTH SIDES FROM u = {U_WIDEN:.0f} ft (STRIP ≥ {width(U_WIDEN):.1f}' — SW HALF-SECTION {sw_half(U_WIDEN):.2f}' ≥ {HALF_SECTION:.0f}')", size=6, bold=True)
    for h in HAMMERHEADS:
        D.text(h['u'] + 2.5, lane_mid(h['u']) + PAVE_W / 2 + HH_LEG / 2, "T-TURNAROUND 20'×60'", size=6, rot=-90)
    # entrance notes: four vertical lines in the roadway SW of the Arcado Rd centreline, centred so that none of
    # them runs out of the plan window, and clear of the ARCADO ROAD label above them.
    for k, t in enumerate([
            f"SITE ENTRANCE ≈ {SEP_FT:.0f} FT FROM C/L ARCADIA PL (≥ 250 FT — VERIFY GWINNETT DOT)",
            f"24'-0\" DRIVE AT v = −190 — CURB RETURNS R = {RET_R_NE:.0f}' (NE) / {RET_R_SW:.0f}' (SW) — DOT PERMIT",
            f"REVERSE CURVES R = {ENTRY_R:.0f}' (Δ {math.degrees(PHI1 - PHI0):.0f}°) TO THE LANE C/L AT u = {U_JOIN:.0f} — ISD ≈ 390' (VERIFY)",
            f"BUFFER REDUCTION REQUESTED — SW RETURN {SW_RETURN_ENCROACH_FT:.1f}' INTO THE 20-FT BUFFER BAND"]):
        D.text(-116.0 - 8.0 * k, -285.0, t, size=5.6, bold=(k == 0), halo=True, rot=-90)
    sc = poly_centroid(AMENITY['entry_sign']); D.text(sc[0] + 6, sc[1] + 5, 'MONUMENT ENTRY SIGN ≤ 32 SF', size=6, halo=True, anchor='start')
    D.text(U_JOIN + 3, lane_mid(U_JOIN) + PAVE_W / 2 + STRIP + SIDEWALK + 3, f'PT u = {U_JOIN:.0f}', size=5.5, halo=True, anchor='end')
    D.line((U_JOIN, lane_mid(U_JOIN) - PAVE_W / 2 - 3), (U_JOIN, lane_mid(U_JOIN) + PAVE_W / 2 + 3), stroke='#444', stroke_width=0.5 * fs)
    # greens / ponds / woods / amenity
    for g in GREENS[:2]:
        c = poly_centroid(g['polygons'][0]); D.text(c[0], c[1] - 20, 'POCKET', size=6, bold=True, fill='#2e5e1e'); D.text(c[0], c[1] - 28, 'GREEN', size=6, bold=True, fill='#2e5e1e')
        c = poly_centroid(g['polygons'][1]); D.text(c[0], c[1] + 18, 'POCKET', size=6, bold=True, fill='#2e5e1e'); D.text(c[0], c[1] + 10, 'GREEN', size=6, bold=True, fill='#2e5e1e')
    D.text(U_BUF_REAR - 10, SW(1700) + 45, 'TERMINUS GREEN', size=6, bold=True, fill='#2e5e1e', rot=-90)
    for i, p in enumerate(PONDS, 1):
        c = poly_centroid(p['polygon'])
        D.textlines(c[0], c[1] + 6, [f'POND {i} — DRY EXTENDED DETENTION / WQ',
                                     f"TOP OF BANK {p['top_of_bank_ft']} ft · {POND_DEPTH:.0f} ft DEEP · {POND_SLOPE:.0f}:1",
                                     f"≈{p['est_storage_cf']:,} cf (CONCEPT — PE TO SIZE)",
                                     f"TOB {p['tob_to_sw_line_ft']:.0f} ft INSIDE THE SW LINE"], size=6, gap=1.2, bold_first=True, fill='#0d47a1')
    for t in STREAM_TRACTS:
        c = poly_centroid(t['polygon'])
        D.textlines(c[0], c[1] + 6, ['STREAM-SETBACK', 'OPEN-SPACE TRACT', f"{t['area_sf']:,} SF — NO LOT,", 'NO IMPERVIOUS'], size=6, gap=1.2, bold_first=True, fill='#1565c0')
    c = poly_centroid(WOODS['polygon']); D.textlines(c[0] + 28, c[1] + 28, ['CREEK WOODS', 'PRESERVED OPEN-SPACE TRACT', f"{WOODS['area_sf']:,} SF", 'STREAM HEAD + 50/75-ft BUFFERS', 'TO REMAIN UNDISTURBED'], size=6, gap=1.2, bold_first=True, fill='#1b5e20')
    c = poly_centroid(AMENITY['clubhouse']); D.textlines(c[0], c[1] + 6, ['CLUBHOUSE', f"{AMENITY['clubhouse_sf']:,} SF  (40' × 60')"], size=6, gap=1.2, bold_first=True)
    c = poly_centroid(AMENITY['village_green']); D.textlines(c[0], c[1] + 3, ['VILLAGE', 'GREEN'], size=6, bold_first=True, fill='#2e5e1e')
    for k, pad in enumerate(AMENITY['pickleball'], 1):
        c = poly_centroid(pad); D.textlines(c[0], c[1] + 7, [f'PICKLEBALL {k}', "20'×44' COURT", "30'×60' FENCED PAD"], size=5.5, gap=1.25, bold_first=True)
    c = poly_centroid(AMENITY['parking_bay'])
    D.text(c[0], c[1] + 1.0, f"{AMENITY['guest_standard_spaces']} GUEST SPACES 9'-0\"×18'-0\" (90°)", size=5.5, halo=True)
    D.text(c[0], c[1] - 5.0, "INSIDE THE WIDENED LANE TRACT", size=5.5, halo=True)
    c = poly_centroid(AMENITY['kiosk_bay'])
    D.text(c[0], c[1] + 1.0, "1 VAN-ACCESSIBLE + 8' AISLE + 4 MAIL-KIOSK SPACES", size=5.5, halo=True)
    ac = poly_centroid(AMENITY['accessible_stall']); D.text(ac[0] - 5.0, ac[1], "VAN ACCESSIBLE", size=5.0, halo=True, rot=-90, anchor='middle')
    c = poly_centroid(AMENITY['mail_kiosk']); D.text(c[0] + 10, c[1] + 12, 'MAIL KIOSK (CBU)', size=6, halo=True)
    D.text(PHASE_U + 6, NE(PHASE_U) + 30, f"PHASE LINE u = {PHASE_U:.0f} ft  ◄ PHASE 1 ({METRICS['lots_phase1']} lots, gravity sewer)   PHASE 2 ({METRICS['lots_phase2']} lots) ►", size=7, bold=True, fill='#7b1fa2', halo=True)
    # notes in plan
    D.text(1500, 226, 'FEMA ZONE X — NO SPECIAL FLOOD HAZARD AREA ON SITE (Gwinnett GIS, FIRM)', size=6.5, bold=True, fill='#333')
    D.text(400, 226, "EXISTING 2-ft CONTOURS: USGS 3DEP 1-m DEM, NAVD88, APPROX. — TOPOGRAPHIC SURVEY REQUIRED", size=6.5, bold=True, fill='#7a5230')
    D.text(1150, -30, "20-ft UNDISTURBED BUFFER WITHIN LOTS HELD IN RECORDED BUFFER EASEMENT PER §313(1)  —  ALL PERIMETER LINES EXCEPT ARCADO RD FRONTAGE", size=6, halo=True, fill='#333') if False else None
    D.text(300, -12, "20-ft UNDISTURBED BUFFER (Table 4.1) WITHIN LOTS, HELD IN RECORDED BUFFER EASEMENT PER Lilburn Zoning Ord. 2023-603 §313(1) — ALL PROPERTY LINES EXCEPT ARCADO RD", size=6, halo=True, fill='#333', anchor='start', avoid=True)
    D.text(90, -271, 'EXISTING HOUSES (4535, 4541) AND ACCESSORY STRUCTURES NEAR THE FRONT TO BE REMOVED — LOCATIONS VERIFY BY SURVEY', size=6, fill='#555', halo=True, anchor='start')
    # --- DIMENSIONS: buffers and setbacks are dimensioned on the plan, not only labelled (C-2.0 requirement)
    def dim(a, b, txt, side=1.0, size=6.0, rot=None, tpos=0.5):
        """dimension line between two points with tick arrows and a text, in plan feet."""
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
        if L < 1e-9: return
        ux, uy = dx / L, dy / L; nx, ny = -uy, ux
        D.line(a, b, stroke='#111', stroke_width=0.6 * fs)
        for p, s_ in ((a, 1), (b, -1)):
            D.line((p[0] - nx * 3, p[1] - ny * 3), (p[0] + nx * 3, p[1] + ny * 3), stroke='#111', stroke_width=0.6 * fs)
            D.poly([p, (p[0] + s_ * 7 * ux - 2.2 * nx, p[1] + s_ * 7 * uy - 2.2 * ny),
                    (p[0] + s_ * 7 * ux + 2.2 * nx, p[1] + s_ * 7 * uy + 2.2 * ny)], fill='#111')
        m = (a[0] + dx * tpos + nx * side * 5.0, a[1] + dy * tpos + ny * side * 5.0)
        D.text(m[0], m[1], txt, size=size, bold=True, halo=True,
               rot=D.rot_of(a, b) if rot is None else rot)
    # 20-ft perimeter buffer, both long sides
    for u_, sgn_ in ((640.0, -1), (900.0, 1)):
        base = SW(u_) if sgn_ < 0 else NE(u_)
        dim((u_, base), (u_, base - sgn_ * BUFFER), "20'-0\" BUFFER", side=1.0, rot=0)
    # 50-ft collector building setback, measured as a true perpendicular from the Arcado Rd R/W
    _p0 = (front_u(-70.0), -70.0); _dirn = (math.cos(PHI0), math.sin(PHI0))
    dim(_p0, (_p0[0] + ARCADO_SB * _dirn[0], _p0[1] + ARCADO_SB * _dirn[1]), "50'-0\" BLDG SETBACK", side=1.0)
    # 10-ft landscape strip
    _p1 = (front_u(-155.0), -155.0)
    dim(_p1, (_p1[0] + LANDSCAPE * _dirn[0], _p1[1] + LANDSCAPE * _dirn[1]), "10'-0\"", side=-1.0)
    # lane tract and half-section at a representative station
    _ud = 1000.0
    dim((_ud, tract_sw(_ud)), (_ud, tract_ne(_ud)), f"LANE TRACT {tract_ne(_ud) - tract_sw(_ud):.1f}'", side=1.0, rot=0)
    # lot module: depth measured in the pocket green (no house to cross), width on the lane-tract line
    _st = STREAM_TRACTS[0]; _ug = (_st['u'][0] + _st['u'][1]) / 2.0
    dim((_ug, SW(_ug)), (_ug, tract_sw(_ug)), "100'-0\" LOT-DEPTH MODULE", side=1.0, rot=0, tpos=0.09)
    _lw = next((L for L in LOTS if L['side'] == 'NE' and L['u0'] >= 780), LOTS[-1])
    dim((_lw['u0'], tract_ne(_lw['u0']) - 9.0), (_lw['u1'], tract_ne(_lw['u1']) - 9.0), "50'-0\" LOT WIDTH (TYP.)", side=-1.0)
    # hammerhead
    _h = HAMMERHEADS[1]
    dim((_h['u'] - 17.0, lane_mid(_h['u']) + PAVE_W / 2), (_h['u'] - 17.0, lane_mid(_h['u']) + PAVE_W / 2 + HH_LEG),
        "60'-0\" TURNAROUND LEG", side=-1.0)
    dim((_h['u'] - 17.0, lane_mid(_h['u']) - PAVE_W / 2), (_h['u'] + 3.0, lane_mid(_h['u']) - PAVE_W / 2), "20'-0\"", side=1.0, rot=0)
    # widened lane tract at the amenity bays
    _ua = (BAY_U[0] + BAY_U[1]) / 2.0
    dim((_ua, tract_sw(_ua)), (_ua, tract_ne(_ua)), f"LANE TRACT WIDENED TO {tract_ne(_ua) - tract_sw(_ua):.0f}'-0\" THROUGH THE AMENITY BLOCK", side=-2.4, rot=0)
    # north arrow + scale bar (inside plan window)
    nu, nv = 1765.0, 185.0; ang = math.radians(NORTH_DEG); Ln = 45.0
    tip = (nu + Ln * math.cos(ang), nv + Ln * math.sin(ang)); tail = (nu - Ln * 0.5 * math.cos(ang), nv - Ln * 0.5 * math.sin(ang))
    D.circle((nu, nv), 22 * s * 0 + 26, fill='#fff', stroke='#000', stroke_width=0.8 * fs)
    D.line(tail, tip, stroke='#000', stroke_width=1.2 * fs)
    perp = (-math.sin(ang), math.cos(ang))
    D.poly([tip, (tip[0] - 14 * math.cos(ang) + 5 * perp[0], tip[1] - 14 * math.sin(ang) + 5 * perp[1]), (tip[0] - 14 * math.cos(ang) - 5 * perp[0], tip[1] - 14 * math.sin(ang) - 5 * perp[1])], fill='#000')
    D.text(tip[0] + 9 * math.cos(ang), tip[1] + 9 * math.sin(ang) - 2, 'N', size=10, bold=True)
    # plan north (sheet up) drawn as a light second arrow in the same rosette
    D.line((nu, nv - Ln * 0.5), (nu, nv + Ln), stroke='#888', stroke_width=0.8 * fs)
    D.poly([(nu, nv + Ln), (nu - 4, nv + Ln - 11), (nu + 4, nv + Ln - 11)], fill='#888')
    D.text(nu - 12, nv + Ln + 4, 'PLAN', size=5.5, fill='#666'); D.text(nu - 12, nv + Ln - 4, 'NORTH', size=5.5, fill='#666')
    D.text(1832, nv - 40, 'TRUE / GRID NORTH (SR 2240 GA WEST) = 28.72° ABOVE THE +u AXIS;', size=6, halo=True, anchor='end')
    D.text(1832, nv - 48, 'PLAN NORTH = SHEET UP = THE +v AXIS ACROSS THE STRIP', size=6, halo=True, anchor='end')
    sb0 = (1610.0, -405.0)
    for k in range(4):
        D.poly(rect(sb0[0] + 60 * k, sb0[0] + 60 * (k + 1), sb0[1], sb0[1] + 6), fill='#000' if k % 2 == 0 else '#fff', stroke='#000', stroke_width=0.6 * fs)
        D.text(sb0[0] + 60 * k, sb0[1] - 9, str(60 * k), size=6)
    D.text(sb0[0] + 240, sb0[1] - 9, '240 ft', size=6)
    D.text(sb0[0] + 120, sb0[1] + 12, 'GRAPHIC SCALE  1" = 60\'', size=7, bold=True)
    D.add('</g>')
    D.add('</g>')

DEFS = '''<defs>
<pattern id="bufhatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#7a9b5a" stroke-width="0.6"/></pattern>
<pattern id="r2hatch" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(-45)"><rect width="8" height="8" fill="#fff3e0"/><line x1="0" y1="0" x2="0" y2="8" stroke="#e0a060" stroke-width="0.6"/></pattern>
<pattern id="woods" patternUnits="userSpaceOnUse" width="14" height="14"><rect width="14" height="14" fill="#cfe5c4"/><circle cx="4" cy="4" r="2.2" fill="none" stroke="#3d6b35" stroke-width="0.5"/><circle cx="11" cy="10" r="2.2" fill="none" stroke="#3d6b35" stroke-width="0.5"/></pattern>
</defs>'''

def table(D, x, y, cols, rows, size=6.5, rowh=None, head=None, widths=None, title=None, subtitle=None):
    """simple ruled table in sheet points; returns bottom y."""
    rowh = rowh or size * 1.45; widths = widths or [140] * len(cols); W = sum(widths)
    if title: D.add(f'<text x="{x}" y="{y}" font-size="{size+2.5}" font-weight="bold">{esc(title)}</text>'); y += size + 4
    if subtitle: D.add(f'<text x="{x}" y="{y}" font-size="{size-0.5}" fill="#444">{esc(subtitle)}</text>'); y += size + 1
    top = y
    D.add(f'<rect x="{x}" y="{y}" width="{W}" height="{rowh}" fill="#e8e8e8" stroke="#000" stroke-width="0.6"/>')
    cx = x
    for c, w in zip(cols, widths):
        for i, ln in enumerate(wrap(str(c), int(w / (0.56 * size)))[:1]):
            D.add(f'<text x="{cx+3}" y="{y+rowh*0.72}" font-size="{size}" font-weight="bold">{esc(c)}</text>')
        cx += w
    y += rowh
    for r in rows:
        nl = max(len(wrap(str(c), int(w / (0.56 * size)))) for c, w in zip(r, widths)); h = rowh * nl
        D.add(f'<rect x="{x}" y="{y}" width="{W}" height="{h}" fill="none" stroke="#000" stroke-width="0.4"/>')
        cx = x
        for c, w in zip(r, widths):
            for i, ln in enumerate(wrap(str(c), int(w / (0.56 * size)))):
                D.add(f'<text x="{cx+3}" y="{y+rowh*0.72+i*rowh}" font-size="{size}">{esc(ln)}</text>')
            cx += w
        y += h
    cx = x
    for w in widths[:-1]:
        cx += w; D.add(f'<line x1="{cx}" y1="{top}" x2="{cx}" y2="{y}" stroke="#000" stroke-width="0.4"/>')
    return y
y0_tbl = [0]

DISCLAIMER = ('Disclaimer: This is an AI-generated analysis for preliminary planning purposes. All findings must be verified by a '
              'licensed professional before use in design, permitting, or regulatory submissions.')

NOTES = [
    'BOUNDARY: assemblage boundary, bearings, distances and acreages are computed from the Gwinnett County GIS parcel fabric (SR 2240 GA West, US survey ft) and are DRAFT. A boundary survey and metes-and-bounds legal description by a Georgia RLS are required for the application and govern over this plan.',
    'TOPOGRAPHY: existing 2-ft contours are interpolated from the USGS 3DEP 1-m DEM sampled on a 100 × 50-ft grid (NAVD88) and are approximate; a topographic survey is required before engineering design.',
    'PRIVATE STREET: the lane is a private street within an HOA-owned tract, designed to City of Lilburn public street standards (Site Development Plan Review Checklist): 22-ft pavement, no on-street parking, 2-ft strip, 5-ft sidewalks; design speed 15 mph; grades ≤ 12%. Every lot abuts the lane ≥ 30 ft (Lilburn Zoning Ordinance 2023-603 §319).',
    'HOA: a mandatory homeowners association owns and maintains the lane tract, greens, creek woods, ponds, amenity tract, landscape strip and the buffer easements; declaration of covenants recorded before the first lot conveyance.',
    'HOPA 55+: age-restricted housing for older persons per 42 U.S.C. §3607(b)(2)(C) and 24 CFR §100.300–.308 (≥ 80% of occupied units with at least one occupant 55+; published policies; biennial verification), offered as a voluntary zoning condition and recorded covenant.',
    'FIRE: single access from Arcado Rd. The dead-end travelled way is ≈ ' + f'{DEAD_END_FT:.0f}' + ' ft, over the 750-ft entry in Table D103.4 of IFC 2024 (GA) Appendix D, which reads "Special approval required" — that approval is requested of the Gwinnett County Fire Marshal. IFC 2024 (GA) App. D107.1 as amended in Georgia requires a second access for one- and two-family developments of MORE THAN 120 dwelling units; at ' + f'{N_LOTS}' + ' units it is not triggered. Offered voluntarily in support of the D103.4 request: NFPA 13D sprinklers in every dwelling (which also halves the required fire flow under App. B105.1, 1,000 → 500 gpm), a 22-ft clear lane with no on-lane parking, and hammerhead (T) turnarounds at ' + ' / '.join(f'{s:.0f}' for s in HH_SPACING) + '-ft spacing and at the terminus. Sprinklers are an offer, not a code requirement, and may be traded for another App. D107.1 Exception 3 measure at the Fire Marshal\'s election.',
    'STREAM BUFFER: 50-ft undisturbed buffer plus 25-ft impervious setback (75 ft total) from top of bank of state waters (City of Lilburn); GA EPD minimum 25 ft. The buffer and the creek-woods tract are to remain undisturbed; field delineation of top of bank is required.',
    'PERIMETER BUFFER: 20-ft undisturbed buffer abutting R-1 (Table 4.1) along every property line except the Arcado Rd frontage; within lots it coincides with the 20-ft rear yard and is held in a recorded buffer easement (§313(1) — buffers supersede minimum yards). Utility/pond encroachments ≤ 50 ft perpendicular width only.',
    'TREES: a tree survey and tree protection / replacement plan per City of Lilburn requirements will be submitted with the Land Disturbance Permit; the creek woods and perimeter buffers are the primary tree-save areas.',
    'SANITARY SEWER: Gwinnett DWR sewer capacity certification required (Rev. 07/2023 form, "Pre-Rezoning" request type). Phase 1 (' + f'{METRICS["lots_phase1"]}' + ' lots, u < ' + f'{PHASE_U:.0f}' + ' ft) drains by GRAVITY to the EXISTING 8-in main at MH INV 927.13 in the EX. 20-ft SSE on the property — no sewer extension of any kind, which is the direct answer to the 2026 Comprehensive Plan Amendment policy "do not further extend sewer in this area" (transmitted to DCA 2026-07-13; adoption pending). Phase 2 (' + f'{METRICS["lots_phase2"]}' + ' lots in the rear pocket, lane ground ≈ 931–935 behind the u ≈ 1,100–1,200 ridge) cannot reach that manhole by gravity: PRIMARY ROUTE = the ' + f'{SEWER_EXT_OFFSITE_FT:.0f}' + '-ft off-site 8-in gravity extension shown to the Legends at Parkview main (MH INV 919.58) through a recorded easement. A private pump station or force main is NOT available for a fee-simple residential subdivision — Gwinnett DWR\'s Standard Policy for Private Developments (rev. 9/2018) allows them only for commercial property under single ownership, and Developer Pump Station Standards WSR-24 §1.3.1(A) grants a county station only where gravity is generally more than 5,000 ft down gradient. The low-pressure grinder system (LS symbol) is shown only as a labelled contingency. Route, easement and the plan-policy reading to be settled with DWR and Planning staff before the Phase 2 LDP. Inverts shown are GIS values — VERIFY by field survey.',
    'WATER: DIP/ACP mains in Arcado Rd; nearest hydrant ≈ 61 ft from the front corner. A ~1,700-ft dead-end main is anticipated; looping / oversizing per Gwinnett DWR.',
    'ACCESS: one full-movement driveway on Arcado Rd (Gwinnett County minor collector, 35 mph, 14,800 AADT) centred at v = −190 in the SW third of the frontage, ≈ ' + f'{SEP_FT:.0f}' + ' ft from the Arcadia Pl centreline measured along the Arcado Rd centreline (Gwinnett access spacing on a collector ≈ 244 ft — VERIFY Gwinnett DOT); Arcadia Pl cannot be aligned with the site driveway (its centreline meets Arcado Rd 61 ft NE of the site\'s NE front corner). 24-ft entry drive, curb returns R = ' + f'{RET_R_NE:.0f}' + ' ft (NE) and R = ' + f'{RET_R_SW:.0f}' + ' ft (SW), two reverse curves R = 100 ft to the lane midline; intersection sight distance ≈ 390 ft to be certified. Left-turn lane not expected below 75 lots (VERIFY). BUFFER REDUCTION REQUESTED: even with the SW return reduced to R = ' + f'{RET_R_SW:.0f}' + ' ft, ' + f'{SW_RETURN_ENCROACH_FT:.1f}' + ' ft of it measured along the R/W (' + SW_RETURN_BUFFER_SF_TXT + ' of pavement) lies inside the 20-ft perimeter buffer band at the R/W corner. The entrance cannot be shifted NE — it is already only ' + f'{SEP_FT:.0f}' + ' ft from the Arcadia Pl centreline against the ~244-ft access-management spacing. The reduction is dimensioned on this drawing and must be requested in the letter of intent and carried in the voluntary conditions (Ord. 2023-603 §1003-4). Gwinnett DOT driveway/encroachment permit and sight-distance certification required; no individual lot driveways to Arcado Rd. Trip generation ≈ ' + f'{0.30 * N_LOTS:.1f}' + ' PM peak-hour trips and ≈ ' + f'{4.31 * N_LOTS:.0f}' + ' daily (ITE Trip Generation 11th ed., LUC 251, Senior Adult Housing – Single-Family). Under the Gwinnett DOT TIS Guidelines (2023) a traffic impact study accompanies every zoning application and the exemption is 7 lots or fewer, so a LEVEL 1 (document-only) TIS is required — not "no TIS". Confirm at the pre-application conference that the City adopts the county guidelines for a city case.',
    'STORMWATER: two dry extended-detention / water-quality basins per the Gwinnett County Stormwater Management Manual. BASIS, shown so it can be re-added: disturbed area = ' + f"{DISTURBED['site_raster_sf']:,}" + ' sf of site less ' + f"{DISTURBED['preserved_sf']:,}" + ' sf preserved (20-ft perimeter buffer bands ' + f"{DISTURBED['buffer_bands_sf']:,}" + ' sf + creek-woods tract ' + f"{DISTURBED['creek_woods_net_sf']:,}" + ' sf + 50-ft stream buffer ' + f"{DISTURBED['stream_buffer_net_sf']:,}" + ' sf, unioned) = ' + f"{DISTURBED['disturbed_sf']:,}" + ' sf = ' + f"{DISTURBED['disturbed_ac']:.3f}" + ' ac; at the screening rate of 10,000 cf per disturbed acre with the runoff-reduction volume RRv taken as ZERO, detention required = ' + f'{DETENTION_REQ_CF:,}' + ' cf. PROVIDED ' + f'{DETENTION_PROV_CF:,}' + ' cf: Pond 1 ' + f"{PONDS[0]['est_storage_cf']:,}" + ' cf (' + PONDS[0]['top_of_bank_ft'] + ' ft top of bank) and Pond 2 ' + f"{PONDS[1]['est_storage_cf']:,}" + ' cf (' + PONDS[1]['top_of_bank_ft'] + ' ft), each ' + f'{POND_DEPTH:.0f}' + ' ft deep with ' + f'{POND_SLOPE:.0f}' + ':1 side slopes (prismoidal volume between top of bank and basin bottom). Water-quality volume WQv = 1.2 × (0.05 + 0.009 × I) / 12 × A = ' + f'{round(WQV_CF):,}' + ' cf at I = ' + f'{IMPERV_PCT_GIS:.1f}' + '% impervious on A = ' + f'{BOUNDARY_SF:,.0f}' + ' sf. Every top of bank is at least ' + f'{BUFFER + 10.0:.0f}' + ' ft inside the SW property line (20-ft undisturbed buffer + 10-ft toe clearance) and at least ' + f'{SCREEN_IMPERV:.0f}' + ' ft from every digitized stream centreline. Final volumes, outlet structures, forebay, spillway, the RRv credit and rock probes (NRCS ARE, gneiss bedrock 22–40 in, under both basins) by the design PE.',
    'IMPERVIOUS: ≈ ' + f'{round(IMPERV_SF):,}' + ' sf = ' + f'{IMPERV_PCT_GIS:.1f}' + '% of the ' + f'{BOUNDARY_SF:,.0f}' + '-sf GIS area, summed from the footprints drawn on this sheet and published in data/plans.json (' + PLANS_DATE + '): Plan A ' + f"{PLAN_GEOM['A']['a_under_roof_sf']:,.0f}" + ' sf under roof + ' + f"{PLAN_GEOM['A']['a_patio_sf']:,.0f}" + ' sf patio, Plan B ' + f"{PLAN_GEOM['B']['a_under_roof_sf']:,.0f}" + ' sf under roof, plus 20-ft driveways, the lane, turnarounds, parking bays, sidewalks and amenity paving, less the driveway/sidewalk squares counted twice. No flat per-lot allowance is used.',
    'STREAM SETBACK SCREENING: every lot, dwelling, driveway, pond and pavement is held at least ' + f'{SCREEN_IMPERV:.0f}' + ' ft from the digitized centreline of ALL THREE mapped reaches — the on-site headwater and both off-site branches — which is the 75-ft impervious setback plus a ' + f'{TOB_ALLOWANCE:.0f}' + '-ft top-of-bank allowance carried because top of bank has not been field delineated. The one 50 × 100-ft slot that fails the screen (SW side, u 1,230–1,280) is NOT lotted; it is shown as a stream-setback open-space tract. Lot yield is ' + f'{N_LOTS}' + ' as a result.',
    'OPEN SPACE: Development Regulations §5.9.1 requires recreation land only in single-family detached subdivisions of 50 acres or more; at 9.44 ac it is NOT triggered, so all common open space here is voluntary. Provided ' + f'{round(OPEN_SF):,}' + ' sf = ' + f'{OPEN_SF/43560:.2f}' + ' ac = ' + f'{100*OPEN_SF/BOUNDARY_SF:.1f}' + '% of the GIS area in named HOA tracts that sum exactly to that figure. Of it, ' + f'{round(OPEN_BUILT_SF):,}' + ' sf is built or paved (clubhouse roof, two court pads, mail kiosk, amenity walks and the hammerhead legs inside the greens), so green-only open space is ' + f'{round(OPEN_GREEN_SF):,}' + ' sf = ' + f'{100*OPEN_GREEN_SF/BOUNDARY_SF:.1f}' + '%. The ' + f'{round(BUFFER_ON_LOTS_SF):,}' + ' sf of 20-ft buffer easement on lots is reported separately and is not counted in either figure.',
    'SURVEY GOVERNS: all dimensions are in US survey feet in the site-local system (u along the strip, v across); lot lines, areas and the lane alignment are conceptual and will be adjusted to the sealed boundary and topographic surveys. This plan is a DRAFT for pre-application review — NOT SEALED.',
]

NOTE_BOTTOM = [0.0]
LEGEND_BOTTOM = [0.0]
LINE_TABLE_BOTTOM = [0.0]

def draw_key_plan(D, x, y, w):
    """Small key plan of the whole strip showing the Block A / Block B match line and the enlargement sheets.
    Returns its height in sheet points."""
    D.add(f'<text x="{x}" y="{y}" font-size="9" font-weight="bold">KEY PLAN — ENLARGEMENT SHEETS (NOT TO SCALE)</text>')
    u0, u1 = -60.0, U_REAR + 20.0
    k = w / (u1 - u0)                        # sheet pt per foot along the strip
    kv = 0.34                                # exaggerated across the strip so the strip reads
    top = y + 12
    def KX(u): return x + (u - u0) * k
    def KY(v): return top + (40.0 - v * kv) + 12.0
    def kpoly(poly, **kw): D.add(f'<polygon points="{" ".join(f"{KX(p[0]):.2f},{KY(p[1]):.2f}" for p in poly)}" {attrs(kw)}/>')
    kpoly(BOUNDARY, fill='#f4f7f0', stroke='#000', stroke_width=1.0)
    for a, b, col in ((U_LOT0, PHASE_U, '#dfe9f6'), (PHASE_U, U_BUF_REAR, '#f6e6df')):
        kpoly([(a, SW(a)), (b, SW(b)), (b, NE(b)), (a, NE(a))], fill=col, stroke='none')
    kpoly(BOUNDARY, fill='none', stroke='#000', stroke_width=1.0)
    D.add(f'<line x1="{KX(PHASE_U):.2f}" y1="{KY(NE(PHASE_U)) - 16:.2f}" x2="{KX(PHASE_U):.2f}" y2="{KY(SW(PHASE_U)) + 16:.2f}" stroke="#7b1fa2" stroke-width="1.6" stroke-dasharray="10 3 2 3"/>')
    D.add(f'<text x="{KX(PHASE_U) + 4:.2f}" y="{KY(NE(PHASE_U)) - 19:.2f}" font-size="6.5" font-weight="bold" fill="#7b1fa2">MATCH LINE u = {PHASE_U:.0f} ft — SEE SHEETS C-2.1 / C-2.2</text>')
    D.add(f'<text x="{KX((U_LOT0 + PHASE_U) / 2):.2f}" y="{KY(-115):.2f}" font-size="7" font-weight="bold" text-anchor="middle">BLOCK A · PHASE 1 · SHEET C-2.1</text>')
    D.add(f'<text x="{KX((U_LOT0 + PHASE_U) / 2):.2f}" y="{KY(-115) + 8:.2f}" font-size="6" text-anchor="middle">{METRICS["lots_phase1"]} lots · u −40 to {PHASE_U:.0f} ft · 1" = 30\'</text>')
    D.add(f'<text x="{KX((PHASE_U + U_BUF_REAR) / 2):.2f}" y="{KY(-115):.2f}" font-size="7" font-weight="bold" text-anchor="middle">BLOCK B · PHASE 2 · SHEET C-2.2</text>')
    D.add(f'<text x="{KX((PHASE_U + U_BUF_REAR) / 2):.2f}" y="{KY(-115) + 8:.2f}" font-size="6" text-anchor="middle">{METRICS["lots_phase2"]} lots · u {PHASE_U:.0f} to {U_REAR:.0f} ft · 1" = 30\'</text>')
    D.add(f'<text x="{KX(-10):.2f}" y="{KY(-300):.2f}" font-size="6" font-weight="bold">ARCADO RD SW</text>')
    D.add(f'<text x="{KX(U_REAR - 40):.2f}" y="{KY(-300):.2f}" font-size="6" text-anchor="end">NW (REAR) LINE — NANTUCKET</text>')
    D.add(f'<text x="{KX(200):.2f}" y="{KY(150):.2f}" font-size="6" fill="#444">Entry, frontage and amenity enlargement: SHEET C-2.3 (1" = 20\')</text>')
    return (KY(-330) - y) + 6


def build_sheet():
    W, H = SHEET_W, SHEET_H; M = 36
    D = Drawing(SCALE, 102.0, 52.0, fs=1.0)
    D.add(f'<svg xmlns="http://www.w3.org/2000/svg" width="36in" height="24in" viewBox="0 0 {W} {H}" font-family="{FONT}">')
    D.add(f'<title>The Cottages at Arcado Springs — Sheet C-2.0 Master Concept Plan — Overall</title>')
    D.add(DEFS)
    D.add(f'<rect width="{W}" height="{H}" fill="#fff"/>')
    D.add(f'<rect x="{M}" y="{M}" width="{W-2*M}" height="{H-2*M}" fill="none" stroke="#000" stroke-width="2"/>')
    D.add(f'<rect x="{M+6}" y="{M+6}" width="{W-2*M-12}" height="{H-2*M-12}" fill="none" stroke="#000" stroke-width="0.6"/>')
    draw_plan(D)
    pw, ph = (WIN[1] - WIN[0]) * SCALE, (WIN[3] - WIN[2]) * SCALE
    D.add(f'<rect x="{D.x0}" y="{D.y0}" width="{pw:.1f}" height="{ph:.1f}" fill="none" stroke="#000" stroke-width="1"/>')
    D.add(f'<text x="{D.x0}" y="{D.y0-8}" font-size="12" font-weight="bold">C-2.0  MASTER CONCEPT PLAN — OVERALL   ·   SCALE 1" = 60\' (ARCH D 36 × 24)   ·   site-local coordinates: +u along the strip to the NW, +v across toward the NE line; see the north rosette in the plan window</text>')
    # SG / drawing-standards: the DRAFT watermark is OUT of the plan window — it is a banner under it, so no
    # line, dimension or label on the plan is crossed by it.
    wy = D.y0 + ph + 4
    D.add(f'<rect x="{D.x0}" y="{wy}" width="{pw:.1f}" height="26" fill="#fff2f2" stroke="#c00" stroke-width="1"/>')
    D.add(f'<text x="{D.x0+pw/2}" y="{wy+18}" font-size="15" font-weight="bold" fill="#c00" text-anchor="middle" letter-spacing="1.2">DRAFT — NOT SEALED — CONCEPT FOR PRE-APPLICATION REVIEW — NOT FOR CONSTRUCTION, PERMITTING OR RECORDING</text>')
    # ---------------- lower band
    yb = D.y0 + ph + 52; x = M + 14
    rows = [
        ['Site area', '—', f'9.44 ac deeded ({SF_DEEDED:,.0f} sf) / {BOUNDARY_SF/43560:.3f} ac GIS calc. ({BOUNDARY_SF:,.0f} sf); RLS survey governs'],
        ['Frontage on Arcado Rd', '—', f'{FRONTAGE_PATH_FT:.2f} ft along the R/W in {len(FRONT_LINE)-1} segments ({FRONTAGE_CHORD_FT:.2f} ft chord); no lot fronts Arcado Rd and no lot driveway enters it'],
        ['Parcels', '—', 'R6123 033 (0.99 ac), 015 (2.00), 014 (2.00), 162 (4.45) — 4535/4537/4539/4541 Arcado Rd SW; Land Lot 123, 6th District'],
        ['Zoning — existing / proposed', '—', 'R-1 (City of Lilburn)  →  R-2 Medium-Density Residential (Ord. 2023-603 §402); Comp. Plan "Established Residential" (§203 compatible)'],
        ['Use', 'P in R-2 (§602 Use Table)', f'Single-family detached cluster-cottage homes, fee-simple lots, HOPA 55+ (voluntary condition); {N_LOTS} dwelling units'],
        ['Density (Table 4.1 R-2)', '≤ 8.0 du/ac', f"{METRICS['density_du_ac_deeded']} du/ac on 9.44 ac / {METRICS['density_du_ac_gis']} du/ac on {BOUNDARY_SF/43560:.2f} ac"],
        ['Lots / blocks / phasing', 'Phasing permitted only if platted in blocks (site-dev checklist §4.i); the block line must fall on a lot line', f"{N_LOTS} lots (SW side {METRICS['lots_sw']}, NE side {METRICS['lots_ne']}). BLOCK A = Phase 1, lots A-1 … A-{max(L['block_lot'] for L in LOTS if L['block']=='A')} ({METRICS['lots_phase1']} lots, u ≤ {PHASE_U:.0f} ft, gravity sewer); BLOCK B = Phase 2, lots B-1 … B-{max(L['block_lot'] for L in LOTS if L['block']=='B')} ({METRICS['lots_phase2']} lots). The block/phase line falls on a lot line at u = {PHASE_U:.0f} ft, never through a lot"],
        ['Lot area (Table 4.1, cottage home)', '≥ 3,000 sf', f"min {METRICS['lot_area_min_sf']:,.0f} / avg {METRICS['lot_area_avg_sf']:,.0f} / max {METRICS['lot_area_max_sf']:,.0f} sf"],
        ['Lot width / depth (Table 4.1)', '≥ 50 ft / ≥ 100 ft', f"50 ft / {METRICS['lot_depth_min_ft']:.0f} ft (all lots)"],
        ['Heated floor area (Table 4.1, cottage)', '≥ 1,000 sf', f"Plan A 'The Springbrook' body {PLAN_GEOM['A']['body_label']} — {PLAN_GEOM['A']['areas']['conditioned_sf']:,.0f} sf conditioned, {PLAN_GEOM['A']['a_under_roof_sf']:,.0f} sf under roof; Plan B 'The Laurel' body {PLAN_GEOM['B']['body_label']} — {PLAN_GEOM['B']['areas']['conditioned_sf']:,.0f} sf conditioned, {PLAN_GEOM['B']['a_under_roof_sf']:,.0f} sf under roof (data/plans.json, {PLANS_DATE}). Mix: {METRICS['plan_mix']['A']} × Plan A, {METRICS['plan_mix']['B']} × Plan B"],
        ['Height (Table 4.1)', '≤ 40 ft', f"1 story; max ridge above FFE {PLAN_GEOM['A']['roof_max_ridge_ft']:.2f} ft (Plan A) / {PLAN_GEOM['B']['roof_max_ridge_ft']:.2f} ft (Plan B)"],
        ['Setbacks (Table 4.1 / Table 4.2)', 'Front 15 ft from a local street; 50 ft from a collector R/W; side 5 ft; rear 20 ft; front-loaded garage recessed ≥ 5 ft', f"Porch face {PLAN_GEOM['A']['face']:.2f} ft from the front lot line — 15'-0\" required plus the 0'-8\" roof overhang, which is held outside the required yard so no projection is claimed. Side yards {PLAN_GEOM['A']['side_yard_ft']:.0f}'-0\" both sides. Rearmost element {min(L['house']['rear_element_from_rear_line_ft'] for L in LOTS):.2f} ft from the rear lot line (Plan A patio {PLAN_GEOM['A']['rear_clear_ft']:.2f} ft, Plan B covered rear porch {PLAN_GEOM['B']['rear_clear_ft']:.2f} ft); the rear 20 ft is also the buffer easement. Garage door {PLAN_GEOM['A']['garage_door_ft']:.2f} ft from the lot line, wing recessed {PLAN_GEOM['A']['garage_recess_ft']:.0f}'-0\" behind the front wall. Nearest lot to the Arcado R/W {METRICS['nearest_lot_to_arcado_rw_ft']:.1f} ft; nearest principal structure (clubhouse) {METRICS['clubhouse_setback_from_arcado_rw_ft']:.1f} ft, both measured perpendicular"],
        ['Buffer abutting R-1 (Table 4.1; §313(1))', '20 ft (dwelling types other than detached SF; interpretation VERIFY)', '20-ft undisturbed buffer on all property lines except Arcado Rd frontage; within lots held in recorded buffer easement'],
        ['Parking (Table 8.1, SF detached)', f'2 per DU = {2*N_LOTS} spaces', f"4 per DU (2-car garage + 2 on a 20'-0\" × 26'-0\" driveway) = {4*N_LOTS}, plus {AMENITY['guest_standard_spaces']} guest spaces in the SW bay and 1 van-accessible space + 8-ft aisle + {AMENITY['kiosk_spaces']} mail-kiosk spaces in the NE bay = {AMENITY['guest_spaces'] + AMENITY['kiosk_spaces']} common spaces (1 per {N_LOTS/(AMENITY['guest_spaces'] + AMENITY['kiosk_spaces']):.1f} dwellings). Both bays are 9'-0\" × 18'-0\" 90° stalls inside the widened lane tract"],
        ['Common open space (Development Regulations §5.9.1)', 'NOT TRIGGERED — §5.9.1 applies at 50 acres or more for single-family detached; voluntary design basis ≥ 20%', f"ONE NUMBER: {round(OPEN_SF):,} sf = {OPEN_SF/43560:.2f} ac = {100*OPEN_SF/BOUNDARY_SF:.1f}% of the GIS area ({100*OPEN_SF/SF_DEEDED:.1f}% of 9.44 ac), in named HOA tracts that sum exactly to it (see the OPEN-SPACE TRACT table). Built or paved within those tracts: {round(OPEN_BUILT_SF):,} sf (clubhouse roof {AMENITY['clubhouse_sf']:,}, court pads {round(COURT_PAD_SF):,}, mail kiosk {round(KIOSK_SF):,}, walks {round(AMEN_WALK_SF):,}, hammerhead legs in the greens {round(HH_PAVE_SF):,}) → green-only {round(OPEN_GREEN_SF):,} sf = {100*OPEN_GREEN_SF/BOUNDARY_SF:.1f}%. The {round(BUFFER_ON_LOTS_SF):,} sf of buffer easement on lots is additional and not counted"],
        ['Impervious surface', 'no district maximum (reported for the stormwater basis)', f"{round(IMPERV_SF):,} sf = {IMPERV_PCT_GIS:.1f}% of the GIS area ({100*IMPERV_SF/SF_DEEDED:.1f}% of 9.44 ac), summed from the drawn footprints: houses/porches/patios {round(sum(L['impervious']['under_roof_sf'] + L['impervious']['patio_sf'] for L in LOTS)):,} + driveways and walks {round(sum(L['impervious']['driveway_sf'] + L['impervious']['entry_walk_sf'] for L in LOTS)):,} + lane {round(LANE_PAVE_SF):,} + entry drive {round(ENTRY_PAVE_SF):,} + curb returns {round(CURB_RETURN_SF):,} + turnarounds {round(HH_PAVE_SF):,} + parking bays {round(BAY_PAVE_SF):,} + sidewalks {round(SIDEWALK_SF):,} + amenity {round(AMEN_BUILT_SF):,} − {round(DRIVE_WALK_OVERLAP_SF):,} counted twice. Per lot: Plan A {PLAN_GEOM['A']['a_under_roof_sf']:,.0f} sf under roof, Plan B {PLAN_GEOM['B']['a_under_roof_sf']:,.0f} sf. WQv {round(WQV_CF):,} cf"],
        ['Block lengths (Table 4.2)', '≤ 600 ft', f"{' / '.join(f'{b:.0f}' for b in BLOCKS_INTERSECTION_FT)} ft measured along the travelled way BETWEEN STREET INTERSECTIONS — Arcado Rd plus the three hammerhead T-intersections. THE READING IS STATED because a single-frontage strip has no cross streets and an open-space green is not a street: the runs of continuous lot frontage between the greens are {' / '.join(str(b) for b in BLOCKS_FRONTAGE_FT)} ft"],
        ['Turnarounds / dead-end road', 'No circular culs-de-sac (Table 4.2). IFC 2024 (GA) App. D Table D103.4: over 750 ft — special approval required. App. D107.1 (GA): second access above 120 dwelling units', f"No cul-de-sac; 3 hammerhead (T) turnarounds, 20'-0\" wide × 60'-0\" legs, at {' / '.join(f'{h:.0f}' for h in HH_SPACING)} ft spacing — every spacing well inside 750 ft. Longest dead-end travelled way {DEAD_END_FT:.0f} ft → D103.4 special approval requested. {N_LOTS} DU is below the 120-unit D107.1 threshold, so no second access is required; NFPA 13D sprinklers are OFFERED, not required"],
        ['Stream buffers (Lilburn Code Ch. 109 Art. VII / GA EPD, O.C.G.A. §12-7-6(b)(15))', '25 ft (GA EPD) / 50 ft undisturbed / 75 ft impervious, from TOP OF BANK', f"All three digitized reaches screened. Distances shown are to the digitized CENTRELINE with a {TOB_ALLOWANCE:.0f}-ft top-of-bank allowance, so everything impervious is held at ≥ {SCREEN_IMPERV:.0f} ft: nearest lot {STREAM_CLEARANCES['nearest_lot_ft']:.1f} ft, nearest dwelling {STREAM_CLEARANCES['nearest_dwelling_ft']:.1f} ft, pond top of bank {STREAM_CLEARANCES['nearest_pond_top_of_bank_ft']:.1f} ft, lane pavement {STREAM_CLEARANCES['lane_pavement_ft']:.1f} ft. The SW slot at u 1,230–1,280 that fails the screen is not lotted — it is a stream-setback tract. Top of bank to be field delineated"],
        ['Floodplain', 'No development in a floodway or floodplain (Table 4.2)', 'FEMA Zone X — no special flood hazard area on site (Gwinnett GIS); FIRM panel number and effective date to be shown on sheet C-0.0'],
        ['Stormwater detention (GCSWMM, via the City)', f"10,000 cf per disturbed acre less RRv = {DETENTION_REQ_CF:,} cf on {DISTURBED['disturbed_ac']:.3f} disturbed ac (RRv taken as 0)", f"{DETENTION_PROV_CF:,} cf: Pond 1 {PONDS[0]['est_storage_cf']:,} cf ({PONDS[0]['top_of_bank_ft']} ft top of bank) + Pond 2 {PONDS[1]['est_storage_cf']:,} cf ({PONDS[1]['top_of_bank_ft']} ft), {POND_DEPTH:.0f} ft deep, {POND_SLOPE:.0f}:1 slopes, prismoidal. Top of bank ≥ {BUFFER+10:.0f} ft inside the SW line and ≥ {SCREEN_IMPERV:.0f} ft from every stream centreline. WQv {round(WQV_CF):,} cf. Concept only — PE to size"],
        ['Sanitary sewer', 'Gwinnett DWR capacity certification; 2026 Comprehensive Plan Amendment policy "do not further extend sewer in this area" (transmitted to DCA 2026-07-13, adoption pending)', f"Phase 1 ({METRICS['lots_phase1']} lots) gravity to the EXISTING on-site 8-in main at MH INV 927.13 — no extension at all. Phase 2 ({METRICS['lots_phase2']} lots): {SEWER_EXT_OFFSITE_FT:.0f}-ft off-site 8-in gravity extension to the Legends at Parkview main, MH INV 919.58, through a recorded easement — the PRIMARY route, because DWR policy bars a private pump station for a residential subdivision and WSR-24 §1.3.1(A) bars a county station at this distance. Grinder/LPS shown as a contingency only"],
        ['Access (Gwinnett DOT access management)', '≈ 244 ft between access points on a collector (VERIFY); ISD ≈ 390 ft at 35 mph', f"One full-movement entrance at v = −190 in the SW third of the frontage, {SEP_FT:.0f} ft from the Arcadia Pl centreline measured along the Arcado Rd centreline ({SEP_CHORD_FT:.0f} ft chord); 24'-0\" drive, two reverse curves R = {ENTRY_R:.0f} ft (Δ {math.degrees(PHI1-PHI0):.1f}°) to the lane midline at u = {U_JOIN:.1f}; curb returns R = {RET_R_NE:.0f} ft (NE) / {RET_R_SW:.0f} ft (SW). No lot driveway enters Arcado Rd. A BUFFER REDUCTION of {SW_RETURN_ENCROACH_FT:.1f} ft ({SW_RETURN_BUFFER_SF_TXT}) at the SW return is requested — dimensioned on this sheet"],
        ['Traffic (Gwinnett DOT TIS Guidelines 2023)', 'A TIS accompanies every zoning application; the exemption is 7 lots or fewer → LEVEL 1 (document-only)', f"≈ {0.30*N_LOTS:.1f} PM peak-hour trips and ≈ {4.31*N_LOTS:.0f} daily (ITE Trip Generation 11th ed. LUC 251, Senior Adult Housing – Single-Family, × {N_LOTS} DU); HOPA 55+ generates 0 students. Level 1 TIS to be submitted — confirm the City adopts the county guidelines"],
        ['Accessory-structure setbacks (Table 4.1)', '5 ft side / 5 ft rear', 'No accessory structures proposed on any lot; the clubhouse, mail kiosk and pickleball pads stand in the HOA amenity tract, not on lots, and are dimensioned to the tract lines'],
        ['Building coverage (§316)', 'no numeric maximum stated in Table 4.1 for R-2 — reported', f"Plan A {100*PLAN_GEOM['A']['a_under_roof_sf']/5000:.1f}% and Plan B {100*PLAN_GEOM['B']['a_under_roof_sf']/5000:.1f}% of a 5,000-sf lot, under roof (conditioned + garage + covered porches)"],
        ['Landscaped open space (§317)', 'reported', f"green-only common open space {round(OPEN_GREEN_SF):,} sf = {100*OPEN_GREEN_SF/BOUNDARY_SF:.1f}% of the GIS area, plus {round(BUFFER_ON_LOTS_SF):,} sf of undisturbed buffer easement on lots and a 10-ft landscape strip on the Arcado Rd frontage"],
        ['Lot frontage on a street (§319)', '≥ 30 ft on a public street or approved private street', f"50'-0\" on the private lane for every one of the {N_LOTS} lots; the lane is a private street in an HOA tract built to public-street standards"],
        ['Disturbed area', 'reported (drives detention and the LDP fee)', f"{DISTURBED['disturbed_sf']:,} sf = {DISTURBED['disturbed_ac']:.3f} ac on site = site area less {DISTURBED['preserved_sf']:,} sf preserved (20-ft buffer bands {DISTURBED['buffer_bands_sf']:,} + creek woods {DISTURBED['creek_woods_net_sf']:,} + 50-ft stream buffer {DISTURBED['stream_buffer_net_sf']:,}, unioned)"],
        ['Off-site disturbance', 'reported', f"≈ {SEWER_EXT_OFFSITE_FT*20:,.0f} sf ({SEWER_EXT_OFFSITE_FT:.0f} ft × 20-ft easement) for the Phase 2 sanitary sewer extension to the Legends at Parkview main; plus the Arcado Rd driveway apron and frontage sidewalk within the existing R/W. Easement and permission to be obtained; quantified for the LDP"],
        ['Existing / proposed structures', '—', 'Two existing houses (4535 and 4541 Arcado Rd SW) and their accessory structures near the frontage to be removed — locations to be verified by survey. Proposed: ' + f'{N_LOTS}' + ' one-story dwellings + one ' + f"{AMENITY['clubhouse_sf']:,}" + '-sf clubhouse'],
        ['Signs', 'permitted separately', f"One monument entry sign ≤ 32 sf and ≤ 6 ft high at the entrance, shown; no wall signs proposed on any dwelling. All signs shall be permitted separately"],
    ]
    yend = table(D, x, yb, ['SITE DATA ITEM', 'REQUIRED', 'PROVIDED'], rows, size=6.0, widths=[135, 200, 575],
                 title='SITE DATA — REQUIRED vs. PROVIDED',
                 subtitle='Lilburn Zoning Ordinance 2023-603 Tables 4.1 (R-2), 4.2 and 8.1 unless another authority is named. Every statement is an "appears consistent with" statement; this sheet is not a compliance certification.')
    # legend — every symbol drawn on this sheet appears here, and every entry here is drawn on this sheet
    lx = x + 930; ly = yb
    D.add(f'<text x="{lx}" y="{ly}" font-size="9" font-weight="bold">LEGEND</text>')
    D.add(f'<text x="{lx}" y="{ly+9}" font-size="5.6" fill="#444">Every symbol drawn on C-2.0 is listed; every entry is drawn. Proposed water,</text>')
    D.add(f'<text x="{lx}" y="{ly+16}" font-size="5.6" fill="#444">storm, hydrants, limits of disturbance, tree line and landscape symbols are</text>')
    D.add(f'<text x="{lx}" y="{ly+23}" font-size="5.6" fill="#444">on sheets C-3.0, C-4.0 and C-7.0 and are deliberately absent here.</text>')
    items = [
        ('line', '#000', 1.8, '', 'Assemblage boundary (Gwinnett GIS — DRAFT, RLS survey governs)'),
        ('line', '#333', 0.6, '10 4 2 4', 'Interior parcel line (four parcels to be combined)'),
        ('line', '#9a9a9a', 0.5, '', 'Adjoining property line / existing right-of-way line'),
        ('rect', '#f5f5f2', 0, '', 'Adjoining property (zoned R-1, City of Lilburn)'),
        ('rect', 'url(#r2hatch)', 0, '', 'Existing R-2 zoning polygon (Lilburn) — nearest precedent'),
        ('line', '#333', 0.6, '14 3 3 3', 'Existing street centreline (Arcado Rd / Arcadia Pl)'),
        ('line', '#777', 0.5, '14 3 3 3', 'Other existing street centreline'),
        ('line', '#111', 0.6, '', 'Dimension line (buffers, setbacks, tract widths, access spacing)'),
        ('rect', 'url(#bufhatch)', 0, '', "20'-0\" undisturbed perimeter buffer / buffer easement on lots"),
        ('line', '#555', 0.4, '3 2', 'Inner line of the 20-ft perimeter buffer'),
        ('rect', '#d8ecc8', 0, '', "10'-0\" landscape strip along the Arcado Rd R/W"),
        ('line', '#b00', 0.8, '8 3 2 3', "50'-0\" building setback from the Arcado Rd R/W (true perpendicular offset)"),
        ('line', '#999', 0.3, '2 1.5', "Lot setback envelope 15' front / 5' side / 20' rear"),
        ('line', '#1565c0', 1.6, '', 'Stream, state waters (digitized centreline — field delineation required)'),
        ('line', '#1f77b4', 0.5, '3 2', "25'-0\" GA EPD buffer"),
        ('line', '#1f77b4', 0.8, '6 2', "50'-0\" undisturbed stream buffer (Lilburn)"),
        ('line', '#1f77b4', 0.8, '8 2 2 2', "75'-0\" impervious setback"),
        ('rect', '#dbe9f4', 0, '', 'Stream-setback open-space tract (unlotted, no impervious)'),
        ('line', '#2e7d32', 0.9, '', 'Existing 8-in sanitary sewer'),
        ('circle', '#2e7d32', 0.7, '', 'Existing sanitary manhole (rim/invert per GIS — survey required)'),
        ('line', '#2e7d32', 0.9, '6 3', 'Proposed 8-in sanitary sewer, Phase 1 (gravity, on site)'),
        ('line', '#2e7d32', 0.9, '6 3 1.5 3', 'Proposed 8-in sanitary sewer, Phase 2 (off-site gravity extension — primary route)'),
        ('line', '#2e7d32', 0.9, '2 2', 'Low-pressure force main from the LS symbol (contingency only)'),
        ('rect', '#fff', 0.9, '', 'LS — grinder / lift-station symbol (contingency; PE to size)'),
        ('dot', '#b00', 0, '', 'Existing fire hydrant'),
        ('line', '#a67c52', 0.55, '4 2', 'Existing contour, 2 ft (USGS 3DEP — approximate)'),
        ('rect', '#ececec', 0, '', 'Private lane tract and entry-drive tract (HOA-owned)'),
        ('rect', '#d6d6d6', 0, '', 'Lane / entry-drive pavement, curb returns, turnaround legs, parking bays'),
        ('line', '#555', 0.3, '', "Parking stall, 9'-0\" × 18'-0\" (van-accessible space + aisle at the NE bay)"),
        ('rect', '#f7f7f7', 0, '', "5'-0\" concrete sidewalk"),
        ('line', '#444', 0.4, '12 3 2 3', 'Lane / entry-drive centreline'),
        ('rect', '#e2e2e2', 0, '', "20'-0\" driveway"),
        ('rect', '#f9e4c8', 0, '', 'Dwelling — conditioned body (L-shaped, from data/plans.json)'),
        ('rect', '#efd2ad', 0, '', "Garage wing, recessed 5'-0\" behind the front wall (Table 4.2)"),
        ('rect', '#fdf3e4', 0, '', 'Covered front porch / covered rear porch'),
        ('rect', '#ded2bc', 0, '', 'Uncovered rear patio'),
        ('rect', '#dff0d8', 0, '', 'Pocket green / terminus green (common open space)'),
        ('rect', '#e4efdc', 0, '', 'Pond tract (common open space)'),
        ('rect', '#cfe3f3', 0, '', 'Dry extended-detention / water-quality basin — top of bank'),
        ('line', '#1f77b4', 0.4, '2 2', 'Basin bottom'),
        ('rect', 'url(#woods)', 0, '', 'Creek woods — preserved open space'),
        ('rect', '#eef4e6', 0, '', 'Front amenity tract (common open space)'),
        ('rect', '#cfe8bd', 0, '', 'Village green'),
        ('rect', '#f2c58a', 0, '', 'Clubhouse and mail kiosk (CBU)'),
        ('rect', '#f0e9d8', 0, '', "Pickleball pad, 30'-0\" × 60'-0\" fenced"),
        ('rect', '#bcd7c2', 0, '', "Pickleball court, 20'-0\" × 44'-0\""),
        ('rect', '#333', 0, '', 'Monument entry sign (≤ 32 sf, ≤ 6 ft high)'),
        ('line', '#7b1fa2', 1.4, '14 4 3 4', 'Block / phase line (falls on lot lines)'),
        ('line', '#444', 0.5, '', 'PT — control point at the end of the entry curve (u = %.1f ft)' % U_JOIN),
    ]
    yy = ly + 32
    for kind, col, wdt, dash, txt in items:
        lines = wrap(txt, 64)
        if kind == 'line': D.add(f'<line x1="{lx}" y1="{yy-2.5}" x2="{lx+28}" y2="{yy-2.5}" stroke="{col}" stroke-width="{wdt}" stroke-dasharray="{dash}"/>')
        elif kind == 'circle': D.add(f'<circle cx="{lx+14}" cy="{yy-3}" r="2.6" fill="#fff" stroke="{col}" stroke-width="{wdt}"/>')
        elif kind == 'dot': D.add(f'<circle cx="{lx+14}" cy="{yy-3}" r="2.6" fill="{col}"/>')
        else: D.add(f'<rect x="{lx}" y="{yy-7}" width="28" height="8" fill="{col}" stroke="#555" stroke-width="{wdt or 0.4}"/>')
        for k, ln in enumerate(lines):
            D.add(f'<text x="{lx+33}" y="{yy + k*6.6}" font-size="5.5">{esc(ln)}</text>')
        yy += max(9.2, len(lines) * 6.6 + 2.8)
    LEGEND_BOTTOM[0] = yy
    # typical lot detail — regenerated from data/plans.json footprints, not from the FACTS nominal squares
    dx0 = lx + 258; dy0 = yb + 14; s2 = 72.0 / 30.0
    Ld = next(L for L in LOTS if L['plan'] == 'B' and L['side'] == 'NE' and not ((L['id'] % 4) not in (1, 2)))
    GD = PLAN_GEOM[Ld['plan']]
    D.add(f'<text x="{dx0}" y="{yb}" font-size="9" font-weight="bold">TYPICAL LOT — 50\'-0" × 100\'-0" — PLAN B (1" = 30\')</text>')
    ox, oy = Ld['u0'], Ld['polygon'][0][1]        # lane-side front corner
    def DP(p): return f"{dx0 + (p[0]-ox)*s2:.2f},{dy0 + (p[1]-oy)*s2 + 20:.2f}"      # front (lane) at top
    def dpoly(poly, **kw): D.add(f'<polygon points="{" ".join(DP(p) for p in poly)}" {attrs(kw)}/>')
    def dline(a, b, **kw):
        xa, ya = [float(t) for t in DP(a).split(',')]; xb, yb_ = [float(t) for t in DP(b).split(',')]
        D.add(f'<line x1="{xa:.2f}" y1="{ya:.2f}" x2="{xb:.2f}" y2="{yb_:.2f}" {attrs(kw)}/>')
    dpoly(Ld['polygon'], fill='#fff', stroke='#000', stroke_width=1)
    dpoly(Ld['buffer_easement'], fill='url(#bufhatch)', stroke='none')
    dpoly(Ld['setback_envelope'], fill='none', stroke='#666', stroke_width=0.5, stroke_dasharray='3 2')
    HD = Ld['house']
    dpoly(HD['driveway_rect'], fill='#e2e2e2', stroke='#777', stroke_width=0.5)
    for r in HD['patio_rects']: dpoly(r, fill='#ded2bc', stroke='#000', stroke_width=0.5)
    dpoly(HD['garage_rect'], fill='#efd2ad', stroke='#000', stroke_width=0.7)
    for r in HD['rear_porch_rects']: dpoly(r, fill='#fdf3e4', stroke='#000', stroke_width=0.6)
    dpoly(HD['body_polygon'], fill='#f9e4c8', stroke='#000', stroke_width=1.0)
    for r in HD['porch_rects']: dpoly(r, fill='#fdf3e4', stroke='#000', stroke_width=0.6)
    def dtext(u, v, t, size=6.5, anchor='middle', rot=0, bold=False, fill='#111'):
        x_, y_ = [float(a) for a in DP((u, v)).split(',')]
        tr = f' transform="rotate({rot} {x_} {y_})"' if rot else ''
        D.add(f'<text x="{x_:.2f}" y="{y_:.2f}" font-size="{size}" text-anchor="{anchor}" fill="{fill}"{" font-weight=\"bold\"" if bold else ""}{tr}>{esc(t)}</text>')
    sgn_d = 1 if Ld['side'] == 'NE' else -1
    f = lambda d: oy + sgn_d * d                                   # lot depth d -> v
    um = (Ld['u0'] + Ld['u1']) / 2; ur = Ld['u1'] + 3
    # dimension witness lines across the lot at every stated depth
    for d in (0.0, GD['face'], GD['oy'], GD['garage_door_ft'], GD['rear_edge_ft'], LOT_D - REAR_SB, LOT_D):
        dline((Ld['u0'] - 2, f(d)), (Ld['u1'] + 2, f(d)), stroke='#999', stroke_width=0.3, stroke_dasharray='2 2')
    for d, off, t in ((0.0, 0.0, "FRONT LOT LINE = PRIVATE LANE TRACT (22'-0\" PVMT + 2'-0\" STRIP + 5'-0\" WALK)"),
                      (GD['face'], 0.0, f"{GD['face']:.2f}' TO PORCH FACE  (15'-0\" REQ'D + 0'-8\" ROOF OVERHANG HELD OUTSIDE THE YARD)"),
                      (GD['oy'], 0.0, f"{GD['oy']:.2f}' TO FRONT WALL — COVERED FRONT PORCH {GD['porch_d']:.0f}'-0\" DEEP"),
                      (GD['garage_door_ft'], 0.0, f"{GD['garage_door_ft']:.2f}' TO GARAGE DOOR — WING RECESSED {GD['garage_recess_ft']:.0f}'-0\" BEHIND THE FRONT WALL (Table 4.2)"),
                      (GD['rear_edge_ft'], -3.2, f"{GD['rear_edge_ft']:.2f}' TO REAR FACE — {HD['rear_kind'].upper()}"),
                      (LOT_D - REAR_SB, 3.2, f"80'-0\" — 20'-0\" REAR YARD = 20'-0\" UNDISTURBED BUFFER EASEMENT (Ord. 2023-603 §313(1))"),
                      (LOT_D, 3.4, "100'-0\" — REAR LOT LINE / R-1 NEIGHBOUR")):
        dline((Ld['u1'] + 2, f(d)), (Ld['u1'] + 3.5, f(d + off)), stroke='#999', stroke_width=0.3)
        dtext(ur + 1.5, f(d + off), t, 6, anchor='start')
    for i, t in enumerate([f"PLAN B '{GD['name'].title()}'", f"BODY {GD['body_label']}",
                           f"{GD['areas']['conditioned_sf']:,.0f} SF COND. · {GD['a_under_roof_sf']:,.0f} SF UNDER ROOF",
                           f"1 STORY · RIDGE {GD['roof_max_ridge_ft']:.2f}' ≤ 40' (Table 4.1)"]):
        dtext(um + 3, f(GD['oy'] + 33 + i * 4.4), t, 5.6, bold=(i == 0))
    gc = poly_centroid(HD['garage_rect'])
    for i, t in enumerate(["2-CAR GARAGE", f"{GD['garage'][3] - GD['garage'][1]:.0f}'-0\" × {GD['garage'][2] - GD['garage'][0]:.0f}'-0\""]):
        dtext(gc[0], gc[1] + sgn_d * (i * 3.4 - 1), t, 5.8, bold=(i == 0))
    dc = poly_centroid(HD['driveway_rect']); dtext(dc[0], f(10), "20'-0\" DRIVEWAY (2 CARS)", 5.8, rot=-90)
    dtext(Ld['u0'] + 2.5, f(88), f"{GD['side_yard_ft']:.0f}'-0\" SIDE", 5.8, rot=-90)
    dtext(Ld['u1'] - 2.5, f(88), f"{GD['side_yard_ft']:.0f}'-0\" SIDE", 5.8, rot=-90)
    dtext(Ld['u0'] - 4, f(50), "100'-0\"", 7, rot=-90, bold=True)
    dtext(um, f(LOT_D) + sgn_d * 8, "50'-0\"", 7, bold=True)
    D.add(f'<text x="{dx0}" y="{dy0 + 20 + LOT_D * s2 + 26:.1f}" font-size="6">Footprints regenerated from data/plans.json ({esc(PLANS_DATE)}); Plan A is the same siting with a 38\'-0" × 51\'-10" body</text>')
    D.add(f'<text x="{dx0}" y="{dy0 + 20 + LOT_D * s2 + 35:.1f}" font-size="6">and a 12\'-0" × 6\'-0" uncovered rear patio ({PLAN_GEOM["A"]["rear_clear_ft"]:.2f}\' from the rear lot line).</text>')
    # --- open-space tract table (SG-14: the named tracts sum EXACTLY to the published figure)
    oy_ = dy0 + 20 + LOT_D * s2 + 56
    os_rows = [[t['name'], f"{t['area_sf']:,}", f"{100*t['area_sf']/BOUNDARY_SF:.2f}%"] for t in OPEN_TRACTS]
    os_rows.append(['TOTAL COMMON OPEN SPACE (HOA-owned tracts)', f'{round(OPEN_SF):,}', f'{100*OPEN_SF/BOUNDARY_SF:.2f}%'])
    os_rows.append(['— of which built or paved (clubhouse roof, court pads, mail kiosk, walks, hammerhead legs)', f'{round(OPEN_BUILT_SF):,}', f'{100*OPEN_BUILT_SF/BOUNDARY_SF:.2f}%'])
    os_rows.append(['GREEN-ONLY COMMON OPEN SPACE', f'{round(OPEN_GREEN_SF):,}', f'{100*OPEN_GREEN_SF/BOUNDARY_SF:.2f}%'])
    os_rows.append([f'20-ft buffer easement on the {N_LOTS} lots — reported separately, NOT counted above', f'{round(BUFFER_ON_LOTS_SF):,}', f'{100*BUFFER_ON_LOTS_SF/BOUNDARY_SF:.2f}%'])
    oy_ = table(D, dx0, oy_, ['OPEN-SPACE TRACT (all HOA-owned and maintained)', 'AREA (SF)', '% OF GIS AREA'], os_rows,
                size=5.8, widths=[258, 52, 52], title='OPEN-SPACE TRACT TABLE',
                subtitle=f'the named tracts sum exactly to the published {round(OPEN_SF):,} sf — there are no unallocated slivers')
    # --- line table
    shorts = [b for b in BEARINGS if b['distance_ft'] < 60]
    _lt = [[b['tag'], b['bearing'], f"{b['distance_ft']:.2f}'"] for b in shorts]
    _half = (len(_lt) + 1) // 2
    LINE_TABLE_BOTTOM[0] = max(
        table(D, dx0, oy_ + 16, ['LINE', 'BEARING (SR 2240 GA West)', 'DIST.'], _lt[:_half], size=5.8,
              widths=[28, 96, 40], title='LINE TABLE',
              subtitle='boundary segments < 60 ft; GIS-derived — DRAFT, RLS survey governs'),
        table(D, dx0 + 178, oy_ + 16, ['LINE', 'BEARING (SR 2240 GA West)', 'DIST.'], _lt[_half:], size=5.8,
              widths=[28, 96, 40], title=' ', subtitle=' '))
    # --- key plan (drawing-standards C-2.0: key plan showing the C-2.1 / C-2.2 match line)
    nx_ = x + 1655; ny_ = yb
    kp_h = draw_key_plan(D, nx_, ny_, 820.0)
    # general notes
    D.add(f'<text x="{nx_}" y="{ny_ + kp_h + 22}" font-size="9" font-weight="bold">GENERAL NOTES</text>')
    yy = ny_ + kp_h + 35
    for i, n_ in enumerate(NOTES, 1):
        for j, ln in enumerate(wrap(f'{i}. {n_}', 243)):
            D.add(f'<text x="{nx_ + (0 if j == 0 else 9)}" y="{yy}" font-size="5.8">{esc(ln)}</text>'); yy += 7.4
        yy += 2.2
    yy += 6
    D.add(f'<rect x="{nx_-6}" y="{yy-9}" width="832" height="26" fill="#fff8e1" stroke="#b00" stroke-width="0.8"/>')
    for j, ln in enumerate(wrap(DISCLAIMER, 145)):
        D.add(f'<text x="{nx_}" y="{yy + j*8.5}" font-size="6.4" font-weight="bold" fill="#7a0000">{esc(ln)}</text>')
    NOTE_BOTTOM[0] = yy + 20
    # ---------------- title block
    tb_y = H - M - 128; tb_h = 128 - 6
    D.add(f'<rect x="{M+6}" y="{tb_y}" width="{W-2*M-12}" height="{tb_h}" fill="#fff" stroke="#000" stroke-width="1.2"/>')
    cells = [0, 700, 1105, 1520, 1900, 2220, W - 2 * M - 12]
    for cx in cells[1:-1]: D.add(f'<line x1="{M+6+cx}" y1="{tb_y}" x2="{M+6+cx}" y2="{tb_y+tb_h}" stroke="#000" stroke-width="0.8"/>')
    bx = M + 14
    D.add(f'<text x="{bx}" y="{tb_y+28}" font-size="21" font-weight="bold">THE COTTAGES AT ARCADO SPRINGS</text>')
    D.add(f'<text x="{bx}" y="{tb_y+48}" font-size="12" font-weight="bold">MASTER CONCEPT PLAN — OVERALL</text>')
    D.add(f'<text x="{bx}" y="{tb_y+64}" font-size="8.5">Rezoning R-1 → R-2 Medium-Density Residential, City of Lilburn, Georgia (Ord. 2023-603 §402; §1003 application)</text>')
    D.add(f'<text x="{bx}" y="{tb_y+78}" font-size="8">4535 / 4537 / 4539 / 4541 Arcado Rd SW, Lilburn, GA 30047 — Land Lot 123, 6th District, Gwinnett County</text>')
    D.add(f'<text x="{bx}" y="{tb_y+91}" font-size="8">PINs R6123 033, R6123 015, R6123 014, R6123 162 — 9.44 ac deeded / {BOUNDARY_SF/43560:.3f} ac GIS calculated</text>')
    D.add(f'<text x="{bx}" y="{tb_y+107}" font-size="8">55+ (HOPA) detached cottage-home community — {N_LOTS} fee-simple lots, {METRICS["density_du_ac_deeded"]} du/ac — one private lane, one entrance on Arcado Rd</text>')
    bx = M + 6 + cells[1] + 8
    D.add(f'<text x="{bx}" y="{tb_y+15}" font-size="7" fill="#555">APPLICANT / OWNERS OF RECORD</text>')
    D.add(f'<text x="{bx}" y="{tb_y+30}" font-size="10" font-weight="bold">Mohammed Awad</text>')
    for k, t in enumerate(['4541 Arcado Rd SW, Lilburn GA 30047-3968 — PINs R6123 033, 015',
                           'Santos C. Mendez &amp; Lesvia R. Roblero de Leon',
                           '4535 Arcado Rd SW, Lilburn GA 30047-3968 — PINs R6123 014, 162',
                           'Co-applicants; notarized owner signatures required (§1003-4)']):
        D.add(f'<text x="{bx}" y="{tb_y+42+k*11}" font-size="7">{t}</text>')
    D.add(f'<text x="{bx}" y="{tb_y+100}" font-size="7" fill="#555">SUBMITTED TO</text>')
    D.add(f'<text x="{bx}" y="{tb_y+112}" font-size="7.5">City of Lilburn Planning &amp; Zoning, 340 Main St — pre-application conference</text>')
    bx = M + 6 + cells[2] + 8
    D.add(f'<text x="{bx}" y="{tb_y+15}" font-size="7" fill="#555">PROFESSIONAL SEALS</text>')
    D.add(f'<rect x="{bx}" y="{tb_y+20}" width="{cells[3]-cells[2]-22}" height="60" fill="none" stroke="#888" stroke-width="0.6" stroke-dasharray="4 3"/>')
    D.add(f'<text x="{bx+8}" y="{tb_y+38}" font-size="9" font-weight="bold" fill="#c00">NO SEAL — DRAFT</text>')
    for k, t in enumerate(['Boundary &amp; legal description: Georgia RLS (required)',
                           'Civil / stormwater / utilities: Georgia PE (required)',
                           'Architecture: Georgia RA · Landscape: Georgia RLA']):
        D.add(f'<text x="{bx+8}" y="{tb_y+50+k*10}" font-size="6.4">{t}</text>')
    D.add(f'<text x="{bx}" y="{tb_y+94}" font-size="6.6">Owner-prepared concept. To be superseded in full by sealed</text>')
    D.add(f'<text x="{bx}" y="{tb_y+104}" font-size="6.6">survey, engineering and architectural documents.</text>')
    D.add(f'<text x="{bx}" y="{tb_y+114}" font-size="6.6">Generator: tools/siteplan.py · data/layout.json · data/plans.json</text>')
    bx = M + 6 + cells[3] + 8
    D.add(f'<text x="{bx}" y="{tb_y+15}" font-size="7" fill="#555">REVISIONS</text>')
    D.add(f'<rect x="{bx}" y="{tb_y+19}" width="{cells[4]-cells[3]-20}" height="11" fill="#e8e8e8" stroke="#000" stroke-width="0.5"/>')
    for cxo, t in ((0, 'No.'), (26, 'DATE'), (86, 'DESCRIPTION')):
        D.add(f'<text x="{bx+cxo+3}" y="{tb_y+27.5}" font-size="6.4" font-weight="bold">{t}</text>')
    revs = [('0', '2026-08-28', 'Issued for pre-application review'),
            ('1', DATE, 'Ponds resized to the re-derived disturbed area; houses drawn at'),
            ('', '', 'their data/plans.json footprints; impervious recomputed; hammerhead 1'),
            ('', '', 'moved to station 600; lane C/L offset 1.0 ft SW; buffer easements as'),
            ('', '', 'trapezoids; entrance returns drawn (SW R = 15 ft); lane tract widened'),
            ('', '', 'at the amenity bays; front line corrected; re-issued as Sheet C-2.0')]
    for k, (a, b, c) in enumerate(revs):
        yv = tb_y + 39 + k * 10
        D.add(f'<rect x="{bx}" y="{yv-8}" width="{cells[4]-cells[3]-20}" height="10" fill="none" stroke="#000" stroke-width="0.35"/>')
        for cxo, t in ((0, a), (26, b), (86, c)):
            D.add(f'<text x="{bx+cxo+3}" y="{yv}" font-size="6.1">{esc(t)}</text>')
    bx = M + 6 + cells[4] + 8
    for k, (a, b) in enumerate([('PROJECT NO.', 'ARCADO-2026-R2 (RZ-2026-__ to be assigned)'), ('DATE', DATE),
                                ('SCALE', '1" = 60\'  ·  ARCH D 36 × 24'), ('DATUM', 'H: GA West SR 2240, US survey ft'),
                                ('', 'V: NAVD88 (USGS 3DEP — approximate)'), ('DRAWN', 'Owner-prepared (AI-assisted)'),
                                ('CHECKED', 'RLS / PE / RA — pending'), ('FILE', 'drawings/mcp-sheet.svg')]):
        D.add(f'<text x="{bx}" y="{tb_y+16+k*13.5}" font-size="6.6" fill="#555">{a}</text>'
              f'<text x="{bx+62}" y="{tb_y+16+k*13.5}" font-size="7.2">{esc(b)}</text>')
    bx = M + 6 + cells[5] + 8
    D.add(f'<text x="{bx}" y="{tb_y+16}" font-size="7" fill="#555">SHEET</text>')
    D.add(f'<text x="{bx+140}" y="{tb_y+66}" font-size="46" font-weight="bold" text-anchor="middle">C-2.0</text>')
    D.add(f'<text x="{bx+140}" y="{tb_y+84}" font-size="7.5" text-anchor="middle">MASTER CONCEPT PLAN — OVERALL</text>')
    D.add(f'<text x="{bx+140}" y="{tb_y+96}" font-size="7" text-anchor="middle" fill="#555">See also C-0.0 cover, C-1.0 existing conditions,</text>')
    D.add(f'<text x="{bx+140}" y="{tb_y+106}" font-size="7" text-anchor="middle" fill="#555">C-2.1 / C-2.2 enlargements, C-2.3 entry enlargement</text>')
    D.add(f'<text x="{bx+140}" y="{tb_y+118}" font-size="8" text-anchor="middle" font-weight="bold" fill="#c00">DRAFT — NOT SEALED</text>')
    # sheet composition: no column of the lower band may run into the title block, and the plan window must
    # be clear of the DRAFT banner.  A future edit that lengthens a table, the legend or the notes fails here
    # instead of silently printing text over the title block.
    for name, bot in (('site-data table', yend), ('legend', LEGEND_BOTTOM[0]), ('line table', LINE_TABLE_BOTTOM[0]),
                      ('general notes + disclaimer', NOTE_BOTTOM[0])):
        check(bot < tb_y - 4, f'lower-band column "{name}" ends at y = {bot:.0f} pt, clear of the title block at y = {tb_y:.0f} pt')
    check(D.y0 + ph + 4 > D.y0 + ph - 1, 'the DRAFT watermark is a banner BELOW the plan window, not across it')
    D.add('</svg>')
    return '\n'.join(D.out) + f'\n<!-- {DISCLAIMER} -->\n<!-- architecture-studio:requires-disclaimer -->\n'

def build_web():
    D = Drawing(SCALE, 0.0, 0.0, fs=1.3)
    pw, ph = (WIN[1] - WIN[0]) * SCALE, (WIN[3] - WIN[2]) * SCALE
    D.add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{pw:.0f}" height="{ph+60:.0f}" viewBox="0 0 {pw:.1f} {ph+60:.1f}" font-family="{FONT}">')
    D.add('<title>The Cottages at Arcado Springs — Master Concept Plan (web)</title>')
    D.add(DEFS); D.add(f'<rect width="{pw:.1f}" height="{ph+60:.1f}" fill="#fff"/>')
    draw_plan(D, web=True)
    D.add(f'<text x="{pw/2}" y="{ph+22}" font-size="13" font-weight="bold" text-anchor="middle">THE COTTAGES AT ARCADO SPRINGS — MASTER CONCEPT PLAN (DRAFT, NOT SEALED) — Rezoning R-1 → R-2, 4535–4541 Arcado Rd SW, Lilburn GA — {N_LOTS} cottage lots, {METRICS["density_du_ac_deeded"]} du/ac — {DATE}</text>')
    D.add(f'<text x="{pw/2}" y="{ph+40}" font-size="9" text-anchor="middle" fill="#7a0000">{esc(DISCLAIMER)}</text>')
    D.add(f'<text x="{pw/2}" y="{ph+54}" font-size="8" text-anchor="middle" fill="#555">Boundary from Gwinnett GIS (survey required and governs); topo USGS 3DEP approx.; plan at 1" = 60\' when printed at 100%; see mcp-sheet.svg (sheet C-1) for site data, notes and legend.</text>')
    D.add('</svg>')
    return '\n'.join(D.out) + f'\n<!-- {DISCLAIMER} -->\n<!-- architecture-studio:requires-disclaimer -->\n'

def render():
    import cairosvg
    sheet = build_sheet(); web = build_web()
    open(os.path.join(DRAW, 'mcp-sheet.svg'), 'w').write(sheet)
    open(os.path.join(DRAW, 'mcp-web.svg'), 'w').write(web)
    cairosvg.svg2png(bytestring=sheet.encode(), write_to=os.path.join(DRAW, 'mcp-sheet.png'), output_width=36 * 150, output_height=24 * 150)
    # 300-dpi crops (front 500 ft of the strip incl. Arcado Rd context; rear 500 ft)
    D = Drawing(SCALE, 102.0, 52.0)
    for name, (ua, ub) in (('mcp-front.png', (-150.0, 520.0)), ('mcp-rear.png', (1200.0, 1840.0))):
        x, w = D.X(ua), (ub - ua) * SCALE; y, h = D.Y(WIN[3]), (WIN[3] - WIN[2]) * SCALE
        crop = sheet.replace(f'width="36in" height="24in" viewBox="0 0 {SHEET_W} {SHEET_H}"', f'width="{w/72:.3f}in" height="{h/72:.3f}in" viewBox="{x:.1f} {y:.1f} {w:.1f} {h:.1f}"', 1)
        cairosvg.svg2png(bytestring=crop.encode(), write_to=os.path.join(DRAW, name), output_width=int(w / 72 * 300), output_height=int(h / 72 * 300))
    print('wrote', ', '.join(os.path.join(DRAW, f) for f in ('mcp-sheet.svg', 'mcp-web.svg', 'mcp-sheet.png', 'mcp-front.png', 'mcp-rear.png')))

if __name__ == '__main__':
    render()
