import json
import struct
import unittest
import zlib

from treegen.seasonal_paint import audit, replace_foliage, unpack, view_bytes


def png(pixel):
    def chunk(kind, data):
        return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))+chunk(b'IDAT', zlib.compress(b'\0'+bytes(pixel)))+chunk(b'IEND', b'')


def fixture():
    image = png([10, 200, 10, 255])
    binary = b'GEOM'+image+b'\0'*(-len(image) % 4)+b'BARK'
    doc = {'asset': {'version': '2.0'}, 'buffers': [{'byteLength': len(binary)}],
           'bufferViews': [{'buffer': 0, 'byteOffset': 0, 'byteLength': 4},
                           {'buffer': 0, 'byteOffset': 4, 'byteLength': len(image)},
                           {'buffer': 0, 'byteOffset': len(binary)-4, 'byteLength': 4}],
           'images': [{'bufferView': 1, 'mimeType': 'image/png'}], 'textures': [{'source': 0}],
           'materials': [{'name': 'Painted_Foliage', 'alphaMode': 'MASK', 'doubleSided': True,
                          'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}}}]}
    encoded = json.dumps(doc).encode()
    encoded += b' '*(-len(encoded) % 4)
    return struct.pack('<III', 0x46546C67, 2, 28+len(encoded)+len(binary))+struct.pack('<II', len(encoded), 0x4E4F534A)+encoded+struct.pack('<II', len(binary), 0x004E4942)+binary


class SeasonalPaintTests(unittest.TestCase):
    def test_replacement_preserves_geometry_and_following_resource(self):
        original = fixture()
        replacement = png([170, 90, 25, 255])
        result = replace_foliage(original, replacement)
        self.assertEqual(result, replace_foliage(original, replacement))
        doc, data = unpack(result)
        self.assertEqual(view_bytes(doc, data, 0), b'GEOM')
        self.assertEqual(view_bytes(doc, data, 1), replacement)
        self.assertEqual(view_bytes(doc, data, 2), b'BARK')
        self.assertTrue(audit(original, result, replacement)['geometry_uv_normals_indices_exact'])

    def test_corrupt_or_wrong_resources_rejected(self):
        with self.assertRaises(ValueError): replace_foliage(fixture(), b'invalid')
        with self.assertRaises(ValueError): replace_foliage(fixture(), png([1, 2, 3, 255]), 'Missing')
        with self.assertRaises(ValueError): replace_foliage(fixture()[:-1], png([1, 2, 3, 255]))

    def test_audit_rejects_geometry_tampering(self):
        original = fixture()
        replacement = png([170, 90, 25, 255])
        result = replace_foliage(original, replacement).replace(b'GEOM', b'FAIL')
        with self.assertRaises(ValueError): audit(original, result, replacement)
