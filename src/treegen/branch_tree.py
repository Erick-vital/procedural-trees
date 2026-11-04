"""Contrato y planificación geométrica de árboles ramificados R4 (sin Blender)."""
import copy
import json
import math
from pathlib import Path
from .contracts import ROOT
from .blueprints import load_blueprint,resolve_blueprint
from .oak_crossed_production import build
from .oak_painted_sample import wood_uv
from .branch_sample import make_network,average
from .seeds import derive_seed

VERSION='branch-tree-0.1.0'
KEYS={'version','source_blueprint','profiles','group_count','bare_alpha_cutoff','foliated_alpha_cutoff','collapse_rounds','triangle_limit','material_limit','generation_seconds','foliated_guard'}
PROFILES=['joven','adulto','viejo','viejo_referencia']


def read_strict(path):
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('Campo duplicado: '+k)
            result[k]=v
        return result
    return json.loads(Path(path).read_text(),object_pairs_hook=unique,
                      parse_constant=lambda value:(_ for _ in ()).throw(ValueError(value)))


def validate_definition(d):
    expected={'version':VERSION,'source_blueprint':'blueprints/roble_copa_ancha/2.2.0.json','profiles':PROFILES,
              'group_count':264,'bare_alpha_cutoff':217,'foliated_alpha_cutoff':217,'collapse_rounds':3,
              'triangle_limit':6999,'material_limit':2,'generation_seconds':120,'foliated_guard':'branch-tree-guard-angles-0.1.0'}
    if not isinstance(d,dict) or set(d)!=KEYS or d!=expected:
        raise ValueError('Definición branch-tree 0.1.0 inválida o no soportada')
    if any(type(d[k]) is not int for k in expected if isinstance(expected[k],int)):
        raise ValueError('Límites enteros obligatorios')
    return d


def resolve_tree(definition,request):
    d=validate_definition(definition)
    if not isinstance(request,dict) or set(request)!={'profile','seeds'} or request['profile'] not in PROFILES:
        raise ValueError('Petición de árbol inválida')
    seeds=request['seeds']
    if not isinstance(seeds,dict) or set(seeds)!={'base','canopy','paint'} or any(type(v) is not int or not 0<=v<2147483647 for v in seeds.values()):
        raise ValueError('Semillas enteras explícitas fuera de rango')
    instance={'schema_version':'1.4','blueprint_id':'roble_copa_ancha','blueprint_version':'2.2.0',
              'profile':request['profile'],'seeds':seeds}
    source=resolve_blueprint(load_blueprint(ROOT/d['source_blueprint']),instance)
    n=source['base_spec']['parameters']['primary_branches'];g=source['parameters']['canopy']['group_count']
    if g!=d['group_count']:raise ValueError('Cantidad de grupos incompatible')
    bound=206+158*n+18*g
    if bound>d['triangle_limit']:raise ValueError('Presupuesto previo excedido')
    return {'version':VERSION,'definition':copy.deepcopy(d),'request':copy.deepcopy(request),
            'source_resolved':source,'triangle_upper_bound':bound,
            'components':{'structure':'branch-structure-0.1.0','space':'space-secondary-yaw-0.1.0',
                          'network':'branch-sample-network-0.1.0','bare':'branch-visibility-prune-0.1.0',
                          'foliated':'branch-interior-collapse-0.1.0','foliated_guard':d['foliated_guard']}}


def plan_tree(reference,source,manifest,base_seed):
    """Asignar cada grupo una sola vez al tronco o a su primaria ancestral."""
    wood,foliage,_,_,_=build(reference,source,manifest['resolved_blueprint'])
    by_id={b['id']:b for b in reference['branches']}
    owner={}
    for identifier in by_id:
        current=identifier;seen=set()
        while by_id[current]['parent_id'] is not None and by_id[by_id[current]['parent_id']]['parent_id'] is not None:
            if current in seen:raise ValueError('Jerarquía cíclica')
            seen.add(current);current=by_id[current]['parent_id']
        owner[identifier]=current
    support_owner={s['id']:owner[s['parent_branch_id']] for s in source['supports']}
    majors=[];parts=[]
    for b in reference['branches']:
        if owner[b['id']]!=b['id']:continue
        mesh=copy.deepcopy(b['mesh']);mesh['uv']=wood_uv(b);majors.append({'id':b['id'],'mesh':mesh})
        selected=[p for p in foliage if support_owner[p['source_support_id']]==b['id']]
        ids=sorted({p['source_support_id'] for p in selected})
        if not ids:continue
        points=[];radii=[]
        for i in range(0,len(mesh['vertices']),8):
            ring=mesh['vertices'][i:i+8]
            if len(ring)!=8:raise ValueError('Madera principal sin anillos de ocho lados')
            center=average(ring);points.append(center);radii.append(min(math.dist(v,center) for v in ring))
        if b['parent_id'] is None:
            # Redes de copa del tronco: nacimientos en su tramo alto.
            points=points[6:];radii=radii[6:];seed=derive_seed(base_seed,'branch-tree:trunk')
        else:
            if len(points)!=9:raise ValueError('Resolución primaria incompatible con el presupuesto')
            index=int(b['id'].split(':')[-1])-100;seed=(base_seed+1009*index)%2147483647
        targets=[{'id':identifier,'point':average([v for p in selected if p['source_support_id']==identifier for v in p['vertices']])} for identifier in ids]
        network=make_network(points,radii,targets,seed)
        parts.append({'id':b['id'],'seed':seed,'foliage':selected,'network':network,'axis_points':points,'axis_radii':radii})
    total_groups=len(support_owner)
    if sum(p['network']['targets'] for p in parts)!=total_groups or len(foliage)!=3*total_groups:
        raise ValueError('Asignación incompleta o duplicada de follaje')
    major_triangles=sum(sum(len(f)-2 for f in b['mesh']['polygons']) for b in majors)
    bound=major_triangles+18*total_groups+18*len(majors)
    if bound>6999:raise ValueError('Presupuesto de integración excedido')
    return {'version':VERSION,'majors':majors,'parts':parts,'foliage':foliage,
            'groups':total_groups,'triangle_upper_bound':bound,'major_triangles':major_triangles}
