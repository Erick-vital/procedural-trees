#!/usr/bin/env python3
"""Verificar roble 2.2.0: cuatro casos, repetición, históricos y revisión Godot."""
import argparse
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.runner import execute_blueprint,BLENDER
from treegen.evaluation import validate_result
from treegen.oak_crossed_evaluation import channels
from review_pine_painted import read,write,run,sha,camera
from verify_foliage_unit import GODOT
from verify_painted_oak import mask_metrics
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--stage',choices=['all','generate','review'],default='all');a=p.parse_args();out=a.output.resolve()
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),
             XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    matrix=read(ROOT/'configs/verification/oak-wood-v1.json')
    if a.stage in ('all','generate'):
        out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
        report={'passed':False,'matrix':matrix,'checks':{},'cases':{}}
        old_evidence=read(ROOT/'docs/evidence/roble-pintado/implementacion-01/verification.json')['cases']
        folders=[]
        for row,expected in zip(matrix['cases'],(6812,3132,5820,6900)):
            n=row['id'];new=out/n;before=out/('before-'+n)
            request={**row['instance'],'blueprint_version':'2.1.0'}
            old=execute_blueprint(ROOT/'blueprints/roble_copa_ancha/2.1.0.json',request,before,render=False)
            m=execute_blueprint(ROOT/matrix['blueprint'],row['instance'],new,render=False)
            assert m['metrics']['triangles']==expected
            assert m['export_validation']['selective_wood_valid']
            report['checks'][n+'-historical-2.1-exact']=old['glb_sha256']==old_evidence[n]['glb_sha256']
            _,p,pn,_=channels(new/'tree.glb');_,op,opn,_=channels(before/'tree.glb')
            report['checks'][n+'-foliage-exact']=p['Painted_Foliage']==op['Painted_Foliage'] and pn['Painted_Foliage']==opn['Painted_Foliage']
            report['checks'][n+'-export']=m['export_validation']['trunk_primary_remaining_supports_exact']
            report['cases'][n]={k:m[k] for k in ('metrics','glb_sha256','duration_seconds','export_validation','wood_optimization','reference_glb_sha256')}
            report['cases'][n]['before_metrics']=old['metrics'];folders.extend([before,new])
            print(n+': '+str(old['metrics']['triangles'])+' → '+str(expected)+' tris',flush=True)
        repeat=execute_blueprint(ROOT/matrix['blueprint'],matrix['cases'][0]['instance'],out/'pilot-repeat',render=False)
        report['checks']['repeat-identical']=repeat['glb_sha256']==report['cases']['pilot']['glb_sha256']
        trial=ROOT/'artifacts/roble-pintado/madera-03/after/secondary20mm-tree/branch.glb'
        if trial.is_file():
            _,p,pn,_=channels(out/'pilot/tree.glb');_,tp,tn,_=channels(trial)
            report['checks']['approved-pilot-geometry-uv-normals']=all(sorted(p[k])==sorted(tp[k]) and sorted(pn[k])==sorted(tn[k]) for k in p)
        for n,recipe,request,evidence in [
            ('pine','blueprints/pino_conico/2.3.0.json','presets/blueprints/pino-pintado-laminas/pilot.json','docs/evidence/pino-pintado/pp4-laminas/verification.json'),
            ('columnar','blueprints/arbol_copa_columnar/1.0.0.json','presets/blueprints/columnar/pilot.json','docs/evidence/blueprints/b4/verification.json')]:
            m=execute_blueprint(ROOT/recipe,read(ROOT/request),out/(n+'-regression'),render=False)
            report['checks'][n+'-regression-exact']=m['glb_sha256']==read(ROOT/evidence)['cases']['pilot']['glb_sha256']
        run([BLENDER,'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',ROOT/'blender/export_oak_wood.py','--',*folders],out/'logs/export-wood.log',env)
        report['passed']=all(report['checks'].values());write(out/'verification.json',report);assert report['passed'],report['checks']
    if a.stage=='generate':return
    report=read(out/'verification.json');project=out/'godot';project.mkdir();captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):
        shutil.copy2(ROOT/'godot'/name,project/name)
    script=project/'review_painted_pine.gd';code=script.read_text()
    script.write_text(code.replace('im.get_width()==1254 and im.get_height()==1254','(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)'))
    for row in matrix['cases']:
        n=row['id']
        for prefix,folder in [('before',out/('before-'+n)),('new',out/n)]:
            for kind,file in [('tree','tree.glb'),('wood','wood/branch.glb')]:
                shutil.copy2(folder/file,project/(prefix+'-'+n+'-'+kind+'.glb'))
    godot=os.environ.get('GODOT_BIN',GODOT)
    run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/import.log',env)
    report['godot']=[];report['mask_metrics']={};protocol={}
    for row in matrix['cases']:
        n=row['id'];bounds=report['cases'][n]['before_metrics']['bounds_blender']
        center=[(a+b)/2 for a,b in zip(*bounds)];span=max(b-a for a,b in zip(*bounds))
        shots=[{'id':v,'camera':camera(center,span,d,span*1.15),'background':'#EEE9DF','light':[-35,-25,0]}
               for v,d in [('front',[0,-1,.1]),('side',[1,0,.1]),('perspective',[1,-1,.45]),('back',[-1,1,.3]),('top',[0,0,1]),('below',[1,-1,-.7])]]
        shots += [{'id':v,'camera':camera(center,span,[1,-1,.45],span*f),'background':'#EEE9DF','light':[-35,-25,0]} for v,f in [('close',.4),('medium',4),('far',10)]]
        protocol[n]={'center':center,'span':span,'shots':shots};report['mask_metrics'][n]={}
        for kind in ('tree','wood'):
            entries=[]
            for prefix,folder in [('before',out/('before-'+n)),('new',out/n)]:
                metrics=read(folder/'manifest.json')['metrics'] if kind=='tree' else read(folder/'wood/metrics.json')
                label=prefix+'-'+n+'-'+kind;entries.append({'id':label,'resource':'res://'+label+'.glb','metrics':metrics})
            for mask in (False,True):
                tag=n+'-'+kind+('-mask' if mask else '-color');config=out/(tag+'-input.json');result=out/(tag+'-report.json')
                selected=[{**s,'id':'mask-'+s['id'],'background':'#FFFFFF'} for s in shots] if mask else shots
                write(config,{'output':str(captures),'report':str(result),'center':center,'span':span,'original_low':[0,0,0],'assets':entries,'shots':selected,'mask_pass':mask})
                run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],out/'logs'/(tag+'.log'),env)
                review=read(result);assert review['passed'];report['godot'].append(review)
            report['mask_metrics'][n][kind]={s['id']:mask_metrics(captures/f'before-{n}-{kind}--mask-{s["id"]}.png',captures/f'new-{n}-{kind}--mask-{s["id"]}.png') for s in shots}
            sheet(out,out/(n+'-'+kind+'.jpg'),2,[[(f'captures/{prefix}-{n}-{kind}--{v}.png',prefix+' '+n+' | '+v) for prefix in ('before','new')]
                for v in ('front','side','perspective','back','top','below','close')])
        print(n+': 72 capturas reales verificadas',flush=True)
    write(out/'protocol.json',protocol)
    sheet(out,out/'controls.jpg',4,[[(f'captures/new-{row["id"]}-tree--{v}.png',row['id']+' | '+v) for row in matrix['cases']] for v in ('front','perspective','below')])
    report['capture_sha256']={p.name:sha(p) for p in captures.glob('*.png')};assert len(report['capture_sha256'])==288
    files=[Path(__file__),ROOT/'blender/export_oak_wood.py',ROOT/'blender/generate_crossed_oak.py',ROOT/matrix['blueprint'],ROOT/'configs/verification/oak-wood-v1.json',*sorted((ROOT/'src/treegen').glob('*.py'))]
    report['source_lock']={str(p.relative_to(ROOT)):sha(p) for p in files};write(out/'verification.json',report)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Roble 2.2.0 · madera selectiva</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{width:100%;max-width:1200px}</style><h1>Roble 2.2.0 · madera selectiva</h1><p>Antes: receta 2.1.0. Nueva: secundarias a 20 mm, tronco/primarias/soportes/follaje conservados. Cuatro casos y revisión real de árbol y madera.</p><img src="controls.jpg">'+''.join('<h2>'+row['id']+'</h2>'+''.join('<a href="'+row['id']+'-'+k+'.jpg"><img src="'+row['id']+'-'+k+'.jpg"></a>' for k in ('tree','wood')) for row in matrix['cases']))


if __name__=='__main__':main()
