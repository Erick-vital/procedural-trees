"""Contrato1.8: resolución, preparación y auditoría del roble joven completo."""
import copy
import hashlib
import json
from pathlib import Path
from .contracts import ROOT
from .blueprints import canonical_hash
from .oak_crossed_production import validate_resources,PATHS

def canopy_module(blueprint):
    version=blueprint['components']['distribution'].split('@')[1]
    expected={'base':'oak-growth-young@0.5.0','distribution':'oak-young-chains@'+version,'representation':'oak-young-crossed@'+version}
    if version not in ('0.1.0','0.2.0') or blueprint['components']!=expected:raise ValueError('Componentes jóvenes incompatibles')
    if version=='0.2.0':
        from . import oak_young_volume
        return oak_young_volume
    from . import oak_young_canopy
    return oak_young_canopy


def check_parameters(parameters,blueprint):
    validate_resources(blueprint['resources'])
    module=canopy_module(blueprint)
    module.validate_canopy({'version':module.VERSION,'preset':parameters['base']['preset'],'seed':0,'layout_seed':0,'paint_seed':0,**parameters['canopy']})
    limits=blueprint['limits']
    if parameters['base']['height_m']!=5 or limits['triangles']!=6999 or limits['materials']!=2 or not 0<limits['generation_seconds']<=120:
        raise ValueError('Joven requiere5 m,6999 tris,dos materiales y máximo120 s')
    if set(blueprint['profiles'])!={'joven'} or blueprint['default_profile']!='joven':raise ValueError('Solo perfil joven fijo')
    groups=parameters['canopy']['tree_groups']
    return {'wood_triangles_max':5415,'foliage_triangles_max':6*groups,'triangles_max':5415+6*groups,
            'materials_max':2,'groups_max':groups,'candidates_per_axis_max':32,'groups_per_axis_max':12}


def resolve(blueprint,instance,name,profile,defaults,parameters,budget):
    seed=instance['seeds']
    module=canopy_module(blueprint)
    canopy={'version':module.VERSION,'preset':parameters['base']['preset'],'seed':seed['base'],
            'layout_seed':seed['canopy'],'paint_seed':seed['paint'],**parameters['canopy']}
    module.validate_canopy(canopy)
    r={'resolved_version':'1.8','blueprint_id':blueprint['id'],'blueprint_version':blueprint['version'],
       'blueprint_sha256':canonical_hash(blueprint),'blueprint_definition':copy.deepcopy(blueprint),
       'instance_request':copy.deepcopy(instance),'profile':name,'parameters':copy.deepcopy(parameters),
       'profile_validation_claim':copy.deepcopy(profile['validation']),'parameters_differ_from_profile':parameters!=defaults,
       'base_spec':{'schema_version':'oak-young-1.0','algorithm':'oak-young','algorithm_version':'0.1.0',
                    'seed':seed['base'],'parameters':copy.deepcopy(parameters['base'])},
       'base_seeds':{'structure':seed['base'],'foliage':seed['canopy']},'canopy_spec':canopy,
       'paint_seed':seed['paint'],'resources':copy.deepcopy(blueprint['resources']),
       'appearance':copy.deepcopy(blueprint['appearance']),'limits':copy.deepcopy(blueprint['limits']),'budget_upper_bound':budget}
    r['resolved_sha256']=canonical_hash(r)
    return r


def prepare(resolved):
    from PIL import Image
    from .oak_crown_contract import load_growth_preset
    from .oak_growth_v5 import generate
    from .oak_foliage_cards import prepare_templates
    from .oak_growth_mesh import tube
    frozen=dict(resolved)
    if frozen.pop('resolved_sha256')!=canonical_hash(frozen):raise ValueError('Resolución joven alterada')
    templates=validate_resources(resolved['resources'])['templates']
    prepared=prepare_templates(templates,Image.open(ROOT/PATHS['foliage']).convert('RGBA'))
    spec=resolved['canopy_spec'];preset=ROOT/spec['preset']
    structure=generate(load_growth_preset(preset),spec['seed'])
    result=canopy_module(resolved['blueprint_definition']).build(structure,spec,templates,prepared=prepared)
    return {'version':'oak-young-prepared-1.0','resolved_sha256':resolved['resolved_sha256'],
            'wood':[tube(b) for b in result['wood']],'foliage':result['foliage'],'groups':result['groups'],
            'structure':result['structure'],'ledger':result['ledger'],'masses_by_primary':result['masses_by_primary'],
            'diagnostics':result['diagnostics'],'growth_preset_sha256':hashlib.sha256(preset.read_bytes()).hexdigest()}


def inspect_export(directory,manifest,resolved):
    from PIL import Image
    from .evaluation import validate_glb
    from .oak_crossed_evaluation import channels,validate_wood_faces
    from .oak_foliage_evaluation import audit_contacts
    directory=Path(directory);data=json.loads((directory/'prepared-canopy.json').read_text())
    if canonical_hash(data)!=manifest['prepared_geometry_sha256'] or data['resolved_sha256']!=resolved['resolved_sha256']:
        raise ValueError('Preparación joven alterada')
    if data['growth_preset_sha256']!=hashlib.sha256((ROOT/resolved['canopy_spec']['preset']).read_bytes()).hexdigest():raise ValueError('Preset joven alterado')
    validate_resources(resolved['resources'])
    report=validate_glb(directory/'tree.glb',resolved['base_spec'],triangle_limit=6999,height_materials={'Painted_Bark'})
    doc,rows,_,images=channels(directory/'tree.glb')
    validate_wood_faces(rows['Painted_Bark'],[(m,0,m['uv']) for m in data['wood']])
    validate_wood_faces(rows['Painted_Foliage'],[(m,1,m['uv']) for m in data['foliage']])
    contacts=audit_contacts(directory/'tree.glb',data['groups'],Image.open(ROOT/PATHS['foliage']).convert('RGBA'))
    checks={'triangles':report['triangles']==data['ledger']['tree_projected_triangles']<=resolved['budget_upper_bound']['triangles_max'],
            'two-materials':len(doc['materials'])==2 and set(rows)=={'Painted_Bark','Painted_Foliage'},
            'textures':len(images)==2 and set(images)=={resolved['resources'][k]['sha256'] for k in ('bark','foliage')},
            'groups':len(data['groups'])==resolved['canopy_spec']['tree_groups'],'contacts':contacts['passed'],
            'joins':manifest['wood_joins']['passed'],
            'wood-faces-and-uv':True,'foliage-faces-and-uv':True}
    for mat in doc['materials']:
        leaf=mat['name']=='Painted_Foliage';pbr=mat['pbrMetallicRoughness']
        checks[mat['name']+'-settings']=(mat.get('doubleSided') is True and mat.get('alphaMode','OPAQUE')==('MASK' if leaf else 'OPAQUE') and
            (not leaf or mat.get('alphaCutoff',.5)==.5) and abs(pbr.get('roughnessFactor',1)-.95)<1e-6 and pbr.get('metallicFactor',1)==0 and pbr.get('baseColorFactor',[1,1,1,1])==[1,1,1,1])
    if not all(checks.values()):raise ValueError('GLB joven inválido: '+str([k for k,v in checks.items() if not v]))
    report.update(checks=checks,group_count=len(data['groups']),maximum_contact_error_m=contacts['maximum_error_m'])
    return report
