"""GLB sintético: comprobar los errores numéricos sobre bytes exportados."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
from treegen.contracts import ROOT, load_spec
from treegen.evaluation import validate_glb


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'tree.glb'
        self.spec = load_spec(ROOT / 'presets/adulto.json')

    def write_glb(self, vertices=None, indices=(0, 1, 2)):
        vertices = vertices or [(0,0,0), (1,10,0), (0,0,1)]
        binary = struct.pack('<9f3I', *(x for p in vertices for x in p), *indices)
        doc = {'asset': {'version':'2.0'}, 'nodes':[{'mesh':0}],
               'meshes':[{'primitives':[{'attributes':{'POSITION':0}, 'indices':1, 'material':0}]}],
               'materials':[{'name':'Oak_Bark'}], 'buffers':[{'byteLength':len(binary)}],
               'bufferViews':[{'buffer':0, 'byteOffset':0, 'byteLength':36},
                              {'buffer':0, 'byteOffset':36, 'byteLength':12}],
               'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'},
                            {'bufferView':1,'componentType':5125,'count':3,'type':'SCALAR'}]}
        content = json.dumps(doc).encode()
        content += b' ' * (-len(content) % 4)
        chunks = struct.pack('<II',len(content),0x4e4f534a)+content+struct.pack('<II',len(binary),0x004e4942)+binary
        self.path.write_bytes(struct.pack('<4sII',b'glTF',2,12+len(chunks))+chunks)

    def test_valid_export(self):
        self.write_glb()
        report = validate_glb(self.path, self.spec)
        self.assertEqual(report['triangles'], 1)
        self.assertEqual(report['dimensions_m'], [1,10,1])

    def test_reject_invalid_numeric_geometry(self):
        cases = [([(0,0,0),(1,10,0),(0,0,float('nan'))], (0,1,2)),
                 ([(0,0,0),(1,10,0),(2,20,0)], (0,1,2)),
                 (None, (0,1,99))]
        for vertices, indices in cases:
            with self.subTest(vertices=vertices, indices=indices):
                self.write_glb(vertices, indices)
                with self.assertRaises(ValueError):
                    validate_glb(self.path, self.spec)

    def test_reject_truncated_file_and_wrong_height(self):
        self.write_glb()
        self.path.write_bytes(self.path.read_bytes()[:-1])
        with self.assertRaises(ValueError):
            validate_glb(self.path, self.spec)
        self.write_glb()
        self.spec['parameters']['height_m'] = 4
        with self.assertRaises(ValueError):
            validate_glb(self.path, self.spec)

    def test_explicit_rf3_budget_preserves_historical_default(self):
        self.write_glb()
        raw = self.path.read_bytes()
        length = struct.unpack_from('<I', raw, 12)[0]
        doc = json.loads(raw[20:20+length])
        original = raw[28+length:]
        binary = original[:36]+original[36:]*10001
        doc['accessors'][1]['count'] = 3*10001
        doc['bufferViews'][1]['byteLength'] = 12*10001
        doc['buffers'][0]['byteLength'] = len(binary)
        encoded = json.dumps(doc).encode()
        encoded += b' '*(-len(encoded) % 4)
        chunks = struct.pack('<II', len(encoded), 0x4e4f534a)+encoded+struct.pack('<II', len(binary), 0x004e4942)+binary
        self.path.write_bytes(struct.pack('<4sII', b'glTF', 2, 12+len(chunks))+chunks)
        with self.assertRaises(ValueError):
            validate_glb(self.path, self.spec)
        self.assertEqual(validate_glb(self.path, self.spec, triangle_limit=12500)['triangles'], 10001)
        for limit in (True, 12501, float('nan')):
            with self.assertRaises(ValueError):
                validate_glb(self.path, self.spec, triangle_limit=limit)
