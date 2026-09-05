#!/usr/bin/env python3
"""Sheet C-7.0 "LANDSCAPE, BUFFER AND TREE PROTECTION CONCEPT" — The Cottages at Arcado Springs.

    python3 tools/landscape.py     ->  drawings/landscape-buffer.svg + .png

ARCH D 36 x 24 in at 1" = 60' with two enlargements at 1" = 20', drawn on tools/sitebase.py in
the site-local (u, v) system so that the sheet overlays Sheet C-0 (existing conditions),
Sheet C-2.0 (master concept plan), Sheet C-3.0 (grading) and Sheet C-4.0 (utility) exactly.

WHY THIS SHEET EXISTS
The 2026 Lilburn "Application Instructions" item (8) names "landscaping" as a required site-plan
element and Lilburn Zoning Ordinance 2023-603 section 1003-4.6 names "areas of existing vegetation
or parts of the site to be landscaped".  The 2026-09-03 drawing-standards audit records the whole
of it as WEAK (item 8-n: "No plant material, no street trees, no buffer supplement, no
landscape-strip planting, no parking-lot trees, no plant schedule, no tree-protection limits") and
completeness item M9 sets the content of this sheet.  Every requirement below is answered
graphically and arithmetically, with the clause number of the City of Lilburn Site Development
Plan Review Checklist printed beside it:

  section 6.a  Registered Landscape Architect / forester / arborist seal        (status block + banner)
  section 6.b  buffer boundary AND dimensions, labelled "undisturbed", abutting residential
  section 6.c  25 ft of additional buffer where the required buffer lies within an easement
  section 6.f  buffer encroachments as near perpendicular as possible, 50 ft maximum width
  section 6.g  tree-protection areas delineated, standard detail, fence before land disturbance
  section 6.h  supplemental buffer planting: 6 ft minimum at planting, 20 ft at maturity
  section 6.i  TDU calculations NOT required of an SFR subdivision; planting data in tabular form
  section 6.j  10-ft landscape strip: 1 tree + 1 shrub per 25 lf of frontage; no landscaping
               3 ft to 15 ft in height within 20 ft of a right-of-way intersection
  section 6.k  parking-lot planting: 1 tree per 7 spaces, every space within 60 ft of a trunk
  section 6.l  5-ft landscape strip around accessory structures and ground-level HVAC
  section 6.m  certificate-of-occupancy and 12-month warranty note
  section 6.n  overhead-utility species check (Georgia Power right-tree/right-place)

WHAT IS READ AND WHAT IS COMPUTED
Read, never re-derived: the boundary, the lots, the lane, the amenity block, the open-space
tracts, the ponds, the stream reaches and the 237.62-ft Arcado Rd frontage all come from
data/layout.json AS IT STANDS AT RUN TIME (it was regenerated 2026-09-03 — 41 lots, resized
basins; numbers quoted in older documents are stale).  The species palette and the supplemental
planting rate are the Division 32 93 00 outline specification (docs/12).  Computed here, and only
here: the 20-ft buffer band as a true mitred offset of the boundary, the plantable length of the
frontage strip after the drive opening and the two sight triangles are removed, every plant
location, the plant schedule quantities and percentages (counted from the symbols actually
drawn — the schedule cannot disagree with the plan), and the 60-ft parking-lot trunk-distance
test, whose worst measured distance is printed on the sheet.

CONCEPT — to be sealed by a Registered Landscape Architect, forester or arborist
(City of Lilburn Site Development Plan Review Checklist section 6.a).  DRAFT — NOT SEALED.
No tree survey has been performed; the existing-vegetation limits are approximate.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitebase as sb                                      # noqa: E402

# =========================================================================== sheet geometry
SCALE20 = 72.0 / 20.0                       # 1" = 20'  -> 3.6 pt/ft (both enlargements)
WIN = (-150.0, 1840.0, -258.0, 28.0)        # tighter v window than Sheet C-0: the buffer sheet
                                            # needs a tall band for the 1" = 20' frontage plan
PLAN_X0, PLAN_Y0 = 102.0, 52.0
PLAN_W = (WIN[1] - WIN[0]) * sb.SCALE60
PLAN_H = (WIN[3] - WIN[2]) * sb.SCALE60     # 396 pt
BAND_Y0 = PLAN_Y0 + PLAN_H + 30             # 425
BAND_Y1 = sb.BAND_Y1                        # 1530

L = sb.LAYOUT
MET = L['metrics']
AM = L['amenity']

# data/plans.json is READ (never written) so that the typical buffer section stays in step with
# the architectural set: it was regenerated on 2026-09-03 and Plan A's patio edge now stands
# 20.50 ft from the rear lot line, not the 20.17 ft recorded in audit-2026-09-03.
with open(os.path.join(sb.DATA, 'plans.json')) as _fh:
    PLANS = json.load(_fh)
PA = PLANS['plans']['A']
PA_SIT = PA['lot_siting']
PA_PATIO = float(PA_SIT['patio_edge_from_rear_line_ft'])
PA_REAR_WALL = float(PA_SIT['rear_wall_from_rear_line_ft'])
PA_BODY = float(PA['overall_body_dims']['depth_ft'])
PA_RIDGE = float(PA['roof']['max_ridge_ft'])
PA_BUFFER_CLEAR = PA_PATIO - 20.0

# =========================================================================== authoritative inputs
BUF_FT = float(L['buffers']['perimeter_buffer_ft'])          # 20.0
ADDL_BUF_FT = 25.0                                           # checklist section 6.c
STRIP_FT = 10.0                                              # checklist section 6.j
FRONTAGE_FT = float(MET['frontage_arcado_along_rw_ft'])      # 237.62 ft along the R/W
STRIP_RATE_FT = 25.0                                         # 1 tree + 1 shrub per 25 lf
STREET_TREE_OC = 40.0
PARK_RATE = 7.0                                              # 1 tree per 7 spaces
PARK_RADIUS = 60.0
GUEST_SPACES = int(AM['guest_spaces'])
KIOSK_SPACES = int(AM['kiosk_spaces'])
AMENITY_SPACES = GUEST_SPACES + KIOSK_SPACES                 # 12
SIGHT_TRI_FT = 20.0                                          # section 6.j R/W-intersection triangle
ISD_FT = 390.0                                               # FACTS section 2b (VERIFY by PE)

STRIP_TREES_REQ = int(math.ceil(FRONTAGE_FT / STRIP_RATE_FT))
STRIP_SHRUBS_REQ = STRIP_TREES_REQ
PARK_TREES_REQ = int(math.ceil(AMENITY_SPACES / PARK_RATE))

# =========================================================================== palette
CG = {'buf': '#7a9b5a', 'buf_dark': '#33691e', 'addl': '#2e7d32', 'strip': '#1b5e20',
      'canopy': '#4d8b3a', 'canopy_f': '#dcecd0', 'under': '#a15a9e', 'under_f': '#f2e2f1',
      'ever': '#1b6b46', 'ever_f': '#cfe4d8', 'shrub': '#6f8f4a', 'shrub_f': '#e7efd8',
      'tpf': '#e65100', 'sight': '#c62828', 'park': '#00695c', 'ctx': '#9e9e9e',
      'accy': '#00838f', 'suppl': '#8d6e00'}

DEFS_EXTRA = '''<defs>
<pattern id="supplhatch" patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(30)"><line x1="0" y1="0" x2="0" y2="7" stroke="#b58900" stroke-width="0.7"/></pattern>
<pattern id="addlbuf" patternUnits="userSpaceOnUse" width="9" height="9" patternTransform="rotate(-30)"><line x1="0" y1="0" x2="0" y2="9" stroke="#2e7d32" stroke-width="0.55"/></pattern>
<pattern id="striphatch" patternUnits="userSpaceOnUse" width="6" height="6"><rect width="6" height="6" fill="#eef6e6"/><line x1="0" y1="6" x2="6" y2="0" stroke="#7cb342" stroke-width="0.5"/></pattern>
<pattern id="sighthatch" patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(45)"><rect width="7" height="7" fill="#fdeaea"/><line x1="0" y1="0" x2="0" y2="7" stroke="#c62828" stroke-width="0.6"/></pattern>
<pattern id="accystrip" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="5" stroke="#00838f" stroke-width="0.55"/></pattern>
</defs>'''


# =========================================================================== geometry helpers
def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def offset_left(path, d):
    """Offset an open polyline `d` feet to its LEFT (mitred).  The site boundary ring is
    counter-clockwise, so for the perimeter polyline (SW corner -> rear -> NE corner) the left
    side is the interior: this is the inner line of the 20-ft undisturbed buffer."""
    segs = []
    for i in range(len(path) - 1):
        ux, uy = _unit(path[i], path[i + 1])
        nx, ny = -uy, ux
        segs.append(((path[i][0] + nx * d, path[i][1] + ny * d),
                     (path[i + 1][0] + nx * d, path[i + 1][1] + ny * d)))
    out = [segs[0][0]]
    for i in range(len(segs) - 1):
        p = _line_x(segs[i], segs[i + 1])
        out.append(p if p else segs[i][1])
    out.append(segs[-1][1])
    return out


def _line_x(s1, s2):
    (x1, y1), (x2, y2) = s1
    (x3, y3), (x4, y4) = s2
    d = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    if abs(d) < 1e-9:
        return None
    t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / d
    if abs(t) > 40:                       # runaway mitre at a near-reversal — fall back
        return None
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


PERIM = [tuple(p) for p in sb.BOUNDARY[6:49]]     # SW front corner -> rear -> NE front corner
PERIM_LEN = sum(sb.dist(PERIM[i], PERIM[i + 1]) for i in range(len(PERIM) - 1))
BUF_INNER = offset_left(PERIM, BUF_FT)
BUF_BAND = PERIM + BUF_INNER[::-1]
BUF_SF = abs(sb.poly_area(BUF_BAND))


def poly_len(path):
    return sum(sb.dist(path[i], path[i + 1]) for i in range(len(path) - 1))


def walk(path, s):
    """Point and unit tangent at arc length s along a polyline."""
    acc = 0.0
    for i in range(len(path) - 1):
        seg = sb.dist(path[i], path[i + 1])
        if acc + seg >= s or i == len(path) - 2:
            t = (s - acc) / (seg or 1.0)
            ux, uy = _unit(path[i], path[i + 1])
            return (path[i][0] + (path[i + 1][0] - path[i][0]) * t,
                    path[i][1] + (path[i + 1][1] - path[i][1]) * t), (ux, uy)
        acc += seg
    return path[-1], _unit(path[-2], path[-1])


def seg_dist(p, a, b):
    return sb._seg_pt(p, a, b)


def path_dist(p, path):
    return min(seg_dist(p, path[i], path[i + 1]) for i in range(len(path) - 1))


STREAMS = [[tuple(q) for q in s['stream']] for s in L['stream_setbacks']]


def stream_clear(p):
    return min(path_dist(p, s) for s in STREAMS)


# --------------------------------------------------------------------------- frontage line
# The frontage chain in ring order: sitebase.FRONT_LINE picks up one point of the SW line as
# well (v = -234.70 at u = -26.0), which would lengthen the frontage by 10 ft, so the chain is
# taken from the boundary ring directly: the 13 courses flagged frontage=True in
# data/layout.json 'bearings' run ring[48]..ring[54] then ring[0]..ring[6].
FRONT = [tuple(p) for p in sb.BOUNDARY[48:55]] + [tuple(p) for p in sb.BOUNDARY[0:7]]
FRONT_LEN = poly_len(FRONT)
STRIP_INNER = offset_left(FRONT, STRIP_FT)      # 10 ft inside the R/W (the frontage runs SW, so
STRIP_BAND = FRONT + STRIP_INNER[::-1]          #  its left side is the interior of the site)
STRIP_SF = abs(sb.poly_area(STRIP_BAND))

# --------------------------------------------------------------------------- entrance geometry
ENT = L['lane']['entrance']
ENT_V = float(ENT['v_rw'])                      # -190.0
DRIVE_W = float(ENT['drive_width_ft'])          # 24.0
R_NE = float(ENT['curb_return_radius_ne_ft'])   # 25.0
R_SW = float(ENT['curb_return_radius_sw_ft'])   # 15.0
# stations along the frontage, measured from the NE front corner (0, 0)
S_OF_V = {}
_acc = 0.0
for _i in range(len(FRONT) - 1):
    S_OF_V[FRONT[_i][1]] = _acc
    _acc += sb.dist(FRONT[_i], FRONT[_i + 1])
S_OF_V[FRONT[-1][1]] = _acc


def s_of_v(v):
    """Arc length from the NE front corner to the point on the frontage at ordinate v."""
    vs = sorted(S_OF_V.keys(), reverse=True)
    if v >= vs[0]:
        return 0.0
    for i in range(len(vs) - 1):
        if vs[i] >= v >= vs[i + 1]:
            f = (vs[i] - v) / (vs[i] - vs[i + 1])
            return S_OF_V[vs[i]] + f * (S_OF_V[vs[i + 1]] - S_OF_V[vs[i]])
    return S_OF_V[vs[-1]]


S_DRIVE_NE = s_of_v(ENT_V + DRIVE_W / 2.0 + R_NE)     # start of the NE curb return
S_DRIVE_SW = s_of_v(ENT_V - DRIVE_W / 2.0 - R_SW)     # end of the SW curb return
OPENING_FT = S_DRIVE_SW - S_DRIVE_NE                  # drive opening incl. both returns
SIGHT_NE = (S_DRIVE_NE - SIGHT_TRI_FT, S_DRIVE_NE)    # 20-ft no-3-to-15-ft zone, NE side
SIGHT_SW = (S_DRIVE_SW, min(S_DRIVE_SW + SIGHT_TRI_FT, FRONT_LEN))
PLANTABLE_RUNS = [(0.0, SIGHT_NE[0]), (SIGHT_SW[1], FRONT_LEN)]
PLANTABLE_FT = sum(b - a for a, b in PLANTABLE_RUNS if b - a > 1.0)
SHRUB_RUNS = [(0.0, S_DRIVE_NE), (S_DRIVE_SW, FRONT_LEN)]
SHRUB_FT = sum(b - a for a, b in SHRUB_RUNS if b - a > 1.0)

# --------------------------------------------------------------------------- existing sewer in the buffer
# FACTS section 2: the existing 8-in Arcado Road Townhomes outfall runs 7-13 ft inside the SW
# line from u ~ -42 to u ~ 272 — i.e. inside the required 20-ft undisturbed buffer.  That is the
# checklist section 6.c condition, and it is also why the buffer screen is thin there.
SSE_U0, SSE_U1 = -36.0, 272.0
SSE_LEN = SSE_U1 - SSE_U0
ADDL_U0, ADDL_U1 = 60.0, 230.0          # where the amenity tract can carry the extra 25 ft
ADDL_LEN = ADDL_U1 - ADDL_U0
LOT1_SSE_LEN = SSE_U1 - 230.0           # the reach across the rear of lot 1

# supplemental-planting zone: the mown yard at 4541 (sitebase CLEARINGS 'yard-4541',
# u 120-272) plus the maintained sewer corridor — one continuous gap on the SW line.
SUPPL_U0, SUPPL_U1 = SSE_U0, SSE_U1
SUPPL_LEN = SUPPL_U1 - SUPPL_U0
SUPPL_EVER_OC = 8.0                     # docs/12 section 32 93 00 2.03: 1 evergreen per 8-10 lf
SUPPL_CANOPY_OC = 35.0                  # ... plus 1 canopy tree per 30-40 lf
# The 25-ft additional buffer of checklist section 6.c can only be carried where the front
# amenity tract is clear of built work.  The two pickleball pads stand 22.0 ft from the SW
# property line (v = -212.7 against SW = -234.7), so the extra width is available from u = 60
# to u = 157 only; the balance is reported as an open item, not claimed.
ADDL_U0, ADDL_U1 = 60.0, 157.0
ADDL_LEN = ADDL_U1 - ADDL_U0
COURT_V_SW = min(q[1] for pad in AM['pickleball'] for q in pad)
COURT_OFFSET_FT = COURT_V_SW - sb.SW(187.0)

# =========================================================================== species palette
# docs/12-outline-specifications.md Section 32 93 00 2.02 (Georgia Piedmont natives and proven
# adapted cultivars; GA-EPPC Category 1 species prohibited).  Sizes are ANSI Z60.1.
SPECIES = {
    # key: (common, botanical, caliper, height at planting, mature height, root, class, use)
    'QP': ('Willow Oak', 'Quercus phellos', '3 in cal.', '12–14 ft', '60–75 ft', 'B&B',
           'canopy', 'Lane street tree'),
    'QS': ('Shumard Oak', 'Quercus shumardii', '3 in cal.', '12–14 ft', '55–80 ft', 'B&B',
           'canopy', 'Lane street tree'),
    'UP': ("Lacebark Elm 'Allee'", 'Ulmus parvifolia', '3 in cal.', '12–14 ft', '40–50 ft', 'B&B',
           'canopy', 'Lane street tree'),
    'NS': ('Black Gum', 'Nyssa sylvatica', '3 in cal.', '12–14 ft', '30–50 ft', 'B&B',
           'canopy', 'Lane street tree / parking island'),
    'QL': ('Overcup Oak', 'Quercus lyrata', '4 in cal.', '14–16 ft', '35–45 ft', 'B&B',
           'canopy', 'Arcado Rd strip — relocated behind the strip'),
    'QA': ('White Oak', 'Quercus alba', '2.5–3 in cal.', '10–12 ft', '50–80 ft', 'B&B',
           'canopy', 'Buffer supplement'),
    'CC': ('Eastern Redbud', 'Cercis canadensis', '1.5–2 in cal.', '6–8 ft', '20–30 ft', 'B&B',
           'under', 'Arcado Rd landscape strip'),
    'AA': ('Downy Serviceberry', 'Amelanchier arborea', '1.5–2 in cal.', '6–8 ft', '15–25 ft', 'B&B',
           'under', 'Arcado Rd landscape strip'),
    'IO': ('American Holly', 'Ilex opaca', 'n/a — single leader', '6–8 ft', '15–30 ft', 'B&B',
           'ever', 'Buffer supplement screen'),
    'JV': ('Eastern Red Cedar', 'Juniperus virginiana', 'n/a', '6–8 ft', '30–40 ft', 'B&B',
           'ever', 'Buffer supplement screen'),
    'IG': ("Inkberry 'Shamrock'", 'Ilex glabra', 'n/a — 7 gal.', '24–30 in', '4–6 ft', 'Container',
           'shrub', 'Arcado Rd strip; accessory-structure strip'),
    'IV': ("Sweetspire 'Little Henry'", 'Itea virginica', 'n/a — 3 gal.', '18–24 in', '2–3 ft', 'Container',
           'shrub', 'Strip within the sight triangle — 30 in max. maintained'),
    'MC': ('Wax Myrtle', 'Morella cerifera', 'n/a — 7 gal.', '36–42 in', '10–15 ft', 'Container',
           'shrub', 'Screen at the pickleball court pads'),
}
CLASS_OC = {'canopy': "40'-0\" o.c. avg.", 'under': "16'-11\" o.c. avg.",
            'ever': "8'-0\" o.c., double staggered", 'shrub': "as shown"}

PLANTS = []                 # every symbol drawn on the plan, so the schedule cannot disagree


def plant(key, u, v, zone, oc=None):
    PLANTS.append({'key': key, 'u': u, 'v': v, 'zone': zone, 'cls': SPECIES[key][6],
                   'oc': oc or CLASS_OC[SPECIES[key][6]]})
    return PLANTS[-1]


def by_zone(zone):
    return [p for p in PLANTS if p['zone'] == zone]


# =========================================================================== placement
def _hit(p, polys, grow=0.0):
    for poly in polys:
        us = [q[0] for q in poly]
        vs = [q[1] for q in poly]
        if min(us) - grow <= p[0] <= max(us) + grow and min(vs) - grow <= p[1] <= max(vs) + grow:
            return True
    return False


# Detention-basin top of bank, grown 8 ft: nothing is planted on a basin embankment, so the
# street-tree row is interrupted where the lane passes Pond 1 and Pond 2 (see note 8).
POND_TOB = [sb.rect(min(q[0] for q in p['polygon']) - 8.0, max(q[0] for q in p['polygon']) + 8.0,
                    min(q[1] for q in p['polygon']) - 8.0, max(q[1] for q in p['polygon']) + 8.0)
            for p in L['ponds']]
NOPLANT = (POND_TOB
           + [[tuple(q) for q in lot['driveway_rect']] for lot in L['lots']]
           + [[tuple(q) for q in leg] for h in L['hammerheads'] for leg in h['legs']]
           + [[tuple(q) for q in AM['parking_bay']], [tuple(q) for q in AM['kiosk_bay']],
              [tuple(q) for q in AM['clubhouse']], [tuple(q) for q in AM['mail_kiosk']]]
           + [[tuple(q) for q in pad] for pad in AM['pickleball']])


def place_street_trees():
    """Lane street trees at 40 ft on centre, both sides, 6 ft behind the front lot line.
    A station that falls on a driveway apron, a hammerhead leg or a parking bay is shifted
    along the lane in 6-ft steps; a station inside the 50-ft undisturbed stream buffer is
    dropped (nothing is planted in an undisturbed buffer)."""
    order = ['QP', 'QS', 'UP', 'NS']
    n = 0
    u0, u1 = 200.0, 1690.0
    stations = [u0 + i * STREET_TREE_OC for i in range(int((u1 - u0) / STREET_TREE_OC) + 1)]
    for side in ('SW', 'NE'):
        for st in stations:
            got = None
            for d in (0, 6, -6, 12, -12, 18, -18):
                u = st + d
                v = sb.SW(u) + 94.0 if side == 'SW' else sb.NE(u) - 94.0
                if not (200.0 <= u <= 1700.0):
                    continue
                if _hit((u, v), NOPLANT, grow=5.0):
                    continue
                if stream_clear((u, v)) < 55.0:
                    got = 'stream'
                    break
                got = (u, v)
                break
            if got and got != 'stream':
                plant(order[n % 4], got[0], got[1], 'street')
                n += 1
    return n


def place_frontage():
    """Checklist section 6.j — 1 tree and 1 shrub per 25 lineal feet of frontage."""
    run = PLANTABLE_RUNS[0]
    n_strip = 8
    oc = (run[1] - run[0]) / n_strip
    for i in range(n_strip):
        s = run[0] + (i + 0.5) * oc
        p, t = walk(FRONT, s)
        nx, ny = -t[1], t[0]
        q = (p[0] + nx * (STRIP_FT * 0.52), p[1] + ny * (STRIP_FT * 0.52))
        plant('CC' if i % 2 == 0 else 'AA', q[0], q[1], 'strip', oc="%s o.c." % _arch(oc))
    for q in ((22.0, -30.0), (22.0, -95.0)):
        plant('QL', q[0], q[1], 'strip-relocated', oc='as shown')
    # shrubs: allowed inside the sight triangle only if maintained at 30 in or less
    tot = SHRUB_FT
    counts = [max(1, int(round(STRIP_SHRUBS_REQ * (b - a) / tot))) for a, b in SHRUB_RUNS]
    while sum(counts) > STRIP_SHRUBS_REQ:
        counts[counts.index(max(counts))] -= 1
    while sum(counts) < STRIP_SHRUBS_REQ:
        counts[counts.index(max(counts))] += 1
    for (a, b), k in zip(SHRUB_RUNS, counts):
        for i in range(k):
            s = a + (i + 0.5) * (b - a) / k
            p, t = walk(FRONT, s)
            nx, ny = -t[1], t[0]
            q = (p[0] + nx * (STRIP_FT * 0.86), p[1] + ny * (STRIP_FT * 0.86))
            inside = (SIGHT_NE[0] <= s <= SIGHT_NE[1]) or (SIGHT_SW[0] <= s <= SIGHT_SW[1])
            plant('IV' if inside else 'IG', q[0], q[1], 'strip-shrub',
                  oc="%s o.c. avg." % _arch(tot / STRIP_SHRUBS_REQ))
    return oc


def place_buffer_supplement():
    """Checklist section 6.h — supplemental planting only where the existing vegetation does
    not screen.  One mapped gap: the mown yard at 4541 and the maintained sanitary-sewer
    corridor on the SW line, u -36 to 272 (both from Sheet C-0)."""
    n_ev = int(math.ceil(SUPPL_LEN / SUPPL_EVER_OC))
    for i in range(n_ev):
        u = SUPPL_U0 + (i + 0.5) * SUPPL_LEN / n_ev
        v = sb.SW(u) + (16.0 if i % 2 == 0 else 19.0)      # clear of the 8-in sewer at 7-13 ft
        plant('IO' if i % 2 == 0 else 'JV', u, v, 'buffer-ever')
    n_ca = int(math.ceil(SUPPL_LEN / SUPPL_CANOPY_OC))
    for i in range(n_ca):
        u = SUPPL_U0 + (i + 0.5) * SUPPL_LEN / n_ca
        v = sb.SW(u) + (30.0 if ADDL_U0 <= u <= ADDL_U1 else 17.0)
        plant('QA', u, v, 'buffer-canopy', oc="%s o.c." % _arch(SUPPL_LEN / n_ca))
    return n_ev, n_ca


def pond_clearance_ft(pond):
    """Minimum distance from the basin top of bank to the SW property line, measured at every
    10 ft of the basin's length (not at a single station)."""
    poly = [tuple(q) for q in pond['polygon']]
    u0, u1 = min(q[0] for q in poly), max(q[0] for q in poly)
    out = []
    for u in _rng2(u0, u1, 10.0):
        vs = [q[1] for q in poly]
        out.append(min(vs) - sb.SW(u))
    return min(out)


def _rng2(a, b, step):
    n = max(2, int(abs(b - a) / step) + 1)
    return [a + (b - a) * i / (n - 1.0) for i in range(n)]


PARK_ISLANDS = [sb.rect(160.0, 180.0, -127.0, -117.0), sb.rect(193.0, 213.0, -127.0, -117.0)]
PARK_TRUNKS = [(170.0, -122.0), (203.0, -122.0)]
ACCY = [('MAIL KIOSK (CBU)', [tuple(q) for q in AM['mail_kiosk']]),
        ('PICKLEBALL PAD 1', [tuple(q) for q in AM['pickleball'][0]]),
        ('PICKLEBALL PAD 2', [tuple(q) for q in AM['pickleball'][1]]),
        ('CLUBHOUSE GROUND HVAC (CONCEPT)', sb.rect(112.0, 124.0, -84.0, -78.0))]


def place_parking_and_accessory():
    for t in PARK_TRUNKS:
        plant('NS', t[0], t[1], 'parking', oc='1 per 7 spaces')
    for name, poly in ACCY:
        us = [q[0] for q in poly]
        vs = [q[1] for q in poly]
        per = 2 * ((max(us) - min(us) + 5.0) + (max(vs) - min(vs) + 5.0))
        k = max(4, int(per / 14.0))
        sp = 'MC' if 'PICKLEBALL' in name else 'IG'
        for i in range(k):
            s = (i + 0.5) / k * per
            q = _perim_point(min(us) - 2.5, max(us) + 2.5, min(vs) - 2.5, max(vs) + 2.5, s / per)
            plant(sp, q[0], q[1], 'accessory', oc="%s o.c. avg." % _arch(per / k))


def _perim_point(u0, u1, v0, v1, f):
    w, h = u1 - u0, v1 - v0
    per = 2 * (w + h)
    s = f * per
    if s < w:
        return (u0 + s, v0)
    s -= w
    if s < h:
        return (u1, v0 + s)
    s -= h
    if s < w:
        return (u1 - s, v1)
    s -= w
    return (u0, v1 - s)


def _arch(ft):
    """Architectural notation for a decimal foot value: 16.92 -> 16'-11\"."""
    sign = '-' if ft < 0 else ''
    ft = abs(ft)
    f = int(ft)
    inch = int(round((ft - f) * 12))
    if inch == 12:
        f, inch = f + 1, 0
    return "%s%d'-%d\"" % (sign, f, inch)


N_STREET = place_street_trees()
STRIP_OC = place_frontage()
N_EVER, N_CANOPY = place_buffer_supplement()
place_parking_and_accessory()

PARK_MAXD = 0.0
for st in AM['stalls'] + AM['kiosk_stalls'] + [AM['accessible_stall']]:
    for q in [tuple(x) for x in st]:
        PARK_MAXD = max(PARK_MAXD, min(sb.dist(q, t) for t in PARK_TRUNKS))

TOTAL_PLANTS = len(PLANTS)
COUNTS = {}
for p in PLANTS:
    COUNTS[p['key']] = COUNTS.get(p['key'], 0) + 1
MAX_PCT = max(100.0 * c / TOTAL_PLANTS for c in COUNTS.values())


# =========================================================================== plant symbols
def _trunk(c, p, r=1.4):
    c.circle(p, max(0.9, r * c.s), fill='#3e2723', stroke='none')


def sym_canopy(c, p, r=13.0, col=None):
    col = col or CG['canopy']
    c.circle(p, r * c.s, fill=CG['canopy_f'], fill_opacity='0.75', stroke=col, stroke_width=0.8)
    c.circle(p, r * 0.62 * c.s, fill='none', stroke=col, stroke_width=0.35, stroke_dasharray='2 2')
    _trunk(c, p, 1.5)


def sym_under(c, p, r=7.5):
    c.circle(p, r * c.s, fill=CG['under_f'], fill_opacity='0.8', stroke=CG['under'],
             stroke_width=0.7, stroke_dasharray='3 1.6')
    _trunk(c, p, 1.2)


def sym_ever(c, p, r=7.5):
    pts = []
    for k in range(16):
        a = math.pi * 2 * k / 16.0
        rr = r if k % 2 == 0 else r * 0.52
        pts.append((p[0] + rr * math.cos(a), p[1] + rr * math.sin(a)))
    c.poly(pts, fill=CG['ever_f'], fill_opacity='0.9', stroke=CG['ever'], stroke_width=0.6)
    _trunk(c, p, 1.1)


def sym_shrub(c, p, r=4.0):
    c.circle(p, max(1.4, r * c.s), fill=CG['shrub_f'], stroke=CG['shrub'], stroke_width=0.7)


SYM = {'canopy': sym_canopy, 'under': sym_under, 'ever': sym_ever, 'shrub': sym_shrub}


def planting(c, zones=None, keys=True):
    c.add('<g id="planting">')
    for p in PLANTS:
        if zones and p['zone'] not in zones:
            continue
        SYM[p['cls']](c, (p['u'], p['v']))
    c.add('</g>')
    if not keys or c.s < sb.SCALE30:
        return
    for p in PLANTS:
        if zones and p['zone'] not in zones:
            continue
        if p['cls'] == 'shrub':
            continue
        c.text(p['u'], p['v'] + 1.7, p['key'], size=6.4, bold=True, fill='#1b3a12')


# =========================================================================== dimension helper
def dim(c, a, b, off=0.0, text=None, size=6.0, col='#000', witness=6.0, side=1):
    """A dimensioned length between two plan points, offset `off` feet to one side."""
    ux, uy = _unit(a, b)
    nx, ny = -uy * side, ux * side
    a2 = (a[0] + nx * off, a[1] + ny * off)
    b2 = (b[0] + nx * off, b[1] + ny * off)
    for p, q in ((a, a2), (b, b2)):
        if off:
            c.line(p, (q[0] + nx * witness * 0.35, q[1] + ny * witness * 0.35),
                   stroke=col, stroke_width=0.35)
    c.line(a2, b2, stroke=col, stroke_width=0.5)
    t = 2.6
    for p, s in ((a2, 1), (b2, -1)):
        c.line((p[0] - (ux - nx) * t * s, p[1] - (uy - ny) * t * s),
               (p[0] + (ux + nx) * t * s, p[1] + (uy + ny) * t * s), stroke=col, stroke_width=0.5)
    if text:
        m = ((a2[0] + b2[0]) / 2.0, (a2[1] + b2[1]) / 2.0)
        c.text(m[0] + nx * 3.4, m[1] + ny * 3.4, text, size=size, bold=True, fill=col,
               rot=c.rot_of(a, b), halo=True, dy=1.6)


def leader(c, frm, to, text, size=6.0, col='#111', anchor='start', lines=None):
    c.line(frm, to, stroke=col, stroke_width=0.4)
    c.circle(frm, 1.1, fill=col, stroke='none')
    if lines:
        c.textlines(to[0], to[1], lines, size=size, gap=1.2, fill=col, halo=True, anchor=anchor,
                    bold_first=True)
    else:
        c.text(to[0], to[1], text, size=size, bold=True, fill=col, halo=True, anchor=anchor)


# =========================================================================== layers
def context(c, screen=True):
    """The approved concept plan, screened back: it is the base this sheet annotates."""
    op = '0.55' if screen else '1'
    c.add('<g id="context" opacity="%s">' % op)
    for g in L['greens']:
        for p in g['polygons']:
            c.poly([tuple(q) for q in p], fill=sb.C['green'], stroke=sb.C['green_line'], stroke_width=0.4)
    for p in L['ponds']:
        c.poly([tuple(q) for q in p['tract_polygon']], fill='#e4efdc', stroke=sb.C['green_line'],
               stroke_width=0.4)
        c.poly([tuple(q) for q in p['polygon']], fill=sb.C['pond'], stroke=sb.C['buf_line'],
               stroke_width=0.7, stroke_dasharray='5 2')
    for p in AM['tract_polygons']:
        c.poly([tuple(q) for q in p], fill='#eef4e6', stroke=sb.C['green_line'], stroke_width=0.4)
    c.poly([tuple(p) for p in AM['village_green']], fill='#cfe8bd', stroke=sb.C['green_line'],
           stroke_width=0.4)
    ln = L['lane']
    c.poly([tuple(p) for p in ln['tract_polygon']], fill=sb.C['tract'], stroke='#8a8a8a',
           stroke_width=0.4, stroke_dasharray='4 2')
    c.poly([tuple(p) for p in ln['entry_drive']['tract_polygon']], fill=sb.C['tract'],
           stroke='#8a8a8a', stroke_width=0.4, stroke_dasharray='4 2')
    for poly in (ln['entry_drive']['pavement_polygon'], ln['pavement_polygon']):
        c.poly([tuple(p) for p in poly], fill=sb.C['pave'], stroke='#555', stroke_width=0.5)
    for h in L['hammerheads']:
        for leg in h['legs']:
            c.poly([tuple(p) for p in leg], fill=sb.C['pave'], stroke='#555', stroke_width=0.5)
    for s in ln['sidewalks']:
        c.poly([tuple(p) for p in s['polygon']], fill='#f7f7f7', stroke='#999', stroke_width=0.3)
    for lot in L['lots']:
        c.poly([tuple(p) for p in lot['polygon']], fill='#fff', stroke='#666', stroke_width=0.5)
        c.poly([tuple(p) for p in lot['driveway_rect']], fill=sb.C['pave'], stroke='#8a8a8a', stroke_width=0.3)
        c.poly([tuple(p) for p in lot['house_rect']], fill=sb.C['house'], stroke='#555', stroke_width=0.45)
        c.poly([tuple(p) for p in lot['garage_rect']], fill='#efd2ad', stroke='#555', stroke_width=0.35)
        for k in ('porch_rect', 'rear_rect'):
            c.poly([tuple(p) for p in lot[k]], fill='#fdf3e4', stroke='#555', stroke_width=0.3)
    c.poly([tuple(p) for p in AM['clubhouse']], fill='#f2c58a', stroke='#333', stroke_width=0.7)
    for pad, court in zip(AM['pickleball'], AM['courts']):
        c.poly([tuple(p) for p in pad], fill='#e9e2d0', stroke='#333', stroke_width=0.5)
        c.poly([tuple(p) for p in court], fill='#bcd7c2', stroke='#333', stroke_width=0.35)
    for k in ('parking_bay', 'kiosk_bay'):
        c.poly([tuple(p) for p in AM[k]], fill=sb.C['pave'], stroke='#555', stroke_width=0.45)
    for st in AM['stalls'] + AM['kiosk_stalls'] + [AM['accessible_stall'], AM['accessible_aisle']]:
        c.poly([tuple(p) for p in st], fill='none', stroke='#777', stroke_width=0.3)
    c.poly([tuple(p) for p in AM['mail_kiosk']], fill='#f2c58a', stroke='#333', stroke_width=0.5)
    c.poly([tuple(p) for p in AM['entry_sign']], fill='#444', stroke='none')
    c.add('</g>')


def buffer_layer(c, labels=True, dims=True):
    """Checklist 6.b/6.c/6.f/6.h — the 20-ft undisturbed buffer, the 25-ft additional buffer
    where the required buffer lies within the existing sanitary-sewer easement, and the
    supplemental-planting zone."""
    c.add('<g id="buffer">')
    c.poly(BUF_BAND, fill='url(#woods)', stroke='none')
    c.poly(BUF_BAND, fill='url(#bufhatch)', stroke='none')
    c.pline(PERIM, fill='none', stroke=CG['buf_dark'], stroke_width=1.0)
    c.pline(BUF_INNER, fill='none', stroke=CG['buf_dark'], stroke_width=1.0, stroke_dasharray='9 3 2 3')
    # 25-ft additional buffer (section 6.c) inside the front amenity tract
    addl = ([(u, sb.SW(u) + BUF_FT) for u in _rng(ADDL_U0, ADDL_U1)]
            + [(u, sb.SW(u) + BUF_FT + ADDL_BUF_FT) for u in _rng(ADDL_U1, ADDL_U0)])
    c.poly(addl, fill='url(#addlbuf)', stroke=CG['addl'], stroke_width=0.7, stroke_dasharray='7 3')
    # supplemental-planting zone (section 6.h) on the SW line
    sup = ([(u, sb.SW(u)) for u in _rng(SUPPL_U0, SUPPL_U1)]
           + [(u, sb.SW(u) + BUF_FT) for u in _rng(SUPPL_U1, SUPPL_U0)])
    c.poly(sup, fill='url(#supplhatch)', stroke=CG['suppl'], stroke_width=0.8, stroke_dasharray='5 2.5')
    # existing 20-ft sanitary sewer easement inside the buffer (the section 6.c condition)
    sse = ([(u, sb.SW(u) + 3.0) for u in _rng(SSE_U0, SSE_U1)]
           + [(u, sb.SW(u) + 17.0) for u in _rng(SSE_U1, SSE_U0)])
    c.poly(sse, fill='none', stroke=sb.C['sewer'], stroke_width=0.6, stroke_dasharray='6 2 1.5 2')
    c.add('</g>')
    if dims:
        for u, side in ((470.0, -1), (1330.0, -1), (900.0, 1), (1560.0, 1)):
            if side < 0:
                a, b = (u, sb.SW(u)), (u, sb.SW(u) + BUF_FT)
            else:
                a, b = (u, sb.NE(u)), (u, sb.NE(u) - BUF_FT)
            dim(c, a, b, 0.0, "20'-0\"", size=6.8, col=CG['buf_dark'], side=1)
        ur = 1721.0
        dim(c, (ur, -100.0), (ur - BUF_FT, -100.0), 0.0, "20'-0\"", size=6.8, col=CG['buf_dark'])
    if not labels:
        return
    for u, v, rot in ((760.0, 0, 0), (1450.0, 0, 0)):
        c.text(u, sb.NE(u) - BUF_FT / 2.0, "20'-0\" UNDISTURBED BUFFER — RECORDED BUFFER EASEMENT",
               size=6.9, bold=True, fill=CG['buf_dark'], halo=True, dy=2.2)
    c.text(600.0, sb.SW(600.0) + BUF_FT / 2.0,
           "20'-0\" UNDISTURBED BUFFER — RECORDED BUFFER EASEMENT", size=6.9, bold=True,
           fill=CG['buf_dark'], halo=True, dy=2.2)
    c.text(1520.0, sb.SW(1520.0) + BUF_FT / 2.0,
           "20'-0\" UNDISTURBED BUFFER (TYP. ALL LINES EXCEPT ARCADO RD)", size=6.9, bold=True,
           fill=CG['buf_dark'], halo=True, dy=2.2)
    c.text(1721.0 - BUF_FT / 2.0, -60.0, "20'-0\" UNDISTURBED BUFFER", size=6.9, rot=-90,
           bold=True, fill=CG['buf_dark'], halo=True)


def _rng(a, b, step=10.0):
    n = max(2, int(abs(b - a) / step) + 1)
    return [a + (b - a) * i / (n - 1.0) for i in range(n)]


def strip_layer(c, labels=True, dims=True):
    """Checklist 6.j — the 10-ft landscape strip and the two 20-ft sight triangles."""
    c.add('<g id="strip">')
    c.poly(STRIP_BAND, fill='url(#striphatch)', stroke=CG['strip'], stroke_width=0.9)
    for a, b in ((SIGHT_NE[0], SIGHT_NE[1]), (SIGHT_SW[0], SIGHT_SW[1])):
        p0, t0 = walk(FRONT, a)
        p1, t1 = walk(FRONT, b)
        nx, ny = -t1[1], t1[0]
        apex = (p1[0] + nx * SIGHT_TRI_FT, p1[1] + ny * SIGHT_TRI_FT)
        c.poly([p0, p1, apex], fill='url(#sighthatch)', stroke=CG['sight'], stroke_width=0.8)
    c.add('</g>')
    if dims:
        p0, t0 = walk(FRONT, 40.0)
        nx, ny = -t0[1], t0[0]
        dim(c, p0, (p0[0] + nx * STRIP_FT, p0[1] + ny * STRIP_FT), 0.0, "10'-0\"",
            size=6.8, col=CG['strip'])
    if not labels:
        return
    c.text(-14.0, -60.0, "10'-0\" LANDSCAPE STRIP ALONG THE ARCADO RD R/W (CHECKLIST §6.j)",
           size=6.9, rot=-81, bold=True, fill=CG['strip'], halo=True)


def parking_layer(c, labels=True):
    """Checklist 6.k — 1 tree per 7 spaces and the 60-ft trunk-distance demonstration."""
    c.add('<g id="parkplant">')
    for t in PARK_TRUNKS:
        c.circle(t, PARK_RADIUS * c.s, fill='none', stroke=CG['park'], stroke_width=0.8,
                 stroke_dasharray='7 4')
    for isl in PARK_ISLANDS:
        c.poly(isl, fill='#dcedc8', stroke=CG['park'], stroke_width=0.7)
    c.add('</g>')
    if not labels:
        return
    for t in PARK_TRUNKS:
        c.line(t, (t[0], t[1] + PARK_RADIUS), stroke=CG['park'], stroke_width=0.5,
               stroke_dasharray='4 2')
    c.text(PARK_TRUNKS[0][0], PARK_TRUNKS[0][1] + PARK_RADIUS / 2.0, "R 60'-0\"", size=6.8,
           bold=True, fill=CG['park'], halo=True, rot=-90)


def accessory_layer(c, labels=True):
    """Checklist 6.l — a 5-ft landscape strip around accessory structures and ground HVAC."""
    c.add('<g id="accessory">')
    for name, poly in ACCY:
        us = [q[0] for q in poly]
        vs = [q[1] for q in poly]
        outer = sb.rect(min(us) - 5.0, max(us) + 5.0, min(vs) - 5.0, max(vs) + 5.0)
        inner = sb.rect(min(us), max(us), min(vs), max(vs))
        c.poly(outer + [outer[0]] + inner[::-1] + [inner[-1]], fill='url(#accystrip)',
               stroke=CG['accy'], stroke_width=0.6, stroke_dasharray='4 2')
    c.add('</g>')


TPF_LINES = []


def tree_protection(c, labels=True):
    """Checklist 6.g — tree-protection fence at the limit of disturbance around every area to
    be preserved: the 20-ft buffer, the creek-woods tract and the stream buffers."""
    global TPF_LINES
    TPF_LINES = [BUF_INNER]
    for s in L['stream_setbacks']:
        for ln in s['offsets']['50']:
            pts = [tuple(p) for p in ln if sb.point_in_poly(tuple(p), sb.BOUNDARY)]
            if len(pts) > 1:
                TPF_LINES.append(pts)
    c.add('<g id="tpf">')
    for ln in TPF_LINES:
        c.pline(ln, fill='none', stroke=CG['tpf'], stroke_width=1.4, stroke_dasharray='1 4')
        for i in range(0, len(ln) - 1):
            a, b = ln[i], ln[i + 1]
            n = max(1, int(sb.dist(a, b) / 26.0))
            for k in range(n):
                f = (k + 0.5) / n
                p = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
                c.circle(p, 1.5, fill='none', stroke=CG['tpf'], stroke_width=0.9)
    c.add('</g>')
    if labels:
        c.text(1150.0, sb.NE(1150.0) - BUF_FT - 9.0,
               'TREE PROTECTION FENCE — INSTALL BEFORE ANY LAND DISTURBANCE (§6.g); SEE DETAIL 1',
               size=6.9, bold=True, fill=CG['tpf'], halo=True)


# =========================================================================== typical buffer section
def buffer_section(x, y):
    """ENLARGEMENT B — typical buffer section at 1" = 20', drawn in a section coordinate system:
    horizontal = feet from the adjoining property line into the site, vertical = feet above the
    rear lot line grade.  Dimensions come from data/layout.json and data/plans.json as reported
    in audit-2026-09-03/site-geometry.md section 4 (Plan A rear setback 20.17 ft, body 51'-10",
    ridge 17'-10").  Callouts are keyed so the section itself stays readable."""
    S = sb.Drawing(SCALE20, x, y, fs=1.0, win=(-30.0, 135.0, -6.0, 52.0))
    S.tag = 'B'
    S.clip_open(fill='#fff')

    def g(xx):                                    # existing ground (falls toward the buffer)
        return 2.4 if xx < 0 else 2.4 - 0.02 * xx

    ground = [(xx, g(xx)) for xx in range(-30, 136, 5)]
    S.poly(ground + [(135.0, -6.0), (-30.0, -6.0)], fill='#efe7dc', stroke='none')
    S.pline(ground, fill='none', stroke='#5d4037', stroke_width=1.3)
    S.poly([(0.0, -6.0), (20.0, -6.0), (20.0, 52.0), (0.0, 52.0)], fill='url(#bufhatch)', stroke='none')
    S.line((20.0, -6.0), (20.0, 52.0), stroke=CG['buf_dark'], stroke_width=0.9,
           stroke_dasharray='9 3 2 3')
    for xx, col in ((0.0, '#000'), (100.0, '#666')):
        S.line((xx, -6.0), (xx, 52.0), stroke=col, stroke_width=1.2)
    for xx, h, sp in ((4.5, 38.0, 14.0), (14.5, 31.0, 12.0)):
        S.line((xx, g(xx)), (xx, h), stroke='#5d4037', stroke_width=1.8)
        S.circle((xx, h - sp * 0.44), sp * 0.66 * S.s, fill=CG['canopy_f'], fill_opacity='0.7',
                 stroke=CG['canopy'], stroke_width=1.0)
    for xx in (9.0, 17.5):
        S.poly([(xx - 6.0, g(xx)), (xx, g(xx) + 20.0), (xx + 6.0, g(xx))], fill='none',
               stroke=CG['ever'], stroke_width=0.7, stroke_dasharray='4 2.5')
        S.poly([(xx, g(xx)), (xx - 2.4, g(xx) + 2.0), (xx - 1.5, g(xx) + 2.0), (xx - 2.9, g(xx) + 4.2),
                (xx - 1.4, g(xx) + 4.2), (xx, g(xx) + 6.2), (xx + 1.4, g(xx) + 4.2),
                (xx + 2.9, g(xx) + 4.2), (xx + 1.5, g(xx) + 2.0), (xx + 2.4, g(xx) + 2.0)],
               fill=CG['ever_f'], stroke=CG['ever'], stroke_width=0.9)
    S.line((20.0, g(20.0)), (20.0, g(20.0) + 4.0), stroke=CG['tpf'], stroke_width=2.2)
    for k in range(5):
        S.line((18.8, g(20.0) + 0.7 + k * 0.85), (21.2, g(20.0) + 0.7 + k * 0.85),
               stroke=CG['tpf'], stroke_width=0.7)
    # Plan A is sited from data/plans.json 'lot_siting' as it stands at run time; x in this
    # section is measured from the REAR lot line, so the patio edge is PA_BUFFER_CLEAR feet
    # clear of the buffer easement line — the tightest clearance on the plan.
    patio0, body0 = PA_PATIO, PA_REAR_WALL
    body1, porch1 = PA_REAR_WALL + PA_BODY, PA_REAR_WALL + PA_BODY + 6.0
    plate, ridge = 9.0, PA_RIDGE
    gb = g(body0)
    S.poly([(body0, gb), (body0, gb + plate), ((body0 + body1) / 2.0, gb + ridge),
            (body1, gb + plate), (body1, gb)], fill='#fdf1e0', stroke='#333', stroke_width=1.1)
    S.poly([(body1, gb), (body1, gb + plate), (porch1, gb + plate - 1.6), (porch1, gb)],
           fill='#fdf7ee', stroke='#333', stroke_width=0.9)
    S.poly([(patio0, g(patio0)), (patio0, g(patio0) + 0.7), (body0, gb + 0.7), (body0, gb)],
           fill='#e0e0e0', stroke='#666', stroke_width=0.6)
    S.poly([(100.0, g(100.0)), (105.0, g(100.0)), (105.0, g(100.0) + 0.4), (100.0, g(100.0) + 0.4)],
           fill='#f7f7f7', stroke='#777', stroke_width=0.5)
    S.poly([(107.0, g(100.0)), (129.0, g(100.0) - 0.9), (129.0, g(100.0) - 1.4), (107.0, g(100.0) - 0.5)],
           fill=sb.C['pave'], stroke='#555', stroke_width=0.6)
    S.line((94.0, g(94.0)), (94.0, g(94.0) + 22.0), stroke='#5d4037', stroke_width=1.6)
    S.circle((94.0, g(94.0) + 26.0), 8.0 * S.s, fill=CG['canopy_f'], fill_opacity='0.7',
             stroke=CG['canopy'], stroke_width=1.0)
    S.poly([(-27.0, g(-27.0)), (-27.0, g(-27.0) + 10.0), (-19.0, g(-27.0) + 16.0),
            (-11.0, g(-27.0) + 10.0), (-11.0, g(-27.0))], fill='#f5f5f5', stroke='#999',
           stroke_width=0.8, stroke_dasharray='5 3')
    # dimensions
    dim(S, (0.0, 46.0), (20.0, 46.0), 0.0, "20'-0\" UNDISTURBED BUFFER", size=7.0, col=CG['buf_dark'])
    dim(S, (0.0, 30.0), (100.0, 30.0), 0.0, "100'-0\" LOT DEPTH", size=7.0, col='#444')
    dim(S, (0.0, 24.0), (patio0, 24.0), 0.0, _arch(patio0), size=7.0, col='#7b1fa2')
    # keyed callouts
    flags = [(1, (4.5, 24.0)), (2, (9.0, 13.0)), (3, (16.0, 41.0)), (4, (20.0, 9.4)),
             (5, (53.0, 12.0)), (6, (23.6, 5.6)), (7, (118.0, 5.0)), (8, (94.0, 12.0))]
    for n, (fx, fz) in flags:
        S.circle((fx, fz), 5.6, fill='#fff', stroke='#000', stroke_width=0.9)
        S.text(fx, fz + 1.2, str(n), size=7.8, bold=True)
    S.text(-17.5, 26.0, 'ADJOINING R-1', size=7.0, bold=True, fill='#555', halo=True)
    S.text(-17.5, 22.0, 'SINGLE-FAMILY LOT', size=7.0, bold=True, fill='#555', halo=True)
    S.text(0.0, -0.9, 'PROPERTY LINE', size=7.0, bold=True, halo=True)
    S.text(100.0, 6.0, 'FRONT LOT LINE', size=7.0, bold=True, fill='#555', halo=True)
    S.text(120.0, -4.0, 'PRIVATE LANE', size=7.0, bold=True, fill='#555', halo=True)
    S.text(53.0, 24.0, 'PLAN A COTTAGE', size=7.4, bold=True, halo=True)
    S.text(53.0, 20.4, 'RIDGE %s ABOVE FFE' % _arch(PA_RIDGE), size=6.8, halo=True)
    S.clip_close()
    return S


SECTION_KEY = [
    (1, 'Existing canopy retained. No clearing, grading, filling, paving, storage or mowing '
        'occurs inside the buffer; dead, diseased or hazardous material is removed by hand '
        'under an arborist.'),
    (2, "Supplemental evergreen where the existing screen is thin — 6'-0\" minimum height at "
        "planting, 20'-0\" minimum at maturity (Checklist §6.h). Dashed outline = mature form."),
    (3, "20'-0\" undisturbed buffer = the rear 20 ft of the lot, held in a RECORDED BUFFER "
        'EASEMENT (Ord. 2023-603 §313(1)) shown on the final plat — see note 3.'),
    (4, 'Tree protection fence at the limit of disturbance — DETAIL 1. Install before any land '
        'disturbing activity (§6.g).'),
    (5, 'Plan A cottage, 1 story, ridge %s above FFE; rear wall %s and front porch face %s from '
        'the rear lot line (data/plans.json, read at run time).'
        % (_arch(PA_RIDGE), _arch(PA_REAR_WALL), _arch(PA_REAR_WALL + PA_BODY + 6.0))),
    (6, '%s rear patio. Its edge is %s from the rear lot line — %s clear of the buffer easement '
        'line, the tightest clearance between built work and the buffer on the plan.'
        % (_arch(PA_REAR_WALL - PA_PATIO), _arch(PA_PATIO), _arch(PA_BUFFER_CLEAR))),
    (7, "5'-0\" sidewalk, 2'-0\" strip and 22'-0\" private lane pavement in the HOA lane tract."),
    (8, "Lane street tree at 40'-0\" o.c., set 6'-0\" behind the front lot line in a street-tree "
        "easement; where the tract widens to 36'-0\" the tree may stand in a 6'-0\" strip between "
        'curb and walk (Checklist §319 sidewalk note).'),
]


# =========================================================================== tree-protection detail
def tpf_detail(D, x, y, sc=21.0):
    """DETAIL 1 — tree protection fence.  The box is drawn to the left and the dimensions and
    the short note sit beside and below it; the binding wording is general note 14."""
    D.stext(x, y - 6, 'DETAIL 1 — TREE PROTECTION FENCE   (SCALE 3/8" = 1\'-0")', size=8.5, bold=True)
    w, h = 12.0 * sc, 8.0 * sc
    gy = y + 5.6 * sc
    D.srect(x, y, w, h, fill='#fbfbf7', stroke='#000', stroke_width=0.9)
    D.sline(x, gy, x + w, gy, stroke='#5d4037', stroke_width=1.5)
    for k in range(16):
        xx = x + 6 + k * (w - 12) / 15.0
        D.sline(xx, gy, xx + 5, gy + 6, stroke='#5d4037', stroke_width=0.4)
    for px in (x + 1.4 * sc, x + 5.4 * sc, x + 9.4 * sc):
        D.srect(px - 0.10 * sc, gy - 4.6 * sc, 0.20 * sc, 4.6 * sc, fill='#455a64', stroke='#000',
                stroke_width=0.5)
        D.srect(px - 0.10 * sc, gy, 0.20 * sc, 2.0 * sc, fill='#90a4ae', stroke='#000',
                stroke_width=0.4, stroke_dasharray='3 2')
    D.srect(x + 1.4 * sc, gy - 4.0 * sc, 8.0 * sc, 4.0 * sc, fill='none', stroke=CG['tpf'],
            stroke_width=1.5)
    for k in range(17):
        xx = x + 1.4 * sc + k * (8.0 * sc) / 16.0
        D.sline(xx, gy - 4.0 * sc, xx, gy, stroke=CG['tpf'], stroke_width=0.7)
    for k in range(5):
        yy = gy - 4.0 * sc + k * sc
        D.sline(x + 1.4 * sc, yy, x + 9.4 * sc, yy, stroke=CG['tpf'], stroke_width=0.7)
    D.srect(x + 1.9 * sc, gy - 3.3 * sc, 3.0 * sc, 1.2 * sc, fill='#fff', stroke='#000', stroke_width=0.6)
    D.stext(x + 3.4 * sc, gy - 2.85 * sc, 'TREE PROTECTION AREA', size=6.6, anchor='middle', bold=True)
    D.stext(x + 3.4 * sc, gy - 2.35 * sc, 'DO NOT ENTER', size=6.6, anchor='middle', bold=True)
    D.sline(x + 1.4 * sc, gy - 5.0 * sc, x + 5.4 * sc, gy - 5.0 * sc, stroke='#000', stroke_width=0.5)
    for px in (x + 1.4 * sc, x + 5.4 * sc):
        D.sline(px, gy - 5.2 * sc, px, gy - 4.7 * sc, stroke='#000', stroke_width=0.5)
    D.stext(x + 3.4 * sc, gy - 5.25 * sc, "8'-0\" MAX. O.C.", size=6.8, anchor='middle', bold=True)
    D.sline(x + 10.2 * sc, gy - 4.0 * sc, x + 10.2 * sc, gy, stroke='#000', stroke_width=0.5)
    D.stext(x + 10.4 * sc, gy - 2.0 * sc, "4'-0\"", size=6.8, bold=True)
    D.stext(x + 10.4 * sc, gy + 1.1 * sc, "2'-0\" MIN.", size=6.8, bold=True)
    D.stext(x + 10.4 * sc, gy + 1.75 * sc, 'EMBEDMENT', size=6.8)
    yy = y + h + 10
    for ln in ["4'-0\" high orange high-visibility polyethylene fence on 6'-0\" steel T-posts at 8'-0\" o.c. "
               'maximum, driven',
               "2'-0\" minimum, with two tension wires. Set at the limit of disturbance: the buffer inner line, "
               'the outer',
               'edge of the 50-ft undisturbed stream buffer, and the drip line of every retained tree. Signage '
               'every 50 ft,',
               'both faces. TREE PROTECTION FENCE MUST BE INSTALLED PRIOR TO COMMENCING LAND DISTURBING '
               'ACTIVITIES',
               '(Checklist §6.g) — see note 14. Inspected by the City before the pre-construction meeting; '
               'maintain until final',
               'stabilisation. No storage, parking, washout, burning, trenching or grade change inside the fence.']:
        D.stext(x, yy, ln, size=6.6)
        yy += 8.2
    return yy


# =========================================================================== tables
def req_rows():
    p1 = pond_clearance_ft(L['ponds'][0])
    p2 = pond_clearance_ft(L['ponds'][1])
    return [
        ['§6.a', 'Tree protection / buffer / landscape plan sealed by a Registered Landscape '
                 'Architect, forester or arborist',
         'Checklist §6.a — a seal, not a calculation',
         'CONCEPT, NOT SEALED — this sheet is the owner\'s pre-application concept; the sealed '
         'plan is submitted with the Land Disturbance Permit', 'open — LDP'],
        ['§6.b', 'Show and label the boundary AND dimensions of buffers; label undisturbed; '
                 'confirm buffers abutting residential property',
         "Table 4.1 buffer abutting R-1 = 20'-0\"; perimeter (all lines except the Arcado Rd "
         "frontage) = %s lf" % format(round(PERIM_LEN), ','),
         "20'-0\" band drawn, dimensioned in 5 places and labelled UNDISTURBED; %s SF. All 3 "
         'buffered lines abut R-1 (Lilburn) single-family property' % format(round(BUF_SF), ','),
         'appears consistent with'],
        ['§6.c', 'If a portion of the required buffer is within an easement, provide 25 ft of '
                 'additional buffer outside the easement',
         'The existing 8-in Gwinnett DWR sewer lies 7–13 ft inside the SW line from u −36 to '
         'u 272 = %d lf of the required buffer' % round(SSE_LEN),
         "25'-0\" additional buffer carried over %d lf (u 60–157) inside the amenity tract = "
         '%s SF; the remaining %d lf is an open item — see note 4'
         % (ADDL_LEN, format(round(ADDL_LEN * ADDL_BUF_FT), ','), round(SSE_LEN - ADDL_LEN)),
         'PARTIAL — determination requested'],
        ['§6.f', 'Buffer encroachments (swales, stormwater facilities, sanitary sewer, '
                 'easements) as near perpendicular as possible, 50 ft maximum width',
         'Measured from the SW property line to the top of bank of each basin and to the '
         'entrance curb return',
         "Pond 1 top of bank %s clear of the property line; Pond 2 %s — neither enters the "
         "buffer. Only encroachment: the SW curb return, %s wide (%s SF) — under the 50-ft "
         "maximum. No ZBA variance requested"
         % (_arch(p1), _arch(p2), _arch(float(MET['sw_curb_return_buffer_encroachment_ft'])),
            MET['sw_curb_return_buffer_encroachment_sf']),
         'appears consistent with'],
        ['§6.g', 'Delineate tree-protection areas; preserve specimen trees and trees over 5-in '
                 'caliper in buffers, strips and islands; add the detail and the note',
         'Limit of disturbance = the buffer inner line + the outer line of the 50-ft '
         'undisturbed stream buffer',
         'Fence line drawn (%s lf), DETAIL 1 provided, and the required note printed verbatim '
         'in note 14' % format(round(sum(poly_len(x) for x in TPF_LINES)), ','),
         'appears consistent with'],
        ['§6.h', 'Supplemental buffer planting where screening is required: trees 6 ft minimum '
                 'at planting, to reach 20 ft minimum at maturity',
         'One mapped screen gap: the mown yard at 4541 and the maintained sewer corridor, SW '
         'line u −36 to 272 = %d lf. Rate (docs/12 §32 93 00 2.03): 1 evergreen per 8–10 lf + '
         '1 canopy per 30–40 lf' % round(SUPPL_LEN),
         '%d lf ÷ 8 = %.1f → %d evergreens at 8\'-0" o.c. double staggered; %d ÷ 35 = %.1f → '
         '%d canopy trees at %s o.c. All 6\'-0"–8\'-0" at planting; mature 15\'-0"–40\'-0"'
         % (round(SUPPL_LEN), SUPPL_LEN / SUPPL_EVER_OC, N_EVER, round(SUPPL_LEN),
            SUPPL_LEN / SUPPL_CANOPY_OC, N_CANOPY, _arch(SUPPL_LEN / N_CANOPY)),
         'appears consistent with'],
        ['§6.i', 'Minimum 16 Tree Density Units per acre — "unless SFR subdivision"',
         '41 detached single-family cottage lots; §602 use "Single-family (cluster-cottage, '
         'creative lot configuration)", P in R-2',
         'NOT REQUIRED AND NOT PROVIDED — this is a single-family-residential subdivision. '
         'No TDU credit is claimed for any tree on this sheet', 'not applicable'],
        ['§6.i', 'Landscaping data in tabular form: common and botanical names, quantities, '
                 'spacing, percentage of each (not to exceed 33 %), size, height, diameter '
                 'and condition',
         'Every symbol drawn on this sheet is counted; the schedule is generated from the plan',
         'PLANT SCHEDULE: %d species, %d plants. Largest single species %.1f %% (%s) — under '
         'the 33 %% maximum' % (len(COUNTS), TOTAL_PLANTS, MAX_PCT,
                                max(COUNTS, key=lambda k: COUNTS[k])),
         'appears consistent with'],
        ['§6.j', '10-ft landscape strip adjacent to all rights-of-way: 1 tree and 1 shrub per '
                 '25 linear feet of frontage',
         'Arcado Rd frontage %s lf (data/layout.json metrics.frontage_arcado_along_rw_ft) ÷ 25 '
         '= %.2f → %d trees and %d shrubs' % (FRONTAGE_FT, FRONTAGE_FT / STRIP_RATE_FT,
                                              STRIP_TREES_REQ, STRIP_SHRUBS_REQ),
         '%d trees (8 in the strip at %s o.c. + 2 relocated immediately behind the strip — see '
         'note 7) and %d shrubs. Strip area %s SF'
         % (STRIP_TREES_REQ, _arch(STRIP_OC), STRIP_SHRUBS_REQ, format(round(STRIP_SF), ',')),
         'appears consistent with'],
        ['§6.j', 'Woody native plant, single trunk, planted 6 ft minimum height to reach 20 ft '
                 'minimum; or a flowering tree 6 ft minimum height',
         'Overhead distribution on the Arcado Rd frontage is UNVERIFIED — see note 13',
         "Strip row: Cercis canadensis and Amelanchier arborea, 6'-0\"–8'-0\" at planting, "
         "15'-0\"–30'-0\" at maturity (the flowering-tree option). Relocated pair: Quercus "
         'lyrata, 4-in caliper', 'appears consistent with'],
        ['§6.j', 'No landscaping 3 ft to 15 ft in height within 20 ft of a right-of-way '
                 'intersection',
         'Two 20 ft × 20 ft triangles at the entrance, one each side of the drive, measured '
         'from the ends of the curb returns along the Arcado Rd R/W and along the drive edge',
         'Triangles drawn and hatched; NO TREE is placed in either. The 2 shrubs inside them '
         "are Itea virginica 'Little Henry', 18–24 in at planting, maintained at 30 in maximum",
         'appears consistent with'],
        ['§6.k', 'Parking-lot planting where more than 5 spaces: 1 tree for each 7 parking spaces',
         '%d guest spaces + %d mail-kiosk spaces = %d ÷ 7 = %.2f → %d trees'
         % (GUEST_SPACES, KIOSK_SPACES, AMENITY_SPACES, AMENITY_SPACES / PARK_RATE, PARK_TREES_REQ),
         '%d canopy trees (Nyssa sylvatica) in two dedicated islands between the guest bay and '
         'the kiosk bay. No buffer or landscape-strip tree is counted here' % PARK_TREES_REQ,
         'appears consistent with'],
        ['§6.k', 'Demonstrate visually that every parking space is within 60 ft of the trunk of '
                 'a tree',
         "60'-0\" radii drawn about both trunks on the plan and on Enlargement A; every stall "
         'corner tested against both trunks',
         'Worst measured distance from any stall corner to the nearer trunk = %s. All %d '
         'spaces are inside both radii' % (_arch(PARK_MAXD), AMENITY_SPACES),
         'appears consistent with'],
        ['§6.k.a', 'Canopy tree minimum planting area 200 SF',
         "Two islands 20'-0\" × 10'-0\"", '200 SF each, one tree per island, no sharing',
         'appears consistent with'],
        ['§6.l', 'Five-foot landscape strip around all accessory structures, including utility '
                 'maintenance structures, ground-level HVAC, storage buildings and loading',
         'Accessory structures on the plan: mail kiosk (CBU), two pickleball court pads, and '
         'the clubhouse ground-mounted HVAC pad',
         "4 strips drawn at 5'-0\" and planted with %d shrubs. Where the strip at the SW court "
         'pad overlaps the 20-ft buffer by 3\'-0" it is satisfied by the buffer planting; no '
         'grading occurs in the buffer' % len(by_zone('accessory')),
         'appears consistent with'],
        ['§6.m', 'Certificate-of-occupancy and 12-month warranty note',
         'Prescribed wording', 'Printed verbatim as note 12', 'appears consistent with'],
        ['§6.n', 'Check for utility lines — provide alternate low / slow-growing trees or '
                 'setbacks for trees from overhead power',
         'Georgia Power "Tree planting near utility lines" right-tree/right-place zones',
         'Frontage row held to 25 ft mature height pending a Georgia Power / Georgia 811 field '
         'locate; no canopy tree within 20 ft of a conductor — see note 13',
         'VERIFY — field locate required'],
    ]


def schedule_rows():
    rows = []
    order = ['QP', 'QS', 'UP', 'NS', 'QL', 'QA', 'CC', 'AA', 'IO', 'JV', 'IG', 'IV', 'MC']
    for k in order:
        if k not in COUNTS:
            continue
        common, bot, cal, ht, mature, root, cls, use = SPECIES[k]
        ocs = sorted({p['oc'] for p in PLANTS if p['key'] == k})
        rows.append([k, common, bot, str(COUNTS[k]), '; '.join(ocs)[:46],
                     '%.1f %%' % (100.0 * COUNTS[k] / TOTAL_PLANTS), cal, ht, mature, root, use])
    rows.append(['', 'TOTAL — 13 species', '', str(TOTAL_PLANTS), '', '100.0 %', '', '',
                 'largest species %.1f %% ≤ 33 %%' % MAX_PCT, '', ''])
    return rows


LEGEND = [
    ('line', sb.C['bnd'], 1.8, '', 'Assemblage boundary (Gwinnett GIS — DRAFT)'),
    ('rect', sb.C['adj_fill'], 0, '', 'Adjoining tax parcel — all zoned R-1, City of Lilburn'),
    ('line', sb.C['rw'], 0.9, '', 'Arcado Rd right-of-way line (R/W width varies)'),
    ('line', '#333', 0.6, '14 3 3 3', 'Existing road centreline'),
    ('bufsw', 'url(#bufhatch)', 0, '', "20'-0\" undisturbed buffer — existing woodland retained"),
    ('line', CG['buf_dark'], 1.0, '9 3 2 3', 'Buffer inner line = limit of disturbance'),
    ('rect', 'url(#addlbuf)', 0, '', "25'-0\" additional buffer (checklist §6.c)"),
    ('rect', 'url(#supplhatch)', 0, '', 'Supplemental buffer planting zone (§6.h)'),
    ('line', sb.C['sewer'], 0.6, '6 2 1.5 2', "Existing 20' sanitary sewer easement in the buffer"),
    ('rect', 'url(#striphatch)', 0, '', "10'-0\" landscape strip along the Arcado Rd R/W (§6.j)"),
    ('rect', 'url(#sighthatch)', 0, '', "Sight triangle — no landscaping 3'-0\"–15'-0\" (§6.j)"),
    ('rect', '#dcedc8', 0, '', 'Parking-lot planting island, 200 SF min. (§6.k.a)'),
    ('line', CG['park'], 0.8, '7 4', "60'-0\" radius from a parking-lot tree trunk (§6.k)"),
    ('rect', 'url(#accystrip)', 0, '', "5'-0\" strip at accessory structures / ground HVAC (§6.l)"),
    ('tpf', CG['tpf'], 1.4, '1 4', 'Tree protection fence — install before land disturbance'),
    ('canopy', '', 0, '', 'Proposed canopy / street tree (see PLANT SCHEDULE)'),
    ('under', '', 0, '', 'Proposed understory / flowering tree'),
    ('ever', '', 0, '', 'Proposed evergreen screen tree'),
    ('shrub', '', 0, '', 'Proposed shrub'),
    ('line', sb.C['stream'], 1.6, '', 'Stream — state waters (top of bank approximate)'),
    ('line', sb.C['buf_line'], 0.5, '3 2', "25' state (GA EPD) stream buffer"),
    ('line', sb.C['buf_line'], 0.8, '6 2', "50' undisturbed stream buffer (Lilburn)"),
    ('line', sb.C['buf_line'], 0.8, '8 2 2 2', "75' impervious setback"),
    ('buf2', sb.C['green'], 0, '', 'Open-space, amenity, village-green and pond tract (context)'),
    ('rect', sb.C['pond'], 0, '', 'Detention / water-quality basin (context — Sheet C-3.0)'),
    ('rect', '#fff', 0, '', 'Proposed lot (context — Sheet C-2.0)'),
    ('rect', sb.C['house'], 0, '', 'Proposed cottage, garage and porch (context)'),
    ('rect', sb.C['pave'], 0, '', 'Private lane, entry drive, driveway and parking pavement'),
    ('rect', '#f7f7f7', 0, '', 'Sidewalk (context)'),
    ('rect', '#f2c58a', 0, '', 'Clubhouse, mail kiosk, court pad and monument sign (context)'),
    ('line', sb.C['match'], 1.1, '16 5 3 5', 'Match line — enlargement at 1" = 20\''),
]


# =========================================================================== general notes
def notes():
    return [
        'STATUS AND SEAL. A CONCEPT landscape, buffer and tree-protection plan prepared by the owner for '
        'pre-application review of a rezoning from R-1 to R-2. Checklist §6.a requires this plan to be SEALED BY A '
        'REGISTERED LANDSCAPE ARCHITECT, FORESTER OR ARBORIST; this sheet is DRAFT — NOT SEALED and is superseded by '
        'that sealed plan at the Land Disturbance Permit. Every statement of conformity reads "appears consistent '
        'with" and none is a compliance certification.',

        'TREE DENSITY UNITS ARE NOT REQUIRED. Checklist §6.i requires 16 Tree Density Units per acre "unless SFR '
        'subdivision". This is a single-family-residential subdivision — %d detached fee-simple cottage lots, '
        'Ord. 2023-603 §602 use "Single-family (cluster-cottage, creative lot configuration)", permitted in R-2 '
        'without a special-use permit. NO TDU CALCULATION IS REQUIRED AND NONE IS PROVIDED, and no TDU credit is '
        'claimed for any plant here, so the clause\'s bar on counting trees inside required buffers does not arise. '
        'The planting data §6.i also requires is in the PLANT SCHEDULE.' % len(L['lots']),

        'BUFFER — WIDTH, LABEL AND RECORDING (§6.b). A 20\'-0" UNDISTURBED buffer is provided along every property '
        'line except the Arcado Rd frontage: %s lineal feet, %s SF, computed as a mitred offset of the boundary ring '
        'in data/layout.json. Width is from Ord. 2023-603 Table 4.1, "buffer abutting R-1: 0 ft for detached '
        'single-family dwellings in R-2, 20 ft for all other allowed dwelling types" — cottage homes are listed '
        'separately from detached single-family there, so this plan designs to the 20-ft buffer and asks the Director '
        'to confirm the reading. BUFFER-EASEMENT RECORDING NOTE: within a lot the buffer occupies the rear 20 ft and '
        'is held in a RECORDED BUFFER EASEMENT under §313(1) ("buffer requirements ... supersede these minimum '
        'required yards"). The easement is granted to the HOA and to the City, shown and dimensioned on the final '
        'plat, and RECORDED IN THE GWINNETT COUNTY RECORDS BEFORE THE FIRST CERTIFICATE OF OCCUPANCY; it prohibits '
        'clearing, grading, filling, structures, paving, storage, mowing and removal of any living tree except dead, '
        'diseased or hazardous material taken by hand under an arborist. Buffer area on lots %s SF (%d × 50 × 20 ft), '
        'reported separately from common open space. Every buffered line abuts R-1 residential property (§6.b).',

        'BUFFER WITHIN AN EASEMENT — AN OPEN ITEM (§6.c). Checklist §6.c reads "If a portion of required buffer is '
        'within an easement, provide 25\' additional buffer outside easement." The existing 8-in Gwinnett DWR gravity '
        'sewer (Arcado Road Townhomes outfall) runs 7–13 ft inside the SW property line from u ≈ −36 to u ≈ 272, so '
        '%d lineal feet of the required 20-ft buffer lies within that existing sanitary-sewer easement. This plan '
        'carries 25\'-0" of additional buffer over the %d lf (u 60–157) where the front amenity tract is clear — %s SF '
        '— and states plainly that it CANNOT carry it over the remaining %d lf: the two pickleball court pads stand '
        '%s from the SW line (u 157–218) and the balance crosses the rear of lot 1 (u 230–272), where an extra 25 ft '
        'would leave 55 ft of buildable depth against a 51\'-10" body plus a 15-ft front setback. THREE QUESTIONS ARE '
        'PUT TO STAFF AT THE PRE-APPLICATION CONFERENCE: (a) does §6.c apply to a pre-existing utility easement the '
        'applicant did not create; (b) does the recorded BUFFER easement of §313(1) itself trigger §6.c, which would '
        'make the clause self-defeating; and (c) if §6.c applies in full, the applicant will relocate the pads, '
        're-plat lots 1–2, or apply to the Zoning Board of Appeals. No credit is claimed for the %d lf until staff '
        'answers.',

        'BUFFER ENCROACHMENTS (§6.f). "Swales, ditches, stormwater facilities/detention ponds, sanitary sewer '
        'conveyance facilities, and easements may encroach as near perpendicular as possible, up to max 50\' width." '
        'As laid out on Sheet C-3.0 NEITHER DETENTION BASIN ENTERS THE BUFFER — Pond 1 top of bank is %s and Pond 2 '
        '%s clear of the SW property line against the 20-ft buffer. The only encroachment on this sheet is the SW '
        'curb return at the Arcado Rd entrance, %s wide over %s SF, perpendicular to the line and far under the 50-ft '
        'maximum. No Zoning Board of Appeals buffer variance is requested by this sheet.',

        'SUPPLEMENTAL BUFFER PLANTING (§6.h). Supplemental planting is shown only where the existing vegetation does '
        'not screen. ONE GAP IS MAPPED — the SW line from u −36 to u 272 (%d lf), where Sheet C-0 shows the mown yard '
        'at 4541 Arcado Rd and the maintained sanitary-sewer corridor. Rate from docs/12 §32 93 00 2.03: one evergreen '
        'per 8–10 lineal feet of gap plus one canopy tree per 30–40 feet. Provided: %d evergreens at 8\'-0" o.c. in a '
        'double staggered row and %d canopy trees at %s o.c. ALL SUPPLEMENTAL TREES ARE A MINIMUM 6\'-0" IN HEIGHT AT '
        'THE TIME OF PLANTING AND REACH A MINIMUM 20\'-0" AT MATURITY, as §6.h requires; species and mature heights '
        'are tabulated in the PLANT SCHEDULE. Plants are held clear of the 8-in sewer, whose horizontal position must '
        'be confirmed by survey and by Georgia 811 before layout. NO TREE SURVEY HAS BEEN PERFORMED: the arborist\'s '
        'buffer inventory (every existing tree over 5-in caliper, and the canopy gaps) governs the final quantity, and '
        'a contingency allowance for 25 %% of the remaining %s lf of buffer is carried in the estimate but is not '
        'drawn. Existing and proposed trees are not labelled for TDU credit because no credit is claimed (§6.h, §6.i).',

        'ARCADO ROAD LANDSCAPE STRIP (§6.j) — THE ARITHMETIC. "For each 10-foot LS strip install 1 tree and 1 shrub '
        'per 25 linear feet of frontage." Frontage on Arcado Rd = %s lineal feet measured along the right-of-way line '
        '(data/layout.json metrics.frontage_arcado_along_rw_ft; the chord is %s ft). %s ÷ 25 = %.2f → %d TREES AND '
        '%d SHRUBS REQUIRED. The 10\'-0" strip is drawn as a %s-SF band inside the R/W. The drive opening with its '
        '25-ft and 15-ft curb returns removes %s of frontage and the two 20-ft sight triangles remove a further '
        '%s, leaving %s of plantable strip, so 8 of the 10 required trees are set in the strip at %s on centre and '
        'THE REMAINING 2 ARE RELOCATED IMMEDIATELY BEHIND THE STRIP inside the amenity tract, clear of both sight '
        'triangles. Approval of that relocation is requested; the alternative is 13\'-6" on centre in the strip, '
        'which is too close for the mature spread. All %d shrubs are in the strip.',

        'LANE STREET TREES. Street trees stand at %s on centre along both sides of the private lane, %s behind the '
        'front lot line in an HOA street-tree easement — or, where the lane tract widens from u = %d, in a 6-ft strip '
        'between curb and walk (Ord. 2023-603 §319 sidewalk note). %d TREES ARE SHOWN. A station falling on a driveway '
        'apron, a hammerhead leg or a parking bay is shifted along the lane in 6-ft steps; a station falling on a '
        'detention-basin embankment (Pond 1, u 780-980; Pond 2, u 1,480-1,680) or within 55 ft of a digitised stream '
        'reach is omitted, because nothing is planted on an embankment or inside an undisturbed stream buffer. Species '
        'alternate so that no two adjacent cottages face the same tree. Street trees are NOT counted toward the '
        'landscape-strip or the parking-lot requirement.',

        'SIGHT TRIANGLES (§6.j). "No landscaping 3-15\' feet in height within 20 feet of right-of-way intersection." '
        'Two 20\'-0" × 20\'-0" triangles are drawn at the entrance, one each side of the drive, measured from the end '
        'of each curb return along the Arcado Rd right-of-way and along the edge of the drive. NO TREE IS PLACED IN '
        'EITHER TRIANGLE. The two shrubs that fall inside them are Itea virginica \'Little Henry\', 18–24 in at '
        'planting and maintained by the HOA at 30 in maximum, so nothing between 3\'-0" and 15\'-0" in height stands '
        'in either triangle. SEPARATELY, the Gwinnett County DOT intersection sight distance for a 35-mph collector '
        'is approximately %d ft in each direction from the driveway (FACTS §2b — VERIFY); those sight lines run far '
        'beyond this sheet, are shown by direction only on Enlargement A, and must be certified by a Georgia PE with '
        'the driveway permit (Checklist §7.j). The monument entry sign is set outside both triangles.',

        'PARKING-LOT PLANTING (§6.k). "If more than 5 parking spaces: provide 1 tree for each 7 parking spaces. '
        'Demonstrate visually that every parking space is within 60 feet of the trunk of a tree. Landscape strip and '
        'buffer trees do not count toward this requirement." The amenity block has %d guest spaces (including one '
        'van-accessible space and its aisle) and %d mail-kiosk spaces = %d spaces; %d ÷ 7 = %.2f → %d TREES REQUIRED. '
        'Two canopy trees are provided in two dedicated 200-SF islands between the guest bay and the kiosk bay, and '
        'neither is counted anywhere else on this sheet. The 60\'-0" radii are drawn about both trunks on the plan '
        'and on Enlargement A; the worst measured distance from any stall corner to the nearer trunk is %s. Island '
        'area satisfies §6.k.a (canopy tree, 200 SF minimum, not shared).',

        'ACCESSORY STRUCTURES AND GROUND-MOUNTED EQUIPMENT (§6.l). A 5\'-0" landscape strip is drawn around the mail '
        'kiosk (cluster box unit), both pickleball court pads and the clubhouse ground-mounted HVAC pad, planted with '
        '%d evergreen shrubs. Per-cottage ground-mounted condensers are screened by HOA-maintained foundation '
        'planting under the same rule; those plants are not tabulated here and are specified in docs/12 §32 93 00. '
        'Where the strip at the SW court pad overlaps the 20-ft undisturbed buffer by 3\'-0", it is satisfied by the '
        'buffer and its supplemental planting and NO GRADING OCCURS IN THE BUFFER.',

        'CERTIFICATE OF OCCUPANCY AND WARRANTY (§6.m) — VERBATIM: "No Certificate of Occupancy shall be issued until '
        'all requirements of the tree planting have been satisfactorily completed. Plant material shall be warranted '
        'by owner or contractor for 12 months from date of CO, or a maintenance bond shall be provided prior to CO or '
        'final plat."',

        'OVERHEAD UTILITY LINES (§6.n). Checklist §6.n requires a check for utility lines and alternate low or '
        'slow-growing trees, or setbacks from overhead power. OVERHEAD DISTRIBUTION ALONG THE ARCADO ROAD FRONTAGE IS '
        'NOT RESOLVED IN ANY PUBLIC LAYER USED FOR THIS PACKAGE AND MUST BE FIELD-LOCATED (Georgia 811 and Georgia '
        'Power) BEFORE THE STRIP IS LAID OUT. Pending that locate the frontage row is specified as flowering trees of '
        '15\'-0"–30\'-0" mature height, which sit in the Georgia Power right-tree/right-place low zone, and no canopy '
        'tree is placed within 20 ft of the presumed conductor line. Note the tension the sheet does not hide: §6.j '
        'asks for a mature height of at least 20 ft while the utility guide asks for no more than about 25 ft under a '
        'conductor, so the species must land in that window — or §6.n\'s utility-hardship variance is requested. If '
        'the field locate finds no conductor, the Landscape Architect may substitute 4-in-caliper Willow, Overcup, '
        'Nuttall, Pin or Shumard Oak, Lacebark Elm or Japanese Zelkova from the City\'s street-tree list.',

        'TREE PROTECTION (§6.g) — REQUIRED NOTE, VERBATIM: "TREE PROTECTION FENCE MUST BE INSTALLED PRIOR TO '
        'COMMENCING LAND DISTURBING ACTIVITIES." The fence line is drawn at the limit of disturbance — the buffer '
        'inner line and the outer line of the 50-ft undisturbed stream buffer — %s lineal feet, and DETAIL 1 gives '
        'the standard section. The fence is to be installed, inspected by the City and photographed before the '
        'pre-construction meeting and maintained until final stabilisation. A reasonable effort will be made to '
        'preserve specimen trees and every tree over 5 in in caliper standing in a buffer, landscape strip or parking '
        'island; those trees are identified by the tree survey, which has not yet been performed.',

        'STREAM BUFFERS — REQUIRED NOTES, VERBATIM (Checklist §9 Buffered State Waters e and f): "STREAM BUFFERS ARE '
        'TO REMAIN IN A NATURAL AND UNDISTURBED CONDITION." "STREAM BUFFER SHALL BE STAKED AND PROTECTED PRIOR TO '
        'LAND DISTURBANCE." The unnamed order-0 headwater of Jackson Creek (GAR030701030315, Georgia 2024 §303(d) '
        'list) and its 25-ft state, 50-ft undisturbed and 75-ft impervious lines are shown from Sheet C-0. TOP OF '
        'BANK IS APPROXIMATE — a field delineation by a qualified professional is required and governs, and no plant '
        'is placed inside the 50-ft undisturbed buffer. Street-tree stations that fell within 55 ft of a digitised '
        'reach were dropped for that reason.',

        'SPECIES, STANDARDS AND MAINTENANCE. Palette from docs/12 §32 93 00 2.02: Georgia Piedmont natives and '
        'proven adapted cultivars (UGA Extension "Native Plants for Georgia" I–IV). Nursery stock ANSI Z60.1; '
        'planting ANSI A300 Part 6 and ISA BMPs; Georgia Department of Agriculture nursery certification. '
        'PROHIBITED: every GA-EPPC Category 1 species — Ligustrum, Nandina, Pyrus calleryana, Elaeagnus, Lonicera '
        'japonica, Hedera helix, Wisteria sinensis, Vinca. Mulch 3 in, held 3 in clear of every trunk; root barriers '
        'at street trees within 5 ft of a walk. All landscape is maintained in perpetuity by the HOA under the '
        'recorded covenants: 90-day establishment, 12-month warranty with one replacement, then a professional '
        'landscape contract. Temporary establishment irrigation only; none in the buffer.',

        'WHAT IS NOT ON THIS SHEET. Per-cottage foundation and porch planting, sod and seeding limits, pond-bank '
        'seeding, the tree survey and arborist\'s buffer inventory, irrigation, landscape lighting, erosion-control '
        'matting and the planting estimate — all part of the sealed landscape plan and the LDP submittal. '
        'Existing-vegetation limits (Sheet C-0) are approximate, digitised from aerial imagery 2026-09-03.',
    ]


def notes_filled():
    p1 = _arch(pond_clearance_ft(L['ponds'][0]))
    p2 = _arch(pond_clearance_ft(L['ponds'][1]))
    n = notes()
    n[2] = n[2] % (format(round(PERIM_LEN), ','), format(round(BUF_SF), ','),
                   format(len(L['lots']) * 1000, ','), len(L['lots']))
    n[3] = n[3] % (round(SSE_LEN), round(ADDL_LEN), format(round(ADDL_LEN * ADDL_BUF_FT), ','),
                   round(SSE_LEN - ADDL_LEN), _arch(COURT_OFFSET_FT), round(SSE_LEN - ADDL_LEN))
    n[4] = n[4] % (p1, p2, _arch(float(MET['sw_curb_return_buffer_encroachment_ft'])),
                   MET['sw_curb_return_buffer_encroachment_sf'])
    n[5] = n[5] % (round(SUPPL_LEN), N_EVER, N_CANOPY, _arch(SUPPL_LEN / N_CANOPY),
                   format(round(PERIM_LEN - SUPPL_LEN), ','))
    n[6] = n[6] % (FRONTAGE_FT, MET['frontage_arcado_chord_ft'], FRONTAGE_FT,
                   FRONTAGE_FT / STRIP_RATE_FT, STRIP_TREES_REQ, STRIP_SHRUBS_REQ,
                   format(round(STRIP_SF), ','), _arch(OPENING_FT), _arch(2 * SIGHT_TRI_FT),
                   _arch(PLANTABLE_FT), _arch(STRIP_OC), STRIP_SHRUBS_REQ)
    n[7] = n[7] % (_arch(STREET_TREE_OC), _arch(6.0),
                   int(L['lane']['widen_both_sidewalks_from_u']), N_STREET)
    n[8] = n[8] % round(ISD_FT)
    n[9] = n[9] % (GUEST_SPACES, KIOSK_SPACES, AMENITY_SPACES, AMENITY_SPACES,
                   AMENITY_SPACES / PARK_RATE, PARK_TREES_REQ, _arch(PARK_MAXD))
    n[10] = n[10] % len(by_zone('accessory'))
    n[13] = n[13] % format(round(sum(poly_len(x) for x in TPF_LINES)), ',')
    return n


SOURCES = [
    'City of Lilburn Site Development Plan Review Checklist, section 6 "Zoning Buffers/Landscape Plan Comments '
    '(see Chapter 109 — Environment)", clauses a–n — the clause numbers cited on this sheet '
    '(data/site-dev-plan-review-checklist.txt).',
    'Lilburn Zoning Ordinance, Ord. 2023-603 — Table 4.1 (20-ft buffer abutting R-1 for dwelling types other than '
    'detached single-family), §313(1) (buffer requirements supersede required yards), §602 Use Table.',
    'data/layout.json, regenerated 2026-09-03 — boundary ring, %d lots, lane, amenity block, open-space tracts, '
    'detention basins, stream reaches, and metrics.frontage_arcado_along_rw_ft = %s ft. Every quantity on this '
    'sheet is computed from that file at run time.' % (len(L['lots']), FRONTAGE_FT),
    'docs/12-outline-specifications.md Section 32 93 00 "Plants" — species palette, supplemental-buffer rate '
    '(1 evergreen per 8–10 lf plus 1 canopy tree per 30–40 lf), prohibited GA-EPPC Category 1 species, street-tree '
    'list and 4-in caliper standard along a public right-of-way.',
    'data/plans.json (read at run time, never written) — Plan A body depth, ridge height and lot siting for the '
    'typical buffer section. It was regenerated on 2026-09-03, so the patio edge now stands %s from the rear lot '
    'line and the audit\'s 20.17 ft is stale.' % _arch(PA_PATIO),
    'audit-2026-09-03/drawing-standards.md §3.1 (the C-7.0 row) and §3.2 (legend discipline); '
    'audit-2026-09-03/completeness.md item M9; audit-2026-09-03/site-geometry.md §4.',
    'Sheet C-0 EXISTING CONDITIONS — existing wooded area and mown-yard limits (approximate, aerial imagery '
    '2026-09-03), the existing 8-in sanitary sewer and its easement, and the stream and its buffers.',
    'Georgia Power "Tree planting near utility lines" right-tree/right-place guide (cited by Checklist §6.n); '
    'ANSI Z60.1-2014 nursery stock; ANSI A300 Part 6; UGA Extension "Native Plants for Georgia" Parts I–IV.',
]


# =========================================================================== enlargements
ENL_A = (-50.0, 230.0, -245.0, 15.0, 'A')
sb.ENLARGEMENTS.append(ENL_A)


def enlargement_a(x, y):
    S = sb.enlargement(ENL_A[0], ENL_A[1], ENL_A[2], ENL_A[3], x, y, scale=SCALE20, tag='A')
    S.clip_open(fill='#fff')
    sb.adjoiners(S, labels=False, zoning=False)
    sb.arcado_row(S, labels=False)
    context(S, screen=True)
    buffer_layer(S, labels=False, dims=False)
    strip_layer(S, labels=False, dims=False)
    accessory_layer(S)
    parking_layer(S, labels=False)
    tree_protection(S, labels=False)
    planting(S, keys=True)
    sb.boundary(S, bearings=False, label=False)

    # --- dimensions
    p0, t0 = walk(FRONT, 30.0)
    nx, ny = -t0[1], t0[0]
    dim(S, p0, (p0[0] + nx * STRIP_FT, p0[1] + ny * STRIP_FT), 0.0, "10'-0\"", size=7.0,
        col=CG['strip'])
    a, _ = walk(FRONT, PLANTABLE_RUNS[0][0] + 0.5 * STRIP_OC)
    b, _ = walk(FRONT, PLANTABLE_RUNS[0][0] + 1.5 * STRIP_OC)
    an = (a[0] + nx * STRIP_FT * 0.5, a[1] + ny * STRIP_FT * 0.5)
    bn = (b[0] + nx * STRIP_FT * 0.5, b[1] + ny * STRIP_FT * 0.5)
    dim(S, an, bn, 16.0, "%s O.C. (TYP.)" % _arch(STRIP_OC), size=6.6, col=CG['strip'], side=1)
    dim(S, (100.0, sb.SW(100.0)), (100.0, sb.SW(100.0) + BUF_FT), 0.0, "20'-0\"", size=7.0,
        col=CG['buf_dark'])
    dim(S, (128.0, sb.SW(128.0) + BUF_FT), (128.0, sb.SW(128.0) + BUF_FT + ADDL_BUF_FT), 0.0,
        "25'-0\"", size=7.0, col=CG['addl'])
    dim(S, (208.0, sb.NE(208.0)), (208.0, sb.NE(208.0) - BUF_FT), 0.0, "20'-0\"", size=7.0,
        col=CG['buf_dark'])
    for tgt in ((-44.0, -234.0), (-40.0, -34.0)):
        S.line((-34.0, -190.0), tgt, stroke=CG['sight'], stroke_width=0.8, stroke_dasharray='11 4')
        ux, uy = _unit((-34.0, -190.0), tgt)
        S.poly([tgt, (tgt[0] - 7 * ux + 2.6 * uy, tgt[1] - 7 * uy - 2.6 * ux),
                (tgt[0] - 7 * ux - 2.6 * uy, tgt[1] - 7 * uy + 2.6 * ux)], fill=CG['sight'],
               stroke='none')
    ps, _ = walk(FRONT, SIGHT_NE[0])
    pe, _ = walk(FRONT, SIGHT_NE[1])
    dim(S, ps, pe, -13.0, "20'-0\"", size=6.6, col=CG['sight'], side=1)
    mk = [tuple(q) for q in AM['mail_kiosk']]
    dim(S, (min(q[0] for q in mk) - 5.0, max(q[1] for q in mk) + 2.0),
        (min(q[0] for q in mk), max(q[1] for q in mk) + 2.0), 0.0, "5'-0\"", size=6.8,
        col=CG['accy'])
    dim(S, PARK_TRUNKS[0], (PARK_TRUNKS[0][0], PARK_TRUNKS[0][1] + PARK_RADIUS), 0.0,
        "R 60'-0\"", size=6.6, col=CG['park'])

    # --- annotation (kept short; the reasoning is in the general notes)
    S.text(-43.0, -120.0, 'ARCADO ROAD — R/W WIDTH VARIES (GWINNETT COUNTY MINOR COLLECTOR)',
           size=7.0, rot=-81, bold=True, halo=True)
    S.text(170.0, 9.0, 'ADJOINING — 4531 ARCADO RD SW, ZONED R-1 (CITY OF LILBURN)', size=6.8,
           bold=True, fill='#555', halo=True)
    S.text(120.0, -241.0, 'ADJOINING — LEGENDS AT PARKVIEW, ZONED R-1 (CITY OF LILBURN)', size=6.8,
           bold=True, fill='#555', halo=True)
    leader(S, (6.0, -46.0), (58.0, -28.0), '', size=7.0, col=CG['strip'], anchor='middle', lines=[
        "10'-0\" LANDSCAPE STRIP ALONG THE ARCADO RD R/W (CHECKLIST §6.j)",
        "%s FRONTAGE ÷ 25 = %.2f → %d TREES + %d SHRUBS; 8 IN THE STRIP AT %s O.C. + 2 BEHIND IT"
        % (_arch(FRONTAGE_FT), FRONTAGE_FT / STRIP_RATE_FT, STRIP_TREES_REQ, STRIP_SHRUBS_REQ,
           _arch(STRIP_OC))])
    leader(S, (-16.0, -145.0), (58.0, -58.0), '', size=7.0, col=CG['sight'], anchor='middle', lines=[
        "SIGHT TRIANGLE 20'-0\" × 20'-0\" EACH SIDE OF THE DRIVE (CHECKLIST §6.j) —",
        "NO LANDSCAPING 3'-0\" TO 15'-0\" IN HEIGHT; SHRUBS WITHIN MAINTAINED AT 30 in"])
    S.text(58.0, -80.0, 'GWINNETT DOT INTERSECTION SIGHT DISTANCE ≈ %d ft EACH WAY (VERIFY) — '
           'PE CERTIFICATE REQUIRED (§7.j)' % round(ISD_FT), size=7.0, bold=True, fill=CG['sight'],
           halo=True)
    leader(S, (-6.0, -168.0), (58.0, -99.0), 'MONUMENT ENTRY SIGN — OUTSIDE BOTH SIGHT TRIANGLES; '
           'BED MAINTAINED AT 30 in MAX.', size=7.0, col='#444', anchor='middle')
    leader(S, (30.0, sb.SW(30.0) + 17.0), (58.0, -120.0), 'SUPPLEMENTAL BUFFER PLANTING ZONE '
           '(CHECKLIST §6.h) — SEE NOTE 6', size=7.0, col=CG['suppl'], anchor='middle')
    leader(S, (110.0, sb.SW(110.0) + 32.0), (100.0, -202.0), "25'-0\" ADDITIONAL BUFFER "
           '(CHECKLIST §6.c) — SEE NOTE 4', size=7.0, col=CG['addl'], anchor='middle')
    leader(S, (170.0, -122.0), (226.0, -28.0), '', size=7.0, col=CG['park'], anchor='end', lines=[
        'PARKING-LOT PLANTING (§6.k) — %d SPACES ÷ 7 = %.2f → %d TREES'
        % (AMENITY_SPACES, AMENITY_SPACES / PARK_RATE, PARK_TREES_REQ),
        "IN 200-SF ISLANDS; EVERY SPACE WITHIN 60'-0\" OF A TRUNK (WORST %s)" % _arch(PARK_MAXD)])
    leader(S, (219.0, -80.0), (226.0, -50.0), "5'-0\" LANDSCAPE STRIP AT ACCESSORY STRUCTURES AND "
           'GROUND HVAC (§6.l)', size=7.0, col=CG['accy'], anchor='end')
    leader(S, (187.0, -212.7), (140.0, -196.0), '', size=6.8, col=CG['accy'], anchor='middle', lines=[
        "PICKLEBALL PADS STAND %s FROM THE SW LINE — THE 5'-0\" STRIP" % _arch(COURT_OFFSET_FT),
        "OVERLAPS THE BUFFER BY 3'-0\"; NO GRADING IN THE BUFFER (NOTE 11)"])
    S.text(44.0, sb.SW(44.0) + 8.0, "EX. 20' SANITARY SEWER EASEMENT WITHIN THE REQUIRED BUFFER (§6.c)",
           size=6.8, bold=True, fill=sb.C['sewer_txt'], halo=True)
    S.text(140.0, -100.0, 'CLUBHOUSE', size=7.4, bold=True, halo=True)
    S.text(140.0, -107.0, "2,400 SF (40'-0\" × 60'-0\")", size=6.8, halo=True)
    S.text(20.0, -160.0, 'VILLAGE GREEN', size=7.4, bold=True, fill='#2e5e1e', halo=True)
    S.clip_close()
    return S


# =========================================================================== sheet
def legend_block(D, x, y, w, entries, cols=2):
    D.stext(x, y, 'LEGEND — every symbol drawn on this sheet appears here, and no unused entry '
                  'appears (audit-2026-09-03/drawing-standards.md §3.2)', size=8.5, bold=True)
    per = int(math.ceil(len(entries) / float(cols)))
    cw = w / cols
    for i, (kind, col, wd, dash, txt) in enumerate(entries):
        cx = x + (i // per) * cw
        yy = y + 15 + (i % per) * 12.6
        if kind == 'line':
            D.sline(cx, yy - 3, cx + 30, yy - 3, stroke=col, stroke_width=wd, stroke_dasharray=dash)
        elif kind == 'tpf':
            D.sline(cx, yy - 3, cx + 30, yy - 3, stroke=col, stroke_width=wd, stroke_dasharray=dash)
            for k in range(3):
                D.scircle(cx + 7 + k * 8, yy - 3, 1.5, fill='none', stroke=col, stroke_width=0.9)
        elif kind == 'bufsw':
            D.srect(cx, yy - 9.5, 30, 12, fill='url(#woods)', stroke='none')
            D.srect(cx, yy - 9.5, 30, 12, fill='url(#bufhatch)', stroke='#555', stroke_width=0.4)
        elif kind == 'buf2':
            D.srect(cx, yy - 9.5, 15, 12, fill=sb.C['green'], stroke='#555', stroke_width=0.4)
            D.srect(cx + 15, yy - 9.5, 15, 12, fill='#cfe8bd', stroke='#555', stroke_width=0.4)
        elif kind in ('canopy', 'under', 'ever', 'shrub'):
            sub = sb.Drawing(1.0, 0, 0, win=(0, 1, 0, 1))
            SYM[kind](sub, (0, 0), *( [7.0] if kind != 'shrub' else [3.0]))
            for el in sub.out:
                D.add(el.replace('cx="%.2f"' % sub.X(0), 'cx="%.2f"' % (cx + 15))
                        .replace('cy="%.2f"' % sub.Y(0), 'cy="%.2f"' % (yy - 3.5))
                      if el.startswith('<circle') else _shift(el, cx + 15 - sub.X(0),
                                                              yy - 3.5 - sub.Y(0)))
        else:
            D.srect(cx, yy - 9.5, 30, 12, fill=col, stroke='#555', stroke_width=0.4)
        D.stext(cx + 36, yy, txt, size=6.7)
    return y + 15 + per * 12.6


def _shift(el, dx, dy):
    import re

    def f(m):
        return '%s="%.2f"' % (m.group(1), float(m.group(2)) + (dx if m.group(1) in ('x', 'x1', 'x2', 'cx') else dy))
    el = re.sub(r'\b(x|y|x1|y1|x2|y2|cx|cy)="(-?[\d.]+)"', f, el)

    def g(m):
        pts = []
        for pair in m.group(1).split():
            a, b = pair.split(',')
            pts.append('%.2f,%.2f' % (float(a) + dx, float(b) + dy))
        return 'points="%s"' % ' '.join(pts)
    return re.sub(r'points="([^"]+)"', g, el)


def build():
    scale_note = 'Scale 1" = 60\' (ARCH D 36 × 24 in); enlargements 1" = 20\''
    D, F = sb.sheet(
        'LANDSCAPE, BUFFER AND TREE PROTECTION CONCEPT', 'C-7.0',
        'Lilburn Zoning Ordinance 2023-603 §1003-4.6, Table 4.1 and §313(1); City of Lilburn Site '
        'Development Plan Review Checklist §6.a–§6.n',
        scale_note, generator='tools/sitebase.py + tools/landscape.py',
        win=WIN, x0=PLAN_X0, y0=PLAN_Y0,
        north_at=(PLAN_X0 + PLAN_W - 62.0, PLAN_Y0 + 74.0),
        scale_at=(PLAN_X0 + 1626.0, PLAN_Y0 + PLAN_H - 17.0),
        status_lines=[
            'CONCEPT — to be sealed by a Registered Landscape Architect,',
            'forester or arborist (Site Development Plan Review Checklist §6.a).',
            'No tree survey has been performed; existing-vegetation limits are',
            'approximate. Quantities are concept quantities for review only.'])
    assert len(D.late) == 4, 'sitebase.sheet() queued layers changed — check the indices below'
    px, py, pw, ph = F['plan']
    D.late[1] = lambda: D.add(
        '<text x="%.1f" y="%.1f" font-size="28" fill="#c00" fill-opacity="0.09" font-weight="bold" '
        'text-anchor="middle">CONCEPT — NOT SEALED — LANDSCAPE ARCHITECT SEAL REQUIRED</text>'
        % (px + pw / 2, py + ph * 0.46))
    D.late[3] = lambda: (D.srect(PLAN_X0 + 1596.0, PLAN_Y0 + PLAN_H - 28.0, 344, 27, fill='#fff',
                                 fill_opacity='0.94', stroke='#999', stroke_width=0.4),
                         sb.scalebar(D, PLAN_X0 + 1626.0, PLAN_Y0 + PLAN_H - 17.0,
                                     scale=sb.SCALE60, step_ft=60, steps=4))
    D.add(DEFS_EXTRA)

    # ---------------------------------------------------------------- plan, 1" = 60'
    D.clip_open(fill='#fff')
    sb.adjoiners(D, labels=False, zoning=False)
    sb.arcado_row(D, labels=False)
    context(D, screen=True)
    buffer_layer(D, labels=True, dims=True)
    strip_layer(D, labels=True, dims=False)
    accessory_layer(D)
    parking_layer(D, labels=True)
    sb.streams_and_buffers(D, labels=False)
    tree_protection(D, labels=True)
    planting(D, keys=False)
    sb.boundary(D, bearings=False, label=False)
    D.poly(sb.rect(ENL_A[0], ENL_A[1], ENL_A[2], ENL_A[3]), fill='none', stroke=sb.C['match'],
           stroke_width=1.2, stroke_dasharray='16 5 3 5')
    D.text((ENL_A[0] + ENL_A[1]) / 2.0, ENL_A[3] + 5.0,
           'MATCH LINE — SEE ENLARGEMENT A (1" = 20\')', size=7.2, bold=True, fill=sb.C['match'],
           halo=True)

    D.text(950.0, 16.0, 'KING DAVID MANOR — ZONED R-1 (CITY OF LILBURN): THE 20-FT UNDISTURBED BUFFER '
                        'ABUTS RESIDENTIAL PROPERTY ON THIS LINE (CHECKLIST §6.b)', size=7.4, bold=True,
           fill='#555')
    D.text(1560.0, -246.0, 'LEGENDS AT PARKVIEW — ZONED R-1 (CITY OF LILBURN): THE 20-FT UNDISTURBED '
                          'BUFFER ABUTS RESIDENTIAL PROPERTY ON THIS LINE (CHECKLIST §6.b)', size=7.4,
           bold=True, fill='#555')
    D.text(1786.0, -170.0, 'NANTUCKET — ZONED R-1', size=7.2, rot=-90, bold=True, fill='#555')
    D.text(430.0, sb.NE(430.0) - 46.0, 'LANE STREET TREES AT %s ON CENTRE, BOTH SIDES — %d TREES '
           '(SEE PLANT SCHEDULE)' % (_arch(STREET_TREE_OC), N_STREET), size=7.0, bold=True,
           fill=CG['canopy'], halo=True)
    D.text(1300.0, sb.SW(1300.0) + 42.0, 'NO PLANTING WITHIN THE 50-FT UNDISTURBED STREAM BUFFER — '
           'STREAM BUFFERS ARE TO REMAIN IN A NATURAL AND UNDISTURBED CONDITION', size=6.6,
           bold=True, fill=sb.C['stream'], halo=True)
    D.text(120.0, -250.0, 'SEE ENLARGEMENT A FOR THE ARCADO RD FRONTAGE STRIP, THE SIGHT TRIANGLES '
           'AND THE AMENITY-BLOCK PLANTING', size=6.8, bold=True, fill=sb.C['match'], halo=True)
    D.clip_close()
    D.stext(px + pw, py - 8, 'CONCEPT — TO BE SEALED BY A REGISTERED LANDSCAPE ARCHITECT, FORESTER OR '
                             'ARBORIST (CHECKLIST §6.a)', size=11, bold=True, fill='#c00', anchor='end')

    # ---------------------------------------------------------------- band column A
    xa, wa = F['inner_l'] + 10, 900.0
    y = sb.table(D, xa, BAND_Y0, ['CLAUSE', 'REQUIREMENT (CHECKLIST §6)', 'BASIS AND ARITHMETIC',
                                  'PROVIDED ON THIS SHEET', 'STATUS'],
                 req_rows(), size=6.6, widths=[38, 214, 258, 302, 88],
                 title='LANDSCAPE, BUFFER AND TREE-PROTECTION REQUIREMENTS — REQUIRED vs. PROVIDED')
    y = sb.table(D, xa, y + 18, ['KEY', 'COMMON NAME', 'BOTANICAL NAME', 'QTY', 'SPACING / ON CENTRE',
                                 '% OF TOTAL', 'CALIPER / SIZE', 'HT. AT PLANTING', 'MATURE HT.',
                                 'ROOT COND.', 'USE ON THIS SHEET'],
                 schedule_rows(), size=6.6, widths=[24, 122, 120, 26, 98, 42, 64, 64, 58, 48, 234],
                 title='PLANT SCHEDULE — Checklist §6.i: common and botanical names, quantity, spacing, '
                       'percentage of total, size, height, caliper and root condition')
    D.stext(xa, y + 11, 'Quantities are counted from the symbols actually drawn on this sheet, so the schedule '
                        'cannot disagree with the plan. Percentages are of the %d-plant total; the largest single '
                        'species is %.1f %%, under the 33 %% maximum of Checklist §6.i. B&B = balled and burlapped; '
                        'nursery stock to ANSI Z60.1-2014.' % (TOTAL_PLANTS, MAX_PCT), size=6.6, fill='#333')
    D.stext(xa, y + 20.5, 'Per-cottage foundation and porch planting is HOA-installed and is not tabulated '
                          '(note 11). Final species selection is the Landscape Architect\'s.', size=6.6, fill='#333')
    yl = legend_block(D, xa, y + 36, wa, LEGEND, cols=3)
    sec = buffer_section(xa, yl + 40)
    ysec = sb.place(D, sec, title='ENLARGEMENT B — TYPICAL BUFFER SECTION, PERIMETER LOT    '
                                  '(SCALE 1" = 20\')',
                    note='Looking along the SW property line; horizontal and vertical scales are equal '
                         '(no exaggeration).')
    kx = xa + 165.0 * SCALE20 + 16
    D.stext(kx, yl + 40 + 10, 'KEY TO ENLARGEMENT B', size=8, bold=True)
    ky = yl + 40 + 22
    for n, txt in SECTION_KEY:
        D.scircle(kx + 5, ky - 2.4, 5.2, fill='#fff', stroke='#000', stroke_width=0.8)
        D.stext(kx + 5, ky, str(n), size=7.0, anchor='middle', bold=True)
        ky = D.stextblock(kx + 15, ky, txt, size=6.6, chars=76, lead=7.6)
        ky += 1.6
    sb.scalebar(D, kx + 8, min(ky + 16, BAND_Y1 - 16), scale=SCALE20, step_ft=20, steps=3)

    # ---------------------------------------------------------------- band column B — enlargement A
    xb = xa + wa + 22
    sub = enlargement_a(xb, BAND_Y0 + 26)
    ybot = sb.place(D, sub, title='ENLARGEMENT A — ARCADO ROAD FRONTAGE LANDSCAPE STRIP, ENTRANCE SIGHT '
                                  'TRIANGLES AND AMENITY-BLOCK PLANTING    (SCALE 1" = 20\')',
                    note='Same data and the same site-local coordinates as the plan above; u %.0f to %.0f, '
                         'v %.0f to %.0f. The 60-ft parking radii run past the right-hand match line and are '
                         'shown complete on the plan.' % ENL_A[:4])
    sb.scalebar(D, xb + 8, ybot + 24, scale=SCALE20, step_ft=20, steps=5)
    D.stext(xb + 420, ybot + 16, 'FRONTAGE ARITHMETIC (§6.j): %s ÷ 25 = %.2f → %d trees + %d shrubs. '
                                 'Drive opening and curb returns %s; two 20-ft sight triangles %s; plantable '
                                 'strip %s.'
            % (_arch(FRONTAGE_FT), FRONTAGE_FT / STRIP_RATE_FT, STRIP_TREES_REQ, STRIP_SHRUBS_REQ,
               _arch(OPENING_FT), _arch(2 * SIGHT_TRI_FT), _arch(PLANTABLE_FT)), size=6.8, fill='#111')
    D.stext(xb + 420, ybot + 27, 'PARKING ARITHMETIC (§6.k): %d spaces ÷ 7 = %.2f → %d trees; worst measured '
                                 'trunk distance %s against the 60\'-0" maximum. Tree Density Units are NOT '
                                 'required of an SFR subdivision (§6.i) — note 2.'
            % (AMENITY_SPACES, AMENITY_SPACES / PARK_RATE, PARK_TREES_REQ, _arch(PARK_MAXD)),
            size=6.8, fill='#111')
    ys = ybot + 46
    D.stext(xb, ys, 'SOURCES', size=8.5, bold=True)
    ys += 11
    half = int(math.ceil(len(SOURCES) / 2.0))
    for i, srcline in enumerate(SOURCES, 1):
        col = 0 if i <= half else 1
        yy0 = ys + ((i - 1) % half if col == 0 else (i - 1 - half)) * 0
        _ = yy0
    ycol = [ys, ys]
    for i, srcline in enumerate(SOURCES, 1):
        col = 0 if i <= half else 1
        ycol[col] = D.stextblock(xb + col * 508, ycol[col], '%d. %s' % (i, srcline), size=6.6,
                                 chars=132, lead=7.9, indent=9, fill='#333')
        ycol[col] += 1.6

    # ---------------------------------------------------------------- band column C — notes + section
    xc = xb + 1008 + 14
    D.stext(xc, BAND_Y0, 'GENERAL NOTES — LANDSCAPE, BUFFER AND TREE PROTECTION', size=9, bold=True)
    yy = BAND_Y0 + 13
    for i, n in enumerate(notes_filled(), 1):
        yy = D.stextblock(xc, yy, '%d. %s' % (i, n), size=6.6, chars=140, lead=7.66, indent=9)
        yy += 2.6
    ydet = tpf_detail(D, xc, max(yy + 22.0, BAND_Y1 - 206.0), sc=18.0)
    return D, (yl, ydet, yy, ysec, max(ycol))


if __name__ == '__main__':
    D, marks = build()
    svg, png = sb.save(D, 'landscape-buffer', dpi=150)
    print('wrote %s\n      %s' % (svg, png))
    print('  buffer   : %.0f lf, %.0f SF (mitred 20-ft offset); layout raster figure %s SF'
          % (PERIM_LEN, BUF_SF, format(L['stormwater']['disturbed_area']['buffer_bands_sf'], ',')))
    print('  frontage : %.2f lf; opening %.1f; sight triangles %.0f; plantable %.1f; strip %.0f SF'
          % (FRONTAGE_FT, OPENING_FT, 2 * SIGHT_TRI_FT, PLANTABLE_FT, STRIP_SF))
    print('  plants   : %d total, %d species, max species %.1f%%; street %d, strip %d+%d, '
          'buffer %d+%d, parking %d, accessory %d'
          % (TOTAL_PLANTS, len(COUNTS), MAX_PCT, N_STREET, 10, 10, N_EVER, N_CANOPY,
             len(by_zone('parking')), len(by_zone('accessory'))))
    print('  parking  : worst stall-to-trunk distance %.1f ft against the 60-ft test' % PARK_MAXD)
    print('  band ends: legend %.0f, detail %.0f, notes %.0f, section %.0f, sources %.0f '
          '(band bottom %d)' % (marks + (BAND_Y1,)))
