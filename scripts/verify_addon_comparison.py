#!/usr/bin/env python3
"""Reproduce intentos, repite candidatos y compara seis árboles en Godot."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from treegen.evaluation import validate_glb, validate_result
from treegen.foliage import digest
from treegen.runner import BLENDER
from verify_foliage_unit import GODOT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def validate(folder, target_height):
    m = json.loads((folder/'manifest.json').read_text())
    metrics = m['metrics']
    report = validate_glb(folder/'tree.glb', {'parameters': {'height_m': target_height}})
    assert report['triangles'] == metrics['triangles'] and report['materials'] == metrics['triangles_by_material']
    assert abs(metrics['height_m']-target_height) < .001 and abs(metrics['bounds_blender'][0][2]) < .001
    raw = (folder/'tree.glb').read_bytes()
    length = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+length])
    assert len(doc['materials']) == 2 and not doc.get('textures')
    colors = {'Oak_Bark': [.24, .105, .045, 1], 'Oak_Leaves': [.23, .43, .065, 1]}
    for material in doc['materials']:
        assert material.get('alphaMode', 'OPAQUE') == 'OPAQUE'
        assert material.get('doubleSided'), 'Material de una sola cara'
        rgba = material['pbrMetallicRoughness']['baseColorFactor']
        assert all(abs(a-b) < 1e-5 for a, b in zip(rgba, colors[material['name']]))
    report['opaque_common_palette'] = True
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=ROOT/'presets/addon-comparison.json')
    parser.add_argument('--q3', type=Path, default=ROOT/'artifacts/q3/acceptance/lote')
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out/'logs').mkdir()
    tracked = ['presets/addon-comparison.json', 'scripts/compare_addons.py', 'scripts/verify_addon_comparison.py',
        'blender/addon_comparison.py', 'blender/render_addon_comparison.py', 'godot/verify_addon_comparison.gd',
        'godot/verify_oak.gd', 'blender/foliage_lab.py', 'blender/generate_oak.py', 'src/treegen/foliage.py',
        'src/treegen/evaluation.py']
    hashes = {name: sha(ROOT/name) for name in tracked}
    env = dict(os.environ, ARBOLES_ADDON_STUDY=str(out), PYTHONPATH=str(ROOT/'src'),
        XDG_DATA_HOME=str(out/'xdg/data'), XDG_CONFIG_HOME=str(out/'xdg/config'), XDG_CACHE_HOME=str(out/'xdg/cache'))

    def run(label, command, timeout=120):
        path = out/'logs'/(label+'.log')
        with path.open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        content = path.read_text()
        if result.returncode or 'SCRIPT ERROR:' in content or '\nERROR:' in content:
            raise RuntimeError(label+': '+content[-4000:])
        print(label+': OK', flush=True)
        return content.strip()

    run('tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    q3_hashes = {}
    for age, case in config['references'].items():
        validate_result(args.q3/case)
        q3_hashes[age] = {name: sha(args.q3/case/name) for name in ('tree.blend', 'tree.glb', 'manifest.json')}
    # El supervisor tiene un límite agregado; cada Blender conserva 120 s.
    run('attempts', [sys.executable, str(ROOT/'scripts/compare_addons.py'), '--config', str(args.config.resolve()),
        '--output', str(out/'attempts')], timeout=120*len(config['attempts']))
    attempts = json.loads((out/'attempts/attempts.json').read_text())
    selected = [config['selection'][age][engine] for age in ('adulto', 'viejo') for engine in ('easy', 'sapling')]
    assert all(attempts[name]['status'] == 'generated' and attempts[name]['within_budget'] for name in selected)
    unexpected = [name for name, value in attempts.items() if value['status'] == 'failed' and name != 'easy-viejo-initial']
    assert not unexpected, unexpected
    run('repeats', [sys.executable, str(ROOT/'scripts/compare_addons.py'), '--config', str(args.config.resolve()),
        '--output', str(out/'repeats'), '--only', *selected], timeout=120*len(selected))
    repeat_checks = {}
    for name in selected:
        a, b = [json.loads((out/folder/name/'manifest.json').read_text()) for folder in ('attempts', 'repeats')]
        assert a['metrics'] == b['metrics'] and a['native_geometry_sha256'] == b['native_geometry_sha256']
        assert a['addon_sources_unchanged'] and b['addon_sources_unchanged']
        repeat_checks[name] = {'geometry_sha256': a['metrics']['geometry_sha256'], 'native_geometry_sha256': a['native_geometry_sha256']}
    models = []
    for age in ('adulto', 'viejo'):
        models.append({'id': 'q3-'+age, 'engine': 'q3', 'age': age, 'folder': str((args.q3/config['references'][age]).resolve())})
        for engine in ('easy', 'sapling'):
            models.append({'id': engine+'-'+age, 'engine': engine, 'age': age,
                'folder': str(out/'attempts'/config['selection'][age][engine])})
    write(out/'models.json', models)
    run('render', [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup', '--threads', '1',
        '--python-exit-code', '1', '--python', str(ROOT/'blender/render_addon_comparison.py'), '--',
        '--models', str(out/'models.json'), '--output', str(out/'comparison')])
    exports = {item['id']: validate(out/'comparison'/item['id'], 10 if item['age'] == 'adulto' else 9) for item in models}
    for age in ('adulto', 'viejo'):
        rig_hashes = {digest(json.loads((out/'comparison'/(engine+'-'+age)/'cameras.json').read_text())) for engine in ('q3', 'easy', 'sapling')}
        assert len(rig_hashes) == 1
    assets = ROOT/'godot/addon-comparison'
    assets.mkdir(exist_ok=True)
    entries = []
    for item in models:
        folder = out/'comparison'/item['id']
        shutil.copy2(folder/'tree.glb', assets/(item['id']+'.glb'))
        entries.append({'id': item['id'], 'folder': str(folder)})
    write(out/'godot-input.json', entries)
    godot = os.environ.get('GODOT_BIN', GODOT)
    assert run('godot-version', [godot, '--version']) == '4.7.2.stable.official.ed1daf0bf'
    run('godot-import', [godot, '--headless', '--path', str(ROOT/'godot'), '--editor', '--import'])
    command = [godot, '--path', str(ROOT/'godot'), '--script', 'res://verify_addon_comparison.gd']
    run('godot-headless', command[:1]+['--headless']+command[1:])
    report = json.loads((out/'godot-report.json').read_text())
    assert report['passed'] and len(report['assets']) == 6
    visible = {}
    if args.visual:
        for start in range(0, len(entries), 2):
            path, result_path = out/f'godot-input-{start}.json', out/f'godot-visual-{start}.json'
            write(path, entries[start:start+2])
            run('godot-visual-'+str(start), command+['--', '--visual', '--input='+str(path), '--report='+str(result_path)])
            partial = json.loads(result_path.read_text())
            assert partial['passed']
            for name, result in partial['assets'].items():
                assert result == report['assets'][name]
        for entry in entries:
            folder = Path(entry['folder'])
            for view in json.loads((folder/'cameras.json').read_text()):
                with Image.open(folder/('godot-'+view+'.png')) as original:
                    image = original.convert('RGB')
                    delta = ImageChops.difference(image, Image.new('RGB', image.size, image.getpixel((0, 0)))).convert('L')
                    pixels = sum(count for value, count in enumerate(delta.histogram()) if value > 8)
                    assert pixels > 100, (entry['id'], view)
                    visible[entry['id']+'/'+view] = pixels
    for age, case in config['references'].items():
        assert q3_hashes[age] == {name: sha(args.q3/case/name) for name in q3_hashes[age]}
    assert hashes == {name: sha(ROOT/name) for name in tracked}
    write(out/'summary.json', {'version': config['version'], 'sources_sha256': hashes, 'runner_python': sys.version,
        'config': config, 'attempts': attempts, 'repeat_checks': repeat_checks, 'exports': exports, 'godot': report,
        'q3_sources_sha256': q3_hashes, 'q3_sources_unchanged': True, 'same_cameras_per_age': True,
        'capture_visible_pixels': visible, 'visual_captures_generated': args.visual,
        'visual_acceptance': 'pending', 'runtime_generation_tested': False, 'rf3_started': False})
    print('Comparación verificada; evidencia en '+str(out))


if __name__ == '__main__':
    main()
