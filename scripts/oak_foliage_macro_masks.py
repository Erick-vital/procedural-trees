#!/usr/bin/env python3
"""Diagnóstico de cobertura/continuidad proyectada OF4/OF5 en Godot."""
import argparse
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from review_pine_painted import read,write,sha
from verify_branch_space import run
from verify_foliage_unit import GODOT
from foliage_evidence import sheet
from oak_foliage_chain_masks import pixels,describe


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);a=p.parse_args();study=a.study.resolve()
    project=study/'godot';mask=study/'masks';mask.mkdir()
    harness=ROOT/'godot/review_oak_peripheral_masks.gd';shutil.copy2(harness,project/harness.name)
    shots=[{**s,'background':'#FFFFFF','receiver':False} for s in read(study/'review.json')['protocols']['tree'] if s['id'] in ('front','side','perspective','top')]
    env=dict(os.environ,XDG_DATA_HOME=str(study/'xdg/data'),XDG_CONFIG_HOME=str(study/'xdg/config'),XDG_CACHE_HOME=str(study/'xdg/cache'))
    reports=[]
    for name in ('baseline','painted'):
        config=read(study/(name+'-review-input.json'));report=study/(name+'-mask-godot.json');config.update(output=str(mask),report=str(report),shots=shots)
        path=study/(name+'-mask-input.json');write(path,config)
        run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://'+harness.name,'--',path,'--visual'],study/'logs'/(name+'-mask.log'),env)
        r=read(report);assert r['passed'];reports.append(r)
    metrics={}
    for view in ('front','side','perspective','top'):
        metrics[view]={}
        for name in ('baseline','painted'):
            size,data=pixels(mask/f'{name}--{view}.png');metrics[view][name]=describe(data,size)
    sheet(study,study/'masks.jpg',2,[[(f'masks/{n}--{v}.png',label+' | '+v) for n,label in [('baseline','OF4'),('painted','OF5')]] for v in ('front','side','perspective','top')])
    write(study/'mask-review.json',{'passed':True,'godot':reports,'metrics':metrics,'shots':shots,'captures_sha256':{p.name:sha(p) for p in mask.glob('*.png')},
        'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),harness)},
        'scope':'visible foliage projection; white wood retains real occlusion; no physical crown volume or artistic acceptance'})
    print(metrics)

if __name__=='__main__':main()
