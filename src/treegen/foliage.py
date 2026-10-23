"""Contrato y colocaciones RF1 en metros finales; sin bpy ni reglas de ramas.

La geometría local pertenece al adaptador Blender. Cada hoja conserva su raíz,
soporte y marco ortonormal dextrógiro: +X largo, +Y ancho y +Z normal.
"""
import hashlib
import json
import math
from pathlib import Path

VERSION = 'foliage-unit-0.1.0'
MAX_LEAVES = 32
MAX_TRIANGLES = 128
SCHEMA = json.loads((Path(__file__).resolve().parents[2] / 'schemas/foliage-unit.schema.json').read_text())


def validate_schema(spec):
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        # Blender incluye fastjsonschema. Este contrato usa el subconjunto draft7.
        import fastjsonschema
        try:
            fastjsonschema.compile({**SCHEMA, '$schema': 'http://json-schema.org/draft-07/schema#'})(spec)
        except fastjsonschema.JsonSchemaException as exc:
            raise ValueError(str(exc)) from exc
    else:
        for error in Draft202012Validator(SCHEMA).iter_errors(spec):
            raise ValueError(f'{list(error.path)}: {error.message}')


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def mul(a, k):
    return tuple(x*k for x in a)


def sub(a, b):
    return add(a, mul(b, -1))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def norm(a):
    length = math.sqrt(dot(a, a))
    if length < 1e-8:
        raise ValueError('Vector nulo o segmento demasiado corto')
    return mul(a, 1/length)


def finite(data):
    if isinstance(data, dict):
        return all(finite(v) for v in data.values())
    if isinstance(data, (list, tuple)):
        return all(finite(v) for v in data)
    if isinstance(data, (int, float)):
        return not isinstance(data, bool) and math.isfinite(data)
    return True


def validate_unit(spec):
    # terminal es el único booleano permitido; los numéricos no aceptan bool.
    if not isinstance(spec, dict):
        raise ValueError('La especificación debe ser un objeto')
    validate_schema(spec)
    numeric = {**spec, 'support': {k: v for k, v in spec['support'].items() if k != 'terminal'}}
    if not finite(numeric):
        raise ValueError('Valores numéricos no finitos o booleanos')
    points = spec['support']['points_m']
    directions = [norm(sub(b, a)) for a, b in zip(points, points[1:])]
    if any(dot(a, b) < -.95 for a, b in zip(directions, directions[1:])):
        raise ValueError('El portador no admite un giro de casi 180 grados')
    length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
    if length > 2:
        raise ValueError('RF1 limita el portador a 2 m')
    count = math.floor(length/spec['parameters']['spacing_m'] + 1e-8)
    if not 1 <= count <= MAX_LEAVES:
        raise ValueError(f'Número de hojas fuera de 1..{MAX_LEAVES}: {count}')
    return spec


def load_unit(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Campo repetido: {key}')
            result[key] = value
        return result
    spec = json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    return validate_unit(spec)


def support_frames(points):
    """Transporte mínimo de la normal entre segmentos, sin cambios de eje global."""
    frames = []
    for a, b in zip(points, points[1:]):
        tangent = norm(sub(b, a))
        if not frames:
            axis = min(((1., 0., 0.), (0., 1., 0.), (0., 0., 1.)), key=lambda v: abs(dot(tangent, v)))
            radial = norm(sub(axis, mul(tangent, dot(axis, tangent))))
        else:
            old, radial, _ = frames[-1]
            axis = cross(old, tangent)
            sine = math.sqrt(dot(axis, axis))
            if sine > 1e-8:
                axis = mul(axis, 1/sine)
                cosine = dot(old, tangent)
                radial = add(add(mul(radial, cosine), mul(cross(axis, radial), sine)),
                             mul(axis, dot(axis, radial)*(1-cosine)))
            radial = norm(sub(radial, mul(tangent, dot(tangent, radial))))
        frames.append((tangent, radial, norm(cross(tangent, radial))))
    return frames


def signed_noise(seed, leaf_id, channel):
    # Muestreo por id/canal: cantidad y forma no cambian sorteos supervivientes.
    raw = hashlib.sha256(f'{VERSION}:{seed}:{leaf_id}:{channel}'.encode()).digest()
    return int.from_bytes(raw[:8], 'big')/(2**64-1)*2-1


def placements(spec):
    validate_unit(spec)
    support, p = spec['support'], spec['parameters']
    points = support['points_m']
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    length = sum(lengths)
    frames = support_frames(points)
    count = math.floor(length/p['spacing_m'] + 1e-8)
    result = []
    for i in range(count):
        distance = (i+.5)*p['spacing_m']
        index, start = 0, 0.
        while index < len(lengths)-1 and start+lengths[index] < distance:
            start += lengths[index]
            index += 1
        tangent, radial, side = frames[index]
        origin = add(points[index], mul(tangent, distance-start))
        leaf_id = f'{support["id"]}:leaf:{i:02d}'
        noise = lambda channel: signed_noise(spec['seed'], leaf_id, channel)
        azimuth = math.radians(i*p['azimuth_step_deg']+noise('azimuth')*p['jitter_deg'])
        inclination = math.radians(p['inclination_deg']+noise('inclination')*p['jitter_deg'])
        outward = add(mul(radial, math.cos(azimuth)), mul(side, math.sin(azimuth)))
        x = norm(add(mul(tangent, math.cos(inclination)), mul(outward, math.sin(inclination))))
        y = norm(cross(tangent, outward))
        z = norm(cross(x, y))
        roll = math.radians(p['roll_deg']+noise('roll')*p['jitter_deg'])
        y, z = add(mul(y, math.cos(roll)), mul(z, math.sin(roll))), add(mul(z, math.cos(roll)), mul(y, -math.sin(roll)))
        result.append({'id': leaf_id, 'support_id': support['id'],
                       'parent_branch_id': support['parent_branch_id'], 'support_t': distance/length,
                       'origin_m': origin, 'axes': [x, y, z],
                       'length_m': p['leaf_length_m']*(1+noise('size')*p['scale_jitter']),
                       'width_ratio': p['width_ratio'], 'variant': p['variant'], 'fold_deg': p['fold_deg']})
    return result
