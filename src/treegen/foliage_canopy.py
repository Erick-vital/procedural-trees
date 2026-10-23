"""RF3: ocupación global de moldes Q3 y representación aprobada de RF2."""
import bisect
import copy
import json
import math
from pathlib import Path

from .foliage import add, cross, dot, finite, mul, norm, sub
from .foliage_molds import connection_geometry, noise, validate_molds

VERSION = 'foliage-canopy-0.1.0'
MAX_CANDIDATES = 8192
MAX_SUPPORT_ATTEMPTS = 2048
TREE_TRIANGLE_LIMIT = 12500
REGIONS = ('north', 'east', 'south', 'west')
SCHEMA = json.loads((Path(__file__).resolve().parents[2]/'schemas/foliage-canopy.schema.json').read_text())


def validate_canopy(spec):
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        import fastjsonschema
        try:
            fastjsonschema.compile({**SCHEMA, '$schema': 'http://json-schema.org/draft-07/schema#'})(spec)
        except fastjsonschema.JsonSchemaException as exc:
            raise ValueError(str(exc)) from exc
    else:
        for error in Draft202012Validator(SCHEMA).iter_errors(spec):
            raise ValueError(f'{list(error.path)}: {error.message}')
    if not finite(spec) or any(type(spec[k]) is not int for k in ('seed', 'group_count')):
        raise ValueError('Valores no finitos o enteros inválidos')
    if sum(spec['region_weights'].values()) <= 0:
        raise ValueError('RF3 requiere una región ocupada')
    return spec


def load_canopy(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Campo repetido: {key}')
            result[key] = value
        return result
    return validate_canopy(json.loads(Path(path).read_text(), object_pairs_hook=pairs,
        parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v))))


def budget(base_triangles, groups):
    if type(base_triangles) is not int or not 1 <= base_triangles <= 10000 or type(groups) is not int or not 0 <= groups <= 360:
        raise ValueError('Trabajo RF3 inválido')
    total = base_triangles+20*groups
    if total > TREE_TRIANGLE_LIMIT:
        raise ValueError('Presupuesto RF3 excedido antes de mallar')
    return {'base_triangles': base_triangles, 'groups': groups, 'leaves': groups*6,
            'twig_triangles': groups*8, 'leaf_triangles': groups*12,
            'triangles': total, 'triangle_limit': TREE_TRIANGLE_LIMIT}


def validate_guides(molds):
    if not isinstance(molds, list) or not 1 <= len(molds) <= 128:
        raise ValueError('Cantidad de moldes RF3 inválida')
    if sum(len(m['triangles']) for m in molds) > 4096 or sum(len(m['vertices']) for m in molds) > 16384:
        raise ValueError('Geometría guía RF3 excesiva')
    if len({m['id'] for m in molds}) != len(molds):
        raise ValueError('Ids de moldes repetidos')
    for start in range(0, len(molds), 32):
        validate_molds(molds[start:start+32])


def profile_molds(spec, molds, center):
    validate_canopy(spec)
    validate_guides(molds)
    result = copy.deepcopy(molds)
    for mold in result:
        mold['vertices'] = [[center[k]+(v[k]-center[k])*spec['profile_width_scale'] if k < 2 else v[k]
                             for k in range(3)] for v in mold['vertices']]
    return result


def region_of(point, center):
    x, y = point[0]-center[0], point[1]-center[1]
    if abs(x) >= abs(y):
        return 'east' if x >= 0 else 'west'
    return 'north' if y >= 0 else 'south'


def sample_exposed(spec, molds, center, exposed):
    validate_canopy(spec)
    validate_guides(molds)
    rows, cumulative, total = [], [], 0.
    for mold in molds:
        for face in mold['triangles']:
            a, b, c = [mold['vertices'][i] for i in face]
            normal = cross(sub(b, a), sub(c, a))
            total += math.sqrt(dot(normal, normal))*.5
            rows.append((mold, a, b, c, norm(normal)))
            cumulative.append(total)
    pool = []
    for index in range(MAX_CANDIDATES):
        identifier = f'canopy:surface:{index:04d}'
        mold, a, b, c, normal = rows[min(len(rows)-1,
            bisect.bisect_right(cumulative, total*noise(spec['seed'], identifier, 'area')))]
        u = math.sqrt(noise(spec['seed'], identifier, 'u'))
        v = noise(spec['seed'], identifier, 'v')
        point = add(mul(a, 1-u), add(mul(b, u*(1-v)), mul(c, u*v)))
        if exposed(mold['id'], add(point, mul(normal, .0002))):
            pool.append({'id': f'{mold["id"]}:{identifier}', 'mold_id': mold['id'],
                'parent_branch_id': mold['parent_branch_id'], 'surface_m': point,
                'normal': normal, 'region': region_of(point, center)})
    return pool, {'attempts': MAX_CANDIDATES, 'exposed_samples': len(pool),
                  'interior_rejected': MAX_CANDIDATES-len(pool), 'guide_area_m2_with_overlaps': total}


def region_quotas(group_count, counts, weights):
    total = sum(counts.values())
    if total <= 0:
        raise ValueError('Superficie expuesta vacía')
    raw = {r: group_count*counts[r]/total for r in REGIONS}
    initial = {r: math.floor(raw[r]) for r in REGIONS}
    for r in sorted(REGIONS, key=lambda r: (-(raw[r]-initial[r]), r))[:group_count-sum(initial.values())]:
        initial[r] += 1
    return initial, {r: math.floor(initial[r]*weights[r]+1e-8) for r in REGIONS}


def group_placements(spec, carrier):
    """Cuatro hojas RF2 originales y dos adiciones, con el mismo protocolo."""
    a, b = carrier['points_m']
    tangent = norm(sub(b, a))
    result = []
    for i in range(6):
        leaf_id = f'{carrier["id"]}:leaf:{i:02d}'
        t = .75+.23*(i+.5)/4 if i < 4 else .75+.23*(.25+.5*noise(spec['seed'], leaf_id, 'extra-root'))
        normal = (norm(add(mul(carrier['normal_start'], 1-t), mul(carrier['normal_end'], t)))
                  if i < 4 else norm(carrier['normal_start']))
        flat = sub(tangent, mul(normal, dot(tangent, normal)))
        if dot(flat, flat) < 1e-10:
            axis = min(((1, 0, 0), (0, 1, 0), (0, 0, 1)), key=lambda v: abs(dot(normal, v)))
            flat = cross(normal, axis)
        x0 = norm(flat)
        y0 = norm(cross(normal, x0))
        angle = (noise(spec['seed'], leaf_id, 'azimuth')*2-1)*math.pi
        x = add(mul(x0, math.cos(angle)), mul(y0, math.sin(angle)))
        y = norm(cross(normal, x))
        tilt = math.radians((noise(spec['seed'], leaf_id, 'tilt')*2-1)*30)
        x = add(mul(x, math.cos(tilt)), mul(normal, math.sin(tilt)))
        result.append({'id': leaf_id, 'support_id': carrier['id'], 'parent_branch_id': carrier['parent_branch_id'],
            'mold_id': carrier['mold_id'], 'origin_m': add(mul(a, 1-t), mul(b, t)),
            'axes': [x, y, norm(cross(x, y))],
            'length_m': spec['leaf_length_m']*(.9+.2*noise(spec['seed'], leaf_id, 'size')),
            'width_ratio': .6, 'variant': 'diamond', 'fold_deg': 0, 'surface_segment_t': t})
    return result


def diamond_vertices(leaf):
    return [add(leaf['origin_m'], add(mul(leaf['axes'][0], x*leaf['length_m']),
                 mul(leaf['axes'][1], y*.6*leaf['length_m']))) for x, y in [(0, 0), (.48, -.5), (1, 0), (.48, .5)]]


def select_canopy(spec, pool, parent_surface, height_m, *, layout_leaf_length_m=None):
    validate_canopy(spec)
    if len(pool) > MAX_CANDIDATES or not math.isfinite(height_m) or not 0 < height_m <= 40:
        raise ValueError('Pool o altura RF3 inválidos')
    if layout_leaf_length_m is not None and (not math.isfinite(layout_leaf_length_m) or not .2 <= layout_leaf_length_m <= 1):
        raise ValueError('Escala de planificación inválida')
    counts = {r: sum(c['region'] == r for c in pool) for r in REGIONS}
    initial, quotas = region_quotas(spec['group_count'], counts, spec['region_weights'])
    carriers, leaves = [], []
    attempts, failures = 0, {'short_or_long': 0, 'height': 0}
    # El adaptador puede congelar una escala de planificación para un control
    # exclusivo de representación. El piloto usa su propia escala explícita.
    planning = dict(spec, leaf_length_m=layout_leaf_length_m or spec['leaf_length_m'])
    for region in REGIONS:
        candidates = [c for c in pool if c['region'] == region]
        nearest = [float('inf')]*len(candidates)
        available = set(range(len(candidates)))
        selected = 0
        while selected < quotas[region]:
            if not available or attempts >= MAX_SUPPORT_ATTEMPTS:
                raise ValueError('No se completó el cupo RF3 dentro del trabajo acotado')
            index = min(available, key=lambda i: (-nearest[i], candidates[i]['id']))
            available.remove(index)
            attempts += 1
            sample = candidates[index]
            end = add(sample['surface_m'], mul(sample['normal'], -spec['shell_depth_m']))
            insertion, wood_normal = parent_surface(sample['parent_branch_id'], end)
            length = math.dist(insertion, end)
            if not .05 <= length <= 4:
                failures['short_or_long'] += 1
                continue
            carrier = {'id': sample['id']+':support', 'mold_id': sample['mold_id'],
                'parent_branch_id': sample['parent_branch_id'], 'points_m': [insertion, end],
                'normal_start': sample['normal'], 'normal_end': sample['normal'],
                'wood_normal': wood_normal, 'length_m': length, 'region': region,
                'surface_start_m': sample['surface_m'], 'surface_end_m': sample['surface_m']}
            placed = group_placements(planning, carrier)
            points, _ = connection_geometry(carrier, spec)
            points.extend(p for leaf in placed for p in diamond_vertices(leaf))
            if any(p[2] < -1e-5 or p[2] > height_m+1e-5 for p in points):
                failures['height'] += 1
                continue
            carriers.append(carrier)
            leaves.extend(group_placements(spec, carrier))
            selected += 1
            for i in available:
                nearest[i] = min(nearest[i], sum((x-y)**2 for x, y in zip(candidates[i]['surface_m'], sample['surface_m'])))
    if not carriers:
        raise ValueError('Copa sin grupos ocupados')
    return carriers, leaves, {'samples_by_region': counts, 'unweighted_quotas': initial,
        'group_quotas': quotas, 'connection_attempts': attempts, 'rejected_connections': failures}
