#!/usr/bin/env python3
"""OF2: tres variantes sobre la misma rama, cámaras comunes y pintura intacta."""
import argparse
from pathlib import Path
import sys
import os
import shutil
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from prepare_oak_foliage_chains import generate_sample
from review_pine_painted import read,write,sha,camera
from verify_branch_space import run
from verify_foliage_unit import GODOT
from foliage_evidence import sheet

REFERENCE=ROOT/'artifacts/oak-foliage/of1-rama-04'


def generate_study(study):
    study.mkdir(parents=True,exist_ok=False)
    for mode in 'ABC':generate_sample(ROOT/f'configs/oak-foliage/chains-{mode}.json',study/mode)


def review_study(study):
    project=study/'godot';project.mkdir();cap=study/'captures';cap.mkdir();logs=study/'logs';logs.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    p=project/'review_painted_pine.gd';p.write_text(p.read_text().replace('im.get_width()==1254 and im.get_height()==1254','(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)'))
    entries=[]
    sources=[('bare',study/'A','bare'),('OF1',REFERENCE,'painted')]+[(v,study/v,'painted') for v in 'ABC']+[(v+'-foliage',study/v,'foliage') for v in 'ABC']
    for name,folder,variant in sources:
        m=read(folder/'manifest.json');assert m['status']=='completed'
        shutil.copy2(folder/variant/'tree.glb',project/(name+'.glb'));entries.append({'id':name,'resource':'res://'+name+'.glb','metrics':m['variants'][variant]['metrics']})
    bounds=[e['metrics']['bounds_blender'] for e in entries];lo=[min(b[0][k] for b in bounds) for k in range(3)];hi=[max(b[1][k] for b in bounds) for k in range(3)]
    center=[(a+b)/2 for a,b in zip(lo,hi)];span=max(b-a for a,b in zip(lo,hi))
    directions=[('front',[0,-1,.12]),('side',[1,0,.12]),('perspective',[1,-1,.4]),('back',[-1,1,.3]),('top',[0,0,1]),('below',[1,-1,-.7])]
    shots=[{'id':n,'camera':camera(center,span,d,span*1.15),'background':'#EEE9DF','light':[-35,-25,0]} for n,d in directions]
    for n,s,bg,light in [('medium',2.2,'#EEE9DF',[-35,-25,0]),('far',4.,'#EEE9DF',[-35,-25,0]),('dark',1.15,'#252A28',[-35,-25,0]),('alternate-light',1.15,'#EEE9DF',[35,120,0]),('shadow',1.4,'#EEE9DF',[-75,-25,0])]:
        shots.append({'id':n,'camera':camera(center,span,[1,-1,.4],span*s),'background':bg,'light':light,'receiver':n=='shadow'})
    env=dict(os.environ,XDG_DATA_HOME=str(study/'xdg/data'),XDG_CONFIG_HOME=str(study/'xdg/config'),XDG_CACHE_HOME=str(study/'xdg/cache'))
    run([GODOT,'--headless','--path',project,'--editor','--import'],logs/'import.log',env)
    results=[]
    for entry in entries:
        name=entry['id'];selected=shots if name in ('OF1','A','B','C') else shots[:6]
        config=study/(name+'-review-input.json');report=study/(name+'-godot.json')
        write(config,{'output':str(cap),'report':str(report),'center':center,'span':span,'original_low':lo,'shots':selected,'assets':[entry]})
        run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],logs/(name+'.log'),env)
        r=read(report);assert r['passed'];results.append(r);print(name,'capturas',len(r['captures']),flush=True)
    # Máscaras de follaje aislado: permiten comparar continuidad en proyección.
    # La referencia OF1 se añade solo aquí, conservando su GLB histórico.
    shutil.copy2(REFERENCE/'foliage/tree.glb',project/'OF1-foliage.glb')
    run([GODOT,'--headless','--path',project,'--editor','--import'],logs/'mask-import.log',env)
    maskcap=study/'masks';maskcap.mkdir();masks=[]
    for name,folder,variant in [('bare',study/'A','bare'),('OF1-foliage',REFERENCE,'foliage')]+[(v+'-foliage',study/v,'foliage') for v in 'ABC']:
        metrics=read(folder/'manifest.json')['variants'][variant]['metrics'];config=study/(name+'-mask-input.json');report=study/(name+'-mask-godot.json')
        write(config,{'output':str(maskcap),'report':str(report),'center':center,'span':span,'original_low':lo,'mask_pass':True,
            'shots':[{**s,'background':'#FFFFFF','receiver':False} for s in shots[:5] if s['id']!='back'],
            'assets':[{'id':name,'resource':'res://'+name+'.glb','metrics':metrics}]})
        run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],logs/(name+'-mask.log'),env)
        r=read(report);assert r['passed'];masks.append(r)
    labels={'OF1':'OF1 anterior','A':'A | terminal/lateral','B':'B | continuidad media','C':'C | fragmentada'}
    for mode,views in [('comparison',('front','side','perspective','back','top','below')),('appearance',('medium','far','dark','alternate-light','shadow'))]:
        sheet(study,study/(mode+'.jpg'),4,[[(f'captures/{v}--{view}.png',labels[v]+' | '+view) for v in ('OF1','A','B','C')] for view in views])
    sheet(study,study/'preview.jpg',3,[[(f'captures/{v}--perspective.png',labels[v]) for v in 'ABC']])
    write(study/'review.json',{'passed':True,'godot':results,'mask_godot':masks,'shots':shots,'captures_sha256':{p.name:sha(p) for p in cap.glob('*.png')},
        'masks_sha256':{p.name:sha(p) for p in maskcap.glob('*.png')},'visual_review':'pending_agent','artistic_acceptance':'pending_user',
        'protocol_source_sha256':sha(Path(__file__))})
    html='<!doctype html><meta charset="utf-8"><title>OF2 · masas por brazo</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}</style><h1>OF2 · misma rama, tres distribuciones</h1><p>A terminal/lateral, B continuidad media y C fragmentada. Madera, pintura, tamaños, plantillas y tris comunes. Muestra madura; no integra copa completa.</p>'
    html+='<img src="preview.jpg"><h2>OF1 / A / B / C, cámaras comunes</h2><img src="comparison.jpg"><h2>Distancias, fondos y sombras</h2><img src="appearance.jpg">'
    html+=''.join(f'<h2>{v}</h2><p><a href="{v}/painted/tree.glb">GLB {v}</a></p><img src="captures/{v}--perspective.png">' for v in 'ABC')
    (study/'index.html').write_text(html)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--stage',choices=('generate','review','all'),default='all');a=p.parse_args();study=a.output.resolve()
    if a.stage in ('all','generate'):generate_study(study)
    if a.stage in ('all','review'):review_study(study)

if __name__=='__main__':main()
