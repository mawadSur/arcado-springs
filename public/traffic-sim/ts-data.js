/* ============================================================================
 * Arcado Springs Traffic Simulator — DATA (single source of truth)
 * window.TS.DATA: mapCenter, nodes, edges, scenarios, metrics, layers,
 * hotspots, presentationSteps. Pure data, no logic. Frozen by ts-app boot.
 * Every number here is an ILLUSTRATIVE planning-model estimate.
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  TS.DATA = {
    mapCenter: {
      address: "4541 Arcado Rd, Lilburn, GA 30047",
      fallback: { lat: 33.9446, lng: -84.0533 },
      defaultZoom: 15,
      siteZoom: 16,
      tiles: {
        url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        maxZoom: 19,
        attribution: "Imagery © Esri, Maxar, Earthstar Geographics"
      },
      presets: {
        topdown: { lat: 33.9446, lng: -84.0533, zoom: 16 },
        angled: { lat: 33.9446, lng: -84.0533, zoom: 16 },
        intersectionZoom: { lat: 33.9446, lng: -84.0521, zoom: 18 }
      }
    },

    /* Corridor graph in NORMALIZED canvas coordinates (0..1). */
    nodes: [
      { id: "subW", label: "Legends of Parkview / west subdivisions", x: 0.04, y: 0.30, type: "source", desc: "Residential trip origin west of site" },
      { id: "subSW", label: "South neighborhood feed", x: 0.04, y: 0.62, type: "source", desc: "Secondary residential origin" },
      { id: "arcW", label: "Arcado Rd west approach", x: 0.20, y: 0.46, type: "road", desc: "Two-lane collector entering frame from west" },
      { id: "siteFrontW", label: "Site frontage (west)", x: 0.36, y: 0.50, type: "road", desc: "Arcado Rd along the north edge of the parcel" },
      { id: "drivewayJ", label: "Site driveway junction", x: 0.46, y: 0.52, type: "intersection", desc: "Proposed main site access onto Arcado Rd (becomes signalized AFTER)" },
      { id: "siteFrontE", label: "Site frontage (east)", x: 0.58, y: 0.50, type: "road", desc: "Arcado Rd continuing toward the main corner" },
      { id: "turnLaneBay", label: "Added left-turn bay", x: 0.52, y: 0.58, type: "road", desc: "Dedicated left-turn storage into the site (AFTER only); removes turners from the through lane" },
      { id: "mainXN", label: "Killian Hill Rd north leg", x: 0.80, y: 0.16, type: "road", desc: "Arterial approaching the signalized corner from north" },
      { id: "mainX", label: "Arcado Rd x Killian Hill Rd", x: 0.80, y: 0.46, type: "intersection", desc: "Primary signalized intersection and chief bottleneck" },
      { id: "mainXS", label: "Killian Hill Rd south leg", x: 0.80, y: 0.84, type: "road", desc: "Arterial leaving the corner to the south" },
      { id: "arcE", label: "Arcado Rd east exit", x: 0.97, y: 0.46, type: "sink", desc: "Through traffic leaving frame east" },
      { id: "d1", label: "Town-center loop NW", x: 0.50, y: 0.70, type: "internal", desc: "Internal walkable street node" },
      { id: "d2", label: "Town-center loop NE", x: 0.66, y: 0.70, type: "internal", desc: "Internal walkable street node" },
      { id: "d3", label: "Town-center loop SE", x: 0.66, y: 0.88, type: "internal", desc: "Internal walkable street node" },
      { id: "d4", label: "Town-center loop SW", x: 0.50, y: 0.88, type: "internal", desc: "Internal walkable street node" },
      { id: "plaza", label: "Central plaza / green", x: 0.58, y: 0.79, type: "plaza", desc: "3.6-acre open green; ped/bike hub" },
      { id: "pedX1", label: "Frontage crossing", x: 0.41, y: 0.50, type: "crossing", desc: "Pedestrian crossing of Arcado Rd at the site frontage (AFTER: signal-protected)" },
      { id: "pedX2", label: "Driveway crossing", x: 0.46, y: 0.46, type: "crossing", desc: "Crossing tied to the new driveway signal phase" },
      { id: "qhot1", label: "Corner eastbound queue", x: 0.66, y: 0.46, type: "hotspot", desc: "Eastbound queue spillback approaching the main signal" },
      { id: "qhot2", label: "Northbound left queue", x: 0.80, y: 0.30, type: "hotspot", desc: "Northbound-to-westbound left-turn queue on Killian Hill" }
    ],

    edges: [
      { id: "e1", from: "subW", to: "arcW", lanes: 1, cls: "collector", label: "west feed" },
      { id: "e2", from: "subSW", to: "arcW", lanes: 1, cls: "collector", label: "south feed" },
      { id: "e3", from: "arcW", to: "siteFrontW", lanes: 2, cls: "arterial", label: "Arcado Rd" },
      { id: "e4", from: "siteFrontW", to: "drivewayJ", lanes: 2, cls: "arterial", label: "Arcado Rd frontage" },
      { id: "e5", from: "drivewayJ", to: "siteFrontE", lanes: 2, cls: "arterial", label: "Arcado Rd frontage" },
      { id: "e6", from: "siteFrontE", to: "mainX", lanes: 2, cls: "arterial", label: "Arcado Rd approach" },
      { id: "e7", from: "mainXN", to: "mainX", lanes: 2, cls: "major-arterial", label: "Killian Hill Rd N" },
      { id: "e8", from: "mainX", to: "mainXS", lanes: 2, cls: "major-arterial", label: "Killian Hill Rd S" },
      { id: "e9", from: "mainX", to: "arcE", lanes: 2, cls: "arterial", label: "Arcado Rd east" },
      { id: "e10", from: "drivewayJ", to: "turnLaneBay", lanes: 1, cls: "turn-bay", afterOnly: true, label: "added left-turn bay" },
      { id: "e11", from: "turnLaneBay", to: "d1", lanes: 1, cls: "site-access", label: "into site" },
      { id: "e12", from: "d1", to: "d2", lanes: 1, cls: "internal", label: "main street" },
      { id: "e13", from: "d2", to: "d3", lanes: 1, cls: "internal", label: "east lane" },
      { id: "e14", from: "d3", to: "d4", lanes: 1, cls: "internal", label: "south lane" },
      { id: "e15", from: "d4", to: "d1", lanes: 1, cls: "internal", label: "west lane" },
      { id: "e16", from: "d1", to: "plaza", lanes: 0, cls: "ped-path", label: "plaza path" },
      { id: "e17", from: "d3", to: "plaza", lanes: 0, cls: "ped-path", label: "plaza path" },
      { id: "e18", from: "pedX1", to: "d1", lanes: 0, cls: "ped-path", label: "frontage crossing path" }
    ],

    scenarios: [
      {
        id: "am-peak", label: "Morning peak",
        timeWindow: { start: "7:00 AM", end: "9:00 AM", peakAt: "8:00 AM" },
        description: "School + commute rush; demand peaks mid-window. Internal capture lower than PM (people leaving, not arriving).",
        demandProfile: {
          type: "bell",
          points: [{ t: 0, mult: 0.45 }, { t: 0.25, mult: 0.7 }, { t: 0.5, mult: 1 }, { t: 0.75, mult: 0.78 }, { t: 1, mult: 0.5 }],
          baseVehPerHr: 1850,
          internalCapture: { before: 0, after: 0.18 },
          walkBikeShift: { before: 0, after: 0.07 }
        },
        metrics: {
          avgDelay: { before: 72, after: 38 },
          corridorTravelTime: { before: 7.4, after: 4.6 },
          maxQueue: { before: 620, after: 340 },
          throughput: { before: 1480, after: 1760 },
          intersectionLOS: { before: "E", after: "C" },
          pedCrossingDelay: { before: 58, after: 26 }
        }
      },
      {
        id: "pm-peak", label: "Evening peak",
        timeWindow: { start: "4:00 PM", end: "6:00 PM", peakAt: "5:15 PM" },
        description: "Highest external demand AND highest internal capture (errands, dining stay on-site). The thesis shows strongest here.",
        demandProfile: {
          type: "bell-skewed-late",
          points: [{ t: 0, mult: 0.55 }, { t: 0.25, mult: 0.8 }, { t: 0.5, mult: 0.95 }, { t: 0.7, mult: 1 }, { t: 1, mult: 0.62 }],
          baseVehPerHr: 1980,
          internalCapture: { before: 0, after: 0.3 },
          walkBikeShift: { before: 0, after: 0.1 }
        },
        metrics: {
          avgDelay: { before: 81, after: 40 },
          corridorTravelTime: { before: 8.1, after: 4.9 },
          maxQueue: { before: 700, after: 360 },
          throughput: { before: 1520, after: 1820 },
          intersectionLOS: { before: "F", after: "D" },
          pedCrossingDelay: { before: 64, after: 28 }
        }
      },
      {
        id: "midday", label: "Midday",
        timeWindow: { start: "11:00 AM", end: "1:00 PM", peakAt: "12:00 PM" },
        description: "Moderate, flatter demand (lunch + errands). Signal + driveway organization still trims delay; capture is moderate.",
        demandProfile: {
          type: "flat-bump",
          points: [{ t: 0, mult: 0.6 }, { t: 0.4, mult: 0.85 }, { t: 0.5, mult: 0.9 }, { t: 0.6, mult: 0.88 }, { t: 1, mult: 0.62 }],
          baseVehPerHr: 1180,
          internalCapture: { before: 0, after: 0.24 },
          walkBikeShift: { before: 0, after: 0.09 }
        },
        metrics: {
          avgDelay: { before: 34, after: 21 },
          corridorTravelTime: { before: 4.8, after: 3.6 },
          maxQueue: { before: 280, after: 160 },
          throughput: { before: 1080, after: 1140 },
          intersectionLOS: { before: "C", after: "B" },
          pedCrossingDelay: { before: 36, after: 19 }
        }
      },
      {
        id: "future-buildout", label: "Future build-out",
        timeWindow: { start: "4:00 PM", end: "6:00 PM", peakAt: "5:15 PM" },
        description: "PM peak at projected regional 2035 demand (~+18%). BEFORE degrades sharply; AFTER (with capture, signal, turn lane, complementing the Killian Hill widening) holds an acceptable LOS.",
        demandProfile: {
          type: "bell-skewed-late",
          points: [{ t: 0, mult: 0.6 }, { t: 0.25, mult: 0.85 }, { t: 0.5, mult: 1 }, { t: 0.7, mult: 1.05 }, { t: 1, mult: 0.68 }],
          baseVehPerHr: 2340,
          internalCapture: { before: 0, after: 0.3 },
          walkBikeShift: { before: 0, after: 0.1 }
        },
        metrics: {
          avgDelay: { before: 118, after: 52 },
          corridorTravelTime: { before: 10.6, after: 5.8 },
          maxQueue: { before: 910, after: 430 },
          throughput: { before: 1510, after: 1880 },
          intersectionLOS: { before: "F", after: "D" },
          pedCrossingDelay: { before: 78, after: 32 }
        }
      }
    ],

    metrics: [
      { id: "avgDelay", label: "Avg control delay", unit: "s/veh", lowerIsBetter: true, format: "integer", decimals: 0, description: "Average signalized intersection control delay per vehicle (illustrative HCM-style)." },
      { id: "corridorTravelTime", label: "Corridor travel time", unit: "min", lowerIsBetter: true, format: "decimal", decimals: 1, description: "Modeled time to traverse the Arcado Rd study corridor end to end." },
      { id: "maxQueue", label: "Max queue length", unit: "ft", lowerIsBetter: true, format: "integer", decimals: 0, description: "Longest 95th-percentile queue at the critical approach." },
      { id: "throughput", label: "Throughput", unit: "veh/hr", lowerIsBetter: false, format: "integer", decimals: 0, description: "Vehicles served through the main intersection per hour at peak." },
      { id: "intersectionLOS", label: "Intersection LOS", unit: "grade", lowerIsBetter: true, scale: ["A", "B", "C", "D", "E", "F"], format: "grade", description: "Illustrative level of service (A best, F worst). NOT an official LOS determination." },
      { id: "pedCrossingDelay", label: "Pedestrian crossing delay", unit: "s", lowerIsBetter: true, format: "integer", decimals: 0, description: "Average wait to cross Arcado Rd at the frontage crossing." }
    ],

    layers: [
      { id: "congestion", label: "Congestion heatmap", defaultOn: true, description: "Edge coloring by density on the free-flow to severe scale.", colorScale: ["#16a34a", "#eab308", "#f97316", "#dc2626"] },
      { id: "queues", label: "Queue lengths", defaultOn: true, description: "Stacked vehicle queues drawn back from stop bars." },
      { id: "signals", label: "Traffic signals", defaultOn: true, description: "Red/green signal heads at the main intersection and (after) the new driveway signal." },
      { id: "turningMovements", label: "Turning movements", defaultOn: false, description: "Arrows showing left/through/right volumes at intersections." },
      { id: "siteAccess", label: "Site access", defaultOn: true, description: "Proposed driveway, added left-turn bay, and internal loop (after only)." },
      { id: "pedCrossings", label: "Pedestrian crossings", defaultOn: true, description: "The two crossings plus pedestrian/cyclist agents on dedicated paths." },
      { id: "proposedImprovements", label: "Proposed improvements", defaultOn: true, description: "Highlights new signal + turn lane + crossings; only meaningful in the after scenario." },
      { id: "projectBoundary", label: "Project boundary", defaultOn: false, description: "Dashed outline of the ~9-acre parcel." }
    ],

    hotspots: [
      { id: "hs-mainX", label: "Main intersection: Arcado Rd & Killian Hill Rd", type: "intersection", position: { x: 0.80, y: 0.46 },
        beforeText: "This corner is where everything piles up. Today the light has no separate turn for cars heading into the area, so a single left-turning car can hold up everyone behind it. At rush hour the line of cars stretches well back down Arcado Road.",
        afterText: "With an organized site entrance and a smarter signal, cars turning into Arcado Springs get out of the way of through traffic. The line at the corner is noticeably shorter and the light moves more cars each cycle." },
      { id: "hs-driveway", label: "New site driveway", type: "site-access", position: { x: 0.46, y: 0.52 },
        beforeText: "Today there is no organized entrance here. Cars hunting for shops elsewhere make extra trips out to the busy corner instead of having one clear place to turn in.",
        afterText: "One clearly marked, signal-coordinated driveway gives drivers a single, predictable place to enter and leave the site, so turning traffic no longer mixes unpredictably with the through lane." },
      { id: "hs-newSignal", label: "New traffic signal at the driveway", type: "signal", position: { x: 0.46, y: 0.46 },
        beforeText: "There is no signal here today, so turning into or out of the area means waiting for a gap in oncoming traffic, which backs cars up behind you.",
        afterText: "A new signal, timed together with the main corner, creates safe protected gaps for turning and crossing on foot, and keeps the through traffic flowing in steady platoons instead of stop-and-go." },
      { id: "hs-turnLane", label: "Added left-turn lane", type: "turn-lane", position: { x: 0.52, y: 0.58 },
        beforeText: "With only one lane each way, a car waiting to turn left blocks the cars behind it, stalling the whole road during the turn.",
        afterText: "A dedicated left-turn pocket lets turning cars pull aside and wait without stopping the through lane, so traffic behind keeps moving." },
      { id: "hs-pedCrossing", label: "Pedestrian crossing", type: "crossing", position: { x: 0.41, y: 0.50 },
        beforeText: "Crossing Arcado Road on foot today means a long wait for a gap, which is why almost everyone drives even for short trips.",
        afterText: "A protected crossing tied to the signal lets people walk to the shops and green space safely. Every person who walks is one car that never enters the road." },
      { id: "hs-queue", label: "Eastbound queue hotspot", type: "queue", position: { x: 0.66, y: 0.46 },
        beforeText: "This is where the back of the line forms. When the corner jams, the queue spills back along the frontage and blocks the area entrance.",
        afterText: "With fewer car trips overall and a turn lane keeping the through lane clear, the queue forms later and clears faster, so spillback past the site entrance is rare." }
    ],

    presentationSteps: [
      { id: "step-existing", order: 1, title: "Today's corridor", preset: "topdown", scenario: { id: "am-peak", mode: "toggle", side: "before" },
        layers: { congestion: true, queues: true, signals: true, siteAccess: false, proposedImprovements: false },
        narration: "This is Arcado Road today during the morning rush. Subdivision and school traffic funnels onto one two-lane collector and out to the corner with Killian Hill Road.", focusHotspot: null },
      { id: "step-bottlenecks", order: 2, title: "Where it breaks down", preset: "intersectionZoom", scenario: { id: "am-peak", mode: "toggle", side: "before" },
        layers: { congestion: true, queues: true, turningMovements: true },
        narration: "Zoom in on the corner. With no separate turn lane, one left-turning car stalls the lane behind it, the queue spills back, and the signal cannot clear the demand. This is the bottleneck.", focusHotspot: "hs-mainX" },
      { id: "step-proposed", order: 3, title: "The proposed fixes", preset: "angled", scenario: { id: "am-peak", mode: "toggle", side: "after" },
        layers: { siteAccess: true, proposedImprovements: true, signals: true, pedCrossings: true },
        narration: "Now the build-out: a single organized driveway, a new coordinated signal, a dedicated left-turn lane, and protected pedestrian crossings to the shops and green.", focusHotspot: "hs-driveway" },
      { id: "step-after-sim", order: 4, title: "After: how it flows", preset: "topdown", scenario: { id: "pm-peak", mode: "toggle", side: "after" },
        layers: { congestion: true, queues: true, signals: true, pedCrossings: true, siteAccess: true },
        narration: "Watch the evening peak after build-out. Many trips now start and end on-site or on foot, so fewer cars reach the corner, and the ones that do keep moving.", focusHotspot: null },
      { id: "step-sidebyside", order: 5, title: "Before vs. after", preset: "topdown", scenario: { id: "pm-peak", mode: "split" },
        layers: { congestion: true, queues: true },
        narration: "Side by side at the evening peak: same regional demand, two outcomes. Average delay drops, the queue shortens, and the corner moves more cars per hour.", focusHotspot: null },
      { id: "step-takeaways", order: 6, title: "The takeaway", preset: "topdown", scenario: { id: "am-peak", mode: "toggle", side: "after" },
        layers: { congestion: true, proposedImprovements: true },
        narration: "Mixed-use walkability removes car trips at the source; organized access smooths what remains. In the AM peak that is roughly a 47 percent cut in average delay. These are illustrative planning estimates, not a sealed traffic study.", focusHotspot: null }
    ]
  };
})();
