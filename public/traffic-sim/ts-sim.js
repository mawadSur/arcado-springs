/* ============================================================================
 * Arcado Springs Traffic Simulator — SIM (window.TS.sim)
 * Geometry is PIXEL polylines from the projection cache (TS.map.projectAll).
 * Vehicles carry a distance d along a road's pixel polyline; the rAF loop reads
 * only the cache (never re-projects). setProjection() re-derives each vehicle's
 * d from its prior fractional progress so cars don't jump on resize/preset.
 * Roads map to roles: STUDY (Arcado + Killian Hill) carry the heavy traffic,
 * congestion stroke + queue bars; CROSS (Camp Creek, Cole) carry lighter
 * ambient movement. Cap: <=150 active vehicles across visible sides.
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  var MAX_VEHICLES = 150;
  var sides = {};            // 'before' | 'after' -> per-side state
  var proj = null;           // projection cache (pixel polylines)
  var poly = {};             // roadName -> {pts, len}
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
    var prev = poly;
    poly = {};
    Object.keys(proj.roads).forEach(function (name) {
      var pts = proj.roads[name];
      poly[name] = { pts: pts, len: polyLen(pts) };
    });
    sitePx = proj.site;
    isxPx = proj.intersection;

    // Precompute stop-bar index (distance to intersection) per study road.
    STUDY.forEach(function (name) {
      if (poly[name]) stopIdx[name] = distAtNearestVertex(poly[name].pts, isxPx);
    });

    // Rescale existing vehicles' d from prior fractional progress so they don't
    // jump when the polyline pixel length changes (resize/preset).
    ["before", "after"].forEach(function (side) {
      var s = sides[side];
      if (!s) return;
      s.vehicles.forEach(rescale);
      s.peds.forEach(rescale);
      s.cyclists.forEach(rescale);
    });
    function rescale(v) {
      var p = poly[v.roadKey];
      if (!p) return;
      var frac = v.len ? Math.max(0, Math.min(1, v.d / v.len)) : 0;
      v.len = p.len;
      v.d = frac * p.len;
    }
  }
  function ready() { return !!(poly["Arcado Road"] && poly["Killian Hill Road"]); }

  /* ---- per-side state ---- */
  function makeSideState() {
    return {
      vehicles: [], peds: [], cyclists: [],
      spawnAcc: 0,
      signals: {
        mainX: { phase: "green", t: 0, durGreen: 6.5, durRed: 4.5 },
        driveway: { phase: "green", t: 0, durGreen: 5.5, durRed: 3.0 }
      },
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
    if (TS.config.mode === "split") return ["before", "after"];
    return [TS.config.side];
  }
  function perSideCap() {
    var n = activeSides().length || 1;
    return Math.floor(MAX_VEHICLES / n);
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

  /* ---- signals ---- */
  function stepSignals(s, dt) {
    ["mainX", "driveway"].forEach(function (k) {
      var sig = s.signals[k];
      sig.t += dt;
      var dur = sig.phase === "green" ? sig.durGreen : sig.durRed;
      if (sig.t >= dur) { sig.t = 0; sig.phase = sig.phase === "green" ? "red" : "green"; }
    });
  }

  /* ---- step ---- */
  function stepSide(side, dt) {
    var s = sides[side];
    if (!s || !ready()) return;
    stepSignals(s, dt);

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

      // Study-road congestion near the intersection stop bar.
      if (veh.study) {
        var sb = stopIdx[veh.roadKey] || 0;
        var toStop = (sb - veh.d) * veh.dir; // >0 = approaching stop bar
        var nearStop = toStop > -34 && toStop < 150;
        if (nearStop) {
          // Red signal -> stop near the bar.
          if (s.signals.mainX.phase === "red" && toStop > 0 && toStop < 60) target = 0;
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
      signals: s.signals, queues: s.queues, density: s.density,
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
  }

  function setScenario(id) { TS.config.activeScenarioId = id; reseed(); }
  function setMode(m) { TS.config.mode = m; rebalance(); }
  function setSide(side) { TS.config.side = side; }
  function setTimeT(t) { TS.config.timeT = Math.max(0, Math.min(1, t)); }

  function reseed() {
    sides = { before: makeSideState(), after: makeSideState() };
    seed("before"); seed("after");
  }
  function rebalance() {
    var cap = perSideCap();
    ["before", "after"].forEach(function (side) {
      var s = sides[side];
      while (s.vehicles.length > cap) s.vehicles.pop();
    });
  }

  TS.sim = {
    init: init,
    setProjection: setProjection,
    setScenario: setScenario,
    setMode: setMode,
    setSide: setSide,
    setTimeT: setTimeT,
    getState: getState,
    getMetrics: getMetrics,
    start: start,
    stop: stop,
    step: function (dt) { activeSides().forEach(function (side) { stepSide(side, dt); }); },
    activeSides: activeSides,
    MAX_VEHICLES: MAX_VEHICLES
  };
})();
