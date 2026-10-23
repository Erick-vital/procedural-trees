#!/usr/bin/env python3
"""Integración real HTTP → ejecutor → Blender; fallo y rechazo de contrato."""
import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from treegen.api import make_server
from treegen.contracts import load_spec
from treegen.runner import write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/f2/api-verification')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    server = make_server(output / 'jobs', 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    def post(body):
        request = Request(base + '/jobs', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=5) as response:
            if response.status != 202:
                raise ValueError('Se esperaba 202')
            return json.load(response)
    def get(path):
        with urlopen(base + path, timeout=5) as response:
            return json.load(response)
    def finish(job):
        deadline = time.monotonic() + 130
        while time.monotonic() < deadline:
            state = get(job['status_url'])
            if state['status'] in ('completed', 'failed'):
                return state
            time.sleep(.1)
        raise TimeoutError('Trabajo API no terminó')
    old_blender = os.environ.get('BLENDER_BIN')
    try:
        spec = load_spec(ROOT / 'presets/adulto.json')
        started = time.monotonic()
        job = post({'spec': spec, 'render': False})
        latency = time.monotonic() - started
        state = finish(job)
        if state['status'] != 'completed':
            raise ValueError(state)
        manifest = get(state['result'])
        if manifest['status'] != 'completed' or 'export_validation' not in manifest:
            raise ValueError('Resultado no validado')
        os.environ['BLENDER_BIN'] = '/no-existe/blender'
        failed = post({'spec': spec, 'render': False})
        failure = finish(failed)
        if failure['status'] != 'failed' or get(failed['status_url'] + '/manifest.json')['status'] != 'failed':
            raise ValueError('Fallo no propagado')
        try:
            post({'spec': {}})
            raise ValueError('Contrato inválido aceptado')
        except HTTPError as exc:
            if exc.code != 400:
                raise
            exc.close()
        write_json(output / 'summary.json', {'passed': True, 'accepted_http': 202,
                   'post_latency_seconds': latency, 'completed': state, 'failure': failure, 'invalid_http': 400})
        print('API: generación real, consulta de resultado, fallo y rechazo de contrato: OK')
    finally:
        if old_blender is None:
            os.environ.pop('BLENDER_BIN', None)
        else:
            os.environ['BLENDER_BIN'] = old_blender
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == '__main__':
    main()
