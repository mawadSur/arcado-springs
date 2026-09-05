#!/usr/bin/env python3
"""Sheet C-8.0 "CIVIL DETAILS" — The Cottages at Arcado Springs (R-1 -> R-2, Lilburn GA).

    python3 tools/details.py     ->  drawings/civil-details.svg + .png

ARCH D 36 x 24 in, scales as noted per detail. Ten details:

    1  TYPICAL LOT ........................................ 1" = 10'
    2  TYPICAL PRIVATE LANE SECTION (walk one side) ....... 1/2" = 1'-0"
    3  WIDENED PRIVATE LANE SECTION (walks both sides) .... 1/2" = 1'-0"
    4  HAMMERHEAD TURNAROUND PLAN ......................... 1" = 20'
    5  PAVEMENT STRUCTURES — LANE / DRIVEWAY / PARKING .... 1-1/2" = 1'-0"
    6  ACCESSIBLE SPACE, ACCESS AISLE AND SIGN ............ plan 3/16" = 1'-0"; sign 3/8" = 1'-0"
    7  MONUMENT ENTRY SIGN — PLAN AND ELEVATION ........... 1/2" = 1'-0"
    8  MAIL KIOSK / CLUSTER BOX UNIT ...................... 3/16" = 1'-0"
    9  TREE-PROTECTION FENCE .............................. 3/8" = 1'-0"
   10  TYPICAL BUFFER SECTION ............................. 1" = 10'

WHY THIS SHEET EXISTS
The City of Lilburn Site Development Plan Review Checklist section 4.s says "All components of
private streets and alleys must meet minimum standards for public street", section 7.i asks for a
"typical paving section for parking areas and drives", section 4.t for driveway and parking
materials with standard details, section 4.r for a mail-delivery accessory structure "with
protection from the elements", section 4.x for the accessible space "with details", section 4.q for
the sign location, and section 6.g for the tree-protection fence detail and its note. Nothing in the
package answered any of those with a drawn, dimensioned detail. This sheet does, and it is also the
one picture that explains the section 313(1) design basis: the 20-ft undisturbed buffer held inside
the rear of every lot under a recorded easement (detail 10).

WHERE THE GEOMETRY COMES FROM — nothing on this sheet is a hand-drawn coordinate
    data/layout.json   lots 21 and 22 (Block A lots 17 and 18, the NE side of the lane at
                       u 580-680 ft, Phase 1) drive detail 1 in full: lot polygons, buffer
                       easements, setback envelopes, house / garage / porch / rear-element and
                       driveway rectangles.  The lane tract, pavement, centreline and sidewalk
                       polygons drive details 1, 2 and 3 at stations u = 300 and u = 700.  The
                       hammerhead legs drive detail 4.  amenity.accessible_stall / accessible_aisle
                       / kiosk_stalls drive detail 6, amenity.entry_sign detail 7 and
                       amenity.mail_kiosk detail 8.
    data/plans.json    Plan A "The Springbrook" and Plan B "The Laurel" body dimensions, footprint
                       polygons, garage / porch / patio rectangles, areas and lot_siting — the
                       reason detail 1 is drawn at the TRUE body depths of 38'-0" x 51'-10" and
                       38'-0" x 57'-6" and not at the 38 x 38 / 40 x 40 nominal program figures.
    docs/12-outline-specifications.md sections 32 12 16, 32 16 13, 10 14 00 — pavement structures,
                       curb, sidewalk and monument-sign materials.
    docs/08-technical-memoranda.md Memo E — the fire-access position.

sitebase.py is imported for the palette, the drawing primitives, the disclaimer text and the marker,
and for render/save; the ARCH D title block is rebuilt here rather than taken from sitebase.sheet()
because a details sheet has no single plan window, no single scale and no plan-window watermark.
The block's cell grid, wording and type sizes are copied from sitebase.sheet() so C-8.0 sits in the
same set as C-0 and C-1.

DRAFT — NOT SEALED. Concept details for a rezoning application. Not construction documents. Every
structural section, pavement section, footing and slope shown must be designed and sealed by a
Georgia registered professional engineer (and, for the tree-protection and buffer details, a
registered landscape architect, forester or certified arborist) before any permit.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sitebase as sb                                       # noqa: E402

LAYOUT = sb.LAYOUT
MET = LAYOUT['metrics']
LANE = LAYOUT['lane']
AMEN = LAYOUT['amenity']
PLANS = sb._load('plans.json')['plans']
LOTS = {L['id']: L for L in LAYOUT['lots']}

SHEET_NO = 'C-8.0'
SHEET_TITLE = 'CIVIL DETAILS'
GEN = 'tools/sitebase.py + tools/details.py'

# ============================================================================ lettering
# House rule (FACTS.md section 6): minimum lettering 1/8 in at full size so the 11 x 17 reduction
# still reads.  Every string on this sheet is set at 9.0 pt or larger: 9.0 pt Liberation Sans is
# 0.125 in from ascender to descender and 0.089 in of cap height at full size, and 0.058 in of cap
# height at the 46.4 % reduction to 11 x 17.  The basis is stated in general note 12.
TXT = 9.0            # minimum body / annotation lettering
DIM = 9.0            # dimension lettering
LBL = 10.0           # emphasised callout
DTL = 14.0           # detail title
SUB = 9.5            # detail sub-title / scale note

C = dict(sb.C)
C.update({
    'dim': '#b0121a', 'note': '#111', 'lot': '#111', 'setb': '#8a8a8a', 'walkf': '#e9e9e6',
    'asph_s': '#4a4a4a', 'asph_i': '#6f6f6f', 'gab': '#cbc2ab', 'sub': '#a89b80',
    'conc': '#e6e6e2', 'mas': '#c8ac8a', 'grass': '#dfeed3', 'tree': '#3f7a37',
    'wood': '#7a5230', 'blue': '#1565c0', 'fire': '#b00020', 'code': '#1b5e20',
})

DEFS2 = '''<defs>
<pattern id="d_conc" patternUnits="userSpaceOnUse" width="9" height="9"><rect width="9" height="9" fill="#eeeeea"/><circle cx="2" cy="3" r="0.5" fill="#a9a9a2"/><circle cx="6.5" cy="6" r="0.6" fill="#a9a9a2"/><circle cx="7.5" cy="1.5" r="0.4" fill="#b8b8b0"/><circle cx="3.5" cy="7.5" r="0.4" fill="#b8b8b0"/></pattern>
<pattern id="d_gab" patternUnits="userSpaceOnUse" width="8" height="8"><rect width="8" height="8" fill="#ded4bb"/><circle cx="2" cy="2" r="1.15" fill="none" stroke="#8f8straight" stroke-width="0.4"/></pattern>
<pattern id="d_gab2" patternUnits="userSpaceOnUse" width="9" height="9"><rect width="9" height="9" fill="#ded4bb"/><path d="M1 3 l2 -2 l2 2 z" fill="none" stroke="#8d8261" stroke-width="0.45"/><path d="M5 8 l2 -2 l1.6 2 z" fill="none" stroke="#8d8261" stroke-width="0.45"/><circle cx="7.2" cy="2.2" r="0.9" fill="none" stroke="#8d8261" stroke-width="0.45"/><circle cx="2.2" cy="6.6" r="0.7" fill="none" stroke="#8d8261" stroke-width="0.45"/></pattern>
<pattern id="d_sub" patternUnits="userSpaceOnUse" width="10" height="10" patternTransform="rotate(45)"><rect width="10" height="10" fill="#efe9dc"/><line x1="0" y1="0" x2="0" y2="10" stroke="#b3a급" stroke-width="0.4"/></pattern>
<pattern id="d_earth" patternUnits="userSpaceOnUse" width="11" height="11" patternTransform="rotate(45)"><rect width="11" height="11" fill="#fbfaf6"/><line x1="0" y1="0" x2="0" y2="11" stroke="#b2a488" stroke-width="0.45"/><line x1="5.5" y1="0" x2="5.5" y2="5" stroke="#c6bba4" stroke-width="0.35"/></pattern>
<pattern id="d_mas" patternUnits="userSpaceOnUse" width="16" height="9"><rect width="16" height="9" fill="#e8d8bf"/><line x1="0" y1="4.5" x2="16" y2="4.5" stroke="#b09166" stroke-width="0.5"/><line x1="0" y1="9" x2="16" y2="9" stroke="#b09166" stroke-width="0.5"/><line x1="0" y1="0" x2="0" y2="4.5" stroke="#b09166" stroke-width="0.5"/><line x1="8" y1="4.5" x2="8" y2="9" stroke="#b09166" stroke-width="0.5"/></pattern>
<pattern id="d_grass" patternUnits="userSpaceOnUse" width="14" height="14"><rect width="14" height="14" fill="#e8f3de"/><path d="M3 12 l1 -4 M4 12 l0 -4.5 M5 12 l1 -4" fill="none" stroke="#8fb37c" stroke-width="0.4"/><path d="M10 13 l0.8 -3.5 M11 13 l0 -4" fill="none" stroke="#8fb37c" stroke-width="0.4"/></pattern>
<pattern id="d_mulch" patternUnits="userSpaceOnUse" width="10" height="6"><rect width="10" height="6" fill="#e3d6c4"/><line x1="0.5" y1="2" x2="4" y2="2" stroke="#9c8465" stroke-width="0.5"/><line x1="5" y1="4.5" x2="8.5" y2="4.5" stroke="#9c8465" stroke-width="0.5"/></pattern>
</defs>'''
DEFS2 = DEFS2.replace('#8f8straight', '#8d8261').replace('#b3a급', '#b3a68c')


# ============================================================================ small helpers
FRAC = {0: '', 1: '⅛', 2: '¼', 3: '⅜', 4: '½', 5: '⅝', 6: '¾', 7: '⅞'}


def fti(v, base=2):
    """Feet (decimal) -> architectural string, e.g. 26.67 -> 26'-8\".  Rounds to 1/base inch."""
    neg = v < 0
    v = abs(v)
    n = int(round(v * 12.0 * base))
    ft, rem = divmod(n, 12 * base)
    inch, fr = divmod(rem, base)
    s = "%d'-%d%s\"" % (ft, inch, FRAC.get(fr * (8 // base), ''))
    return ('-' + s) if neg else s


def inch(v_in):
    """Inches (decimal) -> string, e.g. 1.25 -> 1¼ in."""
    n = int(round(v_in * 8))
    whole, fr = divmod(n, 8)
    return '%d%s in' % (whole, FRAC.get(fr, ''))


def sf(v):
    return format(int(round(v)), ',') + ' SF'


def interp(path, u):
    pts = sorted(path)
    if u <= pts[0][0]:
        return pts[0][1]
    for i in range(len(pts) - 1):
        if pts[i][0] <= u <= pts[i + 1][0] and pts[i + 1][0] > pts[i][0]:
            t = (u - pts[i][0]) / (pts[i + 1][0] - pts[i][0])
            return pts[i][1] + t * (pts[i + 1][1] - pts[i][1])
    return pts[-1][1]


def halves(poly):
    n = len(poly) // 2
    return poly[:n], poly[n:]


_TR_SW, _TR_NE = halves(LANE['tract_polygon'])
_PV_SW, _PV_NE = halves(LANE['pavement_polygon'])
_SWK = {s['side']: halves(s['polygon']) for s in LANE['sidewalks']}


def station(u):
    """Every cross-section dimension of the lane at station u, straight from layout.json."""
    cl = interp(LANE['centerline'], u)
    a, b = interp(_TR_SW, u), interp(_TR_NE, u)
    pa, pb = interp(_PV_SW, u), interp(_PV_NE, u)
    d = {'u': u, 'cl': cl, 'tr_sw': min(a, b), 'tr_ne': max(a, b),
         'pv_sw': min(pa, pb), 'pv_ne': max(pa, pb)}
    d['tract_w'] = d['tr_ne'] - d['tr_sw']
    d['pave_w'] = d['pv_ne'] - d['pv_sw']
    for side, key in (('NE', 'ne'), ('SW', 'sw')):
        h = _SWK.get(side)
        if not h:
            continue
        us = [p[0] for p in h[0]]
        if not (min(us) - 0.01 <= u <= max(us) + 0.01):
            continue                       # the SW walk starts at u = 530 ft; do not extrapolate
        lo, hi = interp(h[0], u), interp(h[1], u)
        d['w_%s' % key] = (min(lo, hi), max(lo, hi))
    return d


ST_TYP = station(300.0)          # detail 2 — sidewalk on the NE side only
ST_WID = station(700.0)          # detail 3 — sidewalks both sides


# ============================================================================ detail window
HEAD = 46.0          # points reserved above every detail box for title + two-line sub-title


class Det:
    """One detail window on the sheet.

    Model units are feet with y UP.  (ox, oy) is the model point that lands on the box's
    bottom-left corner, so a detail is positioned by naming the model coordinate of its
    lower-left corner and its scale in points per foot.
    """

    def __init__(self, D, x, y, w, h, scale, ox, oy, num=None, title=None, scale_note=None,
                 sub=None, box=True):
        self.D, self.s = D, scale
        self.x, self.w = x, w
        self.y, self.h = (y + HEAD, h - HEAD) if title else (y, h)
        self.ox, self.oy = ox, oy
        self.num, self.title = num, title
        if title:
            self._head(y, scale_note, sub)
        if box:
            D.srect(self.x, self.y, self.w, self.h, fill='none', stroke='#000', stroke_width=0.9)

    # -- transforms ---------------------------------------------------------
    def X(self, u):
        return self.x + (u - self.ox) * self.s

    def Y(self, v):
        return self.y + self.h - (v - self.oy) * self.s

    def P(self, p):
        return '%.2f,%.2f' % (self.X(p[0]), self.Y(p[1]))

    # -- title --------------------------------------------------------------
    def _head(self, ytop, scale_note, sub):
        D = self.D
        cy = ytop + 15
        D.scircle(self.x + 11, cy - 4, 10.5, fill='#111', stroke='none')
        D.stext(self.x + 11, cy, str(self.num), size=12.5, bold=True, fill='#fff', anchor='middle')
        D.stext(self.x + 26, cy, self.title, size=DTL, bold=True)
        D.stext(self.x + self.w - 4, cy, 'SCALE %s' % scale_note, size=SUB, fill='#444',
                anchor='end')
        if sub:
            chars = max(int((self.w - 30) / (0.545 * TXT)), 20)
            for i, ln in enumerate(sb.wrap(sub, chars)[:2]):
                D.stext(self.x + 4, ytop + 27 + i * 10.5, ln, size=TXT, fill='#444')

    # -- model primitives ---------------------------------------------------
    def poly(self, pts, **kw):
        self.D.add('<polygon points="%s" %s/>' % (' '.join(self.P(p) for p in pts), sb.attrs(kw)))

    def pline(self, pts, **kw):
        self.D.add('<polyline points="%s" %s/>' % (' '.join(self.P(p) for p in pts), sb.attrs(kw)))

    def line(self, a, b, **kw):
        self.D.sline(self.X(a[0]), self.Y(a[1]), self.X(b[0]), self.Y(b[1]), **kw)

    def rect(self, x0, y0, x1, y1, **kw):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], **kw)

    def circ(self, c, r_ft, **kw):
        self.D.scircle(self.X(c[0]), self.Y(c[1]), r_ft * self.s, **kw)

    def arc(self, c, r, a0, a1, **kw):
        """Circular arc, angles in degrees measured CCW from +x in model space."""
        pts = [(c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a)))
               for a in [a0 + (a1 - a0) * i / 24.0 for i in range(25)]]
        self.pline(pts, fill='none', **kw)

    def txt(self, u, v, t, size=TXT, anchor='middle', dx=0, dy=0, **kw):
        self.D.stext(self.X(u) + dx, self.Y(v) + dy, t, size=size, anchor=anchor, **kw)

    def txts(self, u, v, lines, size=TXT, anchor='middle', dx=0, dy=0, lead=None, bold_first=False,
             **kw):
        lead = lead or size * 1.22
        for i, ln in enumerate(lines):
            self.D.stext(self.X(u) + dx, self.Y(v) + dy + i * lead, ln, size=size, anchor=anchor,
                         bold=(bold_first and i == 0), **kw)
        return self.Y(v) + dy + len(lines) * lead

    # -- leaders and annotation --------------------------------------------
    def leader(self, u, v, tx, ty, lines, size=TXT, anchor='start', col='#111', bold_first=False,
               lead=None, dot=True):
        """Leader from model point (u, v) to a text block whose first line sits at (tx, ty) in
        SHEET points relative to the detail box origin."""
        x1, y1 = self.x + tx, self.y + ty
        self.D.sline(self.X(u), self.Y(v), x1 - (5 if anchor == 'start' else -5), y1 - 2.5,
                     stroke=col, stroke_width=0.55)
        if dot:
            self.D.scircle(self.X(u), self.Y(v), 1.5, fill=col, stroke='none')
        lead = lead or size * 1.2
        for i, ln in enumerate(lines):
            self.D.stext(x1, y1 + i * lead, ln, size=size, anchor=anchor, fill=col,
                         bold=(bold_first and i == 0))
        return y1 + len(lines) * lead

    # -- dimensions ---------------------------------------------------------
    def _tick(self, x, y, vertical=False):
        r = 4.0
        if vertical:
            self.D.sline(x - r * 0.7, y + r * 0.7, x + r * 0.7, y - r * 0.7,
                         stroke=C['dim'], stroke_width=0.9)
        else:
            self.D.sline(x - r * 0.7, y + r * 0.7, x + r * 0.7, y - r * 0.7,
                         stroke=C['dim'], stroke_width=0.9)

    def dimh(self, u0, u1, v, txt=None, off=16, size=DIM, ext=True, force_out=False):
        """Horizontal dimension between u0 and u1, dimension line `off` points BELOW model line v
        (negative off = above)."""
        D = self.D
        x0, x1 = self.X(u0), self.X(u1)
        yv, yd = self.Y(v), self.Y(v) + off
        t = txt if txt is not None else fti(abs(u1 - u0))
        if ext:
            s = 1 if off > 0 else -1
            for x in (x0, x1):
                D.sline(x, yv + s * 2.0, x, yd + s * 3.0, stroke=C['dim'], stroke_width=0.4)
        tw = 0.58 * size * len(t)
        span = abs(x1 - x0)
        if span > tw + 10 and not force_out:
            g = tw / 2.0 + 3
            xm = (x0 + x1) / 2.0
            D.sline(x0, yd, xm - g, yd, stroke=C['dim'], stroke_width=0.7)
            D.sline(xm + g, yd, x1, yd, stroke=C['dim'], stroke_width=0.7)
            D.srect(xm - tw / 2.0 - 1.5, yd - size * 0.68, tw + 3, size * 1.05, fill='#fff',
                    fill_opacity='0.9', stroke='none')
            D.stext(xm, yd + size * 0.36, t, size=size, anchor='middle', fill=C['dim'], bold=True)
        else:
            D.sline(x0, yd, x1, yd, stroke=C['dim'], stroke_width=0.7)
            D.sline(max(x0, x1), yd, max(x0, x1) + 9, yd, stroke=C['dim'], stroke_width=0.7)
            D.srect(max(x0, x1) + 10.5, yd - size * 0.68, tw + 3, size * 1.05, fill='#fff',
                    fill_opacity='0.9', stroke='none')
            D.stext(max(x0, x1) + 12, yd + size * 0.36, t, size=size, anchor='start',
                    fill=C['dim'], bold=True)
        self._tick(x0, yd)
        self._tick(x1, yd)
        return yd

    def dimv(self, v0, v1, u, txt=None, off=-16, size=DIM, ext=True, force_out=False):
        """Vertical dimension between v0 and v1, dimension line `off` points RIGHT of model line u
        (negative off = left)."""
        D = self.D
        y0, y1 = self.Y(v0), self.Y(v1)
        xv, xd = self.X(u), self.X(u) + off
        t = txt if txt is not None else fti(abs(v1 - v0))
        if ext:
            s = 1 if off > 0 else -1
            for y in (y0, y1):
                D.sline(xv + s * 2.0, y, xd + s * 3.0, y, stroke=C['dim'], stroke_width=0.4)
        tw = 0.58 * size * len(t)
        span = abs(y1 - y0)
        if span > tw + 10 and not force_out:
            g = tw / 2.0 + 3
            ym = (y0 + y1) / 2.0
            D.sline(xd, y0, xd, ym - g if y0 < y1 else ym + g, stroke=C['dim'], stroke_width=0.7)
            D.sline(xd, ym + g if y0 < y1 else ym - g, xd, y1, stroke=C['dim'], stroke_width=0.7)
            D.srect(xd - size * 0.68, ym - tw / 2.0 - 1.5, size * 1.05, tw + 3, fill='#fff',
                    fill_opacity='0.9', stroke='none')
            D.stext(xd + size * 0.36, ym, t, size=size, anchor='middle', fill=C['dim'], bold=True,
                    rot=-90)
        else:
            D.sline(xd, y0, xd, y1, stroke=C['dim'], stroke_width=0.7)
            ye = min(y0, y1)
            D.sline(xd, ye, xd, ye - 9, stroke=C['dim'], stroke_width=0.7)
            D.stext(xd + size * 0.36, ye - 12, t, size=size, anchor='end', fill=C['dim'],
                    bold=True, rot=-90)
        self._tick(xd, y0, True)
        self._tick(xd, y1, True)
        return xd

    def chain_h(self, stops, v, off=16, size=DIM, labels=None):
        for i in range(len(stops) - 1):
            t = labels[i] if labels else None
            self.dimh(stops[i], stops[i + 1], v, txt=t, off=off, size=size)

    def chain_v(self, stops, u, off=-16, size=DIM, labels=None):
        for i in range(len(stops) - 1):
            t = labels[i] if labels else None
            self.dimv(stops[i], stops[i + 1], u, txt=t, off=off, size=size)

    # -- graphic scale ------------------------------------------------------
    def gscale(self, dx, dy, step_ft, steps, unit='ft', anchor_right=False):
        """Small graphic scale bar inside the box, positioned in sheet points from the box origin."""
        D = self.D
        w = step_ft * self.s * steps
        x = self.x + (self.w - dx - w if anchor_right else dx)
        y = self.y + dy
        D.srect(x - 16, y - 12, w + 34, 22, fill='#fff', fill_opacity='0.92', stroke='none')
        for k in range(steps):
            D.srect(x + step_ft * self.s * k, y, step_ft * self.s, 5.0,
                    fill='#000' if k % 2 == 0 else '#fff', stroke='#000', stroke_width=0.5)
        for k in (0, steps):
            D.stext(x + step_ft * self.s * k, y - 2.5, ('%g' % (step_ft * k)) + (
                '' if k == 0 else ' ' + unit), size=TXT, anchor='middle')
        return y


# ============================================================================ north arrow
def north(D, x, y, flip=False, r=26.0, caption='GRID NORTH (SR 2240 GA WEST)',
          sub="= 28°43' ABOVE THE +u AXIS"):
    """Grid-north arrow. `flip` draws it for a frame rotated 180 degrees (detail 1)."""
    a = math.radians(sb.NORTH_DEG)
    dx, dy = math.cos(a), -math.sin(a)
    if flip:
        dx, dy = -dx, -dy
    px, py = -dy, dx
    D.scircle(x, y, r, fill='#fff', stroke='#000', stroke_width=0.8)
    tip = (x + dx * r * 0.86, y + dy * r * 0.86)
    tail = (x - dx * r * 0.78, y - dy * r * 0.78)
    D.sline(tail[0], tail[1], tip[0], tip[1], stroke='#000', stroke_width=2.0)
    D.spoly([tip, (tip[0] - 14 * dx + 5.2 * px, tip[1] - 14 * dy + 5.2 * py),
             (tip[0] - 14 * dx - 5.2 * px, tip[1] - 14 * dy - 5.2 * py)], fill='#000')
    D.stext(tip[0] + 9 * dx, tip[1] + 9 * dy + 3.5, 'N', size=12, bold=True, anchor='middle')
    cw = 0.56 * TXT * max(len(caption), len(sub)) + 10
    D.srect(x - cw / 2.0, y + r + 2, cw, 23, fill='#fff', fill_opacity='0.92', stroke='none')
    D.stext(x, y + r + 12, caption, size=TXT, anchor='middle')
    D.stext(x, y + r + 22, sub, size=TXT, anchor='middle')


# ============================================================================ sheet frame
def sheet_frame(status_lines, scale_note):
    """ARCH D 36 x 24 frame + title block + disclaimer strip, on the Sheet C-0 / C-1 grid."""
    W, H, M, IN_ = sb.SHEET_W, sb.SHEET_H, sb.MARGIN, sb.INNER
    D = sb.Drawing(1.0, 0.0, 0.0, win=(0.0, 1.0, 0.0, 1.0))
    D.add('<svg xmlns="http://www.w3.org/2000/svg" width="36in" height="24in" '
          'viewBox="0 0 %d %d" font-family="%s">' % (W, H, sb.FONT))
    D.add('<title>%s</title>' % sb.esc('%s — %s — Sheet %s'
                                       % (sb.PROJECT.title(), SHEET_TITLE, SHEET_NO)))
    D.add(sb.DEFS)
    D.add(DEFS2)
    D.srect(0, 0, W, H, fill='#fff')
    D.srect(M, M, W - 2 * M, H - 2 * M, fill='none', stroke='#000', stroke_width=2)
    D.srect(M + IN_, M + IN_, W - 2 * M - 2 * IN_, H - 2 * M - 2 * IN_,
            fill='none', stroke='#000', stroke_width=0.6)

    tb_y, tb_h = sb.TB_Y, sb.TB_H - 6
    D.srect(M + IN_, tb_y, W - 2 * M - 2 * IN_, tb_h, fill='#fff', stroke='#000', stroke_width=1.2)
    cells = [0, 820, 1330, 1780, 2180, W - 2 * M - 2 * IN_]
    for cx in cells[1:-1]:
        D.sline(M + IN_ + cx, tb_y, M + IN_ + cx, tb_y + tb_h, stroke='#000', stroke_width=0.8)
    bx = M + 8
    D.stext(bx, tb_y + 30, sb.PROJECT, size=22, bold=True)
    D.stext(bx, tb_y + 52, '%s — Rezoning R-1 → R-2 (City of Lilburn, Georgia)' % SHEET_TITLE,
            size=13, bold=True)
    D.stext(bx, tb_y + 70, '%s — %s' % (sb.ADDRESSES, sb.LEGAL), size=9)
    D.stext(bx, tb_y + 86, 'Typical lot, private-lane sections, hammerhead turnaround, paving, '
                           'accessible space, monument sign, mail kiosk, tree protection and the '
                           '20-ft buffer', size=9)
    bx = M + IN_ + cells[1] + 8
    D.stext(bx, tb_y + 18, 'APPLICANT / OWNER', size=9, fill='#555')
    D.stext(bx, tb_y + 34, sb.APPLICANT, size=11, bold=True)
    D.stext(bx, tb_y + 48, '4541 Arcado Rd SW, Lilburn GA 30047-3968 (parcels 033, 015); '
                           'Mendez / Roblero de Leon', size=9)
    D.stext(bx, tb_y + 60, '(parcels 014, 162) — co-applicants, owner signatures required', size=9)
    D.stext(bx, tb_y + 76, 'PREPARED FOR', size=9, fill='#555')
    D.stext(bx, tb_y + 90, 'Pre-application conference, City of Lilburn Planning & Zoning '
                           '(340 Main St) —', size=9)
    D.stext(bx, tb_y + 101, 'rezoning application per Ord. 2023-603 §1003 (2026 Application '
                            'Instructions)', size=9)
    bx = M + IN_ + cells[2] + 8
    D.stext(bx, tb_y + 18, 'STATUS', size=9, fill='#555')
    D.stext(bx, tb_y + 38, 'DRAFT — NOT SEALED', size=14, bold=True, fill='#c00')
    for k, ln in enumerate(status_lines):
        D.stext(bx, tb_y + 54 + k * 11, ln, size=9)
    D.stext(bx, tb_y + 101, 'Generator: %s' % GEN, size=9)
    bx = M + IN_ + cells[3] + 8
    for k, (a, b) in enumerate([('DATE', sb.DATE), ('SCALE', scale_note),
                                ('DATUM', 'SR 2240 GA West US-ft; NAVD88'),
                                ('DRAWN', 'owner-prepared (AI-assisted)'),
                                ('CHECKED', 'PE / RLS / LA — pending')]):
        D.stext(bx, tb_y + 16 + k * 18, a, size=9, fill='#555')
        D.stext(bx + 58, tb_y + 16 + k * 18, b, size=9)
    bx = M + IN_ + cells[4] + 8
    D.stext(bx, tb_y + 18, 'SHEET', size=9, fill='#555')
    D.stext(bx + 150, tb_y + 72, SHEET_NO, size=48, bold=True, anchor='middle')
    D.stext(bx + 150, tb_y + 92, SHEET_TITLE, size=9, anchor='middle')

    dy = sb.TB_Y - 46
    D.srect(M + IN_, dy, W - 2 * M - 2 * IN_, 40, fill='#fff8e1', stroke='#b00', stroke_width=0.8)
    D.stext(M + IN_ + 8, dy + 15, 'Disclaimer: ' + sb.DISCLAIMER.split('Disclaimer: ')[-1],
            size=9.5, bold=True, fill='#7a0000')
    D.stext(M + IN_ + 8, dy + 30,
            'Label: DRAFT / NOT SEALED — every detail on this sheet is a concept that must be '
            'designed and sealed by a Georgia PE, RLS, architect or landscape architect. Statements '
            'of conformity read "appears consistent with"; nothing here is a compliance '
            'certification.', size=9, fill='#7a0000')
    D.add('<!-- %s -->' % sb.MARKER)
    return D


# ============================================================================ sheet layout (points)
S10, S20 = 72.0 / 10.0, 72.0 / 20.0            # 1" = 10' ; 1" = 20'
S12, S38, S316, S32 = 36.0, 27.0, 13.5, 108.0  # 1/2", 3/8", 3/16", 1-1/2" = 1'-0"

BOX = {
    'd1':  (52, 54, 956, 954),
    'd4':  (1020, 54, 576, 601),
    'd10': (1020, 667, 576, 341),
    'd7':  (1608, 54, 500, 502),
    'd6':  (1608, 568, 500, 440),
    'd8':  (2120, 54, 426, 310),
    'd9':  (2120, 376, 426, 274),
    'd5':  (2120, 662, 426, 346),
    'd2':  (52, 1014, 1448, 178),
    'd3':  (52, 1196, 1448, 178),
    'leg': (52, 1378, 1448, 150),
    'not': (1512, 1014, 1034, 514),
}


def band(lo, hi, u0, u1, n=16):
    """Closed polygon between two v = f(u) functions over [u0, u1]."""
    us = [u0 + (u1 - u0) * i / float(n) for i in range(n + 1)]
    return [(u, lo(u)) for u in us] + [(u, hi(u)) for u in reversed(us)]


# ============================================================================ 1 — TYPICAL LOT
# Lots 7 and 8 — Block A lots 7 and 8, the SOUTH-WEST side of the lane at u 580-680 ft, Phase 1.
# They are used rather than a north-east pair because the south-west lots are exactly rectangular
# in the site-local system (front line v = -134.60, rear v = -234.60 for their whole 50-ft width),
# so every setback prints as one exact number instead of a range.  The detail is drawn in a frame
# rotated 180 degrees about the middle of the pair, R(u, v) = (1260 - u, -v - 134.60), so that the
# lane reads at the bottom of the detail and the rear lot line at the top.  A 180-degree rotation
# is rigid and preserves handedness: left and right of each dwelling are as built.
L7, L8 = LOTS[7], LOTS[8]
PA, PB = PLANS['A'], PLANS['B']
U_SUM, V_OFF = 1260.0, 134.60


def R(p):
    return (U_SUM - p[0], -p[1] - V_OFF)


def RP(poly):
    return [R(p) for p in poly]


def _lot_stats(L, P):
    """Every dimension detail 1 prints, re-derived from the lot and plan records in the R frame."""
    poly = RP(L['polygon'])
    body = RP(L['house_rect'])
    gar = RP(L['garage_rect'])
    por = RP(L['porch_rect'])
    rr = RP(L['rear_rect'])
    dr = RP(L['driveway_rect'])
    env = RP(L['setback_envelope'])
    buf = RP(L['buffer_easement'])
    return {
        'poly': poly, 'body': body, 'gar': gar, 'por': por, 'rear': rr, 'drv': dr,
        'env': env, 'buf': buf,
        'u0': min(p[0] for p in poly), 'u1': max(p[0] for p in poly),
        'uc': sum(p[0] for p in poly) / 4.0,
        'fv': min(p[1] for p in poly), 'rv': max(p[1] for p in poly),
        'porch_face': min(p[1] for p in por), 'body_front': min(p[1] for p in body),
        'body_rear': max(p[1] for p in body), 'gar_face': min(p[1] for p in gar),
        'rear_el': max(p[1] for p in rr), 'buf_v': min(p[1] for p in buf),
        'setb_f': min(p[1] for p in env), 'setb_r': max(p[1] for p in env),
        'bu0': min(p[0] for p in body), 'bu1': max(p[0] for p in body),
        'gu0': min(p[0] for p in gar), 'gu1': max(p[0] for p in gar),
        'pu0': min(p[0] for p in por), 'pu1': max(p[0] for p in por),
        'du0': min(p[0] for p in dr), 'du1': max(p[0] for p in dr),
        'dv0': min(p[1] for p in dr), 'dv1': max(p[1] for p in dr),
        'ru0': min(p[0] for p in rr), 'ru1': max(p[0] for p in rr),
        'body_depth': P['overall_body_dims']['depth_ft'],
        'label': P['overall_body_dims']['label'],
        'imp': L['impervious'], 'plan': P,
    }


A = _lot_stats(L7, PA)          # Plan A "The Springbrook" — the right-hand lot in the R frame
B = _lot_stats(L8, PB)          # Plan B "The Laurel" — the left-hand lot


def d1(D):
    x, y, w, h = BOX['d1']
    TAB = 58.0                       # bottom strip inside the box frame, for the tabulation
    d = Det(D, x, y, w, h - TAB, S10, 558.0, -12.5, 1, 'TYPICAL LOT', '1" = 10\'',
            'Regenerated from data/layout.json lots 7 and 8 (Block A, south-west side of the lane, '
            'u 580–680 ft, Phase 1) and the true body geometry of data/plans.json — NOT from the '
            'nominal program dimensions. Drawn rotated 180° so the lane reads at the bottom.')
    u0, u1 = 558.0, 691.0
    pv = lambda u: -interp(_PV_SW, U_SUM - u) - V_OFF                                # noqa: E731
    tr = lambda u: -interp(_TR_SW, U_SUM - u) - V_OFF                                # noqa: E731
    wlo = lambda u: -interp(_SWK['SW'][0], U_SUM - u) - V_OFF                        # noqa: E731
    whi = lambda u: -interp(_SWK['SW'][1], U_SUM - u) - V_OFF                        # noqa: E731

    # ---- lane: pavement, 18-in gutter pan, 6-in curb, verge, 5-ft walk, verge to the lot line
    d.poly(band(lambda u: -13.0, pv, u0, u1), fill=C['asph_s'], stroke='none')
    d.poly(band(lambda u: pv(u) - 1.5, pv, u0, u1), fill='url(#d_conc)', stroke='#8a8a8a',
           stroke_width=0.4)
    d.poly(band(pv, lambda u: pv(u) + 0.5, u0, u1), fill='url(#d_conc)', stroke='#555',
           stroke_width=0.5)
    d.poly(band(lambda u: pv(u) + 0.5, wlo, u0, u1), fill='url(#d_grass)', stroke='none')
    d.poly(band(wlo, whi, u0, u1), fill='url(#d_conc)', stroke='#8a8a8a', stroke_width=0.5)
    d.poly(band(whi, tr, u0, u1), fill='url(#d_grass)', stroke='none')
    d.pline([(u, pv(u)) for u in (u0, u1)], fill='none', stroke='#222', stroke_width=1.2)

    # ---- the two lots
    for s in (B, A):
        d.poly(s['poly'], fill='#fff', stroke='none')
        d.poly(s['buf'], fill='url(#bufhatch)', stroke=C['green_line'], stroke_width=0.8)
        d.poly(s['env'], fill='none', stroke=C['setb'], stroke_width=0.8,
               stroke_dasharray='7 3 2 3')
        d.poly(s['drv'], fill='url(#d_conc)', stroke='#7a7a7a', stroke_width=0.6)
        wu = (s['pu0'] + s['pu1']) / 2.0
        d.rect(wu - 2.0, s['porch_face'], wu + 2.0, whi(wu), fill='url(#d_conc)', stroke='#7a7a7a',
               stroke_width=0.5)
        d.poly(s['body'], fill=C['house'], stroke='#111', stroke_width=1.5)
        d.poly(s['gar'], fill='#efd2ad', stroke='#111', stroke_width=0.9)
        d.poly(s['por'], fill='#fdf3e4', stroke='#111', stroke_width=0.9)
        d.poly(s['rear'], fill='#fdf3e4' if s is B else '#f0efe6', stroke='#111', stroke_width=0.9)
        d.poly(s['poly'], fill='none', stroke=C['lot'], stroke_width=1.7)

    # ---- labels inside the lots
    for s, nm, blk in ((A, 'A', 7), (B, 'B', 8)):
        P = s['plan']
        d.txts(s['uc'], 64.0, ['BLOCK A, LOT %d' % blk,
                               'PLAN %s "%s"' % (nm, P['name'].title()),
                               'BODY %s' % s['label'],
                               '%s CONDITIONED' % sf(P['areas']['conditioned_sf']),
                               '%s UNDER ROOF' % sf(P['areas']['total_under_roof_sf']),
                               "LOT 50'-0\" × 100'-0\" = 5,000 SF"],
               size=TXT, bold_first=True)
        d.txt((s['gu0'] + s['gu1']) / 2.0, 38.0, '2-CAR GARAGE', size=TXT)
        d.txt((s['gu0'] + s['gu1']) / 2.0, 35.6, "21'-0\" × 21'-10\"", size=TXT)
        d.txt((s['pu0'] + s['pu1']) / 2.0, 20.0, 'COVERED', size=TXT)
        d.txt((s['pu0'] + s['pu1']) / 2.0, 17.8, 'PORCH', size=TXT)
        d.txt((s['du0'] + s['du1']) / 2.0, 23.0, 'DRIVEWAY', size=TXT)
        d.txt((s['du0'] + s['du1']) / 2.0, 20.8, '2 CARS', size=TXT)
        d.txt(s['uc'], 91.0, "20'-0\" BUFFER EASEMENT — UNDISTURBED", size=TXT, fill='#2e5e1e')
        d.txt(s['uc'], 88.6, '(SEE 10/C-8.0)', size=TXT, fill='#2e5e1e')
    d.txt((A['ru0'] + A['ru1']) / 2.0, 76.4, 'UNCOVERED', size=TXT)
    d.txt((A['ru0'] + A['ru1']) / 2.0, 74.2, "PATIO 12' × 6'", size=TXT)
    d.txt((B['ru0'] + B['ru1']) / 2.0, 76.4, 'COVERED REAR PORCH', size=TXT)
    d.txt((B['ru0'] + B['ru1']) / 2.0, 74.2, "14' × 6' (RECESSED)", size=TXT)

    # ---- vertical chains, left of lot 8 (Plan B)
    d.chain_v([B['fv'], B['setb_f']], 580.0, off=-22, labels=["15'-0\""])
    d.chain_v([B['setb_r'], B['rv']], 580.0, off=-22, labels=["20'-0\""])
    d.chain_v([B['fv'], B['porch_face'], B['body_front'], B['body_rear'], B['rv']], 580.0, off=-52,
              labels=[fti(B['porch_face'] - B['fv']), "6'-0\"", fti(B['body_depth']),
                      fti(B['rv'] - B['body_rear'])])
    d.dimv(B['fv'], B['rv'], 580.0, txt="100'-0\" LOT DEPTH", off=-88)

    # ---- vertical chains, right of lot 7 (Plan A)
    d.chain_v([A['fv'], A['setb_f']], 680.0, off=20, labels=["15'-0\""])
    d.chain_v([A['setb_r'], A['rv']], 680.0, off=20, labels=["20'-0\""])
    d.chain_v([A['fv'], A['porch_face'], A['body_front'], A['body_rear'], A['rear_el'],
               A['rv']], 680.0, off=48,
              labels=[fti(A['porch_face'] - A['fv']), "6'-0\"", fti(A['body_depth']), "6'-0\"",
                      fti(A['rv'] - A['rear_el'])])
    d.dimv(B['body_front'], B['gar_face'], B['gu0'], txt="5'-0\" RECESS", off=-14)

    # ---- driveway chain on the shared lot line, clear of both dwellings
    ud = 630.0
    d.D.sline(d.X(A['gu0'] - 8.0), d.Y(A['gar_face']), d.X(A['gu0']), d.Y(A['gar_face']),
              stroke=C['dim'], stroke_width=0.4, stroke_dasharray='4 2')
    d.chain_v([A['gar_face'], tr(ud), whi(ud), wlo(ud), pv(ud)], ud, off=16,
              labels=[fti(A['gar_face'] - tr(ud)), None, "5'-0\"", "2'-0\""])
    d.dimv(A['gar_face'], pv(ud), ud, off=54,
           txt='%s GARAGE DOOR TO FACE OF CURB' % fti(A['gar_face'] - pv(ud)))

    # ---- horizontal chains
    d.chain_h([B['u0'], B['u1'], A['u1']], A['rv'], off=-22, labels=["50'-0\"", "50'-0\""])
    d.txt(615.0, 96.4, 'REAR LOT LINE = ASSEMBLAGE BOUNDARY — ADJOINING R-1 SINGLE-FAMILY '
          'LOT BEYOND (SEE 10/C-8.0)', size=TXT, fill='#2e5e1e')
    for s in (B, A):
        d.chain_h([s['u0'], s['bu0'], s['bu1'], s['u1']], s['porch_face'], off=22,
                  labels=["6'-0\"", "38'-0\" BODY", "6'-0\""])
        d.dimh(s['du0'], s['du1'], s['porch_face'], txt="20'-0\" DRIVEWAY", off=46)
        d.dimh(s['gu0'], s['gu1'], s['porch_face'], txt="21'-0\" GARAGE", off=68)

    # ---- lane annotation
    d.txt(561.0, -9.3, "PRIVATE LANE — 22'-0\" PAVEMENT FACE TO FACE, NO ON-LANE PARKING; "
          "HOA TRACT 35'-11\" TO 46'-1\" WIDE", size=TXT, anchor='start', fill='#fff')
    d.txt(561.0, -11.6, 'SEE SECTIONS 2/C-8.0 AND 3/C-8.0 FOR THE TRACT, CURB, WALK AND PAVEMENT '
          'STRUCTURE', size=TXT, anchor='start', fill='#fff')
    d.txt(566.0, (wlo(566.0) + whi(566.0)) / 2.0 - 0.55, "5'-0\" WALK", size=TXT, anchor='start')
    d.txt(566.0, tr(566.0) + 1.2, 'LANE TRACT LINE = FRONT LOT LINE', size=TXT, anchor='start')

    # ---- tabulation strip below the drawing frame
    lines = ['REAR 20 FT OF EVERY PERIMETER LOT = THE REQUIRED 20-ft REAR YARD AND THE 20-ft '
             'UNDISTURBED BUFFER, COINCIDENT, IN A RECORDED BUFFER EASEMENT — Ord. 2023-603 '
             '§313(1) with Table 4.1. SEE 10/C-8.0.']
    for s2 in (A, B):
        im = s2['imp']
        nm = 'A' if s2 is A else 'B'
        lines.append('PLAN %s — under roof %s · %s · driveway %s · walk %s · TOTAL IMPERVIOUS %s '
                     '(%.1f %% of the lot) · coverage %.1f %% · rearmost element %s from the rear '
                     'line, %s clear of the buffer'
                     % (nm, sf(im['under_roof_sf']),
                        ('patio ' + sf(im['patio_sf'])) if im['patio_sf'] else 'rear porch in roof',
                        sf(im['driveway_sf']), sf(im['entry_walk_sf']), sf(im['total_sf']),
                        100.0 * im['total_sf'] / 5000.0,
                        s2['plan']['lot_siting']['building_coverage_pct'],
                        fti(s2['rv'] - s2['rear_el']), fti(s2['buf_v'] - s2['rear_el'])))
    lines.append('Table 4.1 (R-2) minima: front 15\'-0", side 5\'-0" (6\'-0" provided), rear 20\'-0"; '
                 'garage door 26\'-8" from the front lot line, recessed 5\'-0" (Table 4.2); 50\'-0" of '
                 'frontage on the private street (§319 requires 30 ft). APPEARS CONSISTENT WITH.')
    for i, t in enumerate(lines):
        D.stext(x + 8, y + h - TAB + 12 + i * 11, t, size=TXT, fill='#333')

    north(D, d.x + 62, d.y + 58, flip=True, sub='DETAIL ROTATED 180° — SEE 4/C-8.0')
    d.gscale(16, d.h - 16, 10, 4, anchor_right=True)


# ============================================================================ 2 / 3 — LANE SECTIONS
# Pavement structure — docs/12-outline-specifications.md 32 12 16 2.03, taking Gwinnett County
# UDO 900-70.4.A as the presumptive public-street standard because the Lilburn Development
# Regulations (Code Appendix B) are not retrievable online.
LANE_STRUCT = [('SURFACE COURSE', 1.25, C['asph_s'], '1¼ in — 9.5 mm Superpave Type II (GDOT 828)'),
               ('INTERMEDIATE COURSE', 2.00, C['asph_i'], '2 in — 19 mm Superpave (GDOT 828)'),
               ('GRADED AGGREGATE BASE', 8.00, 'url(#d_gab2)', '8 in — GAB, GDOT 815, 100 % ASTM D698')]
DRIVE_STRUCT = [('CONCRETE', 6.00, 'url(#d_conc)', '6 in — GDOT Class A, 3,500 psi, broom finish'),
                ('GRADED AGGREGATE BASE', 4.00, 'url(#d_gab2)', '4 in — GAB (checklist §7.i minimum)')]
BAY_STRUCT = [('SURFACE COURSE', 2.00, C['asph_s'], '2 in — 9.5 mm Superpave Type II'),
              ('GRADED AGGREGATE BASE', 6.00, 'url(#d_gab2)', '6 in — GAB')]
CURB_W, CURB_H, PAN_W, PAN_T = 0.5, 0.5, 1.5, 0.5     # 24-in curb and gutter, 6-in vertical face
XSLOPE = 0.02


def _pav_y(x):
    return -XSLOPE * abs(x)


def lane_section(D, key, st, num, title, sub, walk_sw):
    x, y, w, h = BOX[key]
    STRIP = 12.0                      # one-line strip under the drawing frame
    half = (w - 20) / (2.0 * S12)
    d = Det(D, x, y, w, h - STRIP, S12, -half, -1.60, num, title, '1/2" = 1\'-0"', sub)
    cl = st['cl']
    tsw, tne = st['tr_sw'] - cl, st['tr_ne'] - cl
    pne, psw = 11.0, -11.0
    wne = (st['w_ne'][0] - cl, st['w_ne'][1] - cl)
    wsw = (st['w_sw'][0] - cl, st['w_sw'][1] - cl) if walk_sw else None
    gab = sum(t for _, t, _, _ in LANE_STRUCT) / 12.0

    # ---- subgrade
    d.poly([(tsw, _pav_y(psw) - gab), (tne, _pav_y(pne) - gab), (tne, -1.56), (tsw, -1.56)],
           fill='url(#d_earth)', stroke='none')
    d.pline([(tsw, _pav_y(psw) - gab), (psw, _pav_y(psw) - gab), (pne, _pav_y(pne) - gab),
             (tne, _pav_y(pne) - gab)], fill='none', stroke='#8a7a5c', stroke_width=1.2)
    # ---- pavement structure
    top = 0.0
    for nm, t, col, _ in LANE_STRUCT:
        bot = top - t / 12.0
        d.poly([(psw, _pav_y(psw) + top), (0.0, top), (pne, _pav_y(pne) + top),
                (pne, _pav_y(pne) + bot), (0.0, bot), (psw, _pav_y(psw) + bot)],
               fill=col, stroke='#222', stroke_width=0.4)
        top = bot
    # ---- 24-in curb and gutter both sides (18-in pan + 6-in vertical face)
    for sgn in (-1, 1):
        e = sgn * 11.0
        p0, p1 = e - sgn * PAN_W, e
        d.poly([(p0, _pav_y(p0)), (p1, _pav_y(p1)), (p1 + sgn * CURB_W, _pav_y(p1) + CURB_H),
                (p1 + sgn * CURB_W, _pav_y(p1) - PAN_T), (p0, _pav_y(p0) - PAN_T)],
               fill='url(#d_conc)', stroke='#333', stroke_width=0.9)
    # ---- verge, sidewalks and ground line out to the tract lines
    y_curb = _pav_y(11.0) + CURB_H
    for sgn, wk, tl in ((1, wne, tne), (-1, wsw, tsw)):
        pts = [(sgn * 11.5, y_curb)]
        pts += ([(wk[0], y_curb + 0.02), (wk[1], y_curb + 0.12), (tl, y_curb + 0.20)] if wk
                else [(tl, y_curb + 0.26)])
        d.poly(pts + [(tl, y_curb - 0.55), (sgn * 11.5, y_curb - 0.55)], fill='url(#d_grass)',
               stroke='none')
        d.pline(pts, fill='none', stroke='#4b6b3a', stroke_width=1.1)
    for wk, sgn in ((wne, 1), (wsw, -1)):
        if not wk:
            continue
        w0, w1 = min(wk), max(wk)
        d.poly([(w0, y_curb + 0.02), (w1, y_curb + 0.12), (w1, y_curb + 0.12 - 0.333),
                (w0, y_curb + 0.02 - 0.333)], fill='url(#d_conc)', stroke='#333', stroke_width=0.9)
        d.txt((w0 + w1) / 2.0, y_curb + 0.30, '5\'-0" WALK, 4 in', size=TXT)
    # ---- centreline, tract lines
    d.D.sline(d.X(0), d.Y(1.55), d.X(0), d.Y(-1.5), stroke='#444', stroke_width=0.7,
              stroke_dasharray='16 3 3 3')
    d.txt(0, 0.50, 'C/L LANE', size=TXT, bold=True)
    for tl, sgn in ((tsw, 1), (tne, -1)):
        d.D.sline(d.X(tl), d.Y(1.60), d.X(tl), d.Y(-1.56), stroke='#111', stroke_width=1.6)
        d.txt(tl + sgn * 0.25, 1.53, 'HOA LANE TRACT LINE = FRONT LOT LINE', size=TXT,
              anchor='start' if sgn > 0 else 'end', bold=True)
    d.txt(-6.0, 0.10, '2 % CROWN', size=TXT, fill='#fff')
    d.txt(6.0, 0.10, '2 % CROWN', size=TXT, fill='#fff')

    # ---- dimensions
    if walk_sw:
        stops = [tsw, wsw[0], wsw[1], psw, pne, wne[0], wne[1], tne]
        labs = [fti(wsw[0] - tsw), '5\'-0"', '2\'-0"',
                '22\'-0" PAVEMENT, FACE OF CURB TO FACE OF CURB', '2\'-0"', '5\'-0"',
                fti(tne - wne[1])]
    else:
        stops = [tsw, psw, pne, wne[0], wne[1], tne]
        labs = [fti(psw - tsw), '22\'-0" PAVEMENT, FACE OF CURB TO FACE OF CURB', '2\'-0"',
                '5\'-0"', fti(tne - wne[1])]
    d.chain_h(stops, 0.45, off=-14, labels=labs)
    d.dimh(tsw, tne, 0.45, off=-36,
           txt='HOA LANE TRACT %s AT STATION u = %d FT — TRACT WIDTH VARIES 35\'-11" TO 46\'-1"'
               % (fti(st['tract_w']), int(st['u'])))
    d.gscale(12, d.h - 14, 2, 6)

    # ---- text strip under the frame
    yy = y + h - STRIP + 11
    D.stext(x + 8, y + h - STRIP + 9,
            'PAVEMENT STRUCTURE 1¼ in 9.5 mm Superpave Type II · 2 in 19 mm Superpave · 8 in GAB · '
            'subgrade 95 % — SEE 5/C-8.0.   PRIVATE STREET: "All components of private streets and '
            'alleys must meet minimum standards for public street" (Checklist §4.s); 15 mph, no '
            'on-lane parking, D103.6 fire-lane signs.   SEE GENERAL NOTES 2, 3 AND 4.',
            size=TXT, fill='#333')
    return d


def d2(D):
    return lane_section(D, 'd2', ST_TYP, 2, 'TYPICAL PRIVATE LANE SECTION',
                        'Station u = 300 ft — sidewalk on the north-east side only; typical of the '
                        'lane from the amenity block (u = 149.5 ft) to u = 530 ft', False)


def d3(D):
    return lane_section(D, 'd3', ST_WID, 3, 'WIDENED PRIVATE LANE SECTION — SIDEWALKS BOTH SIDES',
                        'Station u = 700 ft — typical of the lane from u = 530 ft '
                        '(data/layout.json lane.widen_both_sidewalks_from_u) to the terminus at '
                        'u = 1,701 ft', True)


# ============================================================================ 5 — PAVEMENT SECTIONS
def d5(D):
    x, y, w, h = BOX['d5']
    NOTE = 56.0
    d = Det(D, x, y, w, h - NOTE, S32, -0.20, -1.42, 5, 'PAVEMENT STRUCTURES', '1½" = 1\'-0"',
            'Private lane and turnarounds · residential driveway · guest and mail-kiosk parking bay')
    cols = [(['PRIVATE LANE, TURNAROUNDS', 'AND THE ENTRANCE APRON'], LANE_STRUCT,
             ['1¼ in 9.5 mm SP II', '2 in 19 mm SP', '8 in GAB']),
            (['RESIDENTIAL DRIVEWAY', '(asphalt option 2 in on 4 in)'], DRIVE_STRUCT,
             ['6 in CONCRETE', '4 in GAB']),
            (['GUEST / MAIL-KIOSK BAY', '(pervious pavers an option)'], BAY_STRUCT,
             ['2 in 9.5 mm SP II', '6 in GAB'])]
    pitch, cw = 1.24, 1.10
    for k, (title, struct, labs) in enumerate(cols):
        x0 = k * pitch
        d.txt(x0 + cw / 2.0, 0.28, title[0], size=TXT, bold=True)
        d.txt(x0 + cw / 2.0, 0.185, title[1], size=TXT)
        top = 0.0
        for (nm, t, col, _), lab in zip(struct, labs):
            bot = top - t / 12.0
            d.rect(x0, top, x0 + cw, bot, fill=col, stroke='#222', stroke_width=0.7)
            d.txt(x0 + cw / 2.0, (top + bot) / 2.0 - 0.026, lab, size=TXT,
                  fill='#fff' if t <= 2.0 else '#111')
            if t >= 4.0:
                d.dimv(top, bot, x0, txt=inch(t), off=-11, size=TXT)
            top = bot
        d.rect(x0, top, x0 + cw, top - 0.17, fill='url(#d_earth)', stroke='none')
        d.pline([(x0, top), (x0 + cw, top)], fill='none', stroke='#8a7a5c', stroke_width=1.3)
        d.txt(x0 + cw / 2.0, top - 0.115, 'COMPACTED SUBGRADE', size=TXT)
    d.txt(1.79, -1.24, 'SP = Superpave (GDOT 828) · GAB = graded aggregate base (GDOT 815, '
          '100 % ASTM D698)', size=TXT)
    d.txt(1.79, -1.32, 'concrete = GDOT Class A, 3,500 psi, broom finish · subgrade 95 % '
          '(top 12 in 100 %) of max. dry density', size=TXT)
    d.gscale(8, 12, 0.5, 2, unit='ft', anchor_right=True)
    D.stextblock(x + 8, y + h - NOTE + 11,
                 'BASIS: Checklist §7.i (minimum 4 in GAB and 2 in Type E or F) and §4.t; Gwinnett '
                 'County UDO §900-70.4.A taken as the presumptive public-street standard under §4.s; '
                 'GDOT Standard Specifications 2021 §310, §400, §815, §828. The Lilburn Development '
                 'Regulations are not retrievable online — VERIFY the required section. The lane '
                 'shall carry a 75,000-lb apparatus (IFC 2024 (GA) D102.1); a geotechnical pavement '
                 'design by the PE governs.', size=TXT, chars=86, lead=10.4, fill='#333')


# ============================================================================ 6 — ACCESSIBLE SPACE
ACC_W = max(p[0] for p in AMEN['accessible_stall']) - min(p[0] for p in AMEN['accessible_stall'])
AIS_W = max(p[0] for p in AMEN['accessible_aisle']) - min(p[0] for p in AMEN['accessible_aisle'])
ACC_D = max(p[1] for p in AMEN['accessible_stall']) - min(p[1] for p in AMEN['accessible_stall'])
STD_W = (max(p[0] for p in AMEN['kiosk_stalls'][0])
         - min(p[0] for p in AMEN['kiosk_stalls'][0]))


def _isa(d, cx, cy, s, col='#fff'):
    """Painted International Symbol of Accessibility, s = overall height in feet."""
    d.circ((cx, cy + s * 0.40), s * 0.10, fill=col, stroke='none')
    d.poly([(cx - s * 0.09, cy + s * 0.30), (cx + s * 0.05, cy + s * 0.30),
            (cx + s * 0.22, cy + s * 0.14), (cx + s * 0.15, cy + s * 0.05),
            (cx + s * 0.03, cy + s * 0.16), (cx + s * 0.03, cy - s * 0.02),
            (cx - s * 0.09, cy - s * 0.02)], fill=col, stroke='none')
    d.arc((cx - s * 0.02, cy - s * 0.16), s * 0.20, 200, 20, stroke=col, stroke_width=2.0)
    d.poly([(cx + s * 0.16, cy - s * 0.10), (cx + s * 0.26, cy - s * 0.24),
            (cx + s * 0.18, cy - s * 0.29), (cx + s * 0.09, cy - s * 0.15)], fill=col,
           stroke='none')


def _stripes(d, x0, x1, y0, y1, n=9, col='#fff'):
    """45-degree hatching clipped to the rectangle — the ADA 502.3.3 aisle marking."""
    span = (x1 - x0) + (y1 - y0)
    for i in range(1, n + 1):
        c = x0 - (y1 - y0) + span * i / float(n + 1)
        pts = []
        for xx, yy in ((c, y0), (c + (y1 - y0), y1)):
            pts.append((xx, yy))
        (ax, ay), (bx, by) = pts
        if bx <= x0 or ax >= x1:
            continue
        if ax < x0:
            ay += (x0 - ax)
            ax = x0
        if bx > x1:
            by -= (bx - x1)
            bx = x1
        d.line((ax, ay), (bx, by), stroke=col, stroke_width=1.1)


def d6(D):
    x, y, w, h = BOX['d6']
    NOTE = 84.0
    Det(D, x, y, w, h, 1.0, 0, 0, 6, 'ACCESSIBLE SPACE AND SIGN',
        'plan 3/16" = 1\'-0"; sign 3/8" = 1\'-0"',
        'One van-accessible space and its 8\'-0" aisle in the mail-kiosk bay — data/layout.json '
        'amenity.accessible_stall / accessible_aisle')
    ph = h - HEAD - NOTE - 8
    p = Det(D, x + 6, y + HEAD + 4, 336, ph, S316, -1.5, -2.3, box=False)
    dep = ACC_D
    p.rect(-1.5, -2.3, 22.6, 20.0, fill='#fff', stroke='none')
    p.rect(-1.5, -2.3, 22.6, dep, fill=C['asph_s'], stroke='none')
    p.rect(-1.5, dep, 22.6, dep + 0.4, fill='url(#d_conc)', stroke='#333', stroke_width=0.8)
    p.rect(-1.5, dep + 0.4, 22.6, dep + 1.7, fill='url(#d_conc)', stroke='#333', stroke_width=0.8)
    p.txt(9.5, dep + 0.85, '5\'-0" WALK — ACCESSIBLE ROUTE TO THE MAIL KIOSK (§208.3.1)',
          size=TXT)
    p.rect(0.0, 0.0, ACC_W, dep, fill=C['asph_s'], stroke='#fff', stroke_width=1.8)
    p.rect(ACC_W, 0.0, ACC_W + AIS_W, dep, fill='#2f4a66', stroke='#fff', stroke_width=1.8)
    p.rect(ACC_W + AIS_W, 0.0, ACC_W + AIS_W + 5.0, dep, fill=C['asph_s'], stroke='#fff',
           stroke_width=1.8)
    _stripes(p, ACC_W + 0.35, ACC_W + AIS_W - 0.35, 0.35, dep - 0.35, n=8)
    _isa(p, ACC_W / 2.0, dep / 2.0 + 1.8, 7.5)
    p.txt(ACC_W / 2.0, 1.4, 'VAN', size=TXT, fill='#fff', bold=True)
    p.txt(ACC_W + AIS_W / 2.0, dep / 2.0 + 0.6, 'NO', size=TXT, fill='#fff', bold=True)
    p.txt(ACC_W + AIS_W / 2.0, dep / 2.0 - 0.9, 'PARKING', size=TXT, fill='#fff', bold=True)
    p.txt(ACC_W + AIS_W + 2.5, dep / 2.0 + 0.6, 'STANDARD', size=TXT, fill='#fff')
    p.txt(ACC_W + AIS_W + 2.5, dep / 2.0 - 0.9, '9\'-0" × 18\'-0"', size=TXT, fill='#fff')
    p.chain_h([0.0, ACC_W, ACC_W + AIS_W, ACC_W + AIS_W + 5.0], 0.0, off=14,
              labels=['8\'-0" VAN SPACE', '8\'-0" AISLE', '9\'-0"'])
    p.dimv(0.0, dep, 0.0, txt='18\'-0"', off=-14)
    p.txt(11.0, -2.2, 'DRIVE AISLE — 22\'-0" LANE PAVEMENT', size=TXT, fill='#fff')
    p.txt(-1.4, -2.25, 'PLAN', size=11, bold=True, anchor='start', fill='#fff')

    e = Det(D, x + 352, y + HEAD + 4, 142, ph, S38, -0.9, -1.6, box=False)
    e.rect(-0.9, -1.6, 4.4, 0.0, fill='url(#d_earth)', stroke='none')
    e.line((-0.9, 0.0), (4.4, 0.0), stroke='#5a4a30', stroke_width=1.4)
    e.rect(1.55, 0.0, 1.95, 7.5, fill='#8a8a8a', stroke='#333', stroke_width=0.7)
    e.rect(0.75, 5.0, 2.75, 7.5, fill='#1b5fa8', stroke='#111', stroke_width=1.0)
    _isa(e, 1.75, 6.25, 2.1)
    e.rect(0.75, 3.9, 2.75, 5.0, fill='#fff', stroke='#111', stroke_width=1.0)
    e.txt(1.75, 4.30, 'VAN ACCESSIBLE', size=TXT, bold=True)
    e.dimv(0.0, 3.9, 3.3, txt='5\'-0" MIN.', off=13)
    e.dimv(0.0, 7.5, -0.55, txt='7\'-6"', off=-12)
    e.txt(1.75, 8.6, 'SIGN', size=11, bold=True)
    e.txt(1.75, -1.25, 'CONCRETE FOOTING', size=TXT)

    yy = y + h - NOTE + 10
    for t in ['2010 ADA Standards §208.2 — 1 accessible space where 1 to 25 are provided; 12 guest '
              'and kiosk spaces are provided, so 1 is required and 1 is shown. §502.2 — a 96-in '
              'space with a 96-in aisle IS a van-accessible space (8\'-0" + 8\'-0" as drawn). '
              '§502.3 — the aisle runs the full length of the space, marked to discourage parking. '
              '§502.4 — space and aisle ≤ 1:48 in all directions (a PE grading item). §502.6 — sign '
              'with the ISA and a "VAN ACCESSIBLE" designation, bottom ≥ 60 in above the '
              'surface; O.C.G.A. §40-6-226 requires it. Checklist §4.x: the count is "calculated by '
              'Gwinnett Fire Marshal" — VERIFY. §4.w — standard spaces '
              '9\'-0" × 18\'-0".']:
        yy = D.stextblock(x + 8, yy, t, size=TXT, chars=101, lead=10.4, fill='#333')


# ============================================================================ 7 — MONUMENT SIGN
SG_LEN, SG_W = 8.0, 4.0                 # amenity.entry_sign footprint, data/layout.json
SG_H, SG_CAP, SG_TH, SG_WING, SG_FTG = 3.75, 0.33, 1.33, 1.33, 1.5
SG_PANEL = (6.0, 1.75)
SG_FACE_SF = SG_LEN * SG_H
SG_PANEL_SF = SG_PANEL[0] * SG_PANEL[1]
SG_MAX_SF, SG_MAX_H = 32.0, 6.0


def d7(D):
    x, y, w, h = BOX['d7']
    NOTE = 66.0
    Det(D, x, y, w, h, 1.0, 0, 0, 7, 'MONUMENT ENTRY SIGN', '1/2" = 1\'-0"',
        'The only sign proposed in the development — footprint from data/layout.json '
        'amenity.entry_sign. NO WALL SIGNS ARE PROPOSED ON ANY STRUCTURE.')
    e = Det(D, x + 6, y + HEAD + 4, 344, 210, S12, -0.75, -1.85, box=False)
    e.rect(-0.75, -1.85, 8.85, 0.0, fill='url(#d_earth)', stroke='none')
    e.line((-0.75, 0.0), (8.85, 0.0), stroke='#5a4a30', stroke_width=1.5)
    e.rect(0.0, -SG_FTG, SG_LEN, -0.1, fill='url(#d_conc)', stroke='#333', stroke_width=0.8)
    e.rect(0.0, 0.0, SG_LEN, SG_H - SG_CAP, fill='url(#d_mas)', stroke='#111', stroke_width=1.2)
    e.rect(-0.2, SG_H - SG_CAP, SG_LEN + 0.2, SG_H, fill='#ded3c2', stroke='#111',
           stroke_width=1.2)
    px0 = (SG_LEN - SG_PANEL[0]) / 2.0
    e.rect(px0, 0.85, px0 + SG_PANEL[0], 0.85 + SG_PANEL[1], fill='#ded3c2', stroke='#111',
           stroke_width=1.0)
    e.txt(SG_LEN / 2.0, 1.90, 'THE COTTAGES', size=11.5, bold=True)
    e.txt(SG_LEN / 2.0, 1.20, 'AT ARCADO SPRINGS', size=9.5, bold=True)
    e.dimh(0.0, SG_LEN, SG_H, txt='8\'-0"', off=-11)
    e.dimv(0.0, SG_H, SG_LEN, txt='3\'-9"', off=16)
    e.dimv(-SG_FTG, 0.0, 0.0, txt='1\'-6"', off=-13)
    e.dimh(px0, px0 + SG_PANEL[0], 0.85, txt='6\'-0"', off=17)
    e.dimv(0.85, 0.85 + SG_PANEL[1], px0, txt='1\'-9"', off=-13)
    e.txt(SG_LEN / 2.0, -0.95, 'CONCRETE FOOTING — PE DESIGN', size=TXT)
    e.txt(-0.70, -1.72, 'ELEVATION', size=11, bold=True, anchor='start')
    e.gscale(6, 190, 2, 3, anchor_right=True)

    p = Det(D, x + 6, y + HEAD + 220, 344, 169, S12, -0.75, -0.86, box=False)
    p.rect(-0.75, -0.86, 8.85, 3.95, fill='url(#d_grass)', stroke='none')
    p.rect(0.0, (SG_W - SG_TH) / 2.0, SG_LEN, (SG_W + SG_TH) / 2.0, fill='url(#d_mas)',
           stroke='#111', stroke_width=1.2)
    for xx in (0.0, SG_LEN - SG_TH):
        p.rect(xx, 0.0, xx + SG_TH, SG_W, fill='url(#d_mas)', stroke='#111', stroke_width=1.2)
    p.dimh(0.0, SG_LEN, 0.0, txt='8\'-0"', off=14)
    p.dimv(0.0, SG_W, SG_LEN, txt='4\'-0"', off=15)
    p.dimv((SG_W - SG_TH) / 2.0, (SG_W + SG_TH) / 2.0, 2.4, txt='1\'-4"', off=-12)
    p.txt(SG_LEN / 2.0, -0.76, 'PLAN — SIGN FACE ON BOTH SIDES OF THE WALL', size=11,
          bold=True)

    D.stext(x + 8, y + h - NOTE + 10, 'AREA COMPUTATION', size=10.5, bold=True)
    D.stextblock(x + 8, y + h - NOTE + 21,
                 'WHOLE STRUCTURE FACE (most conservative): 8\'-0" × 3\'-9" = %.1f SF ≤ %.0f SF · '
                 'SIGN PANEL ONLY 6\'-0" × 1\'-9" = %.1f SF · OVERALL HEIGHT 3\'-9" ≤ 6\'-0" · 19.0 ft '
                 'from the Arcado Rd R/W, outside the 390-ft sight triangle (C-2.3). The 32-SF and '
                 '6-ft limits are the applicant\'s voluntary condition, not a cited ordinance limit '
                 '— the Lilburn sign article is not in data/ordinance-excerpts.md; VERIFY. See '
                 'general note 8.' % (SG_FACE_SF, SG_MAX_SF, SG_PANEL_SF),
                 size=TXT, chars=101, lead=10.4, fill='#333')


# ============================================================================ 8 — MAIL KIOSK
K_L = max(p[0] for p in AMEN['mail_kiosk']) - min(p[0] for p in AMEN['mail_kiosk'])   # 16'-0"
K_W = max(p[1] for p in AMEN['mail_kiosk']) - min(p[1] for p in AMEN['mail_kiosk'])   # 10'-0"
K_CBU, K_COMP, K_PARCEL = 3, 16, 2
K_PLATE, K_HEEL, K_OH, K_SLAB = 8.83, 0.42, 1.0, 0.33
K_RIDGE = K_SLAB + K_PLATE + K_HEEL + ((K_W + 2 * K_OH) / 2.0) * 4.0 / 12.0


S18 = 9.0                                     # 1/8" = 1'-0"


def d8(D):
    x, y, w, h = BOX['d8']
    Det(D, x, y, w, h, 1.0, 0, 0, 8, 'MAIL KIOSK — CLUSTER BOX UNITS', '1/8" = 1\'-0"',
        'Footprint from data/layout.json amenity.mail_kiosk — %s × %s; weather protection per '
        'Checklist §4.r' % (fti(K_L), fti(K_W)))
    p = Det(D, x + 6, y + HEAD + 4, 160, 116, S18, -0.9, -1.9, box=False)
    p.rect(-0.9, -1.9, 17.0, 11.6, fill='#fff', stroke='none')
    p.rect(-0.8, -0.8, K_L + 0.9, K_W + 1.0, fill='url(#d_conc)', stroke='none')
    p.rect(-K_OH, -K_OH, K_L + K_OH, K_W + K_OH, fill='none', stroke='#777', stroke_width=0.7,
           stroke_dasharray='7 3')
    p.rect(0.0, 0.0, K_L, K_W, fill='#fdf3e4', stroke='#111', stroke_width=1.5)
    p.rect(0.0, K_W - 0.67, K_L, K_W, fill='url(#d_mas)', stroke='#111', stroke_width=1.0)
    for i2 in range(K_CBU):
        x0 = 2.4 + i2 * 3.9
        p.rect(x0, K_W - 2.4, x0 + 2.5, K_W - 0.67, fill='#cfd6dc', stroke='#111',
               stroke_width=0.9)
    for xx in (0.0, K_L - 0.9):
        for yy2 in (0.0, K_W - 0.9):
            p.rect(xx, yy2, xx + 0.9, yy2 + 0.9, fill='url(#d_mas)', stroke='#111',
                   stroke_width=0.9)
    p.dimh(0.0, K_L, 0.0, txt=fti(K_L), off=14)
    p.dimv(0.0, K_W, K_L, txt=fti(K_W), off=13)
    p.txt(K_L / 2.0, 3.2, '5\'-0" CLEAR APPROACH', size=TXT)
    p.txt(K_L / 2.0, 1.5, 'OPEN TO THE LANE', size=TXT)
    p.txt(0.0, -1.7, 'PLAN (ROOF DASHED)', size=10.5, bold=True, anchor='start')
    p.gscale(4, 6, 4, 4, anchor_right=True)

    e = Det(D, x + 6, y + HEAD + 126, 160, 134, S18, -0.9, -2.0, box=False)
    e.rect(-0.9, -2.0, 17.0, 0.0, fill='url(#d_earth)', stroke='none')
    e.line((-0.9, 0.0), (K_L + 0.9, 0.0), stroke='#5a4a30', stroke_width=1.5)
    e.rect(-0.4, 0.0, K_L + 0.4, K_SLAB, fill='url(#d_conc)', stroke='#333', stroke_width=0.9)
    ep = K_SLAB + K_PLATE
    e.poly([(-K_OH, ep + K_HEEL), (K_L / 2.0, K_RIDGE), (K_L + K_OH, ep + K_HEEL),
            (K_L + K_OH, ep), (-K_OH, ep)], fill='#8d7f6c', stroke='#111', stroke_width=1.2)
    for xx in (0.6, K_L - 1.4):
        e.rect(xx, K_SLAB, xx + 0.8, ep, fill='url(#d_mas)', stroke='#111', stroke_width=1.1)
    for i2 in range(K_CBU):
        x0 = 2.4 + i2 * 3.9
        e.rect(x0, K_SLAB + 1.25, x0 + 2.5, K_SLAB + 5.0, fill='#cfd6dc', stroke='#111',
               stroke_width=1.1)
    e.dimv(0.0, K_RIDGE, -0.5, txt=fti(K_RIDGE), off=-12)
    e.txt(K_L / 2.0, ep + 1.5, '4:12 HIP ROOF', size=TXT)
    e.txt(0.0, -1.75, 'FRONT (SOUTH-WEST) ELEVATION', size=10.5, bold=True, anchor='start')

    yy = y + HEAD + 8
    for t in ['%d USPS-approved cluster box units = %d tenant' % (K_CBU, K_CBU * K_COMP),
              'compartments + %d parcel lockers (VERIFY the' % (K_CBU * K_PARCEL),
              'approved model with USPS)', '',
              'Roofed, three-sided shelter open to the lane;',
              'masonry piers and water table matching the',
              'cottages; ridge %s above finished grade' % fti(K_RIDGE), '',
              '6-in concrete pad, 5\'-0" clear approach,', 'flush with the walk (no step)', '',
              'Four 9\'-0" × 18\'-0" short-term stalls in the',
              'kiosk bay, plus the van-accessible space',
              'of 6/C-8.0 on the accessible route', '',
              'Operable parts of every CBU between 15 in',
              'and 48 in above the slab; 36-in clear route',
              'and a 5-ft turning space (ICC A117.1-2017)', '',
              'MAIL DELIVERY — SEE GENERAL NOTE 9',
              '(Checklist §4.r: contact the Lilburn Post',
              'Office Growth Manager; "provide accessory',
              'structure details with protection from the',
              'elements")']:
        D.stext(x + 176, yy, t, size=TXT, fill='#333')
        yy += 10.4


# ============================================================================ 9 — TREE PROTECTION
def d9(D):
    x, y, w, h = BOX['d9']
    NOTE = 46.0
    d = Det(D, x, y, w, h - NOTE, 18.0, -1.4, -2.7, 9, 'TREE-PROTECTION FENCE', '1/4" = 1\'-0"',
            'At the limits of disturbance, the buffer line and the drip line of every retained tree')
    d.rect(-1.4, -2.7, 24.0, 0.0, fill='url(#d_earth)', stroke='none')
    d.line((-1.4, 0.0), (24.0, 0.0), stroke='#5a4a30', stroke_width=1.6)
    for px in (1.0, 9.0):
        d.rect(px - 0.16, -2.0, px + 0.16, 6.0, fill='#8a8a8a', stroke='#222', stroke_width=0.6)
    d.rect(1.0, 0.0, 9.0, 4.0, fill='#d2691e', fill_opacity='0.28', stroke='#d2691e',
           stroke_width=1.2)
    for i2 in range(9):
        d.line((1.0 + i2, 0.0), (1.0 + i2, 4.0), stroke='#d2691e', stroke_width=0.7)
    for j2 in range(5):
        d.line((1.0, j2), (9.0, j2), stroke='#d2691e', stroke_width=0.7)
    d.rect(2.9, 4.4, 7.1, 5.7, fill='#fff', stroke='#111', stroke_width=1.0)
    d.txt(5.0, 5.15, 'TREE PROTECTION AREA', size=TXT, bold=True)
    d.txt(5.0, 4.62, 'DO NOT ENTER', size=TXT, bold=True)
    d.rect(9.6, 0.0, 12.6, 0.33, fill='url(#d_mulch)', stroke='#9c8465', stroke_width=0.5)
    _tree(d, 14.8, 0.0, 6.4, 5.6)
    d.line((11.9, 0.0), (11.9, 6.4), stroke='#3f7a37', stroke_width=0.8, stroke_dasharray='5 3')
    d.dimh(9.0, 11.9, 0.0, txt='AT THE DRIP LINE', off=15)
    d.dimv(0.0, 6.0, 0.5, txt='6\'-0" POST', off=-12)
    d.dimv(0.0, 4.0, 9.1, txt='4\'-0"', off=12)
    d.dimv(-2.0, 0.0, 1.0, txt='2\'-0"', off=-12)
    d.dimh(1.0, 9.0, 6.0, txt='8\'-0" O.C. MAX.', off=-13)
    d.txt(19.2, 5.8, 'RETAINED TREE', size=TXT)
    d.txt(12.9, 0.95, '4-in MULCH', size=TXT, anchor='start')
    d.txt(19.2, 3.9, 'NO STORAGE, PARKING,', size=TXT)
    d.txt(19.2, 2.9, 'GRADE CHANGE,', size=TXT)
    d.txt(19.2, 1.9, 'TRENCHING OR', size=TXT)
    d.txt(0.0, 7.1, '4\'-0" ORANGE SAFETY FENCE ON 6-ft STEEL T-POSTS', size=TXT,
          anchor='start')
    d.txt(19.2, 0.9, 'SPOIL INSIDE THE FENCE', size=TXT)
    D.stextblock(x + 8, y + h - NOTE + 11,
                 'REQUIRED NOTE (Checklist §6.g, verbatim): "Tree Protection fence must be '
                 'installed prior to commencing land disturbing activities." A reasonable effort '
                 'must be made to preserve specimen trees and trees over 5-in caliper in buffers, '
                 'landscape strips and parking islands. The tree-protection, buffer and landscape '
                 'plan must be sealed by a registered landscape architect, forester or arborist '
                 '(§6.a) — Sheet C-7.0.', size=TXT, chars=86, lead=10.4, fill='#333')


# ============================================================================ 4 — HAMMERHEAD
HH = LAYOUT['hammerheads'][1]                 # u = 1,110 ft — the middle turnaround, typical of 3
HH_STA = [594.5, 1164.5, 1744.5]              # stations along the travelled way (docs/08 Memo E)
RET_R = 25.0                                  # curb-return radius at the turnaround legs


def fillet(d, px, py, cx, cy, r, **kw):
    """Curb-return wedge: the square corner at (px, py) less the quarter circle of radius r."""
    a_h = 90.0 if py > cy else 270.0
    a_v = 0.0 if px > cx else 180.0
    if a_v - a_h > 180.0:
        a_v -= 360.0
    elif a_v - a_h < -180.0:
        a_v += 360.0
    n = 18
    arc = [(cx + r * math.cos(math.radians(a_h + (a_v - a_h) * i / n)),
            cy + r * math.sin(math.radians(a_h + (a_v - a_h) * i / n))) for i in range(n + 1)]
    d.poly([(px, py), (cx, py)] + arc + [(px, cy)], **kw)
    d.pline(arc, fill='none', stroke='#222', stroke_width=1.1)


def d4(D):
    x, y, w, h = BOX['d4']
    d = Det(D, x, y, w, h, S20, 1030.0, -191.0, 4, 'HAMMERHEAD TURNAROUND', '1" = 20\'',
            'Turnaround at u = 1,110 ft (station 1,164.5 ft on the travelled way) — typical of the '
            'three; legs and pavement from data/layout.json hammerheads[1]')
    u0, u1 = 1030.0, 1190.0
    psw = lambda u: interp(_PV_SW, u)                                                # noqa: E731
    pne = lambda u: interp(_PV_NE, u)                                                # noqa: E731
    tsw = lambda u: interp(_TR_SW, u)                                                # noqa: E731
    tne = lambda u: interp(_TR_NE, u)                                                # noqa: E731
    lg0, lg1 = HH['legs'][0], HH['legs'][1]
    a0, a1 = min(p[0] for p in lg0), max(p[0] for p in lg0)
    sw_end = min(p[1] for p in lg0)
    ne_end = max(p[1] for p in lg1)

    d.poly(band(tsw, tne, u0, u1), fill='none', stroke=C['lot'], stroke_width=1.4)
    d.poly(band(psw, pne, u0, u1), fill=C['asph_s'], stroke='none')
    for lg in (lg0, lg1):
        d.poly(lg, fill=C['asph_s'], stroke='none')
    for (px, py, cx, cy) in ((a0, psw(a0), a0 - RET_R, psw(a0) - RET_R),
                             (a1, psw(a1), a1 + RET_R, psw(a1) - RET_R),
                             (a0, pne(a0), a0 - RET_R, pne(a0) + RET_R),
                             (a1, pne(a1), a1 + RET_R, pne(a1) + RET_R)):
        fillet(d, px, py, cx, cy, RET_R, fill=C['asph_s'], stroke='none')
    for f in (psw, pne):
        d.pline([(u, f(u)) for u in (u0, a0 - RET_R)], fill='none', stroke='#222',
                stroke_width=1.2)
        d.pline([(u, f(u)) for u in (a1 + RET_R, u1)], fill='none', stroke='#222',
                stroke_width=1.2)
    for lg, f in ((lg0, psw), (lg1, pne)):
        far = min(p[1] for p in lg) if f is psw else max(p[1] for p in lg)
        d.pline([(a0, f(a0)), (a0, far), (a1, far), (a1, f(a1))], fill='none', stroke='#222',
                stroke_width=1.2)
    d.pline([(u0, (psw(u0) + pne(u0)) / 2.0), (u1, (psw(u1) + pne(u1)) / 2.0)], fill='none',
            stroke='#eee', stroke_width=0.9, stroke_dasharray='14 8')

    d.dimv(sw_end, psw(a0), a0, txt="60'-0\"", off=-20)
    d.dimv(pne(a0), ne_end, a0, txt="60'-0\"", off=-20)
    d.dimv(sw_end, ne_end, a0, txt="142'-0\" OVERALL", off=-48, force_out=True)
    d.dimh(a0, a1, ne_end, txt="20'-0\"", off=-18)
    for (px, py, sx, sy) in ((a0, psw(a0), -1, -1), (a1, pne(a1), 1, 1)):
        d.txt(px + sx * 21, py + sy * 11, "R = 25'-0\"", size=TXT, fill=C['dim'], bold=True)
    d.txt(a0 - 36, psw(a0) - 34, 'CURB RETURN (TYP. 4)', size=TXT, fill=C['dim'])

    d.txt(1152.0, -110.0, 'HAMMERHEAD (T) TURNAROUND — TYPICAL OF THREE', size=TXT, bold=True,
          fill='#fff')
    d.txt(1152.0, -119.0, "22'-0\" PRIVATE LANE — NO ON-LANE PARKING", size=TXT, fill='#fff')
    d.txts(1128.0, -46.0, ['HYDRANT AT THE TURNAROUND LEG: the lane is',
                           'locally 142 ft wide here, so the 26-ft width',
                           'that Appendix D103.1 asks for where a hydrant',
                           'stands on the access road is met at the hydrant'],
           size=TXT, anchor='start')
    d.circ((1112.0, -66.0), 1.8, fill=C['fire'], stroke='#fff', stroke_width=0.7)
    d.line((1113.5, -66.0), (1126.0, -66.0), stroke='#333', stroke_width=0.6)
    d.txt(1128.0, -67.0, 'PROPOSED HYDRANT', size=TXT, anchor='start')
    d.txts(1128.0, -150.0, ['"NO PARKING — FIRE LANE" SIGNS BOTH SIDES',
                            'of the lane and both legs (Appendix D103.6),',
                            'with an HOA covenant prohibiting on-lane',
                            'parking; 4 spaces are provided on every lot',
                            'and 12 in the guest and mail-kiosk bays'],
           size=TXT, anchor='start')
    d.txt(1170.0, tne(1170.0) + 4.5, 'HOA LANE TRACT', size=TXT, anchor='middle')
    d.txt(1048.0, tsw(1048.0) - 5.5, 'HOA LANE TRACT', size=TXT, anchor='middle')
    d.txt(1036.0, -166.0, 'DEAD END 1,754 ft → SPECIAL APPROVAL', size=TXT, anchor='start',
          bold=True)
    d.txt(1036.0, -170.5, 'REQUIRED, Table D103.4 (IFC 2024 as', size=TXT, anchor='start')
    d.txt(1036.0, -175.0, 'modified by 120-3-3-.04) — SEE NOTE 6', size=TXT, anchor='start')
    north(D, d.x + 92, d.y + 54, r=21)
    d.gscale(14, d.h - 16, 20, 4)
    return d


# ============================================================================ 10 — BUFFER SECTION
def _tree(d, x, g, hgt, spread, col=C['tree'], trunk='#6b4c2a', ever=False):
    d.line((x, g), (x, g + hgt * 0.42), stroke=trunk, stroke_width=1.7)
    if ever:
        for i in range(4):
            f = 1.0 - i * 0.22
            yb = g + hgt * (0.20 + 0.19 * i)
            d.poly([(x, yb + hgt * 0.32 * f), (x - spread / 2.0 * f, yb),
                    (x + spread / 2.0 * f, yb)], fill=col, fill_opacity='0.50', stroke=col,
                   stroke_width=0.6)
    else:
        d.circ((x, g + hgt * 0.70), spread / 2.0, fill=col, fill_opacity='0.28', stroke=col,
               stroke_width=0.9)


def d10(D):
    x, y, w, h = BOX['d10']
    NOTE = 46.0
    d = Det(D, x, y, w, h - NOTE, S10, 0.0, -5.6, 10, 'TYPICAL BUFFER SECTION',
            '1" = 10\' (no exaggeration)',
            'The §313(1) design basis in one picture — the 20-ft undisturbed buffer held inside the '
            'rear of the lot under a recorded easement')
    RL, BF = 15.0, 35.0
    rear_el, body_r = BF + 0.5, BF + 6.5
    g = 0.0
    d.rect(0.0, g, 79.0, -5.6, fill='url(#d_earth)', stroke='none')
    d.rect(0.0, g, 79.0, g + 0.55, fill='url(#d_grass)', stroke='none')
    d.rect(RL, g, BF, g + 26.0, fill='url(#bufhatch)', fill_opacity='0.75', stroke='none')
    d.line((0.0, g), (79.0, g), stroke='#5a4a30', stroke_width=1.7)

    d.poly([(0.0, g), (0.0, g + 17.5), (5.0, g + 21.0), (10.0, g + 17.5), (10.0, g)],
           fill='#efe7dc', stroke='#7a6a55', stroke_width=1.1)
    d.txt(5.2, g + 10.5, 'ADJOINING', size=TXT)
    d.txt(5.2, g + 8.3, 'R-1 DWELLING', size=TXT)

    for xx, hgt, sp in ((17.5, 21.0, 12.0), (26.0, 23.5, 14.0), (33.0, 19.5, 11.0)):
        _tree(d, xx, g, hgt, sp)
    for xx in (20.5, 23.5, 30.0):
        _tree(d, xx, g, 10.0, 6.0, col='#2f6b46', ever=True)
    _tree(d, 6.5, g, 16.5, 9.5)

    ffe = g + 0.67
    d.rect(rear_el, ffe, body_r, ffe + 9.5, fill='#fdf3e4', stroke='#111', stroke_width=1.0)
    d.poly([(body_r, ffe), (body_r, ffe + 9.5), (73.0, ffe + 9.5), (73.0, ffe)],
           fill=C['house'], stroke='#111', stroke_width=1.4)
    d.poly([(rear_el - 1.0, ffe + 9.2), (54.0, ffe + 17.83), (73.0, ffe + 9.2)],
           fill='#8d7f6c', stroke='#111', stroke_width=1.2)
    d.pline([(72.0, ffe + 12.0), (73.4, ffe + 10.6), (72.0, ffe + 9.2), (73.4, ffe + 7.8),
             (72.0, ffe + 6.4), (73.4, ffe + 5.0), (72.0, ffe + 3.6), (73.4, ffe + 2.2),
             (72.0, ffe + 0.8), (73.0, ffe - 0.2)], fill='none', stroke='#777', stroke_width=1.1)
    d.txt((rear_el + body_r) / 2.0, ffe + 5.0, 'REAR', size=TXT)
    d.txt((rear_el + body_r) / 2.0, ffe + 2.8, 'PORCH', size=TXT)
    d.txt(57.0, ffe + 6.2, 'ONE-STORY COTTAGE', size=TXT)
    d.txt(57.0, ffe + 4.0, 'RIDGE 17\'-10" (PLAN A) /', size=TXT)
    d.txt(57.0, ffe + 1.8, '19\'-0" (PLAN B) ABOVE FFE', size=TXT)

    d.line((RL, -5.2), (RL, g + 25.0), stroke='#111', stroke_width=1.6)
    d.line((BF, -5.2), (BF, g + 25.0), stroke='#2e5e1e', stroke_width=1.6)
    d.txt(RL, g + 27.4, 'REAR LOT LINE = ASSEMBLAGE BOUNDARY', size=TXT)
    d.txt(RL, g + 25.4, '= R-2 / R-1 ZONING LINE', size=TXT)
    d.txt(BF + 1.5, g + 27.4, 'BUFFER EASEMENT LINE =', size=TXT, anchor='start', fill='#2e5e1e')
    d.txt(BF + 1.5, g + 25.4, '20-ft REAR BUILDING SETBACK', size=TXT, anchor='start',
          fill='#2e5e1e')
    d.dimh(RL, BF, -0.7, txt='20\'-0" UNDISTURBED BUFFER', off=15)
    d.dimh(RL, rear_el, -0.7, txt='20\'-6" TO THE NEAREST STRUCTURE', off=32)
    d.dimh(0.0, RL, -0.7, txt='ADJOINING R-1 LOT', off=15)
    D.srect(d.X(15.6), d.Y(2.5), d.X(34.4) - d.X(15.6), 12.0, fill='#fff', fill_opacity='0.85',
            stroke='none')
    d.txt(25.0, g + 1.6, 'NO CLEARING · NO GRADING · NO STRUCTURES · NO STORAGE', size=TXT,
          fill='#2e5e1e', bold=True)
    d.gscale(12, 12, 10, 2, anchor_right=True)

    D.stextblock(x + 8, y + h - NOTE + 11,
                 'Cottage homes are listed separately from detached single-family in Table 4.1, '
                 'so the plan designs to the 20-ft buffer. §313(1): "Buffer requirements … '
                 'supersede these minimum required yards" — %s SF of buffer easement over %d lots, '
                 'reported separately from the %s SF of common open space. 100\'-0" + 35\'-11" of '
                 'tract + 100\'-0" = 235\'-11" against 235\'-11" available at u = 230 ft.'
                 % (format(MET['buffer_easement_on_lots_sf'], ','), MET['lots'],
                    format(MET['open_space_sf'], ',')),
                 size=TXT, chars=131, lead=10.4, fill='#333')
    return d


# ============================================================================ legend
# Legend discipline (audit-2026-09-03/drawing-standards.md §3.2): every symbol drawn on this sheet
# appears below, and no entry below is unused.  build() asserts the fills against the SVG.
LEGEND = [
    ('line', C['lot'], 1.6, '', 'Property / lot line; HOA lane tract line'),
    ('line', C['setb'], 0.7, '7 3 2 3', 'Building setback line (15 / 5 / 20 ft)'),
    ('rect', 'url(#bufhatch)', 0, '', "20'-0\" undisturbed buffer easement, on the lot"),
    ('rect', C['house'], 0, '', 'Dwelling — conditioned body'),
    ('rect', '#efd2ad', 0, '', "Garage, recessed 5'-0\" behind the front wall"),
    ('rect', '#fdf3e4', 0, '', 'Covered porch; roofed open shelter'),
    ('rect', '#f0efe6', 0, '', 'Uncovered patio'),
    ('rect', 'url(#d_conc)', 0, '', 'Concrete — walk, drive, curb, pad, footing'),
    ('rect', C['asph_s'], 0, '', 'Asphalt surface course / pavement in plan'),
    ('rect', C['asph_i'], 0, '', 'Asphalt intermediate course'),
    ('rect', 'url(#d_gab2)', 0, '', 'Graded aggregate base (GAB)'),
    ('rect', 'url(#d_earth)', 0, '', 'Compacted subgrade / undisturbed earth'),
    ('rect', 'url(#d_grass)', 0, '', 'Grass verge, lawn, landscape area'),
    ('rect', 'url(#d_mas)', 0, '', 'Masonry — sign base, piers, water table'),
    ('rect', 'url(#d_mulch)', 0, '', 'Mulch inside the tree-protection zone'),
    ('rect', '#8d7f6c', 0, '', 'Roof, seen in section or elevation'),
    ('rect', '#ded3c2', 0, '', 'Cast-stone sign panel and cap'),
    ('rect', '#efe7dc', 0, '', 'Adjoining R-1 dwelling (section, for scale)'),
    ('rect', '#cfd6dc', 0, '', 'USPS cluster box unit'),
    ('rect', '#2f4a66', 0, '', 'Painted access aisle — no parking'),
    ('rect', '#8a8a8a', 0, '', 'Steel post — sign post, fence post'),
    ('rect', '#1b5fa8', 0, '', 'Accessible parking sign (R7-8 + van plaque)'),
    ('rect', '#d2691e', 0, '', "Tree-protection fence, 4'-0\", on steel posts"),
    ('tree', C['tree'], 0, '', 'Tree retained or supplemental canopy planting'),
    ('tree', '#2f6b46', 0, '', 'Supplemental evergreen screen planting'),
    ('dot', C['fire'], 0, '', 'Proposed fire hydrant'),
    ('line', '#444', 0.7, '16 3 3 3', 'Centreline'),
    ('line', C['dim'], 0.7, '', 'Dimension line (US survey feet and inches)'),
]

SOURCES = [
    'GEOMETRY: data/layout.json and data/plans.json, regenerated 2026-09-03. Detail 1 is lots 7 and '
    '8 (Block A, south-west side); details 2 and 3 are lane stations u = 300 and u = 700 ft; detail '
    '4 is hammerheads[1] at u = 1,110 ft; details 6, 7 and 8 are the amenity records.',
    'SPECIFICATIONS: docs/12-outline-specifications.md §32 12 16, §32 16 13, §10 14 00. FIRE: '
    'docs/08-technical-memoranda.md Memo E.',
    'CODE: Lilburn Zoning Ordinance 2023-603; Lilburn Site Development Plan Review Checklist; IFC '
    '2024 as modified by Ga. Comp. R. & Regs. R. 120-3-3-.04; Gwinnett County UDO §900-70; GDOT '
    'Standard Specifications 2021; 2010 ADA Standards.',
]


def legend(D):
    x, y, w, h = BOX['leg']
    D.srect(x, y, w, h, fill='#fff', stroke='#000', stroke_width=0.9)
    D.stext(x + 8, y + 16, 'LEGEND', size=13, bold=True)
    D.stext(x + 74, y + 16, '— every symbol drawn on this sheet appears below, and no entry below '
            'is unused (audit-2026-09-03/drawing-standards.md §3.2)', size=TXT, fill='#555')
    rows = 10
    cw = (w - 16) / 3.0
    for k, (kind, col, wd, dash, txt) in enumerate(LEGEND):
        cx = x + 8 + (k // rows) * cw
        yy = y + 32 + (k % rows) * 11.7
        if kind == 'line':
            D.sline(cx, yy - 3, cx + 32, yy - 3, stroke=col, stroke_width=wd,
                    stroke_dasharray=dash)
        elif kind == 'dot':
            D.scircle(cx + 16, yy - 3, 3.0, fill=col, stroke='#fff', stroke_width=0.6)
        elif kind == 'tree':
            D.scircle(cx + 16, yy - 4, 6.0, fill=col, fill_opacity='0.28', stroke=col,
                      stroke_width=0.8)
        else:
            D.srect(cx, yy - 10, 32, 12, fill=col, stroke='#555', stroke_width=0.4)
        D.stext(cx + 38, yy, txt, size=TXT)


# ============================================================================ general notes
NOTES = [
    'STATUS AND SCOPE. CONCEPT DETAILS prepared by the owner for a rezoning application under '
    'Lilburn Zoning Ordinance 2023-603 §1003. NOT construction documents and NOT SEALED. Every '
    'pavement section, curb, footing, slope and structural element must be designed and sealed by a '
    'Georgia PE, and the tree-protection and buffer details by a registered landscape architect, '
    'forester or arborist, before any permit. Every statement of conformity reads "appears '
    'consistent with"; none is a certification.',

    'PRIVATE STREET STANDARD. The lane is a private street in an HOA tract. Checklist §4.s: "Label '
    'new streets as \'Private\' unless previously approved by Gwinnett and City of Lilburn. All '
    'components of private streets and alleys must meet minimum standards for public street." '
    'Details 2 and 3 are drawn to Gwinnett County UDO §900-70.4.A as the PRESUMPTIVE public-street '
    'standard because the Lilburn Development Regulations (Code Appendix B) are not retrievable '
    'online. VERIFY the required section, curb profile, sidewalk thickness and horizontal-curve '
    'standard at the pre-application conference.',

    'PAVING. Checklist §7.i requires a typical paving section for parking areas and drives at a '
    'minimum of 4 in GAB and 2 in Type E or F; §4.t requires the materials to be labelled with '
    'standard details. Detail 5 gives three: lane, turnarounds and entrance apron at 8 in GAB + 2 '
    'in 19 mm Superpave + 1¼ in 9.5 mm Superpave Type II; driveways at 6 in concrete on 4 in GAB '
    '(asphalt option 2 in on 4 in, the §7.i minimum); guest and kiosk bays at 2 in on 6 in GAB, '
    'pervious pavers an owner option (Table 4.2). GDOT Standard Specifications 2021.',

    'SIDEWALKS — ONE OPEN QUESTION, STATED. A 5\'-0" walk is carried on the north-east side of the '
    'whole lane and the entry drive, and on the south-west side from u = 530 ft to the terminus '
    '(detail 3). As drawn the walk sits 2\'-0" from the FACE of curb, i.e. 1\'-6" behind the back of '
    'a 6-in curb; the checklist asks for 2 ft off the BACK of curb, which needs 2\'-6" from the '
    'face. The north-east half-section is 18\'-9" at its narrowest (u = 149.5 ft) against the 18\'-0" '
    'used, so the shift fits there; the south-west half-section is 18\'-4" at u = 530 ft, so it does '
    'not without taking 2 in from the lot depth. Over u = 230–530 ft the south-west half-width is '
    '16\'-11" to 18\'-4" and a second walk does not fit at all. The question is put to staff rather '
    'than drawn away.',

    'GRADES. Street grades shall not exceed 12 %. REQUIRED NOTE (Checklist §7.k, verbatim): "12% to '
    '15% street grades require an \'As Graded\' survey before installation of the curb." IFC 2024 '
    '(GA) Appendix D103.2 limits the fire apparatus access road to 10 % unless approved. The '
    'steepest EXISTING ground grade on the lane centreline is {G} at u ≈ {U} ft (3DEP, approx.). '
    'The FINISHED profile is not designed here — see Sheet C-5.0.',

    'FIRE ACCESS. IFC 2024, as adopted and modified by Ga. Comp. R. & Regs. R. 120-3-3-.04. Table '
    'D103.4: 0–150 ft, 20 ft wide, no turnaround; 151–500 ft, 20 ft + a 120-ft hammerhead; 501–750 '
    'ft, 26 ft + turnaround; over 750 ft, "Special approval required". The travelled way is 1,754 ft '
    'from the Arcado Rd right-of-way, so SPECIAL APPROVAL IS REQUESTED and must be obtained in '
    'writing from the Gwinnett County Fire Marshal before the Planning Commission hearing. Three '
    'hammerhead turnarounds (detail 4), each two 20\'-0" × 60\'-0" legs = 142\'-0" overall, exceed '
    'Figure D103.1\'s 120-ft hammerhead; runs between intersections are 594.5 / 570.0 / 580.0 ft. '
    'D107.1 as replaced by 120-3-3-.04 requires two access roads only above 120 dwelling units, so '
    'at 41 units it is NOT triggered and NFPA 13D sprinklers are a VOLUNTARY offer. "NO PARKING — '
    'FIRE LANE" signs both sides (D103.6). The 22-ft width against Table D103.4\'s 26 ft is the '
    'relief item; 26\'-0" of pavement is offered from u ≈ 1,010 ft where the tract reaches 40\'-0".',

    'SETBACKS AND BUFFER. Table 4.1 (R-2): lot area 3,000 SF min (5,000 provided), width 50 ft '
    '(50), depth 100 ft (100), front 15 ft from the right-of-way, side 5 ft (6 provided), rear 20 '
    'ft; buffer abutting R-1 is 0 ft for detached single-family and 20 ft for all other allowed '
    'dwelling types. Cottage homes are listed separately from detached single-family, so the plan '
    'designs to the 20-ft buffer and states the interpretation. §313(1): "Buffer requirements … '
    'supersede these minimum required yards" — the buffer is held inside the rear 20 ft of the lot, '
    'coincident with the rear yard, in a recorded easement (details 1 and 10). Table 4.2 requires '
    'front-loaded garages recessed ≥ 5 ft behind the front wall; 5\'-0" is provided. THE '
    'INTERPRETATION IS TO BE CONFIRMED AT THE PRE-APPLICATION CONFERENCE; the fallback (buffer in a '
    'separate tract, 50 × 82 lots, §1005 variance) is Sheet C-2.4.',

    'SIGNS. One ground-mounted monument entry sign is proposed (detail 7). NO WALL SIGNS ARE '
    'PROPOSED on any dwelling, on the clubhouse or on any accessory structure. REQUIRED NOTE '
    '(Checklist §4.q, verbatim): "All signs shall be permitted separately." A sign easement may be '
    'required. The 32-SF face and 6\'-0" height are the applicant\'s voluntary condition, not a cited '
    'ordinance limit — the Lilburn sign article has not been obtained. VERIFY the article, edition, '
    'measurement method, setback and illumination limits.',

    'MAIL DELIVERY. REQUIRED NOTE (Checklist §4.r): a cluster-box system is proposed for the entire '
    'project and one street name may serve to assign all house numbers. Contact the Lilburn Post '
    'Office Growth Manager for mail delivery and mailbox requirements. The accessory structure and '
    'its protection from the elements are detail 8.',

    'TREE PROTECTION. REQUIRED NOTE (Checklist §6.g, verbatim): "Tree Protection fence must be '
    'installed prior to commencing land disturbing activities." Fence at the limits of disturbance, '
    'the buffer line and the drip line of retained trees (detail 9). Tree density unit calculations '
    'are not required of an SFR subdivision (§6.i). No tree survey has been performed; one is '
    'required with the Land Disturbance Permit.',

    'ACCESSIBILITY. The 2010 ADA Standards govern the common facilities (§208 parking, §502 space '
    'and aisle, §402–403 routes); PROWAG (2023 final rule, 36 CFR 1190) is applied by policy on the '
    'private lane and is mandatory at the Arcado Rd public sidewalk; ICC A117.1-2017 governs the '
    'reach ranges at the cluster boxes. All 41 cottages are offered with zero-step entries, 36-in '
    'doors and blocking for grab bars as a voluntary condition; §734 applies to attached dwellings '
    'only.',

    'LETTERING, SCALES AND UNITS. Minimum lettering is 9.0 pt — 0.125 in of overall glyph height '
    'and 0.089 in of cap height at full size, 0.058 in at the 46.4 % reduction to 11 × 17. The '
    'scale is stated at every detail and a graphic scale is drawn on details 1, 2, 3, 4, 5, 7, 8 '
    'and 10. Dimensions are US customary in architectural notation; areas are SF with the area type '
    'named. Site-local coordinates (u along the strip from the Arcado Rd right-of-way, v across, '
    'feet) are those of FACTS.md §1; detail 1\'s north arrow is drawn for that detail\'s 180°-'
    'rotated frame and detail 4 carries true plan north.',

    'SOURCES. GEOMETRY — data/layout.json and data/plans.json, regenerated 2026-09-03: detail 1 is '
    'lots 7 and 8; details 2 and 3 are lane stations u = 300 and 700 ft; detail 4 is hammerheads[1] '
    'at u = 1,110 ft; details 6, 7 and 8 are the amenity records. Every dimension on this sheet is '
    'regenerated by tools/details.py — none is typed by hand. SPECIFICATIONS — docs/12 §32 12 16, '
    '§32 16 13, §10 14 00. FIRE — docs/08 Memo E. CODE — Lilburn Zoning Ordinance 2023-603; '
    'Lilburn Site Development Plan Review Checklist; IFC 2024 as modified by Ga. Comp. R. & Regs. '
    'R. 120-3-3-.04; Gwinnett County UDO §900-70; GDOT Specs 2021; 2010 ADA Standards.',
]


def notes(D):
    x, y, w, h = BOX['not']
    D.srect(x, y, w, h, fill='#fff', stroke='#000', stroke_width=0.9)
    D.stext(x + 8, y + 17, 'GENERAL NOTES — CIVIL DETAILS', size=13, bold=True)
    yy = y + 30
    for i, n in enumerate(NOTES, 1):
        n = n.replace('{G}', '%.1f %%' % MET['max_existing_lane_grade_pct'])
        n = n.replace('{U}', format(int(MET['max_existing_lane_grade_at_u_ft']), ','))
        yy = D.stextblock(x + 8, yy, '%d. %s' % (i, n), size=TXT, chars=205, lead=10.0,
                          indent=10)
        yy += 2.0
    return yy


# ============================================================================ build
STATUS = ['Concept civil details for pre-application review. Every section,',
          'structure, footing and slope shown must be designed and sealed by',
          'a Georgia PE (and the tree / buffer details by a registered LA,',
          'forester or arborist). NOT CONSTRUCTION DOCUMENTS.']


def build():
    D = sheet_frame(STATUS, 'As noted per detail')
    D.stext(sb.MARGIN + sb.INNER + 12, 46,
            'CIVIL DETAILS — SCALES AS NOTED PER DETAIL  (ARCH D 36 × 24 in) — every dimension is '
            'regenerated from data/layout.json and data/plans.json; the sealed survey and the PE '
            'design govern', size=12, bold=True)
    D.add('<text x="%.1f" y="%.1f" font-size="34" fill="#c00" fill-opacity="0.085" '
          'font-weight="bold" text-anchor="middle" transform="rotate(-7 %.1f %.1f)">'
          'DRAFT — NOT SEALED — CONCEPT DETAILS, NOT FOR CONSTRUCTION</text>'
          % (1290, 760, 1290, 760))
    d1(D)
    d2(D)
    d3(D)
    d4(D)
    d5(D)
    d6(D)
    d7(D)
    d8(D)
    d9(D)
    d10(D)
    legend(D)
    notes(D)
    return D


def _audit(svg):
    """Legend discipline: every legend swatch must appear in the body, and vice versa."""
    missing = [t for k, col, _, _, t in LEGEND if k in ('rect', 'tree', 'dot')
               and ('fill="%s"' % col) not in svg]
    return missing


if __name__ == '__main__':
    D = build()
    svg_path, png_path = sb.save(D, 'civil-details', dpi=150)
    svg = open(svg_path).read()
    print('wrote %s\n      %s' % (svg_path, png_path))
    print('  details   : 10 (typical lot, 2 lane sections, hammerhead, paving, accessible, sign, '
          'kiosk, tree fence, buffer)')
    print('  lot 7 (A) : porch face %s · garage door %s · body %s · rear element %s from the rear '
          'line, %s clear of the buffer'
          % (fti(A['porch_face'] - A['fv']), fti(A['gar_face'] - A['fv']), A['label'],
             fti(A['rv'] - A['rear_el']), fti(A['buf_v'] - A['rear_el'])))
    print('  lot 8 (B) : porch face %s · garage door %s · body %s · rear element %s from the rear '
          'line, %s clear of the buffer'
          % (fti(B['porch_face'] - B['fv']), fti(B['gar_face'] - B['fv']), B['label'],
             fti(B['rv'] - B['rear_el']), fti(B['buf_v'] - B['rear_el'])))
    _tr630 = -interp(_TR_SW, U_SUM - 630.0) - V_OFF
    _pv630 = -interp(_PV_SW, U_SUM - 630.0) - V_OFF
    print('  driveway  : %s garage door to the lane tract; %s to the face of curb'
          % (fti(A['gar_face'] - _tr630), fti(A['gar_face'] - _pv630)))
    print('  section   : u=300 tract %s, pavement %s; u=700 tract %s, walks both sides'
          % (fti(ST_TYP['tract_w']), fti(ST_TYP['pave_w']), fti(ST_WID['tract_w'])))
    print('  hammerhead: legs %s × %s, %s overall; stations %s ft'
          % (fti(HH['width_ft']), fti(HH['leg_ft']), fti(2 * HH['leg_ft'] + 22.0),
             ' / '.join('%.1f' % s for s in HH_STA)))
    print('  sign      : face %.1f SF ≤ %.0f SF; height %s ≤ %s; panel %.1f SF'
          % (SG_FACE_SF, SG_MAX_SF, fti(SG_H), fti(SG_MAX_H), SG_PANEL_SF))
    print('  kiosk     : %s × %s, %d CBUs = %d compartments + %d parcel lockers, ridge %s AFG'
          % (fti(K_L), fti(K_W), K_CBU, K_CBU * K_COMP, K_CBU * K_PARCEL, fti(K_RIDGE)))
    print('  legend    : %d entries; unused swatches: %s'
          % (len(LEGEND), _audit(svg) or 'none'))
    print('  marker    : %s ; disclaimer: %s' % (sb.MARKER in svg, 'Disclaimer:' in svg))
