#!/usr/bin/env python3
"""House-rule checks for docs/03-letter-of-intent.md and docs/04-standards-governing-zoning-power.md.
Run: python3 tools/check_docs.py   (exit 1 on any failure)"""
import json, re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
DISCLAIMER = ("> **Disclaimer:** This is an AI-generated analysis for preliminary planning purposes. "
              "All findings must be verified by a licensed professional before use in design, permitting, or regulatory submissions.")
MARKER = "<!-- architecture-studio:requires-disclaimer -->"
_metrics = json.load(open(ROOT / "data/layout.json"))["metrics"]
lots = _metrics["lots"]
dens = round(lots / 9.44, 2)
# PM peak-hour trips (ITE Trip Generation 11th ed., LUC 251 at 0.30/unit) is derived from the lot count,
# so read it from the layout rather than hard-coding it — it changed with the 2026-09-03 lot-count correction.
trips = ("%g" % _metrics["pm_peak_trips_ite_251"])
# the data file carries a generated header and the canonical disclaimer; compare only the numbered list
import re as _re
_raw = (ROOT / "data/voluntary-conditions.md").read_text()
_m = _re.search(r"^1\. .*?(?=\n\n> \*\*Disclaimer|\Z)", _raw, _re.S | _re.M)
conds = (_m.group(0) if _m else _raw).strip()
fails = []
def check(cond, msg):
    if not cond: fails.append(msg)

for name in ["docs/03-letter-of-intent.md", "docs/04-standards-governing-zoning-power.md"]:
    t = (ROOT / name).read_text()
    lines = t.rstrip("\n").split("\n")
    check(lines[-1] == MARKER, f"{name}: last line is not the marker")
    check(lines[-2] == "", f"{name}: no blank line before marker")
    check(lines[-3] == DISCLAIMER, f"{name}: disclaimer block is not the third-to-last line")
    for bad in [r"\bcompl(y|ies|iance|iant)\b", r"IFC 2018", r"329[- ]f", r"1,250 ft", r"9\.00 ac"]:
        for m in re.finditer(bad, t, re.I):
            # allow 'complies' only inside a direct ordinance quotation? none expected
            fails.append(f"{name}: banned phrase {bad!r} at ...{t[max(0,m.start()-40):m.end()+20]!r}")
    check("appears consistent" in t or name.endswith("power.md"), f"{name}: missing 'appears consistent' phrasing")
    check(f"{lots} " in t and str(dens) in t, f"{name}: unit count {lots} / density {dens} not both present")
    check("VERIFY" in t, f"{name}: no VERIFY flags")
    check("2026-09-__" in t, f"{name}: date placeholder missing")

# LOI: conditions verbatim, buffer statement, contract-status bracket
loi = (ROOT / "docs/03-letter-of-intent.md").read_text()
check(conds in loi, "LOI: voluntary conditions differ from data/voluntary-conditions.md")
ds = (ROOT / "docs/02-development-summary.md")
if ds.exists():
    m = re.search(r"^## 9\. Voluntary zoning conditions.*?\n\n(.*?)\n\n---", ds.read_text(), re.S | re.M)
    check(m is not None and m.group(1).strip() in loi, "LOI: conditions drift from docs/02 §9 — run tools/sync_conditions.py")
check("No buffer reduction is requested" in loi or "no buffer reduction is requested" in loi, "LOI: buffer-reduction statement missing")
check("§313(1)" in loi, "LOI: §313(1) easement basis missing")
check("[contract status: VERIFY before filing]" in loi, "LOI: contract-status bracket missing")
for pin in ["6123 033", "6123 015", "6123 014", "6123 162"]:
    check(pin in loi, f"LOI: PIN {pin} missing")
for s in ["§602", "§402-1", "§203", "p. 37", "RZ-2025-01", "104", "24,400", trips, "Reid Turner", "340 Main Street"]:
    check(s in loi, f"LOI: expected token {s!r} missing")

# Standards: six criteria, 150-300 words each
std = (ROOT / "docs/04-standards-governing-zoning-power.md").read_text()
parts = re.split(r"^### \(([A-F])\) .*?:\s*$", std, flags=re.M)
# parts: [pre, 'A', bodyA, 'B', bodyB, ...]; last body runs to '---'
letters = parts[1::2]; bodies = parts[2::2]
check(letters == list("ABCDEF"), f"Standards: criteria found {letters}")
for L, body in zip(letters, bodies):
    body = body.split("\n---")[0]
    words = len(re.findall(r"\S+", body))
    print(f"  criterion {L}: {words} words")
    check(150 <= words <= 300, f"Standards ({L}): {words} words, outside 150-300")
for s in ["106 feet", "Zone X", "zero", "gravity", "Killian Hill", "$349,200", "$693,500", trips, "Established Residential", "Suburban-Low", "Attorney-review note"]:
    check(s in std, f"Standards: expected token {s!r} missing")

print(f"layout.json lots={lots}, density={dens}")
if fails:
    print("FAIL"); [print(" -", f) for f in fails]; sys.exit(1)
print("PASS: all checks")
