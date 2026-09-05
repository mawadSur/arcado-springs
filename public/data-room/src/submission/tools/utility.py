#!/usr/bin/env python3
"""Sheet C-4.0 "UTILITY AND PHASING CONCEPT" — The Cottages at Arcado Springs (R-1 -> R-2, Lilburn GA).

    python3 tools/utility.py        ->  drawings/utility-phasing.svg + .png

ARCH D 36 x 24 in at 1" = 60'. Everything is drawn through tools/sitebase.py from
data/layout.json, data/site-context-local.json and data/topo-samples.json; no coordinate in
this file is hand-drawn except the two DWR points of connection, which are quoted from the
Gwinnett DWR GIS attributes recorded in FACTS.md section 2.

WHY THIS SHEET EXISTS
The C-4.0 row of audit-2026-09-03/drawing-standards.md section 3.1 and item M11 of
audit-2026-09-03/completeness.md require one sheet that carries (a) the proposed water main,
meters, services and hydrants at IFC 2024 (GA) Appendix C Table C102.1 spacing with the
dead-end length stated and the looping / oversizing question put to Gwinnett DWR ON THE SHEET;
(b) the Phase 1 gravity sewer to the existing on-site manhole at invert 927.13 with a manhole
schedule; (c) the Phase 2 off-site gravity extension to the Legends at Parkview main at invert
919.58 drawn as the PRIMARY route, with the two governing Gwinnett DWR policy quotations
printed on the sheet rather than buried in a memo; and (d) the phase line on lot lines with the
lot count in each phase.

WHAT THIS SHEET CORRECTS
data/layout.json still carries `sewer.phase2_primary = "in-tract lift station / grinder pumps"`,
which FACTS.md section 2 and audit-2026-09-03/external-facts.md section 3.4 reversed on
2026-09-03. Gwinnett DWR's Standard Policy for Private Developments (Condominiums, Townhomes and
Subdivisions, rev. 9/2018) allows private pump stations, force mains and gravity sewers "only ...
for commercial properties under single ownership within a development", and Developer Pump
Station Standards WSR-24 section 1.3.1(A) allows a county station only where gravity is "more
than 5,000 feet down gradient" against an actual 178 ft. This sheet therefore draws the off-site
gravity tie as the primary Phase 2 route and shows the lift station only as a labelled
contingency. The generator reads the layout geometry, not the layout's stale `phase2_primary`
string, and never writes to data/.

DRAFT — NOT SEALED. Concept only. All water and sanitary design must be prepared, signed and
sealed by a Georgia-registered professional engineer and approved by Gwinnett County DWR.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitebase as sb                                      # noqa: E402

LAY = sb.LAYOUT
LOTS = LAY['lots']
LANE = LAY['lane']
CL = [tuple(p) for p in LANE['centerline']]
AMEN = LAY['amenity']

# ============================================================================ ground model
# The USGS 3DEP samples are a 100 x 50-ft grid covering u -16..1,684 and v -217.5..-17.5.
# ground() is a bilinear interpolation over that grid; the interpolation parameter is allowed
# to run to -0.5 / +1.5 so that a point just outside the grid (the SW property line at
# v = -235) is linearly EXTRAPOLATED from the nearest two rows rather than clamped. Every rim
# elevation on this sheet is therefore approximate and the one at MH-B4 is extrapolated
# 17.7 ft beyond the sampled grid — both facts are stated in the general notes.
_GU = sorted(set(round(s['u'], 1) for s in sb.TOPO['samples']))
_GV = sorted(set(round(s['v'], 1) for s in sb.TOPO['samples']))
_GZ = {(round(s['u'], 1), round(s['v'], 1)): s['z_ft'] for s in sb.TOPO['samples']}


def _bracket(vals, x):
    if x <= vals[0]:
        i = 0
    elif x >= vals[-1]:
        i = len(vals) - 2
    else:
        i = max(k for k in range(len(vals) - 1) if vals[k] <= x)
    t = (x - vals[i]) / (vals[i + 1] - vals[i])
    return i, max(-0.5, min(1.5, t))


def ground(u, v):
    i, tu = _bracket(_GU, u)
    j, tv = _bracket(_GV, v)
    z00, z10 = _GZ[(_GU[i], _GV[j])], _GZ[(_GU[i + 1], _GV[j])]
    z01, z11 = _GZ[(_GU[i], _GV[j + 1])], _GZ[(_GU[i + 1], _GV[j + 1])]
    return (1 - tu) * ((1 - tv) * z00 + tv * z01) + tu * ((1 - tv) * z10 + tv * z11)


GP = LANE['ground_profile']


def lane_ground(u):
    """Existing ground on the lane centreline (data/layout.json lane.ground_profile, 3DEP)."""
    if u <= GP[0][0]:
        return GP[0][1]
    for i in range(len(GP) - 1):
        if GP[i][0] <= u <= GP[i + 1][0]:
            t = (u - GP[i][0]) / (GP[i + 1][0] - GP[i][0])
            return GP[i][1] + t * (GP[i + 1][1] - GP[i][1])
    return GP[-1][1]


def lane_v(u):
    return sb.interp_v(CL, u)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ============================================================================ design constants
W_OFF = 14.0          # proposed water main, ft NE of the lane centreline (3 ft behind back of curb)
S_OFF = -5.0          # proposed sanitary main, ft SW of the lane centreline
SEP_FT = W_OFF - S_OFF                                   # horizontal water/sewer separation
COVER = 5.0           # ft, ground to invert at every upstream terminus
PVMT_HALF = LANE['pavement_width_ft'] / 2.0

U_ENTRY = LANE['entrance']['join_u']                      # 149.5 — entry drive joins the lane
U_END = LANE['pavement_end_u']                            # 1700
ED = [tuple(p) for p in LANE['entry_drive']['centerline']]
ED_LEN = LANE['entry_drive']['length_ft']                 # 204.0
LANE_LEN = LAY['metrics']['lane_length_ft']               # 1754.0
U_PHASE = LAY['phase_line_u']                             # 980.0
U_DIVIDE = 1280.0     # sanitary divide: System A drains back to the existing on-site MH,
#                       System B drains forward to the rear low point and the off-site tie
U_CREST = 1179.0      # lane ridge crest (3DEP 953.5) — the reason the project is phased
U_SAG = 779.0         # front lane sag (3DEP 936.3) — start of the controlling Phase 1 reach
U_LOW = 1479.0        # rear lane low point (3DEP 931.5)

POC1 = (271.7, -224.0)                                    # existing MH, invert 927.13
POC1_INV = 927.13
POC2 = (1348.9, -406.5)                                   # Legends at Parkview MH, invert 919.58
POC2_INV = 919.58
LS_BOX = [tuple(p) for p in LAY['lift_station_symbol']]
FORCE_MAIN = [tuple(p) for p in LAY['sewer']['phase2_force_main_concept']]

HYD_U = [170.0, 530.0, 880.0, 1230.0, 1580.0, 1690.0]     # proposed hydrants, lane stations below
VALVE_U = [170.0, 530.0, 1230.0]                          # in-line valves (every third hydrant)
EX_HYD = min(sb.CTX['hydrants'], key=lambda h: h['dist_ft'])


def station(u):
    """Distance along the travelled way from the Arcado Rd right-of-way to lane station u."""
    return ED_LEN + (u - U_ENTRY)


# ============================================================================ proposed alignments
def water_path():
    """8-in DI main: Arcado Rd tap -> entry drive -> lane, 14 ft NE of the lane centreline."""
    tap = (-82.2, -195.3)                                  # nearest published DIP main vertex
    pts = [tap] + [p for p in ED if p[0] > -32.0]
    pts += [(u, lane_v(u) + W_OFF) for u in _steps(U_ENTRY + 6.0, U_END, 20.0)]
    return tap, pts


def _steps(a, b, d):
    n = max(int(math.ceil((b - a) / d)), 1)
    return [a + (b - a) * k / n for k in range(n + 1)]


def sanA_path():
    """System A — gravity to the existing on-site manhole (POC-1). Upstream terminus u 1,280."""
    pts = [(u, lane_v(u) + S_OFF) for u in _steps(U_DIVIDE, 272.0, 20.0)]
    return pts + [POC1]


def sanB_path():
    """System B — rear collector + the off-site extension (POC-2)."""
    top = [(u, lane_v(u) + S_OFF) for u in _steps(U_END - 10.0, U_LOW, 20.0)]
    out = [(u, lane_v(u) + S_OFF) for u in _steps(U_LOW, 1300.0, 20.0)]
    return top, out + [(1300.0, sb.SW(1300.0)), POC2]


WATER_TAP, WATER = water_path()
SAN_A = sanA_path()
SAN_B_TOP, SAN_B_OUT = sanB_path()
OFFSITE_A = (1300.0, sb.SW(1300.0))                        # SW property line, start of the extension
OFFSITE_LEN = dist(OFFSITE_A, POC2)

# ---------------------------------------------------------------- manhole schedules
def _mh(tag, pt, inv, nxt_len, slope, remark, rim=None, phase=1, offsite=False):
    g = rim if rim is not None else lane_ground(pt[0])
    return {'tag': tag, 'pt': pt, 'rim': g, 'inv': inv, 'depth': g - inv, 'len': nxt_len,
            'slope': slope, 'remark': remark, 'phase': phase, 'offsite': offsite}


def build_system_a():
    """Upstream terminus u 1,280 -> POC-1. Fixed points: 5.00 ft of cover at u 1,280 and at the
    lane sag u 779, and invert 927.13 at the existing manhole."""
    p = {u: (u, lane_v(u) + S_OFF) for u in (U_DIVIDE, U_CREST, U_PHASE, U_SAG, 500.0, 272.0)}
    L1 = dist(p[U_DIVIDE], p[U_CREST])
    L2 = dist(p[U_CREST], p[U_PHASE])
    L3 = dist(p[U_PHASE], p[U_SAG])
    L4 = dist(p[U_SAG], p[500.0])
    L5 = dist(p[500.0], p[272.0])
    L6 = dist(p[272.0], POC1)
    inv_sag = lane_ground(U_SAG) - COVER                       # 931.30
    s_ctrl = (inv_sag - POC1_INV) / (L4 + L5 + L6)             # controlling reach, sag -> POC-1
    inv500 = inv_sag - s_ctrl * L4
    inv272 = inv500 - s_ctrl * L5
    inv_top = lane_ground(U_DIVIDE) - COVER                    # 938.70
    s_up = (inv_top - (lane_ground(U_PHASE) - COVER)) / (L1 + L2)
    inv_crest = inv_top - s_up * L1
    inv_ph = inv_crest - s_up * L2
    s_ph = (inv_ph - inv_sag) / L3
    rows = [
        _mh('MH-A1', p[U_DIVIDE], inv_top, L1, s_up,
            'Upstream terminus of System A; sanitary divide (Block B lots up-station of u 1,280 '
            'drain to System B). Phase 2 construction.', phase=2),
        _mh('MH-A2', p[U_CREST], inv_crest, L2, s_up,
            'Under the u 1,179 ridge crest (3DEP 953.5) — the deepest structure on System A. '
            'Phase 2 construction.', phase=2),
        _mh('MH-A3', p[U_PHASE], inv_ph, L3, s_ph,
            'ON THE PHASE / BLOCK LINE. Upstream terminus of the Phase 1 contract; receives the '
            'Phase 2 reach MH-A1 → MH-A3 later.', phase=1),
        _mh('MH-A4', p[U_SAG], inv_sag, L4, s_ctrl,
            'Lane sag (3DEP 936.3). START OF THE CONTROLLING REACH: %.1f ft at %.3f %% to POC-1 '
            'against a 0.40 %% minimum.' % (L4 + L5 + L6, 100 * s_ctrl), phase=1),
        _mh('MH-A5', p[500.0], inv500, L5, s_ctrl, 'Deep cut under the u 480–600 lane rise.', phase=1),
        _mh('MH-A6', p[272.0], inv272, L6, s_ctrl,
            'DEEPEST STRUCTURE ON THE SHEET — the lane hump at u 272 (3DEP 946.3). Trunk turns SW '
            'to POC-1 across Lot A-1 in a 20-ft sanitary sewer easement (see note 8).', phase=1),
        _mh('POC-1', POC1, POC1_INV, None, None,
            'EXISTING manhole, "Arcado Road Townhomes sewer outfall" (Gwinnett DWR). Invert is a '
            'GIS attribute, UNSURVEYED. Rim not published — field survey required.',
            rim=None, phase=1),
    ]
    rows[-1]['rim'] = None
    rows[-1]['depth'] = None
    return rows, (L4 + L5 + L6), s_ctrl, L1 + L2, L3 + L4 + L5 + L6


def build_system_b():
    """Terminus u 1,690 -> rear low point -> the off-site tie at POC-2."""
    p = {u: (u, lane_v(u) + S_OFF) for u in (U_END - 10.0, U_LOW, 1300.0)}
    L1 = dist(p[U_END - 10.0], p[U_LOW])
    L2 = dist(p[U_LOW], p[1300.0])
    L3 = dist(p[1300.0], OFFSITE_A)
    L4 = OFFSITE_LEN
    inv_low = lane_ground(U_LOW) - COVER                       # 926.50
    inv_top = lane_ground(U_END - 10.0) - COVER                # 942.40
    s1 = (inv_top - inv_low) / L1
    s_out = 0.01                                               # 1.00 % on the two on-site legs
    inv1300 = inv_low - s_out * L2
    invPL = inv1300 - s_out * L3
    s_off = (invPL - POC2_INV) / L4
    rows = [
        _mh('MH-B1', p[U_END - 10.0], inv_top, L1, s1,
            'Upstream terminus at the terminus hammerhead (u 1,690). Slope follows existing '
            'ground; < 10 %, so no concrete anchors are indicated at concept.', phase=2),
        _mh('MH-B2', p[U_LOW], inv_low, L2, s_out,
            'REAR LANE LOW POINT (3DEP 931.5) — 0.63 ft BELOW the POC-1 invert before any slope '
            'is applied, which is why the rear cannot reach POC-1 by gravity.', phase=2),
        _mh('MH-B3', p[1300.0], inv1300, L3, s_out,
            'JUNCTION / OUTFALL. Deep: the alignment is held at u 1,300 so the SW leg stays 91.7 ft '
            'from the stream head and clear of the 50/75-ft buffers (see note 10).', phase=2),
        _mh('MH-B4', OFFSITE_A, invPL, L4, s_off,
            'AT THE SW PROPERTY LINE — start of the ≈%.0f-ft OFF-SITE extension. Rim EXTRAPOLATED '
            '%.1f ft beyond the 3DEP sample grid.' % (L4, abs(OFFSITE_A[1]) - 217.5),
            rim=ground(*OFFSITE_A), phase=2),
        _mh('POC-2', POC2, POC2_INV, None, None,
            'EXISTING manhole on the Legends at Parkview 8-in main (Gwinnett DWR). Invert is a GIS '
            'attribute, UNSURVEYED. Doghouse / drop connection and manhole type per DWR.', phase=2),
    ]
    rows[-1]['rim'] = None
    rows[-1]['depth'] = None
    return rows, L1 + L2 + L3, L4, s_off


MH_A, CTRL_LEN, CTRL_S, A_PH2_LEN, A_PH1_LEN = build_system_a()
MH_B, B_ONSITE, B_OFFSITE, B_S_OFF = build_system_b()

# ---------------------------------------------------------------- lot -> system, meters, laterals
def lot_front(lot):
    """(u0, u1, v of the front lot line) for a lot."""
    us = [p[0] for p in lot['polygon']]
    vs = [p[1] for p in lot['polygon']]
    return min(us), max(us), (max(vs) if lot['side'] == 'SW' else min(vs))


SERVICES = []
for _l in LOTS:
    _u0, _u1, _fv = lot_front(_l)
    _uc = 0.5 * (_u0 + _u1)
    SERVICES.append({'lot': _l, 'u0': _u0, 'u1': _u1, 'front_v': _fv,
                     'meter_u': _u0 + 12.0, 'lat_u': _u0 + 38.0,
                     'system': 'B' if _uc >= U_DIVIDE else 'A'})
N_SYS_B = sum(1 for s in SERVICES if s['system'] == 'B')
N_SYS_A = len(SERVICES) - N_SYS_B
SYS_B_LOTS = sorted('%s-%d' % (s['lot']['block'], s['lot']['block_lot'])
                    for s in SERVICES if s['system'] == 'B')

P1 = [l for l in LOTS if l['phase'] == 1]
P2 = [l for l in LOTS if l['phase'] == 2]
P1_SW = sum(1 for l in P1 if l['side'] == 'SW')
P2_SW = sum(1 for l in P2 if l['side'] == 'SW')

# ---------------------------------------------------------------- hydrant schedule
HYD = []
for _i, _u in enumerate(HYD_U, 1):
    HYD.append({'id': 'FH-%d' % _i, 'u': _u, 'v': lane_v(_u) + W_OFF, 'sta': station(_u)})
for _i in range(len(HYD) - 1):
    HYD[_i]['spacing'] = HYD[_i + 1]['sta'] - HYD[_i]['sta']
HYD[-1]['spacing'] = None
HYD_MAX_SP = max(h['spacing'] for h in HYD if h['spacing'])
HYD_AVG_SP = (HYD[-1]['sta'] - HYD[0]['sta']) / (len(HYD) - 1)
HYD_MAX_REACH = max([HYD[0]['sta']] + [h['spacing'] / 2.0 for h in HYD if h['spacing']])

# ---------------------------------------------------------------- flows (Gwinnett DWR guidelines)
N_LOTS = len(LOTS)
CLUB_SF = AMEN['clubhouse_sf']
UNIT_GPD, CLUB_GPD_K, PEAK = 250.0, 175.0, 4.0
CLUB_GPD = CLUB_SF / 1000.0 * CLUB_GPD_K
AADF_ALL = N_LOTS * UNIT_GPD + CLUB_GPD
AADF_P1 = len(P1) * UNIT_GPD + CLUB_GPD
AADF_P2 = len(P2) * UNIT_GPD
AADF_B = N_SYS_B * UNIT_GPD
CAP_8IN_GPM = (1.49 / 0.013) * (math.pi * (8 / 12.) ** 2 / 4) * ((8 / 12.) / 4) ** (2 / 3.) \
    * 0.004 ** 0.5 * 448.831

# ---------------------------------------------------------------- water demand
W_AVG = N_LOTS * UNIT_GPD + CLUB_GPD
W_MAXDAY = 2.0 * W_AVG
W_PEAKHR = 4.0 * W_AVG / 1440.0
MAIN_LEN_LANE = LANE_LEN
MAIN_LEN_RW = dist(WATER_TAP, (LANE['entrance']['u_rw'], LANE['entrance']['v_rw']))
MAIN_LEN = MAIN_LEN_LANE + MAIN_LEN_RW
MAIN_VOL_GAL = MAIN_LEN * (math.pi * (8 / 12.) ** 2 / 4) * 7.4805

# ---------------------------------------------------------------- off-site disturbance
EASE_W, TEMP_W = 20.0, 10.0
OFF_ROWS = [
    ('Phase 2 sanitary sewer extension — %.1f LF x %.0f-ft construction corridor '
     '(%.0f-ft permanent sanitary sewer easement + %.0f-ft temporary construction easement) '
     'across PIN R6123 302, %s' % (OFFSITE_LEN, EASE_W + TEMP_W, EASE_W, TEMP_W,
                                   sb.address_of('6123 302')),
     OFFSITE_LEN * (EASE_W + TEMP_W)),
    ('Connection work area at the Legends at Parkview manhole (POC-2), 20 ft x 20 ft assumed',
     400.0),
    ('Water connection in the Arcado Rd right-of-way — tapping sleeve, valve, meter vault and '
     'pavement cut, 20 ft x 60 ft assumed', 1200.0),
    ('Entrance apron, curb returns and the 5-ft frontage sidewalk within the Arcado Rd '
     'right-of-way (24-ft drive x 20 ft + returns; 5 ft x %.0f ft of frontage; assumed)'
     % LAY['metrics']['frontage_arcado_along_rw_ft'],
     1080.0 + 5.0 * LAY['metrics']['frontage_arcado_along_rw_ft']),
]
OFF_SF = sum(r[1] for r in OFF_ROWS)
ON_SF = LAY['stormwater']['disturbed_area']['disturbed_sf']

# ============================================================================ sheet-only symbols
DEFS2 = '''<defs>
<pattern id="ssease" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(30)"><rect width="6" height="6" fill="#eef7ee"/><line x1="0" y1="0" x2="0" y2="6" stroke="#1b5e20" stroke-width="0.55"/></pattern>
<pattern id="ph1tint" patternUnits="userSpaceOnUse" width="14" height="14" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="14" stroke="#7b1fa2" stroke-width="0.5" stroke-opacity="0.35"/></pattern>
</defs>'''

CW = '#0277bd'          # proposed water
CWL = '#4fa3d1'         # proposed water service
CS = '#1b5e20'          # proposed sanitary
CSL = '#4c9a55'         # proposed lateral
CH = '#c62828'          # hydrant
CP = sb.C['phase']      # phase line
CX = '#6d6d6d'          # contingency / withdrawn


def arrow(c, p, q, size=3.6, fill=CS):
    """Flow arrowhead at the midpoint of p->q, pointing at q (sheet points)."""
    x0, y0, x1, y1 = c.X(p[0]), c.Y(p[1]), c.X(q[0]), c.Y(q[1])
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    dx, dy = (x1 - x0) / L, (y1 - y0) / L
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    px, py = -dy, dx
    c.spoly([(mx + dx * size, my + dy * size),
             (mx - dx * size * 0.7 + px * size * 0.6, my - dy * size * 0.7 + py * size * 0.6),
             (mx - dx * size * 0.7 - px * size * 0.6, my - dy * size * 0.7 - py * size * 0.6)],
            fill=fill, stroke='none')


def manhole(c, p, r=3.4, col=CS, fill='#fff'):
    c.circle(p, r, fill=fill, stroke=col, stroke_width=1.0)


def hydrant(c, p, r=3.4):
    c.circle(p, r + 1.4, fill='#fff', stroke='none')
    c.circle(p, r, fill=CH, stroke='#fff', stroke_width=0.6)


def valve(c, p, s=3.2):
    x, y = c.X(p[0]), c.Y(p[1])
    c.spoly([(x, y - s), (x + s, y), (x, y + s), (x - s, y)], fill=CW, stroke='#fff',
            stroke_width=0.4)


def meter(c, p, s=2.0):
    x, y = c.X(p[0]), c.Y(p[1])
    c.srect(x - s, y - s, 2 * s, 2 * s, fill='#fff', stroke=CW, stroke_width=0.7)


def band(path, half):
    return sb.offset_band(path, half)


# ============================================================================ plan layers
def proposed_water(c, labels=True):
    c.add('<g id="water-proposed">')
    c.pline(WATER, fill='none', stroke=CW, stroke_width=2.1)
    for s in SERVICES:
        a = (s['meter_u'], lane_v(s['meter_u']) + W_OFF)
        b = (s['meter_u'], s['front_v'])
        c.line(a, b, stroke=CWL, stroke_width=0.55)
        meter(c, b)
    club = [tuple(q) for q in AMEN['clubhouse']]
    cu = 165.0                                          # inside the clubhouse u-range and on the main
    c.line((cu, lane_v(cu) + W_OFF), (cu, min(q[1] for q in club)), stroke=CWL, stroke_width=0.7)
    meter(c, (cu, min(q[1] for q in club)), s=2.4)
    for u in VALVE_U:
        valve(c, (u, lane_v(u) + W_OFF))
    valve(c, WATER[2])
    for h in HYD:
        c.line((h['u'], lane_v(h['u']) + W_OFF), (h['u'], lane_v(h['u']) + W_OFF + 6.0),
               stroke=CH, stroke_width=1.0)
        hydrant(c, (h['u'], lane_v(h['u']) + W_OFF + 8.0))
    c.circle((U_END - 1.0, lane_v(U_END - 1.0) + W_OFF), 2.6, fill='none', stroke=CW,
             stroke_width=1.1)
    c.add('</g>')
    if not labels:
        return
    for h in HYD:
        c.text(h['u'], lane_v(h['u']) + W_OFF + 14.0, h['id'], size=6, bold=True, fill=CH, halo=True)
    c.text(700, lane_v(700) + 26.0, 'PROPOSED 8-in DI WATER MAIN — %s ft SINGLE DEAD-END RUN '
           '(NO SECOND FRONTAGE TO LOOP TO)' % format(round(MAIN_LEN_LANE), ','),
           size=6.5, bold=True, fill=CW, halo=True)
    c.text(-66.0, -212.0, 'CONNECT TO THE EXISTING ARCADO RD MAIN — TAPPING '
           'SLEEVE, VALVE AND BOX (SIZE AND MATERIAL: VERIFY WITH DWR)', size=6, fill=CW,
           halo=True, anchor='end', rot=-81)
    c.line((U_END - 1.0, lane_v(U_END) + W_OFF - 4.0), (U_END + 2.0, -150.0), stroke=CW,
           stroke_width=0.5)
    c.text(U_END + 4.0, -154.0, 'TERMINAL BLOW-OFF / AUTOMATIC FLUSHING DEVICE (DWR DETAIL W4)',
           size=6, fill=CW, halo=True, anchor='end')
    c.line((EX_HYD['local'][0], EX_HYD['local'][1] - 4.0), (EX_HYD['local'][0] + 4.0, -6.0),
           stroke=CH, stroke_width=0.5)
    c.text(EX_HYD['local'][0] + 6.0, -8.0,
           'EXISTING FIRE HYDRANT — %.0f ft FROM THE FRONT CORNER' % EX_HYD['dist_ft'],
           size=6, fill=CH, halo=True, anchor='start')


def proposed_sewer(c, labels=True):
    c.add('<g id="sewer-proposed">')
    # --- System B off-site easement band + construction corridor
    off = [OFFSITE_A, POC2]
    c.poly(band(off, (EASE_W + TEMP_W) / 2.0), fill='none', stroke=CS, stroke_width=0.6,
           stroke_dasharray='7 3')
    c.poly(band(off, EASE_W / 2.0), fill='url(#ssease)', stroke=CS, stroke_width=0.5)
    # --- mains
    c.pline(SAN_A, fill='none', stroke=CS, stroke_width=2.1)
    c.pline(SAN_B_TOP, fill='none', stroke=CS, stroke_width=2.1)
    c.pline(SAN_B_OUT, fill='none', stroke=CS, stroke_width=2.1)
    # --- laterals
    for s in SERVICES:
        a = (s['lat_u'], lane_v(s['lat_u']) + S_OFF)
        c.line(a, (s['lat_u'], s['front_v']), stroke=CSL, stroke_width=0.55)
    club = [tuple(q) for q in AMEN['clubhouse']]
    cx = 157.0
    c.line((cx, lane_v(cx) + S_OFF), (cx, min(q[1] for q in club)), stroke=CSL, stroke_width=0.7)
    # --- structures
    for m in MH_A + MH_B:
        manhole(c, m['pt'], r=(3.9 if m['tag'].startswith('POC') else 3.2),
                col=(sb.C['sewer_txt'] if m['tag'].startswith('POC') else CS))
    # --- flow arrows
    for path in (SAN_A[:2], SAN_A[-3:-1], SAN_B_TOP[:2], SAN_B_OUT[:2], [OFFSITE_A, POC2]):
        arrow(c, path[0], path[1])
    c.add('</g>')
    # --- contingency lift station (drawn only as a labelled contingency)
    c.add('<g id="ls-contingency">')
    c.poly(LS_BOX, fill='#f2f2f2', stroke=CX, stroke_width=0.9, stroke_dasharray='4 3')
    c.pline(FORCE_MAIN, fill='none', stroke=CX, stroke_width=1.2, stroke_dasharray='9 4 2 4')
    c.add('</g>')
    if not labels:
        return
    tagdv = {'MH-B3': -15.0, 'MH-A1': 7.0, 'POC-1': -12.0, 'POC-2': 0.0}
    for m in MH_A + MH_B:
        if m['tag'].startswith('POC'):
            continue                                   # POC callouts are labelled in full below
        c.text(m['pt'][0], m['pt'][1] + tagdv.get(m['tag'], 7.0), m['tag'], size=6, bold=True,
               fill=CS, halo=True)
    c.text(1275, -133, 'SANITARY DIVIDE AT u = 1,280 — SYSTEMS A AND B DO NOT CONNECT', size=6,
           fill=CS, halo=True, anchor='end')
    c.text(620, lane_v(620) - 24.0, 'PROPOSED 8-in PVC SANITARY SEWER — SYSTEM A: GRAVITY TO THE '
           'EXISTING ON-SITE MANHOLE, INV 927.13 — NO EXTENSION OF THE PUBLIC SEWER',
           size=6.5, bold=True, fill=CS, halo=True)
    c.text(1420, lane_v(1420) - 24.0, 'SYSTEM B — 8-in GRAVITY COLLECTOR', size=6.5,
           bold=True, fill=CS, halo=True)
    c.text(POC1[0] - 10, POC1[1] + 14, 'POC-1 — EXISTING MH, INV 927.13 (GIS ATTRIBUTE, UNSURVEYED)',
           size=6.5, bold=True, fill=sb.C['sewer_txt'], halo=True, anchor='end')
    c.text(POC1[0] - 10, POC1[1] + 5, 'PHASE 1 POINT OF CONNECTION — NO SEWER EXTENSION REQUIRED',
           size=6, bold=True, fill=sb.C['sewer_txt'], halo=True, anchor='end')
    c.text(POC2[0] - 10, POC2[1] + 4, 'POC-2 — EXISTING LEGENDS AT PARKVIEW MH, INV 919.58',
           size=6.5, bold=True, fill=sb.C['sewer_txt'], halo=True, anchor='end')
    c.text(POC2[0] - 10, POC2[1] + 13, '(GIS ATTRIBUTE, UNSURVEYED)', size=6,
           fill=sb.C['sewer_txt'], halo=True, anchor='end')
    mid = (0.5 * (OFFSITE_A[0] + POC2[0]), 0.5 * (OFFSITE_A[1] + POC2[1]))
    c.textlines(mid[0] + 16, mid[1] - 14,
                ['PHASE 2 — PRIMARY ROUTE',
                 '%.0f-ft OFF-SITE 8-in GRAVITY EXTENSION @ %.2f %%' % (OFFSITE_LEN, 100 * B_S_OFF),
                 "IN A 20'-0\" PERMANENT SANITARY SEWER EASEMENT",
                 "+ 10'-0\" TEMPORARY CONSTRUCTION EASEMENT",
                 'ACROSS PIN R%s, %s' % ('6123 302', sb.address_of('6123 302').upper()),
                 '(%s — 2026 DIGEST) — EASEMENT TO BE' % sb.owner_of('6123 302').upper(),
                 'NEGOTIATED AND RECORDED; NOT YET OBTAINED'],
                size=6.2, gap=1.24, bold_first=True, fill=CS, halo=True, anchor='start')
    c.text(1323.1, -316.0 - 12, 'STREAM CROSSING — 84.0 ft OFF THE SW LINE, ≈70° TO THE CHANNEL',
           size=6, bold=True, fill=sb.C['stream'], halo=True, anchor='middle')
    c.text(1323.1, -325.0 - 12, 'CORRIDOR ≈32 ft MEASURED ALONG THE BUFFER ≤ 50 ft '
           '(CHECKLIST §6.f); §9.g BUFFER VARIANCE TO BE FILED', size=6,
           fill=sb.C['stream'], halo=True, anchor='middle')
    ls = sb.poly_centroid(LS_BOX)
    c.line((ls[0] - 4.0, ls[1] - 4.0), (1470.0, -184.0), stroke=CX, stroke_width=0.5)
    c.textlines(1466, -186,
                ['CONTINGENCY ONLY — NOT PROPOSED', 'IN-TRACT LIFT STATION AND FORCE MAIN,',
                 'FORECLOSED BY GWINNETT DWR POLICY —', 'SEE THE POLICY PANEL AT THE RIGHT'],
                size=6, gap=1.3, bold_first=True, fill=CX, halo=True, anchor='end')
    c.textlines(1315, -150,
                ['DEEP OUTFALL LEG — %.1f ft DEEP AT MH-B3;' % MH_B[2]['depth'],
                 'HELD AT u = 1,300 TO KEEP 91.7 ft FROM THE STREAM HEAD'],
                size=6, gap=1.3, bold_first=True, fill=CS, halo=True, anchor='start')
    c.text(290, -142, 'DEEP CUT — %.1f ft AT MH-A6' % MH_A[5]['depth'], size=6, bold=True,
           fill=CS, halo=True, anchor='start')


def phasing(c, labels=True):
    v0, v1 = sb.SW(U_PHASE), sb.NE(U_PHASE)
    c.add('<g id="phase">')
    c.line((U_PHASE, v0), (U_PHASE, v1), stroke=CP, stroke_width=2.6, stroke_dasharray='18 6 4 6')
    for leg in TEMP_TURN:
        c.poly(leg, fill='none', stroke=CP, stroke_width=1.0, stroke_dasharray='5 3')
    c.add('</g>')
    if not labels:
        return
    c.text(U_PHASE, v1 + 40, 'PHASE / BLOCK LINE — ON LOT LINES', size=8, bold=True, fill=CP,
           halo=True)
    c.text(U_PHASE - 8, v0 - 12, 'u = 980 (STATION 1,034 ft)', size=6.5, fill=CP, halo=True,
           anchor='end')
    c.text(760, 190, 'PHASE 1 — BLOCK A — %d LOTS (%d SW / %d NE)' % (len(P1), P1_SW, len(P1) - P1_SW),
           size=13, bold=True, fill=CP)
    c.text(760, 176, 'DESIGNED TO STAND ALONE: ENTRANCE, AMENITY BLOCK, POND 1 AND GRAVITY SEWER '
           'TO A PUBLIC MAIN ALREADY INSIDE THE PROPERTY LINE', size=7, fill=CP)
    c.text(1420, 190, 'PHASE 2 — BLOCK B — %d LOTS (%d SW / %d NE)' % (len(P2), P2_SW, len(P2) - P2_SW),
           size=13, bold=True, fill=CP)
    c.text(1420, 176, 'ONLY %d OF THE %d LOTS (%s … %s) DEPEND ON THE OFF-SITE SEWER EXTENSION'
           % (N_SYS_B, N_LOTS, SYS_B_LOTS[0], SYS_B_LOTS[-1]), size=7, fill=CP)
    c.line((982.0, -216.0), (995.0, -178.0), stroke=CP, stroke_width=0.5)
    c.textlines(800, -215,
                ['TEMPORARY 120-ft FIRE-APPARATUS HAMMERHEAD AT THE PHASE 1 TERMINUS',
                 "20'-0\" LEGS x 60'-0\" — IFC 2024 (GA) TABLE D103.4 (STATION 1,034 ft > 750 ft).",
                 'BUILT ON THE UNDEVELOPED BLOCK B LOTS; REMOVED AND RESTORED IN PHASE 2.'],
                size=6, gap=1.3, bold_first=True, fill=CP, halo=True, anchor='start')


# Phase 1 ends at the phase line (station 1,034 ft > 750 ft), so IFC 2024 (GA) Table D103.4 asks
# for a turnaround there while Phase 1 stands alone. It is drawn on the UNDEVELOPED Block B lots
# immediately past the phase line — land the applicant already owns and does not build on until
# Phase 2 — rather than in the Pond 1 tract, whose basin (v -140.7 to -193.3) leaves no room.
TEMP_TURN = [sb.rect(985.0, 1005.0, lane_v(995.0) - PVMT_HALF - 60.0, lane_v(995.0) - PVMT_HALF),
             sb.rect(985.0, 1005.0, lane_v(995.0) + PVMT_HALF, lane_v(995.0) + PVMT_HALF + 60.0)]


def context(c):
    """Lots, tracts, ponds and the clubhouse, drawn light so the utilities read on top."""
    c.add('<g id="tracts">')
    for p in AMEN['tract_polygons']:
        c.poly([tuple(q) for q in p], fill=sb.C['green'], stroke=sb.C['green_line'],
               stroke_width=0.4)
    for g in LAY['greens']:
        for p in g['polygons']:
            c.poly([tuple(q) for q in p], fill=sb.C['green'], stroke=sb.C['green_line'],
                   stroke_width=0.4)
    for p in LAY['ponds']:
        c.poly([tuple(q) for q in p['tract_polygon']], fill=sb.C['green'],
               stroke=sb.C['green_line'], stroke_width=0.4)
        c.poly([tuple(q) for q in p['polygon']], fill=sb.C['pond'], stroke=sb.C['buf_line'],
               stroke_width=0.7, stroke_dasharray='5 2')
    c.add('</g>')
    c.add('<g id="lots">')
    for l in LOTS:
        c.poly([tuple(p) for p in l['polygon']], fill='#fff', stroke='#333', stroke_width=0.55)
        c.poly([tuple(p) for p in l['house']['body_polygon']], fill=sb.C['house'], stroke='#555',
               stroke_width=0.4)
        c.poly([tuple(p) for p in l['house']['garage_rect']], fill='#efd2ad', stroke='#555',
               stroke_width=0.35)
    c.add('</g>')
    c.poly([tuple(q) for q in AMEN['clubhouse']], fill='#f2c58a', stroke='#222', stroke_width=0.8)
    for l in LOTS:
        ctr = sb.poly_centroid([tuple(p) for p in l['polygon']])
        c.text(ctr[0], ctr[1] + (34 if l['side'] == 'NE' else -30),
               '%s-%d' % (l['block'], l['block_lot']), size=5.6, fill='#555')


# ============================================================================ band content
def water_rows():
    return [
        ['Main', 'Proposed 8-in ductile iron, in the private lane tract %.0f ft NE of the lane '
                 'centreline, 3.5-ft cover. 8-in (not 6-in) so that 500–1,000 gpm reaches the '
                 'terminus at ≥ 20 psi residual on a %s-ft dead end.' % (W_OFF, format(round(MAIN_LEN_LANE), ','))],
        ['Length', '%s ft in the lane tract + %.0f ft of connection in the Arcado Rd right-of-way = '
                   '%s ft. DEAD-END MAIN — there is no second public frontage to loop to.'
                   % (format(round(MAIN_LEN_LANE), ','), MAIN_LEN_RW, format(round(MAIN_LEN), ','))],
        ['Point of connection', 'Tapping sleeve, valve and box on the existing Arcado Rd main '
                                '(DIP; diameter not published in the public layer — VERIFY with '
                                'Gwinnett DWR) at local (u %.0f, v %+.0f).' % WATER_TAP],
        ['Domestic demand', '%d DU x 250 gpd + clubhouse %s SF x 175 gpd/1,000 SF = %s gpd average; '
                            'max day (x 2.0) %s gpd; peak hour (x 4.0) %.1f gpm.'
                            % (N_LOTS, format(CLUB_SF, ','), format(round(W_AVG), ','),
                               format(round(W_MAXDAY), ','), W_PEAKHR)],
        ['Fire flow', 'Stated both ways because the sprinklers are voluntary: 1,000 gpm at 20 psi '
                      'for 1 hour for one- and two-family dwellings ≤ 3,600 SF, reduced 50 % (floor '
                      '500 gpm) where every dwelling is sprinklered to NFPA 13D — IFC 2024 (GA) '
                      'Appendix B §B105.1 and Table B105.1(1). Clubhouse is a separate Table B105.2 '
                      'check — VERIFY with the Gwinnett Fire Marshal.'],
        ['Hydrants', '%d proposed on the lane (FH-1 … FH-%d) + 1 existing on Arcado Rd %.0f ft from '
                     'the front corner. Maximum spacing %.0f ft, average %.0f ft; maximum distance '
                     'from any point on the travelled way to a hydrant %.0f ft.'
                     % (len(HYD), len(HYD), EX_HYD['dist_ft'], HYD_MAX_SP, HYD_AVG_SP, HYD_MAX_REACH)],
        ['Spacing standard', 'IFC 2024 (GA) Appendix C Table C102.1 — fire-flow requirement ≤ 1,750 '
                             'gpm: average spacing 500 ft, REDUCED 100 ft for a dead-end road = '
                             '400 ft; maximum distance from any point on the road frontage to a '
                             'hydrant 250 ft. Both are met (%.0f ft average, %.0f ft maximum '
                             'reach). Gwinnett DWR Standards (2016) §2.2.15(b) asks 350–450 ft: '
                             'FH-1 to FH-5 are 350–360 ft apart. FH-6 sits 110 ft beyond FH-5 '
                             'because §2.2.15(d) asks for "a fire hydrant near the end of each '
                             'main"; confirm with DWR that the 350-ft minimum does not govern a '
                             'terminal hydrant.' % (HYD_AVG_SP, HYD_MAX_REACH)],
        ['Valves', '3 at the connection (tee assembly) + in-line valves at u 170, 530 and 1,230 — '
                   'one every third hydrant and none more than 1,000 ft apart (DWR Standards (2016) '
                   '§2.2.16(b)). Hydrant lead valves not separately shown.'],
        ['Meters and services', '%d individual 5/8-in x 3/4-in meters in the lane tract at each lot '
                                'frontage + 1 clubhouse service + 1 HOA irrigation meter. SW-side '
                                'services cross under the 22-ft pavement in casing or by bore. '
                                'Backflow prevention per the DWR cross-connection policy.' % N_LOTS],
        ['Dead-end treatment', 'Terminal blow-off or automatic flushing device at the terminus '
                               'hammerhead (DWR Standards (2016) Detail W4, "Typical Dead End Street '
                               'Termination"). The main holds ≈ %s gal against ≈ %s gpd of use — '
                               'turnover under one day — but the device is DWR\'s call.'
                               % (format(round(MAIN_VOL_GAL, -1), ',.0f'), format(round(W_AVG), ','))],
        ['Separation', 'Water main %.0f ft NE and sanitary main %.0f ft SW of the lane centreline = '
                       '%.0f ft horizontal separation, against a 10-ft minimum; 18-in vertical '
                       'separation at every crossing.' % (W_OFF, -S_OFF, SEP_FT)],
    ]


def hydrant_rows():
    rows = [['EX', '—', '(u %.0f, v %+.1f)' % (EX_HYD['local'][0], EX_HYD['local'][1]), '—',
             'EXISTING hydrant in the Arcado Rd right-of-way, %.1f ft from the front corner '
             '(Gwinnett DWR GIS). Covers the entrance apron.' % EX_HYD['dist_ft']]]
    where = {170.0: 'At the amenity block, opposite the guest parking bay.',
             530.0: 'At pocket green 1 and hammerhead 1 (u 540) — the lane is locally wider here, '
                    'which suits IFC Appendix D §D103.1.',
             880.0: 'On the lot line at u 880, opposite the Pond 1 tract frontage.',
             1230.0: 'On the lot line at u 1,230, at pocket green 2 / hammerhead 2 (u 1,110–1,130) '
                     'reach.',
             1580.0: 'On the lot line at u 1,580, opposite the Pond 2 tract frontage.',
             1690.0: 'At the terminus hammerhead, with the terminal blow-off — "a fire hydrant near '
                     'the end of each main" (DWR Standards (2016) §2.2.15(d)). Its 110-ft spacing '
                     'from FH-5 is shorter than the 350-ft minimum of §2.2.15(b) — confirm with '
                     'DWR.'}
    for h in HYD:
        rows.append([h['id'], '%s' % format(round(h['sta']), ','),
                     '(u %.0f, v %+.0f)' % (h['u'], h['v']),
                     ('%.0f' % h['spacing']) if h['spacing'] else '— (end)',
                     where[h['u']]])
    return rows


def mh_rows(rows):
    out = []
    for m in rows:
        out.append([m['tag'], '(%.0f, %+.0f)' % m['pt'],
                    ('%.1f' % m['rim']) if m['rim'] else 'VERIFY',
                    '%.2f' % m['inv'],
                    ('%.1f' % m['depth']) if m['depth'] is not None else '—',
                    ('%.1f' % m['len']) if m['len'] else '—',
                    ('%.3f' % (100 * m['slope'])) if m['slope'] else '—',
                    m['remark']])
    return out


def flow_rows():
    return [
        ['Whole development — %d lots x 250 gpd + clubhouse %s SF x 175 gpd/1,000 SF'
         % (N_LOTS, format(CLUB_SF, ',')), '%s gpd' % format(round(AADF_ALL), ','),
         '%s gpd = %.1f gpm' % (format(round(PEAK * AADF_ALL), ','), PEAK * AADF_ALL / 1440.0),
         'Governs the DWR capacity certification'],
        ['Phase 1 — %d lots + clubhouse (System A, to POC-1)' % len(P1),
         '%s gpd' % format(round(AADF_P1), ','),
         '%s gpd = %.1f gpm' % (format(round(PEAK * AADF_P1), ','), PEAK * AADF_P1 / 1440.0),
         'No public sewer is extended'],
        ['Phase 2 — %d lots, of which %d also drain to POC-1 by gravity' % (len(P2), len(P2) - N_SYS_B),
         '%s gpd' % format(round(AADF_P2), ','),
         '%s gpd = %.1f gpm' % (format(round(PEAK * AADF_P2), ','), PEAK * AADF_P2 / 1440.0),
         'Split between System A and System B'],
        ['System B only — the %d lots that need the off-site extension (%s … %s)'
         % (N_SYS_B, SYS_B_LOTS[0], SYS_B_LOTS[-1]), '%s gpd' % format(round(AADF_B), ','),
         '%s gpd = %.1f gpm' % (format(round(PEAK * AADF_B), ','), PEAK * AADF_B / 1440.0),
         'Into an 8-in main whose full-flow capacity at 0.40 %% is ≈ %.0f gpm' % CAP_8IN_GPM],
    ]


def phase_rows():
    return [
        ['Lots', '%d  (%d SW, %d NE)  —  Block A' % (len(P1), P1_SW, len(P1) - P1_SW),
         '%d  (%d SW, %d NE)  —  Block B' % (len(P2), P2_SW, len(P2) - P2_SW)],
        ['Lot stations (u)', '230 – 980', '980 – 1,680'],
        ['Cumulative density on 9.44 ac deeded', '%.2f du/ac' % (len(P1) / 9.44),
         '%.2f du/ac' % (N_LOTS / 9.44)],
        ['Private lane built', 'Arcado Rd R/W → u 980; station 0 – %s ft'
         % format(round(station(U_PHASE)), ','),
         'u 980 → 1,700; station %s – %s ft' % (format(round(station(U_PHASE)), ','),
                                                format(round(LANE_LEN), ','))],
        ['Fire-apparatus turnarounds', 'Hammerhead at u 540, plus a TEMPORARY 120-ft hammerhead at '
                                       'u 950–970 while Phase 1 stands alone',
         'Hammerheads at u 1,110 and u 1,690; the temporary turnaround is removed and restored'],
        ['Amenity', 'Entrance, clubhouse, village green, courts, mail kiosk, guest bay, monument '
                    'sign and frontage landscape strip — ALL in Phase 1', 'None'],
        ['Stormwater', 'Pond 1, u 790–970 — %s cf' % format(LAY['ponds'][0]['est_storage_cf'], ','),
         'Pond 2, u 1,490–1,670 — %s cf' % format(LAY['ponds'][1]['est_storage_cf'], ',')],
        ['Water main + hydrants', '%s ft of 8-in main; FH-1, FH-2, FH-3'
         % format(round(station(U_PHASE)), ','),
         '%s ft of 8-in main; FH-4, FH-5, FH-6 and the terminal blow-off'
         % format(round(LANE_LEN - station(U_PHASE)), ',')],
        ['Sanitary sewer', 'System A, MH-A3 → POC-1: %s ft of 8-in gravity, ALL ON SITE, to the '
                           'existing manhole at invert 927.13. NO EXTENSION OF THE PUBLIC SEWER.'
                           % format(round(A_PH1_LEN), ','),
         'System A extended MH-A1 → MH-A3: %s ft on site, serving %d lots. System B: %s ft on site + '
         '%.0f ft OFF SITE to POC-2 at invert 919.58, serving %d lots.'
         % (format(round(A_PH2_LEN), ','), len(P2) - N_SYS_B, format(round(B_ONSITE), ','),
            B_OFFSITE, N_SYS_B)],
        ['Depends on a third party?', 'NO — no off-site easement, no off-site sewer, no second '
                                      'access', 'YES — a recorded off-site sanitary sewer easement, '
                                                'a DWR capacity certification and the City\'s '
                                                'reading of the comprehensive-plan sewer policy'],
    ]


def disturbed_rows():
    rows = [[t, format(round(a), ','), '%.3f' % (a / 43560.0)] for t, a in OFF_ROWS]
    rows.append(['TOTAL DISTURBED AREA OFF SITE — Checklist §4.e, "Indicate any disturbed acres '
                 'offsite"', format(round(OFF_SF), ','), '%.3f' % (OFF_SF / 43560.0)])
    rows.append(['Disturbed area ON SITE (layout.json: site raster less the 20-ft perimeter buffer '
                 'bands and the creek-woods tract)',
                 format(round(ON_SF), ','), '%.3f' % (ON_SF / 43560.0)])
    rows.append(['TOTAL DISTURBED AREA, ON AND OFF SITE', format(round(ON_SF + OFF_SF), ','),
                 '%.3f' % ((ON_SF + OFF_SF) / 43560.0)])
    return rows


LEGEND = [
    ('line', CW, 2.1, '', 'Proposed 8-in DI water main'),
    ('line', CWL, 0.55, '', 'Proposed water service and 5/8-in meter'),
    ('sq', CW, 0, '', 'Water meter (typical, each lot)'),
    ('dia', CW, 0, '', 'Proposed gate valve and box'),
    ('dot', CH, 0, '', 'Proposed fire hydrant (FH-1 … FH-6)'),
    ('ring', CW, 0, '', 'Terminal blow-off / automatic flushing device'),
    ('line', CS, 2.1, '', 'Proposed 8-in PVC gravity sanitary sewer'),
    ('line', CSL, 0.55, '', 'Proposed sanitary service lateral (typical)'),
    ('mh', CS, 0, '', 'Proposed sanitary manhole (MH-A1 … MH-A6, MH-B1 … MH-B4)'),
    ('mh', sb.C['sewer_txt'], 0, '', 'Existing manhole / point of connection (POC-1, POC-2)'),
    ('rect', 'url(#ssease)', 0, '', "Proposed 20'-0\" sanitary sewer easement (off site)"),
    ('line', CS, 0.6, '7 3', "Temporary construction easement, 10'-0\" (off site)"),
    ('line', CX, 1.2, '9 4 2 4', 'CONTINGENCY ONLY — lift station and force main (not proposed)'),
    ('line', CP, 2.6, '18 6 4 6', 'Phase / block line — on lot lines'),
    ('line', CP, 1.0, '5 3', 'Temporary fire-apparatus turnaround (Phase 1)'),
    ('line', sb.C['sewer'], 0.9, '', 'Existing 8-in sanitary sewer and manholes'),
    ('rect', 'url(#ssehatch)', 0, '', "Existing 20' sanitary sewer easement (VERIFY)"),
    ('line', sb.C['water'], 0.9, '9 3 2 3', 'Existing water main (Gwinnett DWR)'),
    ('dot', sb.C['hydrant'], 0, '', 'Existing fire hydrant'),
    ('line', sb.C['stream'], 1.6, '', 'Stream — state waters (top of bank approximate)'),
    ('line', sb.C['buf_line'], 0.5, '3 2', "25' state (GA EPD) buffer"),
    ('line', sb.C['buf_line'], 0.8, '6 2', "50' undisturbed stream buffer (Lilburn)"),
    ('line', sb.C['buf_line'], 0.8, '8 2 2 2', "75' impervious setback"),
    ('line', sb.C['contour_txt'], 0.9, '7 3', 'Existing index contour, 10 ft (3DEP approximate)'),
    ('line', sb.C['contour'], 0.45, '3 2', 'Existing contour, 2 ft (3DEP approximate)'),
    ('line', sb.C['bnd'], 1.8, '', 'Assemblage boundary (Gwinnett GIS — DRAFT)'),
    ('rect', sb.C['adj_fill'], 0, '', 'Adjoining tax parcel (all zoned R-1, Lilburn)'),
    ('line', sb.C['rw'], 0.9, '', 'Arcado Rd right-of-way line'),
    ('line', '#333', 0.6, '14 3 3 3', 'Existing road centreline'),
    ('rect', '#fff', 0.55, '', 'Proposed lot (41 lots — see Sheet C-2.0)'),
    ('rect', sb.C['house'], 0, '', 'Proposed dwelling and garage (typical)'),
    ('rect', '#f2c58a', 0, '', 'Clubhouse (water and sanitary service shown)'),
    ('rect', sb.C['green'], 0, '', 'Common open-space tract (HOA)'),
    ('rect', sb.C['pond'], 0, '', 'Dry detention / water-quality pond (Sheet C-3.0)'),
    ('rect', sb.C['tract'], 0, '', 'Private lane tract'),
    ('rect', sb.C['pave'], 0, '', 'Private lane pavement and hammerhead turnarounds'),
    ('rect', '#f7f7f7', 0.35, '', "Sidewalk, 5'-0\" (Sheets C-2.0 and C-8.0)"),
    ('line', '#444', 0.4, '12 3 2 3', 'Private lane centreline'),
    ('arrow', CS, 0, '', 'Direction of flow (gravity sanitary sewer)'),
]

POLICY = [
    ('Gwinnett County DWR, Developer Pump Station Standards (January 2014, posting WSR-24), '
     '§1.3.1(A):', True),
    ('"Approval for the installation of a new pump station will only be granted by the GCDWR\'s '
     'AMIS Division Director through consultation with the GCDP&D. Generally, pump stations will '
     'only be permitted when gravity sewer is unavailable to the property. Unavailable shall '
     'generally be interpreted to mean more than 5,000 feet down gradient, but this distance can '
     'be increased or decreased by GCDWR Division Directors based upon actual field conditions and '
     'the size of the project involved."', False),
    ('Gwinnett County DWR, Standard Policy for Private Developments: Condominiums, Townhomes and '
     'Subdivisions (rev. September 2018):', True),
    ('"PRIVATE FACILITIES: Private pump stations, private force mains and private gravity sewers '
     'are only allowed for commercial properties under single ownership within a development. '
     'Gwinnett County is not responsible for operation and maintenance of these facilities."', False),
    ('and, immediately above it: "OWNERSHIP OF MAINS AND APPURTENANCES: Absolute title and '
     'ownership of all water and sanitary sewer mains within the private development shall be '
     'conveyed to Gwinnett County WSA at the time of acceptance by the County."', False),
]


def legend_panel(D, x, y, w=624.0, h=276.0):
    """Boxed legend inside the plan window's empty NE margin (u -8 to 508, v 15 to 232 — off the
    property, north-east of the NE line). Two columns; every symbol drawn on the sheet appears."""
    D.srect(x, y, w, h, fill='#fff', fill_opacity='0.94', stroke='#000', stroke_width=1.0)
    D.stext(x + 10, y + 15, 'LEGEND — every symbol drawn on this sheet appears here, and no unused '
                            'entry appears', size=8.5, bold=True)
    half = (len(LEGEND) + 1) // 2
    for i, (kind, col, wdt, dash, txt) in enumerate(LEGEND):
        cx = x + 10 + (0 if i < half else w / 2.0)
        yy = y + 31 + (i % half) * 11.9
        if kind == 'line':
            D.sline(cx, yy - 3, cx + 34, yy - 3, stroke=col, stroke_width=wdt, stroke_dasharray=dash)
        elif kind == 'dot':
            D.scircle(cx + 17, yy - 3, 3.4, fill=col, stroke='#fff', stroke_width=0.6)
        elif kind == 'ring':
            D.scircle(cx + 17, yy - 3, 2.6, fill='none', stroke=col, stroke_width=1.1)
        elif kind == 'mh':
            D.scircle(cx + 17, yy - 3, 3.4, fill='#fff', stroke=col, stroke_width=1.0)
        elif kind == 'sq':
            D.srect(cx + 15, yy - 5, 4, 4, fill='#fff', stroke=col, stroke_width=0.7)
        elif kind == 'dia':
            D.spoly([(cx + 17, yy - 6.2), (cx + 20.2, yy - 3), (cx + 17, yy + 0.2),
                     (cx + 13.8, yy - 3)], fill=col, stroke='#fff', stroke_width=0.4)
        elif kind == 'arrow':
            D.sline(cx, yy - 3, cx + 34, yy - 3, stroke=col, stroke_width=2.1)
            D.spoly([(cx + 26, yy - 3), (cx + 17.5, yy - 7.2), (cx + 17.5, yy + 1.2)], fill=col,
                    stroke='none')
        else:
            D.srect(cx, yy - 9.5, 34, 12, fill=col, stroke='#555',
                    stroke_width=(wdt if wdt else 0.4))
        D.stext(cx + 40, yy, txt, size=6.4)


def build():
    scale_note = 'Scale 1" = 60\' (ARCH D 36 × 24 in)'
    D, F = sb.sheet('UTILITY AND PHASING CONCEPT', 'C-4.0',
                    'Water, sanitary sewer and phasing concept — Lilburn Zoning Ordinance 2023-603 '
                    '§1003-4.6 and City of Lilburn Site Development Plan Review Checklist §4.d, '
                    '§4.e, §4.i, §4.o, §6.f, §9.g, §10.c and §10.h',
                    scale_note, generator='tools/sitebase.py + tools/utility.py',
                    status_lines=[
                        'Utility and phasing CONCEPT compiled from public records for',
                        'pre-application review. Every existing invert shown is a Gwinnett',
                        'DWR GIS attribute and is UNSURVEYED; proposed rims are USGS 3DEP',
                        'interpolations. To be superseded by a sealed PE utility design and',
                        'a Gwinnett DWR sewer capacity certification.'],
                    scale_at=(sb.PLAN_X0 + 690, sb.PLAN_Y0 + sb.PLAN_H - 30))
    px, py, pw, ph = F['plan']
    # the base watermark names Sheet C-0's subject; replace it with this sheet's, and move it
    # clear of the drawn work into the Legends at Parkview margin
    wmx, wmy = px + 700, py + ph - 140
    D.late[1] = lambda: D.add(
        '<text x="%.1f" y="%.1f" font-size="34" fill="#c00" fill-opacity="0.10" font-weight="bold" '
        'text-anchor="middle" transform="rotate(-6 %.1f %.1f)">DRAFT — NOT SEALED — UTILITY AND '
        'PHASING CONCEPT, NOT FOR CONSTRUCTION</text>' % (wmx, wmy, wmx, wmy))
    D.add(DEFS2)

    # ---------------------------------------------------------------- plan
    D.clip_open(fill='#fff')
    sb.adjoiners(D, labels=False, zoning=False)
    sb.arcado_row(D, labels=False)
    sb.contours(D, existing=True, labels=False)
    context(D)
    sb.lane(D, labels=False)
    sb.streams_and_buffers(D, labels=False)
    sb.sewer_existing(D, labels=False)
    sb.water_existing(D, labels=False)
    sb.boundary(D, bearings=False, label=False)
    phasing(D)
    proposed_sewer(D)
    proposed_water(D)

    D.text(60, -258, 'EXISTING 8-in SANITARY SEWER IN A 20-ft EASEMENT ("EX. 20\' SSE") — THE MAIN '
                     'ALREADY CROSSES THE PROPERTY, SO PHASE 1 EXTENDS NOTHING', size=6.5,
           bold=True, fill=sb.C['sewer_txt'], halo=True, anchor='start')
    D.text(-138, -150, 'EXISTING WATER MAINS IN ARCADO RD (DIP / ACP — SIZES NOT PUBLISHED; VERIFY)',
           size=6, rot=-81, fill=sb.C['water'], halo=True)
    D.text(1455, -368, 'UNNAMED STREAM (STATE WATERS, ORDER-0 HEADWATER OF JACKSON CREEK '
                       'GAR030701030315) — TOP OF BANK APPROXIMATE, FIELD DELINEATION REQUIRED',
           size=6, fill=sb.C['stream'], halo=True, anchor='end')
    D.text(1250, 232, 'PROPOSED UTILITIES ARE A CONCEPT ONLY — NO PROFILE IS DESIGNED ON THIS SHEET; '
                      'SEE SHEET C-4.1 SANITARY SEWER PROFILES AND SHEET C-5.0 PRIVATE LANE PLAN '
                      'AND PROFILE', size=7, bold=True, fill='#444')
    D.text(1000, -412, 'LEGENDS AT PARKVIEW (PLAT 118/187) — ZONED R-1 (CITY OF LILBURN); '
                       'EXISTING 8-in SANITARY SEWER SHOWN', size=7.5, bold=True, fill='#555')
    D.text(1160, 150, 'KING DAVID MANOR (PLAT S/159) — ZONED R-1 (CITY OF LILBURN)', size=7.5,
           bold=True, fill='#555')
    legend_panel(D, px + 168, py + 6)
    D.clip_close()
    D.later(lambda: D.srect(sb.PLAN_X0 + 676, sb.PLAN_Y0 + sb.PLAN_H - 46, 320, 62, fill='#fff',
                            fill_opacity='0.85', stroke='none'))
    D.late.append(D.late.pop(-2))          # keep the scale bar above its white backing panel
    D.stext(px + pw, py - 8, 'PHASE 1 IS DESIGNED TO STAND ALONE — SEE THE PHASING TABLE BELOW',
            size=11, bold=True, fill=CP, anchor='end')

    # ================================================================ band
    ends = {}
    # ---------------------------------------------------------------- A: water + disturbed area
    xa, wa = F['inner_l'] + 10, 452.0
    y = sb.table(D, xa, sb.BAND_Y0, ['ITEM', 'PROPOSED — CONCEPT ONLY; PE DESIGN AND GWINNETT DWR '
                                     'APPROVAL REQUIRED'],
                 water_rows(), size=6.4, widths=[98, 354],
                 title='WATER — PROPOSED SYSTEM DATA')
    y = sb.table(D, xa, y + 18, ['ID', 'STATION', 'LOCATION (u, v)', 'TO NEXT', 'PLACEMENT AND BASIS'],
                 hydrant_rows(), size=6.4, widths=[28, 42, 66, 42, 274],
                 title='HYDRANT SCHEDULE — stations along the travelled way')
    y = D.stextblock(xa, y + 10, 'Every hydrant is on the proposed 8-in main on the NE side of the '
                                 'lane, 3 ft behind the back of curb, on a lot line where one is '
                                 'available. Hydrant lead valves are required at each hydrant and are '
                                 'not separately symbolised; see Sheet C-8.0 for the hydrant assembly '
                                 'detail.', size=6.2, chars=118, lead=7.9, fill='#444')
    D.stext(xa, y + 26, 'CONSTRUCTION SEQUENCE — CONCEPT; THE APPROVALS EACH PHASE DEPENDS ON',
            size=9, bold=True)
    yy = D.stextblock(xa, y + 39,
                      'PHASE 1 — (1) Georgia RLS boundary and topographic survey, an invert survey '
                      'of POC-1 and rock probes on the System A trunk; (2) Gwinnett DWR sewer '
                      'capacity certification ("Pre-Rezoning" request) and a DWR flow test at the '
                      'Arcado Rd hydrant; (3) Gwinnett DOT driveway permit and the City land '
                      'disturbance permit (NPDES NOI, erosion-control bond); (4) entrance, entry '
                      'drive and lane to u 980 with the temporary hammerhead, System A sewer '
                      'MH-A3 → POC-1, 8-in water main to FH-3, Pond 1 and the amenity block; '
                      '(5) as-builts, DWR acceptance and the Block A final plat.',
                      size=6.4, chars=118, lead=7.9)
    yy = D.stextblock(xa, yy + 6,
                 'PHASE 2 — (6) a recorded off-site sanitary sewer easement across PIN R6123 302 and '
                 'the Checklist §9.g buffer variance for the stream crossing; (7) lane u 980 → 1,700, '
                 'temporary hammerhead removed and the area restored; (8) System A extension '
                 'MH-A1 → MH-A3, the System B collector and the %.0f-ft off-site extension to POC-2, '
                 'water main to FH-6 and the terminal blow-off; (9) Pond 2, as-builts, DWR acceptance '
                 'and the Block B final plat.' % OFFSITE_LEN, size=6.4, chars=118, lead=7.9)
    ends['A'] = yy

    # ---------------------------------------------------------------- B: sanitary schedules
    xb, wb = xa + wa + 16, 580.0
    cols = ['STR.', 'LOCATION (u, v)', 'RIM', 'INVERT', 'DEPTH', 'RUN (ft)', 'SLOPE %', 'REMARKS']
    wid = [38, 76, 40, 44, 38, 42, 42, 260]
    y = sb.table(D, xb, sb.BAND_Y0, cols, mh_rows(MH_A), size=6.4, widths=wid,
                 title='SANITARY MANHOLE SCHEDULE — SYSTEM A (PHASE 1 GRAVITY TO POC-1, INV 927.13)')
    y = D.stextblock(xb, y + 10, 'Phase 1 constructs MH-A3 → POC-1 = %s ft; Phase 2 extends MH-A1 → '
                                 'MH-A3 = %s ft, all on site. RIM = existing ground interpolated from '
                                 'the USGS 3DEP 1-m DEM (APPROXIMATE). DEPTH = rim − invert. '
                                 'SLOPE = (invert in − invert out) ÷ run. The finished lane profile is '
                                 'not designed on this sheet; every rim and every slope must be re-cut '
                                 'to it — see Sheets C-4.1 and C-5.0.'
                     % (format(round(A_PH1_LEN), ','), format(round(A_PH2_LEN), ',')),
                     size=6.2, chars=152, lead=7.9, fill='#444')
    y = sb.table(D, xb, y + 14, cols, mh_rows(MH_B), size=6.4, widths=wid,
                 title='SANITARY MANHOLE SCHEDULE — SYSTEM B (PHASE 2, THE %.0f-ft OFF-SITE '
                       'EXTENSION TO POC-2, INV 919.58)' % OFFSITE_LEN)
    y = D.stextblock(xb, y + 10, 'System B: %s ft on site + %.1f ft off site = %s ft, falling %.2f ft '
                                 'from invert %.2f at MH-B1 to invert %.2f at POC-2 — an overall '
                                 '%.2f %% against a 0.40 %% minimum. MH-B4 → POC-2 is the only reach '
                                 'outside the property. The MH-B2 → POC-2 sub-reach is %.0f ft, of '
                                 'which %.0f ft is off site: that is the route docs/08 Memo B B.5 '
                                 'prices at "≈479 ft, of which ≈178 ft off-site".'
                     % (format(round(B_ONSITE), ','), B_OFFSITE,
                        format(round(B_ONSITE + B_OFFSITE), ','), MH_B[0]['inv'] - POC2_INV,
                        MH_B[0]['inv'], POC2_INV,
                        100 * (MH_B[0]['inv'] - POC2_INV) / (B_ONSITE + B_OFFSITE),
                        MH_B[1]['len'] + MH_B[2]['len'] + OFFSITE_LEN, OFFSITE_LEN),
                     size=6.2, chars=152, lead=7.9, fill='#444')
    y = sb.table(D, xb, y + 14, ['BASIS (Gwinnett DWR Flow Estimation Guidelines, Rev. 10/2022)',
                                 'AADF', 'PEAK (× 4.0)', 'NOTE'],
                 flow_rows(), size=6.4, widths=[236, 68, 96, 180],
                 title='ESTIMATED SANITARY FLOWS — 250 gpd/home, 175 gpd per 1,000 SF of clubhouse, '
                       'peaking factor 4.0')
    D.stextblock(xb, y + 10, 'The constraint is the downstream county system, not the on-site pipe — '
                             'which is exactly what the Gwinnett DWR sewer capacity certification '
                             'tests. See question Q1 at the right.', size=6.2, chars=152, lead=7.9,
                 fill='#444')
    y = sb.table(D, xb, y + 34, ['OFF-SITE WORK — ASSUMPTIONS STATED', 'AREA (SF)', 'AREA (AC)'],
                 disturbed_rows(), size=6.4, widths=[392, 90, 98],
                 title='DISTURBED AREA — SITE DEVELOPMENT PLAN REVIEW CHECKLIST §4.e')
    ends['B'] = y

    # ---------------------------------------------------------------- C: governing policy + questions
    xc, bw = xb + wb + 16, 418.0
    D.stext(xc, sb.BAND_Y0 - 3, 'GOVERNING GWINNETT DWR POLICY', size=9, bold=True)
    D.stext(xc, sb.BAND_Y0 + 7, 'why the off-site gravity tie is the PRIMARY Phase 2 route and no '
                                'pumping solution is proposed', size=7.4, bold=True, fill='#7a0000')
    box_y = sb.BAND_Y0 + 13
    yy = box_y + 13
    for txt, head in POLICY:
        yy = D.stextblock(xc + 7, yy, txt, size=6.4, chars=94, lead=8.0,
                          bold=head, fill=('#111' if head else '#7a0000'))
        yy += 3.0
    D.srect(xc, box_y, bw, yy - box_y + 3, fill='none', stroke='#7a0000', stroke_width=1.0)
    yy += 13
    yy = D.stextblock(xc, yy, 'Gravity is %.0f ft away, not more than 5,000 ft. A %d-lot FEE-SIMPLE '
                              'subdivision is not "commercial property under single ownership". '
                              'Gwinnett DWR publishes no design standard for grinder pumps or '
                              'low-pressure sewer — zero occurrences of "grinder" in the Water and '
                              'Sewer Standards (April 2016) and in WSR-24. An in-tract lift station, '
                              'private force main, private gravity sewer or grinder / low-pressure '
                              'system is therefore NOT AVAILABLE to this project and is shown on the '
                              'plan only as a labelled contingency.' % (OFFSITE_LEN, N_LOTS),
                      size=6.6, chars=92, lead=8.4, bold=True)
    yy += 11
    D.stext(xc, yy, 'QUESTIONS PUT TO GWINNETT DWR AND TO THE CITY ON THIS SHEET', size=9, bold=True)
    qy = yy + 5
    yy = qy + 12
    for head, body in questions():
        D.stext(xc + 7, yy, head, size=6.6, bold=True)
        yy = D.stextblock(xc + 7, yy + 8.4, body, size=6.4, chars=94, lead=8.0)
        yy += 3.6
    D.srect(xc, qy, bw, yy - qy - 2, fill='none', stroke='#333', stroke_width=0.8)
    ends['C'] = yy

    # ---------------------------------------------------------------- D: phasing
    xd, wd = xc + bw + 16, 358.0
    y = sb.table(D, xd, sb.BAND_Y0, ['ITEM', 'PHASE 1 — BLOCK A', 'PHASE 2 — BLOCK B'],
                 phase_rows(), size=6.4, widths=[80, 139, 139],
                 title='PHASING — %d LOTS IN TWO BLOCKS' % N_LOTS)
    yy = D.stextblock(xd, y + 10, 'Site Development Plan Review Checklist §4.i: "Phasing is not '
                                  'permitted unless platted in Blocks." The phase line at u = 980 is '
                                  'drawn ON LOT LINES — it is the common line between Lots A-10 and '
                                  'B-1 (SW), between Lots A-24 and B-5 (NE) and along the Pond 1 '
                                  'tract; no lot is divided by it. Blocks A and B are to be platted '
                                  'as such on the final plat, by a Georgia RLS.',
                      size=6.2, chars=96, lead=8.0, fill='#444')
    yy += 12
    yy = D.stextblock(xd, yy, 'PHASE 1 STANDS ALONE. It contains the entrance, the whole amenity '
                              'block, Pond 1, a turnaround and gravity sewer to a public main that '
                              'is already inside the property line. It needs no off-site easement, '
                              'no off-site sewer main and no second access. Phase 2 is the only part '
                              'of this application that depends on a third party, and only %d of the '
                              '%d lots depend on it.' % (N_SYS_B, N_LOTS),
                      size=6.6, chars=88, lead=8.4, bold=True, fill=CP)
    yy += 14
    D.stext(xd, yy, 'SOURCES AND ACCESS DATES', size=9, bold=True)
    yy = D.stextblock(xd, yy + 13, sources(), size=6.2, chars=96, lead=7.9)
    ends['D'] = yy

    # ---------------------------------------------------------------- E/F: general notes, 2 columns
    xe, we = xd + wd + 16, 288.0
    xf = xe + we + 16
    NN = notes()
    hs = [len(sb.wrap('%d. %s' % (i, n), 70)) * 7.9 + 2.4 for i, n in enumerate(NN, 1)]
    brk = min(range(1, len(hs)), key=lambda k: max(sum(hs[:k]), sum(hs[k:])))
    D.stext(xe, sb.BAND_Y0, 'GENERAL NOTES — UTILITY AND PHASING', size=9, bold=True)
    D.stext(xf, sb.BAND_Y0, 'GENERAL NOTES (continued)', size=9, bold=True)
    yy = sb.BAND_Y0 + 13
    for i, n in enumerate(NN, 1):
        if i == brk + 1:
            ends['E'] = yy
            yy = sb.BAND_Y0 + 13
        yy = D.stextblock(xe if i <= brk else xf, yy, '%d. %s' % (i, n), size=6.4, chars=70,
                          lead=7.9, indent=9)
        yy += 2.4
    ends['F'] = yy

    for k in sorted(ends):
        print('  band column %-4s ends at y = %.0f   (band runs %d → %d)'
              % (k, ends[k], sb.BAND_Y0, sb.BAND_Y1))
    return D


def questions():
    return [
        ('Q1 — DWR, sewer capacity certification.',
         'Submitted on the Sewer Capacity Certification Request, Rev. 07/2023, "Pre-Rezoning" request '
         'type, sealed by a design professional, to DWRCapacityCertification@GwinnettCounty.com '
         '(allow 10 business days, +20 if analysis or flow monitoring is required). Does downstream '
         'capacity exist for %s gpd AADF at POC-1, the Arcado Road Townhomes outfall, and %s gpd at '
         'POC-2, Legends at Parkview? Please confirm both facility IDs.'
         % (format(round(AADF_P1), ','), format(round(AADF_B), ','))),
        ('Q2 — DWR, pumping.',
         'Does DWR concur that no pumping solution — county-owned station, HOA-owned station, force '
         'main, grinder pump or low-pressure sewer — is available to a fee-simple residential '
         'subdivision under the two policies quoted above, so that the %.0f-ft gravity tie is the '
         'only Phase 2 route?' % OFFSITE_LEN),
        ('Q3 — DWR, the dead-end water main: LOOPING AND OVERSIZING.',
         'The lane is a single %s-ft dead-end main and there is no second public frontage to loop to. '
         '(a) Does DWR accept an 8-in dead-end main at this length, or does it require an oversized '
         'main? (b) Is a terminal blow-off sufficient, or is an automatic flushing device required '
         '(DWR Standards (2016) Detail W4)? (c) Is any looping alternative available — a connection '
         'through the Nantucket or King David Manor systems at the rear, for example — that DWR would '
         'prefer? Please schedule a flow test at the existing Arcado Rd hydrant so the 8-in size can '
         'be confirmed against 1,000 gpm at 20 psi residual.' % format(round(MAIN_LEN_LANE), ',')),
        ('Q4 — DWR, easement, connection and ownership.',
         'What permanent easement width and manhole type does DWR require at POC-2, and will DWR '
         'accept a doghouse connection on the existing main? Would DWR instead prefer a new manhole '
         'on the existing on-site main at u ≈ 220, inside the amenity tract, in place of the Lot A-1 '
         'crossing to POC-1 (note 8)? All mains are to be conveyed to Gwinnett County WSA on '
         'acceptance, per the ownership clause quoted above.'),
        ('Q5 — City of Lilburn, the comprehensive-plan sewer policy.',
         'The 2026 Comprehensive Plan Amendment (transmitted to DCA 2026-07-13; adoption pending as '
         'of %s) carries the Suburban-Low policy "Do not further extend sewer in this area". Phase 1 '
         'extends nothing — the existing 8-in main already crosses the property. Phase 2 is a %.0f-ft '
         'connection between two existing county mains in the same drainage basin that opens no '
         'unsewered land. Does the City read the policy as reaching that connection? And which Future '
         'Development class do these four parcels fall in — Suburban-Low (p. 73) or Suburban-Medium '
         '(p. 71)? THIS QUESTION IS UNRESOLVED AND IS DISCLOSED HERE RATHER THAN ASSUMED AWAY.'
         % (sb.DATE, OFFSITE_LEN)),
    ]


def sources():
    return ('SOURCES. data/layout.json (boundary, lots, lane, ground profile, ponds, phase line, '
        'disturbed area); data/site-context-local.json (existing sewer, water mains, hydrants, '
        'adjoining parcels — Gwinnett County GIS, queried 2026-08-28); data/topo-samples.json (USGS '
        '3DEP 1-m DEM); Gwinnett County Tax Assessor 2026 property-ownership file; Gwinnett DWR '
        'Developer Pump Station Standards (Jan 2014, WSR-24), Standard Policy for Private '
        'Developments: Condominiums, Townhomes and Subdivisions (rev. 9/2018), Water and Sewer '
        'Standards (April 2016), Wastewater Flow Estimation Guidelines (Rev. 10/2022) and Sewer '
        'Capacity Certification Request (Rev. 07/2023); IFC 2024 as adopted and modified by Ga. Comp. '
        'R. & Regs. R. 120-3-3-.04, Appendices B, C and D; City of Lilburn Site Development Plan '
        'Review Checklist; Lilburn Zoning Ordinance 2023-603 §1003-4.6; FACTS.md §2, §2b, §3; '
        'docs/08 Memos B and C; audit-2026-09-03 external-facts.md §3.4 and §3.5 and site-geometry.md '
        '§4.')


def notes():
    return [
        'STATUS. DRAFT — NOT SEALED. A utility and phasing CONCEPT prepared by the owner from public '
        'records for pre-application review; not a construction document, and no profile is designed '
        'on it. All water and sanitary design must be prepared, signed and sealed by a Georgia-'
        'registered professional engineer and approved by Gwinnett County DWR before any land '
        'disturbance permit. Every statement of conformity reads "appears consistent with" and none '
        'is a compliance certification.',

        'PROVISION FOR UTILITIES (Checklist §4.d — "Note provision for all utilities (GC to provide '
        'only water and sewer)"). Water and sanitary sewer: Gwinnett County Department of Water '
        'Resources. Electric, natural gas and telecommunication providers are NOT confirmed — VERIFY '
        'territory and availability in Arcado Rd. All dry utilities to be placed UNDERGROUND in a '
        'common trench in the private lane tract; no overhead line is proposed within the '
        'development. Georgia 811 locates (O.C.G.A. §25-9) before any field work; a full '
        'existing-utility survey with the land disturbance permit. Storm drainage: Sheet C-3.0.',

        'THE INVERTS GOVERN EVERYTHING AND NONE OF THEM IS SURVEYED. Invert 927.13 at POC-1 and '
        'invert 919.58 at POC-2 are Gwinnett DWR GIS attributes. A sewer-invert survey of both '
        'manholes is the first field task: a 1.00-ft error at POC-1 moves the Phase 1 controlling '
        'slope from %.3f %% to about %.3f %%. Proposed rims are interpolated from the USGS 3DEP 1-m '
        'DEM on a 100 × 50-ft grid and are APPROXIMATE; the rim at MH-B4 is EXTRAPOLATED %.1f ft beyond '
        'the sampled grid. A topographic survey governs.'
        % (100 * CTRL_S, 100 * (CTRL_S - 1.0 / CTRL_LEN), abs(OFFSITE_A[1]) - 217.5),

        'PHASE 1 REQUIRES NO SEWER EXTENSION. The existing 8-in "Arcado Road Townhomes" gravity '
        'outfall (Gwinnett DWR) already crosses the property, 7–13 ft inside the SW line from '
        'u ≈ −42 to the manhole at (u 272, v −224). All %d Phase 1 lots and the clubhouse connect to '
        'it by gravity WITHIN THE PROPERTY: no public main is extended, no new service area is '
        'opened, no off-site easement is needed. That is the direct answer to the Suburban-Low policy '
        '"Do not further extend sewer in this area" — see question Q5.' % len(P1),

        'SYSTEM A — THE CONTROLLING CONSTRAINT IS DEPTH, NOT SLOPE. From the lane sag at u %d (3DEP '
        '%.1f) the trunk has %.2f ft of fall in %.0f ft to invert 927.13 — %.3f %% against a 0.40 %% '
        'minimum, so gravity works comfortably. What costs money is cover: the ground rises to %.1f '
        'at u 272, so the trench reaches %.1f ft at MH-A6 and %.1f ft at MH-A5. A shallower SW-edge '
        'alignment inside the existing easement corridor was tested against the 3DEP grid and does '
        'NOT solve it — its controlling station is u ≈ 484, ground 944.1, depth about 15.5 ft. '
        '(docs/08 Memo B B.3 quotes "about 10 ft" for that corridor; that figure is taken at '
        'u 200–300 and is not the controlling station.) Rock probes are required before either '
        'alignment is priced — NRCS map unit ARE, gneiss bedrock at 22–40 in.'
        % (U_SAG, lane_ground(U_SAG), MH_A[3]['inv'] - POC1_INV, CTRL_LEN, 100 * CTRL_S,
           lane_ground(272.0), MH_A[5]['depth'], MH_A[4]['depth']),

        'WHY THE PROJECT IS PHASED AT ALL. The rear lane low point at u %d (3DEP %.1f) puts a sewer '
        'invert with 5 ft of cover at %.2f — already %.2f ft BELOW the POC-1 invert of 927.13 before '
        'any slope is applied — and the route back to POC-1 would pass beneath the u %d ridge crest '
        '(3DEP %.1f) at roughly 28 ft of cut. The rear pocket cannot reach the on-site manhole by '
        'gravity. That fact, not marketing, sets the phase line.'
        % (U_LOW, lane_ground(U_LOW), lane_ground(U_LOW) - COVER,
           POC1_INV - (lane_ground(U_LOW) - COVER), U_CREST, lane_ground(U_CREST)),

        'ONLY %d OF THE %d LOTS DEPEND ON THE OFF-SITE EXTENSION. The sanitary divide falls at '
        'u 1,280, not at the topographic ridge: Block B lots between u 980 and u 1,280 drain BACKWARD '
        'into System A and reach POC-1 by gravity with no extension. Lots %s through %s (NE side, '
        'u 1,280–1,680) are the only lots served by System B. If the off-site easement or the '
        'capacity certification cannot be obtained, %d of the %d lots remain serviceable.'
        % (N_SYS_B, N_LOTS, SYS_B_LOTS[0], SYS_B_LOTS[-1], N_LOTS - N_SYS_B, N_LOTS),

        'SANITARY EASEMENTS ON SITE (Checklist §4.o, §10.h). A 20-ft permanent sanitary sewer '
        'easement is required over the whole of Systems A and B, including the %.0f-ft leg from MH-A6 '
        'SW to POC-1, which crosses Lot A-1 and its rear 20-ft buffer easement. Checklist §6.f permits '
        'sanitary sewer conveyance facilities to encroach into a buffer "as near as perpendicular as '
        'possible, up to max 50\' width"; §6.c asks for 25 ft of additional buffer outside an '
        'easement, which cannot be provided inside a 100-ft lot — a question for staff. ALTERNATIVE, '
        'and probably better: a new manhole on the existing main at u ≈ 220, where the interpolated '
        'existing invert is 927.85, entirely inside the front amenity tract. That avoids the lot '
        'easement and the buffer question and saves about 1.8 ft of trench depth, but it requires DWR '
        'approval to tap an existing county main mid-run (question Q4). The PE decides; both are '
        'shown as options, not as a design.' % MH_A[5]['len'],

        'PHASE 2 — THE OFF-SITE EXTENSION IS THE PRIMARY ROUTE. %.0f ft of 8-in gravity sewer at '
        '%.2f %% from MH-B4 on the SW property line to POC-2, the existing Legends at Parkview manhole '
        'at invert 919.58, in a 20-ft permanent sanitary sewer easement with a 10-ft temporary '
        'construction easement across PIN R6123 302, %s (%s, Gwinnett 2026 digest). THE EASEMENT HAS '
        'NOT BEEN OBTAINED: it is a private negotiation with a private owner; the City cannot grant '
        'it and the applicant cannot promise it. Checklist §1.d.4 lists "Easement agreement(s) for '
        'offsite work" as a submittal.'
        % (OFFSITE_LEN, 100 * B_S_OFF, sb.address_of('6123 302'), sb.owner_of('6123 302')),

        'STREAM CROSSING AND BUFFERS. The off-site extension crosses the unnamed order-0 headwater of '
        'Jackson Creek 84.0 ft off the SW property line at about 70° to the channel; it lies within '
        'the 50-ft undisturbed buffer for about 130 ft of its length and within the 25-ft state '
        'buffer for about 57 ft. At 70° a 30-ft construction corridor measures about 32 ft along the '
        'buffer, inside the 50-ft maximum of Checklist §6.f. A buffer variance under Checklist §9.g '
        'is to be applied for for any non-exempt encroachment into the 25-ft (GA EPD) or 50-ft '
        '(Lilburn ZBA) undisturbed buffer, and the crossing restored under the Lilburn Stream Buffer '
        'Restoration Guidelines. STREAM BUFFERS ARE TO REMAIN IN A NATURAL AND UNDISTURBED CONDITION; '
        'STREAM BUFFER SHALL BE STAKED AND PROTECTED PRIOR TO LAND DISTURBANCE (Checklist §9.e, '
        '§9.f). Top of bank is NOT field delineated — a 5-ft top-of-bank allowance is carried and the '
        'delineation governs. The on-site leg is held at u = 1,300 so that it stays 91.7 ft from the '
        'stream head and clear of the 50/75-ft buffers; that is why MH-B3 is %.1f ft deep, and it is a '
        'deliberate trade of depth for buffer clearance.' % MH_B[2]['depth'],

        'NO PUMPING SOLUTION IS PROPOSED. The lift station and force main shown dashed at the rear '
        'low point are a LABELLED CONTINGENCY carried forward from an earlier revision and are NOT '
        'part of this application — see the governing policy panel. data/layout.json still carries '
        'the superseded string sewer.phase2_primary = "in-tract lift station / grinder pumps"; this '
        'sheet follows FACTS.md §2 as corrected on 2026-09-03, not that string.',

        'CAPACITY CERTIFICATION AND OWNERSHIP. A Gwinnett DWR sewer capacity certification is required '
        'for both connections (Sewer Capacity Certification Request, Rev. 07/2023, "Pre-Rezoning" '
        'type; sealed by a design professional; 10 business days, +20 if analysis or flow monitoring '
        'is required; no fee stated — VERIFY). Absolute title to all water and sanitary sewer mains '
        'within the development is to be conveyed to Gwinnett County WSA at acceptance; the private '
        'lane, sidewalks, storm system, ponds and open space remain HOA-owned and HOA-maintained '
        '(Checklist §4.o).',

        'WATER — DEAD-END MAIN. %s ft of 8-in main in the lane tract plus %.0f ft of connection in '
        'the Arcado Rd right-of-way. There is no second public frontage, so the main cannot be looped; '
        'the looping and oversizing question is put to DWR at Q3 rather than answered here. Hydrant '
        'spacing is %.0f ft maximum and %.0f ft average, and no point on the travelled way is more '
        'than %.0f ft from a hydrant — inside IFC 2024 (GA) Appendix C Table C102.1 (500 ft average, '
        'reduced 100 ft for a dead-end road; 250 ft maximum reach). FH-1 to FH-5 are 350–360 ft '
        'apart, inside the 350–450 ft of Gwinnett DWR Standards (2016) §2.2.15(b); FH-6 is the '
        'terminal hydrant §2.2.15(d) asks for and sits 110 ft beyond FH-5 — the one spacing that '
        'needs DWR concurrence.'
        % (format(round(MAIN_LEN_LANE), ','), MAIN_LEN_RW, HYD_MAX_SP, HYD_AVG_SP, HYD_MAX_REACH),

        'FIRE ACCESS — WHAT IS AND IS NOT REQUIRED. IFC 2024 as adopted and modified by Ga. Comp. R. '
        '& Regs. R. 120-3-3-.04 replaces Appendix D107.1 and requires two fire apparatus access roads '
        'only where dwelling units exceed 120. At %d units the two-access requirement is NOT engaged '
        'and NFPA 13D sprinklers are a VOLUNTARY offer, not a required mitigation. The one live item '
        'is the %s-ft dead end: Table D103.4 requires special approval over 750 ft, with the '
        'Exception 3 alternatives menu and the O.C.G.A. §25-2-12(e)(4) waiver (30-day deemed '
        'approval) as the routes to it. A temporary 120-ft hammerhead is shown at u 985–1,005 so '
        'that Phase 1 satisfies D103.4 while it stands alone.'
        % (N_LOTS, format(round(LANE_LEN), ',')),

        'PHASING (Checklist §4.i: "Phasing is not permitted unless platted in Blocks"). The phase line '
        'at u = 980 is drawn ON LOT LINES and divides no lot. Block A = Phase 1 = %d lots; Block B = '
        'Phase 2 = %d lots; %d lots total at %.2f du/ac on 9.44 deeded acres. If Phase 2 never '
        'proceeds, Phase 1 is a complete %d-lot development at %.2f du/ac.'
        % (len(P1), len(P2), N_LOTS, N_LOTS / 9.44, len(P1), len(P1) / 9.44),

        'DISTURBED AREA (Checklist §4.e). On site %s SF = %.2f ac; OFF SITE %s SF = %.2f ac; total %s '
        'SF = %.2f ac. The off-site figure is built from the assumptions tabulated at the left and is '
        'a concept estimate, not a survey quantity. The erosion-control bond, the NPDES notice of '
        'intent and the $40 per disturbed acre fees are computed on the total at the land disturbance '
        'permit stage.'
        % (format(round(ON_SF), ','), ON_SF / 43560.0, format(round(OFF_SF), ','), OFF_SF / 43560.0,
           format(round(ON_SF + OFF_SF), ','), (ON_SF + OFF_SF) / 43560.0),

    ]


if __name__ == '__main__':
    D = build()
    svg, png = sb.save(D, 'utility-phasing', dpi=150)
    print('wrote %s\n      %s' % (svg, png))
    print('  lots            : %d (Phase 1 %d, Phase 2 %d); System A %d, System B %d (%s … %s)'
          % (N_LOTS, len(P1), len(P2), N_SYS_A, N_SYS_B, SYS_B_LOTS[0], SYS_B_LOTS[-1]))
    print('  water           : %.0f ft in the lane + %.0f ft in the R/W = %.0f ft dead end; '
          '%d hydrants, max spacing %.0f ft, average %.0f ft, max reach %.0f ft'
          % (MAIN_LEN_LANE, MAIN_LEN_RW, MAIN_LEN, len(HYD), HYD_MAX_SP, HYD_AVG_SP, HYD_MAX_REACH))
    for m in MH_A + MH_B:
        print('  %-6s (%7.1f,%8.1f) rim %s inv %8.2f depth %s run %s slope %s'
              % (m['tag'], m['pt'][0], m['pt'][1],
                 ('%7.1f' % m['rim']) if m['rim'] else '  VERIFY', m['inv'],
                 ('%5.1f' % m['depth']) if m['depth'] is not None else '    —',
                 ('%6.1f' % m['len']) if m['len'] else '     —',
                 ('%6.3f%%' % (100 * m['slope'])) if m['slope'] else '      —'))
    print('  controlling     : %.1f ft at %.3f %% (sag -> POC-1); off site %.1f ft at %.3f %%'
          % (CTRL_LEN, 100 * CTRL_S, OFFSITE_LEN, 100 * B_S_OFF))
    print('  disturbed       : on site %s SF (%.3f ac), off site %s SF (%.3f ac)'
          % (format(round(ON_SF), ','), ON_SF / 43560.0, format(round(OFF_SF), ','), OFF_SF / 43560.0))
