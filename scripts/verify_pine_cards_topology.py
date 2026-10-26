#!/usr/bin/env python3
"""Comparar topología con idéntico ajuste de anchura, cámaras y pintura."""
import argparse
import os
from pathlib import Path
import sys
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.runner import BLENDER
from verify_foliage_unit import GODOT
from review_pine_painted import run,read,write,sha

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analyze-only',action='store_true');p.add_argument('--study',required=True,type=Path);args=p.parse_args();out=args.study.resolve()
env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
def command(name,cmd):
    run(cmd,out/'logs'/(name+'.log'),env);print(name+': OK',flush=True)
if '--analyze-only' not in sys.argv:
    command('topology-reference',[os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',ROOT/'blender/pine_cards_reference.py','--',out])
    godot=os.environ.get('GODOT_BIN',GODOT);project=out/'godot'
    command('topology-import',[godot,'--headless','--path',project,'--editor','--import'])
    r=read(out/'verification.json');shots=read(out/'protocol.json')['shots'];entries=[]
    for row in r['matrix']['cases']:
        n=row['id'];entries.append({'id':'topology-'+n,'resource':'res://topology-'+n+'.glb','metrics':read(out/('topology-'+n+'-metrics.json'))})
    reports=[]
    for i in range(0,4,2):
        config=out/f'topology-input-{i}.json';result=out/f'topology-report-{i}.json'
        write(config,{'output':str(out/'captures'),'report':str(result),'span':12,'center':[0,0,6],'original_low':[0,0,0],'assets':entries[i:i+2],'shots':shots})
        command('topology-godot-'+str(i),[godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_pine.gd','--',config,'--visual']);reports.append(read(result))
else:
    r=read(out/'verification.json');shots=read(out/'protocol.json')['shots']
    reports=[read(out/f'topology-report-{i}.json') for i in (0,2)]
rows={}
for row in r['matrix']['cases']:
    n=row['id'];rows[n]={}
    for shot in shots:
        view=shot['id'];a=Image.open(out/f'captures/topology-{n}--{view}.png').convert('RGB');b=Image.open(out/f'captures/new-{n}--{view}.png').convert('RGB')
        diffs=list(ImageChops.difference(a,b).get_flattened_data());changed=sum(max(v)>20 for v in diffs)
        rows[n][view]={'pixels_rgb_delta_gt20':changed,'fraction':changed/(900*900),'maximum_rgb_delta':max(max(v) for v in diffs)}
        def mask(im):
            delta=ImageChops.difference(im,Image.new('RGB',im.size,im.getpixel((0,0))));red,green,blue=delta.split()
            return ImageChops.lighter(ImageChops.lighter(red,green),blue).point(lambda x:255 if x>20 else 0)
        am,bm=mask(a),mask(b)
        rows[n][view]['silhouette_xor_pixels']=ImageChops.difference(am,bm).histogram()[255]
        rows[n][view]['reference_covered_pixels']=am.histogram()[255]
mask_passed=all(v['silhouette_xor_pixels']/max(1,v['reference_covered_pixels'])<=.002 for row in rows.values() for v in row.values())
write(out/'topology-comparison.json',{'passed':all(t['passed'] for t in reports) and mask_passed,'maximum_mask_difference_fraction':.002,'cases':rows,
    'note':'Misma anchura sqrt(.9) en referencia de 12 tris y cruzadas de 6; ninguna diferencia se atribuye al estrechamiento.',
    'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'blender/pine_cards_reference.py']},
    'capture_sha256':{p.name:sha(p) for p in sorted((out/'captures').glob('topology-*.png'))}})
from foliage_evidence import sheet
sheet(out,out/'topology-comparison.jpg',4,[[(f'captures/{kind}-{row["id"]}--{v}.png',kind+' '+row['id']+' | '+v) for row in r['matrix']['cases']] for v in ('front','perspective','top') for kind in ('topology','new')])
assert mask_passed,'Diferencia de silueta mayor de .2 % del área de referencia'
print('Comparación aislada: 36 pares; métricas y lámina guardadas.',flush=True)
