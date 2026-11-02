"""Rama aislada de abedul: recorridos y cruzadas, sin dependencia de Blender."""
import math
import random

from .pine import add, sub, mul, unit, cross, point_on, tube

VERSION = 'birch-branch-sample-0.1.1'
STRUCTURE_SEED = 6100
PAINT_SEED = 2718


def crossed_group(origin, axis, length, region, atlas_size, phase=0.0):
    """Tres planos de dos tris; el tallo pintado comparte anclaje con la madera."""
    if not math.isfinite(length) or not .1 <= length <= 1.2:
        raise ValueError('Longitud de grupo fuera de .1–1.2 m')
    if len(origin) != 3 or len(axis) != 3 or not all(math.isfinite(v) for v in [*origin, *axis, phase]):
        raise ValueError('Marco no finito')
    if sum(v*v for v in axis) < 1e-12:
        raise ValueError('Eje nulo')
    width, height = atlas_size
    x0, y0, x1, y1 = region['box']
    ax, ay = region['anchor']
    top = region['tip_y']
    if not (0 <= x0 < ax < x1 <= width <= 2048 and 0 <= y0 <= top < ay < y1 <= height <= 2048):
        raise ValueError('Región de atlas inválida')
    axis = unit(axis)
    side = unit(cross(axis, [0, 1, 0] if abs(axis[2]) > .9 else [0, 0, 1]))
    normal = cross(axis, side)
    vertices, faces, uv = [], [], []
    for plane in range(3):
        angle = phase + plane*math.pi/3
        radial = add(mul(side, math.cos(angle)), mul(normal, math.sin(angle)))
        # Inclinar el eje dentro de cada plano hacia su normal rompe el eje
        # común de desaparición: cruzadas con algo de presencia desde la punta.
        plane_normal = cross(axis, radial)
        growth = add(mul(axis, math.cos(.44)), mul(plane_normal, math.sin(.44)))
        offset = len(vertices)
        # Inset de medio texel para no muestrear celdas vecinas con filtrado.
        for x, y in ((x0+.5, y1-.5), (x1-.5, y1-.5), (x1-.5, y0+.5), (x0+.5, y0+.5)):
            vertices.append(add(origin, add(mul(growth, (ay-y)*length/(ay-top)),
                                             mul(radial, (x-ax)*length/(ay-top)))))
            uv.append([x/width, 1-y/height])
        faces.extend([[offset, offset+1, offset+2], [offset, offset+2, offset+3]])
    return {'vertices': vertices, 'polygons': faces, 'uv': uv,
            'origin_m': list(origin), 'axis': axis, 'length_m': length, 'planes': 3}


def wood_uv(branch):
    sides = branch['sides']
    distances = [0]
    for a, b in zip(branch['points_m'], branch['points_m'][1:]):
        distances.append(distances[-1]+math.dist(a, b))
    # Marcas legibles en ramas finas; V representa longitud, U perímetro.
    return [[(i % sides)/sides, distances[i//sides]/.65]
            for i in range(len(branch['mesh']['vertices']))]


def build_sample(atlas, seed=STRUCTURE_SEED, paint_seed=PAINT_SEED):
    if type(seed) is not int or type(paint_seed) is not int or not 0 <= seed <= 2147483647 or not 0 <= paint_seed <= 2147483647:
        raise ValueError('Semillas enteras fuera de rango')
    rng, paint = random.Random(seed), random.Random(paint_seed)
    wood, groups = [], []

    def branch(identifier, parent, points, radii, sides):
        item = {'id': identifier, 'parent_id': parent, 'points_m': points,
                'radii_m': radii, 'sides': sides, 'mesh': tube(points, radii, sides)}
        wood.append(item)
        return item

    main = branch('birch:sample:primary', None,
                  [[0, 0, 0], [.5, 0, .10], [1.15, .02, .20], [1.7, .08, .17], [2.05, .10, .04]],
                  [.055, .043, .028, .016, .004], 8)
    for i, t in enumerate((.24, .34, .46, .57, .69, .81)):
        origin = point_on(main, t)
        sign = -1 if i % 2 else 1
        length = rng.uniform(.53, .72)*(1-.15*i/5)
        axis = unit([.58, sign*.82, rng.uniform(.06, .16)])
        points = [add(origin, add(mul(axis, length*s), [0, 0, -.16*s*s])) for s in (0, .4, .75, 1)]
        r = .018*(1-.5*i/5)
        branch(f'birch:sample:s:{i}', main['id'], points, [r, r*.68, r*.32, .002], 6)
    for i, item in enumerate(wood):
        # El tallo alfa empieza 12 mm antes del extremo; ambos se solapan.
        axis = unit(sub(item['points_m'][-1], item['points_m'][-2]))
        origin = add(item['points_m'][-1], mul(axis, -.012))
        variant = paint.randrange(4)
        group = crossed_group(origin, axis, .61 if i == 0 else rng.uniform(.56, .68),
                              atlas['regions'][variant], atlas['atlas_size'], paint.uniform(0, math.pi))
        group.update(id=f'birch:sample:group:{i}', support_id=item['id'], atlas_variant=variant)
        groups.append(group)
    total = sum(len(b['mesh']['polygons']) for b in wood)+sum(len(g['polygons']) for g in groups)
    if total >= 7000:
        raise ValueError('Presupuesto de muestra excedido')
    return {'version': VERSION, 'seeds': {'structure': seed, 'paint': paint_seed},
            'wood': wood, 'groups': groups, 'triangles': total,
            'scope': 'Rama aislada; no es receta del árbol completo.'}
