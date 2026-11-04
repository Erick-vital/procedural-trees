"""Ejecución R4 acotada: fuentes → árbol completo, sin ensayos geométricos previos."""
from importlib.metadata import version
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from PIL import Image
from .contracts import ROOT
from .runner import BLENDER,write_json,timestamp
from .blueprints import canonical_hash
from .branch_tree import read_strict,resolve_tree,plan_tree
from .branch_visibility import prune_network
from .branch_tree_audit import raw_channels
from .branch_interior import proposals,apply_proposals
from .evaluation import validate_glb,validate_result
from .oak_crossed_evaluation import channels


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute_branch_tree(definition_path,request,output):
    definition=read_strict(definition_path);resolved=resolve_tree(definition,request)
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
    started=time.monotonic();deadline=started+definition['generation_seconds']
    manifest={'version':resolved['version'],'status':'running','started_at':timestamp(),'request':request,'resolved':resolved}
    write_json(out/'manifest.json',manifest);write_json(out/'definition.json',definition);write_json(out/'request.json',request)
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))

    def run(label,script,job):
        seconds=min(120,deadline-time.monotonic())
        if seconds<=0:raise TimeoutError('Árbol completo excedió 120 segundos')
        with (out/'logs'/(label+'.log')).open('w') as log:
            process=subprocess.Popen([os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1',
                '--python-exit-code','1','--python',str(ROOT/script),'--',str(job)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:code=process.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();raise TimeoutError(label+': tiempo excedido')
        if code:raise RuntimeError(label+': '+(out/'logs'/(label+'.log')).read_text()[-2500:])

    try:
        source=out/'source';source.mkdir();r=resolved['source_resolved']
        job={'spec':r['base_spec'],'spec_sha256':canonical_hash(r['base_spec']),'seeds':r['base_seeds'],'resolved_blueprint':r,
             'output':str(source),'render':False,'runner_python':sys.version,'jsonschema_version':version('jsonschema'),'f5_variant':'candidate'}
        write_json(source/'input.json',job);run('source','blender/f5_structure.py',source/'input.json')
        source_manifest=read_strict(source/'manifest.json');source_manifest['required_views']=[];write_json(source/'manifest.json',source_manifest)
        validate_result(source)
        reference=read_strict(source/'base-reference.json');rf3=read_strict(source/'reference/manifest.json')
        plan=plan_tree(reference,rf3,source_manifest,request['seeds']['base']);write_json(out/'tree-plan.json',plan)
        if plan['triangle_upper_bound']>resolved['triangle_upper_bound']:raise ValueError('Cota real supera la planificación')
        image=Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').getchannel('A');raw=image.tobytes()
        alpha_bare=out/'alpha-bare.bin';alpha_bare.write_bytes(raw)
        alpha_fol=out/'alpha-foliated.bin';alpha_fol.write_bytes(bytes(255 if a>=definition['foliated_alpha_cutoff'] else 0 for a in raw))
        bare_meshes=[b['mesh'] for b in plan['majors']];fol_meshes=list(bare_meshes);networks=[]

        def classify(edges,foliage,folder,alpha):
            folder.mkdir(parents=True,exist_ok=False)
            job={'output':str(folder),'network':{'edges':edges},'foliage':foliage,'alpha_path':str(alpha),'alpha_size':list(image.size)}
            write_json(folder/'input.json',job)
            script='blender/classify_tree_visibility.py' if alpha==alpha_fol else 'blender/classify_branch_visibility.py'
            run(str(folder.relative_to(out)).replace('/','-'),script,folder/'input.json')
            return read_strict(folder/'visibility.json')

        for i,part in enumerate(plan['parts']):
            folder=out/'networks'/f'{i:02}';folder.mkdir(parents=True)
            original=part['network']
            bare_v=classify(original['edges'],part['foliage'],folder/'bare-visibility',alpha_bare)
            bare,bare_selection=prune_network(original,bare_v['protected_exposed_ids'])
            fol_v=classify(bare['edges'],part['foliage'],folder/'foliated-visibility',alpha_fol)
            protected=set(fol_v['protected_exposed_ids']);fol,fol_selection=prune_network(bare,protected)
            rounds=[]
            for j in range(3):
                options=proposals(fol,protected)
                if not options:break
                candidates=[{**e,'id':option['removed']+'>'+e['id']} for option in options for e in option['replacements']]
                visibility=classify(candidates,part['foliage'],folder/f'collapse-{j}',alpha_fol)
                hidden={e['id'] for e in candidates}-set(visibility['protected_exposed_ids'])
                fol,audit=apply_proposals(fol,options,hidden);rounds.append(audit)
                if not audit['accepted']:break
            old={e['id']:e for e in original['edges']};current={e['id']:e for e in fol['edges']}
            if not all(identifier in current and current[identifier]['mesh']==old[identifier]['mesh'] for identifier in protected):
                raise ValueError('Malla expuesta modificada')
            record={'id':part['id'],'seed':part['seed'],'bare':bare,'foliated':fol,'bare_selection':bare_selection,
                    'foliated_selection':fol_selection,'collapse_rounds':rounds}
            write_json(folder/'network.json',record);networks.append(record)
            bare_meshes.extend(e['mesh'] for e in bare['edges']);fol_meshes.extend(e['mesh'] for e in fol['edges'])
            print('Red '+part['id']+': R2 '+str(bare['triangles'])+' / R3 '+str(fol['triangles']),flush=True)
        variants={'full':{'wood':bare_meshes,'foliage':plan['foliage']},'simple':{'wood':fol_meshes,'foliage':plan['foliage']},
                  'bare':{'wood':bare_meshes,'foliage':[]},'foliage-before':{'wood':[],'foliage':plan['foliage']},'foliage-after':{'wood':[],'foliage':plan['foliage']}}
        job={'output':str(out),'variants':variants,'majors':plan['majors'],'root_networks':[{'id':n['id'],'edges':n['bare']['edges']} for n in networks]}
        write_json(out/'input.json',job);run('export','blender/export_branch_tree.py',out/'input.json')
        exports=read_strict(out/'exports.json');checks={};data={}
        for name,item in exports['variants'].items():
            m=item['metrics'];inspection=validate_glb(out/name/'tree.glb',{'parameters':{'height_m':m['height_m']}},triangle_limit=6999)
            checks[name+'-export']=inspection['triangles']==m['triangles'] and len(inspection['materials'])<=2
            checks[name+'-prebudget']=m['triangles']<=resolved['triangle_upper_bound']
            data[name]=channels(out/name/'tree.glb')
        prior=channels(source/'tree.glb')
        raw_source=raw_channels(source/'tree.glb');raw_simple=raw_channels(out/'simple/tree.glb')
        checks['foliage_all_raw_attributes_exact']=raw_source['Painted_Foliage']==raw_simple['Painted_Foliage']
        nominal=validate_glb(out/'simple/tree.glb',source_manifest['spec'],triangle_limit=6999,height_materials={'Painted_Bark'})
        checks['nominal_wood_height']=True
        checks['nominal_wood_height_bare']=bool(validate_glb(out/'bare/tree.glb',source_manifest['spec'],triangle_limit=6999))
        checks['frozen_foliage_exact']=sorted(prior[1]['Painted_Foliage'])==sorted(data['simple'][1]['Painted_Foliage'])==sorted(data['full'][1]['Painted_Foliage'])
        checks['foliage_normals_exact']=sorted(prior[2]['Painted_Foliage'])==sorted(data['simple'][2]['Painted_Foliage'])
        checks['bare_wood_matches_full']=sorted(data['bare'][1]['Painted_Bark'])==sorted(data['full'][1]['Painted_Bark'])
        checks['textures_exact']=data['simple'][3]==data['full'][3]==prior[3]
        checks['foliage_controls_glb_exact']=sha(out/'foliage-before/tree.glb')==sha(out/'foliage-after/tree.glb')
        checks['roots_inside_main_wood']=read_strict(out/'roots-audit.json')['passed']
        manifest.update(status='completed' if all(checks.values()) else 'failed',checks=checks,variants=exports['variants'],
            groups=plan['groups'],networks=[{'id':n['id'],'seed':n['seed'],'bare_triangles':n['bare']['triangles'],'foliated_triangles':n['foliated']['triangles'],
                'bare_edges':len(n['bare']['edges']),'foliated_edges':len(n['foliated']['edges'])} for n in networks],
            source_glb_sha256=sha(source/'tree.glb'),source_metrics=source_manifest['metrics'],source_spec=source_manifest['spec'],
            blueprint_sha256=sha(ROOT/definition['source_blueprint']),definition_sha256=sha(definition_path),
            sources_sha256={str(p.relative_to(ROOT)):sha(p) for folder in ('src/treegen','blender') for p in (ROOT/folder).glob('*.py')},
            duration_seconds=time.monotonic()-started,finished_at=timestamp(),artistic_acceptance='pending_for_complete_trees',
            modes={'without_foliage':'bare/tree.glb','with_foliage':'simple/tree.glb'},blender=exports['blender'],blender_build=exports['build'])
        write_json(out/'manifest.json',manifest)
        if not all(checks.values()):raise ValueError('Auditoría de árbol fallida: '+str(checks))
        return {'status':'completed','version':manifest['version'],'output':str(out),'profile':request['profile'],
                'triangles':{name:exports['variants'][name]['metrics']['triangles'] for name in ('bare','simple')},'duration_seconds':manifest['duration_seconds']}
    except Exception as exc:
        manifest.update(status='failed',error={'type':type(exc).__name__,'message':str(exc)},duration_seconds=time.monotonic()-started,finished_at=timestamp())
        write_json(out/'manifest.json',manifest);raise
