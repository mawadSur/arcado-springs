#!/usr/bin/env python3
"""Floor-plan drawing engine + Plan A "The Springbrook" + Plan B "The Laurel" — The Cottages at Arcado Springs (R-2 rezoning, Lilburn GA).

ILLUSTRATIVE ARCHITECTURAL PLANS — NOT FOR CONSTRUCTION. DRAFT — to be superseded by sealed work (GA architect).
Program per FACTS.md §4; drawing rules per FACTS.md §6. Run:  python3 tools/floorplans.py  [plan_id ...]

===================================================================================================
SPEC FORMAT (how to add Plan B: append a dict to PLANS keyed by plan id and re-run)
===================================================================================================
Plan coordinates are FEET. Origin = front-left corner of the body's bounding box, x to the right
(looking at the house from the lane), y toward the REAR (front = lane side = y 0). The drawing flips y
so the lane is at the bottom of the sheet.

Rooms are laid out on a "grid" whose lines are the OUTSIDE FACE of exterior walls and the CENTERLINE of
interior walls. The engine derives the wall network from the room polygons: an edge shared by two rooms
is an interior wall (4 in, centered); an edge belonging to one room only is exterior (6 in, drawn inward).
Each room's CLEAR polygon (inside face) is the grid polygon offset inward by 6 in on exterior edges and
2 in on interior edges. Areas: room area_sf = clear polygon; conditioned SF = union of `cond` rooms on the
grid (= outside-face polygon on exterior walls, centerline at the garage separation wall).

spec = {
  'id': 'A', 'name': 'THE SPRINGBROOK', 'date': '2026-08-28', 'target_cond_sf': 1444,
  'nominal_body': '38\'-0" x 38\'-0"',            # program label, reported alongside the actual envelope
  'rooms': [ {'name': 'GREAT ROOM', 'kind': 'cond'|'garage'|'porch'|'patio',
              'rect': (x0, y0, x1, y1)  OR  'poly': [(x, y), ...]  (rectilinear, any winding),
              'label': 'GREAT ROOM' (optional; default name), 'label_at': (x, y) (optional),
              'label_dims': 'W x D' (optional override), 'narrow_ok': True (baths/halls/closets),
              'bedroom': True, 'bath': True, 'circle': (cx, cy) (60-in turning circle centre, baths),
              'vaulted': True, 'fixtures': [ ... see FIXTURES ... ],
              'closet_rod': [ (x0, y0, x1, y1), ... ]  (shelf/rod strips: rect of the 24-in shelf) }, ...],
  'open_edges': [ (x0, y0, x1, y1), ... ],  # shared grid edges drawn as cased openings (dashed header), no wall
  'doors':   [ {'at': (x, y), 'axis': 'h'|'v', 'w': 3.0, 'hinge': -1|+1, 'swing': -1|+1,
                'type': 'door'|'garage'|'french'|'cased'|'bifold', 'h': 6.67, 'tag': '...'} ],
             #  at = centre of the opening ON the wall grid line; axis = direction the wall runs;
             #  hinge = which end of the opening the hinge is on (-1 = lower x/y end); swing = which side
             #  of the wall the leaf swings to (+1 = toward +y for 'h' walls, toward +x for 'v' walls)
  'windows': [ {'at': (x, y), 'axis': 'h'|'v', 'w': 6.0, 'h': 5.0, 'sill': 2.67, 'tag': 'twin'} ],
  'porch_columns': [ (x, y), ... ],  # 8x8 posts (centre)
  'roof': {'plate_ft': 9.0, 'elements': [{'name': 'main gable', 'span_ft': 25, 'pitch': (8, 12), 'ridge': 'x'}, ...]},
  'accessibility': [ (item, provided, status), ... ],
  'materials_by_scheme': {...},
  'dims': { 'front': [[x...], ...], 'rear': [...], 'left': [[y...], ...], 'right': [...] },  # chains, outermost last
  'notes': [ '...' ],
}
FIXTURES (all in absolute feet, clear coordinates): {'t': 'counter'|'island'|'range'|'fridge'|'sink'|'dw'|
 'toilet'|'vanity'|'tub'|'shower'|'washer'|'dryer'|'wh'|'bench'|'bed'|'sofa'|'table'|'shelf'|'fireplace', 'r': (x0,y0,x1,y1),
 'label': '...' (optional; 'lx','ly','ls' position/size), 'sinks': 2 (vanity)}.  'wh' uses 'c': (cx, cy), 'rad'.
 'bed' takes 'head': 'y1'|'y0'|'x1'|'x0'; 'fireplace' takes 'back' (wall side) + 'hearth' depth.
Other spec keys: a 'porch' room with 'side': 'rear' is a covered REAR porch (tabulated separately, counted under roof;
 draw it as a notch in the conditioned envelope to recess it under the main roof); 'sheet': 'A-2' (title-block number);
 'envelope_note' (plans.json overall_body_dims.note); 'verify': [...] (open items exported to plans.json).
Plan B "The Laurel" (2026-08-29) is the second spec; both plans share the engine, standards and plans.json field structure.
===================================================================================================
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data')
DRAW = os.path.join(ROOT, 'drawings')
os.makedirs(DRAW, exist_ok=True); os.makedirs(DATA, exist_ok=True)

EXT_T, INT_T = 0.5, 4.0 / 12.0            # wall thicknesses, ft
DATE = '2026-08-28'
TITLE_SUFFIX = 'ILLUSTRATIVE ARCHITECTURAL PLAN — NOT FOR CONSTRUCTION — ' + DATE
DISCLAIMER = ('Disclaimer: This is an AI-generated analysis for preliminary planning purposes. All findings must be '
              'verified by a licensed professional before use in design, permitting, or regulatory submissions.')
MARKER = 'architecture-studio:requires-disclaimer'

# ----------------------------------------------------------------------------- geometry helpers
def fti(v):
    """feet (float) -> architectural notation 26'-10"."""
    neg = v < 0; v = abs(v)
    ft = int(v); inch = int(round((v - ft) * 12))
    if inch == 12: ft += 1; inch = 0
    return ('-' if neg else '') + '%d\'-%d"' % (ft, inch)

def poly_area(p):
    return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))

def ccw(p): return list(p) if poly_area(p) > 0 else list(p)[::-1]

def rect_poly(r): x0, y0, x1, y1 = r; return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

def room_poly(room): return ccw(room['poly'] if 'poly' in room else rect_poly(room['rect']))

def bbox(p): return (min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p))

def point_in_poly(pt, poly):
    x, y = pt; inside = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x: inside = not inside
    return inside

def rects_overlap(a, b, tol=0.02):
    return not (a[2] <= b[0] + tol or b[2] <= a[0] + tol or a[3] <= b[1] + tol or b[3] <= a[1] + tol)

def offset_rectilinear(poly, offsets):
    """Inward offset of a CCW rectilinear polygon; offsets[i] = offset of edge i (from vertex i to i+1)."""
    n = len(poly); lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        d = offsets[i]
        if abs(y1 - y0) < 1e-9:                     # horizontal edge; inward normal for CCW = left of travel
            nx, ny = 0.0, (1.0 if x1 > x0 else -1.0)
            lines.append(('h', y0 + ny * d))
        else:
            nx = -1.0 if y1 > y0 else 1.0
            lines.append(('v', x0 + nx * d))
    out = []
    for i in range(n):
        a, b = lines[i - 1], lines[i]              # vertex i is the meet of edge i-1 and edge i
        if a[0] == b[0]:
            raise ValueError('non-rectilinear corner in polygon %r' % (poly,))
        x = a[1] if a[0] == 'v' else b[1]; y = a[1] if a[0] == 'h' else b[1]
        out.append((x, y))
    return out

def split_edges(poly):
    """Axis-aligned edges of a polygon as (x0,y0,x1,y1) with the room on the LEFT (CCW)."""
    p = ccw(poly); return [(p[i][0], p[i][1], p[(i + 1) % len(p)][0], p[(i + 1) % len(p)][1]) for i in range(len(p))]

def seg_key(e):
    x0, y0, x1, y1 = e
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

def build_walls(spec):
    """Derive wall segments. Split every room edge at every grid coordinate so shared edges match exactly.
    Returns list of dicts: {'seg': (x0,y0,x1,y1) normalized, 'axis', 'ext': bool, 'rooms': [..], 'inward': ±1,
    'open': bool}."""
    rooms = [r for r in spec['rooms'] if r['kind'] in ('cond', 'garage')]
    xs = sorted({v for r in rooms for q in room_poly(r) for v in (q[0],)})
    ys = sorted({v for r in rooms for q in room_poly(r) for v in (q[1],)})
    pieces = {}
    for r in rooms:
        for e in split_edges(room_poly(r)):
            x0, y0, x1, y1 = e
            if abs(y1 - y0) < 1e-9:       # horizontal; room on left of travel: travel +x -> room at +y
                inward = 1 if x1 > x0 else -1
                cuts = [v for v in xs if min(x0, x1) - 1e-9 < v < max(x0, x1) + 1e-9]
                for a, b in zip(cuts[:-1], cuts[1:]):
                    k = (a, y0, b, y0); pieces.setdefault(k, []).append((r['name'], r['kind'], inward, 'h'))
            else:
                inward = -1 if y1 > y0 else 1   # travel +y -> room at -x
                cuts = [v for v in ys if min(y0, y1) - 1e-9 < v < max(y0, y1) + 1e-9]
                for a, b in zip(cuts[:-1], cuts[1:]):
                    k = (x0, a, x0, b); pieces.setdefault(k, []).append((r['name'], r['kind'], inward, 'v'))
    open_keys = set()
    for oe in spec.get('open_edges', []):
        k = seg_key(oe)
        for pk in pieces:
            if pk[0] >= k[0] - 1e-9 and pk[2] <= k[2] + 1e-9 and pk[1] >= k[1] - 1e-9 and pk[3] <= k[3] + 1e-9 and \
               ((pk[0] == pk[2] and k[0] == k[2]) or (pk[1] == pk[3] and k[1] == k[3])):
                open_keys.add(pk)
    walls = []
    for k, owners in pieces.items():
        ext = len(owners) == 1
        walls.append({'seg': k, 'axis': owners[0][3], 'ext': ext, 'rooms': [o[0] for o in owners],
                      'kinds': [o[1] for o in owners], 'inward': owners[0][2], 'open': k in open_keys,
                      't': EXT_T if ext else INT_T})
    return walls

def wall_rect(w):
    x0, y0, x1, y1 = w['seg']; t = w['t']
    if w['axis'] == 'h':
        if w['ext']: return (x0, y0, x1, y0 + t) if w['inward'] > 0 else (x0, y0 - t, x1, y0)
        return (x0, y0 - t / 2, x1, y0 + t / 2)
    if w['ext']: return (x0, y0, x0 + t, y1) if w['inward'] > 0 else (x0 - t, y0, x0, y1)
    return (x0 - t / 2, y0, x0 + t / 2, y1)

def clear_poly(room, walls):
    p = room_poly(room); offs = []
    ext_index = {}
    for w in walls:
        ext_index.setdefault(w['seg'], w)
    for e in split_edges(p):
        k = seg_key(e)
        # find any wall piece inside this edge to learn ext/int (all pieces of one room edge may differ; use max)
        ts = []
        for w in walls:
            s = w['seg']
            same_axis = (w['axis'] == 'h' and abs(s[1] - k[1]) < 1e-9 and abs(s[3] - k[3]) < 1e-9) or \
                        (w['axis'] == 'v' and abs(s[0] - k[0]) < 1e-9 and abs(s[2] - k[2]) < 1e-9)
            if same_axis and s[0] >= k[0] - 1e-9 and s[2] <= k[2] + 1e-9 and s[1] >= k[1] - 1e-9 and s[3] <= k[3] + 1e-9:
                ts.append(0.0 if w['open'] else (EXT_T if w['ext'] else INT_T / 2))
        offs.append(max(ts) if ts else INT_T / 2)
    return offset_rectilinear(p, offs)

# ----------------------------------------------------------------------------- SVG primitives (plan feet, y flipped)
def esc(t): return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

class Canvas:
    """Collects SVG in plan-feet units. Y is flipped so the front (lane) is at the bottom. All sizes in ft."""
    LW = 0.035          # thin line, ft
    def __init__(self, ymax):
        self.ymax = ymax; self.out = []
    def X(self, x): return x
    def Y(self, y): return self.ymax - y
    def add(self, s): self.out.append(s)
    def line(self, x0, y0, x1, y1, lw=None, cls='', dash=None, color='#111'):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        self.add('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" stroke="%s" stroke-width="%.3f"%s stroke-linecap="round"/>'
                 % (self.X(x0), self.Y(y0), self.X(x1), self.Y(y1), color, lw or self.LW, d))
    def rect(self, r, fill='none', stroke='#111', lw=None, dash=None, opacity=None):
        x0, y0, x1, y1 = r
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        o = ' fill-opacity="%.2f"' % opacity if opacity is not None else ''
        self.add('<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" fill="%s" stroke="%s" stroke-width="%.3f"%s%s/>'
                 % (self.X(min(x0, x1)), self.Y(max(y0, y1)), abs(x1 - x0), abs(y1 - y0), fill, stroke,
                    lw if lw is not None else self.LW, d, o))
    def poly(self, pts, fill='none', stroke='#111', lw=None, dash=None, opacity=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        o = ' fill-opacity="%.2f"' % opacity if opacity is not None else ''
        self.add('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%.3f"%s%s/>'
                 % (' '.join('%.3f,%.3f' % (self.X(x), self.Y(y)) for x, y in pts), fill, stroke,
                    lw if lw is not None else self.LW, d, o))
    def circle(self, cx, cy, r, fill='none', stroke='#111', lw=None, dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        self.add('<circle cx="%.3f" cy="%.3f" r="%.3f" fill="%s" stroke="%s" stroke-width="%.3f"%s/>'
                 % (self.X(cx), self.Y(cy), r, fill, stroke, lw if lw is not None else self.LW, d))
    def arc(self, cx, cy, r, a0, a1, lw=None, color='#111'):
        """arc from angle a0 to a1 (degrees, plan CCW from +x) — drawn thin."""
        x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
        x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
        large = 1 if abs(a1 - a0) > 180 else 0
        sweep = 0 if a1 > a0 else 1      # plan CCW becomes SVG CW because Y is flipped
        self.add('<path d="M %.3f %.3f A %.3f %.3f 0 %d %d %.3f %.3f" fill="none" stroke="%s" stroke-width="%.3f"/>'
                 % (self.X(x0), self.Y(y0), r, r, large, sweep, self.X(x1), self.Y(y1), color, lw or self.LW))
    def text(self, x, y, s, size=0.55, anchor='middle', weight='normal', rot=0, color='#111', family='Helvetica, Arial, sans-serif', italic=False):
        tr = ' transform="rotate(%.1f %.3f %.3f)"' % (rot, self.X(x), self.Y(y)) if rot else ''
        st = ' font-style="italic"' if italic else ''
        self.add('<text x="%.3f" y="%.3f" font-size="%.3f" font-family="%s" text-anchor="%s" font-weight="%s" fill="%s" dominant-baseline="middle"%s%s>%s</text>'
                 % (self.X(x), self.Y(y), size, family, anchor, weight, color, tr, st, esc(s)))
    def svg(self): return '\n'.join(self.out)

# ----------------------------------------------------------------------------- drawing the plan
def draw_fixture(c, f):
    t = f['t']; lw = 0.03
    if t in ('counter', 'island', 'vanity', 'bench', 'shelf', 'dryer', 'washer', 'fridge', 'range', 'dw', 'sofa', 'table'):
        r = f['r']; c.rect(r, fill='#fff', lw=lw)
        x0, y0, x1, y1 = r; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if t == 'vanity':
            n = f.get('sinks', 1); w = x1 - x0; h = y1 - y0
            for i in range(n):
                if w >= h: sx = x0 + w * (i + 0.5) / n; sy = cy
                else: sx = cx; sy = y0 + h * (i + 0.5) / n
                c.rect((sx - 0.75, sy - 0.6, sx + 0.75, sy + 0.6), lw=lw, fill='#fff')
                c.circle(sx, sy, 0.12, lw=lw)
        elif t == 'range':
            for dx, dy in ((-0.5, -0.45), (0.5, -0.45), (-0.5, 0.45), (0.5, 0.45)):
                c.circle(cx + dx * (x1 - x0) / 1.6, cy + dy * (y1 - y0) / 1.6, 0.3, lw=lw)
        elif t == 'fridge':
            c.line(x0, y0, x1, y1, lw=lw); c.line(x0, y1, x1, y0, lw=lw)
        elif t in ('washer', 'dryer'):
            c.circle(cx, cy, min(x1 - x0, y1 - y0) * 0.33, lw=lw); c.text(cx, cy, 'W' if t == 'washer' else 'D', size=0.4)
        elif t == 'dw':
            c.text(cx, cy, 'DW', size=0.32)
        elif t == 'sofa':
            c.rect((x0 + 0.5, y0 + 0.5, x1 - 0.5, y1 - 0.15), lw=lw, fill='#fff')
        elif t == 'table':
            c.rect((x0 + 0.15, y0 + 0.15, x1 - 0.15, y1 - 0.15), lw=lw, fill='#fff')
        elif t == 'bench':
            c.text(cx, cy, 'BENCH', size=0.3)
        elif t == 'shelf':
            c.line(x0, y0, x1, y1, lw=lw) if (x1 - x0) > (y1 - y0) else None
        if f.get('label'):
            c.text(f.get('lx', cx), f.get('ly', cy), f['label'], size=f.get('ls', 0.32), rot=f.get('rot', 0))
    elif t == 'sink':
        r = f['r']; x0, y0, x1, y1 = r; c.rect((x0 + 0.15, y0 + 0.15, x1 - 0.15, y1 - 0.15), lw=lw, fill='#fff', )
        c.circle((x0 + x1) / 2, (y0 + y1) / 2, 0.1, lw=lw)
        if f.get('label'): c.text(f.get('lx', (x0 + x1) / 2), f.get('ly', y1 + 0.4), f['label'], size=f.get('ls', 0.28))
    elif t == 'toilet':
        x0, y0, x1, y1 = f['r']; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; ax = f.get('back', 'y1')
        w, h = x1 - x0, y1 - y0
        if ax in ('y1', 'y0'):        # tank against a horizontal wall
            ty0, ty1 = (y1 - 0.7, y1) if ax == 'y1' else (y0, y0 + 0.7)
            c.rect((x0 + 0.25, ty0, x1 - 0.25, ty1), lw=lw, fill='#fff')
            by = (ty0 - 0.95) if ax == 'y1' else (ty1 + 0.95)
            c.add('<ellipse cx="%.3f" cy="%.3f" rx="%.3f" ry="%.3f" fill="#fff" stroke="#111" stroke-width="%.3f"/>' % (c.X(cx), c.Y(by), 0.62, 0.95, lw))
        else:                           # tank against a vertical wall
            tx0, tx1 = (x1 - 0.7, x1) if ax == 'x1' else (x0, x0 + 0.7)
            c.rect((tx0, y0 + 0.25, tx1, y1 - 0.25), lw=lw, fill='#fff')
            bx = (tx0 - 0.95) if ax == 'x1' else (tx1 + 0.95)
            c.add('<ellipse cx="%.3f" cy="%.3f" rx="%.3f" ry="%.3f" fill="#fff" stroke="#111" stroke-width="%.3f"/>' % (c.X(bx), c.Y(cy), 0.95, 0.62, lw))
    elif t == 'tub':
        r = f['r']; x0, y0, x1, y1 = r; c.rect(r, lw=lw, fill='#fff'); c.rect((x0 + 0.3, y0 + 0.3, x1 - 0.3, y1 - 0.3), lw=lw, fill='#fff')
        c.text((x0 + x1) / 2, (y0 + y1) / 2, f.get('label', 'TUB/SHWR'), size=0.3, rot=f.get('rot', 90))
    elif t == 'shower':
        r = f['r']; x0, y0, x1, y1 = r; c.rect(r, lw=lw, fill='#fff', dash='0.15,0.1')
        c.line(x0, y0, x1, y1, lw=0.02, color='#666'); c.line(x0, y1, x1, y0, lw=0.02, color='#666')
        c.circle(f.get('dx', (x0 + x1) / 2), f.get('dy', (y0 + y1) / 2), 0.15, lw=lw)
        c.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.7, f.get('label', 'CURBLESS SHWR'), size=0.28)
    elif t == 'wh':
        cx, cy = f['c']; c.circle(cx, cy, f.get('rad', 0.9), lw=lw, fill='#fff'); c.text(cx, cy, 'WH', size=0.32)
    elif t == 'bed':
        r = f['r']; x0, y0, x1, y1 = r; c.rect(r, lw=lw, fill='#fff')
        head = f.get('head', 'y1')
        if head == 'y1': c.rect((x0 + 0.2, y1 - 1.3, x1 - 0.2, y1 - 0.2), lw=lw, fill='#fff'); c.line(x0, y1 - 1.6, x1, y1 - 1.6, lw=lw)
        elif head == 'x1': c.rect((x1 - 1.3, y0 + 0.2, x1 - 0.2, y1 - 0.2), lw=lw, fill='#fff'); c.line(x1 - 1.6, y0, x1 - 1.6, y1, lw=lw)
        elif head == 'y0': c.rect((x0 + 0.2, y0 + 0.2, x1 - 0.2, y0 + 1.3), lw=lw, fill='#fff'); c.line(x0, y0 + 1.6, x1, y0 + 1.6, lw=lw)
        elif head == 'x0': c.rect((x0 + 0.2, y0 + 0.2, x0 + 1.3, y1 - 0.2), lw=lw, fill='#fff'); c.line(x0 + 1.6, y0, x0 + 1.6, y1, lw=lw)
        c.text((x0 + x1) / 2, (y0 + y1) / 2 - 0.6, f.get('label', 'QUEEN'), size=0.3)
    elif t == 'fireplace':
        # prefabricated/direct-vent unit box against a wall ('back' = 'y1' default) + hearth slab in front
        r = f['r']; x0, y0, x1, y1 = r; hd = f.get('hearth', 1.5); back = f.get('back', 'y1')
        c.rect(r, lw=0.04, fill='#fff')
        if back in ('y1', 'y0'):
            fb = (x0 + 0.6, y0 + 0.3, x1 - 0.6, y1 - 0.3); c.rect(fb, lw=lw, fill='#e8e8e8')
            hr = (x0 - 0.5, y0 - hd, x1 + 0.5, y0) if back == 'y1' else (x0 - 0.5, y1, x1 + 0.5, y1 + hd)
        else:
            fb = (x0 + 0.3, y0 + 0.6, x1 - 0.3, y1 - 0.6); c.rect(fb, lw=lw, fill='#e8e8e8')
            hr = (x0 - hd, y0 - 0.5, x0, y1 + 0.5) if back == 'x1' else (x1, y0 - 0.5, x1 + hd, y1 + 0.5)
        c.rect(hr, lw=0.025, fill='#f4f4f4', dash='0.2,0.12')
        c.text((hr[0] + hr[2]) / 2, (hr[1] + hr[3]) / 2, f.get('label', 'FIREPLACE'), size=f.get('ls', 0.3))

def find_wall(walls, ax, x, y, w, default_t=INT_T, default_ext=False):
    """Wall (t, ext, inward) hosting an opening. Collinear pieces with the same ext/inward/t are merged first so an
    opening that spans a grid cut (e.g. a window crossing an interior-partition line) still finds its wall."""
    lo, hi = (x - w / 2, x + w / 2) if ax == 'h' else (y - w / 2, y + w / 2)
    runs = {}
    for wl in walls:
        s = wl['seg']
        if wl['axis'] != ax or wl['open']: continue
        if (ax == 'h' and abs(s[1] - y) > 1e-6) or (ax == 'v' and abs(s[0] - x) > 1e-6): continue
        key = (wl['t'], wl['ext'], wl['inward'])
        runs.setdefault(key, []).append((s[0], s[2]) if ax == 'h' else (s[1], s[3]))
    for key, iv in runs.items():
        iv = sorted(iv); merged = []
        for a, b in iv:
            if merged and a <= merged[-1][1] + 1e-6: merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else: merged.append((a, b))
        if any(a - 1e-6 <= lo and hi <= b + 1e-6 for a, b in merged): return key
    return (default_t, default_ext, 1)

def draw_door(c, d, walls):
    x, y = d['at']; w = d['w']; ax = d['axis']; typ = d.get('type', 'door')
    # find wall thickness at the opening
    t, ext, inward = find_wall(walls, ax, x, y, w, INT_T, False)
    # opening rect (paint white over the wall poché)
    if ax == 'h':
        wy0, wy1 = ((y, y + t) if inward > 0 else (y - t, y)) if ext else (y - t / 2, y + t / 2)
        c.rect((x - w / 2, wy0 - 0.01, x + w / 2, wy1 + 0.01), fill='#fff', stroke='none')
        c.line(x - w / 2, wy0, x - w / 2, wy1, lw=0.03); c.line(x + w / 2, wy0, x + w / 2, wy1, lw=0.03)
        face = wy1 if d.get('swing', 1) > 0 else wy0
    else:
        wx0, wx1 = ((x, x + t) if inward > 0 else (x - t, x)) if ext else (x - t / 2, x + t / 2)
        c.rect((wx0 - 0.01, y - w / 2, wx1 + 0.01, y + w / 2), fill='#fff', stroke='none')
        c.line(wx0, y - w / 2, wx1, y - w / 2, lw=0.03); c.line(wx0, y + w / 2, wx1, y + w / 2, lw=0.03)
        face = wx1 if d.get('swing', 1) > 0 else wx0
    if typ == 'garage':
        if ax == 'h':
            c.line(x - w / 2, y + t / 2, x + w / 2, y + t / 2, lw=0.06)
            c.rect((x - w / 2, wy0, x + w / 2, wy1), fill='none', lw=0.03)
            c.text(x, y + t / 2 + 0.7, d.get('label', 'GARAGE DOOR %s' % fti(w)), size=0.36, weight='bold')
        return
    if typ == 'cased':
        if ax == 'h': c.line(x - w / 2, y, x + w / 2, y, lw=0.03, dash='0.3,0.2')
        else: c.line(x, y - w / 2, x, y + w / 2, lw=0.03, dash='0.3,0.2')
        return
    sw = d.get('swing', 1); hg = d.get('hinge', -1)
    leaves = 2 if typ == 'french' else 1
    lw_ = w / leaves
    for i in range(leaves):
        if ax == 'h':
            hx = (x - w / 2) if (hg < 0) ^ (i == 1) else (x + w / 2)
            dirx = 1 if hx < x else -1
            # leaf perpendicular to wall
            c.line(hx, face, hx, face + sw * lw_, lw=0.05)
            a_start = 90 if sw > 0 else -90
            a_end = 0 if dirx > 0 else (180 if sw > 0 else -180)     # always a 90-degree sweep
            c.arc(hx, face, lw_, a_start, a_end)
        else:
            hy = (y - w / 2) if (hg < 0) ^ (i == 1) else (y + w / 2)
            diry = 1 if hy < y else -1
            c.line(face, hy, face + sw * lw_, hy, lw=0.05)
            a_start = 0 if sw > 0 else 180
            a_end = 90 if diry > 0 else (-90 if sw > 0 else 270)     # always a 90-degree sweep
            c.arc(face, hy, lw_, a_start, a_end)
    if typ == 'bifold':
        pass
    lab = d.get('label') or ('%s' % fti(w))
    if ax == 'h': c.text(x, face + sw * 0.45 * lw_ + (0.25 if sw > 0 else -0.25), lab, size=0.28, color='#333') if d.get('show_label', True) else None
    else: c.text(face + sw * 0.45 * lw_, y + (w / 2 + 0.3) * (1 if d.get('lab_side', 1) > 0 else -1), lab, size=0.28, color='#333') if d.get('show_label', True) else None

def draw_window(c, wn, walls):
    x, y = wn['at']; w = wn['w']; ax = wn['axis']
    t, _ext, inward = find_wall(walls, ax, x, y, w, EXT_T, True)
    if ax == 'h':
        wy0, wy1 = (y, y + t) if inward > 0 else (y - t, y)
        c.rect((x - w / 2, wy0 - 0.01, x + w / 2, wy1 + 0.01), fill='#fff', stroke='none')
        for yy in (wy0, (wy0 + wy1) / 2, wy1): c.line(x - w / 2, yy, x + w / 2, yy, lw=0.03)
        c.line(x - w / 2, wy0, x - w / 2, wy1, lw=0.03); c.line(x + w / 2, wy0, x + w / 2, wy1, lw=0.03)
        c.text(x, (y - 0.55) if inward > 0 else (y + 0.55), fti(w), size=0.28, color='#333')
    else:
        wx0, wx1 = (x, x + t) if inward > 0 else (x - t, x)
        c.rect((wx0 - 0.01, y - w / 2, wx1 + 0.01, y + w / 2), fill='#fff', stroke='none')
        for xx in (wx0, (wx0 + wx1) / 2, wx1): c.line(xx, y - w / 2, xx, y + w / 2, lw=0.03)
        c.line(wx0, y - w / 2, wx1, y - w / 2, lw=0.03); c.line(wx0, y + w / 2, wx1, y + w / 2, lw=0.03)
        c.text((x - 0.55) if inward > 0 else (x + 0.55), y, fti(w), size=0.28, color='#333', rot=-90)

def dim_chain(c, pts, axis, pos, size=0.42, tick=0.22, ext_from=None):
    """Dimension string. axis 'h': pts are x values at line y=pos; 'v': pts are y values at line x=pos.
    ext_from: coordinate the extension lines start from (drawn thin up to the dimension line)."""
    pts = sorted(pts)
    if axis == 'h':
        c.line(pts[0] - 0.3, pos, pts[-1] + 0.3, pos, lw=0.03)
        for p in pts:
            if ext_from is not None: c.line(p, ext_from, p, pos + (0.3 if pos > ext_from else -0.3), lw=0.02, color='#555')
            c.line(p - tick, pos - tick, p + tick, pos + tick, lw=0.05)
        for a, b in zip(pts[:-1], pts[1:]):
            c.text((a + b) / 2, pos + 0.45, fti(b - a), size=size)
    else:
        c.line(pos, pts[0] - 0.3, pos, pts[-1] + 0.3, lw=0.03)
        for p in pts:
            if ext_from is not None: c.line(ext_from, p, pos + (0.3 if pos > ext_from else -0.3), p, lw=0.02, color='#555')
            c.line(pos - tick, p - tick, pos + tick, p + tick, lw=0.05)
        for a, b in zip(pts[:-1], pts[1:]):
            c.text(pos - 0.45, (a + b) / 2, fti(b - a), size=size, rot=-90)

# ----------------------------------------------------------------------------- analysis
def cond_polygon(spec):
    """Outer polygon of the conditioned envelope (union of `cond` rooms on the grid), via boundary edges."""
    rooms = [r for r in spec['rooms'] if r['kind'] == 'cond']
    walls = build_walls({'rooms': rooms, 'open_edges': []})
    edges = [w['seg'] for w in walls if w['ext']]
    # chain edges into a loop (rectilinear, single loop)
    from collections import defaultdict
    adj = defaultdict(list)
    for e in edges:
        a, b = (e[0], e[1]), (e[2], e[3]); adj[a].append(b); adj[b].append(a)
    start = min(adj); loop = [start]; prev = None; cur = start
    while True:
        nxt = [p for p in adj[cur] if p != prev]
        if not nxt: break
        nxt = nxt[0]
        if nxt == start: break
        loop.append(nxt); prev, cur = cur, nxt
    # drop collinear points
    out = []
    for i in range(len(loop)):
        a, b, d = loop[i - 1], loop[i], loop[(i + 1) % len(loop)]
        if (a[0] == b[0] == d[0]) or (a[1] == b[1] == d[1]): continue
        out.append(b)
    return ccw(out)

def exterior_openings(spec, walls):
    """Classify every door/window on an exterior wall: wall face + offset from the wall's left end seen from outside."""
    ext = [w for w in walls if w['ext']]
    X0 = min(w['seg'][0] for w in ext); X1 = max(w['seg'][2] for w in ext)
    Y0 = min(w['seg'][1] for w in ext); Y1 = max(w['seg'][3] for w in ext)
    res = []
    # merge collinear exterior pieces into runs keyed by (axis, line coordinate, inward)
    runs = {}
    for wl in ext:
        s = wl['seg']; key = (wl['axis'], round(s[1] if wl['axis'] == 'h' else s[0], 4), wl['inward'])
        runs.setdefault(key, []).append((s[0], s[2]) if wl['axis'] == 'h' else (s[1], s[3]))
    merged = {}
    for key, iv in runs.items():
        iv = sorted(iv); out = []
        for a, b in iv:
            if out and a <= out[-1][1] + 1e-6: out[-1] = (out[-1][0], max(out[-1][1], b))
            else: out.append((a, b))
        merged[key] = out
    items = [(d, 'door') for d in spec['doors']] + [(wn, 'window') for wn in spec['windows']]
    for it, cat in items:
        x, y = it['at']; w = it['w']; ax = it['axis']
        host = None
        lo, hi = (x - w / 2, x + w / 2) if ax == 'h' else (y - w / 2, y + w / 2)
        for key, iv in merged.items():
            if key[0] != ax or abs(key[1] - (y if ax == 'h' else x)) > 1e-6: continue
            if any(a - 1e-6 <= lo and hi <= b + 1e-6 for a, b in iv):
                host = {'inward': key[2]}; break
        if host is None: continue
        if ax == 'h':
            face = 'front' if host['inward'] > 0 else 'rear'     # room is at +y => wall faces the front (-y)
            # extent of the collinear exterior wall run containing this piece
            run = [wl['seg'] for wl in ext if wl['axis'] == 'h' and abs(wl['seg'][1] - y) < 1e-6 and wl['inward'] == host['inward']]
            rx0, rx1 = min(r[0] for r in run), max(r[2] for r in run)
            off = (x - w / 2 - rx0) if face == 'front' else (rx1 - (x + w / 2))
            line = y
        else:
            face = 'left' if host['inward'] > 0 else 'right'
            run = [wl['seg'] for wl in ext if wl['axis'] == 'v' and abs(wl['seg'][0] - x) < 1e-6 and wl['inward'] == host['inward']]
            ry0, ry1 = min(r[1] for r in run), max(r[3] for r in run)
            off = (ry1 - (y + w / 2)) if face == 'left' else (y - w / 2 - ry0)
            line = x
        typ = it.get('type', 'window' if cat == 'window' else 'door')
        res.append({'wall': face, 'wall_line_ft': round(line, 2), 'type': typ, 'offset_ft': round(off, 2),
                    'width_ft': round(w, 2), 'height_ft': round(it.get('h', 6.67 if cat == 'door' else 5.0), 2),
                    'sill_ft': round(it.get('sill', 0.0), 2), 'tag': it.get('tag', ''), 'at': [round(x, 2), round(y, 2)]})
    return res

def analyze(spec):
    walls = build_walls(spec)
    rooms = []
    for r in spec['rooms']:
        if r['kind'] in ('cond', 'garage'):
            cp = clear_poly(r, walls)
        else:
            cp = room_poly(r)
        bb = bbox(cp)
        lab = r.get('label_dims') or ('%s × %s' % (fti(bb[2] - bb[0]), fti(bb[3] - bb[1])))
        rooms.append({'name': r['name'], 'kind': r['kind'], 'polygon': [[round(x, 3), round(y, 3)] for x, y in room_poly(r)],
                      'clear_polygon': [[round(x, 3), round(y, 3)] for x, y in cp], 'area_sf': round(abs(poly_area(cp)), 1),
                      'label_dims': lab, 'clear_w_ft': round(bb[2] - bb[0], 2), 'clear_d_ft': round(bb[3] - bb[1], 2),
                      'bedroom': bool(r.get('bedroom')), 'bath': bool(r.get('bath'))})
    cp = cond_polygon(spec)
    cond_sf = abs(poly_area(cp))
    gar = [r for r in spec['rooms'] if r['kind'] == 'garage']
    por = [r for r in spec['rooms'] if r['kind'] == 'porch' and r.get('side', 'front') != 'rear']
    rpor = [r for r in spec['rooms'] if r['kind'] == 'porch' and r.get('side') == 'rear']
    pat = [r for r in spec['rooms'] if r['kind'] == 'patio']
    A = lambda rs: sum(abs(poly_area(room_poly(r))) for r in rs)
    areas = {'conditioned_sf': round(cond_sf, 1), 'conditioned_basis': 'outside face of exterior walls / centreline of garage separation wall (grid union of conditioned rooms)',
             'garage_sf': round(A(gar), 1), 'front_porch_sf': round(A(por), 1), 'rear_porch_covered_sf': round(A(rpor), 1),
             'rear_patio_uncovered_sf': round(A(pat), 1),
             'total_under_roof_sf': round(cond_sf + A(gar) + A(por) + A(rpor), 1),
             'total_under_roof_basis': 'conditioned + garage + covered porch(es) (patio uncovered, excluded)',
             'sum_of_room_clear_sf': round(sum(r['area_sf'] for r in rooms if r['kind'] == 'cond'), 1)}
    allp = [q for r in spec['rooms'] for q in room_poly(r)]
    bb_body = bbox([q for r in spec['rooms'] if r['kind'] in ('cond', 'garage') for q in room_poly(r)])
    bb_all = bbox(allp)
    # roof
    plate = spec['roof']['plate_ft']; heel = spec['roof'].get('heel_ft', 0.5)
    roof_el = []
    for e in spec['roof']['elements']:
        rise = (e['span_ft'] / 2.0) * e['pitch'][0] / e['pitch'][1] if e.get('form', 'gable') == 'gable' else e['span_ft'] * e['pitch'][0] / e['pitch'][1]
        roof_el.append(dict(e, rise_ft=round(rise, 2), ridge_height_ft=round(plate + heel + rise, 2),
                            basis='plate %.1f ft + heel %.2f ft + (span/2)·pitch' % (plate, heel) if e.get('form', 'gable') == 'gable' else 'plate + heel + span·pitch (shed)'))
    roof = {'plate_ft': plate, 'heel_ft': heel, 'elements': roof_el, 'max_ridge_ft': max(e['ridge_height_ft'] for e in roof_el),
            'ridge_direction': spec['roof']['ridge_direction']}
    return {'walls': walls, 'rooms': rooms, 'cond_poly': cp, 'areas': areas, 'body_bbox': bb_body, 'all_bbox': bb_all,
            'exterior_openings': exterior_openings(spec, walls), 'roof': roof}

def run_checks(spec, an):
    fails = []
    def chk(ok, msg):
        print(('  PASS  ' if ok else '  FAIL  ') + msg)
        if not ok: fails.append(msg)
    rooms = an['rooms']; areas = an['areas']
    # 1 rooms tile the conditioned envelope (grid areas)
    grid_sum = sum(abs(poly_area(room_poly(r))) for r in spec['rooms'] if r['kind'] == 'cond')
    chk(abs(grid_sum - areas['conditioned_sf']) / areas['conditioned_sf'] <= 0.03,
        'rooms tile the conditioned envelope: grid sum %.1f vs envelope %.1f sf' % (grid_sum, areas['conditioned_sf']))
    # 2 min clear width
    for r in rooms:
        spec_r = next(s for s in spec['rooms'] if s['name'] == r['name'])
        if r['kind'] != 'cond' or spec_r.get('narrow_ok'): continue
        chk(min(r['clear_w_ft'], r['clear_d_ft']) >= 8.0, '%s narrowest clear dim %.2f ft ≥ 8 ft' % (r['name'], min(r['clear_w_ft'], r['clear_d_ft'])))
    # 3 bedrooms
    for r in rooms:
        if not r['bedroom']: continue
        chk(r['area_sf'] >= 120, '%s area %.0f sf ≥ 120 sf' % (r['name'], r['area_sf']))
        spec_r = next(s for s in spec['rooms'] if s['name'] == r['name']); rp = room_poly(spec_r)
        nwin = 0
        for wn in spec['windows']:
            x, y = wn['at']
            # window on this room's boundary?
            for e in split_edges(rp):
                k = seg_key(e)
                if (wn['axis'] == 'h' and abs(k[1] - y) < 1e-6 and k[0] - 1e-6 <= x <= k[2] + 1e-6) or \
                   (wn['axis'] == 'v' and abs(k[0] - x) < 1e-6 and k[1] - 1e-6 <= y <= k[3] + 1e-6): nwin += 1; break
        chk(nwin >= 1, '%s has %d window(s)' % (r['name'], nwin))
    # 4 baths: 60-in circle clear of fixtures (door swings and curbless shower floor allowed)
    for spec_r in spec['rooms']:
        if not spec_r.get('bath'): continue
        cx, cy = spec_r['circle']; rr = 2.5
        cp = next(r for r in rooms if r['name'] == spec_r['name'])['clear_polygon']
        inside = all(point_in_poly((cx + rr * math.cos(a), cy + rr * math.sin(a)), cp) for a in [i * math.pi / 12 for i in range(24)])
        hits = []
        for f in spec_r.get('fixtures', []):
            if f['t'] in ('shower',) or 'r' not in f: continue
            x0, y0, x1, y1 = f['r']
            ddx = max(x0 - cx, 0, cx - x1); ddy = max(y0 - cy, 0, cy - y1)
            if math.hypot(ddx, ddy) < rr - 0.01: hits.append(f['t'])
        chk(inside and not hits, '%s 60-in turning circle at (%.1f, %.1f) clear (inside=%s, hits=%s)' % (spec_r['name'], cx, cy, inside, hits))
    # 5 garage clear
    for r in rooms:
        if r['kind'] == 'garage':
            chk(r['clear_w_ft'] >= 20 and r['clear_d_ft'] >= 21, 'garage clear %.2f × %.2f ft ≥ 20 × 21' % (r['clear_w_ft'], r['clear_d_ft']))
    # 6 width
    bb = an['body_bbox']
    chk(bb[2] - bb[0] <= 40.0 + 1e-6, 'overall body width %.2f ft ≤ 40 ft' % (bb[2] - bb[0]))
    # 7 conditioned area
    tgt = spec['target_cond_sf']
    chk(abs(areas['conditioned_sf'] - tgt) / tgt <= 0.03, 'conditioned %.1f sf within ±3%% of %d (%.1f%%)' % (areas['conditioned_sf'], tgt, 100 * (areas['conditioned_sf'] - tgt) / tgt))
    # 8 openings consistent with walls (each opening fully inside one wall run; no overlaps)
    walls = an['walls']; placed = []
    for it in spec['doors'] + spec['windows']:
        x, y = it['at']; w = it['w']; ax = it['axis']; ok = False
        run = [wl['seg'] for wl in walls if wl['axis'] == ax and not wl['open'] and
               ((ax == 'h' and abs(wl['seg'][1] - y) < 1e-6) or (ax == 'v' and abs(wl['seg'][0] - x) < 1e-6))]
        lo, hi = (x - w / 2, x + w / 2) if ax == 'h' else (y - w / 2, y + w / 2)
        # coverage by union of collinear wall pieces
        cov = sorted([(s[0], s[2]) if ax == 'h' else (s[1], s[3]) for s in run])
        merged = []
        for a, b in cov:
            if merged and a <= merged[-1][1] + 1e-6: merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else: merged.append((a, b))
        ok = any(a - 1e-6 <= lo and hi <= b + 1e-6 for a, b in merged)
        ov = [p for p in placed if p[0] == ax and abs(p[1] - (y if ax == 'h' else x)) < 1e-6 and not (hi <= p[2] + 0.01 or lo >= p[3] - 0.01)]
        placed.append((ax, y if ax == 'h' else x, lo, hi))
        chk(ok and not ov, 'opening %s %s w=%.2f at (%.2f, %.2f) sits in a wall (in-wall=%s, overlaps=%d)' % (it.get('type', 'window'), it.get('tag', ''), w, x, y, ok, len(ov)))
    # 9 ridge
    chk(an['roof']['max_ridge_ft'] <= 24.0, 'max ridge %.2f ft ≤ 24 ft (FACTS §4)' % an['roof']['max_ridge_ft'])
    # 10 fixtures inside their room's clear polygon and not overlapping each other
    for spec_r in spec['rooms']:
        cp = next(r for r in rooms if r['name'] == spec_r['name'])['clear_polygon']
        fx = [f for f in spec_r.get('fixtures', []) if 'r' in f]
        for i, f in enumerate(fx):
            x0, y0, x1, y1 = f['r']
            ins = all(point_in_poly((px, py), cp) for px, py in ((x0 + .01, y0 + .01), (x1 - .01, y0 + .01), (x1 - .01, y1 - .01), (x0 + .01, y1 - .01)))
            ovl = [g['t'] for g in fx[i + 1:] if rects_overlap(f['r'], g['r'])]
            chk(ins and not ovl, '%s fixture %s inside room and clear of others (inside=%s, overlaps=%s)' % (spec_r['name'], f['t'], ins, ovl))
    return fails

# ----------------------------------------------------------------------------- plan assembly
def draw_plan(spec, an, c, with_dims=True, legend=True):
    walls = an['walls']
    # porch / patio slabs first
    for r in spec['rooms']:
        if r['kind'] == 'porch':
            c.poly(room_poly(r), fill='#f3efe6', stroke='#111', lw=0.04)
        elif r['kind'] == 'patio':
            c.poly(room_poly(r), fill='#eeeeee', stroke='#111', lw=0.04, dash='0.4,0.2')
    # floors
    for r in spec['rooms']:
        if r['kind'] == 'garage': c.poly(room_poly(r), fill='#f6f6f6', stroke='none')
        elif r['kind'] == 'cond': c.poly(room_poly(r), fill='#ffffff', stroke='none')
    # walls (poché)
    for w in walls:
        if w['open']:
            x0, y0, x1, y1 = w['seg']; c.line(x0, y0, x1, y1, lw=0.03, dash='0.35,0.2', color='#333'); continue
        c.rect(wall_rect(w), fill='#2b2b2b' if w['ext'] else '#555', stroke='#111', lw=0.02)
    # closet rods / shelves
    for r in spec['rooms']:
        for s in r.get('closet_rod', []):
            x0, y0, x1, y1 = s; c.rect(s, fill='none', lw=0.025, color='#333') if False else c.rect(s, fill='none', lw=0.025)
            if (x1 - x0) >= (y1 - y0): c.line(x0, (y0 + y1) / 2, x1, (y0 + y1) / 2, lw=0.025, dash='0.25,0.15')
            else: c.line((x0 + x1) / 2, y0, (x0 + x1) / 2, y1, lw=0.025, dash='0.25,0.15')
    # fixtures
    for r in spec['rooms']:
        for f in r.get('fixtures', []): draw_fixture(c, f)
        if r.get('circle'):
            cx, cy = r['circle']; c.circle(cx, cy, 2.5, lw=0.025, dash='0.3,0.2', stroke='#1a6faa'); c.text(cx, cy, '5\'-0" Ø', size=0.3, color='#1a6faa')
    # openings
    for d in spec['doors']: draw_door(c, d, walls)
    for wn in spec['windows']: draw_window(c, wn, walls)
    # porch columns
    for (px, py) in spec.get('porch_columns', []):
        c.rect((px - 0.33, py - 0.33, px + 0.33, py + 0.33), fill='#2b2b2b', lw=0.02)
    # room labels
    for r, ra in zip(spec['rooms'], an['rooms']):
        cp = ra['clear_polygon']; bb = bbox(cp)
        lx, ly = r.get('label_at', ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2))
        size = r.get('label_size', 0.5)
        rot = r.get('label_rot', 0)
        if rot:
            c.text(lx - 0.3, ly, r.get('label', r['name']), size=size, weight='bold', rot=rot)
            c.text(lx + 0.35, ly, ra['label_dims'], size=size * 0.8, rot=rot)
        else:
            c.text(lx, ly + 0.35, r.get('label', r['name']), size=size, weight='bold')
            c.text(lx, ly - 0.35, ra['label_dims'], size=size * 0.8)
        if r.get('sub'): c.text(lx, ly - 0.95, r['sub'], size=size * 0.65, italic=True, color='#333')
    # dimension strings
    bb = an['all_bbox']
    if with_dims:
        D = spec['dims']
        for i, chain in enumerate(D.get('front', [])):
            dim_chain(c, chain, 'h', bb[1] - 2.0 - 2.0 * i, ext_from=bb[1] - 0.2)
        for i, chain in enumerate(D.get('rear', [])):
            dim_chain(c, chain, 'h', bb[3] + 2.0 + 2.0 * i, ext_from=bb[3] + 0.2)
        for i, chain in enumerate(D.get('left', [])):
            dim_chain(c, chain, 'v', bb[0] - 2.0 - 2.0 * i, ext_from=bb[0] - 0.2)
        for i, chain in enumerate(D.get('right', [])):
            dim_chain(c, chain, 'v', bb[2] + 2.5 + 2.0 * i, ext_from=bb[2] + 0.2)
        for ch in D.get('interior', []):
            dim_chain(c, ch['pts'], ch['axis'], ch['pos'], size=0.36, tick=0.18)
    # front toward lane note
    if not with_dims: return None
    fx = (bb[0] + bb[2]) / 2
    nf = len(spec['dims'].get('front', [])); yy = bb[1] - 2.0 - 2.0 * nf - 0.6
    c.text(fx, yy, '▼  FRONT — TOWARD THE LANE (ENTRY, GARAGE, PORCH FACE AT THE 15-FT SETBACK LINE)  ▼', size=0.5, weight='bold')
    return yy

def draw_legend(c, x, y, w=14.0):
    """Legend block; returns bottom y."""
    c.text(x, y, 'LEGEND', size=0.5, weight='bold', anchor='start'); y -= 1.0
    c.rect((x, y - 0.3, x + 1.6, y + 0.3), fill='#2b2b2b', lw=0.02); c.text(x + 2.2, y, 'Exterior wall — 2×6 @ 6 in (poché)', size=0.4, anchor='start'); y -= 0.9
    c.rect((x, y - 0.2, x + 1.6, y + 0.2), fill='#555', lw=0.02); c.text(x + 2.2, y, 'Interior partition — 2×4 @ 4 in', size=0.4, anchor='start'); y -= 0.9
    c.line(x, y, x + 1.6, y, lw=0.03, dash='0.35,0.2'); c.text(x + 2.2, y, 'Cased opening / ceiling beam (no wall)', size=0.4, anchor='start'); y -= 0.9
    for yy in (y - 0.25, y, y + 0.25): c.line(x, yy, x + 1.6, yy, lw=0.03)
    c.text(x + 2.2, y, 'Window (triple line), width noted', size=0.4, anchor='start'); y -= 0.9
    c.line(x, y - 0.3, x, y + 0.5, lw=0.05); c.arc(x, y - 0.3, 0.8, 90, 0); c.text(x + 2.2, y, 'Door leaf + swing, width noted (36 in typ.)', size=0.4, anchor='start'); y -= 1.0
    c.circle(x + 0.8, y, 0.5, lw=0.025, dash='0.3,0.2', stroke='#1a6faa'); c.text(x + 2.2, y, '5\'-0" turning circle (ANSI A117.1-type)', size=0.4, anchor='start'); y -= 0.9
    c.rect((x, y - 0.3, x + 1.6, y + 0.3), fill='none', lw=0.025); c.line(x, y, x + 1.6, y, lw=0.025, dash='0.25,0.15'); c.text(x + 2.2, y, 'Closet shelf + rod', size=0.4, anchor='start'); y -= 0.9
    c.rect((x, y - 0.3, x + 1.6, y + 0.3), fill='#f3efe6', lw=0.03); c.text(x + 2.2, y, 'Covered porch slab', size=0.4, anchor='start'); y -= 0.9
    c.rect((x, y - 0.3, x + 1.6, y + 0.3), fill='#eeeeee', lw=0.03, dash='0.4,0.2'); c.text(x + 2.2, y, 'Uncovered patio slab', size=0.4, anchor='start'); y -= 0.9
    return y

def draw_scalebar(c, x, y, label='SCALE BAR — 4 FT'):
    for i in range(4):
        c.rect((x + i, y - 0.25, x + i + 1, y + 0.25), fill='#111' if i % 2 == 0 else '#fff', lw=0.03)
    for i in range(5): c.text(x + i, y - 0.7, str(i), size=0.35)
    c.text(x + 2, y + 0.75, label + '  (1 FT DIVISIONS)', size=0.38)

def draw_notes(c, x, y, notes, size=0.38, width_chars=95):
    c.text(x, y, 'NOTES', size=0.5, weight='bold', anchor='start'); y -= 0.9
    import textwrap
    for i, n in enumerate(notes, 1):
        lines = textwrap.wrap(n, width_chars)
        for j, ln in enumerate(lines):
            c.text(x, y, ('%d.  ' % i if j == 0 else '     ') + ln, size=size, anchor='start'); y -= size * 1.5
        y -= 0.2
    return y

def area_table_rows(spec, an):
    a = an['areas']; rows = [('Conditioned (heated) area', a['conditioned_sf'], 'outside face of ext. walls'),
                             ('2-car garage', a['garage_sf'], 'outside face / centreline'),
                             ('Covered front porch', a['front_porch_sf'], 'slab')]
    if a['rear_porch_covered_sf'] > 0:
        rows.append(('Covered rear porch (recessed under main roof)', a['rear_porch_covered_sf'], 'slab'))
        rows.append(('TOTAL UNDER ROOF', a['total_under_roof_sf'], 'cond. + garage + porches'))
    else:
        rows.append(('TOTAL UNDER ROOF', a['total_under_roof_sf'], 'cond. + garage + porch'))
    if a['rear_patio_uncovered_sf'] > 0 or not a['rear_porch_covered_sf']:
        rows.append(('Rear patio (uncovered, not under roof)', a['rear_patio_uncovered_sf'], 'slab'))
    return rows

def draw_area_table(c, x, y, spec, an, w=17.0):
    c.text(x, y, 'AREA TABULATION — computed by tools/floorplans.py from the wall-face polygons', size=0.45, weight='bold', anchor='start'); y -= 0.9
    for name, v, basis in area_table_rows(spec, an):
        bold = name.startswith('TOTAL')
        c.text(x, y, name, size=0.4, anchor='start', weight='bold' if bold else 'normal')
        c.text(x + w - 4.2, y, '%s SF' % format(int(round(v)), ','), size=0.4, anchor='end', weight='bold' if bold else 'normal')
        c.text(x + w, y, basis, size=0.3, anchor='end', color='#444'); y -= 0.75
    c.line(x, y + 0.35, x + w, y + 0.35, lw=0.02)
    c.text(x, y, 'Program target %s conditioned (FACTS §4 nominal %s); Lilburn Table 4.1 R-2 cottage min heated 1,000 SF.' % (format(spec['target_cond_sf'], ','), spec['nominal_body']), size=0.32, anchor='start', color='#333'); y -= 0.6
    y -= 0.3
    c.text(x, y, 'ROOM SCHEDULE (clear, inside face)', size=0.45, weight='bold', anchor='start'); y -= 0.8
    for r in an['rooms']:
        if r['kind'] not in ('cond', 'garage'): continue
        c.text(x, y, r['name'], size=0.36, anchor='start'); c.text(x + w - 4.2, y, r['label_dims'], size=0.34, anchor='end'); c.text(x + w, y, '%d SF' % round(r['area_sf']), size=0.34, anchor='end'); y -= 0.62
    return y

def wrap_svg(body, vb, w_px=None, h_px=None, scale=1.0, bg='#fff'):
    x0, y0, x1, y1 = vb
    W = (x1 - x0) * scale; H = (y1 - y0) * scale
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%.1f" height="%.1f" viewBox="%.3f %.3f %.3f %.3f" font-family="Helvetica, Arial, sans-serif">'
            '<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" fill="%s"/>\n%s\n</svg>' %
            (W, H, x0, y0, x1 - x0, y1 - y0, x0, y0, x1 - x0, y1 - y0, bg, body))

# ============================================================================= PLAN SPECS
MATERIALS_BY_SCHEME = {
    '1': {'name': 'Warm White', 'siding': 'fiber-cement board-and-batten (12-in o.c. battens), warm white', 'base': 'stacked/ledge stone water table (30 in) and porch piers',
          'roof': 'architectural asphalt shingle, weathered wood / charcoal', 'trim': 'painted fiber-cement trim, soft white; 8×8 cedar porch posts + brackets', 'door': 'front door deep green or black; garage door carriage-style, painted to match trim'},
    '2': {'name': 'Sage', 'siding': 'fiber-cement lap siding, 6-in exposure, sage green', 'base': 'brick veneer water table (30 in), red-brown blend; brick porch piers',
          'roof': 'architectural asphalt shingle, charcoal', 'trim': 'painted trim, soft white; 8×8 cedar posts', 'door': 'front door natural stain or oxblood; garage door painted to match siding'},
    '3': {'name': 'Clay', 'siding': 'fiber-cement lap siding, 6-in exposure, clay/beige', 'base': 'ledge stone water table (30 in) and porch piers, buff blend',
          'roof': 'architectural asphalt shingle, weathered wood', 'trim': 'painted trim, cream; 8×8 cedar posts', 'door': 'front door navy; garage door painted to match trim'},
    'source': 'docs/12-outline-specifications.md (04 20 00, 04 40 00, 07 31 00, 07 46 46, 09 91 13); FACTS §4 "three color schemes (warm white / sage / clay)"'}

ACCESSIBILITY_A = [
    ('Zero-step entries', 'front porch (slab flush with finished floor) and garage-to-mud-room door; patio door ≤ 1/2-in threshold', 'design intent'),
    ('Door clear width', 'all passage doors 36 in (3\'-0"); closets 30 in; french door 6\'-0"', 'design intent'),
    ('Hall width', 'main hall 3\'-6" clear (42 in); suite hall 4\'-0" clear', 'design intent'),
    ('Turning circles', '5\'-0" (60 in) circle drawn and checked clear in both baths', 'checked by script'),
    ('Curbless shower', 'primary bath 5\'-0" × 3\'-10" curbless (recessed slab per 03 30 00 §2.05)', 'design intent'),
    ('Grab-bar blocking', '2×10 solid blocking 33–36 in AFF at all toilets, tub and showers (2024 IRC (GA 2026) — voluntary; ANSI A117.1 Type C-type)', 'design intent — VERIFY blocking heights with architect'),
    ('Plate height / vaulted', '9\'-0" plate; great room vaulted', 'design intent'),
    ('Single-level living', '1 story; no interior steps; laundry on the living level', 'design intent'),
    ('Lever hardware, rocker switches, 48-in max reach', 'to be specified (Division 08 / 26)', 'later stage'),
    ('Lilburn §734 visitability', 'applies to attached dwellings only; voluntarily exceeded (100% zero-step)', 'appears consistent with Ord. 2023-603 §734 (not applicable)'),
]

PLAN_A = {
    'id': 'A', 'name': 'THE SPRINGBROOK', 'date': DATE, 'target_cond_sf': 1444, 'nominal_body': '38\'-0" × 38\'-0"',
    'program': '2 BR / 2 BA, 1 story, 2-car front-loaded garage recessed 5\'-0", covered front porch, rear patio',
    'rooms': [
        {'name': '2-CAR GARAGE', 'kind': 'garage', 'rect': (0, 5, 21, 26.83), 'sub': 'ZERO-STEP DOOR TO MUD ROOM', 'label_at': (10.5, 13.5)},
        {'name': 'HALL', 'kind': 'cond', 'rect': (21, 0, 25.17, 26.83), 'narrow_ok': True, 'label_rot': -90, 'label_at': (23.3, 13.5), 'label_size': 0.4},
        {'name': 'BEDROOM 2', 'kind': 'cond', 'poly': [(25.17, 0), (38, 0), (38, 14), (31, 14), (31, 11.5), (25.17, 11.5)], 'bedroom': True,
         'label_at': (30.2, 9.4), 'label_size': 0.45, 'label_dims': '12\'-2" × 10\'-10"',
         'fixtures': [{'t': 'bed', 'r': (30.8, 2.5, 37.45, 7.5), 'head': 'x1', 'label': 'QUEEN'}]},
        {'name': 'CLOSET', 'kind': 'cond', 'rect': (25.17, 11.5, 31, 14), 'narrow_ok': True, 'label': 'CLO. — BIFOLD 5\'-0"', 'label_size': 0.28, 'label_at': (28.0, 12.7),
         'closet_rod': [(25.33, 11.9, 30.83, 13.83)]},
        {'name': 'BATH 2', 'kind': 'cond', 'rect': (25.17, 14, 38, 22.17), 'bath': True, 'narrow_ok': True, 'circle': (29.5, 16.7), 'label_at': (32.4, 17.7), 'label_size': 0.4,
         'fixtures': [{'t': 'tub', 'r': (35.0, 14.17, 37.5, 19.17), 'rot': 90}, {'t': 'vanity', 'r': (25.33, 20.17, 29.33, 22.0), 'sinks': 1},
                      {'t': 'toilet', 'r': (30.3, 19.5, 32.8, 22.0), 'back': 'y1'}]},
        {'name': 'COAT', 'kind': 'cond', 'rect': (25.17, 22.17, 28.17, 26.83), 'narrow_ok': True, 'label_size': 0.3, 'label_at': (27.0, 24.5), 'label_rot': -90,
         'closet_rod': [(26.0, 22.33, 28.0, 26.67)]},
        {'name': 'PANTRY', 'kind': 'cond', 'rect': (28.17, 22.17, 38, 26.83), 'narrow_ok': True, 'label_size': 0.36, 'label_at': (33.6, 25.3),
         'fixtures': [{'t': 'shelf', 'r': (28.33, 22.33, 37.5, 23.83)}, {'t': 'shelf', 'r': (36.0, 23.83, 37.5, 26.67)}]},
        {'name': 'LAUNDRY / MUD', 'kind': 'cond', 'rect': (14, 26.83, 21, 37.5), 'narrow_ok': True, 'label_size': 0.36, 'label_at': (18.8, 32.6),
         'fixtures': [{'t': 'washer', 'r': (14.17, 30.0, 16.67, 32.5)}, {'t': 'dryer', 'r': (14.17, 32.5, 16.67, 35.0)},
                      {'t': 'wh', 'c': (19.85, 36.3), 'rad': 0.9}, {'t': 'bench', 'r': (15.3, 35.9, 18.6, 37.33)}]},
        {'name': 'KITCHEN / DINING', 'kind': 'cond', 'rect': (21, 26.83, 38, 37.5), 'label_at': (24.9, 28.5), 'label_size': 0.45,
         'fixtures': [{'t': 'counter', 'r': (35.5, 27.0, 37.5, 29.5)}, {'t': 'range', 'r': (35.0, 29.5, 37.5, 32.0)}, {'t': 'counter', 'r': (35.5, 32.0, 37.5, 33.0)},
                      {'t': 'sink', 'r': (35.5, 33.0, 37.5, 35.5)}, {'t': 'dw', 'r': (35.5, 35.5, 37.5, 37.5)},
                      {'t': 'fridge', 'r': (32.0, 27.0, 35.0, 29.5), 'label': 'REF', 'ls': 0.3},
                      {'t': 'island', 'r': (28.5, 29.8, 31.5, 36.5), 'label': 'ISLAND 3\'×6\'-8"', 'rot': -90, 'ls': 0.3},
                      {'t': 'table', 'r': (22.6, 30.5, 25.6, 35.5), 'label': 'DINING', 'rot': -90, 'ls': 0.3}]},
        {'name': 'W.I.C.', 'kind': 'cond', 'rect': (0, 26.83, 14, 32.5), 'narrow_ok': True, 'label_size': 0.36, 'label_at': (6.5, 30.7),
         'closet_rod': [(0.5, 27.0, 13.83, 29.0), (11.83, 29.0, 13.83, 32.33)]},
        {'name': 'PRIMARY BATH', 'kind': 'cond', 'rect': (0, 32.5, 14, 41), 'bath': True, 'narrow_ok': True, 'circle': (8.2, 38.2), 'label_at': (8.2, 35.35), 'label_size': 0.4,
         'fixtures': [{'t': 'vanity', 'r': (4.0, 32.67, 11.0, 34.5), 'sinks': 2}, {'t': 'toilet', 'r': (11.4, 34.5, 13.83, 37.0), 'back': 'x1'},
                      {'t': 'shower', 'r': (0.5, 37.0, 5.5, 40.83), 'label': 'CURBLESS', 'dx': 1.0, 'dy': 40.3}]},
        {'name': 'PRIMARY BEDROOM', 'kind': 'cond', 'rect': (0, 41, 14, 51.83), 'bedroom': True, 'label_at': (4.0, 46.9), 'label_size': 0.42,
         'fixtures': [{'t': 'bed', 'r': (7.3, 44.5, 13.7, 51.3), 'head': 'y1', 'label': 'KING'}]},
        {'name': 'SUITE HALL', 'kind': 'cond', 'rect': (14, 37.5, 18.17, 45), 'narrow_ok': True, 'label_size': 0.3, 'label_rot': -90, 'label_at': (16.1, 41.2)},
        {'name': 'GREAT ROOM', 'kind': 'cond', 'poly': [(18.17, 37.5), (38, 37.5), (38, 51.83), (14, 51.83), (14, 45), (18.17, 45)], 'vaulted': True,
         'label_dims': '19\'-4" × 13\'-10"', 'sub': 'VAULTED CEILING', 'label_at': (28.0, 47.6), 'label_size': 0.55,
         'fixtures': [{'t': 'sofa', 'r': (23.5, 41.0, 31.0, 44.0)}]},
        {'name': 'COVERED PORCH', 'kind': 'porch', 'rect': (21, -6, 38, 0), 'sub': 'ZERO-STEP ENTRY · UNDER THE FRONT GABLE', 'label_size': 0.42},
        {'name': 'PATIO (UNCOVERED)', 'kind': 'patio', 'rect': (21, 51.83, 33, 57.83), 'label_size': 0.4},
    ],
    'open_edges': [(21, 37.5, 38, 37.5), (21, 26.83, 25.17, 26.83), (18.17, 37.5, 18.17, 45)],
    'doors': [
        {'at': (23.08, 0), 'axis': 'h', 'w': 3.0, 'hinge': -1, 'swing': 1, 'type': 'door', 'h': 6.67, 'tag': 'entry'},
        {'at': (10.5, 5), 'axis': 'h', 'w': 16.0, 'type': 'garage', 'h': 7.0, 'tag': 'garage 16x7', 'label': 'GARAGE DOOR 16\'-0" × 7\'-0"'},
        {'at': (16.5, 26.83), 'axis': 'h', 'w': 3.0, 'hinge': -1, 'swing': 1, 'type': 'door', 'tag': 'garage-mud'},
        {'at': (21, 32.5), 'axis': 'v', 'w': 3.0, 'hinge': -1, 'swing': -1, 'type': 'door', 'tag': 'mud-kitchen'},
        {'at': (25.17, 7.5), 'axis': 'v', 'w': 3.0, 'hinge': -1, 'swing': 1, 'type': 'door', 'tag': 'bedroom 2'},
        {'at': (25.17, 17.0), 'axis': 'v', 'w': 3.0, 'hinge': -1, 'swing': 1, 'type': 'door', 'tag': 'bath 2'},
        {'at': (25.17, 24.5), 'axis': 'v', 'w': 2.5, 'hinge': -1, 'swing': -1, 'type': 'door', 'tag': 'coat'},
        {'at': (30.33, 26.83), 'axis': 'h', 'w': 2.67, 'hinge': -1, 'swing': -1, 'type': 'door', 'tag': 'pantry'},
        {'at': (28.0, 11.5), 'axis': 'h', 'w': 5.0, 'swing': -1, 'type': 'french', 'tag': 'closet bifold', 'show_label': False},
        {'at': (2.5, 32.5), 'axis': 'h', 'w': 2.5, 'hinge': -1, 'swing': -1, 'type': 'door', 'tag': 'wic'},
        {'at': (8.5, 41), 'axis': 'h', 'w': 3.0, 'hinge': -1, 'swing': 1, 'type': 'door', 'tag': 'primary bath (out-swing)'},
        {'at': (14, 43.0), 'axis': 'v', 'w': 3.0, 'hinge': -1, 'swing': -1, 'type': 'door', 'tag': 'primary bedroom'},
        {'at': (27.0, 51.83), 'axis': 'h', 'w': 6.0, 'swing': -1, 'type': 'french', 'h': 6.67, 'tag': 'patio french door'},
    ],
    'windows': [
        {'at': (33.0, 0), 'axis': 'h', 'w': 6.0, 'h': 5.0, 'sill': 2.67, 'tag': 'BR2 front twin 3-0x5-0 (egress)'},
        {'at': (38, 10.5), 'axis': 'v', 'w': 3.0, 'h': 5.0, 'sill': 2.67, 'tag': 'BR2 side'},
        {'at': (38, 20.5), 'axis': 'v', 'w': 2.0, 'h': 2.5, 'sill': 4.5, 'tag': 'bath 2'},
        {'at': (38, 34.25), 'axis': 'v', 'w': 3.5, 'h': 3.0, 'sill': 3.5, 'tag': 'kitchen over sink'},
        {'at': (38, 44.0), 'axis': 'v', 'w': 6.0, 'h': 5.0, 'sill': 2.67, 'tag': 'great room twin'},
        {'at': (35.0, 51.83), 'axis': 'h', 'w': 5.0, 'h': 5.0, 'sill': 2.67, 'tag': 'great room rear'},
        {'at': (4.5, 51.83), 'axis': 'h', 'w': 5.0, 'h': 5.0, 'sill': 2.67, 'tag': 'primary rear (egress)'},
        {'at': (0, 46.5), 'axis': 'v', 'w': 6.0, 'h': 5.0, 'sill': 2.67, 'tag': 'primary side twin'},
        {'at': (0, 35.25), 'axis': 'v', 'w': 2.5, 'h': 2.5, 'sill': 4.5, 'tag': 'primary bath'},
        {'at': (0, 15.0), 'axis': 'v', 'w': 3.0, 'h': 3.0, 'sill': 4.0, 'tag': 'garage'},
    ],
    'porch_columns': [(21.33, -5.67), (29.5, -5.67), (37.67, -5.67)],
    'roof': {'plate_ft': 9.0, 'heel_ft': 0.5, 'ridge_direction': 'main ridge parallel to the lane (x) over the 25-ft rear block; a front-facing 8:12 gable over the 17-ft front wing, carried 6 ft forward over the covered porch; a subordinate front-facing 6:12 gable over the 21-ft garage',
             'elements': [{'name': 'main gable (rear block)', 'span_ft': 25.0, 'pitch': (8, 12), 'ridge': 'x'},
                          {'name': 'front-wing gable (extended over the porch)', 'span_ft': 17.0, 'pitch': (8, 12), 'ridge': 'y'},
                          {'name': 'garage gable', 'span_ft': 21.0, 'pitch': (6, 12), 'ridge': 'y'}]},
    'accessibility': ACCESSIBILITY_A,
    'materials_by_scheme': MATERIALS_BY_SCHEME,
    'dims': {'front': [[0, 2.5, 18.5, 21, 25.17, 38], [0, 21, 38], [0, 38]],
             'rear': [[0, 14, 21, 33, 38], [0, 38]],
             'left': [[5, 26.83, 32.5, 41, 51.83], [0, 5, 51.83], [-6, 0, 51.83, 57.83]],
             'right': [[-6, 0, 14, 22.17, 26.83, 37.5, 51.83], [-6, 0, 51.83]],
             'interior': [{'axis': 'v', 'pos': 6.0, 'pts': [5, 26.83]}, {'axis': 'h', 'pos': 22.5, 'pts': [0, 21]}]},
    'envelope_note': 'program body 38 × 38 nominal; actual envelope is L-shaped because the 2-car garage must be a front wing under the 40-ft width cap',
    'verify': ['Rear patio depth 8 ft vs 20-ft buffer easement (drawn 7 ft) — Planning staff / Dev. Regs. App. B',
               'Egress window net clear opening — 2024 IRC (GA 2026) R310 at unit selection',
               'Grab-bar blocking heights and ANSI A117.1 references — architect of record',
               'Max impervious / lot coverage for R-2 — Lilburn Development Regulations App. B §5.9 (not retrievable online)',
               'data/layout.json house_rect assumes a 38 × 38 footprint; the actual envelope is 38 × 51\'-10" + porch/patio — the site-plan agent must re-check lot fit (rear wall 27 ft from the rear line on a 100-ft lot)'],
    'notes': [
        'Illustrative architectural plan for the rezoning application (Lilburn Zoning Ordinance 2023-603 §1003-4 renderings/elevations item). NOT FOR CONSTRUCTION. DRAFT — to be superseded by sealed drawings by a Georgia-registered architect.',
        'Dimensions are to the outside face of exterior walls (2×6, 6 in nominal) and to the centreline of interior partitions (2×4, 4 in). Plate height 9\'-0"; great room vaulted; roof 8:12 main gables, 4:12 porch shed, architectural shingles.',
        'Accessibility (voluntary — Ord. 2023-603 §734 applies to attached dwellings only): zero-step entries at the porch and garage/mud room; 36-in passage doors; 42-in halls; 5\'-0" turning circles in both baths; curbless primary shower; 2×10 blocking for grab bars at all toilets, tub and showers.',
        'Garage door 16\'-0" × 7\'-0" recessed 5\'-0" behind the front wall of the dwelling — appears consistent with Ord. 2023-603 Table 4.2 (front-loaded garages recessed ≥ 5 ft). Garage clear 20\'-4" × 21\'-2" ≥ 20 × 21 program minimum.',
        'Life safety: NFPA 13D residential sprinklers (mitigation for the single access road, IFC 2024 (GA) App. D107.1); smoke/CO alarms per 2024 IRC (GA 2026) R314/R315; bedroom egress windows per 2024 IRC (GA 2026) R310 — VERIFY net clear opening at unit selection.',
        'Program body is nominally 38\'-0" × 38\'-0" (1,444 SF). With the 2-car garage as a front wing (the only way to keep the 40-ft width cap), the conditioned envelope is an L: 17\'-0" × 26\'-10" front wing + 38\'-0" × 25\'-0" rear block = 1,406 SF conditioned (−2.6%); overall body 38\'-0" × 51\'-10" plus porch and patio.',
        'Rear patio drawn 12\'-0" × 7\'-0": the program 12 × 8 slab would end 10 in inside the 20-ft rear buffer easement on a 100-ft lot (15 + 6 + 5 + 21\'-10" + 25 + 8 = 80\'-10"). VERIFY with Planning staff whether an at-grade uncovered slab is a buffer encroachment; otherwise hold the patio at 7 ft.',
        'Areas are computed by tools/floorplans.py from the wall-face polygons (conditioned = outside face of exterior walls; total under roof = conditioned + garage + covered porch; the uncovered patio is excluded).',
    ],
}
ACCESSIBILITY_B = [
    ('Zero-step entries', 'front porch (slab flush with finished floor), garage-to-laundry/mud-room door and recessed rear porch (french door ≤ 1/2-in threshold)', 'design intent'),
    ('Door clear width', 'all passage doors 36 in (3\'-0"); closets/pantry 30–32 in; french doors 5\'-0" (den) and 6\'-0" (porch)', 'design intent'),
    ('Hall width', 'foyer/hall 3\'-6" clear (42 in); kitchen corridor 3\'-10" clear', 'design intent'),
    ('Turning circles', '5\'-0" (60 in) circle drawn and checked clear in both baths', 'checked by script'),
    ('Curbless shower', 'primary bath 5\'-0" × 3\'-10" curbless (recessed slab per 03 30 00 §2.05)', 'design intent'),
    ('Out-swinging bath door', 'primary bath door swings into the bedroom (fall-rescue clearance)', 'design intent'),
    ('Grab-bar blocking', '2×10 solid blocking 33–36 in AFF at all toilets, tub and showers (2024 IRC (GA 2026) — voluntary; ANSI A117.1 Type C-type)', 'design intent — VERIFY blocking heights with architect'),
    ('Plate height / vaulted', '9\'-0" plate; great room vaulted', 'design intent'),
    ('Single-level living', '1 story; no interior steps; laundry/mud room on the living level off the garage', 'design intent'),
    ('Lever hardware, rocker switches, 48-in max reach', 'to be specified (Division 08 / 26)', 'later stage'),
    ('Lilburn §734 visitability', 'applies to attached dwellings only; voluntarily exceeded (100% zero-step)', 'appears consistent with Ord. 2023-603 §734 (not applicable)'),
]

# Plan B grid (ft) — re-proportioned 2026-09-03 to a 38'-0" body (see note 6): garage x 0–21 / y 5–29 (24 ft deep bay);
# foyer x 21–25.17; front-wing rooms x 25.17–38 (den y 0–9, bedroom 2 y 9–21 with the closet strip, bath 2 y 21–29);
# rear block y 29–58.5 = primary suite (x 0–14), laundry/mud (x 14–21) + pantry (x 21–25.17), kitchen (x 21–38, y 29–40),
# great room (x 14–38, y 40–58.5) with the 14 × 6 covered rear porch recessed at x 24–38, y 52.5–58.5.
PLAN_B = {
    'id': 'B', 'name': 'THE LAUREL', 'sheet': 'A-2', 'date': DATE, 'target_cond_sf': 1520, 'nominal_body': '38\'-0" × 40\'-0"',
    'program': '2 BR + den / 2 BA, 1 story, 2-car front-loaded garage recessed 5\'-0", covered front porch, covered rear porch 14\'×6\' (recessed), fireplace, walk-in pantry, laundry/mud room off the garage',
    'rooms': [
        {'name': '2-CAR GARAGE', 'kind': 'garage', 'rect': (0, 5, 21, 29), 'sub': 'ZERO-STEP DOOR TO LAUNDRY / MUD ROOM', 'label_at': (10.5, 15.0)},
        {'name': 'FOYER / HALL', 'kind': 'cond', 'rect': (21, 0, 25.17, 29), 'narrow_ok': True, 'label_rot': -90, 'label_at': (23.3, 15.0), 'label_size': 0.38},
        {'name': 'DEN', 'kind': 'cond', 'rect': (25.17, 0, 38, 9.5), 'label_at': (31.6, 5.5), 'label_size': 0.45, 'sub': 'FRENCH DOORS 5\'-0" · STUDY / GUEST FLEX',
         'fixtures': [{'t': 'table', 'r': (29.5, 0.75, 34.5, 3.0), 'label': 'DESK', 'ls': 0.3},
                      {'t': 'shelf', 'r': (28.0, 8.0, 37.3, 9.3), 'label': 'BOOKSHELVES', 'ls': 0.26, 'ly': 8.4}]},
        {'name': 'BEDROOM 2', 'kind': 'cond', 'poly': [(25.17, 9.5), (38, 9.5), (38, 21), (30, 21), (30, 18.5), (25.17, 18.5)], 'bedroom': True,
         'label_at': (28.1, 16.6), 'label_size': 0.45, 'label_dims': '12\'-2" × 11\'-2"',
         'fixtures': [{'t': 'bed', 'r': (31.0, 10.0, 36.0, 16.67), 'head': 'y0', 'label': 'QUEEN'}]},
        {'name': 'CLOSET', 'kind': 'cond', 'rect': (25.17, 18.5, 30, 21), 'narrow_ok': True, 'label': 'CLO. — BIFOLD 4\'-0"', 'label_size': 0.26, 'label_at': (27.6, 19.75),
         'closet_rod': [(25.33, 18.9, 29.83, 20.83)]},
        {'name': 'BATH 2', 'kind': 'cond', 'rect': (25.17, 21, 38, 29), 'bath': True, 'narrow_ok': True, 'circle': (29.5, 24.0), 'label_at': (33.3, 23.6), 'label_size': 0.36,
         'fixtures': [{'t': 'tub', 'r': (34.5, 21.333, 37.5, 26.333), 'rot': 90}, {'t': 'vanity', 'r': (28.5, 26.833, 33.5, 28.667), 'sinks': 1},
                      {'t': 'toilet', 'r': (25.5, 26.167, 28.0, 28.667), 'back': 'y1'}]},
        {'name': 'LAUNDRY / MUD', 'kind': 'cond', 'rect': (14, 29, 21, 40), 'narrow_ok': True, 'label_size': 0.36, 'label_at': (18.8, 33.6), 'sub': 'DROP ZONE',
         'fixtures': [{'t': 'washer', 'r': (14.17, 32.5, 16.67, 35.0)}, {'t': 'dryer', 'r': (14.17, 35.0, 16.67, 37.5)},
                      {'t': 'sink', 'r': (14.17, 37.5, 16.17, 39.5), 'label': 'UTIL. SINK', 'lx': 17.4, 'ly': 37.85, 'ls': 0.24},
                      {'t': 'wh', 'c': (19.85, 38.8), 'rad': 0.9}, {'t': 'bench', 'r': (16.5, 38.4, 18.8, 39.8)}]},
        {'name': 'PANTRY', 'kind': 'cond', 'rect': (21, 34, 25.17, 40), 'narrow_ok': True, 'label': 'W.I. PANTRY', 'label_size': 0.3, 'label_rot': -90, 'label_at': (23.9, 37.0),
         'fixtures': [{'t': 'shelf', 'r': (21.17, 34.17, 22.67, 39.83)}]},
        {'name': 'KITCHEN', 'kind': 'cond', 'poly': [(21, 29), (38, 29), (38, 40), (25.17, 40), (25.17, 34), (21, 34)], 'label_at': (27.0, 36.8), 'label_size': 0.42,
         'label_dims': '12\'-2" × 10\'-10"',
         'fixtures': [{'t': 'fridge', 'r': (26.0, 29.17, 29.0, 31.67), 'label': 'REF', 'ls': 0.3}, {'t': 'counter', 'r': (29.0, 29.17, 33.0, 31.17)},
                      {'t': 'range', 'r': (33.0, 29.17, 35.5, 31.67)}, {'t': 'counter', 'r': (35.5, 29.17, 37.5, 31.17)},
                      {'t': 'counter', 'r': (35.5, 31.17, 37.5, 33.0)}, {'t': 'sink', 'r': (35.5, 33.0, 37.5, 35.5)}, {'t': 'dw', 'r': (35.5, 35.5, 37.5, 37.5)},
                      {'t': 'counter', 'r': (35.5, 37.5, 37.5, 39.5)},
                      {'t': 'island', 'r': (29.0, 33.5, 32.0, 39.0), 'label': 'ISLAND 3\'×5\'-6"', 'rot': -90, 'ls': 0.3}]},
        {'name': 'W.I.C.', 'kind': 'cond', 'rect': (0, 29, 14, 35), 'narrow_ok': True, 'label_size': 0.36, 'label_at': (6.5, 33.0),
         'closet_rod': [(0.5, 29.17, 13.83, 31.17), (11.83, 31.17, 13.83, 34.83)]},
        {'name': 'PRIMARY BATH', 'kind': 'cond', 'rect': (0, 35, 14, 43.5), 'bath': True, 'narrow_ok': True, 'circle': (8.5, 40.6), 'label_at': (8.6, 38.3), 'label_size': 0.4,
         'fixtures': [{'t': 'vanity', 'r': (4.0, 35.17, 11.0, 37.0), 'sinks': 2}, {'t': 'toilet', 'r': (11.4, 37.0, 13.83, 39.5), 'back': 'x1'},
                      {'t': 'shower', 'r': (0.5, 39.5, 5.5, 43.33), 'label': 'CURBLESS', 'dx': 1.0, 'dy': 42.8}]},
        {'name': 'PRIMARY BEDROOM', 'kind': 'cond', 'rect': (0, 43.5, 14, 57.5), 'bedroom': True, 'label_at': (4.0, 49.6), 'label_size': 0.42,
         'fixtures': [{'t': 'bed', 'r': (7.33, 48.5, 13.83, 55.17), 'head': 'x1', 'label': 'KING'}]},
        {'name': 'GREAT ROOM', 'kind': 'cond', 'poly': [(14, 40), (38, 40), (38, 51.5), (24, 51.5), (24, 57.5), (14, 57.5)], 'vaulted': True,
         'label_dims': '23\'-4" × 11\'-10" + 9\'-4" × 6\'-0"', 'sub': 'VAULTED CEILING · DINING AREA · FIREPLACE', 'label_at': (26.5, 47.5), 'label_size': 0.55,
         'fixtures': [{'t': 'sofa', 'r': (15.5, 48.5, 22.5, 51.5)}, {'t': 'table', 'r': (28.0, 41.0, 34.0, 44.5), 'label': 'DINING', 'ls': 0.3},
                      {'t': 'fireplace', 'r': (17.0, 55.75, 21.0, 57.0), 'back': 'y1', 'hearth': 1.5, 'label': 'FIREPLACE', 'ls': 0.26}]},
        {'name': 'COVERED PORCH', 'kind': 'porch', 'rect': (21, -6, 38, 0), 'sub': 'ZERO-STEP ENTRY · UNDER THE FRONT GABLE', 'label_size': 0.42},
        {'name': 'COVERED REAR PORCH', 'kind': 'porch', 'side': 'rear', 'rect': (24, 51.5, 38, 57.5), 'sub': 'RECESSED UNDER MAIN ROOF · ZERO-STEP', 'label_size': 0.4, 'label_at': (31.0, 56.3)},
    ],
    'open_edges': [(25.17, 40, 38, 40), (21, 29, 25.17, 29)],
    'doors': [
        {'at': (23.08, 0), 'axis': 'h', 'w': 3.0, 'hinge': -1, 'swing': 1, 'type': 'door', 'h': 6.67, 'tag': 'entry'},
        {'at': (10.5, 5), 'axis': 'h', 'w': 16.0, 'type': 'garage', 'h': 7.0, 'tag': 'garage 16x7', 'label': 'GARAGE DOOR 16\'-0" × 7\'-0"'},
        {'at': (25.17, 4.75), 'axis': 'v', 'w': 5.0, 'swing': 1, 'type': 'french', 'tag': 'den french doors', 'label': '5\'-0" FRENCH'},
        {'at': (25.17, 13.5), 'axis': 'v', 'w': 3.0, 'hinge': -1, 'swing': 1, 'type': 'door', 'tag': 'bedroom 2'},
        {'at': (27.58, 18.5), 'axis': 'h', 'w': 4.0, 'swing': -1, 'type': 'french', 'tag': 'closet bifold', 'show_label': False},
        {'at': (25.17, 23.5), 'axis': 'v', 'w': 3.0, 'hinge': -1, 'swing': 1, 'type': 'door', 'tag': 'bath 2'},
        {'at': (16.0, 29), 'axis': 'h', 'w': 3.0, 'hinge': -1, 'swing': 1, 'type': 'door', 'tag': 'garage-mud'},
        {'at': (21, 32.0), 'axis': 'v', 'w': 3.0, 'hinge': -1, 'swing': -1, 'type': 'door', 'tag': 'mud-kitchen'},
        {'at': (25.17, 37.0), 'axis': 'v', 'w': 2.67, 'hinge': -1, 'swing': -1, 'type': 'door', 'tag': 'pantry'},
        {'at': (2.5, 35), 'axis': 'h', 'w': 2.5, 'hinge': -1, 'swing': -1, 'type': 'door', 'tag': 'wic'},
        {'at': (8.5, 43.5), 'axis': 'h', 'w': 3.0, 'hinge': -1, 'swing': 1, 'type': 'door', 'tag': 'primary bath (out-swing)'},
        {'at': (14, 45.5), 'axis': 'v', 'w': 3.0, 'hinge': -1, 'swing': -1, 'type': 'door', 'tag': 'primary bedroom'},
        {'at': (28.5, 51.5), 'axis': 'h', 'w': 6.0, 'swing': -1, 'type': 'french', 'h': 6.67, 'tag': 'rear porch french door'},
    ],
    'windows': [
        {'at': (33.6, 0), 'axis': 'h', 'w': 6.0, 'h': 5.0, 'sill': 2.67, 'tag': 'den front twin 3-0x5-0'},
        {'at': (38, 4.75), 'axis': 'v', 'w': 3.0, 'h': 5.0, 'sill': 2.67, 'tag': 'den side'},
        {'at': (38, 15.0), 'axis': 'v', 'w': 6.0, 'h': 5.0, 'sill': 2.67, 'tag': 'BR2 side twin (egress — casement leaf)'},
        {'at': (38, 23.83), 'axis': 'v', 'w': 2.0, 'h': 2.5, 'sill': 4.5, 'tag': 'bath 2 (obscure, over tub)'},
        {'at': (38, 34.25), 'axis': 'v', 'w': 3.5, 'h': 3.0, 'sill': 3.5, 'tag': 'kitchen over sink'},
        {'at': (38, 46.0), 'axis': 'v', 'w': 6.0, 'h': 5.0, 'sill': 2.67, 'tag': 'great room twin'},
        {'at': (35.0, 51.5), 'axis': 'h', 'w': 4.0, 'h': 5.0, 'sill': 2.67, 'tag': 'great room to rear porch'},
        {'at': (15.5, 57.5), 'axis': 'h', 'w': 2.0, 'h': 5.0, 'sill': 2.67, 'tag': 'fireplace flank L'},
        {'at': (22.5, 57.5), 'axis': 'h', 'w': 2.0, 'h': 5.0, 'sill': 2.67, 'tag': 'fireplace flank R'},
        {'at': (7.0, 57.5), 'axis': 'h', 'w': 5.0, 'h': 5.0, 'sill': 2.67, 'tag': 'primary rear (egress — casement leaf)'},
        {'at': (0, 51.0), 'axis': 'v', 'w': 6.0, 'h': 5.0, 'sill': 2.67, 'tag': 'primary side twin'},
        {'at': (0, 38.5), 'axis': 'v', 'w': 2.5, 'h': 2.5, 'sill': 4.5, 'tag': 'primary bath'},
        {'at': (0, 16.0), 'axis': 'v', 'w': 3.0, 'h': 3.0, 'sill': 4.0, 'tag': 'garage'},
    ],
    'porch_columns': [(21.33, -5.67), (29.5, -5.67), (37.67, -5.67), (24.33, 58.17), (31.0, 58.17), (37.67, 58.17)],
    'roof': {'plate_ft': 9.0, 'heel_ft': 0.5, 'ridge_direction': 'main ridge parallel to the lane (x) over the rear block (rear porch recessed under it); a front-facing 8:12 gable over the 17-ft front wing, carried 6 ft forward over the covered porch; a subordinate front-facing 6:12 gable over the 21-ft garage',
             'elements': [{'name': 'main gable (rear block)', 'span_ft': 28.5, 'pitch': (8, 12), 'ridge': 'x'},
                          {'name': 'front-wing gable (extended over the porch)', 'span_ft': 17.0, 'pitch': (8, 12), 'ridge': 'y'},
                          {'name': 'garage gable', 'span_ft': 21.0, 'pitch': (6, 12), 'ridge': 'y'}]},
    'accessibility': ACCESSIBILITY_B,
    'materials_by_scheme': MATERIALS_BY_SCHEME,
    'dims': {'front': [[0, 2.5, 18.5, 21, 25.17, 38], [0, 21, 38], [0, 38]],
             'rear': [[0, 14, 24, 38], [0, 38]],
             'left': [[5, 29, 35, 43.5, 57.5], [0, 5, 57.5], [-6, 0, 57.5]],
             'right': [[-6, 0, 9.5, 21, 29, 40, 51.5, 57.5], [-6, 0, 51.5, 57.5]],
             'interior': [{'axis': 'v', 'pos': 6.0, 'pts': [5, 29]}, {'axis': 'h', 'pos': 22.5, 'pts': [0, 21]},
                          {'axis': 'h', 'pos': 54.0, 'pts': [24, 38]}, {'axis': 'v', 'pos': 26.0, 'pts': [51.5, 57.5]}]},
    'envelope_note': 'body 38\'-0" wide (re-proportioned 2026-09-03 from the 40\'-0" FACTS §4 nominal so that the roof, not just the walls, fits the 40\'-0" buildable width); actual envelope is L-shaped (garage front wing) with the 14 × 6 covered rear porch recessed under the main roof',
    'verify': ['REAR-YARD EAVE — the same question as the side yards, unresolved: the roof carries a 12-in eave front and rear (tools/elevations.py OH_FR), so at a 58\'-6" body the rear roof edge sits 19\'-6" from the rear lot line, 6 in INSIDE the 20-ft rear yard / buffer easement, while the side eaves were held 4 in outside the side-yard lines (note 6). Ord. 2023-603 has no projections/encroachments provision either way, and the front porch roof likewise projects 1\'-0" past the porch face into the 15-ft front setback (Plan A the same). If staff require the rear eave outside the line too, hold the body at 58\'-0" (rear wall 21\'-0" from the rear line; 8-in rear eave -> roof edge 20\'-4"; conditioned 1,511 SF) or at 57\'-6" with the 12-in eave (conditioned 1,492 SF). Resolve at the pre-application conference — this is a lot-fit decision, not a floor-plan decision',
               'Side-yard eave projection: Ord. 2023-603 was searched and contains no projections/encroachments provision permitting an eave in a required yard, so the 8-in overhangs are held inside the 40\'-0" buildable width. CONFIRM with the Planning Director at the pre-application conference — if eaves may project, the body could return to 40\'-0" and the plan to ~1,595 SF',
               'Fireplace type/venting (direct-vent gas assumed; no masonry chimney drawn) — architect of record / 2024 IRC (GA 2026) Ch. 10',
               'Egress leaf type and net clear opening at unit selection — 2024 IRC (GA 2026) R310.2.1 (see note 9): a 3\'-0" × 5\'-0" single-hung does NOT reliably deliver 5.7 SF; the egress leaf at each bedroom is specified as a casement',
               'Grab-bar blocking heights and ANSI A117.1 references — architect of record',
               'Max impervious / lot coverage for R-2 — Lilburn Development Regulations App. B §5.9 is "Recreation Areas" and does not apply to this 9.44-ac subdivision (audit 2026-09-03), so no App. B coverage limit has been located — confirm at the pre-application conference',
               'data/layout.json house_rect for Plan B lots is a 40 × 40 box; the actual envelope is 38\'-0" × 58\'-6" plus the 17\' × 6\' front porch — the site-plan agent must re-cut the house/driveway/rear rectangles (rear wall 20\'-6" from the rear line on a 100-ft lot, i.e. 6 in outside the 20-ft buffer easement)',
               'tools/elevations.py MASSING[\'B\'] must be conformed to this spec (blocks (0,29,38,57.5) / (21,−6,38,29) / (0,5,21,29); footprint_deduct (24,51.5,38,57.5); porch_sf 102) or check_massing() and check_width() will fail',
               'Front wall at 21 ft from the lot line (porch face on the 15-ft setback + 6-ft porch), not the 20 ft assumed in the program brief — confirm the siting convention with the site-plan agent'],
    'notes': [
        'Illustrative architectural plan for the rezoning application (Lilburn Zoning Ordinance 2023-603 §1003-4 renderings/elevations item). NOT FOR CONSTRUCTION. DRAFT — to be superseded by sealed drawings by a Georgia-registered architect.',
        'Dimensions are to the outside face of exterior walls (2×6, 6 in nominal) and to the centreline of interior partitions (2×4, 4 in). Plate height 9\'-0"; great room vaulted; roof 8:12 main gables, 4:12 front-porch shed, architectural shingles; the rear porch is recessed under the main roof.',
        'Accessibility (voluntary — Ord. 2023-603 §734 applies to attached dwellings only): zero-step entries at the front porch, garage/mud room and rear porch; 36-in passage doors; 3\'-6" (42-in) clear foyer/hall; 5\'-0" turning circles drawn and checked clear in both baths; curbless primary shower; out-swinging primary bath door; 2×10 blocking for grab bars at all toilets, tub and showers.',
        'Garage door 16\'-0" × 7\'-0" recessed 5\'-0" behind the front wall of the dwelling — appears consistent with Ord. 2023-603 Table 4.2 (front-loaded garages recessed ≥ 5 ft). Garage clear 20\'-4" × 23\'-4" ≥ the 20\'-0" × 20\'-0" program minimum (extra bay depth for storage / golf cart).',
        'Life safety: smoke and CO alarms per 2024 IRC (GA 2026) R314/R315; bedroom emergency escape and rescue openings per 2024 IRC (GA 2026) R310 (note 9). NFPA 13D residential sprinklers are offered as a VOLUNTARY condition, not as code-required mitigation: IFC 2024 as adopted and modified by Ga. Comp. R. & Regs. R. 120-3-3-.04 replaces Appendix D107.1\'s 30-unit trigger with 120 dwelling units, so at 43 units a second fire-apparatus access road is not required and no sprinkler exception is being relied on. (The 1,754-ft dead-end lane still needs IFC 2024 (GA) Appendix D103.4 special approval — a site-plan issue, not a house-plan issue.)',
        'BODY WIDTH — why 38\'-0" and not the 40\'-0" of the program brief. A 50\'-0" lot less two 5\'-0" side yards (Ord. 2023-603 Table 4.1, R-2) leaves 40\'-0" of buildable width, and the ROOF has to fit inside it, not just the walls: at an 8-in overhang on each side wall a 40\'-0" body measures 41\'-4" roof to roof and does not fit. Ord. 2023-603 was searched and contains no provision permitting a projection or encroachment into a required yard (VERIFY at pre-application). The body is therefore 38\'-0" wide — 38\'-0" + 2 × 0\'-8" = 39\'-4" roof to roof, 4 in of clearance to each side-yard line — and the depth was increased 1\'-0" to 58\'-6" to recover floor area. Conditioned area 1,530 SF, against 1,595 SF for the superseded 40\'-0" × 57\'-6" version (−4.1%).',
        'BODY DEPTH — why 58\'-6" is the maximum. On the typical 50\'-0" × 100\'-0" lot the front porch face sits on the 15-ft front setback, the porch is 6\'-0" deep and the rear 20\'-0" of the lot is the undisturbed buffer easement (Ord. 2023-603 Table 4.1 rear yard; §313(1) buffer-in-lot reading): 100 − 15 − 6 − 20 = 59\'-0" of available body depth. At 58\'-6" the rear wall stands 20\'-6" from the rear lot line — 6 in outside the buffer easement (the ROOF is a separate question: see the first VERIFY item — the drawn 12-in rear eave reaches 19\'-6" from the rear line). Verified against data/layout.json (Plan B lot 2: lot 50 × 100, setback envelope 15 ft front / 20 ft rear, porch rect 6 ft deep).',
        'Rear porch: recessing the 14\'-0" × 6\'-0" covered porch under the main roof keeps the roof edge on the line of the rear wall, so nothing projects past 58\'-6" and the 20-ft buffer easement is not touched. No uncovered patio is proposed (an added at-grade slab would reach the buffer line — VERIFY with Planning staff).',
        'EGRESS. Both bedrooms have an emergency escape and rescue opening in an exterior wall: BEDROOM 2 a 6\'-0" × 5\'-0" twin on the right side wall, the PRIMARY BEDROOM a 5\'-0" × 5\'-0" unit on the rear wall; sills at 2\'-8" (32 in) above the finished floor, well under the 44-in maximum (2024 IRC (GA 2026) R310.2.2). The egress leaf of each unit is specified as a 3\'-0" × 5\'-0" CASEMENT: taking a 3-in allowance all round for frame, sash and hardware, net clear opening = 2\'-6" × 4\'-6" = 30 in × 54 in = 11.25 SF ≥ 5.7 SF, net clear width 30 in ≥ 20 in, net clear height 54 in ≥ 24 in — appears consistent with 2024 IRC (GA 2026) R310.2.1. A 3\'-0" × 5\'-0" single-hung is NOT relied on: its net clear height is roughly half the unit height and the resulting area is marginal against 5.7 SF. Companion leaves and all other windows may be single-hung.',
        'Program body is nominally 38\'-0" × 40\'-0" = 1,520 SF (re-proportioned 2026-09-03 from the FACTS §4 nominal 40\'-0" × 40\'-0" = 1,600 SF — see note 6). With the 2-car garage as a front wing and the 14\'-0" × 6\'-0" rear porch recessed under the main roof, the conditioned envelope is a 17\'-0" × 29\'-0" front wing + a 38\'-0" × 29\'-6" rear block less the 84-SF porch notch = 1,530 SF conditioned (+0.7% on the 1,520-SF nominal); overall body 38\'-0" × 58\'-6" plus the front porch. 1,530 SF exceeds the ≥ 1,400-SF voluntary condition (docs/10 item 14) and the 1,000-SF minimum heated floor area for a cottage home in R-2 (Ord. 2023-603 Table 4.1).',
        'Areas are computed by tools/floorplans.py from the wall-face polygons (conditioned = outside face of exterior walls; total under roof = conditioned + garage + both covered porches).',
    ],
}
PLANS = {'A': PLAN_A, 'B': PLAN_B}

# ============================================================================= OUTPUTS
PX_PER_FT = 24.0                 # tight web SVG
SHEET_IN = (24.0, 18.0)          # ARCH C landscape
SHEET_SCALE_PT_PER_FT = 13.5     # 3/16 in = 1 ft  (0.1875 in × 72 pt)

def render_png(svg_path, png_path, dpi=150, px_scale=None):
    import cairosvg
    kw = {'dpi': dpi}
    if px_scale: kw['scale'] = px_scale
    cairosvg.svg2png(url=svg_path, write_to=png_path, **kw)

def title_line(spec): return 'PLAN %s — %s — %s' % (spec['id'], spec['name'], TITLE_SUFFIX)

def make_tight(spec, an, path):
    bb = an['all_bbox']
    nf, nr, nl, nrt = (len(spec['dims'].get(k, [])) for k in ('front', 'rear', 'left', 'right'))
    x0 = bb[0] - 2.0 - 2.0 * nl - 1.5; x1 = bb[2] + 2.5 + 2.0 * nrt + 1.5
    y_top = bb[3] + 2.0 + 2.0 * nr + 3.5; y_bot = bb[1] - 2.0 - 2.0 * nf - 2.0
    c = Canvas(ymax=y_top)
    c.text((x0 + x1) / 2 + 8, y_top - 1.0, title_line(spec), size=0.75, weight='bold')
    c.text((x0 + x1) / 2 + 8, y_top - 2.3, 'Scale: 1 ft = %.0f px in this file · %s · %s' % (PX_PER_FT, spec['program'], 'DRAFT — to be superseded by sealed architectural drawings'), size=0.42, color='#333')
    draw_plan(spec, an, c)
    # legend + scale bar + areas at the right
    lx = x1 + 1.0
    y = draw_legend(c, lx, y_top - 4.0)
    draw_scalebar(c, lx + 1.0, y - 1.5); y -= 4.0
    y = draw_area_table(c, lx, y, spec, an, w=17.0)
    x_end = lx + 18.5
    c.text(x0 + 0.5, y_bot + 0.7, DISCLAIMER, size=0.3, anchor='start', color='#333')
    c.text(x0 + 0.5, y_bot + 0.2, '<!-- ' + MARKER + ' -->', size=0.3, anchor='start', color='#999')
    body = c.svg()
    vb = (x0, 0, x_end, y_top - y_bot)
    svg = wrap_svg(body, vb, scale=PX_PER_FT)
    open(path, 'w').write(svg + '\n<!-- ' + MARKER + ' -->\n')
    return vb

def make_sheet(spec, an, path):
    W, H = SHEET_IN[0] * 72, SHEET_IN[1] * 72
    S = SHEET_SCALE_PT_PER_FT
    Wf, Hf = W / S, H / S                      # sheet in "ft" drawing units (128 × 96)
    c = Canvas(ymax=Hf)
    m = 2.0                                     # margin ft-units (~27 pt)
    c.rect((m, m, Wf - m, Hf - m), fill='none', lw=0.12)
    c.rect((m + 0.4, m + 0.4, Wf - m - 0.4, Hf - m - 0.4), fill='none', lw=0.04)
    # title strip (bottom)
    tb_h = 7.0
    c.line(m + 0.4, m + 0.4 + tb_h, Wf - m - 0.4, m + 0.4 + tb_h, lw=0.08)
    c.text(m + 1.2, m + 0.4 + tb_h - 1.2, title_line(spec), size=0.95, weight='bold', anchor='start')
    c.text(m + 1.2, m + 0.4 + tb_h - 2.5, 'THE COTTAGES AT ARCADO SPRINGS — R-1 → R-2 REZONING (Lilburn Zoning Ordinance 2023-603 §1003-4) — 4535/4537/4539/4541 Arcado Rd SW, Lilburn GA 30047 — Land Lot 123, 6th District, Gwinnett County', size=0.45, anchor='start')
    c.text(m + 1.2, m + 0.4 + tb_h - 3.5, 'Sheet %s · %s · Scale 3/16" = 1\'-0" on ARCH C (18 × 24 in) · Prepared by the owner-applicant (Mohammed Awad) with AI drafting tools · DRAFT — to be superseded by sealed drawings (GA-registered architect)' % (spec.get('sheet', 'A-1'), spec['name'].title()), size=0.42, anchor='start')
    c.text(m + 1.2, m + 0.4 + tb_h - 4.6, DISCLAIMER, size=0.4, anchor='start', color='#222')
    c.text(m + 1.2, m + 0.4 + tb_h - 5.6, '<!-- ' + MARKER + ' -->', size=0.36, anchor='start', color='#999')
    # scale bar in the title strip, right
    draw_scalebar(c, Wf - m - 16.0, m + 0.4 + tb_h - 2.6, label='GRAPHIC SCALE — 4 FT')
    c.text(Wf - m - 2.0, m + 0.4 + tb_h - 5.2, 'NORTH: see site plan (lots face the lane; N 28°43\' W along the strip)', size=0.36, anchor='end', color='#333')
    # plan
    bb = an['all_bbox']
    nf, nr, nl, nrt = (len(spec['dims'].get(k, [])) for k in ('front', 'rear', 'left', 'right'))
    px0 = bb[0] - 2.0 - 2.0 * nl - 0.5; py0 = bb[1] - 2.0 - 2.0 * nf - 1.5
    px1 = bb[2] + 2.5 + 2.0 * nrt + 0.5; py1 = bb[3] + 2.0 + 2.0 * nr + 0.5
    avail_h = Hf - 2 * m - tb_h - 3.0
    tx = m + 2.0 - px0; ty = (m + 0.4 + tb_h + 1.5) - py0
    if (py1 - py0) > avail_h: print('  WARN plan taller than sheet area: %.1f > %.1f ft' % (py1 - py0, avail_h))
    pc = Canvas(ymax=Hf - ty)      # shift: plan y -> sheet y = y + ty
    draw_plan(spec, an, pc)
    c.add('<g transform="translate(%.3f 0)">%s</g>' % (tx, pc.svg()))
    # right column (drawn on its own canvas, scaled 1.3x for print legibility)
    rx = m + 2.0 + (px1 - px0) + 3.0; ry = Hf - m - 2.5
    K = 1.3; main_c = c; c = Canvas(ymax=Hf)
    c.text(rx, ry, 'PLAN %s — %s' % (spec['id'], spec['name']), size=0.8, weight='bold', anchor='start'); ry -= 1.0
    import textwrap
    for ln in textwrap.wrap(spec['program'], 118):
        c.text(rx, ry, ln, size=0.42, anchor='start', color='#333'); ry -= 0.6
    ry -= 0.8
    ry = draw_area_table(c, rx, ry, spec, an, w=26.0); ry -= 1.0
    # roof + accessibility summary
    c.text(rx, ry, 'ROOF / HEIGHT', size=0.45, weight='bold', anchor='start'); ry -= 0.8
    for e in an['roof']['elements']:
        c.text(rx, ry, '%s: span %s, %d:%d → ridge %s above FF (plate %s + heel + rise)' % (e['name'], fti(e['span_ft']), e['pitch'][0], e['pitch'][1], fti(e['ridge_height_ft']), fti(an['roof']['plate_ft'])), size=0.34, anchor='start'); ry -= 0.6
    c.text(rx, ry, 'Max ridge %s ≤ 24 ft program cap; Ord. 2023-603 Table 4.1 R-2 max height 40 ft — appears consistent.' % fti(an['roof']['max_ridge_ft']), size=0.34, anchor='start'); ry -= 1.2
    c.text(rx, ry, 'ACCESSIBILITY CHECKLIST (voluntary)', size=0.45, weight='bold', anchor='start'); ry -= 0.8
    for item, prov, st in spec['accessibility']:
        c.text(rx, ry, '• %s — %s [%s]' % (item, prov, st), size=0.31, anchor='start'); ry -= 0.55
    ry -= 0.6
    ry = draw_legend(c, rx, ry); ry -= 0.4
    nx = rx + 27.5
    draw_notes(c, nx, Hf - m - 2.5, spec['notes'], size=0.33, width_chars=88)
    col = c.svg(); c = main_c
    ax, ay = rx, Hf - (Hf - m - 2.5)          # SVG coords of the column's top-left anchor
    c.add('<g transform="translate(%.3f %.3f) scale(%.2f) translate(%.3f %.3f)">%s</g>' % (ax, ay, K, -ax, -ay, col))
    body = c.svg()
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%gin" height="%gin" viewBox="0 0 %.3f %.3f" font-family="Helvetica, Arial, sans-serif">'
           '<rect width="%.3f" height="%.3f" fill="#fff"/>\n%s\n</svg>' % (SHEET_IN[0], SHEET_IN[1], Wf, Hf, Wf, Hf, body))
    open(path, 'w').write(svg + '\n<!-- ' + MARKER + ' -->\n')

def make_lot(spec, an, path):
    """Plan sited on a typical 50 × 100 lot (FACTS §4): 15-ft front / 5-ft side / 20-ft rear (= buffer easement)."""
    LW_, LD_ = 50.0, 100.0
    bbx = an['body_bbox']; body_w = bbx[2] - bbx[0]
    hx = (LW_ - body_w) / 2.0          # centre the body between the side yards
    # The ROOF, not just the wall, is held outside the required yards: no projection into a required yard
    # is claimed, because Ord. 2023-603 as excerpted contains no projection allowance. The 8-in rake over
    # the porch gable therefore sits ON the 15-ft front setback line and the porch face 8 in behind it.
    ROOF_OH = 0.667
    porch_depth = 6.0; hy = 15.0 + ROOF_OH + porch_depth
    ymax_ = LD_ + 8; ymin_ = -31.0 - 9
    c = Canvas(ymax=ymax_)
    X0, X1 = -14.0, LW_ + 14.0
    c.text(LW_ / 2, LD_ + 6.0, 'PLAN %s — %s — TYPICAL 50\'-0" × 100\'-0" LOT (5,000 SF) — %s' % (spec['id'], spec['name'], TITLE_SUFFIX), size=0.9, weight='bold')
    c.text(LW_ / 2, LD_ + 4.6, 'Setbacks per Lilburn Zoning Ordinance 2023-603 Table 4.1 (R-2): front 15 ft (local street), side 5 ft, rear 20 ft; rear 20 ft = undisturbed buffer easement (§313(1)); Table 4.2 garage recess ≥ 5 ft', size=0.42, color='#333')
    # lane tract
    c.rect((X0 + 2, -31, X1 - 2, -7), fill='#d9d9d9', stroke='none'); c.text(LW_ / 2, -19, 'PRIVATE LANE — 22-FT PAVEMENT (NO PARKING) — 31-FT TRACT', size=0.55, weight='bold', color='#333')
    c.rect((X0 + 2, -7, X1 - 2, -5), fill='#cfe3c9', stroke='none'); c.text(LW_ / 2, -6, '2-FT STRIP', size=0.32, color='#333')
    c.rect((X0 + 2, -5, X1 - 2, 0), fill='#eeeeee', stroke='#111', lw=0.04); c.text(LW_ / 2 + 14, -2.5, '5-FT SIDEWALK (2 FT OFF BACK OF CURB)', size=0.42, color='#333')
    c.line(X0 + 2, 0, X1 - 2, 0, lw=0.12); c.text(LW_ - 1, 1.0, 'LOT LINE = LANE TRACT EDGE (FRONTAGE 50 FT ≥ 30 FT, §319)', size=0.38, anchor='end', color='#333')
    # lot
    c.rect((0, 0, LW_, LD_), fill='#fbfbf6', lw=0.12)
    c.rect((0, LD_ - 20, LW_, LD_), fill='#dfe9d5', stroke='none')
    for i in range(0, int(LW_ + LD_), 3):
        x_a, y_a = i, LD_ - 20; 
        # hatch lines (45°) clipped to the buffer band
        xa = i; ya = LD_ - 20; xb = i - 20; yb = LD_
        if xb < 0: ya = LD_ - 20 + (0 - xb) * (-1) * -1; 
        pass
    for k in range(-20, 50, 4):
        xa, ya, xb, yb = k, LD_ - 20, k + 20, LD_
        if xa < 0: ya = LD_ - 20 - xa; xa = 0
        if xb > LW_: yb = LD_ - (xb - LW_); xb = LW_
        if xa < xb: c.line(xa, ya, xb, yb, lw=0.03, color='#7a9a6a')
    c.text(LW_ / 2, LD_ - 10, '20-FT UNDISTURBED BUFFER EASEMENT (REAR YARD) — NO STRUCTURES', size=0.5, weight='bold', color='#3d5a2e')
    # setback lines
    c.line(0, 15, LW_, 15, lw=0.04, dash='0.8,0.4', color='#a33'); c.text(1.0, 15.7, '15-FT FRONT SETBACK', size=0.36, anchor='start', color='#a33')
    c.line(5, 0, 5, LD_ - 20, lw=0.04, dash='0.8,0.4', color='#a33'); c.text(4.3, 60, '5-FT SIDE', size=0.36, rot=-90, color='#a33')
    c.line(LW_ - 5, 0, LW_ - 5, LD_ - 20, lw=0.04, dash='0.8,0.4', color='#a33'); c.text(LW_ - 4.3, 60, '5-FT SIDE', size=0.36, rot=90, color='#a33')
    c.line(0, LD_ - 20, LW_, LD_ - 20, lw=0.05, dash='0.8,0.4', color='#a33'); c.text(1.0, LD_ - 20 - 0.8, '20-FT REAR SETBACK / BUFFER LINE', size=0.36, anchor='start', color='#a33')
    # driveway + walk
    gar = next(r for r in spec['rooms'] if r['kind'] == 'garage'); gx0, gy0, gx1, gy1 = gar['rect']
    gdoor = next(d for d in spec['doors'] if d.get('type') == 'garage')
    dcx = hx + gdoor['at'][0]; dy_top = hy + gdoor['at'][1]
    c.rect((dcx - 10, 0, dcx + 10, dy_top), fill='#e6e6e6', lw=0.04); c.text(dcx, dy_top / 2, 'DRIVEWAY 20\' × %s (2 CARS)' % fti(dy_top), size=0.42, weight='bold')
    porch = next(r for r in spec['rooms'] if r['kind'] == 'porch' and r.get('side', 'front') != 'rear'); pr = porch['rect']
    rporch = next((r for r in spec['rooms'] if r['kind'] == 'porch' and r.get('side') == 'rear'), None)
    wx = hx + (pr[0] + pr[2]) / 2 + 1.0
    c.rect((wx - 2, 0, wx + 2, hy - porch_depth), fill='#eeeeee', lw=0.04); c.text(wx, 7.5, '4-FT WALK', size=0.32, rot=-90)
    # house
    pc = Canvas(ymax=ymax_ - hy)
    draw_plan(spec, an, pc, with_dims=False)
    c.add('<g transform="translate(%.3f 0)">%s</g>' % (hx, pc.svg()))
    # AC pad
    c.rect((hx + bbx[2] + 0.8, hy + 30, hx + bbx[2] + 3.8, hy + 33), fill='#fff', lw=0.03); c.text(hx + bbx[2] + 2.3, hy + 31.5, 'AC', size=0.32)
    # dimensions
    rear_wall = hy + bbx[3]; patio = next((r for r in spec['rooms'] if r['kind'] == 'patio'), None)
    pts = [0, 15, hy, dy_top, rear_wall] + ([hy + patio['rect'][3]] if patio else []) + ([hy + rporch['rect'][1]] if rporch else []) + [LD_ - 20, LD_]
    dim_chain(c, sorted(set(round(p, 2) for p in pts)), 'v', -3.0, size=0.38, ext_from=-0.2)
    dim_chain(c, [0, LD_], 'v', -7.5, size=0.42, ext_from=-0.2)
    dim_chain(c, [0, hx, hx + bbx[2], LW_], 'h', -33.5, size=0.38, ext_from=-31.2)
    dim_chain(c, [0, LW_], 'h', -35.5, size=0.42, ext_from=-31.2)
    c.text(LW_ / 2, -12.5, '▼  FRONT — LOTS FACE THE PRIVATE LANE; ENTRY DRIVE AND WALK FROM THE LANE TRACT  ▼', size=0.5, weight='bold', color='#333')
    # coverage tabulation
    a = an['areas']; drive = 20 * dy_top; walk = 4 * (hy - porch_depth); imp = a['total_under_roof_sf'] + a['rear_patio_uncovered_sf'] + drive + walk
    tx = LW_ + 6.5; ty = LD_ - 1
    lines = ['LOT COVERAGE (computed):', 'Lot 50 × 100 = 5,000 SF', 'Building under roof %s SF → %.1f%%' % (format(int(a['total_under_roof_sf']), ','), 100 * a['total_under_roof_sf'] / 5000),
             'Impervious (roof + patio + drive + walk) %s SF → %.1f%%' % (format(int(round(imp)), ','), 100 * imp / 5000),
             'Max impervious: Table 4.1 gives none for R-2 — VERIFY', '(Dev. Regs. App. B §5.9 at pre-app)',
             '', 'Front porch face at the 15-ft setback line.', 'Garage door %s from the lot line (≥ 25 ft).' % fti(dy_top),
             'Rear wall %s from the rear line' % fti(LD_ - rear_wall), ('Patio edge %s from the rear line' % fti(LD_ - hy - patio['rect'][3])) if patio else '',
             ('Rear porch (covered, recessed) edge %s from the rear line' % fti(LD_ - hy - rporch['rect'][3])) if rporch else '',
             'Side yards %s each (≥ 5 ft).' % fti(hx), 'Front toward the lane; north per site plan.']
    for s in lines:
        c.text(tx, ty, s, size=0.4, anchor='start', weight='bold' if s.endswith(':') else 'normal'); ty -= 0.85
    draw_scalebar(c, tx + 1, 12.0)
    c.text(X0 + 0.5, ymin_ + 1.4, DISCLAIMER, size=0.32, anchor='start', color='#333')
    c.text(X0 + 0.5, ymin_ + 0.7, '<!-- ' + MARKER + ' -->', size=0.3, anchor='start', color='#999')
    body = c.svg()
    vb = (X0, 0, LW_ + 30, ymax_ - ymin_)
    # Emit on a real ARCH C sheet in PORTRAIT (18 x 24 in) rather than tight to the drawing, so the sheet
    # prints at a true, standard size in the filing set. The content keeps its aspect and is centred; the
    # drawn scale is stated on the sheet's own graphic scale bar, which scales with it.
    sw_in, sh_in = 18.0, 24.0
    cw, ch = vb[2], vb[3]
    k = min(sw_in / cw, sh_in / ch)
    px, py = (sw_in / k - cw) / 2.0, (sh_in / k - ch) / 2.0
    page_vb = (vb[0] - px, vb[1] - py, sw_in / k, sh_in / k)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%gin" height="%gin" viewBox="%.3f %.3f %.3f %.3f" '
           'font-family="Helvetica, Arial, sans-serif"><rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" '
           'fill="#fff"/>\n%s\n</svg>'
           % (sw_in, sh_in, page_vb[0], page_vb[1], page_vb[2], page_vb[3],
              page_vb[0], page_vb[1], page_vb[2], page_vb[3], body))
    open(path, 'w').write(svg + '\n<!-- ' + MARKER + ' -->\n')
    return {'lot_w_ft': LW_, 'lot_d_ft': LD_, 'house_origin_on_lot_ft': [hx, hy], 'garage_door_from_lot_line_ft': round(dy_top, 2),
            'rear_wall_from_rear_line_ft': round(LD_ - rear_wall, 2), 'patio_edge_from_rear_line_ft': round(LD_ - hy - patio['rect'][3], 2) if patio else None,
            'rear_porch_edge_from_rear_line_ft': round(LD_ - hy - rporch['rect'][3], 2) if rporch else None,
            'side_yard_ft': hx, 'building_coverage_pct': round(100 * a['total_under_roof_sf'] / 5000, 1), 'impervious_pct_est': round(100 * imp / 5000, 1),
            'impervious_basis': 'roof %.0f + patio %.0f + driveway %.0f + walk %.0f SF' % (a['total_under_roof_sf'], a['rear_patio_uncovered_sf'], drive, walk)}

def plan_record(spec, an, lot):
    bb = an['body_bbox']
    rp = lambda p: [[round(x, 3), round(y, 3)] for x, y in p]
    return {
        'id': spec['id'], 'name': spec['name'], 'title': title_line(spec), 'date': spec['date'], 'program': spec['program'],
        'status': 'ILLUSTRATIVE — NOT FOR CONSTRUCTION — DRAFT, to be superseded by sealed architectural drawings',
        'coordinate_system': 'feet; origin = front-left corner of the body bounding box; x to the right seen from the lane; y toward the rear (front = lane side = y 0)',
        'nominal_body': spec['nominal_body'], 'target_cond_sf': spec['target_cond_sf'],
        'overall_body_dims': {'width_ft': round(bb[2] - bb[0], 2), 'depth_ft': round(bb[3] - bb[1], 2), 'label': '%s × %s' % (fti(bb[2] - bb[0]), fti(bb[3] - bb[1])),
                              'basis': 'bounding box of conditioned + garage (outside face); porch and patio excluded',
                              'note': spec.get('envelope_note', 'program body nominal; actual envelope is L-shaped because the 2-car garage must be a front wing under the 40-ft width cap')},
        'footprint_polygon_ft': rp(an['cond_poly']), 'footprint_polygon_basis': 'conditioned envelope, outside face of exterior walls (garage separate)',
        'garage_rect': list(next(r for r in spec['rooms'] if r['kind'] == 'garage')['rect']),
        'porch_rects': [list(r['rect']) for r in spec['rooms'] if r['kind'] == 'porch' and r.get('side', 'front') != 'rear'],
        'rear_porch_rects': [list(r['rect']) for r in spec['rooms'] if r['kind'] == 'porch' and r.get('side') == 'rear'],
        'patio_rects': [list(r['rect']) for r in spec['rooms'] if r['kind'] == 'patio'],
        'rooms': [{'name': r['name'], 'kind': r['kind'], 'polygon': r['polygon'], 'clear_polygon': r['clear_polygon'], 'area_sf': r['area_sf'], 'label_dims': r['label_dims']} for r in an['rooms']],
        'exterior_openings': an['exterior_openings'],
        'exterior_openings_convention': 'offset_ft measured from the wall\'s left end looking at that wall from outside; wall_line_ft = the grid line (y for front/rear, x for left/right); front has two lines (0 = front wing, 5 = garage face)',
        'roof': an['roof'], 'areas': an['areas'], 'accessibility_checklist': [{'item': i, 'provided': p, 'status': s} for i, p, s in spec['accessibility']],
        'materials_by_scheme': spec['materials_by_scheme'], 'lot_siting': lot, 'notes': spec['notes'],
        'verify': spec['verify'],
    }

def build(plan_id):
    spec = PLANS[plan_id]
    print('== PLAN %s — %s' % (spec['id'], spec['name']))
    an = analyze(spec)
    fails = run_checks(spec, an)
    tag = 'plan-%s' % plan_id.lower()
    p_t = os.path.join(DRAW, tag + '.svg'); p_s = os.path.join(DRAW, tag + '-sheet.svg'); p_l = os.path.join(DRAW, tag + '-lot.svg')
    make_tight(spec, an, p_t); make_sheet(spec, an, p_s); lot = make_lot(spec, an, p_l)
    for p in (p_t, p_l): render_png(p, p[:-4] + '.png', px_scale=150.0 / 96.0)
    render_png(p_s, p_s[:-4] + '.png', dpi=150)
    rec = plan_record(spec, an, lot)
    pj = os.path.join(DATA, 'plans.json')
    db = json.load(open(pj)) if os.path.exists(pj) else {'generated_by': 'tools/floorplans.py', 'date': DATE, 'plans': {}}
    db['plans'][plan_id] = rec; db['date'] = DATE
    json.dump(db, open(pj, 'w'), indent=1, ensure_ascii=False)
    print('  areas:', json.dumps(an['areas']))
    print('  body bbox:', an['body_bbox'], ' ridge max %.2f ft' % an['roof']['max_ridge_ft'])
    print('  wrote', p_t, p_s, p_l, pj)
    assert not fails, 'CHECK FAILURES: %s' % fails
    return rec

if __name__ == '__main__':
    ids = sys.argv[1:] or list(PLANS)
    for pid in ids: build(pid)
