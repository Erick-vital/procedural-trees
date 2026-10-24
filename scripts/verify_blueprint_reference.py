#!/usr/bin/env python3
"""B0: auditar la referencia aprobada y, opcionalmente, reproducir RF3."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from treegen.foliage import digest
from treegen.foliage_twigs_evaluation import inspect_twigs_glb
from treegen.runner import BLENDER

LOCK = ROOT / 'docs/evidence/blueprints/b0/reference-lock.json'
MANIFEST_KEYS = (
    'version', 'spec', 'base_spec', 'base_seeds', 'normalization',
    'base_matrix_world', 'output_matrix_world', 'wood_sha256', 'molds_sha256',
    'metrics', 'budget', 'support_count', 'leaf_count', 'sampling', 'selection',
    'supports_sha256', 'placements_sha256', 'twigs_sha256',
    'layout_leaf_length_m', 'cameras_sha256', 'molds_exported',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def oriented_geometry(path):
    """Firma a 1e-6 por triángulo, preservando orientación y normales por esquina.

    Tolera reordenar índices/triángulos y rotar cíclicamente sus esquinas;
    invertir el sentido de una cara sí modifica su firma.
    """
    raw = Path(path).read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + size])
    binary = raw[28 + size:]

    def values(index, width):
        a = doc['accessors'][index]
        view = doc['bufferViews'][a['bufferView']]
        fmt = '<' + {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[a['componentType']] * width
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = view.get('byteStride', struct.calcsize(fmt))
        return [struct.unpack_from(fmt, binary, start + i * stride) for i in range(a['count'])]

    channels = {}
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            positions = values(primitive['attributes']['POSITION'], 3)
            normals = values(primitive['attributes']['NORMAL'], 3)
            indices = [i[0] for i in values(primitive['indices'], 1)]
            name = doc['materials'][primitive['material']]['name']
            rows = channels.setdefault(name, [])
            for offset in range(0, len(indices), 3):
                corners = tuple(tuple(round(x, 6) for x in positions[i] + normals[i])
                                for i in indices[offset:offset + 3])
                rows.append(min(corners[i:] + corners[:i] for i in range(3)))
    return {
        'oriented_channel_sha256': {k: digest(sorted(v)) for k, v in channels.items()},
        'scene_nodes_sha256': digest(doc.get('nodes', [])),
        'scenes_sha256': digest({'scenes': doc.get('scenes'), 'scene': doc.get('scene')}),
        'materials': doc['materials'],
    }


def snapshot(folder):
    manifest = read(folder / 'manifest.json')
    report = inspect_twigs_glb(folder / 'tree.glb', manifest['metrics'], triangle_limit=12500)
    # El SHA binario se audita por separado: los metadatos no son geometría.
    report.pop('glb_sha256')
    return {
        'manifest_invariants': {k: manifest[k] for k in MANIFEST_KEYS},
        'export': report,
        'oriented_export': oriented_geometry(folder / 'tree.glb'),
    }


def run_blender(output, label, options):
    command = [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup',
               '--threads', '1', '--python-exit-code', '1', '--python',
               str(ROOT / 'blender/foliage_canopy_lab.py'), '--', *map(str, options)]
    with (output / (label + '.log')).open('w') as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            code = process.wait(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise TimeoutError(f'{label}: Blender excedió 120 s')
    if code:
        raise RuntimeError(f'{label}: Blender terminó con {code}; consultar {label}.log')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reproduce', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {'phase': 'B0', 'passed': False, 'reproduction_requested': args.reproduce}
    try:
        lock = read(LOCK)
        mismatches = [name for name, expected in lock['files_sha256'].items()
                      if not (ROOT / name).is_file() or sha(ROOT / name) != expected]
        report['file_count'] = len(lock['files_sha256'])
        report['file_mismatches'] = mismatches
        if mismatches:
            raise ValueError('Archivos congelados ausentes o distintos: ' + ', '.join(mismatches))
        pilot = ROOT / lock['pilot_directory']
        actual = snapshot(pilot)
        report['pilot_matches_lock'] = actual == lock['snapshot']
        if not report['pilot_matches_lock']:
            raise ValueError('El piloto no coincide con la referencia normalizada')
        if args.reproduce:
            run_blender(output, 'prepare', ['prepare', '--rf0', ROOT / lock['rf0'],
                        '--acceptance', ROOT / lock['rf2_acceptance'], '--output', output / 'reference'])
            run_blender(output, 'candidate', ['candidate', '--reference', output / 'reference/reference.json',
                        '--spec', ROOT / lock['pilot_spec_file'], '--output', output / 'repeat', '--no-render'])
            report['reproduction_matches_lock'] = snapshot(output / 'repeat') == lock['snapshot']
            report['prepared_reference_matches'] = sha(output / 'reference/reference.json') == lock['reference_sha256']
            if not report['reproduction_matches_lock'] or not report['prepared_reference_matches']:
                raise ValueError('La reproducción difiere de la referencia aprobada')
        report['passed'] = True
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        write(output / 'verification.json', report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
