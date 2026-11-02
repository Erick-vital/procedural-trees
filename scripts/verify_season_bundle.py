#!/usr/bin/env python3
"""T5: auditar cuatro casos, repetir estados y probar el paquete fuera del repo."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile
from PIL import Image,ImageDraw
from build_season_bundle import ROOT,build,sha,write
from treegen.season_bundle import validate_portable
from treegen.runner import BLENDER
from review_pine_painted import run
from verify_foliage_unit import GODOT


def locked(output):
    manifest=json.loads((output/'manifest.json').read_text())
    for p,h in {**manifest['source_lock'],**manifest['input_lock']}.items():
        if sha(ROOT/p)!=h:raise ValueError('Fuente/entrada modificada: '+p)
    for p,h in manifest['project_lock'].items():
        if sha(output/'godot'/p)!=h:raise ValueError('Paquete modificado: '+p)
    if sha(output/'portable/manifest.json')!=manifest['portable_manifest_sha256']:raise ValueError('Manifiesto portable modificado')
    validate_portable(output/'portable')
    return manifest


def import_project(project,logs,godot):
    run([godot,'--headless','--path',project,'--editor','--import'],logs/'import.log',os.environ)
    for p in project.rglob('*.png.import'):
        s=p.read_text();s=re.sub(r'mipmaps/generate=(true|false)','mipmaps/generate=true',s)
        s=re.sub(r'process/fix_alpha_border=(true|false)','process/fix_alpha_border=false',s)
        s=re.sub(r'compress/mode=\d+','compress/mode=0',s);p.write_text(s)
    run([godot,'--headless','--path',project,'--editor','--import'],logs/'reimport.log',os.environ)


def review(output):
    manifest=locked(output);project=output/'godot';logs=output/'logs';logs.mkdir(exist_ok=True)
    historical={str(p.relative_to(ROOT)):sha(p) for folder in ('blueprints','presets','assets') for p in sorted((ROOT/folder).rglob('*')) if p.is_file()}
    run([os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1',
         '--python',ROOT/'blender/verify_canopy_normals.py','--',output/'blender-input.json'],logs/'blender.log',os.environ)
    godot=os.environ.get('GODOT_BIN',GODOT);import_project(project,logs,godot)
    captures=output/'captures';captures.mkdir(exist_ok=True);reports={}
    for item in manifest['bundle']['cases']:
        name=item['id'];reports[name]={}
        for stage in ('matrix','fixed','orbit'):
            folder=captures/name/stage;folder.mkdir(parents=True,exist_ok=True)
            run([godot,'--fixed-fps','60','--disable-render-loop','--path',project,'--audio-driver','Dummy','--script','res://review_season_bundle.gd','--',folder,name,stage],logs/(name+'-'+stage+'.log'),os.environ)
            reports[name][stage]=json.loads((folder/(stage+'-report.json')).read_text())
            print(name+' '+stage+': Godot OK',flush=True)
    ui=captures/'viewer';ui.mkdir(exist_ok=True)
    run([godot,'--fixed-fps','60','--disable-render-loop','--path',project,'--audio-driver','Dummy','--script','res://review_season_bundle.gd','--',ui,'all','viewer'],logs/'viewer.log',os.environ)
    ui_report=json.loads((ui/'viewer-report.json').read_text())
    run([godot,'--fixed-fps','60','--disable-render-loop','--path',project,'--audio-driver','Dummy','--script','res://review_season_bundle_resources.gd','--',output/'resource-report.json'],logs/'resources.log',os.environ)
    resource_report=json.loads((output/'resource-report.json').read_text())
    # Copia limpia: sin imports ni cachés y sin enlaces de vuelta al repositorio.
    with tempfile.TemporaryDirectory(prefix='season-bundle-portable-') as tmp:
        cold=Path(tmp);cold_project=cold/'godot';cold_project.mkdir();(cold/'logs').mkdir();(cold/'captures').mkdir()
        shutil.copytree(output/'portable',cold/'portable');validate_portable(cold/'portable')
        for rel in manifest['project_lock']:
            target=cold_project/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(project/rel,target)
        import_project(cold_project,cold/'logs',godot)
        run([godot,'--fixed-fps','60','--disable-render-loop','--path',cold_project,'--audio-driver','Dummy','--script','res://review_season_bundle.gd','--',cold/'captures','all','portable'],cold/'logs/run.log',os.environ)
        cold_report=json.loads((cold/'captures/portable-report.json').read_text())
        for p in (cold/'logs').iterdir():shutil.copy2(p,logs/('portable-'+p.name))
        cold_captures=output/'portable-captures';cold_captures.mkdir(exist_ok=True)
        for p in (cold/'captures').iterdir():shutil.copy2(p,cold_captures/p.name)
    # Archivo revisable sin .godot, .import, UIDs o texturas extraídas regenerables.
    archive=output/'roble-estacional-0.1.0.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        files={**{'godot/'+n:project/n for n in manifest['project_lock']},
               **{'portable/'+str(p.relative_to(output/'portable')):p for p in (output/'portable').rglob('*') if p.is_file()}}
        for rel,p in sorted(files.items()):
            info=zipfile.ZipInfo(rel,date_time=(2026,11,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,p.read_bytes())
    # Vista de las cinco fases de los cuatro casos, con normal seleccionada.
    sheet=Image.new('RGB',(5*300,4*330),'#eee9df');draw=ImageDraw.Draw(sheet)
    for row,item in enumerate(manifest['bundle']['cases']):
        for col in range(5):
            path=captures/item['id']/'matrix'/f'mix-light-l0-d0-p{col}.png'
            im=Image.open(path).convert('RGB');im.thumbnail((300,300));sheet.paste(im,(300*col,row*330+30))
            draw.text((300*col+4,row*330+9),f'{item["id"]} | p={col/4:g}',fill='#29221b')
    sheet.save(output/'comparison.jpg',quality=94)
    for stage in ('fixed','orbit'):
        frames=[]
        for i in range(241):
            sheet=Image.new('RGB',(640,680),'#eee9df');draw=ImageDraw.Draw(sheet)
            for j,item in enumerate(manifest['bundle']['cases']):
                im=Image.open(captures/item['id']/stage/f'{stage}-{i:03}.png').convert('RGB');im.thumbnail((320,320))
                x=(j%2)*320;y=(j//2)*340;sheet.paste(im,(x,y+20));draw.text((x+4,y+4),item['id'],fill='#29221b')
            frames.append(sheet)
        frames[0].save(output/(stage+'.webp'),save_all=True,append_images=frames[1:],duration=67,loop=0,quality=83,method=4)
    checks={'all_four_case_godot':all(r['passed'] for case in reports.values() for r in case.values()),
            '16_blender_endpoints':len(json.loads((output/'blender-report.json').read_text())['cases'])==16,
            'viewer_passed':ui_report['passed'],'three_textures_two_shared_materials':resource_report['passed'],'clean_external_copy_passed':cold_report['passed'],
            '1928_sequence_frames':sum(len(reports[i][s]['frames']) for i in reports for s in ('fixed','orbit'))==1928,
            'historical_catalog_exact':all(sha(ROOT/p)==h for p,h in historical.items()),'final_locks_exact':locked(output)==manifest}
    result={'version':manifest['version'],'passed':all(checks.values()),'checks':checks,'manifest':manifest,'godot':reports,'viewer':ui_report,
            'portable':cold_report,'resources':resource_report,'blender':json.loads((output/'blender-report.json').read_text()),'historical_catalog_sha256':historical,
            'capture_sha256':{str(p.relative_to(captures)):sha(p) for p in sorted(captures.glob('**/*.png'))},
            'archive':{'file':archive.name,'sha256':sha(archive),'bytes':archive.stat().st_size},'review_source_sha256':sha(Path(__file__)),
            'protocol':{'capture_fixed_fps':60,'automatic_render_loop':False,'resolution':[600,600],'msaa':4,'backgrounds':['#EEE9DF','#182027'],'phases':[0,.25,.5,.75,1],
                        'scales':[1.15,2.8,6],'lights':[[-35,-25,0],[-35,-90,0],[-35,155,0]],'normals':'n35 selected; originals as controls',
                        'sun_energy':1.2,'ambient_energy':.5,'roughness':.95,'cutoff':.5,'tonemap':'linear','shadow_normal_bias':1,'ground_casts_shadows':False}}
    write(output/'verification.json',result)
    (output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>T5 · cuatro robles estacionales</title><style>body{font:16px sans-serif;background:#eee9df;max-width:1500px;margin:24px auto}img{max-width:100%}section{display:flex;flex-wrap:wrap}</style><h1>T5 · cuatro robles estacionales</h1><p>Normales .35 seleccionadas, calendario por grupo y atlas compatibles. Candidata explícita 0.1.0; receta histórica conservada.</p><section><figure><img src="fixed.webp"><figcaption>Cámara fija · ida y vuelta</figcaption></figure><figure><img src="orbit.webp"><figcaption>Órbita · ida y vuelta</figcaption></figure></section><a href="comparison.jpg"><img src="comparison.jpg"></a><p><a href="roble-estacional-0.1.0.zip">Paquete Godot y extremos GLB</a> · Abrir godot/project.godot para el visor.</p>''')
    assert result['passed'],{k:v for k,v in checks.items() if not v}
    print(f'{len(result["capture_sha256"])} capturas; T5 verificada; paquete {archive.stat().st_size} bytes',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--stage',choices=('all','build','review'),default='all')
    a=p.parse_args();out=a.output.resolve()
    if a.stage in ('all','build'):
        manifest=build(out)
        with tempfile.TemporaryDirectory(prefix='season-bundle-repeat-') as tmp:assert build(Path(tmp)/'repeat')==manifest
    if a.stage in ('all','review'):review(out)
