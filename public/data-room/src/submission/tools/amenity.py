#!/usr/bin/env python3
"""Sheet A-3 — CLUBHOUSE, MAIL KIOSK AND ENTRY MONUMENT SIGN — plans, elevations and details.

The Cottages at Arcado Springs (R-1 -> R-2 rezoning, City of Lilburn, GA).

    python3 tools/amenity.py            ->  drawings/amenity-sheet.svg + .png

WHY THIS SHEET EXISTS
    City of Lilburn 2026 Application Instructions item (11), "Architectural Renderings and Elevations":
    "An architectural rendering or elevation of each side of the structure visible from the street shall be
     submitted. The drawings shall be to scale or in proper perspective and shall include the color and
     materials of all structures and roofing and location and size of wall signs."
    Sheets A-2.1 / A-2.2 / A-2.3 (tools/elevations.py) cover the two dwelling plans. This sheet covers the
    three NON-DWELLING structures: the clubhouse, the mail kiosk and the monument entry sign -- and the sign
    is the only sign in the project, so the "wall signs" statement is made here.

WHERE THE GEOMETRY COMES FROM  (nothing is hand-placed; every position and size is read at run time)
    data/layout.json  amenity.clubhouse      the 60'-0" x 40'-0" = 2,400 SF footprint and its position
                      amenity.mail_kiosk     the 16'-0" x 10'-0" CBU shelter
                      amenity.kiosk_stalls   the four 9'-0" x 18'-0" short-term spaces beside it
                      amenity.entry_sign     the 8'-0" x 4'-0" monument footprint
                      lane.entrance / lane.arcado_centerline / boundary_ring
                                             the Arcado Rd R/W, the drive centreline and the departure
                                             sight triangle used for the sign's clearance dimension
    The room plan, the roof and every height are derived here from that footprint and are printed by the
    script; the elevation painting helpers (siding, stone, shingles, openings, porch piers) are imported
    from tools/elevations.py so this sheet cannot drift from sheets A-2.x.

ILLUSTRATIVE - NOT FOR CONSTRUCTION.  DRAFT - to be superseded by sealed drawings (GA-registered architect).
"""
import json, math, os, re, sys, textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import floorplans as fp                                            # noqa: E402  (house drawing standard)
import elevations as ev                                            # noqa: E402  (elevation painting + keys)

ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data')
DRAW = os.path.join(ROOT, 'drawings')
os.makedirs(DRAW, exist_ok=True)

fti, esc = fp.fti, fp.esc
DISCLAIMER, MARKER = fp.DISCLAIMER, fp.MARKER

SHEET_IN = (24.0, 18.0)          # ARCH C landscape, as sheets A-1 / A-2.x
PT_PER_FT = 13.5                 # sheet unit = 1 ft at 3/16" = 1'-0"  (0.1875 in x 72 pt)
WF, HF = SHEET_IN[0] * 72 / PT_PER_FT, SHEET_IN[1] * 72 / PT_PER_FT       # 128 x 96 sheet units

# scale factors: sheet units per drawing foot  (0.1875 in per sheet unit)
K18 = (1.0 / 8.0) / 0.1875       # 1/8"  = 1'-0"   -> 0.6667
K14 = (1.0 / 4.0) / 0.1875       # 1/4"  = 1'-0"   -> 1.3333
K12 = (1.0 / 2.0) / 0.1875       # 1/2"  = 1'-0"   -> 2.6667
K38 = (3.0 / 8.0) / 0.1875       # 3/8"  = 1'-0"   -> 2.0000
K80 = (1.0 / 80.0) / 0.1875      # 1"    = 80'-0"  -> 0.0667  (key plan)

# ------------------------------------------------------------------ site data
LAYOUT = json.load(open(os.path.join(DATA, 'layout.json')))
AM = LAYOUT['amenity']
LANE = LAYOUT['lane']
MET = LAYOUT['metrics']

def rect_of(poly):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    return (min(xs), min(ys), max(xs), max(ys))

CLUB_R = rect_of(AM['clubhouse'])                     # (u0, v0, u1, v1) local feet
KIOSK_R = rect_of(AM['mail_kiosk'])
SIGN_R = rect_of(AM['entry_sign'])
STALLS = [rect_of(s) for s in AM['kiosk_stalls']]
CLUB_L = CLUB_R[2] - CLUB_R[0]                        # 60'-0" along u (SE -> NW)
CLUB_W = CLUB_R[3] - CLUB_R[1]                        # 40'-0" across v (SW lane -> NE)
CLUB_SF = CLUB_L * CLUB_W
KIOSK_L = KIOSK_R[2] - KIOSK_R[0]
KIOSK_W = KIOSK_R[3] - KIOSK_R[1]
SIGN_L = SIGN_R[2] - SIGN_R[0]
SIGN_W = SIGN_R[3] - SIGN_R[1]

def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])

def seg_pt_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))

def poly_line_dist(poly, line):
    return min(seg_pt_dist(p, line[i], line[i + 1]) for p in poly for i in range(len(line) - 1))

# Arcado Rd R/W = the front run of the boundary, (0,0) -> (-36, -234.7)
_ring = [tuple(p) for p in LAYOUT['boundary_ring']]
_start = min(range(len(_ring)), key=lambda i: abs(_ring[i][0]) + abs(_ring[i][1]))
_min_u = min(p[0] for p in _ring)                       # the front SW corner, (-36.0, -234.7)
RW = []
i = _start
while True:
    RW.append(_ring[i])
    if abs(_ring[i][0] - _min_u) < 0.05 and len(RW) > 1:
        break
    i = (i + 1) % len(_ring)
    if len(RW) > len(_ring):
        raise SystemExit('could not trace the Arcado Rd R/W run of the boundary ring')

NE_LINE = sorted([p for p in _ring if p[1] > -30.0])           # the NE property line (v ~ 0 to +9)
def ne_v(u):
    for a, b in zip(NE_LINE, NE_LINE[1:]):
        if a[0] <= u <= b[0]:
            t = (u - a[0]) / (b[0] - a[0]); return a[1] + t * (b[1] - a[1])
    return NE_LINE[-1][1]

CLUB_TO_RW = poly_line_dist(AM['clubhouse'], RW)                       # perpendicular, ft
CLUB_TO_NE = ne_v((CLUB_R[0] + CLUB_R[2]) / 2.0) - CLUB_R[3]           # to the NE property line
CLUB_TO_BUF = CLUB_TO_NE - LAYOUT['buffers']['perimeter_buffer_ft']    # clear of the 20-ft buffer band
SIGN_TO_RW = poly_line_dist(AM['entry_sign'], RW)

# lane centreline v at a given u (for the kiosk / clubhouse offsets)
def lane_v(u):
    cl = LANE['centerline']
    for a, b in zip(cl, cl[1:]):
        if a[0] <= u <= b[0]:
            t = (u - a[0]) / (b[0] - a[0]); return a[1] + t * (b[1] - a[1])
    return cl[-1][1]

PAVE_W = LANE['pavement_width_ft']
CLUB_TO_LANE = CLUB_R[1] - (lane_v((CLUB_R[0] + CLUB_R[2]) / 2.0) + PAVE_W / 2.0)   # face to pavement edge
KIOSK_TO_LANE = KIOSK_R[1] - (lane_v((KIOSK_R[0] + KIOSK_R[2]) / 2.0) + PAVE_W / 2.0)
STALL_W = STALLS[0][2] - STALLS[0][0]
STALL_D = STALLS[0][3] - STALLS[0][1]
STALL_GAP = KIOSK_R[0] - max(s[2] for s in STALLS)                      # walk between the bay and the slab

# ---- departure sight triangle (Gwinnett UDO 900-40 Table 900.2: ISD 390 ft at 35 mph; AASHTO Case B1)
ISD_FT = 390.0
ENT = LANE['entrance']
P_RW = (ENT['u_rw'], ENT['v_rw'])                       # drive centreline at the R/W
P_CL = tuple(ENT['entrance_cl_on_arcado_cl'])           # drive centreline at the Arcado Rd centreline
ACL = [tuple(p) for p in LANE['arcado_centerline']]
_S = [0.0]
for a, b in zip(ACL, ACL[1:]):
    _S.append(_S[-1] + dist(a, b))

def acl_at(s):
    if s <= 0:
        a, b = ACL[0], ACL[1]; t = s / dist(a, b)
    elif s >= _S[-1]:
        a, b = ACL[-2], ACL[-1]; t = 1 + (s - _S[-1]) / dist(a, b)
    else:
        for i in range(len(_S) - 1):
            if _S[i] <= s <= _S[i + 1]:
                a, b = ACL[i], ACL[i + 1]; t = (s - _S[i]) / (_S[i + 1] - _S[i]); break
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))

def acl_station(p):
    best = (1e9, 0.0)
    for i in range(len(ACL) - 1):
        a, b = ACL[i], ACL[i + 1]; dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
        q = (a[0] + t * dx, a[1] + t * dy); dd = dist(p, q)
        if dd < best[0]:
            best = (dd, _S[i] + t * math.hypot(dx, dy))
    return best[1]

RW_TO_CL = dist(P_RW, P_CL)                              # 27.8 ft: R/W line to the Arcado Rd centreline
LANE_HALF = 11.0                                         # half of a 22-ft travelled way -- VERIFY by survey
_dir = ((P_RW[0] - P_CL[0]) / RW_TO_CL, (P_RW[1] - P_CL[1]) / RW_TO_CL)     # from the road toward the site
EDGE = (P_CL[0] + _dir[0] * LANE_HALF, P_CL[1] + _dir[1] * LANE_HALF)       # near edge of travelled way
DRIVER = (EDGE[0] + _dir[0] * 14.5, EDGE[1] + _dir[1] * 14.5)               # AASHTO decision point, 14.5 ft
_s0 = acl_station(P_CL)
SIGHT_NE = acl_at(_s0 - ISD_FT)
SIGHT_SW = acl_at(_s0 + ISD_FT)

def side_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    return ((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / L

def in_tri(p, a, b, c):
    s = [side_dist(p, a, b), side_dist(p, b, c), side_dist(p, c, a)]
    return all(v >= -1e-9 for v in s) or all(v <= 1e-9 for v in s)

SIGN_PTS = [tuple(p) for p in AM['entry_sign']]
SIGHT_CLEAR = min(min(abs(side_dist(p, DRIVER, SIGHT_NE)) for p in SIGN_PTS),
                  min(abs(side_dist(p, DRIVER, SIGHT_SW)) for p in SIGN_PTS))
SIGN_IN_TRI = any(in_tri(p, DRIVER, SIGHT_NE, SIGHT_SW) for p in SIGN_PTS)
SIGN_BEHIND = min(((p[0] - DRIVER[0]) * _dir[0] + (p[1] - DRIVER[1]) * _dir[1]) for p in SIGN_PTS)

# axis bearings (FACTS 1): +u = N 28 deg 43' W, +v = perpendicular toward the NE line
U_BEARING_DEG = 28.72
NORTH_FROM_U_DEG = U_BEARING_DEG          # north lies this many degrees CCW... see note below

# ------------------------------------------------------------------ clubhouse design (derived here)
# Local clubhouse frame, to match the elevation-engine view convention of tools/elevations.py:
#   X = across the building, 0 at the SW (private-lane) wall  -> CLUB_W  (v direction)
#   Y = along the building,  0 at the SE (village-green) end  -> CLUB_L  (u direction)
#   'front' = SE (village green, covered porch)   'rear' = NW
#   'left'  = SW (private lane)                   'right' = NE (20-ft buffer side)
PORCH_D = 10.0                     # covered porch depth, recessed under the main roof
PORCH_POSTS = (1.0, 10.5, 20.0, 29.5, 39.0)   # across the gable end, X
PORCH_SIDE_POSTS = (1.0, 5.5)                 # on the two side eave lines, Y
T = 0.5                            # exterior wall thickness (2x6 + sheathing/siding)
P = 0.5                            # partition thickness (plumbing/assembly walls)
PLATE = 10.0                       # top of wall plate above finished floor
HEEL = 10.0 / 12.0                 # raised-heel truss
PITCH = (6, 12)                    # main gable (see note 9: 8:12 over a 40-ft span breaks the 24-ft cap)
OH_EAVE = 1.0                      # roof overhang at the eaves
OH_RAKE = 1.0                      # roof overhang at the gable rakes
FF = ev.FF                         # 8 in finished floor above finished grade (zero-step entry)
BEAM = ev.BEAM

CL_X0, CL_X1 = 0.0, CLUB_W
CL_Y0, CL_Y1 = 0.0, CLUB_L
ENC_Y0 = PORCH_D                                     # front wall of the enclosure
SPAN = CLUB_W                                        # gable span, eave plate to eave plate
EAVE_AFF = PLATE + HEEL
RIDGE_AFF = EAVE_AFF + (SPAN / 2.0) * PITCH[0] / float(PITCH[1])
EAVE_AG = FF + EAVE_AFF
RIDGE_AG = FF + RIDGE_AFF
CAP_RIDGE = ev.CAP_RIDGE                             # 24'-0" voluntary condition
DISTRICT_MAX = ev.DISTRICT_MAX                       # 40'-0", Ord. 2023-603 Table 4.1 (R-2)

BAND = 18.5                                          # NW service band depth
SUPP = 13.0                                          # NE support band width
LOBBY_L = 11.5
CORR = 4.5
XB = CL_X1 - T - SUPP - P                            # great room / support band partition (x face)
YB = CL_Y1 - T - BAND - P                            # great room / NW band partition (y face)

def room(nm, x0, y0, x1, y1, sub=''):
    return {'name': nm, 'r': (x0, y0, x1, y1), 'sub': sub,
            'w': x1 - x0, 'd': y1 - y0, 'sf': (x1 - x0) * (y1 - y0)}

_x_i0, _x_i1 = CL_X0 + T, CL_X1 - T                  # 0.5 .. 39.5
_y_i0, _y_i1 = ENC_Y0 + T, CL_Y1 - T                 # 10.5 .. 59.5
_rr_y = YB                                            # restrooms/corridor run to the NW partition
ROOMS = [
    room('GREAT ROOM / GATHERING', _x_i0, _y_i0, XB, _rr_y, 'assembly, unconcentrated (tables and chairs)'),
    room('LOBBY / VESTIBULE', XB + P, _y_i0, _x_i1, _y_i0 + LOBBY_L, 'main entry from the covered porch'),
    room('CORRIDOR', XB + P, _y_i0 + LOBBY_L + P, XB + P + CORR, _rr_y, '4\'-6" clear'),
    room('RESTROOM A', XB + P + CORR + P, _y_i0 + LOBBY_L + P, _x_i1,
         (_y_i0 + LOBBY_L + P + _rr_y - P / 2.0) / 2.0, 'single-user, accessible'),
    room('RESTROOM B', XB + P + CORR + P, (_y_i0 + LOBBY_L + P + _rr_y + P / 2.0) / 2.0, _x_i1, _rr_y,
         'single-user, accessible'),
    room('CATERING KITCHEN', _x_i0, YB + P, 14.0, _y_i1, 'warming / serving, no grease-producing cooking'),
    room('STORAGE', 14.0 + P, YB + P, 20.5, _y_i1, 'tables, chairs, HOA records'),
    room('FITNESS ROOM', 20.5 + P, YB + P, 35.5, _y_i1, 'exercise machines'),
    room('MECH / FIRE RISER', 35.5 + P, YB + P, _x_i1, _y_i1, 'NFPA 13 riser, WH, air handlers'),
]
NET_SF = sum(r['sf'] for r in ROOMS)
ENCLOSED_SF = CLUB_W * (CLUB_L - PORCH_D)
PORCH_SF = CLUB_W * PORCH_D

# IBC 2024 (GA 2026) Table 1004.5 occupant-load factors (net where noted)
OCC_ROWS = [
    ('GREAT ROOM / GATHERING', ROOMS[0]['sf'], 15, 'assembly, unconcentrated (net)'),
    ('LOBBY / VESTIBULE', ROOMS[1]['sf'], 15, 'assembly, unconcentrated (net)'),
    ('FITNESS ROOM', ROOMS[7]['sf'], 50, 'exercise room (gross)'),
    ('CATERING KITCHEN', ROOMS[5]['sf'], 200, 'commercial kitchen (gross)'),
    ('STORAGE', ROOMS[6]['sf'], 300, 'storage (gross)'),
    ('MECH / FIRE RISER', ROOMS[8]['sf'], 300, 'mechanical (gross)'),
]
OCC = sum(int(math.ceil(a / f)) for _n, a, f, _b in OCC_ROWS)
DIAG = math.hypot(ENCLOSED_SF / CLUB_W, CLUB_W)      # diagonal of the enclosed rectangle
SEP_REQ = DIAG / 3.0                                 # sprinklered: 1/3 diagonal (IBC 1007.1.1 Exc. 2)

# openings: (view, position along that wall in the clubhouse frame, kind, width, height, sill)
W_H, W_SILL = 5.0, 2.5
DR_H = 6.8
OPEN = [
    # front (SE) wall = the recessed wall at Y = ENC_Y0, positions are X (set clear of the porch posts)
    ('front', 5.0, 'window', 4.0, W_H, W_SILL), ('front', 14.0, 'french', 6.0, DR_H, 0.0),
    ('front', 23.0, 'window', 4.0, W_H, W_SILL),
    ('front', 27.5, 'window', 3.0, W_H, W_SILL), ('front', 33.5, 'french', 6.0, DR_H, 0.0),
    # left (SW / private lane) wall at X = 0, positions are Y
    ('left', 14.0, 'window', 4.0, W_H, W_SILL), ('left', 20.0, 'french', 6.0, DR_H, 0.0),
    ('left', 26.0, 'window', 4.0, W_H, W_SILL), ('left', 31.0, 'window', 4.0, W_H, W_SILL),
    ('left', 36.0, 'window', 4.0, W_H, W_SILL),
    ('left', 46.0, 'window', 3.0, W_H, W_SILL), ('left', 52.0, 'window', 3.0, W_H, W_SILL),
    # right (NE / buffer side) wall at X = CLUB_W, positions are Y
    ('right', 14.0, 'window', 3.0, W_H, W_SILL), ('right', 18.5, 'window', 3.0, W_H, W_SILL),
    ('right', 27.0, 'window', 2.5, 2.5, 5.0), ('right', 36.0, 'window', 2.5, 2.5, 5.0),
    ('right', 50.0, 'door', 3.0, DR_H, 0.0),
    # rear (NW) wall at Y = CLUB_L, positions are X
    ('rear', 7.0, 'door', 3.0, DR_H, 0.0), ('rear', 11.0, 'window', 3.0, W_H, W_SILL),
    ('rear', 24.0, 'window', 3.0, W_H, W_SILL), ('rear', 28.0, 'window', 3.0, W_H, W_SILL),
    ('rear', 32.0, 'window', 3.0, W_H, W_SILL),
]

# cross gable over the great room on the private-lane (southwest) side: it breaks the 60-ft roof plane
# and lights the gathering room. Its span is set so the secondary ridge dies into the main roof well
# below the main ridge.
XG_W = 20.0                                  # width of the cross gable, measured along Y
XG_C = 25.0                                  # its centreline, Y
XG_RIDGE_AFF = EAVE_AFF + (XG_W / 2.0) * PITCH[0] / float(PITCH[1])
XG_DIE = (XG_RIDGE_AFF - EAVE_AFF) / (PITCH[0] / float(PITCH[1]))     # X where it meets the main roof

# the three exits that serve the assembly areas, in the (X, Y) clubhouse frame
EXITS = [(at, ENC_Y0) for v, at, kind, _w, _h, _s in OPEN if v == 'front' and kind == 'french'] + \
        [(0.0, at) for v, at, kind, _w, _h, _s in OPEN if v == 'left' and kind == 'french']
EXIT_SEP = max(math.hypot(a[0] - b[0], a[1] - b[1]) for a in EXITS for b in EXITS)

# ------------------------------------------------------------------ mail kiosk design
CBU_N = 3                            # USPS-approved 16-compartment CBUs
CBU_COMP, CBU_PARCEL = 16, 2         # tenant compartments / parcel lockers per unit -- VERIFY with USPS
CBU_W, CBU_D = 2.5, 1.67             # approximate cabinet footprint -- VERIFY the approved model
DU = MET['lots']
K_PLATE = 8.83                       # top of the porch beam / eave plate above the slab
K_HEEL = 0.42
K_PITCH = (4, 12)                    # hip, subordinate to the cottages' 8:12 gable
K_OH = 1.0
K_SLAB = 0.33                        # slab above finished grade (flush walk, 1:20 max)
K_EAVE_AFF = K_PLATE + K_HEEL
K_RIDGE_AFF = K_EAVE_AFF + ((KIOSK_W + 2 * K_OH) / 2.0) * K_PITCH[0] / float(K_PITCH[1])
K_RIDGE_AG = K_SLAB + K_RIDGE_AFF

# ------------------------------------------------------------------ monument sign design
SG_LEN = SIGN_L                      # 8'-0" overall face length, from layout.json
SG_H = 3.75                          # overall height above finished grade (cap included)
SG_CAP = 0.33                        # cast-stone cap
SG_TH = 1.33                         # wall thickness (8-in CMU core + veneer both faces)
SG_WING = 1.33                       # masonry wing / planter return at each end
SG_FTG = 1.5                         # footing depth below grade
SG_FACE_SF = SG_LEN * SG_H           # the whole structure face, the most conservative measurement
SG_PANEL = (6.0, 1.75)               # cast-stone sign panel
SG_PANEL_SF = SG_PANEL[0] * SG_PANEL[1]
SG_MAX_SF, SG_MAX_H = 32.0, 6.0      # the self-imposed limits (see the VERIFY note on the sheet)

# ------------------------------------------------------------------ drawing helpers
SCHEME = dict(ev.SCHEMES['1'])       # Scheme 1 "Warm White" for all three non-dwelling structures
SCHEME['door'] = '#3B3F44'           # deep charcoal per docs/12 09 91 13 Scheme 1
SCHEME_NAME = 'SCHEME 1 - WARM WHITE'


def sub(k):
    """A canvas drawn in real feet; grade/origin at y = 0, y flipped by the placing transform."""
    c = fp.Canvas(ymax=0.0)
    c.LW = 0.03
    c.k = k
    return c


def tx(c, x, y, s, size=0.42, **kw):
    """Text sized in SHEET units on a canvas that will be scaled by c.k."""
    c.text(x, y, s, size=size / c.k, **kw)


def _restroke(svg, f):
    if abs(f - 1.0) < 1e-9:
        return svg
    return re.sub(r'stroke-width="([0-9.]+)"',
                  lambda m: 'stroke-width="%.5f"' % (float(m.group(1)) * f), svg)


def place(sheet, g, x, y, k, clip=None):
    """Put a sub-canvas group on the sheet with its origin at sheet point (x, y)."""
    body = '<g transform="translate(%.3f %.3f) scale(%.5f)">%s</g>' % (x, HF - y, k, _restroke(g, 1.0 / k))
    if clip:
        body = '<g clip-path="url(#%s)">%s</g>' % (clip, body)
    sheet.add(body)


def dim_h(c, y, x0, x1, label, size=0.34, tick=0.25, off=0.42, above=False):
    c.line(x0, y, x1, y, lw=0.022)
    for x in (x0, x1):
        c.line(x - tick * 0.7, y - tick, x + tick * 0.7, y + tick, lw=0.022)
    tx(c, (x0 + x1) / 2.0, y + (off / c.k if above else -off / c.k), label, size=size)


def dim_chain(c, y, stations, size=0.34, tick=0.25, off=0.42):
    """One horizontal dimension line with ticks at every station and a label in each bay."""
    c.line(stations[0], y, stations[-1], y, lw=0.022)
    for x in stations:
        c.line(x - tick * 0.7, y - tick, x + tick * 0.7, y + tick, lw=0.022)
    for a, b in zip(stations, stations[1:]):
        tx(c, (a + b) / 2.0, y - off / c.k, fti(b - a), size=size)


def dim_v(c, x, y0, y1, label, size=0.34, tick=0.25, off=0.32):
    c.line(x, y0, x, y1, lw=0.022)
    for y in (y0, y1):
        c.line(x - tick, y - tick * 0.7, x + tick, y + tick * 0.7, lw=0.022)
    tx(c, x - off / c.k, (y0 + y1) / 2.0, label, size=size, rot=-90)


def scalebar(c, x, y, total_ft, step_ft, label):
    """Graphic scale in drawing feet, drawn on a sub-canvas."""
    n = int(round(total_ft / step_ft))
    h = 0.5 / c.k
    for i in range(n):
        c.rect((x + i * step_ft, y, x + (i + 1) * step_ft, y + h),
               fill='#111' if i % 2 == 0 else '#fff', lw=0.02)
    for i in range(n + 1):
        tx(c, x + i * step_ft, y - 0.55 / c.k, str(int(i * step_ft)), size=0.32)
    tx(c, x + n * step_ft / 2.0, y + h + 0.5 / c.k, label, size=0.36, weight='bold')


def north_arrow(c, x, y, r, up_is='+v'):
    """North arrow. +u bears N 28 deg 43' W and +v bears N 61 deg 17' E (FACTS 1), so with +u to the
    right and +v up, north is 28.72 deg above the +x axis."""
    a = math.radians(U_BEARING_DEG) if up_is == '+v' else math.radians(90.0 - U_BEARING_DEG)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    c.poly([(x + dx * r, y + dy * r), (x + px * r * 0.30, y + py * r * 0.30),
            (x - dx * r * 0.35, y - dy * r * 0.35), (x - px * r * 0.30, y - py * r * 0.30)],
           fill='#111', stroke='#111', lw=0.02)
    tx(c, x + dx * (r + 0.9 / c.k), y + dy * (r + 0.9 / c.k), 'N', size=0.5, weight='bold')


def notes_block(c, x, y, title, items, w, size=0.4, lead=0.62, numbered=True, gap=0.18):
    if title:
        c.text(x, y, title, size=0.58, weight='bold', anchor='start')
        y -= 1.0
    ch = max(24, int(w / (0.5 * size)))
    for i, n in enumerate(items, 1):
        bold = n.startswith('**')
        n = n.replace('**', '')
        for j, ln in enumerate(textwrap.wrap(n, ch)):
            pre = ('%d.  ' % i if numbered else '') if j == 0 else ('    ' if numbered else '')
            c.text(x, y, pre + ln, size=size, anchor='start', weight='bold' if bold else 'normal')
            y -= lead
        y -= gap
    return y


# ============================================================================ CLUBHOUSE PLAN
def wall(c, x0, y0, x1, y1, ext=True):
    c.rect((x0, y0, x1, y1), fill='#2b2b2b' if ext else '#5a5a5a', stroke='none')


def punch(c, x0, y0, x1, y1):
    c.rect((x0, y0, x1, y1), fill='#ffffff', stroke='none')


def swing(c, hx, hy, w, ang0, ang1, dx, dy):
    """Door leaf from the hinge (hx, hy) plus its swing arc."""
    c.line(hx, hy, hx + dx * w, hy + dy * w, lw=0.05)
    c.arc(hx, hy, w, ang0, ang1, lw=0.02)


def door_in_wall(c, axis, pos, at, w, thick, leaf=True, hinge=1, swing_in=1, label=None):
    """axis 'v': wall runs in y at x = pos (faces pos..pos+thick); axis 'h': wall runs in x at y = pos."""
    if axis == 'h':
        punch(c, at - w / 2.0, pos, at + w / 2.0, pos + thick)
        c.line(at - w / 2.0, pos, at - w / 2.0, pos + thick, lw=0.03)
        c.line(at + w / 2.0, pos, at + w / 2.0, pos + thick, lw=0.03)
        if leaf:
            hx = at - w / 2.0 if hinge > 0 else at + w / 2.0
            yy = pos + thick if swing_in > 0 else pos
            a0 = 90 if swing_in > 0 else -90
            a1 = 0 if hinge > 0 else 180
            swing(c, hx, yy, w, a0, a1, 0, 1 if swing_in > 0 else -1)
    else:
        punch(c, pos, at - w / 2.0, pos + thick, at + w / 2.0)
        c.line(pos, at - w / 2.0, pos + thick, at - w / 2.0, lw=0.03)
        c.line(pos, at + w / 2.0, pos + thick, at + w / 2.0, lw=0.03)
        if leaf:
            hy = at - w / 2.0 if hinge > 0 else at + w / 2.0
            xx = pos + thick if swing_in > 0 else pos
            a0 = 0 if swing_in > 0 else 180
            a1 = 90 if hinge > 0 else -90
            swing(c, xx, hy, w, a0, a1, 1 if swing_in > 0 else -1, 0)


def pair_in_wall(c, axis, pos, at, w, thick):
    """A pair of doors (each leaf w/2) with both swings."""
    if axis == 'h':
        punch(c, at - w / 2.0, pos, at + w / 2.0, pos + thick)
        for sgn in (-1, 1):
            hx = at + sgn * w / 2.0
            swing(c, hx, pos + thick, w / 2.0, 90, 0 if sgn < 0 else 180, -sgn, 0)
            c.line(hx, pos + thick, hx - sgn * w / 2.0, pos + thick, lw=0.05)
    else:
        punch(c, pos, at - w / 2.0, pos + thick, at + w / 2.0)
        for sgn in (-1, 1):
            hy = at + sgn * w / 2.0
            swing(c, pos, hy, w / 2.0, 0, 90 if sgn < 0 else -90, 0, -sgn)
            c.line(pos, hy, pos, hy - sgn * w / 2.0, lw=0.05)


def window_in_wall(c, axis, pos, at, w, thick):
    if axis == 'h':
        punch(c, at - w / 2.0, pos, at + w / 2.0, pos + thick)
        for f in (0.0, 0.5, 1.0):
            c.line(at - w / 2.0, pos + thick * f, at + w / 2.0, pos + thick * f, lw=0.028)
        for e in (at - w / 2.0, at + w / 2.0):
            c.line(e, pos, e, pos + thick, lw=0.028)
    else:
        punch(c, pos, at - w / 2.0, pos + thick, at + w / 2.0)
        for f in (0.0, 0.5, 1.0):
            c.line(pos + thick * f, at - w / 2.0, pos + thick * f, at + w / 2.0, lw=0.028)
        for e in (at - w / 2.0, at + w / 2.0):
            c.line(pos, e, pos + thick, e, lw=0.028)


def club_plan(k):
    """Clubhouse floor plan. Paper x = Y (along, SE->NW), paper y = X (across, lane->buffer)."""
    c = sub(k)

    # roof overhang
    c.rect((CL_Y0 - OH_RAKE, CL_X0 - OH_EAVE, CL_Y1 + OH_RAKE, CL_X1 + OH_EAVE),
           fill='none', stroke='#8a8a8a', lw=0.025, dash='0.9,0.5')
    tx(c, CL_Y1 - 2.0, CL_X0 - 1.9, 'ROOF OVERHANG (TYP. 1\'-0")', size=0.32, anchor='end', color='#666')
    # porch slab + posts
    c.rect((CL_Y0, CL_X0, ENC_Y0, CL_X1), fill='#f3efe6', stroke='#111', lw=0.04)
    for px in PORCH_POSTS:
        c.rect((PORCH_SIDE_POSTS[0] - 0.67, px - 0.67, PORCH_SIDE_POSTS[0] + 0.67, px + 0.67),
               fill='#cfc7b4', stroke='#111', lw=0.03)
    for px in (PORCH_POSTS[0], PORCH_POSTS[-1]):
        c.rect((PORCH_SIDE_POSTS[1] - 0.67, px - 0.67, PORCH_SIDE_POSTS[1] + 0.67, px + 0.67),
               fill='#cfc7b4', stroke='#111', lw=0.03)
    tx(c, (CL_Y0 + ENC_Y0) / 2.0, CL_X1 / 2.0 + 6.0, 'COVERED PORCH', size=0.46, weight='bold', rot=90)
    tx(c, (CL_Y0 + ENC_Y0) / 2.0, CL_X1 / 2.0 - 1.0,
       '%s x %s   %d SF' % (fti(PORCH_D), fti(CLUB_W), round(PORCH_SF)), size=0.34, rot=90)
    tx(c, PORCH_SIDE_POSTS[0] + 1.4, CL_X1 / 2.0, 'FACES THE VILLAGE GREEN', size=0.32, rot=90,
       color='#444')
    # exterior walls of the enclosure
    wall(c, ENC_Y0, CL_X0, CL_Y1, CL_X0 + T)
    wall(c, ENC_Y0, CL_X1 - T, CL_Y1, CL_X1)
    wall(c, ENC_Y0, CL_X0, ENC_Y0 + T, CL_X1)
    wall(c, CL_Y1 - T, CL_X0, CL_Y1, CL_X1)
    # partitions
    wall(c, _y_i0, XB, _rr_y, XB + P, ext=False)                       # great room | support band
    wall(c, _y_i0 + LOBBY_L, XB, _y_i0 + LOBBY_L + P, _x_i1, ext=False)   # lobby | corridor
    wall(c, _y_i0 + LOBBY_L + P, XB + P + CORR, _rr_y, XB + P + CORR + P, ext=False)  # corridor | restrooms
    _mid = (_y_i0 + LOBBY_L + P + _rr_y) / 2.0
    wall(c, _mid - P / 2.0, XB + P + CORR + P, _mid + P / 2.0, _x_i1, ext=False)      # restroom A | B
    wall(c, YB, CL_X0, YB + P, CL_X1, ext=False)                        # great room | NW band
    for xx in (14.0, 20.5, 35.5):
        wall(c, YB + P, xx, _y_i1, xx + P, ext=False)

    # openings ------------------------------------------------------------------
    # NOTE the plan is drawn with paper x = building Y (along) and paper y = building X (across):
    # a wall at a fixed building Y is a VERTICAL wall on paper ('v'), one at a fixed X is horizontal.
    for view, at, kind, w, _h, _s in OPEN:
        if view == 'front':                                    # wall at Y = ENC_Y0, position along X
            (pair_in_wall if kind == 'french' else window_in_wall)(c, 'v', ENC_Y0, at, w, T)
        elif view == 'rear':                                   # wall at Y = CL_Y1
            if kind == 'door':
                door_in_wall(c, 'v', CL_Y1 - T, at, w, T, hinge=1, swing_in=-1)
            else:
                window_in_wall(c, 'v', CL_Y1 - T, at, w, T)
        elif view == 'left':                                   # wall at X = 0, position along Y
            (pair_in_wall if kind == 'french' else window_in_wall)(c, 'h', CL_X0, at, w, T)
        else:                                                  # wall at X = CL_X1
            if kind == 'door':
                door_in_wall(c, 'h', CL_X1 - T, at, w, T, hinge=1, swing_in=-1)
            else:
                window_in_wall(c, 'h', CL_X1 - T, at, w, T)
    # interior doors
    door_in_wall(c, 'v', _y_i0 + LOBBY_L, XB + P + 2.6, 3.0, P)                     # lobby -> corridor
    door_in_wall(c, 'h', XB + P + CORR, _y_i0 + LOBBY_L + 4.6, 3.0, P)              # corridor -> RR A
    door_in_wall(c, 'h', XB + P + CORR, _rr_y - 4.6, 3.0, P, hinge=-1)              # corridor -> RR B
    door_in_wall(c, 'v', YB, 7.0, 3.0, P, swing_in=-1)                              # great room -> kitchen
    door_in_wall(c, 'v', YB, 17.5, 3.0, P, swing_in=-1)                             # great room -> storage
    door_in_wall(c, 'v', YB, 28.0, 3.0, P, swing_in=-1)                             # corridor -> fitness
    # cased opening great room -> lobby
    punch(c, _y_i0 + 2.0, XB, _y_i0 + 10.0, XB + P)
    for yy in (_y_i0 + 2.0, _y_i0 + 10.0):
        c.line(yy, XB, yy, XB + P, lw=0.03)
    c.line(_y_i0 + 2.0, XB + P / 2.0, _y_i0 + 10.0, XB + P / 2.0, lw=0.028, dash='0.5,0.3')
    # serving pass-through great room -> kitchen
    punch(c, YB, 9.5, YB + P, 13.5)
    c.line(YB, 9.5, YB + P, 9.5, lw=0.03); c.line(YB, 13.5, YB + P, 13.5, lw=0.03)
    c.line(YB + P / 2.0, 9.5, YB + P / 2.0, 13.5, lw=0.028, dash='0.5,0.3')
    tx(c, YB - 0.9, 11.5, 'SERVING', size=0.3, rot=90, color='#333')

    # fixtures ------------------------------------------------------------------
    ki = ROOMS[5]['r']
    fp.draw_fixture(c, {'t': 'counter', 'r': (ki[1], ki[0], ki[3], ki[0] + 2.0)})
    fp.draw_fixture(c, {'t': 'counter', 'r': (ki[3] - 2.0, ki[0], ki[3], ki[2])})
    fp.draw_fixture(c, {'t': 'island', 'r': (ki[1] + 4.5, ki[0] + 4.5, ki[1] + 11.0, ki[0] + 7.0)})
    fp.draw_fixture(c, {'t': 'sink', 'r': (ki[1] + 4.0, ki[0], ki[1] + 6.5, ki[0] + 2.0)})
    fp.draw_fixture(c, {'t': 'range', 'r': (ki[1] + 8.0, ki[0], ki[1] + 10.5, ki[0] + 2.0)})
    fp.draw_fixture(c, {'t': 'fridge', 'r': (ki[3] - 2.0, ki[2] - 3.0, ki[3], ki[2])})
    for rr in (ROOMS[3], ROOMS[4]):
        x0, y0, x1, y1 = rr['r'][1], rr['r'][0], rr['r'][3], rr['r'][2]
        fp.draw_fixture(c, {'t': 'toilet', 'r': (x0 + 0.6, y1 - 2.6, x0 + 3.2, y1), 'back': 'y1'})
        fp.draw_fixture(c, {'t': 'vanity', 'r': (x1 - 2.2, y0 + 0.8, x1, y0 + 4.2)})
        c.circle((x0 + x1) / 2.0 + 0.4, (y0 + y1) / 2.0 - 0.6, 2.5, lw=0.025, dash='0.4,0.25',
                 stroke='#1a6faa')
    me = ROOMS[8]['r']
    fp.draw_fixture(c, {'t': 'wh', 'c': (me[1] + 1.4, me[0] + 1.6), 'rad': 0.9})
    c.rect((me[1] + 3.4, me[0] + 0.6, me[1] + 6.4, me[0] + 2.8), fill='#fff', lw=0.03)
    tx(c, me[1] + 4.9, me[0] + 1.7, 'AHU', size=0.3)
    c.rect((me[3] - 2.6, me[0] + 0.6, me[3] - 0.6, me[0] + 2.0), fill='#fff', lw=0.03)
    tx(c, me[3] - 1.6, me[0] + 1.3, 'RISER', size=0.28)
    st = ROOMS[6]['r']
    for j in range(3):
        c.line(st[1] + 0.4, st[0] + 1.2 + j * 1.6, st[3] - 0.4, st[0] + 1.2 + j * 1.6, lw=0.025,
               color='#777')

    # room labels ---------------------------------------------------------------
    for r in ROOMS:
        x0, y0, x1, y1 = r['r']
        cx, cy = (y0 + y1) / 2.0, (x0 + x1) / 2.0
        rot = 0 if (y1 - y0) >= (x1 - x0) else 90
        if r['name'].startswith('GREAT'):
            cy = (x0 + x1) / 2.0 + 4.0
        tx(c, cx, cy + (0.9 if rot == 0 else 0.0), r['name'], size=0.44, weight='bold', rot=rot)
        tx(c, cx + (0.0 if rot == 0 else 1.1), cy + (-0.1 if rot == 0 else 0.0),
           '%s x %s' % (fti(r['d']), fti(r['w'])), size=0.34, rot=rot)
        tx(c, cx + (0.0 if rot == 0 else 2.1), cy + (-1.1 if rot == 0 else 0.0),
           '%s SF' % format(int(round(r['sf'])), ','), size=0.34, rot=rot)
    tx(c, (ROOMS[0]['r'][1] + ROOMS[0]['r'][3]) / 2.0, ROOMS[0]['r'][0] + 3.0,
       'VAULTED CEILING TO %s AT THE RIDGE' % fti(RIDGE_AFF - 1.2), size=0.32, color='#444')
    # ridge line + the cross gable over the great room
    c.line(CL_Y0 - OH_RAKE, CL_X1 / 2.0, CL_Y1 + OH_RAKE, CL_X1 / 2.0, lw=0.03, dash='1.6,0.6,0.35,0.6',
           color='#8a8a8a')
    tx(c, CL_Y1 - 8.0, CL_X1 / 2.0 + 0.7, 'RIDGE ABOVE', size=0.32, color='#666')
    c.line(XG_C, CL_X0 - OH_EAVE, XG_C, XG_DIE, lw=0.03, dash='1.6,0.6,0.35,0.6', color='#8a8a8a')
    for sgn in (-1, 1):
        c.line(XG_C + sgn * XG_W / 2.0, CL_X0 - OH_EAVE, XG_C, XG_DIE, lw=0.025, color='#8a8a8a')
    tx(c, XG_C, XG_DIE + 1.2, 'CROSS GABLE OVER', size=0.3, color='#666')

    # dimensions ----------------------------------------------------------------
    dim_chain(c, CL_X0 - 2.6, [CL_Y0, ENC_Y0, YB, CL_Y1])
    dim_h(c, CL_X0 - 5.4, CL_Y0, CL_Y1, fti(CLUB_L))
    dim_v(c, CL_Y1 + 2.0, CL_X0, CL_X1, fti(CLUB_W))
    dim_v(c, CL_Y0 - 2.4, CL_X0, XB, fti(XB - CL_X0))
    dim_v(c, CL_Y0 - 2.4, XB, CL_X1, fti(CL_X1 - XB))

    # entry call-outs
    tx(c, ENC_Y0 - 1.2, 34.6, 'MAIN ENTRY', size=0.34, anchor='end', weight='bold')
    tx(c, ENC_Y0 - 1.2, 33.4, 'ZERO-STEP, %s PAIR' % fti(6.0), size=0.3, anchor='end', color='#333')
    tx(c, ENC_Y0 - 1.2, 14.0, 'EXIT 2 TO PORCH', size=0.32, anchor='end', color='#333')
    tx(c, 20.0, CL_X0 - 1.1, 'EXIT 3 / TERRACE', size=0.32, color='#333')
    tx(c, 50.0, CL_X1 + 2.3, 'FIRE-RISER ROOM DOOR', size=0.32, color='#333')
    tx(c, CL_Y1 + 1.4, 7.0, 'SERVICE / CATERING', size=0.32, anchor='start', color='#333', rot=90)

    north_arrow(c, CL_Y1 - 2.5, CL_X0 - 5.6, 2.4)
    scalebar(c, CL_Y0 + 2.0, CL_X0 - 8.6, 20.0, 5.0, 'GRAPHIC SCALE — FEET  (1/8" = 1\'-0")')
    return c.svg()


# ============================================================================ CLUBHOUSE ELEVATIONS
VIEWS = [('front', 'SOUTHEAST ELEVATION - FACES THE VILLAGE GREEN (S 28 deg 43\' E)'),
         ('left', 'SOUTHWEST ELEVATION - FACES THE PRIVATE LANE (S 61 deg 17\' W)'),
         ('right', 'NORTHEAST ELEVATION - FACES THE 20-FT BUFFER (N 61 deg 17\' E)'),
         ('rear', 'NORTHWEST ELEVATION - FACES THE INTERIOR OF THE SITE (N 28 deg 43\' W)')]


def porch_base(c, S, h0, h1, plate_z, posts):
    """Porch skirt, 20-in masonry piers with cast-stone caps and 8x8 cedar posts at the given h's."""
    c.rect((h0, 0, h1, FF), fill=S['base'], stroke='#111', lw=0.028)
    ev.base_tex(S)(c, h0, 0, h1, FF, S['base_line'])
    for cx in posts:
        c.rect((cx - ev.PIER_W / 2, FF, cx + ev.PIER_W / 2, FF + ev.PIER_H), fill=S['base'],
               stroke='#111', lw=0.028)
        ev.base_tex(S)(c, cx - ev.PIER_W / 2, FF, cx + ev.PIER_W / 2, FF + ev.PIER_H, S['base_line'])
        c.rect((cx - ev.PIER_W / 2 - 0.1, FF + ev.PIER_H, cx + ev.PIER_W / 2 + 0.1,
                FF + ev.PIER_H + 0.17), fill=S['trim'], stroke='#111', lw=0.022)
        c.rect((cx - ev.COL / 2, FF + ev.PIER_H + 0.17, cx + ev.COL / 2, plate_z - BEAM),
               fill=S['post'], stroke='#111', lw=0.028)


def Hh(view, pt):
    """(X, Y) in the clubhouse frame -> paper-horizontal h, starting at 0."""
    x, y = pt
    if view == 'front':
        return x
    if view == 'rear':
        return CLUB_W - x
    if view == 'left':
        return CLUB_L - y
    return y


def club_elev(view, k, labels='right'):
    c = sub(k)
    S = SCHEME
    gable = view in ('front', 'rear')
    plate_z = FF + PLATE
    eave_z = FF + EAVE_AFF
    ridge_z = FF + RIDGE_AFF
    pitch = PITCH[0] / float(PITCH[1])
    ops = [(at, kind, w, h, sill) for v, at, kind, w, h, sill in OPEN if v == view]

    if gable:
        h0, h1 = 0.0, CLUB_W
        if view == 'front':
            # the covered porch: recessed wall, gable above the beam, posts in front
            c.rect((h0 + T, 0, h1 - T, plate_z), fill='#EDEAE3', stroke='none')
            ev.wall_band(c, S, h0 + T, h1 - T, 0, plate_z)
            c.rect((h0 + T, 0, h1 - T, plate_z), fill='#2B2B2B', stroke='none', opacity=0.10)
            for at, kind, w, hh, sill in ops:
                ev.opening(c, S, {'width_ft': w, 'height_ft': hh, 'type': kind}, Hh(view, (at, 0.0)), FF + sill)
            ev.wall_band(c, S, h0, h1, plate_z, eave_z, base=False)
            ev.gable_wall(c, S, h0, h1, eave_z, ridge_z, brackets=True)
            c.rect((h0, plate_z - BEAM, h1, plate_z), fill=S['trim'], stroke='#111', lw=0.04)
        else:
            ev.wall_band(c, S, h0, h1, 0, eave_z)
            ev.corner_and_frieze(c, S, h0, h1, FF + ev.WATER_TABLE, eave_z, frieze=False)
            ev.gable_wall(c, S, h0, h1, eave_z, ridge_z)
            for at, kind, w, hh, sill in ops:
                ev.opening(c, S, {'width_ft': w, 'height_ft': hh, 'type': kind}, Hh(view, (at, 0.0)), FF + sill)
        drop = OH_EAVE * pitch
        ev.roof_poly(c, S, [(h0 - OH_EAVE, eave_z - drop - ev.FASCIA), (h0 - OH_EAVE, eave_z - drop),
                            ((h0 + h1) / 2.0, ridge_z), (h1 + OH_EAVE, eave_z - drop),
                            (h1 + OH_EAVE, eave_z - drop - ev.FASCIA), ((h0 + h1) / 2.0, ridge_z - ev.FASCIA)])
        c.line(h0, 0, h0, eave_z, lw=0.05)
        c.line(h1, 0, h1, eave_z, lw=0.05)
        if view == 'front':
            porch_base(c, S, h0, h1, plate_z, [Hh(view, (px, 0.0)) for px in PORCH_POSTS])
        hmin, hmax = h0 - OH_EAVE, h1 + OH_EAVE
    else:
        h0, h1 = 0.0, CLUB_L
        ph = (Hh(view, (0, 0.0)), Hh(view, (0, PORCH_D)))
        p0, p1 = min(ph), max(ph)
        seg = [(h0, p0), (p1, h1)]
        for a, b in seg:
            if b - a > 0.05:
                ev.wall_band(c, S, a, b, 0, eave_z)
                ev.corner_and_frieze(c, S, a, b, FF + ev.WATER_TABLE, eave_z)
        c.rect((p0, 0, p1, plate_z - BEAM), fill='#3A3A3A', stroke='none', opacity=0.13)
        c.rect((p0, plate_z - BEAM, p1, plate_z), fill=S['trim'], stroke='#111', lw=0.03)
        porch_base(c, S, p0, p1, plate_z, [Hh(view, (0.0, py)) for py in PORCH_SIDE_POSTS])
        for at, kind, w, hh, sill in ops:
            ev.opening(c, S, {'width_ft': w, 'height_ft': hh, 'type': kind}, Hh(view, (0.0, at)), FF + sill)
        ev.gutter(c, S, h0 - OH_RAKE, h1 + OH_RAKE, eave_z)
        ev.roof_poly(c, S, [(h0 - OH_RAKE, eave_z - ev.FASCIA), (h0 - OH_RAKE, ridge_z),
                            (h1 + OH_RAKE, ridge_z), (h1 + OH_RAKE, eave_z - ev.FASCIA)])
        c.line(h0 - OH_RAKE, ridge_z, h1 + OH_RAKE, ridge_z, lw=0.055)
        c.line(h0 - OH_RAKE, eave_z, h1 + OH_RAKE, eave_z, lw=0.03, color='#666')
        if view == 'left':                       # the cross gable stands on this face
            xc = Hh(view, (0.0, XG_C))
            g0, g1 = xc - XG_W / 2.0, xc + XG_W / 2.0
            xr = FF + XG_RIDGE_AFF
            ev.gable_wall(c, S, g0, g1, eave_z, xr)
            drop = OH_EAVE * pitch
            ev.roof_poly(c, S, [(g0 - OH_EAVE, eave_z - drop - ev.FASCIA), (g0 - OH_EAVE, eave_z - drop),
                                (xc, xr), (g1 + OH_EAVE, eave_z - drop),
                                (g1 + OH_EAVE, eave_z - drop - ev.FASCIA), (xc, xr - ev.FASCIA)])
            c.line(g0, eave_z - 0.1, g0, eave_z + 0.1, lw=0.04)
            c.line(g1, eave_z - 0.1, g1, eave_z + 0.1, lw=0.04)
        hmin, hmax = h0 - OH_RAKE, h1 + OH_RAKE

    # ground + level datums
    c.line(hmin - 1.6, 0, hmax + 1.6, 0, lw=0.085)
    x = hmin - 1.6
    while x < hmax + 1.6:
        c.line(x, 0, x - 0.4, -0.4, lw=0.018, color='#777')
        x += 1.2
    tags = [(eave_z, 'EAVE %s' % fti(eave_z)), (ridge_z, 'RIDGE %s' % fti(ridge_z))]
    if labels == 'right':
        tags = [(0.0, 'FIN. GRADE 0\'-0"'), (FF, 'FIN. FLOOR %s' % fti(FF))] + tags
    else:
        for z in (0.0, FF):
            c.line(hmin - 1.2, z, hmax + 1.2, z, lw=0.016, dash='0.5,0.35', color='#8A8A8A')
        tx(c, hmin + 1.3, -1.5, 'FIN. GRADE 0\'-0"  ·  FIN. FLOOR %s' % fti(FF), size=0.34,
           anchor='start', color='#333')
    for z, tag in tags:
        c.line(hmin - 1.2, z, hmax + 1.2, z, lw=0.016, dash='0.5,0.35', color='#8A8A8A')
        if labels == 'right':
            tx(c, hmax + 1.6, z, tag, size=0.34, anchor='start', color='#333')
        else:                       # long elevations: tag inside, over the drawing, on a white pad
            c.rect((hmin + 1.0, z + 0.15, hmin + 1.0 + 0.20 * len(tag) / k, z + 0.15 + 1.0 / k),
                   fill='#fff', stroke='none', opacity=0.82)
            tx(c, hmin + 1.3, z + 0.62 / k, tag, size=0.34, anchor='start', color='#333')
    if labels != 'right':
        hmax += 0.4
    return c.svg(), hmin, hmax


# ============================================================================ MAIL KIOSK
def kiosk_plan(k):
    c = sub(k)
    S = SCHEME
    L, W = KIOSK_L, KIOSK_W
    c.rect((-K_OH, -K_OH, L + K_OH, W + K_OH), fill='none', stroke='#8a8a8a', lw=0.025, dash='0.6,0.35')
    c.rect((0, 0, L, W), fill='#f3efe6', stroke='#111', lw=0.05)
    # back (northeast) wall with the water table
    c.rect((0, W - 0.5, L, W), fill='#2b2b2b', stroke='none')
    # posts
    for px in (0.67, L - 0.67):
        c.rect((px - 0.33, 0.33, px + 0.33, 0.99), fill='#cfc7b4', stroke='#111', lw=0.03)
        c.rect((px - 0.33, W - 1.16, px + 0.33, W - 0.5), fill='#cfc7b4', stroke='#111', lw=0.03)
    # cluster box units against the back wall
    x0 = (L - (CBU_N * CBU_W + (CBU_N - 1) * 0.5)) / 2.0
    for i in range(CBU_N):
        bx = x0 + i * (CBU_W + 0.5)
        c.rect((bx, W - 0.5 - CBU_D, bx + CBU_W, W - 0.5), fill='#ffffff', stroke='#111', lw=0.045)
        for j in range(1, 4):
            c.line(bx, W - 0.5 - CBU_D * j / 4.0, bx + CBU_W, W - 0.5 - CBU_D * j / 4.0, lw=0.02,
                   color='#888')
        tx(c, bx + CBU_W / 2.0, W - 0.5 - CBU_D / 2.0, 'CBU %d' % (i + 1), size=0.3)
    tx(c, L / 2.0, W - 0.5 - CBU_D - 0.75,
       '%d USPS-APPROVED CBUs' % CBU_N, size=0.36, weight='bold')
    # clear standing area
    c.rect((x0 - 0.5, W - 0.5 - CBU_D - 4.5, x0 + CBU_N * CBU_W + (CBU_N - 1) * 0.5 + 0.5,
            W - 0.5 - CBU_D), fill='none', stroke='#1a6faa', lw=0.028, dash='0.45,0.3')
    tx(c, L / 2.0, W - 0.5 - CBU_D - 2.4, '4\'-6" CLEAR APPROACH', size=0.32, color='#1a6faa')
    tx(c, L / 2.0, W - 0.5 - CBU_D - 3.3, '(ADA 30 x 48 CLEAR FLOOR SPACE)', size=0.28, color='#1a6faa')
    # bench + trash
    c.rect((0.9, 0.9, 4.4, 2.3), fill='#fff', stroke='#111', lw=0.035)
    tx(c, 2.65, 1.6, 'BENCH', size=0.3)
    c.circle(L - 1.9, 1.7, 0.75, fill='#fff', lw=0.035)
    tx(c, L - 1.9, 1.7, 'TR', size=0.28)
    # the short-term parking bay, southeast of the slab
    c.rect((-STALL_GAP - 3.4, 0.0, -STALL_GAP, W - 0.5), fill='#e9e9e9', stroke='#666', lw=0.03)
    c.line(-STALL_GAP - 3.4, W - 0.5, -STALL_GAP - 1.2, W + 0.9, lw=0.025, color='#666')
    c.line(-STALL_GAP - 3.4, 0.0, -STALL_GAP - 1.2, -1.4, lw=0.025, color='#666')
    tx(c, -STALL_GAP - 1.7, W / 2.0, '4 SHORT-TERM SPACES', size=0.3, weight='bold', rot=90)
    tx(c, -STALL_GAP - 2.7, W / 2.0, '%s x %s EACH' % (fti(STALL_W), fti(STALL_D)), size=0.28, rot=90)
    dim_h(c, -1.3, -STALL_GAP, 0, fti(STALL_GAP) + ' WALK', above=True)
    dim_h(c, -2.9, 0, L, fti(L))
    dim_v(c, L + 2.4, 0, W, fti(W))
    north_arrow(c, L + 5.2, W - 1.6, 1.3)
    return c.svg()


def kiosk_elev(front, k):
    """front=True: the open 16-ft face seen from the parking spaces; else the 10-ft side."""
    c = sub(k)
    S = SCHEME
    L, W = KIOSK_L, KIOSK_W
    span = (L if front else W)
    h0, h1 = 0.0, span
    slab, plate_z = K_SLAB, K_SLAB + K_PLATE
    eave_z = K_SLAB + K_EAVE_AFF
    ridge_z = K_SLAB + K_RIDGE_AFF
    # slab
    c.rect((h0 - 0.2, 0, h1 + 0.2, slab), fill=S['base'], stroke='#111', lw=0.03)
    ev.base_tex(S)(c, h0 - 0.2, 0, h1 + 0.2, slab, S['base_line'])
    # back wall (seen behind the opening on the front view, in section-like elevation on the side view)
    if front:
        c.rect((h0, slab, h1, plate_z), fill='#3A3A3A', stroke='none', opacity=0.14)
        ev.wall_band(c, S, h0 + 0.5, h1 - 0.5, slab, plate_z - BEAM)
        x0 = (L - (CBU_N * CBU_W + (CBU_N - 1) * 0.5)) / 2.0
        for i in range(CBU_N):
            bx = x0 + i * (CBU_W + 0.5)
            c.rect((bx, slab + 1.33, bx + CBU_W, slab + 1.33 + 4.83), fill='#E8E4DA', stroke='#111',
                   lw=0.04)
            for j in range(1, 6):
                c.line(bx, slab + 1.33 + 4.83 * j / 6.0, bx + CBU_W, slab + 1.33 + 4.83 * j / 6.0,
                       lw=0.018, color='#8a8a8a')
            c.line(bx + CBU_W / 2.0, slab + 1.33, bx + CBU_W / 2.0, slab + 1.33 + 4.83, lw=0.018,
                   color='#8a8a8a')
            c.rect((bx + 0.25, slab, bx + CBU_W - 0.25, slab + 1.33), fill='#D8D3C6', stroke='#111',
                   lw=0.03)
    else:
        ev.wall_band(c, S, h0, h1, slab, plate_z - BEAM)
        c.rect((h0, slab, h0 + 0.9, plate_z - BEAM), fill='#3A3A3A', stroke='none', opacity=0.12)
    # beam + posts + piers
    c.rect((h0, plate_z - BEAM, h1, plate_z), fill=S['trim'], stroke='#111', lw=0.04)
    posts = (0.67, span - 0.67)
    for px in posts:
        c.rect((px - 0.83, slab, px + 0.83, slab + 1.7), fill=S['base'], stroke='#111', lw=0.028)
        ev.base_tex(S)(c, px - 0.83, slab, px + 0.83, slab + 1.7, S['base_line'])
        c.rect((px - 0.93, slab + 1.7, px + 0.93, slab + 1.87), fill=S['trim'], stroke='#111', lw=0.022)
        c.rect((px - 0.33, slab + 1.87, px + 0.33, plate_z - BEAM), fill=S['post'], stroke='#111', lw=0.028)
    # hip roof
    if front:
        ridge_len = max(1.0, L - W)
        ev.roof_poly(c, S, [(h0 - K_OH, eave_z - ev.FASCIA), (h0 - K_OH, eave_z),
                            ((span - ridge_len) / 2.0, ridge_z), ((span + ridge_len) / 2.0, ridge_z),
                            (h1 + K_OH, eave_z), (h1 + K_OH, eave_z - ev.FASCIA)])
    else:
        ev.roof_poly(c, S, [(h0 - K_OH, eave_z - ev.FASCIA), (h0 - K_OH, eave_z),
                            (span / 2.0, ridge_z), (h1 + K_OH, eave_z), (h1 + K_OH, eave_z - ev.FASCIA)])
    ev.gutter(c, S, h0 - K_OH, h1 + K_OH, eave_z)
    # light fixture
    c.rect((span / 2.0 - 0.5, plate_z - BEAM - 0.55, span / 2.0 + 0.5, plate_z - BEAM - 0.2),
           fill='#fff', stroke='#111', lw=0.03)
    # ground and levels
    c.line(h0 - 2.2, 0, h1 + 2.2, 0, lw=0.08)
    x = h0 - 2.2
    while x < h1 + 2.2:
        c.line(x, 0, x - 0.35, -0.35, lw=0.018, color='#777')
        x += 1.0
    tags = ((slab, 'SLAB %s' % fti(slab)), (plate_z - BEAM, 'CLEAR %s' % fti(plate_z - BEAM - slab)),
            (eave_z, 'EAVE %s' % fti(eave_z)), (ridge_z, 'RIDGE %s' % fti(ridge_z)))
    for z, tag in tags:
        c.line(h0 - 1.6, z, h1 + 1.6, z, lw=0.016, dash='0.45,0.3', color='#8A8A8A')
        if front:
            tx(c, h1 + 1.9, z, tag, size=0.32, anchor='start', color='#333')
    dim_h(c, -2.4, h0, h1, fti(span))
    return c.svg(), h0 - K_OH, h1 + K_OH + (5.2 if front else 0.0)


# ============================================================================ MONUMENT SIGN
def sign_elev(k):
    c = sub(k)
    S = SCHEME
    L, H = SG_LEN, SG_H
    # footing (broken-out section at the left end)
    cut = 1.6
    c.rect((0, -SG_FTG, cut, 0), fill='#d9d9d9', stroke='#111', lw=0.03)
    c.rect((-0.5, -SG_FTG, cut, -SG_FTG + 0.9), fill='#d9d9d9', stroke='#111', lw=0.03)
    c.rect((0, 0, cut, H - SG_CAP), fill='#e8e4da', stroke='#111', lw=0.03)
    for j in range(4):
        c.line(0, 0.5 + j * 0.75, cut, 0.5 + j * 0.75, lw=0.016, color='#999')
    tx(c, cut / 2.0, (H - SG_CAP) / 2.0, 'CMU', size=0.3, rot=90)
    # ledge-stone veneer + cast-stone cap
    c.rect((cut, 0, L, H - SG_CAP), fill=S['base'], stroke='#111', lw=0.04)
    ev.base_tex(S)(c, cut, 0, L, H - SG_CAP, S['base_line'])
    c.rect((-0.17, H - SG_CAP, L + 0.17, H), fill=S['trim'], stroke='#111', lw=0.04)
    c.line(-0.17, H - SG_CAP + 0.1, L + 0.17, H - SG_CAP + 0.1, lw=0.02, color=S['trim_line'])
    # sign panel + letters
    pw, ph = SG_PANEL
    px0, py0 = (L - pw) / 2.0, 1.05
    c.rect((px0, py0, px0 + pw, py0 + ph), fill='#F5EFE2', stroke='#111', lw=0.04)
    tx(c, L / 2.0, py0 + ph - 0.62, 'THE COTTAGES', size=0.62, weight='bold')
    tx(c, L / 2.0, py0 + ph - 1.28, 'AT ARCADO SPRINGS', size=0.44, weight='bold')
    c.rect((px0, 0.35, px0 + 3.2, 0.85), fill='#EFE9DC', stroke='#111', lw=0.03)
    tx(c, px0 + 1.6, 0.6, '4535-4541 ARCADO RD SW', size=0.26)
    # ground line
    c.line(-1.6, 0, L + 1.6, 0, lw=0.08)
    x = -1.6
    while x < L + 1.6:
        c.line(x, 0, x - 0.28, -0.28, lw=0.016, color='#777')
        x += 0.8
    c.line(-1.0, -SG_FTG, L + 1.0, -SG_FTG, lw=0.03, dash='0.4,0.3', color='#777')
    # ground-mounted shielded fixtures
    for fx in (px0 + 0.5, px0 + pw - 0.5):
        c.rect((fx - 0.28, 0, fx + 0.28, 0.45), fill='#444', stroke='#111', lw=0.028)
        c.line(fx, 0.45, fx - 0.25, 1.3, lw=0.018, dash='0.25,0.18', color='#B08A2E')
        c.line(fx, 0.45, fx + 0.25, 1.3, lw=0.018, dash='0.25,0.18', color='#B08A2E')
    dim_v(c, -2.4, 0, H, fti(H))
    dim_v(c, -2.4, -SG_FTG, 0, fti(SG_FTG))
    dim_v(c, L + 1.4, py0, py0 + ph, fti(ph))
    tx(c, L + 1.9, py0 + ph / 2.0 + 0.3, 'PANEL %s x %s (%.1f SF)' % (fti(pw), fti(ph), pw * ph),
       size=0.3, anchor='start', color='#333')
    tx(c, L + 1.9, py0 + ph / 2.0 - 0.4, 'CUT-ALUMINIUM LETTERS 6 IN / 4 IN', size=0.3, anchor='start',
       color='#333')
    tx(c, L + 1.9, H - SG_CAP / 2.0, 'CAST-STONE CAP', size=0.3, anchor='start', color='#333')
    tx(c, L + 1.9, (H - SG_CAP) / 2.0 - 0.5, 'LEDGE STONE (04 40 00)', size=0.3, anchor='start',
       color='#333')
    tx(c, L + 1.9, 0.45, 'SHIELDED LED (2)', size=0.3, anchor='start', color='#333')
    tx(c, L + 1.9, -SG_FTG / 2.0, 'FOOTING 12 IN BELOW GRADE', size=0.3, anchor='start', color='#333')
    return c.svg()


def sign_plan(k):
    c = sub(k)
    S = SCHEME
    L, W = SG_LEN, SIGN_W
    # landscape bed
    c.rect((-1.2, -1.2, L + 1.2, W + 1.2), fill='#eaf0e4', stroke='#4a7a3a', lw=0.03, dash='0.5,0.35')
    # wall + wing planters
    c.rect((0, (W - SG_TH) / 2.0, L, (W + SG_TH) / 2.0), fill=S['base'], stroke='#111', lw=0.05)
    ev.base_tex(S)(c, 0, (W - SG_TH) / 2.0, L, (W + SG_TH) / 2.0, S['base_line'])
    for wx in (0.0, L - SG_WING):
        c.rect((wx, 0, wx + SG_WING, W), fill='#f0ece2', stroke='#111', lw=0.035)
    tx(c, SG_WING / 2.0, W * 0.24, 'MASONRY WING / PLANTER', size=0.28, rot=90, color='#333')
    tx(c, L / 2.0, (W + SG_TH) / 2.0 + 0.62, 'SIGN FACE (BOTH SIDES)', size=0.3)
    tx(c, L / 2.0, -0.75, 'LANDSCAPE BED - PLANTING BELOW 2\'-6"', size=0.3, color='#3d6b30')
    # the Arcado Rd R/W lies at lower u, i.e. off the left of this plan
    c.line(-1.6, W / 2.0, -3.4, W / 2.0, lw=0.025)
    c.line(-3.4, W / 2.0, -2.8, W / 2.0 + 0.28, lw=0.025)
    c.line(-3.4, W / 2.0, -2.8, W / 2.0 - 0.28, lw=0.025)
    tx(c, -3.6, W / 2.0, 'TO ARCADO RD', size=0.3, anchor='end', rot=90)
    dim_h(c, -2.0, 0, L, fti(L))
    dim_v(c, L + 2.0, 0, W, fti(W))
    dim_v(c, L + 1.6, (W - SG_TH) / 2.0, (W + SG_TH) / 2.0, fti(SG_TH))
    north_arrow(c, L + 3.4, W - 0.4, 0.8)
    return c.svg()


# ============================================================================ KEY PLAN
def key_plan(k):
    c = sub(k)
    lw = 0.03 / k

    def poly(pts, **kw):
        c.poly([(p[0], p[1]) for p in pts], **kw)

    for tract in AM['tract_polygons']:
        poly(tract, fill='#f6f3ea', stroke='#999', lw=0.02)
    poly(LANE['tract_polygon'], fill='#efefef', stroke='none')
    poly(LANE['pavement_polygon'], fill='#d8d8d8', stroke='#777', lw=0.02)
    poly(LANE['entry_drive']['pavement_polygon'] if 'pavement_polygon' in LANE['entry_drive']
         else LANE['entry_drive']['polygon'], fill='#d8d8d8', stroke='#777', lw=0.02)
    poly(AM['village_green'], fill='#e4eedd', stroke='#7aa06a', lw=0.02)
    for pad in AM['pickleball']:
        poly(pad, fill='#e8eef3', stroke='#5b7b93', lw=0.02)
    for crt in AM['courts']:
        poly(crt, fill='none', stroke='#5b7b93', lw=0.02)
    poly(AM['parking_bay'], fill='#e2e2e2', stroke='#666', lw=0.02)
    for s in AM['stalls']:
        poly(s, fill='none', stroke='#888', lw=0.015)
    poly(AM['kiosk_bay'], fill='#e2e2e2', stroke='#666', lw=0.02)
    for s in AM['kiosk_stalls']:
        poly(s, fill='none', stroke='#888', lw=0.015)
    poly(AM['clubhouse'], fill='#f2c58a', stroke='#111', lw=0.05)
    poly(AM['mail_kiosk'], fill='#f2c58a', stroke='#111', lw=0.05)
    poly(AM['entry_sign'], fill='#333', stroke='#111', lw=0.04)
    # R/W, setback and landscape strip
    for i in range(len(RW) - 1):
        c.line(RW[i][0], RW[i][1], RW[i + 1][0], RW[i + 1][1], lw=0.06)
    sb = LAYOUT['buffers']['arcado_setback_line']
    for a, b in zip(sb, sb[1:]):
        c.line(a[0], a[1], b[0], b[1], lw=0.025, dash='2.5,1.6,0.7,1.6', color='#b03a2e')
    # sight lines from the driver's eye
    for tgt in (SIGHT_NE, SIGHT_SW):
        c.line(DRIVER[0], DRIVER[1], tgt[0], tgt[1], lw=0.03, dash='2.2,1.4', color='#1a6faa')
    c.circle(DRIVER[0], DRIVER[1], 2.0, fill='#1a6faa', stroke='#1a6faa', lw=0.02)
    tx(c, DRIVER[0] + 4.0, DRIVER[1] - 12.0, 'DRIVER EYE', size=0.3, anchor='start', color='#1a6faa')
    tx(c, DRIVER[0] + 4.0, DRIVER[1] - 20.0, '14.5 FT BACK', size=0.28, anchor='start', color='#1a6faa')

    # markers
    for n, poly_, dx, dy in ((1, AM['clubhouse'], 0, 26), (2, AM['mail_kiosk'], 0, 20),
                             (3, AM['entry_sign'], 26, -14)):
        cx = sum(p[0] for p in poly_) / len(poly_); cy = sum(p[1] for p in poly_) / len(poly_)
        c.circle(cx + dx, cy + dy, 5.5, fill='#fff', stroke='#111', lw=0.03)
        tx(c, cx + dx, cy + dy, str(n), size=0.4, weight='bold')
        c.line(cx + dx, cy + dy - 5.5, cx, cy, lw=0.02)
    tx(c, -44.0, -130.0, 'ARCADO RD SW', size=0.34, rot=90, color='#333')
    tx(c, 60.0, -150.0, 'VILLAGE GREEN', size=0.3, color='#4a7a3a')
    tx(c, 183.0, -197.0, 'PICKLEBALL', size=0.3, color='#5b7b93')
    north_arrow(c, 205.0, -20.0, 16.0)
    scalebar(c, 0.0, -262.0, 160.0, 40.0, 'GRAPHIC SCALE - FEET  (1" = 80\'-0")')
    return c.svg()


# ============================================================================ SHEET
def build():
    c = fp.Canvas(ymax=HF)
    mg, tb = ev._sheet_frame(
        c, WF, HF, None, 'A-3',
        'CLUBHOUSE, MAIL KIOSK AND ENTRY MONUMENT SIGN — PLANS, ELEVATIONS AND DETAILS',
        'Scales as noted — clubhouse 1/8" = 1\'-0"; mail kiosk 1/4" = 1\'-0"; monument sign 3/8" = 1\'-0"; '
        'key plan 1" = 80\'-0" — on ARCH C (24 x 18 in)')

    def blocktitle(x, y, s, sub_=None):
        c.text(x, y, s, size=0.66, weight='bold', anchor='start')
        if sub_:
            c.text(x, y - 0.95, sub_, size=0.38, anchor='start', color='#333')

    # ---------------------------------------------------------------- clubhouse plan  (x 3-46)
    blocktitle(3.0, 92.6, 'CLUBHOUSE — FLOOR PLAN',
               '%s SF under roof on the %s x %s footprint of Sheet C-1 — SCALE 1/8" = 1\'-0"'
               % (format(int(CLUB_SF), ','), fti(CLUB_L), fti(CLUB_W)))
    place(c, club_plan(K18), 4.9, 64.0, K18)

    # ---------------------------------------------------------------- monument sign  (x 48-81)
    blocktitle(48.5, 92.6, 'MONUMENT ENTRY SIGN',
               'The only sign in the project — SCALE 3/8" = 1\'-0"')
    sx = 55.0
    place(c, sign_elev(K38), sx, 83.4, K38)
    c.text(sx + SG_LEN * K38 / 2.0, 79.4, 'ELEVATION — BROKEN-OUT SECTION AT THE LEFT END', size=0.44,
           weight='bold')
    place(c, sign_plan(K38), sx, 67.5, K38)
    c.text(sx + SG_LEN * K38 / 2.0, 62.0, 'PLAN', size=0.44, weight='bold')
    c.text(sx + SG_LEN * K38 / 2.0, 60.9,
           'Face %s x %s = %.1f SF (limit 32 SF)  ·  height %s (limit 6\'-0")'
           % (fti(SG_LEN), fti(SG_H), SG_FACE_SF, fti(SG_H)), size=0.38)
    c.text(sx + SG_LEN * K38 / 2.0, 60.0,
           '%s from the Arcado Rd R/W  ·  %s clear of the 390-ft departure sight line'
           % (fti(SIGN_TO_RW), fti(SIGHT_CLEAR)), size=0.38)
    sbc = sub(K38)
    scalebar(sbc, 0.0, 0.0, 4.0, 1.0, 'GRAPHIC SCALE — FEET  (3/8" = 1\'-0")')
    place(c, sbc.svg(), sx + 1.0, 57.9, K38)

    # ---------------------------------------------------------------- mail kiosk  (y 34-57)
    blocktitle(3.0, 56.9, 'MAIL KIOSK — USPS CLUSTER BOX UNIT SHELTER',
               '%s x %s shelter and its four short-term spaces, from data/layout.json — '
               'SCALE 1/4" = 1\'-0"' % (fti(KIOSK_L), fti(KIOSK_W)))
    place(c, kiosk_plan(K14), 14.6, 39.6, K14)
    c.text(14.6 + KIOSK_L * K14 / 2.0, 34.7, 'PLAN (ROOF DASHED)', size=0.46, weight='bold')
    gf, f0, f1 = kiosk_elev(True, K14)
    place(c, gf, 36.5 - f0 * K14, 39.6, K14)
    c.text(36.5 + (KIOSK_L / 2.0 - f0) * K14, 34.7, 'FRONT (SOUTHWEST) ELEVATION', size=0.46,
           weight='bold')
    gs, s0, s1 = kiosk_elev(False, K14)
    place(c, gs, 67.0 - s0 * K14, 39.6, K14)
    c.text(67.0 + (KIOSK_W / 2.0 - s0) * K14, 34.7, 'SIDE (SOUTHEAST) ELEVATION', size=0.46,
           weight='bold')
    kbar = sub(K14)
    scalebar(kbar, 0.0, 0.0, 8.0, 2.0, 'GRAPHIC SCALE — FEET  (1/4" = 1\'-0")')
    place(c, kbar.svg(), 46.5, 55.5, K14)

    # ---------------------------------------------------------------- key plan  (x 3-24)
    blocktitle(3.0, 33.8, 'KEY PLAN — FRONT AMENITY BLOCK',
               'The front block only — the full site is Sheet C-1 — SCALE 1" = 80\'-0"')
    c.add('<defs><clipPath id="kp"><rect x="2.6" y="%.2f" width="21.4" height="18.6"/></clipPath></defs>'
          % (HF - 31.4))
    place(c, key_plan(K80), 3.0 + 48.0 * K80, 12.8 + 246.0 * K80, K80, clip='kp')
    kp_bar = sub(K80)
    scalebar(kp_bar, 0.0, 0.0, 160.0, 40.0, 'GRAPHIC SCALE — FEET  (1" = 80\'-0")')
    place(c, kp_bar.svg(), 3.4, 11.5, K80)
    c.text(3.0, 10.6, '1  CLUBHOUSE   2  MAIL KIOSK   3  MONUMENT ENTRY SIGN   ·   blue: the 390-ft '
           'departure sight lines from the driver eye', size=0.34, anchor='start')

    # ---------------------------------------------------------------- materials and colours (x 26-54)
    x = 26.0
    c.text(x, 33.8, 'MATERIALS AND COLOURS — Application Instructions item (11)', size=0.6,
           weight='bold', anchor='start')
    c.text(x, 32.8, 'All three non-dwelling structures are built in %s - the palette of Sheets A-2.1 / '
           'A-2.2 / A-2.3' % SCHEME_NAME, size=0.38, anchor='start')
    c.text(x, 32.0, 'and docs/12-outline-specifications.md. The three cottage schemes are distributed '
           'among the dwellings.', size=0.38, anchor='start')
    yy = 30.9
    for i, (name, csi, txt_) in enumerate(ev.MATERIAL_KEYS, 1):
        c.circle(x + 0.4, yy, 0.36, fill='#fff', stroke='#111', lw=0.03)
        c.text(x + 0.4, yy, str(i), size=0.38, weight='bold')
        c.text(x + 1.05, yy, '%s (%s)' % (name, csi), size=0.38, weight='bold', anchor='start')
        yy -= 0.52
        for ln in textwrap.wrap(txt_, 136):
            c.text(x + 1.05, yy, ln, size=0.36, anchor='start', color='#333')
            yy -= 0.48
        yy -= 0.12

    # ---------------------------------------------------------------- clubhouse data block
    xd = 26.0
    c.text(xd, yy - 0.4, 'CLUBHOUSE — AREAS, HEIGHT AND OCCUPANT LOAD', size=0.6, weight='bold',
           anchor='start')
    yy -= 1.5
    rows = [('Building footprint (Sheet C-1)', '%s x %s = %s SF' % (fti(CLUB_L), fti(CLUB_W),
                                                                    format(int(CLUB_SF), ','))),
            ('Enclosed (gross, outside face)', '%s SF' % format(int(round(ENCLOSED_SF)), ',')),
            ('Covered porch (village green)', '%s SF' % format(int(round(PORCH_SF)), ',')),
            ('Net room area (sum of rooms)', '%s SF' % format(int(round(NET_SF)), ',')),
            ('Eave / ridge above finished grade', '%s / %s' % (fti(EAVE_AG), fti(RIDGE_AG))),
            ('Voluntary ridge condition / Table 4.1 max', '%s / %s' % (fti(CAP_RIDGE), fti(DISTRICT_MAX))),
            ('Setback from the Arcado Rd R/W (50 ft req.)', '%.1f ft' % CLUB_TO_RW),
            ('Clear of the 20-ft NE buffer band', '%.1f ft' % CLUB_TO_BUF),
            ('Lane-facing wall to the lane pavement edge', fti(CLUB_TO_LANE)),
            ('Occupant load (IBC 2024 Table 1004.5)', '%d' % OCC),
            ('Exits required / provided', '2 / 3'),
            ('Exit separation req. (1/3 diagonal) / provided', '%s / %s' % (fti(SEP_REQ), fti(EXIT_SEP)))]
    for nm, val in rows:
        c.text(xd, yy, nm, size=0.36, anchor='start')
        c.text(xd + 27.5, yy, val, size=0.36, anchor='end', weight='bold')
        yy -= 0.52
    yy -= 0.15
    for ln in textwrap.wrap('Occupant load: ' + '; '.join(
            '%s %s SF / %d = %d' % (n.split(' /')[0].split(' (')[0].title(), format(int(round(a)), ','), f,
                                    int(math.ceil(a / f))) for n, a, f, _b in OCC_ROWS), 138):
        c.text(xd, yy, ln, size=0.34, anchor='start', color='#333')
        yy -= 0.46

    # ---------------------------------------------------------------- notes  (x 56-80.5)
    ybot = notes_block(c, 55.0, 33.8, 'GENERAL AND CODE NOTES', NOTES, 26.2, size=0.35, lead=0.43,
                       gap=0.07)
    print('notes block bottom y = %.1f (must stay above 10.2)' % ybot)

    # ---------------------------------------------------------------- clubhouse elevations (x 82-125.4)
    c.line(82.0, 10.2, 82.0, 93.6, lw=0.05, color='#999')
    blocktitle(82.8, 92.6, 'CLUBHOUSE — EXTERIOR ELEVATIONS, ALL FOUR SIDES',
               'Application Instructions item (11): an elevation of each side visible from the street — '
               'SCALE 1/8" = 1\'-0" — %s' % SCHEME_NAME)
    base_y = [73.6, 55.2, 36.8, 18.4]
    for (view, title), Y0 in zip(VIEWS, base_y):
        long_ = view in ('left', 'right')
        g, h0, h1 = club_elev(view, K18, labels='inside' if long_ else 'right')
        wdt = (h1 - h0) * K18
        X0 = 82.8 + (42.6 - wdt) / 2.0
        place(c, g, X0 - h0 * K18, Y0, K18)
        c.text(X0 + wdt / 2.0, Y0 - 2.4, title, size=0.46, weight='bold')
    roof_note = (
        'ROOF GEOMETRY, computed from this plan: plate %s above finished floor + %s raised heel = eave '
        '%s AFF; main gable span %s (eave plate to eave plate) at %d:%d gives a rise of %s, so the ridge '
        'is %s AFF and, with the finished floor %s above finished grade, %s above finished grade. The '
        'cross gable over the great room spans %s at %d:%d, %s AFF, and dies into the main roof %s in '
        'from the eave. Roof overhangs %s at the eaves and %s at the rakes; the %s x %s rectangle on '
        'Sheet C-1 is the wall and porch-slab footprint, not the roof edge.'
        % (fti(PLATE), fti(HEEL), fti(EAVE_AFF), fti(SPAN), PITCH[0], PITCH[1],
           fti((SPAN / 2.0) * PITCH[0] / float(PITCH[1])), fti(RIDGE_AFF), fti(FF), fti(RIDGE_AG),
           fti(XG_W), PITCH[0], PITCH[1], fti(XG_RIDGE_AFF), fti(XG_DIE), fti(OH_EAVE), fti(OH_RAKE),
           fti(CLUB_L), fti(CLUB_W)))
    yy = 14.6
    c.text(82.8, yy, 'CLUBHOUSE ROOF AND HEIGHT — HOW THE NUMBERS ARE DERIVED', size=0.5,
           weight='bold', anchor='start')
    yy -= 0.95
    for ln in textwrap.wrap(roof_note, 128):
        c.text(82.8, yy, ln, size=0.38, anchor='start', color='#222')
        yy -= 0.52

    body = c.svg()
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%gin" height="%gin" viewBox="0 0 %.3f %.3f" '
           'font-family="Helvetica, Arial, sans-serif"><rect width="%.3f" height="%.3f" fill="#fff"/>\n%s\n'
           '</svg>' % (SHEET_IN[0], SHEET_IN[1], WF, HF, WF, HF, body))
    path = os.path.join(DRAW, 'amenity-sheet.svg')
    open(path, 'w').write(svg + '\n<!-- ' + MARKER + ' -->\n')
    return path


NOTES = [
    '**ONE GROUND-MOUNTED MONUMENT SIGN. NO WALL SIGNS ARE PROPOSED ON ANY DWELLING, ON THE CLUBHOUSE OR '
    'ON ANY ACCESSORY STRUCTURE.**',
    'SIGN STANDARD — VERIFY: the ordinance excerpts collected for this application (data/ordinance-'
    'excerpts.md — Lilburn Zoning Ordinance 2023-603, Articles 3 and 4, §602, §734, §§1003–1005) contain '
    'NO sign article, so '
    'the permitted area, height, setback and illumination for a residential subdivision entrance sign are '
    'NOT established here. The sign is drawn to a self-imposed limit of 32 SF of face and 6\'-0" of height '
    '(it is built at %.1f SF and %s). Confirm the governing article and the area-measurement method at the '
    'pre-application conference. All signs are permitted separately and a sign easement may be required '
    '(Site Development Plan Review Checklist §4.q).' % (SG_FACE_SF, fti(SG_H)),
    'SIGN FOOTPRINT: the %s x %s rectangle shown for the sign on Sheet C-1 is the bounding footprint of '
    'the monument, not a wall thickness: an %s long x %s thick masonry wall with a %s wide masonry '
    'wing/planter return at each end, %s deep, in a landscaped bed. Both faces carry copy; the area above '
    'is one face.' % (fti(SIGN_L), fti(SIGN_W), fti(SG_LEN), fti(SG_TH), fti(SG_WING), fti(SIGN_W)),
    'SIGN ILLUMINATION: external only - two ground-mounted, fully shielded LED sign lights with glare '
    'louvers set in the bed and aimed at the face, cut off at the top of the cap so no light is emitted '
    'above the horizontal; 3000K maximum, photocell and timer, spill 0.1 fc or less at any property line. '
    'A shielded, downward-directed cap-mounted LED downlight is an approved alternate. No internal '
    'illumination, no exposed lamps, no changeable copy (docs/12 10 14 00 2.03).',
    'SIGHT DISTANCE: intersection sight distance 390 ft at 35 mph (Gwinnett County Unified Development '
    'Ordinance §900-40 Table 900.2, AASHTO Case B1; docs/08 Memo A, docs/11 §5). The departure sight '
    'triangle is struck from a driver '
    'eye 14.5 ft behind the near edge of the travelled way on the drive centreline. The sign stands '
    '%s behind that point and its nearest corner is %s clear of the nearer sight line; no part of the sign '
    'or its bed lies within the triangle. Planting in the bed is held below 2\'-6". A field '
    'sight-distance survey and the Gwinnett DOT driveway permit govern - VERIFY.'
    % (fti(SIGN_BEHIND), fti(SIGHT_CLEAR)),
    'MAIL DELIVERY (City of Lilburn Site Development Plan Review Checklist §4.r): a cluster-box system is proposed for the '
    'entire project and one street name serves all house numbers. Contact the Lilburn Post Office Growth '
    'Manager before construction drawings. The checklist directs "accessory structure details with '
    'protection from the elements" - the shelter above provides a roofed, three-sided enclosure over the '
    'boxes with a closed northeast wall, a clear approach and a bench.',
    'CLUBHOUSE OCCUPANCY AND SPRINKLERS: Group A-3 with accessory Group B, Type V-B construction, one '
    'story, no basement (IBC 2024 (GA 2026) §303.4, Table 601). '
    'Sprinklered throughout under NFPA 13 and monitored; the 43 dwellings are sprinklered under NFPA 13D '
    '(voluntary condition 5; docs/08 Memo E). Knox box at the clubhouse. Fire-riser room with a direct '
    'exterior door on the northeast elevation. VERIFY the occupant load, exiting and panic hardware with '
    'the Gwinnett County Fire Marshal at plan review.',
    'ACCESSIBILITY: accessible route from the van-accessible space in the guest bay across the lane at a '
    'marked crossing with flush ramps to the porch and a zero-step entry (finished floor %s above '
    'finished grade, entry walk 1:20 or flatter). Two single-user accessible toilet rooms, each with a '
    '60-in turning circle and grab-bar blocking; 36-in doors throughout; a 34-in accessible counter '
    'segment in the kitchen. 2010 ADA Standards and ICC A117.1-2017 - final layouts by the Architect.'
    % fti(FF),
    'PLUMBING: at an occupant load of %d, IPC 2024 (GA 2026) Table 403.1 (A-3) calls for 1 water closet '
    'and 1 lavatory per sex, a drinking fountain and a service sink. Two single-user accessible toilet '
    'rooms, a bottle-filler/fountain at the corridor and a service sink in the kitchen appear consistent - '
    'VERIFY at plan review.' % OCC,
    'HEIGHTS (Checklist §4.g, height at the highest point): clubhouse ridge %s, mail kiosk ridge %s, '
    'monument sign %s above finished grade - each below the %s voluntary ridge condition and the %s '
    'maximum of Ord. 2023-603 Table 4.1 (R-2). The clubhouse gable is %d:%d, not the cottages\' 8:12: '
    'over the %s span an 8:12 roof puts the ridge %s above finished grade, above the voluntary '
    'condition. Materials, trim, porch and detailing are the cottages\'. Kiosk 4:12 hip, subordinate.'
    % (fti(RIDGE_AG), fti(K_RIDGE_AG), fti(SG_H), fti(CAP_RIDGE), fti(DISTRICT_MAX), PITCH[0], PITCH[1],
       fti(SPAN), fti(FF + EAVE_AFF + (SPAN / 2.0) * 8.0 / 12.0)),
    'CLUSTER BOX UNITS: %d dwellings served by %d USPS-approved 16-compartment CBUs = %d tenant '
    'compartments (%d spare, %.0f%%) and %d parcel lockers, plus an outgoing-mail slot. Compartments '
    'assigned to residents needing accessible reach are to fall between 15 in and 48 in above the slab '
    '(ICC A117.1-2017 308; USPS-STD-4C). Model, dimensions and the final count are VERIFY items with '
    'USPS.' % (DU, CBU_N, CBU_N * CBU_COMP, CBU_N * CBU_COMP - DU,
               100.0 * (CBU_N * CBU_COMP - DU) / float(CBU_N * CBU_COMP), CBU_N * CBU_PARCEL),
    'PARKING AT THE KIOSK: %d short-term spaces, %s x %s each (Checklist §4.w), in an %s x %s bay %s '
    'southeast of the shelter slab; %d guest spaces (one van-accessible) serve the clubhouse across a '
    'marked crossing of the lane (Sheet C-1). The shelter slab stands %s from the edge of the %s lane '
    'pavement and %s behind the back of the %s sidewalk (%s pavement half-width + %s strip + %s walk).'
    % (len(STALLS), fti(STALL_W), fti(STALL_D), fti(len(STALLS) * STALL_W), fti(STALL_D), fti(STALL_GAP),
       AM.get('guest_spaces', 8), fti(KIOSK_TO_LANE), fti(PAVE_W), fti(KIOSK_TO_LANE - 7.0), fti(5.0),
       fti(PAVE_W / 2.0), fti(2.0), fti(5.0)),
    'Accessory structures are set back at least 5 ft from any lot line and any required buffer '
    '(Checklist §4.l and §4.m); the clubhouse stands %.1f ft from the Arcado Rd R/W against the 50-ft '
    'collector setback of Ord. 2023-603 Table 4.1 and %.1f ft clear of the 20-ft northeast buffer band.'
    % (CLUB_TO_RW, CLUB_TO_BUF),
    '**DRAFT - NOT SEALED.** These are concept drawings by the owner-applicant for the rezoning hearing. '
    'The clubhouse and the kiosk must be designed and sealed by a Georgia-registered architect and '
    'engineer before permit; the sign requires a separate sign permit and, if it exceeds 6 ft or 32 SF, '
    'a Georgia PE footing design (docs/12 10 14 00 1.05).',
]

if __name__ == '__main__':
    p = build()
    fp.render_png(p, p[:-4] + '.png', dpi=200)
    print('CLUBHOUSE  footprint %s x %s = %s SF (data/layout.json amenity.clubhouse, u %.1f-%.1f, v %.1f-%.1f)'
          % (fti(CLUB_L), fti(CLUB_W), format(int(CLUB_SF), ','), CLUB_R[0], CLUB_R[2], CLUB_R[1], CLUB_R[3]))
    print('           enclosed %.0f SF + covered porch %.0f SF = %.0f SF under roof; net rooms %.0f SF'
          % (ENCLOSED_SF, PORCH_SF, ENCLOSED_SF + PORCH_SF, NET_SF))
    print('           plate %s + heel %s -> eave %s AFF; span %s at %d:%d -> ridge %s AFF = %s above grade'
          % (fti(PLATE), fti(HEEL), fti(EAVE_AFF), fti(SPAN), PITCH[0], PITCH[1], fti(RIDGE_AFF),
             fti(RIDGE_AG)))
    print('           occupant load %d; exits 3; separation required %s; to R/W %.1f ft; buffer clear %.1f ft'
          % (OCC, fti(SEP_REQ), CLUB_TO_RW, CLUB_TO_BUF))
    print('KIOSK      %s x %s; %d CBUs = %d compartments + %d parcel lockers; ridge %s above grade; '
          '%d stalls %s x %s, %s walk'
          % (fti(KIOSK_L), fti(KIOSK_W), CBU_N, CBU_N * CBU_COMP, CBU_N * CBU_PARCEL, fti(K_RIDGE_AG),
             len(STALLS), fti(STALL_W), fti(STALL_D), fti(STALL_GAP)))
    print('SIGN       %s x %s footprint; face %s x %s = %.1f SF (limit %.0f SF); height %s (limit %s); '
          'panel %.1f SF' % (fti(SIGN_L), fti(SIGN_W), fti(SG_LEN), fti(SG_H), SG_FACE_SF, SG_MAX_SF,
                             fti(SG_H), fti(SG_MAX_H), SG_PANEL_SF))
    print('           setback from Arcado R/W %.2f ft; %s behind the driver eye; sight-line clearance '
          '%.1f ft; inside the 390-ft triangle: %s' % (SIGN_TO_RW, fti(SIGN_BEHIND), SIGHT_CLEAR,
                                                       SIGN_IN_TRI))
    print('wrote', p, 'and', p[:-4] + '.png')
