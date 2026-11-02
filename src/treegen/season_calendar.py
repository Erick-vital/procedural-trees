"""Calendario puro y acotado por ID de grupo; sin dependencias Blender/Godot."""
import hashlib
import json
import math
from pathlib import Path
import struct

from jsonschema import Draft202012Validator
from jsonschema.validators import extend

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'season-calendar-0.1.0'
RESOURCE_PATHS = {
    'summer': 'assets/roble-pintado/v0.3.0/foliage.png',
    'autumn': 'assets/roble-otono-pintado/v0.1.0/crossed-atlas.png',
    'bark': 'assets/roble-pintado/v0.2.0/bark.png',
}
StrictValidator = extend(Draft202012Validator, type_checker=Draft202012Validator.TYPE_CHECKER
    .redefine('integer', lambda checker, v: type(v) is int)
    .redefine('number', lambda checker, v: type(v) in (int, float) and math.isfinite(v)))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _schema(name, value):
    schema = json.loads((ROOT/'schemas'/name).read_text())
    error = next(StrictValidator(schema).iter_errors(value), None)
    if error is not None:
        raise ValueError('Contrato estacional: '+str(list(error.path))+' '+error.message)


def validate_profile(profile, *, resources=True):
    _schema('tree-season-calendar-profile.schema.json', profile)
    c = profile['calendar']
    if any(type(v) is not int for v in profile['limits'].values()):
        raise ValueError('Los límites deben ser enteros')
    if not (c['start_min'] <= c['start_max'] and 0 < c['duration_min'] <= c['duration_max']
            and c['start_max']+c['duration_max'] <= 1):
        raise ValueError('Intervalos del calendario incompatibles')
    for name, path in RESOURCE_PATHS.items():
        resource = profile['resources'][name]
        if resource['path'] != path:
            raise ValueError('Recurso fuera del catálogo estacional')
        if not resources:
            continue
        target = ROOT/path
        if not target.is_file() or not 33 <= target.stat().st_size <= 16*1024*1024:
            raise ValueError('Recurso ausente o excesivo')
        raw = target.read_bytes()
        expected_size = (1254, 1254) if name == 'bark' else (2000, 2000)
        if raw[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack_from('>II', raw, 16) != expected_size:
            raise ValueError('Recurso PNG incompatible')
        if hashlib.sha256(raw).hexdigest() != resource['sha256']:
            raise ValueError('Hash de recurso estacional distinto')
    return profile


def _vector(v, low, high):
    return isinstance(v, list) and len(v) == 3 and all(
        type(x) in (int, float) and math.isfinite(x) and low <= x <= high for x in v)


def validate_groups(groups):
    if not isinstance(groups, list) or not 1 <= len(groups) <= 360:
        raise ValueError('Número de grupos estacionales fuera de presupuesto')
    identifiers = set()
    for g in groups:
        if not isinstance(g, dict) or set(g) != {'id', 'center_m', 'size_m', 'axes'}:
            raise ValueError('Volumen de grupo incompleto o desconocido')
        identifier = g['id']
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 200 or identifier in identifiers:
            raise ValueError('ID de grupo inválido o duplicado')
        identifiers.add(identifier)
        axes = g['axes']
        if not _vector(g['center_m'], -100, 100) or not _vector(g['size_m'], .01, 40):
            raise ValueError('Dimensiones de grupo inválidas')
        if not isinstance(axes, list) or len(axes) != 3 or not all(_vector(a, -1.000001, 1.000001) for a in axes):
            raise ValueError('Ejes de grupo inválidos')
        if any(abs(sum(x*x for x in a)-1) > 1e-5 for a in axes) or any(
            abs(sum(x*y for x, y in zip(axes[i], axes[j]))) > 1e-5 for i, j in ((0, 1), (0, 2), (1, 2))):
            raise ValueError('Ejes de grupo no ortonormales')
    return sorted(groups, key=lambda g: g['id'])


def _random(seed, identifier, domain):
    # 53 bits, sin dependencia del hash aleatorio de Python ni módulo de semilla.
    return (int(digest([VERSION, seed, identifier, domain])[:14], 16) >> 3)/2**53


def _distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def _chord(origin, direction, volume, reach):
    # Intersección de rayo con el elipsoide orientado; t expresado en metros.
    delta = [x-y for x, y in zip(origin, volume['center_m'])]
    scales = [s/2 for s in volume['size_m']]
    p = [sum(x*y for x, y in zip(delta, a))/s for a, s in zip(volume['axes'], scales)]
    d = [sum(x*y for x, y in zip(direction, a))/s for a, s in zip(volume['axes'], scales)]
    aa = sum(x*x for x in d)
    bb = sum(x*y for x, y in zip(p, d))
    cc = sum(x*x for x in p)-1
    disc = bb*bb-aa*cc
    if disc <= 0:
        return 0.0
    root = math.sqrt(disc)
    return max(0.0, min(reach, (-bb+root)/aa)-max(0.0, (-bb-root)/aa))


def build_calendar(groups, profile):
    validate_profile(profile)
    ordered = validate_groups(groups)
    e, c, seed = profile['exposure'], profile['calendar'], profile['seed']
    sizes = {g['id']: max(g['size_m'])/2 for g in ordered}
    chance = {g['id']: _random(seed, g['id'], 'order') for g in ordered}
    directions = []
    for i in range(e['rays']):
        z = 1-2*(i+.5)/e['rays']
        angle = i*math.pi*(3-math.sqrt(5))
        directions.append([math.cos(angle)*math.sqrt(1-z*z), math.sin(angle)*math.sqrt(1-z*z), z])
    rows = []
    for g in ordered:
        identifier = g['id']
        radius = sizes[identifier]
        reach = radius*e['reach_scale']
        neighbors = [o for o in ordered if o['id'] != identifier and
                     _distance(g['center_m'], o['center_m'])-sizes[o['id']] < reach]
        neighbors.sort(key=lambda o: (_distance(g['center_m'], o['center_m'])-sizes[o['id']], o['id']))
        neighbors = neighbors[:e['neighbors']]
        opened = []
        for direction in directions:
            depth = sum(_chord(g['center_m'], direction, o, reach)/max(o['size_m']) for o in neighbors)
            opened.append(math.exp(-e['density']*depth))
        exposure = sum(opened)/len(opened)
        # Correlación local del azar, independiente de los recorridos y de la cámara.
        weighted = [(chance[o['id']], 1/(1+(_distance(g['center_m'], o['center_m'])/radius)**2)) for o in neighbors]
        local = (chance[identifier]+sum(v*w for v, w in weighted))/(1+sum(w for _, w in weighted))
        correlated = (1-c['correlation'])*chance[identifier]+c['correlation']*local
        order = c['exposure_weight']*(1-exposure)+(1-c['exposure_weight'])*correlated
        start = c['start_min']+(c['start_max']-c['start_min'])*order
        duration = c['duration_min']+(c['duration_max']-c['duration_min'])*_random(seed, identifier, 'duration')
        rows.append({'id': identifier, 'start': start, 'duration': duration, 'exposure': exposure,
                     'variation': _random(seed, identifier, 'variation'), 'order': order,
                     'neighbors': [o['id'] for o in neighbors]})
    result = {'schema_version': '1.0', 'algorithm_version': VERSION, 'profile_sha256': digest(profile),
              'groups_sha256': digest(ordered), 'species': profile['species'], 'phase': profile['phase'],
              'seed': seed, 'groups': rows}
    validate_calendar(result)
    return result


def validate_calendar(data):
    _schema('tree-season-calendar-data.schema.json', data)
    identifiers = {g['id'] for g in data['groups']}
    if len(identifiers) != len(data['groups']):
        raise ValueError('Calendario con grupos duplicados')
    for row in data['groups']:
        if row['duration'] <= 0 or row['start']+row['duration'] > 1 or row['id'] in row['neighbors'] or not set(row['neighbors']) <= identifiers:
            raise ValueError('Intervalos o vecindad de calendario inválidos')
    return data


def weight(phase, start, duration):
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in (phase, start, duration)) or not (
            0 <= phase <= 1 and 0 <= start < start+duration <= 1):
        raise ValueError('Fase o intervalo inválido')
    x = max(0.0, min(1.0, (phase-start)/duration))
    return x*x*(3-2*x)
