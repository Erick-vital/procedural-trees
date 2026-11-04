"""Blueprint3.0.0: resolver y ejecutar OF11 sin depender de resultados previos."""
import copy
import hashlib
import json
from pathlib import Path
from .contracts import ROOT
from .blueprints import canonical_hash
from .oak_crossed_production import validate_resources,PATHS


def check_parameters(parameters,blueprint):
    validate_resources(blueprint['resources'])
    limits=blueprint['limits']
    if limits['triangles']!=6999 or limits['materials']!=2 or not 0<limits['generation_seconds']<=120:
        raise ValueError('El roble central requiere techo6999, dos materiales y120 s')
    # La topología base y los ensayos están acotados por O5/OF11. La generación
    # rechaza antes de mallar las semillas que no completan el perfil o su cupo.
    return {'triangles_max':6999,'materials_max':2,'groups_max':216,
            'added_wood_triangles_max':600,'central_groups':24,
            'region_candidates_max':216*9*12,'fan_candidates_max':216*2*3*3*3,
            'central_candidates_max':24*12}


def resolve(blueprint,instance,name,profile,defaults,parameters,budget):
    seed=instance['seeds']
    spec={'version':'oak-foliage-canopy-0.11.0','preset':parameters['base']['preset'],
          'seed':seed['base'],'layout_seed':seed['canopy'],'paint_seed':seed['paint'],**parameters['canopy']}
    from .oak_foliage_central_contract import validate_canopy
    validate_canopy(spec)
    result={'resolved_version':'1.7','blueprint_id':blueprint['id'],'blueprint_version':blueprint['version'],
            'blueprint_sha256':canonical_hash(blueprint),'blueprint_definition':copy.deepcopy(blueprint),
            'instance_request':copy.deepcopy(instance),'profile':name,'parameters':copy.deepcopy(parameters),
            'profile_validation_claim':copy.deepcopy(profile['validation']),'parameters_differ_from_profile':parameters!=defaults,
            'base_spec':{'schema_version':'oak-central-1.0','algorithm':'oak-central','algorithm_version':'0.1.0',
                         'seed':seed['base'],'parameters':copy.deepcopy(parameters['base'])},
            'base_seeds':{'structure':seed['base'],'foliage':seed['canopy']},'canopy_spec':spec,
            'paint_seed':seed['paint'],'resources':copy.deepcopy(blueprint['resources']),
            'appearance':copy.deepcopy(blueprint['appearance']),'limits':copy.deepcopy(blueprint['limits']),
            'budget_upper_bound':budget}
    result['resolved_sha256']=canonical_hash(result)
    return result


def prepare(resolved):
    """Geometría derivada en Python anfitrión: Blender no necesita Pillow."""
    from PIL import Image
    from .oak_crown_contract import load_growth_preset
    from .oak_growth_v5 import generate
    from .oak_foliage_central import build
    from .oak_foliage_cards import prepare_templates
    from .oak_foliage_top import prepare_opaque_samples
    from .oak_growth_mesh import tube
    frozen=dict(resolved)
    if frozen.pop('resolved_sha256')!=canonical_hash(frozen):raise ValueError('Resolución central alterada')
    templates=validate_resources(resolved['resources'])['templates']
    image=Image.open(ROOT/PATHS['foliage']).convert('RGBA')
    prepared=prepare_opaque_samples(prepare_templates(templates,image),image)
    spec=resolved['canopy_spec'];structure=generate(load_growth_preset(ROOT/spec['preset']),spec['seed'])
    result=build(structure,spec,templates,prepared=prepared)
    if result['ledger']['tree_projected_triangles']>resolved['limits']['triangles']:
        raise ValueError('Presupuesto central excedido antes de Blender')
    return {'version':'oak-central-prepared-1.0','resolved_sha256':resolved['resolved_sha256'],
            'wood':[tube(b) for b in result['wood']], 'foliage':result['foliage'],
            'structure':result['structure'],'groups':result['groups'],'gap_fans':result['gap_fans'],
            'ledger':result['ledger'],'central_protection':result['central_protection'],
            'central_changes':result['central_changes'],'central_extension':result['central_extension']}


def inspect_export(directory,manifest,resolved):
    from PIL import Image
    from .evaluation import validate_glb
    from .oak_crossed_evaluation import channels
    from .oak_foliage_evaluation import audit_contacts
    from .oak_foliage_gap_evaluation import audit_fans
    from .oak_foliage_central import minimum_radius_below
    directory=Path(directory)
    data=json.loads((directory/'prepared-canopy.json').read_text())
    if canonical_hash(data)!=manifest['prepared_geometry_sha256'] or data['resolved_sha256']!=resolved['resolved_sha256']:
        raise ValueError('Geometría preparada alterada o de otro blueprint')
    validate_resources(resolved['resources'])
    report=validate_glb(directory/'tree.glb',resolved['base_spec'],triangle_limit=6999,height_materials={'Painted_Bark'})
    doc,rows,_,images=channels(directory/'tree.glb')
    image=Image.open(ROOT/PATHS['foliage']).convert('RGBA')
    contacts=audit_contacts(directory/'tree.glb',data['groups'],image)
    fans=audit_fans(directory/'tree.glb',data['gap_fans'],image)
    triangles=[{'vertices':[(v[0],-v[2],v[1]) for v in tri],'polygons':[(0,1,2)]} for tri in rows['Painted_Foliage']]
    lower=minimum_radius_below(triangles,data['central_protection']['maximum_protected_z_m'])
    leaf=next(m for m in doc['materials'] if m['name']=='Painted_Foliage')
    checks={'triangles':report['triangles']==data['ledger']['tree_projected_triangles']<=6999,
            'two-materials':len(doc['materials'])==2 and set(rows)=={'Painted_Bark','Painted_Foliage'},
            'textures':set(images)=={resolved['resources'][k]['sha256'] for k in ('bark','foliage')},
            'alpha':leaf.get('alphaMode')=='MASK' and leaf.get('alphaCutoff',.5)==.5,
            'double-sided':all(m.get('doubleSided') for m in doc['materials']),
            'groups':len(data['groups'])==216,'central-groups':len(data['central_changes'])==24,
            'contacts':contacts['passed'],'fan-contacts':fans['passed'],
            'lower-core':lower>=data['central_protection']['radius_m']-1e-5}
    if not all(checks.values()):raise ValueError('GLB central inválido: '+str([k for k,v in checks.items() if not v]))
    report.update(checks=checks,group_count=216,lower_core_radius_m=lower,
                  maximum_contact_error_m=contacts['maximum_error_m'])
    return report
