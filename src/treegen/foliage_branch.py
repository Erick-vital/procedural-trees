"""RF2: recorridos virtuales sobre madera fija; no genera ramas de madera."""
import copy
import json
import math
from pathlib import Path

from .foliage import (add, cross, digest, dot, finite, mul, norm, placements,
                      signed_noise, sub, support_frames, validate_unit)

VERSION = 'foliage-branch-0.1.0'
MAX_LEAVES = 192
ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT/'schemas/foliage-branch.schema.json').read_text())


def validate_branch(spec):
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
    if not finite(spec) or any(type(spec[key]) is not int for key in ('seed', 'support_count')):
        raise ValueError('Valores no finitos o enteros inválidos')
    count = math.floor(spec['support_length_m']*spec['leaves_per_m']+1e-8)
    if not 1 <= count <= 32 or count*spec['support_count'] > MAX_LEAVES:
        raise ValueError('Trabajo de follaje RF2 excesivo o vacío')
    return spec


def load_branch(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Campo repetido: {key}')
            result[key] = value
        return result
    return validate_branch(json.loads(Path(path).read_text(), object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value))))


def path_sample(points, t):
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    target = t*sum(lengths)
    index, start = 0, 0.
    while index < len(lengths)-1 and start+lengths[index] < target:
        start += lengths[index]
        index += 1
    tangent, radial, side = support_frames(points)[index]
    return add(points[index], mul(tangent, target-start)), tangent, radial, side


def supports(spec, branches, surface_point):
    """surface_point localiza la superficie original; se inyecta desde Blender.

    Pool de 24 recorridos con ids/raíces estables. Cantidad elige un prefijo;
    densidad, forma y patrón no intervienen en la construcción de recorridos.
    """
    validate_branch(spec)
    if len(branches) != 4 or len({b['id'] for b in branches}) != 4:
        raise ValueError('RF2 requiere la primaria congelada y sus tres secundarias')
    result = []
    # Empezar por puntas y extender gradualmente hacia la base, sin concentrar
    # todos los puntos en el extremo. La pequeña perturbación mantiene orden.
    slots = [.86, .68, .96, .77, .58, .91]
    for index in range(spec['support_count']):
        branch = branches[index % 4]
        rank = index//4
        support_id = f'{branch["id"]}:support:{rank:02d}'
        noise = signed_noise(spec['seed'], support_id, 'rf2-support')
        t = slots[rank]+noise*.012
        origin, tangent, radial, side = path_sample(branch['points_final_m'], t)
        azimuth = math.radians(rank*137.5+(index % 4)*83+spec['support_roll_deg']+noise*12)
        outward = norm(add(mul(radial, math.cos(azimuth)), mul(side, math.sin(azimuth))))
        insertion = tuple(surface_point(branch['id'], origin, outward))
        angle = math.radians(spec['support_angle_deg'])
        direction = norm(add(mul(tangent, math.cos(angle)), mul(outward, math.sin(angle))))
        length = spec['support_length_m']
        # Recorrido suave de tres puntos; sin bifurcar ni añadir cilindros.
        middle = add(insertion, mul(direction, length*.5))
        bend = norm(add(mul(direction, .95), mul(tangent, .05)))
        end = add(middle, mul(bend, length*.5))
        result.append({'id': support_id, 'parent_branch_id': branch['id'],
            'parent_t': t, 'terminal': t > .9, 'region': 'middle',
            'points_m': [list(p) for p in (insertion, middle, end)], 'centerline_origin_m': origin,
            'surface_direction': outward})
    return result


def branch_placements(spec, carriers):
    validate_branch(spec)
    if len(carriers) != spec['support_count']:
        raise ValueError('Cantidad de soportes incoherente')
    result = []
    for carrier in carriers:
        unit = {'version': 'foliage-unit-0.1.0', 'seed': spec['seed'],
            'support': {key: carrier[key] for key in ('id', 'parent_branch_id', 'parent_t', 'terminal', 'region', 'points_m')},
            'parameters': copy.deepcopy(spec['leaf'])}
        unit['parameters']['spacing_m'] = 1/spec['leaves_per_m']
        validate_unit(unit)
        leaves = placements(unit)
        for i, leaf in enumerate(leaves):
            if spec['pattern'] == 'terminal':
                # Mismo conteo, tamaño, ids y ejes que longitudinal. Solo cambian
                # las raíces: último 15 % del recorrido, sin codificar en signos.
                t = .85+.14*i/max(1, len(leaves)-1)
                leaf['origin_m'] = path_sample(carrier['points_m'], t)[0]
                leaf['support_t'] = t
            leaf['pattern'] = spec['pattern']
            result.append(leaf)
    if len(result) > MAX_LEAVES:
        raise ValueError('Demasiadas hojas')
    return result
