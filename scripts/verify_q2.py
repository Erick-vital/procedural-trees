#!/usr/bin/env python3
"""Q2 sobre Q1b: copa, independencia de madera, extremos, comparación y Godot."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'scripts'))
from treegen.contracts import load_spec, SCHEMA
from treegen.runner import BLENDER, batch, execute, write_json
from treegen.quality import validate_q1
from treegen.evaluation import validate_result
from generate_f1 import generate

FOCUS = ['viejo-00', 'viejo-03', 'viejo-09', 'adulto-00', 'joven-00']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/q2/acceptance')
    parser.add_argument('--base', type=Path, default=ROOT/'artifacts/q1b/acceptance/lote')
    parser.add_argument('--visual', action='store_true')
    args = parser.parse_args()
    output, base = args.output.resolve(), args.base.resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONPATH=str(ROOT/'src'))
    blender = os.environ.get('BLENDER_BIN', BLENDER)

    def run(label, command):
        with (output/f'{label}.log').open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        if result.returncode:
            raise RuntimeError(label+': '+(output/f'{label}.log').read_text()[-5000:])
        print(label+': OK', flush=True)

    def blender_script(script, *arguments):
        return [blender, '--background', '--factory-startup', '--threads', '1', '--python-exit-code', '1',
                '--python', str(ROOT/script), '--', *arguments]

    run('unit-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    report = batch(ROOT/'presets/q2-cases.json', output/'lote')
    assert report['status'] == 'completed'
    cases = json.loads((output/'lote/cases.json').read_text())
    for c in cases:
        validate_result(base/c['id'])
        old = json.loads((base/c['id']/'manifest.json').read_text())
        assert c['spec']['seed'] == old['spec']['seed']
        assert all(v == old['spec']['parameters'][k] for k,v in c['spec']['parameters'].items() if not k.startswith('foliage'))
    # Control con todos los parámetros de Q1b, aislando el cambio de algoritmo.
    controlled = json.loads((ROOT/'presets/q2-controlled-cases.json').read_text())
    for c in controlled:
        if c['id'] in FOCUS:
            old = json.loads((base/c['id']/'manifest.json').read_text())
            assert c['spec']['parameters'] == old['spec']['parameters']
            execute(c['spec'], output/'controlled'/c['id'], render=False)
    reference = json.loads((base/'viejo-09/manifest.json').read_text())
    repeated_base = execute(reference['spec'], output/'q1b-repeat', render=False)
    assert repeated_base['metrics']['geometry_sha256'] == reference['metrics']['geometry_sha256']
    for path in ('blender/oak_nodes.py', 'blender/oak_nodes_v2.py', 'blender/oak_nodes_v21.py'):
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == reference['sources_sha256'][path]
    reference = json.loads((output/'lote/viejo-09/manifest.json').read_text())
    repeated = execute(reference['spec'], output/'repeat', render=False)
    assert repeated['metrics']['geometry_sha256'] == reference['metrics']['geometry_sha256']
    assert repeated['crown_checks'] == reference['crown_checks']
    effects = generate(ROOT/'presets/v0.3.0/adulto.json', output/'parameter-effects', render=False, check_parameters=True)
    foliage = generate(ROOT/'presets/v0.3.0/adulto.json', output/'foliage-seed', render=False, foliage_seed=12345)
    assert effects['structure_checks'] == foliage['structure_checks']
    assert effects['normalization'] == foliage['normalization']
    assert effects['crown_checks']['wood_geometry_sha256'] == foliage['crown_checks']['wood_geometry_sha256']
    assert effects['metrics']['geometry_sha256'] != foliage['metrics']['geometry_sha256']
    independence = {'seed':True}
    for label, changes in [('density-zero', {'foliage_density':0}), ('scale', {'foliage_scale_m':2.2}), ('density-full', {'foliage_density':1})]:
        spec = load_spec(ROOT/'presets/v0.3.0/adulto.json')
        spec['parameters'].update(changes)
        changed = execute(spec, output/f'foliage-{label}', render=False)
        assert changed['crown_checks']['wood_geometry_sha256'] == effects['crown_checks']['wood_geometry_sha256']
        assert changed['normalization'] == effects['normalization']
        independence[label] = True
    edges = {}
    for label in ('minimum', 'maximum', 'thin-many', 'bare-depth1', 'one-primary-depth2', 'short-big-crown'):
        spec = load_spec(ROOT/'presets/v0.3.0/adulto.json')
        if label in ('minimum','maximum'):
            spec['parameters'] = {k:r[label] for k,r in SCHEMA['properties']['parameters']['properties'].items()}
        elif label == 'thin-many':
            spec['parameters'].update(height_m=2, base_radius_m=.05, primary_branches=12, branch_length_ratio=.1, foliage_density=0)
        elif label == 'bare-depth1':
            spec['parameters'].update(max_depth=1, foliage_density=0)
        elif label == 'one-primary-depth2':
            spec['parameters'].update(primary_branches=1, max_depth=2)
        else:
            spec['parameters'].update(height_m=2, foliage_scale_m=3, foliage_density=1)
        m = execute(spec, output/label, render=False)
        edges[label] = {'metrics':m['metrics'], 'crown_checks':m['crown_checks'], 'normalization':m['normalization']}
        bounds = m['crown_checks']['leaf_bounds_blender']
        if bounds:
            assert bounds[0][2] >= -1e-5 and bounds[1][2] <= spec['parameters']['height_m']+1e-5
    print('repetición, diez parámetros, independencia de madera y seis extremos: OK', flush=True)
    run('diagnosis', blender_script('scripts/diagnose_structure.py', '--batch', str(output/'lote'),
         '--output', str(output/'diagnosis'), '--cases', *[c['id'] for c in cases]))
    diagnosis = json.loads((output/'diagnosis/diagnosis.json').read_text())
    measures = {c['id']:validate_q1(c) for c in diagnosis['cases']}
    run('diagnosis-edges', blender_script('scripts/diagnose_structure.py', '--batch', str(output),
         '--output', str(output/'diagnosis-edges'), '--cases', *edges))
    edge_measures = {c['id']:validate_q1(c) for c in json.loads((output/'diagnosis-edges/diagnosis.json').read_text())['cases']}
    run('diagnosis-base', blender_script('scripts/diagnose_structure.py', '--batch', str(base),
         '--output', str(output/'diagnosis-base'), '--cases', *[c['id'] for c in cases]))
    before = {c['id']:c for c in json.loads((output/'diagnosis-base/diagnosis.json').read_text())['cases']}
    tilts = {c['id']:max(abs(a['inclination_final_deg']-b['inclination_final_deg']) for a,b in zip(c['curves'],before[c['id']]['curves'])) for c in diagnosis['cases']}
    for label, folder, names in [('inspection', output/'lote', [c['id'] for c in cases]), ('inspection-controlled', output/'controlled', FOCUS)]:
        run(label, blender_script('blender/inspect_q2.py', '--base', str(base), '--candidate', str(folder), '--output', str(output/label), '--cases', *names))
    inspection = json.loads((output/'inspection/report.json').read_text())
    for name, values in inspection['cases'].items():
        crown = values['candidate']
        assert crown['occupied_height_bins'] >= 2
        if not name.startswith('joven'):
            assert crown['occupied_azimuth_sectors'] >= 6
    run('comparison', blender_script('blender/render_comparison.py', '--base', str(base), '--reference', str(output/'controlled'),
         '--candidate', str(output/'lote'), '--output', str(output/'comparison'), '--cases', *FOCUS))
    command = [sys.executable, str(ROOT/'scripts/verify_f2.py'), '--batch', str(output/'lote'), '--output', str(output/'godot'), '--asset-dir', 'q2']
    if args.visual:
        command.append('--visual')
    run('godot', command)
    write_json(output/'summary.json', {'stage':'Q2', 'algorithm_version':'0.3.0', 'technical_passed':True,
        'user_visual_acceptance':'pending', 'base_version':'0.2.1', 'base_reproduced':True,
        'same_native_structure':True, 'same_wood_xy':True, 'repeated_geometry':True,
        'foliage_changes_preserve_wood':independence, 'parameter_effects':effects['parameter_effect_checks'],
        'cases':measures, 'max_final_inclination_change_deg':tilts, 'edges':edges, 'edge_structure':edge_measures,
        'inspection':inspection, 'batch':report, 'godot':json.loads((output/'godot/summary.json').read_text())['godot'],
        'visual_captures_generated':args.visual,
        'shared_cameras':{c:json.loads((output/'comparison'/c/'cameras.json').read_text())['same_cameras'] for c in FOCUS}})
    print('Q2: comprobaciones técnicas completadas; revisar copas y proporciones con el usuario.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, AssertionError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print('Q2 FALLÓ: '+str(exc), file=sys.stderr)
        sys.exit(1)
