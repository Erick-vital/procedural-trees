"""PP2 0.1.0: selección congelada y láminas; sin dependencias de Blender."""
import math
from .pine import build_pine, point_on, sub, unit, cross, add, mul
import hashlib
import json

def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()

VERSION = 'pine-painted-sample-0.1.0'
BRANCH_ID = 'pine:p:2:0'
ATLAS_SEED = 2718
# Coordenadas UV Blender (origen abajo); sprites originales sin remuestrear.
ROW_CENTERS = (.785, .47, .16)


def select(resolved, branch_id=BRANCH_ID):
    if resolved['base_spec']['algorithm_version'] != '0.2.0':
        raise ValueError('La muestra requiere la estructura pine-whorls@0.2.0')
    branches, needles = build_pine(resolved)
    primary = next((b for b in branches if b['id'] == branch_id and b['parent_id'] == 'pine:trunk'), None)
    if primary is None:
        raise ValueError('Identificador de rama primaria inexistente')
    wood = [primary] + [b for b in branches if b['parent_id'] == branch_id]
    ids = {b['id'] for b in wood}
    foliage = [n for n in needles if n['support_id'] in ids]
    coords = [v for b in wood for v in b['mesh']['vertices']] + [v for n in foliage for v in n['vertices']]
    bounds = [[fn(v[k] for v in coords) for k in range(3)] for fn in (min, max)]
    return wood, foliage, {'version': VERSION, 'branch_id': branch_id,
        'resolved_sha256': resolved['resolved_sha256'], 'seeds': resolved['instance_request']['seeds'],
        'atlas_seed': ATLAS_SEED, 'original_bounds_m': bounds,
        'source_geometry_sha256': canonical_hash([wood, foliage]),
        'end_on_direction': unit(sub(primary['points_m'][-1], primary['points_m'][0]))}


def panels(branch, variant, atlas_variant, *, primary=False):
    if variant not in ('folded', 'crossed') or type(atlas_variant) is not int or not 0 <= atlas_variant < 3:
        raise ValueError('Variante de geometría o atlas inválida')
    origin = point_on(branch, .35 if primary else 0)
    end = branch['points_m'][-1]
    axis = unit(sub(end, origin))
    lateral = unit(cross(axis, [0, 0, 1]))
    normal = cross(axis, lateral)
    length = math.dist(origin, end)
    # Atlas horizontal: longitud útil .92, altura de cada sprite ~.30.
    # Extender el extremo solo .06L evita reducirlo a un mechón sin punta.
    length *= 1.06
    vertices, faces, uvs = [], [], []
    strips = [0] if variant == 'folded' else [0, math.pi/2]
    stations = ((.05,.045),(.23,.155),(.65,.155),(.97,.12))
    for angle in strips:
        side = add(mul(lateral, math.cos(angle)), mul(normal, math.sin(angle)))
        up = cross(axis, side)
        for u, half in stations:
            for y in (-half, 0, half) if variant == 'folded' else (-half, half):
                x = (u-.05)/.92
                lift = abs(y)*length*.65 if variant == 'folded' else 0
                vertices.append(add(origin, add(mul(axis,x*length), add(mul(side,y*length),mul(up,lift)))))
                uvs.append([u, ROW_CENTERS[atlas_variant]+y])
        cols = 3 if variant == 'folded' else 2
        offset = len(vertices)-4*cols
        for row in range(3):
            for col in range(cols-1):
                a = offset+row*cols+col
                faces.extend([[a,a+1,a+cols+1],[a,a+cols+1,a+cols]])
    return {'vertices':vertices, 'polygons':faces, 'uv':uvs, 'origin_m':origin,
            'support_id':branch['id'], 'atlas_variant':atlas_variant}


def sample_panels(branches, variant):
    return [panels(b, variant, int(canonical_hash([ATLAS_SEED,b['id']])[:8],16)%3,
                   primary=i==0) for i,b in enumerate(branches)]
