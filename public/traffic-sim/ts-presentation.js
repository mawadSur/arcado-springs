/* ============================================================================
 * Arcado Springs Traffic Simulator — PRESENTATION (window.TS.presentation)
 * Guided-tour sequencer. Walks DATA.presentationSteps, applying each step's
 * preset + scenario + mode/side + layers + focusHotspot via the other modules.
 * Prev/Next/Exit buttons + arrow-key + Esc. Honors reduced-motion (static).
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  var overlay, titleEl, narrEl, counterEl, prevBtn, nextBtn, exitBtn, dotsEl;
  var idx = 0, open = false;
  var savedLayers = null;

  function init() {
    overlay = document.getElementById("ts-tour");
    titleEl = document.getElementById("ts-tour-title");
    narrEl = document.getElementById("ts-tour-narration");
    counterEl = document.getElementById("ts-tour-counter");
    prevBtn = document.getElementById("ts-tour-prev");
    nextBtn = document.getElementById("ts-tour-next");
    exitBtn = document.getElementById("ts-tour-exit");
    dotsEl = document.getElementById("ts-tour-dots");

    var startBtn = document.getElementById("ts-tour-start");
    if (startBtn) startBtn.addEventListener("click", start);
    if (prevBtn) prevBtn.addEventListener("click", prev);
    if (nextBtn) nextBtn.addEventListener("click", next);
    if (exitBtn) exitBtn.addEventListener("click", exit);

    document.addEventListener("keydown", onKey);
    buildDots();
  }

  function buildDots() {
    if (!dotsEl) return;
    dotsEl.innerHTML = "";
    TS.DATA.presentationSteps.forEach(function (s, i) {
      var d = document.createElement("span");
      d.className = "ts-tour-dot";
      d.setAttribute("role", "presentation");
      d.title = s.title;
      dotsEl.appendChild(d);
    });
  }

  function onKey(e) {
    if (!open) return;
    if (e.key === "ArrowRight") { e.preventDefault(); next(); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); prev(); }
    else if (e.key === "Escape") { e.preventDefault(); exit(); }
  }

  function start() {
    open = true;
    idx = 0;
    savedLayers = cloneLayers();
    if (overlay) {
      overlay.hidden = false;
      overlay.setAttribute("aria-hidden", "false");
    }
    document.body.classList.add("ts-tour-active");
    applyStep();
    if (exitBtn) exitBtn.focus();
  }

  function exit() {
    open = false;
    if (overlay) {
      overlay.hidden = true;
      overlay.setAttribute("aria-hidden", "true");
    }
    document.body.classList.remove("ts-tour-active");
    if (savedLayers) {
      TS.config.layers = savedLayers;
      if (TS.ui && TS.ui.applyLayers) TS.ui.applyLayers();
    }
    // Resume normal animation if appropriate.
    if (TS.config.playing && TS.config.visible && !TS.config.reducedMotion) TS.sim.start();
    else if (TS.render) TS.render.staticFrame();
  }

  function next() { if (idx < TS.DATA.presentationSteps.length - 1) { idx++; applyStep(); } else exit(); }
  function prev() { if (idx > 0) { idx--; applyStep(); } }

  function cloneLayers() {
    var o = {};
    for (var k in TS.config.layers) if (TS.config.layers.hasOwnProperty(k)) o[k] = TS.config.layers[k];
    return o;
  }

  function applyStep() {
    var step = TS.DATA.presentationSteps[idx];
    if (!step) return;

    // Scenario + mode/side.
    if (step.scenario) {
      if (step.scenario.id) TS.sim.setScenario(step.scenario.id);
      if (step.scenario.mode) { TS.config.mode = step.scenario.mode; TS.sim.setMode(step.scenario.mode); }
      if (step.scenario.side) { TS.config.side = step.scenario.side; TS.sim.setSide(step.scenario.side); }
      if (TS.ui) { TS.ui.setMode(TS.config.mode); if (step.scenario.side) TS.ui.setSide(step.scenario.side); }
      if (TS.ui && TS.ui.applyScenario) TS.ui.applyScenario();
    }

    // Layers: start from defaults, apply the step overrides.
    var base = {};
    TS.DATA.layers.forEach(function (l) { base[l.id] = !!l.defaultOn; });
    if (step.layers) for (var k in step.layers) if (step.layers.hasOwnProperty(k)) base[k] = step.layers[k];
    TS.config.layers = base;
    if (TS.ui && TS.ui.applyLayers) TS.ui.applyLayers();

    // Camera preset.
    if (step.preset && TS.ui && TS.ui.setPreset) TS.ui.setPreset(step.preset);

    // Narration + chrome.
    if (titleEl) titleEl.textContent = step.title;
    if (narrEl) narrEl.textContent = step.narration;
    if (counterEl) counterEl.textContent = (idx + 1) + " / " + TS.DATA.presentationSteps.length;
    updateDots();
    if (prevBtn) prevBtn.disabled = idx === 0;
    if (nextBtn) nextBtn.textContent = idx === TS.DATA.presentationSteps.length - 1 ? "Finish" : "Next";

    // Hotspot focus (open the popup so its before/after explanation shows).
    if (step.focusHotspot && TS.ui && TS.ui.openHotspot) TS.ui.openHotspot(step.focusHotspot);
    else if (TS.ui && TS.ui.closeHotspot) TS.ui.closeHotspot();

    // Render: animate unless reduced-motion.
    if (TS.config.reducedMotion) {
      if (TS.render) TS.render.staticFrame();
    } else if (TS.config.playing && TS.config.visible) {
      TS.sim.start();
    } else if (TS.render) {
      TS.render.staticFrame();
    }
  }

  function updateDots() {
    if (!dotsEl) return;
    var kids = dotsEl.children;
    for (var i = 0; i < kids.length; i++) {
      kids[i].setAttribute("aria-current", i === idx ? "true" : "false");
      kids[i].classList.toggle("is-active", i === idx);
    }
  }

  TS.presentation = {
    init: init,
    start: start,
    next: next,
    prev: prev,
    exit: exit
  };
})();
