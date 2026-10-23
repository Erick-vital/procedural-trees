"""Inspección independiente del GLB RF1, incluidas hojas planas y normales."""
import hashlib
import json
import math
from pathlib import Path
import struct

from .foliage import cross, dot, sub


def validate_unit_glb(path, manifest):
    raw = Path(path).read_bytes()
    if len(raw) < 20 or struct.unpack_from('<4sII', raw) != (b'glTF', 2, len(raw)):
        raise ValueError('Cabecera GLB inválida')
    chunks, offset = {}, 12
    while offset < len(raw):
        if offset+8 > len(raw):
            raise ValueError('Chunk incompleto')
        length, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        if offset+length > len(raw):
            raise ValueError('Chunk truncado')
        chunks[kind] = raw[offset:offset+length]
        offset += length
    doc = json.loads(chunks[0x4e4f534a])
    binary = chunks[0x004e4942]
    if len(doc.get('nodes', [])) != 1 or len(doc.get('meshes', [])) != 1:
        raise ValueError('Se requiere una sola malla, sin soporte visible')
    if any(key in doc['nodes'][0] for key in ('matrix', 'translation', 'rotation', 'scale')):
        raise ValueError('Transformación inesperada')
    if len(doc.get('materials', [])) != 1 or doc.get('textures'):
        raise ValueError('Materiales o texturas inesperados')
    material = doc['materials'][0]
    if not material.get('doubleSided') or material.get('alphaMode', 'OPAQUE') != 'OPAQUE':
        raise ValueError('La hoja debe ser opaca y visible por ambos lados')
    if material['pbrMetallicRoughness'].get('baseColorFactor', [1, 1, 1, 1])[3] != 1:
        raise ValueError('Alfa no opaco')

    def accessor(index, width):
        a = doc['accessors'][index]
        fmt = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[a['componentType']]
        if a['type'] != ('VEC3' if width == 3 else 'SCALAR') or 'sparse' in a:
            raise ValueError('Accessor no admitido')
        view = doc['bufferViews'][a['bufferView']]
        size = struct.calcsize('<'+fmt*width)
        stride = view.get('byteStride', size)
        start = view.get('byteOffset', 0)+a.get('byteOffset', 0)
        end = start+(a['count']-1)*stride+size
        if a['count'] <= 0 or stride < size or end > len(binary) or end > view.get('byteOffset', 0)+view['byteLength']:
            raise ValueError('Accessor fuera del buffer')
        return [struct.unpack_from('<'+fmt*width, binary, start+i*stride) for i in range(a['count'])]

    points, count = [], 0
    for primitive in doc['meshes'][0]['primitives']:
        if primitive.get('mode', 4) != 4 or primitive['material'] != 0:
            raise ValueError('Primitiva no admitida')
        vertices = accessor(primitive['attributes']['POSITION'], 3)
        normals = accessor(primitive['attributes']['NORMAL'], 3)
        indices = [v[0] for v in accessor(primitive['indices'], 1)]
        if len(indices) % 3 or any(i >= len(vertices) for i in indices) or len(normals) != len(vertices):
            raise ValueError('Índices o normales incoherentes')
        if not all(math.isfinite(x) for v in vertices+normals for x in v):
            raise ValueError('Coordenadas no finitas')
        if any(abs(dot(n, n)-1) > .0001 for n in normals):
            raise ValueError('Normal no unitaria')
        for start in range(0, len(indices), 3):
            ia, ib, ic = indices[start:start+3]
            n = cross(sub(vertices[ib], vertices[ia]), sub(vertices[ic], vertices[ia]))
            if dot(n, n) < 4e-20 or any(dot(n, normals[i]) <= 0 for i in (ia, ib, ic)):
                raise ValueError('Cara degenerada o normal invertida')
        points.extend(vertices)
        count += len(indices)//3
    expected = manifest['metrics']
    if not 1 <= count <= 128 or count != expected['triangles']:
        raise ValueError('Conteo fuera de presupuesto o distinto del manifiesto')
    bounds = [[fn(p[k] for p in points) for k in range(3)] for fn in (min, max)]
    low, high = expected['bounds_blender']
    converted = [[low[0], low[2], -high[1]], [high[0], high[2], -low[1]]]
    if any(abs(x-y) > .0001 for actual, wanted in zip(bounds, converted) for x, y in zip(actual, wanted)):
        raise ValueError('Escala o ejes exportados incorrectos')
    return {'triangles': count, 'bounds_gltf': bounds, 'normals_valid': True,
            'opaque_double_sided': True, 'glb_sha256': hashlib.sha256(raw).hexdigest()}
