#!/usr/bin/env python3
"""Annual HOA operating and reserve budget for The Cottages at Arcado Springs.

Deterministic generator for the budget tables in `docs/13-hoa-hopa-and-covenant-outline.md`.
Every quantity is derived from `data/layout.json` and `data/plans.json`; every unit price is a
named planning allowance carried in UNIT_COSTS below with its benchmark source.  Nothing is
hand-copied out of the JSON.

Run:  cd status/cottage-submission-2026-08-28 && python3 tools/hoa_budget.py
Outputs:
  data/hoa-budget-derived.json   machine-readable quantities, lines and totals
  verify/hoa-budget-output.md    the markdown tables reproduced verbatim in docs/13
Exit code 1 if a self-check fails or (when docs/13 exists) if its headline numbers drift.
"""

import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = json.load(open(os.path.join(ROOT, "data", "layout.json")))
P = json.load(open(os.path.join(ROOT, "data", "plans.json")))["plans"]
M = L["metrics"]

# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------


def shoelace(poly):
    a = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def centerline_length(pts, u_max=None):
    """Plan length of the lane centreline, optionally truncated at u <= u_max."""
    total = 0.0
    for (u1, v1), (u2, v2) in zip(pts, pts[1:]):
        if u_max is not None and u1 >= u_max:
            break
        seg = math.hypot(u2 - u1, v2 - v1)
        if u_max is not None and u2 > u_max:
            frac = (u_max - u1) / (u2 - u1) if u2 != u1 else 0.0
            total += seg * max(0.0, min(1.0, frac))
            break
        total += seg
    return total


# ---------------------------------------------------------------------------
# quantities
# ---------------------------------------------------------------------------

lane = L["lane"]
Q = {}

Q["lots_total"] = M["lots"]
Q["lots_phase1"] = M["lots_phase1"]
Q["lots_phase2"] = M["lots_phase2"]
Q["plan_A_lots"] = sum(1 for x in L["lots"] if x["plan"] == "A")
Q["plan_B_lots"] = sum(1 for x in L["lots"] if x["plan"] == "B")

# --- lane and walks ---------------------------------------------------------
Q["lane_cl_ft"] = round(centerline_length(lane["centerline"]), 1)
Q["entry_drive_ft"] = lane["entry_drive"]["length_ft"]
Q["lane_length_ft"] = M["lane_length_ft"]          # entrance to terminus, published
Q["pavement_width_ft"] = lane["pavement_width_ft"]

pave_lane = shoelace(lane["pavement_polygon"])
pave_entry = shoelace(lane["entry_drive"]["pavement_polygon"])
pave_hh = sum(shoelace(leg) for h in L["hammerheads"] for leg in h["legs"])
# metrics.pavement_sf also counts the 90-deg guest and mail-kiosk bays and the two entrance curb
# returns; the three polygons above do not, so add them or the cross-check fails for the wrong reason.
pave_bays = shoelace(L["amenity"]["parking_bay"]) + shoelace(L["amenity"]["kiosk_bay"])
pave_returns = M["impervious_components_sf"].get("Entrance curb returns", 0)
Q["pavement_lane_sf"] = round(pave_lane)
Q["pavement_entry_sf"] = round(pave_entry)
Q["pavement_hammerhead_sf"] = round(pave_hh)
Q["pavement_bay_sf"] = round(pave_bays)
Q["pavement_curb_return_sf"] = round(pave_returns)
Q["pavement_sf_computed"] = round(pave_lane + pave_entry + pave_hh + pave_bays + pave_returns)
Q["pavement_sf_published"] = M["pavement_sf"]

# lane["sidewalks"] already carries the entry-drive walk as its own "NE (entry drive)" polygon,
# so entry_drive["sidewalk_polygon"] must not be added again.
walk_lane = sum(shoelace(s["polygon"]) for s in lane["sidewalks"])
Q["sidewalk_sf_computed"] = round(walk_lane)
Q["sidewalk_sf_published"] = M["sidewalk_sf"]

Q["lane_tract_sf"] = M["lane_tract_sf"]
Q["lane_verge_sf"] = round(M["lane_tract_sf"] - M["pavement_sf"] - M["sidewalk_sf"])

Q["hammerheads"] = len(L["hammerheads"])

# --- open space -------------------------------------------------------------
tracts = {t["name"]: t["area_sf"] for t in L["open_space_tracts"]}
Q["open_space_tracts"] = tracts
Q["greens_sf"] = sum(g["area_sf"] for g in L["greens"])
Q["pond_tract_sf"] = sum(v for k, v in tracts.items() if k.startswith("Pond"))
Q["creek_woods_sf"] = sum(v for k, v in tracts.items() if k.startswith("Creek woods"))
Q["amenity_tract_sf"] = M["amenity_tract_sf"]
Q["ponds"] = len(L["ponds"])
Q["pond_water_area_sf"] = sum(p["area_sf"] for p in L["ponds"])
Q["pond_storage_cf"] = sum(p["est_storage_cf"] for p in L["ponds"])
Q["buffer_easement_on_lots_sf"] = M["buffer_easement_on_lots_sf"]
Q["open_space_sf"] = M["open_space_sf"]

# hard surfaces inside the front amenity tract (everything else is maintained landscape)
am = L["amenity"]
amenity_hard = (
    shoelace(am["clubhouse"])
    + sum(shoelace(p) for p in am["pickleball"])
    + shoelace(am["parking_bay"])
    + shoelace(am["kiosk_bay"])
    + shoelace(am["mail_kiosk"])
    + shoelace(am["entry_sign"])
)
Q["amenity_hard_sf"] = round(amenity_hard)
Q["amenity_soft_sf"] = round(M["amenity_tract_sf"] - amenity_hard)
Q["clubhouse_sf"] = am["clubhouse_sf"]
Q["guest_spaces"] = am["guest_spaces"]
Q["kiosk_spaces"] = am["kiosk_spaces"]
Q["pickleball_courts"] = len(am["courts"])
Q["pickleball_pad_perimeter_lf"] = round(
    sum(
        2 * (max(p[0] for p in pad) - min(p[0] for p in pad))
        + 2 * (max(p[1] for p in pad) - min(p[1] for p in pad))
        for pad in am["pickleball"]
    )
)

# --- per-lot maintained yard ------------------------------------------------
# plans.json lot_siting carries the authoritative per-lot impervious estimate; the rear 20 ft
# of every lot is the undisturbed buffer easement (not mown).
LOT_SF = M["lot_area_avg_sf"]
BUFFER_PER_LOT_SF = M["buffer_easement_on_lots_sf"] / M["lots"]
yard = {}
for k in ("A", "B"):
    ls = P[k]["lot_siting"]
    imperv = LOT_SF * ls["impervious_pct_est"] / 100.0
    yard[k] = LOT_SF - imperv - BUFFER_PER_LOT_SF
    Q[f"plan_{k}_lot_impervious_sf"] = round(imperv)
    Q[f"plan_{k}_yard_sf"] = round(yard[k])
Q["yard_total_sf"] = round(Q["plan_A_lots"] * yard["A"] + Q["plan_B_lots"] * yard["B"])
Q["yard_avg_sf"] = round(Q["yard_total_sf"] / M["lots"])

# --- trees and lights (design rules stated with the number) -----------------
STREET_TREE_SPACING_FT = 40.0     # docs/12 §32 93 00; audit M9 "lane street trees at 40 ft o.c."
LIGHT_SPACING_FT = 150.0          # assumption — photometric plan at LDP (checklist §1.11)
ARCADO_FRONTAGE_FT = 237.63       # docs/05 §5 chord
STRIP_TREE_PER_LF = 25.0          # checklist §6.j: 1 tree + 1 shrub per 25 lf of frontage
PARKING_TREE_PER_SPACES = 7.0     # checklist §6.k: 1 tree per 7 spaces

second_side_ft = max(0.0, Q["lane_length_ft"] - lane["widen_both_sidewalks_from_u"])
Q["street_trees"] = int(Q["lane_length_ft"] // STREET_TREE_SPACING_FT) + int(
    second_side_ft // STREET_TREE_SPACING_FT
)
Q["frontage_strip_trees"] = math.ceil(ARCADO_FRONTAGE_FT / STRIP_TREE_PER_LF)
Q["frontage_strip_shrubs"] = Q["frontage_strip_trees"]
Q["parking_lot_trees"] = math.ceil(
    (Q["guest_spaces"] + Q["kiosk_spaces"]) / PARKING_TREE_PER_SPACES
)
Q["trees_total"] = Q["street_trees"] + Q["frontage_strip_trees"] + Q["parking_lot_trees"]
Q["light_poles"] = int(math.ceil(Q["lane_length_ft"] / LIGHT_SPACING_FT)) + 4  # +4 amenity/entry

# --- maintained landscape acreage ------------------------------------------
Q["common_landscape_sf"] = (
    Q["lane_verge_sf"] + Q["amenity_soft_sf"] + Q["greens_sf"] + Q["pond_tract_sf"]
)
Q["common_landscape_ac"] = round(Q["common_landscape_sf"] / 43560.0, 2)
Q["natural_area_sf"] = Q["creek_woods_sf"] + Q["buffer_easement_on_lots_sf"]
Q["natural_area_ac"] = round(Q["natural_area_sf"] / 43560.0, 2)

# ---------------------------------------------------------------------------
# unit costs — every one is a planning allowance with a stated benchmark
# ---------------------------------------------------------------------------

UNIT_COSTS = {
    "mow_visit_per_lot": (
        22.00,
        "$/lot/visit",
        f"routed price for {M['lots']} stops on one "
        f"{M['lane_length_ft']:,.0f}-ft lane at ~1,340 SF of maintained turf each; "
        "Atlanta open-market mowing is $35–55/visit on a 10,890-SF quarter-acre lot "
        "(yourgreenpal 2026; Angi 2026)",
    ),
    "mow_visits_per_year": (
        34,
        "visits/yr",
        "weekly April–October (31) + 3 winter cleanups; Georgia Piedmont growing season",
    ),
    "lot_beds_per_year": (
        120.00,
        "$/lot/yr",
        "2 visits: shrub pruning + pre-emergent + 2 CY mulch at ~$45/CY installed; well below the "
        "$100–300/unit/month full-service national range because the yards are ~1,340 SF",
    ),
    "common_landscape_per_ac": (
        4500.00,
        "$/ac/yr",
        "Southeast HOA common-area maintenance contracts $2,500–6,000/ac/yr "
        "(United Land Services 2026 budget guide); midpoint for mown turf + beds",
    ),
    "natural_area_per_ac": (
        900.00,
        "$/ac/yr",
        "2 crew-visits/yr for vine and invasive removal, storm debris and buffer-marker checks, "
        "plus one arborist walk; no mowing (undisturbed buffer)",
    ),
    "tree_prune_each": (
        65.00,
        "$/tree per 3-yr cycle",
        "structural pruning of young street trees on a 3-year cycle, annualised",
    ),
    "plant_replacement_each": (
        450.00,
        "$/tree",
        "2-in caliper B&B canopy tree installed; 3 % annual loss after the 12-month warranty "
        "(checklist §6.m)",
    ),
    "irrigation_year": (
        1400.00,
        "$/yr",
        "spring start-up + winterisation + 2 backflow tests at $150 + repair allowance "
        "(amenity block only; no lot irrigation)",
    ),
    "sweep_event": (
        650.00,
        "$/event",
        "mobilisation + 1,754 ft of curb line; 2 events/yr",
    ),
    "pavement_patch_per_sf": (
        0.05,
        "$/SF/yr",
        "operating crack-fill and pothole allowance; the 20-year overlay is in reserves",
    ),
    "signs_markings_year": (
        900.00,
        "$/yr",
        "'NO PARKING — FIRE LANE' signs both sides (IFC 2024 (GA) App. D103.6), stop and speed "
        "signs, hammerhead striping; ~10 % of the installed sign inventory per year",
    ),
    "storm_structure_clean": (
        1400.00,
        "$/yr",
        "vacuum-truck day for inlets, pipes and both outlet structures",
    ),
    "pond_inspection_each": (
        900.00,
        "$/pond/yr",
        "annual inspection and written report by a qualified professional, as the recorded Storm "
        "Water BMP Maintenance Agreement requires (Site Development Plan Review Checklist §2.g.3)",
    ),
    "pond_routine_each": (
        1300.00,
        "$/pond/yr",
        "trash-rack and orifice cleaning, forebay hand-cleaning, rip-rap reset, erosion repair, "
        "mosquito/vegetation control (dry ponds; the mowing is in the common-landscape line)",
    ),
    "light_per_fixture_month": (
        23.00,
        "$/fixture/month",
        "Georgia Power outdoor-lighting service (energy + lamp/fixture maintenance) for a "
        "decorative post-top; VERIFY the tariff and whether the fixtures are company- or "
        "association-owned",
    ),
    "snow_year": (
        600.00,
        "$/yr",
        "one plow/sand event every other year at ~$1,200 for 1,754 ft",
    ),
    "clubhouse_electric_per_sf": (
        1.85,
        "$/SF/yr",
        "small assembly/community building ~14 kWh/SF/yr at ~$0.13/kWh; VERIFY against the "
        "Georgia Power commercial rate",
    ),
    "clubhouse_water_year": (
        2600.00,
        "$/yr",
        "clubhouse restrooms and kitchen plus amenity irrigation on a 1-in meter, Gwinnett DWR "
        "inside-county water and sewer rates; VERIFY",
    ),
    "clubhouse_gas_year": (
        700.00,
        "$/yr",
        "water heating and supplemental heat",
    ),
    "janitorial_visit": (
        65.00,
        "$/visit",
        "2 visits/week for a 2,400-SF clubhouse with two restrooms",
    ),
    "clubhouse_rm_year": (
        3900.00,
        "$/yr",
        "HVAC service contract (2 systems × $220), pest control, quarterly fire-alarm monitoring "
        "and the annual NFPA 13 sprinkler inspection/test of the clubhouse system, plus a repair "
        "allowance",
    ),
    "clubhouse_tel_year": (
        1700.00,
        "$/yr",
        "internet, cameras, access-control/fob service, Knox-box and alarm line",
    ),
    "court_year": (
        900.00,
        "$/yr",
        "nets, wind screens, blowing and washing 2 courts; resurfacing is in reserves",
    ),
    "kiosk_year": (
        500.00,
        "$/yr",
        "cleaning, lighting, lock and key replacement for the cluster-box unit shelter",
    ),
    "management_per_door_month": (
        22.00,
        "$/door/month",
        "Georgia management fees run $15–30/unit/month and small associations pay the top of the "
        "band (Access Management Group 2026; FirstService Residential Georgia; hoamanagement.com)",
    ),
    "hopa_survey_per_unit": (
        18.00,
        "$/unit per survey",
        "printing, mailing, follow-up and filing of the biennial occupancy survey and affidavit "
        "required by 24 CFR §100.307(b)–(c); run every 2 years, annualised",
    ),
    "hopa_certificate_each": (
        150.00,
        "$/certificate",
        f"resale/lease occupancy certification and age verification; ~3 transfers/yr at {M['lots']} units "
        "(often reimbursed by the seller — carried as a cost, not netted)",
    ),
    "hopa_admin_year": (
        600.00,
        "$/yr",
        "records retention, the annual §100.308(b)(2) written certification, the public postings "
        "required by 24 CFR §100.306(a)(7) and the annual compliance letter to the City",
    ),
    "hopa_legal_cycle": (
        900.00,
        "$/3 yr",
        "counsel's review of the survey form, affidavit and published policies every 3 years",
    ),
    "insurance_year": (
        13500.00,
        "$/yr",
        "master property on association assets + GL $1M/$2M + D&O $1M + crime/fidelity + $5M "
        "umbrella; a 25–75-unit PUD with a clubhouse quotes $9,000–24,300 in 2026 "
        "(Professional Insurance Group 2026), $120–325/unit",
    ),
    "audit_year": (
        1600.00,
        "$/yr",
        "financial review (not a full audit) and Form 1120-H preparation",
    ),
    "legal_year": (
        2500.00,
        "$/yr",
        "general counsel, covenant enforcement demand letters, annual document review",
    ),
    "reserve_study_cycle": (
        3500.00,
        "$/3 yr",
        "full study then an update every 3 years; US HOA reserve studies run $2,500–5,000 "
        "(CMGT 2026; CAMS 2026)",
    ),
    "admin_year": (
        1900.00,
        "$/yr",
        "bank and lockbox fees, accounting software, owner portal/website, postage, annual "
        "meeting, registered agent, Georgia nonprofit annual registration ($50)",
    ),
    "bad_debt_pct": (
        0.02,
        "of assessments",
        "2 % delinquency allowance; the POA Act lien (O.C.G.A. §44-3-232) makes eventual recovery "
        "likely but the budget cannot assume it",
    ),
    "contingency_pct": (
        0.05,
        "of operating",
        "5 % operating contingency; this is a first-year budget for a community that does not yet "
        "exist",
    ),
    "waste_per_home_month": (
        22.00,
        "$/home/month",
        "bundled residential hauler contract, one truck per week on a private lane; shown as an "
        "option — VERIFY whether the City's residential collection serves private streets",
    ),
}

# reserve components: (component, quantity, unit, unit cost, useful life yr, basis)
RESERVE_COMPONENTS = [
    (
        "Lane and entry-drive asphalt — mill and overlay",
        "pavement_sf",
        "SF",
        4.00,
        20,
        "overlay $3.50–5.50/SF and mill-and-overlay $4.50–8.00/SF in 2026 (Buildcalchub; Wright "
        "Construction; Paving Estimator); $4.00 assumes a single mobilisation for the whole lane",
    ),
    (
        "Lane crack sealing and surface treatment",
        "pavement_sf",
        "SF",
        0.30,
        7,
        "crack seal + fog/seal coat between overlays",
    ),
    (
        "Concrete sidewalk — 25 % panel replacement per cycle",
        "sidewalk_quarter_sf",
        "SF",
        9.00,
        20,
        "4-in walk removal and replacement; 25 % of panels per 20-year cycle (root heave, "
        "settlement, ADA cross-slope corrections)",
    ),
    (
        "Curb, gutter and valley-gutter repair allowance",
        "lane_length_ft",
        "LF",
        4.00,
        25,
        "10 % of the curb line replaced per 25-year cycle at ~$40/LF",
    ),
    (
        "Detention pond sediment removal",
        "ponds",
        "pond",
        18000.00,
        10,
        f"dry basins of {Q['pond_water_area_sf'] / 43560.0 / Q['ponds']:.2f} ac each holding "
        f"{Q['pond_storage_cf']:,} cf between them (2026-09-03 re-sizing); Southeast stormwater dredging "
        "$25–75/CY and $25,000–75,000 for a half-acre HOA pond (Angi 2026; AUE Land; Landshore 2026) — "
        "the allowance predates the enlargement and is to be re-priced before the first reserve study",
    ),
    (
        "Pond outlet structures, trash racks, rip-rap, emergency spillway",
        "ponds",
        "pond",
        12000.00,
        30,
        "outlet control structure and headwall rehabilitation",
    ),
    (
        "Storm sewer pipe and structure rehabilitation",
        "lane_length_ft",
        "LF of lane",
        68.50,
        50,
        "lane storm drainage — pipe, inlets and junction boxes at end of service life, priced per "
        "foot of lane so the Phase-1 case scales",
    ),
    (
        "Clubhouse roof — architectural asphalt shingles",
        "clubhouse_roof_sf",
        "SF",
        6.50,
        25,
        "clubhouse footprint × 1.25 slope factor; tear-off and replacement",
    ),
    (
        "Clubhouse HVAC (2 split systems)",
        "hvac_units",
        "each",
        11000.00,
        15,
        "3-ton systems, replacement including duct repairs",
    ),
    (
        "Clubhouse exterior repaint",
        "lump_paint",
        "LS",
        9000.00,
        8,
        "docs/12 §09 91 13 2.03 sets the HOA repaint cycle at 8–10 years",
    ),
    (
        "Clubhouse interior — flooring, paint, kitchen, restrooms, furnishings",
        "lump_interior",
        "LS",
        60000.00,
        15,
        "$25/SF of clubhouse for finishes and FF&E",
    ),
    (
        "Clubhouse water heater, appliances, fitness equipment",
        "lump_equip",
        "LS",
        14000.00,
        12,
        "allowance",
    ),
    (
        "Pickleball court resurfacing",
        "pickleball_courts",
        "court",
        8000.00,
        6,
        "acrylic resurface of a 30' × 60' pad; 5–8-year cycle",
    ),
    (
        "Pickleball fencing",
        "pickleball_pad_perimeter_lf",
        "LF",
        28.00,
        20,
        "4-ft black vinyl-coated chain link on the pad perimeter",
    ),
    (
        "Lane and amenity light poles and fixtures",
        "light_poles",
        "each",
        3800.00,
        25,
        "14-ft full-cutoff post-top ≤3000 K (voluntary condition 11); assumes association-owned "
        "fixtures — if they are on the Georgia Power tariff this component drops out",
    ),
    (
        "Mail kiosk — cluster box units and shelter",
        "lump_kiosk",
        "LS",
        28000.00,
        25,
        "4 USPS-approved CBUs at ~$2,600 plus a 16' × 10' shelter (checklist §4.r, "
        "'protection from the elements')",
    ),
    (
        "Monument entry sign, wall and landscape lighting",
        "lump_sign",
        "LS",
        28000.00,
        20,
        "≤32-SF monument sign (voluntary condition 14), masonry base, external lighting",
    ),
    (
        "Site furnishings — benches, tables, trash receptacles, kiosk board",
        "lump_furn",
        "LS",
        16000.00,
        15,
        "village green and pocket greens",
    ),
    (
        "Irrigation system replacement (amenity block)",
        "lump_irrig",
        "LS",
        18000.00,
        20,
        "controller, valves, heads and mainline",
    ),
    (
        "Landscape renovation and buffer re-planting fund",
        "lump_landscape",
        "LS",
        20000.00,
        15,
        "periodic renovation of common beds and the supplemental evergreen buffer planting; also "
        "the fund behind the re-planting remedy in Article 6 of the declaration",
    ),
]


def money(x):
    return f"${x:,.0f}"


def unit(x):
    """Unit prices keep their cents; whole-dollar prices do not print '.00'."""
    return f"${x:,.2f}" if abs(x - round(x)) > 1e-9 else f"${x:,.0f}"


def build(scenario):
    """scenario: 'full' (every lot, whole lane, 2 ponds) or 'phase1' (lots at u < the phase line, 1 pond)."""
    q = dict(Q)
    if scenario == "phase1":
        u_lim = M["phase_line_u_ft"]
        cl = centerline_length(lane["centerline"], u_max=u_lim)
        q["lots_total"] = M["lots_phase1"]
        q["plan_A_lots"] = sum(1 for x in L["lots"] if x["phase"] == 1 and x["plan"] == "A")
        q["plan_B_lots"] = sum(1 for x in L["lots"] if x["phase"] == 1 and x["plan"] == "B")
        q["lane_length_ft"] = round(cl + Q["entry_drive_ft"], 1)
        hh1 = sum(shoelace(leg) for leg in L["hammerheads"][0]["legs"])
        q["pavement_sf_published"] = round(cl * lane["pavement_width_ft"] + Q["pavement_entry_sf"] + hh1)
        q["sidewalk_sf_published"] = round((cl + Q["entry_drive_ft"]) * 5.0)
        q["lane_verge_sf"] = round(
            Q["lane_verge_sf"] * (cl + Q["entry_drive_ft"]) / Q["lane_length_ft"]
        )
        q["ponds"] = 1
        q["pond_tract_sf"] = Q["open_space_tracts"]["Pond 1 (dry detention / WQ) tract"]
        q["greens_sf"] = L["greens"][0]["area_sf"]
        q["creek_woods_sf"] = 0
        q["buffer_easement_on_lots_sf"] = q["lots_total"] * BUFFER_PER_LOT_SF
        q["yard_total_sf"] = round(q["plan_A_lots"] * yard["A"] + q["plan_B_lots"] * yard["B"])
        q["common_landscape_sf"] = (
            q["lane_verge_sf"] + Q["amenity_soft_sf"] + q["greens_sf"] + q["pond_tract_sf"]
        )
        q["common_landscape_ac"] = round(q["common_landscape_sf"] / 43560.0, 2)
        q["natural_area_sf"] = q["creek_woods_sf"] + q["buffer_easement_on_lots_sf"]
        q["natural_area_ac"] = round(q["natural_area_sf"] / 43560.0, 2)
        q["street_trees"] = int(q["lane_length_ft"] // STREET_TREE_SPACING_FT)
        q["trees_total"] = q["street_trees"] + Q["frontage_strip_trees"] + Q["parking_lot_trees"]
        q["light_poles"] = int(math.ceil(q["lane_length_ft"] / LIGHT_SPACING_FT)) + 4

    n = q["lots_total"]
    uc = {k: v[0] for k, v in UNIT_COSTS.items()}
    lines = []   # (group, item, qty text, unit cost text, annual $)

    def add(group, item, qty, unitcost, amount):
        lines.append([group, item, qty, unitcost, round(amount)])

    # --- 1 grounds ---------------------------------------------------------
    mow = n * uc["mow_visits_per_year"] * uc["mow_visit_per_lot"]
    add("1 Grounds", "Lot yard care — mow, edge, trim, blow",
        f"{n} lots × {uc['mow_visits_per_year']:.0f} visits",
        f"{unit(uc['mow_visit_per_lot'])}/lot/visit", mow)
    add("1 Grounds", "Lot beds — pruning, pre-emergent, mulch, leaf removal",
        f"{n} lots × 2 visits", f"{unit(uc['lot_beds_per_year'])}/lot/yr",
        n * uc["lot_beds_per_year"])
    add("1 Grounds", "Common-area turf and beds (lane verge, greens, amenity, pond tracts)",
        f"{q['common_landscape_ac']:.2f} ac", f"{unit(uc['common_landscape_per_ac'])}/ac/yr",
        q["common_landscape_ac"] * uc["common_landscape_per_ac"])
    add("1 Grounds", "Buffer easement and creek-woods stewardship (undisturbed areas)",
        f"{q['natural_area_ac']:.2f} ac", f"{unit(uc['natural_area_per_ac'])}/ac/yr",
        q["natural_area_ac"] * uc["natural_area_per_ac"])
    add("1 Grounds", "Street- and strip-tree pruning (3-year cycle, annualised)",
        f"{q['trees_total']} trees ÷ 3", f"{unit(uc['tree_prune_each'])}/tree",
        q["trees_total"] / 3.0 * uc["tree_prune_each"])
    add("1 Grounds", "Tree, shrub and turf replacement (3 % of stock per year)",
        f"{q['trees_total']} trees × 3 %", f"{unit(uc['plant_replacement_each'])}/tree",
        q["trees_total"] * 0.03 * uc["plant_replacement_each"])
    add("1 Grounds", "Irrigation operation, backflow testing and repair (amenity block)",
        "1 system", f"{unit(uc['irrigation_year'])}/yr", uc["irrigation_year"])

    # --- 2 lane, walks, stormwater ----------------------------------------
    add("2 Lane and stormwater", "Lane sweeping and gutter cleaning",
        "2 events/yr", f"{unit(uc['sweep_event'])}/event", 2 * uc["sweep_event"])
    add("2 Lane and stormwater", "Pavement crack fill and pothole patching (operating)",
        f"{q['pavement_sf_published']:,} SF", f"{unit(uc['pavement_patch_per_sf'])}/SF/yr",
        q["pavement_sf_published"] * uc["pavement_patch_per_sf"])
    add("2 Lane and stormwater", "Fire-lane and traffic signs, pavement markings",
        "lane inventory", f"{unit(uc['signs_markings_year'])}/yr", uc["signs_markings_year"])
    add("2 Lane and stormwater", "Storm inlet, pipe and outlet-structure cleaning",
        "1 vacuum-truck day", f"{unit(uc['storm_structure_clean'])}/yr",
        uc["storm_structure_clean"])
    add("2 Lane and stormwater", "Pond annual inspection and report to the City",
        f"{q['ponds']} pond" + ("s" if q["ponds"] != 1 else ""), f"{unit(uc['pond_inspection_each'])}/pond/yr",
        q["ponds"] * uc["pond_inspection_each"])
    add("2 Lane and stormwater", "Pond routine maintenance (racks, forebay, rip-rap, erosion)",
        f"{q['ponds']} pond" + ("s" if q["ponds"] != 1 else ""), f"{unit(uc['pond_routine_each'])}/pond/yr",
        q["ponds"] * uc["pond_routine_each"])
    add("2 Lane and stormwater", "Lane and common lighting — energy and fixture maintenance",
        f"{q['light_poles']} fixtures × 12 mo",
        f"{unit(uc['light_per_fixture_month'])}/fixture/mo",
        q["light_poles"] * 12 * uc["light_per_fixture_month"])
    add("2 Lane and stormwater", "Snow and ice event allowance",
        "0.5 event/yr", f"{unit(uc['snow_year'])}/yr", uc["snow_year"])

    # --- 3 amenity ---------------------------------------------------------
    add("3 Amenity", "Clubhouse electricity",
        f"{q['clubhouse_sf']:,} SF", f"{unit(uc['clubhouse_electric_per_sf'])}/SF/yr",
        q["clubhouse_sf"] * uc["clubhouse_electric_per_sf"])
    add("3 Amenity", "Clubhouse water and sewer, amenity irrigation water",
        "1 meter", f"{unit(uc['clubhouse_water_year'])}/yr", uc["clubhouse_water_year"])
    add("3 Amenity", "Clubhouse gas", "1 service", f"{unit(uc['clubhouse_gas_year'])}/yr",
        uc["clubhouse_gas_year"])
    add("3 Amenity", "Clubhouse janitorial and supplies",
        "104 visits/yr", f"{unit(uc['janitorial_visit'])}/visit", 104 * uc["janitorial_visit"])
    add("3 Amenity", "Clubhouse repairs, HVAC contract, pest, alarm and NFPA 13 sprinkler ITM",
        "1 building", f"{unit(uc['clubhouse_rm_year'])}/yr", uc["clubhouse_rm_year"])
    add("3 Amenity", "Internet, cameras, access control, Knox box",
        "1 building", f"{unit(uc['clubhouse_tel_year'])}/yr", uc["clubhouse_tel_year"])
    add("3 Amenity", "Pickleball court cleaning, nets and screens",
        f"{q['pickleball_courts']} courts", f"{unit(uc['court_year'])}/yr", uc["court_year"])
    add("3 Amenity", "Mail kiosk cleaning, lighting and locks",
        "1 kiosk", f"{unit(uc['kiosk_year'])}/yr", uc["kiosk_year"])

    # --- 4 administration --------------------------------------------------
    add("4 Administration", "Professional community management",
        f"{n} doors × 12 mo", f"{unit(uc['management_per_door_month'])}/door/mo",
        n * 12 * uc["management_per_door_month"])
    hopa = (
        n * uc["hopa_survey_per_unit"] / 2.0
        + 3 * uc["hopa_certificate_each"]
        + uc["hopa_admin_year"]
        + uc["hopa_legal_cycle"] / 3.0
    )
    add("4 Administration",
        "HOPA age-verification program (biennial survey, transfer certificates, records)",
        f"{n} units ÷ 2 yr + 3 transfers",
        f"{unit(uc['hopa_survey_per_unit'])}/unit + {unit(uc['hopa_certificate_each'])}/transfer",
        hopa)
    add("4 Administration", "Insurance — property, GL, D&O, crime, umbrella",
        f"{n} units + clubhouse", f"{unit(uc['insurance_year'])}/yr", uc["insurance_year"])
    add("4 Administration", "Financial review and Form 1120-H", "1/yr",
        f"{unit(uc['audit_year'])}/yr", uc["audit_year"])
    add("4 Administration", "Legal — counsel and covenant enforcement", "allowance",
        f"{unit(uc['legal_year'])}/yr", uc["legal_year"])
    add("4 Administration", "Reserve study (update every 3 years, annualised)", "1 ÷ 3 yr",
        f"{unit(uc['reserve_study_cycle'])}/study", uc["reserve_study_cycle"] / 3.0)
    add("4 Administration", "Banking, software, portal, postage, meetings, state registration",
        "1/yr", f"{unit(uc['admin_year'])}/yr", uc["admin_year"])

    operating = sum(l[4] for l in lines)

    # --- 5 reserves --------------------------------------------------------
    qmap = {
        "pavement_sf": q["pavement_sf_published"],
        "sidewalk_quarter_sf": round(q["sidewalk_sf_published"] * 0.25),
        "lane_length_ft": q["lane_length_ft"],
        "ponds": q["ponds"],
        "clubhouse_roof_sf": round(q["clubhouse_sf"] * 1.25),
        "hvac_units": 2,
        "pickleball_courts": q["pickleball_courts"],
        "pickleball_pad_perimeter_lf": q["pickleball_pad_perimeter_lf"],
        "light_poles": q["light_poles"],
        "lump_paint": 1,
        "lump_interior": 1,
        "lump_equip": 1,
        "lump_kiosk": 1,
        "lump_sign": 1,
        "lump_furn": 1,
        "lump_irrig": 1,
        "lump_landscape": 1,
    }
    reserves = []
    for name, qkey, unitname, cost, life, basis in RESERVE_COMPONENTS:
        qty = qmap[qkey]
        if qkey == "ponds" and q["ponds"] == 1:
            pass  # quantity already scenario-scaled
        repl = qty * cost
        reserves.append([name, qty, unitname, cost, repl, life, repl / life, basis])
    reserve_annual = sum(r[6] for r in reserves)

    contingency = operating * uc["contingency_pct"]
    bad_debt = (operating + contingency + reserve_annual) * uc["bad_debt_pct"]
    total = operating + contingency + bad_debt + reserve_annual

    return {
        "scenario": scenario,
        "lots": n,
        "quantities": q,
        "lines": lines,
        "operating": round(operating),
        "reserves": [
            [r[0], r[1], r[2], r[3], round(r[4]), r[5], round(r[6]), r[7]] for r in reserves
        ],
        "reserve_annual": round(reserve_annual),
        "contingency": round(contingency),
        "bad_debt": round(bad_debt),
        "total": round(total),
        "per_lot_year": round(total / n),
        "per_lot_month": round(total / n / 12),
        "operating_per_lot_month": round(operating / n / 12),
        "reserve_per_lot_month": round(reserve_annual / n / 12),
        "waste_option_per_lot_month": uc["waste_per_home_month"],
    }


FULL = build("full")
PH1 = build("phase1")

# ---------------------------------------------------------------------------
# self-checks
# ---------------------------------------------------------------------------
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


check(
    abs(Q["pavement_sf_computed"] - Q["pavement_sf_published"]) / Q["pavement_sf_published"] < 0.03,
    f"pavement polygons {Q['pavement_sf_computed']} vs metrics {Q['pavement_sf_published']} differ >3%",
)
check(
    abs(Q["sidewalk_sf_computed"] - Q["sidewalk_sf_published"]) / Q["sidewalk_sf_published"] < 0.05,
    f"sidewalk polygons {Q['sidewalk_sf_computed']} vs metrics {Q['sidewalk_sf_published']} differ >5%",
)
check(Q["plan_A_lots"] + Q["plan_B_lots"] == M["lots"], "plan mix does not sum to the lot count")
check(FULL["total"] > 0 and FULL["per_lot_month"] > 0, "budget did not compute")
check(PH1["lots"] == M["lots_phase1"], "phase-1 lot count mismatch")

# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------


def md_tables(b):
    out = []
    groups = []
    for g, item, qty, uctxt, amt in b["lines"]:
        if not groups or groups[-1][0] != g:
            groups.append((g, []))
        groups[-1][1].append((item, qty, uctxt, amt))
    out.append("| Line | Quantity (from `data/layout.json` / `data/plans.json`) | Unit cost | Annual |")
    out.append("|---|---|---|---:|")
    for g, items in groups:
        out.append(f"| **{g}** | | | |")
        for item, qty, uctxt, amt in items:
            out.append(f"| {item} | {qty} | {uctxt} | {money(amt)} |")
    out.append(f"| **Operating subtotal** | | | **{money(b['operating'])}** |")
    out.append(f"| Operating contingency, 5 % | | | {money(b['contingency'])} |")
    out.append(f"| **Reserve contribution** (schedule below) | | | **{money(b['reserve_annual'])}** |")
    out.append(f"| Delinquency allowance, 2 % of assessments | | | {money(b['bad_debt'])} |")
    out.append(f"| **TOTAL ANNUAL BUDGET** | | | **{money(b['total'])}** |")
    out.append(f"| **Per lot per year** ({b['lots']} lots) | | | **{money(b['per_lot_year'])}** |")
    out.append(f"| **Per lot per month** | | | **{money(b['per_lot_month'])}** |")
    return "\n".join(out)


def md_reserves(b):
    out = ["| Component | Qty | Unit | Unit cost | Replacement cost | Life (yr) | Annual | Basis |",
           "|---|---:|---|---:|---:|---:|---:|---|"]
    for name, qty, unitname, cost, repl, life, ann, basis in b["reserves"]:
        qtxt = f"{qty:,.0f}" if isinstance(qty, (int, float)) else str(qty)
        out.append(
            f"| {name} | {qtxt} | {unitname} | {unit(cost)} | {money(repl)} | {life} | {money(ann)} | {basis} |"
        )
    out.append(
        f"| **Total annual reserve contribution** | | | | | | **{money(b['reserve_annual'])}** | "
        f"straight-line component method, no interest or inflation offset |"
    )
    return "\n".join(out)


report = [
    "# HOA budget — computed output (generator `tools/hoa_budget.py`)",
    "",
    "Reproduced verbatim in `docs/13-hoa-hopa-and-covenant-outline.md` §8. Re-run the generator "
    "after any change to `data/layout.json` or `data/plans.json`.",
    "",
    "## Quantities",
    "",
    "| Quantity | Value | Source |",
    "|---|---:|---|",
    f"| Lots | {Q['lots_total']} | `layout.json` metrics.lots |",
    f"| Plan mix | {Q['plan_A_lots']} A / {Q['plan_B_lots']} B | `layout.json` lots |",
    f"| Lane length (entrance to terminus) | {Q['lane_length_ft']:,.0f} ft | metrics.lane_length_ft |",
    f"| Lane + entry pavement | {Q['pavement_sf_published']:,} SF | metrics.pavement_sf (polygons compute {Q['pavement_sf_computed']:,} SF) |",
    f"| Sidewalk | {Q['sidewalk_sf_published']:,} SF | metrics.sidewalk_sf (polygons compute {Q['sidewalk_sf_computed']:,} SF) |",
    f"| Lane tract, less pavement and walk (verge) | {Q['lane_verge_sf']:,} SF | tract − pavement − sidewalk |",
    f"| Front amenity tract | {Q['amenity_tract_sf']:,} SF, of which {Q['amenity_hard_sf']:,} SF built/paved | metrics + amenity polygons |",
    f"| Greens (3 tracts) | {Q['greens_sf']:,} SF | `layout.json` greens |",
    f"| Pond tracts | {Q['pond_tract_sf']:,} SF ({Q['ponds']} ponds, {Q['pond_water_area_sf']:,} SF of basin) | open_space_tracts, ponds |",
    f"| Creek woods (preserved) | {Q['creek_woods_sf']:,} SF | open_space_tracts |",
    f"| Buffer easement inside lots | {Q['buffer_easement_on_lots_sf']:,} SF | metrics.buffer_easement_on_lots_sf |",
    f"| Maintained common landscape | {Q['common_landscape_sf']:,} SF = {Q['common_landscape_ac']:.2f} ac | verge + amenity soft + greens + pond tracts |",
    f"| Undisturbed natural area | {Q['natural_area_sf']:,} SF = {Q['natural_area_ac']:.2f} ac | creek woods + buffer easement |",
    f"| Maintained yard per lot | Plan A {Q['plan_A_yard_sf']:,} SF / Plan B {Q['plan_B_yard_sf']:,} SF (avg {Q['yard_avg_sf']:,} SF) | 5,000 SF − plans.json lot_siting impervious − 1,000 SF buffer |",
    f"| Street trees / total trees | {Q['street_trees']} / {Q['trees_total']} | 40 ft o.c. + frontage strip + parking bay |",
    f"| Light fixtures | {Q['light_poles']} | 150 ft o.c. + 4 at the amenity block (assumption) |",
    "",
    f"## Budget — full build-out ({FULL['lots']} lots)",
    "",
    md_tables(FULL),
    "",
    "### Reserve component schedule — full build-out",
    "",
    md_reserves(FULL),
    "",
    f"Optional bundled solid-waste contract: {unit(FULL['waste_option_per_lot_month'])}/home/month "
    f"= {money(FULL['waste_option_per_lot_month'] * 12 * FULL['lots'])}/yr, which would raise dues to "
    f"{money(FULL['per_lot_month'] + FULL['waste_option_per_lot_month'])}/month.",
    "",
    f"## Budget — Phase 1 only ({PH1['lots']} lots), the condition-16 downside case",
    "",
    md_tables(PH1),
    "",
    "### Reserve component schedule — Phase 1 only",
    "",
    md_reserves(PH1),
    "",
]

os.makedirs(os.path.join(ROOT, "verify"), exist_ok=True)
open(os.path.join(ROOT, "verify", "hoa-budget-output.md"), "w").write("\n".join(report) + "\n")
json.dump(
    {
        "generated_by": "tools/hoa_budget.py",
        "inputs": ["data/layout.json", "data/plans.json"],
        "unit_costs": {k: {"value": v[0], "unit": v[1], "basis": v[2]} for k, v in UNIT_COSTS.items()},
        "full_buildout": FULL,
        "phase1_only": PH1,
    },
    open(os.path.join(ROOT, "data", "hoa-budget-derived.json"), "w"),
    indent=1,
)

# docs/13 cross-check
doc = os.path.join(ROOT, "docs", "13-hoa-hopa-and-covenant-outline.md")
if os.path.exists(doc):
    t = open(doc).read()
    for label, val in [
        ("total annual budget", money(FULL["total"])),
        ("dues per lot per month", money(FULL["per_lot_month"])),
        ("reserve contribution", money(FULL["reserve_annual"])),
        ("phase-1 dues", money(PH1["per_lot_month"])),
    ]:
        check(val in t, f"docs/13 does not contain the computed {label} {val}")
    check(
        t.rstrip("\n").split("\n")[-1] == "<!-- architecture-studio:requires-disclaimer -->",
        "docs/13: last line is not the disclaimer marker",
    )
    check("appears consistent with" in t, "docs/13: missing the required 'appears consistent with' phrasing")
    check(t.count("[ATTORNEY REVIEW REQUIRED]") >= 10,
          "docs/13: fewer than 10 [ATTORNEY REVIEW REQUIRED] flags")
    check("DRAFT — NOT SEALED" in t, "docs/13: missing the DRAFT — NOT SEALED label")
    for banned in (r"\bcomplies\b", r"\bcompliant\b", r"IFC 2018", r"329[- ]f"):
        m = re.search(banned, t, re.I)
        check(m is None, f"docs/13: banned phrase {banned!r} at ...{t[max(0, (m.start() if m else 0) - 40):(m.end() if m else 0) + 20]!r}")

print(f"quantities: {Q['lots_total']} lots, pavement {Q['pavement_sf_published']:,} SF "
      f"(polygons {Q['pavement_sf_computed']:,}), walk {Q['sidewalk_sf_published']:,} SF, "
      f"common landscape {Q['common_landscape_ac']:.2f} ac, {Q['light_poles']} lights, "
      f"{Q['trees_total']} trees")
print(f"FULL   {FULL['lots']} lots: operating {money(FULL['operating'])} + reserves {money(FULL['reserve_annual'])} "
      f"+ contingency {money(FULL['contingency'])} + bad debt {money(FULL['bad_debt'])} "
      f"= {money(FULL['total'])} -> {money(FULL['per_lot_month'])}/lot/month "
      f"({money(FULL['operating_per_lot_month'])} operating + {money(FULL['reserve_per_lot_month'])} reserve)")
print(f"PHASE1 {PH1['lots']} lots: {money(PH1['total'])} -> {money(PH1['per_lot_month'])}/lot/month")
print("wrote data/hoa-budget-derived.json and verify/hoa-budget-output.md")
if fails:
    print("\nFAILED:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("checks: PASS")
