/* ============================================================================
 * Arcado Springs Traffic Simulator — UI (window.TS.ui)
 * Wires scenario picker, mode (split/toggle), before/after toggle, play/pause,
 * timeline slider, layer checkboxes, hotspot popups, metric cards. Full
 * keyboard operability + ARIA. Honesty label sits beside the metrics.
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  var els = {};

  function $(id) { return document.getElementById(id); }
  function scenarioById(id) {
    for (var i = 0; i < TS.DATA.scenarios.length; i++) if (TS.DATA.scenarios[i].id === id) return TS.DATA.scenarios[i];
    return TS.DATA.scenarios[0];
  }
  function metricDef(id) {
    for (var i = 0; i < TS.DATA.metrics.length; i++) if (TS.DATA.metrics[i].id === id) return TS.DATA.metrics[i];
    return null;
  }

  function init() {
    cacheEls();
    buildScenarioOptions();
    buildLayerToggles();
    buildMetricCards();
    wireControls();
    applyModeUI();
    setScenarioLabel();
    requestPlayStateUI();
  }

  function cacheEls() {
    els.scenario = $("ts-scenario");
    els.modeSplit = $("ts-mode-split");
    els.modeToggle = $("ts-mode-toggle");
    els.sideGroup = $("ts-side-group");
    els.sideBefore = $("ts-side-before");
    els.sideAfter = $("ts-side-after");
    els.play = $("ts-play");
    els.timeline = $("ts-timeline");
    els.timeLabel = $("ts-time-label");
    els.cams = document.querySelectorAll("[data-cam]");
    els.layers = $("ts-layers");
    els.metrics = $("ts-metrics");
    els.scenarioPill = $("ts-scenario-pill");
    els.stageBefore = $("ts-stage-before");
    els.stageAfter = $("ts-stage-after");
    els.popup = $("ts-popup");
    els.popupTitle = $("ts-popup-title");
    els.popupBefore = $("ts-popup-before");
    els.popupAfter = $("ts-popup-after");
    els.popupClose = $("ts-popup-close");
  }

  function buildScenarioOptions() {
    if (!els.scenario) return;
    els.scenario.innerHTML = "";
    TS.DATA.scenarios.forEach(function (s) {
      var o = document.createElement("option");
      o.value = s.id; o.textContent = s.label;
      els.scenario.appendChild(o);
    });
    els.scenario.value = TS.config.activeScenarioId;
  }

  function buildLayerToggles() {
    if (!els.layers) return;
    els.layers.innerHTML = "";
    TS.DATA.layers.forEach(function (lyr) {
      var id = "ts-layer-" + lyr.id;
      var wrap = document.createElement("label");
      wrap.className = "ts-layer-opt";
      wrap.setAttribute("for", id);
      var cb = document.createElement("input");
      cb.type = "checkbox"; cb.id = id; cb.checked = !!TS.config.layers[lyr.id];
      cb.setAttribute("aria-describedby", id + "-d");
      cb.addEventListener("change", function () {
        TS.config.layers[lyr.id] = cb.checked;
        rerenderStatic();
      });
      var txt = document.createElement("span");
      txt.textContent = lyr.label;
      var desc = document.createElement("span");
      desc.id = id + "-d"; desc.className = "ts-sr-only"; desc.textContent = lyr.description;
      wrap.appendChild(cb); wrap.appendChild(txt); wrap.appendChild(desc);
      els.layers.appendChild(wrap);
    });
  }

  function buildMetricCards() {
    if (!els.metrics) return;
    els.metrics.innerHTML = "";
    TS.DATA.metrics.forEach(function (m) {
      var card = document.createElement("div");
      card.className = "ts-metric-card";
      card.innerHTML =
        '<div class="ts-metric-label">' + esc(m.label) + ' <span class="ts-metric-unit">' + esc(m.unit) + '</span></div>' +
        '<div class="ts-metric-row">' +
          '<div class="ts-metric-col"><span class="ts-metric-tag">Before</span><span class="ts-metric-val" id="m-' + m.id + '-before">—</span></div>' +
          '<div class="ts-metric-arrow" aria-hidden="true">' +
            '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>' +
          '</div>' +
          '<div class="ts-metric-col"><span class="ts-metric-tag">After</span><span class="ts-metric-val ts-metric-val--after" id="m-' + m.id + '-after">—</span></div>' +
        '</div>' +
        '<div class="ts-metric-delta" id="m-' + m.id + '-delta">—</div>';
      els.metrics.appendChild(card);
    });
  }

  function wireControls() {
    if (els.scenario) els.scenario.addEventListener("change", function () {
      TS.sim.setScenario(els.scenario.value);
      setScenarioLabel();
      setTimeFromSlider();
      rerenderStatic();
    });

    if (els.modeSplit) els.modeSplit.addEventListener("click", function () { setMode("split"); });
    if (els.modeToggle) els.modeToggle.addEventListener("click", function () { setMode("toggle"); });
    if (els.sideBefore) els.sideBefore.addEventListener("click", function () { setSide("before"); });
    if (els.sideAfter) els.sideAfter.addEventListener("click", function () { setSide("after"); });

    if (els.play) els.play.addEventListener("click", togglePlay);

    if (els.timeline) {
      els.timeline.addEventListener("input", function () { setTimeFromSlider(); rerenderStatic(); });
    }

    Array.prototype.forEach.call(els.cams, function (btn) {
      btn.addEventListener("click", function () {
        var p = btn.getAttribute("data-cam");
        setPreset(p);
        Array.prototype.forEach.call(els.cams, function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      });
    });

    if (els.popupClose) els.popupClose.addEventListener("click", closeHotspot);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && els.popup && !els.popup.hidden) closeHotspot();
    });
  }

  function setMode(m) {
    TS.config.mode = m;
    TS.sim.setMode(m);
    applyModeUI();
    rebindRenderers();
    setPreset(TS.config.preset);
    rerenderStatic();
  }
  function applyModeUI() {
    var split = TS.config.mode === "split";
    if (els.modeSplit) els.modeSplit.setAttribute("aria-pressed", String(split));
    if (els.modeToggle) els.modeToggle.setAttribute("aria-pressed", String(!split));
    if (els.sideGroup) els.sideGroup.hidden = split;
    if (els.stageAfter) els.stageAfter.hidden = !split;
    if (els.stageBefore) {
      var lbl = els.stageBefore.querySelector(".ts-stage-tag");
      if (lbl) lbl.textContent = split ? "Existing · today" : (TS.config.side === "after" ? "Proposed · Arcado Springs" : "Existing · today");
    }
    if (!split) updateSideUI();
  }
  function setSide(side) {
    TS.config.side = side;
    TS.sim.setSide(side);
    updateSideUI();
    rerenderStatic();
  }
  function updateSideUI() {
    if (els.sideBefore) els.sideBefore.setAttribute("aria-pressed", String(TS.config.side === "before"));
    if (els.sideAfter) els.sideAfter.setAttribute("aria-pressed", String(TS.config.side === "after"));
    if (els.stageBefore) {
      var lbl = els.stageBefore.querySelector(".ts-stage-tag");
      if (lbl) lbl.textContent = TS.config.side === "after" ? "Proposed · Arcado Springs" : "Existing · today";
    }
  }

  /* Renderers must be (re)bound when toggling split (2 canvases) vs toggle (1). */
  function rebindRenderers() {
    var cBefore = $("ts-canvas-before");
    var cAfter = $("ts-canvas-after");
    if (cBefore) TS.render.init(cBefore, "before");
    if (TS.config.mode === "split" && cAfter) TS.render.init(cAfter, "after");
    else if (cAfter) TS.render.init(cAfter, "after"); // keep bound; hidden by CSS
  }

  function togglePlay() {
    TS.config.playing = !TS.config.playing;
    requestPlayStateUI();
    if (TS.config.playing && TS.config.visible) TS.sim.start();
    else TS.sim.stop();
  }
  function requestPlayStateUI() {
    if (!els.play) return;
    var playing = TS.config.playing;
    els.play.setAttribute("aria-pressed", String(playing));
    els.play.setAttribute("aria-label", playing ? "Pause animation" : "Play animation");
    var icon = playing
      ? '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>'
      : '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';
    els.play.innerHTML = icon + '<span>' + (playing ? "Pause" : "Play") + '</span>';
  }

  function setPreset(p) {
    TS.config.preset = p;
    if (TS.map && TS.map.setPreset) TS.map.setPreset(p);
    if (TS.render && TS.render.setPreset) TS.render.setPreset(p);
    rerenderStatic();
  }

  function setTimeFromSlider() {
    if (!els.timeline) return;
    var t = parseFloat(els.timeline.value) / 100;
    TS.sim.setTimeT(t);
    updateTimeLabel(t);
  }
  function updateTimeLabel(t) {
    if (!els.timeLabel) return;
    var s = scenarioById(TS.config.activeScenarioId);
    els.timeLabel.textContent = lerpClock(s.timeWindow.start, s.timeWindow.end, t);
  }
  function lerpClock(start, end, t) {
    var m1 = parseClock(start), m2 = parseClock(end);
    var m = Math.round(m1 + (m2 - m1) * t);
    return fmtClock(m);
  }
  function parseClock(str) {
    var mm = str.match(/(\d+):(\d+)\s*(AM|PM)/i);
    if (!mm) return 0;
    var h = parseInt(mm[1], 10) % 12, min = parseInt(mm[2], 10);
    if (/pm/i.test(mm[3])) h += 12;
    return h * 60 + min;
  }
  function fmtClock(total) {
    total = (total + 1440) % 1440;
    var h = Math.floor(total / 60), m = total % 60;
    var ap = h >= 12 ? "PM" : "AM";
    var h12 = h % 12; if (h12 === 0) h12 = 12;
    return h12 + ":" + (m < 10 ? "0" + m : m) + " " + ap;
  }

  function setScenarioLabel() {
    var s = scenarioById(TS.config.activeScenarioId);
    if (els.scenario) els.scenario.value = s.id;
    if (els.scenarioPill) {
      els.scenarioPill.innerHTML =
        '<span class="ts-pill-time">' + esc(s.timeWindow.start) + " – " + esc(s.timeWindow.end) + '</span>';
    }
    if (els.timeline) { els.timeline.value = "50"; TS.sim.setTimeT(0.5); }
    updateTimeLabel(0.5);
  }

  /* Metrics: large numbers, deltas, LOS badges, per-metric lowerIsBetter color. */
  function syncMetrics(beforeVals, afterVals) {
    TS.DATA.metrics.forEach(function (m) {
      var bEl = $("m-" + m.id + "-before");
      var aEl = $("m-" + m.id + "-after");
      var dEl = $("m-" + m.id + "-delta");
      if (!bEl || !aEl || !dEl) return;
      var bv = beforeVals[m.id], av = afterVals[m.id];
      if (m.format === "grade") {
        bEl.textContent = bv; aEl.textContent = av;
        bEl.className = "ts-metric-val ts-los los-" + String(bv).toLowerCase();
        aEl.className = "ts-metric-val ts-metric-val--after ts-los los-" + String(av).toLowerCase();
        var bi = m.scale.indexOf(bv), ai = m.scale.indexOf(av);
        dEl.textContent = ai < bi ? (bv + " to " + av + " — improved") : (av === bv ? "no change" : av);
        dEl.className = "ts-metric-delta " + (ai < bi ? "is-better" : "is-neutral");
        return;
      }
      bEl.textContent = fmtNum(bv, m); aEl.textContent = fmtNum(av, m);
      var improved = m.lowerIsBetter ? av < bv : av > bv;
      var pct = computePct(bv, av, m.lowerIsBetter);
      dEl.textContent = (improved ? (m.lowerIsBetter ? "−" : "+") : "") + Math.abs(pct) + "% " + (improved ? (m.lowerIsBetter ? "reduction" : "increase") : "change");
      dEl.className = "ts-metric-delta " + (improved ? "is-better" : "is-neutral");
    });
  }
  function computePct(bv, av, lowerIsBetter) {
    if (!bv) return 0;
    var raw = ((av - bv) / bv) * 100;
    return Math.round(Math.abs(raw));
  }
  function fmtNum(v, m) {
    if (v === null || v === undefined) return "—";
    if (m.format === "decimal") return (Math.round(v * 10) / 10).toFixed(m.decimals);
    return String(Math.round(v));
  }

  function rerenderStatic() {
    // When paused or reduced-motion, redraw a single representative frame.
    if (!TS.config.playing || TS.config.reducedMotion) {
      if (TS.render && TS.render.staticFrame) TS.render.staticFrame();
    }
  }

  /* ---- hotspot popups ---- */
  var popupTrigger = null;

  function focusableIn(root) {
    if (!root) return [];
    var sel = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    return Array.prototype.filter.call(root.querySelectorAll(sel), function (el) {
      return !el.disabled && el.offsetParent !== null;
    });
  }
  function trapFocus(e) {
    if (e.key !== "Tab" || !els.popup || els.popup.hidden) return;
    var panel = els.popup.querySelector(".ts-popup-panel") || els.popup;
    var f = focusableIn(panel);
    if (!f.length) { e.preventDefault(); return; }
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault(); last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault(); first.focus();
    } else if (!els.popup.contains(document.activeElement)) {
      e.preventDefault(); first.focus();
    }
  }

  function openHotspot(id) {
    var h = null;
    for (var i = 0; i < TS.DATA.hotspots.length; i++) if (TS.DATA.hotspots[i].id === id) h = TS.DATA.hotspots[i];
    if (!h || !els.popup) return;
    // Remember the element that opened the dialog so focus can return to it.
    popupTrigger = (document.activeElement && document.activeElement !== document.body)
      ? document.activeElement : null;
    els.popupTitle.textContent = h.label;
    els.popupBefore.textContent = h.beforeText;
    els.popupAfter.textContent = h.afterText;
    els.popup.hidden = false;
    els.popup.setAttribute("aria-hidden", "false");
    document.addEventListener("keydown", trapFocus, true);
    if (els.popupClose) els.popupClose.focus();
  }
  function closeHotspot() {
    if (!els.popup) return;
    els.popup.hidden = true;
    els.popup.setAttribute("aria-hidden", "true");
    document.removeEventListener("keydown", trapFocus, true);
    // Return focus to the triggering control for accessible modal behavior.
    if (popupTrigger && typeof popupTrigger.focus === "function") {
      try { popupTrigger.focus(); } catch (e) {}
    }
    popupTrigger = null;
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  TS.ui = {
    init: init,
    syncMetrics: syncMetrics,
    openHotspot: openHotspot,
    closeHotspot: closeHotspot,
    setMode: setMode,
    setSide: setSide,
    setPreset: setPreset,
    requestPlayStateUI: requestPlayStateUI,
    setScenarioLabel: setScenarioLabel,
    applyLayers: function () { buildLayerToggles(); },
    applyScenario: function () { setScenarioLabel(); }
  };
})();
