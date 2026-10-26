#!/usr/bin/env python3
"""Generar, repetir y comparar madera sin ramillas directas de la primaria."""
import argparse
from collections import Counter
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.runner import BLENDER
from review_pine_painted import read,write,run,sha
from verify_foliage_unit import GODOT
from oak_painted_sample import inspect
from oak_sample_evidence import channel
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'artifacts/roble-pintado/rama-muestra-01')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();source=a.source.resolve();out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    for name in ('after','repeat'):
        target=out/name;target.mkdir()
        run([os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1',
            '--python',ROOT/'blender/oak_wood_hierarchy.py','--',source,target],out/'logs'/(name+'.log'),env)
    before=read(source/'manifest.json');after=read(out/'after/manifest.json')
    assert after['passed'] and len(after['kept_support_ids'])==13 and len(after['removed_support_ids'])==19
    assert sha(out/'after/wood/branch.glb')==sha(out/'repeat/wood/branch.glb')
    validation=inspect(out/'after/wood/branch.glb',[before['resources']['bark.png']['sha256']])
    old=Counter(tuple(tuple(v) for v in t) for t in channel(source/'wood/branch.glb','Painted_Bark'))
    new=Counter(tuple(tuple(v) for v in t) for t in channel(out/'after/wood/branch.glb','Painted_Bark'))
    assert not (new-old) and sum((old-new).values())==19*8
    original_tris=before['variants']['wood']['metrics']['triangles'];tris=after['variants']['wood']['metrics']['triangles']
    assert original_tris-tris==152
    project=out/'godot';project.mkdir();captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','painted_pine_asset.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    entries=[]
    for label,base,metrics in [('before',source,before['variants']['wood']['metrics']),('after',out/'after',after['variants']['wood']['metrics'])]:
        shutil.copy2(base/'wood/branch.glb',project/(label+'.glb'))
        entries.append({'id':label,'resource':'res://'+label+'.glb','metrics':metrics})
    godot=os.environ.get('GODOT_BIN',GODOT)
    run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/import.log',env)
    protocol=read(source/'protocol.json')
    shots=[dict(s) for s in protocol['shots'] if not s.get('only') or s['only']=='wood']
    for s in shots:s.pop('only',None)
    config=out/'review-input.json';result=out/'review-report.json'
    write(config,{'output':str(captures),'report':str(result),'center':protocol['center'],'span':protocol['span'],'original_low':[0,0,0],'assets':entries,'shots':shots})
    run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_pine.gd','--',config,'--visual'],out/'logs/review.log',env)
    review=read(result);assert review['passed']
    for name,views in [('comparison',('bark-close','perspective','below')),('all-views',tuple(s['id'] for s in shots)),('detail',('bark-close',))]:
        sheet(out,out/(name+'.jpg'),2,[[(f'captures/{label}--{view}.png',title+' | '+view) for label,title in [('before','Antes: 32 ramillas'),('after','Propuesta: 13 ramillas')]] for view in views])
    sources=[Path(__file__),ROOT/'blender/oak_wood_hierarchy.py',ROOT/'blender/oak_painted_sample.py',ROOT/'blender/pine_painted_sample.py',ROOT/'blender/foliage_lab.py',ROOT/'src/treegen/oak_painted_sample.py',ROOT/'src/treegen/foliage_molds.py',ROOT/'scripts/oak_painted_sample.py',ROOT/'scripts/oak_sample_evidence.py',ROOT/'scripts/review_pine_painted.py',ROOT/'scripts/foliage_evidence.py',ROOT/'godot/review_painted_pine.gd',ROOT/'godot/verify_oak.gd']
    write(out/'audit.json',{'passed':True,'profile':after['profile'],'before':str(source.relative_to(ROOT)),'after':str((out/'after').relative_to(ROOT)),
        'triangles_before':original_tris,'triangles_after':tris,'triangles_saved':152,'kept_support_ids':after['kept_support_ids'],
        'removed_support_ids':after['removed_support_ids'],'retained_geometry_and_normals_exact':True,'repeat_glb_identical':True,
        'export_validation':validation,'real_captures':len(review['captures']),'capture_sha256':{f.name:sha(f) for f in captures.glob('*.png')},
        'source_sha256':{str(f.relative_to(ROOT)):sha(f) for f in sources}})
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Roble · jerarquía de ramillas</title><style>body{font:18px sans-serif;background:#eee9df;margin:30px}img{width:100%;max-width:1100px}</style><h1>Madera: quitar ramillas directas de la rama gruesa</h1><p>Izquierda: 32 ramillas. Derecha: 13 ramillas nacidas de secundarias. Mismos grosores originales, pintura, cámaras y luz. Madera: 720 → 568 tris (−152; −21,1 %).</p><a href="detail.jpg"><img src="detail.jpg"></a><h2>Comparación</h2><img src="comparison.jpg"><h2>Todas las vistas</h2><img src="all-views.jpg">')
    print('Madera: '+str(original_tris)+' → '+str(tris)+' tris; repetición idéntica; '+str(len(review['captures']))+' capturas reales.',flush=True)


if __name__=='__main__':main()
