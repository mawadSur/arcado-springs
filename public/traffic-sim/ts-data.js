/* ============================================================================
 * Arcado Springs Traffic Simulator — DATA (single source of truth)
 * window.TS.CORRIDOR: real OSM geometry (embedded, NOT fetched) for the
 *   Arcado Rd / Killian Hill Rd corridor at 4541 Arcado Rd SW, Lilburn GA.
 * window.TS.DATA: mapCenter, scenarios, metrics, layers, hotspots,
 *   presentationSteps. Pure data, no logic. Frozen by ts-app boot.
 * Every number here is an ILLUSTRATIVE planning-model estimate.
 * ==========================================================================*/
(function () {
  "use strict";
  var TS = (window.TS = window.TS || {});

  /* ---- Embedded real geometry (verbatim from corridor-osm.json) ---- */
  TS.CORRIDOR = {
    center: [33.87985, -84.119684],
    site: [33.87985, -84.119684],
    siteLabel: "4541 Arcado Rd SW — Arcado Springs",
    intersection: { name: "Arcado Rd & Killian Hill Rd", ll: [33.883026, -84.11597] },
    bounds: [[33.865601, -84.133657], [33.888629, -84.097376]],
    basemap: {
      voyager: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
      attribution: "© OpenStreetMap, © CARTO"
    },
    roads: [
      { name: "Killian Hill Road", class: "secondary", path: [[33.888629, -84.123983], [33.885686, -84.120643], [33.883893, -84.117301], [33.883336, -84.116371], [33.883026, -84.11597], [33.881694, -84.114689], [33.880367, -84.11327], [33.879653, -84.112693], [33.878611, -84.112075], [33.878161, -84.111658], [33.87782, -84.111128], [33.876731, -84.108551], [33.876415, -84.107995], [33.875395, -84.106649], [33.87469, -84.106027], [33.872341, -84.104433], [33.870359, -84.102423], [33.869593, -84.101537], [33.869098, -84.100608], [33.868927, -84.099821], [33.868924, -84.099195], [33.869125, -84.097376]] },
      { name: "Arcado Road", class: "tertiary", path: [[33.887611, -84.111966], [33.886717, -84.113218], [33.885532, -84.114473], [33.884708, -84.115101], [33.883026, -84.11597], [33.881707, -84.117945], [33.880133, -84.119126], [33.879684, -84.119758], [33.878496, -84.12235], [33.87779, -84.123599], [33.877098, -84.125189], [33.876763, -84.125804], [33.876481, -84.126095], [33.874685, -84.127369], [33.874425, -84.127662], [33.873799, -84.128662], [33.873628, -84.128862], [33.873229, -84.129101]] },
      { name: "Camp Creek Road", class: "tertiary", path: [[33.885087, -84.133657], [33.883223, -84.131933], [33.882482, -84.131049], [33.882103, -84.130725], [33.881426, -84.130447], [33.880308, -84.129663], [33.878498, -84.129055], [33.87753, -84.129124], [33.877228, -84.12902], [33.876658, -84.128581], [33.87572, -84.128069], [33.875441, -84.127659], [33.875209, -84.126964]] },
      { name: "Cole Drive", class: "tertiary", path: [[33.875209, -84.126964], [33.87506, -84.126621], [33.874694, -84.126228], [33.872908, -84.125033], [33.87106, -84.123971], [33.869704, -84.122873], [33.869175, -84.122263], [33.868867, -84.12175], [33.868525, -84.120888], [33.868364, -84.1203], [33.868169, -84.119918], [33.867397, -84.119258], [33.86639, -84.118527], [33.866008, -84.118355], [33.865601, -84.118328]] }
    ]
  };

  TS.DATA = {
    /* Geometry now comes from CORRIDOR; mapCenter is just descriptive. */
    mapCenter: {
      address: "4541 Arcado Rd SW, Lilburn, GA 30047",
      siteLabel: "4541 Arcado Rd SW — Arcado Springs"
    },

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
      { id: "congestion", label: "Congestion heatmap", defaultOn: true, description: "Study-corridor coloring by density on the free-flow to severe scale.", colorScale: ["#16a34a", "#eab308", "#f97316", "#dc2626"] },
      { id: "queues", label: "Queue lengths", defaultOn: true, description: "Stacked vehicle queues drawn back from stop bars." },
      { id: "signals", label: "Traffic signals", defaultOn: true, description: "Red/green signal heads at the main intersection and (after) the new driveway signal." },
      { id: "turningMovements", label: "Turning movements", defaultOn: false, description: "Arrows showing left/through/right volumes at intersections." },
      { id: "siteAccess", label: "Site access", defaultOn: true, description: "Proposed driveway, added left-turn bay, and on-site capture (after only)." },
      { id: "pedCrossings", label: "Pedestrian crossings", defaultOn: true, description: "The corridor crossings plus pedestrian/cyclist agents on the frontage." },
      { id: "proposedImprovements", label: "Proposed improvements", defaultOn: true, description: "Highlights new signal + turn lane + crossings; only meaningful in the after scenario." },
      { id: "projectBoundary", label: "Project boundary", defaultOn: false, description: "Highlighted outline of the ~9-acre parcel on Arcado Rd." }
    ],

    /* Hotspots carry REAL lat/lng. ids preserved so presentationSteps work. */
    hotspots: [
      { id: "hs-mainX", label: "Main intersection: Arcado Rd & Killian Hill Rd", type: "intersection", ll: [33.883026, -84.11597],
        beforeText: "This corner is where everything piles up. Today the light has no separate turn for cars heading into the area, so a single left-turning car can hold up everyone behind it. At rush hour the line of cars stretches well back down Arcado Road.",
        afterText: "With an organized site entrance and a smarter signal, cars turning into Arcado Springs get out of the way of through traffic. The line at the corner is noticeably shorter and the light moves more cars each cycle." },
      { id: "hs-driveway", label: "New site driveway", type: "site-access", ll: [33.879684, -84.119758],
        beforeText: "Today there is no organized entrance here. Cars hunting for shops elsewhere make extra trips out to the busy corner instead of having one clear place to turn in.",
        afterText: "One clearly marked, signal-coordinated driveway gives drivers a single, predictable place to enter and leave the site, so turning traffic no longer mixes unpredictably with the through lane." },
      { id: "hs-newSignal", label: "New traffic signal at the driveway", type: "signal", ll: [33.880133, -84.119126],
        beforeText: "There is no signal here today, so turning into or out of the area means waiting for a gap in oncoming traffic, which backs cars up behind you.",
        afterText: "A new signal, timed together with the main corner, creates safe protected gaps for turning and crossing on foot, and keeps the through traffic flowing in steady platoons instead of stop-and-go." },
      { id: "hs-turnLane", label: "Added left-turn lane", type: "turn-lane", ll: [33.881707, -84.117945],
        beforeText: "With only one lane each way, a car waiting to turn left blocks the cars behind it, stalling the whole road during the turn.",
        afterText: "A dedicated left-turn pocket lets turning cars pull aside and wait without stopping the through lane, so traffic behind keeps moving." },
      { id: "hs-pedCrossing", label: "Pedestrian crossing", type: "crossing", ll: [33.879653, -84.112693],
        beforeText: "Crossing the road on foot today means a long wait for a gap, which is why almost everyone drives even for short trips.",
        afterText: "A protected crossing tied to the signal lets people walk to the shops and green space safely. Every person who walks is one car that never enters the road." },
      { id: "hs-queue", label: "Killian Hill approach queue", type: "queue", ll: [33.881694, -84.114689],
        beforeText: "This is where the back of the line forms. When the corner jams, the queue spills back along the approach and blocks the entrance to the area.",
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
