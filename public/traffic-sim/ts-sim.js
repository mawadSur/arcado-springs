/* ============================================================================
 * Arcado Springs Traffic Simulator — SIM (window.TS.sim)
 * Geometry is PIXEL polylines from the projection cache (TS.map.projectAll).
 * Vehicles carry a distance d along a road's pixel polyline; the rAF loop reads
 * only the cache (never re-projects). setProjection() re-derives each vehicle's
 * d from its prior fractional progress so cars don't jump on resize/preset.
 * Roads map to roles: STUDY (Arcado + Killian Hill) carry the heavy traffic,
 * congestion stroke + queue bars; CROSS (Camp Creek, Cole) carry lighter
 * ambient movement. Cap: <=150 active vehicles on the single live side.
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  var MAX_VEHICLES = 150;
  var MAX_CAPTURES = 26;     // local-trip agents (additional, distinct layer)
  var sides = {};            // 'before' | 'after' -> per-side state
  var proj = null;           // projection cache (pixel polylines)
  var poly = {};             // roadName -> {pts, len}
  var feedPoly = {};         // feederName -> {pts, len, siteEnd} (siteEnd: 1|-1)
  var feedNames = [];        // feeder names with valid geometry
  var STUDY = ["Arcado Road", "Killian Hill Road"];
  var CROSS = ["Camp Creek Road", "Cole Drive"];
  var stopIdx = {};          // roadName -> polyline index nearest intersection
  var sitePx = null, isxPx = null;

  /* ---- pixel-polyline geometry helpers ---- */
  function segLen(a, b) { return Math.hypot(b[0] - a[0], b[1] - a[1]); }
  function polyLen(pts) {
    var L = 0;
    for (var i = 1; i < pts.length; i++) L += segLen(pts[i - 1], pts[i]);
    return L;
  }
  function pointAtPx(pts, d) {
    if (!pts || pts.length < 2) return { x: 0, y: 0, angle: 0 };
    var rem = d;
    for (var i = 1; i < pts.length; i++) {
      var a = pts[i - 1], b = pts[i], seg = segLen(a, b);
      if (rem <= seg || i === pts.length - 1) {
        var t = seg ? rem / seg : 0;
        return { x: a[0] + (b[0] - a[0]) * t, y: a[1] + (b[1] - a[1]) * t, angle: Math.atan2(b[1] - a[1], b[0] - a[0]) };
      }
      rem -= seg;
    }
    var last = pts[pts.length - 1];
    return { x: last[0], y: last[1], angle: 0 };
  }

  /* Distance (along polyline) of the vertex nearest a pixel point. */
  function distAtNearestVertex(pts, px) {
    var best = 0, bestD = Infinity, acc = 0;
    for (var i = 0; i < pts.length; i++) {
      if (i > 0) acc += segLen(pts[i - 1], pts[i]);
      var dd = Math.hypot(pts[i][0] - px[0], pts[i][1] - px[1]);
      if (dd < bestD) { bestD = dd; best = acc; }
    }
    return best;
  }

  /* ---- projection wiring ---- */
  function setProjection(cache) {
    proj = cache || (TS.map && TS.map.getProjection ? TS.map.getProjection() : null);
    if (!proj) return;
    poly = {};
    Object.keys(proj.roads).forEach(function (name) {
      var pts = proj.roads[name];
      poly[name] = { pts: pts, len: polyLen(pts) };
    });
    sitePx = proj.site;
    isxPx = proj.intersection;

    // Feeder pixel polylines. siteEnd = +1 means d→len heads toward the site.
    feedPoly = {}; feedNames = [];
    var feeders = proj.feeders || {};
    Object.keys(feeders).forEach(function (name) {
      var pts = feeders[name];
      if (!pts || pts.length < 2) return;
      var len = polyLen(pts); if (!(len > 0)) return;
      var a = pts[0], b = pts[pts.length - 1];
      var dA = sitePx ? Math.hypot(a[0] - sitePx[0], a[1] - sitePx[1]) : 0;
      var dB = sitePx ? Math.hypot(b[0] - sitePx[0], b[1] - sitePx[1]) : 1;
      feedPoly[name] = { pts: pts, len: len, siteEnd: dB <= dA ? 1 : -1 };
      feedNames.push(name);
    });

    // Precompute stop-bar index (distance to intersection) per study road.
    STUDY.forEach(function (name) {
      if (poly[name]) stopIdx[name] = distAtNearestVertex(poly[name].pts, isxPx);
    });

    // Rescale existing agents' d from prior fractional progress so they don't
    // jump when the polyline pixel length changes (resize/preset).
    ["before", "after"].forEach(function (side) {
      var s = sides[side];
      if (!s) return;
      s.vehicles.forEach(rescale);
      s.peds.forEach(rescale);
      s.cyclists.forEach(rescale);
      s.captures.forEach(rescaleCap);
    });
    function rescale(v) {
      var p = poly[v.roadKey];
      if (!p) return;
      var frac = v.len ? Math.max(0, Math.min(1, v.d / v.len)) : 0;
      v.len = p.len;
      v.d = frac * p.len;
    }
    function rescaleCap(c) {
      var p = feedPoly[c.feederKey]; if (!p) return;
      var frac = c.len ? Math.max(0, Math.min(1, c.d / c.len)) : 0;
      c.len = p.len; c.d = frac * p.len;
    }
  }
  function ready() { return !!(poly["Arcado Road"] && poly["Killian Hill Road"]); }

  /* ---- per-side state ---- */
  function makeSideState() {
    return {
      vehicles: [], peds: [], cyclists: [],
      captures: [],            // local-trip agents on the feeder streets
      spawnAcc: 0, capAcc: 0,
      queues: { arcadoEB: 0, killianNBL: 0 },
      density: {} // roadName -> 0..1
    };
  }

  function curScenario() {
    var id = TS.config.activeScenarioId;
    for (var i = 0; i < TS.DATA.scenarios.length; i++)
      if (TS.DATA.scenarios[i].id === id) return TS.DATA.scenarios[i];
    return TS.DATA.scenarios[0];
  }

  function demandAt(t) {
    var pts = curScenario().demandProfile.points;
    if (t <= pts[0].t) return pts[0].mult;
    for (var i = 1; i < pts.length; i++) {
      if (t <= pts[i].t) {
        var f = (t - pts[i - 1].t) / (pts[i].t - pts[i - 1].t || 1);
        return pts[i - 1].mult + (pts[i].mult - pts[i - 1].mult) * f;
      }
    }
    return pts[pts.length - 1].mult;
  }

  function activeSides() {
    // Single map: only the toggled side is live at a time.
    return [TS.config.side];
  }
  function perSideCap() {
    return MAX_VEHICLES;
  }

  /* AFTER reduces car demand via internal capture + walk shift. */
  function effectiveCarRate(side) {
    var dp = curScenario().demandProfile;
    var base = dp.baseVehPerHr * demandAt(TS.config.timeT);
    if (side === "after") base = base * (1 - dp.internalCapture.after) * (1 - dp.walkBikeShift.after);
    return base;
  }

  function pick(arr) { return arr[(Math.random() * arr.length) | 0]; }

  /* Choose a road for a new vehicle. STUDY roads carry the bulk; CROSS lighter
     (~30%). AFTER peels some trips into the site (shorter trips / capture). */
  function chooseRoad(side) {
    var r = Math.random();
    if (r < 0.30) return pick(CROSS);
    return pick(STUDY);
  }

  function makeVehicle(side) {
    var roadKey = chooseRoad(side);
    var p = poly[roadKey];
    var kind = "car";
    var hv = Math.random();
    if (hv < 0.05) kind = "bus";
    else if (hv < 0.13) kind = "truck";
    var study = STUDY.indexOf(roadKey) >= 0;
    // px/sec base speed; trucks/buses slower; cross roads a touch faster (free).
    var spd = (kind === "car" ? 58 : kind === "truck" ? 44 : 40);
    spd *= (study ? 1 : 1.15) * (0.85 + Math.random() * 0.3);
    return {
      roadKey: roadKey, dir: Math.random() < 0.5 ? 1 : -1,
      d: 0, len: p ? p.len : 0, v: 0, base: spd, kind: kind, study: study,
      onSite: side === "after" && study && roadKey === "Arcado Road" && Math.random() < curScenario().demandProfile.internalCapture.after
    };
  }
  function makePed() {
    // Peds loop on a short stretch of Arcado Rd near the site frontage.
    var p = poly["Arcado Road"];
    return { roadKey: "Arcado Road", dir: Math.random() < 0.5 ? 1 : -1, d: p ? Math.random() * p.len : 0, len: p ? p.len : 0, v: 14 * (0.8 + Math.random() * 0.4), kind: "ped" };
  }
  function makeCyclist() {
    var p = poly["Arcado Road"];
    return { roadKey: "Arcado Road", dir: Math.random() < 0.5 ? 1 : -1, d: p ? Math.random() * p.len : 0, len: p ? p.len : 0, v: 34 * (0.85 + Math.random() * 0.3), kind: "cyclist" };
  }

  /* ---- captured local trips (feeder streets) ----
     A local trip runs the neighborhood end of a feeder toward the site end.
     PROPOSED: it pulls INTO the parcel (free/green, may walk/bike) and fades on
     arrival. EXISTING: the same trip joins Arcado Rd toward the congested Killian
     Hill corner (car, slower/redder). Toggling DIVERTS flow corner<->site. */
  function capturesReady() { return feedNames.length > 0; }

  function makeCapture(side) {
    var feederKey = pick(feedNames), fp = feedPoly[feederKey];
    if (!fp) return null;
    var dir = fp.siteEnd;                 // +1 -> d→len heads to site; -1 -> d→0
    var mode = "car";                     // Proposed peels a few to walk/bike
    if (side === "after") {
      var wb = curScenario().demandProfile.walkBikeShift.after || 0;
      if (Math.random() < Math.min(0.45, wb * 3.2)) mode = Math.random() < 0.5 ? "walk" : "bike";
    }
    var spd = (mode === "walk" ? 16 : mode === "bike" ? 34 : 52) * (0.85 + Math.random() * 0.3);
    return {
      feederKey: feederKey, dir: dir, d: dir > 0 ? 0 : fp.len, len: fp.len,
      v: spd, base: spd, mode: mode, side: side,
      phase: "feeder", arrive: 0,         // arrive: 0..1 fade-on-park (Proposed)
      corridorKey: null, corridorD: 0, corridorDir: 1
    };
  }

  /* Illustrative captured local trips per hour, from the scenario's internal-
     capture + walk share (consistent with metrics). Existing captures none. */
  function captureTripsPerHr(side) {
    if (side !== "after") return 0;
    var dp = curScenario().demandProfile;
    var share = (dp.internalCapture.after || 0) + (dp.walkBikeShift.after || 0);
    return Math.round(dp.baseVehPerHr * share * demandAt(TS.config.timeT));
  }

  function stepCaptures(side, dt) {
    var s = sides[side];
    if (!s || !capturesReady()) return;
    if (!TS.config.layers || !TS.config.layers.localTrips) { s.captures.length = 0; return; }

    var dp = curScenario().demandProfile;
    var share = (dp.internalCapture.after || 0) + (dp.walkBikeShift.after || 0);
    var rate = Math.max(0.25, dp.baseVehPerHr * share * demandAt(TS.config.timeT) / 3600);
    s.capAcc += rate * dt * 0.9;
    while (s.capAcc >= 1 && s.captures.length < MAX_CAPTURES) {
      s.capAcc -= 1;
      var c = makeCapture(side); if (c) s.captures.push(c);
    }

    var arcado = poly["Arcado Road"];
    for (var i = s.captures.length - 1; i >= 0; i--) {
      var a = s.captures[i], fp = feedPoly[a.feederKey];
      if (!fp) { s.captures.splice(i, 1); continue; }

      if (a.phase === "feeder") {
        a.len = fp.len; a.d += a.v * a.dir * dt;
        if (a.dir > 0 ? a.d >= fp.len : a.d <= 0) {
          if (side === "after") a.phase = "arriving";
          else {                          // Existing: hop onto Arcado Rd to corner
            a.phase = "corridor"; a.corridorKey = "Arcado Road";
            if (arcado && isxPx) {
              var pos = pointAtPx(fp.pts, a.dir > 0 ? fp.len : 0);
              a.corridorD = distAtNearestVertex(arcado.pts, [pos.x, pos.y]);
              a.corridorDir = distAtNearestVertex(arcado.pts, isxPx) >= a.corridorD ? 1 : -1;
            }
          }
        }
      } else if (a.phase === "arriving") {  // Proposed: converge on parcel, fade
        a.arrive += dt * 1.3;
        if (a.arrive >= 1) { s.captures.splice(i, 1); continue; }
      } else if (a.phase === "corridor") {  // Existing: slow at the jammed corner
        var p = poly[a.corridorKey];
        if (!p) { s.captures.splice(i, 1); continue; }
        a.len = p.len;
        var cp = pointAtPx(p.pts, a.corridorD);
        var dCorner = isxPx ? Math.hypot(cp.x - isxPx[0], cp.y - isxPx[1]) : 999;
        var jam = (side === "before" ? 0.7 : 0.35) * (0.5 + 0.5 * demandAt(TS.config.timeT));
        a.v += (a.base * (dCorner < 200 ? 1 - jam * 0.85 : 1) - a.v) * Math.min(1, dt * 5);
        a.corridorD += a.v * a.corridorDir * dt;
        if (a.corridorD <= -2 || a.corridorD >= a.len + 2 || dCorner < 16) { s.captures.splice(i, 1); }
      }
    }
  }

  /* ---- step ---- */
  function stepSide(side, dt) {
    var s = sides[side];
    if (!s || !ready()) return;

    // Spawn.
    var perSec = effectiveCarRate(side) / 3600;
    s.spawnAcc += perSec * dt * 4; // visual density scaling
    var cap = perSideCap();
    while (s.spawnAcc >= 1 && s.vehicles.length < cap) {
      s.spawnAcc -= 1;
      var v = makeVehicle(side);
      v.d = v.dir > 0 ? 0 : v.len; // enter from the appropriate end
      s.vehicles.push(v);
    }

    // Peds/cyclists: a friendly fixed count, heavier AFTER (walkable site).
    var wantPed = side === "after" ? 12 : 2;
    var wantCyc = side === "after" ? 4 : 1;
    while (s.peds.length < wantPed) s.peds.push(makePed());
    while (s.peds.length > wantPed) s.peds.pop();
    while (s.cyclists.length < wantCyc) s.cyclists.push(makeCyclist());
    while (s.cyclists.length > wantCyc) s.cyclists.pop();

    // Reset queues + density accumulators.
    s.queues.arcadoEB = 0;
    s.queues.killianNBL = 0;
    var dCount = {};

    var jamBase = side === "before" ? 0.72 : 0.34;
    jamBase *= 0.5 + 0.5 * demandAt(TS.config.timeT);

    for (var i = s.vehicles.length - 1; i >= 0; i--) {
      var veh = s.vehicles[i];
      var p = poly[veh.roadKey];
      if (!p) { s.vehicles.splice(i, 1); continue; }
      var pos = pointAtPx(p.pts, veh.d);
      var target = veh.base;

      // Car-following: slow if a same-road same-direction vehicle is just ahead.
      for (var k = 0; k < s.vehicles.length; k++) {
        if (k === i) continue;
        var o = s.vehicles[k];
        if (o.roadKey === veh.roadKey && o.dir === veh.dir) {
          var gap = (o.d - veh.d) * veh.dir;
          if (gap > 0 && gap < 26) target = Math.min(target, gap * 2.4);
        }
      }

      // Study-road congestion near the (unsignalized) corner. Density-based:
      // the closer to the corner and the heavier the demand, the slower the
      // approach — backup/queues form by congestion, not by a signal phase.
      if (veh.study) {
        var sb = stopIdx[veh.roadKey] || 0;
        var toStop = (sb - veh.d) * veh.dir; // >0 = approaching the corner
        var nearStop = toStop > -34 && toStop < 150;
        if (nearStop) {
          // General jam zone within 220px of the corner.
          var dCorner = Math.hypot(pos.x - isxPx[0], pos.y - isxPx[1]);
          if (dCorner < 220) target *= (1 - jamBase * 0.85);
        }
        if (target < veh.base * 0.28 && nearStop) {
          if (veh.roadKey === "Arcado Road") s.queues.arcadoEB += 1;
          else s.queues.killianNBL += 1;
        }
      }

      // AFTER on-site capture: such a trip "arrives" (leaves the corridor) early.
      veh.v += (target - veh.v) * Math.min(1, dt * 5);
      veh.d += veh.v * veh.dir * dt;

      // Density tally per road (within the corridor frame).
      dCount[veh.roadKey] = (dCount[veh.roadKey] || 0) + 1;

      // Remove when off either end, or when an AFTER on-site car passes the site.
      var off = veh.d <= -2 || veh.d >= veh.len + 2;
      if (veh.onSite && veh.roadKey === "Arcado Road" && sitePx) {
        var dSite = Math.hypot(pos.x - sitePx[0], pos.y - sitePx[1]);
        if (dSite < 18) off = true;
      }
      if (off) s.vehicles.splice(i, 1);
    }

    advanceLoop(s.peds, dt);
    advanceLoop(s.cyclists, dt);
    stepCaptures(side, dt);

    // Normalize per-road density (vehicles -> 0..1), weighted toward intersection.
    s.density = {};
    STUDY.concat(CROSS).forEach(function (name) {
      var n = dCount[name] || 0;
      var capR = name === "Killian Hill Road" ? 22 : name === "Arcado Road" ? 18 : 10;
      s.density[name] = Math.min(1, n / capR);
    });
  }

  function advanceLoop(list, dt) {
    for (var i = 0; i < list.length; i++) {
      var a = list[i];
      var p = poly[a.roadKey];
      if (!p) continue;
      a.len = p.len;
      a.d += a.v * a.dir * dt;
      if (a.d > a.len) a.d -= a.len;
      if (a.d < 0) a.d += a.len;
    }
  }

  /* ---- public state for render ---- */
  function getState(side) {
    var s = sides[side];
    if (!s) return null;
    return {
      vehicles: s.vehicles, peds: s.peds, cyclists: s.cyclists,
      captures: s.captures, feedNames: feedNames,
      queues: s.queues, density: s.density,
      stopIdx: stopIdx, study: STUDY, cross: CROSS
    };
  }

  /* ---- metrics: interpolate before/after anchors eased toward peak by timeT ---- */
  function getMetrics(side) {
    var sc = curScenario();
    var peakEase = demandAt(TS.config.timeT);
    var out = {};
    TS.DATA.metrics.forEach(function (m) {
      var anchor = sc.metrics[m.id];
      if (!anchor) { out[m.id] = null; return; }
      var v = anchor[side];
      if (m.format === "grade") { out[m.id] = v; return; }
      var best = m.lowerIsBetter ? Math.min(anchor.before, anchor.after) : Math.max(anchor.before, anchor.after);
      out[m.id] = v + (best - v) * (1 - peakEase) * 0.45;
    });
    return out;
  }

  /* ---- shared rAF loop ---- */
  var rafId = null, last = 0, statAcc = 0;
  function loop(ts) {
    if (!TS.config.playing || !TS.config.visible) { rafId = null; return; }
    if (!last) last = ts;
    var dt = Math.min(0.05, (ts - last) / 1000);
    last = ts;

    var sds = activeSides();
    sds.forEach(function (side) { stepSide(side, dt); });
    if (TS.render) {
      sds.forEach(function (side) {
        TS.render.drawFrame(getState(side), TS.config.layers, side);
      });
    }
    statAcc += dt;
    if (statAcc > 0.3) {
      statAcc = 0;
      if (TS.ui && TS.ui.syncMetrics) TS.ui.syncMetrics(getMetrics("before"), getMetrics("after"));
      if (TS.ui && TS.ui.syncCapture) TS.ui.syncCapture(captureTripsPerHr(TS.config.side));
    }
    rafId = requestAnimationFrame(loop);
  }

  function start() { if (rafId) cancelAnimationFrame(rafId); last = 0; rafId = requestAnimationFrame(loop); }
  function stop() { if (rafId) cancelAnimationFrame(rafId); rafId = null; }

  function init() {
    sides = { before: makeSideState(), after: makeSideState() };
    if (TS.map && TS.map.getProjection) setProjection(TS.map.getProjection());
    seed("before");
    seed("after");
  }
  function seed(side) {
    var s = sides[side];
    if (!ready()) return;
    var cap = Math.floor(perSideCap() * 0.55);
    for (var i = 0; i < cap; i++) {
      var v = makeVehicle(side);
      v.d = Math.random() * v.len;
      s.vehicles.push(v);
    }
    var wantPed = side === "after" ? 12 : 2;
    var wantCyc = side === "after" ? 4 : 1;
    for (var p = 0; p < wantPed; p++) s.peds.push(makePed());
    for (var c = 0; c < wantCyc; c++) s.cyclists.push(makeCyclist());
    // Seed a handful of local-trip agents already in motion along the feeders.
    if (capturesReady() && TS.config.layers && TS.config.layers.localTrips) {
      for (var k = 0; k < Math.floor(MAX_CAPTURES * 0.5); k++) {
        var cap = makeCapture(side); if (!cap) break;
        cap.d = cap.dir > 0 ? Math.random() * cap.len : cap.len * (1 - Math.random());
        s.captures.push(cap);
      }
    }
  }

  function setScenario(id) { TS.config.activeScenarioId = id; reseed(); }
  function setSide(side) { TS.config.side = side; }
  function setTimeT(t) { TS.config.timeT = Math.max(0, Math.min(1, t)); }

  function reseed() {
    sides = { before: makeSideState(), after: makeSideState() };
    seed("before"); seed("after");
  }

  TS.sim = {
    init: init,
    setProjection: setProjection,
    setScenario: setScenario,
    setSide: setSide,
    setTimeT: setTimeT,
    getState: getState,
    getMetrics: getMetrics,
    captureTripsPerHr: captureTripsPerHr,
    start: start,
    stop: stop,
    step: function (dt) { activeSides().forEach(function (side) { stepSide(side, dt); }); },
    activeSides: activeSides,
    MAX_VEHICLES: MAX_VEHICLES
  };
})();
