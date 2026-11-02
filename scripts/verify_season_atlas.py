#!/usr/bin/env python3
"""T2: atlas repetibles y revisión Godot de hojas/rama del piloto."""
import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile
from PIL import Image, ImageChops, ImageDraw, ImageStat
from build_season_atlas import ROOT, SUMMER, AUTUMN, build, sha, write
from review_pine_painted import run
from verify_foliage_unit import GODOT
from treegen.runner import BLENDER
from treegen.seasonal_paint import replace_foliage, audit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    for name in ('logs','godot','captures'): (out/name).mkdir()
    manifest=build(out/'atlas')
    with tempfile.TemporaryDirectory(prefix='season-atlas-') as tmp:
        repeated=build(Path(tmp)/'atlas')
        repeat=manifest==repeated
    project=out/'godot'
    source=ROOT/'artifacts/roble-pintado/integracion-madera-01/pilot'
    run([os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1',
         '--python',ROOT/'blender/season_atlas_sample.py','--',source,out],out/'logs/blender.log',os.environ)
    raw=(out/'branch/branch.glb').read_bytes()
    shutil.copy2(out/'branch/branch.glb',project/'branch.glb')
    shutil.copy2(SUMMER,project/'summer-original.png');shutil.copy2(AUTUMN,project/'autumn-original.png')
    audits={}
    for name in manifest['files']:
        shutil.copy2(out/'atlas'/name,project/name)
        png=(out/'atlas'/name).read_bytes()
        derived=replace_foliage(raw,png)
        (out/'branch'/name.replace('.png','.glb')).write_bytes(derived)
        audits[name]=audit(raw,derived,png)
    for name in ('verify_oak.gd','review_season_atlas.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    shutil.copy2(ROOT/'godot/project.godot',project/'project.godot')
    godot=os.environ.get('GODOT_BIN',GODOT)
    run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/import.log',os.environ)
    # Aislar nuestro tratamiento: desactivar la dilatación automática de Godot.
    for path in project.glob('*.png.import'):
        config=path.read_text()
        assert 'process/fix_alpha_border=true' in config
        assert 'mipmaps/generate=' in config
        path.write_text(config.replace('process/fix_alpha_border=true','process/fix_alpha_border=false').replace('mipmaps/generate=false','mipmaps/generate=true'))
    run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/reimport.log',os.environ)
    run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_season_atlas.gd','--',out/'captures'],out/'logs/godot.log',os.environ)
    import json
    report=json.loads((out/'captures/godot-report.json').read_text())
    for scope in ('board','branch'):
        for bg in ('light','dark'):
            styles=['summer-original','summer-common','summer-padded','autumn-original','autumn-common','autumn-padded']
            sheet=Image.new('RGB',(6*300,3*330),'#eee9df');draw=ImageDraw.Draw(sheet)
            for row,distance in enumerate(('near','medium','far')):
                for col,style in enumerate(styles):
                    im=Image.open(out/'captures'/f'{scope}-{style}-{bg}-{distance}.png').convert('RGB');im.thumbnail((300,300))
                    sheet.paste(im,(col*300,row*330+30));draw.text((col*300+4,row*330+8),style+' | '+distance,fill='black')
            sheet.save(out/f'{scope}-{bg}.jpg',quality=95)
    differences={}
    for scope in ('board','branch'):
        for bg in ('light','dark'):
            for season in ('summer','autumn'):
                for distance in ('near','medium','far'):
                    a=Image.open(out/'captures'/f'{scope}-{season}-common-{bg}-{distance}.png').convert('RGB')
                    b=Image.open(out/'captures'/f'{scope}-{season}-padded-{bg}-{distance}.png').convert('RGB')
                    d=ImageChops.difference(a,b)
                    differences[f'{scope}-{season}-{bg}-{distance}']={'mean_abs_rgb_0_255':sum(ImageStat.Stat(d).mean)/3,'bbox':d.getbbox()}
    paths=[Path(__file__),ROOT/'scripts/build_season_atlas.py',ROOT/'src/treegen/season_atlas.py',ROOT/'blender/season_atlas_sample.py',ROOT/'godot/review_season_atlas.gd']
    result={'passed':repeat and report['passed'] and len(report['captures'])==72,'repeat_atlas_manifest_and_png_exact':repeat,
            'atlas':manifest,'exports':audits,'godot':report,'padding_render_differences':differences,
            'source_lock':{str(p.relative_to(ROOT)):sha(p) for p in paths},
            'pilot_inputs':{str(p.relative_to(ROOT)):sha(p) for p in (source/'manifest.json',source/'base-reference.json',source/'reference/manifest.json',source/'tree.glb')},
            'capture_sha256':{p.name:sha(p) for p in sorted((out/'captures').glob('*.png'))}}
    write(out/'verification.json',result)
    pictures=''.join(f'<figure><a href="captures/{n}"><img width="300" src="captures/{n}"></a><figcaption>{n}</figcaption></figure>' for n in result['capture_sha256'])
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>T2 · atlas compatibles</title><style>body{font:16px sans-serif;background:#eee9df}main{display:flex;flex-wrap:wrap}</style><h1>T2 · hojas y rama del piloto</h1><p>Extremos fijos y ensayo de padding; aceptación artística pendiente. Sin mezcla T3.</p><main>'+pictures+'</main>')
    assert result['passed']
    print('Repetición exacta, cuatro GLB auditados y 72 capturas Godot: OK',flush=True)

if __name__=='__main__':main()
