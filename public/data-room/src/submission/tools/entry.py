#!/usr/bin/env python3
"""Sheet C-2.3 "ENTRY, FRONTAGE AND AMENITY ENLARGEMENT" — The Cottages at Arcado Springs.

    python3 tools/entry.py        ->  drawings/entry-enlargement.svg + .png

ARCH C 24 x 18 in at 1" = 20', with one sight-distance / access-spacing diagram at 1" = 200'.
The sheet is the review-scale enlargement of the front of the site: the Arcado Road frontage,
the single entrance, the front amenity block and everything the City and Gwinnett DOT read at
a driveway — right-of-way, sight triangles, curb returns, curve data, setbacks, buffers, the
landscape strip, the frontage sidewalk, parking, the monument sign and the mail kiosk.

WHY THIS SHEET EXISTS
    audit-2026-09-03/drawing-standards.md section 3.1, row C-2.3, and the City of Lilburn
    Site Development Plan Review Checklist: section 7.j (sight distance at the proposed
    driveway "is not shown ... Provide engineer's certificate (DR 9.7.4)"), section 7.f
    (driveways on both sides of the street with the centreline-to-centreline offset,
    DR 9.7.5), section 4.k/l/m/n/p/q/r/s/t/u/v/w/x/z and section 6.f/6.j/6.k/6.l.
    Sheet C-2.0 carries the whole site at 1" = 60'; nothing at that scale can be dimensioned
    to a driveway standard, so the frontage is enlarged here.

WHERE THE GEOMETRY COMES FROM  (nothing on this sheet is a hand-drawn coordinate)
    tools/sitebase.py       the site-local (u, v) system, the boundary, the adjoining parcels,
                            the Arcado Rd right-of-way and centrelines, the existing sanitary
                            sewer and water, the existing house and drive at 4541, the amenity
                            block, the lane and the entry drive, the north arrow and scale bar.
    data/layout.json        the CURRENT layout (regenerated 2026-09-03): entrance station and
                            offset, drive width, curb-return radii (NE 25'-0", SW 15'-0"), the
                            reverse-curve radius and deflection, the join station, the Arcadia
                            Place separation, the 10-ft landscape strip, the 50-ft collector
                            setback line, the amenity polygons and the metrics block.
    The front property line is rebuilt here by WALKING THE BOUNDARY RING from the NE front
    corner to the SW front corner, the way tools/siteplan.py does it. sitebase's FRONT_LINE
    uses a bounding-box filter that also admits the first 10.04-ft course of the SW PROPERTY
    line; that tips the inward right-of-way normal by about 2.4 deg and would mis-place the
    entrance tangent and both curb returns at 1" = 20'. The curb returns, the entrance
    stationing and the buffer encroachment computed here are asserted against the values
    published in data/layout.json (metrics block) before the sheet is drawn.

WHAT IS DRAWN THAT NO OTHER SHEET CARRIES
    * the two departure (intersection) sight triangles and the 390-ft sight lines, with a
      BLANK engineer's certificate block for a Georgia PE;
    * the potential Arcado Rd right-of-way dedication as a separate hatched strip;
    * the 5-ft Arcado Rd frontage sidewalk, its curb ramps and the driveway crossing;
    * the SW curb return's 2.0-ft encroachment into the 20-ft perimeter buffer, dimensioned
      and labelled as the buffer reduction request that it is;
    * the van-accessible space, its 8-ft access aisle and its sign;
    * the monument sign's clearance from the sight triangle.

DRAFT — NOT SEALED. Every dimension is a GIS-derived draft value in US survey feet. A sealed
Georgia RLS boundary and right-of-way survey, a PE sight-distance certificate and a Gwinnett
County DOT driveway permit are required and govern over this sheet.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitebase as sb                                          # noqa: E402

L = sb.LAYOUT
LANE = L['lane']
AM = L['amenity']
MET = L['metrics']
ENT = LANE['entrance']

# ============================================================================ sheet standards
SHEET_W, SHEET_H = 24 * 72, 18 * 72            # ARCH C landscape = 1728 x 1296 pt
MARGIN, INNER = 27.0, 6.0
SCALE20 = 72.0 / 20.0                          # 1" = 20'  -> 3.6 pt/ft   (the required scale)
WIN = (-100.0, 241.0, -240.0, 8.0)             # u0, u1, v0, v1 (ft)  -> 341 x 248 ft
PLAN_X0, PLAN_Y0 = 39.0, 62.0
PLAN_W, PLAN_H = (WIN[1] - WIN[0]) * SCALE20, (WIN[3] - WIN[2]) * SCALE20      # 1227.6 x 907.2
BAND_X0 = PLAN_X0 + PLAN_W + 12.0              # 1278.6 — right-hand band
BAND_X1 = SHEET_W - MARGIN - INNER - 6.0       # 1689
NOTE_Y0 = PLAN_Y0 + PLAN_H + 8.0               # 962.8 — general-notes strip under the plan
BAND_Y1 = NOTE_Y0 - 8.0
SCALE200 = 72.0 / 200.0                        # 1" = 200' -> 0.36 pt/ft (sight-distance diagram)
WIN2 = (-300.0, 60.0, -600.0, 210.0)           # the diagram window (u0, u1, v0, v1)
DISC_Y = 1123.0
TB_Y, TB_H = 1161.0, 98.0
FONT = sb.FONT

# lettering: nothing on this sheet is smaller than 7.0 pt (0.097 in) and the plan annotation is
# 8.0-8.4 pt, so an 11 x 17 reduction of this ARCH C sheet holds 5.0-6.0 pt lettering.
S_PLAN, S_DIM, S_SMALL, S_NOTE, S_TAB, S_HEAD = 8.2, 7.6, 7.2, 7.3, 7.2, 10.5

C = dict(sb.C)
C.update({'dim': '#0b3d91', 'sight': '#b8860b', 'sight_fill': '#fff3cf', 'ded': '#8e24aa',
          'ls': '#2e7d32', 'ada': '#0b5394', 'fence': '#455a64', 'flag': '#c62828',
          'walk': '#f4f4f0', 'ramp': '#cfd8dc'})

DEFS_EXTRA = '''<defs>
<pattern id="dedhatch" patternUnits="userSpaceOnUse" width="9" height="9" patternTransform="rotate(35)"><line x1="0" y1="0" x2="0" y2="9" stroke="#8e24aa" stroke-width="0.85"/></pattern>
<pattern id="sighthatch" patternUnits="userSpaceOnUse" width="11" height="11" patternTransform="rotate(-35)"><line x1="0" y1="0" x2="0" y2="11" stroke="#c9a227" stroke-width="0.55"/></pattern>
<pattern id="adahatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)"><rect width="6" height="6" fill="#e8f0fb"/><line x1="0" y1="0" x2="0" y2="6" stroke="#0b5394" stroke-width="0.8"/></pattern>
<pattern id="lshatch" patternUnits="userSpaceOnUse" width="12" height="12"><rect width="12" height="12" fill="#eef6e8"/><circle cx="6" cy="6" r="2.4" fill="none" stroke="#5a8a4a" stroke-width="0.5"/></pattern>
<pattern id="dwarn" patternUnits="userSpaceOnUse" width="4" height="4"><rect width="4" height="4" fill="#cfd8dc"/><circle cx="2" cy="2" r="0.9" fill="#607d8b"/></pattern>
</defs>'''


# ============================================================================ front line rebuilt from the ring
def _ring_chain(i0, i1):
    out, i = [], i0
    while True:
        out.append(sb.BOUNDARY[i])
        if i == i1:
            return out
        i = (i + 1) % len(sb.BOUNDARY)


I_FRONT_NE = min(range(len(sb.BOUNDARY)), key=lambda i: sb.dist(sb.BOUNDARY[i], (0.0, 0.0)))
I_FRONT_SW = min(range(len(sb.BOUNDARY)), key=lambda i: sb.BOUNDARY[i][0])
FRONT_LINE = _ring_chain(I_FRONT_NE, I_FRONT_SW)                      # NE -> SW, v decreasing
assert all(FRONT_LINE[i][1] > FRONT_LINE[i + 1][1] for i in range(len(FRONT_LINE) - 1))
FRONT_CHORD = sb.dist(FRONT_LINE[0], FRONT_LINE[-1])                  # 237.44 ft
FRONT_PATH = sum(sb.dist(FRONT_LINE[i], FRONT_LINE[i + 1]) for i in range(len(FRONT_LINE) - 1))


def front_u(v):
    return sb.interp_v(sorted([(p[1], p[0]) for p in FRONT_LINE]), v)


def front_along(v0, v1):
    """length of the right-of-way line between two v stations (measured along the R/W)."""
    tot = 0.0
    for i in range(len(FRONT_LINE) - 1):
        a, b = FRONT_LINE[i], FRONT_LINE[i + 1]
        lo, hi = min(a[1], b[1]), max(a[1], b[1])
        s0, s1 = max(min(v0, v1), lo), min(max(v0, v1), hi)
        if s1 > s0 and hi > lo:
            tot += sb.dist(a, b) * (s1 - s0) / (hi - lo)
    return tot


def pt_path_dist(p, path):
    return min(sb._seg_pt(p, path[i], path[i + 1]) for i in range(len(path) - 1))


def offset_path(path, d):
    """path offset by d ft toward +normal (left of the direction of travel)."""
    out = []
    n = len(path)
    for i, p in enumerate(path):
        a, b = path[max(i - 1, 0)], path[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        out.append((p[0] - dy / ln * d, p[1] + dx / ln * d))
    return out


# ============================================================================ entrance geometry
CTX_STREETS = sb.CTX['streets']
ENTRY_V = ENT['v_rw']                                    # -190.0
ENTRY_W = ENT['drive_width_ft']                          # 24.0
ENTRY_R = ENT['reverse_curve_radius_ft']                 # 100.0
ENTRY_T0 = ENT['tangent_at_rw_ft']                       # 10.0
RET_R_SW = ENT['curb_return_radius_sw_ft']               # 15.0
RET_R_NE = ENT['curb_return_radius_ne_ft']               # 25.0
U_ENTRY = front_u(ENTRY_V)
_fd = (FRONT_LINE[-1][0] - FRONT_LINE[0][0], FRONT_LINE[-1][1] - FRONT_LINE[0][1])
_fl = math.hypot(*_fd)
PHI0 = math.atan2(_fd[0] / _fl, -_fd[1] / _fl)           # inward R/W normal, rad from +u toward +v
N0 = (-math.sin(PHI0), math.cos(PHI0))                   # along the R/W, toward +v
T0 = (math.cos(PHI0), math.sin(PHI0))                    # into the site
DEFL1 = math.radians(ENT['deflection_deg'])              # left-hand curve, PHI0 -> PHI1
PHI1 = PHI0 + DEFL1
DEFL2 = PHI1                                             # right-hand curve, PHI1 -> heading 0
ARC1, ARC2 = ENTRY_R * DEFL1, ENTRY_R * DEFL2
TAN1, TAN2 = ENTRY_R * math.tan(DEFL1 / 2), ENTRY_R * math.tan(DEFL2 / 2)
STA_PC, STA_PRC, STA_PT = ENTRY_T0, ENTRY_T0 + ARC1, ENTRY_T0 + ARC1 + ARC2
ENTRY_CL = [tuple(p) for p in LANE['entry_drive']['centerline']]
P_RW = (U_ENTRY, ENTRY_V)
P_PC = (P_RW[0] + ENTRY_T0 * T0[0], P_RW[1] + ENTRY_T0 * T0[1])
_c1 = (P_PC[0] - ENTRY_R * math.sin(PHI0), P_PC[1] + ENTRY_R * math.cos(PHI0))
P_PRC = (_c1[0] + ENTRY_R * math.sin(PHI1), _c1[1] - ENTRY_R * math.cos(PHI1))
P_PT = (ENT['join_u'], sb.interp_v([(p[0], p[1]) for p in LANE['centerline']], ENT['join_u']))


def curb_return(sgn, R, n=18):
    """quarter-round fillet between the R/W line and the drive pavement edge (siteplan.py)."""
    E = (U_ENTRY + sgn * (ENTRY_W / 2) * N0[0], ENTRY_V + sgn * (ENTRY_W / 2) * N0[1])
    Cc = (E[0] + sgn * R * N0[0] + R * T0[0], E[1] + sgn * R * N0[1] + R * T0[1])
    A = (E[0] + sgn * R * N0[0], E[1] + sgn * R * N0[1])          # tangent point on the R/W
    B = (E[0] + R * T0[0], E[1] + R * T0[1])                      # tangent point on the drive edge
    a0 = math.atan2(A[1] - Cc[1], A[0] - Cc[0])
    a1 = math.atan2(B[1] - Cc[1], B[0] - Cc[0])
    while a1 - a0 > math.pi:
        a1 -= 2 * math.pi
    while a0 - a1 > math.pi:
        a1 += 2 * math.pi
    pts = [E] + [(Cc[0] + R * math.cos(a0 + (a1 - a0) * k / n), Cc[1] + R * math.sin(a0 + (a1 - a0) * k / n))
                 for k in range(n + 1)]
    return {'polygon': pts, 'E': E, 'A': A, 'B': B, 'C': Cc, 'R': R}


RET_SW, RET_NE = curb_return(-1, RET_R_SW), curb_return(+1, RET_R_NE)
SW_BUF_V = sb.SW(0.0) + 20.0                                       # -214.7
SW_ENCROACH = max(0.0, SW_BUF_V - RET_SW['A'][1])                  # 2.0 ft along the R/W

# ---- assertions against the published metrics (the sheet must not drift from data/layout.json)
assert abs(U_ENTRY - ENT['u_rw']) < 0.02, (U_ENTRY, ENT['u_rw'])
assert abs(STA_PT - ENT['drive_length_ft']) < 0.6, (STA_PT, ENT['drive_length_ft'])
assert abs(SW_ENCROACH - MET['sw_curb_return_buffer_encroachment_ft']) < 0.06, SW_ENCROACH
assert abs(sb.dist(P_PT, ENTRY_CL[-1])) < 0.05, (P_PT, ENTRY_CL[-1])
assert abs(sb.dist(P_PC, ENTRY_CL[5]) - 0.0) < 1.5

# ============================================================================ Arcado Rd + sight distance
# The Arcado Rd centreline published in data/layout.json is truncated to the site frontage
# (v +61 to -377). The 390-ft sight lines run past both ends, so the full Gwinnett GIS street
# centreline is rebuilt here from data/site-context-local.json: every ARCADO RD path within
# 400 ft of the site, de-duplicated and ordered NE -> SW (the road is monotone in v). The
# result spans v +512 to -692 and both sight lines fall inside MAPPED centreline.
ARCADO_CL_SHORT = [tuple(p) for p in LANE['arcado_centerline']]
ARCADO_CL = sorted({(round(q[0], 2), round(q[1], 2))
                    for st in CTX_STREETS if st['name'] == 'ARCADO RD' and st['min_dist_ft'] < 400
                    for path in st['paths_local'] for q in path}, key=lambda q: -q[1])
ARCADIA_CL = tuple(ENT['arcadia_pl_cl_at_arcado'])
ARCADIA_PATH = [tuple(p) for p in LANE['arcadia_pl_centerline']]
ENTRY_ON_CL = tuple(ENT['entrance_cl_on_arcado_cl'])
SEP_FT, SEP_CHORD = ENT['separation_along_cl_ft'], ENT['separation_chord_ft']

ISD_FT = 390.0                    # Gwinnett UDO 900-40.4 Table 900.2 / AASHTO case B1, 35 mph
LANE_HALF = 11.0                  # assumed half travelled way (2-lane, 11-ft lanes) — VERIFY
EYE_SETBACK = 14.4                # AASHTO driver's eye behind the edge of the travelled way
EYE_H, OBJ_H = 3.50, 4.25         # ft (AASHTO Green Book: eye 3.50, approaching vehicle 4.25)
RW_TO_CL = sb.dist(P_RW, ENTRY_ON_CL)
P_EDGE = (ENTRY_ON_CL[0] + LANE_HALF * T0[0], ENTRY_ON_CL[1] + LANE_HALF * T0[1])
P_EYE = (ENTRY_ON_CL[0] + (LANE_HALF + EYE_SETBACK) * T0[0],
         ENTRY_ON_CL[1] + (LANE_HALF + EYE_SETBACK) * T0[1])


def cl_station(path, p):
    """(segment index, t) of the point on `path` nearest p."""
    best = (0, 0.0, 1e18)
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l2 = dx * dx + dy * dy or 1.0
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
        q = (a[0] + t * dx, a[1] + t * dy)
        d = sb.dist(p, q)
        if d < best[2]:
            best = (i, t, d)
    return best[0], best[1]


def cl_walk(path, p, length, forward):
    """walk `length` ft along `path` from p (forward=True toward the end of the list).
    Beyond the mapped centreline the last bearing is projected; the polyline is returned."""
    i, t = cl_station(path, p)
    a, b = path[i], path[i + 1]
    cur = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    out, left = [cur], length
    idx = list(range(i + 1, len(path))) if forward else list(range(i, -1, -1))
    for k in idx:
        d = sb.dist(cur, path[k])
        if d >= left:
            f = left / (d or 1.0)
            out.append((cur[0] + f * (path[k][0] - cur[0]), cur[1] + f * (path[k][1] - cur[1])))
            return out, 0.0
        out.append(path[k])
        cur, left = path[k], left - d
    q, r = out[-2], out[-1]                                   # project the last mapped bearing
    dx, dy = r[0] - q[0], r[1] - q[1]
    ln = math.hypot(dx, dy) or 1.0
    out.append((r[0] + dx / ln * left, r[1] + dy / ln * left))
    return out, left


SIGHT_NE, PROJ_NE = cl_walk(ARCADO_CL, ENTRY_ON_CL, ISD_FT, forward=False)   # toward Arcadia Pl (+v)
SIGHT_SW, PROJ_SW = cl_walk(ARCADO_CL, ENTRY_ON_CL, ISD_FT, forward=True)    # toward Killian Hill (-v)
TRI_NE = [P_EYE] + SIGHT_NE[::-1]
TRI_SW = [P_EYE] + SIGHT_SW
SIGN_POLY = [tuple(p) for p in AM['entry_sign']]
SIGN_CLEAR = min(sb._seg_pt(p, P_EYE, SIGHT_NE[-1]) for p in SIGN_POLY)
CLUB_POLY = [tuple(p) for p in AM['clubhouse']]
CLUB_RW = min(pt_path_dist(p, FRONT_LINE) for p in CLUB_POLY)
SIGN_RW = min(pt_path_dist(p, FRONT_LINE) for p in SIGN_POLY)
assert abs(CLUB_RW - MET['clubhouse_setback_from_arcado_rw_ft']) < 0.1
assert abs(SIGN_RW - MET['entry_sign_setback_from_arcado_rw_ft']) < 0.1

# ============================================================================ frontage improvements
DED_FT = 10.0                     # ASSUMED half-R/W dedication — VERIFY with Gwinnett DOT
DED_LINE = offset_path(FRONT_LINE, DED_FT)             # 10 ft inside the site (FRONT_LINE runs NE->SW)
LS_BAND = [tuple(p) for p in L['buffers']['landscape_strip']]
SETBACK_LINE = [tuple(p) for p in L['buffers']['arcado_setback_line']]
SETBACK_DED = offset_path(SETBACK_LINE, DED_FT)
WALK_W = 5.0
WALK_OFF = 3.0                    # walk sits 3.0-8.0 ft into the R/W off the property line
RAMP_V = (RET_NE['A'][1], RET_SW['A'][1])              # the drive opening measured on the R/W


def walk_piece(v0, v1):
    """the frontage sidewalk between two v stations, as a closed polygon in the R/W."""
    vs = [v for v in [p[1] for p in FRONT_LINE] if min(v0, v1) < v < max(v0, v1)]
    vs = [max(v0, v1)] + sorted(vs, reverse=True) + [min(v0, v1)]
    a = [(front_u(v) - WALK_OFF * T0[0], v - WALK_OFF * T0[1]) for v in vs]
    b = [(front_u(v) - (WALK_OFF + WALK_W) * T0[0], v - (WALK_OFF + WALK_W) * T0[1]) for v in vs]
    return a + b[::-1]


WALK_NE = walk_piece(0.0, RAMP_V[0])
WALK_SW = walk_piece(RAMP_V[1], -234.7)
RAMP_NE = walk_piece(RAMP_V[0], RAMP_V[0] - 8.0)
RAMP_SW = walk_piece(RAMP_V[1] + 8.0, RAMP_V[1])
CROSSWALK = [(front_u(RAMP_V[0]) - WALK_OFF * T0[0], RAMP_V[0]),
             (front_u(RAMP_V[1]) - WALK_OFF * T0[0], RAMP_V[1]),
             (front_u(RAMP_V[1]) - (WALK_OFF + WALK_W) * T0[0], RAMP_V[1]),
             (front_u(RAMP_V[0]) - (WALK_OFF + WALK_W) * T0[0], RAMP_V[0])]
WALK_LEN = front_along(0.0, -234.7)

# ============================================================================ amenity dimensions
PADS = [[tuple(p) for p in q] for q in AM['pickleball']]
COURTS = [[tuple(p) for p in q] for q in AM['courts']]
BAY = [tuple(p) for p in AM['parking_bay']]
KBAY = [tuple(p) for p in AM['kiosk_bay']]
STALLS = [[tuple(p) for p in q] for q in AM['stalls']]
KSTALLS = [[tuple(p) for p in q] for q in AM['kiosk_stalls']]
ADA_STALL = [tuple(p) for p in AM['accessible_stall']]
ADA_AISLE = [tuple(p) for p in AM['accessible_aisle']]
KIOSK = [tuple(p) for p in AM['mail_kiosk']]
FENCE_H, FENCE_MAT = 10.0, 'black PVC-coated chain link (ASTM F668 Cl. 2B, F1043 Gp. IC framework)'


def rect_of(poly):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return (min(xs), min(ys), max(xs), max(ys))


PAD_R = rect_of(PADS[0] + PADS[1])
CT_R = rect_of(COURTS[0])
BAY_R, KBAY_R, KIOSK_R, CLUB_R = rect_of(BAY), rect_of(KBAY), rect_of(KIOSK), rect_of(CLUB_POLY)
PAD_TO_BUFFER = PAD_R[1] - SW_BUF_V                     # 2.0 ft — flagged on the sheet
CLUB_TO_NE_LINE = sb.NE(CLUB_R[2]) - CLUB_R[3]
CLUB_TO_NE_BUFFER = CLUB_TO_NE_LINE - 20.0
LANE_PAVE_W = LANE['pavement_width_ft']


# ============================================================================ drawing helpers
def arrow_head(c, tip, d, size=5.2, w=1.9, color=None):
    """filled arrow head whose point is at plan point `tip`, pointing along plan vector `d`."""
    color = color or C['dim']
    x, y = c.X(tip[0]), c.Y(tip[1])
    dx, dy = c.X(tip[0] + d[0]) - x, c.Y(tip[1] + d[1]) - y
    ln = math.hypot(dx, dy) or 1.0
    dx, dy = dx / ln, dy / ln
    px, py = -dy, dx
    c.spoly([(x, y), (x - size * dx + w * px, y - size * dy + w * py),
             (x - size * dx - w * px, y - size * dy - w * py)], fill=color, stroke='none')


def dim(c, a, b, txt, off=0.0, side=1, size=S_DIM, color=None, ext=2.2, gap=1.2, lw=0.45,
        txt_at='auto', halo=True, bold=False, sub=None):
    """A dimension between plan points a and b, offset `off` ft to `side` of the line."""
    color = color or C['dim']
    dx, dy = b[0] - a[0], b[1] - a[1]
    Lft = math.hypot(dx, dy)
    if Lft < 1e-9:
        return
    ux, uy = dx / Lft, dy / Lft
    nx, ny = -uy * side, ux * side
    A = (a[0] + nx * off, a[1] + ny * off)
    B = (b[0] + nx * off, b[1] + ny * off)
    if abs(off) > 0.01:
        c.line((a[0] + nx * gap, a[1] + ny * gap), (A[0] + nx * ext, A[1] + ny * ext),
               stroke=color, stroke_width=0.35)
        c.line((b[0] + nx * gap, b[1] + ny * gap), (B[0] + nx * ext, B[1] + ny * ext),
               stroke=color, stroke_width=0.35)
    c.line(A, B, stroke=color, stroke_width=lw)
    fits = c.tw(txt, size) < Lft * c.s - 14
    if txt_at == 'auto':
        txt_at = 'mid' if fits else 'end'
    if txt_at == 'mid':
        arrow_head(c, A, (-ux, -uy), color=color)
        arrow_head(c, B, (ux, uy), color=color)
    else:
        e = 13.0 / c.s
        c.line((A[0] - ux * e, A[1] - uy * e), A, stroke=color, stroke_width=lw)
        c.line(B, (B[0] + ux * e, B[1] + uy * e), stroke=color, stroke_width=lw)
        arrow_head(c, A, (ux, uy), color=color)
        arrow_head(c, B, (-ux, -uy), color=color)
    rot = c.rot_of(A, B)
    toff = (size * 0.62) / c.s
    if txt_at == 'mid':
        p = ((A[0] + B[0]) / 2 + nx * toff, (A[1] + B[1]) / 2 + ny * toff)
        anc = 'middle'
    elif txt_at == 'end':
        p = (B[0] + ux * (16.0 / c.s) + nx * toff, B[1] + uy * (16.0 / c.s) + ny * toff)
        anc = 'start' if math.cos(math.radians(rot)) * ux + math.sin(math.radians(rot)) * uy > 0 else 'end'
    else:
        p = (A[0] - ux * (16.0 / c.s) + nx * toff, A[1] - uy * (16.0 / c.s) + ny * toff)
        anc = 'end' if math.cos(math.radians(rot)) * ux + math.sin(math.radians(rot)) * uy > 0 else 'start'
    lines = [txt] + ([sub] if sub else [])
    for k, t in enumerate(lines):
        c.text(p[0], p[1], t, size=size if k == 0 else size - 0.6, anchor=anc, rot=rot,
               bold=bold and k == 0, fill=color if k == 0 else '#444', halo=halo,
               dy=k * (size + 0.4))


def leader(c, at, to, lines, size=S_PLAN, anchor='start', color='#111', bold_first=True,
           gap=1.15, dot=True, halo=True):
    """A leader line from feature point `at` to text block anchored at `to`."""
    c.line(at, to, stroke=color, stroke_width=0.4)
    if dot:
        c.circle(at, 1.5, fill=color, stroke='none')
    c.textlines(to[0], to[1], lines, size=size, anchor=anchor, gap=gap, bold_first=bold_first,
                fill=color, halo=halo)


def tick_fence(c, poly, color=None, step=6.0):
    """fence symbol: a line with short cross ticks."""
    color = color or C['fence']
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        c.line(a, b, stroke=color, stroke_width=0.8)
        Lft = sb.dist(a, b)
        if Lft < 1e-6:
            continue
        ux, uy = (b[0] - a[0]) / Lft, (b[1] - a[1]) / Lft
        k = step
        while k < Lft:
            p = (a[0] + ux * k, a[1] + uy * k)
            c.line((p[0] - uy * 1.1, p[1] + ux * 1.1), (p[0] + uy * 1.1, p[1] - ux * 1.1),
                   stroke=color, stroke_width=0.6)
            k += step


def ada_symbol(c, ctr, r=3.2, color=None):
    """international symbol of accessibility, schematically, inside the stall."""
    color = color or C['ada']
    c.circle(ctr, r * c.s * 0.62, fill='none', stroke=color, stroke_width=0.8)
    c.circle((ctr[0], ctr[1] + r * 0.62), 1.5, fill=color, stroke='none')
    c.line((ctr[0], ctr[1] + r * 0.35), (ctr[0] - r * 0.35, ctr[1] - r * 0.15), stroke=color, stroke_width=1.0)
    c.line((ctr[0] - r * 0.35, ctr[1] - r * 0.15), (ctr[0] + r * 0.45, ctr[1] - r * 0.5),
           stroke=color, stroke_width=1.0)


def sign_post(c, at, label, size=S_SMALL, color=None, up=9.0):
    """a small post-mounted sign symbol with its legend."""
    color = color or C['ada']
    c.line(at, (at[0], at[1] + up), stroke=color, stroke_width=0.7)
    c.poly([(at[0] - 2.0, at[1] + up), (at[0] + 2.0, at[1] + up),
            (at[0] + 2.0, at[1] + up + 3.4), (at[0] - 2.0, at[1] + up + 3.4)],
           fill='#fff', stroke=color, stroke_width=0.7)
    c.text(at[0] + 3.2, at[1] + up + 3.0, label, size=size, anchor='start', fill=color, halo=True)


def tree_row(c, path, step=25.0, r=3.0, color=None):
    """landscape-strip planting: one tree + one shrub per 25 linear feet (checklist 6.j)."""
    color = color or C['ls']
    acc, out = 0.0, []
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        Lft = sb.dist(a, b)
        t = step - acc
        while t < Lft:
            f = t / Lft
            out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
            t += step
        acc = (acc + Lft) % step
    for p in out:
        c.circle(p, r * c.s * 0.5, fill='none', stroke=color, stroke_width=0.6)
        c.circle((p[0] - 6.0, p[1]), 1.6, fill='#dcedd4', stroke=color, stroke_width=0.4)
    return out


def north_arrow(c, x, y, r=26.0):
    """Grid-north arrow — same construction as sitebase.north_arrow(), with 7.2-pt lettering so the
    sheet holds the 1/8-in minimum at full size (sitebase letters its arrow at 6.0 pt)."""
    a = math.radians(sb.NORTH_DEG)
    dx, dy = math.cos(a), -math.sin(a)
    px, py = -dy, dx
    c.scircle(x, y, r, fill='#fff', stroke='#000', stroke_width=0.8)
    tip = (x + dx * r * 0.86, y + dy * r * 0.86)
    tail = (x - dx * r * 0.78, y - dy * r * 0.78)
    c.sline(tail[0], tail[1], tip[0], tip[1], stroke='#000', stroke_width=2.0)
    c.spoly([tip, (tip[0] - 15 * dx + 5.4 * px, tip[1] - 15 * dy + 5.4 * py),
             (tip[0] - 15 * dx - 5.4 * px, tip[1] - 15 * dy - 5.4 * py)], fill='#000')
    c.stext(tip[0] + 10 * dx, tip[1] + 10 * dy + 4, 'N', size=13, bold=True, anchor='middle')
    c.stext(x, y + r + 12, 'GRID NORTH (SR 2240 GA WEST)', size=7.2, anchor='middle')
    c.stext(x, y + r + 21, "= 28°43' ABOVE THE +u AXIS", size=7.2, anchor='middle')


def scalebar(c, x, y, scale, step_ft, steps=4):
    """Graphic scale bar — as sitebase.scalebar(), lettered at 7.2 pt."""
    h = 7.5
    for k in range(steps):
        c.srect(x + step_ft * scale * k, y, step_ft * scale, h,
                fill='#000' if k % 2 == 0 else '#fff', stroke='#000', stroke_width=0.6)
        c.stext(x + step_ft * scale * k, y - 4, str(step_ft * k), size=7.2, anchor='middle')
    c.stext(x + step_ft * scale * steps, y - 4, '%d ft' % (step_ft * steps), size=7.2, anchor='middle')
    c.stext(x + step_ft * scale * steps / 2.0, y + h + 12,
            'GRAPHIC SCALE  1" = %d\'' % round(72.0 / scale), size=8.5, bold=True, anchor='middle')


# ============================================================================ the ARCH C sheet frame
def sheet_c(title, sheet_no, subtitle, scale_note, status_lines):
    D = sb.Drawing(SCALE20, PLAN_X0, PLAN_Y0, fs=1.0, win=WIN)
    D.add('<svg xmlns="http://www.w3.org/2000/svg" width="24in" height="18in" viewBox="0 0 %d %d" '
          'font-family="%s">' % (SHEET_W, SHEET_H, FONT))
    D.add('<title>%s</title>' % sb.esc('%s — %s — Sheet %s' % (sb.PROJECT.title(), title, sheet_no)))
    D.add(sb.DEFS)
    D.add(DEFS_EXTRA)
    D.srect(0, 0, SHEET_W, SHEET_H, fill='#fff')
    D.srect(MARGIN, MARGIN, SHEET_W - 2 * MARGIN, SHEET_H - 2 * MARGIN, fill='none', stroke='#000',
            stroke_width=2)
    D.srect(MARGIN + INNER, MARGIN + INNER, SHEET_W - 2 * (MARGIN + INNER),
            SHEET_H - 2 * (MARGIN + INNER), fill='none', stroke='#000', stroke_width=0.6)

    # ---- title block (same cell grid and wording as tools/sitebase.py, scaled to ARCH C)
    x0, w = MARGIN + INNER, SHEET_W - 2 * (MARGIN + INNER)
    D.srect(x0, TB_Y, w, TB_H, fill='#fff', stroke='#000', stroke_width=1.2)
    cells = [0, 545, 900, 1180, 1420, w]
    for cx in cells[1:-1]:
        D.sline(x0 + cx, TB_Y, x0 + cx, TB_Y + TB_H, stroke='#000', stroke_width=0.8)
    bx = x0 + 8
    D.stext(bx, TB_Y + 25, sb.PROJECT, size=17, bold=True)
    D.stext(bx, TB_Y + 44, '%s — Rezoning R-1 → R-2 (City of Lilburn, Georgia)' % title, size=10.5, bold=True)
    D.stext(bx, TB_Y + 58, sb.ADDRESSES, size=8)
    D.stext(bx, TB_Y + 70, sb.LEGAL, size=8)
    for k, ln in enumerate(sb.wrap(subtitle, 124)[:2]):
        D.stext(bx, TB_Y + 82 + k * 9.4, ln, size=7.2)
    bx = x0 + cells[1] + 8
    D.stext(bx, TB_Y + 15, 'APPLICANT / OWNER', size=7.4, fill='#555')
    D.stext(bx, TB_Y + 30, sb.APPLICANT, size=10.5, bold=True)
    D.stext(bx, TB_Y + 42, '4541 Arcado Rd SW, Lilburn GA 30047-3968 (parcels 033, 015);', size=7.2)
    D.stext(bx, TB_Y + 52, 'Mendez / Roblero de Leon (parcels 014, 162) — co-applicants,', size=7.2)
    D.stext(bx, TB_Y + 62, 'owner signatures required', size=7.2)
    D.stext(bx, TB_Y + 75, 'PREPARED FOR', size=7.4, fill='#555')
    D.stext(bx, TB_Y + 86, 'Pre-application conference, City of Lilburn Planning & Zoning', size=7.4)
    D.stext(bx, TB_Y + 94, '(340 Main St) — rezoning per Ord. 2023-603 §1003', size=7.4)
    bx = x0 + cells[2] + 8
    D.stext(bx, TB_Y + 15, 'STATUS', size=7.4, fill='#555')
    D.stext(bx, TB_Y + 33, 'DRAFT — NOT SEALED', size=12.5, bold=True, fill='#c00')
    for k, ln in enumerate(status_lines):
        D.stext(bx, TB_Y + 45 + k * 9.4, ln, size=7.2)
    D.stext(bx, TB_Y + 92, 'Generator: tools/sitebase.py + tools/entry.py', size=7.2)
    bx = x0 + cells[3] + 8
    for k, (a, b) in enumerate([('DATE', sb.DATE), ('SCALE', scale_note),
                                ('DATUM', 'SR 2240 GA West US-ft; NAVD88'),
                                ('DRAWN', 'owner-prepared (AI-assisted)'),
                                ('CHECKED', 'RLS / PE — pending')]):
        D.stext(bx, TB_Y + 15 + k * 17, a, size=7.2, fill='#555')
        D.stext(bx + 48, TB_Y + 15 + k * 17, b, size=7.6)
    bx = x0 + cells[4] + 8
    D.stext(bx, TB_Y + 15, 'SHEET', size=7.4, fill='#555')
    D.stext(bx + 108, TB_Y + 63, sheet_no, size=44, bold=True, anchor='middle')
    D.stext(bx + 108, TB_Y + 80, title, size=7.4, anchor='middle')
    D.stext(bx + 108, TB_Y + 91, 'ARCH C 24" × 18"', size=7.2, anchor='middle', fill='#555')

    # ---- disclaimer strip (house rule)
    D.srect(x0, DISC_Y, w, 32, fill='#fff8e1', stroke='#b00', stroke_width=0.8)
    D.stext(x0 + 8, DISC_Y + 13, 'Disclaimer: ' + sb.DISCLAIMER.split('Disclaimer: ')[-1], size=8.4,
            bold=True, fill='#7a0000')
    D.stext(x0 + 8, DISC_Y + 25,
            'DRAFT / NOT SEALED — every item that must be sealed by a Georgia RLS, PE, architect or landscape '
            'architect is shown as a concept only. Statements of conformity read "appears consistent with"; '
            'nothing on this sheet certifies compliance.', size=7.4, fill='#7a0000')
    D.add('<!-- %s -->' % sb.MARKER)

    px, py, pw, ph = D.box()
    D.stext(px, py - 26, '%s — SCALE 1" = 20\'' % title.upper(), size=13, bold=True)
    D.stext(px, py - 14, 'Site-local coordinates: +u along the strip to the NW, +v across toward the NE line '
                         '(see north arrow). All dimensions in US survey feet, DRAFT — the sealed RLS boundary '
                         'and right-of-way survey governs.', size=7.6, fill='#444')
    D.later(lambda: D.srect(px, py, pw, ph, fill='none', stroke='#000', stroke_width=1))
    return D


# ============================================================================ the plan (1" = 20')
def buffer_band(u0, u1, side):
    """the 20-ft undisturbed perimeter buffer band along the NE or SW property line."""
    us = [u0 + (u1 - u0) * k / 24.0 for k in range(25)]
    if side == 'NE':
        return [(u, sb.NE(u)) for u in us] + [(u, sb.NE(u) - 20.0) for u in reversed(us)]
    return [(u, sb.SW(u)) for u in us] + [(u, sb.SW(u) + 20.0) for u in reversed(us)]


def plan(c, small=False):
    """Every layer of the enlargement. `small` drops the annotation for the key diagram."""
    sb.adjoiners(c, labels=False, zoning=False)
    sb.arcado_row(c, labels=False)

    # --- departure (intersection) sight triangles, under the site improvements
    for tri in (TRI_NE, TRI_SW):
        c.poly(tri, fill='url(#sighthatch)', stroke='none')
    if small:
        return

    # --- right-of-way dedication, landscape strip and perimeter buffers
    # the 10-ft landscape strip and the assumed 10-ft dedication occupy the same band: the strip is the
    # ground (pale green with its planting symbols), the dedication is the purple hatch drawn over it.
    c.poly(LS_BAND, fill='url(#lshatch)', stroke=C['ls'], stroke_width=0.45)
    c.poly(FRONT_LINE + DED_LINE[::-1], fill='url(#dedhatch)', stroke='none')
    c.pline(DED_LINE, fill='none', stroke=C['ded'], stroke_width=1.0, stroke_dasharray='11 3 2 3')
    for side, u1 in (('NE', WIN[1]), ('SW', WIN[1])):
        c.poly(buffer_band(front_u(sb.NE(0) if side == 'NE' else sb.SW(0)), u1, side),
               fill='url(#bufhatch)', stroke='#5a7b3a', stroke_width=0.5, stroke_dasharray='6 3')

    # --- amenity tract, village green, lane and entry drive
    c.poly([tuple(p) for p in AM['tract_polygons'][0]], fill='#eef4e6', stroke=C['green_line'],
           stroke_width=0.5, stroke_dasharray='9 3 2 3')
    c.poly([tuple(p) for p in AM['village_green']], fill='#cfe8bd', stroke=C['green_line'], stroke_width=0.5)
    for key in ('tract_polygon',):
        c.poly([tuple(p) for p in LANE[key]], fill=C['tract'], stroke='#666', stroke_width=0.5,
               stroke_dasharray='5 2')
    c.poly([tuple(p) for p in LANE['entry_drive']['tract_polygon']], fill=C['tract'], stroke='#666',
           stroke_width=0.5, stroke_dasharray='5 2')
    for r in (RET_SW, RET_NE):
        c.poly(r['polygon'], fill=C['pave'], stroke='#333', stroke_width=0.7)
    c.poly([tuple(p) for p in LANE['entry_drive']['pavement_polygon']], fill=C['pave'], stroke='#333',
           stroke_width=0.8)
    c.poly([tuple(p) for p in LANE['pavement_polygon']], fill=C['pave'], stroke='#333', stroke_width=0.8)
    for s in LANE['sidewalks']:
        c.poly([tuple(p) for p in s['polygon']], fill=C['walk'], stroke='#777', stroke_width=0.45)
    c.pline(ENTRY_CL, fill='none', stroke='#444', stroke_width=0.5, stroke_dasharray='14 3 2 3')
    c.pline([tuple(p) for p in LANE['centerline'] if p[0] <= WIN[1]], fill='none', stroke='#444',
            stroke_width=0.5, stroke_dasharray='14 3 2 3')

    # --- Arcado Rd frontage sidewalk, ramps and the driveway crossing
    for poly in (WALK_NE, WALK_SW):
        c.poly(poly, fill=C['walk'], stroke='#555', stroke_width=0.55)
    for poly in (RAMP_NE, RAMP_SW):
        c.poly(poly, fill='url(#dwarn)', stroke='#455a64', stroke_width=0.6)
    c.poly(CROSSWALK, fill='none', stroke='#555', stroke_width=0.5, stroke_dasharray='4 3')

    # --- amenity structures
    c.poly(CLUB_POLY, fill='#f2c58a', stroke='#222', stroke_width=0.9)
    for pad, court in zip(PADS, COURTS):
        c.poly(pad, fill='#e9e2d0', stroke='#222', stroke_width=0.5)
        c.poly(court, fill='#bcd7c2', stroke='#222', stroke_width=0.5)
        c.line(((court[0][0] + court[1][0]) / 2, court[0][1]), ((court[0][0] + court[1][0]) / 2, court[2][1]),
               stroke='#456', stroke_width=0.5)
        tick_fence(c, pad)
    for b in (BAY, KBAY):
        c.poly(b, fill=C['pave'], stroke='#333', stroke_width=0.6)
    for st in STALLS + KSTALLS:
        c.poly(st, fill='none', stroke='#555', stroke_width=0.4)
    c.poly(ADA_STALL, fill='url(#adahatch)', stroke=C['ada'], stroke_width=0.7)
    c.poly(ADA_AISLE, fill='url(#adahatch)', stroke=C['ada'], stroke_width=0.7)
    for k in range(1, 9):
        v = ADA_AISLE[0][1] + (ADA_AISLE[2][1] - ADA_AISLE[0][1]) * k / 9.0
        c.line((ADA_AISLE[0][0], v), (ADA_AISLE[1][0], v), stroke=C['ada'], stroke_width=0.5)
    ada_symbol(c, ((ADA_STALL[0][0] + ADA_STALL[1][0]) / 2, (ADA_STALL[0][1] + ADA_STALL[2][1]) / 2))
    sign_post(c, (ADA_STALL[0][0] + 4.0, ADA_STALL[0][1] - 1.5), 'R7-8 + R7-8P "VAN ACCESSIBLE"')
    c.poly(KIOSK, fill='#f2c58a', stroke='#222', stroke_width=0.8)
    c.poly(SIGN_POLY, fill='#333', stroke='#000', stroke_width=0.6)
    tree_row(c, LS_BAND[:14])

    # --- first lots of Block A (context at the east edge of the window)
    for lot in L['lots']:
        if min(p[0] for p in lot['polygon']) > WIN[1]:
            continue
        c.poly([tuple(p) for p in lot['polygon']], fill='#fff', stroke='#222', stroke_width=0.7)
        c.poly([tuple(p) for p in lot['buffer_easement']], fill='url(#bufhatch)', stroke='none')
        c.poly([tuple(p) for p in lot['setback_envelope']], fill='none', stroke='#999', stroke_width=0.4,
               stroke_dasharray='3 2')
        c.poly([tuple(p) for p in lot['driveway_rect']], fill='#e2e2e2', stroke='#777', stroke_width=0.4)
        c.poly([tuple(p) for p in lot['house_rect']], fill=C['house'], stroke='#222', stroke_width=0.6)
        c.poly([tuple(p) for p in lot['garage_rect']], fill='#efd2ad', stroke='#222', stroke_width=0.5)
        for k in ('porch_rect', 'rear_rect'):
            c.poly([tuple(p) for p in lot[k]], fill='#fdf3e4', stroke='#222', stroke_width=0.4)
        ctr = sb.poly_centroid([tuple(p) for p in lot['house_rect']])
        c.textlines(ctr[0], ctr[1] + 9, ['LOT %s, BLOCK %s' % (lot['block_lot'], lot['block']),
                                         'PLAN %s' % lot['plan'], "50'-0\" × 100'-0\" = 5,000 SF"],
                    size=S_SMALL, gap=1.2, bold_first=True, halo=True)

    # --- existing utilities and improvements to be removed
    sb.sewer_existing(c, labels=False)
    sb.water_existing(c, labels=False)
    sb.existing_structures(c, labels=False)

    # --- boundary, setback lines
    c.poly(sb.BOUNDARY, fill='none', stroke=C['bnd'], stroke_width=2.0)
    c.pline(SETBACK_LINE, fill='none', stroke='#c62828', stroke_width=0.9, stroke_dasharray='12 4 3 4')
    c.pline(SETBACK_DED, fill='none', stroke='#e08a8a', stroke_width=0.7, stroke_dasharray='6 4')

    # --- sight lines, on top
    for tri, tag in ((TRI_NE, 'NE'), (TRI_SW, 'SW')):
        c.line(tri[0], tri[-1] if tag == 'NE' else tri[-1], stroke=C['sight'], stroke_width=1.3,
               stroke_dasharray='16 4 3 4')
    c.pline(SIGHT_NE, fill='none', stroke=C['sight'], stroke_width=1.0)
    c.pline(SIGHT_SW, fill='none', stroke=C['sight'], stroke_width=1.0)
    c.circle(P_EYE, 3.2, fill='#fff', stroke=C['sight'], stroke_width=1.1)
    c.circle(P_EYE, 1.4, fill=C['sight'], stroke='none')
    for p, lab in ((P_PC, 'PC 0+10.00'), (P_PRC, 'PRC 1+%05.2f' % (STA_PRC - 100)), (P_PT, 'PT 2+%05.2f' % (STA_PT - 200))):
        c.circle(p, 2.6, fill='#fff', stroke=C['dim'], stroke_width=1.0)
        c.circle(p, 1.1, fill=C['dim'], stroke='none')


# ============================================================================ annotation
def annotate(c):
    RED, DIMC, LSC, DEDC, SGT = C['flag'], C['dim'], C['ls'], C['ded'], C['sight']
    P_NE, P_SW = FRONT_LINE[0], FRONT_LINE[-1]
    ROT = -81.0

    # ------------------------------------------------- Arcado Rd, the R/W and the frontage dimensions
    c.text(-97, -168, 'ARCADO ROAD — GWINNETT COUNTY MINOR COLLECTOR, 35 MPH, 14,800 AADT (GDOT STN 135-6689)',
           size=S_PLAN, rot=ROT, bold=True, halo=True)
    c.text(-97, -66, 'OPPOSITE ARCADO RD R/W LINE — R/W WIDTH VARIES (44\'–60\' SCALED, NOT SURVEYED)',
           size=S_SMALL, rot=ROT, halo=True, fill='#555')
    c.text(-84, -58, 'EX. WATER MAIN (DIP, GWINNETT DWR — SIZE NOT PUBLISHED, VERIFY)', size=S_SMALL,
           rot=ROT, halo=True, fill=C['water'])
    c.text(-62, -20, 'C/L ARCADO RD', size=S_SMALL, rot=ROT, halo=True)
    c.text(-11, -88, 'ARCADO RD R/W LINE = FRONT PROPERTY LINE', size=S_SMALL, rot=ROT, halo=True, bold=True)
    c.text(14, -33, 'NO LOT FRONTS ON OR TAKES ACCESS FROM ARCADO RD', size=S_SMALL, anchor='start',
           halo=True)
    dim(c, P_NE, P_SW, "237.63' ALONG THE R/W  (237.44' CHORD)", off=25.0, side=-1, size=S_DIM + 0.4,
        bold=True, txt_at='mid', sub='FRONTAGE COURSES AND BEARINGS: SEE SHEET C-0 LINE TABLE')
    dim(c, P_NE, P_RW, "192.68'", off=13.0, side=-1, txt_at='mid')
    dim(c, P_RW, P_SW, "44.93'", off=13.0, side=-1, txt_at='mid')
    dim(c, P_RW, ENTRY_ON_CL, "27.89' ± TO C/L", off=0.0, side=1, size=S_SMALL, txt_at='end')

    # ------------------------------------------------- dedication, landscape strip, setbacks
    v0 = -46.0
    dim(c, (front_u(v0), v0), (front_u(v0) + DED_FT * T0[0], v0 + DED_FT * T0[1]), "10'-0\"",
        off=0.0, side=1, size=S_SMALL, color=DEDC, txt_at='start')
    c.text(14, -6, "10'-0\" LANDSCAPE STRIP — 1 TREE + 1 SHRUB PER 25 LF OF FRONTAGE (CHECKLIST §6.g, §6.j)",
           size=S_SMALL, anchor='start', fill=LSC, halo=True, bold=True)
    c.text(14, -13, "POTENTIAL 10'-0\" ARCADO RD R/W DEDICATION SHOWN HATCHED — ASSUMED WIDTH, SEE NOTE 2",
           size=S_SMALL, anchor='start', fill=DEDC, halo=True, bold=True)
    c.text(14, -20, "NO PLANTING 3'-0\" TO 15'-0\" HIGH WITHIN 20'-0\" OF THE R/W INTERSECTION (§6.j)",
           size=S_SMALL, anchor='start', fill=LSC, halo=True)
    v1 = -84.0
    p50 = (front_u(v1), v1)
    dim(c, p50, (p50[0] + 50.0 * T0[0], p50[1] + 50.0 * T0[1]), "50'-0\"", off=0.0, side=1, size=S_DIM,
        color='#c62828', txt_at='mid')
    c.text(22, -140, "50'-0\" BUILDING SETBACK FROM ARCADO RD R/W — TABLE 4.1", size=S_SMALL, rot=ROT,
           fill='#c62828', halo=True, bold=True)
    c.text(38, -140, 'SETBACK IF THE DEDICATION IS TAKEN (SEE NOTE 2)', size=S_SMALL, rot=ROT,
           fill='#b06a6a', halo=True)

    # ------------------------------------------------- frontage sidewalk and ramps
    c.line((front_u(-40.0) - 5.5 * T0[0], -40.0), (12.0, -40.0), stroke='#333', stroke_width=0.4)
    c.text(14, -40, "PROPOSED 5'-0\" CONCRETE SIDEWALK — ARCADO RD FRONTAGE, %.0f LF, IN THE EXISTING R/W,"
           % WALK_LEN, size=S_SMALL, anchor='start', halo=True, bold=True)
    c.text(14, -47, "SHOWN 3'-0\" INSIDE THE R/W LINE; FINAL OFFSET BY THE R/W SURVEY AND THE DOT PERMIT (§5.b)",
           size=S_SMALL, anchor='start', halo=True)
    for r in (RAMP_NE, RAMP_SW):
        c.line(sb.poly_centroid(r), (12.0, -54.0), stroke='#37474f', stroke_width=0.4)
    c.text(14, -54, 'CURB RAMP + DETECTABLE WARNING EACH SIDE OF THE DRIVE; WALK CARRIED THROUGH AT GRADE (§5.d)',
           size=S_SMALL, anchor='start', fill='#37474f', halo=True)

    # ------------------------------------------------- entrance geometry
    dim(c, RET_SW['E'], RET_NE['E'], "24'-0\" ENTRY DRIVE", off=8.0, side=-1, size=S_DIM, bold=True,
        txt_at='mid')
    for r, lab in ((RET_NE, "R = 25'-0\""), (RET_SW, "R = 15'-0\"")):
        m = r['polygon'][len(r['polygon']) // 2]
        c.line(r['C'], m, stroke=DIMC, stroke_width=0.45)
        arrow_head(c, m, (m[0] - r['C'][0], m[1] - r['C'][1]), color=DIMC)
        c.text((r['C'][0] + m[0]) / 2, (r['C'][1] + m[1]) / 2 + 2.4, lab, size=S_DIM, fill=DIMC,
               halo=True, bold=True)
    c.line(_c1, P_PC, stroke=DIMC, stroke_width=0.4, stroke_dasharray='7 3')
    c.line(_c1, P_PRC, stroke=DIMC, stroke_width=0.4, stroke_dasharray='7 3')
    c.circle(_c1, 2.0, fill='none', stroke=DIMC, stroke_width=0.6)
    c.textlines(2.0, -95.0, ['CURVE 1 (LEFT) — R = 100\'-0"', "Δ = 59.9°   L = 104.55'   T = 57.62'"],
                size=S_SMALL, anchor='start', gap=1.3, bold_first=True, fill=DIMC, halo=True)
    _c2 = (P_PRC[0] + ENTRY_R * math.sin(PHI1), P_PRC[1] - ENTRY_R * math.cos(PHI1))
    c.line(_c2, P_PRC, stroke=DIMC, stroke_width=0.4, stroke_dasharray='7 3')
    c.line(_c2, P_PT, stroke=DIMC, stroke_width=0.4, stroke_dasharray='7 3')
    c.circle(_c2, 2.0, fill='none', stroke=DIMC, stroke_width=0.6)
    c.textlines(146.0, -176.0, ['CURVE 2 (RIGHT) — R = 100\'-0"', "Δ = 51.2°   L = 89.33'   T = 47.89'"],
                size=S_SMALL, anchor='end', gap=1.3, bold_first=True, fill=DIMC, halo=True)
    c.text(-30.0, -160.0, "PC  STA 0+10.00  (10'-0\" TANGENT)", size=S_SMALL, anchor='end', bold=True,
           fill=DIMC, halo=True)
    c.text(P_PRC[0] - 3.0, P_PRC[1] - 7.0, 'PRC  STA 1+14.55', size=S_SMALL, anchor='end', bold=True,
           fill=DIMC, halo=True)
    c.line(P_PT, (182.0, -66.0), stroke=DIMC, stroke_width=0.4)
    c.textlines(182.0, -60.0, ['PT  STA 2+03.87  (u = 149.50) — POINT OF TANGENCY',
                               'ON THE LANE MIDLINE; TOTAL ENTRY DRIVE 203.87 LF',
                               'DESIGN SPEED 15 MPH ON THE PRIVATE LANE'],
                size=S_SMALL, anchor='start', gap=1.3, bold_first=True, fill=DIMC, halo=True)

    # ------------------------------------------------- access spacing to Arcadia Place
    a = ENTRY_ON_CL
    b = (sb.interp_v(sorted([(p[1], p[0]) for p in ARCADO_CL]), 2.0), 2.0)
    c.line(a, b, stroke=C['match'], stroke_width=1.3)
    arrow_head(c, a, (a[0] - b[0], a[1] - b[1]), color=C['match'])
    for k in range(1, 6):                                   # ticks so the long dimension reads as one
        q = (a[0] + (b[0] - a[0]) * k / 6.0, a[1] + (b[1] - a[1]) * k / 6.0)
        c.line((q[0] - 1.6, q[1]), (q[0] + 1.6, q[1]), stroke=C['match'], stroke_width=0.5)
    c.text(b[0] - 2.5, -10.0, 'TO C/L ARCADIA PL →', size=S_SMALL, rot=ROT, bold=True,
           fill=C['match'], halo=True, anchor='end')
    c.text(-70.0, -100.0, "251.2' ALONG C/L ARCADO RD TO C/L ARCADIA PL (250.7' CHORD) — GWINNETT ACCESS "
                          "SPACING ON A COLLECTOR ≈ 244' (VERIFY), CHECKLIST §7.f (DR 9.7.5)",
           size=S_SMALL, rot=ROT, bold=True, fill=C['match'], halo=True)

    # ------------------------------------------------- sight triangles
    c.text(-20.0, -50.0, "DEPARTURE SIGHT TRIANGLE — 390'-0\" LEFT (SEE NOTE 3)", size=S_DIM, rot=ROT,
           bold=True, fill=SGT, halo=True)
    c.text(-53.0, -196.0, "DEPARTURE SIGHT TRIANGLE — 390'-0\" RIGHT", size=S_DIM, rot=ROT, bold=True,
           fill=SGT, halo=True)
    c.line(P_EYE, (38.0, -110.0), stroke=SGT, stroke_width=0.4)
    c.text(40.0, -108.0, "DRIVER'S EYE / DECISION POINT — 14.4' BEHIND THE EDGE OF THE TRAVELLED WAY;",
           size=S_SMALL, anchor='start', fill=SGT, halo=True, bold=True)
    c.text(40.0, -115.0, "EYE 3.50', OBJECT 4.25'; CLEAR SIGHT AREA — NOTHING 3'-0\" TO 15'-0\" ABOVE GRADE",
           size=S_SMALL, anchor='start', fill=SGT, halo=True)

    # ------------------------------------------------- buffers
    dim(c, (128.0, sb.SW(128.0)), (128.0, SW_BUF_V), "20'-0\"", off=0.0, side=1, size=S_DIM,
        color='#3f6b2a', txt_at='mid')
    c.text(20.0, -217.0, "20'-0\" UNDISTURBED PERIMETER BUFFER (TABLE 4.1; §313(1))", size=S_SMALL,
           fill='#3f6b2a', halo=True, anchor='start', bold=True)
    dim(c, (196.0, sb.NE(196.0)), (196.0, sb.NE(196.0) - 20.0), "20'-0\"", off=0.0, side=1, size=S_DIM,
        color='#3f6b2a', txt_at='mid')
    c.text(116.0, -13.0, "20'-0\" UNDISTURBED PERIMETER BUFFER — NE LINE", size=S_SMALL, fill='#3f6b2a',
           halo=True, anchor='start', bold=True)

    # ------------------------------------------------- clubhouse
    dim(c, (CLUB_R[0], CLUB_R[1]), (CLUB_R[2], CLUB_R[1]), "60'-0\"", off=-5.0, side=1, size=S_DIM)
    dim(c, (CLUB_R[2], CLUB_R[1]), (CLUB_R[2], CLUB_R[3]), "40'-0\"", off=6.0, side=1, size=S_DIM)
    dim(c, (CLUB_R[2], CLUB_R[3]), (CLUB_R[2], sb.NE(CLUB_R[2])), "%.1f'" % CLUB_TO_NE_LINE,
        off=0.0, side=1, size=S_DIM, txt_at='mid')
    c.textlines(CLUB_R[0] + 30.0, CLUB_R[1] + 21.0,
                ['CLUBHOUSE — 2,400 SF', "60'-0\" × 40'-0\", 1 STORY", 'HOA ACCESSORY STRUCTURE (SEE A-3)',
                 "%.1f' FROM THE ARCADO RD R/W" % CLUB_RW, "(50'-0\" REQUIRED ON A COLLECTOR)",
                 "%.1f' TO THE NE LINE (5'-0\" REQ'D)" % CLUB_TO_NE_LINE],
                size=S_SMALL, gap=1.25, bold_first=True, halo=True)
    c.text(CLUB_R[0] - 3.0, -25.0, "5'-0\" LANDSCAPE STRIP AROUND ALL ACCESSORY STRUCTURES (§6.l)",
           size=S_SMALL, anchor='end', halo=True, fill=LSC)

    # ------------------------------------------------- pickleball
    dim(c, (PAD_R[0], PAD_R[1]), (PAD_R[2], PAD_R[1]), "60'-0\"", off=-4.0, side=1, size=S_DIM)
    dim(c, (PAD_R[0], PAD_R[1]), (PAD_R[0], PADS[0][2][1]), "30'-0\"", off=-4.0, side=1, size=S_DIM)
    dim(c, (PAD_R[0], PADS[0][2][1]), (PAD_R[0], PAD_R[3]), "30'-0\"", off=-4.0, side=1, size=S_DIM)
    dim(c, (CT_R[0], CT_R[3]), (CT_R[2], CT_R[3]), "44'-0\"", off=-3.0, side=-1, size=S_SMALL)
    dim(c, (CT_R[2], CT_R[1]), (CT_R[2], CT_R[3]), "20'-0\"", off=-3.0, side=-1, size=S_SMALL)
    c.line((PAD_R[0] + 4.0, PAD_R[1] + 2.0), (150.0, -205.0), stroke='#333', stroke_width=0.4)
    c.text(150.0, -205.0, "2 PICKLEBALL COURTS — 20'-0\" × 44'-0\" ON 30'-0\" × 60'-0\" PADS;", size=S_SMALL,
           anchor='end', halo=True, bold=True)
    c.text(150.0, -211.0, "10'-0\" HIGH BLACK PVC-COATED CHAIN-LINK FENCE (§4.n) — SEE NOTE 12", size=S_SMALL,
           anchor='end', halo=True)
    dim(c, (PAD_R[0] + 22.0, SW_BUF_V), (PAD_R[0] + 22.0, PAD_R[1]), "2.0'", off=0.0, side=1,
        size=S_DIM, color=RED, txt_at='end')
    c.text(238.0, -194.0, "FLAG: THE PAD STANDS 2.0' FROM THE 20-FT BUFFER; THE ≥ 5'-0\" SEPARATION",
           size=S_SMALL, anchor='end', fill=RED, halo=True, bold=True)
    c.text(238.0, -200.0, "OFFERED IN docs/12 (§4.m PARKING ANALOG) IS NOT ACHIEVED — SHIFT THE PADS 3'-0\" NE",
           size=S_SMALL, anchor='end', fill=RED, halo=True)

    # ------------------------------------------------- parking bays
    dim(c, (BAY_R[0], BAY_R[1]), (BAY_R[2], BAY_R[1]), "7 STALLS @ 9'-0\" = 63'-0\"", off=-4.0, side=1,
        size=S_DIM)
    dim(c, (BAY_R[0], BAY_R[1]), (BAY_R[0], BAY_R[3]), "18'-0\"", off=-4.0, side=1, size=S_DIM)
    dim(c, (KBAY_R[0], KBAY_R[3]), (KBAY_R[2], KBAY_R[3]), "8'-0\" + 8'-0\" + 4 @ 9'-0\" = 52'-0\"",
        off=5.0, side=1, size=S_DIM)
    dim(c, (KBAY_R[2], KBAY_R[1]), (KBAY_R[2], KBAY_R[3]), "18'-0\"", off=4.0, side=1, size=S_DIM)
    dim(c, ADA_STALL[0], ADA_STALL[1], "8'-0\"", off=-3.0, side=1, size=S_SMALL, color=C['ada'])
    dim(c, ADA_AISLE[0], ADA_AISLE[1], "8'-0\"", off=-3.0, side=1, size=S_SMALL, color=C['ada'])
    dim(c, (234.0, LANE['centerline'][0][1] - LANE_PAVE_W / 2),
        (234.0, LANE['centerline'][0][1] + LANE_PAVE_W / 2), "22'-0\" LANE PAVEMENT — 22'-0\" MIN. TWO-WAY "
        'WITH 90° PARKING (§4.u)', off=0.0, side=1, size=S_SMALL, txt_at='end')
    dim(c, (212.0, -147.95), (212.0, -87.77), "60'-0\" LANE TRACT THROUGH THE AMENITY BLOCK", off=0.0,
        side=1, size=S_SMALL, txt_at='end', color='#555')
    c.line((BAY_R[0] + 8.0, BAY_R[3]), (150.0, -132.0), stroke='#333', stroke_width=0.4)
    c.text(150.0, -132.0, "GUEST PARKING BAY — 7 STALLS AT 9'-0\" × 18'-0\" (§4.w), 90° TO THE LANE;",
           size=S_SMALL, anchor='end', halo=True, bold=True)
    c.text(150.0, -138.0, "MAX 1'-6\" OVERHANG, NOT OVER A SIDEWALK OR RIGHT-OF-WAY", size=S_SMALL,
           anchor='end', halo=True)
    c.line((ADA_AISLE[1][0], ADA_AISLE[3][1]), (106.0, -62.0), stroke=C['ada'], stroke_width=0.4)
    c.textlines(106.0, -62.0,
                ["MAIL-KIOSK BAY — 1 VAN-ACCESSIBLE SPACE 8'-0\" WIDE, AN 8'-0\" ACCESS AISLE AND AN",
                 'R7-8 / R7-8P "VAN ACCESSIBLE" SIGN, PLUS 4 SHORT-TERM STALLS AT 9\'-0" × 18\'-0".',
                 '2010 ADA STANDARDS §208.2, §502; SIZE AND LOCATION TO BE CONFIRMED BY THE GWINNETT',
                 'COUNTY FIRE MARSHAL (§4.x). ACCESSIBLE ROUTE TO THE ARCADO RD SIDEWALK — §4.z'],
                size=S_SMALL, anchor='end', gap=1.3, bold_first=True, fill=C['ada'], halo=True)

    # ------------------------------------------------- mail kiosk and monument sign
    dim(c, (KIOSK_R[0], KIOSK_R[3]), (KIOSK_R[2], KIOSK_R[3]), "16'-0\"", off=4.0, side=1, size=S_SMALL)
    dim(c, (KIOSK_R[2], KIOSK_R[1]), (KIOSK_R[2], KIOSK_R[3]), "10'-0\"", off=4.0, side=1, size=S_SMALL)
    c.line((KIOSK_R[2], KIOSK_R[3]), (232.0, -28.0), stroke='#333', stroke_width=0.4)
    c.textlines(232.0, -28.0, ["CLUSTER MAIL KIOSK — 16'-0\" × 10'-0\" ROOFED CBU SHELTER",
                               'WITH 4 SHORT-TERM SPACES; USPS GROWTH MANAGER TO',
                               'CONFIRM THE CBU TYPE AND COUNT (CHECKLIST §4.r)'],
                size=S_SMALL, anchor='end', gap=1.3, bold_first=True, halo=True)
    dim(c, sb.poly_centroid(SIGN_POLY), (front_u(SIGN_POLY[0][1]) - 0.4, SIGN_POLY[0][1]),
        "%.1f' TO THE R/W" % SIGN_RW, off=0.0, side=-1, size=S_SMALL, txt_at='start')
    c.line(sb.poly_centroid(SIGN_POLY), (12.0, -186.0), stroke='#333', stroke_width=0.4)
    c.textlines(14.0, -186.0,
                ["PROPOSED MONUMENT ENTRY SIGN — SIGN FACE ≤ 32 SF, HEIGHT ≤ 6'-0\" ABOVE GRADE — SEE "
                 'DETAIL 3/C-8.0.',
                 'NO WALL SIGNS PROPOSED. ALL SIGNS SHALL BE PERMITTED SEPARATELY.',
                 "8'-0\" × 4'-0\" BASE, OUTSIDE BOTH SIGHT TRIANGLES BY %.1f'; A SIGN EASEMENT MAY BE "
                 'REQUIRED (§4.q)' % SIGN_CLEAR],
                size=S_SMALL, anchor='start', gap=1.3, bold_first=True, halo=True)
    q = min(SIGN_POLY, key=lambda p: sb._seg_pt(p, P_EYE, SIGHT_NE[-1]))
    dx, dy = SIGHT_NE[-1][0] - P_EYE[0], SIGHT_NE[-1][1] - P_EYE[1]
    ln2 = dx * dx + dy * dy
    t = ((q[0] - P_EYE[0]) * dx + (q[1] - P_EYE[1]) * dy) / ln2
    foot2 = (P_EYE[0] + t * dx, P_EYE[1] + t * dy)
    dim(c, q, foot2, "%.1f' CLEAR" % SIGN_CLEAR, off=0.0, side=1, size=S_SMALL, color=SGT, txt_at='end')

    # ------------------------------------------------- tracts, open space, existing
    c.text(40.0, -88.0, 'VILLAGE GREEN — COMMON OPEN SPACE, HOA-OWNED', size=S_PLAN, bold=True,
           fill='#2e5e1e', halo=True, anchor='start')
    c.text(40.0, -96.0, 'FRONT AMENITY TRACT %s SF — HOA MAINTAINED (CHECKLIST §4.o)'
           % format(AM['tract_sf'], ','), size=S_SMALL, fill='#2e5e1e', halo=True, anchor='start')
    c.text(14.0, -179.0, 'PRIVATE ENTRY DRIVE — 24\'-0" PAVEMENT, HOA-OWNED AND MAINTAINED; LABEL "PRIVATE" '
                         '(§4.s)', size=S_SMALL, anchor='start', halo=True, bold=True)
    c.text(14.0, -204.0, "BUFFER REDUCTION REQUESTED — 2.0' ALONG THE R/W", size=S_SMALL,
           anchor='start', fill=RED, halo=True, bold=True)
    c.text(14.0, -210.0, '(0.1 SF) AT THE SW CURB RETURN — SEE NOTE 6', size=S_SMALL,
           anchor='start', fill=RED, halo=True)
    p_buf = (front_u(SW_BUF_V), SW_BUF_V)
    dim(c, p_buf, RET_SW['A'], "2.0'", off=-6.0, side=1, size=S_DIM, color=RED, bold=True, txt_at='start')
    c.line(((p_buf[0] + RET_SW['A'][0]) / 2, (p_buf[1] + RET_SW['A'][1]) / 2), (12.0, -207.0),
           stroke=RED, stroke_width=0.4)
    st = sb.existing_polys()[0]
    c.line(sb.poly_centroid(st[1]), (218.0, -156.0), stroke=C['exist'], stroke_width=0.4)
    c.textlines(218.0, -156.0, ['EXISTING HOUSE AT 4541 ARCADO RD SW — TO BE REMOVED',
                                '%s ± SF, APPROXIMATE — LOCATE BY SURVEY (SEE C-1.1)'
                                % format(round(st[2], -1), ',.0f')],
                size=S_SMALL, anchor='end', gap=1.3, bold_first=True, fill=C['exist'], halo=True)
    c.text(95.0, -217.0, "EXISTING 12'-0\" DRIVE TO 4541 — TO BE REMOVED", size=S_SMALL, fill=C['exist'],
           halo=True, anchor='start')
    c.text(20.0, -224.0, "EX. 8-in SANITARY SEWER IN A 20'-0\" SANITARY SEWER EASEMENT — GWINNETT DWR "
                         '(WIDTH AND HOLDER: VERIFY)', size=S_SMALL, fill=C['sewer_txt'], halo=True,
           anchor='start')

    # ------------------------------------------------- adjoining property
    c.text(128.0, -237.0, 'LEGENDS AT PARKVIEW (PLAT 118/187) — 250 / 260 VILLAGE GREEN CT — ZONED R-1, '
                          'CITY OF LILBURN', size=S_SMALL, bold=True, fill='#555', halo=True, anchor='start')
    c.text(150.0, 4.0, '4531 ARCADO RD SW (PIN R6123 017) — ZONED R-1, CITY OF LILBURN', size=S_SMALL,
           bold=True, fill='#555', halo=True, anchor='start')


# ============================================================================ legend / tables / notes
LEGEND = [
    ('line', C['bnd'], 2.0, '', 'Property line / Arcado Rd R/W line'),
    ('rect', C['adj_fill'], 0, '', 'Adjoining parcel — zoned R-1 (Lilburn)'),
    ('line', C['rw'], 0.9, '', 'Opposite R/W line (R/W width varies)'),
    ('line', '#333', 0.6, '14 3 3 3', 'Existing road centreline'),
    ('rect', 'url(#dedhatch)', 0, '', "Potential R/W dedication (10'-0\" assumed)"),
    ('rect', 'url(#lshatch)', 0, '', "10'-0\" landscape strip + planting"),
    ('rect', 'url(#bufhatch)', 0, '', "20'-0\" undisturbed perimeter buffer"),
    ('line', '#c62828', 0.9, '12 4 3 4', "50'-0\" building setback from the R/W"),
    ('line', '#e08a8a', 0.7, '6 4', 'Setback line if the dedication is taken'),
    ('rect', C['pave'], 0, '', 'Proposed pavement (drive, lane, bays)'),
    ('rect', C['walk'], 0, '', "Proposed 5'-0\" concrete sidewalk"),
    ('rect', 'url(#dwarn)', 0, '', 'Curb ramp + detectable warning'),
    ('line', '#666', 0.5, '5 2', 'HOA tract line (amenity / lane / drive)'),
    ('rect', '#eef4e6', 0, '', 'Front amenity tract — common open space'),
    ('rect', '#cfe8bd', 0, '', 'Village green'),
    ('rect', '#f2c58a', 0, '', 'Clubhouse / mail kiosk (accessory)'),
    ('rect', '#e9e2d0', 0, '', "Pickleball pad 30'-0\" × 60'-0\""),
    ('rect', '#bcd7c2', 0, '', "Court surface 20'-0\" × 44'-0\""),
    ('fence', C['fence'], 0.8, '', "10'-0\" black chain-link fence"),
    ('line', '#555', 0.4, '', "Parking stall 9'-0\" × 18'-0\""),
    ('rect', 'url(#adahatch)', 0, '', 'Van-accessible space + access aisle'),
    ('rect', 'url(#sighthatch)', 0, '', 'Sight triangle — clear sight area'),
    ('line', C['sight'], 1.0, '', "Sight line — 390' ISD leg"),
    ('eye', C['sight'], 0, '', "Driver's eye / decision point"),
    ('dot2', C['dim'], 0, '', 'Curve point — PC / PRC / PT'),
    ('rect', '#333', 0, '', 'Monument entry sign (face ≤ 32 SF)'),
    ('rect', C['house'], 0, '', 'Proposed cottage, garage and porch'),
    ('line', C['sewer'], 0.9, '', 'Existing 8-in sanitary sewer + MH'),
    ('rect', 'url(#ssehatch)', 0, '', "Existing 20'-0\" sewer easement"),
    ('line', C['water'], 0.9, '9 3 2 3', 'Existing water main (Gwinnett DWR)'),
    ('rect', 'url(#exhatch)', 0, '', 'Existing building / drive — to be removed'),
]

ENTRY_TABLE = [
    ['Entrance on the R/W', "u −31.43, v −190.00 — SW third of the frontage; 192.68' from the NE front corner, "
                            "44.93' from the SW corner, along the R/W"],
    ['Entry drive', "24'-0\" pavement, private, two-way; 203.87 LF, R/W to the lane midline"],
    ['Curb returns', "NE R = 25'-0\"; SW R = 15'-0\", reduced from 25'-0\" to clear the buffer"],
    ['Access spacing', "251.2' to the C/L of Arcadia Pl along the Arcado Rd C/L (250.7' chord) "
                       'against ≈ 244 ft — VERIFY (Checklist §7.f)'],
    ['Sight distance', "390'-0\" required each way at 35 mph; drawn, NOT certified here (Checklist §7.j)"],
    ['Left-turn lane', 'Not warranted below 75 lots (41 proposed) — VERIFY with Gwinnett DOT'],
    ['Buffer reduction', "2.0' along the R/W (0.1 SF) at the SW curb return — §1003-4, Checklist §6.f"],
]

PARK_TABLE = [
    ['Required, 41 dwellings', '2 per dwelling unit, no maximum (Table 8.1) = 82 spaces'],
    ['Provided on lot', '164 — 2-car garage + 2-car driveway on every lot (Sheet C-2.1)'],
    ['Guest bay', "7 stalls at 9'-0\" × 18'-0\", 90° to the lane (Checklist §4.w)"],
    ['Mail-kiosk bay', "1 van-accessible 8'-0\" stall + 8'-0\" access aisle + R7-8 / R7-8P sign, "
                       "and 4 stalls at 9'-0\" × 18'-0\""],
    ['Accessible required', '1 of the 12 front-block spaces; 1 in 6 van-accessible (2010 ADA §208.2, '
                            '§502.2) — 1 provided; size and location to be confirmed by the Gwinnett '
                            'County Fire Marshal (Checklist §4.x)'],
    ['Drive aisle', "22'-0\" minimum two-way with 90° parking (Checklist §4.u) — 22'-0\" provided"],
]

NOTES = [
    'SCOPE AND STATUS. This sheet enlarges the frontage, entrance and front amenity block of Sheet C-2.0 at '
    '1" = 20\'. Coordinates are site-local (u, v) US survey feet from the Gwinnett GIS parcel fabric and '
    'data/layout.json. DRAFT, NOT SEALED: a Georgia RLS boundary and R/W survey, a PE sight-distance '
    'certificate and PE civil design are required and govern. Nothing here certifies compliance.',

    'RIGHT-OF-WAY AND DEDICATION. R/W WIDTH VARIES — 44-60 ft scaled between the two Gwinnett GIS R/W lines, '
    '27.89 ft from the entrance to the mapped centreline; scaled, not surveyed. A Gwinnett minor-collector '
    'section is wider, so a dedication is likely: the 10\'-0" strip is SHOWN HATCHED AS AN ASSUMPTION ONLY. If '
    'taken, the 50-ft setback line moves inboard 10 ft (dashed), the landscape strip moves with it and the '
    'monument sign, at 9.0 ft from the new R/W, must be re-set. Establish the R/W by survey and the Gwinnett '
    'DOT permit.',

    'INTERSECTION SIGHT DISTANCE. 390\'-0" required each way at 35 mph (Gwinnett UDO §900-40.4 Table 900.2; '
    'AASHTO case B1). Triangles are drawn from a decision point on the drive centreline 14.4 ft behind the '
    'edge of the travelled way, eye 3.50 ft, object 4.25 ft, to points 390 ft each way on the mapped '
    'centreline. Edge of travelled way ASSUMED 11\'-0" from the C/L — verify. THE AVAILABLE SIGHT DISTANCE IS '
    'NOT CERTIFIED HERE: the certificate is blank (Checklist §7.j, DR 9.7.4). Vertical (crest) sight distance '
    'must be field-measured too.',

    'CLEAR SIGHT AREA. Nothing between 3\'-0" and 15\'-0" above the roadway grade may stand in either triangle '
    '— no sign, wall, fence, berm, cabinet, parked vehicle or landscape planting (Checklist §6.j bars planting '
    '3-15 ft high within 20 ft of a R/W intersection). The monument sign is clear by %.1f ft at its nearest '
    'corner. Keeping the area clear is an HOA covenant obligation.',

    'ACCESS. One full-movement private entrance; no lot fronts Arcado Rd or takes a driveway from it. The '
    'entrance C/L is 251.2 ft from the C/L of Arcadia Pl along the Arcado Rd centreline (250.7 ft chord) '
    'against a collector spacing of about 244 ft — VERIFY with Gwinnett DOT. Arcadia Pl cannot be aligned '
    'with the drive: it meets Arcado Rd 61 ft NE of the NE front corner. Checklist §7.f (DR 9.7.5) offsets: '
    'no other access is mapped within 400 ft.',

    'BUFFER REDUCTION REQUESTED. With the SW curb return cut from R = 25\'-0" to R = 15\'-0", 2.0 ft of it '
    'measured along the R/W (0.1 SF of pavement) still lies inside the 20-ft perimeter buffer at the R/W '
    'corner. It is requested as a buffer reduction under Ord. 2023-603 §1003-4; Checklist §6.f allows drives '
    'and utilities to encroach up to 50 ft of width and no further without a ZBA variance. The letter of '
    'intent and the voluntary conditions must match.',

    'PRIVATE STREET AND PAVING. The entry drive and lane are private, HOA-owned and labelled "PRIVATE" per '
    'Checklist §4.s; all components must meet minimum public-street standards. Paving 4" GAB with 2" Type E or '
    'F asphalt minimum (§7.i), to be confirmed against the Lilburn Development Regulations and a Gwinnett Fire '
    'apparatus-load check. Materials and details on C-8.0 (§4.t).',

    'SIDEWALKS AND ACCESSIBLE ROUTE. A 5\'-0" concrete walk runs the full %.0f-LF frontage, shown 3\'-0" inside '
    'the R/W line; the final offset (2\'-0" min. behind back of curb, 6\'-0" with street trees) is set by the '
    'R/W survey and the DOT permit. It is carried through the drive at grade with a curb ramp and detectable '
    'warning each side (§5.d). A 5\'-0" walk on the NE side of the drive and lane links the clubhouse, kiosk '
    'and guest bay to the public walk (§4.z).',

    'LANDSCAPE. 10\'-0" landscape strip along the R/W: 1 tree + 1 shrub per 25 LF = 10 trees and 10 shrubs '
    'over 237.63 LF (§6.g, §6.j); parking-lot planting 1 tree per 7 spaces with every space within 60 ft of a '
    'trunk (§6.k); 5\'-0" landscape strip around every accessory structure (§6.l). The tree-protection, buffer '
    'and landscape plan must be sealed by a registered landscape architect, forester or arborist (§6.a) and is '
    'not part of this sheet.',

    'BUFFERS AND SETBACKS. 20\'-0" undisturbed perimeter buffer on the NE and SW lines (Table 4.1, R-2 '
    'abutting R-1, "all other allowed dwelling types"); §313(1) buffers supersede the minimum yards; none on '
    'the Arcado Rd frontage. Collector building setback 50\'-0": the clubhouse, the nearest structure, is '
    '%.1f ft from the R/W and %.1f ft from the NE line against a 5\'-0" accessory setback. Buffers in recorded '
    'easements (§4.j, §4.k, §4.l, §4.o).',

    'SIGNS. One ground-mounted monument entry sign, face not exceeding 32 SF and height not exceeding 6\'-0" '
    'above grade — see Detail 3/C-8.0 for the elevation and area computation. NO WALL SIGNS ARE PROPOSED on '
    'any dwelling, the clubhouse or any accessory structure. ALL SIGNS SHALL BE PERMITTED SEPARATELY (§4.q); '
    'a sign easement may be required. The sign regulations\' area, height, setback and illumination limits to '
    'be confirmed at the pre-application.',

    'MAIL AND FENCING. Cluster box units in a roofed 16\'-0" x 10\'-0" kiosk with four short-term spaces; the '
    'Lilburn Post Office Growth Manager confirms CBU type, count and the single street name used for house '
    'numbering (§4.r). The two pickleball pads are enclosed by a 10\'-0" high black PVC-coated chain-link '
    'fence (§4.n); VERIFY the residential fence-height limit for a 10-ft sport-court fence. No court lighting '
    '(voluntary condition 11).',

    'EXISTING CONDITIONS SHOWN. The house and drive at 4541 Arcado Rd SW are dashed and ARE TO BE REMOVED '
    '(C-1.1); the footprints are aerial-imagery approximations to be located by survey. The existing 8-in '
    'Gwinnett DWR gravity sewer and its 20-ft easement run inside the SW line through the buffer; the easement '
    'width and holder are from the 2025 hydrology sheet and are NOT surveyed. Georgia 811 locates (O.C.G.A. '
    '§25-9) are required before field work. Electric, gas, telecom and storm structures are NOT shown. The '
    'nearest existing fire hydrant is 61 ft from the front corner, NE of this sheet — see C-0.',

    'PERMITS STILL REQUIRED. Gwinnett DOT driveway / encroachment permit and sight-distance certification; '
    'Gwinnett DWR sewer capacity certification; City of Lilburn Land Disturbance Permit; §1106 site and design '
    'review; a separate sign permit.',
]


def legend(D, x, y, cols=2, w=205.0, rows=16, lead=9.2):
    D.stext(x, y, 'LEGEND — every symbol drawn on this sheet appears here', size=S_HEAD, bold=True)
    y0 = y + 12
    for i, (kind, col, wdt, dash, txt) in enumerate(LEGEND):
        cx = x + (i // rows) * w
        yy = y0 + (i % rows) * lead
        if kind == 'line':
            D.sline(cx, yy - 2.6, cx + 22, yy - 2.6, stroke=col, stroke_width=wdt, stroke_dasharray=dash)
        elif kind == 'fence':
            D.sline(cx, yy - 2.6, cx + 22, yy - 2.6, stroke=col, stroke_width=wdt)
            for k in (4, 11, 18):
                D.sline(cx + k, yy - 4.8, cx + k, yy - 0.4, stroke=col, stroke_width=0.6)
        elif kind == 'dot':
            D.scircle(cx + 11, yy - 2.6, 2.4, fill=col, stroke='#fff', stroke_width=0.5)
        elif kind == 'dot2':
            D.scircle(cx + 11, yy - 2.6, 2.9, fill='#fff', stroke=col, stroke_width=1.0)
            D.scircle(cx + 11, yy - 2.6, 1.2, fill=col, stroke='none')
        elif kind == 'eye':
            D.scircle(cx + 11, yy - 2.6, 3.4, fill='#fff', stroke=col, stroke_width=1.1)
            D.scircle(cx + 11, yy - 2.6, 1.5, fill=col, stroke='none')
        else:
            D.srect(cx, yy - 7.6, 22, 9.6, fill=col, stroke='#555', stroke_width=0.4)
        D.stext(cx + 26, yy, txt, size=7.0)
    return y0 + rows * lead + 4


def sight_diagram(D, x, y):
    """1" = 200' key diagram: the whole frontage, both 390-ft sight legs and the access spacing."""
    w2 = (WIN2[1] - WIN2[0]) * SCALE200
    h2 = (WIN2[3] - WIN2[2]) * SCALE200
    D.stext(x, y, 'SIGHT DISTANCE & ACCESS SPACING DIAGRAM', size=S_HEAD, bold=True)
    D.stext(x, y + 11, 'Both departure sight triangles at full length. Scale 1" = 200\' — NOT the scale '
                       'of the plan above.', size=7.0, fill='#444')
    y += 18
    sub = sb.Drawing(SCALE200, x, y, fs=1.0, win=WIN2)
    sub.clip_open(fill='#fff')
    sb.adjoiners(sub, labels=False, zoning=False)
    sb.arcado_row(sub, labels=False)
    for tri in (TRI_NE, TRI_SW):
        sub.poly(tri, fill='url(#sighthatch)', stroke=C['sight'], stroke_width=0.7)
    sub.pline([tuple(p) for p in ARCADIA_PATH], fill='none', stroke='#333', stroke_width=0.7,
              stroke_dasharray='10 3 2 3')
    sub.poly(sb.BOUNDARY, fill='none', stroke=C['bnd'], stroke_width=1.4)
    sub.pline(ENTRY_CL, fill='none', stroke='#444', stroke_width=0.9)
    sub.pline([tuple(p) for p in LANE['centerline']], fill='none', stroke='#444', stroke_width=0.7)
    sub.circle(P_EYE, 2.6, fill='#fff', stroke=C['sight'], stroke_width=1.0)
    dim(sub, P_EYE, SIGHT_NE[-1], "390'-0\" ISD", off=0.0, side=1, size=7.0, color=C['sight'], txt_at='mid')
    dim(sub, P_EYE, SIGHT_SW[-1], "390'-0\" ISD", off=0.0, side=-1, size=7.0, color=C['sight'], txt_at='mid')
    dim(sub, ENTRY_ON_CL, ARCADIA_CL, "251.2'", off=26.0, side=-1, size=7.0, color=C['match'], txt_at='mid')
    sub.circle(ARCADIA_CL, 2.4, fill=C['match'], stroke='#fff', stroke_width=0.6)
    sub.text(24.0, -120.0, 'SITE', size=8.0, bold=True, halo=True, rot=-81)
    sub.clip_close()
    D.add(sub.render())
    D.srect(x, y, w2, h2, fill='none', stroke='#000', stroke_width=0.9)
    tx = x + w2 + 8
    for k, (col, t) in enumerate([
            ('#000', 'A  C/L ARCADIA PLACE at Arcado Rd — local (u −12, v +61)'),
            ('#000', 'B  PROPOSED ENTRANCE C/L on the Arcado Rd C/L — (u −59, v −186)'),
            ('#000', 'A–B  251.2 ft along the Arcado Rd centreline (250.7 ft chord);'),
            ('#555', '     Gwinnett collector access spacing ≈ 244 ft — VERIFY'),
            ('#000', 'C  390\'-0" departure sight distance, LEFT (toward Arcadia Pl)'),
            ('#000', 'D  390\'-0" departure sight distance, RIGHT (toward Killian Hill Rd)'),
            ('#555', '     both legs lie on MAPPED Gwinnett GIS centreline — no projection'),
            ('#000', 'E  Driver\'s eye 14.4 ft behind the edge of the travelled way'),
            ('#555', '     eye height 3.50 ft; object height 4.25 ft (AASHTO case B1)'),
            ('#c62828', 'The available sight distance is NOT certified on this sheet —'),
            ('#c62828', 'see the blank engineer\'s certificate below (Checklist §7.j).')]):
        D.stext(tx, y + 10 + k * 10.4, t, size=7.0, fill=col, bold=(len(t) > 2 and t[1] == ' ' and t[0] in 'ABCDE'))
    for lab, p in (('A', ARCADIA_CL), ('B', ENTRY_ON_CL), ('C', SIGHT_NE[-1]), ('D', SIGHT_SW[-1]),
                   ('E', P_EYE)):
        D.scircle(sub.X(p[0]), sub.Y(p[1]), 5.2, fill='#fff', stroke='#000', stroke_width=0.7)
        D.stext(sub.X(p[0]), sub.Y(p[1]) + 2.6, lab, size=7.2, anchor='middle', bold=True)
    scalebar(D, tx + 4, y + 148, scale=SCALE200, step_ft=200, steps=3)
    sb.table(D, tx, y + 196, ['CURVE', 'RADIUS', 'Δ', 'LENGTH', 'TANGENT', 'FROM → TO'],
             [['1 (left)', "100'-0\"", '59.9°', "104.55'", "57.62'", 'PC 0+10.00 → PRC 1+14.55'],
              ['2 (right)', "100'-0\"", '51.2°', "89.33'", "47.89'", 'PRC 1+14.55 → PT 2+03.87']],
             size=7.0, rowh=9.4, widths=[44, 38, 28, 40, 40, 83],
             title='ENTRY DRIVE — HORIZONTAL CURVE DATA (DRAFT)')
    return y + h2 + 10


def certificate(D, x, y, w):
    """The blank sight-distance certificate for a Georgia registered professional engineer."""
    h = 128.0
    D.srect(x, y, w, h, fill='#fbfbfb', stroke='#000', stroke_width=1.0)
    D.srect(x, y, w, 15, fill='#e8e8e8', stroke='#000', stroke_width=1.0)
    D.stext(x + 5, y + 11, "ENGINEER'S CERTIFICATE — SIGHT DISTANCE  (BLANK — TO BE COMPLETED AND SEALED)",
            size=8.0, bold=True)
    yy = y + 25
    for t in ['City of Lilburn Site Development Plan Review Checklist §7.j; Gwinnett Dev. Regulations 9.7.4.',
              'To be completed, signed, dated and sealed across the seal by a Georgia registered professional',
              'engineer. NOT COMPLETED — this sheet makes no sight-distance claim.']:
        D.stext(x + 5, yy, t, size=7.0, fill='#444')
        yy += 8.6
    yy += 3
    for t in ['I certify that I have field-measured the intersection sight distance available at the entrance',
              "shown on this sheet, from a driver's eye height of 3.50 ft located 14.4 ft behind the edge of the",
              'travelled way to an object height of 4.25 ft, and that the available sight distance is:',
              '     LEFT (toward Arcadia Pl) _________ ft      RIGHT (toward Killian Hill Rd) _________ ft',
              '     REQUIRED _______ ft at _____ mph.   Vertical (crest) sight distance: YES __ NO __',
              '     Clearing required in the R/W or the landscape strip:  YES __   NO __']:
        D.stext(x + 5, yy, t, size=7.0)
        yy += 8.8
    D.stext(x + 5, yy + 3, 'Signature ______________  Printed ______________  GA P.E. No. ______  Date ______',
            size=7.0)
    D.srect(x + w - 74, y + h - 44, 66, 36, fill='#fff', stroke='#888', stroke_width=0.7,
            stroke_dasharray='4 3')
    D.stext(x + w - 41, y + h - 23, 'SEAL', size=7.4, anchor='middle', fill='#888')
    return y + h + 16


def tables(D, x, y, w):
    """Curve data, access data and parking data."""
    y = sb.table(D, x, y, ['ITEM', 'VALUE / BASIS'], ENTRY_TABLE, size=7.0, rowh=9.4,
                 widths=[100, w - 100], title='ENTRANCE AND ACCESS DATA (DRAFT — Checklist §4.p, §7.f, §7.j)') + 12
    y = sb.table(D, x, y, ['ITEM', 'REQUIRED / PROVIDED'], PARK_TABLE, size=7.0, rowh=9.4,
                 widths=[100, w - 100], title='PARKING AND ACCESSIBILITY (Checklist §4.v, §4.w, §4.x)')
    return y


def notes_strip(D, x0, y0, x1, y1, cols=6, gap=7.0, size=7.0, lead=7.7, note_gap=2.6):
    """General notes flowed across `cols` columns. Returns the number of lines that did not fit."""
    D.stext(x0, y0, 'GENERAL NOTES — SHEET C-2.3', size=S_HEAD, bold=True)
    D.stext(x0 + 186, y0, 'Ordinance citations: City of Lilburn Zoning Ordinance, Ord. 2023-603. '
                          '"Checklist §" = City of Lilburn Site Development Plan Review Checklist. Every '
                          'statement of conformity reads "appears consistent with".', size=7.0, fill='#444')
    w = (x1 - x0 - gap * (cols - 1)) / cols
    chars = max(int(w / (0.56 * size)), 20)
    items = []
    for i, n in enumerate(NOTES, 1):
        body = (n % ((SIGN_CLEAR,) if '%.1f ft at its nearest' in n else
                     (WALK_LEN,) if '-LF frontage' in n else
                     (CLUB_RW, CLUB_TO_NE_LINE))) if '%' in n else n
        wrapped = sb.wrap('%d. %s' % (i, body), chars)
        items.append([(wrapped[0], True)] + [('    ' + t, False) for t in wrapped[1:]])
    top, bot = y0 + 14, y1
    col, y = 0, top
    over = 0
    for blk in items:
        if y + 2 * lead > bot and col < cols - 1:
            col, y = col + 1, top            # never leave a note's first line alone at a column foot
        for t, bold in blk:
            if y + lead > bot:
                if col >= cols - 1:
                    over += 1
                    continue
                col, y = col + 1, top
            D.stext(x0 + col * (w + gap), y + size, t, size=size, bold=bold)
            y += lead
        y += note_gap
    return over


# ============================================================================ build
def build():
    scale_note = 'Scale 1" = 20\' (ARCH C 24 × 18 in)'
    D = sheet_c('ENTRY, FRONTAGE & AMENITY ENLARGEMENT', 'C-2.3',
                'Enlargement of Sheet C-2.0 at the Arcado Rd frontage — right-of-way and dedication, sight '
                'triangles and ISD lines, curb returns and curve data, buffers, landscape strip, frontage '
                'sidewalk, clubhouse, courts, parking, sign, mail kiosk',
                scale_note,
                ['Entry geometry, sight triangles and dimensions are DRAFT,',
                 'from the Gwinnett GIS parcel fabric and data/layout.json.',
                 'A sealed RLS boundary and right-of-way survey, a PE',
                 'sight-distance certificate (blank at right) and a Gwinnett',
                 'County DOT driveway permit are required and govern.'])

    # ---------------------------------------------------------------- plan
    D.clip_open(fill='#fff')
    plan(D)
    annotate(D)
    D.clip_close()
    px, py, pw, ph = D.box()
    north_arrow(D, px + pw - 62, py + 58, r=26)
    D.srect(px + 8, py + ph - 48, 336, 42, fill='#fff', fill_opacity='0.86', stroke='#999',
            stroke_width=0.4)
    scalebar(D, px + 20, py + ph - 30, scale=SCALE20, step_ft=20, steps=4)
    D.stext(px + pw, py - 26, 'DRAFT — NOT SEALED    ·    SEE SHEET C-2.0 FOR THE WHOLE SITE AND C-2.1 '
                              'FOR THE LOTS', size=10, bold=True, fill='#7b1fa2', anchor='end')

    # ---------------------------------------------------------------- right-hand band
    x, w = BAND_X0, BAND_X1 - BAND_X0
    y = legend(D, x, PLAN_Y0 + 4)
    y = sight_diagram(D, x, y + 8)
    y = certificate(D, x, y, w)
    y = tables(D, x, y, w)

    # ---------------------------------------------------------------- general notes
    over = notes_strip(D, PLAN_X0, NOTE_Y0, BAND_X1, DISC_Y - 6)
    return D, y, over


if __name__ == '__main__':
    D, band_bottom, over = build()
    svg, png = sb.save(D, 'entry-enlargement', dpi=150)
    print('wrote %s\n      %s' % (svg, png))
    print('  entrance   : R/W point (u %.2f, v %.2f); PC %.2f  PRC %.2f  PT %.2f; drive %.2f LF'
          % (U_ENTRY, ENTRY_V, STA_PC, STA_PRC, STA_PT, STA_PT))
    print('  curves     : R = %.0f, D1 = %.1f deg (L %.2f, T %.2f), D2 = %.1f deg (L %.2f, T %.2f)'
          % (ENTRY_R, math.degrees(DEFL1), ARC1, TAN1, math.degrees(DEFL2), ARC2, TAN2))
    print('  returns    : NE R = %.0f (tangent on the R/W at v %.2f), SW R = %.0f (v %.2f)'
          % (RET_R_NE, RET_NE['A'][1], RET_R_SW, RET_SW['A'][1]))
    print('  buffer     : SW inner edge v = %.2f -> encroachment %.2f ft (layout.json %.1f ft, %.1f sf)'
          % (SW_BUF_V, SW_ENCROACH, MET['sw_curb_return_buffer_encroachment_ft'],
             MET['sw_curb_return_buffer_encroachment_sf']))
    print('  sight      : ISD %.0f ft each way; eye at (u %.2f, v %.2f); NE leg ends (u %.1f, v %.1f), '
          'SW leg ends (u %.1f, v %.1f); projection beyond mapped C/L: %.1f / %.1f ft'
          % (ISD_FT, P_EYE[0], P_EYE[1], SIGHT_NE[-1][0], SIGHT_NE[-1][1], SIGHT_SW[-1][0],
             SIGHT_SW[-1][1], PROJ_NE, PROJ_SW))
    print('  clearances : monument sign %.1f ft from the R/W, %.1f ft clear of the sight triangle; '
          'clubhouse %.1f ft from the R/W, %.1f ft from the NE line'
          % (SIGN_RW, SIGN_CLEAR, CLUB_RW, CLUB_TO_NE_LINE))
    print('  flags      : pickleball pad %.1f ft from the 20-ft buffer (>= 5 ft offered in docs/12)'
          % PAD_TO_BUFFER)
    print('  band ends at y = %.0f (limit %.0f); notes overflow: %d lines' % (band_bottom, BAND_Y1, over))
