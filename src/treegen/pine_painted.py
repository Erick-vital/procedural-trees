"""PP4: recorridos 0.2.0, anclajes por grupo y representación pintada explícita."""
import copy
import hashlib
import math
import struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
from .pine_painted_sample import canonical_hash
from .pine import point_on, seed
from .pine_structure_v2 import structure
from .pine_painted_sample import panels


def validate_resources(resources):
    for role in ('bark', 'foliage'):
        resource = resources[role]
        expected = f'assets/pino-pintado/v0.1.0/{role}.png'
        if resource['path'] != expected:
            raise ValueError('Recurso fuera del catálogo de pintura')
        path = ROOT / expected
        if not path.is_file() or path.stat().st_size > 16*1024*1024:
            raise ValueError('Textura ausente o demasiado grande')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != resource['sha256']:
            raise ValueError('Hash de textura distinto de la receta')
        if raw[:8] != b'\x89PNG\r\n\x1a\n' or not all(0 < n <= 2048 for n in struct.unpack_from('>II', raw, 16)):
            raise ValueError('Textura PNG fuera de presupuesto')


def check_parameters(parameters, limits, *, representation="pine-painted-crossed@0.1.0"):
    if representation == 'pine-painted-crossed@0.4.0':
        from .pine_painted_cards import budget
        return budget(parameters,limits)
    if representation in ("pine-painted-crossed@0.2.0","pine-painted-crossed@0.3.0"):
        from .pine_painted_volume import budget
        return budget(parameters,limits)
    b = parameters['base']; n = b['whorl_count']*b['branches_per_whorl']
    if b['base_radius_m'] > b['height_m']*.04:
        raise ValueError('Radio incompatible con altura')
    wood = 188+n*44
    groups = n*5+1
    total = wood+groups*12
    if total > limits['triangles'] or limits['materials'] < 2:
        raise ValueError('Presupuesto pintado excedido')
    return {'wood_triangles':wood, 'added_triangles_max':groups*12, 'triangles_max':total,
            'materials_max':2, 'branches_max':1+n*5, 'groups_max':groups, 'support_attempts_max':0}


def resolve(blueprint, instance, name, profile, defaults, parameters, budget):
    result = {'resolved_version':'1.2', 'blueprint_id':blueprint['id'], 'blueprint_version':blueprint['version'],
        'blueprint_sha256':canonical_hash(blueprint), 'blueprint_definition':copy.deepcopy(blueprint),
        'instance_request':copy.deepcopy(instance), 'profile':name, 'parameters':parameters,
        'profile_validation_claim':copy.deepcopy(profile['validation']),
        'parameters_differ_from_profile':parameters != defaults,
        'base_spec':{'schema_version':'pine-1.0','algorithm':'pine-whorls','algorithm_version':'0.2.0',
                     'seed':instance['seeds']['base'],'parameters':parameters['base']},
        'base_seeds':{s:seed(instance['seeds']['base'],s) for s in ('structure','foliage')},
        'canopy_spec':{'version':'pine-path-groups-'+blueprint['components']['distribution'].split('@')[1],'seed':instance['seeds']['canopy'],**parameters['canopy']},
        'paint_seed':instance['seeds']['paint'], 'resources':copy.deepcopy(blueprint['resources']),
        'appearance':copy.deepcopy(blueprint['appearance']), 'limits':copy.deepcopy(blueprint['limits']),
        'budget_upper_bound':budget}
    result['resolved_sha256']=canonical_hash(result)
    return result


def build(resolved):
    """Un grupo por recorrido; tronco/primarias se conservan, secundarias se sustituyen."""
    if resolved['blueprint_definition']['components']['representation'] == 'pine-painted-crossed@0.4.0':
        from .pine_painted_cards import build as cards_build
        return cards_build(resolved)
    if resolved['blueprint_definition']['components']['representation'] == 'pine-painted-crossed@0.3.0':
        from .pine_painted_wood import build as wood_build
        return wood_build(resolved)
    if resolved['blueprint_definition']['components']['representation'] == 'pine-painted-crossed@0.2.0':
        from .pine_painted_volume import build as volume_build
        return volume_build(resolved)
    branches = structure(resolved['parameters'], resolved['base_seeds']['structure'])
    wood = [b for b in branches if b['parent_id'] in (None, 'pine:trunk')]
    groups = []
    for b in branches:
        atlas = int(canonical_hash([resolved['paint_seed'],b['id']])[:8],16)%3
        leader = b['parent_id'] is None
        if leader:
            # El eje vertical necesita una base estable y termina antes de H; la madera conserva la altura exacta.
            # Construir sobre X y transportar al tramo distal vertical evita una base singular.
            origin = point_on(b,.90);end = point_on(b,.995)
            length = math.dist(origin,end)
            proxy = {'id':b['id'],'points_m':[[0,0,0],[length/1.06,0,0]]}
            g = panels(proxy,'crossed',atlas)
            axis = [(end[i]-origin[i])/length for i in range(3)]
            from .pine import cross, unit
            side = unit(cross(axis,[0,1,0]));up = cross(axis,side)
            g['vertices'] = [[origin[i]+v[0]*axis[i]-v[1]*side[i]-v[2]*up[i] for i in range(3)] for v in g['vertices']]
            g['origin_m']=origin
        else:
            g=panels(b,'crossed',atlas,primary=b['parent_id']=='pine:trunk')
        # Escala transversal separada de los recorridos. PP4 usa 1 en los cuatro casos.
        g['anchor_t']=.90 if leader else .35 if b['parent_id']=='pine:trunk' else 0
        g['replacement']='leader-needles' if leader else 'primary-needles' if b['parent_id']=='pine:trunk' else 'secondary-and-needles'
        # La versión inicial congela width_scale=1 en la receta.
        if resolved['parameters']['canopy']['width_scale'] != 1:
            raise ValueError('Esta versión solo admite width_scale=1')
        groups.append(g)
    assert len(groups)==resolved['budget_upper_bound']['groups_max']
    return branches, wood, groups
