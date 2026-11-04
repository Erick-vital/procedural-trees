#!/usr/bin/env python3
"""Madera visible real y ventanas sobre tronco/bifurcaciones de OF9/OF10."""
import argparse
import math
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from review_pine_painted import read,write,sha
from verify_branch_space import run
from verify_foliage_unit import GODOT
from foliage_evidence import sheet
from oak_foliage_chain_masks import pixels
from treegen.oak_growth import sample


def roi_for(shot,size,points,radius):
    cam=shot['camera'];x,y,_=cam['basis_columns'];scale=cam['ortho_scale'];w,h=size
    cells=set();rp=radius*h/scale
    for p in points:
        d=[a-b for a,b in zip(p,cam['location'])]
        px=w/2+sum(a*b for a,b in zip(d,x))*h/scale
        py=h/2-sum(a*b for a,b in zip(d,y))*h/scale
        for iy in range(max(0,int(py-rp)),min(h,int(py+rp)+1)):
            for ix in range(max(0,int(px-rp)),min(w,int(px+rp)+1)):
                if (ix-px)**2+(iy-py)**2<=rp*rp:cells.add(iy*w+ix)
    return cells


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);a=p.parse_args();study=a.study.resolve()
    project=study/'godot';out=study/'wood-masks';out.mkdir(exist_ok=True)
    harness=ROOT/'godot/review_oak_wood_masks.gd';shutil.copy2(harness,project/harness.name)
    shots=[{**s,'background':'#FFFFFF','receiver':False} for s in read(study/'review.json')['protocols']['tree'] if s['id'] in ('front','side','perspective','top')]
    env=dict(os.environ,XDG_DATA_HOME=str(study/'xdg/data'),XDG_CONFIG_HOME=str(study/'xdg/config'),XDG_CACHE_HOME=str(study/'xdg/cache'))
    reports=[]
    for name in ('bare','baseline','painted'):
        config=read(study/(name+'-review-input.json'));report=study/(name+'-wood-mask-godot.json');config.update(output=str(out),report=str(report),shots=shots)
        path=study/(name+'-wood-mask-input.json');write(path,config)
        run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://'+harness.name,'--',path,'--visual'],study/'logs'/(name+'-wood-mask.log'),env)
        r=read(report);assert r['passed'];reports.append(r)
    s=read(study/'o5-structure.json');height=s['preset']['height_m']
    points=[sample(b['points'],t)[0] for b in s['branches'] if b['order']==0 for t in (0.,.15,.3,.45,.6,.75,.9)]
    points.extend(sample(b['points'],t)[0] for b in s['branches'] if b['order']==1 for t in (0.,.10,.20,.30))
    metrics={}
    for shot in shots:
        view=shot['id'];size,bare=pixels(out/f'bare--{view}.png');roi=roi_for(shot,size,points,height*.045)
        denom=sum(bool(bare[i]) for i in roi);row={}
        for name in ('baseline','painted'):
            dims,data=pixels(out/f'{name}--{view}.png');assert dims==size
            visible=sum(bool(data[i]) and bool(bare[i]) for i in roi)
            row[name]={'central_visible_wood_pixels':visible,'central_reference_wood_pixels':denom,
                       'central_wood_visibility_fraction':visible/max(1,denom),'whole_visible_wood_pixels':sum(bool(v) for v in data)}
        row['central_visible_wood_ratio']=row['painted']['central_visible_wood_pixels']/max(1,row['baseline']['central_visible_wood_pixels'])
        metrics[view]=row
    sheet(study,study/'wood-masks.jpg',3,[[(f'wood-masks/{n}--{v}.png',label+' | '+v) for n,label in [('bare','O5'),('baseline','OF9'),('painted','OF10')]] for v in ('front','side','perspective','top')])
    write(study/'wood-mask-review.json',{'passed':True,'godot':reports,'metrics':metrics,'shots':shots,
        'roi':{'points_blender_m':points,'radius_m':height*.045,'method':'union of projected circles around trunk and inner primary stations; evaluate only bare-wood pixels'},
        'captures_sha256':{p.name:sha(p) for p in out.glob('*.png')},'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),harness)},
        'scope':'unshaded alpha-tested wood occlusion diagnostic; not artistic approval or guarantee for all angles'})
    print(metrics)

if __name__=='__main__':main()
