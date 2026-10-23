#!/usr/bin/env python3
"""Q1b: ramas largas/gruesas, tres secundarias, regresión y referencias 0.1/0.2."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'scripts'))
from treegen.runner import BLENDER, execute, batch, write_json
from treegen.contracts import load_spec, SCHEMA
from treegen.evaluation import validate_result
from treegen.quality import validate_q1
from generate_f1 import generate

FOCUS = ['viejo-00', 'viejo-03', 'viejo-09', 'adulto-00', 'joven-00']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/q1b/acceptance')
    parser.add_argument('--base', type=Path, default=ROOT/'artifacts/f2/lote-final')
    parser.add_argument('--q1', type=Path, default=ROOT/'artifacts/q1/acceptance/lote')
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONPATH=str(ROOT/'src'))
    blender = os.environ.get('BLENDER_BIN', BLENDER)

    def run(label, command):
        with (output/f'{label}.log').open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=120)
        if result.returncode:
            raise RuntimeError(f'{label}: '+(output/f'{label}.log').read_text()[-5000:])
        print(label+': OK', flush=True)

    run('unit-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    report = batch(ROOT/'presets/q1b-cases.json', output/'lote')
    if report['status'] != 'completed':
        raise ValueError('Lote Q1b incompleto')
    cases = json.loads((output/'lote/cases.json').read_text())
    for c in cases:
        for folder in (args.base, args.q1):
            old = json.loads((folder/c['id']/'manifest.json').read_text())
            assert old['spec']['seed'] == c['spec']['seed']
            assert old['spec']['parameters'] == c['spec']['parameters']
            validate_result(folder/c['id'])
    for label, folder in [('legacy', args.base), ('q1', args.q1), ('candidate', output/'lote')]:
        reference = json.loads((folder/'viejo-09/manifest.json').read_text())
        repeated = execute(reference['spec'], output/f'repeat-{label}', render=False)
        assert repeated['metrics']['geometry_sha256'] == reference['metrics']['geometry_sha256']
        assert repeated['structure_checks'] == reference['structure_checks']
    effects = generate(ROOT/'presets/v0.2.1/adulto.json', output/'parameter-effects', render=False, check_parameters=True)
    foliage = generate(ROOT/'presets/v0.2.1/adulto.json', output/'foliage-seed', render=False, foliage_seed=12345)
    assert effects['structure_checks'] == foliage['structure_checks']
    assert effects['metrics']['geometry_sha256'] != foliage['metrics']['geometry_sha256']
    edge_metrics = {}
    for label in ('minimum', 'maximum', 'thin-many', 'bare-depth1', 'one-primary-depth2'):
        spec = load_spec(ROOT/'presets/v0.2.1/adulto.json')
        if label in ('minimum', 'maximum'):
            spec['parameters'] = {k:r[label] for k,r in SCHEMA['properties']['parameters']['properties'].items()}
        elif label == 'thin-many':
            spec['parameters'].update(height_m=2, base_radius_m=.05, primary_branches=12,
                                      branch_length_ratio=.1, foliage_density=0)
        elif label == 'bare-depth1':
            spec['parameters'].update(max_depth=1, foliage_density=0)
        else:
            spec['parameters'].update(primary_branches=1, max_depth=2)
        edge_metrics[label] = execute(spec, output/label, render=False)['metrics']
    print('referencias, repetición, parámetros, semillas y extremos: OK', flush=True)
    diagnose = [blender, '--background', '--factory-startup', '--threads', '1', '--python-exit-code', '1',
                '--python', str(ROOT/'scripts/diagnose_structure.py'), '--']

    def diagnosis(label, folder, names):
        run(label, diagnose+['--batch', str(folder.resolve()), '--output', str(output/label), '--cases']+names)
        return {c['id']:c for c in json.loads((output/label/'diagnosis.json').read_text())['cases']}

    candidates = diagnosis('diagnosis', output/'lote', [c['id'] for c in cases])
    measures = {name:validate_q1(c) for name,c in candidates.items()}
    edges = diagnosis('diagnosis-edges', output, list(edge_metrics))
    edge_structure = {name:validate_q1(c) for name,c in edges.items()}
    measured_cases = [c['id'] for c in cases if c['id'].startswith('viejo')] + ['adulto-00', 'joven-00']
    legacy = diagnosis('diagnosis-base', args.base, measured_cases)
    q1 = diagnosis('diagnosis-q1', args.q1, FOCUS)
    comparisons = {}
    for name in measured_cases:
        before, after = (d[name]['summary'] for d in (legacy, candidates))
        keys = ['skeleton_width_xy_m', 'primary_length_total_m', 'curve_length_total_m', 'lower_primary_mean_radius_m']
        comparisons[name] = {'base':{k:before[k] for k in keys},
                             'candidate':{k:after[k] for k in keys},
                             'ratio_to_base':{k:after[k]/before[k] for k in keys}}
        if name in q1:
            middle = q1[name]['summary']
            comparisons[name].update(q1={k:middle[k] for k in keys},
                                     ratio_to_q1={k:after[k]/middle[k] for k in keys})
        # Recuperar extensión y peso de los tres viejos que motivaron la revisión.
        # Las siete semillas restantes se miden sin ajustar las reglas a ellas.
        if name in FOCUS and name.startswith('viejo'):
            for k in ('skeleton_width_xy_m', 'primary_length_total_m', 'lower_primary_mean_radius_m'):
                assert after[k] >= .95*before[k], (name, k, after[k]/before[k])
    run('comparison', [blender, '--background', '--factory-startup', '--threads', '1', '--python-exit-code', '1',
        '--python', str(ROOT/'blender/render_comparison.py'), '--', '--base', str(args.base.resolve()),
        '--reference', str(args.q1.resolve()), '--candidate', str(output/'lote'),
        '--output', str(output/'comparison'), '--cases']+FOCUS)
    command = [sys.executable, str(ROOT/'scripts/verify_f2.py'), '--batch', str(output/'lote'),
               '--output', str(output/'godot'), '--asset-dir', 'q1b']
    if args.visual:
        command.append('--visual')
    run('godot', command)
    write_json(output/'summary.json', {'technical_passed':True, 'user_visual_acceptance':'pending',
        'stage':'Q1b', 'algorithm_version':'0.2.1', 'same_seeds_and_parameters':True,
        'references_reproduced':['0.1.0', '0.2.0'], 'repeated_geometry':True, 'cases':measures,
        'shape_comparisons':comparisons, 'parameter_effects':effects['parameter_effect_checks'],
        'foliage_seed_preserves_curves':True, 'edge_metrics':edge_metrics, 'edge_structure':edge_structure,
        'batch':report, 'godot':json.loads((output/'godot/summary.json').read_text())['godot'],
        'visual_captures_generated':args.visual,
        'shared_cameras':{c:json.loads((output/'comparison'/c/'cameras.json').read_text())['same_cameras'] for c in FOCUS}})
    print('Q1b: comprobaciones técnicas terminadas; valoración estética pendiente del usuario.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, AssertionError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f'Q1b FALLÓ: {exc}', file=sys.stderr)
        sys.exit(1)
