#!/usr/bin/env python3
"""Pino: cuatro semillas, controles, repetición, contactos GLB y vistas Godot."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.runner import execute_blueprint, BLENDER
from treegen.blueprints import canonical_hash
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def read(path):return json.loads(Path(path).read_text())


def write(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--visual',action='store_true')
    parser.add_argument('--matrix',type=Path,default=ROOT/'configs/verification/pine-v1.json')
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'logs').mkdir()
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),
             XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    matrix=read(args.matrix);write(out/'matrix.json',matrix)
    sources=[p for folder in ('src/treegen','blender','schemas','blueprints','godot','presets/blueprints/pino','presets/blueprints/pino-v2')
             for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.json','.gd')]
    sources += [Path(__file__),ROOT/matrix['objective'],args.matrix.resolve()]
    before={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)}
    report={'passed':False,'version':matrix['version'],'matrix_sha256':canonical_hash(matrix),
            'sources_sha256':before,'cases':{},'checks':{},'visual_requested':args.visual}
    def run(name,command):
        with (out/'logs'/(name+'.log')).open('w') as log:
            process=subprocess.Popen(list(map(str,command)),cwd=ROOT,env=env,stdout=log,
                                     stderr=subprocess.STDOUT,start_new_session=True)
            try:code=process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();raise TimeoutError(name)
        content=(out/'logs'/(name+'.log')).read_text()
        if code or 'SCRIPT ERROR:' in content or '\nERROR:' in content:raise RuntimeError(name+': '+content[-2500:])
        print(name+': OK',flush=True)
    def blender(name,script,*arguments):
        run(name,[os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1',
                  '--python-exit-code','1','--python',ROOT/script,'--',*arguments])
    manifests={}
    try:
        run('tests',[sys.executable,'-m','unittest','discover','-s','tests','-v'])
        cases=copy.deepcopy(matrix['cases'])
        if 'comparison' in matrix:
            for row in matrix['cases']:
                request=copy.deepcopy(row['instance']);request['blueprint_version']='1.0.0'
                cases.append({'id':'before-'+row['id'],'instance':request,'blueprint':matrix['comparison']['blueprint']})
        cases.append({'id':'pilot-repeat','instance':copy.deepcopy(cases[0]['instance'])})
        for name,change in [('canopy-seed',{'seeds':{'base':5100,'canopy':101}}),
                            ('needle-size',{'overrides':{'canopy':{'needle_length_m':.4,'needle_width_m':.06}}})]:
            request=copy.deepcopy(cases[0]['instance']);request.update(change)
            cases.append({'id':name,'instance':request})
        cases += [{'id':'oak-reference','blueprint':'blueprints/roble_copa_ancha/1.0.0.json',
                   'instance':read(ROOT/'presets/blueprints/roble-copa-ancha-viejo-09.json')},
                  {'id':'columnar-reference','blueprint':'blueprints/arbol_copa_columnar/1.0.0.json',
                   'instance':read(ROOT/'configs/verification/b4-v1.json')['cases'][0]['instance']}]
        for row in cases:
            name=row['id']
            m=execute_blueprint(ROOT/row.get('blueprint',matrix['blueprint']),row['instance'],out/name,render=False)
            manifests[name]=m
            report['cases'][name]={k:m[k] for k in ('glb_sha256','metrics','duration_seconds','glb_bytes','wood_sha256')}
            report['cases'][name]['resolved_sha256']=m['resolved_blueprint']['resolved_sha256']
            print(name+': generado',flush=True)
            write(out/'verification.json',report)
        checks=report['checks'];pilot=manifests['pilot']
        checks['pilot-repeat-identical']=pilot['glb_sha256']==manifests['pilot-repeat']['glb_sha256']
        for row in matrix['cases']:
            m=manifests[row['id']]
            checks[row['id']+'-same-parameters']=m['resolved_blueprint']['parameters']==pilot['resolved_blueprint']['parameters']
            checks[row['id']+'-height-budget']=m['metrics']['height_m']==12 and m['metrics']['triangles']<=12500
            checks[row['id']+'-source-only']=m['external_geometry_inputs']==[]
        checks['four-distinct-geometries']=len({manifests[r['id']]['glb_sha256'] for r in matrix['cases']})==4
        if 'comparison' in matrix:
            from treegen.pine_structure_v2 import diagnostics
            previous=read(ROOT/matrix['comparison']['evidence'])
            report['structure_comparison']={}
            for row in matrix['cases']:
                name=row['id'];old=manifests['before-'+name];new=manifests[name]
                old_ref=read(out/('before-'+name)/'base-reference.json');new_ref=read(out/name/'base-reference.json')
                a,b=diagnostics(old_ref['branches']),diagnostics(new_ref['branches'])
                report['structure_comparison'][name]={'before':a,'after':b}
                checks[name+'-before-identical-v1']=old['glb_sha256']==previous['cases'][name]['glb_sha256']
                checks[name+'-same-counts']=all(old[k]==new[k] for k in ('branch_count','leaf_count')) and old['metrics']['triangles']==new['metrics']['triangles']
                checks[name+'-same-inputs']=old['resolved_blueprint']['parameters']==new['resolved_blueprint']['parameters'] and old['canopy_spec']==new['canopy_spec']
                checks[name+'-staggered-roots']=min(b['root_height_spread_by_level_m'])>.7
                checks[name+'-mixed-slopes']=b['descending_primaries']>0 and b['ascending_primaries']>0
        for name in ('canopy-seed','needle-size'):
            checks[name+'-preserves-wood']=manifests[name]['export_validation']['channel_sha256']['Pine_Bark']==pilot['export_validation']['channel_sha256']['Pine_Bark']
            checks[name+'-changes-foliage']=manifests[name]['export_validation']['channel_sha256']['Pine_Needles']!=pilot['export_validation']['channel_sha256']['Pine_Needles']
        lock=read(ROOT/'docs/evidence/blueprints/b0/reference-lock.json')
        checks['oak-identical-b0']=manifests['oak-reference']['glb_sha256']==lock['files_sha256'][lock['pilot_directory']+'/tree.glb']
        b4=read(ROOT/'docs/evidence/blueprints/b4/verification.json')
        checks['columnar-identical-b4']=manifests['columnar-reference']['glb_sha256']==b4['cases']['pilot']['glb_sha256']
        write(out/'contact-input.json',[str(out/r['id']) for r in cases if manifests[r['id']]['spec']['algorithm']=='pine-whorls'])
        blender('export-contacts','blender/verify_pine_contacts.py',out/'contact-input.json',out/'export-contacts.json')
        report['contacts']=read(out/'export-contacts.json');checks['export-contacts']=report['contacts']['passed']
        visible=[r['id'] for r in matrix['cases']]
        if 'comparison' in matrix:visible += ['before-'+r['id'] for r in matrix['cases']]
        write(out/'wood-input.json',[{'source':str(out/n),'output':str(out/'inspection'/(n+'-wood'))} for n in visible])
        blender('wood-inspections','blender/inspect_blueprint_controls.py',out/'wood-input.json')
        # Un mismo encuadre físico para todos los pinos y sus maderas.
        rig=copy.deepcopy(manifests.get('before-pilot',pilot)['cameras'])
        for view in rig:
            rig[view]['ortho_scale']=15.6 if view not in ('near','medium','far') else {'near':24,'medium':48,'far':120}[view]
        report['camera_protocol']={'shared_by_all_assets':True,'cameras':rig,'light_rotation_deg':[-35,-25,0],
                                   'light_energy':1.2,'ambient_energy':.5}
        project=out/'godot';project.mkdir()
        for filename in ('project.godot','verify_oak.gd','verify_foliage_molds.gd'):
            shutil.copy2(ROOT/'godot'/filename,project/filename)
        entries=[]
        for name in visible+[n+'-wood' for n in visible]:
            folder=out/'inspection'/name;folder.mkdir(parents=True,exist_ok=True)
            if not name.endswith('-wood'):
                for filename in ('tree.glb','manifest.json'):shutil.copy2(out/name/filename,folder/filename)
            write(folder/'cameras.json',rig)
            shutil.copy2(folder/'tree.glb',project/(name+'.glb'))
            entries.append({'id':name,'folder':str(folder),'capture':args.visual,'resource':'res://'+name+'.glb'})
        godot=os.environ.get('GODOT_BIN',GODOT)
        run('godot-import',[godot,'--headless','--path',project,'--editor','--import'])
        report['godot']=[]
        for index in range(0,len(entries),2):
            config=out/f'godot-input-{index}.json';result=out/f'godot-report-{index}.json'
            write(config,entries[index:index+2])
            command=[godot,'--path',project,'--script','res://verify_foliage_molds.gd','--',
                     '--input='+str(config),'--report='+str(result)]
            run('godot-check-'+str(index),command[:1]+['--headless']+command[1:])
            if args.visual:run('godot-visual-'+str(index),command+['--visual'])
            data=read(result);checks['godot-'+str(index)]=data['passed'];report['godot'].append(data)
        if args.visual:
            current=[r['id'] for r in matrix['cases']]
            for filename,suffix,views in [('controls.jpg','',('front','side','perspective','top')),
                                          ('wood.jpg','-wood',('front','side','perspective')),
                                          ('distances.jpg','',('near','medium','far'))]:
                sheet(out,out/filename,4,[[(f'inspection/{n}{suffix}/godot-{v}.png',n+suffix+' | '+v)
                                          for n in current] for v in views])
            if 'comparison' in matrix:
                for filename,suffix in [('comparison.jpg',''),('comparison-wood.jpg','-wood')]:
                    sheet(out,out/filename,4,[[(f'inspection/{n}{suffix}/godot-{v}.png',label+' | '+v)
                          for n,label in [('before-'+a,'1.0.0 '+a),(a,'1.1.0 '+a),('before-'+b,'1.0.0 '+b),(b,'1.1.0 '+b)]]
                          for a,b in [('pilot','control-01'),('control-02','control-03')] for v in ('front','side','perspective')])
            rows=''.join('<tr><th>'+e['id']+'</th>'+''.join(f'<td><a href="inspection/{e["id"]}/godot-{v}.png"><img width="240" src="inspection/{e["id"]}/godot-{v}.png"></a></td>' for v in rig)+'</tr>' for e in entries)
            version=pilot['resolved_blueprint']['blueprint_version']
            navigation=('<p><a href="comparison.jpg">Comparación 1.0.0 / 1.1.0</a> · <a href="comparison-wood.jpg">Comparación de madera</a></p>' if 'comparison' in matrix else '')
            (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Pino '+version+'</title><style>body{font:16px sans-serif;background:#e9edf1}img{display:block}</style><h1>Pino cónico '+version+' · cuatro semillas</h1><p>pilot y control-01/02/03: versión a revisar. before-: versión 1.0.0 anterior. -wood: madera sin follaje. Cámaras y luz comunes; aceptación artística pendiente.</p>'+navigation+'<a href="verification.json">Verificación</a><table>'+rows+'</table>')
            report['real_captures']=sum(len(list((out/'inspection'/e['id']).glob('godot-*.png'))) for e in entries)
            checks['all-real-captures']=report['real_captures']==len(entries)*9
        checks['sources-unchanged']=before=={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)}
        report['passed']=all(checks.values())
    finally:write(out/'verification.json',report)
    print('Pino: passed='+str(report['passed']),flush=True)
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
