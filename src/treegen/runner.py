"""Ejecutor secuencial compartido por CLI y API; un directorio nuevo por trabajo."""
from datetime import datetime, timezone
from importlib.metadata import version
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

from .contracts import ROOT, validate_spec, spec_hash, load_spec
from .seeds import derive_seed
from .evaluation import validate_result

BLENDER = '/home/tao/repos/blender/.tools/blender-5.2.1-linux-x64/blender'
VIEWS = ['front', 'side', 'top', 'perspective']


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def execute(spec, output, render=True, timeout=120, job_id=None, *, blueprint=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    job_id = job_id or str(uuid.uuid4())
    manifest = {'manifest_version': '1.0', 'job_id': job_id, 'status': 'running', 'started_at': timestamp()}
    write_json(output / 'manifest.json', manifest)
    started = time.monotonic()
    try:
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 600:
            raise ValueError('timeout debe estar entre 0 y 600 segundos')
        resolved = None
        if blueprint is not None:
            from .blueprints import load_blueprint, load_instance, resolve_blueprint
            definition = load_blueprint(blueprint) if isinstance(blueprint, (str, Path)) else blueprint
            instance = load_instance(spec) if isinstance(spec, (str, Path)) else spec
            resolved = resolve_blueprint(definition, instance)
            timeout = min(timeout, resolved['limits']['generation_seconds'])
            spec = resolved['base_spec']
            manifest.update(kind='blueprint', resolved_blueprint=resolved)
        elif isinstance(spec, (str, Path)):
            spec = load_spec(spec)
        pine = resolved is not None and resolved['base_spec']['algorithm'] == 'pine-whorls'
        if pine:
            from .blueprints import canonical_hash
            input_hash = canonical_hash(spec)
        else:
            validate_spec(spec)
            input_hash = spec_hash(spec)
        job = {'spec': spec, 'spec_sha256': input_hash, 'output': str(output), 'render': render,
               'runner_python': sys.version, 'jsonschema_version': version('jsonschema'),
               'seeds': {s: derive_seed(spec['seed'], s) for s in ('structure', 'foliage')}}
        if resolved is not None:
            job['resolved_blueprint'] = resolved
            job['seeds'] = resolved['base_seeds']
        job['timeout_seconds'] = timeout
        write_json(output / 'input.json', job)
        manifest.update(spec=spec, spec_sha256=job['spec_sha256'])
        write_json(output / 'manifest.json', manifest)
        command = [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup',
                   '--threads', '1', '--python-exit-code', '1', '--python',
                   str(ROOT / ('blender/generate_crossed_oak.py' if resolved and resolved['resolved_version'] == '1.4' else
                               'blender/generate_painted_oak.py' if resolved and resolved['resolved_version'] == '1.3' else
                               'blender/generate_painted_pine.py' if resolved and resolved['resolved_version'] == '1.2' else
                               'blender/generate_pine.py' if pine else
                               'blender/generate_blueprint.py' if resolved else 'blender/generate_oak.py')),
                   '--', str(output / 'input.json')]
        with (output / 'blender.log').open('w') as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise TimeoutError(f'Blender excedió {timeout} s; proceso y descendientes terminados')
        if code:
            raise RuntimeError(f'Blender terminó con código {code}; consultar blender.log: ' +
                               (output / 'blender.log').read_text()[-2000:])
        result = json.loads((output / 'manifest.json').read_text())
        if 'metrics' not in result:
            raise RuntimeError('Blender no produjo un manifiesto de resultados')
        result.update(manifest_version='1.0', job_id=job_id, started_at=manifest['started_at'],
                      required_views=list(result['cameras']) if render else [],
                      adapter_version=result.get('adapter_version', '1.0'), timeout_seconds=timeout,
                      duration_seconds=round(time.monotonic()-started, 3), finished_at=timestamp())
        # Procedencia de todos los componentes ejecutados, sin depender de Git.
        result['sources_sha256'].update({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / 'src/treegen').glob('*.py')) + [ROOT / 'schemas/tree-spec.schema.json']})
        if resolved is not None and isinstance(blueprint, (str, Path)):
            recipe_path = Path(blueprint).resolve()
            result['blueprint_file_sha256'] = hashlib.sha256(recipe_path.read_bytes()).hexdigest()
        # El adaptador TreeSpec histórico no emite este campo; ambos contratos
        # comparten el registro final de artefactos, sin cambiar su geometría.
        result.setdefault('files_sha256', {})
        if resolved is not None:
            result['files_sha256'].update({name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                                           for name in ('input.json', 'base-reference.json', 'cameras.json')})
        write_json(output / 'manifest.json', result)
        result['export_validation'] = validate_result(output)
        result['files_sha256'].update({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.iterdir()) if p.is_file() and p.suffix in ('.glb', '.blend', '.png')})
        write_json(output / 'manifest.json', result)
        return result
    except Exception as exc:
        manifest.update(status='failed', finished_at=timestamp(), duration_seconds=round(time.monotonic()-started, 3),
                        error={'type': type(exc).__name__, 'message': str(exc)})
        write_json(output / 'manifest.json', manifest)
        raise


def execute_blueprint(blueprint, instance, output, render=True, timeout=120):
    """Mismo ejecutor, fallos y timeout que los trabajos TreeSpec históricos."""
    return execute(instance, output, render, timeout, blueprint=blueprint)


def batch(cases_path, output, timeout=120):
    cases = json.loads(Path(cases_path).read_text())
    if len(cases) != 30 or len({c['id'] for c in cases}) != 30 or len({c['spec']['seed'] for c in cases}) != 30:
        raise ValueError('El lote requiere 30 ids y semillas distintos')
    for case in cases:
        if not case['id'].replace('-', '').isalnum():
            raise ValueError('Id de caso inválido')
        validate_spec(case['spec'])
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'cases.json', cases)
    results = []
    for case in cases:
        try:
            m = execute(case['spec'], output / case['id'], timeout=timeout)
            results.append({'id': case['id'], 'status': 'completed', 'spec_sha256': m['spec_sha256'],
                            'metrics': m['export_validation'], 'duration_seconds': m['duration_seconds']})
            print(f"{case['id']}: OK ({m['metrics']['triangles']} triángulos)", flush=True)
        except Exception as exc:
            results.append({'id': case['id'], 'status': 'failed', 'error': str(exc)})
            print(f"{case['id']}: FALLÓ: {exc}", flush=True)
        hashes = [r['metrics']['geometry_sha256'] for r in results if r['status'] == 'completed']
        report = {'status': 'running' if len(results) < 30 else ('completed' if len(hashes) == 30 and len(set(hashes)) == 30 else 'failed'),
                  'cases_sha256': hashlib.sha256(Path(cases_path).read_bytes()).hexdigest(),
                  'unique_geometries': len(set(hashes)), 'cases': results}
        write_json(output / 'batch.json', report)
    return report
