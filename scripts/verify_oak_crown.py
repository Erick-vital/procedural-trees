#!/usr/bin/env python3
"""O2: misma seed y madurez; comparación antes/después desnuda y primarias."""
import argparse
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.oak_growth_runner import execute_growth
from review_pine_painted import read,write,sha,camera
from verify_branch_space import run
from verify_foliage_unit import GODOT
from foliage_evidence import sheet
from verify_oak_growth import VIEWS,review_ages

MATRIX=read(ROOT/'configs/verification/oak-crown-v2.json')
CASES=[('maduro',seed) for seed in MATRIX['seeds']]+[(stage,MATRIX['age_controls']['seed']) for stage in MATRIX['age_controls']['stages'] if stage!='maduro']


def review(study,case):
    out=study/case;project=out/'godot';project.mkdir();cap=out/'captures';cap.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):
        shutil.copy2(ROOT/'godot'/name,project/name)
    path=project/'review_painted_pine.gd';text=path.read_text().replace('im.get_width()==1254 and im.get_height()==1254',
        '(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)')
    # La revisión de edades reutiliza este adaptador, con escala de presentación explícita.
    text=text.replace('\t\tfor shot in config.shots:',"\t\tasset.scale=Vector3.ONE*float(item.get('display_scale',1.0))\n\t\tfor shot in config.shots:");path.write_text(text)
    entries=[]
    for label,folder in [('before',study/'before'/case),('after',out)]:
        m=read(folder/'manifest.json');assert m['status']=='completed'
        for mode,item in m['variants'].items():
            name=label+'-'+mode;shutil.copy2(folder/mode/'tree.glb',project/(name+'.glb'))
            if label=='after' and mode=='bare':shutil.copy2(folder/mode/'tree.glb',project/'bare.glb')
            entries.append({'id':name,'resource':'res://'+name+'.glb','metrics':item['metrics']})
    lo=[min(e['metrics']['bounds_blender'][0][k] for e in entries) for k in range(3)]
    hi=[max(e['metrics']['bounds_blender'][1][k] for e in entries) for k in range(3)]
    center=[(a+b)/2 for a,b in zip(lo,hi)];span=max(b-a for a,b in zip(lo,hi))
    shots=[{'id':name,'camera':camera(center,span,direction,span*1.15),'background':'#EEE9DF','light':[-35,-25,0]} for name,direction in VIEWS]
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    run([GODOT,'--headless','--path',project,'--editor','--import'],out/'logs/godot-import.log',env)
    results=[]
    for entry in entries:
        name=entry['id'];config=out/(name+'-review-input.json');result=out/(name+'-godot.json')
        write(config,{'output':str(cap),'report':str(result),'center':center,'span':span,'original_low':lo,'shots':shots,'assets':[entry]})
        run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],out/'logs'/('godot-'+name+'.log'),env)
        r=read(result);assert r['passed'];results.append(r)
    for mode in ('bare','scaffold'):
        sheet(out,out/(mode+'-comparison.jpg'),2,[[(f'captures/{label}-{mode}--{view}.png',label+' | '+case+' | '+view) for label in ('before','after')] for view,_ in VIEWS])
    write(out/'review.json',{'passed':True,'godot':results,'shots':shots,'captures_sha256':{p.name:sha(p) for p in cap.glob('*.png')},
        'visual_review':'pending_agent','artist_acceptance':'pending_user','display_scale':1.})
    print(case,'16 capturas',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--stage',choices=('generate','review','ages'),default='generate');p.add_argument('--case');a=p.parse_args();study=a.output.resolve()
    if a.stage=='ages':review_ages(study);return
    for stage,seed in CASES:
        case=f'{stage}-{seed}'
        if a.case and a.case!=case:continue
        if a.stage=='generate':
            for version,folder in [('0.1.0',study/'before'/case),('0.2.0',study/case)]:execute_growth(ROOT/Path(MATRIX['before' if version=='0.1.0' else 'after']).parent/(stage+'.json'),seed,folder)
        else:review(study,case)

if __name__=='__main__':main()
