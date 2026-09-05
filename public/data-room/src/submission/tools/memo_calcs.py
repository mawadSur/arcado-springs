#!/usr/bin/env python3
"""Technical-memoranda calculations for docs/08-technical-memoranda.md.

Reads data/layout.json (which governs) + data/topo-samples.json; prints every derived number with its
inputs, and writes verify/memo-calcs.json for tools/verify_memo08.py.

    python3 tools/memo_calcs.py        (run from anywhere; paths are absolute off this file)

REBUILT 2026-09-03 against the corrected site plan: the lot count fell from 43 to 41 (one lot inside a
stream buffer once all three digitised reaches were screened, one lost to the enlarged stormwater basins),
the basins were enlarged, and the sewer keys in layout.json were renamed. Nothing here is a design.
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
L = json.load(open(os.path.join(ROOT, 'data', 'layout.json')))
TOPO = json.load(open(os.path.join(ROOT, 'data', 'topo-samples.json')))['samples']
M = L['metrics']; N = M['lots']
out = {}


def p(k, v, note=''):
    out[k] = v
    print(f"{k:44s} {v!s:>16}  {note}")


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def pathlen(pts):
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def ground(u, v, k=4):
    """inverse-distance ground elevation from the 3DEP sample grid (approximate)."""
    d = sorted((math.hypot(s['u'] - u, s['v'] - v), s['z_ft']) for s in TOPO)[:k]
    if d[0][0] < 1e-6:
        return d[0][1]
    w = sum(1 / dd ** 2 for dd, _ in d)
    return sum(z / dd ** 2 for dd, z in d) / w


print("=== PROGRAM")
p('units', N, 'layout.json metrics.lots')
p('lots phase 1 / phase 2', f"{M['lots_phase1']} / {M['lots_phase2']}", f"phase line u = {M['phase_line_u_ft']:.0f} ft")
p('density du/ac (9.44 deeded)', M['density_du_ac_deeded'])
p('open space sf / pct', f"{M['open_space_sf']:,} / {M['open_space_pct_gis']}%")
p('impervious sf / pct', f"{M['impervious_sf']:,} / {M['impervious_pct_gis']}%")

print("\n=== HOPA (24 CFR §100.305(a) with the fractional-unit rule of §100.305(g))")
need = math.ceil(0.80 * N)
p('0.80 x units', round(0.80 * N, 2), f"0.80 x {N}")
p('units needing a 55+ resident', need, f"the fraction counts INTO the 80% -> {need} of {N} = {100*need/N:.1f}%")
p('units with no age requirement', N - need, f"{N} - {need}")

print("\n=== A. TRAFFIC (ITE Trip Generation 11th ed.)")
# LUC 251 rate is UNRESOLVED (no primary 11th-ed. source reachable); a range is carried - see memo A.3.
r_lo = {'daily': 3.70, 'am': 0.20, 'pm': 0.30}      # Falls Church VA study (states ITE 9th ed.)
r_mid = {'daily': 4.31, 'am': 0.24, 'pm': 0.30}     # Palm Beach County sheet (matches the FACTS PM 0.30)
r_hi = {'am': 0.34, 'pm': 0.39}                     # Corpus Christi "common rates 11th ed." sheet
r210 = {'daily': 9.43, 'am': 0.70, 'pm': 0.94}      # LUC 210 Single-Family Detached
r220 = {'daily': 6.74, 'am': 0.40, 'pm': 0.51}      # LUC 220 Multifamily Low-Rise
r822_pm, r822_daily = 6.59, 54.45                   # LUC 822 Strip Retail Plaza (<40 ksf), per 1,000 sf
CAP = 47
p('251 daily lo', round(N * r_lo['daily']), f"{N} x 3.70")
p('251 daily mid', round(N * r_mid['daily']), f"{N} x 4.31")
p('251 AM lo', round(N * r_lo['am'], 1), f"{N} x 0.20")
p('251 AM mid', round(N * r_mid['am'], 1), f"{N} x 0.24")
p('251 AM hi', round(N * r_hi['am'], 1), f"{N} x 0.34")
p('251 PM lo/mid', round(N * r_mid['pm'], 1), f"{N} x 0.30 (the package headline figure)")
p('251 PM hi', round(N * r_hi['pm'], 1), f"{N} x 0.39")
p('251 daily @cap', round(CAP * r_mid['daily']), f"{CAP} x 4.31")
p('251 AM @cap hi', round(CAP * r_hi['am'], 1), f"{CAP} x 0.34")
p('251 PM @cap hi', round(CAP * r_hi['pm'], 1), f"{CAP} x 0.39 — the highest figure anywhere")
r1_lots = math.floor(9.44 * 4)
p('R-1 lots @4 du/ac', r1_lots, "floor(9.44 x 4), Table 4.1 R-1 max 4 du/ac")
p('210 daily', round(r1_lots * r210['daily'], 1)); p('210 AM', round(r1_lots * r210['am'], 1)); p('210 PM', round(r1_lots * r210['pm'], 1))
p('vs R-1 daily', f"-{100*(1-N*r_mid['daily']/(r1_lots*r210['daily'])):.0f}%", f"{N*r_mid['daily']:.0f} vs {r1_lots*r210['daily']:.0f}")
p('vs R-1 PM', f"-{100*(1-N*r_mid['pm']/(r1_lots*r210['pm'])):.0f}%", f"{N*r_mid['pm']:.1f} vs {r1_lots*r210['pm']:.1f}")
mu_pm = 104 * r220['pm'] + 24.4 * r822_pm
mu_daily = 104 * r220['daily'] + 24.4 * r822_daily
p('2025 MU PM raw', round(mu_pm, 1), "104 x 0.51 (LUC 220) + 24.4 ksf x 6.59 (LUC 822)")
p('2025 MU daily raw', round(mu_daily), "104 x 6.74 + 24.4 x 54.45")
p('vs 2025 MU PM', f"-{100*(1-N*r_mid['pm']/mu_pm):.0f}%", f"{N*r_mid['pm']:.1f} vs {mu_pm:.0f}")
p('AADT share (daily/14,800)', f"{N*r_mid['daily']/14800*100:.2f}%", "2017 count, INELIGIBLE — context only")
p('entrance to Arcadia Pl cl', f"{M['entrance_to_arcadia_cl_ft']} ft", f"chord {M['entrance_to_arcadia_cl_chord_ft']} ft; standard 244 ft")
p('frontage on Arcado Rd', f"{M['frontage_arcado_chord_ft']} ft chord", f"{M['frontage_arcado_along_rw_ft']} ft along the R/W; 1 driveway per 400 ft")

print("\n=== B. SANITARY SEWER")
gp = dict(L['lane']['ground_profile'])
MH_INV, MH, COVER, SMIN, N_MAN = 927.13, (271.7, -224.0), 5.0, 0.004, 0.013
PHASE_U = M['phase_line_u_ft']
front = L['sewer']['proposed_phase1_gravity']
Lf = pathlen(front)
p('front reach length ft', round(Lf), f"lane u {PHASE_U:.0f} -> lane u 272 -> EX MH (271.7,-224)")
cross = dist((272.0, -117.65), MH)
p('cross leg to the EX MH ft', round(cross, 1), "lane u 272 across the amenity tract")
u_top = min(gp, key=lambda u: abs(u - PHASE_U))
inv_top = gp[u_top] - COVER
p('invert at the phase line', round(inv_top, 2), f"ground {gp[u_top]} at u {u_top} less {COVER:.0f} ft of cover")
sag_u = min((u for u in gp if 272 <= u <= PHASE_U), key=lambda u: gp[u]); sag_z = gp[sag_u]
inv_sag = sag_z - COVER
p('front-reach lane sag', f"u {sag_u} / {sag_z}", "lowest lane ground between u 272 and the phase line")
p('invert at the sag (5-ft cover)', round(inv_sag, 2))
p('slope phase line -> sag', f"{(inv_top-inv_sag)/(u_top-sag_u)*100:.2f} %", f"({inv_top:.1f}-{inv_sag:.1f})/{u_top-sag_u:.0f}")
L_sag = (sag_u - 272) + cross
p('length sag -> MH ft', round(L_sag))
s_avail = (inv_sag - MH_INV) / L_sag
p('available slope sag->MH', f"{s_avail*100:.2f} %", f"({inv_sag:.2f}-{MH_INV})/{L_sag:.0f}; min 0.40% for 8-in")
hump_u = max((u for u in gp if 272 <= u <= sag_u), key=lambda u: gp[u]); hump_z = gp[hump_u]
inv_hump = inv_sag - SMIN * (sag_u - hump_u)
p('lane hump between sag and MH', f"u {hump_u} / {hump_z}")
p('pipe depth under the hump @0.40%', round(hump_z - inv_hump, 1), "ft to invert (deep-cut item)")
p('SW-edge alternative ground', f"{ground(250,-215):.1f} at (250,-215)", "shallower corridor for the front trunk")
Q_full = 1.49 / N_MAN * (math.pi * (8 / 12) ** 2 / 4) * ((8 / 12) / 4) ** (2 / 3) * SMIN ** 0.5
p('8-in full-flow Q @0.40%', f"{Q_full*448.83:.0f} gpm", f"Manning n=0.013 -> {Q_full:.3f} cfs")
low = M['rear_lane_low_point']
ridge_u = max((u for u in gp if 1000 <= u <= 1300), key=lambda u: gp[u]); ridge_z = gp[ridge_u]
inv_low = low['ground_ft'] - COVER
L_rear = (low['u'] - 272) + cross
p('rear low point', f"u {low['u']} / {low['ground_ft']}")
p('ridge on the lane', f"u {ridge_u} / {ridge_z}")
p('rear invert (5-ft cover)', round(inv_low, 2), f"already BELOW the {MH_INV} MH invert")
p('rear->MH length ft', round(L_rear))
arrive = inv_low - SMIN * L_rear
p('invert reached at the MH @0.40%', round(arrive, 2), f"vs {MH_INV} -> deficit {MH_INV-arrive:.1f} ft")
p('cut under the ridge if forced', round(ridge_z - (inv_low - SMIN * (low['u'] - ridge_u)), 1), "ft (not buildable)")
ext = L['sewer']['phase2_alternative_extension']; Lext = pathlen(ext)
p('extension total length ft', round(Lext), "rear low -> lane u 1,300 -> SW line -> Legends MH")
p('extension off-site ft', L['sewer']['extension_offsite_ft'])
s_ext = (inv_low - 919.58) / Lext
p('extension slope', f"{s_ext*100:.2f} %", f"({inv_low:.2f}-919.58)/{Lext:.0f}")
d1 = pathlen(ext[:2])
p('depth where it crosses the lane', round(ground(*ext[1]) - (inv_low - s_ext * d1), 1),
  f"ft at u 1,300 (ground {ground(*ext[1]):.1f}) — the deep point on the drawn route")
d2 = pathlen(ext[:3])
p('depth at the SW property line', round(ground(*ext[2]) - (inv_low - s_ext * d2), 1),
  f"ft at (1300,-235) (ground {ground(*ext[2]):.1f})")
p('SW low-pocket ground', f"{ground(1400,-210):.1f} at (1400,-210)", "the shallower alternative alignment")
PPU, GPCD, PF, UNIT, CLUB = 2.2, 70, 4.0, 250, 2400 * 175 / 1000
aadf_g = N * UNIT + CLUB
p('AADF (DWR table)', f"{aadf_g:.0f} gpd", f"{N} x {UNIT} + 2,400 sf clubhouse x 175/ksf ({CLUB:.0f} gpd)")
p('AADF gpm', f"{aadf_g/1440:.2f} gpm")
p('peak (x4.0) DWR', f"{aadf_g*PF:.0f} gpd = {aadf_g*PF/1440:.1f} gpm")
ph1, ph2 = M['lots_phase1'], M['lots_phase2']
p('Phase 1 AADF DWR', f"{ph1*UNIT+CLUB:.0f} gpd", f"{ph1} lots + clubhouse; {(ph1*UNIT+CLUB)/1440:.1f} gpm")
p('Phase 1 peak', f"{(ph1*UNIT+CLUB)*PF:.0f} gpd = {(ph1*UNIT+CLUB)*PF/1440:.1f} gpm")
p('Phase 2 AADF DWR', f"{ph2*UNIT:.0f} gpd", f"{ph2} lots; {ph2*UNIT/1440:.2f} gpm")
p('Phase 2 peak', f"{ph2*UNIT*PF:.0f} gpd = {ph2*UNIT*PF/1440:.1f} gpm")
aadf = N * PPU * GPCD
p('AADF (population cross-check)', f"{aadf:.0f} gpd", f"{N} x 2.2 x 70")
p('peak (x4.0) population', f"{aadf*PF:.0f} gpd = {aadf*PF/1440:.1f} gpm")
COST = [('8-in PVC gravity sewer', Lext, 150, 225), ]
p('extension pipe cost', f"${Lext*150:,.0f}-${Lext*225:,.0f}", f"{Lext:.0f} LF x $150-$225/LF")
lo = Lext * 150 + 21000 + 30000 + 10000 + 15000 + 20000
hi = Lext * 225 + 30000 + 30000 + 20000 + 50000 + 35000
p('extension order-of-magnitude', f"${lo:,.0f}-${hi:,.0f}", "pipe + MHs + rock + crossing + easement + design")
p('per Phase-2 lot', f"${lo/ph2:,.0f}-${hi/ph2:,.0f}", f"over {ph2} Phase-2 lots")

print("\n=== C. WATER")
avg = N * UNIT
p('avg day', f"{avg:.0f} gpd", f"{N} x 250 gpd")
p('max day (x2.0)', f"{avg*2:.0f} gpd")
p('peak hour (x4.0)', f"{avg*4/1440:.1f} gpm")
p('fire flow unsprinklered', "1,000 gpm / 1 h", "IFC 2024 (GA) App. B Table B105.1(1), <=3,600 sf")
p('fire flow w/ NFPA 13D', "500 gpm / 1 h", "B105.1: 50% reduction, not below 500 gpm")
main_len = M['lane_length_ft']
p('main length ft', round(main_len), "single dead-end run in the lane tract")
p('hydrants @~400 ft', math.ceil(main_len / 400) + 1, "DWR Standards (2016) 2.2.15(b): 350-450 ft; one near the end of the main")
p('main volume 8-in', f"{math.pi*(8/12)**2/4*main_len*7.48:.0f} gal", f"over {main_len:.0f} ft — turnover on a dead end")

print("\n=== D. STORMWATER  (layout.json governs)")
A_sf = M['boundary_sf']
I = 100.0 * M['impervious_sf'] / A_sf
Rv = 0.05 + 0.009 * I
WQr = 1.2 * Rv
D = M['disturbed_area']
p('site area', f"{A_sf:,} sf = {A_sf/43560:.2f} ac")
p('impervious', f"{M['impervious_sf']:,} sf = {M['impervious_sf']/43560:.2f} ac = {I:.2f}%")
p('Rv', round(Rv, 4), f"0.05 + 0.009 x {I:.2f}")
p('WQr (in)', round(WQr, 4), "1.2 x Rv")
p('WQv', f"{WQr/12*A_sf:,.0f} cf", f"WQr/12 x A; layout.json carries {M['wqv_cf']:,} cf")
p('RRv (1.0-in basis)', f"{Rv*1.0/12*A_sf:,.0f} cf", "Rv x 1.0 in /12 x A — NOT claimed on the plan (RRv = 0)")
p('disturbed area', f"{D['disturbed_sf']:,} sf = {D['disturbed_ac']:.3f} ac",
  f"raster {D['site_raster_sf']:,} less buffer bands {D['buffer_bands_sf']:,} less creek woods {D['creek_woods_net_sf']:,}")
p('detention required', f"{M['detention_required_cf']:,} cf", f"10,000 x {D['disturbed_ac']:.3f} ac, RRv = 0")
p('detention provided', f"{M['detention_provided_cf']:,} cf", str(M['ponds_cf']))
p('provided / required', f"{100*M['detention_provided_cf']/M['detention_required_cf']:.1f} %",
  f"margin {M['detention_provided_cf']-M['detention_required_cf']:,} cf")
p('detention net of a 1.0-in RRv', f"{M['detention_required_cf']-Rv/12*A_sf:,.0f} cf", "if the PE earns the full credit")
for P in L['ponds']:
    p(P['name'], f"{P['est_storage_cf']:,} cf", f"top of bank {P['top_of_bank_ft']} ft, 6 ft deep, 3:1")


def pris(w, l, h=6.0, s=3.0):
    return h / 6 * (w * l + 4 * (w - s * h) * (l - s * h) + (w - 2 * s * h) * (l - 2 * s * h))


p('prismoidal check 52 x 180 x 6', f"{pris(52,180):,.0f} cf", "h/6 (A_top + 4 A_mid + A_bot), 3:1 slopes")
p('prismoidal check 64 x 180 x 6', f"{pris(64,180):,.0f} cf", "the drawn basins are trapezoidal, hence slightly less")
p('impervious vs 2025 MU', f"{I:.1f}% vs 50-57%", "2025 hydro sheet: 55/57/50% per basin")

print("\n=== E. FIRE")
p('dead-end length', f"{M['longest_dead_end_ft']:.0f} ft", "> 750 ft -> IFC 2024 (GA) App. D103.4 special approval")
p('units on a single access', N, "GA D107.1 trigger is 120 -> not engaged")
p('hammerhead spacing', M['hammerhead_spacing_ft'], f"max {M['hammerhead_spacing_max_ft']:.1f} ft")
p('lane pavement width', f"{L['lane']['pavement_width_ft']} ft", "IFC 503.2.1 min 20 ft; Table D103.4 pairs 26 ft with long dead ends")
p('lane tract width', f"{M['lane_tract_width_ft_min']}-{M['lane_tract_width_ft_max']} ft",
  f"{M['lane_tract_width_ft_at_amenity_block']:.0f} ft through the amenity block")
far = max(L['lots'], key=lambda x: sum(q[0] for q in x['driveway_rect']) / 4)
u_far = sum(q[0] for q in far['driveway_rect']) / 4
p('farthest driveway, travelled way', f"{M['entry_drive_length_ft'] + (u_far - M['entry_join_u_ft']):.0f} ft",
  f"entry drive {M['entry_drive_length_ft']:.0f} ft + (u {u_far:.0f} - join u {M['entry_join_u_ft']:.1f})")
p('steepest existing lane grade', f"{M['max_existing_lane_grade_pct']} %", f"at u = {M['max_existing_lane_grade_at_u_ft']:.0f} ft (existing ground)")
p('sprinkler offer', f"${3000*N:,}", f"{N} homes x ~$3,000 (NFPA 13D)")
p('parking', f"{M['parking_provided_on_lot']} on lot + {M['guest_spaces']} guest/kiosk", f"required {M['parking_required']} (2/DU x {N})")

json.dump(out, open(os.path.join(ROOT, 'verify', 'memo-calcs.json'), 'w'), indent=1, default=str)
print("\nwrote verify/memo-calcs.json")
