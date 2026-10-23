"""RF2 revisada: contrato, región objetivo y selección espacial sin bpy."""
import copy
import json
import math
from pathlib import Path

from .foliage import add, finite, mul, sub, support_frames
from .foliage_branch import validate_branch, supports, branch_placements

VERSION = 'foliage-branch-0.2.0'
MAX_ADDED_TRIANGLES = 768
ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT/'schemas/foliage-twigs.schema.json').read_text())


def budget(spec):
    base, twig = spec['base'], spec['twigs']
    leaves = math.floor(base['support_length_m']*base['leaves_per_m']+1e-8)*base['support_count']
    sides = twig['profile_sides']
    wood = base['support_count']*(4*sides+2*(sides-2)) if twig['enabled'] else 0
    foliage = leaves*(2 if base['leaf']['variant'] == 'diamond' else 4)
    return {'leaves': leaves, 'twig_triangles': wood, 'leaf_triangles': foliage,
            'added_triangles': wood+foliage, 'repeated_11_tree_triangles': 5292+11*(wood+foliage)}


def validate_twigs(spec):
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
    numeric = copy.deepcopy(spec)
    del numeric['twigs']['enabled']
    if not finite(numeric) or type(spec['twigs']['profile_sides']) is not int:
        raise ValueError('Valores no finitos o enteros inválidos')
    validate_branch(spec['base'])
    if budget(spec)['added_triangles'] > MAX_ADDED_TRIANGLES:
        raise ValueError('Presupuesto de hojas y ramillas excedido antes de mallar')
    return spec


def load_twigs(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Campo repetido: {key}')
            result[key] = value
        return result
    return validate_twigs(json.loads(Path(path).read_text(), object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value))))


def target_region(bounds, reference_sha256):
    low, high = bounds
    if not finite(bounds) or len(low) != 3 or len(high) != 3 or any(b <= a for a, b in zip(low, high)):
        raise ValueError('Caja objetivo inválida')
    center = [(a+b)/2 for a, b in zip(low, high)]
    radii = [(b-a)/2 for a, b in zip(low, high)]
    cells = []
    for i in range(8):
        for j in range(8):
            for k in range(4):
                local = [(i+.5)/4-1, (j+.5)/4-1, (k+.5)/2-1]
                if sum(x*x for x in local) <= 1:
                    cells.append([c+x*r for c, x, r in zip(center, local, radii)])
    return {'version': 'rf2-crown-region-0.1.0', 'reference_sha256': reference_sha256,
            'source': 'bounds_of_associated_q3_foliage', 'center_m': center,
            'radii_m': radii, 'grid_shape': [8, 8, 4], 'cells_m': cells}


def segment_distance(point, a, b):
    delta = sub(b, a)
    length2 = sum(x*x for x in delta)
    t = max(0, min(1, sum(x*y for x, y in zip(sub(point, a), delta))/length2))
    return math.dist(point, add(a, mul(delta, t)))


def covered_cells(carrier, target, radius):
    return {i for i, cell in enumerate(target['cells_m'])
            if min(segment_distance(cell, a, b) for a, b in zip(carrier['points_m'], carrier['points_m'][1:])) <= radius}


def validate_target(target):
    if (not isinstance(target, dict) or target.get('version') != 'rf2-crown-region-0.1.0'
            or not isinstance(target.get('cells_m'), list) or not 1 <= len(target['cells_m']) <= 256
            or any(not isinstance(cell, (list, tuple)) or len(cell) != 3
                   or any(type(x) not in (int, float) for x in cell) for cell in target['cells_m'])
            or not finite(target)):
        raise ValueError('Región objetivo inválida o excesiva')


def directed_supports(spec, branches, surface_point, target):
    """192 candidatos como máximo; sin dependencia de parámetros de hoja."""
    validate_twigs(spec)
    validate_target(target)
    pool = []
    for direction in range(8):
        base = copy.deepcopy(spec['base'])
        base.update(support_count=24, support_roll_deg=-180+direction*45)
        # El pool de recorridos no debe depender del trabajo de hojas.
        base['leaves_per_m'] = 5
        for carrier in supports(base, branches, surface_point):
            anchor = carrier['id']
            carrier['id'] += f':direction:{direction}'
            cells = covered_cells(carrier, target, spec['distribution']['influence_radius_m'])
            pool.append((anchor, carrier, cells))
    selected, used, occupied = [], set(), set()
    reachable = set().union(*(cells for _, _, cells in pool))
    while len(selected) < spec['base']['support_count']:
        eligible = [entry for entry in pool if entry[0] not in used]
        anchor, carrier, cells = min(eligible, key=lambda entry: (
            -len(entry[2]-occupied), -len(entry[2]), entry[1]['id']))
        used.add(anchor)
        occupied.update(cells)
        selected.append(carrier)
    return selected, {'candidate_count': len(pool), 'target_cells': len(target['cells_m']),
                      'reachable_cells': len(reachable), 'selected_cells': len(occupied)}


def build_layout(spec, branches, surface_point, target):
    validate_twigs(spec)
    validate_target(target)
    if spec['distribution']['mode'] == 'target':
        carriers, diagnostics = directed_supports(spec, branches, surface_point, target)
    else:
        carriers = supports(spec['base'], branches, surface_point)
        occupied = set().union(*(covered_cells(c, target, spec['distribution']['influence_radius_m']) for c in carriers))
        diagnostics = {'candidate_count': len(carriers), 'target_cells': len(target['cells_m']),
                       'selected_cells': len(occupied)}
    return carriers, branch_placements(spec['base'], carriers), diagnostics


def twig_geometry(carrier, twig):
    """Tubo cerrado de tres anillos; solo convierte un recorrido ya decidido."""
    points = [tuple(p) for p in carrier['points_m']]
    frames = support_frames(points)
    points[0] = add(points[0], mul(frames[0][0], -twig['root_overlap_m']))
    vertices, faces = [], []
    sides = twig['profile_sides']
    for ring, point in enumerate(points):
        _, radial, side = frames[min(ring, len(frames)-1)]
        radius = twig['radius_m']*(1-ring/2*(1-twig['tip_radius_ratio']))
        for i in range(sides):
            angle = 2*math.pi*i/sides
            vertices.append(add(point, mul(add(mul(radial, math.cos(angle)), mul(side, math.sin(angle))), radius)))
    for ring in range(2):
        for i in range(sides):
            a, b = ring*sides+i, ring*sides+(i+1)%sides
            faces.extend([(a, b, b+sides), (a, b+sides, a+sides)])
    for i in range(1, sides-1):
        faces.append((0, i+1, i))
        faces.append((2*sides, 2*sides+i, 2*sides+i+1))
    return vertices, faces
