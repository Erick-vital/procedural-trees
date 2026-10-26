#!/usr/bin/env python3
"""Cuatro robles: exportación, regresiones, máscaras y revisión Godot real."""
import argparse
import copy
import os
from pathlib import Path
import shutil
import sys
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.runner import execute_blueprint
from treegen.evaluation import validate_result
from treegen.pine_painted_sample import canonical_hash
from treegen.oak_painted import card
from review_pine_painted import camera,read,write,run,sha
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def mask_metrics(old,new):
    def mask(path):
        im=Image.open(path).convert('L')
        return im.point(lambda p:255 if p<128 else 0)
    a,b=mask(old),mask(new);area=a.histogram()[255];new_area=b.histogram()[255]
    intersection=ImageChops.darker(a,b).histogram()[255];union=ImageChops.lighter(a,b).histogram()[255]
    return {'old_pixels':area,'new_pixels':new_area,'coverage_ratio':new_area/area,'iou':intersection/union,'xor_pixels':union-intersection}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--stage',choices=['all','generate','review'],default='all')
    a=p.parse_args();out=a.output.resolve();matrix=read(ROOT/'configs/verification/oak-painted-v1.json')
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    if a.stage in ('all','generate'):
        out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir();report={'passed':False,'matrix':matrix,'cases':{},'checks':{}}
        historical=read(ROOT/'docs/evidence/blueprints/b3-revision/verification.json')['cases']
        for row in matrix['cases']:
            n=row['id'];m=execute_blueprint(ROOT/matrix['blueprint'],row['instance'],out/n,render=False)
            old=read(out/n/'reference/manifest.json');g=read(out/n/'placements.json');c=report['checks']
            c[n+'-historical-exact']=m['reference_glb_sha256']==historical[n]['glb_sha256']
            c[n+'-six-per-support']=len(g)==1584 and len(m['supports'])==264
            c[n+'-wood-and-twigs-exact']=m['export_validation']['exact_wood_and_twig_channels']
            c[n+'-distribution-exact']=m['placements']==old['placements'] and m['supports']==old['supports']
            c[n+'-cards-exact']=canonical_hash(g)==canonical_hash([card(leaf,m['paint_seed']) for leaf in old['placements']])
            c[n+'-reduction']=m['metrics']['triangles']==old['metrics']['triangles']-1584
            c[n+'-export']=validate_result(out/n)['exported_cards_valid']
            report['cases'][n]={k:m[k] for k in ('metrics','reference_metrics','reference_glb_sha256','glb_sha256','duration_seconds','glb_bytes','wood_sha256')}
            write(out/'verification.json',report);print(n+': generado/verificado',flush=True)
        repeated=execute_blueprint(ROOT/matrix['blueprint'],matrix['cases'][0]['instance'],out/'pilot-repeat',render=False)
        c['repeat-identical']=repeated['glb_sha256']==report['cases']['pilot']['glb_sha256']
        for name,blueprint,request,evidence in [
            ('pine-reference','blueprints/pino_conico/2.3.0.json','presets/blueprints/pino-pintado-laminas/pilot.json','docs/evidence/pino-pintado/pp4-laminas/verification.json'),
            ('columnar-reference','blueprints/arbol_copa_columnar/1.0.0.json','presets/blueprints/columnar/pilot.json','docs/evidence/blueprints/b4/verification.json')]:
            m=execute_blueprint(ROOT/blueprint,read(ROOT/request),out/name,render=False)
            c[name+'-unchanged']=m['glb_sha256']==read(ROOT/evidence)['cases']['pilot']['glb_sha256']
        report['source_lock']={str(path.relative_to(ROOT)):sha(path) for folder in ('src/treegen','blender','schemas','godot','assets/roble-pintado') for path in (ROOT/folder).rglob('*') if path.is_file() and '__pycache__' not in str(path) and '.godot' not in path.parts and path.suffix not in ('.glb','.import')}
        report['source_lock'].update({str(path.relative_to(ROOT)):sha(path) for path in [Path(__file__),ROOT/matrix['blueprint'],ROOT/'scripts/build_oak_atlas.py',ROOT/'configs/verification/oak-painted-v1.json']})
        report['passed']=all(c.values());write(out/'verification.json',report);assert report['passed'],[k for k,v in c.items() if not v]
    if a.stage=='generate':return
    report=read(out/'verification.json');assert all(sha(ROOT/p)==v for p,v in report['source_lock'].items())
    project=out/'godot';project.mkdir(exist_ok=False);captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_oak.gd','painted_oak_asset.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    views=[('front',[0,-1,.1]),('side',[1,0,.1]),('perspective',[1,-1,.45]),('back',[-1,1,.3]),('top',[0,0,1]),('below',[1,-1,-.7])]
    godot=os.environ.get('GODOT_BIN',GODOT);entries=[];protocol={}
    for row in matrix['cases']:
        n=row['id'];m=read(out/n/'manifest.json');bounds=m['reference_metrics']['bounds_blender'];center=[(x+y)/2 for x,y in zip(*bounds)]
        span=max(y-x for x,y in zip(*bounds));scale=span*1.15
        shots=[{'id':v,'camera':camera(center,span,d,scale),'background':'#EEE9DF','light':[-35,-25,0]} for v,d in views]
        shots += [{'id':name,'camera':camera(center,span,[1,-1,.45],span*factor),'background':'#EEE9DF','light':[-35,-25,0]} for name,factor in [('near',2),('medium',4),('far',10)]]
        shots += [{**s,'id':'mask-'+s['id'],'mask':True,'background':'#FFFFFF'} for s in shots]
        protocol[n]={'center':center,'span':span,'shots':shots}
        for kind in ('before','new'):
            source=out/n/('reference/tree.glb' if kind=='before' else 'tree.glb');name=kind+'-'+n
            shutil.copy2(source,project/(name+'.glb'))
            resource='res://'+name+'.glb'
            if kind=='new':
                (project/(name+'.tscn')).write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="PackedScene" path="res://'+name+'.glb" id="1"]\n[ext_resource type="Script" path="res://painted_oak_asset.gd" id="2"]\n[node name="PaintedOak" instance=ExtResource("1")]\nscript=ExtResource("2")\n')
                resource='res://'+name+'.tscn'
            entries.append({'id':name,'resource':resource,'metrics':m['reference_metrics'] if kind=='before' else m['metrics']})
    write(out/'protocol.json',protocol)
    run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/godot-import.log',env)
    reports=[]
    for index,row in enumerate(matrix['cases']):
        n=row['id'];config=out/(n+'-review-input.json');result=out/(n+'-review-report.json');p=protocol[n]
        write(config,{'output':str(captures),'report':str(result),'span':p['span'],'center':p['center'],'original_low':[0,0,0],'assets':entries[index*2:index*2+2],'shots':p['shots']})
        run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak.gd','--',config,'--visual'],out/'logs'/('godot-'+n+'.log'),env)
        reports.append(read(result));print(n+': 36 capturas reales',flush=True)
    report['godot']=reports;report['silhouette']={};checks=report['checks']
    for row in matrix['cases']:
        n=row['id'];metrics={s['id']:mask_metrics(captures/f'before-{n}--{s["id"]}.png',captures/f'new-{n}--{s["id"]}.png') for s in protocol[n]['shots'] if s.get('mask')}
        report['silhouette'][n]=metrics
        checks[n+'-shape-iou-99']=all(v['iou']>=.99 and .99<=v['coverage_ratio']<=1.01 for key,v in metrics.items() if key not in ('mask-near','mask-medium','mask-far'))
    report['capture_sha256']={p.name:sha(p) for p in captures.glob('*.png')}
    checks['real-captures']=len(report['capture_sha256'])==144;checks['godot']=all(r['passed'] for r in reports)
    report['passed']=all(checks.values());write(out/'verification.json',report)
    for name,views in [('comparison.jpg',['front','side','perspective']),('controls.jpg',['front','side','perspective','back','top','below']),('distances.jpg',['near','medium','far']),('masks.jpg',['mask-front','mask-side','mask-perspective'])]:
        sheet(out,out/name,4,[[(f'captures/{kind}-{r["id"]}--{v}.png',kind+' '+r['id']+' | '+v) for r in matrix['cases']] for v in views for kind in ('before','new')])
    cells=''.join('<figure><a href="captures/'+p+'"><img width="250" src="captures/'+p+'"></a><figcaption>'+p+'</figcaption></figure>' for p in sorted(report['capture_sha256']))
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Roble pintado 2.0.0</title><style>body{font:16px sans-serif;background:#eee}main{display:flex;flex-wrap:wrap}</style><h1>Roble: 1.2.0 / 2.0.0</h1><p>Mismos planos, hojas y madera; contorno recortado por atlas. Aceptación artística pendiente.</p><main>'+cells+'</main>')
    print('passed='+str(report['passed']),flush=True)
    assert report['passed'],[k for k,v in checks.items() if not v]

if __name__=='__main__':main()
