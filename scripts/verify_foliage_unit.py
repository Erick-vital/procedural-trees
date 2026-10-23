#!/usr/bin/env python3
"""RF0/RF1: referencia, tres formas, controles, repetición y GLB/Godot."""
import argparse
import copy
import html
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from treegen.foliage import digest, load_unit
from treegen.foliage_evaluation import validate_unit_glb
from treegen.runner import BLENDER

GODOT = '/home/tao/repos/godot/openworld-forever/.tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64'


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def gallery(output, names, visual):
    views = ['front', 'side', 'top', 'below', 'perspective', 'reverse', 'alternate-light']
    if visual:
        views.extend(['godot-perspective', 'godot-reverse'])
    sheet = Image.new('RGB', (420*len(names), 450*len(views)), '#e9edf1')
    draw = ImageDraw.Draw(sheet)
    rows = []
    for row, view in enumerate(views):
        cells = []
        for col, name in enumerate(names):
            relative = f'{name}/{view}.png'
            with Image.open(output/relative) as original:
                pic = original.convert('RGB')
                pic.thumbnail((416, 416))
            sheet.paste(pic, (col*420, row*450+30))
            draw.text((col*420+8, row*450+8), f'{name} | {view}', fill='black')
            cells.append(f'<td><a href="{relative}"><img src="{relative}" alt="{name} {view}"></a></td>')
        rows.append(f'<tr><th>{view}</th>'+''.join(cells)+'</tr>')
    sheet.save(output/'variants.jpg', quality=90)
    controls = ''.join(f'<a href="{name}/perspective.png">{html.escape(name)}</a> · ' for name in
                       ['folded-hex', 'control-length', 'control-spacing', 'control-inclination'])
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>RF0 y RF1</title>'
        '<style>body{font:16px sans-serif;background:#e9edf1;margin:24px}table{table-layout:fixed;width:100%}'
        'img{width:100%}th{width:110px}</style><h1>RF0 y RF1: unidad de follaje</h1>'
        '<p>Tres formas sobre el mismo portador virtual, siete hojas, cámaras compartidas, sin madera añadida. '
        'No es todavía la copa ni una rama poblada. Aceptación artística pendiente.</p>'
        '<p>RF0: <a href="reference/tree/perspective.png">Q3</a> · '
        '<a href="reference/tree/near.png">Cerca (50 %)</a> · '
        '<a href="reference/tree/medium.png">Media (25 %)</a> · '
        '<a href="reference/tree/far.png">Lejos (10 %)</a> · '
        '<a href="reference/branch/perspective.png">Rama congelada</a></p><p>Controles: '+controls+'</p>'
        '<table><tr><th>Vista</th>'+''.join(f'<th>{n}</th>' for n in names)+'</tr>'+''.join(rows)+'</table>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT/'artifacts/q3/acceptance/lote/viejo-09')
    parser.add_argument('--preset', type=Path, default=ROOT/'presets/foliage-unit.json')
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    spec = load_unit(args.preset)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    logs = output/'logs'
    logs.mkdir()
    tracked = ['scripts/verify_foliage_unit.py', 'blender/foliage_lab.py', 'src/treegen/foliage.py',
               'src/treegen/foliage_evaluation.py', 'schemas/foliage-unit.schema.json',
               'godot/verify_foliage.gd', 'godot/verify_oak.gd', 'presets/foliage-unit.json']
    source_hashes = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in tracked}
    env = dict(os.environ, ARBOLES_FOLIAGE_STUDY=str(output),
               XDG_DATA_HOME=str(output/'xdg/data'), XDG_CONFIG_HOME=str(output/'xdg/config'),
               XDG_CACHE_HOME=str(output/'xdg/cache'), PYTHONPATH=str(ROOT/'src'))

    def run(label, command):
        with (logs/f'{label}.log').open('w') as stream:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=120)
        content = (logs/f'{label}.log').read_text()
        if result.returncode or 'SCRIPT ERROR:' in content or '\nERROR:' in content:
            raise RuntimeError(label+': '+content[-4000:])
        print(label+': OK', flush=True)
        return content.strip()

    def blender(mode, *options):
        return [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup', '--threads', '1',
                '--python-exit-code', '1', '--python', str(ROOT/'blender/foliage_lab.py'), '--', mode, *map(str, options)]

    run('tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    run('reference', blender('reference', '--source', args.source.resolve(), '--output', output/'reference'))
    lock = json.loads((output/'reference/reference-lock.json').read_text())
    manifests, validations, entries = {}, {}, []

    def generate(name, current, capture, camera=None):
        path = output/(name+'-input.json')
        write(path, current)
        command = blender('unit', '--spec', path, '--output', output/name)
        if camera:
            command.extend(['--cameras', str(camera)])
        if not capture:
            command.append('--no-render')
        run(name, command)
        manifest = json.loads((output/name/'manifest.json').read_text())
        validations[name] = validate_unit_glb(output/name/'unit.glb', manifest)
        manifests[name] = manifest
        entries.append({'id': name, 'folder': str(output/name), 'capture': capture})
        return manifest

    names = ['diamond', 'hex', 'folded-hex']
    for name in names:
        current = copy.deepcopy(spec)
        current['parameters'].update(variant=name, fold_deg=25 if name == 'folded-hex' else 0)
        generate(name, current, True, output/'diamond/cameras.json' if name != 'diamond' else None)
    cameras = output/'diamond/cameras.json'
    base_spec = manifests['folded-hex']['spec']
    repeat = generate('repeat', base_spec, False, cameras)
    assert repeat['metrics'] == manifests['folded-hex']['metrics']
    assert repeat['placements_sha256'] == manifests['folded-hex']['placements_sha256']
    controls = {'length': ('leaf_length_m', .27), 'width': ('width_ratio', .85),
        'spacing': ('spacing_m', .06), 'azimuth': ('azimuth_step_deg', 90),
        'inclination': ('inclination_deg', 105), 'roll': ('roll_deg', -35),
        'fold': ('fold_deg', 45), 'jitter': ('jitter_deg', 0), 'scale-jitter': ('scale_jitter', 0)}
    for name, (field, value) in controls.items():
        current = copy.deepcopy(base_spec)
        current['parameters'][field] = value
        changed = generate('control-'+name, current, name in ('length', 'spacing', 'inclination'), cameras)
        assert changed['metrics']['geometry_sha256'] != repeat['metrics']['geometry_sha256'], field
    current = copy.deepcopy(base_spec)
    current['seed'] += 1
    changed = generate('control-seed', current, False, cameras)
    assert changed['metrics']['geometry_sha256'] != repeat['metrics']['geometry_sha256']
    # Límite de trabajo real en Blender, y un solo plano sin espesor.
    for name, count, variant in [('maximum', 32, 'folded-hex'), ('single-plane', 1, 'diamond')]:
        current = copy.deepcopy(base_spec)
        current['support']['points_m'] = [[0, 0, 0], [0, 0, count*.03]]
        current['parameters'].update(spacing_m=.03, variant=variant, fold_deg=25 if variant == 'folded-hex' else 0,
                                     inclination_deg=90, roll_deg=0, jitter_deg=0, scale_jitter=0)
        generate(name, current, False, cameras)
    assert all(m['cameras_sha256'] == repeat['cameras_sha256'] for m in manifests.values())
    assets = ROOT/'godot/rf1'
    assets.mkdir(exist_ok=True)
    for entry in entries:
        shutil.copy2(output/entry['id']/'unit.glb', assets/(entry['id']+'.glb'))
    write(output/'godot-input.json', entries)
    godot = os.environ.get('GODOT_BIN', GODOT)
    assert run('godot-version', [godot, '--version']) == '4.7.2.stable.official.ed1daf0bf'
    run('godot-import', [godot, '--headless', '--path', str(ROOT/'godot'), '--editor', '--import'])
    command = [godot, '--path', str(ROOT/'godot'), '--script', 'res://verify_foliage.gd']
    run('godot-headless', command[:1]+['--headless']+command[1:])
    if args.visual:
        run('godot-visual', command+['--', '--visual'])
        visible_pixels = {}
        for entry in entries:
            if not entry['capture']:
                continue
            for view in json.loads((output/entry['id']/'cameras.json').read_text()):
                path = output/entry['id']/('godot-'+view+'.png')
                with Image.open(path) as original:
                    image = original.convert('RGB')
                    background = Image.new('RGB', image.size, image.getpixel((0, 0)))
                    delta = ImageChops.difference(image, background).convert('L')
                    pixels = sum(count for value, count in enumerate(delta.histogram()) if value > 8)
                    if pixels < 100:
                        raise ValueError(f'Captura vacía o ilegible: {path} ({pixels} píxeles)')
                    visible_pixels[entry['id']+'/'+view] = pixels
    report = json.loads((output/'godot-report.json').read_text())
    assert report['passed'] and len(report['assets']) == len(entries)
    wood = lock['metrics']['triangles_by_material']['Oak_Bark']
    remaining = 10000-wood
    summary = {'version': spec['version'], 'reference_lock_sha256': digest(lock),
        'sources_sha256': source_hashes, 'runner_python': sys.version,
        'wood_triangles': wood, 'remaining_foliage_triangles': remaining,
        'variants': {name: {'leaves': manifests[name]['leaf_count'],
            'triangles_per_leaf': manifests[name]['triangles_per_leaf'],
            'triangles_per_unit': manifests[name]['metrics']['triangles'],
            'max_leaves_per_tree': remaining//manifests[name]['triangles_per_leaf'],
            'max_units_per_tree': remaining//manifests[name]['metrics']['triangles']} for name in names},
        'repeated_geometry_matches': True, 'same_cameras': True, 'control_checks': list(controls)+['seed'],
        'export_validation': validations, 'godot': report, 'visual_captures_generated': args.visual,
        'capture_visible_pixels': visible_pixels if args.visual else {},
        'visual_acceptance': 'pending', 'rf2_started': False}
    assert source_hashes == {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in tracked}
    write(output/'summary.json', summary)
    gallery(output, names, args.visual)
    print('RF0/RF1 verificadas técnicamente; aceptación visual pendiente: '+str(output/'index.html'))


if __name__ == '__main__':
    main()
