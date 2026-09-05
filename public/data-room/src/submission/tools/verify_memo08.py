#!/usr/bin/env python3
"""House-rule + number checks for docs/08-technical-memoranda.md. Exit 1 on any failure.

Every expected figure is read from verify/memo-calcs.json, which tools/memo_calcs.py derives from
data/layout.json — so this script fails whenever the document drifts from the drawing. Run
tools/memo_calcs.py first if layout.json has changed.
"""
import json, math, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
doc = open(os.path.join(ROOT, 'docs', '08-technical-memoranda.md'), encoding='utf-8').read()
lines = doc.rstrip('\n').split('\n')
fails = []


def check(cond, msg):
    (print("ok  ", msg) if cond else (fails.append(msg), print("FAIL", msg)))


check(lines[-1] == '<!-- architecture-studio:requires-disclaimer -->', 'marker is the last line')
check(lines[-2] == '' and lines[-3].startswith('> **Disclaimer:** This is an AI-generated analysis'), 'disclaimer block then blank line before marker')
check('IFC 2018' not in doc, 'no "IFC 2018" citation')
check(not re.search(r'\bcomplies\b|\bcompliant\b', doc, re.I), 'never says "complies"')
check(all(y == '2024' for y in re.findall(r'IFC (\d{4})', doc)), 'every IFC citation that carries a year carries 2024')
check(len(re.findall(r'appears consistent', doc, re.I)) >= 5, '"appears consistent with" language present')
check(doc.count('VERIFY') >= 15, 'VERIFY markers present')

lay = json.load(open(os.path.join(ROOT, 'data', 'layout.json')))
M = lay['metrics']
N = M['lots']
calc = json.load(open(os.path.join(ROOT, 'verify', 'memo-calcs.json')))
check(calc['units'] == N, f'verify/memo-calcs.json is current with layout.json (N = {N}) — else re-run tools/memo_calcs.py')

# every one of these is derived from the lot count, the basin sizes or the impervious area
expect = {
    'units': f'N = {N}',
    '251 daily mid': '177', '251 daily lo': '152',
    '251 PM lo/mid': '12.3', '251 AM mid': '9.8', '251 PM hi': '16.0', '251 PM @cap hi': '18.3',
    '210 PM': '34.8', '2025 MU PM raw': '214',
    'front reach length ft': '814', 'available slope sag->MH': '0.68 %',
    'rear->MH length ft': '1,313', 'extension total length ft': '478', 'extension slope': '1.45 %',
    'AADF (DWR table)': '10,670 gpd', 'peak (x4.0) DWR': '29.6 gpm',
    'Phase 2 AADF DWR': '4,250 gpd', 'Phase 2 peak': '11.8 gpm',
    'avg day': '10,250 gpd', 'hydrants @~400 ft': '**6 hydrants**',
    'WQv': '18,659', 'RRv (1.0-in basis)': '15,549',
    'disturbed area': '7.541', 'detention required': '75,410', 'detention provided': '77,863',
    'Pond 1 (dry detention / WQ)': '33,129', 'Pond 2 (dry detention / WQ)': '44,734',
    'impervious': '184,148', 'units needing a 55+ resident': '33 of the 41 units',
    'sprinkler offer': '$123,000', 'steepest existing lane grade': '10.9 %',
    'dead-end length': '1,754', 'entrance to Arcadia Pl cl': '251 ft',
}
for k, s in expect.items():
    check(s in doc, f'{k} = {calc.get(k)} appears in doc as "{s}"')

# Figures that must NOT survive from the 43-lot issues. Three kinds of line quote a superseded number on
# purpose and are excluded: the revision notes at the head of the document (everything before Memo A), and
# any sentence that marks the figure as superseded or withdrawn.
body = [ln for ln in doc[doc.index('## Memo A'):].split('\n')
        if not re.search(r'supersed|withdraw|is retired|previously said|previously reported', ln)]
body = '\n'.join(body)
for stale in ['11,170 gpd', '10,750 gpd', '188,483 SF', '132,959', '75,133', '19,049 cf**',
              '**12.9', '13.2 gpm', '$129,000', '35 of 43', '4,750 gpd', '44,680']:
    check(stale not in body, f'stale 43-lot figure removed from the body: {stale!r}')
stale_43 = re.findall(r'\b43[- ](?:lot|unit|home|dwelling)\w*', body)
check(not stale_43, f'no live "43-lot"/"43 units" phrasing in the body (found {stale_43})')

check(re.search(r'5\.9-ft deficit', doc) is not None, 'rear gravity deficit 5.9 ft stated')
check('33 of the 41 units' in doc and '0.80 × 41 = 32.8' in doc, 'HOPA 24 CFR §100.305(g) recomputation shown with its inputs')
check('24 + 17' in doc, 'phase split 24 + 17 stated')
check('4535 Arcado Rd' in doc and '1,202' in doc, 'the 4535 dwelling is placed 1,200 ft back on the lane alignment')
for edition in ['11th ed.', 'Zoning Ordinance 2023-603', 'NFPA 13D', 'O.C.G.A. §12-7-6', 'Ch. 109 Art. VII', 'Ch. 109 Art. V']:
    check(edition in doc, f'citation present: {edition}')

print(f"\n{len(fails)} failure(s); {len(doc.split())} words, {len(lines)} lines")
sys.exit(1 if fails else 0)
