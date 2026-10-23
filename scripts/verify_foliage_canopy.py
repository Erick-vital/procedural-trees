#!/usr/bin/env python3
"""RF3: viejo-09 completo, controles de perfil/ocupación y Godot."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from treegen.foliage_canopy import VERSION, load_canopy
from treegen.foliage_twigs_evaluation import inspect_twigs_glb
from treegen.foliage_molds_evaluation import foliage_masks, compare_masks
from treegen.runner import BLENDER
from verify_foliage_unit import GODOT
from verify_foliage_branch import sha, write


def gallery(output, visual):
    names = ['reference', 'pilot', 'wider', 'open-east', 'leaf-size']
    views = ['front', 'side', 'top', 'below', 'perspective', 'reverse', 'near', 'medium', 'far',
             'detail-top', 'detail-below', 'detail-perspective']
    prefix = 'godot-' if visual else ''
    rows = ['<tr><th>'+v+'</th>'+''.join(f'<td><a href="{n}/{prefix}{v}.png"><img src="{n}/{prefix}{v}.png" alt="{n} {v}"></a></td>' for n in names)+'</tr>' for v in views]
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>RF3: viejo-09</title>'
        '<style>body{font:16px sans-serif;background:#e9edf1;margin:20px}table{table-layout:fixed;width:100%}img{width:100%}th:first-child{width:130px}</style>'
        '<h1>RF3: copa completa de viejo-09</h1><p>Madera Q3 intacta, moldes invisibles y regla de hoja RF2 aprobada. '
        'Piloto, perfil horizontal ×1.12, ocupación este ×.4 y hoja .75 m. Techo 12500 triángulos/3 materiales. '
        'Aceptación artística de copa pendiente; RF4 sin iniciar.</p><p><a href="summary.json">Verificación y controles</a></p>'
        '<table><tr><th>Vista</th>'+''.join('<th>'+n+'</th>' for n in names)+'</tr>'+''.join(rows)+'</table>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preset', type=Path, default=ROOT/'presets/foliage-canopy.json')
    parser.add_argument('--rf0', type=Path, default=ROOT/'docs/evidence/rf0-rf1/reference-lock.json')
    parser.add_argument('--acceptance', type=Path, default=ROOT/'docs/evidence/rediseno-follaje/rf2-densidad/aceptacion.json')
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    spec = load_canopy(args.preset)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output/'logs').mkdir()
    tracked = sorted({str(p.relative_to(ROOT)) for folder, pattern in [('src/treegen', '*.py'), ('blender', '*.py'),
        ('scripts', '*.py'), ('schemas', '*.json'), ('tests', '*.py')] for p in (ROOT/folder).glob(pattern)} |
        {'presets/foliage-canopy.json', 'godot/verify_foliage_molds.gd', 'godot/verify_oak.gd',
         'docs/contrato-rf3-copa.md'})
    hashes = {name: sha(ROOT/name) for name in tracked}
    inputs = {'rf0': args.rf0.resolve(), 'acceptance': args.acceptance.resolve(), 'preset': args.preset.resolve()}
    input_hashes = {name: sha(path) for name, path in inputs.items()}
    env = dict(os.environ, ARBOLES_RF2_MOLDS_STUDY=str(output), PYTHONPATH=str(ROOT/'src'),
        XDG_DATA_HOME=str(output/'xdg/data'), XDG_CONFIG_HOME=str(output/'xdg/config'), XDG_CACHE_HOME=str(output/'xdg/cache'))

    def run(name, command, timeout=120):
        log = output/'logs'/(name+'.log')
        with log.open('w') as stream:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                result = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                write(output/'failure.json', {'stage': name, 'timeout_s': timeout, 'log': str(log)})
                raise
        content = log.read_text()
        if result or 'SCRIPT ERROR:' in content or '\nERROR:' in content:
            write(output/'failure.json', {'stage': name, 'exit_code': result, 'log': str(log)})
            raise RuntimeError(name+': '+content[-4500:])
        print(name+': OK', flush=True)
        return content.strip()

    def blender(mode, *options):
        return [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup', '--threads', '1',
            '--python-exit-code', '1', '--python', str(ROOT/'blender/foliage_canopy_lab.py'), '--', mode, *map(str, options)]

    run('tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    run('reference', blender('prepare', '--rf0', args.rf0.resolve(), '--acceptance', args.acceptance.resolve(), '--output', output/'reference'))
    reference = output/'reference/reference.json'
    ref = json.loads(reference.read_text())
    manifests, exports, entries = {}, {}, []
    source_manifest = json.loads((Path(ref['source'])/'manifest.json').read_text())
    source_export = inspect_twigs_glb(Path(ref['source'])/'tree.glb', source_manifest['metrics'])

    def validate(name, capture):
        m = json.loads((output/name/'manifest.json').read_text())
        exports[name] = inspect_twigs_glb(output/name/'tree.glb', m['metrics'], triangle_limit=12500)
        assert exports[name]['triangles'] <= 12500
        assert exports[name]['exported_wood_sha256'] == source_export['exported_wood_sha256']
        assert exports[name]['bark_material_sha256'] == source_export['bark_material_sha256']
        assert m['wood_sha256'] == ref['wood_sha256']
        assert abs(m['metrics']['height_m']-9) < .0001
        if name != 'reference':
            assert m['base_spec'] == ref['spec'] and m['base_seeds'] == ref['seeds'] and m['normalization'] == ref['normalization']
            assert m['output_matrix_world'] == m['base_matrix_world'] == ref['matrix_world']
            assert m['contacts']['all_insertions_on_q3_and_inside_twig'] and m['contacts']['all_leaf_roots_inside_own_twig']
            assert not m['molds_exported']
        manifests[name] = m
        entries.append({'id': name, 'folder': str(output/name), 'capture': capture, 'resource': f'res://rf3_canopy/{name}.glb'})

    validate('reference', True)
    for name, capture in [('pilot', True), ('wider', True), ('open-east', True), ('leaf-size', True), ('repeat', False), ('control-seed', False)]:
        current = copy.deepcopy(spec)
        options = [] if capture else ['--no-render']
        if name == 'wider':
            current['profile_width_scale'] = 1.12
        elif name == 'open-east':
            current['region_weights']['east'] = .4
        elif name == 'leaf-size':
            current['leaf_length_m'] = .75
            options += ['--layout-leaf-length-m', str(spec['leaf_length_m'])]
        elif name == 'control-seed':
            current['seed'] = 18
        write(output/(name+'.json'), current)
        run(name, blender('candidate', '--reference', reference, '--spec', output/(name+'.json'), '--output', output/name, *options))
        validate(name, capture)
    pilot = manifests['pilot']
    for key in ('metrics', 'supports_sha256', 'placements_sha256', 'twigs_sha256'):
        assert pilot[key] == manifests['repeat'][key]
    assert exports['pilot']['channel_sha256'] == exports['repeat']['channel_sha256']
    assert manifests['wider']['molds_sha256'] != pilot['molds_sha256']
    opened = manifests['open-east']
    for region in ('north', 'south', 'west'):
        assert [c for c in pilot['supports'] if c['region'] == region] == [c for c in opened['supports'] if c['region'] == region]
    assert opened['selection']['group_quotas']['east'] < pilot['selection']['group_quotas']['east']
    smaller = manifests['leaf-size']
    assert smaller['supports_sha256'] == pilot['supports_sha256'] and smaller['twigs_sha256'] == pilot['twigs_sha256']
    assert exports['leaf-size']['channel_sha256']['RF2_Twig'] == exports['pilot']['channel_sha256']['RF2_Twig']
    for a, b in zip(pilot['placements'], smaller['placements']):
        for key in ('id', 'origin_m', 'axes'):
            assert a[key] == b[key]
    assert manifests['control-seed']['supports_sha256'] != pilot['supports_sha256']
    assert len({m['cameras_sha256'] for m in manifests.values()}) == 1
    cameras = ref['cameras']
    masks = {name: foliage_masks(output/name/'tree.glb', cameras) for name in manifests}
    projected = {name: compare_masks(masks['reference'], mask) for name, mask in masks.items()}
    for entry in entries:
        if entry['capture']:
            folder = output/entry['id']/'masks'
            folder.mkdir()
            for view, mask in masks[entry['id']].items():
                mask.save(folder/(view+'.png'))
    assets = ROOT/'godot/rf3_canopy'
    assets.mkdir(exist_ok=True)
    for entry in entries:
        shutil.copy2(output/entry['id']/'tree.glb', assets/(entry['id']+'.glb'))
    write(output/'godot-input.json', entries)
    godot = os.environ.get('GODOT_BIN', GODOT)
    assert run('godot-version', [godot, '--version']) == '4.7.2.stable.official.ed1daf0bf'
    run('godot-import', [godot, '--headless', '--path', str(ROOT/'godot'), '--editor', '--import'], 180)
    command = [godot, '--path', str(ROOT/'godot'), '--script', 'res://verify_foliage_molds.gd']
    run('godot-headless', command[:1]+['--headless']+command[1:], 180)
    report = json.loads((output/'godot-report.json').read_text())
    assert report['passed'] and len(report['assets']) == len(entries)
    visible = {}
    if args.visual:
        captured = [entry for entry in entries if entry['capture']]
        for start in range(0, len(captured), 2):
            batch = captured[start:start+2]
            input_path, report_path = output/f'godot-input-{start}.json', output/f'godot-report-{start}.json'
            write(input_path, batch)
            run(f'godot-visual-{start}', command+['--', '--visual', '--input='+str(input_path), '--report='+str(report_path)], 180)
            partial = json.loads(report_path.read_text())
            assert partial['passed'] and len(partial['assets']) == len(batch)
            for entry in batch:
                assert partial['assets'][entry['id']] == report['assets'][entry['id']]
                for view in cameras:
                    with Image.open(output/entry['id']/('godot-'+view+'.png')) as original:
                        image = original.convert('RGB')
                        delta = ImageChops.difference(image, Image.new('RGB', image.size, image.getpixel((0, 0)))).convert('L')
                        pixels = sum(count for value, count in enumerate(delta.histogram()) if value > 8)
                        assert pixels > 100
                        visible[entry['id']+'/'+view] = pixels
    assert hashes == {name: sha(ROOT/name) for name in tracked}
    assert input_hashes == {name: sha(path) for name, path in inputs.items()}
    assert ref['source_files_sha256'] == {name: sha(Path(ref['source'])/name) for name in ref['source_files_sha256']}
    summary = {'version': VERSION, 'phase': 'RF3', 'sources_sha256': hashes, 'runner_python': sys.version,
        'inputs_sha256': input_hashes,
        'reference_sha256': sha(reference), 'rf2_acceptance_sha256': sha(args.acceptance.resolve()),
        'same_final_q3_wood': True, 'source_unchanged': True, 'same_cameras': True, 'repeat_matches': True,
        'controls_verified': ['profile_width', 'east_occupancy', 'leaf_size', 'foliage_seed'],
        'cases': {name: {key: m[key] for key in ('spec', 'metrics', 'budget', 'support_count', 'leaf_count', 'sampling', 'selection',
            'contacts', 'height_check', 'projection_clips', 'generation_before_render_export_s', 'total_s', 'glb_bytes')}
            for name, m in manifests.items() if name != 'reference'},
        'exports': exports, 'source_export': source_export, 'projected_foliage': projected,
        'godot': report, 'visual_captures_generated': args.visual, 'capture_visible_pixels': visible,
        'visual_acceptance': 'pending', 'rf4_started': False}
    write(output/'summary.json', summary)
    gallery(output, args.visual)
    print('RF3 verificada técnicamente; aprobación visual pendiente: '+str(output/'index.html'))


if __name__ == '__main__':
    main()
