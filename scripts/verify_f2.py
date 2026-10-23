#!/usr/bin/env python3
"""Verificar un lote F2 existente, repetir un caso e importar los 30 GLB en Godot."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from treegen.evaluation import validate_result, compare
from treegen.runner import execute, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, default=ROOT / 'artifacts/f2/lote')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/f2/verification')
    parser.add_argument('--visual', action='store_true')
    parser.add_argument('--asset-dir', choices=('f2', 'q1', 'q1b', 'q2', 'q3', 'q3b'), default='f2')
    args = parser.parse_args()
    batch, output = args.batch.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    cases = json.loads((batch / 'cases.json').read_text())
    manifest = json.loads((batch / 'batch.json').read_text())
    if manifest['status'] != 'completed' or len(cases) != 30:
        raise ValueError('Lote incompleto')
    reports = {c['id']: validate_result(batch / c['id']) for c in cases}
    if len({r['geometry_sha256'] for r in reports.values()}) != 30:
        raise ValueError('Geometría duplicada')
    reference = cases[10]
    execute(reference['spec'], output / 'repeat')
    comparison = compare(batch / reference['id'], output / 'repeat', output / 'comparison')
    if not comparison['same_geometry'] or not comparison['same_spec'] or not comparison['same_sources']:
        raise ValueError('Repetición no reproducible')
    assets = ROOT / 'godot' / args.asset_dir
    assets.mkdir(exist_ok=True)
    for case in cases:
        shutil.copy2(batch / case['id'] / 'tree.glb', assets / f"{case['id']}.glb")
    env = dict(os.environ, ARBOLES_F2_OUTPUT=str(batch), ARBOLES_ASSET_PREFIX=f'res://{args.asset_dir}/', XDG_DATA_HOME=str(output / 'xdg/data'),
               XDG_CONFIG_HOME=str(output / 'xdg/config'), XDG_CACHE_HOME=str(output / 'xdg/cache'))
    godot = os.environ.get('GODOT_BIN', '/home/tao/repos/godot/openworld-forever/.tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
    def run(label, command):
        with (output / f'{label}.log').open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        text = (output / f'{label}.log').read_text()
        if result.returncode or 'SCRIPT ERROR:' in text or '\nERROR:' in text:
            raise RuntimeError(f'{label}: {text[-4000:]}')
        return text.strip()
    if run('version', [godot, '--version']) != '4.7.2.stable.official.ed1daf0bf':
        raise ValueError('Versión Godot distinta de la fijada')
    run('import', [godot, '--headless', '--path', str(ROOT / 'godot'), '--editor', '--import'])
    run('verify', [godot, '--headless', '--path', str(ROOT / 'godot'), '--script', 'res://verify_oak.gd'])
    if args.visual:
        run('visual', [godot, '--path', str(ROOT / 'godot'), '--script', 'res://verify_oak.gd', '--', '--visual'])
    godot_report = json.loads((batch / 'godot-report.json').read_text())
    if not godot_report['passed'] or len(godot_report['assets']) != 30:
        raise ValueError('Importación Godot incompleta')
    summary = {'passed': True, 'cases': reports, 'comparison': comparison, 'godot': godot_report,
               'visual_captures_generated': args.visual}
    write_json(output / 'summary.json', summary)
    print('F2: 30 GLB válidos, únicos e importados; repetición idéntica. Revisar capturas.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f'F2 FALLÓ: {exc}', file=sys.stderr)
        sys.exit(1)
