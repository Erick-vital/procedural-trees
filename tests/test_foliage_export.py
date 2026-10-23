import json
from pathlib import Path
import struct
import tempfile
import unittest

from treegen.foliage_evaluation import validate_unit_glb


class FoliageExportTests(unittest.TestCase):
    def asset(self, *, double_sided=True, normal_z=1., alpha_mode='OPAQUE'):
        # Triángulo plano en glTF X/Y; el adaptador debe admitir espesor cero.
        binary = struct.pack('<9f', 0, 0, 0, 1, 0, 0, 0, 1, 0)
        binary += struct.pack('<9f', *([0, 0, normal_z]*3))
        binary += struct.pack('<3I', 0, 1, 2)
        doc = {'asset': {'version': '2.0'}, 'nodes': [{'mesh': 0}],
               'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1}, 'indices': 2, 'material': 0}]}],
               'materials': [{'doubleSided': double_sided, 'alphaMode': alpha_mode,
                              'pbrMetallicRoughness': {'baseColorFactor': [.2, .4, .1, 1]}}],
               'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': 3, 'type': 'VEC3'},
                             {'bufferView': 1, 'componentType': 5126, 'count': 3, 'type': 'VEC3'},
                             {'bufferView': 2, 'componentType': 5125, 'count': 3, 'type': 'SCALAR'}],
               'bufferViews': [{'byteOffset': 0, 'byteLength': 36}, {'byteOffset': 36, 'byteLength': 36},
                               {'byteOffset': 72, 'byteLength': 12}]}
        text = json.dumps(doc).encode()
        text += b' '*(-len(text) % 4)
        data = struct.pack('<4sII', b'glTF', 2, 28+len(text)+len(binary))
        data += struct.pack('<II', len(text), 0x4e4f534a)+text
        return data+struct.pack('<II', len(binary), 0x004e4942)+binary

    def validate(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'unit.glb'
            path.write_bytes(data)
            return validate_unit_glb(path, {'metrics': {'triangles': 1,
                'bounds_blender': [[0, 0, 0], [1, 0, 1]]}})

    def test_single_plane_has_valid_normals_without_thickness(self):
        self.assertTrue(self.validate(self.asset())['normals_valid'])

    def test_reject_backface_culling_transparency_normals_and_truncation(self):
        for data in (self.asset(double_sided=False), self.asset(normal_z=-1),
                     self.asset(normal_z=.5), self.asset(alpha_mode='BLEND'), self.asset()[:-3]):
            with self.subTest(data=data[:12]), self.assertRaises(ValueError):
                self.validate(data)


if __name__ == '__main__':
    unittest.main()
