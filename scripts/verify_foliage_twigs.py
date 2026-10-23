#!/usr/bin/env python3
"""Revisión RF2: pareja con/sin ramillas, región congelada y coste acotado."""
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
from treegen.foliage import digest
from treegen.foliage_twigs import VERSION, load_twigs
from treegen.foliage_twigs_evaluation import inspect_twigs_glb
from treegen.runner import BLENDER
from verify_foliage_unit import GODOT
from verify_foliage_branch import sha, write


def gallery(output, names, visual):
    views = ['front', 'side', 'top', 'below', 'perspective', 'reverse',
             'detail-perspective', 'detail-below', 'near', 'medium', 'far']
    if visual:
        views = ['godot-'+view for view in views]
    rows = []
    for view in views:
        rows.append('<tr><th>'+view+'</th>'+''.join(
            f'<td><a href="{name}/{view}.png"><img src="{name}/{view}.png" alt="{name} {view}"></a></td>' for name in names)+'</tr>')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>RF2: ramillas</title>'
        '<style>body{font:16px sans-serif;background:#e9edf1;margin:20px}table{table-layout:fixed;width:100%}img{width:100%}th:first-child{width:120px}</style>'
        '<h1>RF2: ramillas y contribución espacial</h1><p>Madera Q3 y cámaras compartidas. Pareja con/sin ramillas: hojas idénticas. '
        'Después, distribución hacia región congelada y control de 12 soportes. RF3 sin iniciar; aceptación artística pendiente.</p>'
        '<p><a href="summary.json">Verificación y límites</a> · <a href="reference/target.json">Región objetivo</a></p>'
        '<table><tr><th>Vista</th>'+''.join(f'<th>{name}</th>' for name in names)+'</tr>'+''.join(rows)+'</table>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rf0', type=Path, default=ROOT/'docs/evidence/rf0-rf1/reference-lock.json')
    parser.add_argument('--preset', type=Path, default=ROOT/'presets/foliage-twigs.json')
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    spec = load_twigs(args.preset)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output/'logs').mkdir()
    tracked = sorted({str(path.relative_to(ROOT)) for folder, suffix in
        [('src/treegen', '*.py'), ('blender', '*.py'), ('scripts', '*.py'), ('schemas', '*.json'), ('tests', '*.py')]
        for path in (ROOT/folder).glob(suffix)} | {
            'presets/foliage-twigs.json', 'godot/verify_foliage_twigs.gd', 'godot/verify_oak.gd',
            'docs/contrato-rf2-ramillas.md'})
    hashes = {name: sha(ROOT/name) for name in tracked}
    env = dict(os.environ, ARBOLES_RF2_TWIGS_STUDY=str(output), PYTHONPATH=str(ROOT/'src'),
        XDG_DATA_HOME=str(output/'xdg/data'), XDG_CONFIG_HOME=str(output/'xdg/config'), XDG_CACHE_HOME=str(output/'xdg/cache'))

    def run(name, command, timeout=120):
        log = output/'logs'/(name+'.log')
        with log.open('w') as stream:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=True)
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
            raise RuntimeError(name+': '+content[-4000:])
        print(name+': OK', flush=True)
        return content.strip()

    def blender(script, mode, *options):
        return [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup', '--threads', '1',
            '--python-exit-code', '1', '--python', str(ROOT/'blender'/script), '--', mode, *map(str, options)]

    run('tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    run('source-reference', blender('foliage_branch_lab.py', 'prepare', '--rf0', args.rf0.resolve(), '--output', output/'source-reference'))
    reference = output/'source-reference/reference.json'
    ref = json.loads(reference.read_text())
    run('freeze-target', blender('foliage_twigs_lab.py', 'target', '--reference', reference, '--output', output/'reference'))
    target = output/'reference/target.json'
    manifests, exports, entries = {}, {}, []

    def validate(name, capture):
        m = json.loads((output/name/'manifest.json').read_text())
        exports[name] = inspect_twigs_glb(output/name/'branch.glb', m['metrics'])
        assert m['wood_sha256'] == ref['wood_sha256']
        if name != 'reference':
            assert exports[name]['exported_wood_sha256'] == exports['reference']['exported_wood_sha256']
            assert exports[name]['bark_material_sha256'] == exports['reference']['bark_material_sha256']
            assert m['base_matrix_world'] == m['output_matrix_world'] == ref['matrix_world']
            if m['spec']['twigs']['enabled']:
                assert m['contacts']['all_insertions_on_q3_and_inside_twig'] and m['contacts']['all_leaf_roots_inside_own_twig']
        entries.append({'id': name, 'folder': str(output/name), 'capture': capture})
        manifests[name] = m
        return m

    validate('reference', True)
    cases = []
    for name, visible, mode, count in [('without-twigs', False, 'original', 16), ('with-twigs', True, 'original', 16),
                                      ('directed-16', True, 'target', 16), ('directed-12', True, 'target', 12)]:
        current = copy.deepcopy(spec)
        current['twigs']['enabled'] = visible
        current['distribution']['mode'] = mode
        current['base']['support_count'] = count
        cases.append((name, current, True))
    for name, key, value in [('control-size', 'leaf_length_m', .32), ('control-density', 'leaves_per_m', 12),
                             ('control-radius', 'radius_m', .018), ('control-seed', 'seed', 18)]:
        current = copy.deepcopy(cases[3][1])
        section = current['twigs'] if key == 'radius_m' else current['base']['leaf'] if key == 'leaf_length_m' else current['base']
        section[key] = value
        cases.append((name, current, name != 'control-seed'))
    for name, rate in [('control-length', 9), ('control-reach-same-count', 6)]:
        current = copy.deepcopy(cases[3][1])
        current['base'].update(support_length_m=.8, leaves_per_m=rate)
        cases.append((name, current, True))
    cases.extend([('repeat-original', copy.deepcopy(cases[1][1]), False), ('repeat-directed', copy.deepcopy(cases[3][1]), False)])
    for name, current, capture in cases:
        write(output/(name+'.json'), current)
        run(name, blender('foliage_twigs_lab.py', 'candidate', '--reference', reference, '--target', target,
            '--spec', output/(name+'.json'), '--output', output/name, *([] if capture else ['--no-render'])))
        validate(name, capture)
    left, right = manifests['without-twigs'], manifests['with-twigs']
    for key in ('supports_sha256', 'placements_sha256', 'cameras_sha256', 'wood_sha256'):
        assert left[key] == right[key]
    assert exports['without-twigs']['channel_sha256']['RF1_Leaf'] == exports['with-twigs']['channel_sha256']['RF1_Leaf']
    # El par también reconstruye las colocaciones RF2 originales, sin corrección oculta.
    from treegen.foliage_branch import branch_placements
    assert digest(branch_placements(spec['base'], left['supports'])) == left['placements_sha256']
    for repeated, base in [('repeat-original', 'with-twigs'), ('repeat-directed', 'directed-12')]:
        for key in ('metrics', 'supports_sha256', 'placements_sha256', 'twigs_sha256'):
            assert manifests[repeated][key] == manifests[base][key]
        assert exports[repeated]['channel_sha256'] == exports[base]['channel_sha256']
    for name in ('control-size', 'control-density'):
        for key in ('supports_sha256', 'twigs_sha256'):
            assert manifests[name][key] == manifests['directed-12'][key]
        assert exports[name]['channel_sha256']['RF2_Twig'] == exports['directed-12']['channel_sha256']['RF2_Twig']
    for key in ('supports_sha256', 'placements_sha256'):
        assert manifests['control-radius'][key] == manifests['directed-12'][key]
    assert manifests['control-seed']['supports_sha256'] != manifests['directed-12']['supports_sha256']
    assert manifests['control-reach-same-count']['budget'] == manifests['directed-12']['budget']
    assert manifests['directed-12']['supports'] == manifests['directed-16']['supports'][:12]
    assert len({m['cameras_sha256'] for m in manifests.values()}) == 1
    assets = ROOT/'godot/rf2_twigs'
    assets.mkdir(exist_ok=True)
    for entry in entries:
        shutil.copy2(output/entry['id']/'branch.glb', assets/(entry['id']+'.glb'))
    write(output/'godot-input.json', entries)
    godot = os.environ.get('GODOT_BIN', GODOT)
    assert run('godot-version', [godot, '--version']) == '4.7.2.stable.official.ed1daf0bf'
    run('godot-import', [godot, '--headless', '--path', str(ROOT/'godot'), '--editor', '--import'], 180)
    command = [godot, '--path', str(ROOT/'godot'), '--script', 'res://verify_foliage_twigs.gd']
    run('godot-headless', command[:1]+['--headless']+command[1:], 180)
    report = json.loads((output/'godot-report.json').read_text())
    assert report['passed'] and len(report['assets']) == len(entries)
    visible = {}
    if args.visual:
        captured = [entry for entry in entries if entry['capture']]
        for start in range(0, len(captured), 3):
            batch = captured[start:start+3]
            input_path, report_path = output/f'godot-input-{start}.json', output/f'godot-report-{start}.json'
            write(input_path, batch)
            run(f'godot-visual-{start}', command+['--', '--visual', '--input='+str(input_path), '--report='+str(report_path)], 180)
            partial = json.loads(report_path.read_text())
            assert partial['passed'] and len(partial['assets']) == len(batch)
            for entry in batch:
                assert partial['assets'][entry['id']] == report['assets'][entry['id']]
                for view in json.loads(target.read_text())['cameras']:
                    with Image.open(output/entry['id']/('godot-'+view+'.png')) as original:
                        image = original.convert('RGB')
                        delta = ImageChops.difference(image, Image.new('RGB', image.size, image.getpixel((0, 0)))).convert('L')
                        pixels = sum(count for value, count in enumerate(delta.histogram()) if value > 8)
                        assert pixels > 100, (entry['id'], view, pixels)
                        visible[entry['id']+'/'+view] = pixels
    assert hashes == {name: sha(ROOT/name) for name in tracked}
    assert ref['source_files_sha256'] == {name: sha(Path(ref['source'])/name) for name in ref['source_files_sha256']}
    summary = {'version': VERSION, 'sources_sha256': hashes, 'runner_python': sys.version,
        'reference_sha256': sha(reference), 'target_sha256': sha(target),
        'reference_source_unchanged': True, 'same_final_q3_wood': True, 'same_cameras': True,
        'pair_same_supports_and_leaves': True, 'repeat_matches': ['with-twigs', 'directed-12'],
        'controls_verified': ['size', 'density', 'radius', 'seed', 'length', 'reach-same-count'],
        'cases': {name: {key: m[key] for key in ('metrics', 'budget', 'leaf_count', 'support_count', 'distribution', 'contacts',
            'max_insertion_error_m', 'twigs_sha256', 'generation_before_render_export_s', 'total_s', 'glb_bytes')}
            for name, m in manifests.items() if name != 'reference'},
        'exports': exports, 'godot': report, 'visual_captures_generated': args.visual,
        'capture_visible_pixels': visible, 'visual_acceptance': 'pending', 'rf3_started': False}
    write(output/'summary.json', summary)
    gallery(output, ['reference', 'without-twigs', 'with-twigs', 'directed-16', 'directed-12'], args.visual)
    print('Revisión RF2 verificada técnicamente; revisión visual pendiente: '+str(output/'index.html'))


if __name__ == '__main__':
    main()
