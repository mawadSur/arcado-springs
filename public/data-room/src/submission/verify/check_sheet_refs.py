#!/usr/bin/env python3
"""Every sheet a document names must exist — The Cottages at Arcado Springs.

    python3 verify/check_sheet_refs.py

The completeness audit's worst finding was a document and a drawing disagreeing with each other. The
cheapest version of that failure is a document that cites "Sheet C-2.3" when no such sheet is in the set:
staff turn to it, find nothing, and the application looks careless. This script reads every markdown
document in docs/, pulls out every sheet reference of the form "Sheet X-N.N" or "sheets A-2.1 and A-2.2",
and checks each one against the sheet register in tools/transmittal.py and against the files actually in
drawings/.

Three outcomes per reference:
    OK          the sheet is in the register and its file exists
    NOT ISSUED  the sheet is in the register but the drawing has not been generated yet
    UNKNOWN     the document cites a sheet number the register has never heard of  -> always a failure

Exit status 0 when there are no UNKNOWN references and no NOT-ISSUED reference is cited as though it
existed; 1 otherwise.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import transmittal                                                     # noqa: E402

REGISTER = {no: (title, f or '') for no, title, f, size, scale in transmittal.SHEETS}
DRAW = os.path.join(ROOT, 'drawings')
DOCS = os.path.join(ROOT, 'docs')

# "Sheet C-2.3", "Sheets A-2.1 and A-2.2", "on C-8.0", "sheet A-3.0 (with the clubhouse)"
REF = re.compile(r'\b[Ss]heets?\s+((?:[A-Z]-\d+(?:\.\d+)?)(?:\s*(?:,|and|/|through|to)\s*[A-Z]-\d+(?:\.\d+)?)*)')
NUM = re.compile(r'[A-Z]-\d+(?:\.\d+)?')


def norm(n):
    """C-1 and C-1.0 are the same sheet; normalise to the register's form."""
    if n in REGISTER:
        return n
    if '.' not in n and n + '.0' in REGISTER:
        return n + '.0'
    if n.endswith('.0') and n[:-2] in REGISTER:
        return n[:-2]
    return n


def main():
    unknown, notissued, ok = [], [], 0
    for fn in sorted(os.listdir(DOCS)):
        if not fn.endswith('.md'):
            continue
        text = open(os.path.join(DOCS, fn), encoding='utf-8').read()
        for lineno, line in enumerate(text.split('\n'), 1):
            for m in REF.finditer(line):
                for raw in NUM.findall(m.group(1)):
                    n = norm(raw)
                    if n not in REGISTER:
                        unknown.append((fn, lineno, raw, line.strip()[:110]))
                        continue
                    title, f = REGISTER[n]
                    if f and os.path.exists(os.path.join(DRAW, f)):
                        ok += 1
                    else:
                        # a reference is acceptable if the sentence says the sheet is not yet drawn
                        excused = re.search(r'NOT YET (DRAWN|ISSUED)|not yet drawn|not yet issued|'
                                            r'must be built|to be (drawn|built|issued)|recommended', line)
                        notissued.append((fn, lineno, n, bool(excused), line.strip()[:110]))
    print('sheet references resolved: %d' % ok)
    hard = list(unknown) + [x for x in notissued if not x[3]]
    if notissued:
        print('\nreferences to sheets that are in the register but NOT YET GENERATED (%d):' % len(notissued))
        for fn, ln, n, excused, line in notissued:
            print('  %-12s %s:%d  %s' % (n, fn, ln, 'flagged in the text — OK' if excused
                                         else 'CITED AS IF IT EXISTS — fix the document or build the sheet'))
            if not excused:
                print('        %s' % line)
    if unknown:
        print('\nreferences to sheet numbers the register does not contain (%d):' % len(unknown))
        for fn, ln, raw, line in unknown:
            print('  %-12s %s:%d' % (raw, fn, ln))
            print('        %s' % line)
    print('\n' + ('FAIL' if hard else 'PASS'))
    return 1 if hard else 0


if __name__ == '__main__':
    sys.exit(main())
