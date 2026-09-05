#!/usr/bin/env python3
"""legal.py — DRAFT metes-and-bounds courses for the Arcado Road assemblage (one tract).

Derives the OUTER boundary of the four Gwinnett GIS parcels in data/site-parcels-2240.json
(SR 2240, NAD83 Georgia West, US survey feet) by cancelling the shared interior segments
(033/015, 015/014, 015/162, 014/162), then walks the outer ring clockwise from the point of
beginning (the 162 / Arcado Rd R/W corner, world 2310954.00 E, 1411431.50 N) and prints
every course as a quadrant bearing (deg-min-sec, GRID bearing) and distance (0.01 ft),
the closure computed from the typed (rounded) courses, and the area.

This is NOT a survey.  It reproduces the county's parcel fabric so that the application
can carry a typed description until a Georgia RLS boundary survey replaces it
(Lilburn Zoning Ordinance 2023-603 §1003-4.3 and 4.4).

Usage:  python3 tools/legal.py            # markdown report to stdout
        python3 tools/legal.py --json     # machine-readable courses
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "data", "site-parcels-2240.json")
LAYOUT = os.path.join(ROOT, "data", "layout.json")

POB = (2310954.0006996617, 1411431.499569498)      # 162 / R-W corner (local origin)
AXIS_DEG = 28.72                                    # strip axis bears N 28°43' W (FACTS §1)
TOL = 0.02                                          # ft — vertex/edge coincidence tolerance
SF_PER_AC = 43560.0

PIN_ORDER = ["6123 033", "6123 015", "6123 014", "6123 162"]


# ---------- geometry helpers ----------
def key(p):
    return (round(p[0], 3), round(p[1], 3))


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def on_segment(p, a, b, tol=TOL):
    """True if p lies on segment ab (strictly inside), within tol."""
    ab = dist(a, b)
    if ab < tol:
        return False
    # perpendicular distance
    cross = abs((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) / ab
    if cross > tol:
        return False
    t = ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / (ab * ab)
    return tol / ab < t < 1 - tol / ab


def azimuth_deg(a, b):
    """Grid azimuth from north, clockwise, degrees 0–360."""
    az = math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))
    return az % 360.0


def quadrant_bearing(az):
    """Return (ns, deg, min, sec, ew) rounded to the second, carrying seconds→minutes→degrees."""
    if az <= 90:
        ns, ew, ang = "N", "E", az
    elif az <= 180:
        ns, ew, ang = "S", "E", 180 - az
    elif az <= 270:
        ns, ew, ang = "S", "W", az - 180
    else:
        ns, ew, ang = "N", "W", 360 - az
    total_sec = int(round(ang * 3600))
    d, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    return ns, d, m, s, ew


def bearing_str(az):
    ns, d, m, s, ew = quadrant_bearing(az)
    return f"{ns} {d:02d}°{m:02d}'{s:02d}\" {ew}"


def bearing_to_az(ns, d, m, s, ew):
    ang = d + m / 60 + s / 3600
    if ns == "N" and ew == "E":
        return ang
    if ns == "S" and ew == "E":
        return 180 - ang
    if ns == "S" and ew == "W":
        return 180 + ang
    return 360 - ang


def shoelace(ring):
    """Signed area; positive = counter-clockwise in an E/N frame."""
    a = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def to_local(p):
    """Site-local (u, v) feet: u along N 28.72° W from the POB, v positive toward the NE line."""
    th = math.radians(AXIS_DEG)
    dE, dN = p[0] - POB[0], p[1] - POB[1]
    u = -dE * math.sin(th) + dN * math.cos(th)
    v = dE * math.cos(th) + dN * math.sin(th)
    return u, v



# ---------- adjoiner lookup (data/site-context-local.json + data/owners-found.json) ----------
CTX_PATH = os.path.join(ROOT, "data", "site-context-local.json")
OWN_PATH = os.path.join(ROOT, "data", "owners-found.json")
SUBDIV = {"NE": "King David Manor Unit 1", "NW": "Nantucket", "SW": "Legends at Parkview"}
STREET = {"ARCADO RD": "Arcado Rd SW", "KING DAVID DR": "King David Dr SW", "NANTUCKET DR": "Nantucket Dr SW",
          "VILLAGE GREEN CT": "Village Green Ct SW", "FIELDHOUSE CIR": "Fieldhouse Cir SW"}


def seg_dist(p, a, b):
    ab2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
    if ab2 == 0:
        return dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / ab2))
    return dist(p, (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))


def load_adjoiners():
    if not (os.path.exists(CTX_PATH) and os.path.exists(OWN_PATH)):
        return []
    with open(CTX_PATH) as f:
        ctx = json.load(f)
    with open(OWN_PATH) as f:
        own = json.load(f)
    out = []
    for ap in ctx["adjoining_parcels"]:
        pin = ap["PIN"]
        if pin in PIN_ORDER:
            continue
        if pin == "R/W":
            out.append({"pin": "R/W", "label": "the northwesterly right-of-way line of Arcado Road (R/W width varies)",
                        "ring": ap["ring_local"]})
            continue
        rec = own[pin][0]
        st = rec["PROPERTYSTREET"]
        num, _, name = st.partition(" ")
        addr = f"{num} {STREET.get(name, name.title())}"
        vs = [q[1] for q in ap["ring_local"]]
        us = [q[0] for q in ap["ring_local"]]
        side = "NE" if min(vs) > -50 else ("SW" if max(vs) < -150 and max(us) < 1760 else "NW")
        label = f"Lot {ap['LOT']}, Block A, {SUBDIV[side]} — {addr} (PIN R{pin})"
        out.append({"pin": pin, "label": label, "ring": ap["ring_local"]})
    return out


def adjoiner_of(course, adjoiners, tol=1.5):
    """Adjoiner whose ring lies along the course (checked at 1/4, 1/2, 3/4 points, site-local)."""
    a, b = to_local(course["from"]), to_local(course["to"])
    best, bestd = None, 1e9
    for adj in adjoiners:
        r = adj["ring"]
        worst = 0.0
        for t in (0.25, 0.5, 0.75):
            p = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
            d = min(seg_dist(p, r[i], r[(i + 1) % len(r)]) for i in range(len(r)))
            worst = max(worst, d)
        if worst < bestd:
            best, bestd = adj, worst
    return (best["label"] if best and bestd <= tol else "VERIFY — no GIS adjoiner within 1.5 ft"), bestd


# ---------- build the outer ring ----------
def load_parcels():
    with open(SRC) as f:
        return json.load(f)


def outer_ring(parcels):
    # 1. collect every vertex (for splitting edges that another ring subdivides)
    verts = []
    for pin in PIN_ORDER:
        verts.extend(parcels[pin]["ring"])
    # 2. directed edges, split at foreign vertices lying on them
    edges = []  # (a, b, pin)
    for pin in PIN_ORDER:
        ring = parcels[pin]["ring"]
        n = len(ring)
        for i in range(n):
            a, b = ring[i], ring[(i + 1) % n]
            if dist(a, b) < TOL:
                continue
            inside = [v for v in verts if on_segment(v, a, b)]
            inside.sort(key=lambda v: dist(a, v))
            chain = [a] + inside + [b]
            for j in range(len(chain) - 1):
                edges.append((chain[j], chain[j + 1], pin))
    # 3. cancel shared interior segments (same segment, opposite direction)
    from collections import Counter
    count = Counter((key(a), key(b)) for a, b, _ in edges)
    outer = []
    for a, b, pin in edges:
        if count[(key(b), key(a))] > 0:
            continue                      # interior: partner exists in the other ring
        outer.append((a, b, pin))
    # 4. chain into one loop
    nxt = {key(a): (a, b, pin) for a, b, pin in outer}
    if len(nxt) != len(outer):
        raise SystemExit("branching boundary — vertex reused")
    start = key(outer[0][0])
    loop, k = [], start
    while True:
        a, b, pin = nxt[k]
        loop.append((a, b, pin))
        k = key(b)
        if k == start:
            break
        if len(loop) > len(outer):
            raise SystemExit("boundary does not close")
    if len(loop) != len(outer):
        raise SystemExit(f"outer boundary has {len(outer)} edges but the loop uses {len(loop)} — more than one ring?")
    return loop


def orient_and_rotate(loop):
    """Clockwise traverse (surveying convention) starting at the POB."""
    ring = [a for a, b, pin in loop]
    if shoelace(ring) > 0:                       # CCW → reverse
        loop = [(b, a, pin) for a, b, pin in reversed(loop)]
    i0 = min(range(len(loop)), key=lambda i: dist(loop[i][0], POB))
    if dist(loop[i0][0], POB) > 0.05:
        raise SystemExit("POB is not a boundary vertex")
    return loop[i0:] + loop[:i0]


def classify(courses):
    """Label each course: frontage → SW → NW → NE, walking clockwise from the POB."""
    side = "frontage"
    out = []
    for c in courses:
        az = c["az"]
        if side == "frontage" and 300 <= az <= 340:      # turns NW up the SW line
            side = "SW"
        elif side == "SW" and 40 <= az <= 80:            # turns NE across the rear
            side = "NW"
        elif side == "NW" and 140 <= az <= 170:          # turns SE down the NE line
            side = "NE"
        c["side"] = side
        out.append(c)
    return out


def build():
    parcels = load_parcels()
    loop = orient_and_rotate(outer_ring(parcels))
    courses = []
    for i, (a, b, pin) in enumerate(loop, 1):
        az = azimuth_deg(a, b)
        ns, d, m, s, ew = quadrant_bearing(az)
        courses.append({
            "no": i, "from": a, "to": b, "pin": pin, "az": az,
            "bearing": bearing_str(az), "qb": (ns, d, m, s, ew),
            "dist": round(dist(a, b), 2),
        })
    courses = classify(courses)
    adjs = load_adjoiners()
    for c in courses:
        c["adjoiner"], c["adjoiner_gap_ft"] = adjoiner_of(c, adjs) if adjs else ("n/a", 0.0)
    ring = [c["from"] for c in courses]
    area_sf = abs(shoelace(ring))
    # closure from the TYPED courses (bearing to 1", distance to 0.01 ft)
    lat = dep = 0.0
    for c in courses:
        az = math.radians(bearing_to_az(*c["qb"]))
        lat += c["dist"] * math.cos(az)
        dep += c["dist"] * math.sin(az)
    perim = sum(c["dist"] for c in courses)
    err = math.hypot(lat, dep)
    # area from the typed courses (coordinates re-derived from the rounded courses)
    x = y = 0.0
    typed = []
    for c in courses:
        typed.append((x, y))
        az = math.radians(bearing_to_az(*c["qb"]))
        x += c["dist"] * math.sin(az)
        y += c["dist"] * math.cos(az)
    typed_area = abs(shoelace(typed))
    sides = {}
    for c in courses:
        sides[c["side"]] = sides.get(c["side"], 0.0) + c["dist"]
    parcel_sum = sum(parcels[p]["area_sf"] for p in PIN_ORDER)
    return {
        "courses": courses, "area_sf": area_sf, "typed_area_sf": typed_area,
        "perimeter_ft": perim, "closure_lat": lat, "closure_dep": dep, "closure_err": err,
        "precision": (perim / err) if err > 1e-9 else float("inf"),
        "sides": sides, "parcel_area_sum_sf": parcel_sum, "ring": ring, "parcels": parcels,
    }


# ---------- checks ----------
def checks(r):
    msgs = []
    ok = True
    # 1. union area equals the sum of the parcel areas (no interior edge survived, none dropped)
    d = abs(r["area_sf"] - r["parcel_area_sum_sf"])
    msgs.append(f"union area {r['area_sf']:.1f} sf vs parcel sum {r['parcel_area_sum_sf']:.1f} sf (Δ {d:.2f} sf)")
    ok &= d < 1.0
    # 2. clockwise, starts at POB
    ok &= shoelace(r["ring"]) < 0
    ok &= dist(r["ring"][0], POB) < 0.05
    msgs.append(f"clockwise from POB: {shoelace(r['ring']) < 0 and dist(r['ring'][0], POB) < 0.05}")
    # 3. closure of the typed description
    msgs.append(f"typed-course closure {r['closure_err']:.3f} ft in {r['perimeter_ft']:.2f} ft (1:{r['precision']:,.0f})")
    ok &= r["closure_err"] < 0.10
    # 4. four sides present in order
    order = [c["side"] for c in r["courses"]]
    seq = [s for i, s in enumerate(order) if i == 0 or order[i - 1] != s]
    msgs.append(f"side sequence: {' → '.join(seq)}")
    ok &= seq == ["frontage", "SW", "NW", "NE"]
    # 5. against layout.json local ring (site plan generator) if present
    if os.path.exists(LAYOUT):
        with open(LAYOUT) as f:
            L = json.load(f)
        lr = [tuple(p) for p in L["boundary_ring"]]
        mine = [to_local(p) for p in r["ring"]]
        worst = 0.0
        for p in mine:
            worst = max(worst, min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in lr))
        msgs.append(f"layout.json boundary_ring: {len(lr)} vertices vs {len(mine)} here; worst vertex offset {worst:.2f} ft; "
                    f"layout boundary_sf {L['boundary_sf']:.1f}")
        ok &= worst < 0.15 and len(lr) == len(mine)
    # 6. every course runs along exactly one GIS adjoiner ring (within 1.5 ft)
    unk = [c["no"] for c in r["courses"] if c["adjoiner"].startswith("VERIFY")]
    gap = max(c["adjoiner_gap_ft"] for c in r["courses"])
    msgs.append(f"adjoiner identified for every course: {not unk} (unresolved: {unk}); worst gap to adjoiner ring {gap:.2f} ft")
    ok &= not unk
    return ok, msgs


# ---------- report ----------
def report(r):
    P = r["parcels"]
    out = []
    out.append("Point of beginning: the 162 / Arcado Rd R/W corner, SR 2240 GA West (US ft) "
               f"E {POB[0]:,.2f}  N {POB[1]:,.2f}  (site-local u 0.00, v 0.00)")
    out.append("")
    out.append("| No. | Side | Bearing (grid) | Distance (ft) | To: E | To: N | To: u | To: v | GIS parcel | Along (GIS adjoiner) |")
    out.append("|---:|---|---|---:|---:|---:|---:|---:|---|---|")
    for c in r["courses"]:
        u, v = to_local(c["to"])
        out.append(f"| {c['no']} | {c['side']} | {c['bearing']} | {c['dist']:.2f} | {c['to'][0]:,.2f} | {c['to'][1]:,.2f} "
                   f"| {u:.1f} | {v:.1f} | {c['pin']} | {c['adjoiner']} |")
    out.append("")
    s = r["sides"]
    out.append(f"Side totals (ft): Arcado Rd frontage {s['frontage']:.2f} | SW line {s['SW']:.2f} | "
               f"NW end {s['NW']:.2f} | NE line {s['NE']:.2f} | perimeter {r['perimeter_ft']:.2f}")
    # widths
    ring = r["ring"]
    front_sw = [c for c in r["courses"] if c["side"] == "frontage"][-1]["to"]
    rear_sw = [c for c in r["courses"] if c["side"] == "SW"][-1]["to"]
    rear_ne = [c for c in r["courses"] if c["side"] == "NW"][-1]["to"]
    out.append(f"Chord widths (ft): front (POB → SW front corner) {dist(POB, front_sw):.2f}; "
               f"rear (SW rear corner → NE rear corner) {dist(rear_sw, rear_ne):.2f}")
    out.append(f"Closure of the typed courses: ΔN {r['closure_lat']:+.3f} ft, ΔE {r['closure_dep']:+.3f} ft, "
               f"linear error {r['closure_err']:.3f} ft in {r['perimeter_ft']:.2f} ft = 1 : {r['precision']:,.0f}")
    out.append(f"Area (coordinate/shoelace, GIS fabric): {r['area_sf']:,.1f} sf = {r['area_sf']/SF_PER_AC:.3f} ac; "
               f"area from the typed courses: {r['typed_area_sf']:,.1f} sf = {r['typed_area_sf']/SF_PER_AC:.3f} ac")
    out.append("Parcel check: " + " + ".join(f"{p} {P[p]['area_sf']:,.1f}" for p in PIN_ORDER) +
               f" = {r['parcel_area_sum_sf']:,.1f} sf (GIS CALCULATEDACREAGE sum "
               f"{sum(P[p]['attributes']['CALCULATEDACREAGE'] for p in PIN_ORDER):.3f} ac; "
               f"DEEDEDACREAGE sum {sum(P[p]['attributes']['DEEDEDACREAGE'] for p in PIN_ORDER):.2f} ac)")
    return "\n".join(out)


def prose(r):
    """Legal-description prose: consecutive courses grouped by the adjoiner they run along."""
    groups = []
    for c in r["courses"]:
        if groups and groups[-1][0] == c["adjoiner"]:
            groups[-1][1].append(c)
        else:
            groups.append((c["adjoiner"], [c]))
    corner_names = {"frontage->SW": "the southwesterly corner of the tract herein described",
                    "SW->NW": "the westerly corner of the tract herein described",
                    "NW->NE": "the northerly corner of the tract herein described"}
    paras = []
    for gi, (adj, cs) in enumerate(groups):
        along = adj if adj.startswith("the ") else "the common line with " + adj
        n = len(cs)
        body = "; thence ".join(f"{c['bearing']} a distance of {c['dist']:.2f} feet" for c in cs)
        if n == 1:
            head = f"thence along {along} {body}"
        else:
            head = f"thence along {along} the following {n} courses: {body}"
        # what the run ends at
        last = cs[-1]
        nxt = groups[gi + 1] if gi + 1 < len(groups) else None
        if nxt is None:
            tail = " to the northwesterly right-of-way line of Arcado Road and the POINT OF BEGINNING."
        else:
            key_ = f"{last['side']}->{nxt[1][0]['side']}"
            corner = corner_names.get(key_)
            nxt_label = nxt[0]
            if corner:
                tail = f" to a point at {corner}, being a corner common to {nxt_label};"
            else:
                tail = f" to a point, being a corner common to {nxt_label};"
        paras.append(head + tail)
    return "\n\n".join(paras)


if __name__ == "__main__":
    r = build()
    ok, msgs = checks(r)
    if "--json" in sys.argv:
        print(json.dumps({"courses": [{k: v for k, v in c.items() if k != "qb"} for c in r["courses"]],
                          "area_sf": r["area_sf"], "closure_err_ft": r["closure_err"],
                          "perimeter_ft": r["perimeter_ft"]}, indent=1, default=list))
        sys.exit(0)
    print(report(r))
    print()
    print("PROSE")
    print(prose(r))
    print()
    print("CHECKS")
    for m in msgs:
        print(" -", m)
    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
