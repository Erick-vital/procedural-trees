#!/usr/bin/env python3
"""Comprobar rechazo de defectos inyectados en una copia del GLB de sauce."""
import argparse
import copy
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from treegen.willow_evaluation import inspect_willow
from treegen.pine_painted_sample import canonical_hash
import hashlib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Carpeta de un caso generado')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = args.source.resolve()
    manifest = json.loads((source/'manifest.json').read_text())
    resolved = manifest['resolved_blueprint']
    inspect_willow(source/'tree.glb', manifest, resolved)
    raw = (source/'tree.glb').read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    original_doc, original_bin = json.loads(raw[20:20+size]), raw[28+size:]
    results = {}
    for defect in ('alpha-cutoff', 'single-sided', 'wrong-image-channel', 'moved-leaf', 'uv-outside-atlas', 'nan-normal', 'missing-wood-face', 'changed-placement-hash'):
        doc, binary, meta = copy.deepcopy(original_doc), bytearray(original_bin), copy.deepcopy(manifest)
        leaf = next(p for p in doc['meshes'][0]['primitives'] if doc['materials'][p['material']]['name'] == 'Painted_Foliage')
        wood = next(p for p in doc['meshes'][0]['primitives'] if doc['materials'][p['material']]['name'] == 'Painted_Bark')
        mat = doc['materials'][leaf['material']]
        if defect == 'alpha-cutoff':
            mat['alphaCutoff'] = .1
        elif defect == 'single-sided':
            mat['doubleSided'] = False
        elif defect == 'wrong-image-channel':
            mat['pbrMetallicRoughness']['baseColorTexture'] = copy.deepcopy(doc['materials'][wood['material']]['pbrMetallicRoughness']['baseColorTexture'])
        elif defect in ('moved-leaf', 'uv-outside-atlas', 'nan-normal'):
            attribute = {'moved-leaf': 'POSITION', 'uv-outside-atlas': 'TEXCOORD_0', 'nan-normal': 'NORMAL'}[defect]
            accessor = doc['accessors'][leaf['attributes'][attribute]]
            view = doc['bufferViews'][accessor['bufferView']]
            start = view.get('byteOffset', 0)+accessor.get('byteOffset', 0)
            old = struct.unpack_from('<f', binary, start)[0]
            value = old+.03 if defect == 'moved-leaf' else 2.0 if defect == 'uv-outside-atlas' else float('nan')
            struct.pack_into('<f', binary, start, value)
        elif defect == 'missing-wood-face':
            doc['accessors'][wood['indices']]['count'] -= 3
        else:
            meta['placements_sha256'] = '0'*64
        encoded = json.dumps(doc, separators=(',', ':')).encode()
        encoded += b' '*((-len(encoded)) % 4)
        data = struct.pack('<4sII', b'glTF', 2, 28+len(encoded)+len(binary))
        data += struct.pack('<II', len(encoded), 0x4e4f534a)+encoded+struct.pack('<II', len(binary), 0x004e4942)+binary
        path = out/(defect+'.glb')
        path.write_bytes(data)
        try:
            inspect_willow(path, meta, resolved)
        except ValueError as exc:
            results[defect] = {'rejected': True, 'reason': str(exc)}
        else:
            results[defect] = {'rejected': False}
    passed = all(row['rejected'] for row in results.values())
    report = {'passed': passed, 'source_glb_sha256': hashlib.sha256(raw).hexdigest(),
              'auditor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'resolved_sha256': canonical_hash(resolved), 'defects': results}
    (out/'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    assert passed, 'El validador aceptó un defecto inyectado'


if __name__ == '__main__':
    main()
