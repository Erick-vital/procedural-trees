#!/usr/bin/env python3
"""R2: encuadre auxiliar del receptor de sombras bajo la rama aislada."""
import argparse
from pathlib import Path
import os
import math
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'src')]
from review_pine_painted import read,write,sha,camera
from verify_branch_space import run
from verify_foliage_unit import GODOT
from verify_branch_simplification import compare_images
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True,type=Path);p.add_argument('--label',default='shadows-framed')
    a=p.parse_args();study=a.study.resolve();label=a.label
    if not label.replace('-','').isalnum():raise ValueError('Etiqueta inválida')
    captures=study/'captures'/label;captures.mkdir()
    config=read(study/'color-input.json');metrics=config['assets'][0]['metrics'];lo,hi=metrics['bounds_blender']
    vertices=[v for mesh in read(study/'input.json')['variants']['full']['wood']+read(study/'input.json')['variants']['full']['foliage'] for v in mesh['vertices']]
    floor=lo[2]-.15;shots=[]
    for i,light in enumerate(([-35,-25,0],[-35,-90,0],[-35,155,0])):
        pitch,yaw=map(math.radians,light[:2])
        direction=[-math.sin(yaw)*math.cos(pitch),math.cos(yaw)*math.cos(pitch),math.sin(pitch)]
        projected=[[v[k]+direction[k]*(floor-v[2])/direction[2] for k in range(3)] for v in vertices]
        points=vertices+projected
        low=[min(v[k] for v in points) for k in range(3)];high=[max(v[k] for v in points) for k in range(3)]
        center=[(a+b)/2 for a,b in zip(low,high)];span=max(b-a for a,b in zip(low,high))
        shots.append({'id':f'ground-{i}','camera':camera(center,span,[1,-1,1.5],span*1.35),
                      'background':'#EEE9DF','light':light,'receiver':True})
    config.update(output=str(captures),report=str(study/(label+'-godot.json')),shots=shots,original_low=lo)
    input_path=study/(label+'-input.json');write(input_path,config)
    env=dict(os.environ,XDG_DATA_HOME=str(study/'xdg/data'),XDG_CONFIG_HOME=str(study/'xdg/config'),XDG_CACHE_HOME=str(study/'xdg/cache'))
    run([GODOT,'--path',study/'godot','--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',input_path,'--visual'],
        study/'logs'/(label+'.log'),env)
    assert read(study/(label+'-godot.json'))['passed']
    result={'source_sha256':sha(__file__),'comparisons':{s['id']:compare_images(captures/('full--'+s['id']+'.png'),captures/('simple--'+s['id']+'.png')) for s in shots},
            'captures_sha256':{p.name:sha(p) for p in captures.glob('*.png')}}
    write(study/(label+'-verification.json'),result)
    sheet(study,study/(label+'.jpg'),2,[[(f'captures/{label}/{name}--{s["id"]}.png',name+' '+s['id']) for name in ('full','simple')] for s in shots])
    print(result['comparisons'],flush=True)


if __name__=='__main__':main()
