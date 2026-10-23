#!/usr/bin/env python3
"""Prueba acotada de integración F0, con límites de tiempo por proceso."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from treegen.contracts import load_spec, spec_hash

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--visual', action='store_true', help='Renderiza el asset en una ventana Godot y guarda PNG')
args = parser.parse_args()
out = ROOT / 'artifacts/f0'
out.mkdir(parents=True, exist_ok=True)
blender = os.environ.get('BLENDER_BIN', '/home/tao/repos/blender/.tools/blender-5.2.1-linux-x64/blender')
godot = os.environ.get('GODOT_BIN', '/home/tao/repos/godot/openworld-forever/.tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), ARBOLES_F0_OUTPUT=str(out),
           XDG_DATA_HOME=str(out / 'xdg/data'), XDG_CONFIG_HOME=str(out / 'xdg/config'),
           XDG_CACHE_HOME=str(out / 'xdg/cache'))


def run(label, command, timeout=120):
    log = out / f'{label}.log'
    with log.open('w') as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
    output = log.read_text()
    if result.returncode or 'SCRIPT ERROR:' in output or '\nERROR:' in output:
        raise RuntimeError(f'{label}: código {result.returncode}\n{output[-6000:]}')
    print(f'{label}: OK', flush=True)
    return output.strip()


try:
    version = run('godot-version', [godot, '--version'])
    if version != '4.7.2.stable.official.ed1daf0bf':
        raise ValueError(f'Versión Godot no fijada: {version}')
    run('contracts', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    hashes = {name: spec_hash(load_spec(ROOT / f'presets/{name}.json')) for name in ('joven', 'adulto')}
    command = [blender, '--background', '--factory-startup', '--threads', '1', '--python-exit-code', '1',
               '--python', str(ROOT / 'blender/probe.py'), '--', str(out)]
    run('blender-first', command)
    first = json.loads((out / 'blender-report.json').read_text())
    run('blender-repeat', command)
    second = json.loads((out / 'blender-report.json').read_text())
    if first['geometry_sha256'] != second['geometry_sha256']:
        raise ValueError('Geometría no reproducible')
    shutil.copy2(out / 'probe.glb', ROOT / 'godot/probe.glb')
    run('godot-import', [godot, '--headless', '--path', str(ROOT / 'godot'), '--editor', '--import'])
    run('godot-verify', [godot, '--headless', '--path', str(ROOT / 'godot'),
                         '--script', 'res://verify_probe.gd'])
    if args.visual:
        run('godot-visual', [godot, '--path', str(ROOT / 'godot'), '--script',
                             'res://verify_probe.gd', '--', '--visual'])
    report = json.loads((out / 'godot-report.json').read_text())
    if not report['passed']:
        raise ValueError('Godot rechazó el asset')
    sources = [ROOT / p for p in ('blender/probe.py', 'godot/verify_probe.gd', 'schemas/tree-spec.schema.json',
                                  'src/treegen/contracts.py', 'scripts/verify_f0.py', 'requirements.txt')]
    summary = {'python': sys.version, 'presets_sha256': hashes, 'blender': second, 'godot': report,
               'repeated_geometry_matches': True, 'visual_capture_generated': args.visual,
               'sources_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(f'F0: integración verificada; resultados en {out}')
except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
    print(f'F0 FALLÓ: {exc}', file=sys.stderr)
    sys.exit(1)
