/* ============================================================================
 * Arcado Springs Traffic Simulator — APP (window.TS.boot orchestrator)
 * Strict init order on DOMContentLoaded. Freezes DATA, sets config defaults,
 * inits map -> render(s) -> sim -> ui -> presentation, attaches visibility +
 * IntersectionObserver pause logic, applies preset, starts (or static frame).
 * Runs last. Cross-module calls go only through documented methods.
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  function detectReducedMotion() {
    return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  function defaultLayers() {
    var o = {};
    (TS.DATA.layers || []).forEach(function (l) { o[l.id] = !!l.defaultOn; });
    return o;
  }

  function boot() {
    if (!TS.DATA) return;

    // 1. Freeze DATA (read-only contract).
    try { deepFreeze(TS.DATA); } catch (e) {}

    // 2. Reduced-motion + config defaults.
    var reduced = detectReducedMotion();
    TS.config = {
      activeScenarioId: "am-peak",
      mode: "split",
      side: "after",
      preset: "topdown",
      playing: !reduced,
      timeT: 0.5,
      layers: defaultLayers(),
      reducedMotion: reduced,
      visible: true,
      _renderSide: null
    };

    // 3. Map (graceful if Leaflet missing).
    var mapOk = false;
    try { mapOk = TS.map.init("ts-map"); } catch (e) { mapOk = false; }

    // 4. Render bindings — one per side.
    var cBefore = document.getElementById("ts-canvas-before");
    var cAfter = document.getElementById("ts-canvas-after");
    if (cBefore) TS.render.init(cBefore, "before");
    if (cAfter) TS.render.init(cAfter, "after");

    // 5. Sim.
    TS.sim.init();

    // 6. UI.
    TS.ui.init();

    // 7. Presentation.
    TS.presentation.init();

    // Hotspot markers on the map (clickable) — open the UI popups.
    if (mapOk && TS.map.addHotspots) {
      TS.map.addHotspots(function (id) { TS.ui.openHotspot(id); });
    }
    // Also wire the in-page hotspot button list (works with or without Leaflet).
    wireHotspotButtons();

    // Keep canvases sized to their containers (CLS-safe + crisp).
    if (TS.map.onResize) TS.map.onResize(function () { TS.render.resize(); });
    window.addEventListener("resize", debounce(function () {
      TS.render.resize();
      if (!TS.config.playing || TS.config.reducedMotion) TS.render.staticFrame();
    }, 150));

    // 8. Visibility + off-screen pause.
    document.addEventListener("visibilitychange", function () {
      TS.config.visible = !document.hidden && TS.config._inView !== false;
      reconcileLoop();
    });
    attachIntersectionObserver();

    // 9. Apply preset + start (or freeze to static frame).
    TS.ui.setPreset(TS.config.preset);
    TS.sim.setScenario(TS.config.activeScenarioId);
    if (reduced) {
      TS.config.playing = false;
      TS.ui.requestPlayStateUI();
      TS.render.staticFrame();
    } else {
      TS.sim.start();
    }
  }

  function wireHotspotButtons() {
    var list = document.getElementById("ts-hotspot-list");
    if (!list) return;
    list.innerHTML = "";
    TS.DATA.hotspots.forEach(function (h) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ts-hotspot-btn";
      btn.textContent = h.label;
      btn.addEventListener("click", function () { TS.ui.openHotspot(h.id); });
      list.appendChild(btn);
    });
  }

  function attachIntersectionObserver() {
    var stage = document.getElementById("ts-sim-section");
    if (!stage || typeof IntersectionObserver === "undefined") return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        TS.config._inView = en.isIntersecting;
        TS.config.visible = en.isIntersecting && !document.hidden;
        reconcileLoop();
      });
    }, { threshold: 0.08 });
    io.observe(stage);
  }

  function reconcileLoop() {
    if (TS.config.reducedMotion) { TS.render.staticFrame(); return; }
    if (TS.config.playing && TS.config.visible) TS.sim.start();
    else TS.sim.stop();
  }

  function debounce(fn, ms) {
    var t = null;
    return function () { clearTimeout(t); t = setTimeout(fn, ms); };
  }

  function deepFreeze(o) {
    Object.getOwnPropertyNames(o).forEach(function (k) {
      var v = o[k];
      if (v && typeof v === "object" && !Object.isFrozen(v)) deepFreeze(v);
    });
    return Object.freeze(o);
  }

  TS.boot = boot;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
