import copy
import json
from pathlib import Path
import unittest

from treegen.seasons import validate_profile, validate_source

ROOT = Path(__file__).resolve().parents[1]


class SeasonTests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads((ROOT/'configs/seasons/roble-otono-v1.json').read_text())

    def test_valid_profile(self):
        validate_profile(self.profile)

    def test_rejects_invalid_inputs(self):
        for key, value in [('amount', float('nan')), ('amount', True), ('seed', -1),
                           ('patch_scale_m', 0), ('green_retention', .9),
                           ('palette_srgb', ['#fff']*3), ('species', 'pino_conico'),
                           ('phase', 'winter'), ('limits', {'triangles': 7000, 'materials': 2})]:
            with self.subTest(key=key, value=value):
                profile = copy.deepcopy(self.profile)
                profile[key] = value
                with self.assertRaises(ValueError): validate_profile(profile)

    def test_source_identity_and_budget(self):
        import hashlib
        data = b'fixture'
        manifest = {'resolved_blueprint': {'blueprint_definition': {'id': 'roble_copa_ancha', 'version': '2.2.0'}},
                    'glb_sha256': hashlib.sha256(data).hexdigest(),
                    'metrics': {'triangles': 6999, 'triangles_by_material': {'Painted_Bark': 5000, 'Painted_Foliage': 1999}}}
        validate_source(manifest, self.profile, data)
        with self.assertRaises(ValueError): validate_source(manifest, self.profile, b'changed')
        manifest['metrics']['triangles'] = 7000
        with self.assertRaises(ValueError): validate_source(manifest, self.profile, data)
