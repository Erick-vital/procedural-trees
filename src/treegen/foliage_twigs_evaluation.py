"""Firmas independientes por canal de la revisión RF2, sobre el GLB final."""
import json
from pathlib import Path
import struct

from .foliage import digest, cross, dot, sub
from .foliage_branch_evaluation import inspect_branch_glb


def inspect_twigs_glb(path, metrics, *, triangle_limit=10000, wood_material='Oak_Bark', leaf_material='RF1_Leaf'):
    report = inspect_branch_glb(path, metrics, triangle_limit=triangle_limit,
                                wood_material=wood_material, leaf_material=leaf_material)
    raw = Path(path).read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+size])
    binary = raw[28+size:]

    def read(index, width):
        accessor = doc['accessors'][index]
        view = doc['bufferViews'][accessor['bufferView']]
        fmt = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[accessor['componentType']]
        length = struct.calcsize('<'+fmt*width)
        start = view.get('byteOffset', 0)+accessor.get('byteOffset', 0)
        stride = view.get('byteStride', length)
        return [struct.unpack_from('<'+fmt*width, binary, start+i*stride) for i in range(accessor['count'])]

    signatures, materials = {}, {}
    for primitive in doc['meshes'][0]['primitives']:
        mat = doc['materials'][primitive['material']]
        positions = read(primitive['attributes']['POSITION'], 3)
        normals = read(primitive['attributes']['NORMAL'], 3)
        indices = [v[0] for v in read(primitive['indices'], 1)]
        rows = signatures.setdefault(mat['name'], [])
        materials[mat['name']] = digest({k: v for k, v in mat.items() if k != 'name'})
        for start in range(0, len(indices), 3):
            ids = indices[start:start+3]
            if mat['name'] == 'RF2_Twig':
                face_normal = cross(sub(positions[ids[1]], positions[ids[0]]), sub(positions[ids[2]], positions[ids[0]]))
                if any(dot(face_normal, normals[i]) <= 0 for i in ids):
                    raise ValueError('Normal de ramilla invertida')
            rows.append(sorted(tuple(round(x, 6) for x in positions[i]+normals[i]) for i in ids))
    if 'RF2_Twig' in materials and materials['RF2_Twig'] != materials['Oak_Bark']:
        raise ValueError('Las ramillas no comparten las propiedades de corteza')
    return {**report, 'channel_sha256': {name: digest(sorted(rows)) for name, rows in signatures.items()},
            'material_properties_sha256': materials}
