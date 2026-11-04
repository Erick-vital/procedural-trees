#!/usr/bin/env python3
"""F5: base Python/candidata, treinta parejas y revisión Godot reproducible."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.blueprints import load_blueprint,resolve_blueprint,canonical_hash
from treegen.runner import BLENDER
from treegen.evaluation import validate_result
from treegen.branch_structure import generate_structure
from treegen.branch_space import measure,separate
from review_pine_painted import read,write,sha,camera
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def run(command, log, env, timeout=180):
    with Path(log).open('w') as stream:
        process=subprocess.Popen(list(map(str,command)),cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            code=process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait()
            raise TimeoutError(str(log)+': tiempo excedido')
    content=Path(log).read_text()
    if code or 'SCRIPT ERROR:' in content or '\nERROR:' in content:
        raise RuntimeError(str(log)+': '+content[-2500:])


def inputs():
    config=read(ROOT/'configs/verification/f5-v1.json')
    assert sha(ROOT/config['base_cases'])==config['base_cases_sha256']
    blueprint=load_blueprint(ROOT/config['recipe'])
    rows=[]
    for case in read(ROOT/'presets/q3-cases.json'):
        name=case['id']
        profile={'joven':'joven','adulto':'adulto','viejo':'viejo'}[name.split('-')[0]]
        template=read(ROOT/'presets/blueprints/roble-madera'/({'joven':'joven-07','adulto':'adulto-00','viejo':'viejo-00'}[profile]+'.json'))
        instance={**template,'seeds':{'base':case['spec']['seed'],'canopy':17,'paint':2718}}
        resolved=resolve_blueprint(blueprint,instance)
        rows.append({'id':name,'partition':'diagnostic' if int(name[-2:])<4 else 'reserved',
                     'instance':instance,'resolved':resolved})
    assert len(rows)==30 and len({r['id'] for r in rows})==30
    return rows


def summary(rows):
    result={}
    for name in ('all','diagnostic','reserved'):
        selected=[r for r in rows if name=='all' or r['partition']==name]
        complete=[r for r in selected if r.get('status')=='completed']
        base=[r['baseline']['f5']['final_metric']['conflicts_per_m'] for r in complete]
        candidate=[r['candidate']['f5']['final_metric']['conflicts_per_m'] for r in complete]
        b=statistics.median(base) if base else None
        c=statistics.median(candidate) if candidate else None
        reduction=1-c/b if b else None
        ratios=[r['candidate']['f5']['final_metric']['length_m']/r['baseline']['f5']['final_metric']['length_m'] for r in complete]
        result[name]={'expected':len(selected),'completed':len(complete),'baseline_median_conflicts_per_m':b,
            'candidate_median_conflicts_per_m':c,'median_reduction':reduction,
            'minimum_length_ratio':min(ratios) if ratios else None,
            'objective_met':len(complete)==len(selected) and reduction is not None and reduction>=.25 and min(ratios)>=.9}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--stage',choices=('pilot','generate','review'),default='generate')
    a=p.parse_args();out=a.output.resolve()
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    if a.stage in ('pilot','generate'):
        out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
        rows=inputs();write(out/'frozen-inputs.json',rows)
        sources={str(f.relative_to(ROOT)):sha(f) for folder in ('src/treegen','blender','scripts','schemas','blueprints','assets','configs','presets','godot','tests')
                 for f in (ROOT/folder).rglob('*') if f.is_file() and f.suffix in ('.py','.json','.png','.gd','.godot')}
        write(out/'sources.json',sources)
        report={'phase':'F5','status':'running','cases':[],'artistic_acceptance':'pending','sources_sha256':sources}
        for row in (rows[:1] if a.stage=='pilot' else rows):
            result={'id':row['id'],'partition':row['partition'],'status':'running'}
            report['cases'].append(result)
            try:
                for variant in ('baseline','candidate'):
                    folder=out/variant/row['id'];folder.mkdir(parents=True)
                    r=row['resolved']
                    job={'spec':r['base_spec'],'spec_sha256':canonical_hash(r['base_spec']),
                         'seeds':r['base_seeds'],'resolved_blueprint':r,'render':False,'output':str(folder),
                         'runner_python':sys.version,'jsonschema_version':'4.19.2','f5_variant':variant}
                    write(folder/'input.json',job)
                    started=time.monotonic()
                    run([os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1',
                         '--python-exit-code','1','--python',ROOT/'blender/f5_structure.py','--',folder/'input.json'],
                        out/'logs'/f'{row["id"]}-{variant}.log',env,timeout=120)
                    manifest=read(folder/'manifest.json')
                    manifest.update(required_views=[],duration_seconds=time.monotonic()-started)
                    write(folder/'manifest.json',manifest)
                    manifest['export_validation']=validate_result(folder)
                    write(folder/'manifest.json',manifest)
                    result[variant]={'metrics':manifest['metrics'],'f5':{k:v for k,v in manifest['f5'].items() if k not in ('structure','rule')},
                        'glb_sha256':sha(folder/'tree.glb'),'duration_seconds':manifest['duration_seconds']}
                result['status']='completed'
            except Exception as exc:
                result.update(status='failed',error=str(exc))
            report['summary']=summary(report['cases']);write(out/'verification.json',report)
            print(row['id']+': '+result['status'],flush=True)
        report.update(status='completed' if all(r['status']=='completed' for r in report['cases']) else 'failed')
        write(out/'verification.json',report)
        return
    review(out,env)


def review(out,env):
    report=read(out/'verification.json')
    assert all(sha(ROOT/name)==value for name,value in report['sources_sha256'].items()),'Fuentes alteradas'
    project=out/'godot';project.mkdir();captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):
        shutil.copy2(ROOT/'godot'/name,project/name)
    path=project/'review_painted_pine.gd'
    path.write_text(path.read_text().replace('im.get_width()==1254 and im.get_height()==1254',
        '(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)'))
    path.write_text(path.read_text().replace("if mat.resource_name=='Painted_Foliage':", "if mat.resource_name=='Painted_Foliage':\n\t\t\t\t\tmat.albedo_color.a=0.0 if shot.get('wood_only',false) else 1.0"))
    for row in report['cases']:
        for variant in ('baseline','candidate'):
            if variant not in row:continue
            shutil.copy2(out/variant/row['id']/'tree.glb',project/f'{variant}-{row["id"]}.glb')
    godot=os.environ.get('GODOT_BIN',GODOT)
    run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/import.log',env)
    report['godot']=[]
    for row in report['cases']:
        if row['status']!='completed':continue
        name=row['id'];entries=[];lows=[];highs=[]
        for variant in ('baseline','candidate'):
            metrics=row[variant]['metrics'];low,high=metrics['bounds_blender']
            lows.append(low);highs.append(high)
            entries.append({'id':f'{variant}-{name}','resource':f'res://{variant}-{name}.glb','metrics':metrics})
        low=[min(v[i] for v in lows) for i in range(3)];high=[max(v[i] for v in highs) for i in range(3)]
        center=[(x+y)/2 for x,y in zip(low,high)];span=max(y-x for x,y in zip(low,high))
        shots=[{'id':view,'camera':camera(center,span,direction,span*1.15),'background':'#EEE9DF','light':[-35,-25,0]}
               for view,direction in [('front',[0,-1,.1]),('side',[1,0,.1]),('perspective',[1,-1,.45]),('top',[0,0,1])]]
        shots += [{**shot,'id':'wood-'+shot['id'],'wood_only':True} for shot in shots[:]]
        config=out/f'{name}-input.json';result=out/f'{name}-godot.json'
        write(config,{'output':str(captures),'report':str(result),'center':center,'span':span,'original_low':[0,0,0],
                      'assets':entries,'shots':shots})
        run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],
            out/'logs'/f'{name}-godot.log',env)
        data=read(result);assert data['passed'];report['godot'].append(data)
        sheet(out,out/f'{name}.jpg',2,[[(f'captures/{v}-{name}--{view}.png',v+' '+name+' '+view)
            for v in ('baseline','candidate')] for view in ('front','side','perspective','top','wood-front','wood-side','wood-perspective','wood-top')])
        print(name+': dieciséis capturas',flush=True)
        write(out/'verification.json',report)
    report['capture_sha256']={p.name:sha(p) for p in captures.glob('*.png')}
    write(out/'verification.json',report)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>F5</title><style>body{font:18px sans-serif;background:#eee9df}img{max-width:100%}</style><h1>F5: base Python / separación espacial</h1>'+''.join(
        f'<h2>{r["id"]}</h2><img src="{r["id"]}.jpg">' for r in report['cases'] if r['status']=='completed'))


if __name__=='__main__':main()
