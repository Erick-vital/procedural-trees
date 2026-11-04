#!/usr/bin/env python3
"""J1: revisar madera joven O5 y comparar porte con maduro, sin nueva copa."""
import argparse
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.oak_growth_runner import execute_growth
from review_pine_painted import read,write,sha,camera,run
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def generate(out):
    out.mkdir(parents=True,exist_ok=False)
    rows={}
    for seed in range(3100,3104):
        name=f'joven-{seed}'
        execute_growth(ROOT/'presets/oak-growth/0.5.0/joven.json',seed,out/name)
        rows[name]=read(out/name/'manifest.json')
        print(name+': madera verificada',flush=True)
    execute_growth(ROOT/'presets/oak-growth/0.5.0/joven.json',3100,out/'repeat-3100')
    execute_growth(ROOT/'presets/oak-growth/0.5.0/maduro.json',3100,out/'maduro-3100')
    repeated=read(out/'repeat-3100/manifest.json')
    checks={name:all(m['checks'].values()) for name,m in rows.items()}
    for variant in ('bare','scaffold'):
        checks[variant+'-repeat']=rows['joven-3100']['variants'][variant]['glb_sha256']==repeated['variants'][variant]['glb_sha256']
    history=read(ROOT/'docs/evidence/oak-growth/o5/verification.json')['cases']
    for name in ('joven-3100','maduro-3100'):
        m=read(out/name/'manifest.json')
        checks[name+'-historical']=all(m['variants'][v]['glb_sha256']==history[name]['glb_sha256'][v] for v in ('bare','scaffold'))
    checks['distinct-young']=len({m['variants']['bare']['glb_sha256'] for m in rows.values()})==4
    result={'passed':all(checks.values()),'checks':checks,'cases':{n:{'triangles':m['variants']['bare']['metrics']['triangles'],'architecture':m['architecture'],'preset':m['preset'],'glb_sha256':m['variants']['bare']['glb_sha256']} for n,m in rows.items()},
            'wood_only':True,'full_tree_foliage_integrated':False,'artistic_acceptance':'pending_user'}
    write(out/'verification.json',result)
    assert result['passed'],checks


def review(out):
    result=read(out/'verification.json');assert result['passed']
    project,captures,logs=[out/n for n in ('godot','captures','logs')]
    for p in (project,captures,logs):p.mkdir(exist_ok=False)
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    entries=[]
    for name in (*result['cases'],'maduro-3100'):
        m=read(out/name/'manifest.json')
        assert all(sha(ROOT/p)==h for p,h in m['source_inventory'].items())
        for variant in ('bare','scaffold'):
            identifier=name+'-'+variant
            path=out/name/variant/'tree.glb'
            assert sha(path)==m['variants'][variant]['glb_sha256']
            shutil.copy2(path,project/(identifier+'.glb'))
            entries.append({'id':identifier,'resource':'res://'+identifier+'.glb','metrics':m['variants'][variant]['metrics']})
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    run([GODOT,'--headless','--path',project,'--editor','--import'],logs/'import.log',env)
    reports=[];protocol=[]
    # Encuadre métrico común entre todos los jóvenes; otra cámara para el maduro.
    # La comparación normalizada usa cámaras relativas, nunca escala anisótropa.
    for family in ('young','mature','normalized-young'):
        group=[e for e in entries if e['id'].startswith('joven' if family!='mature' else 'maduro')]
        if family=='normalized-young':group=[e for e in group if e['id'].startswith('joven-3100')]
        bounds=[e['metrics']['bounds_blender'] for e in group]
        lo=[min(b[0][k] for b in bounds) for k in range(3)];hi=[max(b[1][k] for b in bounds) for k in range(3)]
        center=[(a+b)/2 for a,b in zip(lo,hi)]
        # Los encuadres de comparación muestran el árbol a igual altura nominal.
        h=12 if family=='mature' else 5
        span=max(hi[k]-lo[k] for k in range(3));scale=1.9*h if family!='young' else span*1.2
        shots=[{'id':family+'-'+name,'camera':camera(center,span,d,scale),'background':'#EEE9DF','light':[-35,-25,0]} for name,d in
               [('front',[0,-1,.1]),('side',[1,0,.1]),('perspective',[1,-1,.4]),('top',[0,0,1])]]
        config,report=out/(family+'-input.json'),out/(family+'-godot.json')
        write(config,{'output':str(captures),'report':str(report),'center':center,'span':span,'original_low':lo,'assets':group,'shots':shots})
        protocol.append(read(config))
        run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],logs/(family+'.log'),env)
        r=read(report);assert r['passed'];reports.append(r)
    sheet(out,out/'wood.jpg',4,[[(f'captures/joven-{seed}-{variant}--young-{view}.png',f'Joven{seed} | {variant} | {view}') for seed in range(3100,3104)] for variant in ('bare','scaffold') for view in ('front','side','perspective','top')])
    sheet(out,out/'age-comparison.jpg',2,[[(f'captures/{name}-bare--{family}-{view}.png',f'{name} | {view} | altura normalizada') for name,family in [('joven-3100','normalized-young'),('maduro-3100','mature')]] for view in ('front','side','perspective','top')])
    write(out/'review.json',{'passed':True,'reports':reports,'protocol':protocol,'captures_sha256':{p.name:sha(p) for p in captures.glob('*.png')},'visual_review':'pending_agent'})
    print('Madera Godot:',len(list(captures.glob('*.png'))),'capturas',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--stage',choices=('generate','review'),required=True);a=p.parse_args()
    (generate if a.stage=='generate' else review)(a.output.resolve())

if __name__=='__main__':main()
