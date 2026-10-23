#!/usr/bin/env python3
"""Ensayo RF2 de moldes Q3: dos tamaños con igual coste, GLB y Godot."""
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
from treegen.foliage_molds import VERSION, load_mold_spec
from treegen.foliage_mold_density import VERSION as DENSITY_VERSION, load_density
from treegen.foliage_molds_evaluation import foliage_masks, compare_masks
from treegen.foliage_twigs_evaluation import inspect_twigs_glb
from treegen.runner import BLENDER
from verify_foliage_unit import GODOT
from verify_foliage_branch import sha, write


def gallery(output, visual, density=False):
    names = (['reference', 'base-96', 'leaves-120', 'leaves-144', 'leaves-192'] if density else
             ['reference', 'previous', 'small', 'large', 'efficient-080', 'efficient-100'])
    views = ['front', 'side', 'top', 'below', 'perspective', 'reverse', 'detail-perspective', 'detail-below', 'near', 'medium', 'far']
    prefix = 'godot-' if visual else ''
    rows = ['<tr><th>'+view+'</th>'+''.join(f'<td><a href="{name}/{prefix}{view}.png"><img src="{name}/{prefix}{view}.png" alt="{name} {view}"></a></td>' for name in names)+'</tr>' for view in views]
    description = ('<h1>RF2: aumento de hojas</h1><p>96, 120, 144 y 192 hojas de 1 m. '
        'Mismas conexiones y hojas originales, moldes invisibles, cámaras y luces comunes. '
        'Nuevo techo: 12500 triángulos por árbol; RF3 sin iniciar.</p>' if density else
        '<h1>RF2: moldes Q3 invisibles</h1><p>Q3, revisión previa, hexágonos .45/.8 m y rombos .8/1 m. '
        'Cada pareja comparte grupos, conexiones y orientaciones. Hexágonos: 48 hojas/416 triángulos añadidos; '
        'rombos: 96 hojas/384 triángulos. Los moldes no se exportan. RF3 sin iniciar.</p>')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>RF2: moldes Q3</title>'
        '<style>body{font:16px sans-serif;background:#e9edf1;margin:20px}table{table-layout:fixed;width:100%}img{width:100%}th:first-child{width:130px}</style>'
        +description+
        '<p><a href="summary.json">Métricas y cobertura proyectada</a> · <a href="molds/molds.json">Moldes congelados</a></p>'
        '<table><tr><th>Vista</th>'+''.join('<th>'+name+'</th>' for name in names)+'</tr>'+''.join(rows)+'</table>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rf0', type=Path, default=ROOT/'docs/evidence/rf0-rf1/reference-lock.json')
    parser.add_argument('--preset', type=Path)
    parser.add_argument('--density', action='store_true', help='Ensayo aditivo 0.1.2, techo 12500 por árbol')
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    preset = args.preset or ROOT/('presets/foliage-mold-density.json' if args.density else 'presets/foliage-molds.json')
    spec = load_density(preset) if args.density else load_mold_spec(preset)
    version = DENSITY_VERSION if args.density else VERSION
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output/'logs').mkdir()
    tracked = sorted({str(p.relative_to(ROOT)) for folder, pattern in [('src/treegen', '*.py'), ('blender', '*.py'),
        ('scripts', '*.py'), ('schemas', '*.json'), ('tests', '*.py')] for p in (ROOT/folder).glob(pattern)} |
        {'presets/foliage-molds.json', 'presets/foliage-mold-density.json', 'presets/foliage-twigs.json', 'godot/verify_foliage_molds.gd',
         'godot/verify_oak.gd', 'docs/contrato-rf2-moldes.md'})
    hashes = {name: sha(ROOT/name) for name in tracked}
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

    def blender(script, mode, *options):
        return [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup', '--threads', '1',
            '--python-exit-code', '1', '--python', str(ROOT/'blender'/script), '--', mode, *map(str, options)]

    run('tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    run('source-reference', blender('foliage_branch_lab.py', 'prepare', '--rf0', args.rf0.resolve(), '--output', output/'source-reference'))
    reference = output/'source-reference/reference.json'
    ref = json.loads(reference.read_text())
    run('reference', blender('foliage_twigs_lab.py', 'target', '--reference', reference, '--output', output/'reference'))
    run('molds', blender('foliage_molds_lab.py', 'prepare', '--reference', reference,
        '--cameras', output/'reference/cameras.json', '--output', output/'molds'))
    molds = output/'molds/molds.json'
    if not args.density:
        previous = json.loads((ROOT/'presets/foliage-twigs.json').read_text())
        previous['base']['support_count'] = 12
        previous['distribution']['mode'] = 'target'
        write(output/'previous.json', previous)
        run('previous', blender('foliage_twigs_lab.py', 'candidate', '--reference', reference,
            '--target', output/'reference/target.json', '--spec', output/'previous.json', '--output', output/'previous'))
    manifests, exports, entries = {}, {}, []
    asset_namespace = 'rf2_molds_density' if args.density else 'rf2_molds'

    def validate(name, capture):
        m = json.loads((output/name/'manifest.json').read_text())
        exports[name] = inspect_twigs_glb(output/name/'branch.glb', m['metrics'])
        assert m['wood_sha256'] == ref['wood_sha256']
        if name != 'reference':
            assert exports[name]['exported_wood_sha256'] == exports['reference']['exported_wood_sha256']
            assert exports[name]['bark_material_sha256'] == exports['reference']['bark_material_sha256']
            assert m['output_matrix_world'] == m['base_matrix_world'] == ref['matrix_world']
            assert m['contacts']['all_insertions_on_q3_and_inside_twig'] and m['contacts']['all_leaf_roots_inside_own_twig']
        manifests[name] = m
        entries.append({'id': name, 'folder': str(output/name), 'capture': capture,
                        'resource': f'res://{asset_namespace}/{name}.glb'})

    validate('reference', True)
    if not args.density:
        validate('previous', True)
    cases = [('small', .45, 17, True), ('large', .8, 17, True),
             ('efficient-080', .8, 17, True), ('efficient-100', 1., 17, True),
             ('repeat-small', .45, 17, False), ('repeat-large', .8, 17, False),
             ('repeat-efficient-080', .8, 17, False), ('repeat-efficient-100', 1., 17, False),
             ('control-seed', 1., 18, False)]
    extras = {'base-96': 0, 'leaves-120': 24, 'leaves-144': 48, 'leaves-192': 96,
              'repeat-144': 48, 'repeat-192': 96, 'control-seed': 48}
    if args.density:
        cases = [(name, 1., 17, capture) for name, capture in [('base-96', True), ('leaves-120', True),
            ('leaves-144', True), ('leaves-192', True), ('legacy-96', False), ('repeat-144', False), ('repeat-192', False)]]
        cases.append(('control-seed', 1., 18, False))
    for name, size, seed, capture in cases:
        if args.density:
            current = copy.deepcopy(spec)
            current['base']['seed'] = seed
            if name == 'legacy-96':
                current = current['base']
            else:
                current['extra_leaf_count'] = extras[name]
        else:
            current = dict(spec, leaf_length_m=size, seed=seed)
        if not args.density and ('efficient' in name or name == 'control-seed'):
            current.update(connection_shape='straight', variant='diamond', group_count=24, leaves_per_group=4)
        write(output/(name+'.json'), current)
        run(name, blender('foliage_molds_lab.py', 'candidate', '--reference', reference, '--molds', molds,
            '--spec', output/(name+'.json'), '--output', output/name, *([] if capture else ['--no-render'])))
        validate(name, capture)
        assert not manifests[name]['molds_exported']
        assert set(exports[name]['materials']) == {'Oak_Bark', 'RF1_Leaf', 'RF2_Twig'}
    pairs = [] if args.density else [('small', 'large'), ('efficient-080', 'efficient-100')]
    for left, right in pairs:
        for key in ('supports_sha256', 'twigs_sha256', 'budget'):
            assert manifests[left][key] == manifests[right][key]
        for a, b in zip(manifests[left]['placements'], manifests[right]['placements']):
            for key in ('id', 'origin_m', 'axes'):
                assert a[key] == b[key]
        assert exports[left]['channel_sha256']['RF2_Twig'] == exports[right]['channel_sha256']['RF2_Twig']
    repeat_pairs = ([('leaves-144', 'repeat-144'), ('leaves-192', 'repeat-192')] if args.density else
                    [(base, 'repeat-'+base) for base in ('small', 'large', 'efficient-080', 'efficient-100')])
    for base, repeated in repeat_pairs:
        for key in ('metrics', 'supports_sha256', 'placements_sha256', 'twigs_sha256'):
            assert manifests[base][key] == manifests[repeated][key]
        assert exports[base]['channel_sha256'] == exports[repeated]['channel_sha256']
    if args.density:
        for key in ('metrics', 'supports_sha256', 'placements_sha256', 'twigs_sha256'):
            assert manifests['legacy-96'][key] == manifests['base-96'][key]
        assert exports['legacy-96']['channel_sha256'] == exports['base-96']['channel_sha256']
        previous_leaves = manifests['base-96']['placements']
        for name in ('leaves-120', 'leaves-144', 'leaves-192'):
            m = manifests[name]
            for key in ('supports_sha256', 'twigs_sha256'):
                assert m[key] == manifests['base-96'][key]
            assert m['placements'][:len(previous_leaves)] == previous_leaves
            assert exports[name]['channel_sha256']['RF2_Twig'] == exports['base-96']['channel_sha256']['RF2_Twig']
            assert exports[name]['material_properties_sha256'] == exports['base-96']['material_properties_sha256']
            previous_leaves = m['placements']
    seed_base = 'leaves-144' if args.density else 'efficient-100'
    assert manifests['control-seed']['supports_sha256'] != manifests[seed_base]['supports_sha256']
    assert len({m['cameras_sha256'] for m in manifests.values()}) == 1
    cameras = json.loads((output/'reference/cameras.json').read_text())
    masks = {name: foliage_masks(output/name/'branch.glb', cameras) for name in manifests}
    projected = {name: compare_masks(masks['reference'], m) for name, m in masks.items()}
    for name in (entry['id'] for entry in entries if entry['capture']):
        folder = output/name/'masks'
        folder.mkdir()
        for view, mask in masks[name].items():
            mask.save(folder/(view+'.png'))
    assets = ROOT/'godot'/asset_namespace
    assets.mkdir(exist_ok=True)
    for entry in entries:
        shutil.copy2(output/entry['id']/'branch.glb', assets/(entry['id']+'.glb'))
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
    assert ref['source_files_sha256'] == {name: sha(Path(ref['source'])/name) for name in ref['source_files_sha256']}
    summary = {'version': version, 'sources_sha256': hashes, 'runner_python': sys.version,
        'reference_sha256': sha(reference), 'molds_file_sha256': sha(molds),
        'same_final_q3_wood': True, 'source_unchanged': True, 'same_cameras': True,
        'pair_same_supports_roots_axes_budget': not args.density,
        'density_same_supports_and_surviving_leaves': args.density,
        'reconstructs_0_1_1': args.density,
        'repeats': [base for base, _ in repeat_pairs], 'seed_control': True,
        'cases': {name: {key: m[key] for key in ('metrics', 'budget', 'leaf_count', 'group_count', 'sampling', 'contacts',
            'connection_lengths_m', 'molds_exported', 'triangle_limits', 'generation_before_render_export_s', 'total_s', 'glb_bytes')}
            for name, m in manifests.items() if m.get('version') == version},
        'exports': exports, 'projected_foliage': projected, 'projection_resolution': 256,
        'godot': report, 'visual_captures_generated': args.visual, 'capture_visible_pixels': visible,
        'visual_acceptance': 'pending', 'rf3_started': False}
    write(output/'summary.json', summary)
    gallery(output, args.visual, args.density)
    print('Moldes RF2 verificados técnicamente; revisión visual pendiente: '+str(output/'index.html'))


if __name__ == '__main__':
    main()
