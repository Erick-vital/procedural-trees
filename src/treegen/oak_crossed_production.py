"""Contrato de producción: tres láminas y atlas/plantillas congelados."""
import copy
import hashlib
import json
from pathlib import Path
import struct
from .oak_crossed import groups,panels
from .oak_painted_tree import build as painted_build
from .pine_painted_sample import canonical_hash
ROOT=Path(__file__).resolve().parents[2]
PATHS={'foliage':'assets/roble-pintado/v0.3.0/foliage.png','bark':'assets/roble-pintado/v0.2.0/bark.png',
    'templates':'assets/roble-pintado/v0.3.0/templates.json','source_foliage':'assets/roble-pintado/v0.2.0/foliage.png','source_layout':'assets/roble-pintado/v0.2.0/manifest.json'}


def validate_resources(resources):
    if set(resources)!=set(PATHS):raise ValueError('Recursos de cruzadas incompletos')
    for key,path in PATHS.items():
        r=resources[key];p=ROOT/path
        if r['path']!=path or not p.is_file() or p.stat().st_size>16*1024*1024:raise ValueError('Recurso fuera del catálogo o excesivo')
        raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=r['sha256']:raise ValueError('Hash de recurso distinto')
        if path.endswith('.png'):
            size=(2000,2000) if key=='foliage' else (1254,1254)
            if raw[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack_from('>II',raw,16)!=size:raise ValueError('Dimensiones de recurso incorrectas')
    frozen=json.loads((ROOT/PATHS['templates']).read_text())
    if len(frozen['templates'])!=8 or (frozen['grid'],frozen['tile_px'],frozen['usable'])!=(5,400,.92):raise ValueError('Plantillas incompatibles')
    return frozen


def check_parameters(parameters,blueprint):
    from .blueprints import _check_parameters
    validate_resources(blueprint['resources'])
    historical=copy.deepcopy(blueprint);historical['schema_version']='1.0';historical['limits']['materials']=3
    previous=_check_parameters(parameters,historical)
    added=14*parameters['canopy']['group_count'];total=previous['wood_triangles']+added
    if blueprint['limits']['materials']<2 or total>blueprint['limits']['triangles']:raise ValueError('Presupuesto de cruzadas excedido')
    return {**previous,'added_triangles_max':added,'triangles_max':total,'materials_max':2,'panels_max':3*parameters['canopy']['group_count']}


def resolve(blueprint,instance,name,profile,defaults,parameters,budget):
    from .oak_painted import resolve as painted_resolve
    result=painted_resolve(blueprint,instance,name,profile,defaults,parameters,budget)
    result['resolved_version']='1.4';result.pop('resolved_sha256');result['resolved_sha256']=canonical_hash(result)
    return result


def build(reference,source,resolved):
    frozen=validate_resources(resolved['resources']);layout=json.loads((ROOT/PATHS['source_layout']).read_text())
    old,cards,kept=painted_build(reference,source,layout,resolved['paint_seed'])
    items=groups(source,cards);templates=frozen['templates'];assignments={};crossed=[]
    for g in items:
        index=min(range(8),key=lambda i:sum((x-y)**2 for x,y in zip(g['descriptor'],templates[i]['descriptor'])))
        assignments[g['id']]=index;crossed.extend(panels(g,index,3))
    return old['wood'],crossed,items,assignments,kept
