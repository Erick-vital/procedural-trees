"""Transporte T1 por TEXCOORD_1: calendario sin tinte ni cambios geométricos."""
import copy
import json
import math
import struct
from collections import Counter

from .season_calendar import digest, validate_calendar
from .seasonal_paint import unpack, view_bytes

VERSION = 'season-calendar-uv2-0.1.0'


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def read_accessor(doc, binary, index, width):
    accessor = doc['accessors'][index]
    if accessor['type'] != {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3'}[width] or 'sparse' in accessor or accessor.get('normalized', False):
        raise ValueError('Accessor incompatible con calendario')
    component = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}.get(accessor['componentType'])
    if component is None or width > 1 and component != 'f':
        raise ValueError('Componente de accessor incompatible')
    fmt = '<'+component*width
    size = struct.calcsize(fmt)
    view = doc['bufferViews'][accessor['bufferView']]
    count = accessor['count']
    offset = accessor.get('byteOffset', 0)
    stride = view.get('byteStride', size)
    if type(count) is not int or not 1 <= count <= 40000 or offset < 0 or stride < size or offset+(count-1)*stride+size > view['byteLength']:
        raise ValueError('Accessor excesivo o fuera de rango')
    start = view.get('byteOffset', 0)+offset
    values = [struct.unpack_from(fmt, binary, start+i*stride) for i in range(count)]
    if any(not math.isfinite(v) for row in values for v in row):
        raise ValueError('Accessor no finito')
    return values


def _key(position, uv):
    return tuple(position)+tuple(uv)


def panel_binding(panels, data):
    validate_calendar(data)
    rows = {g['id']: g for g in data['groups']}
    if not isinstance(panels, list) or len(panels) != 3*len(rows):
        raise ValueError('Número de láminas incompatible')
    binding, planes = {}, set()
    for panel in panels:
        identifier, plane = panel['source_support_id'], panel['plane']
        if not isinstance(identifier, str) or identifier not in rows or type(plane) is not int or plane not in (0, 1, 2) or (identifier, plane) in planes:
            raise ValueError('Grupo/plano ausente o duplicado')
        planes.add((identifier, plane))
        if len(panel['vertices']) != 4 or len(panel['uv']) != 4 or panel['polygons'] != [[0, 1, 2], [0, 2, 3]]:
            raise ValueError('Topología de cruzadas incompatible')
        for v, uv in zip(panel['vertices'], panel['uv']):
            if len(v) != 3 or len(uv) != 2 or any(type(x) not in (float, int) or not math.isfinite(x) or abs(x) > 1000 for x in v+uv) or any(not 0 <= x <= 1 for x in uv):
                raise ValueError('Vértice de lámina inválido')
            key = _key([f32(v[0]), f32(v[2]), f32(-v[1])], [f32(uv[0]), f32(1-f32(uv[1]))])
            if key in binding and binding[key] != identifier:
                raise ValueError('Correspondencia entre grupos ambigua')
            binding[key] = identifier
    return binding


def pack(doc, binary):
    doc = copy.deepcopy(doc)
    binary += b'\0'*(-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    encoded = json.dumps(doc, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()
    encoded += b' '*(-len(encoded) % 4)
    return (struct.pack('<III', 0x46546C67, 2, 28+len(encoded)+len(binary))+
            struct.pack('<II', len(encoded), 0x4E4F534A)+encoded+
            struct.pack('<II', len(binary), 0x004E4942)+binary)


def _primitives(doc):
    if len(doc.get('nodes', [])) != 1 or len(doc.get('meshes', [])) != 1 or len(doc.get('materials', [])) != 2:
        raise ValueError('Se requiere un árbol con una malla y dos materiales')
    if any(k in doc['nodes'][0] for k in ('matrix', 'translation', 'rotation', 'scale')):
        raise ValueError('Transformación de nodo inesperada')
    result = []
    for primitive in doc['meshes'][0]['primitives']:
        if primitive.get('mode', 4) != 4:
            raise ValueError('Primitiva distinta de triángulos')
        name = doc['materials'][primitive['material']]['name']
        if name not in ('Painted_Bark', 'Painted_Foliage'):
            raise ValueError('Material desconocido')
        if 'COLOR_0' in primitive['attributes']:
            raise ValueError('Color de vértices inesperado')
        # TEXCOORD_1 queda reservado: no sobrescribir UV de otra función.
        result.append((name, primitive))
    if {name for name, _ in result} != {'Painted_Bark', 'Painted_Foliage'}:
        raise ValueError('Canales incompletos')
    for material in doc['materials']:
        for key in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
            if key in material and material[key].get('texCoord', 0) != 0:
                raise ValueError('Material consume UV reservados')
        for key in ('baseColorTexture', 'metallicRoughnessTexture'):
            if material['pbrMetallicRoughness'].get(key, {}).get('texCoord', 0) != 0:
                raise ValueError('Material consume UV reservados')
        if material.get('extensions'):
            raise ValueError('Extensión de material no auditada')
    return result


def attach_calendar(raw, panels, data):
    expected = panel_binding(panels, data)
    rows = {g['id']: g for g in data['groups']}
    original, binary = unpack(raw)
    doc = copy.deepcopy(original)
    total_triangles, counts, used_keys = 0, Counter(), set()
    for name, primitive in _primitives(doc):
        attributes = primitive['attributes']
        if 'TEXCOORD_1' in attributes:
            raise ValueError('UV2 ya ocupado')
        positions = read_accessor(doc, binary, attributes['POSITION'], 3)
        indices = [r[0] for r in read_accessor(doc, binary, primitive['indices'], 1)]
        if len(indices) % 3 or any(i >= len(positions) for i in indices):
            raise ValueError('Índices inválidos')
        total_triangles += len(indices)//3
        if name != 'Painted_Foliage':
            continue
        uv = read_accessor(doc, binary, attributes['TEXCOORD_0'], 2)
        if len(uv) != len(positions) or set(indices) != set(range(len(positions))):
            raise ValueError('Vértices o UV de follaje incompatibles')
        owners, values = [], []
        for v, u in zip(positions, uv):
            key = _key(v, u)
            if key not in expected:
                raise ValueError('Vértice exportado sin grupo conocido')
            used_keys.add(key)
            identifier = expected[key]
            row = rows[identifier]
            owners.append(identifier)
            values.append([f32(row['start']), f32(row['duration'])])
        for i in range(0, len(indices), 3):
            identifiers = {owners[j] for j in indices[i:i+3]}
            if len(identifiers) != 1:
                raise ValueError('Triángulo mezcla grupos distintos')
            counts[next(iter(identifiers))] += 1
        offset = len(binary)
        payload = b''.join(struct.pack('<ff', *row) for row in values)
        binary += payload
        view_index = len(doc['bufferViews'])
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(payload), 'target': 34962})
        attributes['TEXCOORD_1'] = len(doc['accessors'])
        doc['accessors'].append({'bufferView': view_index, 'componentType': 5126, 'count': len(values), 'type': 'VEC2'})
    if not 0 < total_triangles <= 6999 or counts != Counter({identifier: 6 for identifier in rows}) or used_keys != set(expected):
        raise ValueError('Presupuesto o cobertura de grupos incorrectos')
    doc.setdefault('extras', {})['treegen_season_calendar'] = {
        'version': VERSION, 'calendar_sha256': digest(data), 'attribute': 'TEXCOORD_1',
        'components': ['start', 'duration'], 'lightmap_uv': False,
    }
    result = pack(doc, binary)
    audit_transport(raw, result, panels, data)
    return result


def audit_transport(before, after, panels, data):
    expected = panel_binding(panels, data)
    rows = {g['id']: g for g in data['groups']}
    old, original = unpack(before)
    new, binary = unpack(after)
    metadata = {'version': VERSION, 'calendar_sha256': digest(data), 'attribute': 'TEXCOORD_1',
                'components': ['start', 'duration'], 'lightmap_uv': False}
    expected_extras = {**old.get('extras', {}), 'treegen_season_calendar': metadata}
    additions = sum(name == 'Painted_Foliage' for name, _ in _primitives(old))
    if new.get('extras') != expected_extras or len(new['accessors']) != len(old['accessors'])+additions or len(new['bufferViews']) != len(old['bufferViews'])+additions:
        raise ValueError('Metadatos o atributos de calendario distintos')
    if binary[:len(original)] != original:
        raise ValueError('Buffer histórico modificado')
    restored = copy.deepcopy(new)
    restored['buffers'] = old['buffers']
    restored['accessors'] = restored['accessors'][:len(old['accessors'])]
    restored['bufferViews'] = restored['bufferViews'][:len(old['bufferViews'])]
    if 'extras' in old:
        restored['extras'] = old['extras']
    else:
        restored.pop('extras', None)
    observed, imported = Counter(), []
    for name, primitive in _primitives(restored):
        if name == 'Painted_Foliage':
            primitive['attributes'].pop('TEXCOORD_1', None)
    if restored != old:
        raise ValueError('Geometría, materiales, recursos o escena modificados')
    for name, primitive in _primitives(new):
        if name != 'Painted_Foliage':
            if 'TEXCOORD_1' in primitive['attributes']:
                raise ValueError('Calendario añadido a madera')
            continue
        a = primitive['attributes']
        positions = read_accessor(new, binary, a['POSITION'], 3)
        uv = read_accessor(new, binary, a['TEXCOORD_0'], 2)
        actual = read_accessor(new, binary, a['TEXCOORD_1'], 2)
        if len(actual) != len(positions) or len(uv) != len(positions):
            raise ValueError('Calendario incompleto')
        for v, u, values in zip(positions, uv, actual):
            identifier = expected.get(_key(v, u))
            if identifier is None or tuple(values) != (f32(rows[identifier]['start']), f32(rows[identifier]['duration'])):
                raise ValueError('Calendario no corresponde al grupo')
            observed[identifier] += 1
            imported.append({'position': list(v), 'uv': list(u), 'group_id': identifier, 'calendar': list(values)})
    if set(observed) != set(rows):
        raise ValueError('Grupos de calendario sin atributos')
    return {'historical_binary_exact': True, 'scene_materials_geometry_exact': True,
            'groups': len(observed), 'foliage_vertices': sum(observed.values()),
            'calendar_attribute_bytes': sum(observed.values())*8, 'vertex_splits': 0,
            'binding': imported}
