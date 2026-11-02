"""Empaquetado estacional portable: sustituir un PNG embebido, geometría intacta."""
import copy
import hashlib
import json
import struct

VERSION = 'seasonal-paint-glb-0.1.0'


def unpack(raw):
    if len(raw) < 28 or len(raw) > 64*1024*1024:
        raise ValueError('Tamaño GLB inválido')
    magic, version, length = struct.unpack_from('<III', raw)
    size, kind = struct.unpack_from('<II', raw, 12)
    if (magic, version, length, kind) != (0x46546C67, 2, len(raw), 0x4E4F534A) or size % 4:
        raise ValueError('Cabecera GLB inválida')
    offset = 20+size
    if offset+8 > len(raw):
        raise ValueError('GLB sin bloque binario')
    binary_size, binary_kind = struct.unpack_from('<II', raw, offset)
    if binary_kind != 0x004E4942 or offset+8+binary_size != len(raw) or binary_size % 4:
        raise ValueError('Bloque binario GLB inválido')
    doc = json.loads(raw[20:offset])
    binary = raw[offset+8:]
    if len(doc.get('buffers', [])) != 1 or 'uri' in doc['buffers'][0]:
        raise ValueError('Se requiere un buffer embebido único')
    if not 0 <= len(binary)-doc['buffers'][0]['byteLength'] <= 3:
        raise ValueError('Longitud de buffer inconsistente')
    for view in doc['bufferViews']:
        start = view.get('byteOffset', 0)
        if view.get('buffer', 0) != 0 or start < 0 or start+view['byteLength'] > doc['buffers'][0]['byteLength']:
            raise ValueError('Vista binaria fuera de rango')
    return doc, binary


def image_view(doc, material_name):
    materials = [m for m in doc['materials'] if m.get('name') == material_name]
    if len(materials) != 1:
        raise ValueError('Material objetivo ausente o ambiguo')
    mat = materials[0]
    if mat.get('alphaMode') != 'MASK' or mat.get('alphaCutoff', .5) != .5 or not mat.get('doubleSided'):
        raise ValueError('Material de follaje incompatible')
    texture = mat['pbrMetallicRoughness']['baseColorTexture']['index']
    image = doc['images'][doc['textures'][texture]['source']]
    if image.get('mimeType') != 'image/png' or 'uri' in image:
        raise ValueError('Se requiere PNG embebido')
    return image['bufferView']


def view_bytes(doc, binary, index):
    view = doc['bufferViews'][index]
    start = view.get('byteOffset', 0)
    return binary[start:start+view['byteLength']]


def replace_foliage(raw, png, material_name='Painted_Foliage'):
    if len(png) < 33 or len(png) > 16*1024*1024 or png[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('PNG inválido o excesivo')
    width, height, depth, color = struct.unpack_from('>IIBB', png, 16)
    if not 1 <= width <= 2048 or not 1 <= height <= 2048 or depth != 8 or color != 6:
        raise ValueError('Se requiere PNG RGBA de 8 bits, hasta 2048²')
    original, binary = unpack(raw)
    doc = copy.deepcopy(original)
    index = image_view(doc, material_name)
    # El PNG sustituido no puede compartir almacenamiento con geometría u otra imagen.
    if any(a.get('bufferView') == index for a in doc.get('accessors', [])) or sum(i.get('bufferView') == index for i in doc['images']) != 1:
        raise ValueError('Imagen comparte almacenamiento')
    view = doc['bufferViews'][index]
    start = view.get('byteOffset', 0)
    stop = (start+view['byteLength']+3)//4*4
    if start % 4:
        raise ValueError('Imagen desalineada')
    for i, other in enumerate(doc['bufferViews']):
        a = other.get('byteOffset', 0)
        if i != index and a < stop and a+other['byteLength'] > start:
            raise ValueError('Vistas solapadas con la imagen')
    padded = png+b'\0'*(-len(png) % 4)
    delta = len(padded)-(stop-start)
    updated = binary[:start]+padded+binary[stop:]
    view['byteLength'] = len(png)
    for i, other in enumerate(doc['bufferViews']):
        if i != index and other.get('byteOffset', 0) >= stop:
            other['byteOffset'] = other.get('byteOffset', 0)+delta
    doc['buffers'][0]['byteLength'] = len(updated)
    encoded = json.dumps(doc, separators=(',', ':'), ensure_ascii=True).encode()
    encoded += b' '*(-len(encoded) % 4)
    result = struct.pack('<III', 0x46546C67, 2, 28+len(encoded)+len(updated))
    result += struct.pack('<II', len(encoded), 0x4E4F534A)+encoded
    result += struct.pack('<II', len(updated), 0x004E4942)+updated
    audit(raw, result, png, material_name)
    return result


def audit(before, after, png, material_name='Painted_Foliage'):
    old, old_binary = unpack(before)
    new, new_binary = unpack(after)
    index = image_view(old, material_name)
    if image_view(new, material_name) != index or view_bytes(new, new_binary, index) != png:
        raise ValueError('Pintura final incorrecta')
    expected = copy.deepcopy(old)
    expected['buffers'] = new['buffers']
    expected['bufferViews'] = new['bufferViews']
    if expected != new or len(old['bufferViews']) != len(new['bufferViews']):
        raise ValueError('Estructura/materiales/escena modificados')
    for i, view in enumerate(old['bufferViews']):
        permitted = dict(view)
        permitted['byteOffset'] = new['bufferViews'][i].get('byteOffset', 0)
        actual = dict(new['bufferViews'][i])
        actual.setdefault('byteOffset', 0)
        if i == index:
            permitted['byteLength'] = len(png)
        elif view_bytes(old, old_binary, i) != view_bytes(new, new_binary, i):
            raise ValueError('Geometría u otro recurso alterados')
        if permitted != actual:
            raise ValueError('Vista binaria alterada')
    return {'geometry_uv_normals_indices_exact': True, 'materials_scene_exact': True,
            'other_images_exact': True, 'foliage_png_sha256': hashlib.sha256(png).hexdigest()}
