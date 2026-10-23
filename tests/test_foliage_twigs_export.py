import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest

import test_foliage_branch_export
from treegen.foliage_twigs_evaluation import inspect_twigs_glb


class TwigExportTests(unittest.TestCase):
    def inspect(self, inverted=False):
        raw = test_foliage_branch_export.BranchExportTests().asset(normal_z=-1 if inverted else 1)
        length = struct.unpack_from('<I', raw, 12)[0]
        doc = json.loads(raw[20:20+length])
        binary = raw[28+length:]
        doc['materials'][1] = dict(copy.deepcopy(doc['materials'][0]), name='RF2_Twig')
        encoded = json.dumps(doc).encode()
        encoded += b' '*(-len(encoded) % 4)
        packed = (struct.pack('<4sII', b'glTF', 2, 28+len(encoded)+len(binary))+
                  struct.pack('<II', len(encoded), 0x4e4f534a)+encoded+
                  struct.pack('<II', len(binary), 0x004e4942)+binary)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'branch.glb'
            path.write_bytes(packed)
            return inspect_twigs_glb(path, {'height_m': 1, 'triangles': 2,
                'triangles_by_material': {'Oak_Bark': 1, 'RF2_Twig': 1},
                'bounds_blender': [[0, -1, 0], [3, 0, 1]]})

    def test_separate_channels_and_matching_bark(self):
        report = self.inspect()
        self.assertEqual(set(report['channel_sha256']), {'Oak_Bark', 'RF2_Twig'})
        self.assertNotEqual(report['channel_sha256']['Oak_Bark'], report['channel_sha256']['RF2_Twig'])
        self.assertEqual(report['material_properties_sha256']['Oak_Bark'], report['material_properties_sha256']['RF2_Twig'])

    def test_reject_inverted_twig_normal(self):
        with self.assertRaises(ValueError):
            self.inspect(inverted=True)


if __name__ == '__main__':
    unittest.main()
