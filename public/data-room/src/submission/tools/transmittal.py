#!/usr/bin/env python3
"""Filing transmittal and index — The Cottages at Arcado Springs (R-1 -> R-2 rezoning, Lilburn GA).

    python3 tools/transmittal.py        # writes docs/00-transmittal-and-index.md

The transmittal is generated rather than typed so its index can never claim a sheet or a document the
package does not actually contain: the tables below are built by scanning drawings/ and docs/ at run time
and matching them against the intended set. Anything intended but not yet issued is printed as
NOT YET ISSUED rather than silently omitted.

> **Disclaimer:** This is an AI-generated analysis for preliminary planning purposes. All findings must be verified by a licensed professional before use in design, permitting, or regulatory submissions.

<!-- architecture-studio:requires-disclaimer -->
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, 'docs')
DRAW = os.path.join(ROOT, 'drawings')
REND = os.path.join(ROOT, 'renderings')
DATE = '2026-09-03'

# The sheet register has ONE home: tools/cover.py, which draws the sheet index on Sheet C-0.0.
# Importing it here means the transmittal, the cover sheet and verify/check_sheet_refs.py can never
# disagree about what sheet a number refers to. A None source file means the sheet is intended but
# not yet issued (an LDP-stage sheet, or one still to be drawn).
import cover as _cover                                       # noqa: E402
SHEETS = [(no, title, f, size, scale) for no, title, f, size, scale in _cover.SHEETS]

# instruction item, what it is, the file that answers it
ITEMS = [
    ('1', 'Application Form', 'docs/01-application-form-data.md',
     'Every field of the City form with its entry and its basis. The form itself is transcribed and signed '
     'by the applicant.'),
    ('2', 'Application Fee', 'docs/01-application-form-data.md',
     'Rezoning fee for a 5.0-9.9 acre property, per the fee schedule in force on the filing date. '
     'Check payable to City of Lilburn. CONFIRM THE CURRENT AMOUNT WITH THE PLANNING DEPARTMENT ON THE '
     'FILING DATE — the FY2026-2027 schedule (Resolution No. 2026-08, adopted 2026-08-31) supersedes the '
     'FY25-26 schedule still posted online.'),
    ('3', 'Standards Governing the Exercise of the Zoning Power', 'docs/04-standards-governing-zoning-power.md',
     'The six criteria of Ordinance 2023-603 section 1003-7, answered in full; "see attached" on the form.'),
    ('4', 'Conflict of Interest Form', 'docs/07-conflict-of-interest-and-certifications.md',
     'Campaign-contribution and gift disclosure under O.C.G.A. section 36-67A-3, filed WITH the application '
     'so the ten-day clock is never at issue. Only the signer can declare the contribution history.'),
    ('5', 'Notarized Signatures', 'docs/07-conflict-of-interest-and-certifications.md',
     'Applicant certification plus an owner certification for each owner of record, before a Georgia notary. '
     'Two ownership groups: PINs 033 and 015 (Awad) and PINs 014 and 162 (Mendez / Roblero de Leon).'),
    ('6', 'Letter of Intent', 'docs/03-letter-of-intent.md',
     'Describes the request and its justification, states whether any buffer reduction is requested, and '
     'offers the voluntary zoning conditions. The conditions are listed separately at '
     '`data/voluntary-conditions.md` and reproduced in the letter.'),
    ('7', 'Legal Description', 'docs/05-legal-description-DRAFT.md',
     'Typed metes and bounds of the property to be rezoned. **DRAFT — derived from the Gwinnett County GIS '
     'parcel fabric. The sealed description from a Georgia registered land surveyor replaces it and governs.**'),
    ('8', 'Site Plan', 'drawings/',
     'One full-size copy drawn to scale, plus the PDF e-mailed to returner@cityoflilburn.com. The C-series '
     'sheets listed below answer this item; sheet C-2.0 is the site plan proper and the others support it.'),
    ('9', 'Boundary Survey', '—',
     '**NOT INCLUDED — must be commissioned.** A survey sealed by a Georgia registered land surveyor. '
     'Section 1003-4.4 permits the Director to accept a Tax Assessor map where no survey is available but '
     'does not oblige him to; the 236-246 ft site width that the entire 50 x 100-ft lot section depends on '
     'is unverified without it. This is the critical-path item.'),
    ('10', 'List of Adjoining Property Owners', 'docs/06-adjoining-property-owners.md',
     'All adjoining owners with mailing addresses, from the Gwinnett County Tax Assessor ownership file. '
     'Re-pull on the filing date.'),
    ('11', 'Architectural Renderings and Elevations', 'docs/09-architectural-character-elevations-and-renderings.md',
     'All four elevations of each dwelling type, the clubhouse, the mail kiosk and the monument entry sign, '
     'to scale, with the colour and material schedule; plus illustrative perspectives. No wall signs are '
     'proposed on any structure.'),
]

SUPPORTING = [
    ('Development Summary', 'docs/02-development-summary.md',
     'Site data in the order staff read it, with the Table 4.1 required-versus-provided matrix.'),
    ('Technical Memoranda', 'docs/08-technical-memoranda.md',
     'Traffic, sanitary sewer, water, stormwater, fire, schools and environmental screening.'),
    ('HOA, HOPA and Covenant Outline', 'docs/13-hoa-hopa-and-covenant-outline.md',
     'How the 55+ restriction and the buffer easement are actually enforced, with a line-item association budget.'),
    ('Outline Specifications', 'docs/12-outline-specifications.md',
     'CSI-format outline specifications establishing the materials and colours shown on the elevations.'),
    ('Site Context Brief', 'docs/11-site-context-brief.md',
     'Environmental, mobility, demographic, market and precedent context for the site.'),
    ('Submittal Checklist and Roadmap', 'docs/10-submittal-checklist-and-roadmap.md',
     'Item-by-item status, the filing calendar, the legal-notice audit and the pre-application agenda.'),
]

BODY = """---
title: "Transmittal and Index — Application for Rezoning, The Cottages at Arcado Springs"
date: {date}
to: "Reid Turner, Planning Director, City of Lilburn, 340 Main Street, Lilburn, Georgia 30047"
status: "DRAFT — owner-prepared. Items marked NOT INCLUDED or DRAFT require a licensed professional before filing."
generator: "tools/transmittal.py (index built by scanning drawings/ and docs/)"
---

# Transmittal and Index

**To:** Reid Turner, Planning Director — Department of Planning and Zoning, City of Lilburn, 340 Main
Street, Lilburn, Georgia 30047 · returner@cityoflilburn.com · (770) 279-3715

**From:** Mohammed Awad, applicant and owner of record of PINs R6123 033 and R6123 015 —
4541 Arcado Road SW, Lilburn, Georgia 30047

**Date:** ____________________  **Zoning case no.:** RZ-2026-______ *(assigned by the City)*

**Re: Application to rezone 9.44 acres from R-1 to R-2 — The Cottages at Arcado Springs**
4535, 4537, 4539 and 4541 Arcado Road SW · Land Lot 123, 6th District, Gwinnett County ·
PINs R6123 033, R6123 015, R6123 014 and R6123 162

---

## 1. The request

The applicant asks the City to rezone the 9.44-acre assemblage from **R-1, Single-Family Residential** to
**R-2, Medium-Density Residential** (Lilburn Zoning Ordinance No. 2023-603, section 402) for **{lots} one-story
detached cottage homes on fee-simple lots**, served by one private lane from Arcado Road, restricted to
housing for older persons under 42 U.S.C. section 3607(b)(2)(C) by voluntary condition. The proposed use,
"Single-family (cluster-cottage, creative lot configuration)", is permitted in R-2 by the section 602 Use
Table; no special use permit is requested. The proposed density is **{dens} dwelling units per acre**
against the {maxdens} units per acre that Table 4.1 allows in R-2.

## 2. What is enclosed — the eleven required items

| Item | Requirement (2026 Application Instructions) | Provided | Notes |
|---|---|---|---|
{items}

## 3. Drawing set

| Sheet | Title | Size | Scale | Status |
|---|---|---|---|---|
{sheets}

## 4. Supporting material (not required by the Instructions; provided so staff and the Commission have the
basis for every number)

| Document | File | What it is |
|---|---|---|
{supporting}

## 5. Illustrative perspectives

{rend}

Each is an illustrative perspective prepared by the owner-applicant from the scaled elevations and the
master concept plan. Where an image and a drawing differ, the drawing governs. Item (11) permits imagery:
"The drawings shall be to scale or in proper perspective … Visual imagery may be used."

## 6. Copies and delivery

| What | How delivered |
|---|---|
| One full-size copy of the site plan drawn to scale | Delivered to the counter at 340 Main Street, printed at ARCH D 36 x 24 in at 1" = 60' |
| PDF of the site plan | E-mailed to returner@cityoflilburn.com on the filing date |
| Complete application in Instruction-item order | One bound copy at the counter, and `submission/RZ-2026_cottages-at-arcado-springs.pdf` by e-mail |
| Application fee | Check payable to "City of Lilburn", amount confirmed with the Department on the filing date |
| Conflict-of-interest disclosure | Filed herewith, so the ten-day period of O.C.G.A. section 36-67A-3(b) is not relied upon |

## 7. Requests to the Department

1. **Completeness review.** The applicant asks the Director to confirm in writing that the application is
   complete under section 1003-3, or to identify what is missing, before the legal advertisement is placed.
2. **Confirmation on RZ-2025-01.** The applicant asks the Department to confirm in writing that
   RZ-2025-01 was **tabled** on 2025-08-28 because of a defect in the legal advertisement, was never heard
   and was **not denied**, so that the twelve-month bar of section 1003-11 does not apply; and to advise
   whether that application should be formally withdrawn before this one is accepted.
3. **Draft advertisement text.** Because RZ-2025-01 was lost to a notice defect, the applicant asks to
   review the draft legal advertisement and the sign copy before they are placed, and to be told the dates
   on which the advertisement runs, the letters are mailed and the sign is posted.
4. **Pre-application conference.** The applicant requests a conference at least one week before filing, on
   the agenda at `docs/10-submittal-checklist-and-roadmap.md` section 3.

## 8. Statements the applicant makes plainly

- **Nothing in this package is sealed.** The boundary survey and legal description require a Georgia
  registered land surveyor; the site, grading, utility and stormwater work require a Georgia professional
  engineer; the architectural drawings require a Georgia registered architect; the landscape plan requires
  a registered landscape architect. Every drawing and document is labelled DRAFT accordingly.
- **The boundary is from the Gwinnett County GIS parcel fabric, not a survey**, and the survey governs.
- Statements of consistency are written as "appears consistent with", never as a compliance certification.

---

> **Disclaimer:** This is an AI-generated analysis for preliminary planning purposes. All findings must be verified by a licensed professional before use in design, permitting, or regulatory submissions.

<!-- architecture-studio:requires-disclaimer -->
"""


def main():
    lay = {}
    p = os.path.join(ROOT, 'data', 'layout.json')
    if os.path.exists(p):
        lay = json.load(open(p)).get('metrics', {})
    rows_i = []
    for num, name, path, note in ITEMS:
        if path in ('—', 'drawings/'):
            provided = '(see the drawing set below)' if path == 'drawings/' else '**NOT INCLUDED**'
        else:
            ok = os.path.exists(os.path.join(ROOT, path))
            provided = ('`%s`' % path) if ok else '**NOT YET ISSUED** (`%s`)' % path
        rows_i.append('| %s | %s | %s | %s |' % (num, name, provided, note))
    rows_s = []
    for no, title, f, size, scale in SHEETS:
        ok = bool(f) and os.path.exists(os.path.join(DRAW, f))
        rows_s.append('| **%s** | %s | %s | %s | %s |'
                      % (no, title, size, scale, 'Issued' if ok else '**NOT YET ISSUED**'))
    rows_sup = []
    for title, f, what in SUPPORTING:
        ok = os.path.exists(os.path.join(ROOT, f))
        rows_sup.append('| %s | %s | %s |' % (title, ('`%s`' % f) if ok else '**NOT YET ISSUED**', what))
    rend = sorted(f for f in os.listdir(REND) if f.startswith('R-') and f.endswith(('.jpg', '.png'))) \
        if os.path.isdir(REND) else []
    if rend:
        rend_txt = '\n'.join('- `%s`' % r for r in rend)
    else:
        rend_txt = '*No perspectives issued yet.*'
    out = BODY.format(
        date=DATE,
        lots=lay.get('lots', 43),
        dens=lay.get('density_du_ac_deeded', '4.56'),
        maxdens='8',
        items='\n'.join(rows_i), sheets='\n'.join(rows_s), supporting='\n'.join(rows_sup), rend=rend_txt)
    dst = os.path.join(DOCS, '00-transmittal-and-index.md')
    open(dst, 'w', encoding='utf-8').write(out)
    issued = sum(1 for no, t, f, s, sc in SHEETS if f and os.path.exists(os.path.join(DRAW, f)))
    print('wrote %s  (%d of %d sheets issued, %d perspectives)' % (dst, issued, len(SHEETS), len(rend)))


if __name__ == '__main__':
    main()
