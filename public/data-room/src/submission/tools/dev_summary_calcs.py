#!/usr/bin/env python3
"""Derived numbers for docs/02-development-summary.md.

Rewritten 2026-09-03 against the three audits in `audit-2026-09-03/`.

Inputs
  data/layout.json  — RAW geometry (boundary_ring, lots, lane, hammerheads, greens, ponds,
                      amenity, open_space_tracts). Every quantity below is recomputed here from
                      that geometry and cross-checked against the file's own `metrics` block
                      (differences greater than 2 % are printed). The generator was corrected on
                      2026-09-03 against `audit-2026-09-03/site-geometry.md` SG-01/02/06/14, so
                      the two now agree; where the generator measures something this script can
                      only approximate — the drawn curb-return fillets, and the rastered disturbed
                      area, which has to subtract the stream buffers as a union — the drawn value
                      is read from `layout.json` and the fact is noted at the point of use.
  data/plans.json   — house envelopes and areas as the architectural sheets draw them
                      (read at run time so a re-proportioned plan flows straight through).
  constants below   — each carries its governing source inline.

Output: data/dev-summary-derived.json  +  a printed table.
Run:    python3 tools/dev_summary_calcs.py
"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = json.load(open(os.path.join(ROOT, "data", "layout.json")))
P = json.load(open(os.path.join(ROOT, "data", "plans.json")))["plans"]
M = L["metrics"]

out, notes = {}, []


# ----------------------------------------------------------------- geometry helpers
def shoelace(poly):
    return abs(0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1]
                         - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly))))


def rect_area(r):
    xs = [p[0] for p in r]; ys = [p[1] for p in r]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def cross_check(key, computed, stated, tol=0.02):
    """Record where a recomputed value differs from layout.json's own metrics block."""
    if stated in (None, 0):
        return
    if abs(computed - stated) > tol * abs(stated):
        notes.append(f"{key}: recomputed {computed:,.0f} vs layout.json metrics {stated:,.0f}")


# ----------------------------------------------------------------- 1. site
AC_DEEDED = 9.44                                   # 0.99 + 2.00 + 2.00 + 4.45, Gwinnett 2026 digest
SF_DEEDED = round(AC_DEEDED * 43560)
BOUNDARY_SF = shoelace(L["boundary_ring"])
out["acreage_deeded_ac"] = AC_DEEDED
out["deeded_sf"] = SF_DEEDED
out["boundary_sf_gis"] = round(BOUNDARY_SF, 1)
out["acreage_gis_ac"] = round(BOUNDARY_SF / 43560, 3)

# ----------------------------------------------------------------- 2. lots
lots = L["lots"]
n = len(lots)
nA = sum(1 for l in lots if l["plan"] == "A")
nB = sum(1 for l in lots if l["plan"] == "B")
out["lots"] = n
out["lots_sw"] = sum(1 for l in lots if l["side"] == "SW")
out["lots_ne"] = sum(1 for l in lots if l["side"] == "NE")
out["plan_A"] = nA
out["plan_B"] = nB
out["lots_phase1"] = sum(1 for l in lots if l["phase"] == 1)
out["lots_phase2"] = sum(1 for l in lots if l["phase"] == 2)
out["lot_area_min_sf"] = round(min(shoelace(l["polygon"]) for l in lots), 1)
out["lot_area_avg_sf"] = round(sum(shoelace(l["polygon"]) for l in lots) / n, 1)
out["lot_area_max_sf"] = round(max(shoelace(l["polygon"]) for l in lots), 1)
out["lot_width_min_ft"] = round(min(l["width_ft"] for l in lots), 2)
out["lot_depth_min_ft"] = round(min(l["depth_ft"] for l in lots), 2)
out["lot_area_total_sf"] = round(sum(shoelace(l["polygon"]) for l in lots))
out["density_du_ac_deeded"] = round(n / AC_DEEDED, 2)
out["density_du_ac_gis"] = round(n / (BOUNDARY_SF / 43560), 2)
out["buffer_easement_on_lots_sf"] = round(sum(shoelace(l["buffer_easement"]) for l in lots))

# ----------------------------------------------------------------- 3. houses (data/plans.json)
for tag in ("A", "B"):
    p = P[tag]; a = p["areas"]; s = p["lot_siting"]; d = p["overall_body_dims"]
    out[f"plan{tag}_name"] = p["name"]
    out[f"plan{tag}_body_label"] = d["label"]
    out[f"plan{tag}_body_w_ft"] = d["width_ft"]
    out[f"plan{tag}_body_d_ft"] = d["depth_ft"]
    out[f"plan{tag}_conditioned_sf"] = a["conditioned_sf"]
    out[f"plan{tag}_target_conditioned_sf"] = p["target_cond_sf"]
    out[f"plan{tag}_garage_sf"] = a["garage_sf"]
    out[f"plan{tag}_front_porch_sf"] = a["front_porch_sf"]
    out[f"plan{tag}_rear_porch_covered_sf"] = a["rear_porch_covered_sf"]
    out[f"plan{tag}_rear_patio_uncovered_sf"] = a["rear_patio_uncovered_sf"]
    out[f"plan{tag}_under_roof_sf"] = a["total_under_roof_sf"]
    out[f"plan{tag}_max_ridge_ft"] = p["roof"]["max_ridge_ft"]
    out[f"plan{tag}_side_yard_ft"] = s["side_yard_ft"]
    out[f"plan{tag}_garage_door_from_lot_line_ft"] = s["garage_door_from_lot_line_ft"]
    rear = s["patio_edge_from_rear_line_ft"] or s["rear_porch_edge_from_rear_line_ft"] or s["rear_wall_from_rear_line_ft"]
    out[f"plan{tag}_rear_structure_to_rear_line_ft"] = rear
    out[f"plan{tag}_rear_wall_from_rear_line_ft"] = s["rear_wall_from_rear_line_ft"]
    out[f"plan{tag}_coverage_under_roof_pct"] = round(100 * a["total_under_roof_sf"] / 5000.0, 1)
out["conditioned_sf_total"] = round(nA * P["A"]["areas"]["conditioned_sf"] + nB * P["B"]["areas"]["conditioned_sf"])
out["conditioned_sf_avg"] = round(out["conditioned_sf_total"] / n)

# ----------------------------------------------------------------- 4. lane, blocks, turnarounds
lane = L["lane"]
U_JOIN = lane["entrance"]["join_u"]
U_END = lane["pavement_end_u"]
ENTRY_LEN = lane["entry_drive"]["length_ft"]
CL = lane["centerline"]


def arc_to(u):
    """Arc length along the lane centreline from the join point to station u (interpolated)."""
    pts = [p for p in CL if U_JOIN <= p[0] <= u]
    d = plen(pts)
    nxt = next((p for p in CL if p[0] > u), None)
    if nxt and pts:
        last = pts[-1]
        span = nxt[0] - last[0]
        if span > 0:
            d += math.dist(last, nxt) * (u - last[0]) / span
    return d


LANE_ARC = arc_to(U_END)
out["entry_drive_length_ft"] = round(ENTRY_LEN, 1)
out["lane_arc_ft"] = round(LANE_ARC, 1)
out["travelled_way_ft"] = round(ENTRY_LEN + LANE_ARC, 1)          # Arcado R/W -> end of pavement
cross_check("travelled way", out["travelled_way_ft"], M.get("lane_length_ft"))
out["pavement_width_ft"] = lane["pavement_width_ft"]
out["lane_tract_sf"] = round(shoelace(lane["tract_polygon"]) + shoelace(lane["entry_drive"]["tract_polygon"]))
cross_check("lane tract area", out["lane_tract_sf"], M.get("lane_tract_sf"))
out["lane_tract_width_ft"] = lane["tract_width_ft"]
out["sidewalk_widen_both_from_u"] = lane["widen_both_sidewalks_from_u"]
out["sidewalk_sf"] = round(sum(shoelace(s["polygon"]) for s in lane["sidewalks"]))
HH = L["hammerheads"]
HH_LEG_SF = sum(shoelace(leg) for h in HH for leg in h["legs"])
# The two entrance curb returns are drawn fillets (R = 25 ft NE, R = 15 ft SW), so their area is
# read from the generator's own take-off rather than allowed for; 270 SF is the fallback.
CURB_RETURN_SF = next((c["area_sf"] for c in L["impervious_summary"]["components_sf"]
                       if "curb return" in c["item"].lower()), 270)
# The lane tract widens to 60 ft through the amenity block so that the guest and mail-kiosk bays
# lie wholly inside it (layout.json metrics.lane_tract_widened_through_amenity_block); the bays are
# therefore lane pavement, not amenity-tract paving.
BAY_SF = shoelace(am_bay := L["amenity"]["parking_bay"]) + shoelace(L["amenity"]["kiosk_bay"])
out["parking_bay_sf"] = round(BAY_SF)
out["pavement_sf"] = round(lane["pavement_width_ft"] * (U_END - U_JOIN)
                           + lane["entry_drive"]["width_ft"] * ENTRY_LEN + HH_LEG_SF
                           + BAY_SF + CURB_RETURN_SF)
cross_check("pavement area", out["pavement_sf"], M.get("pavement_sf"))


def station(u):
    """Travelled-way distance from the Arcado Rd R/W to lane station u."""
    return ENTRY_LEN + arc_to(u)


out["hammerheads_u"] = [h["u"] for h in HH]
out["hammerhead_stations_ft"] = [round(station(h["u"]), 1) for h in HH]
st = [0.0] + out["hammerhead_stations_ft"]
out["hammerhead_spacing_ft"] = [round(st[i + 1] - st[i], 1) for i in range(len(st) - 1)]
out["hammerhead_spacing_max_ft"] = max(out["hammerhead_spacing_ft"])
out["dead_end_ft"] = out["travelled_way_ft"]
# Block length read two ways (audit SG-06): a pocket green is an open-space tract, not a street.
out["blocks_between_intersections_ft"] = out["hammerhead_spacing_ft"]
green_u = sorted([g["polygons"][0][0][0] for g in L["greens"][:2]] + [g["polygons"][0][1][0] for g in L["greens"][:2]])
u_lot0 = min(l["polygon"][0][0] for l in lots)
u_lotN = max(max(p[0] for p in l["polygon"]) for l in lots)
brk = [u_lot0] + green_u + [u_lotN]
out["blocks_lot_frontage_runs_ft"] = [round(brk[i + 1] - brk[i]) for i in range(0, len(brk) - 1, 2)]
ent = lane["entrance"]
out["entrance_v_ft"] = ent["v_rw"]
out["entrance_separation_along_cl_ft"] = ent["separation_along_cl_ft"]
out["entrance_separation_chord_ft"] = ent["separation_chord_ft"]
out["entrance_drive_width_ft"] = ent["drive_width_ft"]
out["entrance_join_u_ft"] = ent["join_u"]
out["sw_curb_return_buffer_encroachment_ft"] = M.get("sw_curb_return_buffer_encroachment_ft")

# ----------------------------------------------------------------- 5. open space
tracts = L["open_space_tracts"]
out["open_space_tracts"] = tracts
out["open_space_sf"] = round(sum(t["area_sf"] for t in tracts))            # enumerated, not residual
out["open_space_ac"] = round(out["open_space_sf"] / 43560, 3)
out["open_space_pct_gis"] = round(100 * out["open_space_sf"] / BOUNDARY_SF, 2)
out["open_space_pct_deeded"] = round(100 * out["open_space_sf"] / SF_DEEDED, 2)
am = L["amenity"]
AMEN_WALKS = 600                                                          # amenity-walk allowance, tools/siteplan.py
AMEN_BUILT = (am["clubhouse_sf"] + sum(shoelace(c) for c in am["pickleball"])
              + shoelace(am["mail_kiosk"]) + AMEN_WALKS)                  # clubhouse roof, 2 court pads, kiosk, walks
out["amenity_built_paved_sf"] = round(AMEN_BUILT)
# The hammerhead turnaround legs are pavement lying inside the pocket / terminus greens, so they are
# built area inside open space too. The guest and kiosk bays are NOT: they sit in the lane tract.
out["open_space_built_paved_sf"] = round(AMEN_BUILT + HH_LEG_SF)
out["open_space_green_only_sf"] = round(out["open_space_sf"] - AMEN_BUILT - HH_LEG_SF)
out["open_space_green_only_pct_gis"] = round(100 * out["open_space_green_only_sf"] / BOUNDARY_SF, 2)
out["open_space_residual_sf"] = round(BOUNDARY_SF - out["lot_area_total_sf"] - out["lane_tract_sf"])
out["open_space_unallocated_slivers_sf"] = round(out["open_space_residual_sf"] - out["open_space_sf"])

# ----------------------------------------------------------------- 6. impervious cover
# Per-lot = total under roof (plans.json) + uncovered patio + the drawn driveway + a 60-SF entry walk.
WALK_SF = 60.0
per_lot, drive_tot = {}, 0.0
for tag in ("A", "B"):
    a = P[tag]["areas"]
    ex = [l for l in lots if l["plan"] == tag]
    drives = [rect_area(l["driveway_rect"]) for l in ex]
    per_lot[tag] = {
        "under_roof_sf": a["total_under_roof_sf"],
        "uncovered_patio_sf": a["rear_patio_uncovered_sf"],
        "driveway_sf_min": round(min(drives), 1), "driveway_sf_max": round(max(drives), 1),
        "walk_sf": WALK_SF,
        "avg_total_sf": round(a["total_under_roof_sf"] + a["rear_patio_uncovered_sf"] + sum(drives) / len(drives) + WALK_SF, 1),
    }
    drive_tot += sum(drives)
LOT_IMPERV = sum(P[l["plan"]]["areas"]["total_under_roof_sf"]
                 + P[l["plan"]]["areas"]["rear_patio_uncovered_sf"]
                 + rect_area(l["driveway_rect"]) + WALK_SF for l in lots)
out["impervious_per_lot"] = per_lot
# driveway/sidewalk double count: one 20 ft x 5 ft crossing per lot that has a walk on its side
cross_lots = sum(1 for l in lots if l["side"] == "NE" or min(p[0] for p in l["polygon"]) >= lane["widen_both_sidewalks_from_u"])
DOUBLE_COUNT = cross_lots * 100.0
AMEN_PAVE = AMEN_BUILT                                                    # walks already included
IMPERV = LOT_IMPERV + out["pavement_sf"] + out["sidewalk_sf"] + AMEN_PAVE - DOUBLE_COUNT
out["impervious_components_sf"] = {
    f"lots ({n} x roof + patio + driveway + walk)": round(LOT_IMPERV),
    "lane pavement + entry drive + hammerheads + guest/kiosk bays + curb returns": out["pavement_sf"],
    "sidewalks": out["sidewalk_sf"],
    "amenity block (clubhouse roof, court pads, mail kiosk, walks)": round(AMEN_PAVE),
    "less driveway/sidewalk overlap": -round(DOUBLE_COUNT),
}
out["impervious_sf"] = round(IMPERV)
out["impervious_ac"] = round(IMPERV / 43560, 2)
out["impervious_pct_gis"] = round(100 * IMPERV / BOUNDARY_SF, 1)
out["impervious_pct_deeded"] = round(100 * IMPERV / SF_DEEDED, 1)
cross_check("impervious", out["impervious_sf"], M.get("impervious_sf"))

# ----------------------------------------------------------------- 7. stormwater
# 2025 hydro basis (HYD-1, Parker Land Design 04-29-2025): detention = 10,000 cf per disturbed
# acre LESS the required runoff-reduction volume RRv;  WQv = 1.2*(0.05+0.009*I)/12 * A.
I = 100.0 * IMPERV / BOUNDARY_SF                                          # unrounded; do not round an intermediate
Rv = 0.05 + 0.009 * I
out["Rv"] = round(Rv, 4)
out["WQr_in"] = round(1.2 * Rv, 3)
out["WQv_cf"] = round(1.2 * Rv / 12.0 * BOUNDARY_SF)
out["RRv_cf"] = round(Rv * 1.0 / 12.0 * BOUNDARY_SF)                      # 1.0-in runoff-reduction basis (GSMM)
# Disturbed area. The generator rasters the site at 2 ft and subtracts the UNION of the 20-ft
# perimeter buffer bands, the creek-woods tract and the 50-ft undisturbed stream buffer, so nothing
# is counted twice; that is the figure of record. The closed-form band arithmetic below is kept as
# an independent cross-check (it cannot do the union, so it runs a few thousand SF high on preserved).
DA = L["stormwater"]["disturbed_area"]
out["preserved_sf"] = DA["preserved_sf"]
out["disturbed_sf"] = DA["disturbed_sf"]
out["disturbed_ac"] = DA["disturbed_ac"]
SW_LEN, NE_LEN, NW_LEN = 1757.01, 1721.68, 246.41                         # docs/05 §5 (GIS boundary courses)
BAND = (SW_LEN + NE_LEN + NW_LEN) * 20.0 - 2 * 20.0 * 20.0                # less the two rear corner overlaps
WOODS_NET = 16000.0                                                       # 20,000-SF tract less its 200 ft x 20 ft inside the band
out["disturbed_sf_closed_form_check"] = round(BOUNDARY_SF - BAND - WOODS_NET)
cross_check("disturbed area", out["disturbed_sf_closed_form_check"], out["disturbed_sf"])
# Screening basis: 10,000 cf of detention per disturbed acre. The RRv credit is carried at ZERO at
# concept stage, as the concept plan states; RRv is reported below as the credit that would reduce it.
out["detention_rate_cf_per_disturbed_ac"] = 10000
out["detention_required_cf"] = round(10000 * out["disturbed_ac"])
out["detention_required_less_rrv_cf"] = round(10000 * out["disturbed_ac"] - out["RRv_cf"])
ponds = L["ponds"]
out["ponds"] = [{"name": p["name"], "top_of_bank_ft": p["top_of_bank_ft"], "area_sf": p["area_sf"],
                 "est_storage_cf": p["est_storage_cf"], "tract_sf": round(shoelace(p["tract_polygon"]))} for p in ponds]
out["detention_provided_cf"] = sum(p["est_storage_cf"] for p in ponds)
out["detention_shortfall_cf"] = out["detention_required_cf"] - out["detention_provided_cf"]
out["detention_provided_pct_of_required"] = round(100 * out["detention_provided_cf"] / out["detention_required_cf"], 1)


def prismoidal(l_ft, w_ft, depth, slope=3.0):
    """Volume between top of bank and basin bottom, side slopes `slope`:1."""
    ins = slope * depth
    top = l_ft * w_ft
    mid = max(l_ft - ins, 0.0) * max(w_ft - ins, 0.0)
    bot = max(l_ft - 2 * ins, 0.0) * max(w_ft - 2 * ins, 0.0)
    return depth / 6.0 * (top + 4 * mid + bot)


# what the drawn tracts can hold at 6-ft depth with a 10-ft offset inside each tract
enl = []
for p in ponds:
    t = p["tract_polygon"]
    tl = max(q[0] for q in t) - min(q[0] for q in t) - 20.0
    tw = max(q[1] for q in t) - min(q[1] for q in t) - 20.0
    w = float(str(p["top_of_bank_ft"]).split("x")[0].strip())             # keep the drawn basin width
    w = min(w, tw)
    enl.append({"name": p["name"], "basin_ft": f"{w:.0f} x {tl:.0f}", "depth_ft": 6.0,
                "est_storage_cf": round(prismoidal(tl, w, 6.0))})
out["ponds_enlarged_6ft"] = enl
out["detention_provided_6ft_cf"] = sum(e["est_storage_cf"] for e in enl)
# 2025 filing comparison (HYD-1 basins)
b2025 = [(51451, 25770, 2570, 9240), (215455, 122543, 12094, 37366), (157642, 87075, 8629, 27561)]
out["hydro2025"] = {"area_sf": sum(b[0] for b in b2025), "impervious_sf": sum(b[1] for b in b2025),
                    "impervious_pct": round(100 * sum(b[1] for b in b2025) / sum(b[0] for b in b2025), 1),
                    "WQv_cf": sum(b[2] for b in b2025), "detention_cf": sum(b[3] for b in b2025)}
out["impervious_reduction_vs_2025_pct"] = round(100 * (1 - IMPERV / out["hydro2025"]["impervious_sf"]), 1)

# ----------------------------------------------------------------- 8. parking
out["parking_required"] = 2 * n                                           # Table 8.1, SF detached
out["parking_on_lot"] = 4 * n
out["parking_guest"] = am["guest_spaces"]
out["parking_kiosk"] = am["kiosk_spaces"]
out["parking_total"] = out["parking_on_lot"] + out["parking_guest"] + out["parking_kiosk"]
out["guest_ratio_lots_per_space"] = round(n / (out["parking_guest"] + out["parking_kiosk"]), 1)

# ----------------------------------------------------------------- 9. traffic
# ITE 11th ed. LUC 251 is paywalled; audit-2026-09-03/external-facts.md §3.6 reconciles four
# secondary compilations into a rate BAND. Every rate in the band lands in Gwinnett DOT's 0-20 band.
R251 = {"am_lo": 0.20, "am_hi": 0.34, "pm_lo": 0.26, "pm_hi": 0.39, "daily_lo": 3.70, "daily_hi": 4.31,
        "am_facts": 0.30, "pm_facts": 0.30}
out["ite_251_rate_band"] = R251
out["trips_251_am"] = [round(R251["am_lo"] * n, 1), round(R251["am_hi"] * n, 1)]
out["trips_251_pm"] = [round(R251["pm_lo"] * n, 1), round(R251["pm_hi"] * n, 1)]
out["trips_251_daily"] = [round(R251["daily_lo"] * n), round(R251["daily_hi"] * n)]
out["trips_251_pm_facts"] = round(R251["pm_facts"] * n, 1)
out["trips_251_pm_at_47_hi"] = round(R251["pm_hi"] * 47, 1)
R210 = (9.43, 0.70, 0.94)                                                 # LUC 210 Single-Family Detached
out["trips_210_same_lots"] = {"daily": round(R210[0] * n), "am": round(R210[1] * n, 1), "pm": round(R210[2] * n, 1)}
r1_max = math.floor(AC_DEEDED * 4)                                        # Table 4.1 R-1: 4 du/ac
out["r1_theoretical_units"] = r1_max
out["trips_210_r1_max"] = {"daily": round(R210[0] * r1_max), "am": round(R210[1] * r1_max, 1), "pm": round(R210[2] * r1_max, 1)}
R220 = (6.74, 0.40, 0.51)                                                 # LUC 220 Multifamily Low-Rise (Memo A)
R822 = (54.45, None, 6.59)                                                # LUC 822 Strip Retail Plaza, per 1,000 SF
out["trips_2025_MU"] = {"daily": round(104 * R220[0] + 24.4 * R822[0]),
                        "pm": round(104 * R220[2] + 24.4 * R822[2], 1)}
out["pm_share_of_2025_MU_pct"] = round(100 * out["trips_251_pm_facts"] / out["trips_2025_MU"]["pm"], 1)

# ----------------------------------------------------------------- 10. sanitary sewer
# Gwinnett DWR Wastewater Flow Estimation Guidelines (Rev. 10/2022): 250 gpd per single-family
# unit; 175 gpd per 1,000 SF of clubhouse; peaking factor 4.0.
GPD_DU, GPD_KSF, PF = 250, 175, 4.0
club = am["clubhouse_sf"] * GPD_KSF / 1000.0
out["sewer_unit_flow_gpd"] = GPD_DU
out["adf_total_gpd"] = round(n * GPD_DU + club)
out["adf_gpm"] = round(out["adf_total_gpd"] / 1440.0, 2)
out["peak_gpd"] = round(out["adf_total_gpd"] * PF)
out["peak_gpm"] = round(out["adf_total_gpd"] * PF / 1440.0, 1)
out["adf_phase1_gpd"] = round(out["lots_phase1"] * GPD_DU + club)
out["adf_phase2_gpd"] = out["lots_phase2"] * GPD_DU
out["peak_phase2_gpm"] = round(out["adf_phase2_gpd"] * PF / 1440.0, 1)
sew = L["sewer"]
out["phase1_gravity_len_ft"] = round(plen(sew["proposed_phase1_gravity"]))
out["phase2_ext_total_len_ft"] = round(plen(sew["phase2_alternative_extension"]))
out["phase2_ext_offsite_ft"] = sew["extension_offsite_ft"]
out["rear_lane_low_point"] = M.get("rear_lane_low_point")
prof = dict(L["lane"]["ground_profile"])
out["lane_ridge_ft"] = max(prof.values())
out["lane_ridge_u"] = max(prof, key=prof.get)
MH_INV = 927.13
out["phase2_slope_pct"] = round(100 * ((out["rear_lane_low_point"]["ground_ft"] - 5.0) - 919.58)
                                / out["phase2_ext_total_len_ft"], 2)

# ----------------------------------------------------------------- 11. fiscal (market figures VERIFY)
PRICE_LO, PRICE_HI = 420_000, 460_000
out["price_lo"], out["price_hi"] = PRICE_LO, PRICE_HI
out["taxbase_lo"] = n * PRICE_LO
out["taxbase_hi"] = n * PRICE_HI
out["existing_fmv_2026"] = 285000 + 87200 + 6800 + 888600
ASSESS, CITY_MILLS, CS_MILLS, SCHOOL_MILLS = 0.40, 5.43, 31.6, 20.15
for tag, v in (("lo", out["taxbase_lo"]), ("hi", out["taxbase_hi"])):
    out[f"city_tax_{tag}"] = round(v * ASSESS * CITY_MILLS / 1000)
    out[f"county_school_tax_{tag}"] = round(v * ASSESS * CS_MILLS / 1000)
    out[f"school_portion_{tag}"] = round(v * ASSESS * SCHOOL_MILLS / 1000)
out["city_tax_existing"] = round(out["existing_fmv_2026"] * ASSESS * CITY_MILLS / 1000)
out["city_tax_lo_all_senior_exempt"] = round((out["taxbase_lo"] * ASSESS - n * 60000) * CITY_MILLS / 1000)
out["taxbase_multiple_lo"] = round(out["taxbase_lo"] / out["existing_fmv_2026"], 1)
out["taxbase_multiple_hi"] = round(out["taxbase_hi"] / out["existing_fmv_2026"], 1)

# ----------------------------------------------------------------- 12. HOPA
out["hopa_units_needing_55plus"] = math.ceil(0.80 * n)                    # 24 CFR §100.305(g): fraction rounds in
out["hopa_units_without_55plus_cap"] = n - out["hopa_units_needing_55plus"]

out["_cross_check_notes"] = notes
json.dump(out, open(os.path.join(ROOT, "data", "dev-summary-derived.json"), "w"), indent=1)

for k, v in out.items():
    if k not in ("open_space_tracts", "impervious_per_lot", "ponds", "_cross_check_notes"):
        print(f"{k}: {v}")
print("\nopen_space_tracts:", json.dumps(out["open_space_tracts"]))
print("impervious_per_lot:", json.dumps(out["impervious_per_lot"]))
print("ponds:", json.dumps(out["ponds"]))
print("\nRecomputed vs layout.json metrics — differences > 2 %:")
for nte in notes:
    print("  !", nte)
print("wrote data/dev-summary-derived.json")
