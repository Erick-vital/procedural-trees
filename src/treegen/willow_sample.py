"""Rama de sauce: madera arqueada y grupos colgantes fijos, sin Blender."""
import math
import random

from .pine import add, sub, mul, unit, cross, point_on, tube
from .birch_sample import wood_uv

VERSION = 'willow-branch-sample-0.1.0'
STRUCTURE_SEED = 7100
PAINT_SEED = 2718


def validate_region(region, size):
    if not isinstance(size, list) or len(size) != 2 or any(type(v) is not int or not 1 <= v <= 2048 for v in size):
        raise ValueError('Tamaño de atlas inválido')
    if not isinstance(region, dict):
        raise ValueError('Región inválida')
    box, anchor, tip = region.get('box'), region.get('anchor'), region.get('tip_y')
    if not isinstance(box, list) or len(box) != 4 or not isinstance(anchor, list) or len(anchor) != 2:
        raise ValueError('Marco de atlas inválido')
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in [*box, *anchor, tip]):
        raise ValueError('Coordenadas de atlas no finitas')
    x0, y0, x1, y1 = box
    ax, ay = anchor
    if not (0 <= x0 < ax < x1 <= size[0] and 0 <= y0 < ay < tip < y1 <= size[1]):
        raise ValueError('Anclaje superior o extremo inválido')
    if tip-ay < 16:
        raise ValueError('Región demasiado corta')


def validate_atlas(atlas):
    """Acotar atlas y anclajes antes de crear geometría."""
    if not isinstance(atlas, dict) or atlas.get('version') != 'willow-paint-0.1.0':
        raise ValueError('Versión de pintura de sauce no admitida')
    size, regions = atlas.get('atlas_size'), atlas.get('regions')
    if not isinstance(size, list) or len(size) != 2 or any(type(v) is not int or not 1 <= v <= 2048 for v in size):
        raise ValueError('Tamaño de atlas inválido')
    if not isinstance(regions, list) or len(regions) != 4:
        raise ValueError('Se requieren cuatro regiones')
    for region in regions:
        validate_region(region, size)
    for i, a in enumerate(regions):
        for b in regions[i+1:]:
            x0, y0, x1, y1 = a['box']
            u0, v0, u1, v1 = b['box']
            if min(x1, u1) > max(x0, u0) and min(y1, v1) > max(y0, v0):
                raise ValueError('Regiones solapadas')


def hanging_group(origin, axis, length, region, atlas_size, phase=0.0):
    """Tres planos inclinados; el inicio superior del tallo coincide en el anclaje."""
    if type(length) not in (int, float) or not math.isfinite(length) or not .2 <= length <= 2.2:
        raise ValueError('Longitud fuera de .2–2.2 m')
    if len(origin) != 3 or len(axis) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) for v in [*origin, *axis, phase]):
        raise ValueError('Marco no finito')
    if sum(v*v for v in axis) < 1e-12:
        raise ValueError('Eje nulo')
    validate_region(region, atlas_size)
    width, height = atlas_size
    x0, y0, x1, y1 = region['box']
    ax, ay = region['anchor']
    tip = region['tip_y']
    axis = unit(axis)
    side = unit(cross(axis, [0, 1, 0] if abs(axis[2]) > .9 else [0, 0, 1]))
    normal = cross(axis, side)
    vertices, faces, uv = [], [], []
    scale = length/(tip-ay)
    for plane in range(3):
        angle = phase + plane*math.pi/3
        radial = add(mul(side, math.cos(angle)), mul(normal, math.sin(angle)))
        growth = add(mul(axis, math.cos(.22)), mul(cross(axis, radial), math.sin(.22)))
        offset = len(vertices)
        for x, y in ((x0+.5, y0+.5), (x1-.5, y0+.5), (x1-.5, y1-.5), (x0+.5, y1-.5)):
            vertices.append(add(origin, add(mul(growth, (y-ay)*scale), mul(radial, (x-ax)*scale))))
            uv.append([x/width, 1-y/height])
        faces.extend([[offset, offset+1, offset+2], [offset, offset+2, offset+3]])
    return {'vertices': vertices, 'polygons': faces, 'uv': uv, 'origin_m': list(origin),
            'axis': axis, 'length_m': length, 'planes': 3, 'tilt_rad': .22}


def build_sample(atlas, seed=STRUCTURE_SEED, paint_seed=PAINT_SEED):
    validate_atlas(atlas)
    for value in (seed, paint_seed):
        if type(value) is not int or not 0 <= value <= 2147483647:
            raise ValueError('Semilla entera fuera de rango')
    rng, paint = random.Random(seed), random.Random(paint_seed)
    wood, groups = [], []

    def branch(identifier, parent, points, radii, sides):
        item = {'id': identifier, 'parent_id': parent, 'points_m': points,
                'radii_m': radii, 'sides': sides, 'mesh': tube(points, radii, sides)}
        wood.append(item)
        return item

    main = branch('willow:sample:primary', None,
                  [[0, 0, 0], [.50, .01, .25], [1.10, .03, .40],
                   [1.72, .08, .35], [2.20, .13, .13], [2.50, .15, -.18]],
                  [.075, .063, .049, .034, .017, .003], 8)
    for i, t in enumerate((.20, .28, .36, .44, .52, .60, .68, .76, .84, .92)):
        origin = point_on(main, t)
        sign = -1 if i % 2 else 1
        extent = rng.uniform(.48, .72)*(1-.25*i/9)
        spread = unit([.58, sign*.82, 0])
        points = [add(origin, add(mul(spread, extent*s), [0, 0, .12*s-.50*s*s]))
                  for s in (0, .35, .70, 1)]
        # El segmento final pasa de expansión lateral a caída casi vertical.
        points.append(add(points[-1], [spread[0]*.045, spread[1]*.045, -.20]))
        radius = .022*(1-.50*i/9)
        branch(f'willow:sample:s:{i}', main['id'], points,
               [radius, radius*.75, radius*.48, radius*.22, .0025], 6)
    for i, item in enumerate(wood):
        axis = unit(sub(item['points_m'][-1], item['points_m'][-2]))
        origin = add(item['points_m'][-1], mul(axis, -.012))
        variant = paint.randrange(4)
        group = hanging_group(origin, axis, rng.uniform(1.10, 1.48), atlas['regions'][variant],
                              atlas['atlas_size'], paint.uniform(0, math.pi))
        group.update(id=f'willow:sample:group:{i}', support_id=item['id'], atlas_variant=variant)
        groups.append(group)
    triangles = sum(len(b['mesh']['polygons']) for b in wood)+sum(len(g['polygons']) for g in groups)
    if triangles >= 7000:
        raise ValueError('Presupuesto de muestra excedido')
    return {'version': VERSION, 'seeds': {'structure': seed, 'paint': paint_seed},
            'wood': wood, 'groups': groups, 'triangles': triangles,
            'scope': 'Rama aislada de sauce; no acredita el presupuesto del árbol completo.'}
