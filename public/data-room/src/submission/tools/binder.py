#!/usr/bin/env python3
"""Assemble the filing binder — The Cottages at Arcado Springs (R-1 -> R-2 rezoning, Lilburn GA).

City of Lilburn 2026 Application Instructions, item (8): "Include one (1) full size copy drawn to scale
and email a pdf electronic file to returner@cityoflilburn.com."

    python3 tools/binder.py            # everything
    python3 tools/binder.py docs       # just the document PDFs
    python3 tools/binder.py sheets     # just the drawing PDFs

Outputs, under submission/:
    submission/sheets/<sheet>.pdf              every drawing at its true sheet size (ARCH D 36x24 / ARCH C 24x18)
    submission/docs/<doc>.pdf                  every markdown document typeset on US Letter
    submission/RZ-2026_cottages-at-arcado-springs.pdf   the whole submittal, bookmarked, in Instruction-item order
    submission/C-2-0_master-concept-plan_36x24.pdf      the full-size site plan for the e-mail

Drawing PDFs come from the SVG sheets through cairosvg, which honours the SVG's declared width/height in
inches, so a 36 x 24 in sheet lands on a 36 x 24 in page at true scale — 1" = 60' really measures.
Documents are typeset with reportlab from the markdown the package already carries; the renderer below
handles the subset of markdown these documents use (ATX headings, paragraphs, bullet and numbered lists,
pipe tables, block quotes, fenced code, horizontal rules, and inline bold / italic / code / links).

> **Disclaimer:** This is an AI-generated analysis for preliminary planning purposes. All findings must be verified by a licensed professional before use in design, permitting, or regulatory submissions.

<!-- architecture-studio:requires-disclaimer -->
"""
import io, os, re, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, 'docs')
DRAW = os.path.join(ROOT, 'drawings')
OUT = os.path.join(ROOT, 'submission')
OUT_S = os.path.join(OUT, 'sheets')
OUT_D = os.path.join(OUT, 'docs')
for d in (OUT, OUT_S, OUT_D):
    os.makedirs(d, exist_ok=True)

TITLE = 'The Cottages at Arcado Springs — Application for Rezoning R-1 to R-2'
SUBTITLE = ('4535, 4537, 4539 and 4541 Arcado Road SW, Lilburn, Georgia 30047 — Land Lot 123, 6th District, '
            'Gwinnett County — PINs R6123 033, 015, 014 and 162 — 9.44 acres')
DATE = '2026-09-03'

# ------------------------------------------------------------------ the binder order (Instruction items 1-11)
# (key, tab label, path relative to ROOT, kind)
ORDER = [
    ('00', 'Transmittal and Index',                                   'docs/00-transmittal-and-index.md', 'doc'),
    ('01', 'Item 1 — Application Form data',                          'docs/01-application-form-data.md', 'doc'),
    ('04', 'Item 3 — Standards Governing the Zoning Power',           'docs/04-standards-governing-zoning-power.md', 'doc'),
    ('07', 'Items 4 and 5 — Conflict of Interest and Certifications', 'docs/07-conflict-of-interest-and-certifications.md', 'doc'),
    ('03', 'Item 6 — Letter of Intent',                               'docs/03-letter-of-intent.md', 'doc'),
    ('cond', 'Item 6 — Voluntary Zoning Conditions',                  'data/voluntary-conditions.md', 'doc'),
    ('05', 'Item 7 — Legal Description (DRAFT)',                      'docs/05-legal-description-DRAFT.md', 'doc'),
    ('C-0.0', 'Item 8 — Sheet C-0.0 Cover, Sheet Index and Vicinity Map', 'drawings/cover.svg', 'sheet'),
    ('C-1.0', 'Item 8 — Sheet C-1.0 Existing Conditions',             'drawings/existing-conditions.svg', 'sheet'),
    ('C-2.0', 'Item 8 — Sheet C-2.0 Master Concept Plan',             'drawings/mcp-sheet.svg', 'sheet'),
    ('C-2.3', 'Item 8 — Sheet C-2.3 Entry, Frontage and Amenity Enlargement', 'drawings/entry-enlargement.svg', 'sheet'),
    ('C-2.4', 'Item 8 — Sheet C-2.4 Fallback Lot-Depth Layout Exhibit', 'drawings/fallback-layout.svg', 'sheet'),
    ('C-3.0', 'Item 8 — Sheet C-3.0 Grading, Drainage and Stormwater Concept', 'drawings/grading-drainage.svg', 'sheet'),
    ('C-4.0', 'Item 8 — Sheet C-4.0 Utility and Phasing Concept',     'drawings/utility-phasing.svg', 'sheet'),
    ('C-7.0', 'Item 8 — Sheet C-7.0 Landscape, Buffer and Tree Protection Concept', 'drawings/landscape-buffer.svg', 'sheet'),
    ('C-8.0', 'Item 8 — Sheet C-8.0 Civil Details',                   'drawings/civil-details.svg', 'sheet'),
    ('02', 'Item 8 — Development Summary',                            'docs/02-development-summary.md', 'doc'),
    ('08', 'Item 8 — Technical Memoranda',                            'docs/08-technical-memoranda.md', 'doc'),
    ('06', 'Item 10 — Adjoining Property Owners',                     'docs/06-adjoining-property-owners.md', 'doc'),
    ('09', 'Item 11 — Architectural Character, Elevations and Renderings', 'docs/09-architectural-character-elevations-and-renderings.md', 'doc'),
    ('A-1.1', 'Item 11 — Sheet A-1.1 Plan A Floor Plan',              'drawings/plan-a-sheet.svg', 'sheet'),
    ('A-1.2', 'Item 11 — Sheet A-1.2 Plan B Floor Plan',              'drawings/plan-b-sheet.svg', 'sheet'),
    ('A-2.1', 'Item 11 — Sheet A-2.1 Plan A Exterior Elevations',     'drawings/plan-a-elev.svg', 'sheet'),
    ('A-2.2', 'Item 11 — Sheet A-2.2 Plan B Exterior Elevations',     'drawings/plan-b-elev.svg', 'sheet'),
    ('A-2.3', 'Item 11 — Sheet A-2.3 Exterior Colour Schemes and Materials', 'drawings/plan-colors.svg', 'sheet'),
    ('A-3.0', 'Item 11 — Sheet A-3.0 Clubhouse, Mail Kiosk and Entry Sign', 'drawings/amenity-sheet.svg', 'sheet'),
    ('R', 'Item 11 — Illustrative Renderings',                        'renderings', 'renderings'),
    ('12', 'Supporting — Outline Specifications',                     'docs/12-outline-specifications.md', 'doc'),
    ('13', 'Supporting — HOA, HOPA and Covenant Outline',             'docs/13-hoa-hopa-and-covenant-outline.md', 'doc'),
    ('11', 'Supporting — Site Context Brief',                         'docs/11-site-context-brief.md', 'doc'),
    ('10', 'Supporting — Submittal Checklist and Roadmap',            'docs/10-submittal-checklist-and-roadmap.md', 'doc'),
]

# ------------------------------------------------------------------ markdown -> reportlab
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                KeepTogether, PageBreak, Image as RLImage)

SS = getSampleStyleSheet()
BODY = ParagraphStyle('body', parent=SS['BodyText'], fontName='Helvetica', fontSize=8.6, leading=11.4,
                      spaceBefore=0, spaceAfter=5, alignment=TA_LEFT)
H = [ParagraphStyle('h%d' % i, parent=BODY, fontName='Helvetica-Bold',
                    fontSize=(15, 12.5, 10.6, 9.4, 8.8, 8.6)[i - 1],
                    leading=(18.5, 15.5, 13.2, 11.8, 11.2, 11),
                    spaceBefore=(13, 11, 9, 7, 6, 5)[i - 1], spaceAfter=(6, 5, 4, 3, 3, 3)[i - 1])
     for i in range(1, 7)]
for i, s in enumerate(H):
    s.leading = (18.5, 15.5, 13.2, 11.8, 11.2, 11)[i]
MONO = ParagraphStyle('mono', parent=BODY, fontName='Courier', fontSize=7.4, leading=9.2,
                      backColor=colors.HexColor('#F4F4F1'), borderPadding=3, spaceBefore=4, spaceAfter=6)
QUOTE = ParagraphStyle('quote', parent=BODY, leftIndent=12, textColor=colors.HexColor('#333333'),
                       borderPadding=0, spaceBefore=4, spaceAfter=6, fontName='Helvetica-Oblique')
CELL = ParagraphStyle('cell', parent=BODY, fontSize=7.2, leading=8.8, spaceAfter=0, spaceBefore=0)
CELLH = ParagraphStyle('cellh', parent=CELL, fontName='Helvetica-Bold')
LI = ParagraphStyle('li', parent=BODY, leftIndent=13, bulletIndent=3, spaceAfter=2.5)
TITLE_S = ParagraphStyle('t', parent=BODY, fontName='Helvetica-Bold', fontSize=19, leading=23, spaceAfter=8)
SUB_S = ParagraphStyle('s', parent=BODY, fontSize=9.6, leading=13, textColor=colors.HexColor('#444444'),
                       spaceAfter=16)

INLINE = [
    (re.compile(r'`([^`]+)`'), r'<font face="Courier" size="7.6">\1</font>'),
    (re.compile(r'\*\*\*(.+?)\*\*\*'), r'<b><i>\1</i></b>'),
    (re.compile(r'\*\*(.+?)\*\*'), r'<b>\1</b>'),
    (re.compile(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])'), r'<i>\1</i>'),
    (re.compile(r'\[([^\]]+)\]\((https?://[^)\s]+)\)'), r'<link href="\2" color="#1A5276">\1</link>'),
    (re.compile(r'(?<![\w/">])(https?://[^\s<>()\]]+)'), r'<link href="\1" color="#1A5276">\1</link>'),
]


def inline(t):
    t = html.escape(t, quote=False)
    for rx, rep in INLINE:
        t = rx.sub(rep, t)
    return t


def para(t, st=BODY):
    return Paragraph(inline(t), st)


def md_to_flowables(md, width):
    """Render the markdown subset these documents use."""
    out = []
    lines = md.split('\n')
    i, n = 0, len(lines)
    # strip a YAML front-matter block into a small header table
    if lines and lines[0].strip() == '---':
        j = 1
        while j < n and lines[j].strip() != '---':
            j += 1
        fm = [l for l in lines[1:j] if l.strip()]
        if fm:
            rows = []
            for l in fm:
                if ':' in l:
                    k, v = l.split(':', 1)
                    rows.append([Paragraph(inline(k.strip()), CELLH), Paragraph(inline(v.strip().strip('"')), CELL)])
            if rows:
                t = Table(rows, colWidths=[width * 0.17, width * 0.83])
                t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                       ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                                       ('TOPPADDING', (0, 0), (-1, -1), 2),
                                       ('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.HexColor('#DDDDDD'))]))
                out += [t, Spacer(1, 8)]
        i = j + 1
    buf = []

    def flush():
        if buf:
            out.append(para(' '.join(buf)))
            del buf[:]

    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s:
            flush(); i += 1; continue
        if s.startswith('```'):
            flush(); i += 1; code = []
            while i < n and not lines[i].strip().startswith('```'):
                code.append(lines[i]); i += 1
            i += 1
            txt = html.escape('\n'.join(code)).replace(' ', '&nbsp;').replace('\n', '<br/>')
            out.append(Paragraph(txt, MONO)); continue
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', s):
            flush()
            out.append(Spacer(1, 3))
            t = Table([['']], colWidths=[width], rowHeights=[0.6])
            t.setStyle(TableStyle([('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#CCCCCC'))]))
            out += [t, Spacer(1, 5)]; i += 1; continue
        m = re.match(r'^(#{1,6})\s+(.*)$', s)
        if m:
            flush()
            out.append(Paragraph(inline(m.group(2)), H[len(m.group(1)) - 1])); i += 1; continue
        if s.startswith('|') and i + 1 < n and re.match(r'^\|[\s:|-]+\|?$', lines[i + 1].strip()):
            flush()
            rows, i = _table(lines, i)
            out.append(_mk_table(rows, width)); out.append(Spacer(1, 5)); continue
        if s.startswith('>'):
            flush(); q = []
            while i < n and lines[i].strip().startswith('>'):
                q.append(lines[i].strip().lstrip('>').strip()); i += 1
            out.append(para(' '.join(q), QUOTE)); continue
        m = re.match(r'^([-*+])\s+(.*)$', s)
        if m:
            flush()
            out.append(Paragraph(inline(m.group(2)), LI, bulletText='•')); i += 1; continue
        m = re.match(r'^(\d+)[.)]\s+(.*)$', s)
        if m:
            flush()
            out.append(Paragraph(inline(m.group(2)), LI, bulletText=m.group(1) + '.')); i += 1; continue
        if s.startswith('<!--'):
            i += 1; continue
        buf.append(s); i += 1
    flush()
    return out


def _table(lines, i):
    def cells(l):
        l = l.strip()
        if l.startswith('|'):
            l = l[1:]
        if l.endswith('|'):
            l = l[:-1]
        return [c.strip() for c in re.split(r'(?<!\\)\|', l)]
    rows = [cells(lines[i])]
    i += 2
    while i < len(lines) and lines[i].strip().startswith('|'):
        rows.append(cells(lines[i])); i += 1
    w = max(len(r) for r in rows)
    rows = [r + [''] * (w - len(r)) for r in rows]
    return rows, i


def _mk_table(rows, width):
    ncol = len(rows[0])
    weights = []
    for c in range(ncol):
        weights.append(max(6, max(len(r[c]) for r in rows) ** 0.72))
    tot = sum(weights)
    cw = [max(0.5 * inch, width * w / tot) for w in weights]
    if sum(cw) > width:
        k = width / sum(cw)
        cw = [c * k for c in cw]
    data = [[Paragraph(inline(c), CELLH if ri == 0 else CELL) for c in r] for ri, r in enumerate(rows)]
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EFEDE7')),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#CFCFCF')),
        ('LEFTPADDING', (0, 0), (-1, -1), 3.5), ('RIGHTPADDING', (0, 0), (-1, -1), 3.5),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    return t


class DocTpl(BaseDocTemplate):
    def __init__(self, path, header, **kw):
        BaseDocTemplate.__init__(self, path, pagesize=letter, leftMargin=0.72 * inch, rightMargin=0.72 * inch,
                                 topMargin=0.78 * inch, bottomMargin=0.72 * inch, title=header, **kw)
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='f')
        self.header = header
        self.addPageTemplates([PageTemplate(id='p', frames=[fr], onPage=self._deco)])

    def _deco(self, c, d):
        c.saveState()
        c.setFont('Helvetica', 6.8)
        c.setFillColor(colors.HexColor('#777777'))
        c.drawString(self.leftMargin, letter[1] - 0.52 * inch,
                     'THE COTTAGES AT ARCADO SPRINGS — ' + self.header.upper())
        c.drawRightString(letter[0] - self.rightMargin, letter[1] - 0.52 * inch,
                          'DRAFT — NOT SEALED — ' + DATE)
        c.setStrokeColor(colors.HexColor('#DDDDDD')); c.setLineWidth(0.4)
        c.line(self.leftMargin, letter[1] - 0.60 * inch, letter[0] - self.rightMargin, letter[1] - 0.60 * inch)
        c.line(self.leftMargin, 0.60 * inch, letter[0] - self.rightMargin, 0.60 * inch)
        c.drawString(self.leftMargin, 0.44 * inch,
                     'Rezoning application R-1 to R-2 — City of Lilburn, Georgia — owner-prepared draft')
        c.drawRightString(letter[0] - self.rightMargin, 0.44 * inch, 'Page %d' % d.page)
        c.restoreState()


def doc_pdf(md_path, pdf_path, header):
    md = open(md_path, encoding='utf-8').read()
    d = DocTpl(pdf_path, header)
    d.build(md_to_flowables(md, d.width))
    return pdf_path


def sheet_pdf(svg_path, pdf_path):
    import cairosvg
    cairosvg.svg2pdf(url=svg_path, write_to=pdf_path)
    return pdf_path


def cover_pdf(pdf_path, index_rows):
    d = DocTpl(pdf_path, 'Cover and contents')
    f = [Spacer(1, 42), Paragraph(TITLE, TITLE_S), Paragraph(SUBTITLE, SUB_S),
         para('**Applicant and owner of record (PINs R6123 033 and 015):** Mohammed Awad, 4541 Arcado Road SW, '
              'Lilburn, Georgia 30047.'),
         para('**Filed under:** City of Lilburn Zoning Ordinance No. 2023-603, Article 10, section 1003, and the '
              'City of Lilburn 2026 Application Instructions — Rezoning / Special Use Permit / Change in Condition, '
              'items (1) through (11).'),
         para('**Request:** rezone 9.44 acres from R-1 (Single-Family Residential) to R-2 (Medium-Density '
              'Residential) for 43 one-story detached cottage homes on fee-simple lots, restricted to housing for '
              'older persons under 42 U.S.C. section 3607(b)(2)(C) by voluntary condition.'),
         Spacer(1, 14),
         Paragraph('Contents', H[1])]
    rows = [['Tab', 'Document or sheet', 'Instruction item']]
    for key, label, _p, _k in index_rows:
        item = ''
        m = re.search(r'Item (\d+)', label)
        if m:
            item = m.group(1)
        elif label.startswith('Supporting'):
            item = 'supporting'
        elif label.startswith('Transmittal'):
            item = '—'
        rows.append([key, re.sub(r'^Item \d+ — |^Supporting — ', '', label), item])
    f.append(_mk_table(rows, d.width))
    f.append(Spacer(1, 14))
    f.append(para('> **Disclaimer:** This is an AI-generated analysis for preliminary planning purposes. All '
                  'findings must be verified by a licensed professional before use in design, permitting, or '
                  'regulatory submissions.', QUOTE))
    d.build(f)
    return pdf_path


def renderings_pdf(pdf_path, folder):
    """One landscape-ish contact set of the illustrative perspectives, each captioned."""
    imgs = sorted(f for f in os.listdir(folder)
                  if f.lower().endswith(('.jpg', '.png')) and f.startswith('R-'))
    if not imgs:
        return None
    d = DocTpl(pdf_path, 'Illustrative renderings')
    f = [Paragraph('Illustrative Renderings — Application Instructions item (11)', H[0]),
         para('These are illustrative perspectives prepared by the owner-applicant. They are generated from the '
              'scaled elevations in sheets A-2.1, A-2.2, A-2.3 and A-3.0 and from the master concept plan, and the '
              'scaled drawings govern wherever an image and a drawing differ. Item (11) permits imagery: '
              '"The drawings shall be to scale or in proper perspective… Visual imagery may be used."'),
         Spacer(1, 6)]
    from PIL import Image as PILImage
    small_dir = os.path.join(OUT_D, '_rend')
    os.makedirs(small_dir, exist_ok=True)
    for name in imgs:
        src = os.path.join(folder, name)
        p = os.path.join(small_dir, os.path.splitext(name)[0] + '.jpg')
        with PILImage.open(src) as im:          # embed a print-resolution copy, not the 2K original
            im = im.convert('RGB')
            im.thumbnail((1700, 1700))
            im.save(p, quality=82, optimize=True)
        with PILImage.open(p) as im:
            w, h = im.size
        iw = d.width
        ih = iw * h / float(w)
        if ih > 6.2 * inch:
            ih = 6.2 * inch; iw = ih * w / float(h)
        cap = os.path.splitext(name)[0].replace('_', ' — ').replace('-', ' ')
        f.append(KeepTogether([RLImage(p, iw, ih), Spacer(1, 3),
                               Paragraph(inline('**%s**' % cap), CELL), Spacer(1, 12)]))
    d.build(f)
    return pdf_path


def merge(parts, out_path):
    from pypdf import PdfWriter, PdfReader
    w = PdfWriter()
    for label, path in parts:
        r = PdfReader(path)
        start = len(w.pages)
        for pg in r.pages:
            w.add_page(pg)
        w.add_outline_item(label, start)
    with open(out_path, 'wb') as fh:
        w.write(fh)
    return out_path


def build(what='all'):
    made, missing = [], []
    parts = []
    index_rows = [r for r in ORDER if r[3] != 'renderings' and os.path.exists(os.path.join(ROOT, r[2]))]
    cov = os.path.join(OUT_D, '_cover.pdf')
    cover_pdf(cov, [r for r in ORDER if os.path.exists(os.path.join(ROOT, r[2]))])
    parts.append(('Cover and contents', cov))
    for key, label, rel, kind in ORDER:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            missing.append('%s  (%s)' % (rel, label)); continue
        try:
            if kind == 'doc' and what in ('all', 'docs'):
                p = os.path.join(OUT_D, os.path.splitext(os.path.basename(rel))[0] + '.pdf')
                doc_pdf(src, p, label); made.append(p); parts.append((label, p))
            elif kind == 'sheet' and what in ('all', 'sheets'):
                p = os.path.join(OUT_S, key.replace('.', '-') + '_' + os.path.basename(rel)[:-4] + '.pdf')
                sheet_pdf(src, p); made.append(p); parts.append((label, p))
            elif kind == 'renderings' and what == 'all':
                p = os.path.join(OUT_D, 'renderings.pdf')
                if renderings_pdf(p, src):
                    made.append(p); parts.append((label, p))
        except Exception as e:                                    # keep going; report at the end
            missing.append('%s  (FAILED: %s)' % (rel, e))
    if what == 'all' and len(parts) > 1:
        b = merge(parts, os.path.join(OUT, 'RZ-2026_cottages-at-arcado-springs.pdf'))
        made.append(b)
        mcp = os.path.join(OUT_S, 'C-2-0_mcp-sheet.pdf')
        if os.path.exists(mcp):
            import shutil
            t = os.path.join(OUT, 'C-2-0_master-concept-plan_36x24.pdf')
            shutil.copyfile(mcp, t); made.append(t)
    print('BUILT %d file(s):' % len(made))
    for m in made:
        print('   ', os.path.relpath(m, ROOT), '(%.0f KB)' % (os.path.getsize(m) / 1024.0))
    if missing:
        print('NOT YET AVAILABLE (%d):' % len(missing))
        for m in missing:
            print('   ', m)
    return made, missing


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'all')# The binder's sheet tabs are DERIVED from the same register the cover sheet and the transmittal use
# (tools/cover.py SHEETS), so a sheet that has been issued can never be left out of the filing PDF —
# five were, before this was single-sourced. Documents keep their explicit order.
import cover as _cover                                            # noqa: E402


def _sheets(prefix):
    out = []
    for no, title, f, size, scale in _cover.SHEETS:
        if not f or not no.startswith(prefix):
            continue
        if not os.path.exists(os.path.join(ROOT, 'drawings', f)):
            continue
        item = '8' if prefix == 'C' else '11'
        out.append((no, 'Item %s — Sheet %s %s' % (item, no, title), 'drawings/' + f, 'sheet'))
    return out


ORDER = ([
    ('00', 'Transmittal and Index', 'docs/00-transmittal-and-index.md', 'doc'),
    ('01', 'Item 1 — Application Form data', 'docs/01-application-form-data.md', 'doc'),
    ('04', 'Item 3 — Standards Governing the Zoning Power', 'docs/04-standards-governing-zoning-power.md', 'doc'),
    ('07', 'Items 4 and 5 — Conflict of Interest and Certifications', 'docs/07-conflict-of-interest-and-certifications.md', 'doc'),
    ('03', 'Item 6 — Letter of Intent', 'docs/03-letter-of-intent.md', 'doc'),
    ('cond', 'Item 6 — Voluntary Zoning Conditions', 'data/voluntary-conditions.md', 'doc'),
    ('05', 'Item 7 — Legal Description (DRAFT)', 'docs/05-legal-description-DRAFT.md', 'doc'),
] + _sheets('C') + [
    ('02', 'Item 8 — Development Summary', 'docs/02-development-summary.md', 'doc'),
    ('08', 'Item 8 — Technical Memoranda', 'docs/08-technical-memoranda.md', 'doc'),
    ('06', 'Item 10 — Adjoining Property Owners', 'docs/06-adjoining-property-owners.md', 'doc'),
    ('09', 'Item 11 — Architectural Character, Elevations and Renderings',
     'docs/09-architectural-character-elevations-and-renderings.md', 'doc'),
] + _sheets('A') + [
    ('R', 'Item 11 — Illustrative Renderings', 'renderings', 'renderings'),
    ('12', 'Supporting — Outline Specifications', 'docs/12-outline-specifications.md', 'doc'),
    ('13', 'Supporting — HOA, HOPA and Covenant Outline', 'docs/13-hoa-hopa-and-covenant-outline.md', 'doc'),
    ('11', 'Supporting — Site Context Brief', 'docs/11-site-context-brief.md', 'doc'),
    ('10', 'Supporting — Submittal Checklist and Roadmap', 'docs/10-submittal-checklist-and-roadmap.md', 'doc'),
])

# ------------------------------------------------------------------ markdown -> reportlab
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                KeepTogether, PageBreak, Image as RLImage)

SS = getSampleStyleSheet()
BODY = ParagraphStyle('body', parent=SS['BodyText'], fontName='Helvetica', fontSize=8.6, leading=11.4,
                      spaceBefore=0, spaceAfter=5, alignment=TA_LEFT)
H = [ParagraphStyle('h%d' % i, parent=BODY, fontName='Helvetica-Bold',
                    fontSize=(15, 12.5, 10.6, 9.4, 8.8, 8.6)[i - 1],
                    leading=(18.5, 15.5, 13.2, 11.8, 11.2, 11),
                    spaceBefore=(13, 11, 9, 7, 6, 5)[i - 1], spaceAfter=(6, 5, 4, 3, 3, 3)[i - 1])
     for i in range(1, 7)]
for i, s in enumerate(H):
    s.leading = (18.5, 15.5, 13.2, 11.8, 11.2, 11)[i]
MONO = ParagraphStyle('mono', parent=BODY, fontName='Courier', fontSize=7.4, leading=9.2,
                      backColor=colors.HexColor('#F4F4F1'), borderPadding=3, spaceBefore=4, spaceAfter=6)
QUOTE = ParagraphStyle('quote', parent=BODY, leftIndent=12, textColor=colors.HexColor('#333333'),
                       borderPadding=0, spaceBefore=4, spaceAfter=6, fontName='Helvetica-Oblique')
CELL = ParagraphStyle('cell', parent=BODY, fontSize=7.2, leading=8.8, spaceAfter=0, spaceBefore=0)
CELLH = ParagraphStyle('cellh', parent=CELL, fontName='Helvetica-Bold')
LI = ParagraphStyle('li', parent=BODY, leftIndent=13, bulletIndent=3, spaceAfter=2.5)
TITLE_S = ParagraphStyle('t', parent=BODY, fontName='Helvetica-Bold', fontSize=19, leading=23, spaceAfter=8)
SUB_S = ParagraphStyle('s', parent=BODY, fontSize=9.6, leading=13, textColor=colors.HexColor('#444444'),
                       spaceAfter=16)

INLINE = [
    (re.compile(r'`([^`]+)`'), r'<font face="Courier" size="7.6">\1</font>'),
    (re.compile(r'\*\*\*(.+?)\*\*\*'), r'<b><i>\1</i></b>'),
    (re.compile(r'\*\*(.+?)\*\*'), r'<b>\1</b>'),
    (re.compile(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])'), r'<i>\1</i>'),
    (re.compile(r'\[([^\]]+)\]\((https?://[^)\s]+)\)'), r'<link href="\2" color="#1A5276">\1</link>'),
    (re.compile(r'(?<![\w/">])(https?://[^\s<>()\]]+)'), r'<link href="\1" color="#1A5276">\1</link>'),
]


def inline(t):
    t = html.escape(t, quote=False)
    for rx, rep in INLINE:
        t = rx.sub(rep, t)
    return t


def para(t, st=BODY):
    return Paragraph(inline(t), st)


def md_to_flowables(md, width):
    """Render the markdown subset these documents use."""
    out = []
    lines = md.split('\n')
    i, n = 0, len(lines)
    # strip a YAML front-matter block into a small header table
    if lines and lines[0].strip() == '---':
        j = 1
        while j < n and lines[j].strip() != '---':
            j += 1
        fm = [l for l in lines[1:j] if l.strip()]
        if fm:
            rows = []
            for l in fm:
                if ':' in l:
                    k, v = l.split(':', 1)
                    rows.append([Paragraph(inline(k.strip()), CELLH), Paragraph(inline(v.strip().strip('"')), CELL)])
            if rows:
                t = Table(rows, colWidths=[width * 0.17, width * 0.83])
                t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                       ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                                       ('TOPPADDING', (0, 0), (-1, -1), 2),
                                       ('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.HexColor('#DDDDDD'))]))
                out += [t, Spacer(1, 8)]
        i = j + 1
    buf = []

    def flush():
        if buf:
            out.append(para(' '.join(buf)))
            del buf[:]

    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s:
            flush(); i += 1; continue
        if s.startswith('```'):
            flush(); i += 1; code = []
            while i < n and not lines[i].strip().startswith('```'):
                code.append(lines[i]); i += 1
            i += 1
            txt = html.escape('\n'.join(code)).replace(' ', '&nbsp;').replace('\n', '<br/>')
            out.append(Paragraph(txt, MONO)); continue
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', s):
            flush()
            out.append(Spacer(1, 3))
            t = Table([['']], colWidths=[width], rowHeights=[0.6])
            t.setStyle(TableStyle([('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#CCCCCC'))]))
            out += [t, Spacer(1, 5)]; i += 1; continue
        m = re.match(r'^(#{1,6})\s+(.*)$', s)
        if m:
            flush()
            out.append(Paragraph(inline(m.group(2)), H[len(m.group(1)) - 1])); i += 1; continue
        if s.startswith('|') and i + 1 < n and re.match(r'^\|[\s:|-]+\|?$', lines[i + 1].strip()):
            flush()
            rows, i = _table(lines, i)
            out.append(_mk_table(rows, width)); out.append(Spacer(1, 5)); continue
        if s.startswith('>'):
            flush(); q = []
            while i < n and lines[i].strip().startswith('>'):
                q.append(lines[i].strip().lstrip('>').strip()); i += 1
            out.append(para(' '.join(q), QUOTE)); continue
        m = re.match(r'^([-*+])\s+(.*)$', s)
        if m:
            flush()
            out.append(Paragraph(inline(m.group(2)), LI, bulletText='•')); i += 1; continue
        m = re.match(r'^(\d+)[.)]\s+(.*)$', s)
        if m:
            flush()
            out.append(Paragraph(inline(m.group(2)), LI, bulletText=m.group(1) + '.')); i += 1; continue
        if s.startswith('<!--'):
            i += 1; continue
        buf.append(s); i += 1
    flush()
    return out


def _table(lines, i):
    def cells(l):
        l = l.strip()
        if l.startswith('|'):
            l = l[1:]
        if l.endswith('|'):
            l = l[:-1]
        return [c.strip() for c in re.split(r'(?<!\\)\|', l)]
    rows = [cells(lines[i])]
    i += 2
    while i < len(lines) and lines[i].strip().startswith('|'):
        rows.append(cells(lines[i])); i += 1
    w = max(len(r) for r in rows)
    rows = [r + [''] * (w - len(r)) for r in rows]
    return rows, i


def _mk_table(rows, width):
    ncol = len(rows[0])
    weights = []
    for c in range(ncol):
        weights.append(max(6, max(len(r[c]) for r in rows) ** 0.72))
    tot = sum(weights)
    cw = [max(0.5 * inch, width * w / tot) for w in weights]
    if sum(cw) > width:
        k = width / sum(cw)
        cw = [c * k for c in cw]
    data = [[Paragraph(inline(c), CELLH if ri == 0 else CELL) for c in r] for ri, r in enumerate(rows)]
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EFEDE7')),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#CFCFCF')),
        ('LEFTPADDING', (0, 0), (-1, -1), 3.5), ('RIGHTPADDING', (0, 0), (-1, -1), 3.5),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    return t


class DocTpl(BaseDocTemplate):
    def __init__(self, path, header, **kw):
        BaseDocTemplate.__init__(self, path, pagesize=letter, leftMargin=0.72 * inch, rightMargin=0.72 * inch,
                                 topMargin=0.78 * inch, bottomMargin=0.72 * inch, title=header, **kw)
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='f')
        self.header = header
        self.addPageTemplates([PageTemplate(id='p', frames=[fr], onPage=self._deco)])

    def _deco(self, c, d):
        c.saveState()
        c.setFont('Helvetica', 6.8)
        c.setFillColor(colors.HexColor('#777777'))
        c.drawString(self.leftMargin, letter[1] - 0.52 * inch,
                     'THE COTTAGES AT ARCADO SPRINGS — ' + self.header.upper())
        c.drawRightString(letter[0] - self.rightMargin, letter[1] - 0.52 * inch,
                          'DRAFT — NOT SEALED — ' + DATE)
        c.setStrokeColor(colors.HexColor('#DDDDDD')); c.setLineWidth(0.4)
        c.line(self.leftMargin, letter[1] - 0.60 * inch, letter[0] - self.rightMargin, letter[1] - 0.60 * inch)
        c.line(self.leftMargin, 0.60 * inch, letter[0] - self.rightMargin, 0.60 * inch)
        c.drawString(self.leftMargin, 0.44 * inch,
                     'Rezoning application R-1 to R-2 — City of Lilburn, Georgia — owner-prepared draft')
        c.drawRightString(letter[0] - self.rightMargin, 0.44 * inch, 'Page %d' % d.page)
        c.restoreState()


def doc_pdf(md_path, pdf_path, header):
    md = open(md_path, encoding='utf-8').read()
    d = DocTpl(pdf_path, header)
    d.build(md_to_flowables(md, d.width))
    return pdf_path


def sheet_pdf(svg_path, pdf_path):
    import cairosvg
    cairosvg.svg2pdf(url=svg_path, write_to=pdf_path)
    return pdf_path


def cover_pdf(pdf_path, index_rows):
    d = DocTpl(pdf_path, 'Cover and contents')
    f = [Spacer(1, 42), Paragraph(TITLE, TITLE_S), Paragraph(SUBTITLE, SUB_S),
         para('**Applicant and owner of record (PINs R6123 033 and 015):** Mohammed Awad, 4541 Arcado Road SW, '
              'Lilburn, Georgia 30047.'),
         para('**Filed under:** City of Lilburn Zoning Ordinance No. 2023-603, Article 10, section 1003, and the '
              'City of Lilburn 2026 Application Instructions — Rezoning / Special Use Permit / Change in Condition, '
              'items (1) through (11).'),
         para('**Request:** rezone 9.44 acres from R-1 (Single-Family Residential) to R-2 (Medium-Density '
              'Residential) for 43 one-story detached cottage homes on fee-simple lots, restricted to housing for '
              'older persons under 42 U.S.C. section 3607(b)(2)(C) by voluntary condition.'),
         Spacer(1, 14),
         Paragraph('Contents', H[1])]
    rows = [['Tab', 'Document or sheet', 'Instruction item']]
    for key, label, _p, _k in index_rows:
        item = ''
        m = re.search(r'Item (\d+)', label)
        if m:
            item = m.group(1)
        elif label.startswith('Supporting'):
            item = 'supporting'
        elif label.startswith('Transmittal'):
            item = '—'
        rows.append([key, re.sub(r'^Item \d+ — |^Supporting — ', '', label), item])
    f.append(_mk_table(rows, d.width))
    f.append(Spacer(1, 14))
    f.append(para('> **Disclaimer:** This is an AI-generated analysis for preliminary planning purposes. All '
                  'findings must be verified by a licensed professional before use in design, permitting, or '
                  'regulatory submissions.', QUOTE))
    d.build(f)
    return pdf_path


def renderings_pdf(pdf_path, folder):
    """One landscape-ish contact set of the illustrative perspectives, each captioned."""
    imgs = sorted(f for f in os.listdir(folder)
                  if f.lower().endswith(('.jpg', '.png')) and f.startswith('R-'))
    if not imgs:
        return None
    d = DocTpl(pdf_path, 'Illustrative renderings')
    f = [Paragraph('Illustrative Renderings — Application Instructions item (11)', H[0]),
         para('These are illustrative perspectives prepared by the owner-applicant. They are generated from the '
              'scaled elevations in sheets A-2.1, A-2.2, A-2.3 and A-3.0 and from the master concept plan, and the '
              'scaled drawings govern wherever an image and a drawing differ. Item (11) permits imagery: '
              '"The drawings shall be to scale or in proper perspective… Visual imagery may be used."'),
         Spacer(1, 6)]
    from PIL import Image as PILImage
    small_dir = os.path.join(OUT_D, '_rend')
    os.makedirs(small_dir, exist_ok=True)
    for name in imgs:
        src = os.path.join(folder, name)
        p = os.path.join(small_dir, os.path.splitext(name)[0] + '.jpg')
        with PILImage.open(src) as im:          # embed a print-resolution copy, not the 2K original
            im = im.convert('RGB')
            im.thumbnail((1700, 1700))
            im.save(p, quality=82, optimize=True)
        with PILImage.open(p) as im:
            w, h = im.size
        iw = d.width
        ih = iw * h / float(w)
        if ih > 6.2 * inch:
            ih = 6.2 * inch; iw = ih * w / float(h)
        cap = os.path.splitext(name)[0].replace('_', ' — ').replace('-', ' ')
        f.append(KeepTogether([RLImage(p, iw, ih), Spacer(1, 3),
                               Paragraph(inline('**%s**' % cap), CELL), Spacer(1, 12)]))
    d.build(f)
    return pdf_path


def merge(parts, out_path):
    from pypdf import PdfWriter, PdfReader
    w = PdfWriter()
    for label, path in parts:
        r = PdfReader(path)
        start = len(w.pages)
        for pg in r.pages:
            w.add_page(pg)
        w.add_outline_item(label, start)
    with open(out_path, 'wb') as fh:
        w.write(fh)
    return out_path


def build(what='all'):
    made, missing = [], []
    parts = []
    index_rows = [r for r in ORDER if r[3] != 'renderings' and os.path.exists(os.path.join(ROOT, r[2]))]
    cov = os.path.join(OUT_D, '_cover.pdf')
    cover_pdf(cov, [r for r in ORDER if os.path.exists(os.path.join(ROOT, r[2]))])
    parts.append(('Cover and contents', cov))
    for key, label, rel, kind in ORDER:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            missing.append('%s  (%s)' % (rel, label)); continue
        try:
            if kind == 'doc' and what in ('all', 'docs'):
                p = os.path.join(OUT_D, os.path.splitext(os.path.basename(rel))[0] + '.pdf')
                doc_pdf(src, p, label); made.append(p); parts.append((label, p))
            elif kind == 'sheet' and what in ('all', 'sheets'):
                p = os.path.join(OUT_S, key.replace('.', '-') + '_' + os.path.basename(rel)[:-4] + '.pdf')
                sheet_pdf(src, p); made.append(p); parts.append((label, p))
            elif kind == 'renderings' and what == 'all':
                p = os.path.join(OUT_D, 'renderings.pdf')
                if renderings_pdf(p, src):
                    made.append(p); parts.append((label, p))
        except Exception as e:                                    # keep going; report at the end
            missing.append('%s  (FAILED: %s)' % (rel, e))
    if what == 'all' and len(parts) > 1:
        b = merge(parts, os.path.join(OUT, 'RZ-2026_cottages-at-arcado-springs.pdf'))
        made.append(b)
        mcp = os.path.join(OUT_S, 'C-2-0_mcp-sheet.pdf')
        if os.path.exists(mcp):
            import shutil
            t = os.path.join(OUT, 'C-2-0_master-concept-plan_36x24.pdf')
            shutil.copyfile(mcp, t); made.append(t)
    print('BUILT %d file(s):' % len(made))
    for m in made:
        print('   ', os.path.relpath(m, ROOT), '(%.0f KB)' % (os.path.getsize(m) / 1024.0))
    if missing:
        print('NOT YET AVAILABLE (%d):' % len(missing))
        for m in missing:
            print('   ', m)
    return made, missing


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'all')
