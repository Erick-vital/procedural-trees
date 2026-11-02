#!/usr/bin/env python3
"""Exportar otoño desde pintura y comparar verano/shader/pintura en Godot."""
import argparse
import os
from pathlib import Path
import shutil
import sys
from PIL import Image, ImageChops, ImageDraw

from build_seasonal_oak import ROOT, build, read, sha, write
from review_pine_painted import run
from verify_foliage_unit import GODOT
from verify_painted_oak import mask_metrics
from treegen.seasonal_paint import VERSION, replace_foliage, audit
from treegen.evaluation import validate_glb

ASSETS = ROOT/'assets/roble-otono-pintado/v0.1.0'


def finalize_manifest(output):
    """El manifiesto final describe el paquete comparativo, incluido su visor."""
    project = output/'godot'
    source = read(output/'manifest.json')
    result = read(output/'verification.json')
    source['version'] = VERSION
    source['kind'] = 'autumn_paint_comparison'
    source['paint_resources'] = read(ASSETS/'manifest.json')
    names = set(source['files_sha256'])
    names.update(('autumn_painted_asset.gd', 'autumn_paint_viewer.gd', 'review_autumn_paint.gd'))
    for name in result['cases']:
        names.update(('painted-'+name+'.glb', 'painted-'+name+'.tscn'))
    source['files_sha256'] = {n: sha(project/n) for n in sorted(names)}
    source['exports'] = result['cases']
    write(output/'manifest.json', source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT/'artifacts/roble-pintado/integracion-madera-01')
    args = parser.parse_args()
    output = args.output.resolve()
    base = build(args.source.resolve(), output, ROOT/'configs/seasons/roble-otono-v1.json')
    project = output/'godot'
    captures = output/'captures'
    captures.mkdir()
    logs = output/'logs'
    logs.mkdir()
    for name in ('autumn_painted_asset.gd', 'autumn_paint_viewer.gd', 'review_autumn_paint.gd'):
        shutil.copy2(ROOT/'godot'/name, project/name)
    viewer = project/'viewer.tscn'
    viewer.write_text(viewer.read_text().replace('seasonal_tree_viewer.gd', 'autumn_paint_viewer.gd'))
    atlas = (ASSETS/'crossed-atlas.png').read_bytes()
    checks = {}
    exports = {}
    for item in base['cases']:
        name = item['id']
        original = (project/(name+'.glb')).read_bytes()
        painted = replace_foliage(original, atlas)
        folder = output/name
        folder.mkdir()
        target = folder/'tree.glb'
        target.write_bytes(painted)
        source = read(args.source/name/'manifest.json')
        exported = validate_glb(target, source['resolved_blueprint']['base_spec'], triangle_limit=6999, height_materials={'Painted_Bark'})
        checks[name+'-geometry-materials-resources-exact'] = all(v is True for k, v in audit(original, painted, atlas).items() if k != 'foliage_png_sha256')
        checks[name+'-repeat-glb-exact'] = painted == replace_foliage(original, atlas)
        checks[name+'-triangles-exact'] = exported['triangles'] == item['metrics']['triangles']
        exports[name] = {'version': VERSION, 'base_glb_sha256': item['base_glb_sha256'], 'glb_sha256': sha(target),
                         'metrics': item['metrics'], 'export_validation': exported,
                         'paint_atlas_sha256': sha(ASSETS/'crossed-atlas.png'), 'audit': audit(original, painted, atlas)}
        write(folder/'manifest.json', exports[name])
        shutil.copy2(target, project/('painted-'+name+'.glb'))
        (project/('painted-'+name+'.tscn')).write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="PackedScene" path="res://painted-'+name+'.glb" id="1"]\n[ext_resource type="Script" path="res://autumn_painted_asset.gd" id="2"]\n[node name="PaintedAutumnOak" instance=ExtResource("1")]\nscript=ExtResource("2")\n')
    godot = os.environ.get('GODOT_BIN', GODOT)
    run([godot, '--headless', '--path', project, '--editor', '--import'], logs/'import.log', os.environ)
    reports = []
    for item in base['cases']:
        write(project/'preview-config.json', {'cases': [item]})
        try:
            run([godot, '--path', project, '--audio-driver', 'Dummy', '--script', 'res://review_autumn_paint.gd', '--', captures], logs/(item['id']+'.log'), os.environ)
            reports.append(read(captures/'godot-report.json'))
        finally:
            write(project/'preview-config.json', {'cases': base['cases']})
    masks = {}
    for item in base['cases']:
        name = item['id']
        for style in ('summer', 'shader', 'painted'):
            a = Image.open(captures/f'{name}-{style}-perspective.png').convert('RGB')
            b = Image.open(captures/f'{name}-{style}-repeat.png').convert('RGB')
            checks[name+'-'+style+'-render-repeat'] = ImageChops.difference(a, b).getbbox() is None
        masks[name] = {v: mask_metrics(captures/f'{name}-summer-mask-{v}.png', captures/f'{name}-painted-mask-{v}.png') for v in ('perspective', 'side', 'back')}
    checks['godot'] = all(r['passed'] for r in reports)
    checks['132-captures'] = sum(len(r['captures']) for r in reports) == 132
    # El nuevo atlas puede cambiar alfa: medirlo, sin exigir identidad artificial.
    for title, names, views in [('comparison', ['pilot'], ['perspective']),
                                 ('controls', [x['id'] for x in base['cases']], ['perspective', 'back']),
                                 ('distances', ['pilot'], ['side', 'below', 'medium', 'far'])]:
        sheet = Image.new('RGB', (1350, 480*len(names)*len(views)), '#EEE9DF')
        draw = ImageDraw.Draw(sheet)
        for row, (name, view) in enumerate((n, v) for n in names for v in views):
            for column, style in enumerate(('summer', 'shader', 'painted')):
                im = Image.open(captures/f'{name}-{style}-{view}.png').convert('RGB')
                im.thumbnail((450, 450))
                sheet.paste(im, (450*column, 480*row+30))
                draw.text((450*column+10, 480*row+9), f'{name} | {style} | {view}', fill='#29221B')
        sheet.save(output/(title+'.jpg'), quality=93)
    paths = [ROOT/'src/treegen/seasonal_paint.py', Path(__file__), ROOT/'blender/bake_autumn_oak.py']
    paths += [ROOT/'godot'/n for n in ('autumn_painted_asset.gd', 'autumn_paint_viewer.gd', 'review_autumn_paint.gd')]
    paths += list(ASSETS.iterdir())
    result = {'version': VERSION, 'passed': all(checks.values()), 'checks': checks,
              'cases': exports, 'silhouette': masks, 'godot': reports,
              'source_lock': {str(p.relative_to(ROOT)): sha(p) for p in paths},
              'capture_sha256': {p.name: sha(p) for p in sorted(captures.glob('*.png'))}}
    write(output/'verification.json', result)
    finalize_manifest(output)
    print(f'{len(checks)} checks; {len(result["capture_sha256"])} capturas; passed={result["passed"]}', flush=True)
    assert result['passed'], [k for k, v in checks.items() if not v]


if __name__ == '__main__':
    main()
