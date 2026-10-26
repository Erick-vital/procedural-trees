#!/usr/bin/env python3
"""Comparar radios de ramillas con cámaras compartidas y auditar repetición."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts')]
from review_pine_painted import read,write,run,sha
from verify_foliage_unit import GODOT
from foliage_evidence import sheet
from oak_sample_evidence import channel


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','repeat','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();before=a.before.resolve();after=a.after.resolve();repeat=a.repeat.resolve();out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    project=out/'godot';project.mkdir();(out/'logs').mkdir();(out/'captures').mkdir()
    reports=[read(s/'manifest.json') for s in (before,after,repeat)]
    assert all(r['passed'] for r in reports)
    assert reports[1]['twig_profile']=='fuller-v1'
    assert reports[0]['reference']['source_subset_sha256']==reports[1]['reference']['source_subset_sha256']
    assert reports[0]['resources']==reports[1]['resources']
    assert sha(before/'placements.json')==sha(after/'placements.json')
    repeated={n:sha(after/n/'branch.glb')==sha(repeat/n/'branch.glb') for n in ('original','painted','wood','swatches')}
    assert all(repeated.values())
    assert sha(before/'original/branch.glb')==sha(after/'original/branch.glb')
    assert sha(before/'swatches/branch.glb')==sha(after/'swatches/branch.glb')
    for name in ('painted','wood'):
        assert reports[0]['variants'][name]['metrics']['triangles']==reports[1]['variants'][name]['metrics']['triangles']
    assert channel(before/'painted/branch.glb','Painted_Foliage')==channel(after/'painted/branch.glb','Painted_Foliage')
    old=Counter(tuple(tuple(v) for v in t) for t in channel(before/'wood/branch.glb','Painted_Bark'))
    new=Counter(tuple(tuple(v) for v in t) for t in channel(after/'wood/branch.glb','Painted_Bark'))
    # Cada soporte conserva 8 tris; solo esos 32 tubos cambian posición/normales.
    changed=sum((old-new).values());expected=reports[1]['reference']['support_count']*8
    assert changed==expected and sum((new-old).values())==expected
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','painted_pine_asset.gd'):
        shutil.copy2(ROOT/'godot'/name,project/name)
    protocol=read(before/'protocol.json');entries={}
    for variant in ('painted','wood'):
        entries[variant]=[]
        for label,source,r in zip(('before','after'),(before,after),reports):
            name=variant+'-'+label
            shutil.copy2(source/variant/'branch.glb',project/(name+'.glb'))
            (project/(name+'.tscn')).write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="PackedScene" path="res://'+name+'.glb" id="1"]\n[ext_resource type="Script" path="res://painted_pine_asset.gd" id="2"]\n[node name="OakTwigs" instance=ExtResource("1")]\nscript=ExtResource("2")\n')
            entries[variant].append({'id':name,'resource':'res://'+name+'.tscn','metrics':r['variants'][variant]['metrics']})
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    godot=os.environ.get('GODOT_BIN',GODOT)
    run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/import.log',env)
    reviewed={}
    for variant in ('wood','painted'):
        shots=[dict(s) for s in protocol['shots'] if (s.get('only')=='wood' or not s.get('only')) and (variant=='wood' or not s.get('only'))]
        for s in shots:s.pop('only',None)
        config=out/(variant+'-input.json');result=out/(variant+'-report.json')
        write(config,{'output':str(out/'captures'),'report':str(result),'center':protocol['center'],'span':protocol['span'],
            'original_low':[0,0,0],'assets':entries[variant],'shots':shots})
        run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_pine.gd','--',config,'--visual'],out/'logs'/(variant+'.log'),env)
        reviewed[variant]=read(result);assert reviewed[variant]['passed']
    for variant,views in [('wood',('bark-close','perspective','below')),('painted',('front','perspective','below'))]:
        sheet(out,out/(variant+'.jpg'),2,[[(f'captures/{variant}-{label}--{view}.png',title+' | '+view) for label,title in [('before','Antes'),('after','Ramillas más gruesas')]] for view in views])
    captures={f.name:sha(f) for f in (out/'captures').glob('*.png')}
    audit={'passed':True,'before':str(before.relative_to(ROOT)),'after':str(after.relative_to(ROOT)),
        'repeat':str(repeat.relative_to(ROOT)),'repeated_glb_identical':repeated,'triangles_before':reports[0]['variants']['painted']['metrics']['triangles'],
        'triangles_after':reports[1]['variants']['painted']['metrics']['triangles'],'changed_support_triangles':changed,
        'unchanged_branch_triangles_and_normals':sum((old&new).values()),'leaf_geometry_normals_placements_exact':True,
        'resources_exact':True,'profile':reports[1]['reference']['twig_geometry_spec'],'real_captures':len(captures),'captures_sha256':captures,
        'source_sha256':{str(f.relative_to(ROOT)):sha(f) for f in [Path(__file__),ROOT/'blender/oak_painted_sample.py',ROOT/'src/treegen/oak_painted_sample.py',ROOT/'scripts/oak_painted_sample.py',ROOT/'scripts/oak_sample_evidence.py',ROOT/'scripts/review_pine_painted.py',ROOT/'scripts/foliage_evidence.py',ROOT/'godot/review_painted_pine.gd',ROOT/'godot/verify_oak.gd',ROOT/'godot/painted_pine_asset.gd']}}
    write(out/'audit.json',audit)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Roble · ramillas</title><style>body{font:18px sans-serif;background:#eee9df;margin:30px}img{width:100%;max-width:1000px}</style><h1>Ramillas: antes / propuesta</h1><p>Izquierda: anterior. Derecha: base +25 %, punta al 50 % del radio de base. 1104 → 1104 tris. Misma pintura, follaje, cámaras y luz.</p><h2>Madera</h2><a href="wood.jpg"><img src="wood.jpg"></a><h2>Con follaje</h2><a href="painted.jpg"><img src="painted.jpg"></a>')
    print(json.dumps({'passed':True,'triangles':audit['triangles_after'],'captures':len(captures)}))


if __name__=='__main__':main()
