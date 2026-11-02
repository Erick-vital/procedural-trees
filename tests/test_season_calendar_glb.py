import copy
import struct
import unittest

from treegen.oak_crossed import panels
from treegen.season_calendar import build_calendar
from treegen.season_calendar_glb import attach_calendar, audit_transport, pack, read_accessor
from treegen.seasonal_paint import unpack
from test_season_calendar import profile, volumes


def fixture():
    groups = volumes()[:2]
    cards = [p for g in groups for p in panels(g, 0, 3)]
    binary = b''
    doc = {'asset': {'version': '2.0'}, 'buffers': [{'byteLength': 0}],
           'bufferViews': [], 'accessors': [], 'nodes': [{'mesh': 0}],
           'scenes': [{'nodes': [0]}], 'scene': 0,
           'materials': [{'name': name, 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1]}} for name in ('Painted_Bark', 'Painted_Foliage')],
           'meshes': [{'primitives': []}]}

    def add(rows, width, fmt='f'):
        nonlocal binary
        offset = len(binary)
        payload = b''.join(struct.pack('<'+fmt*width, *r) for r in rows)
        binary += payload+b'\0'*(-len(payload) % 4)
        index = len(doc['accessors'])
        doc['accessors'].append({'bufferView': len(doc['bufferViews']), 'type': {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3'}[width],
                                 'componentType': 5126 if fmt == 'f' else 5125, 'count': len(rows)})
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(payload)})
        return index

    for material in (0, 1):
        pos, uv, ids = [], [], []
        if material == 0:
            pos, uv, ids = [[0, 0, 0], [1, 0, 0], [0, 1, 0]], [[0, 0]]*3, [0, 1, 2]
        else:
            from treegen.season_calendar_glb import f32
            for card in cards:
                offset = len(pos)
                pos += [[v[0], v[2], -v[1]] for v in card['vertices']]
                uv += [[u, f32(1-f32(v))] for u, v in card['uv']]
                ids += [offset+i for face in card['polygons'] for i in face]
        attributes = {'POSITION': add(pos, 3), 'NORMAL': add([[0, 1, 0]]*len(pos), 3), 'TEXCOORD_0': add(uv, 2)}
        doc['meshes'][0]['primitives'].append({'material': material, 'attributes': attributes, 'indices': add([[i] for i in ids], 1, 'I')})
    return pack(doc, binary), cards, build_calendar(groups, profile())


class CalendarGlbTests(unittest.TestCase):
    def test_transport_preserves_original_bytes_and_materials(self):
        raw, cards, data = fixture()
        result = attach_calendar(raw, cards, data)
        self.assertEqual(result, attach_calendar(raw, list(reversed(cards)), data))
        report = audit_transport(raw, result, cards, data)
        self.assertTrue(report['historical_binary_exact'])
        self.assertEqual(report['groups'], 2)
        self.assertEqual(report['vertex_splits'], 0)
        doc, binary = unpack(result)
        original, _ = unpack(raw)
        self.assertEqual(doc['materials'], original['materials'])
        self.assertNotIn('COLOR_0', doc['meshes'][0]['primitives'][1]['attributes'])
        self.assertNotIn('TEXCOORD_1', doc['meshes'][0]['primitives'][0]['attributes'])
        self.assertEqual(len(report['binding']), 24)

    def test_incorrect_or_ambiguous_binding_rejected(self):
        raw, cards, data = fixture()
        with self.assertRaises(ValueError): attach_calendar(raw, cards[:-1], data)
        bad = copy.deepcopy(cards)
        bad[0]['vertices'][0][0] += .1
        with self.assertRaises(ValueError): attach_calendar(raw, bad, data)
        bad = copy.deepcopy(cards)
        bad[0]['plane'] = bad[1]['plane']
        with self.assertRaises(ValueError): attach_calendar(raw, bad, data)

    def test_rejects_existing_uv2(self):
        raw, cards, data = fixture()
        doc, binary = unpack(raw)
        a = doc['meshes'][0]['primitives'][1]['attributes']
        a['TEXCOORD_1'] = a['TEXCOORD_0']
        with self.assertRaises(ValueError): attach_calendar(pack(doc, binary), cards, data)

    def test_audit_detects_altered_calendar(self):
        raw, cards, data = fixture()
        result = attach_calendar(raw, cards, data)
        doc, binary = unpack(result)
        index = doc['meshes'][0]['primitives'][1]['attributes']['TEXCOORD_1']
        offset = doc['bufferViews'][doc['accessors'][index]['bufferView']]['byteOffset']
        binary = binary[:offset]+struct.pack('<f', .999)+binary[offset+4:]
        with self.assertRaises(ValueError): audit_transport(raw, pack(doc, binary), cards, data)

    def test_audit_detects_geometry_material_and_metadata_changes(self):
        raw, cards, data = fixture()
        result = attach_calendar(raw, cards, data)
        for kind in ('material', 'metadata', 'geometry'):
            doc, binary = unpack(result)
            if kind == 'material': doc['materials'][0]['name'] = 'Changed'
            elif kind == 'metadata': doc['extras']['treegen_season_calendar']['calendar_sha256'] = '0'*64
            else: binary = struct.pack('<f', .5)+binary[4:]
            with self.subTest(kind=kind), self.assertRaises(ValueError): audit_transport(raw, pack(doc, binary), cards, data)
