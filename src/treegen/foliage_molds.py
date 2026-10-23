"""RF2: moldes Q3 invisibles, muestreo de área y hojas conectadas por grupos."""
import bisect
import hashlib
import json
import math
from pathlib import Path

from .foliage import add, cross, dot, finite, mul, norm, sub, support_frames

VERSION = 'foliage-molds-0.1.1'
MAX_CANDIDATES = 2048
MAX_ADDED_TRIANGLES = 428
SCHEMA = json.loads((Path(__file__).resolve().parents[2]/'schemas/foliage-molds.schema.json').read_text())


def budget(spec):
    groups = spec['group_count']
    leaves = groups*spec['leaves_per_group']
    wood = groups*(8 if spec['connection_shape'] == 'straight' else 14)
    foliage = leaves*(2 if spec['variant'] == 'diamond' else 4)
    return {'groups': groups, 'leaves': leaves, 'twig_triangles': wood,
            'leaf_triangles': foliage, 'added_triangles': wood+foliage,
            'repeated_11_tree_triangles': 5292+11*(wood+foliage)}


def validate_mold_spec(spec):
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
    if not finite(spec) or any(type(spec[k]) is not int for k in ('seed', 'group_count', 'leaves_per_group')):
        raise ValueError('Valores no finitos o enteros inválidos')
    work = budget(spec)
    if work['leaves'] > 96 or work['added_triangles'] > MAX_ADDED_TRIANGLES:
        raise ValueError('Presupuesto RF2 de moldes excedido antes de mallar')
    return spec


def load_mold_spec(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Campo repetido: {key}')
            result[key] = value
        return result
    return validate_mold_spec(json.loads(Path(path).read_text(), object_pairs_hook=pairs,
        parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v))))


def noise(seed, identifier, channel):
    # Protocolo congelado: añadir representaciones no cambia los sorteos previos.
    raw = hashlib.sha256(f'foliage-molds-0.1.0:{seed}:{identifier}:{channel}'.encode()).digest()
    return int.from_bytes(raw[:8], 'big')/2**64


def validate_molds(molds):
    if not isinstance(molds, list) or not 1 <= len(molds) <= 64 or not finite(molds):
        raise ValueError('Moldes inválidos o excesivos')
    count = 0
    ids = set()
    for mold in molds:
        if mold['id'] in ids or not 3 <= len(mold['vertices']) <= 4096:
            raise ValueError('Molde duplicado o vértices excesivos')
        ids.add(mold['id'])
        if any(len(v) != 3 or any(type(x) not in (int, float) for x in v) for v in mold['vertices']):
            raise ValueError('Coordenadas de molde inválidas')
        for face in mold['triangles']:
            if len(face) != 3 or any(type(i) is not int or not 0 <= i < len(mold['vertices']) for i in face):
                raise ValueError('Índices de molde inválidos')
            a, b, c = [mold['vertices'][i] for i in face]
            if dot(cross(sub(b, a), sub(c, a)), cross(sub(b, a), sub(c, a))) <= 4e-20:
                raise ValueError('Cara de molde degenerada')
        count += len(mold['triangles'])
    if not 1 <= count <= 4096:
        raise ValueError('Demasiados triángulos guía')


def sample_surface(spec, molds, exposed):
    """Pool proporcional al área; rechazo de superficie interior inyectado."""
    validate_mold_spec(spec)
    validate_molds(molds)
    triangles, cumulative = [], []
    total = 0.
    for mold in molds:
        for face in mold['triangles']:
            a, b, c = [mold['vertices'][i] for i in face]
            normal = cross(sub(b, a), sub(c, a))
            total += math.sqrt(dot(normal, normal))*.5
            triangles.append((mold, a, b, c, norm(normal)))
            cumulative.append(total)
    candidates = []
    rejected = 0
    for index in range(MAX_CANDIDATES):
        sample_id = f'surface:{index:04d}'
        mold, a, b, c, normal = triangles[min(len(triangles)-1,
            bisect.bisect_right(cumulative, noise(spec['seed'], sample_id, 'area')*total))]
        u = math.sqrt(noise(spec['seed'], sample_id, 'u'))
        v = noise(spec['seed'], sample_id, 'v')
        point = add(mul(a, 1-u), add(mul(b, u*(1-v)), mul(c, u*v)))
        if not exposed(mold['id'], add(point, mul(normal, .0002))):
            rejected += 1
            continue
        candidates.append({'id': f'{mold["id"]}:{sample_id}', 'mold_id': mold['id'],
            'parent_branch_id': mold['parent_branch_id'], 'surface_m': point, 'normal': normal})
    if len(candidates) < spec['group_count']:
        raise ValueError('Superficie exterior insuficiente')
    return candidates, {'attempts': MAX_CANDIDATES, 'accepted': len(candidates),
                        'interior_rejected': rejected, 'guide_area_m2_with_overlaps': total}


def make_support(spec, sample, project, parent_surface, exposed):
    normal = sample['normal']
    start = add(sample['surface_m'], mul(normal, -spec['shell_depth_m']))
    insertion, wood_normal = parent_surface(sample['parent_branch_id'], start)
    first = sub(start, insertion)
    if math.dist(start, insertion) < .05:
        return None
    if spec['connection_shape'] == 'straight':
        if math.dist(start, insertion) > 4:
            return None
        return {'id': sample['id']+':support', 'mold_id': sample['mold_id'],
            'parent_branch_id': sample['parent_branch_id'], 'points_m': [insertion, start],
            'surface_start_m': sample['surface_m'], 'surface_end_m': sample['surface_m'],
            'normal_start': normal, 'normal_end': normal, 'wood_normal': wood_normal,
            'length_m': math.dist(start, insertion)}
    axis = min(((1, 0, 0), (0, 1, 0), (0, 0, 1)), key=lambda v: abs(dot(v, normal)))
    tangent = norm(cross(normal, axis))
    side = norm(cross(normal, tangent))
    directions = []
    for direction in range(8):
        angle = direction*math.pi/4
        d = add(mul(tangent, math.cos(angle)), mul(side, math.sin(angle)))
        directions.append((dot(norm(first), d), direction, d))
    for _, _, d in sorted(directions, key=lambda row: (-row[0], row[1])):
        surface, end_normal = project(sample['mold_id'], add(sample['surface_m'], mul(d, spec['surface_span_m'])))
        if not exposed(sample['mold_id'], add(surface, mul(end_normal, .0002))):
            continue
        end = add(surface, mul(end_normal, -spec['shell_depth_m']))
        second = sub(end, start)
        length = math.dist(insertion, start)+math.dist(start, end)
        if math.dist(start, end) < .1 or length > 4 or dot(norm(first), norm(second)) < -.6:
            continue
        return {'id': sample['id']+':support', 'mold_id': sample['mold_id'],
            'parent_branch_id': sample['parent_branch_id'], 'points_m': [insertion, start, end],
            'surface_start_m': sample['surface_m'], 'surface_end_m': surface,
            'normal_start': normal, 'normal_end': end_normal, 'wood_normal': wood_normal,
            'length_m': length}
    return None


def select_supports(spec, candidates, project, parent_surface, exposed):
    """Selección progresiva: máximo 64 inserciones × 8 direcciones."""
    nearest = [float('inf')]*len(candidates)
    available = set(range(len(candidates)))
    result, failed = [], 0
    for attempt in range(64):
        if not available or len(result) == spec['group_count']:
            break
        index = min(available, key=lambda i: (-nearest[i], candidates[i]['id']))
        available.remove(index)
        carrier = make_support(spec, candidates[index], project, parent_surface, exposed)
        if carrier is None:
            failed += 1
            continue
        result.append(carrier)
        point = candidates[index]['surface_m']
        for i in available:
            nearest[i] = min(nearest[i], sum((x-y)**2 for x, y in zip(candidates[i]['surface_m'], point)))
    if len(result) != spec['group_count']:
        raise ValueError('No se encontraron conexiones dentro del alcance acotado')
    return result, {'failed_group_attempts': failed}


def mold_placements(spec, carriers):
    validate_mold_spec(spec)
    if len(carriers) != spec['group_count']:
        raise ValueError('Conteo de grupos incoherente')
    result = []
    for carrier in carriers:
        a, b = carrier['points_m'][-2:]
        tangent = norm(sub(b, a))
        for i in range(spec['leaves_per_group']):
            t = (i+.5)/spec['leaves_per_group']
            if spec['connection_shape'] == 'straight':
                t = .75+.23*t
            leaf_id = f'{carrier["id"]}:leaf:{i:02d}'
            normal = norm(add(mul(carrier['normal_start'], 1-t), mul(carrier['normal_end'], t)))
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
            z = norm(cross(x, y))
            result.append({'id': leaf_id, 'support_id': carrier['id'], 'parent_branch_id': carrier['parent_branch_id'],
                'mold_id': carrier['mold_id'], 'origin_m': add(mul(a, 1-t), mul(b, t)),
                'axes': [x, y, z], 'length_m': spec['leaf_length_m']*(.9+.2*noise(spec['seed'], leaf_id, 'size')),
                'width_ratio': .6, 'variant': spec['variant'],
                'fold_deg': 0 if spec['variant'] == 'diamond' else 25, 'surface_segment_t': t})
    return result


def connection_geometry(carrier, spec):
    """Tubos triangulares de dos/tres anillos; caras exteriores y tapas."""
    points = [tuple(p) for p in carrier['points_m']]
    frames = support_frames(points)
    points[0] = add(points[0], mul(frames[0][0], -.04))
    vertices, faces = [], []
    rings = len(points)
    for ring, point in enumerate(points):
        _, radial, side = frames[min(ring, len(frames)-1)]
        radius = spec['twig_radius_m']*(1-ring/(rings-1)*(1-spec['tip_radius_ratio']))
        for i in range(3):
            angle = 2*math.pi*i/3
            vertices.append(add(point, mul(add(mul(radial, math.cos(angle)), mul(side, math.sin(angle))), radius)))
    for ring in range(rings-1):
        for i in range(3):
            a, b = ring*3+i, ring*3+(i+1)%3
            faces.extend([(a, b, b+3), (a, b+3, a+3)])
    last = (rings-1)*3
    faces.extend([(0, 2, 1), (last, last+1, last+2)])
    return vertices, faces
