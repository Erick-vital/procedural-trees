#!/usr/bin/env python3
"""Casos fijos de aceptación F1; no implementa el lote de producción de F2."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from generate_f1 import ROOT, generate
sys.path.insert(0, str(ROOT / 'src'))
from treegen.contracts import load_spec, SCHEMA

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--visual', action='store_true')
args = parser.parse_args()
out = ROOT / 'artifacts/f1'
out.mkdir(parents=True, exist_ok=True)
(out / 'summary.json').unlink(missing_ok=True)
godot = os.environ.get('GODOT_BIN', '/home/tao/repos/godot/openworld-forever/.tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), ARBOLES_F1_OUTPUT=str(out),
           XDG_DATA_HOME=str(out / 'xdg/data'), XDG_CONFIG_HOME=str(out / 'xdg/config'),
           XDG_CACHE_HOME=str(out / 'xdg/cache'))


def run(label, command):
    path = out / f'{label}.log'
    with path.open('w') as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    text = path.read_text()
    if result.returncode or 'SCRIPT ERROR:' in text or '\nERROR:' in text:
        raise RuntimeError(f'{label}: {text[-6000:]}')
    print(f'{label}: OK', flush=True)
    return text.strip()


try:
    if run('godot-version', [godot, '--version']) != '4.7.2.stable.official.ed1daf0bf':
        raise ValueError('Versión Godot distinta a la fijada')
    run('unit-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    results = {}
    for name in ('joven', 'adulto', 'viejo'):
        results[name] = generate(ROOT / f'presets/v0.1.0/{name}.json', out / name, check_parameters=name == 'adulto')
    reference = results['adulto']
    repeated = generate(ROOT / 'presets/v0.1.0/adulto.json', out / 'repeat', render=False)
    assert reference['metrics']['geometry_sha256'] == repeated['metrics']['geometry_sha256']
    assert reference['structure_checks'] == repeated['structure_checks']
    foliage = generate(ROOT / 'presets/v0.1.0/adulto.json', out / 'foliage-seed', render=False, foliage_seed=12345)
    assert reference['structure_checks'] == foliage['structure_checks']
    assert reference['metrics']['geometry_sha256'] != foliage['metrics']['geometry_sha256']
    for seed in (30, 31):
        name = f'adulto-seed-{seed}'
        results[name] = generate(ROOT / 'presets/v0.1.0/adulto.json', out / name, render=False, seed=seed)
        assert reference['structure_checks']['structure_sha256'] != results[name]['structure_checks']['structure_sha256']
    for label in ('minimum', 'maximum', 'bare-depth1'):
        spec = copy.deepcopy(load_spec(ROOT / 'presets/v0.1.0/adulto.json'))
        if label == 'bare-depth1':
            spec['parameters'].update(max_depth=1, foliage_density=0)
        else:
            boundary = 'minimum' if label == 'minimum' else 'maximum'
            spec['parameters'] = {key: rule[boundary] for key, rule in SCHEMA['properties']['parameters']['properties'].items()}
        path = out / f'{label}-spec.json'
        path.write_text(json.dumps(spec, indent=2) + '\n')
        results[label] = generate(path, out / label, render=False)
    assert results['bare-depth1']['structure_checks']['secondary_branches'] == 0
    assert results['bare-depth1']['metrics']['triangles_by_material'].get('Oak_Leaves', 0) == 0
    assert len({results[name]['metrics']['geometry_sha256'] for name in ('adulto', 'adulto-seed-30', 'adulto-seed-31')}) == 3
    assets = ROOT / 'godot/f1'
    assets.mkdir(exist_ok=True)
    for name in ('joven', 'adulto', 'viejo'):
        shutil.copy2(out / name / 'tree.glb', assets / f'{name}.glb')
    run('godot-import', [godot, '--headless', '--path', str(ROOT / 'godot'), '--editor', '--import'])
    run('godot-verify', [godot, '--headless', '--path', str(ROOT / 'godot'), '--script', 'res://verify_oak.gd'])
    if args.visual:
        run('godot-visual', [godot, '--path', str(ROOT / 'godot'), '--script', 'res://verify_oak.gd', '--', '--visual'])
    report = {'passed': True, 'reproducible': True, 'foliage_seed_preserves_native_curves': True,
              'visual_captures_generated': args.visual, 'python': sys.version,
              'cases': {name: {'seed': m['spec']['seed'], 'metrics': m['metrics'],
                               'structure_checks': m['structure_checks']} for name, m in results.items()},
              'parameter_effects': reference['parameter_effect_checks'],
              'godot': json.loads((out / 'godot-report.json').read_text()),
              'sources_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                  [ROOT / name for name in ('blender/generate_oak.py', 'blender/oak_nodes.py',
                                    'scripts/generate_f1.py', 'scripts/verify_f1.py', 'src/treegen/seeds.py',
                                    'godot/verify_oak.gd', 'schemas/tree-spec.schema.json')]}}
    assert report['godot']['passed']
    (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print('F1: verificaciones automáticas completadas. Revisar visualmente las capturas.', flush=True)
except (AssertionError, ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
    print(f'F1 FALLÓ: {exc}', file=sys.stderr)
    sys.exit(1)
