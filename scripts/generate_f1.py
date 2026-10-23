#!/usr/bin/env python3
"""Ejecutar el prototipo F1 con un preset validado, sin API ni cola de trabajos."""
import argparse
import json
from importlib.metadata import version
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from treegen.contracts import load_spec, spec_hash
from treegen.seeds import derive_seed


def generate(preset, output, render=True, seed=None, foliage_seed=None, check_parameters=False):
    spec = load_spec(preset)
    if seed is not None:
        spec['seed'] = seed
    digest = spec_hash(spec)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'manifest.json').unlink(missing_ok=True)
    job = {'spec': spec, 'spec_sha256': digest, 'output': str(output), 'render': render,
           'check_parameters': check_parameters,
           'runner_python': sys.version, 'jsonschema_version': version('jsonschema'),
           'seeds': {stream: derive_seed(spec['seed'], stream) for stream in ('structure', 'foliage')}}
    if foliage_seed is not None:
        if type(foliage_seed) is not int or not 0 <= foliage_seed < 2147483647:
            raise ValueError('Semilla de follaje fuera de rango')
        job['seeds']['foliage'] = foliage_seed
    (output / 'input.json').write_text(json.dumps(job, indent=2) + '\n')
    blender = os.environ.get('BLENDER_BIN', '/home/tao/repos/blender/.tools/blender-5.2.1-linux-x64/blender')
    command = [blender, '--background', '--factory-startup', '--threads', '1', '--python-exit-code', '1',
               '--python', str(ROOT / 'blender/generate_oak.py'), '--', str(output / 'input.json')]
    with (output / 'blender.log').open('w') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    if result.returncode:
        raise RuntimeError((output / 'blender.log').read_text()[-6000:])
    manifest = json.loads((output / 'manifest.json').read_text())
    print(f"{output.name}: {manifest['metrics']['triangles']} triángulos, {manifest['metrics']['height_m']:.3f} m", flush=True)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preset', type=Path, default=ROOT / 'presets/adulto.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/f1/adulto')
    parser.add_argument('--no-render', action='store_true')
    args = parser.parse_args()
    try:
        generate(args.preset, args.output, not args.no_render)
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f'F1 FALLÓ: {exc}', file=sys.stderr)
        sys.exit(1)
