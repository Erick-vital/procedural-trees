#!/usr/bin/env python3
"""Construir y revisar una rama texturizada; no reanuda optimización del roble."""
import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import math
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.runner import execute_blueprint,BLENDER
from treegen.pine_painted_sample import canonical_hash
from review_pine_painted import read,write,run,camera,sha
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def inspect(path,expected_images):
    data=path.read_bytes();assert struct.unpack_from('<4sII',data)==(b'glTF',2,len(data))
    length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length]);binary=data[28+length:]
    assert not any('uri' in b for b in doc['buffers'])
    images=[]
    for im in doc.get('images',[]):
        assert 'uri' not in im and im['mimeType']=='image/png';view=doc['bufferViews'][im['bufferView']];offset=view.get('byteOffset',0)
        images.append(__import__('hashlib').sha256(binary[offset:offset+view['byteLength']]).hexdigest())
    assert set(images)==set(expected_images)
    for primitive in doc['meshes'][0]['primitives']:
        a=doc['accessors'][primitive['attributes']['TEXCOORD_0']];view=doc['bufferViews'][a['bufferView']];offset=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',8)
        assert a['componentType']==5126 and a['type']=='VEC2'
        assert all(math.isfinite(c) for i in range(a['count']) for c in struct.unpack_from('<2f',binary,offset+i*stride))
    for mat in doc['materials']:
        assert mat.get('doubleSided') is True
        if mat['name']=='Painted_Foliage':assert mat['alphaMode']=='MASK' and mat.get('alphaCutoff',.5)==.5
    return {'passed':True,'glb_sha256':sha(path),'embedded_images_sha256':images,'materials':[m['name'] for m in doc['materials']]}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--stage',choices=['all','generate','review'],default='all')
    p.add_argument('--twig-profile',choices=['original','fuller-v1'],default='original')
    a=p.parse_args();out=a.output.resolve()
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    if a.stage in ('all','generate'):
        out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
        m=execute_blueprint(ROOT/'blueprints/roble_copa_ancha/1.2.0.json',read(ROOT/'configs/verification/b3-v2.json')['cases'][0]['instance'],out/'source',render=False)
        expected=read(ROOT/'docs/evidence/blueprints/b3-revision/verification.json')['cases']['pilot']['glb_sha256'];assert m['glb_sha256']==expected
        run([os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',ROOT/'blender/oak_painted_sample.py','--',out,a.twig_profile],out/'logs/sample.log',env)
        report=read(out/'manifest.json');image_hash={name:info['sha256'] for name,info in report['resources'].items()}
        report['export_validation']={}
        for name in ('original','painted','wood','swatches'):
            images=[] if name=='original' else [image_hash['bark.png']] if name=='wood' else [image_hash['foliage.png']] if name=='swatches' else list(image_hash.values())
            report['export_validation'][name]=inspect(out/name/'branch.glb',images)
        report['source_lock']={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'blender/oak_painted_sample.py',ROOT/'src/treegen/oak_painted_sample.py',ROOT/'godot/review_painted_pine.gd',ROOT/'godot/painted_pine_asset.gd',ROOT/'godot/verify_oak.gd',*sorted((ROOT/'assets/roble-pintado/v0.2.0').glob('*'))] if p.is_file()}
        write(out/'manifest.json',report);print('Rama y cuatro exportaciones verificadas.',flush=True)
    if a.stage=='generate':return
    report=read(out/'manifest.json');assert all(sha(ROOT/p)==v for p,v in report['source_lock'].items())
    project=out/'godot';project.mkdir(exist_ok=False);captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','painted_pine_asset.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    entries=[]
    for name in ('original','painted','wood','swatches'):
        shutil.copy2(out/name/'branch.glb',project/(name+'.glb'))
        (project/(name+'.tscn')).write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="PackedScene" path="res://'+name+'.glb" id="1"]\n[ext_resource type="Script" path="res://painted_pine_asset.gd" id="2"]\n[node name="OakBranchSample" instance=ExtResource("1")]\nscript=ExtResource("2")\n')
        entries.append({'id':name,'resource':'res://'+name+'.tscn','metrics':report['variants'][name]['metrics']})
    bounds=report['variants']['original']['metrics']['bounds_blender'];center=[(a+b)/2 for a,b in zip(*bounds)];span=max(b-a for a,b in zip(*bounds))
    shots=[{'id':name,'camera':camera(center,span,d,span*1.25),'background':'#EEE9DF','light':[-35,-25,0]} for name,d in [('front',[0,-1,.1]),('side',[1,0,.1]),('perspective',[1,-1,.45]),('back',[-1,1,.3]),('top',[0,0,1]),('below',[1,-1,-.7])]]
    shots += [{'id':name,'camera':camera(center,span,[1,-1,.45],span*s),'background':'#EEE9DF','light':[-35,-25,0]} for name,s in [('medium',2.5),('far',5)]]
    # Acercamiento real a madera y tablero de las cuatro hojas.
    wood_bounds=report['variants']['wood']['metrics']['bounds_blender'];wood_center=[sum(v[k] for v in wood_bounds)/2 for k in range(3)]
    shots += [{'id':'bark-close','only':'wood','camera':camera(wood_center,span,[1,-1,.45],span*.6),'background':'#EEE9DF','light':[-35,-25,0]},
              {'id':'leaf-colors','only':'swatches','camera':camera([.5,0,1.1],3,[0,-1,0],2.7),'background':'#EEE9DF','light':[-35,-25,0]},
              {'id':'leaf-dark','only':'swatches','camera':camera([.5,0,1.1],3,[0,-1,0],2.7),'background':'#252A28','light':[-35,-25,0]}]
    write(out/'protocol.json',{'center':center,'span':span,'resolution':[900,900],'shots':shots})
    godot=os.environ.get('GODOT_BIN',GODOT);run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/godot-import.log',env)
    reviews=[]
    for index in range(0,4,2):
        config=out/f'review-input-{index}.json';result=out/f'review-report-{index}.json'
        write(config,{'output':str(captures),'report':str(result),'center':center,'span':span,'original_low':[0,0,0],'assets':entries[index:index+2],
            'shots':shots if index==0 else [s for s in shots if s.get('only') or s['id'] in ('front','side','perspective','top','below')]})
        run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_pine.gd','--',config,'--visual'],out/'logs'/f'godot-{index}.log',env);reviews.append(read(result))
        print('Godot lote '+str(index)+': OK',flush=True)
    report['godot']=reviews;report['capture_sha256']={p.name:sha(p) for p in captures.glob('*.png')};report['passed']=all(r['passed'] for r in reviews)
    write(out/'manifest.json',report)
    sheet(out,out/'comparison.jpg',2,[[(f'captures/{n}--{v}.png',n+' | '+v) for n in ('original','painted')] for v in ('front','side','perspective','top','below')])
    sheet(out,out/'materials.jpg',2,[[('captures/swatches--leaf-colors.png','Hojas | fondo claro'),('captures/swatches--leaf-dark.png','Hojas | fondo oscuro')],[('captures/wood--perspective.png','Corteza | rama'),('captures/wood--bark-close.png','Corteza | acercamiento')]])
    cells=''.join('<figure><a href="captures/'+n+'"><img width="300" src="captures/'+n+'"></a><figcaption>'+n+'</figcaption></figure>' for n in sorted(report['capture_sha256']))
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Roble · rama pintada</title><style>body{font:16px sans-serif;background:#eee}main{display:flex;flex-wrap:wrap}</style><h1>Roble · muestra de pintura</h1><p>Geometría sin optimizar. Dirección aprobada; aplicación a la rama pendiente de revisión.</p><main>'+cells+'</main>')
    assert report['passed'];print('Muestra lista: '+str(len(report['capture_sha256']))+' capturas.',flush=True)

if __name__=='__main__':main()
