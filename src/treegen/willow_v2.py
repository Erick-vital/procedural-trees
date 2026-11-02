"""Sauce 0.2: bifurcaciones, masas superiores y hebras; sin motor 3D."""
import math
import random
import copy

from .pine import add, mul, sub, unit, point_on, tube


def bezier(points, t):
    weights = ((1-t)**3, 3*(1-t)**2*t, 3*(1-t)*t*t, t**3)
    return [math.fsum(w*p[j] for w, p in zip(weights, points)) for j in range(3)]


def structure(parameters, seed):
    b = parameters['base']
    rng = random.Random(seed)
    h, r = b['height_m'], b['base_radius_m']
    phase = rng.uniform(0, 2*math.pi)
    heavy = rng.uniform(0, 2*math.pi)
    branches = []

    def branch(identifier, parent, points, radii, sides, role, vertical=False):
        item = {'id': identifier, 'parent_id': parent, 'points_m': points, 'radii_m': radii,
                'sides': sides, 'role': role, 'mesh': tube(points, radii, sides, vertical)}
        branches.append(item)
        return item

    lean = [math.cos(phase)*h*.045, math.sin(phase)*h*.045, 0]
    trunk_points = [[lean[0]*t*t+h*.012*math.sin(t*math.pi), lean[1]*t*t,
                     h*b['crown_base_ratio']*t] for t in (i/11 for i in range(12))]
    trunk = branch('willow:trunk', None, trunk_points,
                   [r*(1-.30*i/11)+.009 for i in range(12)], 8, 'trunk', True)
    for i in range(4):
        angle = phase+i*math.pi/2+rng.uniform(-.22, .22)
        direction = [math.cos(angle), math.sin(angle), 0]
        branch(f'willow:root:{i}', trunk['id'], [[0, 0, r*1.2], add(mul(direction, r*1.7), [0, 0, r*.6]),
                add(mul(direction, r*3.8), [0, 0, .025])], [r*.52, r*.30, .012], 5, 'root')
    for i in range(b['primary_count']):
        # Una primaria nace en el extremo: el tronco no continúa en un poste
        # central. Las demás se bifurcan a alturas próximas, pero distintas.
        origin = point_on(trunk, 1 if i == 0 else rng.uniform(.76, .98))
        angle = phase+2*math.pi*(i+rng.uniform(-.28, .28))/b['primary_count']
        reach = h*b['crown_radius_ratio']*rng.uniform(.60, 1.02)*(1+.12*math.cos(angle-heavy))
        twist = rng.uniform(-.62, .62)
        top_z = h*rng.uniform(.70, .88)
        rise = top_z-origin[2]
        controls = [origin,
                    add(origin, [math.cos(angle-.20*twist)*reach*.10,
                                 math.sin(angle-.20*twist)*reach*.10, rise*rng.uniform(.42, .62)]),
                    add(origin, [math.cos(angle+twist*.55)*reach*rng.uniform(.42, .67),
                                 math.sin(angle+twist*.55)*reach*.60, rise*rng.uniform(.97, 1.22)]),
                    add(origin, [math.cos(angle+twist)*reach, math.sin(angle+twist)*reach, rise])]
        points = [bezier(controls, j/6) for j in range(7)]
        radius = r*.70*rng.uniform(.65, .86)
        main = branch(f'willow:p:{i}', trunk['id'], points,
                      [radius*(1-.90*j/6)**.85+.003 for j in range(7)], 6, 'limb')
        for k in range(b['secondary_count']):
            crown = k < 3
            if crown:
                along = (.44, .68, .90)[k]+rng.uniform(-.06, .05)
            else:
                along = .32+.66*(k-3+.5)/(b['secondary_count']-3)+rng.uniform(-.02, .02)
            start = point_on(main, along)
            bearing = math.atan2(start[1]-origin[1], start[0]-origin[0])+rng.uniform(-1.0, 1.0)
            out = [math.cos(bearing), math.sin(bearing), 0]
            sideways = [-out[1], out[0], 0]
            if crown:
                extent, lift = rng.uniform(1.1, 2.1), rng.uniform(.35, 1.25)
                side = rng.uniform(-.55, .55)
                controls = [start, add(start, add(mul(out, extent*.22), [0, 0, lift*.80])),
                            add(start, add(mul(out, extent*.67), [0, 0, lift*1.15])),
                            add(start, add(add(mul(out, extent), mul(sideways, side)), [0, 0, lift]))]
                radius_s = radius*(1-.90*along)**.85*.46+.002
            else:
                extent = rng.uniform(.35, .95)
                fall = max(.5, start[2]-.65)*rng.uniform(.52, .88)*b['droop_ratio']/.70
                fall = min(fall, start[2]-.65)
                side = rng.uniform(-.42, .42)
                controls = [start, add(start, add(mul(out, extent*.55), [0, 0, rng.uniform(.02, .32)])),
                            add(start, add(add(mul(out, extent), mul(sideways, side*.35)), [0, 0, -fall*.40])),
                            add(start, add(add(mul(out, extent*.90), mul(sideways, side)), [0, 0, -fall]))]
                radius_s = rng.uniform(.006, .011)
            points = [bezier(controls, t) for t in (0, .33, .70, 1)]
            branch(f'{main["id"]}:s:{k}', main['id'], points,
                   [radius_s, radius_s*.75, radius_s*.46, .0015], 4, 'crown' if crown else 'strand')
    scale_z = h/max(v[2] for b in branches for v in b['mesh']['vertices'])
    for branch in branches:
        for point in branch['points_m']:
            point[2] *= scale_z
            point[:] = [round(v, 12) for v in point]
        for vertex in branch['mesh']['vertices']:
            vertex[2] *= scale_z
            vertex[:] = [round(v, 12) for v in vertex]
        branch['height_scale_z'] = round(scale_z, 12)
    return branches


def distribute(branches, parameters, seed):
    rng = random.Random(seed)
    c = parameters['canopy']
    frames = []

    def frame(branch, t, identifier, crown):
        origin = point_on(branch, t)
        tangent = unit(sub(point_on(branch, min(1, t+.035)), point_on(branch, max(0, t-.035))))
        if crown:
            # Orientaciones propias del volumen, en vez de prolongar todas
            # las láminas como una pluma en la dirección de la rama.
            bearing = rng.uniform(0, 2*math.pi)
            axis = unit([math.cos(bearing), math.sin(bearing), rng.uniform(-.55, .55)])
            length = c['group_length_m']*rng.uniform(.62, .82)
            width_scale = rng.uniform(1.75, 2.0)
        else:
            axis = unit([tangent[0]*.32, tangent[1]*.32, -1])
            length = min(c['group_length_m']*rng.uniform(.72, 1.0)*(1-.35*t), .75*(origin[2]-.18))
            width_scale = rng.uniform(.75, 1.0)
        if length < .2:
            raise ValueError('Sin espacio para una hebra sobre el suelo')
        frames.append({'id': identifier, 'support_id': branch['id'], 'anchor_t': t,
                       'origin_m': origin, 'axis': axis, 'length_m': length, 'phase': rng.uniform(0, math.pi),
                       'foliage_role': 'crown' if crown else 'curtain', 'width_scale': width_scale})

    limbs = []
    for branch in branches:
        role = branch['role']
        if role in ('root', 'trunk'):
            continue
        if role == 'limb':
            limbs.append(branch)
            stations = tuple(.28+.70*i/7 for i in range(8))
        elif role == 'crown':
            count = c['groups_per_secondary']+5
            stations = tuple(.04+.92*i/(count-1) for i in range(count))
        else:
            stations = tuple(.10+.84*i/(c['groups_per_secondary']-1) for i in range(c['groups_per_secondary']))
        for i, t in enumerate(stations):
            frame(branch, t+rng.uniform(-.012, .012), f'{branch["id"]}:g:{i}', role != 'strand')
    # Los tres grupos antes asociados a la punta del tronco rellenan ahora
    # bifurcaciones de copa. Todos conservan soporte geométrico explícito.
    for i in range(3):
        branch = limbs[i*len(limbs)//3]
        frame(branch, .88+rng.uniform(-.04, .04), f'willow:crown-fill:{i}', True)
    return frames


def build_sample(resolved):
    """Una primaria real y sus diez secundarias para revisar antes del árbol."""
    from .willow import build
    _, wood, groups = build(resolved)
    main_id = 'willow:p:0'
    main = next(b for b in wood if b['id'] == main_id)
    selected = copy.deepcopy([b for b in wood if b['id'] == main_id or b['parent_id'] == main_id])
    identifiers = {b['id'] for b in selected}
    leaves = copy.deepcopy([g for g in groups if g['support_id'] in identifiers])
    offset = main['points_m'][0]
    for branch in selected:
        for point in branch['points_m']:
            point[:] = sub(point, offset)
        for point in branch['mesh']['vertices']:
            point[:] = sub(point, offset)
    for group in leaves:
        group['origin_m'] = sub(group['origin_m'], offset)
        group['vertices'] = [sub(v, offset) for v in group['vertices']]
    return {'version': 'willow-branch-sample-0.2.0', 'wood': selected, 'groups': leaves,
            'seeds': resolved['instance_request']['seeds'],
            'triangles': sum(len(b['mesh']['polygons']) for b in selected)+sum(len(g['polygons']) for g in leaves),
            'scope': 'Rama de revisión, sustitución de la muestra anterior autorizada por delegación. No aprobación artística del árbol completo.'}
