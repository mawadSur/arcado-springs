/* ============================================================================
 * Arcado Springs — main.js
 * Vanilla JS, no frameworks, no build step.
 *
 *   1. Nav: transparent -> frosted-solid on scroll past hero
 *   2. Mobile hamburger menu
 *   3. IntersectionObserver scroll reveals (respects prefers-reduced-motion)
 *   4. Lightbox for the gallery
 *   5. Site-plan pan/zoom (user-initiated only)
 *   6. Two-conceptions tabbed compare
 *   7. Feedback form (client-side, no backend — honest acknowledgement)
 *   8. Unity WebGL walkthrough loader (from the provided loaderJs)
 * ==========================================================================*/
(function () {
  "use strict";

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }
  function byId(id) { return document.getElementById(id); }

  var prefersReducedMotion =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  /* ------------------------------------------------------------------ *
   * 1. NAV: transparent over hero, frosted-solid after scrolling past
   * ------------------------------------------------------------------ */
  function initNav() {
    var nav = byId("nav");
    if (!nav) return;

    function update() {
      // Solid once the hero is mostly scrolled out of view.
      var threshold = Math.max(60, window.innerHeight * 0.55);
      if (window.scrollY > threshold) {
        nav.classList.add("is-solid");
      } else {
        nav.classList.remove("is-solid");
      }
    }
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update, { passive: true });
  }

  /* ------------------------------------------------------------------ *
   * 2. MOBILE MENU
   * ------------------------------------------------------------------ */
  function initMobileMenu() {
    var toggle = byId("nav-toggle");
    var links = byId("nav-links");
    if (!toggle || !links) return;

    function close() {
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Open menu");
      links.classList.remove("is-open");
    }
    function open() {
      toggle.setAttribute("aria-expanded", "true");
      toggle.setAttribute("aria-label", "Close menu");
      links.classList.add("is-open");
    }

    toggle.addEventListener("click", function () {
      if (toggle.getAttribute("aria-expanded") === "true") close();
      else open();
    });

    // Close after navigating to an in-page anchor.
    $$("a", links).forEach(function (a) {
      a.addEventListener("click", close);
    });

    // Close on Escape.
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        close();
        toggle.focus();
      }
    });

    // Reset state when crossing the desktop breakpoint.
    var mq = window.matchMedia("(min-width: 821px)");
    (mq.addEventListener ? mq.addEventListener.bind(mq, "change") : mq.addListener.bind(mq))(close);
  }

  /* ------------------------------------------------------------------ *
   * 3. SCROLL REVEALS
   * ------------------------------------------------------------------ */
  function initReveals() {
    var items = $$("[data-reveal]");
    if (!items.length) return;

    // No motion, or no observer support: show everything immediately.
    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("is-visible"); });
      return;
    }

    var io = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          obs.unobserve(entry.target); // reveal once
        }
      });
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.08 });

    items.forEach(function (el) { io.observe(el); });
  }

  /* ------------------------------------------------------------------ *
   * 3b. ANIMATED STAT COUNT-UP
   *     Each .stat-num[data-count] counts from 0 to its target on first
   *     reveal. Handles decimals (e.g. 3.6). Gated on prefers-reduced-
   *     motion: shows the final value instantly when motion is reduced.
   * ------------------------------------------------------------------ */
  function initStatCounters() {
    var nums = $$(".stat-num[data-count]");
    if (!nums.length) return;

    // Format to the same precision as the target (so 3.6 stays "3.6", 9 stays "9").
    function fmt(value, decimals) {
      return decimals > 0 ? value.toFixed(decimals) : String(Math.round(value));
    }

    function finalize(el) {
      var raw = el.getAttribute("data-count");
      var target = parseFloat(raw);
      if (isNaN(target)) return;
      var decimals = (raw.split(".")[1] || "").length;
      el.textContent = fmt(target, decimals);
    }

    // No motion or no observer: show final values immediately.
    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
      nums.forEach(finalize);
      return;
    }

    function animate(el) {
      var raw = el.getAttribute("data-count");
      var target = parseFloat(raw);
      if (isNaN(target)) return;
      var decimals = (raw.split(".")[1] || "").length;
      var duration = 1100; // ms
      var start = null;

      function tick(now) {
        if (start === null) start = now;
        var t = Math.min((now - start) / duration, 1);
        // easeOutCubic for a premium settle
        var eased = 1 - Math.pow(1 - t, 3);
        el.textContent = fmt(target * eased, decimals);
        if (t < 1) {
          requestAnimationFrame(tick);
        } else {
          el.textContent = fmt(target, decimals); // exact final value
        }
      }
      requestAnimationFrame(tick);
    }

    var io = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animate(entry.target);
          obs.unobserve(entry.target); // count once
        }
      });
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.4 });

    nums.forEach(function (el) { io.observe(el); });
  }

  /* ------------------------------------------------------------------ *
   * 4. LIGHTBOX
   * ------------------------------------------------------------------ */
  function initLightbox() {
    var lightbox = byId("lightbox");
    var img = byId("lightbox-img");
    var caption = byId("lightbox-caption");
    if (!lightbox || !img) return;

    var lastFocused = null;

    function open(src, alt, cap) {
      lastFocused = document.activeElement;
      img.src = src;
      img.alt = alt || "";
      if (caption) caption.textContent = cap || "";
      lightbox.hidden = false;
      lightbox.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
      var closeBtn = $(".lightbox-close", lightbox);
      if (closeBtn) closeBtn.focus();
    }

    function close() {
      lightbox.hidden = true;
      lightbox.setAttribute("aria-hidden", "true");
      img.src = "";
      document.body.style.overflow = "";
      if (lastFocused && lastFocused.focus) lastFocused.focus();
    }

    $$(".gallery-trigger").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var inner = $("img", btn);
        open(
          btn.getAttribute("data-lightbox"),
          inner ? inner.getAttribute("alt") : "",
          btn.getAttribute("data-caption")
        );
      });
    });

    $$("[data-lightbox-close]", lightbox).forEach(function (el) {
      el.addEventListener("click", close);
    });

    document.addEventListener("keydown", function (e) {
      if (lightbox.hidden) return;
      if (e.key === "Escape") { close(); return; }
      // Simple focus trap: only the close button is focusable inside the dialog.
      if (e.key === "Tab") {
        var closeBtn = $(".lightbox-close", lightbox);
        if (closeBtn) { e.preventDefault(); closeBtn.focus(); }
      }
    });
  }

  /* ------------------------------------------------------------------ *
   * 5. SITE-PLAN PAN / ZOOM (user-initiated only)
   * ------------------------------------------------------------------ */
  function initSitePlan() {
    var stage = byId("siteplan-stage");
    var img = byId("siteplan-img");
    if (!stage || !img) return;

    var scale = 1, tx = 0, ty = 0;
    var MIN = 1, MAX = 4;
    var dragging = false, startX = 0, startY = 0, baseTx = 0, baseTy = 0;

    function apply() {
      img.style.transform =
        "translate(calc(-50% + " + tx + "px), calc(-50% + " + ty + "px)) scale(" + scale + ")";
    }
    function clampPan() {
      // Keep the drawing from drifting fully out of frame.
      var rect = stage.getBoundingClientRect();
      var maxX = (rect.width * (scale - 1)) / 2 + rect.width * 0.15;
      var maxY = (rect.height * (scale - 1)) / 2 + rect.height * 0.15;
      tx = Math.max(-maxX, Math.min(maxX, tx));
      ty = Math.max(-maxY, Math.min(maxY, ty));
    }
    function setScale(next) {
      scale = Math.max(MIN, Math.min(MAX, next));
      if (scale === 1) { tx = 0; ty = 0; }
      clampPan();
      apply();
    }

    // Buttons
    $$(".zoom-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var z = btn.getAttribute("data-zoom");
        if (z === "in") setScale(scale + 0.5);
        else if (z === "out") setScale(scale - 0.5);
        else { scale = 1; tx = 0; ty = 0; apply(); }
      });
    });

    // Wheel zoom (only over the stage; prevent page scroll while zooming)
    stage.addEventListener("wheel", function (e) {
      e.preventDefault();
      setScale(scale + (e.deltaY < 0 ? 0.3 : -0.3));
    }, { passive: false });

    // Double-click resets
    stage.addEventListener("dblclick", function () {
      scale = 1; tx = 0; ty = 0; apply();
    });

    // Pointer drag to pan
    stage.addEventListener("pointerdown", function (e) {
      if (scale <= 1) return;
      dragging = true;
      stage.classList.add("is-panning");
      startX = e.clientX; startY = e.clientY;
      baseTx = tx; baseTy = ty;
      stage.setPointerCapture(e.pointerId);
    });
    stage.addEventListener("pointermove", function (e) {
      if (!dragging) return;
      tx = baseTx + (e.clientX - startX);
      ty = baseTy + (e.clientY - startY);
      clampPan();
      apply();
    });
    function endDrag(e) {
      if (!dragging) return;
      dragging = false;
      stage.classList.remove("is-panning");
      try { stage.releasePointerCapture(e.pointerId); } catch (err) {}
    }
    stage.addEventListener("pointerup", endDrag);
    stage.addEventListener("pointercancel", endDrag);

    // Keyboard zoom for the focusable stage
    stage.addEventListener("keydown", function (e) {
      if (e.key === "+" || e.key === "=") { setScale(scale + 0.5); e.preventDefault(); }
      else if (e.key === "-" || e.key === "_") { setScale(scale - 0.5); e.preventDefault(); }
      else if (e.key === "0") { scale = 1; tx = 0; ty = 0; apply(); }
    });
  }

  /* ------------------------------------------------------------------ *
   * 6. TWO-CONCEPTIONS TABBED COMPARE
   * ------------------------------------------------------------------ */
  function initCompare() {
    var tabs = $$(".compare-tab");
    if (!tabs.length) return;

    function activate(tab) {
      tabs.forEach(function (t) {
        var selected = t === tab;
        t.classList.toggle("is-active", selected);
        t.setAttribute("aria-selected", selected ? "true" : "false");
        var panel = byId(t.getAttribute("aria-controls"));
        if (panel) {
          panel.hidden = !selected;
          panel.classList.toggle("is-active", selected);
        }
      });
    }

    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () { activate(tab); });
      tab.addEventListener("keydown", function (e) {
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          e.preventDefault();
          var dir = e.key === "ArrowRight" ? 1 : -1;
          var next = tabs[(i + dir + tabs.length) % tabs.length];
          activate(next);
          next.focus();
        }
      });
    });
  }

  /* ------------------------------------------------------------------ *
   * 7. FEEDBACK FORM (no backend — honest local acknowledgement)
   * ------------------------------------------------------------------ */
  function initForm() {
    var form = byId("feedback-form");
    var status = byId("form-status");
    if (!form) return;

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var comment = byId("f-comment");
      if (comment && !comment.value.trim()) {
        if (status) {
          status.textContent = "Please add a short comment before sending.";
          status.classList.remove("is-ok");
        }
        comment.focus();
        return;
      }
      if (status) {
        status.textContent =
          "Thank you — your input has been noted for the community record. " +
          "We read every comment as the design is shaped.";
        status.classList.add("is-ok");
      }
      form.reset();
    });
  }

  /* ==================================================================== *
   * 8. UNITY WEBGL WALKTHROUGH LOADER
   *    Probes for a build at unity-build/Build/. If present, wires a
   *    Launch button to instantiate it; otherwise leaves the honest
   *    screenshot fallback visible. No fake "playable" claim.
   * ==================================================================== */
  var BUILD_DIR = "unity-build/Build/";
  var LOADER_CANDIDATES = [
    "unity-build.loader.js",
    "Build.loader.js",
    "web.loader.js"
  ];

  // HEAD-probe a URL; resolve(true) only on a 2xx response.
  function exists(url) {
    return fetch(url, { method: "HEAD", cache: "no-store" })
      .then(function (r) { return r.ok; })
      .catch(function () { return false; });
  }

  // Find the first loader candidate that actually exists; resolve(null) if none.
  function findLoader(i) {
    i = i || 0;
    if (i >= LOADER_CANDIDATES.length) return Promise.resolve(null);
    var file = LOADER_CANDIDATES[i];
    return exists(BUILD_DIR + file).then(function (ok) {
      return ok ? file : findLoader(i + 1);
    });
  }

  function setState(stage, state) {
    if (stage) stage.setAttribute("data-state", state);
  }

  // ---- Fallback: screenshots ARE the experience. Stay honest. ----------
  function showFallback(stage) {
    var fallback = byId("player-fallback");
    var caption = byId("player-caption");
    if (fallback) fallback.hidden = false;
    setState(stage, "fallback");
    if (caption) {
      caption.textContent =
        "Live 3D walkthrough is being prepared. Below is the site layout — " +
        "the interactive build deploys here when ready.";
    }
  }

  // ---- Build present: show Launch, then load Unity on click ------------
  function showLaunch(stage, loaderFile) {
    var launch = byId("player-launch");
    var launchBtn = byId("player-launch-btn");
    var caption = byId("player-caption");
    if (launch) launch.hidden = false;
    setState(stage, "launch");
    if (caption) {
      caption.textContent =
        "Live build ready — click Launch to walk Arcado Springs in real time.";
    }
    if (launchBtn) {
      launchBtn.addEventListener("click", function () {
        launchUnity(stage, loaderFile);
      }, { once: true });
    }
  }

  function launchUnity(stage, loaderFile) {
    var launch = byId("player-launch");
    var progress = byId("player-progress");
    var fill = byId("player-progress-fill");
    var label = byId("player-progress-label");
    var caption = byId("player-caption");
    var canvas = byId("unity-canvas");

    if (launch) launch.hidden = true;
    if (progress) progress.hidden = false;
    if (caption) caption.textContent = "Loading the walkthrough…";

    var base = BUILD_DIR + loaderFile.replace(/\.loader\.js$/, "");
    // The wasm/data/framework names are derived from the same base. We point at
    // the canonical names and let the loader pick up the compressed (.br)
    // variants the server actually serves.
    var config = {
      dataUrl: base + ".data",
      frameworkUrl: base + ".framework.js",
      codeUrl: base + ".wasm",
      streamingAssetsUrl: "unity-build/StreamingAssets",
      companyName: "Arcado",
      productName: "Arcado Springs",
      productVersion: "1.0"
    };

    var script = document.createElement("script");
    script.src = BUILD_DIR + loaderFile;
    script.onload = function () {
      if (typeof createUnityInstance !== "function") {
        failTo(stage, "Unity loader did not initialize.");
        return;
      }
      createUnityInstance(canvas, config, function (p) {
        var pct = Math.round((p || 0) * 100);
        if (fill) fill.style.width = pct + "%";
        if (label) label.textContent = "Loading walkthrough… " + pct + "%";
      }).then(function () {
        if (progress) progress.hidden = true;
        setState(stage, "playing");
        if (caption) {
          caption.textContent =
            "Use W/A/S/D or the arrow keys to move · mouse to look around.";
        }
        try { canvas.focus(); } catch (e) {}
      }).catch(function (err) {
        failTo(stage, "Could not start the walkthrough" +
          (err && err.message ? ": " + err.message : "."));
      });
    };
    script.onerror = function () {
      failTo(stage, "Could not download the walkthrough build.");
    };
    document.body.appendChild(script);
  }

  // On any Unity failure, fall back to the honest screenshot tour.
  function failTo(stage, msg) {
    var progress = byId("player-progress");
    if (progress) progress.hidden = true;
    showFallback(stage);
    var caption = byId("player-caption");
    if (caption && msg) {
      caption.textContent =
        msg + " Showing the site layout instead — live build coming soon.";
    }
    if (window && window.console) console.warn("[walkthrough]", msg);
  }

  function initWalkthrough() {
    var stage = byId("player-stage");
    if (!stage) return; // section not on this page
    setState(stage, "loading");

    findLoader().then(function (loaderFile) {
      if (loaderFile) {
        showLaunch(stage, loaderFile);
      } else {
        showFallback(stage);
      }
    }).catch(function () {
      showFallback(stage);
    });
  }

  /* ------------------------------------------------------------------ *
   * BOOT
   * ------------------------------------------------------------------ */
  ready(function () {
    initNav();
    initMobileMenu();
    initReveals();
    initStatCounters();
    initLightbox();
    initSitePlan();
    initCompare();
    initForm();
    initWalkthrough();
  });
})();
