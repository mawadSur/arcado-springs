/* ============================================================================
 * Arcado Springs Traffic Simulator — MAP (window.TS.map)
 * Leaflet IS the coordinate system. A LOCKED CARTO Voyager basemap frames the
 * site + Killian Hill junction; real road polylines (TS.CORRIDOR.roads) are
 * projected to container pixels via latLngToContainerPoint. Projection is
 * CACHED (projectAll) and recomputed ONLY on init / resize — never per
 * animation frame. Degrades gracefully if Leaflet (L) is unavailable:
 * a synthetic affine projection of CORRIDOR lat/lng lets the canvas sim run.
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  var map = null;
  var available = false;
  var containerEl = null;
  var parcelLayer = null;
  var hotspotMarkers = {};
  var resizeCbs = [];
  var reprojectCbs = [];
  var onHotspotClick = null;
  var lastCache = null;
  var fallbackSize = { w: 600, h: 360 };

  var C = function () { return TS.CORRIDOR; };

  function leafletReady() {
    return typeof window.L !== "undefined" && window.L && typeof window.L.map === "function";
  }

  /* ---- framed default view: tight box around site + intersection ---- */
  function framedBounds() {
    var co = C();
    var site = co.site, isx = co.intersection.ll;
    var minLat = site[0] - 0.006;
    var maxLat = isx[0] + 0.004;
    var minLng = Math.min(site[1], isx[1]) - 0.006;
    var maxLng = Math.max(site[1], isx[1]) + 0.006;
    return [[minLat, minLng], [maxLat, maxLng]];
  }

  function applyFramedView() {
    if (!map) return;
    map.fitBounds(framedBounds(), { padding: [12, 12], animate: false });
  }

  function init(elId) {
    containerEl = document.getElementById(elId);
    if (!containerEl) return false;
    if (!leafletReady()) {
      // Leaflet failed to load (e.g. CDN blocked). Mark unavailable; sim still
      // runs via a synthetic affine projection (see getProjection fallback).
      available = false;
      containerEl.classList.add("map-unavailable");
      return false;
    }
    var L = window.L;
    var co = C();

    try {
      map = L.map(elId, {
        dragging: false,
        scrollWheelZoom: false,
        doubleClickZoom: false,
        boxZoom: false,
        keyboard: false,
        touchZoom: false,
        zoomControl: false,
        attributionControl: true,
        zoomSnap: 0
      });

      L.tileLayer(co.basemap.voyager, {
        subdomains: "abcd",
        maxZoom: 20,
        attribution: co.basemap.attribution
      }).addTo(map);

      applyFramedView();
      available = true;
      drawParcel();

      // First projection after tiles/map ready.
      projectAll();
      notifyResize();

      return true;
    } catch (e) {
      available = false;
      return false;
    }
  }

  /* ~9-acre highlighted parcel box on the south side of Arcado Rd at the site. */
  function drawParcel() {
    if (!available) return;
    var L = window.L;
    if (parcelLayer) { map.removeLayer(parcelLayer); parcelLayer = null; }
    var s = C().site;
    // ~9 acres ≈ 36,400 m². A ~190m x 190m box, offset slightly south of the
    // Arcado Rd frontage. Lat degree ≈ 111,320 m; lng degree ≈ 92,500 m here.
    var dLat = 0.00085, dLng = 0.00115;
    var cLat = s[0] - 0.0006, cLng = s[1] - 0.0004;
    var ring = [
      [cLat + dLat, cLng - dLng],
      [cLat + dLat, cLng + dLng],
      [cLat - dLat, cLng + dLng],
      [cLat - dLat, cLng - dLng]
    ];
    parcelLayer = L.polygon(ring, {
      color: "#B08D57", weight: 2, fillColor: "#2F5D3A",
      fillOpacity: 0.12, interactive: false
    }).addTo(map);
  }

  /* ---- projection ---- */
  function project(lat, lng) {
    if (available && map) {
      var p = map.latLngToContainerPoint(window.L.latLng(lat, lng));
      return [p.x, p.y];
    }
    return affine(lat, lng);
  }

  // Synthetic fit-bounds affine used when Leaflet is unavailable so real road
  // SHAPES still render (Web-Mercator-ish; lng linear, lat linear over a small
  // span). Frames the same tight box as the live map.
  function affine(lat, lng) {
    var b = framedBounds();
    var minLat = b[0][0], minLng = b[0][1], maxLat = b[1][0], maxLng = b[1][1];
    var sz = getContainerSize();
    var w = sz.w || fallbackSize.w, h = sz.h || fallbackSize.h;
    var pad = 12;
    var iw = Math.max(1, w - pad * 2), ih = Math.max(1, h - pad * 2);
    var sx = iw / (maxLng - minLng);
    var sy = ih / (maxLat - minLat);
    var s = Math.min(sx, sy); // keep aspect, centered
    var offX = pad + (iw - s * (maxLng - minLng)) / 2;
    var offY = pad + (ih - s * (maxLat - minLat)) / 2;
    var px = offX + (lng - minLng) * s;
    var py = offY + (maxLat - lat) * s; // north is up
    return [px, py];
  }

  function projectRoad(road) {
    var out = [];
    for (var i = 0; i < road.path.length; i++) {
      out.push(project(road.path[i][0], road.path[i][1]));
    }
    return out;
  }

  function projectAll() {
    var co = C();
    var roads = {};
    co.roads.forEach(function (r) { roads[r.name] = projectRoad(r); });
    var hs = {};
    (TS.DATA.hotspots || []).forEach(function (h) {
      hs[h.id] = project(h.ll[0], h.ll[1]);
    });
    lastCache = {
      roads: roads,
      hotspots: hs,
      site: project(co.site[0], co.site[1]),
      intersection: project(co.intersection.ll[0], co.intersection.ll[1]),
      size: getContainerSize()
    };
    repositionHotspotMarkers();
    notifyReproject();
    return lastCache;
  }

  function getProjection() {
    if (!lastCache) projectAll();
    return lastCache;
  }

  function onReproject(cb) { if (typeof cb === "function") reprojectCbs.push(cb); }
  function notifyReproject() {
    reprojectCbs.forEach(function (cb) { try { cb(lastCache); } catch (e) {} });
  }

  /* ---- hotspot markers (real lat/lng; click/keyboard accessible) ---- */
  function addHotspots(cb) {
    onHotspotClick = cb;
    if (!available || !map) return;
    var L = window.L;
    (TS.DATA.hotspots || []).forEach(function (h) {
      var icon = L.divIcon({
        className: "ts-hotspot-icon",
        html: '<span class="ts-hotspot-dot" aria-hidden="true"></span>',
        iconSize: [18, 18]
      });
      var m = L.marker(h.ll, { icon: icon, keyboard: true, title: h.label, alt: h.label }).addTo(map);
      m.on("click", function () { if (onHotspotClick) onHotspotClick(h.id); });
      hotspotMarkers[h.id] = m;
    });
  }
  function repositionHotspotMarkers() {
    if (!available || !map) return;
    // Markers stay at their real lat/lng; Leaflet re-projects them itself when
    // the view changes, so this is a no-op safety re-anchor (guarded).
    (TS.DATA.hotspots || []).forEach(function (h) {
      var m = hotspotMarkers[h.id];
      if (m && typeof m.setLatLng === "function") m.setLatLng(h.ll);
    });
  }

  function getContainerSize() {
    // Prefer the map container; if Leaflet is blocked it is display:none (0px),
    // so fall back to the stage element (the real overlay size), then a default.
    var el = containerEl;
    if (el) {
      var r = el.getBoundingClientRect();
      if (Math.round(r.width) > 0 && Math.round(r.height) > 0) {
        return { w: Math.round(r.width), h: Math.round(r.height) };
      }
    }
    var stage = document.getElementById("ts-stages");
    if (stage) {
      var sr = stage.getBoundingClientRect();
      if (Math.round(sr.width) > 0 && Math.round(sr.height) > 0) {
        return { w: Math.round(sr.width), h: Math.round(sr.height) };
      }
    }
    return { w: fallbackSize.w, h: fallbackSize.h };
  }

  function onResize(cb) { if (typeof cb === "function") resizeCbs.push(cb); }
  function notifyResize() {
    if (available && map) {
      try {
        map.invalidateSize(false);
        // Re-frame so the corridor stays framed after a container size change.
        applyFramedView();
      } catch (e) {}
    }
    var sz = getContainerSize();
    projectAll();
    resizeCbs.forEach(function (cb) { try { cb(sz); } catch (e) {} });
  }

  function isAvailable() { return available; }

  TS.map = {
    init: init,
    project: project,
    projectRoad: projectRoad,
    projectAll: projectAll,
    getProjection: getProjection,
    onReproject: onReproject,
    addHotspots: addHotspots,
    getContainerSize: getContainerSize,
    onResize: onResize,
    notifyResize: notifyResize,
    isAvailable: isAvailable
  };
})();
