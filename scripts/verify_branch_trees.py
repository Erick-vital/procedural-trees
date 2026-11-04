#!/usr/bin/env python3
"""Integración R4: matriz reproducible y revisión de árboles completos en Godot."""
import argparse
import os
import math
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.branch_tree_runner import execute_branch_tree
from review_pine_painted import read,write,sha,camera
from verify_branch_simplification import matrix,compare_images,wood_pixels
from verify_branch_space import run
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def shadow_shots(out):
    item=read(out/'input.json')['variants']['full']
    vertices=[v for mesh in item['wood']+item['foliage'] for v in mesh['vertices']]
    floor=min(v[2] for v in vertices)-.15;shots=[]
    for i,light in enumerate(([-35,-25,0],[-35,-90,0],[-35,155,0])):
        pitch,yaw=map(math.radians,light[:2]);direction=[-math.sin(yaw)*math.cos(pitch),math.cos(yaw)*math.cos(pitch),math.sin(pitch)]
        points=vertices+[[v[k]+direction[k]*(floor-v[2])/direction[2] for k in range(3)] for v in vertices]
        lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)]
        center=[(a+b)/2 for a,b in zip(lo,hi)];span=max(b-a for a,b in zip(lo,hi))
        shots.append({'id':f'ground-{i}','camera':camera(center,span,[1,-1,1.5],span*1.35),'background':'#EEE9DF','light':light,'receiver':True})
    return shots


def review(out):
    report=read(out/'manifest.json');assert report['status']=='completed'
    project=out/'godot';project.mkdir();captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd','review_branch_visibility.gd'):
        shutil.copy2(ROOT/'godot'/name,project/name)
    path=project/'review_painted_pine.gd'
    text=path.read_text().replace('im.get_width()==1254 and im.get_height()==1254',
        '(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)')
    text=text.replace("if mat.resource_name=='Painted_Foliage':", "if mat.resource_name=='Painted_Foliage':\n\t\t\t\t\tmat.albedo_color.a=0.0 if shot.get('wood_only',false) else 1.0")
    path.write_text(text)
    entries=[]
    variants={**report['variants'],'source':{'metrics':report['source_metrics']}}
    for name,item in variants.items():
        shutil.copy2(out/name/'tree.glb',project/(name+'.glb'))
        entries.append({'id':name,'resource':'res://'+name+'.glb','metrics':item['metrics']})
    lo,hi=report['source_metrics']['bounds_blender'];center=[(a+b)/2 for a,b in zip(lo,hi)];span=max(b-a for a,b in zip(lo,hi))
    shots=matrix(center,span);basic=[s for s in shots if s['id'].startswith('medium-')]
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    write(out/'view-matrix.json',{'center':center,'span':span,'shots':shots})
    run([GODOT,'--headless','--path',project,'--editor','--import'],out/'logs/godot-import.log',env)
    results={}
    for mode,names,script,selected in [
        ('color',('full','simple'),'review_painted_oak_pilot.gd',shots),
        ('structure',('source','bare'),'review_painted_oak_pilot.gd',[{**s,'wood_only':True} for s in basic]),
        ('baseline',('source','simple'),'review_painted_oak_pilot.gd',basic),
        ('visible-wood',('full','simple'),'review_branch_visibility.gd',[s for s in shots if not s.get('receiver')]),
        ('mask',('foliage-before','foliage-after'),'review_painted_oak_pilot.gd',basic),
        ('shadows',('full','simple'),'review_painted_oak_pilot.gd',shadow_shots(out))]:
        folder=captures/mode;folder.mkdir();config=out/(mode+'-input.json');result=out/(mode+'-godot.json')
        write(config,{'output':str(folder),'report':str(result),'center':center,'span':span,'original_low':lo,
            'assets':[e for e in entries if e['id'] in names],'shots':selected,'mask_pass':mode=='mask'})
        # Un proceso por asset evita diferencias de rasterizado por orden de
        # instancia: dos GLB idénticos variaron dos píxeles en el arnés compartido.
        runs=[];combined=read(config)
        for entry in combined['assets']:
            one=out/(mode+'-'+entry['id']+'-input.json');one_result=out/(mode+'-'+entry['id']+'-godot.json')
            write(one,{**combined,'assets':[entry],'report':str(one_result)})
            run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://'+script,'--',one,'--visual'],out/'logs'/('godot-'+mode+'-'+entry['id']+'.log'),env)
            data=read(one_result);assert data['passed'];runs.append(data)
        results[mode]={'passed':True,'runs':runs};write(result,results[mode])
    comparison={s['id']:compare_images(captures/'color'/('full--'+s['id']+'.png'),captures/'color'/('simple--'+s['id']+'.png')) for s in shots}
    visible={}
    for s in shots:
        if s.get('receiver'):continue
        name=s['id'];a=wood_pixels(captures/'visible-wood'/('full--'+name+'.png'));b=wood_pixels(captures/'visible-wood'/('simple--'+name+'.png'))
        visible[name]={'reference_pixels':sum(a),'lost_pixels':sum(x and not y for x,y in zip(a,b)),'gained_pixels':sum(y and not x for x,y in zip(a,b))}
    checks={'visible_wood_masks_exact':all(v['lost_pixels']==v['gained_pixels']==0 for v in visible.values())}
    for s in basic:
        name=s['id'];checks['foliage-mask-'+name]=compare_images(captures/'mask'/('foliage-before--'+name+'.png'),captures/'mask'/('foliage-after--'+name+'.png'))['changed_pixels']==0
    shadow_comparison={s['id']:compare_images(captures/'shadows'/('full--'+s['id']+'.png'),captures/'shadows'/('simple--'+s['id']+'.png')) for s in shadow_shots(out)}
    checks['shadows_exact']=all(v['changed_pixels']==0 for v in shadow_comparison.values())
    sheet(out,out/'shadows.jpg',2,[[(f'captures/shadows/{name}--{s["id"]}.png',name+' '+s['id']) for name in ('full','simple')] for s in shadow_shots(out)])
    for distance in ('near','medium','far'):
        sheet(out,out/(distance+'.jpg'),2,[[(f'captures/color/{name}--{s["id"]}.png',name+' '+s['id']) for name in ('full','simple')] for s in shots if s['id'].startswith(distance+'-')])
    sheet(out,out/'bare.jpg',2,[[(f'captures/structure/{name}--{s["id"]}.png',name+' '+s['id']) for name in ('source','bare')] for s in basic])
    sheet(out,out/'visible-wood.jpg',2,[[(f'captures/visible-wood/{name}--{s["id"]}.png',name+' '+s['id']) for name in ('full','simple')] for s in basic])
    write(out/'review.json',{'passed':all(checks.values()),'checks':checks,'godot':results,'image_comparison':comparison,'visible_wood_comparison':visible,'shadow_comparison':shadow_comparison,
        'captures_sha256':{str(p.relative_to(captures)):sha(p) for p in captures.rglob('*.png')},'visual_review':'pending_agent','artistic_acceptance':'pending_user_complete_trees'})
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Árbol completo R4</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}</style><h1>Árbol completo: R2 / R3</h1><p>Copa congelada; R2 sin hojas, R3 con hojas. Aceptación artística del árbol completo pendiente.</p>'+''.join('<h2>'+label+'</h2><img src="'+name+'.jpg">' for name,label in [('near','Cerca'),('medium','Media'),('far','Lejos'),('bare','Madera anterior / nueva sin hojas'),('visible-wood','Madera expuesta R2 / R3'),('shadows','Sombras completas')]))
    print(out.name,checks,flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--matrix',type=Path,default=ROOT/'configs/verification/branch-tree-v1.json')
    p.add_argument('--stage',choices=('generate','review'),default='generate');p.add_argument('--case')
    a=p.parse_args();out=a.output.resolve();spec=read(a.matrix)
    for case in spec['cases']:
        if a.case and case['id']!=a.case:continue
        target=out/case['id']
        if a.stage=='generate':
            execute_branch_tree(ROOT/spec['definition'],{'profile':case['profile'],'seeds':case['seeds']},target)
        else:review(target)

if __name__=='__main__':main()
