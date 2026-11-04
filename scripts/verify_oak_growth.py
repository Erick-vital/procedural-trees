#!/usr/bin/env python3
"""O1: cinco semillas, cuatro vistas, ablación de arquitectura y etapas de madurez."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.oak_growth_runner import execute_growth
from treegen.branch_tree_runner import execute_branch_tree
from treegen.oak_growth_contract import load_preset
from review_pine_painted import read,write,sha,camera
from verify_branch_space import run
from verify_foliage_unit import GODOT
from foliage_evidence import sheet

VIEWS=[('front',[0,-1,.12]),('side',[1,0,.12]),('top',[0,0,1]),('perspective',[1,-1,.4])]


def render(study,case,with_reference=True):
    out=study/case;report=read(out/'manifest.json');assert report['status']=='completed'
    project=out/'godot';project.mkdir();captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):
        shutil.copy2(ROOT/'godot'/name,project/name)
    path=project/'review_painted_pine.gd';text=path.read_text().replace('im.get_width()==1254 and im.get_height()==1254',
        '(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)')
    text=text.replace("\t\tfor shot in config.shots:","\t\tasset.scale=Vector3.ONE*float(item.get('display_scale',1.0))\n\t\tfor shot in config.shots:")
    path.write_text(text)
    entries=[]
    for name,item in report['variants'].items():
        shutil.copy2(out/name/'tree.glb',project/(name+'.glb'));entries.append({'id':name,'resource':'res://'+name+'.glb','metrics':item['metrics'],'display_scale':1.})
    if with_reference:
        before=study/'references'/case;old=read(before/'manifest.json')['variants']['bare'];scale=report['preset']['height_m']/old['metrics']['height_m']
        shutil.copy2(before/'bare/tree.glb',project/'old.glb');entries.insert(0,{'id':'old','resource':'res://old.glb','metrics':old['metrics'],'display_scale':scale})
    bounds=[[[v*e['display_scale'] for v in row] for row in e['metrics']['bounds_blender']] for e in entries]
    lo=[min(b[0][k] for b in bounds) for k in range(3)];hi=[max(b[1][k] for b in bounds) for k in range(3)]
    center=[(a+b)/2 for a,b in zip(lo,hi)];span=max(b-a for a,b in zip(lo,hi))
    shots=[{'id':name,'camera':camera(center,span,direction,span*1.18),'background':'#EEE9DF','light':[-35,-25,0]} for name,direction in VIEWS]
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    run([GODOT,'--headless','--path',project,'--editor','--import'],out/'logs/godot-import.log',env)
    results=[]
    config={'center':center,'span':span,'original_low':lo,'shots':shots,'output':str(captures)}
    for entry in entries:
        name=entry['id'];path=out/(name+'-review-input.json');result=out/(name+'-godot.json');write(path,{**config,'assets':[entry],'report':str(result)})
        run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',path,'--visual'],out/'logs'/('godot-'+name+'.log'),env)
        data=read(result);assert data['passed'];results.append(data)
    modes=['old','scaffold','bare'] if with_reference else ['scaffold','bare']
    labels={'old':'R4 anterior','scaffold':'O1 tronco y primarias','bare':'O1 cuatro órdenes'}
    sheet(out,out/'comparison.jpg',len(modes),[[(f'captures/{name}--{view}.png',labels[name]+' | '+view) for name in modes] for view,_ in VIEWS])
    write(out/'review.json',{'passed':all(r['passed'] for r in results),'godot':results,'display_transforms':{e['id']:e['display_scale'] for e in entries},
        'shots':shots,'captures_sha256':{p.name:sha(p) for p in captures.glob('*.png')},'visual_review':'pending_agent','artistic_acceptance':'pending_user'})
    print(case,'capturas',sum(len(r['captures']) for r in results),flush=True)


def review_ages(study):
    stages=('joven','maduro','centenario');items=[]
    for stage in stages:
        out=study/(stage+'-3100');m=read(out/'manifest.json')['variants']['bare']['metrics']
        items.append((stage,out,m,1/m['height_m']))
    lo=[min(m['bounds_blender'][0][k]*scale for _,_,m,scale in items) for k in range(3)]
    hi=[max(m['bounds_blender'][1][k]*scale for _,_,m,scale in items) for k in range(3)]
    center=[(a+b)/2 for a,b in zip(lo,hi)];span=max(b-a for a,b in zip(lo,hi))
    captures=study/'age-captures';captures.mkdir();results=[]
    shots=[{'id':name,'camera':camera(center,span,direction,span*1.18),'background':'#EEE9DF','light':[-35,-25,0]} for name,direction in VIEWS]
    for stage,out,m,scale in items:
        config=out/'age-input.json';result=out/'age-godot.json'
        write(config,{'center':center,'span':span,'original_low':lo,'output':str(captures),'report':str(result),'shots':shots,
            'assets':[{'id':stage,'resource':'res://bare.glb','metrics':m,'display_scale':scale}]})
        run([GODOT,'--path',out/'godot','--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],out/'logs/age.log',dict(os.environ))
        data=read(result);assert data['passed'];results.append(data)
    sheet(study,study/'ages.jpg',3,[[(f'age-captures/{stage}--{view}.png',stage+' | altura visual normalizada') for stage in stages] for view,_ in VIEWS])
    write(study/'ages-review.json',{'passed':True,'godot':results,'display_scale':{stage:scale for stage,_,_,scale in items},'shots':shots,
        'captures_sha256':{p.name:sha(p) for p in captures.glob('*.png')},'meaning':'Stage is structural, not a calibrated age in years; common normalized-height cameras.'})


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--stage',choices=('generate','references','review','pilot-review','ages'),default='generate');parser.add_argument('--case')
    args=parser.parse_args();out=args.output.resolve();matrix=read(ROOT/'configs/verification/oak-growth-v1.json')
    if args.stage=='ages':review_ages(out);return
    cases=[(f'maduro-{seed}',matrix['preset'],seed) for seed in matrix['seeds']]
    cases += [(f'{stage}-3100',f'presets/oak-growth/0.1.0/{stage}.json',3100) for stage in ('joven','centenario')]
    for case,preset,seed in cases:
        if args.case and case!=args.case:continue
        if args.stage=='generate':execute_growth(ROOT/preset,seed,out/case)
        elif args.stage=='references':
            if not case.startswith('maduro-'):continue
            execute_branch_tree(ROOT/matrix['reference_definition'],{'profile':matrix['reference_profile'],'seeds':{'base':seed,'canopy':17,'paint':2718}},out/'references'/case)
        else:render(out,case,args.stage!='pilot-review' and case.startswith('maduro-'))

if __name__=='__main__':main()
