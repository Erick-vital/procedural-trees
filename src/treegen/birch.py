"""Abedul 0.1.0: estructura, distribución y cruzadas sin bpy."""
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import struct

from .pine import add, mul, sub, cross, unit, tube, point_on
from .birch_sample import crossed_group, wood_uv
from .pine_painted_wood import ring_error
from .seeds import derive_seed
from .pine_painted_sample import canonical_hash

ROOT = Path(__file__).resolve().parents[2]
TOLERANCE_M = .005


def validate_resources(resources):
    for role, filename in (('bark', 'bark.png'), ('foliage', 'foliage.png'), ('atlas', 'manifest.json')):
        expected = 'assets/abedul-pintado/v0.1.0/'+filename
        if resources[role]['path'] != expected:
            raise ValueError('Recurso de abedul fuera del catálogo')
        path = ROOT/expected
        limit = 65536 if role == 'atlas' else 16*1024*1024
        if not path.is_file() or path.stat().st_size > limit:
            raise ValueError('Recurso ausente o demasiado grande')
        raw = path.read_bytes()
        if len(raw) > limit or hashlib.sha256(raw).hexdigest() != resources[role]['sha256']:
            raise ValueError('Hash de recurso de abedul distinto de receta')
        if role != 'atlas' and (len(raw) < 33 or raw[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack_from('>II', raw, 16) != (1254, 1254)):
            raise ValueError('PNG de abedul fuera de presupuesto')
    atlas = json.loads((ROOT/resources['atlas']['path']).read_text())
    if atlas['version'] != 'birch-paint-0.1.0' or atlas['atlas_size'] != [1254, 1254] or len(atlas['regions']) != 4:
        raise ValueError('Metadatos de atlas incompatibles')
    for region in atlas['regions']:
        crossed_group([0, 0, 0], [1, 0, 0], .6, region, atlas['atlas_size'])
    return atlas


def budget(parameters, limits):
    # Cota ANTES de simplificar: tubos con tapas y todas las láminas.
    b, c = parameters['base'], parameters['canopy']
    n, s, g = b['primary_count'], b['secondary_count'], c['groups_per_secondary']
    wood = 204+4*26+n*(108+s*20)
    groups = n*(2+s*g)+3
    total = wood+groups*6
    if not 1 <= limits['triangles'] <= 6999 or limits['materials'] != 2 or total > limits['triangles']:
        raise ValueError(f'Presupuesto previo de abedul excedido: {total} tris; máximo 6999/2 materiales')
    if b['base_radius_m'] > b['height_m']*.025:
        raise ValueError('Tronco demasiado grueso para el perfil de abedul')
    return {'wood_triangles': wood, 'added_triangles_max': groups*6, 'triangles_max': total,
            'materials_max': 2, 'groups_max': groups, 'branches_max': 5+n*(1+s), 'support_attempts_max': 0}


def resolve(blueprint, instance, name, profile, defaults, parameters, upper):
    result = {'resolved_version': '1.5', 'blueprint_id': blueprint['id'], 'blueprint_version': blueprint['version'],
              'blueprint_sha256': canonical_hash(blueprint), 'blueprint_definition': copy.deepcopy(blueprint),
              'instance_request': copy.deepcopy(instance), 'profile': name, 'parameters': parameters,
              'profile_validation_claim': copy.deepcopy(profile['validation']),
              'parameters_differ_from_profile': parameters != defaults,
              'base_spec': {'schema_version': 'birch-1.0', 'algorithm': 'birch-crown', 'algorithm_version': '0.1.0',
                            'seed': instance['seeds']['base'], 'parameters': parameters['base']},
              'base_seeds': {s: derive_seed(instance['seeds']['base'], s) for s in ('structure', 'foliage')},
              'canopy_spec': {'version': 'birch-twig-groups-0.1.0', 'seed': instance['seeds']['canopy'], **parameters['canopy']},
              'paint_seed': instance['seeds']['paint'], 'resources': copy.deepcopy(blueprint['resources']),
              'appearance': copy.deepcopy(blueprint['appearance']), 'limits': copy.deepcopy(blueprint['limits']),
              'budget_upper_bound': upper}
    result['resolved_sha256'] = canonical_hash(result)
    return result


def structure(parameters, seed):
    b = parameters['base']
    rng = random.Random(seed)
    h, r = b['height_m'], b['base_radius_m']
    phase = rng.uniform(0, 2*math.pi)
    branches = []

    def branch(identifier, parent, points, radii, sides, vertical=False):
        item = {'id': identifier, 'parent_id': parent, 'points_m': points, 'radii_m': radii, 'sides': sides,
                'mesh': tube(points, radii, sides, vertical)}
        branches.append(item)
        return item

    def center(t):
        return [h*.014*math.sin(t*math.pi)*math.cos(phase+t), h*.012*math.sin(t*math.pi)*math.sin(phase), h*t]

    trunk = branch('birch:trunk', None, [center(i/12) for i in range(13)],
                   [r*(1-i/12)**.9+.006 for i in range(13)], 8, True)
    for i in range(4):
        angle = phase+i*math.pi/2+rng.uniform(-.22, .22)
        direction = [math.cos(angle), math.sin(angle), 0]
        branch(f'birch:root:{i}', trunk['id'], [[0, 0, r*1.2], add(mul(direction, r*1.7), [0, 0, r*.6]),
                add(mul(direction, r*3.4), [0, 0, .025])], [r*.52, r*.30, .018], 5)
    for i in range(b['primary_count']):
        level = i/(b['primary_count']-1)
        t = b['crown_base_ratio']+(.93-b['crown_base_ratio'])*level
        t += rng.uniform(-.022, .022)
        origin = point_on(trunk, t)
        angle = phase+i*2.3999632297+rng.uniform(-1, 1)*b['irregularity']*3
        direction = [math.cos(angle), math.sin(angle), 0]
        envelope = math.sin(math.pi*(.10+.84*level))**.65
        length = h*b['crown_radius_ratio']*envelope*rng.uniform(.78, 1.22)
        # Primarias ascendentes con alturas distintas: las ramillas cuelgan
        # desde ellas, en lugar de formar bandejas horizontales alrededor del eje.
        rise = min(rng.uniform(.55, 1.05), (h-.4-origin[2])/length+.30)
        points = [add(origin, add(mul(direction, length*s), [0, 0, length*(rise*s-.30*s*s)])) for s in [j/8 for j in range(9)]]
        radius = (r*(1-t)**.9+.006)*.36
        main = branch(f'birch:p:{i}', trunk['id'], points,
                      [radius*(1-j/8)**1.15+.0025 for j in range(9)], 6)
        for k in range(b['secondary_count']):
            along = .25+.65*(k+.5)/b['secondary_count']
            origin = point_on(main, along)
            sign = -1 if k % 2 else 1
            a = angle+sign*rng.uniform(.65, 1.15)
            direction = [math.cos(a), math.sin(a), 0]
            extent = length*(.42-.10*along)*rng.uniform(.85, 1.15)
            droop = extent*b['droop_ratio']*rng.uniform(.85, 1.2)
            points = [add(origin, add(mul(direction, extent*s), [0, 0, extent*.14*s-droop*s*s])) for s in (0, .5, 1)]
            rad = radius*(1-along)**1.15*.50+.0015
            branch(f'{main["id"]}:s:{k}', main['id'], points, [rad, rad*.53, .0013], 4)
    return branches


def optimize_wood(branch):
    """Retener extremos y UV; error por tramo completo frente a todos sus anillos."""
    result = copy.deepcopy(branch)
    vertices, sides = branch['mesh']['vertices'], branch['sides']
    kept = list(range(len(branch['points_m'])))
    # Tronco y raíces mantienen sus anillos; solo se simplifican ramas de copa.
    if branch['id'].startswith('birch:p:'):
        while True:
            candidates = [(ring_error(vertices, sides, kept[j-1], kept[j+1]), j) for j in range(1, len(kept)-1)]
            candidates = [v for v in candidates if v[0] <= TOLERANCE_M]
            if not candidates:
                break
            _, index = min(candidates)
            kept.pop(index)
    faces = []
    for ring in range(len(kept)-1):
        for j in range(sides):
            a, b = ring*sides+j, ring*sides+(j+1)%sides
            faces.extend([[a, b, b+sides], [a, b+sides, a+sides]])
    for j in range(1, sides-1):
        faces.append([0, j+1, j])
        a = (len(kept)-1)*sides
        faces.append([a, a+j, a+j+1])
    indices = [ring*sides+j for ring in kept for j in range(sides)]
    original_uv = wood_uv(branch)
    result['mesh'] = {'vertices': [vertices[j] for j in indices], 'polygons': faces}
    result['uv'] = [original_uv[j] for j in indices]
    result['wood_optimization'] = {'tolerance_m': TOLERANCE_M, 'retained_rings': kept,
          'original_triangles': len(branch['mesh']['polygons']), 'triangles': len(faces), 'caps_preserved': True,
          'ring_correspondence_error_m': max(ring_error(vertices, sides, a, z) for a, z in zip(kept, kept[1:]))}
    return result


def distribute(branches, parameters, seed):
    rng = random.Random(seed)
    c, h = parameters['canopy'], parameters['base']['height_m']
    frames = []
    for branch in branches:
        identifier = branch['id']
        if identifier.startswith('birch:root:'):
            continue
        stations = (.83, .89, .94) if identifier == 'birch:trunk' else (
            tuple(.28+.66*i/(c['groups_per_secondary']-1) for i in range(c['groups_per_secondary'])) if ':s:' in identifier else (.64, .92))
        for i, t in enumerate(stations):
            t += rng.uniform(-.012, .012)
            origin = point_on(branch, t)
            axis = unit(sub(point_on(branch, min(1, t+.04)), point_on(branch, max(0, t-.04))))
            if ':s:' in identifier:
                axis = unit(add(axis, [0, 0, -.28]))
            length = c['group_length_m']*rng.uniform(.87, 1.1)
            if identifier == 'birch:trunk':
                length *= .75
            frames.append({'id': f'{identifier}:g:{i}', 'support_id': identifier, 'anchor_t': t,
                           'origin_m': origin, 'axis': axis, 'length_m': length, 'phase': rng.uniform(0, math.pi)})
    return frames


def represent(frames, atlas, seed, height):
    groups = []
    for frame in frames:
        variant = int(canonical_hash([seed, frame['id']])[:8], 16) % 4
        region = atlas['regions'][variant]
        probe = crossed_group(frame['origin_m'], frame['axis'], 1.0, region, atlas['atlas_size'], frame['phase'])
        delta_z = max(v[2]-frame['origin_m'][2] for v in probe['vertices'])
        length = frame['length_m']
        if delta_z > 0:
            length = min(length, (height-.005-frame['origin_m'][2])/delta_z)
        group = crossed_group(frame['origin_m'], frame['axis'], length, region, atlas['atlas_size'], frame['phase'])
        group.update(id=frame['id'], support_id=frame['support_id'], anchor_t=frame['anchor_t'], atlas_variant=variant)
        groups.append(group)
    return groups


def build(resolved):
    upper = budget(resolved['parameters'], resolved['limits'])
    if upper != resolved['budget_upper_bound']:
        raise ValueError('Cota de presupuesto de abedul alterada')
    atlas = validate_resources(resolved['resources'])
    branches = structure(resolved['parameters'], resolved['base_seeds']['structure'])
    frames = distribute(branches, resolved['parameters'], resolved['canopy_spec']['seed'])
    groups = represent(frames, atlas, resolved['paint_seed'], resolved['parameters']['base']['height_m'])
    wood = [optimize_wood(b) for b in branches]
    actual = sum(len(b['mesh']['polygons']) for b in wood)+sum(len(g['polygons']) for g in groups)
    if len(groups) != upper['groups_max'] or actual > upper['triangles_max']:
        raise ValueError('Geometría excede la cota previa')
    return branches, wood, groups
