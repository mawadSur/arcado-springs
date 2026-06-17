/* ============================================================================
 * Arcado Springs Traffic Simulator — RENDER (window.TS.render)
 * Draws in CONTAINER PIXEL space using the projection cache from TS.map. The
 * single canvas overlay sits exactly over the Leaflet container (same
 * size/origin), so there is NO camera matrix — Leaflet's pan/zoom IS the
 * camera. The basemap already draws + labels the gray streets, so this overlay
 * NEVER redraws them. It draws only: congestion stroke on the study corridor,
 * queue bars, moving vehicle glyphs, peds/cyclists, the parcel highlight
 * (fallback only), and proposed-improvement rings. The Existing/Proposed toggle
 * just swaps which traffic overlay is drawn over the one live basemap.
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  var COL = {
    paper: "#F6F2EA", paperAlt: "#efe9dc",
    fallbackRoad: "#c9cdbe", fallbackRoadEdge: "#b3b9a4",
    site: "rgba(47,93,58,.14)", siteStroke: "#B08D57", green: "#2F5D3A",
    gold: "#B08D57", ink: "#3a4231",
    free: "#16a34a", moderate: "#eab308", heavy: "#f97316", severe: "#dc2626"
  };

  var bindings = {}; // side -> {canvas, ctx, dpr, w, h}
  var proj = null;   // shared projection cache

  function init(canvasEl, side) {
    if (!canvasEl) return;
    bindings[side] = { canvas: canvasEl, ctx: canvasEl.getContext("2d"), dpr: 1, w: 0, h: 0 };
    resize(side);
  }

  function setProjection(cache) { proj = cache; }
  function mapAvailable() { return !!(TS.map && TS.map.isAvailable && TS.map.isAvailable()); }

  function resize(side) {
    var b = bindings[side];
    if (!b) return;
    var rect = b.canvas.getBoundingClientRect();
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    b.dpr = dpr;
    b.w = Math.max(1, Math.round(rect.width));
    b.h = Math.max(1, Math.round(rect.height));
    b.canvas.width = Math.round(b.w * dpr);
    b.canvas.height = Math.round(b.h * dpr);
    b.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  function resizeAll() { Object.keys(bindings).forEach(resize); }

  /* ---- color helpers ---- */
  function congestionColor(frac) {
    var stops = [COL.free, COL.moderate, COL.heavy, COL.severe];
    var seg = Math.min(0.999, Math.max(0, frac)) * (stops.length - 1);
    var i = seg | 0, t = seg - i;
    return mix(stops[i], stops[i + 1] || stops[i], t);
  }
  function vehColor(v, base) {
    var r = Math.max(0, Math.min(1, base ? v / base : 1));
    return congestionColor(1 - r);
  }
  function mix(c1, c2, t) {
    var a = hex(c1), b = hex(c2);
    return "rgb(" + ((a[0] + (b[0] - a[0]) * t) | 0) + "," + ((a[1] + (b[1] - a[1]) * t) | 0) + "," + ((a[2] + (b[2] - a[2]) * t) | 0) + ")";
  }
  function hex(h) { var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function pointAtPx(pts, d) {
    if (!pts || pts.length < 2) return { x: 0, y: 0, angle: 0 };
    var rem = d;
    for (var i = 1; i < pts.length; i++) {
      var a = pts[i - 1], b = pts[i], seg = Math.hypot(b[0] - a[0], b[1] - a[1]);
      if (rem <= seg || i === pts.length - 1) {
        var t = seg ? rem / seg : 0;
        return { x: a[0] + (b[0] - a[0]) * t, y: a[1] + (b[1] - a[1]) * t, angle: Math.atan2(b[1] - a[1], b[0] - a[0]) };
      }
      rem -= seg;
    }
    var last = pts[pts.length - 1];
    return { x: last[0], y: last[1], angle: 0 };
  }
  function strokePoly(ctx, pts, w, color, dash) {
    if (!pts || pts.length < 2) return;
    ctx.save();
    ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineCap = "round"; ctx.lineJoin = "round";
    ctx.setLineDash(dash || []);
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (var i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
    ctx.stroke();
    ctx.restore();
  }

  function roadPts(name) { return proj && proj.roads ? proj.roads[name] : null; }

  /* When Leaflet is blocked there is no basemap, so draw the real-shaped roads
     ourselves on the paper background (gray, like the reference) — ONLY then. */
  function drawFallbackRoads(ctx) {
    if (mapAvailable() || !proj) return;
    var order = ["Killian Hill Road", "Arcado Road", "Camp Creek Road", "Cole Drive"];
    order.forEach(function (name) {
      var pts = roadPts(name); if (!pts) return;
      var w = name === "Killian Hill Road" ? 11 : 8;
      strokePoly(ctx, pts, w + 2, COL.fallbackRoadEdge);
      strokePoly(ctx, pts, w, COL.fallbackRoad);
    });
  }

  function drawCongestion(ctx, state) {
    if (!state || !proj) return;
    // Thin overlay stroke on the study corridor, colored by local density.
    state.study.forEach(function (name) {
      var pts = roadPts(name); if (!pts) return;
      var frac = state.density && state.density[name] != null ? state.density[name] : 0;
      ctx.globalAlpha = 0.62;
      strokePoly(ctx, pts, 5, congestionColor(frac));
      ctx.globalAlpha = 1;
    });
  }

  function drawQueues(ctx, state) {
    if (!state || !proj) return;
    drawQueueStack(ctx, "Arcado Road", state.queues.arcadoEB, COL.severe, 1);
    drawQueueStack(ctx, "Killian Hill Road", state.queues.killianNBL, COL.heavy, 1);
  }
  function drawQueueStack(ctx, name, count, color, dir) {
    var pts = roadPts(name); if (!pts || !state2(name)) return;
    var sb = state2(name);
    var n = Math.min(10, count);
    for (var i = 0; i < n; i++) {
      var d = sb - (8 + i * 9) * dir;
      var q = pointAtPx(pts, d);
      ctx.save();
      ctx.translate(q.x, q.y); ctx.rotate(q.angle);
      ctx.fillStyle = color;
      roundRect(ctx, -4, -2.5, 8, 5, 1.4); ctx.fill();
      ctx.restore();
    }
  }
  // stop-bar distance lookup (shared with sim cache via state)
  var _stopIdx = null;
  function state2(name) { return _stopIdx ? _stopIdx[name] : null; }

  function drawTurning(ctx) {
    if (!proj) return;
    var c = proj.intersection;
    arrow(ctx, c[0] - 34, c[1] + 8, c[0] - 8, c[1] + 8);
    arrow(ctx, c[0] - 18, c[1] - 6, c[0] - 18, c[1] - 30);
    arrow(ctx, c[0] + 6, c[1] - 18, c[0] + 30, c[1] - 18);
  }
  function arrow(ctx, x1, y1, x2, y2) {
    ctx.save(); ctx.strokeStyle = COL.gold; ctx.fillStyle = COL.gold; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    var a = Math.atan2(y2 - y1, x2 - x1);
    ctx.beginPath(); ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - 6 * Math.cos(a - 0.4), y2 - 6 * Math.sin(a - 0.4));
    ctx.lineTo(x2 - 6 * Math.cos(a + 0.4), y2 - 6 * Math.sin(a + 0.4));
    ctx.closePath(); ctx.fill(); ctx.restore();
  }

  function drawPedCrossings(ctx) {
    if (!proj || !proj.hotspots) return;
    ["hs-pedCrossing", "hs-driveway"].forEach(function (id) {
      var p = proj.hotspots[id]; if (!p) return;
      ctx.save(); ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 2; ctx.globalAlpha = 0.95;
      for (var i = -2; i <= 2; i++) {
        ctx.beginPath(); ctx.moveTo(p[0] + i * 3, p[1] - 7); ctx.lineTo(p[0] + i * 3, p[1] + 7); ctx.stroke();
      }
      ctx.restore();
    });
  }

  function drawProposed(ctx, side) {
    if (!sideShowsAfter(side) || !proj || !proj.hotspots) return;
    ["hs-siteAccess", "hs-turnLane", "hs-driveway"].forEach(function (id) {
      var p = proj.hotspots[id]; if (!p) return;
      ctx.save(); ctx.strokeStyle = COL.gold; ctx.lineWidth = 2; ctx.setLineDash([3, 3]);
      ctx.beginPath(); ctx.arc(p[0], p[1], 13, 0, 7); ctx.stroke(); ctx.restore();
    });
  }

  /* Parcel highlight: Leaflet draws it on the live basemap. We only need a
     canvas parcel where there is NO live basemap behind the stage: the
     fallback (no Leaflet) case. */
  function drawParcel(ctx, side) {
    if (!proj || !proj.site) return;
    if (mapAvailable()) return; // Leaflet polygon already shows it
    var s = proj.site;
    // Box roughly south of the frontage; size in px scaled from intersection dist.
    var scale = 1;
    if (proj.intersection) scale = Math.max(0.6, Math.min(2.2, Math.hypot(proj.intersection[0] - s[0], proj.intersection[1] - s[1]) / 160));
    var hw = 46 * scale, hh = 34 * scale;
    var cx = s[0] - 8 * scale, cy = s[1] + 26 * scale;
    ctx.save();
    ctx.fillStyle = COL.site; ctx.strokeStyle = COL.siteStroke; ctx.lineWidth = 2;
    roundRect(ctx, cx - hw, cy - hh, hw * 2, hh * 2, 8);
    ctx.fill(); ctx.stroke();
    ctx.restore();
  }

  function drawVehicles(ctx, state) {
    if (!state || !proj) return;
    state.vehicles.forEach(function (veh) {
      var pts = roadPts(veh.roadKey); if (!pts) return;
      var q = pointAtPx(pts, veh.d);
      var w = veh.kind === "bus" ? 13 : veh.kind === "truck" ? 11 : 8;
      var h = veh.kind === "car" ? 5 : 6;
      var ang = q.angle + (veh.dir < 0 ? Math.PI : 0);
      ctx.save(); ctx.translate(q.x, q.y); ctx.rotate(ang);
      ctx.fillStyle = veh.study ? vehColor(veh.v, veh.base) : "#8a93a6";
      roundRect(ctx, -w / 2, -h / 2, w, h, 1.8); ctx.fill();
      ctx.restore();
    });
  }
  function drawAgents(ctx, state) {
    if (!state || !proj) return;
    state.cyclists.forEach(function (c) {
      var pts = roadPts(c.roadKey); if (!pts) return;
      var q = pointAtPx(pts, c.d);
      ctx.fillStyle = COL.green;
      ctx.beginPath(); ctx.arc(q.x, q.y, 3, 0, 7); ctx.fill();
    });
    state.peds.forEach(function (pd) {
      var pts = roadPts(pd.roadKey); if (!pts) return;
      var q = pointAtPx(pts, pd.d);
      ctx.fillStyle = COL.gold;
      ctx.beginPath(); ctx.arc(q.x, q.y, 2.6, 0, 7); ctx.fill();
    });
  }

  function sideShowsAfter(side) {
    return TS.config.side === "after";
  }

  /* Single canvas overlay (#ts-canvas-before) renders whichever side is toggled.
     The Leaflet basemap shows through (overlay stays transparent) unless Leaflet
     is unavailable, in which case we paint the paper fallback. */
  function drawFrame(state, layers, side) {
    var b = bindings["before"];
    if (!b) return;
    var ctx = b.ctx;
    if (state && state.stopIdx) _stopIdx = state.stopIdx;
    ctx.clearRect(0, 0, b.w, b.h);

    if (!mapAvailable()) {
      ctx.fillStyle = COL.paper; ctx.fillRect(0, 0, b.w, b.h);
      drawFallbackRoads(ctx);
    }

    if (sideShowsAfter(side)) drawParcel(ctx, side);
    else if (layers.projectBoundary) drawParcel(ctx, side);

    if (layers.congestion) drawCongestion(ctx, state);
    if (layers.pedCrossings) drawPedCrossings(ctx);
    if (layers.turningMovements) drawTurning(ctx);
    if (layers.queues) drawQueues(ctx, state);
    drawVehicles(ctx, state);
    if (layers.pedCrossings || sideShowsAfter(side)) drawAgents(ctx, state);
    if (layers.proposedImprovements) drawProposed(ctx, side);
  }

  function staticFrame() {
    var side = (TS.sim && TS.sim.activeSides) ? TS.sim.activeSides()[0] : TS.config.side;
    var state = TS.sim ? TS.sim.getState(side) : null;
    drawFrame(state, TS.config.layers, side);
    if (TS.ui && TS.ui.syncMetrics && TS.sim) {
      TS.ui.syncMetrics(TS.sim.getMetrics("before"), TS.sim.getMetrics("after"));
    }
  }

  TS.render = {
    init: init,
    resize: function (side) { if (side) resize(side); else resizeAll(); },
    setProjection: setProjection,
    drawFrame: drawFrame,
    staticFrame: staticFrame,
    hasSide: function (side) { return !!bindings[side]; }
  };
})();
