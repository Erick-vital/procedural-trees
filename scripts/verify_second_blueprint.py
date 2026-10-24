#!/usr/bin/env python3
"""B4: dos recetas, arquitectura distinta, controles fijos y componentes compartidos."""
import argparse
import copy
import html
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from treegen.blueprints import load_blueprint, canonical_hash
from treegen.evaluation import validate_result
from treegen.runner import execute_blueprint, BLENDER
from verify_blueprint_reference import read, write, sha
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'logs').mkdir()
    matrix = read(ROOT/'configs/verification/b4-v1.json')
    write(out/'frozen-matrix.json',matrix)
    sources = [p for folder in ('src','blender','schemas','blueprints') for p in (ROOT/folder).rglob('*')
               if p.is_file() and p.suffix in ('.py','.json')]
    before = {str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)}
    report = {'phase':'B4','passed':False,'matrix_sha256':canonical_hash(matrix),
        'objective_sha256':sha(ROOT/matrix['objective']), 'concept_sha256':sha(ROOT/matrix['concept']),
        'verifier_sha256':sha(Path(__file__)), 'sources_before':before,
        'visual_requested':args.visual,'cases':{},'checks':{}}
    manifests = {}
    env = dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),
               XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))

    def run(name,command,timeout=180):
        with (out/'logs'/(name+'.log')).open('w') as log:
            process = subprocess.Popen(list(map(str,command)),cwd=ROOT,env=env,stdout=log,
                stderr=subprocess.STDOUT,start_new_session=True)
            try:code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();raise TimeoutError(name)
        content = (out/'logs'/(name+'.log')).read_text()
        if code or 'SCRIPT ERROR:' in content or '\nERROR:' in content:
            raise RuntimeError(name+': '+content[-2000:])
        print(name+': OK',flush=True)

    try:
        run('tests',[sys.executable,'-m','unittest','discover','-s','tests','-v'])
        for row in matrix['cases']:
            name = row['id'];started = time.monotonic()
            try:
                m = execute_blueprint(ROOT/row['blueprint'],row['instance'],out/name,render=False)
                manifests[name] = m
                ref = read(out/name/'base-reference.json')
                low,high = m['metrics']['bounds_blender']
                wood = ref['wood_mesh']['vertices']
                spans = [max(p[k] for p in wood)-min(p[k] for p in wood) for k in range(3)]
                report['cases'][name] = {'status':'generated','kind':row['kind'],
                    'blueprint_id':m['resolved_blueprint']['blueprint_id'],
                    'metrics':m['metrics'],'width_height_ratio':[(high[k]-low[k])/(high[2]-low[2]) for k in (0,1)],
                    'wood_width_height_ratio':[spans[k]/spans[2] for k in (0,1)],
                    'supports':m['support_count'],'leaves':m['leaf_count'],
                    'sampling':m['sampling'],'selection':m['selection'],
                    'contacts':m['contacts'],'surface_projection':m['surface_projection'],
                    'glb_sha256':m['glb_sha256'],'resolved_sha256':m['resolved_blueprint']['resolved_sha256'],
                    'wood_sha256':m['wood_sha256'],'glb_bytes':m['glb_bytes'],
                    'duration_seconds':round(time.monotonic()-started,3)}
            except Exception as exc:
                report['cases'][name] = {'status':'failed','kind':row['kind'],'error':str(exc)}
            print(name+': '+report['cases'][name]['status'],flush=True)
            write(out/'verification.json',report)
        checks = report['checks']
        primary = ['pilot','control-01','control-02','control-03']
        for name in primary:
            if name in manifests:
                m = manifests[name]
                checks[name+'-columnar-full'] = max(report['cases'][name]['width_height_ratio']) <= matrix['architecture_diagnostics']['max_width_height_ratio']
                checks[name+'-columnar-wood'] = max(report['cases'][name]['wood_width_height_ratio']) <= matrix['architecture_diagnostics']['max_width_height_ratio']
                checks[name+'-same-parameters'] = m['resolved_blueprint']['parameters'] == manifests['pilot']['resolved_blueprint']['parameters']
                checks[name+'-repeat'] = name+'-repeat' in manifests and m['glb_sha256'] == manifests[name+'-repeat']['glb_sha256']
                checks[name+'-source-only-inputs'] = m['external_geometry_inputs'] == []
        first_lock = read(ROOT/'docs/evidence/blueprints/b0/reference-lock.json')
        checks['first-reference-matches-b0'] = 'first-reference' in manifests and manifests['first-reference']['glb_sha256'] == first_lock['files_sha256'][first_lock['pilot_directory']+'/tree.glb']
        if 'pilot' in manifests and 'wide-same-seed' in manifests:
            a,b = manifests['pilot']['resolved_blueprint'],manifests['wide-same-seed']['resolved_blueprint']
            checks['same-seed-comparison'] = a['instance_request']['seeds'] == b['instance_request']['seeds']
            checks['components-identical'] = a['blueprint_definition']['components'] == b['blueprint_definition']['components']
            checks['palette-identical'] = a['appearance'] == b['appearance']
            checks['architecture-parameters-differ'] = a['parameters']['base'] != b['parameters']['base']
            report['same_seed_diagnostics'] = {n:report['cases'][n]['width_height_ratio'] for n in ('pilot','wide-same-seed')}
        write(out/'export-contact-input.json',[str(out/name) for name in manifests])
        run('export-contacts',[os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1',
            '--python-exit-code','1','--python',ROOT/'blender/verify_export_contacts.py','--',out/'export-contact-input.json',out/'export-contacts.json'])
        report['export_contacts'] = read(out/'export-contacts.json')
        checks['all-export-contacts'] = report['export_contacts']['passed']
        visible = [r['id'] for r in matrix['cases'] if r['kind'] != 'repeat' and r['id'] in manifests]
        write(out/'wood-input.json',[{'source':str(out/name),'output':str(out/'inspection'/(name+'-wood'))} for name in visible])
        run('wood-inspections',[os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1',
            '--python-exit-code','1','--python',ROOT/'blender/inspect_blueprint_controls.py','--',out/'wood-input.json'])
        cameras = read(ROOT/'configs/inspection/rf3-v1.json')['cameras']
        low = [min(m['metrics']['bounds_blender'][0][k] for m in manifests.values()) for k in range(3)]
        high = [max(m['metrics']['bounds_blender'][1][k] for m in manifests.values()) for k in range(3)]
        center = [(a+b)/2 for a,b in zip(low,high)];fit = math.dist(low,high)/.88
        rig = {}
        for view in ('front','side','top','below','perspective','reverse','near','medium','far'):
            camera = copy.deepcopy(cameras[view])
            camera['location'] = [center[k]+80*camera['basis_columns'][2][k] for k in range(3)]
            camera['ortho_scale'] = fit if view not in ('near','medium','far') else max(fit,24)*{'near':1,'medium':2,'far':5}[view]
            camera.pop('target_height_fraction',None)
            rig[view] = camera
        report['camera_protocol'] = {'shared_by_all_assets':True,'cameras':rig,'global_bounds':[low,high],
            'lighting':'Godot RF3/B2: rotación[-35,-25,0], energía1.2, ambiente.5; misma paleta.'}
        project = out/'godot';project.mkdir()
        for filename in ('project.godot','verify_oak.gd','verify_foliage_molds.gd'):
            shutil.copy2(ROOT/'godot'/filename,project/filename)
        entries = []
        for name in visible + [n+'-wood' for n in visible]:
            folder = out/'inspection'/name;folder.mkdir(parents=True,exist_ok=True)
            if not name.endswith('-wood'):
                for filename in ('tree.glb','manifest.json'):shutil.copy2(out/name/filename,folder/filename)
            write(folder/'cameras.json',rig)
            shutil.copy2(folder/'tree.glb',project/(name+'.glb'))
            entries.append({'id':name,'folder':str(folder),'capture':args.visual,'resource':'res://'+name+'.glb'})
        run('godot-import',[os.environ.get('GODOT_BIN',GODOT),'--headless','--path',project,'--editor','--import'])
        report['godot'] = []
        for index in range(0,len(entries),2):
            config=out/f'godot-input-{index}.json';result=out/f'godot-report-{index}.json'
            write(config,entries[index:index+2])
            command=[os.environ.get('GODOT_BIN',GODOT),'--path',project,'--script','res://verify_foliage_molds.gd','--',
                '--input='+str(config),'--report='+str(result)]
            run('godot-check-'+str(index),command[:1]+['--headless']+command[1:])
            if args.visual:run('godot-visual-'+str(index),command+['--visual'])
            result_data=read(result);assert result_data['passed'];report['godot'].append(result_data)
        if args.visual:
            sheet(out,out/'comparison.jpg',3,[[(f'inspection/{n}/godot-{v}.png',n+' | '+v)
                for n in ('first-reference','pilot','wide-same-seed')] for v in ('front','side','below','perspective')])
            sheet(out,out/'controls.jpg',4,[[(f'inspection/{n}/godot-{v}.png',n+' | '+v) for n in primary]
                for v in ('front','side','top','below','near','medium')])
            sheet(out,out/'wood.jpg',4,[[(f'inspection/{n}-wood/godot-{v}.png',n+' madera | '+v) for n in primary]
                for v in ('front','side','perspective')])
            rows=[]
            for entry in entries:
                n=entry['id'];cells=''.join(f'<td><a href="inspection/{n}/godot-{v}.png"><img src="inspection/{n}/godot-{v}.png"></a></td>' for v in rig)
                rows.append('<tr><th>'+html.escape(n)+'</th>'+cells+'</tr>')
            (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>B4 · segundo blueprint</title><style>body{font:16px sans-serif;background:#e9edf1}img{width:210px}th{min-width:160px}</style><h1>B4: copa columnar y reutilización</h1><p>Cuatro semillas con parámetros comunes. Misma paleta, luz, cámaras y escala física para todas las escenas. Aprobación artística pendiente.</p><a href="verification.json">Métricas y fallos</a><table>'+''.join(rows)+'</table>')
        checks['sources-and-recipes-unchanged-during-run'] = before == {str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)}
        report['passed'] = all(checks.values()) and all(c['status']=='generated' for c in report['cases'].values())
        report['matrix_executed'] = True
    finally:write(out/'verification.json',report)
    print('B4 matriz ejecutada; passed='+str(report['passed']),flush=True)


if __name__=='__main__':
    main()
