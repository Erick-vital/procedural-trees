"""Sauce 0.1.0: estructura, distribución y cruzadas sin bpy."""
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import struct

from .pine import add, mul, sub, cross, unit, tube, point_on
from .willow_sample import hanging_group, wood_uv, validate_atlas
from .pine_painted_wood import ring_error
from .seeds import derive_seed
from .pine_painted_sample import canonical_hash

ROOT = Path(__file__).resolve().parents[2]
TOLERANCE_M = .005


def validate_resources(resources):
    for role, filename in (('bark', 'bark.png'), ('foliage', 'foliage.png'), ('atlas', 'manifest.json')):
        expected = 'assets/sauce-pintado/v0.1.0/'+filename
        if resources[role]['path'] != expected:
            raise ValueError('Recurso de sauce fuera del catálogo')
        path = ROOT/expected
        limit = 65536 if role == 'atlas' else 16*1024*1024
        if not path.is_file() or path.stat().st_size > limit:
            raise ValueError('Recurso ausente o demasiado grande')
        raw = path.read_bytes()
        if len(raw) > limit or hashlib.sha256(raw).hexdigest() != resources[role]['sha256']:
            raise ValueError('Hash de recurso de sauce distinto de receta')
        if role != 'atlas' and (len(raw) < 33 or raw[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack_from('>II', raw, 16) != (1254, 1254)):
            raise ValueError('PNG de sauce fuera de presupuesto')
    atlas = json.loads((ROOT/resources['atlas']['path']).read_text())
    if atlas['version'] != 'willow-paint-0.1.0' or atlas['atlas_size'] != [1254, 1254] or len(atlas['regions']) != 4:
        raise ValueError('Metadatos de atlas incompatibles')
    validate_atlas(atlas)
    return atlas


def budget(parameters, limits, *, version='0.1.0'):
    """Cota anterior al mallado y a simplificación, con límites de trabajo."""
    b, c = parameters['base'], parameters['canopy']
    bounds = {'height_m': (10, 10), 'base_radius_m': (.28, .45),
              'crown_base_ratio': (.30, .42), 'primary_count': (8, 14),
              'secondary_count': (4, 10), 'crown_radius_ratio': (.38, .56),
              'droop_ratio': (.5, .9), 'irregularity': (.05, .25)}
    canopy_bounds = {'group_length_m': (1.1, 1.9), 'groups_per_secondary': (2, 5)}
    for values, ranges in ((b, bounds), (c, canopy_bounds)):
        if set(values) != set(ranges):
            raise ValueError('Parámetros de sauce incompletos o desconocidos')
        for key, (lo, hi) in ranges.items():
            value = values[key]
            if type(value) not in (int, float) or not math.isfinite(value) or not lo <= value <= hi:
                raise ValueError('Parámetro de sauce fuera de rango: '+key)
            if key in ('primary_count', 'secondary_count', 'groups_per_secondary') and type(value) is not int:
                raise ValueError('Conteo entero requerido: '+key)
    n, s, g = b['primary_count'], b['secondary_count'], c['groups_per_secondary']
    wood = 188+4*26+n*(80+s*28)
    groups = n*(3+s*g)+3
    if version == '0.2.0':
        groups += 5*n*(1+min(3, s))
    elif version != '0.1.0':
        raise ValueError('Versión de presupuesto de sauce no admitida')
    total = wood+groups*6
    if (type(limits['triangles']) is not int or not 1 <= limits['triangles'] <= 6999
            or limits['materials'] != 2 or total > limits['triangles']):
        raise ValueError(f'Presupuesto previo de sauce excedido: {total} tris; máximo 6999/2 materiales')
    return {'wood_triangles': wood, 'added_triangles_max': groups*6, 'triangles_max': total,
            'materials_max': 2, 'groups_max': groups, 'branches_max': 5+n*(1+s), 'support_attempts_max': 0}


def resolve(blueprint, instance, name, profile, defaults, parameters, upper):
    algorithm_version = blueprint['components']['base'].split('@')[1]
    distribution_version = blueprint['components']['distribution'].split('@')[1]
    result = {'resolved_version': '1.6', 'blueprint_id': blueprint['id'], 'blueprint_version': blueprint['version'],
              'blueprint_sha256': canonical_hash(blueprint), 'blueprint_definition': copy.deepcopy(blueprint),
              'instance_request': copy.deepcopy(instance), 'profile': name, 'parameters': parameters,
              'profile_validation_claim': copy.deepcopy(profile['validation']),
              'parameters_differ_from_profile': parameters != defaults,
              'base_spec': {'schema_version': 'willow-1.0', 'algorithm': 'willow-weeping', 'algorithm_version': algorithm_version,
                            'seed': instance['seeds']['base'], 'parameters': parameters['base']},
              'base_seeds': {s: derive_seed(instance['seeds']['base'], s) for s in ('structure', 'foliage')},
              'canopy_spec': {'version': 'willow-hanging-groups-'+distribution_version, 'seed': instance['seeds']['canopy'], **parameters['canopy']},
              'paint_seed': instance['seeds']['paint'], 'resources': copy.deepcopy(blueprint['resources']),
              'appearance': copy.deepcopy(blueprint['appearance']), 'limits': copy.deepcopy(blueprint['limits']),
              'budget_upper_bound': upper}
    result['resolved_sha256'] = canonical_hash(result)
    return result


def structure(parameters, seed):
    """Copa ancha con andamios arqueados y ramificación descendente."""
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

    points = [[h*.020*math.sin(t*math.pi)*math.cos(phase+t),
               h*.018*math.sin(t*math.pi)*math.sin(phase+t*.5), h*.82*t]
              for t in (i/11 for i in range(12))]
    trunk = branch('willow:trunk', None, points,
                   [r*(1-i/11)**.85+.009 for i in range(12)], 8, True)
    for i in range(4):
        angle = phase+i*math.pi/2+rng.uniform(-.22, .22)
        direction = [math.cos(angle), math.sin(angle), 0]
        branch(f'willow:root:{i}', trunk['id'], [[0, 0, r*1.2], add(mul(direction, r*1.7), [0, 0, r*.6]),
                add(mul(direction, r*3.8), [0, 0, .025])], [r*.52, r*.30, .012], 5)
    for i in range(b['primary_count']):
        level = i/(b['primary_count']-1)
        t = b['crown_base_ratio']+(.62-b['crown_base_ratio'])*level+rng.uniform(-.012, .012)
        origin = point_on(trunk, t)
        angle = phase+i*2.3999632297+rng.uniform(-1, 1)*b['irregularity']*2
        direction = [math.cos(angle), math.sin(angle), 0]
        length = h*b['crown_radius_ratio']*(1-.12*level)*rng.uniform(.92, 1.06)
        points = [add(origin, add(mul(direction, length*s), [0, 0, h*(.95*s-.80*s*s)]))
                  for s in (j/6 for j in range(7))]
        radius = (r*(1-t)**.85+.009)*.65
        main = branch(f'willow:p:{i}', trunk['id'], points,
                      [radius*(1-j/6)**1.08+.003 for j in range(7)], 6)
        for k in range(b['secondary_count']):
            along = .20+.74*(k+.5)/b['secondary_count']
            origin = point_on(main, along)
            angle_s = angle+(-1 if k % 2 else 1)*rng.uniform(.55, 1.0)
            direction_s = [math.cos(angle_s), math.sin(angle_s), 0]
            extent = length*(.36-.08*along)*rng.uniform(.90, 1.10)
            droop = extent*b['droop_ratio']*rng.uniform(.90, 1.10)
            points = [add(origin, add(mul(direction_s, extent*s), [0, 0, extent*.12*s-droop*s*s]))
                      for s in (0, .4, .75, 1)]
            rad = radius*(1-along)**1.08*.48+.002
            branch(f'{main["id"]}:s:{k}', main['id'], points, [rad, rad*.70, rad*.36, .002], 4)
    # Misma transformación Z para todos los ejes y vértices. XY y radios
    # nominales conservados; no se vuelve a mallar ni se rompe el anclaje.
    scale_z = h/max(v[2] for b in branches for v in b['mesh']['vertices'])
    for branch in branches:
        for point in branch['points_m']:
            point[2] *= scale_z
        for vertex in branch['mesh']['vertices']:
            vertex[2] *= scale_z
        branch['height_scale_z'] = scale_z
    return branches


def optimize_wood(branch):
    """Retener extremos y UV; error por tramo completo frente a todos sus anillos."""
    result = copy.deepcopy(branch)
    vertices, sides = branch['mesh']['vertices'], branch['sides']
    kept = list(range(len(branch['points_m'])))
    # Tronco, raíces y secundarias finas mantienen anillos; solo primarias.
    if branch['id'].startswith('willow:p:') and ':s:' not in branch['id']:
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
    c = parameters['canopy']
    frames = []
    for branch in branches:
        identifier = branch['id']
        if identifier.startswith('willow:root:'):
            continue
        stations = (.88, .94, .985) if identifier == 'willow:trunk' else (
            tuple(.18+.78*i/(c['groups_per_secondary']-1) for i in range(c['groups_per_secondary']))
            if ':s:' in identifier else (.50, .76, .97))
        for i, t in enumerate(stations):
            t += rng.uniform(-.008, .008)
            origin = point_on(branch, t)
            tangent = unit(sub(point_on(branch, min(1, t+.03)), point_on(branch, max(0, t-.03))))
            # La caída se define en el mundo del árbol, no en la dirección
            # ascendente de la primaria, y no depende de cámara ni pintura.
            axis = unit([tangent[0]*.16, tangent[1]*.16, -1])
            length = c['group_length_m']*rng.uniform(.87, 1.12)
            if identifier == 'willow:trunk':
                length *= .80
            frames.append({'id': f'{identifier}:g:{i}', 'support_id': identifier, 'anchor_t': t,
                           'origin_m': origin, 'axis': axis, 'length_m': length, 'phase': rng.uniform(0, math.pi)})
    return frames


def represent(frames, atlas, seed, height):
    groups = []
    for frame in frames:
        variant = int(canonical_hash([seed, frame['id']])[:8], 16) % 4
        group = hanging_group(frame['origin_m'], frame['axis'], frame['length_m'],
                              atlas['regions'][variant], atlas['atlas_size'], frame['phase'])
        if 'width_scale' in frame:
            # Escala afín del ancho de cada plano alrededor del tallo anclado.
            # El UV y la pintura se conservan; las masas superiores tienen
            # otra proporción que las hebras, sin sumar caras o materiales.
            for start in (0, 4, 8):
                radial = unit(sub(group['vertices'][start+1], group['vertices'][start]))
                for index in range(start, start+4):
                    delta = sub(group['vertices'][index], frame['origin_m'])
                    distance = math.fsum(x*y for x, y in zip(delta, radial))
                    group['vertices'][index] = add(group['vertices'][index], mul(radial, distance*(frame['width_scale']-1)))
            group['width_scale'] = frame['width_scale']
        # Python de Blender y del ejecutor difieren en algún último bit al
        # normalizar marcos. Fijar precisión antes de registrar y exportar;
        # el GLB float32 se audita por separado sin relajar sus comprobaciones.
        group['vertices'] = [[round(v, 12) for v in point] for point in group['vertices']]
        group['axis'] = [round(v, 12) for v in group['axis']]
        group.update(id=frame['id'], support_id=frame['support_id'], anchor_t=frame['anchor_t'], atlas_variant=variant)
        if 'foliage_role' in frame:
            group['foliage_role'] = frame['foliage_role']
        if min(v[2] for v in group['vertices']) < .05:
            raise ValueError('Cortina de sauce invade el suelo; perfil no admitido')
        groups.append(group)
    return groups


def build(resolved):
    upper = budget(resolved['parameters'], resolved['limits'], version=resolved['base_spec']['algorithm_version'])
    if upper != resolved['budget_upper_bound']:
        raise ValueError('Cota de presupuesto de sauce alterada')
    atlas = validate_resources(resolved['resources'])
    if resolved['base_spec']['algorithm_version'] == '0.2.0':
        from .willow_v2 import structure as structure_v2, distribute as distribute_v2
        branches = structure_v2(resolved['parameters'], resolved['base_seeds']['structure'])
        frames = distribute_v2(branches, resolved['parameters'], resolved['canopy_spec']['seed'])
    else:
        branches = structure(resolved['parameters'], resolved['base_seeds']['structure'])
        frames = distribute(branches, resolved['parameters'], resolved['canopy_spec']['seed'])
    groups = represent(frames, atlas, resolved['paint_seed'], resolved['parameters']['base']['height_m'])
    wood = [optimize_wood(b) for b in branches]
    actual = sum(len(b['mesh']['polygons']) for b in wood)+sum(len(g['polygons']) for g in groups)
    if len(groups) != upper['groups_max'] or actual > upper['triangles_max']:
        raise ValueError('Geometría excede la cota previa')
    return branches, wood, groups
