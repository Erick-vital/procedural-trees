#!/usr/bin/env python3
"""Generar rama de abedul y revisar exportación y apariencia real en Godot."""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from treegen.runner import BLENDER
from treegen.evaluation import validate_glb
from treegen.birch_sample import build_sample
from review_pine_painted import read, write, run, camera, sha
from verify_foliage_unit import GODOT
from oak_painted_sample import inspect
from foliage_evidence import sheet

ASSETS = ROOT/'assets/abedul-pintado/v0.1.0'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--stage', choices=['all', 'generate', 'review'], default='all')
    args = parser.parse_args()
    out = args.output.resolve()
    env = dict(os.environ, PYTHONPATH=str(ROOT/'src'), XDG_DATA_HOME=str(out/'xdg/data'),
               XDG_CONFIG_HOME=str(out/'xdg/config'), XDG_CACHE_HOME=str(out/'xdg/cache'))
    blender = os.environ.get('BLENDER_BIN', BLENDER)
    if args.stage in ('all', 'generate'):
        if out.exists():
            raise SystemExit('Usar una carpeta de salida nueva')
        out.parent.mkdir(parents=True, exist_ok=True)
        log = out.with_suffix('.generation.log')
        run([blender, '--background', '--factory-startup', '--threads', '1', '--python-exit-code', '1',
             '--python', ROOT/'blender/birch_sample.py', '--', out], log, env)
        (out/'logs').mkdir()
        shutil.copy2(log, out/'logs/generation.log')
        # Repetición acotada con los mismos PNG congelados.
        repeat = out/'repeat'
        run([blender, '--background', '--factory-startup', '--threads', '1', '--python-exit-code', '1',
             '--python', ROOT/'blender/birch_sample.py', '--', repeat], out/'logs/repeat.log', env)
        manifest = read(out/'manifest.json')
        checks = {}
        for name, variant in manifest['variants'].items():
            path = out/name/'branch.glb'
            expected = [sha(ASSETS/'bark.png')]
            if name == 'crossed':
                expected.append(sha(ASSETS/'foliage.png'))
            check = inspect(path, expected)
            audit = validate_glb(path, {'parameters': {'height_m': variant['metrics']['height_m']}}, triangle_limit=6999)
            assert audit['triangles'] == variant['metrics']['triangles']
            assert audit['materials'] == variant['metrics']['triangles_by_material']
            assert sha(path) == sha(repeat/name/'branch.glb'), 'Repetición distinta'
            checks[name] = {**check, 'geometry': audit, 'repeat_identical': True}
        manifest['export_validation'] = checks
        files = [Path(__file__), ROOT/'blender/birch_sample.py', ROOT/'src/treegen/birch_sample.py',
                 ROOT/'src/treegen/pine.py', ROOT/'blender/pine_painted_sample.py',
                 ROOT/'godot/review_birch_sample.gd', ROOT/'godot/painted_pine_asset.gd',
                 ROOT/'godot/verify_oak.gd', ROOT/'godot/birch_sample_viewer.gd', *ASSETS.iterdir()]
        manifest['source_lock'] = {str(p.relative_to(ROOT)): sha(p) for p in files if p.is_file()}
        write(out/'manifest.json', manifest)
        print('Rama y repetición verificadas:', manifest['variants']['crossed']['metrics']['triangles'], 'tris', flush=True)
    if args.stage == 'generate':
        return
    manifest = read(out/'manifest.json')
    assert all(sha(ROOT/p) == digest for p, digest in manifest['source_lock'].items())
    project, captures = out/'godot', out/'captures'
    project.mkdir(exist_ok=False)
    captures.mkdir()
    for name in ('verify_oak.gd', 'review_birch_sample.gd', 'painted_pine_asset.gd', 'birch_sample_viewer.gd'):
        shutil.copy2(ROOT/'godot'/name, project/name)
    (project/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Abedul · rama de muestra"\nrun/main_scene="res://preview.tscn"\n[display]\nwindow/size/viewport_width=1200\nwindow/size/viewport_height=850\n[rendering]\nrenderer/rendering_method="gl_compatibility"\ntextures/default_filters/use_nearest_mipmap_filter=false\n')
    (project/'preview.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://birch_sample_viewer.gd" id="1"]\n[node name="BirchSampleReview" type="Node3D"]\nscript=ExtResource("1")\n')
    entries = []
    for name in ('crossed', 'wood'):
        shutil.copy2(out/name/'branch.glb', project/(name+'.glb'))
        (project/(name+'.tscn')).write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="PackedScene" path="res://'+name+'.glb" id="1"]\n[ext_resource type="Script" path="res://painted_pine_asset.gd" id="2"]\n[node name="BirchBranch" instance=ExtResource("1")]\nscript=ExtResource("2")\n')
        entries.append({'id': name, 'resource': 'res://'+name+'.tscn', 'metrics': manifest['variants'][name]['metrics']})
    lo, hi = manifest['variants']['crossed']['metrics']['bounds_blender']
    center = [(a+b)/2 for a, b in zip(lo, hi)]
    span = max(b-a for a, b in zip(lo, hi))
    write(project/'preview-config.json', {'center': center, 'span': span, 'triangles': manifest['variants']['crossed']['metrics']['triangles']})
    shots = []
    views = [('front', [0, -1, .12]), ('side', [1, 0, .12]), ('perspective', [1, -1, .6]),
             ('back', [-1, 1, .3]), ('top', [0, 0, 1]), ('below', [1, -1, -.7])]
    for name, direction in views:
        shots.append({'id': name, 'camera': camera(center, span, direction, span*1.2), 'background': '#EEE9DF', 'light': [-35, -25, 0]})
    for name, scale, bg, light in [('medium', 2.4, '#EEE9DF', [-35, -25, 0]), ('far', 4.8, '#EEE9DF', [-35, -25, 0]),
                                  ('dark', 1.2, '#252A28', [-35, -25, 0]), ('lateral', 1.2, '#EEE9DF', [-35, -90, 0]),
                                  ('backlit', 1.2, '#EEE9DF', [-35, 155, 0])]:
        shots.append({'id': name, 'camera': camera(center, span, [1, -1, .6], span*scale), 'background': bg, 'light': light})
    for i in range(12):
        angle = 2*math.pi*i/12
        shots.append({'id': f'orbit-{i:02}', 'only': 'crossed', 'camera': camera(center, span, [math.cos(angle), math.sin(angle), .25], span*1.2),
                      'background': '#EEE9DF', 'light': [-35, -25, 0]})
    shots.append({'id': 'bark-close', 'only': 'wood', 'camera': camera([.32, 0, .06], span, [0, -1, .2], span*.38),
                  'background': '#EEE9DF', 'light': [-35, -25, 0]})
    write(out/'protocol.json', {'shots': shots, 'center': center, 'span': span, 'resolution': [900, 900],
                               'sun_energy': .75, 'ambient': .35})
    godot = os.environ.get('GODOT_BIN', GODOT)
    run([godot, '--headless', '--path', project, '--editor', '--import'], out/'logs/import.log', env)
    reviews = []
    for index in range(0, len(shots), 6):
        config, result = out/f'review-input-{index}.json', out/f'review-report-{index}.json'
        write(config, {'output': str(captures), 'report': str(result), 'span': span, 'center': center,
                       'original_low': lo, 'assets': entries, 'shots': shots[index:index+6]})
        run([godot, '--path', project, '--audio-driver', 'Dummy', '--script', 'res://review_birch_sample.gd', '--', config, '--visual'],
            out/'logs'/f'review-{index}.log', env)
        review = read(result)
        assert review['passed']
        reviews.append(review)
        print('Godot lote', index, 'OK', flush=True)
    manifest['godot'] = reviews
    manifest['captures'] = {p.name: sha(p) for p in sorted(captures.glob('*.png'))}
    assert len(manifest['captures']) == 35
    manifest['passed'] = True
    write(out/'manifest.json', manifest)
    sheet(out, out/'review.jpg', 3, [[('captures/crossed--'+v+'.png', 'Abedul | '+v) for v in row]
                                  for row in [('perspective', 'front', 'side'), ('top', 'below', 'back'), ('dark', 'medium', 'far')]])
    sheet(out, out/'wood.jpg', 2, [[('captures/wood--'+v+'.png', 'Madera | '+v) for v in row]
                                for row in [('perspective', 'front'), ('side', 'top')]])
    cells = ''.join('<figure><img width="350" src="captures/'+name+'"><figcaption>'+name+'</figcaption></figure>' for name in manifest['captures'])
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Abedul · rama</title><style>body{font:16px sans-serif;background:#eee9df}main{display:flex;flex-wrap:wrap}figure{margin:10px}</style><h1>Abedul · muestra en Godot</h1><p>Pintura aprobada; aplicación a rama pendiente de aprobación. Tres láminas por grupo, dos materiales.</p><main>'+cells+'</main>')
    print('Muestra lista:', out, '| 35 capturas reales', flush=True)


if __name__ == '__main__':
    main()
