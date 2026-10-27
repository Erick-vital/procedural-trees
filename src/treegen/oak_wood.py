"""Ensayo aislado: simplificar anillos de madera sin modificar guías ni follaje."""
import copy
import math
from .oak_painted_sample import wood_uv
from .pine_painted_wood import ring_error

VERSION = 'oak-wood-rings-0.1.0'
SIDES = 8


def optimize(branch, tolerance_m=.005):
    if not isinstance(tolerance_m, (float, int)) or not math.isfinite(tolerance_m) or not 0 < tolerance_m <= .02:
        raise ValueError('Tolerancia fuera de (0, .02] m')
    mesh = branch['mesh']; vertices = mesh['vertices']
    count = len(vertices) // SIDES
    if len(vertices) % SIDES or not 2 <= count <= 64 or not all(math.isfinite(x) for v in vertices for x in v):
        raise ValueError('Anillos de roble inválidos')
    expected = [[r*SIDES+j, r*SIDES+(j+1)%SIDES, (r+1)*SIDES+(j+1)%SIDES, (r+1)*SIDES+j]
                for r in range(count-1) for j in range(SIDES)]
    expected += [list(reversed(range(SIDES))), list(range((count-1)*SIDES, count*SIDES))]
    if mesh['polygons'] != expected or len(mesh['smooth']) != len(expected):
        raise ValueError('Topología de tubo no reconocida')
    kept = list(range(count))
    while True:
        candidates = [(ring_error(vertices, SIDES, kept[i-1], kept[i+1]), i) for i in range(1, len(kept)-1)]
        candidates = [row for row in candidates if row[0] <= tolerance_m]
        if not candidates:
            break
        _, i = min(candidates); kept.pop(i)
    ids = [r*SIDES+j for r in kept for j in range(SIDES)]
    polygons = []; smooth = []
    for span, (a, z) in enumerate(zip(kept, kept[1:])):
        for j in range(SIDES):
            polygons.append([span*SIDES+j, span*SIDES+(j+1)%SIDES, (span+1)*SIDES+(j+1)%SIDES, (span+1)*SIDES+j])
            # Solo fusionar zonas con el mismo modo de sombreado.
            flags = {mesh['smooth'][r*SIDES+j] for r in range(a, z)}
            if len(flags) != 1:
                raise ValueError('Cambio de sombreado dentro de un tramo')
            smooth.append(flags.pop())
    polygons += [list(reversed(range(SIDES))), list(range((len(kept)-1)*SIDES, len(kept)*SIDES))]
    smooth += mesh['smooth'][-2:]
    result = copy.deepcopy(branch)
    result['mesh'] = {'vertices': [vertices[i] for i in ids], 'polygons': polygons, 'smooth': smooth}
    original_uv = wood_uv(branch)
    result['uv'] = [original_uv[i] for i in ids]
    result['optimization'] = {'version': VERSION, 'tolerance_m': tolerance_m, 'retained_rings': kept,
        'original_ring_count': count, 'sides': SIDES, 'caps_preserved': True,
        'max_correspondence_error_m': max(ring_error(vertices, SIDES, a, z) for a, z in zip(kept, kept[1:]))}
    return result


def build(wood, branches, tolerance_m, secondary_only=False):
    if not 1 <= len(branches) <= 64 or len(wood) > 424 or len(wood) < len(branches):
        raise ValueError('Presupuesto de madera inválido')
    optimized = [optimize(b, tolerance_m) for b in branches]
    if secondary_only:
        parents = {b['id']: b['parent_id'] for b in branches}
        for before, after in zip(branches, optimized):
            if before['parent_id'] is None or parents[before['parent_id']] is None:
                after['mesh'] = copy.deepcopy(before['mesh'])
                after['uv'] = wood_uv(before)
                count = len(before['mesh']['vertices'])//SIDES
                after['optimization'].update(retained_rings=list(range(count)), max_correspondence_error_m=0., preserved_exact=True)
    pieces = [(b['mesh'], 0, b['uv']) for b in optimized] + copy.deepcopy(wood[len(branches):])
    return pieces, optimized
