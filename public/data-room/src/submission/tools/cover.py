#!/usr/bin/env python3
"""Sheet C-0.0 "COVER SHEET, SHEET INDEX AND VICINITY MAP" — The Cottages at Arcado Springs.

    python3 tools/cover.py        ->  drawings/cover.svg + drawings/cover.png

ARCH D 36 x 24 in.  This is item M5 of audit-2026-09-03/completeness.md and the C-0.0 row of
audit-2026-09-03/drawing-standards.md section 3.1, and it is the "Cover Page" the City of Lilburn
Site Development Plan Review Checklist section 1.e.1 asks for:

    "Cover Page - Project name and use(s), address and District, Land Lot and Parcel Number(s) or
     PIN in title block; add owner, 24 hr contact, designer and all professional names, addresses,
     email and phone contacts; Sheet Index; site location map, zoning and proposed use data"

WHERE EVERYTHING COMES FROM — nothing on this sheet is a hand-typed coordinate or a hand-typed count
    data/layout.json            lot count, density, open space, disturbed area, lane length, frontage
                                (regenerated 2026-09-03 by tools/siteplan.py — read fresh at run
                                time, never quoted from an older document)
    data/plans.json             conditioned areas and body dimensions of Plan A and Plan B
    data/site-context-local.json    street centrelines, adjoining tax parcels, zoning polygons and
                                streams, already in the site-local (u, v) system, from Gwinnett GIS
    tools/sitebase.py           the boundary ring, the palette, the sheet primitives, the disclaimer
                                and the canonical marker (imported; NOT modified)
    drawings/*.svg              the SHEET INDEX is built by listing the files that actually exist at
                                run time, so the index can never claim a sheet the set does not hold

THE TWO MAPS ARE DRAWN NORTH-UP, NOT IN THE SITE-LOCAL SYSTEM
    Every other C-sheet is drawn in the site-local (u, v) frame with grid north 28 deg 43' above the
    +u axis.  A cover-sheet vicinity map has one job — orientation — so both maps here are rotated
    into grid east / grid north:

        E = -sin(28.72 deg) * u + cos(28.72 deg) * v
        N =  cos(28.72 deg) * u + sin(28.72 deg) * v

    (checked against sitebase.lonlat_of(): 1,722 ft of u gives 1,455 ft of northing and -928 ft of
    easting, which matches the lat/lon of the rear line to better than 5 ft.)

WHY THIS FILE DOES NOT CALL sitebase.sheet()
    sitebase.sheet() is built for a 1" = 60' plan sheet: it opens a fixed 2,388 x 804-pt plan window,
    prints a header line over it and queues a watermark reading "EXISTING CONDITIONS OF RECORD, NOT A
    SURVEY".  None of that belongs on a cover.  _frame() below reproduces sitebase's ARCH D border,
    title-block cell grid, type sizes and disclaimer strip exactly — the sheets must look like one
    set — but leaves the sheet body empty.  If the title block in sitebase.py changes, change it here.

LETTERING
    General notes 10.5 pt; tables, legend and map annotation 8.5-11 pt; block and banner titles
    13-40 pt; title block and map furniture 7-8 pt.  That is a cap height of 0.068-0.107 in at full
    size.  The set standard is a 1/8-in cap height; the volume of content the City's checklist puts
    on a cover page does not fit an ARCH D sheet at that size, so this sheet carries the largest
    type that fits, and general note 17 says so on the sheet.  tw() measures real Helvetica/Arial
    advance widths, so every block is fitted to its column rather than to a flat per-character
    guess; build() prints a WARNING if any column overruns the disclaimer strip.

DRAFT - NOT SEALED.  The seal blocks on this sheet are blank on purpose: Checklist section 1.e.1 asks
for every professional's name, and where none is engaged the blank line makes the omission visible
instead of silent.
"""
import glob
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitebase as sb                                      # noqa: E402

DRAW = sb.DRAW
SHEET_NO = 'C-0.0'
SHEET_TITLE = 'COVER SHEET, SHEET INDEX AND VICINITY MAP'
SELF_FILE = 'cover.svg'

# --------------------------------------------------------------------------- north-up transform
_A = math.radians(sb.NORTH_DEG)
_S, _C = math.sin(_A), math.cos(_A)


def EN(p):
    """site-local (u, v) feet  ->  (grid east, grid north) feet, origin at the Arcado Rd corner."""
    return (-_S * p[0] + _C * p[1], _C * p[0] + _S * p[1])


def ENs(path):
    return [EN(p) for p in path]


# --------------------------------------------------------------------------- live package numbers
L = sb.LAYOUT
M = L['metrics']
PLANS = sb._load('plans.json')['plans']
SW_ = L['stormwater']

LOTS = M['lots']
DENS_DEED, DENS_GIS = M['density_du_ac_deeded'], M['density_du_ac_gis']
GIS_SF, GIS_AC, DEED_AC = M['boundary_sf'], M['acreage_gis_ac'], M['acreage_deeded_ac']
DEED_SF = int(round(DEED_AC * 43560))
OS_SF, OS_AC, OS_PCT = M['open_space_sf'], M['open_space_ac'], M['open_space_pct_gis']
DISTURBED_AC = SW_['disturbed_area']['disturbed_ac']
LANE_FT = M['lane_length_ft']
FRONTAGE_FT = M['frontage_arcado_chord_ft']
LOT_SF = M['lot_area_min_sf']
GUEST = L['amenity']['guest_spaces'] + L['amenity']['kiosk_spaces']
SEWER_EXT_FT = M['sewer_ext_offsite_ft']
LANE_GRADE = M['max_existing_lane_grade_pct']

PA, PB = PLANS['A'], PLANS['B']
COND_A, COND_B = PA['areas']['conditioned_sf'], PB['areas']['conditioned_sf']
BODY_A, BODY_B = PA['overall_body_dims']['label'], PB['overall_body_dims']['label']
RIDGE = max(PA['roof']['max_ridge_ft'], PB['roof']['max_ridge_ft'])

FIRM = '13135C0114F, effective 2006-09-29'


def fmt(n, d=0):
    return format(round(n, d) if d else int(round(n)), ',.%df' % d)


# --------------------------------------------------------------------------- text metrics
# Liberation Sans is metric-compatible with Arial, which is metric-compatible with Helvetica, so
# the Adobe Helvetica / Helvetica-Bold advance widths (per 1000 em, ASCII 32-126) measure this
# sheet's type exactly.  A flat "0.56 em per character" estimate is 15-20% wrong on capitalised
# text, which is what leaves gaps after a run-in bold note head and pushes table cells out of
# their columns.
_ASCII_REG = ('278 278 355 556 556 889 667 191 333 333 389 584 278 333 278 278 '
              '556 556 556 556 556 556 556 556 556 556 278 278 584 584 584 556 '
              '1015 667 667 722 722 667 611 778 722 278 500 667 556 833 722 778 '
              '667 778 722 667 611 722 667 944 667 667 611 278 278 278 469 556 '
              '333 556 556 500 556 556 278 556 556 222 222 500 222 833 556 556 '
              '556 556 333 500 278 556 500 722 500 500 500 334 260 334 584')
_ASCII_BLD = ('278 333 474 556 556 889 722 238 333 333 389 584 278 333 278 278 '
              '556 556 556 556 556 556 556 556 556 556 333 333 584 584 584 611 '
              '975 722 722 722 722 667 611 778 722 278 556 722 611 833 722 778 '
              '667 778 722 667 611 722 667 944 667 667 611 333 278 333 584 556 '
              '333 556 611 556 611 556 333 611 611 278 278 556 278 889 611 611 '
              '611 611 389 556 333 611 556 778 556 556 500 389 280 389 584')
_EXTRA = {'\u2014': 1000, '\u2013': 556, '\u2019': 191, '\u2018': 191, '\u201c': 355,
          '\u201d': 355, '\u00a7': 556, '\u00d7': 584, '\u2192': 1000, '\u00b0': 400}
_WID = {False: {chr(32 + i): int(w) for i, w in enumerate(_ASCII_REG.split())},
        True: {chr(32 + i): int(w) for i, w in enumerate(_ASCII_BLD.split())}}
for _t in (_WID[False], _WID[True]):
    _t.update(_EXTRA)


def tw(text, size, bold=False):
    """Width of `text` at `size` points, in points."""
    t = _WID[bool(bold)]
    return size * sum(t.get(ch, 556) for ch in str(text)) / 1000.0


def wrap_w(text, size, width, bold=False):
    """Greedy word wrap to a measured width in points."""
    out, cur = [], ''
    for w in str(text).split():
        cand = (cur + ' ' + w).strip()
        if cur and tw(cand, size, bold) > width:
            out.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        out.append(cur)
    return out or ['']


# ============================================================================ THE SHEET INDEX
# Explicit file -> sheet-number table.  It is deliberately the same table tools/transmittal.py uses
# to build docs/00, so that the drawing index and the filing transmittal can never disagree,
# extended with the four sheets that audit-2026-09-03/drawing-standards.md section 3.1 names and the
# transmittal omits.  A row with no file, or whose file is absent from drawings/ at run time, prints
# NOT ISSUED.
SHEETS = [
    ('C-0.0', 'Cover Sheet, Sheet Index and Vicinity Map', 'cover.svg', 'ARCH D 36 x 24', 'As noted'),
    ('C-1.0', 'Existing Conditions, Boundary and Topographic Survey', 'existing-conditions.svg',
     'ARCH D 36 x 24', '1" = 60\''),
    ('C-1.1', 'Demolition and Tree Protection Plan', None, 'ARCH D 36 x 24', '1" = 60\''),
    ('C-2.0', 'Master Concept Plan - Overall', 'mcp-sheet.svg', 'ARCH D 36 x 24', '1" = 60\''),
    ('C-2.1', 'Master Concept Plan - Enlargement, Block A', 'mcp-enlargement-a.svg',
     'ARCH D 36 x 24', '1" = 30\''),
    ('C-2.2', 'Master Concept Plan - Enlargement, Block B', 'mcp-enlargement-b.svg',
     'ARCH D 36 x 24', '1" = 30\''),
    ('C-2.3', 'Entry, Frontage and Amenity Enlargement', 'entry-enlargement.svg',
     'ARCH C 24 x 18', '1" = 20\''),
    ('C-2.4', 'Fallback Lot-Depth Exhibit - 50 x 82-ft Lots', 'fallback-layout.svg',
     'ARCH D 36 x 24', '1" = 60\''),
    ('C-3.0', 'Grading, Drainage and Stormwater Concept', 'grading-drainage.svg',
     'ARCH D 36 x 24', '1" = 60\''),
    ('C-3.1', 'Stormwater Details and Sections', None, 'ARCH C 24 x 18', 'As noted'),
    ('C-4.0', 'Utility and Phasing Concept', 'utility-phasing.svg', 'ARCH D 36 x 24', '1" = 60\''),
    ('C-4.1', 'Sanitary Sewer Profiles', None, 'ARCH D 36 x 24', '1" = 50\' H / 5\' V'),
    ('C-5.0', 'Private Lane Plan and Profile', None, 'ARCH D 36 x 24', '1" = 50\' H / 5\' V'),
    ('C-6.0', 'Phasing, Block and Open Space Exhibit', 'phasing-openspace.svg',
     'ARCH D 36 x 24', '1" = 60\''),
    ('C-7.0', 'Landscape, Buffer and Tree Protection Concept', 'landscape-buffer.svg',
     'ARCH D 36 x 24', '1" = 60\''),
    ('C-8.0', 'Civil Details', 'civil-details.svg', 'ARCH D 36 x 24', 'As noted'),
    ('A-1.1', 'Plan A "The Springbrook" - Floor Plan', 'plan-a-sheet.svg', 'ARCH C 24 x 18',
     '3/16" = 1\'-0"'),
    ('A-1.2', 'Plan B "The Laurel" - Floor Plan', 'plan-b-sheet.svg', 'ARCH C 24 x 18',
     '3/16" = 1\'-0"'),
    ('A-2.1', 'Plan A - Exterior Elevations (four sides)', 'plan-a-elev.svg', 'ARCH C 24 x 18',
     '3/16" = 1\'-0"'),
    ('A-2.2', 'Plan B - Exterior Elevations (four sides)', 'plan-b-elev.svg', 'ARCH C 24 x 18',
     '3/16" = 1\'-0"'),
    ('A-2.3', 'Exterior Colour Schemes and Materials', 'plan-colors.svg', 'ARCH C 24 x 18',
     '3/16" = 1\'-0"'),
    ('A-3.0', 'Clubhouse, Mail Kiosk and Entry Monument Sign', 'amenity-sheet.svg',
     'ARCH C 24 x 18', 'As noted'),
    ('A-4.0', 'Typical Lot - Plan A', 'plan-a-lot.svg', 'ARCH C 18 x 24 (portrait)', '1" = 10\''),
    ('A-4.1', 'Typical Lot - Plan B', 'plan-b-lot.svg', 'ARCH C 18 x 24 (portrait)', '1" = 10\''),
]

# Files that live in drawings/ but are exhibits rather than sheets of the bound set.
EXHIBITS = {
    'plan-a.svg': 'Plan A floor plan, tight crop — working exhibit for docs/09 and the web page',
    'plan-b.svg': 'Plan B floor plan, tight crop — working exhibit for docs/09 and the web page',
    'mcp-web.svg': 'Master concept plan, screen version — public web exhibit, not a plot sheet',
}

_NUM = r'[A-Z]{1,2}-[0-9](?:\.[0-9])?'
_PAT = (re.compile(r'<title>[^<]*?Sheet\s+(%s)' % _NUM, re.I),
        re.compile(r'<text\b(?=[^>]*font-weight="bold")[^>]*>\s*(%s)\s*</text>' % _NUM),
        re.compile(r'Sheet\s+(%s)\b' % _NUM))


def titleblock_number(path):
    """The sheet number the file's OWN title block carries, or '' if it declares none.

    Read so that the index can disclose where an issued sheet still carries a provisional number
    from an earlier numbering (existing-conditions.svg says "C-0"; plan-a-sheet.svg says "A-1").
    The index number governs; the discrepancy is shown rather than silently overwritten.
    """
    try:
        txt = open(path, encoding='utf-8', errors='replace').read()
    except OSError:
        return ''
    for p in _PAT:
        m = p.search(txt)
        if m:
            return m.group(1)
    return ''


def index_rows():
    """(rows for the index table, issued count, list of unclaimed .svg files in drawings/).

    This sheet counts as issued whatever the state of drawings/ when the script starts: it is being
    written by this run, so a clean rebuild must not print "NOT ISSUED" against its own row.
    """
    present = {os.path.basename(p) for p in glob.glob(os.path.join(DRAW, '*.svg'))}
    present.add(SELF_FILE)
    claimed, rows, issued = set(), [], 0
    for no, title, fn, size, scale in SHEETS:
        if fn:
            claimed.add(fn)
        if fn and fn in present:
            issued += 1
            png = os.path.exists(os.path.join(DRAW, fn[:-4] + '.png')) or fn == SELF_FILE
            status = 'ISSUED' if png else 'ISSUED (SVG)'
            tb = no if fn == SELF_FILE else titleblock_number(os.path.join(DRAW, fn))
            tb = ('=' if tb == no else (tb or '--'))
            fname = fn[:-4]
        else:
            status, tb, fname = 'NOT ISSUED', '--', '--'
        rows.append([no, title, '%s · %s' % (size, scale), status, fname, tb])
    return rows, issued, sorted(present - claimed)


# ============================================================================ TEXT BLOCKS
_BLANK = '____________________'
_TBE = 'NOT YET ENGAGED  ________________'   # the visible blank line Checklist §1.e.1 asks for
CONTACTS = [
    ['Owner / applicant', 'Mohammed Awad — owner of record, PINs R6123 033 and R6123 015',
     '4541 Arcado Rd SW, Lilburn, GA 30047-3968', _BLANK],
    ['Co-applicant owner', 'Santos C. Mendez and Lesvia Rosario Roblero de Leon — owners of '
     'record, PINs R6123 014 and R6123 162', '4535 Arcado Rd SW, Lilburn, GA 30047-3968', _BLANK],
    ['24-hour contact', 'Mohammed Awad — 24-hour emergency contact for the site',
     '4541 Arcado Rd SW, Lilburn, GA 30047-3968', _BLANK],
    ['Designer / preparer', 'Owner-prepared, AI-assisted drafting. NOT A DESIGN PROFESSIONAL.',
     'As above', _BLANK],
    ['Land surveyor (RLS)', _TBE, _BLANK, _BLANK],
    ['Civil engineer (PE)', _TBE, _BLANK, _BLANK],
    ['Architect (GA RA)', _TBE, _BLANK, _BLANK],
    ['Landscape architect', _TBE, _BLANK, _BLANK],
    ['Geotech. engineer', _TBE, _BLANK, _BLANK],
    ['Stream delineation', _TBE, _BLANK, _BLANK],
    ['Traffic engineer', _TBE, _BLANK, _BLANK],
    ['Attorney', _TBE, _BLANK, _BLANK],
    ['City contact', 'Reid Turner, Planning Director, City of Lilburn',
     '340 Main St, Lilburn, GA 30047', '(770) 279-3715\nreturner@cityoflilburn.com'],
]


def zoning_rows():
    return [
        ['Existing zoning', 'R-1, Single-Family Residential, City of Lilburn — all four parcels '
                            '(Ord. 2023-603 §401)'],
        ['Proposed zoning', 'R-2, Medium-Density Residential, City of Lilburn (Ord. 2023-603 §402)'],
        ['Proposed use', '"Single-family (cluster-cottage, creative lot configuration)" — P '
                         '(permitted by right) in R-2, §602 Use Table. No special use permit; no '
                         'commercial, attached or multi-family use.'],
        ['Occupancy', '55+ Housing for Older Persons (42 U.S.C. §3607(b)(2)(C); 24 CFR Part 100 '
                      'Subpart E) by voluntary condition and recorded covenants. 0 students '
                      'generated.'],
        ['Gross site area', '%s ac deeded (%s SF) = 0.99 + 2.00 + 2.00 + 4.45 ac; %.3f ac (%s SF) '
                            'GIS-calculated. THE SEALED RLS SURVEY GOVERNS.'
                            % (DEED_AC, fmt(DEED_SF), GIS_AC, fmt(GIS_SF))],
        ['Lots / dwelling units', '%d one-story detached cottage homes on fee-simple lots; %d plan '
                                  'types; HOA-maintained yards' % (LOTS, len(PLANS))],
        ['Gross density', 'PROVIDED %.2f du/ac deeded (%.2f GIS) — REQUIRED max. 8.0 du/ac '
                          '(Table 4.1, R-2)' % (DENS_DEED, DENS_GIS)],
        ['Lot area / width /\ndepth', 'PROVIDED %s SF typical, 50\'-0" x 100\'-0" — REQUIRED min. '
                                      '3,000 SF, 50 ft, 100 ft (Table 4.1, cottage home)'
                                      % fmt(LOT_SF)],
        ['Setbacks', 'PROVIDED / REQUIRED front 15\'-0" from the lane tract and 50\'-0" from the '
                     'Arcado Rd R/W; side 5\'-0"; rear 20\'-0"; accessory 5\'-0" (Table 4.1)'],
        ['Buffer abutting R-1', 'PROVIDED / REQUIRED 20\'-0" undisturbed on every line but the '
                                'Arcado Rd frontage, within the lots as a recorded easement '
                                '(§313(1)) — see note 14'],
        ['Height / floor area', 'PROVIDED 1 story, ridge %.1f ft; %s and %s SF conditioned (%s and '
                                '%s bodies) — REQUIRED max. 40 ft, min. 1,000 SF heated'
                                % (RIDGE, fmt(COND_A), fmt(COND_B), BODY_A, BODY_B)],
        ['Parking', 'PROVIDED %d on lot (2-car garage + 2-car drive) + %d guest and kiosk spaces '
                    'incl. 1 van-accessible — REQUIRED %d (Table 8.1, 2 per DU, no maximum)'
                    % (LOTS * 4, GUEST, LOTS * 2)],
        ['Common open space', 'PROVIDED %s SF = %.2f ac = %.1f%% of gross, in common tracts. '
                              'Development Regs. §5.9 does not apply below 50 ac (note 13), so '
                              'this is voluntary.' % (fmt(OS_SF), OS_AC, OS_PCT)],
        ['Streets', 'One private lane %s ft long in a private tract; all components to meet the '
                    'minimum public-street standards (Checklist §4.s). None offered for dedication.'
                    % fmt(LANE_FT)],
        ['Acreage disturbed', '%.2f ac on site. Off-site: the Phase-2 sewer corridor, about %s ft, '
                              'quantified on Sheet C-4.0 (Checklist §4.e).'
                              % (DISTURBED_AC, fmt(SEWER_EXT_FT))],
        ['Adjoining zoning', 'R-1, City of Lilburn, single-family, on every property line. Nearest '
                             'R-2 about 106 ft NE; unincorporated Gwinnett R-100 about 314 ft. '
                             'Owners: docs/06 and Sheet C-1.0.'],
        ['Water and sewer', 'Gwinnett County Dept. of Water Resources — water and sanitary sewer '
                            'only. All other utilities by private providers (note 11).'],
        ['Frontage / access', '%s ft on Arcado Rd SW (chord); one entrance in the SW third of the '
                              'frontage, about 252 ft from the Arcadia Pl centreline. No lot takes '
                              'access from Arcado Rd.' % fmt(FRONTAGE_FT, 1)],
    ]


NOTES = [
    ('STATUS AND SEALS.', 'This set is owner-prepared from public records for pre-application '
     'review and the rezoning hearing. DRAFT — NOT SEALED: no sheet is sealed by a Georgia '
     'registered land surveyor, professional engineer, architect or landscape architect, and the '
     'seal blocks are blank because none is yet engaged. Every statement of conformity reads '
     '"appears consistent with"; none is a certification of compliance. Final plan sets must be '
     'sealed, signed and dated across the seal by the licensed registered party responsible for '
     'the contents of the sheet (Georgia Board Rule 180-12-.02; Checklist §1.e).'),

    ('APPROVAL NOTES — required on the cover by Checklist §4.a, verbatim:',
     '"APPROVAL OF THESE PLANS DOES NOT RELIEVE THE OWNER, DEVELOPER, AND/OR CONTRACTOR FROM '
     'COMPLYING WITH ALL APPLICABLE RULES, REGULATIONS, AND ORDINANCES."   "DEVELOPER TO PROVIDE '
     'TO CITY CERTIFIED DETENTION POST-CONSTRUCTION (RECORD) DRAWINGS WITH THE SUBMITTAL OF THE '
     'FINAL PLAT OR ONE WEEK PRIOR TO REQUESTING A CERTIFICATE OF OCCUPANCY, SO THAT THE '
     'POST-CONSTRUCTION CONDITIONS MAY BE VERIFIED AND APPROVED. CERTIFIED RECORD DRAWINGS SHALL '
     'INCLUDE TOPOGRAPHY OF POND AND OUTLET STRUCTURE DETAIL USING POST-CONSTRUCTION SURVEY DATA. '
     'USING RECORD DRAWINGS, PROVIDE A CERTIFIED HYDROLOGY REPORT VERIFYING POND VOLUMES AND PEAK '
     'OUTFLOWS FROM REGULATED STORM EVENTS."'),

    ('ZONING HISTORY AND CONDITIONS (Checklist §1.a, §4.b).', 'THERE ARE NO ZONING CONDITIONS ON '
     'THIS PROPERTY. Zoning case no. RZ-2026-______ (assigned by the City); date of approval '
     '__________; conditions __________. No special use permit, Zoning Board of Appeals variance '
     'or administrative variance is of record on any of the four parcels, and no overlay district '
     'applies. The only prior case is RZ-2025-01, a mixed-use request for 104 condominium units on '
     'this assemblage, which the Planning Commission TABLED on 2025-08-28 on a defective legal '
     'advertisement. It was never heard on its merits and never denied, so the twelve-month bar of '
     '§1003-11 does not appear to apply — confirm the file status with the Planning Director.'),

    ('FLOODPLAIN (Checklist §9 Floodplain a, b).', 'The property lies wholly in FEMA Zone X (area '
     'of minimal flood hazard), FIRM panel %s (FEMA National Flood Hazard Layer; Gwinnett GIS). NO '
     'SPECIAL FLOOD HAZARD AREA, FLOODWAY OR BASE FLOOD ELEVATION IS MAPPED ON THIS PROPERTY and '
     'no development is proposed in a floodplain. The Gwinnett future-conditions floodplain '
     '(www.gwinnettfloodplain.com) shall be checked before the Land Disturbance Permit; where one '
     'exists, finished floors shall be at least 1 ft above the future-conditions elevation and 3 '
     'ft above the 100-year base flood elevation (§9 Floodplain f). Lilburn Code Ch. 109 Art. III '
     'governs.' % FIRM),

    ('WETLANDS (Checklist §9 Wetlands a, b).', 'No wetland is mapped on the property by the U.S. '
     'Fish and Wildlife Service National Wetlands Inventory. A field survey of any waters of the '
     'United States shall be made with the boundary and topographic survey; any delineation shall '
     'state its source and carry U.S. Army Corps of Engineers approval, and it is the owner\'s '
     'responsibility to obtain any Corps permit required.'),

    ('STREAM BUFFERS — required by Checklist §9 Buffered State Waters e and f, verbatim:',
     '"STREAM BUFFERS ARE TO REMAIN IN A NATURAL AND UNDISTURBED CONDITION."   "STREAM BUFFER '
     'SHALL BE STAKED AND PROTECTED PRIOR TO LAND DISTURBANCE."   An unnamed order-0 headwater of '
     'Jackson Creek (GAR030701030315; Georgia 2024 §303(d) list) reaches about 30 ft inside the SW '
     'property line and ends on the property. The 25-ft state buffer (O.C.G.A. §12-7-6(b)(15)), '
     'the 50-ft undisturbed buffer and the 75-ft impervious setback (Lilburn Code Ch. 109 Art. '
     'VII) are labelled on Sheets C-1.0, C-2.0 and C-2.2 from the top of bank. TOP OF BANK IS '
     'APPROXIMATE: the state waters shall be field-located and both banks delineated by a '
     'qualified professional, and that delineation governs. No buffer variance is requested with '
     'this rezoning.'),

    ('SIGNS (Checklist §4.q).', 'One monument entry sign not over 32 SF is proposed at the Arcado '
     'Rd entrance; its location, size and sight-triangle clearance are on Sheets C-2.3 and A-3.0. '
     'NO WALL SIGNS ARE PROPOSED ON ANY DWELLING OR ON THE CLUBHOUSE. ALL SIGNS SHALL BE PERMITTED '
     'SEPARATELY. A sign easement may be required.'),

    ('MAIL DELIVERY (Checklist §4.r).', 'Mail will be delivered to a cluster box unit (CBU) kiosk '
     'in the amenity tract inside the entrance, with protection from the elements, an accessible '
     'route and four short-term spaces; detailed on Sheet A-3.0. THE LILBURN POST OFFICE GROWTH '
     'MANAGER SHALL BE CONTACTED FOR MAIL DELIVERY AND MAILBOX REQUIREMENTS. A cluster mailbox '
     'system may be required for the entire project and one street name may serve to assign all '
     'house numbers.'),

    ('GRADING — required by Checklist §10.a on the grading plan and on all soil-erosion, '
     'sedimentation and pollution-control sheets, verbatim:',
     '"MAXIMUM CUT OR FILL SLOPES IS 2H:1V"   "CITY OF LILBURN/GWINNETT COUNTY ASSUMES NO '
     'RESPONSIBILITY FOR OVERFLOW OR EROSION OF NATURAL OR ARTIFICIAL DRAINS BEYOND THE EXTENT OF '
     'THE STREET RIGHT-OF-WAY, OR FOR THE EXTENSION OF CULVERTS BEYOND THE POINT SHOWN ON THE '
     'APPROVED AND RECORDED PLAN. THE CITY OF LILBURN/GWINNETT COUNTY DOES NOT ASSUME THE '
     'RESPONSIBILITY FOR THE MAINTENANCE OF PIPES IN DRAINAGE EASEMENTS BEYOND THE CITY/COUNTY '
     'RIGHT-OF-WAY."   "STRUCTURES ARE NOT ALLOWED IN DRAINAGE EASEMENTS."'),

    ('STREET GRADES.', 'Maximum street grade 12%%; grades of 12%% to 15%% require an "As Graded" '
     'survey before installation of the curb (Checklist §7.k). Existing ground on the lane '
     'alignment reaches %.1f%% — see Sheet C-5.0.' % LANE_GRADE),

    ('UTILITIES (Checklist §4.d).', 'Gwinnett County Department of Water Resources provides water '
     'and sanitary sewer only; electric, gas and telecommunication service is by the respective '
     'private providers, and new electric distribution within the development will be underground. '
     'PHASE 1 connects by gravity to the existing 8-in sewer already crossing this property '
     '(manhole invert 927.13) and needs no extension. PHASE 2 needs an off-site gravity extension '
     'of about %s ft to the Legends at Parkview 8-in main at invert 919.58. A private pump '
     'station, force main or gravity sewer is NOT available: Gwinnett DWR\'s Standard Policy for '
     'Private Developments (Condominiums, Townhomes and Subdivisions, rev. 9/2018) allows private '
     'facilities "only ... for commercial properties under single ownership within a development", '
     'and a county station fails WSR-24 §1.3.1(A) because gravity is %s ft away, not "more than '
     '5,000 feet down gradient". A DWR sewer capacity certification is required. See Sheets C-4.0 '
     'and C-4.1.' % (fmt(SEWER_EXT_FT), fmt(SEWER_EXT_FT))),

    ('FIRE ACCESS.', 'One private lane about %s ft long, dead-ended at the NW terminus, 22 ft of '
     'clear pavement, no parking, hammerhead turnarounds. SPECIAL APPROVAL OF A DEAD-END FIRE '
     'APPARATUS ACCESS ROAD OVER 750 FT IS REQUESTED under IFC 2024 (GA) Appendix D103.4, Table '
     'D103.4. Two access roads are NOT required: Ga. Comp. R. & Regs. 120-3-3-.04 replaces '
     'Appendix D107.1 and sets the trigger above 120 dwelling units, and %d are proposed. NFPA 13D '
     'sprinklers in every dwelling are offered VOLUNTARILY and are not a code requirement. Codes: '
     'the Georgia State Minimum Standard Codes effective 1 January 2026 (2024 IRC / IBC / IFC / '
     'IPC / IMC / IFGC with the 2026 Georgia Amendments; 2023 NEC; 2015 IECC as amended).'
     % (fmt(LANE_FT), LOTS)),

    ('OPEN SPACE AND RECREATION AREAS.', 'Development Regulations §5.9.1 requires recreation land '
     'in single-family detached subdivisions "having a gross area of 50 acres or more". At %s '
     'acres this development is below that threshold and §5.9 does not apply; the %.1f%% of common '
     'open space shown is voluntary.' % (DEED_AC, OS_PCT)),

    ('BUFFERS AND THE §313(1) READING.', 'The 20-ft undisturbed buffer required abutting R-1 '
     '(Table 4.1, allowed dwelling types other than detached single-family) is held within the '
     'lots as a recorded buffer easement in reliance on §313(1), "Buffer requirements ... '
     'supersede these minimum required yards". THIS READING IS TO BE CONFIRMED WITH THE PLANNING '
     'DIRECTOR; Sheet C-2.4 carries the fallback layout, 50 x 82-ft lots with the buffer in a '
     'separate common tract, if a separate tract is required.'),

    ('DIMENSIONS, DATUM AND COORDINATES.', 'All dimensions are in US survey feet. Horizontal datum '
     'Georgia State Plane West Zone (SR 2240), NAD83; vertical NAVD88. Sheets C-1.0 to C-8.0 are '
     'drawn in a site-local system (+u along the strip on a bearing of N 28°43\' W from the Arcado '
     'Rd R/W corner at 2,310,954.00 E / 1,411,431.50 N; +v across the strip toward the NE line). '
     'THE TWO MAPS ON THIS SHEET ARE DRAWN NORTH-UP. Boundary geometry is Gwinnett GIS and is '
     'DRAFT; topography is USGS 3DEP and is approximate. THE SEALED SURVEY GOVERNS.'),

    ('SHEET INDEX INTEGRITY.', 'The sheet index is generated at plot time by listing the files '
     'present in the package drawings/ directory and matching them against the sheet table in '
     'tools/cover.py — the same table tools/transmittal.py uses for the filing transmittal. A row '
     'marked NOT ISSUED is not in this set and must not be relied on. Where the "T/B" column shows '
     'a number, that sheet\'s own title block still carries a provisional number from an earlier '
     'numbering; THE NUMBER IN THIS INDEX GOVERNS and the sheet will be renumbered at the next '
     'issue.'),

    ('SCALES AND LETTERING.', 'A graphic scale and a north arrow are shown on each map here and on '
     'every applicable sheet (Checklist §4.h); engineering scales on the C-sheets, architectural '
     'on the A-sheets. DO NOT SCALE A REDUCED PRINT — use the graphic scale. Lettering on this '
     'sheet is 10.5 pt in the general notes, 8.5 to 11 pt in the tables, legend and map '
     'annotation, and 7 to 8 pt in the title block and map furniture — a cap height of 0.068 to '
     '0.107 in at full size. The set standard is a 1/8-in cap height; the content this checklist '
     'requires on a cover page does not fit an ARCH D sheet at that size, so this sheet carries '
     'the largest type that fits.'),

    ('BASIS AND SOURCES.', 'Gwinnett County GIS — parcels, zoning, streets, right-of-way, sewer, '
     'water, hydrology, floodplain, soils, queried 2026-08-28; Gwinnett Tax Assessor 2026 '
     'property-ownership file; USGS 3DEP; FEMA NFHL; Ride Gwinnett GTFS feed 2026-07-02; City of '
     'Lilburn Zoning Ordinance 2023-603, 2026 Application Instructions, Site Development Plan '
     'Review Checklist, 2024 Comprehensive Plan and the 2026 Comprehensive Plan Amendment '
     '(transmitted to DCA 2026-07-13; adoption pending as of %s). Package files FACTS.md, '
     'data/layout.json and data/plans.json, all read at plot time.' % sb.DATE),
]

# The eleven items of the City's 2026 Application Instructions, and what answers each — the same
# list tools/transmittal.py puts in docs/00, so the cover and the transmittal cannot disagree.
SUBMITTAL = [
    ['1  Application Form', 'docs/01-application-form-data.md'],
    ['2  Application Fee', '$1,250 — see APPLICATION DATA in the title banner above'],
    ['3  Standards Governing the Zoning Power (§1003-7)', 'docs/04 — the six §1003-7 criteria'],
    ['4  Conflict of Interest Form (§36-67A-3)', 'docs/07 — file with the application'],
    ['5  Notarized owner signatures', 'docs/07 — two ownership groups'],
    ['6  Letter of Intent', 'docs/03 — states the voluntary conditions offered'],
    ['7  Legal Description (metes and bounds)', 'docs/05 — DRAFT; sealed RLS description governs'],
    ['8  Site Plan', 'This drawing set; Sheet C-2.0 is the site plan proper'],
    ['9  Boundary Survey', 'NOT INCLUDED — must be commissioned (Georgia RLS)'],
    ['10  List of Adjoining Property Owners', 'docs/06 — re-pull on the filing date'],
    ['11  Architectural Renderings and Elevations', 'docs/09 and Sheets A-1.1 to A-4.1'],
]

SEALS = [
    ('GEORGIA REGISTERED LAND SURVEYOR',
     'Boundary survey plat, metes-and-bounds legal description and topographic survey — Ord. '
     '2023-603 §1003-4.3 and §1003-4.4; Checklist §1.e.2. Sheet C-1.0.'),
    ('GEORGIA REGISTERED PROFESSIONAL ENGINEER',
     'Grading, drainage, certified stormwater report, sewer, water, private street design and '
     'retaining walls — Checklist §1.e.7-9, §8.a, §11.a. Sheets C-3.0 to C-5.0 and C-8.0.'),
    ('GEORGIA REGISTERED ARCHITECT',
     'Dwelling and clubhouse plans and elevations — 2026 Application Instructions item (11). '
     'Sheets A-1.1 to A-4.1.'),
    ('GA REGISTERED LANDSCAPE ARCHITECT / FORESTER / ARBORIST',
     'Buffer and landscape plan, tree protection and preservation — Checklist §1.e.10 and §6.a. '
     'Sheets C-1.1 and C-7.0.'),
]

REVISIONS = [['0', sb.DATE, 'Issued for pre-application review — DRAFT, not sealed', 'M.A.']] + \
            [['', '', '', ''] for _ in range(4)]

# Legend — one entry per symbol drawn on the two maps, and no entry that is not drawn.
LEGEND = [
    ('site', '', 0, '', 'Subject property — the %s-ac assemblage to be rezoned R-1 → R-2' % DEED_AC),
    ('line', sb.C['adj_line'], 0.5, '', 'Adjoining tax parcel (Gwinnett GIS) — vicinity map'),
    ('line', '#8a8a8a', 0.8, '', 'Street centreline (Gwinnett GIS)'),
    ('line', '#333333', 2.0, '', 'Arcado Rd SW / Killian Hill Rd — county collectors'),
    ('line', '#333333', 1.2, '7 4', 'Centreline produced — not mapped in the source data'),
    ('line', sb.C['stream'], 1.4, '', 'Stream — state waters (top of bank approximate)'),
    ('stop', sb.C['red'], 0, '', 'Ride Gwinnett Route 25 bus stop (GTFS feed 2026-07-02)'),
    ('line', sb.C['red'], 1.1, '5 3', 'Straight-line distance from the site'),
    ('rect', 'url(#r2hatch)', 0, '', 'Existing R-2 zoning, City of Lilburn — nearest R-2 precedent'),
    ('rect', '#eef2e6', 0, '', 'Existing R-1 zoning, City of Lilburn — location map'),
    ('rect', '#e4ecf4', 0, '', 'R-100 zoning, unincorporated Gwinnett — location map'),
    ('ring', '#7a5230', 0, '', 'Distance ring from the site, 1/4 and 1/2 mile — location map'),
    ('arrow', '#7a5230', 0, '', 'Direction and straight-line distance to an off-map destination'),
]


# ============================================================================ sheet frame
def _frame():
    """ARCH D border, title block and disclaimer strip — sitebase.sheet()'s frame with no plan
    window.  Returns (Drawing, margins dict)."""
    W, H, m, i_ = sb.SHEET_W, sb.SHEET_H, sb.MARGIN, sb.INNER
    D = sb.Drawing(1.0, 0.0, 0.0, fs=1.0, win=(0, 1, 0, 1))
    D.add('<svg xmlns="http://www.w3.org/2000/svg" width="36in" height="24in" '
          'viewBox="0 0 %d %d" font-family="%s">' % (W, H, sb.FONT))
    D.add('<title>%s</title>' % sb.esc('%s — %s — Sheet %s'
                                       % (sb.PROJECT.title(), SHEET_TITLE, SHEET_NO)))
    D.add(sb.DEFS)
    D.srect(0, 0, W, H, fill='#fff')
    D.srect(m, m, W - 2 * m, H - 2 * m, fill='none', stroke='#000', stroke_width=2)
    D.srect(m + i_, m + i_, W - 2 * m - 2 * i_, H - 2 * m - 2 * i_,
            fill='none', stroke='#000', stroke_width=0.6)

    tb_y, tb_h = sb.TB_Y, sb.TB_H - 6
    D.srect(m + i_, tb_y, W - 2 * m - 2 * i_, tb_h, fill='#fff', stroke='#000', stroke_width=1.2)
    cells = [0, 820, 1330, 1780, 2180, W - 2 * m - 2 * i_]
    for cx in cells[1:-1]:
        D.sline(m + i_ + cx, tb_y, m + i_ + cx, tb_y + tb_h, stroke='#000', stroke_width=0.8)
    bx = m + 8
    D.stext(bx, tb_y + 30, sb.PROJECT, size=22, bold=True)
    D.stext(bx, tb_y + 52, '%s — Rezoning R-1 → R-2 (City of Lilburn, Georgia)' % SHEET_TITLE,
            size=13, bold=True)
    D.stext(bx, tb_y + 70, '%s — %s' % (sb.ADDRESSES, sb.LEGAL), size=9)
    D.stext(bx, tb_y + 86, 'Cover page per City of Lilburn Site Development Plan Review Checklist '
                           '§1.e.1, §4.a and §4.b; sheet index generated from drawings/ at plot '
                           'time', size=9)
    bx = m + i_ + cells[1] + 8
    D.stext(bx, tb_y + 18, 'APPLICANT / OWNER', size=8, fill='#555')
    D.stext(bx, tb_y + 34, sb.APPLICANT, size=11, bold=True)
    D.stext(bx, tb_y + 48, '4541 Arcado Rd SW, Lilburn GA 30047-3968 (parcels 033, 015); '
                           'Mendez / Roblero de Leon', size=7)
    D.stext(bx, tb_y + 58, '(parcels 014, 162) — co-applicants, owner signatures required', size=7)
    D.stext(bx, tb_y + 74, 'PREPARED FOR', size=8, fill='#555')
    D.stext(bx, tb_y + 88, 'Pre-application conference, City of Lilburn Planning & Zoning '
                           '(340 Main St) —', size=8)
    D.stext(bx, tb_y + 98, 'rezoning application per Ord. 2023-603 §1003 (2026 Application '
                           'Instructions)', size=8)
    bx = m + i_ + cells[2] + 8
    D.stext(bx, tb_y + 18, 'STATUS', size=8, fill='#555')
    D.stext(bx, tb_y + 38, 'DRAFT — NOT SEALED', size=14, bold=True, fill='#c00')
    for k, ln in enumerate([
            'Owner-prepared cover page for pre-application review. No sheet in',
            'this set is sealed; the seal blocks are blank because no Georgia RLS,',
            'PE, architect or landscape architect is yet engaged. To be superseded',
            'by sealed survey, civil, architectural and landscape drawings.']):
        D.stext(bx, tb_y + 54 + k * 11, ln, size=8)
    D.stext(bx, tb_y + 100, 'Generator: tools/cover.py (on tools/sitebase.py)', size=8)
    bx = m + i_ + cells[3] + 8
    for k, (a, b) in enumerate([('DATE', sb.DATE), ('SCALE', 'As noted — see each map'),
                                ('DATUM', 'SR 2240 GA West US-ft; NAVD88'),
                                ('DRAWN', 'owner-prepared (AI-assisted)'),
                                ('CHECKED', 'RLS / PE — pending')]):
        D.stext(bx, tb_y + 16 + k * 18, a, size=7.5, fill='#555')
        D.stext(bx + 55, tb_y + 16 + k * 18, b, size=8.5)
    bx = m + i_ + cells[4] + 8
    D.stext(bx, tb_y + 18, 'SHEET', size=8, fill='#555')
    D.stext(bx + 150, tb_y + 72, SHEET_NO, size=54, bold=True, anchor='middle')
    D.stext(bx + 150, tb_y + 92, SHEET_TITLE, size=8, anchor='middle')

    dy = sb.TB_Y - 46
    D.srect(m + i_, dy, W - 2 * m - 2 * i_, 40, fill='#fff8e1', stroke='#b00', stroke_width=0.8)
    D.stext(m + i_ + 8, dy + 15, 'Disclaimer: ' + sb.DISCLAIMER.split('Disclaimer: ')[-1],
            size=9, bold=True, fill='#7a0000')
    D.stext(m + i_ + 8, dy + 30,
            'Label: DRAFT / NOT SEALED — every item that must be sealed by a Georgia RLS, PE, '
            'architect or landscape architect is shown as a concept only. Statements of conformity '
            'read "appears consistent with".', size=8, fill='#7a0000')
    D.add('<!-- %s -->' % sb.MARKER)
    return D, {'l': m + i_ + 10, 'r': W - m - i_ - 10, 't': m + i_ + 10, 'b': dy - 14}


# ============================================================================ map furniture
def north_up(c, x, y, r=24.0):
    c.srect(x - 52, y - r - 22, 104, 2 * r + 62, fill='#fff', stroke='#999', stroke_width=0.6)
    c.scircle(x, y, r, fill='#fff', stroke='#000', stroke_width=0.8)
    c.sline(x, y + r * 0.76, x, y - r * 0.84, stroke='#000', stroke_width=2.0)
    c.spoly([(x, y - r * 0.84), (x - 6.0, y - r * 0.84 + 15), (x + 6.0, y - r * 0.84 + 15)],
            fill='#000')
    c.stext(x, y - r - 8, 'N', size=13, bold=True, anchor='middle')
    c.stext(x, y + r + 13, 'GRID NORTH', size=8, anchor='middle', bold=True)
    c.stext(x, y + r + 23, '(SR 2240 GA WEST)', size=7.5, anchor='middle')
    c.stext(x, y + r + 33, 'MAP DRAWN NORTH-UP', size=7.5, anchor='middle')


def scale_bar(c, x, y, pt_per_ft, step_ft, steps, h=8.0, lsize=10.0):
    w = step_ft * pt_per_ft * steps
    cap = 'GRAPHIC SCALE   1" = %s\'' % fmt(72.0 / pt_per_ft)
    pw = max(w + 28, tw(cap, lsize, True) + 14)
    c.srect(x + w / 2.0 - pw / 2.0, y - 18, pw, h + 44, fill='#fff', stroke='#999',
            stroke_width=0.6)
    for k in range(steps):
        c.srect(x + step_ft * pt_per_ft * k, y, step_ft * pt_per_ft, h,
                fill='#000' if k % 2 == 0 else '#fff', stroke='#000', stroke_width=0.6)
        c.stext(x + step_ft * pt_per_ft * k, y - 4, fmt(step_ft * k), size=8.5, anchor='middle')
    c.stext(x + w, y - 4, '%s ft' % fmt(step_ft * steps), size=8.5, anchor='middle')
    c.stext(x + w / 2.0, y + h + 14, cap, size=lsize, bold=True, anchor='middle')


def bus_stop(c, p, r=6.0):
    x, y = c.X(p[0]), c.Y(p[1])
    c.scircle(x, y, r + 2.0, fill='#fff', stroke='#fff', stroke_width=1.5)
    c.scircle(x, y, r, fill=sb.C['red'], stroke='#fff', stroke_width=1.4)
    c.scircle(x, y, r * 0.42, fill='#fff')


def inwin(c, p, pad=0.0):
    u0, u1, v0, v1 = c.win
    return u0 + pad <= p[0] <= u1 - pad and v0 + pad <= p[1] <= v1 - pad


def label_along(c, paths, text, size=9.0, fill='#666', bold=False, pad=0.0):
    """Name a street along its longest segment that lies inside the map window."""
    best, bl = None, 0.0
    for path in paths:
        q = ENs(path)
        for a, b in zip(q[:-1], q[1:]):
            mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            d = sb.dist(a, b)
            if d > bl and inwin(c, mid, pad):
                best, bl = (a, b, mid), d
    if best and bl * c.s > tw(text, size) * 0.85:
        a, b, mid = best
        c.text(mid[0], mid[1], text, size=size, rot=c.rot_of(a, b), fill=fill, halo=True,
               bold=bold, dy=-2.5)
        return True
    return False


def ray_hit(p0, d, segs):
    """First intersection of the ray p0 + t*d (t > 0) with a list of (a, b) segments."""
    best = None
    for a, b in segs:
        e = (b[0] - a[0], b[1] - a[1])
        den = d[0] * e[1] - d[1] * e[0]
        if abs(den) < 1e-9:
            continue
        w = (a[0] - p0[0], a[1] - p0[1])
        t = (w[0] * e[1] - w[1] * e[0]) / den
        s = (w[0] * d[1] - w[1] * d[0]) / den
        if t > 0 and -0.05 <= s <= 1.05 and (best is None or t < best[0]):
            best = (t, (p0[0] + t * d[0], p0[1] + t * d[1]))
    return best


def street_parts(name):
    return [p for s in sb.CTX['streets'] if s['name'] == name for p in s['paths_local']]


def killian_at_arcado():
    """Where Arcado Rd meets Killian Hill Rd, in (E, N).

    The Gwinnett GIS Arcado Rd centreline is clipped short of the intersection.  The point returned
    is that centreline PRODUCED on the bearing of its last mapped course, cut by the mapped Killian
    Hill Rd polyline.  Returns (point, tail of the produced line) or None.
    """
    ends = []
    for path in street_parts('ARCADO RD'):
        q = ENs(path)
        ends += [(q[-1][1], q[-1], q[-2]), (q[0][1], q[0], q[1])]
    if not ends:
        return None
    _, tip, prev = max(ends, key=lambda e: e[0])
    d = (tip[0] - prev[0], tip[1] - prev[1])
    n = math.hypot(*d) or 1.0
    d = (d[0] / n, d[1] / n)
    segs = []
    for path in street_parts('KILLIAN HILL RD'):
        q = ENs(path)
        segs += list(zip(q[:-1], q[1:]))
    hit = ray_hit(tip, d, segs)
    return (hit[1], tip) if hit else None


# ============================================================================ the two maps
VWIN = (-1875.0, 1125.0, -975.0, 2025.0)           # E0, E1, N0, N1 — 3,000 x 3,000 ft
VSC = 72.0 / 400.0                                  # 1" = 400'  -> 540 x 540 pt
LWIN = (-3464.0, 2536.0, -1273.0, 2727.0)          # 6,000 x 4,000 ft, centred on the site
LSC = 72.0 / 1000.0                                 # 1" = 1,000' -> 432 x 316.8 pt

SITE_EN = ENs(sb.BOUNDARY)
SITE_MID = EN((sb.U_REAR / 2.0, -117.0))
HEAVY = ('ARCADO RD', 'KILLIAN HILL RD')


def draw_streets(c, names=True, size=8.5):
    for s in sb.CTX['streets']:
        big = s['name'] in HEAVY
        for path in s['paths_local']:
            c.pline(ENs(path), fill='none', stroke='#333333' if big else '#8a8a8a',
                    stroke_width=2.0 if big else 0.8, stroke_linejoin='round')
    if not names:
        return
    for nm in sorted({s['name'] for s in sb.CTX['streets']}):
        if nm in HEAVY:                       # the two collectors are hand-placed in vicinity()
            continue
        label_along(c, street_parts(nm), nm, size=size, fill='#777', pad=90.0)


def draw_streams(c):
    for st in sb.CTX['streams']:
        for path in st['paths_local']:
            c.pline(ENs(path), fill='none', stroke=sb.C['stream'], stroke_width=1.4,
                    stroke_linejoin='round')


def draw_site(c, heavy=2.4, label=True):
    c.poly(SITE_EN, fill='#fdf3d0', fill_opacity='0.9', stroke='#000', stroke_width=heavy)
    if label:
        rot = c.rot_of(EN((300.0, -117.0)), EN((1300.0, -117.0)))
        c.text(SITE_MID[0], SITE_MID[1], 'SUBJECT PROPERTY — %s AC' % DEED_AC, size=11,
               bold=True, rot=rot, halo=True)


def draw_r2(c, label=True):
    for z in sb.CTX['zoning']:
        if z['type'] != 'R2':
            continue
        ring = ENs(z['ring_local'])
        c.poly(ring, fill='url(#r2hatch)', stroke='#c07a30', stroke_width=1.0)
        if label:
            ctr = sb.poly_centroid(ring)
            c.line((ctr[0] + 60, ctr[1] - 70), (560.0, -40.0), stroke='#8a4b12', stroke_width=0.8)
            c.textlines(1090.0, -30.0,
                        ['EXISTING R-2 (CITY OF LILBURN) —', '"ARCADO ROAD TOWNHOMES",',
                         'THE NEAREST R-2, ABOUT 106 FT NE'],
                        size=8.5, anchor='end', fill='#8a4b12', halo=True, bold_first=True)


def vicinity(x, y):
    c = sb.Drawing(VSC, x, y, fs=1.0, win=VWIN)
    W = (VWIN[1] - VWIN[0]) * VSC
    H = (VWIN[3] - VWIN[2]) * VSC
    c.clip_open(fill='#fbfbf8')
    for a in sb.CTX['adjoining_parcels']:
        c.poly(ENs(a['ring_local']), fill='#f4f4f0', stroke=sb.C['adj_line'], stroke_width=0.5)
    draw_streets(c)
    draw_streams(c)
    draw_r2(c)
    draw_site(c)

    kh = killian_at_arcado()
    if kh:
        stop, tail = kh
        c.pline([tail, stop], fill='none', stroke='#333333', stroke_width=1.2,
                stroke_dasharray='7 4')
        c.pline([(0.0, 0.0), stop], fill='none', stroke=sb.C['red'], stroke_width=1.1,
                stroke_dasharray='5 3')
        d_ft = math.hypot(*stop)
        c.line((900.0, 1830.0), (stop[0] + 20.0, stop[1] + 60.0), stroke=sb.C['red'],
               stroke_width=0.8)
        c.textlines(1085.0, 1900.0, ['RIDE GWINNETT ROUTE 25 STOP',
                                     'KILLIAN HILL RD @ ARCADO RD — 0.30 MI'],
                    size=9, anchor='end', fill=sb.C['red'], halo=True, bold_first=True)
        bus_stop(c, stop)
        mid = (stop[0] * 0.55, stop[1] * 0.55)
        c.text(mid[0] + 90, mid[1] + 50, '%s FT = %.2f MI STRAIGHT-LINE'
               % (fmt(d_ft), d_ft / 5280.0), size=8.5, fill=sb.C['red'], halo=True, bold=True,
               rot=c.rot_of((0.0, 0.0), stop))

    for uv, txt in (((620.0, 250.0), 'KING DAVID MANOR  (PLAT S/159) — ZONED R-1'),
                    ((620.0, -430.0), 'LEGENDS AT PARKVIEW  (PLAT 118/187) — ZONED R-1')):
        p = EN(uv)
        rot = c.rot_of(EN((uv[0] - 300, uv[1])), EN((uv[0] + 300, uv[1])))
        c.text(p[0], p[1], txt, size=9.5, bold=True, fill='#4a4a4a', halo=True, rot=rot)
    c.text(-1150.0, 1800.0, 'NANTUCKET  (PLAT 1/268) — ZONED R-1', size=9.5, bold=True,
           fill='#4a4a4a', halo=True, anchor='start')

    # the two county collectors, hand-placed so they clear the callouts and the map furniture
    a, b = EN((-78.8, -692.1)), EN((-65.1, -235.5))
    c.text((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, 'ARCADO RD SW', size=10.5, bold=True,
           fill='#111', halo=True, rot=c.rot_of(a, b), dy=-3)
    kh_pts = [q for path in street_parts('KILLIAN HILL RD') for q in ENs(path)]
    if len(kh_pts) > 3:
        a, b = kh_pts[3], kh_pts[5]
        c.text((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, 'KILLIAN HILL RD', size=10.5, bold=True,
               fill='#111', halo=True, rot=c.rot_of(a, b), dy=-3)

    ap = EN((-12.4, 60.6))
    c.line(ap, (980.0, -400.0), stroke='#111', stroke_width=0.7)
    c.textlines(1085.0, -440.0, ['ARCADIA PL CENTRELINE MEETS', 'ARCADO RD 61 FT NE OF THE',
                                 "SITE'S NE FRONT CORNER"],
                size=8.5, anchor='end', halo=True, bold_first=True)
    c.clip_close()
    # Furniture sits inside this map: the column is only 20 pt wider than the map.  Bottom-left and
    # bottom-centre are the two corners with no geometry in them.
    c.later(lambda: north_up(c, x + 62, y + H - 70))
    c.later(lambda: scale_bar(c, x + 300, y + H - 52, VSC, 200, 4))
    return c


def location(x, y):
    c = sb.Drawing(LSC, x, y, fs=1.0, win=LWIN)
    W = (LWIN[1] - LWIN[0]) * LSC
    H = (LWIN[3] - LWIN[2]) * LSC
    c.clip_open(fill='#fbfbf8')
    for z in sb.CTX['zoning']:
        if z['type'] == 'R1' and z['jurisdiction'] == 'LILBURN':
            c.poly(ENs(z['ring_local']), fill='#eef2e6', stroke='#b9c7a6', stroke_width=0.6)
        elif z['type'] == 'R100':
            c.poly(ENs(z['ring_local']), fill='#e4ecf4', stroke='#a8bccd', stroke_width=0.6)
    draw_streets(c, names=False)
    draw_streams(c)
    draw_r2(c, label=False)
    draw_site(c, heavy=1.8, label=False)

    for en, lines in (((-2560.0, -700.0), ['CITY OF LILBURN', 'R-1']),
                      ((1420.0, -650.0), ['UNINCORPORATED', 'GWINNETT — R-100'])):
        c.textlines(en[0], en[1], lines, size=9.5, fill='#4a5a3a', halo=True, bold_first=True)
    c.text(SITE_MID[0] - 820, SITE_MID[1] + 250, 'SUBJECT PROPERTY', size=9.5, bold=True,
           halo=True, anchor='middle')
    c.line((SITE_MID[0] - 560, SITE_MID[1] + 230), (SITE_MID[0] - 120, SITE_MID[1] + 60),
           stroke='#111', stroke_width=0.7)

    for ft, txt in ((1320.0, '1/4 MILE'), (2640.0, '1/2 MILE')):
        c.circle(SITE_MID, ft * LSC, fill='none', stroke='#7a5230', stroke_width=0.9,
                 stroke_dasharray='4 3')
        a = math.radians(255.0)
        c.text(SITE_MID[0] + ft * math.sin(a), SITE_MID[1] + ft * math.cos(a), txt,
               size=9, fill='#7a5230', bold=True, halo=True)
    c.circle(SITE_MID, 2.6, fill='#7a5230')

    for ang, txt in ((45.0, 'KILLIAN HILL RD 0.30 MI'), (225.0, 'ROCKBRIDGE RD 0.70 MI'),
                     (315.0, 'DOWNTOWN LILBURN 1.4 MI'), (0.0, 'TRICKUM MS 0.46 MI'),
                     (180.0, 'PARKVIEW HS 1.44 MI')):
        a = math.radians(ang)
        d = (math.sin(a), math.cos(a))
        pad = 34.0 / LSC                                      # arrow tip 34 pt inside the border
        r = 1e9
        for k, (lo, hi) in enumerate(((LWIN[0], LWIN[1]), (LWIN[2], LWIN[3]))):
            if abs(d[k]) > 1e-6:
                r = min(r, (((hi - pad) if d[k] > 0 else (lo + pad)) - SITE_MID[k]) / d[k])
        tip = (SITE_MID[0] + d[0] * r, SITE_MID[1] + d[1] * r)
        tail = (tip[0] - d[0] * 420.0, tip[1] - d[1] * 420.0)
        c.line(tail, tip, stroke='#7a5230', stroke_width=1.4)
        px, py, sx, sy = c.X(tip[0]), c.Y(tip[1]), c.X(tail[0]), c.Y(tail[1])
        vx, vy = px - sx, py - sy
        n = math.hypot(vx, vy) or 1.0
        vx, vy = vx / n, vy / n
        c.spoly([(px, py), (px - 9 * vx + 4 * vy, py - 9 * vy - 4 * vx),
                 (px - 9 * vx - 4 * vy, py - 9 * vy + 4 * vx)], fill='#7a5230')
        lp = (tip[0] - d[0] * 660.0, tip[1] - d[1] * 660.0)   # label INSIDE the tip, 47 pt back
        c.text(lp[0], lp[1], txt, size=8.5, fill='#7a5230', bold=True, halo=True, anchor='middle',
               dy=(9 if d[1] < -0.5 else (-4 if d[1] > 0.5 else 0)))
    c.clip_close()
    # This map is 432 pt wide in a 560-pt column, so its furniture goes OUTSIDE the neatline, clear
    # of the direction arrows.
    c.later(lambda: north_up(c, x + W + 59, y + 56))
    c.later(lambda: scale_bar(c, x + W + 26, y + 176, LSC, 500, 2, lsize=8.5))
    return c


def paste(D, sub, border=True):
    """Paste a sub-drawing onto the sheet.  The queued furniture (north arrow, scale bar) is run
    BEFORE render(): each callback emits several elements, so sitebase.place()'s one-pop-per-
    callback idiom would silently drop all but the last of them."""
    for fn in sub.late:
        fn()
    sub.late = []
    x, y, w, h = sub.box()
    D.add(sub.render())
    if border:
        D.srect(x, y, w, h, fill='none', stroke='#000', stroke_width=1.2)
    return y + h


# ============================================================================ blocks
def block_title(D, x, y, t, sub=None, w=600.0):
    D.stext(x, y, t, size=14, bold=True)
    if not sub:
        return y + 14
    n = 0
    for n, ln in enumerate(sb.wrap(sub, int(w / (0.56 * 9.5)))):
        D.stext(x, y + 13 + n * 11, ln, size=9.5, fill='#444')
    return y + 26 + n * 11


def note_block(D, x, y, num, head, body, size=10.0, width=680.0, lead=12.1, hang=15.0):
    """One general note: a bold run-in head, then the body, with a hanging indent.  Widths are
    measured with tw(), so the body starts hard against the head instead of after a ragged gap."""
    hd = '%d. %s' % (num, head)
    hw = tw(hd, size, True)
    if hw > width - 130:                       # head too long to share a line with the body
        for ln in wrap_w(hd, size, width, True):
            D.stext(x, y, ln, size=size, bold=True)
            y += lead
        first_w, first_x = width - hang, x + hang
    else:
        D.stext(x, y, hd, size=size, bold=True)
        first_w, first_x = width - hw - 8.0, x + hw + 8.0
    lines, cur, avail = [], '', first_w
    for w_ in body.split():
        cand = (cur + ' ' + w_).strip()
        if cur and tw(cand, size) > avail:
            lines.append(cur)
            cur, avail = w_, width - hang
        else:
            cur = cand
    if cur:
        lines.append(cur)
    for i, ln in enumerate(lines):
        D.stext(first_x if i == 0 else x + hang, y, ln, size=size)
        y += lead
    return y


def seal_block(D, x, y, w, h, title, scope):
    D.srect(x, y, w, h, fill='#fff', stroke='#000', stroke_width=1.0)
    D.srect(x, y, w, 17, fill='#e8e8e8', stroke='#000', stroke_width=1.0)
    ts = min(9.5, 9.5 * (w - 14.0) / max(tw(title, 9.5, True), 1.0))
    D.stext(x + 5, y + 12.5, title, size=ts, bold=True)
    sq = min(86.0, h - 74.0)                      # the blank seal area, clear of the signature line
    D.srect(x + 8, y + 22, sq, sq, fill='none', stroke='#999', stroke_width=0.8,
            stroke_dasharray='5 3')
    D.stext(x + 8 + sq / 2, y + 22 + sq / 2, 'SEAL', size=10, fill='#aaa', anchor='middle')
    D.stext(x + 8 + sq / 2, y + 36 + sq / 2, '(BLANK)', size=9, fill='#aaa', anchor='middle')
    yy = y + 32
    for ln in sb.wrap(scope, int((w - sq - 24) / (0.56 * 8.5))):
        D.stext(x + sq + 16, yy, ln, size=8.5, fill='#333')
        yy += 10.2
    D.stext(x + 8, y + h - 42, 'NOT YET ENGAGED — NO SHEET IN THIS SET IS SEALED.', size=8.5,
            bold=True, fill='#b00')
    D.sline(x + 8, y + h - 22, x + w - 88, y + h - 22, stroke='#000', stroke_width=0.6)
    D.stext(x + 8, y + h - 12, 'SIGNATURE', size=8, fill='#666')
    D.sline(x + w - 82, y + h - 22, x + w - 8, y + h - 22, stroke='#000', stroke_width=0.6)
    D.stext(x + w - 82, y + h - 12, 'DATE', size=8, fill='#666')


def legend_block(D, x, y, w):
    D.stext(x, y, 'LEGEND — VICINITY AND LOCATION MAPS', size=13, bold=True)
    yy = y + 18
    nch = int((w - 46) / (0.56 * 10))
    for kind, col, lw, dash, txt in LEGEND:
        if kind == 'site':
            D.srect(x, yy - 9, 36, 12, fill='#fdf3d0', stroke='#000', stroke_width=1.8)
        elif kind == 'line':
            D.sline(x, yy - 3, x + 36, yy - 3, stroke=col, stroke_width=lw, stroke_dasharray=dash)
        elif kind == 'stop':
            D.scircle(x + 18, yy - 3, 6.0, fill=col, stroke='#fff', stroke_width=1.4)
            D.scircle(x + 18, yy - 3, 2.5, fill='#fff')
        elif kind == 'ring':
            D.scircle(x + 18, yy - 3, 6.5, fill='none', stroke=col, stroke_width=0.9,
                      stroke_dasharray='4 3')
        elif kind == 'arrow':
            D.sline(x, yy - 3, x + 28, yy - 3, stroke=col, stroke_width=1.4)
            D.spoly([(x + 36, yy - 3), (x + 27, yy - 7), (x + 27, yy + 1)], fill=col)
        else:
            D.srect(x, yy - 9, 36, 12, fill=col, stroke='#777', stroke_width=0.5)
        lns = sb.wrap(txt, nch)
        for j, ln in enumerate(lns):
            D.stext(x + 44, yy + j * 11, ln, size=10)
        yy += 13.5 + 10.5 * (len(lns) - 1)
    return yy


# ============================================================================ build
def build():
    D, F = _frame()
    L_, R_, T_, B_ = F['l'], F['r'], F['t'], F['b']

    # ---------------------------------------------------------------- banner
    D.srect(L_, T_, R_ - L_, 186, fill='#fff', stroke='#000', stroke_width=1.2)
    D.stext(L_ + 14, T_ + 48, 'THE COTTAGES AT ARCADO SPRINGS', size=40, bold=True)
    D.stext(L_ + 14, T_ + 76, 'SHEET %s — %s' % (SHEET_NO, SHEET_TITLE), size=20, bold=True)
    D.stext(L_ + 14, T_ + 100,
            'APPLICATION TO REZONE %s ACRES FROM R-1 TO R-2 — %d ONE-STORY DETACHED 55+ (HOPA) '
            'COTTAGE HOMES ON FEE-SIMPLE LOTS, %.2f DU/AC' % (DEED_AC, LOTS, DENS_DEED),
            size=16, bold=True, fill='#7b1fa2')
    D.stext(L_ + 14, T_ + 124,
            'Use: "Single-family (cluster-cottage, creative lot configuration)" — permitted in R-2 '
            'by Lilburn Zoning Ordinance 2023-603 §602 Use Table. No special use permit requested.',
            size=13)
    D.stext(L_ + 14, T_ + 145,
            '4535, 4537, 4539 and 4541 Arcado Road SW, Lilburn, Georgia 30047 — Land Lot 123, '
            '6th District, Gwinnett County — PINs R6123 033, R6123 015, R6123 014 and R6123 162',
            size=13, bold=True)
    D.stext(L_ + 14, T_ + 168,
            'City of Lilburn, Gwinnett County, Georgia — Department of Planning and Zoning, '
            '340 Main Street. Filed under Ord. 2023-603 §1003 and the 2026 Application '
            'Instructions (11 items).', size=11, fill='#444')
    D.stext(1390, T_ + 172, 'DRAFT — NOT SEALED', size=18, bold=True, fill='#c00', anchor='end')

    ax, aw = 1404.0, 470.0
    D.srect(ax, T_ + 10, aw, 166, fill='#f7f7f2', stroke='#000', stroke_width=0.9)
    D.stext(ax + 8, T_ + 26, 'APPLICATION DATA', size=11.5, bold=True)
    for k, (a, b) in enumerate([
            ('ZONING CASE NO.', 'RZ-2026-____________  (assigned by the City)'),
            ('DATE FILED', _BLANK),
            ('PLANNING COMMISSION', '____________________  (4th Thursday, 7:30 pm)'),
            ('CITY COUNCIL', '____________________  (2nd Monday, 7:30 pm)'),
            ('APPLICATION FEE', '$1,250 — 5.0 to 9.9 ac; FY2026-2027 Fee Schedule,'),
            ('', 'Res. No. 2026-08, adopted 2026-08-31 (confirm on filing)'),
            ('EXISTING / PROPOSED', 'R-1  →  R-2  (Ord. 2023-603 §402)')]):
        D.stext(ax + 8, T_ + 44 + k * 18, a, size=9.5, fill='#555', bold=True)
        D.stext(ax + 152, T_ + 44 + k * 18, b, size=10.5)

    rx, rw = 1900.0, R_ - 1900.0
    D.stext(rx, T_ + 22, 'REVISIONS', size=11.5, bold=True)
    sb.table(D, rx, T_ + 30, ['NO.', 'DATE', 'DESCRIPTION', 'BY'], REVISIONS, size=10,
             widths=[34, 74, rw - 150, 42])

    # ---------------------------------------------------------------- columns
    y0 = T_ + 202
    CA, CAW = L_, 580.0
    CB, CBW = L_ + 602, 600.0
    CC, CCW = L_ + 1224, 560.0
    CD = L_ + 1806
    CDW = R_ - CD

    # ---- column A: contacts, zoning data
    y = block_title(D, CA, y0, 'OWNER, CONTACTS AND DESIGN PROFESSIONALS',
                    'Site Development Plan Review Checklist §1.e.1 — a blank line means no such '
                    'professional is engaged', w=CAW)
    y = sb.table(D, CA, y + 4, ['ROLE', 'NAME', 'ADDRESS', 'PHONE / E-MAIL'], CONTACTS,
                 size=10, widths=[108, 210, 128, 134])
    y = block_title(D, CA, y + 24, 'ZONING AND PROPOSED USE DATA',
                    'Checklist §1.e.1, §4.b and §4.c ("required versus provided"); Lilburn Zoning '
                    'Ordinance 2023-603 Tables 4.1, 4.2 and 8.1', w=CAW)
    y = sb.table(D, CA, y + 4, ['ITEM', 'REQUIRED / PROVIDED'], zoning_rows(), size=10,
                 widths=[126, 454])
    D.stextblock(CA, y + 13, 'Quantities are read at plot time from data/layout.json '
                             '(regenerated %s) and data/plans.json — the quantities actually drawn '
                             'on Sheet C-2.0. The full required-versus-provided table for Articles '
                             '4, 5 and 8 is on Sheet C-2.0.' % sb.DATE, size=9.5, chars=int(CAW / (0.56 * 9.5)),
                 lead=11.6, fill='#444')
    y = block_title(D, CA, y + 62, 'REZONING SUBMITTAL INDEX — 2026 APPLICATION INSTRUCTIONS')
    ya = sb.table(D, CA, y + 4, ['ITEM', 'PROVIDED'], SUBMITTAL, size=10,
                  widths=[252, 328])

    # ---- column B: sheet index, exhibits, seal blocks
    rows, issued, unclaimed = index_rows()
    y = block_title(D, CB, y0, 'SHEET INDEX',
                    '%d of %d sheets issued as of %s. Built by listing drawings/*.svg at plot '
                    'time — see general note 16.' % (issued, len(SHEETS), sb.DATE), w=CBW)
    y = sb.table(D, CB, y + 4,
                 ['SHEET', 'TITLE', 'SIZE / SCALE', 'STATUS', 'FILE (drawings/…)', 'T/B'],
                 rows, size=10, widths=[40, 178, 108, 84, 132, 58])
    D.stextblock(CB, y + 12, 'T/B is the sheet number printed in that sheet\'s own title block: '
                             '"=" matches this index, "--" means the sheet declares none, and any '
                             'other value is a provisional number to be corrected at the next '
                             'issue (general note 16).', size=9, chars=int(CBW / (0.56 * 9)),
                 lead=11.0, fill='#444')
    y = block_title(D, CB, y + 40, 'ALSO IN drawings/ — EXHIBITS, NOT SHEETS OF THIS SET', w=CBW)
    ex_rows = [[f, EXHIBITS.get(f, 'Unrecognised file — identify it before filing')]
               for f in unclaimed]
    if ex_rows:
        y = sb.table(D, CB, y + 4, ['FILE', 'WHAT IT IS'], ex_rows, size=10, widths=[140, 460])
    else:
        D.stext(CB, y + 12, 'None — every SVG in drawings/ is a numbered sheet of this set.',
                size=10)
        y += 18

    y = block_title(D, CB, y + 14, 'SEAL BLOCKS',
                    'Blank on purpose: no Georgia RLS, PE, architect or landscape architect is yet '
                    'engaged, and no sheet in this set is sealed', w=CBW)
    for k, (t, sc) in enumerate(SEALS):
        seal_block(D, CB + (k % 2) * 310, y + 6 + (k // 2) * 160, 290, 150, t, sc)
    sy = D.stextblock(CB, y + 6 + 160 + 150 + 14,
                      'Final plan sets must be sealed, signed and dated across the seal by the '
                      'licensed registered party responsible for the contents of each sheet '
                      '(Georgia Board Rule 180-12-.02; Checklist §1.e).',
                      size=9.5, chars=int(CBW / (0.56 * 9.5)), lead=11.6, fill='#444')

    # ---- column C: the two maps and the legend
    y = block_title(D, CC, y0, 'VICINITY MAP     SCALE 1" = 400\'',
                    'Arcado Rd, Killian Hill Rd, Arcadia Pl, the three adjoining subdivisions and '
                    'the Ride Gwinnett Route 25 stop', w=CCW)
    ybot = paste(D, vicinity(CC + 10, y + 6))
    yc = D.stextblock(CC, ybot + 14,
                      'Drawn north-up from the Gwinnett County GIS street centrelines, tax-parcel '
                      'fabric, zoning polygons and hydrology carried in '
                      'data/site-context-local.json and from the boundary ring in '
                      'data/layout.json. Adjoining parcels are the 31 abutters plus the Arcado Rd '
                      'right-of-way. Route 25 runs Gwinnett Place Transit Center to Stone '
                      'Mountain: weekday headway about 50 minutes, Saturday hourly, no Sunday '
                      'service. Neither centreline is mapped through the Killian Hill Rd / Arcado '
                      'Rd intersection, so the intersection is shown where the mapped Arcado Rd '
                      'centreline, produced on its last mapped bearing, cuts the mapped Killian '
                      'Hill Rd centreline: it scales 1,483 ft (0.28 mi) against the 0.30-mi '
                      'straight-line distance to stops 2528 and 2578 in the GTFS feed. '
                      'Not a survey.',
                      size=9.0, chars=int(CCW / (0.56 * 9.0)), lead=11.0, fill='#444')

    y = block_title(D, CC, yc + 10, 'LOCATION MAP     SCALE 1" = 1,000\'',
                    'The site in the City of Lilburn zoning pattern, with distance rings on the '
                    'site centroid', w=CCW)
    lbot = paste(D, location(CC + 10, y + 6))
    yc = D.stextblock(CC, lbot + 14,
                      'Zoning polygons and jurisdiction from the Gwinnett County GIS zoning layer; '
                      'the R-1 (Lilburn) and R-100 (unincorporated Gwinnett) fills show the city '
                      'limit. Off-map destinations are straight-line distances from docs/11 §6.3 '
                      'and their compass directions are approximate.',
                      size=9.0, chars=int(CCW / (0.56 * 9.0)), lead=11.0, fill='#444')
    yl = legend_block(D, CC, yc + 10, CCW)

    # ---- column D: general notes
    y = block_title(D, CD, y0, 'GENERAL NOTES',
                    'Notes the City of Lilburn Site Development Plan Review Checklist requires on '
                    'the cover page are reproduced verbatim and identified as such', w=CDW)
    yy = y + 6
    for i, (head, body) in enumerate(NOTES, 1):
        yy = note_block(D, CD, yy, i, head, body, size=10.5, width=CDW - 8.0, lead=12.8)
        yy += 3.0
    for name, bot in (('column A (contacts, zoning data, submittal index)', ya),
                      ('column B (sheet index, exhibits, seal blocks)', sy),
                      ('column C (maps and legend)', yl),
                      ('column D (general notes)', yy)):
        if bot > B_:
            print('  ** WARNING: %s overflows the sheet by %.0f pt' % (name, bot - B_))
    return D


if __name__ == '__main__':
    d = build()
    svg, png = sb.save(d, 'cover', dpi=150)
    rows, issued, unclaimed = index_rows()
    print('wrote %s\n      %s' % (svg, png))
    print('  sheet index: %d of %d issued; exhibits (unclaimed SVGs): %s'
          % (issued, len(SHEETS), ', '.join(unclaimed) or 'none'))
    kh = killian_at_arcado()
    if kh:
        print('  Killian Hill @ Arcado (Arcado centreline produced): E %.0f N %.0f — %.0f ft '
              '(%.2f mi) from the front corner'
              % (kh[0][0], kh[0][1], math.hypot(*kh[0]), math.hypot(*kh[0]) / 5280.0))
    print('  live numbers: %d lots, %.2f du/ac deeded, %s SF open space (%.1f%%), %.2f ac disturbed'
          % (LOTS, DENS_DEED, fmt(OS_SF), OS_PCT, DISTURBED_AC))
