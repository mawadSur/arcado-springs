#!/usr/bin/env python3
"""Generate docs/10-submittal-checklist-and-roadmap.md and self-check it.
Run: python3 tools/roadmap.py   (exit 1 on any failed check)

Inputs: FACTS.md (calendar, fees, notice rules), data/application-instructions-2026.txt (11 items + schedule),
data/ordinance-excerpts.md (§1003-4/-6/-10/-11), data/layout.json + data/dev-summary-derived.json (numbers),
status/rz-2025-01/ (2025 filing facts). Cost/lead-time ranges are the planning allowances supplied in the
2026-08-29 roadmap brief (survey $8–18k / 3–6 wks; MCP seal $8–25k; TIS if required $6–15k; attorney $7.5–25k;
renderings $3–15k) — they are NOT in FACTS.md and are flagged VERIFY-with-quotes in the document."""
import datetime as dt, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/10-submittal-checklist-and-roadmap.md"
lay = json.load(open(ROOT / "data/layout.json"))
der = json.load(open(ROOT / "data/dev-summary-derived.json"))
M = lay["metrics"]
LOTS = M["lots"]; DENS = M["density_du_ac_deeded"]; ACRES = M["acreage_deeded_ac"]; GIS_AC = M["acreage_gis_ac"]
PM = M["pm_peak_trips_ite_251"]; OS_PCT = M["open_space_pct_deeded"]; IMP_PCT = M["impervious_pct_gis"]
assert LOTS == 43 and DENS == 4.56, (LOTS, DENS)

# ---- calendar (Instructions p. 2 schedule rows; §1003-6 windows) ----
D = dt.date
cyc = {
    "A": dict(file=D(2026, 9, 25), ad=D(2026, 9, 29), notice=D(2026, 10, 7), pc=D(2026, 10, 22), cc=D(2026, 11, 9)),
    "B": dict(file=D(2026, 10, 30), ad=D(2026, 11, 3), notice=D(2026, 11, 11), pc=D(2026, 11, 26), cc=D(2026, 12, 14)),
}
for c in cyc.values():
    c["coi_due"] = c["file"] + dt.timedelta(days=10)          # O.C.G.A. §36-67A-3(B): within 10 days of filing
    c["preapp_by"] = c["file"] - dt.timedelta(days=7)         # Instructions: pre-app "one week prior to submittal"
    c["ad_to_pc"] = (c["pc"] - c["ad"]).days
    c["ad_to_cc"] = (c["cc"] - c["ad"]).days
    c["notice_to_pc"] = (c["pc"] - c["notice"]).days
    c["notice_to_cc"] = (c["cc"] - c["notice"]).days
    c["sign_latest"] = c["pc"] - dt.timedelta(days=15)        # §1003-6(2): sign 15–45 days before hearing
    c["sign_earliest_cc"] = c["cc"] - dt.timedelta(days=45)
    # sanity: instructions/ordinance windows
    assert 15 <= c["ad_to_pc"] <= 45 and 30 <= c["ad_to_cc"] <= 45, c
    assert c["notice_to_pc"] >= 15 and 15 <= c["notice_to_cc"] <= 45, c
assert cyc["A"]["file"].strftime("%a") == "Fri" and cyc["A"]["pc"].strftime("%a") == "Thu" and cyc["A"]["cc"].strftime("%a") == "Mon"
TODAY = D(2026, 8, 29)
W1 = D(2026, 8, 31)  # Monday of critical-path week 1
def wk(n):  # week n (1-based) Monday–Friday label
    s = W1 + dt.timedelta(days=7 * (n - 1)); e = s + dt.timedelta(days=4)
    return f"{s.strftime('%m/%d')}–{e.strftime('%m/%d')}"
def f(d): return d.strftime("%a %m/%d/%Y")
def fs(d): return d.strftime("%m/%d")

# ---- budget (planning allowances from the brief; fee from the FY25-26 schedule) ----
budget = [
    # (line, low, high, lead, note)
    ("Application fee — Rezoning, 5.0–9.9 ac (FY25-26 fee schedule; Instructions item 2)", 1250, 1250, "at filing", "Non-refundable; check payable to City of Lilburn. Fixed."),
    ("Boundary survey + sealed metes-and-bounds legal description (GA RLS); add sewer-invert survey and Arcado Rd sight-distance to the scope", 8000, 18000, "3–6 wks", "Planning allowance from the roadmap brief — VERIFY with two RLS quotes; invert/sight-distance add-ons may price separately."),
    ("Master Concept Plan sealed by a Georgia PE (site plan on the survey base; preliminary lane, sewer, pond sketches; DWR capacity request letter)", 8000, 25000, "2–4 wks after survey", "Planning allowance — VERIFY with quotes; scope is the rezoning MCP only, not LDP construction drawings."),
    ("Traffic Impact Study — only if Gwinnett DOT requires one (≈13 PM peak trips is below the 21-trip Level-2 threshold — VERIFY at pre-app)", 0, 15000, "3–5 wks if required", "Low case $0 (letter of trip generation by the PE instead); high case $6–15k if a study is required."),
    ("Attorney — purchase contract / owner consent for R6123 014 & 162, LOI and conditions review, HOPA covenant outline, notice audit, hearing representation", 7500, 25000, "start week 1; through Council", "Planning allowance — VERIFY with an engagement letter; hearing representation drives the high end."),
    ("Architectural elevations and renderings of every street-visible side, to scale or in proper perspective, with colors and materials (Instructions item 11)", 3000, 15000, "2–4 wks", "Planning allowance — VERIFY; the existing AI concept images are illustrative only and are not 'to scale'."),
]
low = sum(b[1] for b in budget); high = sum(b[2] for b in budget)
excluded = [
    ("Gwinnett DWR sewer capacity certification (form Rev. 07/2023)", "fee not in package data — VERIFY with DWR (678-376-7026)"),
    ("Gwinnett DOT access / driveway-permit pre-coordination", "no fee expected at the rezoning stage; permit fee later — VERIFY"),
    ("GCPS school-impact letter", "requested by the City from GCPS planning (the 2025 letter was 'Prepared for City of Lilburn'); no applicant fee expected — VERIFY"),
    ("Notary for four certifications", "nominal — VERIFY current statutory fee"),
    ("Stream top-of-bank field delineation (qualified professional)", "may fold into the survey or a separate environmental scope — VERIFY quote"),
    ("Printing: 1 full-size site plan + 5 reductions (8.5\" × 11\"); tear sheets", "nominal"),
    ("Community record: website update, neighbor-meeting notices, sign photographs", "owner's time; printing/postage nominal"),
]
def usd(n): return f"${n:,.0f}"

# ---- document ----
A, B = cyc["A"], cyc["B"]
doc = f"""---
title: "Submittal Checklist and Roadmap — Cottages at Arcado Springs"
date: 2026-08-29
address: "4535, 4537, 4539 & 4541 Arcado Rd SW, Lilburn, GA 30047 — Land Lot 123, 6th District, Gwinnett County (PINs R6123 033 / 015 / 014 / 162)"
status: "DRAFT — owner-prepared roadmap; costs and lead times are planning allowances to be replaced by quotes; items marked NEEDS PROFESSIONAL are DRAFT until sealed"
generator: "tools/roadmap.py (dates and sums computed; checks pass)"
---

# 10 — Submittal Checklist and Roadmap

**Application:** R-1 → R-2 (Medium-Density Residential), Lilburn Zoning Ordinance 2023-603 §402, for **{LOTS} one-story detached cottage homes** (55+ HOPA, voluntary condition) on **{ACRES} ac deeded** ({GIS_AC} ac by GIS; the RLS survey governs) — **{DENS} du/ac** on the deeded acreage.
**Governing lists:** City of Lilburn 2026 Application Instructions — Rezoning/SUP/CIC, items (1)–(11) (`data/application-instructions-2026.txt`); Lilburn Zoning Ordinance 2023-603 §1003-4 items 1–6, §1003-6 notice, §1003-10 withdrawal, §1003-11 refiling bar (`data/ordinance-excerpts.md`).
**Numbers:** `data/layout.json` metrics (site plan generator v1, {LOTS} lots — being refined for the entrance relocation) and `data/dev-summary-derived.json`. Local coordinates **u** (along the strip from the Arcado Rd R/W corner, N 28°43' W) and **v** (across, + toward the NE line) are those of `FACTS.md` §1.

**How to read the status column.** READY DRAFT = the package contains a complete owner-prepared draft; NEEDS PROFESSIONAL = a licensed Georgia RLS / PE / architect / attorney must produce or seal it before filing; NEEDS SIGNATURE = the content is drafted and only signatures/notarization remain; VERIFY = a fact or a decision outside the package data must be settled first. Cost and lead-time ranges are the planning allowances supplied with the 2026-08-29 roadmap brief (survey $8–18k / 3–6 weeks; MCP seal $8–25k; TIS if required $6–15k; attorney $7.5–25k; renderings $3–15k); none is a quote — **VERIFY each with a written proposal**.

---

## 1. Checklist — the 11 Instruction items, the §1003-4 items, and the practical extras

| # | Item (source) | What it is | What THIS package provides (file) | Who must produce / seal | Status | Est. cost | Lead time |
|---|---|---|---|---|---|---|---|
| 1 | Application Form (Instr. item 1; §1003-4.2) | The 7-page city form (DocumentCenter/View/193): applicant, owners, property, proposed development, attachments list; typed or black ink | `docs/01-application-form-data.md` — every field with its entry and basis (case RZ-2026-__ left blank) | Owner (applicant) transcribes; attorney reviews the two-status rider (owner of 033/015 + contract purchaser of 014/162) | READY DRAFT — owner-status rider VERIFY (executed contract for 014/162) | $0 | 1 day to transcribe |
| 2 | Application Fee (Instr. item 2; §1003-4.1) | Non-refundable fee; 5.0–9.9 ac Rezoning = **$1,250** (FY25-26 schedule) | Amount and payee stated in `docs/01-application-form-data.md` | Owner — check payable to "City of Lilburn" | READY DRAFT | $1,250 | At filing |
| 3 | Standards Governing Exercise of the Zoning Power (Instr. item 3; §1003-7 criteria A–F) | The form's six rezoning criteria; two lines each on the form, answers attached | `docs/04-standards-governing-zoning-power.md` — criteria (A)–(F), 150–300 words each, "See attached" on the form | Owner; attorney review recommended (form cites the 2011 Resolution/§1003-8 — legacy citation noted) | READY DRAFT | in attorney allowance | Done; 1 wk attorney review |
| 4 | Conflict of Interest Form (Instr. item 4; O.C.G.A. §36-67A-3) | Campaign-contribution / gift disclosure ($250+ to any Lilburn official in the prior 2 years) and certification; **due within 10 days of filing** ({fs(A['coi_due'])} if filed {fs(A['file'])}; {fs(B['coi_due'])} if filed {fs(B['file'])}) | `docs/07-conflict-of-interest-and-certifications.md` §1–2 (content; declarations left to the signer) | Owner/applicant signs; attorney co-signs if representing (§36-67A-1(1) makes the attorney an "applicant") | NEEDS SIGNATURE — contribution history is a fact only the signer can declare (VERIFY) | $0 | Same day as filing |
| 5 | Notarized Signatures (Instr. item 5; §1003-4.2) | Applicant certification + property-owner certification for **each** owner of record: Awad (033, 015); Mendez and Roblero de Leon (014, 162) — "an attachment, if multiple owners" | `docs/07-conflict-of-interest-and-certifications.md` §3–6 (who signs for which parcel; signing schedule; cooperation covenant) | Owners + applicant before a Georgia notary; attorney prepares the consent/contract | NEEDS SIGNATURE — VERIFY the 014/162 owners' written consent or executed contract (§1003-2) | notary nominal (VERIFY) | 1 sitting; schedule the Mendez/Roblero signing in week 3 |
| 6 | Letter of Intent (Instr. item 6; §1003-4.5) | Describes the request and its justification; **must state whether any buffer reduction is requested**; lists voluntary conditions | `docs/03-letter-of-intent.md` (states "No buffer reduction is requested"; 18 voluntary conditions verbatim from `data/voluntary-conditions.md`; dated 2026-09-__) | Owner signs; attorney review of conditions and HOPA language | READY DRAFT — attorney review; phone/email/contract-status brackets VERIFY | in attorney allowance | 1 wk review |
| 7 | Legal Description (Instr. item 7; §1003-4.3) | Typed metes-and-bounds description of **only** the property to be rezoned | `docs/05-legal-description-DRAFT.md` — GIS-fabric metes and bounds with per-segment bearings/distances (`tools/legal.py`, `verify/legal-output.md`); marked DRAFT | **Georgia RLS** — the sealed survey description replaces the draft | NEEDS PROFESSIONAL | in survey allowance | 3–6 wks (with item 9) |
| 8 | Site Plan (Instr. item 8; §1003-4.6) | One full-size scaled copy + PDF to returner@cityoflilburn.com; property lines, streets/R/W, buffers, setbacks, buildings, driveways, parking, lots, floodplain, adjoining zoning/owners, existing/proposed topography, landscaping, drainage/ponds | `drawings/mcp-sheet.svg` / `.png` (engineering scale, 1 unit = 1 ft), `drawings/mcp-front.png`, `drawings/mcp-rear.png`, `drawings/mcp-web.svg`; data in `data/layout.json` ({LOTS} lots, lane {M['lane_length_ft']:,.0f} ft, open space {OS_PCT}% of deeded area, impervious {IMP_PCT}% of GIS area, ponds {M['ponds_cf'][0]:,} / {M['ponds_cf'][1]:,} cf) | **Georgia PE** (civil) re-draws on the RLS base and seals; landscape architect for the planting/buffer plan (may follow at §1106 site & design review — VERIFY) | NEEDS PROFESSIONAL — generator v2 (entrance at v ≈ −190) still pending; existing-topo source is USGS 3DEP (approx.) | $8,000–25,000 | 2–4 wks after the survey |
| 9 | Boundary Survey (Instr. item 9; §1003-4.4) | Survey plat sealed by a registered land surveyor; may be combined with the site plan if the plan carries the survey information. §1003-4.4 lets the Director accept a Tax Assessor map "where no survey is available" — **do not rely on it** (FACTS §3) | None — the package has no survey; `data/site-parcels-2240.json` holds the GIS rings the RLS can start from | **Georgia RLS** (boundary, acreage, 236–246-ft width check, sewer inverts, stream top of bank, sight distance) | NEEDS PROFESSIONAL — the width decides the 50 × 100-ft lot section vs the 50 × 82-ft fallback | $8,000–18,000 | **3–6 wks — the critical-path item** |
| 10 | List of Adjoining Property Owners (Instr. item 10; §1003-6.3 mailing) | Names and mailing addresses of all adjoining owners from the Tax Assessor; the City mails hearing letters to them | `docs/06-adjoining-property-owners.md` — 32 parcels (King David Manor, Legends at Parkview, Nantucket, 4531 Arcado) from the 2026 ownership file (`tools/adjoiners.py`, `verify/adjoiners-output.md`) | Owner — re-run the extract on the filing date | READY DRAFT — re-pull at filing (VERIFY no ownership changes) | $0 | 1 hour |
| 11 | Architectural Renderings and Elevations (Instr. item 11) | Each street-visible side of each structure (two house plans, clubhouse, mail kiosk, entry sign) to scale or proper perspective; colors and materials of walls and roofing; wall-sign location/size (none proposed; monument sign ≤ 32 sf) | `docs/12-outline-specifications.md` (materials, colors, roof pitches); concept plans `public/cottages/plan-a.svg`, `plan-b.svg` and AI concept images in `public/cottages/` (illustrative, not to scale); `renderings/` in this package is empty | **Architect** — scaled elevations of Plan A "The Springbrook" (38'-0" × 38'-0") and Plan B "The Laurel" (40'-0" × 40'-0"), the ≈2,400-SF clubhouse and the sign | NEEDS PROFESSIONAL | $3,000–15,000 | 2–4 wks |
| 12 | Development Summary (voluntary; §1003-4.6 "other information as reasonably required by the Director") | Site data report in the §736 order so staff sees the same content as in 2025 | `docs/02-development-summary.md` (`tools/dev_summary_calcs.py` → `data/dev-summary-derived.json`) | Owner; PE confirms the engineering figures | READY DRAFT | $0 | Done |
| 13 | Technical memoranda (voluntary — support for §1003-7(4) "burdensome use of streets, utilities, schools") | Traffic (ITE 11th ed. LUC 251: {PM} PM peak trips), sewer gravity/route, water, stormwater, fire (IFC 2024 (GA) App. D103.4 / D107.1), schools, environmental screen | `docs/08-technical-memoranda.md` memos A–G | **Georgia PE** supersedes A–E; GCPS and GA EPD correspondence supersede F–G | READY DRAFT (feasibility screens only) | in PE allowance | With item 8 |
| 14 | Voluntary zoning conditions (§1003-4.5 "special conditions voluntarily made") | 18 conditions: use, {LOTS}-unit cap, 55+ HOPA, 1 story/24-ft ridge, ≥1,400 SF, garages, materials, 20-ft buffer (no reduction), stream buffers, stormwater, single entrance, NFPA 13D, private lane/HOA, accessibility, sewer, sign/lighting, construction practices, phasing | `data/voluntary-conditions.md` (verbatim in the LOI) | Owner offers; attorney reviews enforceability (HOPA covenant recorded before the first permit) | READY DRAFT — attorney review | in attorney allowance | 1 wk |
| 15 | **Sewer capacity certification** (practical extra; Gwinnett DWR form Rev. 07/2023; condition 16) | DWR's written confirmation that the receiving system can accept {der['total_adf_gpd']:,} gpd ADF (43 DU × 300 gpd — VERIFY DWR unit flow): Phase 1 by gravity to the on-site MH (inv. 927.13 at u ≈ 272, v ≈ −224 per GIS); Phase 2 by lift station/grinders or a ≈{M['sewer_ext_offsite_ft']:.0f}-ft off-site tie to the Legends at Parkview main (inv. 919.58) | `docs/08-technical-memoranda.md` Memo B (B.6 lists the request steps); `docs/02-development-summary.md` §4; 2025 request `status/rz-2025-01/4819_sewer-capacity-request.pdf` (stale) | **Georgia PE** signs the request; Gwinnett DWR issues the certification | NEEDS PROFESSIONAL — inverts are GIS attributes until surveyed (VERIFY) | DWR fee VERIFY; PE time in item 8 | Submit week 1–2; DWR turnaround VERIFY |
| 16 | **DOT access coordination** (practical extra; condition 12) | Gwinnett DOT (Arcado Rd is county-maintained): entrance location in the SW third of the frontage (v ≈ −190, ≥ 250 ft from the Arcadia Pl centerline at v ≈ +61), ≈390-ft intersection sight distance, access spacing (≈244 ft — VERIFY UDO), left-turn-lane warrant (44 lots < 75 — VERIFY), TIS threshold | `docs/08-technical-memoranda.md` Memo A; `docs/11-site-context-brief.md` (entrance alignment); layout v1 throat at v −117 to be moved in v2 | **Georgia PE** requests the pre-application determination; RLS measures sight distance | VERIFY — written DOT determination on TIS and turn lane; driveway permit is an LDP-stage item | $0 now (TIS $6–15k only if required) | 2–3 wks for a written response (VERIFY) |
| 17 | **School letter** (practical extra; §1003-7(4)) | GCPS planning's projection of students from the development (the 2025 letter, "Prepared for City of Lilburn, July 2025", projected +57 students for 104 condos); a HOPA 55+ community generates 0 | `docs/08-technical-memoranda.md` Memo F; `docs/02-development-summary.md` §7; 2025 letter `status/rz-2025-01/4817_school-impact-analysis.pdf` | City requests from GCPS after filing; owner asks the Director at pre-app to request it early | VERIFY — who requests it and when; the HOPA covenant's minor-occupancy clause (attorney) | $0 expected (VERIFY) | 2–4 wks after the City's request (VERIFY) |
| 18 | **Community record** (practical extra; supports §1003-7(1) and the hearing) | Evidence that neighbors were informed: public site (arcado-springs.vercel.app) updated from the 2025 MU concept to this proposal, comment-board log, neighbor-meeting notices and sign-in sheets for King David Manor / Legends at Parkview / Nantucket, sign photographs, tear sheets | `docs/03-letter-of-intent.md` §"community" (commitment to meet before the PC hearing); `public/cottages.html` (unlisted concept study); this document §2 (notice audit) | Owner | VERIFY — public-site update not yet made; meeting dates to set | printing/postage nominal | Weeks 5–8 |
| 19 | Concurrent variance (§1005) — **fallback only** | Lot-depth variance to 82 ft if staff requires the 20-ft buffer in a separate tract instead of the §313(1) easement-in-lot basis (criteria §1005-3.2 a–g: exceptional narrowness) | Not drafted — the design basis avoids it (`FACTS.md` §3) | Owner/attorney; fee per schedule (VERIFY) | VERIFY at pre-app (Q2 below) — draft only if staff rejects §313(1) | VERIFY | Same cycle as the rezoning if needed |

**Package files not on the city's list but part of the record:** `FACTS.md` (basis of everything), `docs/11-site-context-brief.md` (site context), `verify/` outputs, `tools/` generators. Nothing in this package is sealed; every drawing and description carries the DRAFT label required by the house rules.

---

## 2. Filing calendar and legal-notice audit

### 2.1 Two cycles (Instructions p. 2 hearing schedule; §1003-6 windows computed)

| Milestone | Cycle A (target) | Cycle B (fallback) | Rule |
|---|---|---|---|
| Pre-application conference with the Planning Director (Reid Turner, 770-279-3715, returner@cityoflilburn.com) | by {f(A['preapp_by'])} — request it the week of {fs(W1)} | by {f(B['preapp_by'])} | Instructions p. 1: "one week prior to submittal is highly recommended" |
| **Filing deadline** (340 Main St; fee $1,250; 1 full-size site plan + 5 reductions; PDF by email) | **{f(A['file'])}** | **{f(B['file'])}** | Instructions p. 2 schedule |
| Conflict-of-interest disclosure due | {f(A['coi_due'])} | {f(B['coi_due'])} | O.C.G.A. §36-67A-3(B): within 10 days of filing |
| Legal ad out (Gwinnett Daily Post, the official legal organ) | {f(A['ad'])} | {f(B['ad'])} | §1003-6.1: 15–45 days before **each** hearing; Instructions: ≥ 15 days before PC, ≥ 30 before Council |
| Letters mailed and sign posted | {f(A['notice'])} | {f(B['notice'])} | §1003-6.2/.3: sign and letters 15–45 days before the hearing |
| **Planning Commission public hearing** (7:30 PM, 340 Main St; work session 7:00 PM) | **{f(A['pc'])}** | **{f(B['pc'])}** — Thanksgiving Day; the schedule marks it "*subject to change — special called meetings are common" (VERIFY the actual date) | 4th Thursday |
| **City Council public hearing** (7:30 PM; work session 6:30 PM) | **{f(A['cc'])}** | **{f(B['cc'])}** | 2nd Monday |
| Last day to withdraw | the day before the Council legal ad ({fs(A['ad'])} covers both hearings — effectively **before {fs(A['ad'])}**) | before {fs(B['ad'])} | §1003-10: no withdrawal after the Council hearing is advertised; no fee refund once scheduled |
| Day counts (computed) | ad → PC **{A['ad_to_pc']} days**; ad → Council **{A['ad_to_cc']} days**; sign/letters → PC **{A['notice_to_pc']} days** (the bare minimum); sign → Council {A['notice_to_cc']} days | ad → PC {B['ad_to_pc']}; ad → Council {B['ad_to_cc']}; sign/letters → PC **{B['notice_to_pc']} days** (bare minimum) | all inside the 15–45-day window — but **a one-day slip of the sign or letters makes the PC notice defective** |

**Which cycle?** Cycle A is reachable only if the RLS delivers the sealed survey and legal description within about 3½ weeks of a week-1 order ({fs(W1)} → ≈ {fs(W1 + dt.timedelta(days=24))}) and the 014/162 owner consent is executed by then. **Go/no-go on {f(A['file'] - dt.timedelta(days=7))}:** if either is missing, do not file on the Director's §1003-4.4 discretion — move to Cycle B ({fs(B['file'])}), which also avoids advertising a Thanksgiving-week hearing whose date may change.

### 2.2 Legal-notice audit — why and how

RZ-2025-01 was **tabled on 2025-08-28** because of "a clerical error in the legal advertisement for the public hearing via the Gwinnett Daily Post advertisement and on-site sign advertisement" (PC minutes, `status/rz-2025-01/2025-08-28_PC-minutes-item4709.pdf`); it was never heard. The City drafts and places the notice (§1003-6), but the applicant bears the delay, so audit every notice element before and after it runs:

| Step | When (Cycle A) | What to check / keep | Rule |
|---|---|---|---|
| N1. Ask the Director for the **draft ad text** before it goes to the Gwinnett Daily Post | {fs(A['file'])}–{fs(A['ad'] - dt.timedelta(days=1))} | Time, place and purpose; property location (all four addresses: 4535, 4537, 4539, 4541 Arcado Rd SW; PINs R6123 033/015/014/162; Land Lot 123, 6th District); acreage 9.44; **present zoning R-1** and **proposed zoning R-2**; both hearing dates/times; case number | §1003-6.1 lists these elements for applicant-initiated cases |
| N2. Confirm publication and **buy two tear sheets**; obtain the publisher's affidavit copy from the City | {fs(A['ad'])} | Date of issue, page, wording identical to N1; file under `verify/notice/` (create) | Instructions p. 2 item 5 (GDP is the official legal organ) |
| N3. Count days from the publication date to each hearing | {fs(A['ad'])} | PC: {A['ad_to_pc']} (must be 15–45); Council: {A['ad_to_cc']} (must be ≥ 30 and ≤ 45) | §1003-6.1; Instructions |
| N4. **Photograph the sign** the day it is posted, with a date-stamped photo showing the sign text and Arcado Rd frontage; re-photograph weekly and after storms | {fs(A['notice'])}, then weekly to {fs(A['cc'])} | Sign text: case number, both hearing dates and times, place; posted "in a conspicuous location on the property or in the public right-of-way along frontage"; replace immediately if damaged and re-photograph | §1003-6.2: 15–45 days before the hearing |
| N5. Count days from posting to the PC hearing | {fs(A['notice'])} | {A['notice_to_pc']} days — the minimum; if the sign goes up on {fs(A['notice'] + dt.timedelta(days=1))} or later, tell the Director the same day (the remedy is to re-notice for the next cycle, not to hold a defective hearing) | §1003-6.2 |
| N6. Verify the **mailing list** against `docs/06-adjoining-property-owners.md` (32 parcels) and ask for a copy of the mailed letter and the mailing date | {fs(A['notice'])} | Letters go to the owner of record and all abutting owners at the tax-record address, ≥ 15 days before PC | §1003-6.3(a)–(b) |
| N7. Check the agenda posting for the PC and Council meetings (Agenda Center) and that the case appears under the right number, address and zoning | {fs(A['pc'] - dt.timedelta(days=7))}, {fs(A['cc'] - dt.timedelta(days=7))} | Screenshot the agenda with the URL and date | Instructions p. 2 items 4 and 6 |
| N8. Attend both hearings in person (or by counsel) | {fs(A['pc'])}, {fs(A['cc'])} | "The applicant must be represented" at both | Instructions p. 2 |
| N9. Keep the whole record (N1–N8) in one folder and give the attorney a copy before each hearing | continuous | If the notice is defective and the City tables the case, no refiling bar applies (tabling is not a denial under §1003-11), but the cycle is lost | §1003-10, §1003-11 |

For Cycle B substitute: ad {fs(B['ad'])} (PC {B['ad_to_pc']} days, Council {B['ad_to_cc']} days), sign/letters {fs(B['notice'])} ({B['notice_to_pc']} days to PC), hearings {fs(B['pc'])}* and {fs(B['cc'])}.

---

## 3. Pre-application agenda — Reid Turner, Planning Director (one week before filing)

Bring: `drawings/mcp-sheet.png`, `docs/02-development-summary.md` §§1–4, `data/voluntary-conditions.md`, the 2025 PC minutes. Record the answers in `verify/preapp-notes.md` (create) and update `FACTS.md` §3 the same day.

| # | Question (precise) | Why it matters / what we propose | If the answer is unfavorable |
|---|---|---|---|
| Q1 | Table 4.1 (R-2) lists the buffer abutting R-1 as **0 ft for "detached single-family dwellings" and 20 ft for "all other allowed dwelling types."** Does staff read a fee-simple detached **cottage home** on a 50 × 100-ft lot as a detached single-family dwelling (0 ft) or as another dwelling type (20 ft)? | We design to the **20-ft** buffer and offer it as condition 8 either way; the reading decides whether the buffer is a requirement or a voluntary offer, and how the LOI's "no buffer reduction" statement is phrased | None — the plan already provides 20 ft |
| Q2 | **§313(1):** "Buffer requirements … supersede these minimum required yards." May the 20-ft buffer **coincide with the 20-ft rear yard of each perimeter lot**, held in a recorded buffer/conservation easement in favor of the HOA and the City (our design basis: 100 + 31–35 + 100 ft = 231–235 ft across a 236-ft strip)? | This is what lets 50 × 100-ft lots face each other across one lane | If staff wants the buffer in a separate tract: lots become 50 × 82 ft (4,100 SF > 3,000) with a **concurrent §1005 variance on the 100-ft lot depth** (criteria §1005-3.2 a–g: exceptional narrowness) — ask whether it can run in the same cycle and what the variance fee is |
| Q3 | Table 4.1 refers open space to **Development Regulations §5.9 (Appendix B)**, which is not online. What is the minimum common open space for an R-2 cottage subdivision, how is it measured (gross area? excluding ponds? excluding buffer easements on lots?), and does it require a recreation component? Please provide the text. | The plan shows {OS_PCT}% of the deeded area in common tracts (greens, ponds, creek woods, amenity tract) plus {M['buffer_easement_on_lots_sf']:,} SF of buffer easement on lots; we need to know which count | Re-run `tools/siteplan.py` with the confirmed rule; the pond tracts (35,000 SF) and the amenity tract (≈50,000 SF) are the swing items |
| Q4 | **Private lane standard.** The Site Development checklist says private streets must meet the minimum public-street standards. For an "approved private street" under §319, is the accepted section a **31-ft tract with 22-ft pavement, 2-ft strip and one 5-ft sidewalk** (widening to sidewalks both sides beyond u ≈ 1,160), curb and gutter, 15-mph design speed, no on-street parking? Which department reviews the lane — the City engineer or Gwinnett DOT? | The section sets the lot depth arithmetic in Q2; the checklist's 22-ft minimum is for interior drives with 90° parking | If a wider public-standard section (e.g., 24–26 ft + two sidewalks) is required in a 236-ft strip, lot depth falls below 100 ft → Q2 fallback |
| Q5 | Table 4.2 (R-2 "A"): **culs-de-sac "not permitted except in the most unusual circumstances."** With a single public frontage and no abutting street at the rear, does a 1,722-ft lane ending in **hammerhead (T) turnarounds** (20 ft wide, 60-ft legs, at u ≈ 705, 1,255 and 1,690; blocks 450 / 500 / 401 ft ≤ 600) satisfy the rule without a variance? Does the checklist's 2,000-ft cul-de-sac maximum apply to a private lane? | The strip cannot connect through (Nantucket Dr lots close the NW end) | If a circular bulb is required at the terminus, the lot count drops (≈1–3 rear lots) and the terminus green absorbs the bulb |
| Q6 | **Stream buffer.** The headwater channel terminates inside the site at (u 1,392, v −210). We keep every lot, dwelling and pond outside the **75-ft** setback (50-ft undisturbed + 25-ft impervious). Is a City buffer variance or a GA EPD variance needed for (a) the lane crossing nothing, (b) Pond 2 outside the 75-ft line, (c) the second branch's 50-ft buffer clipping the SW edge by ≤ 12 ft at u ≈ 868–1,038? Who delineates top of bank for the City? | Condition 10 promises field delineation and no encroachment | If a lot at u ≈ 1,300–1,470 falls inside the delineated buffer it is removed (yield range 40–47 allows it) |
| Q7 | **Sewer route and the 2026 Comprehensive Plan Amendment policy "Do not further extend sewer in this area."** Phase 1 uses the existing 8-in main on the property (no extension). For Phase 2, is an **in-tract lift station or grinder pumps** (no off-site line) the reading staff prefers, or is a ≈{M['sewer_ext_offsite_ft']:.0f}-ft tie to the Legends at Parkview main through an easement acceptable? Has the Amendment been adopted (June 2026 draft; PC closeout 6/25/2026 — VERIFY)? | Condition 16 leaves the Phase 2 method to DWR and the City; the LOI must not contradict an adopted policy | Present the lift-station option as primary in the LOI; keep the extension as the alternative |
| Q8 | **HOPA 55+ as a zoning condition.** Will the City accept and enforce a condition that the community operate as housing for older persons under 42 U.S.C. §3607(b)(2)(C) / 24 CFR §100.300–.308 (≥ 80% of occupied units with a resident 55+, recorded declaration before the first building permit)? Does staff want the declaration text with the application, and does the 0-student school finding depend on it? | Condition 3 is the basis for the traffic (LUC 251) and school (0 students) findings | If the City will not enforce an age condition, the covenant still binds the HOA; traffic would be re-stated at LUC 210 (40 PM trips for 43 SFD) and the school letter would count students |
| Q9 | **Fire marshal referral.** Will the City refer the plan to the Gwinnett County Fire Marshal at the rezoning stage, or only at LDP? We propose NFPA 13D sprinklers in every home (condition 13), a 22-ft clear lane with no parking, and hammerheads ≤ 750 ft apart as mitigation for a 1,722-ft dead-end road under **IFC 2024 (GA) App. D103.4** (special approval > 750 ft) and **D107.1** (two access roads > 30 units unless sprinklered). Can we get the Fire Marshal's concurrence letter before the PC hearing? | A written concurrence removes the largest technical objection at the hearing | If a second access is demanded, no abutting street exists — document the impossibility and the sprinkler exception |
| Q10 | **Disposition of RZ-2025-01 and the §1003-11 bar.** Please confirm in writing that RZ-2025-01 (R-1 → MU) was **tabled** on 2025-08-28 for a defective legal ad, was never heard, and was **not denied**, so the 12-month refiling bar does not apply; and whether it should be formally withdrawn under §1003-10 before this application is accepted. Will the 2025 file (Agenda item 4643) be referenced in the new staff report? | A denial would bar filing until 12 months after the denial date; a dormant application could be treated as pending | If staff deems it pending, withdraw it in writing before filing (permitted until the Council ad — none ever ran for Council) |

Also ask at the same meeting (not counted among the ten): the Development Regulations text for sidewalks/landscape strip on a collector; whether the City requests the GCPS letter and the DWR certification itself; the current sign-fee/notice-fee, if any (VERIFY); and whether the Director wants the site plan PDF before the filing date for a completeness check.

---

## 4. What changed versus the 2025 filing (RZ-2025-01)

| Topic | RZ-2025-01 (filed July 2025; tabled 2025-08-28) | This application (2026) | Source |
|---|---|---|---|
| Program | "Arcado Springs Mixed-Use Community": 104 condominium units (~1,700 SF each) + 13 commercial buildings, 24,400 SF retail/service/office | **{LOTS} one-story detached cottage homes** on fee-simple 50'-0" × 100'-0" lots (Plan A 1,444 SF / Plan B 1,600 SF conditioned), 55+ HOPA, clubhouse ≈2,400 SF, 2 pickleball courts; **no commercial** | `4814_development-summary-report.pdf`; `FACTS.md` §4 |
| Zoning requested | R-1 → **MU** (Mixed-Use, §736) | R-1 → **R-2** (§402); use "Single-family (cluster-cottage, creative lot configuration)" = **P** in §602 (no SUP) | ordinance excerpts |
| Comprehensive Plan | MU on an "Established Residential" parcel; 2026 draft FDM "Suburban-Low" lists Mixed Use, Multifamily, Retail as **Not Appropriate** | Single-family cottages / single-family = **Appropriate** in Suburban-Low; Established Residential → R-1, R-2 per §203 | 2026 CPA draft p. 73; 2024 plan p. 37 |
| Acreage | "Approximately 9.00-acre" total (the typed legal description's stated acreage, ±) | **9.44 ac deeded** (0.99 + 2.00 + 2.00 + 4.45); 9.58 ac by GIS; RLS survey governs | Gwinnett digest; `FACTS.md` §1 |
| Legal description | Narrative: "extends eastward for approximately 1,250 linear feet"; sides labeled north = Village Green Ct, south = King David Dr; no bearings or distances; "metes-and-bounds survey … attached" (none sealed) | GIS-derived **metes and bounds with per-segment bearings and distances** (strip runs N 28°43' W, ≈1,722–1,757 ft deep, 236–246 ft wide; King David Manor on the **NE**, Legends at Parkview on the **SW**) — DRAFT until the RLS seals | `4818_legal-description_9.00ac.pdf`; `docs/05-legal-description-DRAFT.md` |
| Site plan basis | MCP dated 8/17/2025 on an unsealed boundary; program failed the Table 4.6 MU mix as drawn | Generator on the GIS parcel fabric in surveyable local coordinates (1 unit = 1 ft); every lot tested for boundary, buffer, stream setback, frontage ≥ 30 ft, ≥ 3,000 SF / ≥ 50 ft; to be re-drawn on the RLS base and sealed by a PE | `4813_master-concept-plan.pdf`; `data/layout.json` status list |
| Use mix | Residential + retail/service/office; bike lanes; park-to-park easements | Residential only; greens, creek woods, ponds, amenity tract = {OS_PCT}% common open space of deeded area | `dev-summary-derived.json` |
| Density | 104 DU / 9.44 ac ≈ 11.0 du/ac (MU) | **{DENS} du/ac** on 9.44 ac ({M['density_du_ac_gis']} on GIS acreage) vs R-2 max 8 and R-1's 4 | `layout.json` metrics |
| Buffers | Not stated in the LOI | **20-ft undisturbed buffer, no reduction requested**, in a recorded easement (§313(1)); 50/75-ft stream buffers preserved | `data/voluntary-conditions.md` 8–10 |
| Traffic | No TIS filed; order-of-magnitude ≈ 1,800 daily / 96 AM / 201 PM (LUC 221 + 822 — VERIFY) | ITE 11th ed. **LUC 251**: {der['trips_proposed_251']['daily']} daily / {der['trips_proposed_251']['am']} AM / **{PM} PM** — below the 21-trip Gwinnett DOT Level-2 threshold (VERIFY); ≈6% of the 2025 concept | `docs/08-technical-memoranda.md` Memo A |
| Schools | GCPS letter (July 2025): **+57 students** (Camp Creek ES +25, Trickum MS +13, Parkview HS +19) into a cluster with two over-capacity schools | **0 students** (HOPA covenant); request a fresh GCPS letter | `4817_school-impact-analysis.pdf`; Memo F |
| Impervious / stormwater | Hydro sheet: 235,388 SF impervious (55.4%), 3 basins, 74,167 cf detention by the 10,000-cf/ac rule | {M['impervious_sf']:,} SF ({IMP_PCT}% of GIS area) — **−{der['impervious_reduction_vs_2025_pct']:.0f}%**; 2 dry ponds ≈{der['ponds_cf_drawn_total']:,} cf drawn; PE GCSWMM routing governs | `docs/02-development-summary.md` §5 |
| Sewer | Capacity request filed 2025 (stale-dated) | Phase 1 gravity to the existing on-site main (no extension); Phase 2 lift station/grinders or ≈{M['sewer_ext_offsite_ft']:.0f}-ft tie — DWR certification to be re-requested | Memo B |
| Conditions offered | None recorded in the LOI | 18 voluntary conditions incl. 55+ HOPA, 43-unit cap, 1 story, NFPA 13D | `data/voluntary-conditions.md` |
| Notice / process | Tabled for a defective GDP ad and sign; never heard; no denial → no §1003-11 bar (VERIFY in writing) | Notice audit N1–N9 (§2.2); attend both hearings; no withdrawal after the Council ad | PC minutes 2025-08-28 |

---

## 5. Budget roll-up and 12-week critical path

### 5.1 Budget (planning allowances — VERIFY each with a quote)

| Line | Low | High | Lead time | Note |
|---|---|---|---|---|
""" + "\n".join(f"| {b[0]} | {usd(b[1])} | {usd(b[2])} | {b[3]} | {b[4]} |" for b in budget) + f"""
| **Total of priced lines** | **{usd(low)}** | **{usd(high)}** | | Low = survey/PE/renderings at the bottom of their ranges, no TIS; high = every line at the top, TIS required, full attorney representation |

Not priced (excluded from the totals — VERIFY): """ + "; ".join(f"{e[0]} ({e[1]})" for e in excluded) + f""".

Basis: application fee from the FY25-26 fee schedule (5.0–9.9 ac = $1,250); all other ranges are the allowances in the 2026-08-29 roadmap brief, not quotes. Later-stage costs (§1106 site & design review, LDP at $40/disturbed ac + NPDES $80/ac, DOT driveway permit, geotechnical rock probes at the ARE pond sites, tree survey/TDU calculation, construction documents) are outside this rezoning budget.

### 5.2 Twelve-week critical path (week 1 = Monday {fs(W1)}; Cycle A with the Cycle-B branch)

| Wk | Dates | Tasks | Owner | Gate / deliverable |
|---|---|---|---|---|
| 1 | {wk(1)} | Order the **RLS survey** (boundary, acreage, 236–246-ft width at every lot row, sewer inverts at the u ≈ 272 and Legends manholes, stream top of bank, Arcado Rd sight distance) — the 3–6-week clock starts here. Engage the attorney (014/162 contract or written consent; HOPA covenant outline). Request the pre-app date. Brief the PE (MCP seal scope, DWR capacity request) and the architect (elevations of Plans A/B, clubhouse, sign). Freeze layout v2 (entrance at v ≈ −190). | Owner | Signed RLS proposal with a delivery date; pre-app booked |
| 2 | {wk(2)} | (Labor Day {fs(D(2026,9,7))}.) **Pre-application conference** — the ten questions of §3; record answers in `verify/preapp-notes.md`; update `FACTS.md`. PE submits the DWR sewer capacity request; PE/RLS request the DOT access determination. Attorney reviews the LOI, conditions and criteria responses. Ask the Director to request the GCPS letter. | Owner, PE, attorney | Pre-app notes; DWR and DOT requests logged |
| 3 | {wk(3)} | Survey fieldwork complete (fast case). Re-run `tools/siteplan.py` on the survey rings and the pre-app answers; PE drafts the sealed MCP; architect delivers elevations. Schedule the notary sitting with the Mendez/Roblero owners. | RLS, PE, architect | Draft sealed MCP; elevations |
| 4 | {wk(4)} | **Go/no-go {fs(A['file'] - dt.timedelta(days=7))}**: sealed survey + legal description in hand, 014/162 consent executed, MCP sealed, elevations done → assemble the package (items 1–14), notarize (4 certifications), re-pull the adjoining-owner list, print 1 full-size + 5 reductions, email the PDF. **File {f(A['file'])}.** | Owner | Filed application, receipt, case number |
| 5 | {wk(5)} | N1 review the draft ad text before {fs(A['ad'])}; N2–N3 tear sheets and day counts on {fs(A['ad'])}. Update the public website to the cottage proposal. Set neighbor-meeting dates. | Owner, attorney | Notice folder started |
| 6 | {wk(6)} | **Conflict-of-interest disclosure by {fs(A['coi_due'])}.** N4–N6 on {fs(A['notice'])}: photograph the sign, verify the mailing list, count {A['notice_to_pc']} days. Neighbor meeting 1 (King David Manor). Follow up DWR and DOT responses. | Owner | COI filed; sign photo; mailing confirmation |
| 7 | {wk(7)} | Staff report questions — answer within 48 hours; deliver the Fire Marshal concurrence request; neighbor meeting 2 (Legends at Parkview, Nantucket). N7 agenda check. Weekly sign photo. | Owner, PE | Responses to staff; meeting sign-in sheets |
| 8 | {wk(8)} | PC work session 7:00 PM and **Planning Commission hearing {f(A['pc'])} 7:30 PM** — applicant present with counsel; present conditions, traffic ({PM} PM trips), schools (0), buffer (20 ft, no reduction), sewer (existing main). | Owner, attorney | PC recommendation |
| 9 | {wk(9)} | Revise conditions/plan per the PC recommendation (no unit-count increase). **Cycle-B branch:** if the go/no-go failed in week 4, this is the **{f(B['file'])} filing** with the completed survey (6-week case delivers ≈ {fs(W1 + dt.timedelta(days=41))}). | Owner, PE | Revised condition set; or Cycle-B filing |
| 10 | {wk(10)} | Council work-session materials; re-photograph the sign (still ≥ 15 days before Council — posted {fs(A['notice'])} = {A['notice_to_cc']} days). Cycle B: N1–N3 on {fs(B['ad'])}. | Owner | Council packet |
| 11 | {wk(11)} | **City Council hearing {f(A['cc'])} 7:30 PM** — decision. Cycle B: COI by {fs(B['coi_due'])}; N4–N6 on {fs(B['notice'])} ({B['notice_to_pc']} days to the PC). | Owner, attorney | Ordinance / conditions of approval |
| 12 | {wk(12)} | Record the conditions; order the LDP-stage work (geotechnical rock probes at both pond sites, tree survey, stream delineation if not in the survey, DWR route design); brief the HOA/HOPA covenant drafting. Cycle B: PC {fs(B['pc'])}* → Council {fs(B['cc'])} (weeks 13–15). | Owner | Post-approval task list |

**Critical path:** RLS survey (3–6 wks) → PE re-draw and seal (2–4 wks) → filing. At the fast end (3 + ½ wk) Cycle A holds; at the slow end (6 + 2 wks) only Cycle B does. Everything else (attorney, architect, DWR, DOT, GCPS) runs in parallel and is not on the path unless the DOT determination requires a TIS (3–5 wks), which would also push to Cycle B.

**Statements of consistency in this document are preliminary:** each "appears consistent with" finding in the package rests on GIS geometry, USGS topography and ordinance excerpts, and is to be confirmed by the sealed survey, the PE's plan and the Planning Director's answers at the pre-application conference.

> **Disclaimer:** This is an AI-generated analysis for preliminary planning purposes. All findings must be verified by a licensed professional before use in design, permitting, or regulatory submissions.

<!-- architecture-studio:requires-disclaimer -->
"""

OUT.write_text(doc)

# ---- self-checks ----
DISCLAIMER = ("> **Disclaimer:** This is an AI-generated analysis for preliminary planning purposes. "
              "All findings must be verified by a licensed professional before use in design, permitting, or regulatory submissions.")
MARKER = "<!-- architecture-studio:requires-disclaimer -->"
t = OUT.read_text(); lines = t.rstrip("\n").split("\n"); fails = []
def check(c, m):
    if not c: fails.append(m)
check(lines[-1] == MARKER, "last line is not the marker")
check(lines[-2] == "", "no blank line before marker")
check(lines[-3] == DISCLAIMER, "disclaimer block is not third-to-last")
for bad in [r"\bcompl(y|ies|iance|iant)\b", r"IFC 2018", r"329[- ]f", r"1,250 ft", r"9\.00 ac"]:
    for m in re.finditer(bad, t, re.I):
        fails.append(f"banned phrase {bad!r}: ...{t[max(0,m.start()-40):m.end()+20]!r}")
check("appears consistent" in t, "missing 'appears consistent' phrasing")
check("VERIFY" in t, "no VERIFY flags")
# all 11 instruction items named
for i, key in enumerate(["Application Form", "Application Fee", "Standards Governing Exercise of the Zoning Power", "Conflict of Interest Form",
                         "Notarized Signatures", "Letter of Intent", "Legal Description", "Site Plan", "Boundary Survey",
                         "List of Adjoining Property Owners", "Architectural Renderings and Elevations"], 1):
    check(f"| {i} | {key} (Instr. item {i}" in t, f"instruction item {i} ({key}) row missing")
for extra in ["Sewer capacity certification", "DOT access coordination", "School letter", "Community record"]:
    check(f"**{extra}**" in t, f"practical extra {extra!r} missing")
for s in ["§1003-4.1", "§1003-4.2", "§1003-4.3", "§1003-4.4", "§1003-4.5", "§1003-4.6"]:
    check(s in t, f"{s} not cited")
# ten pre-app questions
qs = re.findall(r"^\| Q(\d+) \|", t, re.M)
check(qs == [str(i) for i in range(1, 11)], f"pre-app questions found: {qs}")
for kw in ["§313(1)", "§5.9", "hammerhead", "Stream buffer", "Sewer route", "HOPA", "Fire marshal", "RZ-2025-01", "12-month", "Private lane"]:
    check(kw.lower() in t.lower(), f"pre-app keyword {kw!r} missing")
# what-changed rows
for row in ["Program", "Acreage", "Legal description", "Site plan basis", "Use mix", "Density", "Traffic", "Schools"]:
    check(f"| {row} |" in t, f"what-changed row {row!r} missing")
# calendar facts
for s in ["09/25/2026", "10/22/2026", "11/09/2026", "10/30/2026", "11/26/2026", "12/14/2026", "tear sheet", "hotograph the sign"]:
    check(s in t, f"calendar/notice token {s!r} missing")
# budget arithmetic and 12 weeks
check(usd(low) in t and usd(high) in t, "budget totals not printed")
check(low == 27750 and high == 99250, f"budget totals unexpected: {low} {high}")
wks = re.findall(r"^\| (\d+) \| \d\d/\d\d–\d\d/\d\d \|", t, re.M)
check(wks == [str(i) for i in range(1, 13)], f"critical-path weeks found: {wks}")
check(f"{LOTS} one-story" in t and str(DENS) in t, "lots/density not stated")
# every regulatory citation carries an edition
check("IFC 2024 (GA)" in t and "ITE 11th ed." in t and "2023-603" in t, "edition-bearing citations missing")
print(f"wrote {OUT.relative_to(ROOT)}: {len(lines)} lines; lots={LOTS} density={DENS}; budget {usd(low)}–{usd(high)}")
print("Cycle A:", {k: (v.isoformat() if isinstance(v, dt.date) else v) for k, v in A.items()})
print("Cycle B:", {k: (v.isoformat() if isinstance(v, dt.date) else v) for k, v in B.items()})
if fails:
    print("FAIL"); [print(" -", x) for x in fails]; sys.exit(1)
print("PASS: all checks")
