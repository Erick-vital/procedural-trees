#!/usr/bin/env python3
"""Verifica el ensayo acotado guardado, repetición e importación/capturas Godot."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from treegen.runner import execute, BLENDER
from treegen.evaluation import validate_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--base', type=Path, default=ROOT/'artifacts/q3/acceptance/lote')
    parser.add_argument('--cameras-root', type=Path, default=ROOT/'artifacts/q3/acceptance/comparison')
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    study, base = args.study.resolve(), args.base.resolve()
    cases = list(json.loads((study/'summary.json').read_text()))
    output = study/'verification'
    output.mkdir(exist_ok=False)
    env = dict(os.environ, ARBOLES_FUSION_STUDY=str(study), XDG_DATA_HOME=str(output/'xdg/data'),
               XDG_CONFIG_HOME=str(output/'xdg/config'), XDG_CACHE_HOME=str(output/'xdg/cache'))

    def run(label, command):
        with (output/f'{label}.log').open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        text = (output/f'{label}.log').read_text()
        if result.returncode or 'SCRIPT ERROR:' in text or '\nERROR:' in text:
            raise RuntimeError(label+': '+text[-3500:])
        print(label+': OK', flush=True)
        return text.strip()

    blender = os.environ.get('BLENDER_BIN', BLENDER)
    def command(script, *arguments):
        return [blender, '--background', '--factory-startup', '--threads', '1', '--python-exit-code', '1',
                '--python', str(ROOT/script), '--', *map(str, arguments)]

    validations = {case: validate_result(study/case/'candidate') for case in cases}
    run('saved-meshes', command('blender/verify_fusion.py', '--study', study, '--base', base))
    first = 'viejo-09'
    original = json.loads((base/first/'manifest.json').read_text())
    repeated_q3 = execute(original['spec'], output/'repeat-q3', render=False)
    assert repeated_q3['metrics']['geometry_sha256'] == original['metrics']['geometry_sha256']
    print('Q3 reconstruida con geometría idéntica: OK', flush=True)
    run('repeat-fusion', command('blender/experiment_fusion.py', '--source', base/first,
        '--output', output/'repeat-fusion', '--cameras', args.cameras_root/first/'cameras.json'))
    repeated = json.loads((output/'repeat-fusion/candidate/manifest.json').read_text())
    reference = json.loads((study/first/'candidate/manifest.json').read_text())
    validate_result(output/'repeat-fusion/candidate')
    assert repeated['metrics'] == reference['metrics'] and repeated['postprocess'] == reference['postprocess']
    print('Fusión repetida con geometría idéntica: OK', flush=True)
    assets = ROOT/'godot/q3-fusion'
    assets.mkdir(exist_ok=True)
    config = []
    for case in cases:
        framing = json.loads((study/case/'reference-lock.json').read_text())['framing']
        for label, folder, images in (('base', base/case, study/case/'base'),
                                       ('fused', study/case/'candidate', study/case/'fused')):
            name = case+'-'+label
            shutil.copy2(folder/'tree.glb', assets/f'{name}.glb')
            config.append({'id': name, 'manifest': str(folder/'manifest.json'), 'output': str(images), 'framing': framing})
    (study/'godot-input.json').write_text(json.dumps(config, indent=2)+'\n')
    godot = os.environ.get('GODOT_BIN', '/home/tao/repos/godot/openworld-forever/.tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
    assert run('godot-version', [godot, '--version']) == '4.7.2.stable.official.ed1daf0bf'
    run('godot-import', [godot, '--headless', '--path', str(ROOT/'godot'), '--editor', '--import'])
    run('godot-headless', [godot, '--headless', '--path', str(ROOT/'godot'), '--script', 'res://verify_fusion.gd'])
    if args.visual:
        run('godot-visual', [godot, '--path', str(ROOT/'godot'), '--script', 'res://verify_fusion.gd', '--', '--visual'])
    report = json.loads((study/'godot-report.json').read_text())
    assert report['passed'] and len(report['assets']) == len(config)
    for case in cases:
        assert report['assets'][case+'-base']['cameras'] == report['assets'][case+'-fused']['cameras']
    summary = {'export_validation': validations, 'q3_reproduced': True, 'fusion_reproduced': True,
               'saved_meshes': json.loads((study/'saved-mesh-verification.json').read_text()),
               'godot': report, 'godot_visual_captures_generated': args.visual,
               'godot_same_cameras_per_pair': True}
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')


if __name__ == '__main__':
    main()
