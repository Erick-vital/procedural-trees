#!/usr/bin/env python3
"""Ejecuta intentos acotados de Easy Tree/Sapling sin alterar sus instalaciones."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from treegen.runner import BLENDER


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'presets/addon-comparison.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--only', nargs='+')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, XDG_DATA_HOME=str(output/'xdg/data'), XDG_CONFIG_HOME=str(output/'xdg/config'),
        XDG_CACHE_HOME=str(output/'xdg/cache'))
    results = {}
    for attempt in config['attempts']:
        name = attempt['id']
        if args.only and name not in args.only:
            continue
        path = output/(name+'.json')
        path.write_text(json.dumps(attempt, indent=2)+'\n')
        command = [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup', '--threads', '1',
            '--python-exit-code', '1', '--python', str(ROOT/'blender/addon_comparison.py'), '--',
            '--attempt', str(path), '--output', str(output/name)]
        log = output/(name+'.log')
        try:
            with log.open('w') as stream:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT,
                    timeout=config['limits']['timeout_seconds'])
            if result.returncode:
                raise RuntimeError(log.read_text()[-3000:])
            row = json.loads((output/name/'manifest.json').read_text())
            results[name] = {'status': 'generated', 'triangles': row['metrics']['triangles'],
                'within_budget': row['within_budget'], 'manifest': str(output/name/'manifest.json')}
        except (subprocess.TimeoutExpired, RuntimeError) as exc:
            results[name] = {'status': 'failed', 'reason': str(exc)}
        (output/'attempts.json').write_text(json.dumps(results, indent=2)+'\n')
        print(name+': '+json.dumps(results[name]), flush=True)


if __name__ == '__main__':
    main()
