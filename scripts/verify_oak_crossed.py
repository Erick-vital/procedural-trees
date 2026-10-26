#!/usr/bin/env python3
"""Verificar receta cruzada, controles, repetición, regresiones y rehorneado."""
import argparse
import os
from pathlib import Path
import shutil
import sys
from PIL import Image
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
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--stage',choices=['all','generate','review'],default='all');a=p.parse_args();out=a.output.resolve()
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    matrix=read(ROOT/'configs/verification/oak-crossed-v1.json')
    if a.stage in ('all','generate'):
        out.mkdir(parents=True,exist_ok=True);(out/'logs').mkdir(exist_ok=True);report={'passed':False,'matrix':matrix,'checks':{},'cases':{}}
        historical=read(ROOT/'docs/evidence/blueprints/b3-revision/verification.json')['cases']
        for row in matrix['cases']:
            n=row['id'];folder=out/n
            if (folder/'manifest.json').is_file():
                m=read(folder/'manifest.json');assert m['resolved_blueprint']['instance_request']==row['instance'];validate_result(folder)
            else:m=execute_blueprint(ROOT/matrix['blueprint'],row['instance'],folder,render=False)
            assert m['reference_glb_sha256']==historical[n]['glb_sha256']
            if not (folder/'baseline/metrics.json').is_file():
                run([BLENDER,'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',ROOT/'blender/oak_crossed_reference.py','--',folder],out/'logs'/(n+'-baseline.log'),env)
            report['cases'][n]={k:m[k] for k in ('metrics','reference_metrics','glb_sha256','reference_glb_sha256','duration_seconds','export_validation','groups_sha256')}
            report['checks'][n+'-export']=m['export_validation']['crossed_panels_valid']
            print(n+': '+str(m['metrics']['triangles'])+' tris',flush=True)
        if (out/'pilot-repeat/manifest.json').is_file():
            repeated=read(out/'pilot-repeat/manifest.json');validate_result(out/'pilot-repeat')
            assert repeated['resolved_blueprint']['instance_request']==matrix['cases'][0]['instance']
        else:repeated=execute_blueprint(ROOT/matrix['blueprint'],matrix['cases'][0]['instance'],out/'pilot-repeat',render=False)
        report['checks']['repeat-identical']=repeated['glb_sha256']==report['cases']['pilot']['glb_sha256'];assert report['checks']['repeat-identical']
        trial=ROOT/'artifacts/roble-pintado/cruzadas-01/tree-cross3/asset.glb'
        if trial.is_file():
            _,p,n,_=channels(out/'pilot/tree.glb');_,tp,tn,_=channels(trial)
            report['checks']['pilot-approved-geometry-uv-normals']=all(sorted(p[k])==sorted(tp[k]) and sorted(n[k])==sorted(tn[k]) for k in p)
        for name,recipe,request,evidence in [('pine','blueprints/pino_conico/2.3.0.json','presets/blueprints/pino-pintado-laminas/pilot.json','docs/evidence/pino-pintado/pp4-laminas/verification.json'),
             ('columnar','blueprints/arbol_copa_columnar/1.0.0.json','presets/blueprints/columnar/pilot.json','docs/evidence/blueprints/b4/verification.json')]:
            folder=out/(name+'-regression')
            if (folder/'manifest.json').is_file():m=read(folder/'manifest.json');validate_result(folder)
            else:m=execute_blueprint(ROOT/recipe,read(ROOT/request),folder,render=False)
            report['checks'][name+'-unchanged']=m['glb_sha256']==read(ROOT/evidence)['cases']['pilot']['glb_sha256']
        run([BLENDER,'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',ROOT/'blender/rebake_oak_crossed.py','--',out/'rebaked-atlas.png'],out/'logs/rebake.log',env)
        a_image=Image.open(out/'rebaked-atlas.png');b_image=Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png')
        report['checks']['rebake-rgba-identical']=(a_image.mode,a_image.size,a_image.tobytes())==(b_image.mode,b_image.size,b_image.tobytes())
        report['rebake_png_bytes_identical']=sha(out/'rebaked-atlas.png')==sha(ROOT/'assets/roble-pintado/v0.3.0/foliage.png')
        report['passed']=all(report['checks'].values());write(out/'verification.json',report);assert report['passed'],report['checks']
    if a.stage=='generate':return
    report=read(out/'verification.json');project=out/'godot';project.mkdir(exist_ok=False);captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    script=project/'review_painted_pine.gd';code=script.read_text();old='im.get_width()==1254 and im.get_height()==1254';assert code.count(old)==1
    script.write_text(code.replace(old,'(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)'))
    for row in matrix['cases']:
        n=row['id']
        for kind,path in [('before',out/n/'baseline/branch.glb'),('new',out/n/'tree.glb')]:shutil.copy2(path,project/(kind+'-'+n+'.glb'))
    godot=os.environ.get('GODOT_BIN',GODOT);run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/import.log',env)
    report['godot']=[];report['mask_metrics']={};protocol={}
    for row in matrix['cases']:
        n=row['id'];m=read(out/n/'manifest.json');bounds=m['reference_metrics']['bounds_blender'];center=[(a+b)/2 for a,b in zip(*bounds)];span=max(b-a for a,b in zip(*bounds))
        views=[('front',[0,-1,.1]),('side',[1,0,.1]),('perspective',[1,-1,.45]),('back',[-1,1,.3]),('top',[0,0,1]),('below',[1,-1,-.7])]
        shots=[{'id':v,'camera':camera(center,span,d,span*1.15),'background':'#EEE9DF','light':[-35,-25,0]} for v,d in views]
        shots += [{'id':v,'camera':camera(center,span,[1,-1,.45],span*f),'background':'#EEE9DF','light':[-35,-25,0]} for v,f in [('near',2),('medium',4),('far',10)]]
        entries=[{'id':kind+'-'+n,'resource':'res://'+kind+'-'+n+'.glb','metrics':read(out/n/'baseline/metrics.json') if kind=='before' else m['metrics']} for kind in ('before','new')]
        protocol[n]={'center':center,'span':span,'shots':shots}
        for mode in ('color','mask'):
            selected=shots if mode=='color' else [{**s,'id':'mask-'+s['id'],'background':'#FFFFFF'} for s in shots]
            config=out/(n+'-'+mode+'-input.json');result=out/(n+'-'+mode+'-report.json')
            write(config,{'output':str(captures),'report':str(result),'center':center,'span':span,'original_low':[0,0,0],'assets':entries,'shots':selected,'mask_pass':mode=='mask'})
            run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],out/'logs'/(n+'-'+mode+'.log'),env)
            r=read(result);assert r['passed'];report['godot'].append(r)
        report['mask_metrics'][n]={s['id']:mask_metrics(captures/('before-'+n+'--mask-'+s['id']+'.png'),captures/('new-'+n+'--mask-'+s['id']+'.png')) for s in shots}
        print(n+': 36 capturas reales OK',flush=True)
    write(out/'protocol.json',protocol)
    for n in ('pilot','joven-07','adulto-00','viejo-00'):
        sheet(out,out/(n+'.jpg'),2,[[(f'captures/{kind}-{n}--{view}.png',kind+' '+n+' | '+view) for kind in ('before','new')] for view in ('front','side','perspective','back','top','below')])
    sheet(out,out/'controls.jpg',4,[[(f'captures/new-{row["id"]}--{view}.png',row['id']+' | '+view) for row in matrix['cases']] for view in ('front','perspective','below')])
    report['capture_sha256']={p.name:sha(p) for p in captures.glob('*.png')};assert len(report['capture_sha256'])==144
    files=[ROOT/matrix['blueprint'],ROOT/'configs/verification/oak-crossed-v1.json',Path(__file__),*sorted((ROOT/'src/treegen').glob('*.py')),*sorted((ROOT/'assets/roble-pintado/v0.3.0').glob('*')),
        ROOT/'blender/generate_crossed_oak.py',ROOT/'blender/oak_crossed_reference.py',ROOT/'blender/rebake_oak_crossed.py',ROOT/'blender/oak_crossed_trial.py',ROOT/'schemas/tree-blueprint-crossed-oak.schema.json',ROOT/'schemas/tree-instance-crossed-oak.schema.json']
    report['source_lock']={str(p.relative_to(ROOT)):sha(p) for p in files if p.is_file()};write(out/'verification.json',report)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Roble 2.1.0 · tres láminas</title><style>body{font:18px sans-serif;background:#eee9df;margin:28px}img{width:100%;max-width:1200px}</style><h1>Roble 2.1.0 · tres láminas</h1><p>Cuatro casos, 264 grupos/792 láminas, atlas y ocho plantillas fijos. Before: seis hojas pintadas con misma madera. New: tres láminas cruzadas.</p><img src="controls.jpg">'+''.join('<h2>'+r['id']+'</h2><a href="'+r['id']+'.jpg"><img src="'+r['id']+'.jpg"></a>' for r in matrix['cases']))
    print('Receta 2.1.0 verificada: cuatro casos, repetición, regresiones, atlas rehorneado y 144 capturas.',flush=True)


if __name__=='__main__':main()
