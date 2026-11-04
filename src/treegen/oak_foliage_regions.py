"""OF9: regiones volumétricas por brazo; nunca añade mallas de envolvente."""
import copy
import math
from collections import Counter
from .branch_structure import add, sub, mul, dot, length
from .oak_growth import sample, unit
from .oak_foliage_balance import build as build_v8
from .oak_foliage_regions_contract import validate_canopy
from .oak_foliage_cards import rooted_panels
from .oak_foliage_canopy import minimum_radius
from .oak_foliage_layout import surface_point
from .seeds import derive_seed


def yaw_vector(v, angle):
    c, s = math.cos(angle), math.sin(angle)
    return (c*v[0]-s*v[1], s*v[0]+c*v[1], v[2])


def transform(g, anchor, angle, branch_id, t):
    axes = [yaw_vector(a, angle) for a in g['axes']]
    center = sub(anchor, [sum(g['root_normalized'][a]*g['size_m'][a]*axes[a][k] for a in range(3)) for k in range(3)])
    return {**g, 'axes': axes, 'center_m': center, 'anchor_m': anchor,
            'parent_branch_id': branch_id, 'parent_t': t}


def centroid(g, geometry):
    points = geometry[g['template_index']]['opaque_samples']
    mean = [sum(q[a] for q in points)/len(points) for a in range(3)]
    return [g['center_m'][k]+sum(mean[a]*g['size_m'][a]*g['axes'][a][k] for a in range(3)) for k in range(3)]


def region_plan(groups, structure, geometry, seed):
    """Cupos heredados de longitud, vigor y exposición; volúmenes no radiales."""
    h = structure['preset']['height_m']; regions = []
    for bid in sorted({g['parent_branch_id'].split('/')[0] for g in groups}):
        gs = [g for g in groups if g['parent_branch_id'].split('/')[0] == bid]
        points = [centroid(g, geometry) for g in gs]
        center = [sum(q[k] for q in points)/len(points) for k in range(3)]
        radial = unit((center[0], center[1], 0)); side = (-radial[1], radial[0], 0)
        # Amplitud transversal mayor que la trayectoria portadora; no escalar hojas.
        widths = [max(h*.095, max(abs(dot(sub(q, center), a)) for q in points)*.80)
                  for a in (radial, side, (0, 0, 1))]
        widths[1] = max(h*.23, widths[1]); widths[2] = max(h*.07, widths[2]*.85)
        regions.append({'id': 'region:'+bid, 'primary_id': bid, 'center_m': center,
                        'axes': [radial, side, (0, 0, 1)], 'radii_m': widths,
                        'group_count': len(gs), 'targets': [], 'neighbor_id': None})
    # Solo interfaces cercanas: no cerrar el grafo de todos los brazos.
    for r in regions:
        neighbors = [q for q in regions if q != r and math.dist(q['center_m'], r['center_m']) < h*.65 and abs(q['center_m'][2]-r['center_m'][2]) < h*.22]
        if neighbors:
            q = min(neighbors, key=lambda q: (math.dist(q['center_m'], r['center_m']), q['id']))
            r['neighbor_id'] = q['id']
        phase = derive_seed(seed, r['id'])/2147483647*2*math.pi
        n = r['group_count']
        for j in range(n):
            # Nube elipsoidal con profundidad, sin sectores ni malla visible.
            z = 2*(j+.5)/n-1; phi = phase+j*2.399963229728653
            radius = math.sqrt(max(0, 1-z*z))
            local = [.82*radius*math.cos(phi), radius*math.sin(phi), .80*z]
            target = [r['center_m'][k]+sum(local[a]*r['radii_m'][a]*r['axes'][a][k] for a in range(3)) for k in range(3)]
            if r['neighbor_id'] and j % 5 == 0:
                other = next(q for q in regions if q['id'] == r['neighbor_id'])
                target = add(mul(target, .65), mul(other['center_m'], .35))
            r['targets'].append(target)
    return regions


def build(structure, spec, templates, *, prepared=None):
    p = validate_canopy(spec)
    result = copy.deepcopy(build_v8(structure, {**p, 'version': 'oak-foliage-canopy-0.8.0'}, templates, prepared=prepared))
    h = structure['preset']['height_m']; core = h*p['core_radius_over_height']
    groups = result['groups']; regions = region_plan(groups, structure, prepared, p['layout_seed'])
    extras = {q['group_id']: q for q in result['lateral_complements']}
    supports = {}
    for b in structure['branches']:
        if b['order'] < 2: continue
        for j in range(12):
            t = .28+.65*(j+.5)/12; point, _ = sample(b['points'], t)
            if math.hypot(*point[:2]) >= core+h*.025:
                supports.setdefault(b['id'].split('/')[0], []).append((b, t, point))
    protected = [sample(b['points'], t)[0] for b in structure['branches'] if b['order'] == 1 for t in (.12, .28, .44)]
    transformed = {}; complements = {}; changes = []; attempts = 0; positions = []
    for region in regions:
        bid = region['primary_id']; remaining = [g for g in groups if g['parent_branch_id'].split('/')[0] == bid]
        # Objetivos exteriores primero para reservar alcance lateral, sin agotar
        # los soportes útiles con objetivos centrales fáciles.
        targets = sorted(region['targets'], key=lambda q: (-abs(dot(sub(q, region['center_m']), region['axes'][1])), tuple(q)))
        used = Counter()
        for target in targets:
            g = min(remaining, key=lambda g: (math.dist(centroid(g, prepared), target), g['id'])); remaining.remove(g)
            pool = sorted(supports.get(bid, []), key=lambda c: (math.dist(c[2], target), c[0]['id'], c[1]))[:8]
            anchors = [(g['parent_branch_id'], g['parent_t'], g['anchor_m'])]
            for b, t, point in pool:
                if used[b['id']] >= 12: continue
                direction = sub(target, point)
                if length(direction) < 1e-8: direction = (0, 0, 1)
                anchor = surface_point(b, t, unit(direction))
                anchors.append((b['id'], t, anchor))
            options = []
            for branch_id, t, anchor in anchors:
                for turn in range(12):
                    angle = turn*math.pi/6; attempts += 1
                    new = transform(g, anchor, angle, branch_id, t)
                    extra = extras.get(g['id'])
                    extra_g = transform(extra['group'], anchor, angle, branch_id, t) if extra else None
                    cards = rooted_panels(new, new['template_index'])
                    if extra: cards += [rooted_panels(extra_g, extra_g['template_index'])[extra['plane']]]
                    if minimum_radius(cards) < core or min(v[2] for c in cards for v in c['vertices']) < 0: continue
                    center = centroid(new, prepared)
                    # Distancia tridimensional más penalización de congestión;
                    # centro transparente y plano rotado no simulan cobertura.
                    crowd = sum(math.exp(-math.dist(center, q)**2/(h*.055)**2) for q in positions)
                    inward = max(0, (core+h*.09-math.hypot(*center[:2]))/(h*.09))
                    score = math.dist(center, target)**2 + (h*.08)**2*crowd + (h*.16)**2*inward
                    obstruction = sum(math.exp(-math.dist(center, q)**2/(h*.11)**2) for q in protected)
                    score += (h*.22)**2*obstruction + .025*math.dist(anchor, g['anchor_m'])**2
                    options.append((score, branch_id, t, turn, new, extra_g, center))
            # El candidato original siempre es válido y conserva toda la base.
            if not options: raise ValueError('OF9 sin colocación válida: '+g['id'])
            _, branch_id, t, turn, new, extra_g, center = min(options, key=lambda q: q[:4])
            new.update(region_id=region['id'], region_target_m=target,
                       candidate_id=f'{branch_id}:of9:{t:.8f}:{g["id"]}')
            transformed[g['id']] = new; positions.append(center); used[branch_id] += 1
            if extra_g: complements[g['id']] = {**extras[g['id']], 'group': extra_g}
            changes.append({'id': g['id'], 'region_id': region['id'], 'from_branch': g['parent_branch_id'],
                            'to_branch': branch_id, 'anchor_shift_m': math.dist(g['anchor_m'], new['anchor_m']),
                            'centroid_before_m': centroid(g, prepared), 'centroid_after_m': center, 'yaw_step': turn})
    final = [transformed[g['id']] for g in groups]
    extra_final = [complements[q['group_id']] for q in result['lateral_complements']]
    cards = [c for g in final for c in rooted_panels(g, g['template_index'])]
    cards += [rooted_panels(q['group'], q['group']['template_index'])[q['plane']] for q in extra_final]
    assert len(cards) == len(result['foliage'])
    result.update(version=p['version'], spec=p, groups=final, foliage=cards, lateral_complements=extra_final,
                  regions=regions, region_changes=changes, region_attempts=attempts,
                  minimum_card_radius_m=minimum_radius(cards), axis_quotas=dict(Counter(g['parent_branch_id'] for g in final)),
                  fork_quotas=dict(Counter('/'.join(g['parent_branch_id'].split('/')[:2]) for g in final)),
                  scope='mature pilot; biological primary quotas, spatial crown regions; exact OF8 triangle budget')
    return result
