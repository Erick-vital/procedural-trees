import copy
import unittest
from treegen.contracts import ROOT, load_spec, validate_spec, spec_hash


class ContractsTest(unittest.TestCase):
    def test_presets(self):
        for name in ('joven', 'adulto', 'viejo'):
            spec = load_spec(ROOT / f'presets/{name}.json')
            self.assertEqual(spec_hash(spec), spec_hash(dict(reversed(list(spec.items())))))

    def test_versioned_algorithms(self):
        spec = load_spec(ROOT / 'presets/viejo.json')
        for version in ('0.1.0', '0.2.0', '0.2.1', '0.3.0', '0.4.0', '0.4.1'):
            spec['algorithm_version'] = version
            validate_spec(spec)

    def test_invalid(self):
        base = load_spec(ROOT / 'presets/joven.json')
        for key, value in [('max_depth', 3), ('primary_branches', 100000),
                           ('height_m', float('nan')), ('height_m', float('inf')),
                           ('height_m', True), ('foliage_density', -1), ('unknown', 1)]:
            with self.subTest(key=key, value=value):
                spec = copy.deepcopy(base)
                spec['parameters'][key] = value
                with self.assertRaises(ValueError):
                    validate_spec(spec)
        for key, value in [('seed', -1), ('seed', True), ('algorithm', 'unknown'), ('algorithm_version', '9.9.9')]:
            spec = copy.deepcopy(base)
            spec[key] = value
            with self.assertRaises(ValueError):
                validate_spec(spec)
