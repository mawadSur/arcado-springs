#!/usr/bin/env python3
"""adjoiners.py — adjoining-owner list (Lilburn application item 10), ordered by side and by
position along the site (front → rear), from
  data/owners-found.json          Gwinnett Tax Assessor 2026 ownership file (retrieved 2026-08-28)
  data/site-context-local.json    adjoining parcel rings in site-local (u, v) feet
Prints a markdown table per side plus the corner adjoiners (used by docs/05 and docs/06).
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OWN = json.load(open(os.path.join(ROOT, "data", "owners-found.json")))
CTX = json.load(open(os.path.join(ROOT, "data", "site-context-local.json")))
SITE = {"6123 033", "6123 015", "6123 014", "6123 162"}

STREET_NAMES = {"ARCADO RD": "Arcado Rd SW", "KING DAVID DR": "King David Dr SW", "NANTUCKET DR": "Nantucket Dr SW",
                "VILLAGE GREEN CT": "Village Green Ct SW", "FIELDHOUSE CIR": "Fieldhouse Cir SW"}


def side_of(ring):
    """Classify by where the ring sits relative to the strip: NE (v>0), SW (v<-230), NW (u>1700)."""
    us = [p[0] for p in ring]
    vs = [p[1] for p in ring]
    if min(vs) > -50:
        return "NE"
    if max(vs) < -150 and max(us) < 1760:
        return "SW"
    return "NW"


def touch_extent(ring, side):
    """u-range (or v-range for the NW end) of the vertices lying on/near the common line."""
    if side == "NE":
        pts = [p for p in ring if -15 < p[1] < 25]
        key = 0
    elif side == "SW":
        pts = [p for p in ring if -255 < p[1] < -220]
        key = 0
    else:
        pts = [p for p in ring if p[0] > 1705]
        key = 1
    if not pts:
        pts = ring
    vals = sorted(p[key] for p in pts)
    return vals[0], vals[-1]


def title(s):
    return " ".join(w.capitalize() if w.isalpha() else w for w in s.split()) if s else ""


def owner_line(rec):
    names = [rec["OWNERNAME1"]]
    if rec.get("OWNERNAME2"):
        names.append(rec["OWNERNAME2"])
    return " & ".join(names)


def mailing(rec):
    return f"{rec['OWNERADDRESS1']}, {rec['OWNERCITY']}, {rec['OWNERSTATE']} {rec['OWNERZIP']}"


def prop_address(rec):
    st = rec["PROPERTYSTREET"]
    num, _, name = st.partition(" ")
    return f"{num} {STREET_NAMES.get(name, title(name))}, Lilburn, GA {rec['PROPERTYZip']}"


def build():
    rows = []
    for ap in CTX["adjoining_parcels"]:
        pin = ap["PIN"]
        if pin == "R/W" or pin in SITE:
            continue
        ring = ap["ring_local"]
        side = side_of(ring)
        lo, hi = touch_extent(ring, side)
        rec = OWN[pin][0]
        rows.append({"pin": pin, "side": side, "lo": lo, "hi": hi, "rec": rec,
                     "address": prop_address(rec), "owner": owner_line(rec), "mail": mailing(rec),
                     "legal": rec["LEGAL1"], "ac": rec["LEGALAC"], "zoning": rec["ZONEDESC"]})
    # NE and SW ordered front → rear by u; NW ordered SW → NE by v
    rows.sort(key=lambda r: ({"NE": 0, "NW": 1, "SW": 2}[r["side"]], r["lo"]))
    return rows


def report(rows):
    out = []
    n = 0
    for side, label in (("NE", "Northeasterly line (King David Manor side), front → rear"),
                        ("NW", "Northwesterly end (Nantucket), SW → NE"),
                        ("SW", "Southwesterly line (Legends at Parkview side), front → rear")):
        out.append(f"### {label}")
        out.append("")
        out.append("| # | PIN | Property address | Owner(s) of record | Mailing address | Frontage on site (local ft) | Digest ac |")
        out.append("|---:|---|---|---|---|---|---:|")
        for r in rows:
            if r["side"] != side:
                continue
            n += 1
            lo, hi = (0.0 if abs(r['lo']) < 0.5 else r['lo']), (0.0 if abs(r['hi']) < 0.5 else r['hi'])
            ext = (f"u {lo:.0f} to {hi:.0f}" if side != "NW" else f"v {lo:.0f} to {hi:.0f}")
            out.append(f"| {n} | R{r['pin']} | {r['address']} | {r['owner']} | {r['mail']} | {ext} | {r['ac']} |")
        out.append("")
    out.append(f"Adjoining parcels listed: {n}")
    zon = {r["zoning"] for r in rows}
    out.append(f"Zoning of all adjoiners (2026 digest ZONEDESC): {', '.join(sorted(zon))}")
    return "\n".join(out)


def corners(rows):
    ne = [r for r in rows if r["side"] == "NE"]
    sw = [r for r in rows if r["side"] == "SW"]
    nw = [r for r in rows if r["side"] == "NW"]
    return {
        "NE_front": ne[0], "NE_rear": ne[-1],
        "SW_front": sw[0], "SW_rear": sw[-1],
        "NW_sw": nw[0], "NW_ne": nw[-1],
    }


if __name__ == "__main__":
    rows = build()
    print(report(rows))
    print()
    print("CORNERS")
    for k, r in corners(rows).items():
        print(f" - {k}: R{r['pin']} {r['address']} ({r['legal']}) {r['owner']}")
    assert len(rows) == 31, len(rows)   # 31 parcels + the Arcado Rd R/W = 32 adjoiners
    missing = [r["pin"] for r in rows if not r["owner"] or r["owner"] == "NOT AVAILABLE"]
    print("Owner name NOT AVAILABLE in digest:", missing)
