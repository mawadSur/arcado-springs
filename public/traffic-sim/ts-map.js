/* ============================================================================
 * Arcado Springs Traffic Simulator — MAP (window.TS.map)
 * Locked Leaflet basemap with Esri World Imagery, fixed site coordinates (no
 * external geocode), per-preset setView (animated, infrequent — NOT per frame),
 * project-boundary circle, accessible hotspot markers. Degrades gracefully if
 * Leaflet (L) is unavailable: the canvas sim still runs.
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  var map = null;
  var available = false;
  var containerEl = null;
  var siteLatLng = null;
  var boundaryCircle = null;
  var hotspotMarkers = {};
  var resizeCbs = [];
  var onHotspotClick = null;

  function leafletReady() {
    return typeof window.L !== "undefined" && window.L && typeof window.L.map === "function";
  }

  function init(elId) {
    containerEl = document.getElementById(elId);
    if (!containerEl) return false;
    if (!leafletReady()) {
      // Leaflet failed to load (e.g. CDN blocked). Mark unavailable; sim runs.
      containerEl.classList.add("map-unavailable");
      containerEl.setAttribute("aria-hidden", "true");
      available = false;
      return false;
    }
    var L = window.L;
    var D = TS.DATA.mapCenter;
    var fb = [D.fallback.lat, D.fallback.lng];

    try {
      map = L.map(elId, {
        dragging: false,
        scrollWheelZoom: false,
        doubleClickZoom: false,
        boxZoom: false,
        keyboard: false,
        touchZoom: false,
        zoomControl: false,
        attributionControl: true
      }).setView(fb, D.defaultZoom);

      L.tileLayer(D.tiles.url, {
        maxZoom: D.tiles.maxZoom,
        attribution: D.tiles.attribution
      }).addTo(map);

      available = true;
      siteLatLng = fb.slice();
      drawBoundary();

      // Use the known-correct fallback coordinates for the address; the map
      // view is locked to presets anyway, so no external geocode is needed.
      setPreset((TS.config && TS.config.preset) || "topdown");
      notifyResize();

      window.addEventListener("resize", notifyResize);
      return true;
    } catch (e) {
      available = false;
      return false;
    }
  }

  function drawBoundary() {
    if (!available || !siteLatLng) return;
    var L = window.L;
    if (boundaryCircle) { map.removeLayer(boundaryCircle); boundaryCircle = null; }
    boundaryCircle = L.circle(siteLatLng, {
      radius: 150, color: "#B08D57", weight: 2,
      fillColor: "#2F5D3A", fillOpacity: 0.12, interactive: false
    }).addTo(map);
  }

  /* Add clickable hotspot markers. Positions are normalized to the corridor,
     so we place them around the site center with small lat/lng offsets that
     mirror the canvas layout. They open the same popups as canvas hotspots. */
  function addHotspots(cb) {
    onHotspotClick = cb;
    if (!available || !siteLatLng) return;
    var L = window.L;
    var lat0 = siteLatLng[0], lng0 = siteLatLng[1];
    // Map normalized (x,y) over a ~600m box centered on site.
    var span = 0.004; // ~lat/lng span across the corridor frame
    TS.DATA.hotspots.forEach(function (h) {
      var dx = (h.position.x - 0.5) * span * 1.6;
      var dy = (0.5 - h.position.y) * span;
      var ll = [lat0 + dy, lng0 + dx];
      var icon = L.divIcon({
        className: "ts-hotspot-icon",
        html: '<span class="ts-hotspot-dot" aria-hidden="true"></span>',
        iconSize: [18, 18]
      });
      var m = L.marker(ll, { icon: icon, keyboard: true, title: h.label, alt: h.label }).addTo(map);
      m.on("click", function () { if (onHotspotClick) onHotspotClick(h.id); });
      hotspotMarkers[h.id] = m;
    });
  }

  function setPreset(presetId) {
    if (!available) return;
    var p = TS.DATA.mapCenter.presets[presetId];
    if (!p) return;
    // Center on site if geocoded, applying the preset's relative zoom + nudge.
    var lat = siteLatLng ? siteLatLng[0] : p.lat;
    var lng = siteLatLng ? siteLatLng[1] : p.lng;
    // Intersection zoom nudges east toward the Killian Hill corner.
    if (presetId === "intersectionZoom") lng += 0.0012;
    map.setView([lat, lng], p.zoom, { animate: true, duration: 0.6 });
  }

  function getContainerSize() {
    if (!containerEl) return { w: 0, h: 0 };
    var r = containerEl.getBoundingClientRect();
    return { w: Math.round(r.width), h: Math.round(r.height) };
  }

  function onResize(cb) { if (typeof cb === "function") resizeCbs.push(cb); }
  function notifyResize() {
    if (available && map) { try { map.invalidateSize(false); } catch (e) {} }
    var sz = getContainerSize();
    resizeCbs.forEach(function (cb) { try { cb(sz); } catch (e) {} });
  }

  function isAvailable() { return available; }

  TS.map = {
    init: init,
    setPreset: setPreset,
    addHotspots: addHotspots,
    getContainerSize: getContainerSize,
    onResize: onResize,
    isAvailable: isAvailable
  };
})();
