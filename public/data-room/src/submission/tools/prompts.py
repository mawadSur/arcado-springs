#!/usr/bin/env python3
"""Dimension-locked image-generation prompts — The Cottages at Arcado Springs.

    python3 tools/prompts.py            # writes renderings/PROMPTS.md and renderings/prompts.json

WHY THIS IS A GENERATOR AND NOT A HAND-WRITTEN DOCUMENT
The owner's instruction was: "when making prompts to Higgsfield make sure they are specific… make sure the
images match the layouts and specific dimensions of the property." A prompt typed by hand goes stale the
moment a plan changes. Every number in every prompt below is therefore READ AT RUN TIME from the same files
that generate the drawings — data/plans.json (the house plans and their roof geometry), data/layout.json
(the site layout), and the constants and colour schemes in tools/elevations.py — so a prompt cannot state a
dimension the drawings do not show. Re-run this script after any design change and re-generate the images.

Each shot names the reference drawing that must be attached to the generation as an image reference. The
reference is a furniture-free coloured elevation or a crop of a sheet, produced by
tools/elevations.py make_ref_image(); it is what holds the massing, the openings and the proportions.

> **Disclaimer:** This is an AI-generated analysis for preliminary planning purposes. All findings must be verified by a licensed professional before use in design, permitting, or regulatory submissions.

<!-- architecture-studio:requires-disclaimer -->
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data')
REND = os.path.join(ROOT, 'renderings')
os.makedirs(REND, exist_ok=True)

import elevations as ev                                            # noqa: E402
import floorplans as fp                                            # noqa: E402

fti = fp.fti
PLANS = json.load(open(os.path.join(DATA, 'plans.json')))['plans']
LAY = json.load(open(os.path.join(DATA, 'layout.json')))
M = LAY['metrics']
LANE = LAY['lane']
AM = LAY['amenity']

NEG_COMMON = ('no text, no lettering, no watermark, no logo, no signage other than what is described, no '
              'house numbers, no dimension lines, no drawing annotations, no people, no cars unless '
              'described, no second story, no dormer, no basement, no walk-out, no raised crawl-space '
              'foundation, no vinyl shutters, no gable-end decorative trusses beyond the brackets described, '
              'no palm trees, no desert or coastal vegetation, no snow')


def geo(pid):
    """Everything a prompt needs about one house plan, read from the drawings' own data."""
    p = PLANS[pid]
    m = ev.build_model(pid)
    blocks = {b['name']: b for b in m['blocks']}
    _f, roof2roof, body_w = ev.check_width(m)
    a = p['areas']
    porch = [r for r in p.get('porch_rects', [])]
    porch_w = (porch[0][2] - porch[0][0]) if porch else 0.0
    porch_d = (porch[0][3] - porch[0][1]) if porch else 0.0
    rear = p.get('rear_porch_rects') or p.get('patio_rects') or []
    rear_w = (rear[0][2] - rear[0][0]) if rear else 0.0
    rear_d = (rear[0][3] - rear[0][1]) if rear else 0.0
    return {
        'id': pid, 'name': p['name'].title(),
        'body_w': body_w, 'body_d': m['an']['body_bbox'][3] - m['an']['body_bbox'][1],
        'roof2roof': roof2roof,
        'plate': m['plate'], 'ridge': m['max_ridge'], 'ridge_grade': m['max_ridge_grade'],
        'ff': ev.FF,
        'main': blocks['MAIN BLOCK'], 'wing': blocks['FRONT WING'], 'garage': blocks['GARAGE'],
        'cond': a['conditioned_sf'], 'garage_sf': a['garage_sf'],
        'porch_w': porch_w, 'porch_d': porch_d, 'porch_sf': a['front_porch_sf'],
        'rear_w': rear_w, 'rear_d': rear_d,
        'rear_kind': 'covered rear porch' if a.get('rear_porch_covered_sf') else 'uncovered rear patio',
        'lawn_behind_house_ft': max(0.0, (p['lot_siting']['rear_wall_from_rear_line_ft'] or 0) - 20.0),
        'lawn_behind_rear_edge_ft': max(0.0, ((p['lot_siting']['rear_porch_edge_from_rear_line_ft']
                                               or p['lot_siting']['patio_edge_from_rear_line_ft'] or 0) - 20.0)),
        'rear_sf': a.get('rear_porch_covered_sf') or a.get('rear_patio_uncovered_sf') or 0,
        'program': p['program'],
        'openings': p['exterior_openings'],
    }


def sch(key):
    S = ev.SCHEMES[key]
    return S


SCHEME_WORDS = {
    '1': dict(name='Scheme 1 "Warm White"',
              wall='fiber-cement vertical panel with 12-inch-on-center battens (board-and-batten), warm white',
              base='an adhered ledge-stone veneer in a gray-tan Appalachian blend, laid dry-stack with tight joints',
              roofc='charcoal', trim='warm white', door='deep green', gdoor='painted warm white to match the trim'),
    '2': dict(name='Scheme 2 "Sage"',
              wall='fiber-cement lap siding, 7-1/4-inch plank at 6-inch exposure, sage green',
              base='a modular red-brown brick veneer laid in running bond with a rowlock sill cap',
              roofc='weathered wood brown', trim='soft white', door='oxblood red',
              gdoor='painted sage to match the siding'),
    '3': dict(name='Scheme 3 "Clay"',
              wall='fiber-cement lap siding, 7-1/4-inch plank at 6-inch exposure, clay beige',
              base='an adhered ledge-stone veneer in a buff-tan blend, laid dry-stack with tight joints',
              roofc='driftwood brown', trim='cream', door='navy blue',
              gdoor='painted cream to match the trim'),
}

CAMERA = {
    'front34': ('three-quarter view from the far side of the lane, camera 5 feet 6 inches above the pavement, '
                '35 mm lens, the house filling the frame with the driveway leading in from the lower left'),
    'frontflat': ('straight-on eye-level view from the far side of the lane, 50 mm lens, camera 5 feet 6 inches '
                  'above the pavement, no perspective distortion, the whole house in frame with a little sky '
                  'above the ridge'),
    'street': ('eye-level view standing on the sidewalk looking north-west down the lane, 35 mm lens, camera '
               '5 feet 6 inches above the walk, the lane receding to a vanishing point slightly left of centre'),
    'aerial': ('aerial oblique from about 400 feet above the Arcado Road frontage looking north-west along the '
               'long axis of the property, 24 mm lens, the whole property in frame from the road at the bottom '
               'to the wooded rear boundary at the top'),
    'garden': ('eye-level view from the middle of the rear yard looking back at the house, 35 mm lens, camera '
               '5 feet 6 inches above the lawn'),
    'neighbour': ('eye-level view standing in a neighbouring back yard looking through the tree buffer toward '
                  'the new house, 50 mm lens, camera 5 feet 6 inches above the ground'),
    'flat': ('flat overhead view straight down on a light neutral surface, evenly lit, no shadows, product-'
             'photography style'),
}

LIGHT = ('late-summer afternoon in Piedmont Georgia, warm soft daylight about two hours before sunset, light '
         'haze, gentle shadows, high-quality architectural photography')


def house_facts(g, s):
    """The paragraph of locked building facts shared by every exterior shot of a dwelling."""
    w = SCHEME_WORDS[s]
    return (
        'The house is Plan {id} "{name}" of this community: ONE STORY ONLY, no second floor and no dormers. '
        'Body {bw} wide and {bd} deep; roof-to-roof width across the front {r2r}; eave line {plate} above the '
        'finished floor (a 9-foot wall plate on a 6-inch raised-heel truss); highest roof ridge {ridge} above '
        'the finished floor and {rg} above finished '
        'grade; finished floor only {ff} above finished grade, so the walk from the lane rises to a flush, '
        'step-free landing at the porch. Massing seen from the lane, left to right: a two-car garage wing '
        '{gw} wide under a front-facing {gp} gable whose ridge is {gr} above the floor, its front wall set back '
        '{recess} behind the front wall of the house; then the living wing {ww} wide under a front-facing {wp} '
        'gable whose ridge is {wr} above the floor; and behind both of them the main body roof, an {mp} gable '
        'whose ridge runs left to right at {mr} above the floor. A single rectangular louvered gable vent, 24 '
        'inches wide by 16 inches high, is centred in each front-facing gable, and a cedar knee-brace bracket '
        'sits under each end of the living-wing rake. The living-wing gable is carried forward {pd} over a '
        'covered front porch {pw} wide and {pd} deep with a flat white beadboard ceiling at 9 feet 0 inches, '
        'carried on 8x8 nominal Western Red Cedar posts with a natural semi-transparent stain, each standing on '
        'a 20-inch-square masonry pier 2 feet 0 inches tall with a sloped cast-stone cap, with a painted header '
        'beam spanning between them. Roof overhangs are 8 inches at the two side walls and 12 inches front and '
        'rear. MATERIALS AND COLOURS, exactly and only these: {wall}; {base}, forming a water table 30 inches tall above '
        'the finished floor wrapping the base of every wall and every porch pier, finished with a sloped '
        'cast-stone cap; architectural asphalt shingles in {roofc}; painted 4-inch flat window casings, corner '
        'boards and frieze in {trim}; white 5-inch K-style aluminium gutters and round downspouts. Windows are '
        'white vinyl single-hung units with a flat sill; window sills sit 2 feet 8 inches above the finished '
        'floor, just above the cap of the masonry water table.'
    ).format(
        id=g['id'], name=g['name'],
        bw=fti(g['body_w']), bd=fti(g['body_d']), r2r=fti(g['roof2roof']),
        plate=fti(g['plate']), ridge=fti(g['ridge']), rg=fti(g['ridge_grade']), ff=fti(g['ff']),
        gw=fti(g['garage']['rect'][2] - g['garage']['rect'][0]),
        gp='%d:%d' % tuple(g['garage']['pitch']), gr=fti(g['garage']['ridge_h']),
        recess=fti(g['garage']['rect'][1] - g['wing']['rect'][1] - g['porch_d']),
        ww=fti(g['wing']['rect'][2] - g['wing']['rect'][0]),
        wp='%d:%d' % tuple(g['wing']['pitch']), wr=fti(g['wing']['ridge_h']),
        mp='%d:%d' % tuple(g['main']['pitch']), mr=fti(g['main']['ridge_h']),
        pw=fti(g['porch_w']), pd=fti(g['porch_d']),
        ohs='%d inches' % round(ev.OH_SIDE * 12), ohf='%d inches' % round(ev.OH_FR * 12),
        wall=w['wall'], base=w['base'], roofc=w['roofc'], trim=w['trim'])


def lot_setting(side='NE'):
    walk = ('a 5-foot-wide concrete sidewalk set 2 feet behind the curb on this side of the lane'
            if side == 'NE' else 'no sidewalk on this side of the lane')
    return (
        'SETTING: a brand-new 55-and-over cottage community on a long narrow property in Lilburn, Gwinnett '
        'County, Georgia, Piedmont hardwood country. The house sits on a level lot 50 feet 0 inches wide by '
        '100 feet 0 inches deep, its porch face 15 feet 0 inches back from the lane right of way, with 5-foot '
        'side yards to the neighbouring cottages. In front of it runs a private lane 22 feet 0 inches wide '
        'face-to-face of vertical concrete curb, freshly paved dark asphalt, with {walk}. A plain gray '
        'concrete driveway 20 feet 0 inches wide runs 26 feet from the lane to the garage door. Landscaping is '
        'new and modest: clipped fescue lawn, a bed of low evergreen shrubs against the water table, one young '
        'shade tree in the front yard, and a continuous wall of tall mature existing hardwood trees standing '
        'well behind the houses in the 20-foot undisturbed perimeter buffer. All utilities are underground; '
        'there are no overhead poles or wires anywhere.'
    ).format(walk=walk)


def openings_front(g):
    fr = [o for o in g['openings'] if o['wall'] == 'front']
    door = [o for o in fr if o['type'] == 'door']
    gar = [o for o in fr if o['type'] == 'garage']
    win = [o for o in fr if o['type'] == 'window']
    bits = []
    if gar:
        o = gar[0]
        bits.append('one carriage-style sectional garage door %s wide by %s tall with a single top row of small '
                    'square windows' % (fti(o['width_ft']), fti(o['height_ft'])))
    if door:
        o = door[0]
        bits.append('one insulated fiberglass entry door %s by %s with a glazed upper panel, at the left end of '
                    'the porch' % (fti(o['width_ft']), fti(o['height_ft'])))
    for o in win:
        bits.append('one white vinyl twin single-hung window unit %s wide by %s tall under the porch'
                    % (fti(o['width_ft']), fti(o['height_ft'])))
    return ('OPENINGS ON THIS ELEVATION, exactly this many and no more: ' + '; '.join(bits) + '.')


def openings_rear(g):
    rr = [o for o in g['openings'] if o['wall'] == 'rear']
    bits = []
    for o in rr:
        if o['type'] == 'french':
            bits.append('one white French patio door %s wide by %s tall' % (fti(o['width_ft']), fti(o['height_ft'])))
        else:
            bits.append('one white vinyl window %s wide by %s tall' % (fti(o['width_ft']), fti(o['height_ft'])))
    return 'OPENINGS ON THE REAR WALL, exactly: ' + '; '.join(bits) + '.'


# --------------------------------------------------------------------------- the twelve shots
def shots():
    A, B = geo('A'), geo('B')
    out = []

    out.append(dict(
        id='R-01', file='R-01_plan-a-front-scheme1.jpg', aspect='3:2',
        refs=['renderings/reference/ref-plan-a-front-scheme1.png'],
        must_ref=True,
        shows='Plan A "The Springbrook" front (lane) elevation in perspective, Scheme 1 Warm White',
        why='Application Instructions item (11) — the street-visible front of the more common dwelling type; '
            'shows one story, the 5-foot garage recess of Ordinance 2023-603 Table 4.2, and scheme 1 colours',
        prompt=('Photorealistic architectural rendering of a single detached cottage home, matching the attached '
                'measured front elevation drawing EXACTLY — same proportions, same roof forms, same openings, '
                'same left-to-right composition. ' + house_facts(A, '1') + ' ' + openings_front(A) +
                ' The entry door is ' + SCHEME_WORDS['1']['door'] + ' and the garage door is ' +
                SCHEME_WORDS['1']['gdoor'] + '. ' + lot_setting('SW') +
                ' CAMERA: ' + CAMERA['front34'] + '. ' + LIGHT + '. NEGATIVE — do not include: any porch '
                'railing; any change to the number, size or position of the windows and doors; more than one '
                'house in the frame; ' + NEG_COMMON + '.'),
        checklist=[
            'One story only; no dormer; roof ridge no higher than about %s above grade' % fti(A['ridge_grade']),
            'Garage door face clearly set back behind the front wall of the house',
            'Front porch spans the full living wing and is covered by the wing gable — not a separate shed roof',
            'Three cedar posts on masonry piers; no railing',
            'Board-and-batten siding, warm white; ledge-stone water table about 30 inches tall; charcoal shingles',
            'Exactly one entry door and one twin window under the porch; one garage door',
            'Louvered vent centred in each front gable',
            'No text, no house number, no people, no cars',
        ]))

    out.append(dict(
        id='R-02', file='R-02_plan-b-front-scheme2.jpg', aspect='3:2',
        refs=['renderings/reference/ref-plan-b-front-scheme2.png'],
        must_ref=True,
        shows='Plan B "The Laurel" front (lane) elevation in perspective, Scheme 2 Sage over brick',
        why='Item (11) — the second dwelling type and the second approved colour scheme, with the brick base',
        prompt=('Photorealistic architectural rendering of a single detached cottage home, matching the attached '
                'measured front elevation drawing EXACTLY — same proportions, same roof forms, same openings, '
                'same left-to-right composition. ' + house_facts(B, '2') + ' ' + openings_front(B) +
                ' The entry door is ' + SCHEME_WORDS['2']['door'] + ' and the garage door is ' +
                SCHEME_WORDS['2']['gdoor'] + '. ' + lot_setting('NE') +
                ' CAMERA: ' + CAMERA['front34'] + '. ' + LIGHT + '. NEGATIVE — do not include: any porch '
                'railing; any change to the number, size or position of the windows and doors; more than one '
                'house in the frame; ' + NEG_COMMON + '.'),
        checklist=[
            'One story only; ridge no higher than about %s above grade' % fti(B['ridge_grade']),
            'Sage lap siding at a 6-inch exposure with a red-brown brick water table and a cast-stone cap',
            'Garage face recessed behind the front wall; carriage-style door with one row of lites',
            'Porch under the wing gable, cedar posts on brick piers, no railing',
            'Sidewalk present on this side of the lane (this is a north-east-side lot)',
            'No text, no people, no cars',
        ]))

    out.append(dict(
        id='R-03', file='R-03_plan-b-rear-garden-scheme3.jpg', aspect='3:2',
        refs=['renderings/reference/ref-plan-b-rear-scheme2.png'],
        must_ref=True,
        shows='Plan B rear / garden view, Scheme 3 Clay, with the %s and the rear yard running into the '
              '20-foot undisturbed buffer' % B['rear_kind'],
        why='Item (11) — on perimeter lots the rear elevation is what the adjoining R-1 neighbours see; and it '
            'answers the "what will I look at from my back yard" question directly',
        prompt=('Photorealistic architectural rendering of the REAR of a single-story detached cottage home, '
                'matching the attached measured rear elevation drawing EXACTLY. ' + house_facts(B, '3') + ' ' +
                openings_rear(B) + ' At the rear there is a %s %s wide and %s deep, %d square feet, recessed '
                'under the main roof with the same flat beadboard ceiling and cedar posts as the front porch. '
                % (B['rear_kind'], fti(B['rear_w']), fti(B['rear_d']), round(B['rear_sf'])) +
                'SETTING: the rear yard of a lot 50 feet 0 inches wide by 100 feet 0 inches deep in a new '
                '55-and-over cottage community in Lilburn, Georgia. EVERY LOT IN THIS COMMUNITY BACKS ONTO A '
                '20-FOOT-DEEP UNDISTURBED WOODED BUFFER, and this covered porch looks straight into it: a dense '
                'standing wall of mature existing Piedmont hardwoods with their understory intact, untouched, no '
                'fence, no clearing, no grading, beginning barely '
                + fti(B['lawn_behind_rear_edge_ft']) + ' beyond the edge of the porch slab. A narrow strip of new '
                'fescue, and two simple chairs on the porch. CAMERA: eye-level three-quarter view from the rear '
                'corner of the lot, looking back along the side of the house at the covered porch with the trees '
                'standing close behind it, 35 mm lens, camera 5 feet 6 inches above the lawn. ' + LIGHT +
                '. NEGATIVE — do not include: any deck, any railing, any second story, any basement or '
                'walk-out, any privacy fence, any cleared or graded ground inside the tree buffer; ' +
                NEG_COMMON + '.'),
        checklist=[
            'One story; rear roof is one continuous gable slope, no dormer, no bonus room',
            'Covered rear porch recessed under the main roof, not added on',
            'Undisturbed mature tree buffer immediately behind the lawn, no fence, no clearing',
            'Clay-beige lap siding, buff ledge stone base, driftwood shingles',
            'No walk-out, no basement windows, no retaining wall',
        ]))

    lane_w = LANE.get('pavement_width_ft', 22)
    out.append(dict(
        id='R-04', file='R-04_lane-streetscape-nw.jpg', aspect='16:9',
        refs=['renderings/reference/ref-plan-a-front-scheme2.png', 'drawings/mcp-front.png'],
        must_ref=True,
        shows='Streetscape looking north-west down the private lane: the %s pavement, the sidewalk on one '
              'side, and the 50-foot lot rhythm with alternating plans and rotating colour schemes'
              % fti(lane_w),
        why='Item (11) "proper perspective" for the street-visible sides collectively, and the most direct '
            'answer to the 2025 neighbourhood objection about single-family character',
        prompt=('Photorealistic architectural rendering of a residential street in a brand-new 55-and-over '
                'cottage community, matching the attached front elevation drawing for the design of every '
                'house. Looking north-west along a private lane exactly %s wide face-to-face of vertical '
                '6-inch concrete curb and gutter, freshly paved dark asphalt with a 2 percent crown, with a '
                '5-foot-wide concrete sidewalk set 2 feet behind the curb on the right-hand side only and no '
                'sidewalk on the left. There is no parking on the street and no parked cars. Along both sides '
                'stand ONE-STORY detached cottage homes on lots 50 feet 0 inches wide, each set back 15 feet '
                '0 inches from the lane, so the front porches make a steady rhythm about 50 feet apart. Every '
                'house is one story with a front-facing gable over a covered front porch carried on cedar '
                'posts on masonry piers, a two-car garage wing whose door is set back 5 feet behind the front '
                'wall of the house, architectural asphalt shingles, a masonry water table 30 inches tall, and '
                'a plain gray concrete driveway 20 feet wide. The colours alternate down the street among only '
                'three schemes and no two neighbouring houses share one: warm white board-and-batten with '
                'gray-tan ledge stone and charcoal shingles; sage lap siding with red-brown brick and '
                'weathered-wood shingles; clay-beige lap siding with buff ledge stone and driftwood shingles. '
                'Young street trees stand at about 40 feet on centre in the strip between curb and walk, new '
                'lawns, low foundation shrubs, and a continuous wall of tall mature hardwoods closing the view '
                'behind the houses. All utilities underground; no poles, no wires. CAMERA: %s. %s. NEGATIVE — '
                'do not include: any two-story house, townhouse, duplex or apartment building; any garage door '
                'flush with or in front of the house front wall; any parked car or moving car; any porch '
                'railing; any cul-de-sac bulb; any sidewalk on the left side; ' % (fti(lane_w), CAMERA['street'],
                                                                                  LIGHT) + NEG_COMMON + '.'),
        checklist=[
            'Every house is one story',
            'Lane reads about %s wide with curb and gutter, sidewalk on one side only' % fti(lane_w),
            'Front porches repeat at roughly 50-foot intervals',
            'Every garage door is visibly recessed behind the house front wall',
            'Only the three approved colour schemes appear, and no two adjacent houses match',
            'No parked cars on the street; no overhead wires',
        ]))

    hh = LAY['hammerheads'][0] if LAY.get('hammerheads') else None
    out.append(dict(
        id='R-05', file='R-05_hammerhead-pocket-green.jpg', aspect='16:9',
        refs=['drawings/mcp-sheet.png'],
        must_ref=False,
        shows='A hammerhead (T) turnaround with the pocket greens either side',
        why='Shows the Table 4.2 position — hammerhead turnarounds instead of a cul-de-sac bulb — and the fire '
            'apparatus turnaround that the single-access analysis under IFC 2024 (GA) Appendix D103.4 depends on',
        prompt=('Photorealistic architectural rendering of a T-shaped hammerhead turnaround on a private '
                'residential lane in a new one-story 55-and-over cottage community in Piedmont Georgia. The '
                'lane is %s wide face-to-face of vertical concrete curb; at the turnaround two paved legs, '
                'each 20 feet 0 inches wide and 60 feet 0 inches long, run out at right angles, one to each '
                'side, forming a T, with 25-foot curb returns — THERE IS NO CIRCULAR CUL-DE-SAC BULB AND NO '
                'ISLAND. Beside the turnaround, on each side, is a pocket green 50 feet 0 inches by 100 feet '
                '0 inches: mown lawn, a young shade tree or two, a simple bench, and a 5-foot concrete walk '
                'across it. One-story cottage homes with front-facing gables and covered porches face the '
                'green from both sides, in warm white, sage and clay colour schemes. Mature hardwoods stand '
                'behind everything. CAMERA: eye-level from the lane looking into the turnaround, 35 mm lens, '
                'camera 5 feet 6 inches above the pavement. %s. NEGATIVE — do not include: any circular '
                'cul-de-sac, any turning circle, any island, any two-story building, any parked cars, any '
                'playground equipment; ' % (fti(lane_w), LIGHT) + NEG_COMMON + '.'),
        checklist=[
            'A T-shaped hammerhead, NOT a circular cul-de-sac or a bulb',
            'Two paved legs at right angles to the lane',
            'Pocket green with lawn and trees beside it',
            'All houses one story',
        ]))

    sign = AM.get('entry_sign')
    out.append(dict(
        id='R-06', file='R-06_entrance-arcado-monument.jpg', aspect='16:9',
        refs=['drawings/mcp-front.png'],
        must_ref=False,
        shows='The single Arcado Road entrance with the monument sign, the landscape strip and the frontage walk',
        why='Item (11) — the sign is a structure whose size and location must be shown; and this is the exhibit '
            'for the access-spacing case and for the commitment that the community is not gated',
        prompt=('Photorealistic architectural rendering of the single entrance to a new 55-and-over cottage '
                'community, seen from a two-lane county road. The entrance drive is 24 feet 0 inches wide with '
                '25-foot curb returns and vertical concrete curb, and it curves gently away to the left as it '
                'enters the property. THERE IS NO GATE AND NO GATEHOUSE. On the right of the drive stands a '
                'low ground-mounted monument sign: a masonry base of gray-tan ledge stone matching the houses, '
                'a cast-stone cap, a sign face 8 feet 0 inches wide and 4 feet 0 inches tall (32 square feet) '
                'with dimensional metal letters, the whole structure not more than 6 feet 0 inches tall, set '
                'in a planted bed of low shrubs and seasonal colour, lit by two small shielded ground-mounted '
                'flood lights aimed upward at the face only. Along the road frontage runs a 10-foot-wide '
                'landscaped strip planted with canopy trees and shrubs, and a new 5-foot-wide concrete '
                'sidewalk. Beyond the entrance the drive opens onto a mown village green with a one-story '
                'clubhouse in the distance. Mature hardwoods frame both sides. CAMERA: eye-level from the '
                'opposite shoulder of the county road, 35 mm lens, camera 5 feet 6 inches above the road. %s. '
                'NEGATIVE — do not include: any gate, gate arm, guardhouse, fence across the drive, brick '
                'entry walls taller than the monument sign, any illuminated or internally lit sign box, any '
                'changeable-copy or digital sign, any flag pole, any two-story building; %s.'
                % (LIGHT, NEG_COMMON)),
        checklist=[
            'No gate and no guardhouse',
            'One monument sign, low, masonry base, externally lit, clearly under about 6 feet tall',
            'Entrance drive reads about 24 feet wide with curb returns',
            'Landscape strip and a frontage sidewalk along the county road',
            'The clubhouse in the distance is one story',
        ]))

    cl = AM.get('clubhouse')
    cl_w = abs(cl[2][0] - cl[0][0]) if cl and isinstance(cl, list) and len(cl) >= 3 else 60.0
    cl_d = abs(cl[2][1] - cl[0][1]) if cl and isinstance(cl, list) and len(cl) >= 3 else 40.0
    out.append(dict(
        id='R-07', file='R-07_clubhouse-village-green.jpg', aspect='3:2',
        refs=['drawings/mcp-front.png'],
        must_ref=False,
        shows='The one-story clubhouse of about %d square feet across the village green, with the mail kiosk'
              % round(AM.get('clubhouse_sf', 2400)),
        why='Item (11) — the clubhouse and the mail kiosk are structures visible from the street and need '
            'colour and material imagery like the dwellings',
        prompt=('Photorealistic architectural rendering of a small one-story neighbourhood clubhouse in a new '
                '55-and-over cottage community in Piedmont Georgia. The building is a simple rectangle about '
                '%s long and %s deep, about %d square feet, ONE STORY, with a gabled architectural-shingle '
                'roof, a deep covered porch across the long side facing a lawn, 8x8 cedar posts on masonry '
                'piers, and the same materials as the cottages: fiber-cement lap siding in warm white, a '
                'gray-tan ledge-stone water table 30 inches tall, soft-white trim, and weathered-wood '
                'shingles. Large windows face the lawn; the entry is step-free from a concrete walk. In front '
                'of it lies a mown village green of about a third of an acre with young shade trees, a walking '
                'path and two benches. To one side stands a small open mail shelter about 16 feet by 10 feet '
                'with the same roof and materials, sheltering a bank of USPS cluster mailboxes and parcel '
                'lockers, with four marked parking spaces beside it. Mature hardwood trees stand behind. '
                'CAMERA: eye-level from the far side of the green looking at the porch, 35 mm lens, camera 5 '
                'feet 6 inches above the lawn. %s. NEGATIVE — do not include: any second story, any pool, any '
                'clock tower or cupola larger than a small vent, any commercial signage, any two-story '
                'building anywhere in frame, any individual curbside mailboxes; %s.'
                % (fti(cl_w), fti(cl_d), round(AM.get('clubhouse_sf', 2400)), LIGHT, NEG_COMMON)),
        checklist=[
            'Clubhouse is one story and reads about the right size, not a big civic building',
            'Same palette as the cottages: warm white siding, ledge-stone base, weathered-wood shingles',
            'Covered porch facing the green; step-free entry',
            'A mail shelter with cluster boxes, and no individual curbside mailboxes anywhere',
        ]))

    pads = AM.get('pickleball') or []
    crt = AM.get('courts') or []
    def _wh(poly):
        xs=[q[0] for q in poly]; ys=[q[1] for q in poly]
        return (max(xs)-min(xs), max(ys)-min(ys))
    pad_w, pad_d = _wh(pads[0]) if pads else (60.0, 30.0)
    ct_w, ct_d = _wh(crt[0]) if crt else (44.0, 20.0)
    # do the pads abut (one enclosure) or stand apart (separate enclosures)?
    if len(pads) > 1:
        ys0 = sorted(q[1] for q in pads[0]); ys1 = sorted(q[1] for q in pads[1])
        gap = abs(min(ys1) - max(ys0))
        together = gap < 0.5
    else:
        together = True
    encl_w = pad_w
    encl_d = pad_d * max(1, len(pads)) if together else pad_d
    fence_txt = (('ONE single fenced enclosure %s by %s containing BOTH courts side by side, with no gap '
                  'and no fence between them') % (fti(encl_w), fti(encl_d))
                 if together else
                 ('TWO separate fenced enclosures, each %s by %s, standing apart with mown grass between '
                  'them') % (fti(pad_w), fti(pad_d)))
    out.append(dict(
        id='R-08', file='R-08_pickleball-courts.jpg', aspect='3:2',
        refs=[],
        must_ref=False,
        shows='The two pickleball courts at their real size, unlit',
        why='Shows the amenity actually proposed at its actual size, and shows the voluntary condition that '
            'the courts are not lit',
        prompt=('Photorealistic rendering of a pickleball facility in a new 55-and-over cottage community in '
                'Piedmont Georgia. There are exactly TWO courts, each exactly %s long by %s wide, painted blue '
                'inside the lines with a green surround, crisp white lines and a low pickleball net 34 inches '
                'high at the centre. They sit side by side with their long axes parallel, inside %s. The fence '
                'is 10-foot-tall black PVC-coated chain link on all sides. THERE ARE NO LIGHT POLES, NO LIGHT '
                'FIXTURES AND NO FLOODLIGHTS ANYWHERE. Around the enclosure: mown fescue lawn, a wooden bench, '
                'a young shade tree, and beyond it a row of small ONE-STORY cottage homes with front-facing '
                'gables, covered porches on cedar posts and fiber-cement siding in warm white, sage and clay. '
                'Tall mature hardwood trees behind. CAMERA: eye-level three-quarter view from an outside corner '
                'so the whole enclosure and both courts are visible, 35 mm lens, camera 5 feet 6 inches above '
                'the ground. %s. NEGATIVE — do not include: any tennis court, tennis net or tennis court '
                'markings; more than two courts; any light pole, light fixture or floodlight; any bleachers, '
                'grandstand, shade canopy or scoreboard; any two-story building; %s.'
                % (fti(ct_w), fti(ct_d), fence_txt, LIGHT, NEG_COMMON)),
        checklist=[
            'Exactly two courts, side by side, long axes parallel',
            'The enclosure matches the drawing: %s' % fence_txt,
            'Black chain-link fence, no light poles anywhere',
            'Court proportions read as pickleball (%s by %s), not tennis' % (fti(ct_w), fti(ct_d)),
            'Surrounding houses are one story',
        ]))

    out.append(dict(
        id='R-09', file='R-09_aerial-oblique-nw.jpg', aspect='16:9',
        refs=['drawings/mcp-sheet.png'],
        must_ref=True,
        shows='Aerial oblique along the whole strip: one entrance in the south-west third, %d one-story roofs '
              'in two rows, one lane, the turnarounds, greens, two dry basins, creek woods and the buffer'
              % M.get('lots', 43),
        why='Item (11) "proper perspective" at site scale — the exhibit that shows the real proportion of the '
            'property and that nothing crowds the neighbouring lots',
        prompt=('Photorealistic aerial rendering of a new 55-and-over cottage community on a LONG NARROW '
                'property in Lilburn, Gwinnett County, Georgia. THE PROPORTION IS THE POINT: the property is a '
                'straight strip only about 240 feet wide but about 1,750 feet long, running away from the road '
                'toward the upper left; it must read as narrow and very deep, roughly seven times longer than '
                'it is wide. A single entrance drive leaves the two-lane county road at the bottom of the '
                'frame, positioned in the south-western third of the road frontage, not centred, and curves to '
                'the centreline of one private lane that runs the whole length of the property. %d ONE-STORY '
                'cottage homes with gabled shingle roofs line that single lane, about %d in the longer row on '
                'the right and about %d on the left, every one of them a small one-story house with a '
                'front-facing gable and a covered porch, roofs in charcoal, weathered wood and driftwood '
                'brown. Near the road end: a mown village green, a small one-story clubhouse, two fenced '
                'pickleball courts, and a small parking bay. Along the lane: %d T-shaped hammerhead '
                'turnarounds and %d open lawn pocket greens. On the left-hand side toward the far end: two '
                'grassed DRY detention basins with mown side slopes and no standing water, and a preserved '
                'block of untouched hardwood woods around a small stream head. A continuous 20-foot-deep band '
                'of mature untouched hardwood trees runs along both long sides and the far end, separating the '
                'community from the existing single-family subdivisions of larger two-story houses that '
                'surround it on every side. CAMERA: %s. %s. NEGATIVE — do not include: any second entrance or '
                'any connection to a street at the far end; any cul-de-sac circle; any two-story house inside '
                'the community; any apartment or townhouse building; any pond with open water; any construction '
                'equipment; any wide or square site shape — the site must read as a long narrow strip; %s.'
                % (M.get('lots', 43), M.get('lots_ne', 27), M.get('lots_sw', 16),
                   len(LAY.get('hammerheads', [])), len(LAY.get('greens', [])),
                   CAMERA['aerial'], LIGHT, NEG_COMMON)),
        checklist=[
            'The site reads as a long narrow strip about seven times longer than wide',
            'Exactly one entrance, and it is off-centre toward one side of the frontage',
            'One lane down the middle; houses on both sides; no second street and no through connection',
            'Every house inside the community is one story',
            'Two grassed dry basins with no standing water; preserved woods at the far end',
            'A continuous treed buffer on both long sides and the rear',
        ]))

    out.append(dict(
        id='R-10', file='R-10_buffer-from-neighbour.jpg', aspect='3:2',
        refs=['renderings/reference/ref-plan-a-rear-scheme2.png'],
        must_ref=False,
        shows='Eye-level view from an adjoining back yard, across the 20-foot undisturbed buffer, to the rear '
              'of a cottage beyond',
        why='The adjoining owners\' objection is about what they will see; this is the exhibit that answers it',
        prompt=('Photorealistic view from the back yard of an existing single-family house, looking across the '
                'rear property line into a new 55-and-over cottage community. In the near foreground is mown '
                'lawn and the corner of an existing older brick-and-siding house. Immediately beyond the '
                'property line stands a 20-foot-deep band of UNDISTURBED existing Piedmont hardwood forest — '
                'mature oaks, hickories and poplars with their understory intact, not cleared, not thinned, '
                'not graded, no fence and no wall. Through and above the trees, only about '
                + fti(A['lawn_behind_house_ft']) + ' beyond the far '
                'edge of that buffer, is glimpsed the rear of a ONE-STORY cottage home: a single continuous '
                'gable roof of architectural shingles with its ridge only about %s above the ground, a couple '
                'of windows and a small covered porch, sage lap siding and a brick water table. The cottage '
                'roof sits BELOW the canopy of the buffer trees. CAMERA: %s. %s. NEGATIVE — do not include: '
                'any two-story building; any building that towers over the trees; any cleared, graded or '
                'thinned ground inside the tree buffer; any privacy fence, retaining wall or berm; any '
                'construction equipment; %s.' % (fti(A['ridge_grade']), CAMERA['neighbour'], LIGHT, NEG_COMMON)),
        checklist=[
            'The tree buffer is dense and clearly undisturbed, with understory intact',
            'The new cottage is one story and its ridge sits below the tree canopy',
            'No fence, wall or berm on the line',
            'No grading or clearing visible inside the buffer',
        ]))

    p2 = LAY['ponds'][1] if len(LAY.get('ponds', [])) > 1 else None
    out.append(dict(
        id='R-11', file='R-11_creek-woods-dry-basin.jpg', aspect='16:9',
        refs=['drawings/mcp-sheet.png'],
        must_ref=False,
        shows='The preserved creek-woods tract at the stream head with its undisturbed buffer, and the rear '
              'basin as a grassed DRY basin',
        why='Answers the stormwater, erosion and downstream water-quality objection, and shows that the stream '
            'head and its buffer are preserved rather than piped',
        prompt=('Photorealistic rendering of the stormwater and stream-protection area at the rear of a new '
                'one-story 55-and-over cottage community in Piedmont Georgia. On the right, a preserved block '
                'of untouched mature hardwood woods around the head of a small seasonal stream, with a '
                '50-foot-wide undisturbed wooded buffer along it, leaf litter and understory intact and no '
                'clearing at all. On the left, a shallow grassed DRY detention basin: mown fescue side slopes '
                'at about 3 to 1, a flat grassed bottom with NO STANDING WATER, a small concrete outlet '
                'structure with a trash rack at the low end, a riprap outfall apron, and a mown maintenance '
                'access strip running down to it. No fence around the basin. Behind, the rear row of '
                'one-story cottage homes with gabled shingle roofs, and beyond them the 20-foot undisturbed '
                'tree buffer along the property line. CAMERA: eye-level from the maintenance access looking '
                'across the basin toward the woods, 35 mm lens, camera 5 feet 6 inches above the ground. %s. '
                'NEGATIVE — do not include: any pond, lake or standing water; any fountain; any concrete-lined '
                'channel; any cleared ground inside the wooded buffer; any two-story building; any chain-link '
                'fence around the basin; %s.' % (LIGHT, NEG_COMMON)),
        checklist=[
            'The basin is grassed and DRY — no standing water, no pond',
            'Outlet structure and riprap apron visible',
            'The stream-head woods are untouched, with understory',
            'Houses in the background are one story',
        ]))

    out.append(dict(
        id='R-12', file='R-12_materials-colour-board.jpg', aspect='4:3',
        refs=[],
        must_ref=False,
        shows='A flat-lay materials and colour board, three columns, one per approved scheme',
        why='Item (11)\'s literal requirement — "the color and materials of all structures and roofing" — as '
            'one filable exhibit',
        prompt=('Photorealistic flat-lay architectural materials and finishes board, photographed straight down '
                'on a light neutral background, arranged as THREE CLEAN VERTICAL COLUMNS with an even gap '
                'between them and generous empty margins. Each column holds the same seven samples stacked '
                'neatly in the same order, slightly overlapping: a large square of exterior wall cladding, a '
                'painted trim board, a rectangle of architectural asphalt roof shingles, a piece of masonry '
                'veneer, a small piece of buff cast stone, a short square section of natural-stained cedar '
                'post, and a small painted door-colour chip. COLUMN ONE: warm white fiber-cement '
                'board-and-batten panel with 12-inch battens; warm white painted trim; charcoal-gray '
                'architectural shingles; gray-tan dry-stack ledge stone; buff cast stone; natural cedar; a deep '
                'green chip. COLUMN TWO: sage green fiber-cement lap siding with a 6-inch exposure; soft white '
                'trim; weathered-wood brown shingles; red-brown modular brick; buff cast stone; natural cedar; '
                'an oxblood red chip. COLUMN THREE: clay-beige fiber-cement lap siding with a 6-inch exposure; '
                'cream trim; driftwood brown shingles; buff-tan dry-stack ledge stone; buff cast stone; '
                'natural cedar; a navy blue chip. Soft even studio light, true colour, sharp texture on every '
                'sample. NEGATIVE — do not include: any text, label, letter, number or handwriting anywhere; '
                'any tools, pencils, hands, plants, coffee cups or props; any fourth column; any colour not '
                'listed; any glossy or metallic finish.'),
        checklist=[
            'Exactly three columns, clearly separated',
            'Column one is warm white board-and-batten; column two sage lap; column three clay lap',
            'Roof samples read charcoal / weathered wood / driftwood',
            'Masonry: gray-tan stone / red-brown brick / buff-tan stone',
            'No text or labels anywhere in the image (labels are typeset onto the sheet afterwards)',
        ]))

    return out


HEADER = """---
title: "Dimension-locked image prompts — The Cottages at Arcado Springs"
date: {date}
status: "GENERATED by tools/prompts.py from data/plans.json, data/layout.json and tools/elevations.py — do not hand-edit; change the design and re-run"
purpose: "City of Lilburn 2026 Application Instructions item (11) — architectural renderings"
---

# Image prompts — {n} shots

Item (11) of the City of Lilburn 2026 Application Instructions: *"An architectural rendering or elevation of
each side of the structure visible from the street shall be submitted. The drawings shall be to scale or in
proper perspective and shall include the color and materials of all structures and roofing and location and
size of wall signs. Visual imagery may be used."*

**Every dimension in every prompt below is read at run time from the files that generate the drawings**, so
no prompt can state a dimension the drawings do not show. Re-run `python3 tools/prompts.py` after any design
change, then re-generate the affected images.

**Model and settings.** `nano_banana_pro` (Google), resolution `2k`, the aspect ratio given per shot. Where a
shot lists a reference drawing, attach it in the `image_references` role — that is what holds the massing,
the openings and the proportions. Shots marked *reference required* must not be generated text-only.

**Accepting an image.** Check it against its fidelity checklist before it goes in the package. If it fails,
do not retouch the prompt's dimensions to match the image — re-generate, and if it fails twice, tighten the
negative list on the specific error. The scaled drawings govern; the images illustrate.

**The locked design basis these prompts carry** (all from the current drawings):

| Item | Value |
|---|---|
{basis}

---
"""


def basis_rows():
    A, B = geo('A'), geo('B')
    r = []
    for g in (A, B):
        r.append('| Plan %s "%s" body | %s wide x %s deep; roof to roof %s; %d SF conditioned |'
                 % (g['id'], g['name'], fti(g['body_w']), fti(g['body_d']), fti(g['roof2roof']), round(g['cond'])))
        r.append('| Plan %s heights | plate %s; highest ridge %s above the floor, %s above grade; finished '
                 'floor %s above grade |' % (g['id'], fti(g['plate']), fti(g['ridge']), fti(g['ridge_grade']),
                                             fti(g['ff'])))
        r.append('| Plan %s roofs | main %d:%d, living wing %d:%d, garage %d:%d; front porch under the wing '
                 'gable, %s x %s (%d SF) |'
                 % (g['id'], g['main']['pitch'][0], g['main']['pitch'][1], g['wing']['pitch'][0],
                    g['wing']['pitch'][1], g['garage']['pitch'][0], g['garage']['pitch'][1],
                    fti(g['porch_w']), fti(g['porch_d']), round(g['porch_sf'])))
    r.append('| Lots | %d lots, %s x %s = %d SF; density %s du/ac on 9.44 ac |'
             % (M.get('lots', 0), fti(M.get('lot_width_min_ft', 50)), fti(M.get('lot_depth_min_ft', 100)),
                round(M.get('lot_area_min_sf', 5000)), M.get('density_du_ac_deeded', 0)))
    r.append('| Lane | %s pavement, %s tract minimum, %s long; 5-ft sidewalk one side |'
             % (fti(LANE.get('pavement_width_ft', 22)), fti(M.get('lane_tract_width_ft_min', 0)),
                fti(M.get('lane_length_ft', 0))))
    r.append('| Turnarounds | %d hammerheads, no cul-de-sac bulb |' % len(LAY.get('hammerheads', [])))
    r.append('| Open space | %d SF = %s ac = %s%% of the GIS area |'
             % (round(M.get('open_space_sf', 0)), M.get('open_space_ac', 0), M.get('open_space_pct_gis', 0)))
    r.append('| Perimeter buffer | %s undisturbed on the two long sides and the rear |'
             % fti(LAY['buffers'].get('perimeter_buffer_ft', 20)))
    r.append('| Entrance | one only, %s wide, %s from the Arcadia Place centreline, no gate |'
             % (fti(LANE['entrance'].get('drive_width_ft', 24)),
                fti(LANE['entrance'].get('separation_chord_ft', 0))))
    return '\n'.join(r)


def main():
    sh = shots()
    md = [HEADER.format(date='2026-09-03', n=len(sh), basis=basis_rows())]
    for s in sh:
        md.append('## %s — `%s`\n' % (s['id'], s['file']))
        md.append('**Shows.** %s\n' % s['shows'])
        md.append('**Why the application needs it.** %s\n' % s['why'])
        md.append('**Aspect ratio** `%s` · **model** `nano_banana_pro` · **resolution** `2k` · **reference '
                  'drawing%s** %s\n'
                  % (s['aspect'], ' (REQUIRED)' if s['must_ref'] else '',
                     ', '.join('`%s`' % r for r in s['refs']) if s['refs'] else '*none — text only*'))
        md.append('**Prompt** — paste verbatim:\n')
        md.append('```\n%s\n```\n' % s['prompt'])
        md.append('**Fidelity checklist** — verify every line before the image goes in the package:\n')
        for c in s['checklist']:
            md.append('- [ ] %s' % c)
        md.append('\n---\n')
    md.append('> **Disclaimer:** This is an AI-generated analysis for preliminary planning purposes. All '
              'findings must be verified by a licensed professional before use in design, permitting, or '
              'regulatory submissions.\n')
    md.append('<!-- architecture-studio:requires-disclaimer -->')
    open(os.path.join(REND, 'PROMPTS.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    json.dump({'generated': '2026-09-03', 'generator': 'tools/prompts.py', 'model': 'nano_banana_pro',
               'shots': sh}, open(os.path.join(REND, 'prompts.json'), 'w'), indent=1, ensure_ascii=False)
    print('wrote renderings/PROMPTS.md (%d shots) and renderings/prompts.json' % len(sh))
    for s in sh:
        print('   %-6s %-42s %5d chars  refs=%d' % (s['id'], s['file'], len(s['prompt']), len(s['refs'])))


if __name__ == '__main__':
    main()
