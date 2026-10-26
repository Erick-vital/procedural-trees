"""Roble pintado 0.1.0: misma geometría visible RF3 con un triángulo por hoja."""
import copy
import hashlib
import math
from pathlib import Path
import struct
from .foliage_canopy import diamond_vertices
from .pine_painted_sample import canonical_hash
ROOT=Path(__file__).resolve().parents[2]
OUTLINE=((-0.04,-.6),(1.04,0),(-.04,.6))


def validate_resources(resources):
    resource=resources['foliage']
    if resource['path']!='assets/roble-pintado/v0.1.0/foliage.png':
        raise ValueError('Atlas fuera del catálogo de roble')
    path=ROOT/resource['path']
    if not path.is_file() or path.stat().st_size>16*1024*1024:raise ValueError('Atlas ausente o excesivo')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=resource['sha256']:raise ValueError('Hash del atlas de roble distinto')
    if raw[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack_from('>II',raw,16)!=(1024,1024):raise ValueError('Atlas de roble inválido')


def check_parameters(parameters,blueprint):
    from .blueprints import _check_parameters
    validate_resources(blueprint['resources'])
    historical=copy.deepcopy(blueprint);historical['schema_version']='1.0'
    result=_check_parameters(parameters,historical)
    reduction=6*parameters['canopy']['group_count']
    return {**result,'added_triangles_max':result['added_triangles_max']-reduction,'triangles_max':result['triangles_max']-reduction}


def resolve(blueprint,instance,name,profile,defaults,parameters,budget):
    from .blueprints import load_blueprint,resolve_blueprint
    source=load_blueprint(ROOT/'blueprints/roble_copa_ancha/1.2.0.json')
    request=copy.deepcopy(instance);request.update(schema_version='1.0',blueprint_version='1.2.0');request['seeds'].pop('paint')
    historical=resolve_blueprint(source,request)
    if historical['parameters']!=parameters:raise ValueError('La revisión requiere parámetros históricos idénticos')
    result=copy.deepcopy(historical)
    result.update(resolved_version='1.3',blueprint_version=blueprint['version'],blueprint_sha256=canonical_hash(blueprint),
        blueprint_definition=copy.deepcopy(blueprint),instance_request=copy.deepcopy(instance),
        source_resolved_blueprint=historical,appearance=copy.deepcopy(blueprint['appearance']),
        resources=copy.deepcopy(blueprint['resources']),paint_seed=instance['seeds']['paint'],budget_upper_bound=budget,
        profile_validation_claim=copy.deepcopy(profile['validation']))
    result.pop('resolved_sha256');result['resolved_sha256']=canonical_hash(result)
    return result


def card(leaf,paint_seed):
    if leaf['variant']!='diamond' or leaf['fold_deg']!=0:raise ValueError('Solo rombos planos RF3')
    variant=int(canonical_hash([paint_seed,leaf['id']])[:8],16)%4
    col,row=variant%2,variant//2
    vertices=[[leaf['origin_m'][k]+leaf['length_m']*(x*leaf['axes'][0][k]+y*leaf['axes'][1][k]) for k in range(3)] for x,y in OUTLINE]
    uv=[[(col*512+8+(x+.04)/1.08*496)/1024,1-(row*512+8+(.5-y/1.2)*496)/1024] for x,y in OUTLINE]
    return {'id':leaf['id'],'support_id':leaf['support_id'],'origin_m':leaf['origin_m'],
        'vertices':vertices,'polygons':[[0,1,2]],'uv':uv,'atlas_variant':variant,
        'visible_vertices_m':diamond_vertices(leaf),'source_placement_sha256':canonical_hash(leaf)}


def build(reference,placements,supports,canopy_spec,paint_seed):
    from .foliage_molds import connection_geometry
    wood=copy.deepcopy(reference['wood_mesh'])
    twigs=[]
    for carrier in supports:
        vertices,faces=connection_geometry(carrier,canopy_spec)
        twigs.append({'vertices':vertices,'polygons':faces,'smooth':[False]*len(faces)})
    return wood,twigs,[card(leaf,paint_seed) for leaf in placements]
