#!/usr/bin/env python3
"""RF2: matriz 2 patrones × 3 densidades × 2 orientaciones, GLB y Godot."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from treegen.foliage_branch_evaluation import inspect_branch_glb
from treegen.foliage import digest
from treegen.foliage_branch import load_branch
from treegen.runner import BLENDER
from verify_foliage_unit import GODOT


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gallery(output, names, visual):
    views = ['perspective', 'top', 'below', 'detail-perspective', 'detail-below']
    if visual:
        views += ['godot-perspective', 'godot-detail-perspective']
    sections = []
    for orientation in (0, 70):
        for pattern in ('longitudinal', 'terminal'):
            columns = ['reference']+[f'{pattern}-r{orientation}-{density}' for density in ('low', 'medium', 'high')]
            rows = []
            for view in views:
                rows.append('<tr><th>'+view+'</th>'+''.join(f'<td><a href="{name}/{view}.png"><img src="{name}/{view}.png" alt="{name} {view}"></a></td>' for name in columns)+'</tr>')
            sections.append(f'<h2>{pattern}, giro de soporte {orientation}°</h2><table><tr><th>Vista</th>'+''.join(f'<th>{n}</th>' for n in columns)+'</tr>'+''.join(rows)+'</table>')
    controls = ''.join(f'<a href="{n}/detail-perspective.png">{n}</a> · ' for n in ['control-size', 'control-count', 'control-inclination', 'control-length'])
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>RF2</title>'
        '<style>body{font:16px sans-serif;background:#e9edf1;margin:24px}table{table-layout:fixed;width:100%}img{width:100%}th:first-child{width:130px}</style>'
        '<h1>RF2: follaje sobre rama Q3</h1><p>Primaria 100 y secundarias 200–202 originales. Madera y cámaras idénticas. '
        'Dos patrones, tres densidades y dos orientaciones; no se ha construido una copa completa.</p>'
        '<p>Controles aislados: '+controls+'</p><p><a href="longitudinal-r0-medium/supports-debug/detail-perspective.png">Recorridos virtuales (solo diagnóstico, ausentes en el GLB)</a></p>'+''.join(sections))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rf0', type=Path, default=ROOT/'docs/evidence/rf0-rf1/reference-lock.json')
    parser.add_argument('--preset', type=Path, default=ROOT/'presets/foliage-branch.json')
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    spec = load_branch(args.preset)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output/'logs').mkdir()
    tracked = ['src/treegen/foliage_branch.py', 'schemas/foliage-branch.schema.json', 'presets/foliage-branch.json',
        'blender/foliage_branch_lab.py', 'scripts/verify_foliage_branch.py', 'godot/verify_foliage_branch.gd',
        'src/treegen/foliage.py', 'blender/foliage_lab.py', 'blender/generate_oak.py', 'blender/foliage_fusion.py',
        'src/treegen/evaluation.py', 'src/treegen/foliage_branch_evaluation.py',
        'godot/verify_oak.gd', 'schemas/foliage-unit.schema.json']
    hashes = {name: sha(ROOT/name) for name in tracked}
    env = dict(os.environ, ARBOLES_RF2_STUDY=str(output), PYTHONPATH=str(ROOT/'src'),
        XDG_DATA_HOME=str(output/'xdg/data'), XDG_CONFIG_HOME=str(output/'xdg/config'), XDG_CACHE_HOME=str(output/'xdg/cache'))

    def run(name, command):
        path = output/'logs'/(name+'.log')
        with path.open('w') as stream:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=120)
        content = path.read_text()
        if result.returncode or 'SCRIPT ERROR:' in content or '\nERROR:' in content:
            raise RuntimeError(name+': '+content[-4000:])
        print(name+': OK', flush=True)
        return content.strip()

    def blender(mode, *options):
        return [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup', '--threads', '1',
            '--python-exit-code', '1', '--python', str(ROOT/'blender/foliage_branch_lab.py'), '--', mode, *map(str, options)]

    run('tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    run('reference', blender('prepare', '--rf0', args.rf0.resolve(), '--output', output/'reference'))
    reference = output/'reference/reference.json'
    ref = json.loads(reference.read_text())
    entries, manifests, exports = [], {}, {}

    def validate(name, capture):
        m = json.loads((output/name/'manifest.json').read_text())
        exports[name] = inspect_branch_glb(output/name/'branch.glb', m['metrics'])
        assert exports[name]['triangles'] == m['metrics']['triangles']
        assert exports[name]['materials'] == m['metrics']['triangles_by_material']
        assert m['wood_sha256'] == ref['wood_sha256']
        if name != 'reference':
            assert exports[name]['exported_wood_sha256'] == exports['reference']['exported_wood_sha256']
            assert exports[name]['bark_material_sha256'] == exports['reference']['bark_material_sha256']
        manifests[name] = m
        entries.append({'id': name, 'folder': str(output/name), 'capture': capture})
        return m

    validate('reference', True)
    names = []
    for roll in (0, 70):
        for pattern in ('longitudinal', 'terminal'):
            for density, rate in [('low', 6), ('medium', 9), ('high', 12)]:
                name = f'{pattern}-r{roll}-{density}'
                current = copy.deepcopy(spec)
                current.update(pattern=pattern, support_roll_deg=roll, leaves_per_m=rate)
                write(output/(name+'.json'), current)
                run(name, blender('candidate', '--reference', reference, '--spec', output/(name+'.json'), '--output', output/name))
                validate(name, True)
                names.append(name)
    base_name = 'longitudinal-r0-medium'
    base = manifests[base_name]
    for name, field, value in [('size', 'leaf_length_m', .32), ('inclination', 'inclination_deg', 100),
                              ('count', 'support_count', 20), ('length', 'support_length_m', .35), ('seed', 'seed', 18)]:
        current = copy.deepcopy(base['spec'])
        if field in current['leaf']:
            current['leaf'][field] = value
        else:
            current[field] = value
        name = 'control-'+name
        write(output/(name+'.json'), current)
        capture = name != 'control-seed'
        options = [] if capture else ['--no-render']
        run(name, blender('candidate', '--reference', reference, '--spec', output/(name+'.json'), '--output', output/name, *options))
        m = validate(name, capture)
        assert m['metrics']['geometry_sha256'] != base['metrics']['geometry_sha256']
        if field in ('leaf_length_m', 'inclination_deg'):
            assert m['supports_sha256'] == base['supports_sha256']
    name = 'repeat'
    run(name, blender('candidate', '--reference', reference, '--spec', output/(base_name+'.json'), '--output', output/name, '--no-render'))
    repeated = validate(name, False)
    assert repeated['metrics'] == base['metrics'] and repeated['placements_sha256'] == base['placements_sha256']
    for roll in (0, 70):
        same = [manifests[f'longitudinal-r{roll}-{d}'] for d in ('low', 'medium', 'high')]
        assert len({m['supports_sha256'] for m in same}) == 1
        for d in ('low', 'medium', 'high'):
            a, b = [manifests[f'{p}-r{roll}-{d}'] for p in ('longitudinal', 'terminal')]
            assert a['supports_sha256'] == b['supports_sha256'] and a['leaf_count'] == b['leaf_count']
            assert all(x['axes'] == y['axes'] and x['length_m'] == y['length_m'] for x, y in zip(a['placements'], b['placements']))
    assert len({m['cameras_sha256'] for m in manifests.values()}) == 1
    assets = ROOT/'godot/rf2'
    assets.mkdir(exist_ok=True)
    for entry in entries:
        shutil.copy2(output/entry['id']/'branch.glb', assets/(entry['id']+'.glb'))
    write(output/'godot-input.json', entries)
    godot = os.environ.get('GODOT_BIN', GODOT)
    assert run('godot-version', [godot, '--version']) == '4.7.2.stable.official.ed1daf0bf'
    run('godot-import', [godot, '--headless', '--path', str(ROOT/'godot'), '--editor', '--import'])
    command = [godot, '--path', str(ROOT/'godot'), '--script', 'res://verify_foliage_branch.gd']
    run('godot-headless', command[:1]+['--headless']+command[1:])
    report = json.loads((output/'godot-report.json').read_text())
    assert report['passed'] and len(report['assets']) == len(entries)
    visible = {}
    if args.visual:
        # Mantener 120 s por proceso aun con muchas capturas: lotes de seis.
        captured = [entry for entry in entries if entry['capture']]
        for start in range(0, len(captured), 6):
            batch = captured[start:start+6]
            input_path = output/f'godot-input-visual-{start}.json'
            report_path = output/f'godot-report-visual-{start}.json'
            write(input_path, batch)
            run(f'godot-visual-{start}', command+['--', '--visual', '--input='+str(input_path), '--report='+str(report_path)])
            partial = json.loads(report_path.read_text())
            assert partial['passed'] and len(partial['assets']) == len(batch)
            for entry in batch:
                assert partial['assets'][entry['id']] == report['assets'][entry['id']]
        for entry in entries:
            if entry['capture']:
                for view in ref['cameras']:
                    with Image.open(output/entry['id']/('godot-'+view+'.png')) as original:
                        image = original.convert('RGB')
                        delta = ImageChops.difference(image, Image.new('RGB', image.size, image.getpixel((0, 0)))).convert('L')
                        pixels = sum(count for value, count in enumerate(delta.histogram()) if value > 8)
                        assert pixels > 100, (entry['id'], view, pixels)
                        visible[entry['id']+'/'+view] = pixels
    assert hashes == {name: sha(ROOT/name) for name in tracked}
    assert ref['source_files_sha256'] == {name: sha(Path(ref['source'])/name) for name in ref['source_files_sha256']}
    summary = {'version': spec['version'], 'sources_sha256': hashes, 'reference_sha256': sha(reference),
        'runner_python': sys.version, 'same_final_wood': True, 'same_cameras': True, 'repeat_matches': True,
        'source_unchanged': True, 'matrix': {n: {key: manifests[n][key] for key in ('leaf_count', 'support_count', 'metrics', 'leaf_root_distance_to_wood_m', 'max_support_attachment_error_m')} for n in names},
        'control_checks': ['size', 'inclination', 'count', 'length', 'seed'], 'exports': exports,
        'godot': report, 'visual_captures_generated': args.visual, 'capture_visible_pixels': visible,
        'visual_acceptance': 'pending', 'rf3_started': False}
    write(output/'summary.json', summary)
    gallery(output, names, args.visual)
    print('RF2 verificada técnicamente; revisión artística pendiente: '+str(output/'index.html'))


if __name__ == '__main__':
    main()
