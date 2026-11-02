#!/usr/bin/env python3
"""T3: mezcla GPU, aislamiento por instancia y secuencias del piloto."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from PIL import Image,ImageChops,ImageDraw,ImageStat
from build_paint_transition import ROOT,build,sha,write
from review_pine_painted import run
from verify_foliage_unit import GODOT


def locked(output):
    manifest=json.loads((output/'manifest.json').read_text())
    for path,h in {**manifest['source_lock'],**manifest['input_lock']}.items():
        if sha(ROOT/path)!=h:raise ValueError('Fuente/entrada modificada: '+path)
    for path,h in manifest['project_lock'].items():
        if sha(output/'godot'/path)!=h:raise ValueError('Paquete modificado: '+path)
    return manifest


def review(output):
    manifest=locked(output)
    project=output/'godot';logs=output/'logs';captures=output/'captures'
    logs.mkdir(exist_ok=True);captures.mkdir(exist_ok=True)
    godot=os.environ.get('GODOT_BIN',GODOT)
    run([godot,'--headless','--path',project,'--editor','--import'],logs/'import.log',os.environ)
    for path in project.glob('*.png.import'):
        config=path.read_text()
        config=re.sub(r'mipmaps/generate=(true|false)','mipmaps/generate=true',config)
        config=re.sub(r'process/fix_alpha_border=(true|false)','process/fix_alpha_border=false',config)
        config=re.sub(r'compress/mode=\d+','compress/mode=0',config)
        path.write_text(config)
    run([godot,'--headless','--path',project,'--editor','--import'],logs/'reimport.log',os.environ)
    reports={}
    for stage in ('static','fixed','orbit','viewer'):
        folder=captures/stage;folder.mkdir(exist_ok=True)
        run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_paint_transition.gd','--',folder,stage],logs/(stage+'.log'),os.environ)
        reports[stage]=json.loads((folder/(stage+'-report.json')).read_text())
        print(stage+': revisión Godot OK',flush=True)
    summaries={}
    for stage in ('fixed','orbit'):
        frames=[];differences=[]
        for index in range(241):
            with Image.open(captures/stage/f'{stage}-{index:03}.png') as im:
                frame=im.convert('RGB');frame.thumbnail((480,480))
                frames.append(frame)
            if index:
                d=ImageChops.difference(frames[-2],frames[-1])
                differences.append(sum(ImageStat.Stat(d).mean)/3)
        frames[0].save(output/(stage+'.webp'),save_all=True,append_images=frames[1:],duration=67,loop=0,quality=85,method=4)
        summaries[stage]={'adjacent_mean_abs_rgb_0_255':differences,'max_adjacent_mean':max(differences),
                          'frames':241,'phase_step':1/120,'presentation_frame_duration_ms':67,
                          'note':'Órbita incluye cambios de visibilidad; esta métrica no prueba ausencia de parpadeo.'}
    sheet=Image.new('RGB',(1500,5*330),'#eee9df');draw=ImageDraw.Draw(sheet)
    for row in range(5):
        for col,title in enumerate(['Calendario','Uniforme','Verano fijo','Otoño fijo','Tinte anterior']):
            im=Image.open(captures/'static'/f'mode-{col}-p{row}.png').convert('RGB');im.thumbnail((300,300))
            sheet.paste(im,(col*300,row*330+30));draw.text((col*300+4,row*330+8),f'{title} | p={row/4:g}',fill='#29221b')
    sheet.save(output/'comparison.jpg',quality=94)
    endpoints={}
    for season in ('summer','autumn'):
        a=Image.open(captures/'static'/f'endpoint-{season}-shader.png').convert('RGB')
        b=Image.open(captures/'static'/f'endpoint-{season}-standard.png').convert('RGB')
        diff=ImageChops.difference(a,b)
        endpoints[season]={'pixels_exact':diff.getbbox() is None,'mean_abs_rgb_0_255':sum(ImageStat.Stat(diff).mean)/3,
                           'maximum_channel_delta':max(v[1] for v in diff.getextrema())}
    def exact(a,b):
        return ImageChops.difference(Image.open(a).convert('RGB'),Image.open(b).convert('RGB')).getbbox() is None
    fixed_endpoints=all(exact(captures/'static'/f'mode-{mode}-p0.png',captures/'static'/f'mode-{mode}-p{j}.png') for mode in (2,3) for j in range(1,5))
    checks={'fixed_paints_phase_independent':fixed_endpoints,
            'all_godot_stages' :all(v['passed'] for v in reports.values()),
            'both_endpoints_standard_exact':all(v['pixels_exact'] for v in endpoints.values()),
            'sequence_482_frames':sum(len(reports[s]['frames']) for s in ('fixed','orbit'))==482,
            'source_locks_still_exact':locked(output)==manifest}
    result={'version':manifest['version'],'passed':all(checks.values()),'checks':checks,'manifest':manifest,
            'godot':reports,'endpoints':endpoints,'sequence_metrics':summaries,
            'capture_sha256':{str(p.relative_to(captures)):sha(p) for p in sorted(captures.glob('*/*.png'))},
            'review_source_sha256':sha(Path(__file__)),
            'project_import_settings':{p.name:p.read_text() for p in project.glob('*.png.import')}}
    write(output/'verification.json',result)
    (output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>T3 · transición pintada</title>
<style>body{font:16px sans-serif;background:#eee9df;max-width:1500px;margin:24px auto}img{max-width:100%}section{display:flex;flex-wrap:wrap}figure{margin:12px}</style>
<h1>Roble · transición pintada T3</h1><p>Piloto 3009/17/2718, calendario 1101. 6812 tris, 264 grupos, 2 materiales. Aceptación artística pendiente.</p>
<p>Secuencias: fase 0→1→0 en pasos de 1/120. Órbita de ida y vuelta. El movimiento de cámara puede cambiar visibilidad de láminas.</p>
<section><figure><img src="fixed.webp"><figcaption>Cámara fija</figcaption></figure><figure><img src="orbit.webp"><figcaption>Órbita</figcaption></figure></section>
<h2>Comparación estática</h2><a href="comparison.jpg"><img src="comparison.jpg"></a>
<p>Abrir godot/project.godot y ejecutar para usar deslizador, pausa, retroceso y modos.</p>''')
    assert result['passed'],{k:v for k,v in checks.items() if not v}
    print(f'{len(result["capture_sha256"])} capturas; extremos exactos; T3 verificada',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--stage',choices=['build','review','all'],default='all');a=p.parse_args();out=a.output.resolve()
    if a.stage in ('build','all'):
        manifest=build(out)
        with tempfile.TemporaryDirectory(prefix='paint-transition-') as tmp:
            assert build(Path(tmp)/'repeat')==manifest
    if a.stage in ('review','all'):review(out)
