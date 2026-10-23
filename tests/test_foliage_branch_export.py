import json
from pathlib import Path
import struct
import tempfile
import unittest

from treegen.foliage_branch_evaluation import inspect_branch_glb


class BranchExportTests(unittest.TestCase):
    def asset(self, normal_z=1., double_sided=True, wood_shift=0.):
        binary = b''
        views, accessors, primitives = [], [], []
        for material in range(2):
            x = 0. if material == 0 else 2.
            values = [struct.pack('<9f', x, 0, 0, 1+x+(wood_shift if material == 0 else 0), 0, 0, x, 1, 1),
                      struct.pack('<9f', *([0, -.70710678, .70710678 if material == 0 else normal_z*.70710678]*3)),
                      struct.pack('<3I', 0, 1, 2)]
            for i, value in enumerate(values):
                views.append({'byteOffset': len(binary), 'byteLength': len(value)})
                binary += value
                accessors.append({'bufferView': len(views)-1, 'componentType': 5125 if i == 2 else 5126,
                                  'count': 3, 'type': 'SCALAR' if i == 2 else 'VEC3'})
            primitives.append({'attributes': {'POSITION': len(accessors)-3, 'NORMAL': len(accessors)-2},
                               'indices': len(accessors)-1, 'material': material})
        doc = {'asset': {'version': '2.0'}, 'nodes': [{'mesh': 0}],
               'meshes': [{'primitives': primitives}], 'accessors': accessors, 'bufferViews': views,
               'materials': [{'name': 'Oak_Bark', 'pbrMetallicRoughness': {}},
                             {'name': 'RF1_Leaf', 'doubleSided': double_sided, 'pbrMetallicRoughness': {}}]}
        encoded = json.dumps(doc).encode()
        encoded += b' '*(-len(encoded) % 4)
        return (struct.pack('<4sII', b'glTF', 2, 28+len(encoded)+len(binary))+
                struct.pack('<II', len(encoded), 0x4e4f534a)+encoded+
                struct.pack('<II', len(binary), 0x004e4942)+binary)

    def inspect(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'branch.glb'
            path.write_bytes(data)
            return inspect_branch_glb(path, {'height_m': 1, 'triangles': 2,
                'triangles_by_material': {'Oak_Bark': 1, 'RF1_Leaf': 1},
                'bounds_blender': [[0, -1, 0], [3, 0, 1]]})

    def test_exported_wood_signature_and_normals(self):
        report = self.inspect(self.asset())
        self.assertTrue(report['normals_valid'])
        self.assertEqual(report['exported_wood_sha256'], self.inspect(self.asset())['exported_wood_sha256'])
        self.assertNotEqual(report['exported_wood_sha256'], self.inspect(self.asset(wood_shift=.1))['exported_wood_sha256'])

    def test_reject_culling_and_inverted_normals(self):
        for data in (self.asset(double_sided=False), self.asset(normal_z=-1)):
            with self.assertRaises(ValueError):
                self.inspect(data)


if __name__ == '__main__':
    unittest.main()
