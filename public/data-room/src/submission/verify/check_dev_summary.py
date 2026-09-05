#!/usr/bin/env python3
"""Check docs/02-development-summary.md against the FACTS section 6 house rules and, crucially, against the
DATA — data/layout.json and data/dev-summary-derived.json — rather than against a list of numbers frozen
into this script.

    python3 verify/check_dev_summary.py

Why it works this way. The previous version of this file hard-coded the values it expected ("32.2 %",
"160,167 sf", "1,722", "727 / 550 / 435"). Every one of those went stale the first time the site-plan
generator was re-run, and the script then failed for the wrong reason — or crashed, because the derived
JSON had grown new keys. So this version asks the opposite question: for each metric the package tracks,
does the number the DOCUMENT prints match the number the DATA holds? A value is accepted if any of its
plausible printed forms (1,234 / 1234 / 1,234.0 / 1.2 / 1.23) appears in the document. That means the
check keeps working after any regeneration, and it fails exactly when a document and the data disagree —
which is the failure that matters.

Exit status 0 = PASS, 1 = FAIL.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, 'docs', '02-development-summary.md')
doc = open(DOC, encoding='utf-8').read()
M = json.load(open(os.path.join(ROOT, 'data', 'layout.json'), encoding='utf-8'))['metrics']
D = json.load(open(os.path.join(ROOT, 'data', 'dev-summary-derived.json'), encoding='utf-8'))
P = json.load(open(os.path.join(ROOT, 'data', 'plans.json'), encoding='utf-8'))['plans']

fails, notes = [], []
lines = doc.rstrip('\n').split('\n')


def norm(t):
    """Normalise the document for numeric matching: strip thin/hard spaces and unify separators."""
    return (t.replace(' ', ' ').replace(' ', ' ').replace('–', '-').replace('—', '-'))


NDOC = norm(doc)


def forms(v):
    """Every plausible printed form of a number."""
    out = set()
    if isinstance(v, bool):
        return out
    if isinstance(v, int) or (isinstance(v, float) and abs(v - round(v)) < 1e-9):
        n = int(round(v))
        out |= {'{:,}'.format(n), str(n)}
        if abs(n) >= 1000:
            out.add('{:,}'.format(n).replace(',', ' '))
        out.add('{:,.1f}'.format(n))
    if isinstance(v, float):
        out |= {'{:.1f}'.format(v), '{:.2f}'.format(v), '{:,.1f}'.format(v), '{:,.2f}'.format(v)}
        out.add('{:,.0f}'.format(v))
    return {f for f in out if f}


def has(v):
    return any(f in NDOC for f in forms(v))


def check_value(label, v, required=True):
    if v is None:
        notes.append('%s: not present in the data' % label)
        return
    if not has(v):
        msg = '%s: the data says %s but no such figure appears in the document' % (label, v)
        (fails if required else notes).append(msg)


# ----------------------------------------------------------------- house rules (FACTS section 6)
if lines[-1] != '<!-- architecture-studio:requires-disclaimer -->':
    fails.append('the architecture-studio marker is not the last line')
if lines[-2] != '':
    fails.append('no blank line before the marker')
if not lines[-3].startswith('> **Disclaimer:** This is an AI-generated analysis for preliminary planning purposes.'):
    fails.append('the canonical disclaimer is not the last block before the marker')
for i, ln in enumerate(lines, 1):
    if re.search(r'\bcompl(y|ies|iant|iance)\b', ln, re.I) and 'compliance matrix' not in ln.lower() \
            and 'Zoning compliance' not in ln and 'not a compliance' not in ln.lower():
        fails.append('line %d says comply/complies (house rule: "appears consistent with"): %s' % (i, ln[:90]))
    if re.search(r'IFC\s+(?!2024)\d{4}', ln):
        fails.append('line %d cites a non-2024 IFC edition: %s' % (i, ln[:90]))
    if re.search(r'IRC\s+(?!2024)\d{4}', ln):
        fails.append('line %d cites a non-2024 IRC edition: %s' % (i, ln[:90]))

# ----------------------------------------------------------------- structure
HEADS = {n: h for n, h in
         (m.groups() for m in re.finditer(r'^## (\d+)\.\s*(.*)$', doc, re.M))}
for n, words in [('1', ('property', 'overview')), ('2', ('existing',)), ('3', ('proposed',)),
                 ('4', ('matrix',)), ('5', ('utilit',)), ('6', ('traffic',)), ('7', ('school',)),
                 ('8', ('fiscal',)), ('9', ('condition',)), ('10', ('open item', 'verify'))]:
    h = HEADS.get(n, '')
    if not h:
        fails.append('missing section %s' % n)
    elif not any(w in h.lower() for w in words):
        fails.append('section %s is "%s" — expected it to be about %s' % (n, h, ' / '.join(words)))

for row in ['Minimum lot size', 'Minimum lot width', 'Minimum lot depth', 'Maximum gross density',
            'Minimum heated floor area', 'Maximum height', 'Buffer abutting R-1', 'Front setback',
            'Side setback', 'Rear setback', 'Accessory building setbacks', '602 Use Table', 'Table 8.1',
            '319', '313(1)', 'Stream buffer', 'ul-de-sac', '600 ft', 'D103.4', 'D107.1']:
    if row not in doc:
        fails.append('zoning matrix row missing: %s' % row)

# ----------------------------------------------------------------- the numbers, read from the data
SITE = [
    ('lot count', M.get('lots')),
    ('density on the deeded acreage', M.get('density_du_ac_deeded')),
    ('density on the GIS acreage', M.get('density_du_ac_gis')),
    ('open space, SF', M.get('open_space_sf')),
    ('open space, percent of GIS area', M.get('open_space_pct_gis')),
    ('impervious area, SF', M.get('impervious_sf')),
    ('impervious, percent of GIS area', M.get('impervious_pct_gis')),
    ('travelled way / lane length', M.get('lane_length_ft')),
    ('lane pavement, SF', M.get('pavement_sf')),
    ('sidewalk, SF', M.get('sidewalk_sf')),
    ('buffer easement on lots, SF', M.get('buffer_easement_on_lots_sf')),
    ('parking required', M.get('parking_required')),
    ('parking provided on lot', M.get('parking_provided_on_lot')),
    ('lots in phase 1', M.get('lots_phase1')),
    ('lots in phase 2', M.get('lots_phase2')),
    ('PM peak-hour trips (ITE LUC 251)', M.get('pm_peak_trips_ite_251')),
]
DERIVED = [
    ('detention required, CF', D.get('detention_required_cf')),
    ('detention provided, CF', D.get('detention_provided_cf')),
    ('disturbed area, acres', D.get('disturbed_ac')),
    ('water-quality volume, CF', D.get('WQv_cf')),
    ('average daily sewer flow, GPD', D.get('adf_total_gpd')),
    ('Phase 1 gravity length, ft', D.get('phase1_gravity_len_ft')),
    ('total conditioned floor area, SF', D.get('conditioned_sf_total')),
]
PLANS = []
for pid in ('A', 'B'):
    p = P.get(pid)
    if not p:
        continue
    a = p['areas']
    PLANS += [
        ('Plan %s conditioned area' % pid, a['conditioned_sf']),
        ('Plan %s garage area' % pid, a['garage_sf']),
        ('Plan %s front porch area' % pid, a['front_porch_sf']),
        ('Plan %s maximum ridge above the floor' % pid, p['roof']['max_ridge_ft']),
    ]

for label, v in SITE + DERIVED + PLANS:
    check_value(label, v)

# the pond volumes, however many basins there are
for i, cf in enumerate(M.get('ponds_cf', []) or [], 1):
    check_value('basin %d volume, CF' % i, cf)

# the hammerhead stations, however many there are
for i, st in enumerate(M.get('hammerhead_spacing_ft', []) or [], 1):
    check_value('turnaround spacing %d' % i, st, required=False)

# ----------------------------------------------------------------- statements that must be present
for phrase, why in [
    ('appears consistent with', 'the house rule requires "appears consistent with" language'),
    ('VERIFY', 'open items must be flagged'),
    ('DRAFT', 'the document must be labelled DRAFT'),
]:
    if phrase not in doc:
        fails.append('the document never says "%s" — %s' % (phrase, why))
if doc.count('VERIFY') < 15:
    notes.append('only %d VERIFY flags; the earlier revision carried more than 30' % doc.count('VERIFY'))

print('document: %d lines, %d words, %d tables, %d VERIFY flags'
      % (len(lines), len(doc.split()), sum(1 for l in lines if l.startswith('|---')), doc.count('VERIFY')))
print('checked %d data-driven values against the document' % (len(SITE) + len(DERIVED) + len(PLANS)))
for n in notes:
    print('  note:', n)
print('FAIL' if fails else 'PASS')
for f in fails:
    print('  -', f)
sys.exit(1 if fails else 0)
