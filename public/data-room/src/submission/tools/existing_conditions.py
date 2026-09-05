#!/usr/bin/env python3
"""Sheet C-0 "EXISTING CONDITIONS" — The Cottages at Arcado Springs (R-1 -> R-2, Lilburn GA).

    python3 tools/existing_conditions.py        ->  drawings/existing-conditions.svg + .png

ARCH D 36 x 24 in at 1" = 60', with one enlargement at 1" = 30'. Everything is drawn by
tools/sitebase.py from data/layout.json, data/site-context-local.json, data/topo-samples.json,
data/adjoining-parcels.json and data/owners-found.json; nothing here is a hand-drawn coordinate.

WHY THIS SHEET EXISTS
Lilburn Zoning Ordinance 2023-603 section 1003-4.6 requires the site plan to show "existing
roads and streams, flood plains, existing and proposed buildings and structures, parking and
loading areas ... [and] areas of existing vegetation". The 2026-09-03 completeness audit
(audit-2026-09-03/completeness.md, item M8) records that two of those named elements are
absent from Sheet C-1: the existing buildings are noted in text but not drawn in place, and
areas of existing vegetation are not delineated at all. C-0 carries both, plus the existing
boundary, parcel lines, topography, stream and buffers, sanitary sewer and easement, water,
right-of-way, adjoining ownership and zoning, and the FEMA determination.

DRAFT — NOT SEALED. To be superseded by a sealed Georgia RLS boundary and topographic survey.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitebase as sb                                      # noqa: E402

# --------------------------------------------------------------------------- derived numbers
BND = sb.BOUNDARY
GIS_AC = sb.BOUNDARY_SF / 43560.0
HI = max(sb.TOPO['samples'], key=lambda s: s['z_ft'])
LO = min(sb.TOPO['samples'], key=lambda s: s['z_ft'])
ROW_W = sb.row_width_ft()
HYDRANT = min(sb.CTX['hydrants'], key=lambda h: h['dist_ft'])
STRUCTS = sb.existing_polys()
DRIVE_PATH, DRIVE_BAND = sb.existing_drive_poly()
DRIVE_LEN = sum(sb.dist(DRIVE_PATH[i], DRIVE_PATH[i + 1]) for i in range(len(DRIVE_PATH) - 1))
# The Gwinnett GIS soils layer publishes the map-unit symbol but not the name (name = null in
# data/site-context-local.json); the names below are the NRCS SSURGO GA135 series recorded in
# FACTS.md section 2b, which are what the package cites elsewhere.
SOIL_NAMES = {'ApB': 'Appling', 'AmC2': 'Appling/Madison', 'PfC2': 'Pacolet', 'GeB2': 'Cecil',
              'GgE2': 'Cecil, steep', 'ARE': 'Ashlar — gneiss at 22–40 in', 'HYB': 'Helena — HSG D'}
SOILS = ', '.join('%s (%s)' % (m, SOIL_NAMES.get(m, 'name not published — VERIFY'))
                  for m in [s['musym'] for s in sb.CTX['soils']])
FEMA = 'Zone X (area of minimal flood hazard) — FIRM panel 13135C0114F, effective 2006-09-29'

# Boundary lengths as reported by the DRAFT metes-and-bounds description (docs/05 section 5),
# which is generated from the same GIS ring this sheet draws.
FRONTAGE_FT, SW_FT, NE_FT, REAR_FT, PERIM_FT = 237.63, 1757.01, 1721.68, 246.41, 3962.73

ENL = (-80.0, 300.0, -255.0, -35.0, 'A')                   # u0, u1, v0, v1, tag — the frontage
# PIN callouts, each inside its own parcel and clear of the existing buildings and utility notes
PIN_AT = {'6123 033': (95.0, -160.0), '6123 015': (560.0, -128.0),
          '6123 014': (880.0, -128.0), '6123 162': (1500.0, -14.0)}
sb.ENLARGEMENTS.append(ENL)

# Short-course tags (L1, L2, ...) for the line table: boundary() assigns them as it labels the
# courses, so run it once on a scratch canvas that is never drawn.
TAGS = sb.boundary(sb.Drawing(sb.SCALE60, 0.0, 0.0), bearings=True, label=False)

NOTES = [
    'BOUNDARY AND PARCEL LINES: the assemblage boundary, the four interior parcel lines, the bearings, the distances '
    'and the acreages shown are computed from the Gwinnett County GIS parcel fabric (SR 2240 GA West, US survey feet) '
    'and are DRAFT. A boundary survey plat and metes-and-bounds legal description sealed by a Georgia registered land '
    'surveyor are required by Lilburn Zoning Ordinance 2023-603 §1003-4.3 and §1003-4.4 and govern over this sheet. '
    'The four parcels are to be combined; the interior lines are shown so the City can read the assemblage.',

    'TOPOGRAPHY: existing 2-ft contours are interpolated from the USGS 3DEP 1-metre digital elevation model sampled on '
    'a 100 × 50-ft grid (NAVD88) and are APPROXIMATE. Elevations on site range %.1f to %.1f ft; the high point is on '
    'the ridge at local (u %.0f, v %+.0f) and the low point is in the rear pocket at (u %.0f, v %+.0f). A topographic '
    'survey is required before any engineering design. Contour interval 2 ft; index contours at 10 ft.'
    % (LO['z_ft'], HI['z_ft'], HI['u'], HI['v'], LO['u'], LO['v']),

    'EXISTING BUILDINGS AND DRIVES (§1003-4.6 "existing buildings and structures"): the two dwellings and the drive '
    'shown are APPROXIMATE — FROM AERIAL IMAGERY / TAX RECORDS, TO BE LOCATED BY SURVEY. Footprint outlines are public '
    'aerial-imagery building footprints published by OpenStreetMap (© OpenStreetMap contributors, ODbL; Microsoft/Bing '
    'ML BuildingFootprints lineage — ways 999395123, 999395265 and 913015145), transformed into the site-local system '
    'and checked against public aerial imagery on 2026-09-03. Footprint areas scale at %s SF (4541) and %s SF (4535) '
    'against 2026 digest heated areas of 2,053 SF (split-level, built 1972) and 4,267 SF (built 1987, full finished '
    'basement). BOTH DWELLINGS, ALL ACCESSORY STRUCTURES AND ALL EXISTING DRIVES ARE TO BE REMOVED. Accessory '
    'structures are reported near the frontage (FACTS §2; docs/02 §2) but none is resolved in the footprint source: '
    'inventory them by survey before demolition permits. The septic-versus-sewer status of 4535 is unconfirmed — VERIFY. '
    'NOTE THE POSITION OF 4535: its dwelling stands about %.0f ft back from the Arcado Rd right-of-way, on the ridge at '
    'mid-strip — NOT at the frontage. FACTS §2 and docs/02 §2, which place both houses "near the front", should be '
    'corrected to match this sheet.'
    % (format(round(STRUCTS[0][2], -1), ',.0f'), format(round(STRUCTS[1][2], -1), ',.0f'),
       sb.poly_centroid(STRUCTS[1][1])[0]),

    'EXISTING VEGETATION (§1003-4.6 "areas of existing vegetation"): EXISTING WOODED AREA — LIMITS APPROXIMATE, TO BE '
    'FIELD-VERIFIED. The wooded limit is the site boundary less the two mown yards at the existing dwellings, digitised '
    'from public aerial imagery on 2026-09-03 and consistent with docs/11 ("the rear two-thirds is Piedmont hardwood") '
    'and FACTS §2 ("wooded rear"). NO TREE SURVEY HAS BEEN PERFORMED: species, calliper, specimen trees and the actual '
    'tree line are unknown. A tree survey and tree protection / replacement plan will be submitted with the Land '
    'Disturbance Permit; tree density units at 16 TDU/ac are not required of a single-family-residential subdivision '
    '(City of Lilburn Site Development Plan Review Checklist §6.i).',

    'STREAM AND BUFFERS: an unnamed order-0 headwater of Jackson Creek (GAR030701030315; Georgia 2024 §303(d) list for '
    'bacteria and biota, urban runoff) reaches about 30 ft inside the SW line and terminates at local (u 1,392, '
    'v −210). TOP OF BANK IS APPROXIMATE — a field delineation by a qualified professional is required and governs. '
    'Buffers shown: 25 ft state (GA EPD, O.C.G.A. §12-7-6(b)(15)); 50 ft undisturbed and 25 ft additional impervious '
    'setback = 75 ft total (City of Lilburn Code Ch. 109 Art. VII). The 50/75-ft buffers of a second branch that runs '
    '38–58 ft outside the SW line clip the SW edge of the site.',

    'FLOODPLAIN: FEMA %s (Gwinnett GIS floodplain layer; docs/11 §2 Flood, FEMA NFHL accessed 2026-08-28). No special '
    'flood hazard area, floodway or base flood elevation is mapped on the site; the headwater stream is not a '
    'FEMA-mapped watercourse, so the local stream buffer, not a BFE, governs the rear pocket.' % FEMA,

    'SANITARY SEWER: an existing 8-in gravity main ("Arcado Road Townhomes sewer outfall", Gwinnett DWR) enters the '
    'site at Arcado Rd and runs 7–13 ft inside the SW line to a manhole at local (u 272, v −224). Both invert '
    'elevations shown — 927.13 at that manhole and 919.58 at the Legends at Parkview manhole at (u 1,349, v −407) — '
    'are GIS ATTRIBUTES, UNSURVEYED: an invert survey is the first field task. The 20-ft sanitary sewer easement shown '
    'is the "EX. 20\' SSE" of the 2025 hydrology sheet and is NOT a surveyed plat dimension — VERIFY the recorded '
    'width and holder. A Gwinnett DWR sewer capacity certification is required for any connection.',

    'WATER: DIP and ACP mains are in the Arcado Rd right-of-way 47–107 ft from the front line; the public layer does '
    'not publish diameters — VERIFY with Gwinnett DWR. The nearest fire hydrant is at local (u %.0f, v %+.1f), %.1f ft '
    'from the front corner. Other hydrants shown are in the adjoining subdivisions.'
    % (HYDRANT['local'][0], HYDRANT['local'][1], HYDRANT['dist_ft']),

    'ARCADO ROAD RIGHT-OF-WAY: R/W WIDTH VARIES. Measured perpendicular between the two Gwinnett GIS right-of-way '
    'lines it scales %s — a GIS-scaled dimension, not a surveyed one; the R/W line, its width and any required '
    'dedication must be established by the RLS survey. Arcado Rd is a Gwinnett County-maintained minor collector, '
    '35 mph, 14,800 AADT (GDOT station 135-6689, 2017). The centreline of Arcadia Place meets the Arcado Rd centreline '
    'at local (u −12, v +61), 61 ft NE of the site\'s NE front corner.'
    % (', '.join('%.1f ft at v %+.0f' % (w, v) for v, w in ROW_W)),

    'ADJOINING PROPERTY: %d privately owned tax parcels adjoin the assemblage — 14 on the NE line (King David Manor, '
    'plat S/159), 14 on the SW line (Legends at Parkview, plat 118/187) and 3 at the NW end (Nantucket) — every one of '
    'them zoned R-1, City of Lilburn, in single-family use. With the Gwinnett County Arcado Rd right-of-way they are '
    'the 32 notice recipients listed in docs/06. PINs, addresses and owners are from the Gwinnett County Tax Assessor '
    '2026 property-ownership file; re-run them on the filing date. The nearest Lilburn R-2 polygon (the "Arcado Road '
    'Townhomes" site) lies about 106 ft NE of the front corner and is the nearest R-2 precedent.'
    % (len(sb.CTX['adjoining_parcels']) - 1),

    'SOILS (NRCS SSURGO GA135, via Gwinnett GIS): %s. HYB (Helena) is hydrologic soil group D with a seasonal high '
    'water table near 24 in; ARE (Ashlar) carries gneiss bedrock at 22–40 in under both proposed pond sites and the '
    'mid-swale. Rock probes and an undercut allowance are required before any hydrology basis is trusted.' % SOILS,

    'UTILITIES NOT SHOWN: electric, gas, telecommunication and storm-drainage structures are not published in the '
    'layers used for this sheet and are NOT shown. Utility locates through Georgia 811 (Georgia Utility Facility '
    'Protection Act, O.C.G.A. §25-9) are required before any field work, and a full existing-utility survey is '
    'required with the Land Disturbance Permit.',

    'STATUS: this sheet is a DRAFT record of existing conditions compiled from public data for pre-application review. '
    'It is NOT a survey and is NOT SEALED. All dimensions are in US survey feet in the site-local system (u along the '
    'strip, v across). Every statement of conformity in this submittal reads "appears consistent with" and none is a '
    'compliance certification. THE SEALED SURVEY GOVERNS.',
]

LEGEND = [
    ('line', sb.C['bnd'], 1.8, '', 'Assemblage boundary (Gwinnett GIS — DRAFT)'),
    ('line', sb.C['parcel'], 0.6, '10 4 2 4', 'Interior parcel line (to be combined)'),
    ('rect', sb.C['adj_fill'], 0, '', 'Adjoining tax parcel (all zoned R-1, Lilburn)'),
    ('line', sb.C['rw'], 0.9, '', 'Arcado Rd right-of-way line (R/W width varies)'),
    ('line', '#333', 0.6, '14 3 3 3', 'Existing road centreline'),
    ('line', sb.C['contour'], 0.6, '4 2', 'Existing index contour, 10 ft (3DEP approx.)'),
    ('line', sb.C['contour'], 0.3, '2 2', 'Existing contour, 2 ft (3DEP approx.)'),
    ('line', sb.C['stream'], 1.6, '', 'Stream — state waters (top of bank approx.)'),
    ('line', sb.C['buf_line'], 0.5, '3 2', "25' state (GA EPD) buffer"),
    ('line', sb.C['buf_line'], 0.8, '6 2', "50' undisturbed stream buffer (Lilburn)"),
    ('line', sb.C['buf_line'], 0.8, '8 2 2 2', "75' impervious setback"),
    ('line', sb.C['sewer'], 0.9, '', 'Existing 8-in sanitary sewer + manhole'),
    ('rect', 'url(#ssehatch)', 0, '', "Existing 20' sanitary sewer easement (VERIFY)"),
    ('line', sb.C['water'], 0.9, '9 3 2 3', 'Existing water main (Gwinnett DWR)'),
    ('dot', sb.C['hydrant'], 0, '', 'Existing fire hydrant'),
    ('rect', 'url(#exhatch)', 0, '', 'Existing building — approximate, to be removed'),
    ('rect', '#efe6dc', 0, '', 'Existing drive — approximate, to be removed'),
    ('rect', 'url(#woods)', 0, '', 'Existing wooded area (limits approximate)'),
    ('line', sb.C['wood_line'], 0.9, '7 3 2 3', 'Tree line at mown yard (approximate)'),
    ('rect', 'url(#r2hatch)', 0, '', 'Existing R-2 zoning (City of Lilburn)'),
    ('line', sb.C['match'], 1.1, '16 5 3 5', 'Match line — enlargement at 1" = 30\''),
]


# The sanitary runs the package relies on: the Arcado Road Townhomes outfall chain that crosses
# the property, plus the two Legends at Parkview runs that carry the 919.58 invert. Everything in
# this schedule is a Gwinnett DWR GIS attribute — none of it is surveyed.
SEWER_RUNS = ([r for r in sb.CTX['sewer'] if 'ARCADO ROAD TOWNHOMES' in r['project'] and r['min_dist_ft'] <= 15]
              + [r for r in sb.CTX['sewer'] if 'LEGENDS' in r['project'] and r['inv_out'] in (919.58, 917.83)])


def sewer_rows():
    rows = []
    for r in sorted(SEWER_RUNS, key=lambda r: -r['inv_in']):
        a = r['paths_local'][0][0]
        b = r['paths_local'][0][-1]
        rows.append([str(r['facility']),
                     '(%.0f, %+.0f) → (%.0f, %+.0f)' % (a[0], a[1], b[0], b[1]),
                     '%s-in %s' % (r['dia'], r['mat']),
                     '%.1f' % r['len'],
                     '%.2f' % (100.0 * (r['inv_in'] - r['inv_out']) / r['len']),
                     '%.2f → %.2f' % (r['inv_in'], r['inv_out']),
                     r['project'].title().replace('Sewer Outfall', 'sewer outfall')])
    return rows


SOURCES = [
    'Gwinnett County GIS — parcels, zoning, streets, right-of-way, sanitary sewer, water mains, hydrants, '
    'subdivisions, city limits (accela/agis_gwinnett MapServer layers 3–7, 21, 23, 25); streams, floodplain, '
    'soils (GISDataBrowser/GC_Main layers 1, 3, 9). Queried 2026-08-28.',
    'Gwinnett County Tax Assessor — 2026 Property Ownership quarterly file (owners, mailing addresses, deeded '
    'acreage, year built, heated area). Accessed 2026-08-28.',
    'USGS 3DEP elevation ImageServer — 1-metre DEM sampled on a 100 × 50-ft grid, NAVD88 (data/topo-samples.json). '
    'Accessed 2026-08-28.',
    'FEMA National Flood Hazard Layer — flood zone and FIRM panel (docs/11 §2). Accessed 2026-08-28.',
    'OpenStreetMap (© OpenStreetMap contributors, ODbL) — aerial-imagery building footprints and the 4541 drive, '
    'ways 999395123, 999395265, 913015145; Microsoft/Bing ML BuildingFootprints lineage. Accessed 2026-09-03.',
    'Public aerial imagery — visual check of the footprints and of the mown-yard (tree-line) limits, 2026-09-03. '
    'Imagery is not reproduced on this sheet.',
    'City of Lilburn Zoning Ordinance 2023-603 §1003-4.6 (site-plan content) and the City of Lilburn Site '
    'Development Plan Review Checklist. FACTS.md §1, §2, §2b; docs/05 §5; docs/06; docs/11 §2.',
]


def site_data_rows():
    return [
        ['Address / PINs', '4535, 4537, 4539, 4541 Arcado Rd SW, Lilburn GA 30047 — R6123 162, 014, 015, 033',
         'Gwinnett 2026 digest'],
        ['Land lot / district', 'Land Lot 123, 6th District, Gwinnett County; City of Lilburn tax district',
         'Gwinnett GIS'],
        ['Area', '9.44 ac deeded (411,206 SF) = 0.99 + 2.00 + 2.00 + 4.45; %.3f ac (%s SF) GIS-calculated; '
                 'RLS survey governs' % (GIS_AC, format(round(sb.BOUNDARY_SF), ',')), '2026 digest / GIS ring'],
        ['Boundary lengths', "Arcado Rd frontage %.2f'; SW line %.2f'; NE line %.2f'; rear line %.2f'; "
                             "perimeter %.2f'" % (FRONTAGE_FT, SW_FT, NE_FT, REAR_FT, PERIM_FT),
         'docs/05 §5 (DRAFT)'],
        ['Width across the strip', "%.1f ft at Arcado Rd; %.1f ft at the NW end (measured NE line to SW line)"
         % (sb.width(0), sb.width(sb.U_REAR - 1)), 'GIS ring'],
        ['Existing zoning', 'R-1, City of Lilburn (all four parcels). Adjoining: R-1 Lilburn on every line; '
                            'nearest R-2 ≈ 106 ft NE; unincorporated Gwinnett R-100 ≈ 314 ft', 'Gwinnett GIS zoning'],
        ['Existing use', 'Two single-family dwellings with drives near the frontage and at mid-strip; the balance '
                         'wooded. No commercial or agricultural use.', 'Aerial imagery / 2026 digest'],
        ['Existing structures', '4541: %s ± SF footprint at (u %.0f, v %+.0f), built 1972, 2,053 SF heated. '
                                '4535: %s ± SF footprint at (u %.0f, v %+.0f), built 1987, 4,267 SF heated. '
                                "Drive ≈ %.0f ft long × 12 ft. All to be removed."
         % (format(round(STRUCTS[0][2], -1), ',.0f'), sb.poly_centroid(STRUCTS[0][1])[0], sb.poly_centroid(STRUCTS[0][1])[1],
            format(round(STRUCTS[1][2], -1), ',.0f'), sb.poly_centroid(STRUCTS[1][1])[0], sb.poly_centroid(STRUCTS[1][1])[1],
            DRIVE_LEN), 'OSM/ML footprints — APPROX.'],
        ['Topography', 'Range %.1f – %.1f ft NAVD88; ridge %.1f at (u %.0f, v %+.0f); low %.1f at (u %.0f, v %+.0f); '
                       'cross-slope falls NE → SW; contour interval 2 ft'
         % (LO['z_ft'], HI['z_ft'], HI['z_ft'], HI['u'], HI['v'], LO['z_ft'], LO['u'], LO['v']),
         'USGS 3DEP 1-m DEM (approx.)'],
        ['Floodplain', FEMA + ' — no SFHA, floodway or BFE on site', 'FEMA NFHL / Gwinnett GIS'],
        ['Stream / buffers', 'One unnamed order-0 headwater (state waters) reaching ≈ 30 ft inside the SW line; '
                             "25' GA EPD / 50' undisturbed / 75' impervious setback shown from approximate top of bank",
         'Gwinnett hydrology layer'],
        ['Sanitary sewer', 'Existing 8-in gravity main in a 20-ft easement inside the SW line, u ≈ −42 to 272; '
                           'MH invert 927.13 on site and 919.58 off site (Legends at Parkview) — GIS attributes, '
                           'unsurveyed', 'Gwinnett DWR GIS'],
        ['Water', 'DIP / ACP mains in Arcado Rd 47–107 ft from the front line; nearest hydrant %.1f ft from the '
                  'front corner at (u %.0f, v %+.1f)' % (HYDRANT['dist_ft'], HYDRANT['local'][0], HYDRANT['local'][1]),
         'Gwinnett DWR GIS'],
        ['Right-of-way', 'Arcado Rd, Gwinnett County minor collector, 35 mph, 14,800 AADT. R/W WIDTH VARIES: '
                         '%s — scaled perpendicular between the two GIS R/W lines, not surveyed'
                         % '; '.join('%.1f ft at v %+.0f' % (w, v) for v, w in ROW_W),
         'Gwinnett GIS R/W parcel'],
        ['Soils', SOILS, 'NRCS SSURGO GA135'],
        ['Vegetation', 'Existing wooded area over the balance of the site; limits approximate, no tree survey '
                       'performed', 'Aerial imagery, 2026-09-03'],
        ['Adjoining owners', '%d private tax parcels (14 NE, 14 SW, 3 NW) + the Gwinnett County right-of-way = 32 '
                             'notice recipients; PIN, owner and R-1 zoning labelled on the plan'
         % (len(sb.CTX['adjoining_parcels']) - 1), 'docs/06; 2026 digest'],
    ]


def build():
    scale_note = 'Scale 1" = 60\' (ARCH D 36 × 24 in); enlargement 1" = 30\''
    D, F = sb.sheet('EXISTING CONDITIONS', 'C-0',
                    'Existing conditions of record — Lilburn Zoning Ordinance 2023-603 §1003-4.6 '
                    '(existing roads, streams, floodplain, buildings and structures, areas of existing vegetation)',
                    scale_note, generator='tools/sitebase.py + tools/existing_conditions.py')

    # ---------------------------------------------------------------- plan (full length, 1" = 60')
    D.clip_open(fill='#fff')
    sb.adjoiners(D, labels=True)
    sb.arcado_row(D)
    sb.wooded_area(D)
    sb.contours(D, existing=True)
    sb.streams_and_buffers(D)
    sb.sewer_existing(D)
    sb.water_existing(D)
    sb.existing_structures(D)
    sb.boundary(D, bearings=True)
    sb.parcel_lines(D, at=PIN_AT)
    sb.spot_elevations(D)
    sb.match_lines(D)

    D.text(1500, 226, 'FEMA %s — NO SPECIAL FLOOD HAZARD AREA ON SITE' % FEMA.upper(), size=6.5, bold=True, fill='#333')
    D.text(400, 226, 'EXISTING 2-ft CONTOURS: USGS 3DEP 1-m DEM, NAVD88, APPROXIMATE — TOPOGRAPHIC SURVEY REQUIRED',
           size=6.5, bold=True, fill=sb.C['contour_txt'])
    D.text(900, 226, 'KING DAVID MANOR (plat S/159) — ZONED R-1 (CITY OF LILBURN)', size=8, bold=True, fill='#555')
    D.text(760, -388, 'LEGENDS AT PARKVIEW (plat 118/187) — ZONED R-1 (CITY OF LILBURN)', size=8, bold=True, fill='#555')
    D.text(1836, -110, 'NANTUCKET (plat 1/268) — ZONED R-1 (LILBURN)', size=8, rot=-90, bold=True, fill='#555')
    D.text(6, 86, "C/L ARCADIA PL MEETS C/L ARCADO RD AT (u −12, v +61) — 61 FT NE OF THE SITE'S NE FRONT CORNER",
           size=6, anchor='start', halo=True)
    D.clip_close()
    px, py, pw, ph = F['plan']
    D.stext(px + pw, py - 8, 'NO PROPOSED IMPROVEMENT IS SHOWN ON THIS SHEET — SEE SHEET C-1, '
                             'MASTER CONCEPT PLAN', size=11, bold=True, fill='#7b1fa2', anchor='end')

    # ---------------------------------------------------------------- band: site data
    x = F['inner_l'] + 20
    y = sb.BAND_Y0
    yend = sb.table(D, x, y, ['EXISTING SITE DATA', 'RECORD VALUE (DRAFT — SURVEY GOVERNS)', 'SOURCE'],
                    site_data_rows(), size=6.5, widths=[110, 400, 130],
                    title='EXISTING SITE DATA — compiled from public records on %s' % sb.DATE)
    D.stext(x, yend + 12, 'Existing building footprints and the 4541 drive: © OpenStreetMap contributors (ODbL), '
                          'ways 999395123 / 999395265 / 913015145 — aerial-imagery footprints, approximate.', size=6.2,
            fill='#444')
    D.stext(x, yend + 21, 'Owner names and mailing addresses: Gwinnett County Tax Assessor 2026 property-ownership '
                          'file. Zoning: Gwinnett GIS zoning layer (City of Lilburn districts).', size=6.2, fill='#444')

    # ---------------------------------------------------------------- band: sanitary sewer schedule
    y2 = sb.table(D, x, yend + 42, ['FACILITY ID', 'FROM (u, v) → TO (u, v)', 'SIZE / MAT.', 'LENGTH (ft)',
                                    'SLOPE (%)', 'INVERT IN → OUT (ft)', 'PROJECT'],
                  sewer_rows(), size=6.5, widths=[52, 132, 60, 48, 44, 90, 214],
                  title='EXISTING SANITARY SEWER SCHEDULE — every value is a Gwinnett DWR GIS attribute, '
                        'UNSURVEYED (an invert survey is required)')
    D.stext(x, y2 + 11, 'Slope is computed from the published invert pair and pipe length: (INV IN − INV OUT) ÷ LENGTH. '
                        'The 927.13 manhole is the Phase 1 point of connection; the 919.58 manhole is the '
                        'Legends at Parkview tie-in studied in docs/08 Memo B.', size=6.2, fill='#444')

    # ---------------------------------------------------------------- band: sources
    D.stext(x, y2 + 34, 'SOURCES AND ACCESS DATES', size=9, bold=True)
    yy2 = y2 + 47
    for i, srcline in enumerate(SOURCES, 1):
        yy2 = D.stextblock(x, yy2, '%d. %s' % (i, srcline), size=6.3, chars=152, lead=7.9, indent=9)
        yy2 += 2.0

    # ---------------------------------------------------------------- band: legend
    lx = x + 665
    D.stext(lx, sb.BAND_Y0, 'LEGEND', size=9, bold=True)
    for i, (kind, col, wdt, dash, txt) in enumerate(LEGEND):
        yy = sb.BAND_Y0 + 14 + i * 12.5
        if kind == 'line':
            D.sline(lx, yy - 3, lx + 34, yy - 3, stroke=col, stroke_width=wdt, stroke_dasharray=dash)
        elif kind == 'dot':
            D.scircle(lx + 17, yy - 3, 2.6, fill=col, stroke='#fff', stroke_width=0.5)
        else:
            D.srect(lx, yy - 9.5, 34, 12, fill=col, stroke='#555', stroke_width=0.4)
        D.stext(lx + 40, yy, txt, size=6.5)

    # ---------------------------------------------------------------- band: line table
    ty = sb.BAND_Y0 + 14 + len(LEGEND) * 12.5 + 16
    tags = [(t, b) for t, b in TAGS]
    sb.table(D, lx, ty, ['LINE', 'BEARING (SR 2240 GA WEST)', 'DISTANCE'],
             [[t, b['bearing'], "%.2f'" % b['distance_ft']] for t, b in tags], size=6.5,
             widths=[34, 116, 50], title='LINE TABLE — courses under 60 ft (GIS-derived, DRAFT)')

    # ---------------------------------------------------------------- band: enlargement A
    ex = lx + 320
    sub = sb.enlargement(ENL[0], ENL[1], ENL[2], ENL[3], ex, sb.BAND_Y0 + 34, scale=sb.SCALE30, tag='A')
    sub.clip_open(fill='#fff')
    sb.adjoiners(sub, labels=False)
    sb.arcado_row(sub, labels=False)
    sb.wooded_area(sub, labels=False)
    sb.contours(sub, existing=True, labels=False)
    sb.sewer_existing(sub, labels=False)
    sb.water_existing(sub, labels=False)
    sb.existing_structures(sub, labels=False)
    sb.boundary(sub, bearings=True, label=False)
    sb.parcel_lines(sub, labels=False)
    # enlargement-only annotation
    sub.text(-52, -228, 'EX. MH', size=6, fill=sb.C['sewer_txt'], halo=True, anchor='end')
    sub.text(-52, -238, 'INV 932.69 / 930.84', size=6, fill=sb.C['sewer_txt'], halo=True, anchor='end')
    sub.text(268, -244, 'EX. MH INV 927.13  (GIS ATTRIBUTE — UNSURVEYED)', size=6.5, bold=True,
             fill=sb.C['sewer_txt'], halo=True, anchor='end')
    sub.line((238.0, -241.0), (268.0, -227.0), stroke=sb.C['sewer_txt'], stroke_width=0.5)
    sub.circle((271.7, -224.0), 3.4, fill='none', stroke=sb.C['sewer_txt'], stroke_width=0.9)
    sub.text(24, -206, "EX. 8-in SANITARY SEWER IN A 20' SANITARY SEWER EASEMENT (VERIFY)", size=6.5,
             bold=True, fill=sb.C['sewer_txt'], halo=True, anchor='start')
    sub.textlines(203, -100, ['EXISTING HOUSE — 4541 ARCADO RD SW',
                              '%s ± SF FOOTPRINT — APPROXIMATE, TO BE LOCATED BY SURVEY'
                              % format(round(STRUCTS[0][2], -1), ',.0f'),
                              'PIN R6123 033 · built 1972 · 2,053 SF heated (2026 digest)',
                              'TO BE REMOVED'],
                  size=6.5, gap=1.25, bold_first=True, fill=sb.C['exist'], halo=True)
    sub.text(40, -216, 'EXISTING DRIVE — TO BE REMOVED', size=6.5, fill=sb.C['exist'], halo=True, anchor='start')
    sub.line((92.0, -218.0), (92.0, -228.0), stroke=sb.C['exist'], stroke_width=0.5)
    sub.text(-30, -100, 'ARCADO RD R/W LINE = FRONT PROPERTY LINE', size=6, rot=-81, bold=True, halo=True)
    sub.text(-64, -100, 'C/L ARCADO RD — R/W WIDTH VARIES (%.1f–%.1f ft SCALED)'
             % (min(w for v, w in ROW_W), max(w for v, w in ROW_W)), size=6, rot=-81, halo=True)
    sub.text(150, -52, 'ARCADO RD FRONTAGE COURSES %s — SEE LINE TABLE' % sb.tag_ranges(TAGS),
             size=6.5, bold=True, halo=True)
    sub.text(255, -70, 'TREE LINE (APPROX.)', size=6, fill=sb.C['wood_line'], halo=True, anchor='start')
    sub.clip_close()
    ybot = sb.place(D, sub, title='ENLARGEMENT A — ARCADO ROAD FRONTAGE, EXISTING HOUSE AT 4541 AND THE EXISTING '
                                  'SANITARY SEWER    (SCALE 1" = 30\')',
                    note='Same data, same coordinates as the plan above; u %.0f to %.0f, v %.0f to %.0f. '
                         'Frontage courses are tabulated in the line table at the left.' % ENL[:4])
    sb.scalebar(D, ex + 8, ybot + 24, scale=sb.SCALE30, step_ft=30, steps=4)
    D.stext(ex + 330, ybot + 20, 'Courses %s lie on the Arcado Rd frontage; courses %s are on the side and '
                                 'rear lines.' % (sb.tag_ranges(TAGS), sb.tag_ranges(TAGS, frontage=False)),
            size=6.5, fill='#444')
    D.stext(ex + 330, ybot + 32, 'Every dimension on this sheet is a GIS-derived DRAFT value in US survey feet; '
                                 'the sealed RLS survey governs.', size=6.5, fill='#444')

    # ---------------------------------------------------------------- band: general notes
    nx = ex + 940
    D.stext(nx, sb.BAND_Y0, 'GENERAL NOTES — EXISTING CONDITIONS', size=9, bold=True)
    yy = sb.BAND_Y0 + 13
    for i, n in enumerate(NOTES, 1):
        yy = D.stextblock(nx, yy, '%d. %s' % (i, n), size=6.4, chars=133, lead=8.0, indent=9)
        yy += 2.5

    return D


if __name__ == '__main__':
    D = build()
    svg, png = sb.save(D, 'existing-conditions', dpi=150)
    print('wrote %s\n      %s' % (svg, png))
    print('  courses: %d (%d under 60 ft, %d of them on the Arcado Rd frontage)'
          % (len(sb.BEARINGS), len(TAGS), sum(1 for t, b in TAGS if b['frontage'])))
    print('  existing structures: ' + '; '.join('%s %.0f SF at (u %.0f, v %.0f)'
          % (s['key'], a, sb.poly_centroid(p)[0], sb.poly_centroid(p)[1]) for s, p, a in STRUCTS))
    print('  R/W width scaled: ' + ', '.join('%.1f ft at v %+.0f' % (w, v) for v, w in ROW_W))
