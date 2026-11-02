#!/usr/bin/env python3
"""T4: normales locales, importaciones Blender/Godot y matriz visual acotada."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from PIL import Image,ImageChops,ImageDraw,ImageStat
from build_canopy_normals import ROOT,build,sha,write
from treegen.runner import BLENDER
from review_pine_painted import run
from verify_foliage_unit import GODOT


def locked(output):
    manifest=json.loads((output/'manifest.json').read_text())
    for path,h in {**manifest['source_lock'],**manifest['input_lock']}.items():
        if sha(ROOT/path)!=h:raise ValueError('Fuente/entrada modificada: '+path)
    for path,h in manifest['files_sha256'].items():
        if sha(output/path)!=h:raise ValueError('Archivo modificado: '+path)
    return manifest


def review(output):
    manifest=locked(output);project=output/'godot';logs=output/'logs';logs.mkdir(exist_ok=True)
    run([os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1',
         '--python',ROOT/'blender/verify_canopy_normals.py','--',output/'blender-input.json'],logs/'blender.log',os.environ)
    godot=os.environ.get('GODOT_BIN',GODOT)
    run([godot,'--headless','--path',project,'--editor','--import'],logs/'import.log',os.environ)
    for path in project.glob('*.png.import'):
        s=path.read_text();s=re.sub(r'mipmaps/generate=(true|false)','mipmaps/generate=true',s)
        s=re.sub(r'process/fix_alpha_border=(true|false)','process/fix_alpha_border=false',s)
        s=re.sub(r'compress/mode=\d+','compress/mode=0',s);path.write_text(s)
    run([godot,'--headless','--path',project,'--editor','--import'],logs/'reimport.log',os.environ)
    captures=output/'captures';captures.mkdir(exist_ok=True);reports={};checks={}
    for scope in ('branch','pilot'):
        for season in ('summer','autumn'):
            name=scope+'-'+season;folder=captures/name;folder.mkdir(exist_ok=True)
            run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_canopy_normals.gd','--',folder,scope,season],logs/(name+'.log'),os.environ)
            reports[name]=json.loads((folder/'godot-report.json').read_text());checks[name+'-godot']=reports[name]['passed']
            for variant in ('n35','n65'):
                checks[name+'-'+variant+'-six-masks-exact']=all(ImageChops.difference(
                    Image.open(folder/f'{scope}-original-{season}-mask-v{view}.png').convert('RGB'),
                    Image.open(folder/f'{scope}-{variant}-{season}-mask-v{view}.png').convert('RGB')).getbbox() is None for view in range(6))
            print(name+': importación/normales/material estándar/capturas OK',flush=True)
    folder=captures/'viewer';folder.mkdir(exist_ok=True)
    run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_canopy_normals.gd','--',folder,'viewer','summer'],logs/'viewer.log',os.environ)
    reports['viewer']=json.loads((folder/'godot-report.json').read_text());checks['viewer-controls']=reports['viewer']['passed']
    metrics={}
    # Selección: todas las orientaciones/luces cercanas y las tres distancias.
    for scope in ('branch','pilot'):
        for season in ('summer','autumn'):
            folder=captures/(scope+'-'+season)
            for title,shots in [('orientations',[(f'l{l}-v{v}-d0',f'luz {l} | vista {v}') for l in range(3) for v in range(6)]),
                                ('distances',[(f'l{l}-v2-d{d}',f'luz {l} | distancia {d}') for l in range(3) for d in range(3)]),
                                ('shadows',[(f'shadow-l{l}-b{b}',f'luz {l} | normal bias {b}') for l in range(3) for b in range(2)])]:
                sheet=Image.new('RGB',(3*350,380*len(shots)),'#eee9df');draw=ImageDraw.Draw(sheet)
                for row,(shot,label) in enumerate(shots):
                    for col,variant in enumerate(('original','n35','n65')):
                        p=folder/f'{scope}-{variant}-{season}-{shot}.png'
                        image=Image.open(p).convert('RGB');image.thumbnail((350,350));sheet.paste(image,(col*350,row*380+30))
                        draw.text((col*350+4,row*380+8),f'{variant} | {label}',fill='#29221b')
                sheet.save(output/f'{scope}-{season}-{title}.jpg',quality=93)
            for variant in ('n35','n65'):
                values=[]
                for light in range(3):
                    for view in range(6):
                        a=Image.open(folder/f'{scope}-original-{season}-l{light}-v{view}-d0.png').convert('RGB')
                        b=Image.open(folder/f'{scope}-{variant}-{season}-l{light}-v{view}-d0.png').convert('RGB')
                        values.append(sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3)
                metrics[scope+'-'+season+'-'+variant]={'mean_abs_rgb_near_0_255':sum(values)/len(values),'max_view_mean':max(values)}
    checks['six-blender-imports']=json.loads((output/'blender-report.json').read_text())['passed']
    checks['793-captures']=sum(len(r['captures']) for r in reports.values())==793
    checks['source-and-assets-still-exact']=locked(output)==manifest
    result={'version':manifest['version'],'passed':all(checks.values()),'checks':checks,'manifest':manifest,
            'godot':reports,'blender':json.loads((output/'blender-report.json').read_text()),'visual_difference_metrics':metrics,
            'review_source_sha256':sha(Path(__file__)),
            'capture_sha256':{str(p.relative_to(captures)):sha(p) for p in sorted(captures.glob('*/*.png'))},
            'protocol':{'views':['front','side','perspective','back','top','below'],'scales':[1.15,2.8,6.0],
                        'lights':[[-35,-25,0],[-35,-90,0],[-35,155,0]],'shadow_normal_bias':[0,1],
                        'renderer':'Compatibility','resolution':[600,600],'msaa':4,'roughness':.95,'alpha_cutoff':.5,
                        'sun_energy':1.2,'ambient_energy':.5,'exposure':1,'tonemap':'linear','shading':'StandardMaterial3D only',
                        'normal_adoption':'pending_user_art_review','season_animation':False}}
    write(output/'verification.json',result)
    images=''.join(f'<figure><a href="{p.name}"><img src="{p.name}" width="350"></a><figcaption>{p.stem}</figcaption></figure>' for p in sorted(output.glob('*.jpg')))
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>T4 · normales locales</title><style>body{font:16px sans-serif;background:#eee9df}main{display:flex;flex-wrap:wrap}img{max-width:100%}</style><h1>T4 · normales locales de copa</h1><p>Original / intensidad .35 / intensidad .65. Material estándar, pinturas fijas, geometría idéntica. Ensayo pendiente de valoración artística.</p><p>Abrir godot/project.godot para comparar en el visor.</p><main>'+images+'</main>')
    assert result['passed'],{k:v for k,v in checks.items() if not v}
    print(f'{len(checks)} checks y {len(result["capture_sha256"])} capturas: T4 verificada técnicamente',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--stage',choices=('all','build','review'),default='all');a=p.parse_args();out=a.output.resolve()
    if a.stage in ('all','build'):
        report=build(out)
        with tempfile.TemporaryDirectory(prefix='canopy-normals-') as tmp:assert build(Path(tmp)/'repeat')==report
    if a.stage in ('all','review'):review(out)
