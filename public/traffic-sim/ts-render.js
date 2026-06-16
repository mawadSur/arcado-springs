/* ============================================================================
 * Arcado Springs Traffic Simulator — RENDER (window.TS.render)
 * Canvas drawing in normalized 0..1 space mapped through a per-preset camera
 * matrix (scale/translate/skew faux-3D), recomputed ONLY on preset change or
 * resize — never per frame. One render binding per side (split = 2, toggle = 1).
 * CLS-safe: canvas width/height attrs derived from container; CSS reserves AR.
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  var COL = {
    ground: "#e9ede2", groundAlt: "#dfe5d6", road: "#7d8a6e", roadEdge: "#9aa888",
    site: "rgba(47,93,58,.14)", siteStroke: "rgba(47,93,58,.55)", green: "#2F5D3A",
    gold: "#B08D57", ink: "#3a4231",
    free: "#16a34a", moderate: "#eab308", heavy: "#f97316", severe: "#dc2626"
  };

  var bindings = {}; // side -> {canvas, ctx, dpr, w, h, cam}
  var nodeById = {};

  function nodesReady() {
    if (Object.keys(nodeById).length) return;
    TS.DATA.nodes.forEach(function (n) { nodeById[n.id] = n; });
  }
  function node(id) { return nodeById[id]; }

  function init(canvasEl, side) {
    if (!canvasEl) return;
    nodesReady();
    bindings[side] = {
      canvas: canvasEl,
      ctx: canvasEl.getContext("2d"),
      dpr: 1, w: 0, h: 0,
      cam: identityCam()
    };
    resize(side);
    setPreset((TS.config && TS.config.preset) || "topdown");
  }

  function identityCam() { return { sx: 1, sy: 1, tx: 0, ty: 0, skew: 0 }; }

  /* Build a camera per preset. Normalized (0..1) -> pixel.
     - topdown: fill canvas.
     - angled: vertical compress + skew for faux-3D tilt + slight lift.
     - intersectionZoom: zoom toward the main corner (0.8,0.46). */
  function buildCam(b, presetId) {
    var W = b.w, H = b.h;
    var cam;
    if (presetId === "angled") {
      cam = { sx: W * 1.0, sy: H * 0.82, tx: 0, ty: H * 0.06, skew: 0.28 };
    } else if (presetId === "intersectionZoom") {
      var z = 2.0;
      var fx = 0.8, fy = 0.46; // focus point in normalized space
      cam = {
        sx: W * z, sy: H * z,
        tx: W * 0.5 - fx * W * z,
        ty: H * 0.5 - fy * H * z,
        skew: 0
      };
    } else {
      cam = { sx: W, sy: H, tx: 0, ty: 0, skew: 0 };
    }
    return cam;
  }

  function project(b, x, y) {
    var c = b.cam;
    var px = x * c.sx + c.tx;
    var py = y * c.sy + c.ty;
    if (c.skew) px += (x - 0.5) * (0.5 - y) * c.skew * c.sx * 0.5; // faux perspective
    return [px, py];
  }

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
    b.cam = buildCam(b, (TS.config && TS.config.preset) || "topdown");
  }
  function resizeAll() { Object.keys(bindings).forEach(resize); }

  function setPreset(presetId) {
    Object.keys(bindings).forEach(function (side) {
      var b = bindings[side];
      b.cam = buildCam(b, presetId);
    });
  }

  /* ---- drawing primitives ---- */
  function edgePts(e) { return [node(e.from), node(e.to)]; }
  function line(ctx, b, a1, a2, w, color, dash) {
    var p1 = project(b, a1.x, a1.y), p2 = project(b, a2.x, a2.y);
    ctx.save();
    ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineCap = "round"; ctx.lineJoin = "round";
    if (dash) ctx.setLineDash(dash); else ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(p1[0], p1[1]); ctx.lineTo(p2[0], p2[1]); ctx.stroke();
    ctx.restore();
  }

  function congestionColor(frac) {
    // frac 0..1 : 0 free, 1 severe
    var stops = [COL.free, COL.moderate, COL.heavy, COL.severe];
    var seg = Math.min(0.999, Math.max(0, frac)) * (stops.length - 1);
    var i = seg | 0, t = seg - i;
    return mix(stops[i], stops[i + 1] || stops[i], t);
  }
  function vehColor(v, base) {
    var r = Math.max(0, Math.min(1, v / base)); // 1 free -> 0 stopped
    return congestionColor(1 - r);
  }
  function mix(c1, c2, t) {
    var a = hex(c1), b = hex(c2);
    return "rgb(" + ((a[0] + (b[0] - a[0]) * t) | 0) + "," + ((a[1] + (b[1] - a[1]) * t) | 0) + "," + ((a[2] + (b[2] - a[2]) * t) | 0) + ")";
  }
  function hex(h) { var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }

  function drawGround(ctx, b) {
    ctx.fillStyle = COL.ground;
    ctx.fillRect(0, 0, b.w, b.h);
  }

  function drawRoads(ctx, b, layers) {
    TS.DATA.edges.forEach(function (e) {
      if (e.cls === "ped-path") return;
      if (e.afterOnly && !showAfter()) return;
      if ((e.cls === "internal" || e.cls === "site-access" || e.cls === "turn-bay") && !showAfter()) return;
      var w = e.cls === "major-arterial" ? 12 : e.cls === "arterial" ? 11 : e.cls === "internal" ? 6 : 8;
      line(ctx, b, node(e.from), node(e.to), w, COL.road);
    });
    // center dashes on the arterial spine
    ["e3", "e4", "e5", "e6", "e7", "e8", "e9"].forEach(function (id) {
      var e = findEdge(id); if (e) line(ctx, b, node(e.from), node(e.to), 1.5, COL.roadEdge, [6, 8]);
    });
  }

  function drawSiteFootprint(ctx, b, layers) {
    // Town-center block
    var nw = node("d1"), se = node("d3");
    var p1 = project(b, nw.x - 0.04, nw.y - 0.06), p2 = project(b, se.x + 0.06, se.y + 0.06);
    ctx.save();
    ctx.fillStyle = COL.site; ctx.strokeStyle = COL.siteStroke; ctx.lineWidth = 1.5;
    roundRect(ctx, p1[0], p1[1], p2[0] - p1[0], p2[1] - p1[1], 10);
    ctx.fill(); ctx.stroke();
    ctx.restore();
    // plaza dot
    var pl = node("plaza"), pp = project(b, pl.x, pl.y);
    ctx.fillStyle = "rgba(47,93,58,.35)";
    ctx.beginPath(); ctx.arc(pp[0], pp[1], 9, 0, 7); ctx.fill();
    // project boundary (optional)
    if (layers.projectBoundary) {
      ctx.save();
      ctx.strokeStyle = COL.gold; ctx.lineWidth = 2; ctx.setLineDash([8, 6]);
      var b1 = project(b, 0.42, 0.62), b2 = project(b, 0.72, 0.94);
      ctx.strokeRect(b1[0], b1[1], b2[0] - b1[0], b2[1] - b1[1]);
      ctx.restore();
    }
  }

  function drawCongestion(ctx, b, state) {
    if (!state) return;
    // Color the arterial spine by local density near each edge midpoint.
    var spine = ["e3", "e4", "e5", "e6", "e9"];
    spine.forEach(function (id) {
      var e = findEdge(id); if (!e) return;
      var a = node(e.from), c = node(e.to);
      var mid = { x: (a.x + c.x) / 2, y: (a.y + c.y) / 2 };
      // Use main-corner density as a proxy weighting by distance.
      var mx = node("mainX");
      var dm = Math.hypot(mid.x - mx.x, mid.y - mx.y);
      var frac = Math.max(0, 1 - dm * 3.5) * Math.min(1, state.density.mainX / 14);
      line(ctx, b, a, c, 13, congestionColor(frac), null);
    });
  }

  function drawQueues(ctx, b, state) {
    if (!state) return;
    // Stack little blocks back from the main stop bar proportional to queue.
    var mx = node("mainX");
    var qE = Math.min(10, state.queues.qhot1);
    for (var i = 0; i < qE; i++) {
      var x = mx.x - 0.03 - i * 0.018;
      var p = project(b, x, mx.y - 0.012);
      ctx.fillStyle = COL.severe;
      roundRect(ctx, p[0] - 4, p[1] - 3, 8, 6, 1.5); ctx.fill();
    }
    var qN = Math.min(8, state.queues.qhot2);
    for (var j = 0; j < qN; j++) {
      var y = mx.y - 0.03 - j * 0.018;
      var pn = project(b, mx.x + 0.012, y);
      ctx.fillStyle = COL.heavy;
      roundRect(ctx, pn[0] - 3, pn[1] - 4, 6, 8, 1.5); ctx.fill();
    }
  }

  function drawSignals(ctx, b, state) {
    if (!state) return;
    drawSignalHead(ctx, b, node("mainX"), state.signals.mainX.phase);
    if (showAfter()) drawSignalHead(ctx, b, node("drivewayJ"), state.signals.driveway.phase);
  }
  function drawSignalHead(ctx, b, n, phase) {
    var p = project(b, n.x, n.y - 0.05);
    ctx.save();
    ctx.fillStyle = "#2a2a28";
    roundRect(ctx, p[0] - 5, p[1] - 12, 10, 24, 3); ctx.fill();
    ctx.fillStyle = phase === "red" ? COL.severe : "#3a3a36";
    ctx.beginPath(); ctx.arc(p[0], p[1] - 6, 3.2, 0, 7); ctx.fill();
    ctx.fillStyle = phase === "green" ? COL.free : "#3a3a36";
    ctx.beginPath(); ctx.arc(p[0], p[1] + 6, 3.2, 0, 7); ctx.fill();
    ctx.restore();
  }

  function drawTurning(ctx, b) {
    var mx = node("mainX");
    arrow(ctx, b, mx.x - 0.06, mx.y - 0.01, mx.x - 0.02, mx.y - 0.01);
    arrow(ctx, b, mx.x - 0.04, mx.y - 0.02, mx.x - 0.04, mx.y - 0.06);
    arrow(ctx, b, mx.x + 0.01, mx.y - 0.04, mx.x + 0.05, mx.y - 0.04);
  }
  function arrow(ctx, b, x1, y1, x2, y2) {
    var p1 = project(b, x1, y1), p2 = project(b, x2, y2);
    ctx.save(); ctx.strokeStyle = COL.gold; ctx.fillStyle = COL.gold; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(p1[0], p1[1]); ctx.lineTo(p2[0], p2[1]); ctx.stroke();
    var a = Math.atan2(p2[1] - p1[1], p2[0] - p1[0]);
    ctx.beginPath(); ctx.moveTo(p2[0], p2[1]);
    ctx.lineTo(p2[0] - 6 * Math.cos(a - 0.4), p2[1] - 6 * Math.sin(a - 0.4));
    ctx.lineTo(p2[0] - 6 * Math.cos(a + 0.4), p2[1] - 6 * Math.sin(a + 0.4));
    ctx.closePath(); ctx.fill(); ctx.restore();
  }

  function drawPedCrossings(ctx, b) {
    [node("pedX1"), node("pedX2")].forEach(function (n) {
      var p = project(b, n.x, n.y);
      ctx.save(); ctx.strokeStyle = "#f4efe4"; ctx.lineWidth = 2;
      for (var i = -2; i <= 2; i++) {
        ctx.beginPath(); ctx.moveTo(p[0] + i * 3, p[1] - 8); ctx.lineTo(p[0] + i * 3, p[1] + 8); ctx.stroke();
      }
      ctx.restore();
    });
  }

  function drawProposed(ctx, b) {
    if (!showAfter()) return;
    // Highlight new signal + turn lane + crossings with gold rings.
    [node("drivewayJ"), node("turnLaneBay"), node("pedX1")].forEach(function (n) {
      var p = project(b, n.x, n.y);
      ctx.save(); ctx.strokeStyle = COL.gold; ctx.lineWidth = 2; ctx.setLineDash([3, 3]);
      ctx.beginPath(); ctx.arc(p[0], p[1], 13, 0, 7); ctx.stroke(); ctx.restore();
    });
  }

  function routeLen(pts) { var L = 0; for (var i = 1; i < pts.length; i++) L += Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y); return L; }
  function pointAt(pts, d) {
    var rem = d;
    for (var i = 1; i < pts.length; i++) {
      var a = pts[i - 1], c = pts[i], seg = Math.hypot(c.x - a.x, c.y - a.y);
      if (rem <= seg || i === pts.length - 1) { var t = seg ? rem / seg : 0; return { x: a.x + (c.x - a.x) * t, y: a.y + (c.y - a.y) * t, a: Math.atan2(c.y - a.y, c.x - a.x) }; }
      rem -= seg;
    }
    var last = pts[pts.length - 1]; return { x: last.x, y: last.y, a: 0 };
  }

  function drawVehicles(ctx, b, state) {
    if (!state) return;
    state.vehicles.forEach(function (veh) {
      var q = pointAt(veh.route, veh.d);
      var p = project(b, q.x, q.y);
      var w = veh.kind === "bus" ? 16 : veh.kind === "truck" ? 14 : 11;
      var h = veh.kind === "car" ? 6 : 7;
      ctx.save(); ctx.translate(p[0], p[1]); ctx.rotate(q.a);
      ctx.fillStyle = vehColor(veh.v, veh.base);
      roundRect(ctx, -w / 2, -h / 2, w, h, 2); ctx.fill();
      ctx.restore();
    });
  }
  function drawAgents(ctx, b, state) {
    if (!state) return;
    state.cyclists.forEach(function (c) {
      var q = pointAt(c.route, c.d), p = project(b, q.x, q.y);
      ctx.fillStyle = COL.green;
      ctx.beginPath(); ctx.arc(p[0], p[1], 3, 0, 7); ctx.fill();
    });
    state.peds.forEach(function (pd) {
      var q = pointAt(pd.route, pd.d), p = project(b, q.x, q.y);
      ctx.fillStyle = COL.gold;
      ctx.beginPath(); ctx.arc(p[0], p[1], 2.6, 0, 7); ctx.fill();
    });
  }

  function findEdge(id) { for (var i = 0; i < TS.DATA.edges.length; i++) if (TS.DATA.edges[i].id === id) return TS.DATA.edges[i]; return null; }
  function showAfter() {
    if (TS.config.mode === "split") return true; // after side drawn separately
    return TS.config.side === "after";
  }
  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  /* In split mode, each side must reflect its own before/after geometry even
     though showAfter() is shared. We pass the side explicitly. */
  function drawFrame(state, layers, side) {
    var b = bindings[side];
    if (!b) return;
    var ctx = b.ctx;
    var prevSide = TS.config._renderSide;
    TS.config._renderSide = side; // used by showAfter via split awareness
    ctx.clearRect(0, 0, b.w, b.h);
    drawGround(ctx, b);
    drawRoads(ctx, b, layers);
    if (sideShowsAfter(side)) drawSiteFootprint(ctx, b, layers);
    else if (layers.projectBoundary) drawSiteFootprint(ctx, b, layers);
    if (layers.congestion) drawCongestion(ctx, b, state);
    if (layers.pedCrossings) drawPedCrossings(ctx, b);
    if (layers.turningMovements) drawTurning(ctx, b);
    if (layers.queues) drawQueues(ctx, b, state);
    drawVehicles(ctx, b, state);
    if (layers.pedCrossings || sideShowsAfter(side)) drawAgents(ctx, b, state);
    if (layers.signals) drawSignals(ctx, b, state);
    if (layers.proposedImprovements && sideShowsAfter(side)) drawProposed(ctx, b);
    TS.config._renderSide = prevSide;
  }

  // Side-aware after check used while drawing a specific canvas.
  function sideShowsAfter(side) {
    if (TS.config.mode === "split") return side === "after";
    return TS.config.side === "after";
  }
  // Override showAfter to consult the side currently rendering.
  showAfter = function () {
    var side = TS.config._renderSide;
    if (!side) {
      if (TS.config.mode === "split") return true;
      return TS.config.side === "after";
    }
    return sideShowsAfter(side);
  };

  function staticFrame() {
    Object.keys(bindings).forEach(function (side) {
      var state = TS.sim ? TS.sim.getState(side) : null;
      drawFrame(state, TS.config.layers, side);
    });
    if (TS.ui && TS.ui.syncMetrics) {
      TS.ui.syncMetrics(TS.sim.getMetrics("before"), TS.sim.getMetrics("after"));
    }
  }

  TS.render = {
    init: init,
    resize: function (side) { if (side) resize(side); else resizeAll(); },
    setPreset: setPreset,
    drawFrame: drawFrame,
    staticFrame: staticFrame,
    hasSide: function (side) { return !!bindings[side]; }
  };
})();
