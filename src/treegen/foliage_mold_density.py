"""RF2: añade hojas al rombo sobre moldes sin mover la distribución previa."""
import json
import math
from pathlib import Path

from .foliage import add, cross, dot, finite, mul, norm, sub
from .foliage_molds import budget as base_budget, mold_placements, noise, validate_mold_spec

VERSION = 'foliage-molds-0.1.2'
TREE_TRIANGLE_LIMIT = 12500
BRANCH_ADDED_LIMIT = (TREE_TRIANGLE_LIMIT-5292)//11
SCHEMA = json.loads((Path(__file__).resolve().parents[2]/'schemas/foliage-mold-density.schema.json').read_text())


def budget(spec):
    result = base_budget(spec['base'])
    extra = spec['extra_leaf_count']
    result.update(leaves=result['leaves']+extra, leaf_triangles=result['leaf_triangles']+2*extra,
                  added_triangles=result['added_triangles']+2*extra,
                  repeated_11_tree_triangles=result['repeated_11_tree_triangles']+22*extra)
    return result


def validate_density(spec):
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
    base = validate_mold_spec(spec['base'])
    if not finite(spec) or type(spec['extra_leaf_count']) is not int:
        raise ValueError('Cantidad adicional inválida')
    if base['variant'] != 'diamond' or base['connection_shape'] != 'straight':
        raise ValueError('El aumento aditivo requiere rombo y conexiones rectas')
    if spec['extra_leaf_count'] > 6*base['group_count']:
        raise ValueError('Máximo seis hojas adicionales por grupo')
    work = budget(spec)
    if work['leaves'] > 231 or work['added_triangles'] > BRANCH_ADDED_LIMIT:
        raise ValueError('Presupuesto de hojas/conexiones excedido antes de mallar')
    return spec


def load_density(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Campo repetido: {key}')
            result[key] = value
        return result
    return validate_density(json.loads(Path(path).read_text(), object_pairs_hook=pairs,
        parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v))))


def density_placements(spec, carriers):
    validate_density(spec)
    base = spec['base']
    result = mold_placements(base, carriers)
    ordered = sorted(carriers, key=lambda c: (noise(base['seed'], c['id'], 'density-priority'), c['id']))
    for extra_index in range(spec['extra_leaf_count']):
        carrier = ordered[extra_index % len(ordered)]
        slot = base['leaves_per_group']+extra_index//len(ordered)
        a, b = carrier['points_m']
        tangent = norm(sub(b, a))
        normal = norm(carrier['normal_start'])
        flat = sub(tangent, mul(normal, dot(tangent, normal)))
        if dot(flat, flat) < 1e-10:
            axis = min(((1, 0, 0), (0, 1, 0), (0, 0, 1)), key=lambda v: abs(dot(normal, v)))
            flat = cross(normal, axis)
        x0 = norm(flat)
        y0 = norm(cross(normal, x0))
        leaf_id = f'{carrier["id"]}:leaf:{slot:02d}'
        angle = (noise(base['seed'], leaf_id, 'azimuth')*2-1)*math.pi
        x = add(mul(x0, math.cos(angle)), mul(y0, math.sin(angle)))
        y = norm(cross(normal, x))
        tilt = math.radians((noise(base['seed'], leaf_id, 'tilt')*2-1)*30)
        x = add(mul(x, math.cos(tilt)), mul(normal, math.sin(tilt)))
        t = .75+.23*(.25+.5*noise(base['seed'], leaf_id, 'extra-root'))
        result.append({'id': leaf_id, 'support_id': carrier['id'], 'parent_branch_id': carrier['parent_branch_id'],
            'mold_id': carrier['mold_id'], 'origin_m': add(mul(a, 1-t), mul(b, t)),
            'axes': [x, y, norm(cross(x, y))],
            'length_m': base['leaf_length_m']*(.9+.2*noise(base['seed'], leaf_id, 'size')),
            'width_ratio': .6, 'variant': 'diamond', 'fold_deg': 0, 'surface_segment_t': t})
    return result
