"""Comprueba madera, normales y materiales del GLB RF2 independientemente de bpy."""
import json
import math
from pathlib import Path
import struct

from .evaluation import validate_glb
from .foliage import cross, digest, dot, sub


def inspect_branch_glb(path, metrics, *, triangle_limit=10000):
    report = validate_glb(path, {'parameters': {'height_m': metrics['height_m']}}, triangle_limit=triangle_limit)
    if report['triangles'] != metrics['triangles'] or report['materials'] != metrics['triangles_by_material']:
        raise ValueError('GLB distinto del manifiesto')
    raw = Path(path).read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+size])
    binary = raw[28+size:]

    def accessor(index, width):
        a = doc['accessors'][index]
        if a['type'] != ('VEC3' if width == 3 else 'SCALAR') or 'sparse' in a:
            raise ValueError('Accessor no admitido')
        view = doc['bufferViews'][a['bufferView']]
        fmt = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[a['componentType']]
        length = struct.calcsize('<'+fmt*width)
        stride = view.get('byteStride', length)
        start = view.get('byteOffset', 0)+a.get('byteOffset', 0)
        end = start+(a['count']-1)*stride+length
        if a['count'] < 1 or stride < length or end > len(binary) or end > view.get('byteOffset', 0)+view['byteLength']:
            raise ValueError('Accessor fuera del buffer')
        return [struct.unpack_from('<'+fmt*width, binary, start+i*stride) for i in range(a['count'])]

    wood, wood_mat = [], None
    for primitive in doc['meshes'][0]['primitives']:
        material = doc['materials'][primitive['material']]
        if material.get('alphaMode', 'OPAQUE') != 'OPAQUE' or doc.get('textures'):
            raise ValueError('Material con transparencia o textura inesperada')
        name = material['name']
        if name == 'RF1_Leaf' and not material.get('doubleSided'):
            raise ValueError('Se descarta el reverso de las hojas')
        positions = accessor(primitive['attributes']['POSITION'], 3)
        normals = accessor(primitive['attributes']['NORMAL'], 3)
        indices = [v[0] for v in accessor(primitive['indices'], 1)]
        if len(normals) != len(positions) or any(not math.isfinite(x) for n in normals for x in n):
            raise ValueError('Normales inválidas')
        if any(abs(dot(n, n)-1) > .0001 for n in normals):
            raise ValueError('Normal no unitaria')
        for offset in range(0, len(indices), 3):
            ids = indices[offset:offset+3]
            a, b, c = [positions[i] for i in ids]
            face_normal = cross(sub(b, a), sub(c, a))
            if name == 'RF1_Leaf' and any(dot(face_normal, normals[i]) <= 0 for i in ids):
                raise ValueError('Normal de hoja invertida')
            if name == 'Oak_Bark':
                # Coordenadas y normales por vértice: conserva también el
                # sombreado exportado, sin depender del orden de los índices.
                wood.append(sorted(tuple(round(x, 6) for x in positions[i]+normals[i]) for i in ids))
                wood_mat = material
    if not wood:
        raise ValueError('Falta la madera')
    low, high = metrics['bounds_blender']
    expected = [[low[0], low[2], -high[1]], [high[0], high[2], -low[1]]]
    if any(abs(x-y) > .0001 for row, target in zip(report['bounds_gltf'], expected) for x, y in zip(row, target)):
        raise ValueError('Caja exportada incorrecta')
    return {**report, 'exported_wood_sha256': digest(sorted(wood)),
        'bark_material_sha256': digest(wood_mat), 'normals_valid': True}
