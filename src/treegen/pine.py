"""Pino 0.1.0: estructura, distribución distal y acículas; independiente de bpy."""
import copy
import hashlib
import math
import random


def add(a, b):
    return [x+y for x, y in zip(a, b)]


def mul(a, s):
    return [x*s for x in a]


def sub(a, b):
    return add(a, mul(b, -1))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def unit(a):
    return mul(a, 1/math.sqrt(sum(x*x for x in a)))


def lerp(a, b, t):
    return add(mul(a, 1-t), mul(b, t))


def seed(value, stream):
    return int.from_bytes(hashlib.sha256(f'pine-v1:{value}:{stream}'.encode()).digest()[:4], 'big') % 2147483647


def check_parameters(parameters, limits):
    b, c = parameters['base'], parameters['canopy']
    if c['needles_per_twig'] % 2:
        raise ValueError('Las acículas se distribuyen en pares; cantidad debe ser par')
    if c['needle_width_m'] > c['needle_length_m']*.25:
        raise ValueError('Acícula demasiado ancha para su longitud')
    if b['base_radius_m'] > b['height_m']*.04:
        raise ValueError('Radio incompatible con la altura del pino')
    n = b['whorl_count'] * b['branches_per_whorl']
    # Tubos: tronco 12x8, primarias 4x6 y cuatro ramillas 3x4 por primaria.
    wood = 188 + n*(44 + 4*20)
    foliage = (n*5 + 1)*c['needles_per_twig']*2
    if wood+foliage > limits['triangles']:
        raise ValueError(f'Presupuesto previo excedido: {wood+foliage} triángulos')
    if limits['materials'] < 2:
        raise ValueError('Pino requiere dos materiales')
    return {'wood_triangles': wood, 'added_triangles_max': foliage,
            'triangles_max': wood+foliage, 'materials_max': 2,
            'branches_max': 1+n*5, 'needles_max': (n*5+1)*c['needles_per_twig'],
            'support_attempts_max': 0}


def resolve_pine(blueprint, instance, name, profile, defaults, parameters, budget):
    from .blueprints import canonical_hash
    result = {
        'resolved_version': '1.1', 'blueprint_id': blueprint['id'], 'blueprint_version': blueprint['version'],
        'blueprint_sha256': canonical_hash(blueprint), 'blueprint_definition': copy.deepcopy(blueprint),
        'instance_request': copy.deepcopy(instance), 'profile': name, 'parameters': parameters,
        'profile_validation_claim': copy.deepcopy(profile['validation']),
        'parameters_differ_from_profile': parameters != defaults,
        'base_spec': {'schema_version': 'pine-1.0', 'algorithm': 'pine-whorls',
                      'algorithm_version': blueprint['components']['base'].split('@')[1],
                      'seed': instance['seeds']['base'], 'parameters': parameters['base']},
        'canopy_spec': {'version': 'pine-distal-0.1.0', 'seed': instance['seeds']['canopy'], **parameters['canopy']},
        'base_seeds': {s: seed(instance['seeds']['base'], s) for s in ('structure', 'foliage')},
        'appearance': copy.deepcopy(blueprint['appearance']), 'limits': copy.deepcopy(blueprint['limits']),
        'budget_upper_bound': budget,
    }
    result['resolved_sha256'] = canonical_hash(result)
    return result


def tube(points, radii, sides, vertical=False):
    vertices, faces = [], []
    for i, (p, radius) in enumerate(zip(points, radii)):
        axis = [0,0,1] if vertical else unit(sub(points[min(i+1, len(points)-1)], points[max(i-1, 0)]))
        u = unit(cross(axis, [0, 1, 0] if abs(axis[2]) > .9 else [0, 0, 1]))
        v = cross(axis, u)
        for j in range(sides):
            angle = 2*math.pi*j/sides
            vertices.append(add(p, mul(add(mul(u, math.cos(angle)), mul(v, math.sin(angle))), radius)))
    for i in range(len(points)-1):
        for j in range(sides):
            a, b = i*sides+j, i*sides+(j+1)%sides
            faces.extend([[a, b, b+sides], [a, b+sides, a+sides]])
    for j in range(1, sides-1):
        faces.append([0, j+1, j])
        a = (len(points)-1)*sides
        faces.append([a, a+j, a+j+1])
    return {'vertices': vertices, 'polygons': faces, 'smooth': [False]*len(faces)}


def point_on(branch, t):
    position = t*(len(branch['points_m'])-1)
    i = min(int(position), len(branch['points_m'])-2)
    return lerp(branch['points_m'][i], branch['points_m'][i+1], position-i)


def structure(parameters, structure_seed):
    """Eje y cinco tubos por rama primaria; raíces sobre ejes interiores del padre."""
    b, c = parameters['base'], parameters['canopy']
    rng = random.Random(structure_seed)
    h, radius = b['height_m'], b['base_radius_m']
    phase = rng.uniform(0, 2*math.pi)
    def center(z):
        sway = math.sin(z/h*math.pi)*h*.012*b['irregularity']
        return [sway*math.cos(phase), sway*math.sin(phase), z]
    branches = []
    def branch(identifier, parent, points, radii, sides, whorl=None):
        item = {'id': identifier, 'parent_id': parent, 'points_m': points, 'radii_m': radii,
                'whorl': whorl, 'mesh': tube(points, radii, sides, vertical=parent is None)}
        branches.append(item)
        return item
    trunk = branch('pine:trunk', None, [center(h*i/11) for i in range(12)],
                   [radius*(1-i/11)*.97+radius*.03 for i in range(12)], 8)
    for level in range(b['whorl_count']):
        t = level/(b['whorl_count']-1)
        z = h*(b['crown_base_ratio'] + (.88-b['crown_base_ratio'])*t)
        nominal_length = h*b['crown_radius_ratio']*(1-.88*t)**.95
        rotation = phase + level*2.399963229728653
        for j in range(b['branches_per_whorl']):
            angle = rotation+2*math.pi*j/b['branches_per_whorl']+rng.uniform(-.2,.2)*b['irregularity']
            length = nominal_length*(1+rng.uniform(-1,1)*b['irregularity'])
            direction = [math.cos(angle), math.sin(angle), 0]
            sideways = [-direction[1], direction[0], 0]
            root = point_on(trunk, (z+rng.uniform(-.06,.06)*h/b['whorl_count'])/h)
            points = [add(root, add(mul(direction, length*s), [0, 0, length*b['branch_rise_ratio']*(2*s*s-s)]))
                      for s in (0, 1/3, 2/3, 1)]
            r = radius*.24*(1-.72*t)
            main = branch(f'pine:p:{level}:{j}', trunk['id'], points, [r, r*.72, r*.38, r*.12], 6, level)
            for k, (along, sign) in enumerate(((.38,-1),(.48,1),(.68,-1),(.78,1))):
                origin = point_on(main, along)
                axis = unit(add(mul(direction,.60), mul(sideways,sign*.80)))
                extent = length*b['secondary_length_ratio']*(1.25-.4*along)
                points = [add(origin, add(mul(axis,extent*s), [0,0,extent*.28*s*s])) for s in (0,.5,1)]
                branch(f'{main["id"]}:s:{k}', main['id'], points, [r*.38,r*.20,r*.065],4,level)
    return branches


def needles(parameters, branches, canopy_seed):
    """Pares de láminas estrechas sobre la mitad distal; sin búsqueda ni reintentos."""
    b, c = parameters['base'], parameters['canopy']
    rng = random.Random(canopy_seed)
    placements = []
    count = c['needles_per_twig']//2
    for branch in branches:
        leader = branch['parent_id'] is None
        axis = unit(sub(branch['points_m'][-1], branch['points_m'][-2]))
        side = unit(cross(axis, [0,1,0] if leader else [0,0,1]))
        up = cross(side, axis)
        branch_length = math.dist(branch['points_m'][0], branch['points_m'][-1])
        phase = rng.uniform(0,2*math.pi)
        for pair in range(count):
            t = (.90+.085*pair/max(1,count-1)) if leader else (.35+.61*pair/max(1,count-1))
            origin = point_on(branch,t)
            scale = max(.45,min(1,branch_length/.6)) if not leader else .75
            length = c['needle_length_m']*scale*rng.uniform(.83,1.12)
            for sign in (-1,1):
                angle = phase+pair*2.399963229728653+sign*.20
                radial = add(mul(side,math.cos(angle)),mul(up,math.sin(angle)))
                direction = unit(add(mul(axis,.60+rng.uniform(-.08,.08)),mul(radial,.8)))
                # Limitar la longitud planificada antes de mallar mantiene la punta a H.
                actual = min(length, (b['height_m']-origin[2])*.94/direction[2]) if direction[2]>0 else length
                width = c['needle_width_m']*(actual/c['needle_length_m'])
                tip = add(origin,mul(direction,actual))
                across = unit(cross(direction,axis))
                middle = add(origin,mul(direction,actual*.35))
                coords = [origin, add(middle,mul(across,-width*.5)), tip, add(middle,mul(across,width*.5))]
                placements.append({'support_id':branch['id'], 'origin_m':origin, 'vertices':coords,
                                   'triangles':[[0,1,2],[0,2,3]], 'length_m':actual})
    return placements


def build_pine(resolved):
    parameters = resolved['parameters']
    check_parameters(parameters, resolved['limits'])
    strategy = structure
    if resolved['base_spec']['algorithm_version'] == '0.2.0':
        from .pine_structure_v2 import structure as strategy
    elif resolved['base_spec']['algorithm_version'] != '0.1.0':
        raise ValueError('Versión de estructura de pino no registrada')
    branches = strategy(parameters, resolved['base_seeds']['structure'])
    leaves = needles(parameters, branches, resolved['canopy_spec']['seed'])
    return branches, leaves
