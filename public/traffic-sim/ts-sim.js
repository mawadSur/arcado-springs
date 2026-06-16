/* ============================================================================
 * Arcado Springs Traffic Simulator — SIM (window.TS.sim)
 * Builds the corridor graph from DATA. Lightweight particle agents follow
 * edge routes; density-scaled speed; signal phase state machine; queues at
 * stop bars. Shared rAF loop drives sim.step -> render.drawFrame -> ui.sync.
 * Cap: <=150 active vehicles across visible sides. Paused when off-screen
 * (IntersectionObserver) or document.hidden. Reduced-motion uses staticFrame.
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  var MAX_VEHICLES = 150;
  var nodeById = {};
  var sides = {}; // 'before' | 'after' -> per-side world state

  /* ---- geometry helpers (normalized space) ---- */
  function dist(a, b) { return Math.hypot(b.x - a.x, b.y - a.y); }
  function routeLen(pts) {
    var L = 0;
    for (var i = 1; i < pts.length; i++) L += dist(pts[i - 1], pts[i]);
    return L;
  }
  function pointAt(pts, d) {
    var rem = d;
    for (var i = 1; i < pts.length; i++) {
      var a = pts[i - 1], b = pts[i], seg = dist(a, b);
      if (rem <= seg || i === pts.length - 1) {
        var t = seg ? rem / seg : 0;
        return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, a: Math.atan2(b.y - a.y, b.x - a.x) };
      }
      rem -= seg;
    }
    var last = pts[pts.length - 1];
    return { x: last.x, y: last.y, a: 0 };
  }
  function node(id) { return nodeById[id]; }
  function chain() {
    var out = [];
    for (var i = 0; i < arguments.length; i++) out.push(node(arguments[i]));
    return out;
  }

  /* ---- route definitions (built once in init) ---- */
  var ROUTES = { beforeCar: [], afterThru: [], afterLocal: [], ped: [], cyclist: [] };

  function buildRoutes() {
    ROUTES.beforeCar = [
      chain("subW", "arcW", "siteFrontW", "drivewayJ", "siteFrontE", "mainX", "arcE"),
      chain("subSW", "arcW", "siteFrontW", "drivewayJ", "siteFrontE", "mainX", "mainXN"),
      chain("subW", "arcW", "siteFrontW", "drivewayJ", "siteFrontE", "mainX", "mainXS"),
      chain("subSW", "arcW", "siteFrontW", "drivewayJ", "siteFrontE", "mainX", "arcE")
    ];
    ROUTES.afterThru = [
      chain("subW", "arcW", "siteFrontW", "drivewayJ", "siteFrontE", "mainX", "arcE"),
      chain("subSW", "arcW", "siteFrontW", "drivewayJ", "siteFrontE", "mainX", "mainXN")
    ];
    ROUTES.afterLocal = [
      chain("subW", "arcW", "siteFrontW", "drivewayJ", "turnLaneBay", "d1", "d2"),
      chain("subSW", "arcW", "siteFrontW", "drivewayJ", "turnLaneBay", "d1", "d4"),
      chain("subW", "arcW", "siteFrontW", "drivewayJ", "turnLaneBay", "d1")
    ];
    ROUTES.ped = [
      chain("d1", "d2", "d3", "d4", "d1"),
      chain("pedX1", "d1", "plaza"),
      chain("d3", "plaza", "d1")
    ];
    ROUTES.cyclist = [
      chain("siteFrontW", "drivewayJ", "siteFrontE"),
      chain("d2", "d3", "d4", "d1", "d2")
    ];
  }

  /* ---- per-side state ---- */
  function makeSideState() {
    return {
      vehicles: [], peds: [], cyclists: [],
      spawnAcc: 0,
      signals: {
        mainX: { phase: "green", t: 0, durGreen: 6.5, durRed: 4.5 },
        driveway: { phase: "green", t: 0, durGreen: 5.5, durRed: 3.0 }
      },
      queues: { qhot1: 0, qhot2: 0 },
      density: { mainX: 0, corridor: 0 }
    };
  }

  function curScenario() {
    var id = TS.config.activeScenarioId;
    for (var i = 0; i < TS.DATA.scenarios.length; i++)
      if (TS.DATA.scenarios[i].id === id) return TS.DATA.scenarios[i];
    return TS.DATA.scenarios[0];
  }

  /* Interpolate a 0..1 demand multiplier from the scenario demand profile. */
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

  /* Which sides are currently visible (need simulation). */
  function activeSides() {
    if (TS.config.mode === "split") return ["before", "after"];
    return [TS.config.side];
  }

  function perSideCap() {
    var n = activeSides().length || 1;
    return Math.floor(MAX_VEHICLES / n);
  }

  /* Demand for a side: AFTER reduces car demand via internal capture + walk shift. */
  function effectiveCarRate(side) {
    var sc = curScenario();
    var dp = sc.demandProfile;
    var base = dp.baseVehPerHr * demandAt(TS.config.timeT);
    if (side === "after") {
      var cap = dp.internalCapture.after;
      var walk = dp.walkBikeShift.after;
      base = base * (1 - cap) * (1 - walk);
    }
    return base;
  }

  function makeVehicle(side) {
    var sc = curScenario();
    var route, kind = "car";
    var r = Math.random();
    if (side === "after") {
      var local = sc.demandProfile.internalCapture.after; // share routed internally
      if (r < local + 0.25) route = pick(ROUTES.afterLocal);
      else route = pick(ROUTES.afterThru);
    } else {
      route = pick(ROUTES.beforeCar);
    }
    // A few trucks/buses: larger + slower.
    var hv = Math.random();
    if (hv < 0.06) kind = "bus";
    else if (hv < 0.14) kind = "truck";
    var baseSpeed = (kind === "car" ? 0.085 : kind === "truck" ? 0.062 : 0.058) * (0.85 + Math.random() * 0.3);
    return { route: route, len: routeLen(route), d: 0, v: 0, base: baseSpeed, kind: kind };
  }
  function makePed() {
    var route = pick(ROUTES.ped);
    return { route: route, len: routeLen(route), d: Math.random() * routeLen(route), v: 0.022 * (0.8 + Math.random() * 0.4), kind: "ped" };
  }
  function makeCyclist() {
    var route = pick(ROUTES.cyclist);
    return { route: route, len: routeLen(route), d: Math.random() * routeLen(route), v: 0.05 * (0.85 + Math.random() * 0.3), kind: "cyclist" };
  }
  function pick(arr) { return arr[(Math.random() * arr.length) | 0]; }

  /* ---- signals ---- */
  function stepSignals(s, dt) {
    ["mainX", "driveway"].forEach(function (k) {
      var sig = s.signals[k];
      sig.t += dt;
      var dur = sig.phase === "green" ? sig.durGreen : sig.durRed;
      if (sig.t >= dur) { sig.t = 0; sig.phase = sig.phase === "green" ? "red" : "green"; }
    });
  }

  /* Is a vehicle approaching a red stop bar near a controlled node? Returns a
     speed cap (0 = full stop) or null if unaffected. */
  function signalCap(s, side, veh, pos) {
    // Main intersection stop bar
    var mx = node("mainX");
    var dMx = Math.hypot(pos.x - mx.x, pos.y - mx.y);
    if (dMx < 0.05 && approaching(veh, pos, mx) && s.signals.mainX.phase === "red") return 0;
    // Driveway signal only exists AFTER build-out
    if (side === "after") {
      var dj = node("drivewayJ");
      var dDj = Math.hypot(pos.x - dj.x, pos.y - dj.y);
      if (dDj < 0.045 && approaching(veh, pos, dj) && s.signals.driveway.phase === "red") return 0;
    }
    return null;
  }
  function approaching(veh, pos, target) {
    var ahead = pointAt(veh.route, Math.min(veh.len, veh.d + 0.02));
    var dn = Math.hypot(ahead.x - target.x, ahead.y - target.y);
    var dc = Math.hypot(pos.x - target.x, pos.y - target.y);
    return dn < dc;
  }

  /* ---- step ---- */
  function stepSide(side, dt) {
    var s = sides[side];
    var sc = curScenario();
    stepSignals(s, dt);

    // Spawn vehicles based on effective hourly rate.
    var rate = effectiveCarRate(side); // veh/hr
    var perSec = rate / 3600;
    s.spawnAcc += perSec * dt * 4; // visual density scaling
    var cap = perSideCap();
    while (s.spawnAcc >= 1 && s.vehicles.length < cap) {
      s.spawnAcc -= 1;
      s.vehicles.push(makeVehicle(side));
    }

    // Maintain peds/cyclists only AFTER (walkable site) — a fixed friendly count.
    var wantPed = side === "after" ? 14 : 2;
    var wantCyc = side === "after" ? 5 : 1;
    while (s.peds.length < wantPed) s.peds.push(makePed());
    while (s.peds.length > wantPed) s.peds.pop();
    while (s.cyclists.length < wantCyc) s.cyclists.push(makeCyclist());
    while (s.cyclists.length > wantCyc) s.cyclists.pop();

    // Reset queue accumulators.
    s.queues.qhot1 = 0;
    s.queues.qhot2 = 0;
    var mxCount = 0;

    // Sort by progress for simple car-following on same route.
    for (var i = s.vehicles.length - 1; i >= 0; i--) {
      var veh = s.vehicles[i];
      var pos = pointAt(veh.route, veh.d);
      var target = veh.base;

      // Density: count vehicles ahead on the same route within a gap.
      for (var k = 0; k < s.vehicles.length; k++) {
        if (k === i) continue;
        var o = s.vehicles[k];
        if (o.route === veh.route) {
          var gap = o.d - veh.d;
          if (gap > 0 && gap < 0.045) target = Math.min(target, gap * 1.6);
        }
      }
      // Signal control.
      var sCap = signalCap(s, side, veh, pos);
      if (sCap !== null) target = Math.min(target, sCap);

      // Congestion near main corner (worse BEFORE, eased AFTER by turn lane).
      var mx = node("mainX");
      var dMx = Math.hypot(pos.x - mx.x, pos.y - mx.y);
      if (dMx < 0.10) {
        var jam = side === "before" ? 0.7 : 0.32;
        jam *= 0.5 + 0.5 * demandAt(TS.config.timeT);
        target *= (1 - jam * 0.8);
        if (target < veh.base * 0.25) {
          mxCount++;
          // Attribute slow vehicles to eastbound / northbound queues.
          if (pos.x < mx.x) s.queues.qhot1 += 1;
          if (pos.y < mx.y) s.queues.qhot2 += 1;
        }
      }

      veh.v += (target - veh.v) * Math.min(1, dt * 5);
      veh.d += veh.v * dt;
      if (veh.d >= veh.len) s.vehicles.splice(i, 1);
    }

    // Advance peds + cyclists (loop).
    advanceAgents(s.peds, dt);
    advanceAgents(s.cyclists, dt);

    s.density.mainX = mxCount;
    s.density.corridor = s.vehicles.length;
  }
  function advanceAgents(list, dt) {
    for (var i = 0; i < list.length; i++) {
      var a = list[i];
      a.d += a.v * dt;
      if (a.d >= a.len) a.d -= a.len; // loop
    }
  }

  /* ---- public state for render ---- */
  function getState(side) {
    var s = sides[side];
    if (!s) return null;
    return { vehicles: s.vehicles, peds: s.peds, cyclists: s.cyclists, signals: s.signals, queues: s.queues, density: s.density };
  }

  /* ---- metrics: interpolate before/after anchors eased toward peak by timeT ---- */
  function getMetrics(side) {
    var sc = curScenario();
    var peakEase = demandAt(TS.config.timeT); // 0..~1: closeness to peak demand
    var out = {};
    TS.DATA.metrics.forEach(function (m) {
      var anchor = sc.metrics[m.id];
      if (!anchor) { out[m.id] = null; return; }
      var v = anchor[side];
      if (m.format === "grade") { out[m.id] = v; return; }
      // Off-peak: blend toward the better end proportional to demand.
      // At full peak (peakEase=1) show the anchor; at low demand, improve.
      var best = m.lowerIsBetter ? Math.min(anchor.before, anchor.after) : Math.max(anchor.before, anchor.after);
      var blended = v + (best - v) * (1 - peakEase) * 0.45;
      out[m.id] = blended;
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

  function start() {
    if (rafId) cancelAnimationFrame(rafId);
    last = 0;
    rafId = requestAnimationFrame(loop);
  }
  function stop() {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
  }

  function init() {
    nodeById = {};
    TS.DATA.nodes.forEach(function (n) { nodeById[n.id] = n; });
    buildRoutes();
    sides = { before: makeSideState(), after: makeSideState() };
    // Seed a representative population so the first frame isn't empty.
    seed("before");
    seed("after");
  }
  function seed(side) {
    var s = sides[side];
    var cap = Math.floor(perSideCap() * 0.6);
    for (var i = 0; i < cap; i++) {
      var v = makeVehicle(side);
      v.d = Math.random() * v.len;
      s.vehicles.push(v);
    }
    var wantPed = side === "after" ? 14 : 2;
    var wantCyc = side === "after" ? 5 : 1;
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
    // Trim each side to its new per-side cap when mode changes.
    var cap = perSideCap();
    ["before", "after"].forEach(function (side) {
      var s = sides[side];
      while (s.vehicles.length > cap) s.vehicles.pop();
    });
  }

  TS.sim = {
    init: init,
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
