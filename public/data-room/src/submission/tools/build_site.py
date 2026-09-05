#!/usr/bin/env python3
"""Build the unlisted results page  public/cottages/submission/index.html  from the package.

Re-runnable: copies drawings/renderings/docs that exist, skips what doesn't. Neighbors' names are
redacted on the web copy of the adjoining-owners list (the full list stays in the local package).
"""
import json, os, re, shutil, html, datetime, sys
from pathlib import Path

W = Path('/home/mawad/arcado-springs/status/cottage-submission-2026-08-28')
PUB = Path('/home/mawad/arcado-springs/public')
OUT = PUB / 'cottages' / 'submission'
(OUT / 'drawings').mkdir(parents=True, exist_ok=True)
(OUT / 'renderings').mkdir(parents=True, exist_ok=True)
(OUT / 'docs').mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().strftime('%d %b %Y')

# ------------------------------------------------------------------ markdown → html (small, dependency-free)
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r'(?<!["\'>=])(https?://[^\s<)]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)
    return s

def md_to_html(text, redact=None):
    lines = text.replace('\r', '').split('\n')
    # strip YAML front matter
    if lines and lines[0].strip() == '---':
        try:
            end = lines[1:].index('---') + 1
            lines = lines[end + 1:]
        except ValueError:
            pass
    out, i, n = [], 0, len(lines)
    para = []
    def flush():
        if para:
            out.append('<p>' + inline(' '.join(para)) + '</p>')
            para.clear()
    while i < n:
        ln = lines[i]
        st = ln.strip()
        if st.startswith('<!--'):
            i += 1; continue
        if st.startswith('```'):
            flush(); j = i + 1; buf = []
            while j < n and not lines[j].strip().startswith('```'):
                buf.append(lines[j]); j += 1
            out.append('<pre><code>' + html.escape('\n'.join(buf)) + '</code></pre>')
            i = j + 1; continue
        m = re.match(r'^(#{1,6})\s+(.*)$', st)
        if m:
            flush(); lvl = min(len(m.group(1)) + 1, 5)
            out.append(f'<h{lvl}>{inline(m.group(2))}</h{lvl}>'); i += 1; continue
        if st.startswith('|') and i + 1 < n and re.match(r'^\|?\s*:?-{2,}', lines[i + 1].strip()):
            flush(); hdr = [c.strip() for c in st.strip('|').split('|')]
            rows = []; j = i + 2
            while j < n and lines[j].strip().startswith('|'):
                rows.append([c.strip() for c in lines[j].strip().strip('|').split('|')]); j += 1
            t = ['<div class="tbl-wrap"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in hdr) + '</tr></thead><tbody>']
            for r in rows:
                cells = r + [''] * (len(hdr) - len(r))
                if redact: cells = [redact(c) for c in cells]
                t.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in cells[:len(hdr)]) + '</tr>')
            t.append('</tbody></table></div>'); out.append(''.join(t)); i = j; continue
        if st.startswith('>'):
            flush(); buf = []
            while i < n and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip()[1:].strip()); i += 1
            out.append('<blockquote>' + inline(' '.join(buf)) + '</blockquote>'); continue
        m = re.match(r'^(\s*)([-*]|\d+[.)])\s+(.*)$', ln)
        if m:
            flush(); ordered = m.group(2)[0].isdigit(); items = []
            while i < n:
                m2 = re.match(r'^(\s*)([-*]|\d+[.)])\s+(.*)$', lines[i])
                if not m2:
                    # continuation line
                    if lines[i].startswith('  ') and lines[i].strip() and items:
                        items[-1] += ' ' + lines[i].strip(); i += 1; continue
                    break
                items.append(m2.group(3)); i += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>'); continue
        if st == '':
            flush(); i += 1; continue
        if re.match(r'^-{3,}$', st):
            flush(); out.append('<hr>'); i += 1; continue
        para.append(st); i += 1
    flush()
    return '\n'.join(out)

# ------------------------------------------------------------------ data
def load(p, default=None):
    try: return json.load(open(p))
    except Exception: return default
layout = load(W / 'data/layout.json', {})
plans = load(W / 'data/plans.json', {})
elev = load(W / 'data/elevations.json', {})
M = layout.get('metrics', {})
owners = load(W / 'data/owners-found.json', {})

# redaction for the adjoining-owner table on the web copy
owner_names = set()
if isinstance(owners, dict):
    for v in owners.values():
        for k in ('OWNERNAME1', 'OWNERNAME2', 'OWNER1', 'OWNER2', 'OWNERNAME'):
            if isinstance(v, dict) and v.get(k): owner_names.add(str(v[k]).strip())
elif isinstance(owners, list):
    for v in owners:
        for k in ('OWNERNAME1', 'OWNERNAME2', 'OWNERNAME'):
            if v.get(k): owner_names.add(str(v[k]).strip())
def redact_names(cell):
    c = cell
    for nm in owner_names:
        if nm and nm.upper() in c.upper() and 'AWAD' not in nm.upper() and 'MENDEZ' not in nm.upper():
            c = re.sub(re.escape(nm), '[owner of record — see local package]', c, flags=re.I)
    return c

# ------------------------------------------------------------------ copy assets
def copy_if(src, dst):
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst); return True
    return False

drawings = {}
for name in ['mcp-web.svg', 'mcp-sheet.svg', 'mcp-sheet.png', 'mcp-front.png', 'mcp-rear.png',
             'plan-a.svg', 'plan-a.png', 'plan-a-sheet.svg', 'plan-a-sheet.png', 'plan-a-lot.svg', 'plan-a-lot.png',
             'plan-b.svg', 'plan-b.png', 'plan-b-sheet.svg', 'plan-b-sheet.png', 'plan-b-lot.svg', 'plan-b-lot.png',
             'elev-a-sheet.svg', 'elev-a-sheet.png', 'elev-b-sheet.svg', 'elev-b-sheet.png',
             'elev-a-front.svg', 'elev-a-rear.svg', 'elev-a-left.svg', 'elev-a-right.svg',
             'elev-b-front.svg', 'elev-b-rear.svg', 'elev-b-left.svg', 'elev-b-right.svg']:
    if copy_if(W / 'drawings' / name, OUT / 'drawings' / name): drawings[name] = f'drawings/{name}'

# renderings: resize to web (≤ 1800 px wide, q85) if PIL available
renders = []
try:
    from PIL import Image
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False
render_meta = load(W / 'renderings/manifest.json', [])
for f in sorted((W / 'renderings').glob('*.jpg')) + sorted((W / 'renderings').glob('*.png')):
    dst = OUT / 'renderings' / (f.stem + '.jpg')
    if HAVE_PIL:
        im = Image.open(f).convert('RGB')
        if im.width > 1800: im = im.resize((1800, int(im.height * 1800 / im.width)), Image.LANCZOS)
        im.save(dst, 'JPEG', quality=85, optimize=True, progressive=True)
    else:
        shutil.copy2(f, dst)
    meta = next((m for m in render_meta if m.get('filename', '').endswith(f.name) or m.get('slug') == f.stem), {})
    renders.append({'file': f'renderings/{dst.name}', 'title': meta.get('title', f.stem.replace('-', ' ').title()),
                    'caption': meta.get('caption', ''), 'status': meta.get('qa_status', '')})

# documents
DOC_ORDER = ['01-application-form-data.md', '02-development-summary.md', '03-letter-of-intent.md',
             '04-standards-governing-zoning-power.md', '05-legal-description-DRAFT.md', '06-adjoining-property-owners.md',
             '07-conflict-of-interest-and-certifications.md', '08-technical-memoranda.md', '09-rendering-plan.md',
             '10-submittal-checklist-and-roadmap.md', '11-site-context-brief.md', '12-outline-specifications.md',
             '13-verification-report.md']
import sys as _sys
_sys.path.insert(0, str(W.parent / 'dataroom'))
import policy as _policy   # single source of truth for what may be published

docs = []
for name in DOC_ORDER:
    p = W / 'docs' / name
    if not p.exists(): continue
    # never publish a document the data-room tiering policy rates owner-only
    if _policy.tier(f'status/cottage-submission-2026-08-28/docs/{name}') == 'confidential':
        print(f'  skipping {name}: owner-only per policy.tier()')
        continue
    txt = p.read_text(encoding='utf-8', errors='replace')
    # same excision + internal-path scrub the data room applies to its shareable copies
    txt = _policy.excise(f'status/cottage-submission-2026-08-28/docs/{name}', txt)
    title = next((l.lstrip('# ').strip() for l in txt.splitlines() if l.startswith('# ')), name)
    body = md_to_html(txt, redact=redact_names if name.startswith('06') else None)
    slug = name.replace('.md', '')
    (OUT / 'docs' / f'{slug}.html').write_text(f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>{html.escape(title)} — Arcado Springs Cottages submission</title><link rel="stylesheet" href="../../../styles.css"><link rel="stylesheet" href="../submission.css"></head><body class="doc-page"><main class="wrap doc-body"><p class="eyebrow"><a href="../">&larr; Submission package</a></p>{body}</main></body></html>''', encoding='utf-8')
    docs.append({'slug': slug, 'title': title, 'name': name, 'words': len(txt.split())})

# verification summary (optional)
verify = load(W / 'verify/summary.json', None)

# ------------------------------------------------------------------ page
def stat(label, value, sub=''):
    return f'<li class="stat-card"><span class="stat-num">{value}</span><span class="stat-label">{label}{(" <span class=stat-plus>"+sub+"</span>") if sub else ""}</span></li>'

lots = M.get('lots', '—'); dens = M.get('density_du_ac_deeded', '—'); osp = M.get('open_space_pct_deeded', '—')
areas_a = (plans.get('plan_a') or plans.get('A') or {}).get('areas', {}) if isinstance(plans, dict) else {}
areas_b = (plans.get('plan_b') or plans.get('B') or {}).get('areas', {}) if isinstance(plans, dict) else {}

def img_block(src, alt, caption, wide=False):
    return f'''<figure class="sub-fig{' sub-fig--wide' if wide else ''}" data-reveal>
  <button class="gallery-trigger" type="button" data-lightbox="{src}" data-caption="{html.escape(caption, quote=True)}">
    <img src="{src}" loading="lazy" decoding="async" alt="{html.escape(alt, quote=True)}"><span class="img-tag">Click to enlarge</span>
  </button><figcaption>{caption}</figcaption></figure>'''

sections = []
# hero / overview
sections.append(f'''
<section class="section" id="overview"><div class="wrap">
  <p class="eyebrow">Rezoning submission package — working draft</p>
  <h1 class="section-title">The Cottages at Arcado Springs — R-1 → R-2 submission</h1>
  <p class="lede-text">Everything the City of Lilburn's 2026 rezoning instructions ask for, rebuilt on the property's real geometry (Gwinnett GIS parcel fabric: a 236–246 ft × ~1,740 ft strip, 9.44 ac deeded), the R-2 cottage-home standards of Zoning Ordinance 2023-603, and the June 2026 Comprehensive Plan Amendment ("Suburban-Low" — single-family cottages are an appropriate use).</p>
  <ul class="stats-grid" data-reveal>
    {stat('Cottage lots', lots, 'both sides of one lane')}
    {stat('Units per acre', dens, 'R-2 allows 8')}
    {stat('% common open space', osp, 'buffers, greens, creek woods, ponds')}
    {stat('Typical lot', "50' × 100'", '5,000 SF (min 3,000)')}
  </ul>
  <p class="muted gallery-foot">Generated {TODAY}. Drawings and documents are DRAFT concept work for the pre-application conference — not sealed, not filed. Boundary from Gwinnett GIS; a Georgia RLS survey governs. Adjoining property owners are named on the plan sheets and in Item 6, as the application requires and as survey convention puts them on a boundary drawing; those names come from the Gwinnett County public parcel record.</p>
</div></section>''')

# site plan
if 'mcp-web.svg' in drawings or 'mcp-sheet.png' in drawings:
    figs = ''
    if 'mcp-sheet.png' in drawings: figs += img_block(drawings['mcp-sheet.png'], 'Master concept plan sheet C-1', 'Sheet C-1 — Master Concept Plan, ARCH D 24×36 at 1"=60\' (boundary bearings, adjoining owners and zoning, buffers, setbacks, stream buffers, sewer, contours, lots, lane, amenity, ponds, site data table).', wide=True)
    if 'mcp-front.png' in drawings: figs += img_block(drawings['mcp-front.png'], 'Front 500 ft of the site plan', 'Front 500 ft — Arcado Rd entrance (SW third of the frontage), clubhouse and village green, pickleball, guest/mail parking, first lots.')
    if 'mcp-rear.png' in drawings: figs += img_block(drawings['mcp-rear.png'], 'Rear 500 ft of the site plan', 'Rear 500 ft — stream-head woods with 50/75-ft buffers, Pond 2, terminal hammerhead, Phase 2 sewer options.')
    if 'mcp-web.svg' in drawings: figs += f'<p class="muted"><a class="link-arrow" href="{drawings["mcp-web.svg"]}" target="_blank" rel="noopener">Open the vector plan (SVG) in a new tab &rarr;</a>{" &middot; <a class=link-arrow href=drawings/mcp-sheet.svg target=_blank rel=noopener>Sheet C-1 SVG &rarr;</a>" if "mcp-sheet.svg" in drawings else ""}</p>'
    sections.append(f'<section class="section section-alt" id="siteplan"><div class="wrap"><p class="eyebrow">Item 8 · Site plan</p><h2 class="section-title">Master Concept Plan on the real parcel geometry.</h2><p class="muted">One private lane on the strip\'s centerline, 50\'×100\' cottage lots on both sides with the 20-ft undisturbed buffer held inside the rear of each lot (§313(1)), hammerhead turnarounds instead of cul-de-sac circles (Table 4.2), two dry water-quality ponds on the south-west side, and the stream-head woods preserved at the rear.</p><div class="sub-grid">{figs}</div></div></section>')

# floor plans
fp = ''
for key, title, areas in (('a', 'Plan A — The Springbrook', areas_a), ('b', 'Plan B — The Laurel', areas_b)):
    imgs = ''
    for suffix, cap in (('', 'dimensioned plan'), ('-lot', 'sited on a typical 50\'×100\' lot'), ('-sheet', 'ARCH C sheet with area tabulation')):
        nm = f'plan-{key}{suffix}.png'
        if nm in drawings: imgs += img_block(drawings[nm], f'{title} {cap}', f'{title} — {cap}.')
    if imgs:
        a = areas or {}
        fp += f'<h3 class="subhead">{title}</h3><p class="muted">Conditioned {a.get("conditioned", "—")} SF · porch {a.get("porch", "—")} SF · garage {a.get("garage", "—")} SF · under roof {a.get("total_under_roof", "—")} SF</p><div class="sub-grid">{imgs}</div>'
if fp:
    sections.append(f'<section class="section" id="plans"><div class="wrap"><p class="eyebrow">Item 11 · Floor plans</p><h2 class="section-title">Two one-story plans, drawn to fit the lot and the code.</h2><p class="muted">38\'×38\' and 40\'×40\' bodies inside a 40-ft buildable width (50-ft lot, 5-ft side yards); zero-step entries, 36-in doors, 5-ft turning circles; garages recessed 5 ft behind the front wall (Table 4.2).</p>{fp}</div></section>')

# elevations
ev = ''
for key, title in (('a', 'Plan A elevations'), ('b', 'Plan B elevations')):
    nm = f'elev-{key}-sheet.png'
    if nm in drawings: ev += img_block(drawings[nm], title, f'{title} — front, rear, left, right at 1/8"=1\'-0" with dimensions, materials and colour schemes.', wide=True)
if ev:
    sections.append(f'<section class="section section-alt" id="elevations"><div class="wrap"><p class="eyebrow">Item 11 · Elevations</p><h2 class="section-title">Every street-visible side, to scale, with colors and materials.</h2><div class="sub-grid">{ev}</div></div></section>')

# renderings
if renders:
    rg = ''.join(img_block(r['file'], r['title'], (r['title'] + (' — ' + r['caption'] if r['caption'] else '') + (f' <span class="pill-mono">{r["status"]}</span>' if r['status'] else ''))) for r in renders)
    sections.append(f'<section class="section" id="renderings"><div class="wrap"><p class="eyebrow">Item 11 · Renderings</p><h2 class="section-title">Dimension-locked AI renderings.</h2><p class="muted">Each image was generated from the drawings above as reference input with a prompt that states the real dimensions (strip width, lot spacing, plate and ridge heights, materials) and was checked by an independent reviewer against an acceptance list. AI-generated concept imagery — not photographs.</p><div class="sub-grid">{rg}</div></div></section>')

# documents
if docs:
    dl = ''.join(f'<li class="doc-item"><a href="docs/{d["slug"]}.html"><span class="doc-num">{d["name"][:2]}</span><span class="doc-title">{html.escape(d["title"])}</span><span class="doc-meta">{d["words"]:,} words</span></a></li>' for d in docs)
    sections.append(f'<section class="section section-alt" id="documents"><div class="wrap"><p class="eyebrow">Items 1–7, 10 and supporting studies</p><h2 class="section-title">The written package.</h2><p class="muted">Application data sheet, development summary with the Table 4.1 compliance matrix, letter of intent with voluntary conditions, the six §1003-7 criteria, GIS-derived legal description (draft), adjoining owners, disclosures, technical memoranda (traffic, sewer, water, stormwater, fire, schools, environmental), site-context brief, outline specifications, and the submittal checklist with costs and calendar.</p><ul class="doc-list">{dl}</ul></div></section>')

# verification
if verify:
    rows = ''.join(f'<tr><td>{html.escape(str(v.get("artifact","")))}</td><td>{html.escape(str(v.get("lens","")))}</td><td>{v.get("findings","")}</td><td>{v.get("fixed","")}</td><td>{html.escape(str(v.get("verdict","")))}</td></tr>' for v in verify.get('rows', []))
    sections.append(f'<section class="section" id="verification"><div class="wrap"><p class="eyebrow">Independent review</p><h2 class="section-title">How the work was checked.</h2><p class="muted">{html.escape(verify.get("summary",""))}</p><div class="tbl-wrap"><table><thead><tr><th>Artifact</th><th>Lens</th><th>Findings</th><th>Fixed</th><th>Verdict</th></tr></thead><tbody>{rows}</tbody></table></div></div></section>')

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="theme-color" content="#2F5D3A" />
  <meta name="color-scheme" content="light" />
  <title>Arcado Springs — Cottages R-2 Submission Package (draft)</title>
  <meta name="description" content="Working draft of the R-2 rezoning submission package for The Cottages at Arcado Springs, Lilburn GA — site plan, floor plans, elevations, renderings and documents." />
  <meta name="robots" content="noindex, nofollow" />
  <link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2032%2032'%3E%3Crect%20width='32'%20height='32'%20rx='7'%20fill='%232F5D3A'/%3E%3Cpath%20d='M16%206l8%2020H8z'%20fill='none'%20stroke='%23C9B896'%20stroke-width='2.4'%20stroke-linejoin='round'/%3E%3C/svg%3E" />
  <link rel="preconnect" href="https://fonts.googleapis.com" /><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap" />
  <link rel="stylesheet" href="../../styles.css" />
  <link rel="stylesheet" href="submission.css" />
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="nav" id="nav" data-nav><div class="wrap nav-inner">
    <a class="brand" href="/" aria-label="Arcado Springs home"><span class="brand-mark">Arcado <span class="brand-accent">Springs</span></span><span class="badge-mono" aria-hidden="true">SUBMISSION DRAFT</span></a>
    <nav class="nav-links" id="nav-links" aria-label="Primary"><a href="#siteplan">Site plan</a><a href="#plans">Floor plans</a><a href="#elevations">Elevations</a><a href="#renderings">Renderings</a><a href="#documents">Documents</a><a class="nav-feedback" href="/cottages.html">&larr; Concept study</a></nav>
    <button class="nav-toggle" id="nav-toggle" type="button" aria-expanded="false" aria-controls="nav-links" aria-label="Open menu"><span class="nav-toggle-bar"></span><span class="nav-toggle-bar"></span><span class="nav-toggle-bar"></span></button>
  </div></header>
  <main id="main"><span id="top" class="anchor-top"></span>
  <div class="trust-bar" role="note"><div class="wrap trust-bar-inner"><span>Working draft for pre-application review</span><span aria-hidden="true">·</span><span>Generated {TODAY}</span><span aria-hidden="true">·</span><span>Not sealed · not filed · not an approval</span><span aria-hidden="true">·</span><span>Renderings are AI-generated</span></div></div>
  {''.join(sections)}
  </main>
  <footer class="footer"><div class="wrap footer-inner"><div class="footer-brand"><span class="brand-mark">Arcado <span class="brand-accent">Springs</span></span><p class="footer-tag">Submission package — owner working draft.</p></div><div class="footer-meta"><p>Generated {TODAY}</p><p class="footer-disclaimer">This is an AI-assisted preliminary planning package. All findings must be verified by licensed professionals (Georgia RLS, PE, architect, attorney) before use in design, permitting, or regulatory submissions. Boundary geometry is from the Gwinnett County GIS parcel fabric, not a survey.</p><p><a href="/cottages.html">&larr; Cottages concept study</a> · <a href="/">Overview</a></p></div></div></footer>
  <div class="lightbox" id="lightbox" hidden aria-hidden="true"><div class="lightbox-backdrop" data-lightbox-close></div><figure class="lightbox-figure" role="dialog" aria-modal="true" aria-label="Enlarged image"><button class="lightbox-close" type="button" data-lightbox-close aria-label="Close">&times;</button><img class="lightbox-img" id="lightbox-img" src="" alt="" /><figcaption class="lightbox-caption" id="lightbox-caption"></figcaption></figure></div>
  <script src="../../main.js"></script>
</body>
</html>'''
(OUT / 'index.html').write_text(page, encoding='utf-8')
(OUT / 'submission.css').write_text('''
.sub-grid{display:grid;gap:26px;margin-top:26px}
@media(min-width:900px){.sub-grid{grid-template-columns:1fr 1fr}.sub-fig--wide{grid-column:1/-1}}
.sub-fig{margin:0;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-lg);overflow:hidden;box-shadow:var(--shadow-sm)}
.sub-fig .gallery-trigger{display:block;width:100%;border:0;padding:0;background:#fff;cursor:zoom-in;position:relative}
.sub-fig img{width:100%;height:auto;display:block}
.sub-fig figcaption{padding:12px 16px;color:var(--muted);font-size:.9rem}
.doc-list{list-style:none;margin:26px 0 0;padding:0;display:grid;gap:10px}
.doc-item a{display:grid;grid-template-columns:44px 1fr auto;gap:14px;align-items:center;padding:14px 18px;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);text-decoration:none;color:var(--text)}
.doc-item a:hover{border-color:var(--accent)}
.doc-num{font-family:var(--font-mono);font-size:.8rem;color:var(--accent2-ink)}
.doc-title{font-weight:600}.doc-meta{font-family:var(--font-mono);font-size:.7rem;color:var(--muted)}
.tbl-wrap{overflow-x:auto;margin:14px 0}
table{border-collapse:collapse;width:100%;font-size:.9rem;background:var(--surface)}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{background:var(--bg);font-family:var(--font-mono);font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.doc-body{padding:40px 0 80px;max-width:900px}
.doc-body h2{font-size:1.9rem;margin-top:1.2em}.doc-body h3{font-size:1.35rem;margin-top:1.4em}.doc-body h4{font-size:1.1rem}
.doc-body blockquote{border-left:4px solid var(--accent2);margin:1.2em 0;padding:8px 16px;background:var(--surface);color:var(--muted)}
.doc-body pre{overflow-x:auto;background:#fff;border:1px solid var(--line);padding:12px;border-radius:8px;font-size:.82rem}
.doc-body code{font-family:var(--font-mono);font-size:.85em}
.doc-body img{max-width:100%}
''', encoding='utf-8')
print(f'built {OUT/"index.html"}: {len(page)//1024} KB; drawings {len(drawings)}; renderings {len(renders)}; docs {len(docs)}; verify {"yes" if verify else "no"}')
