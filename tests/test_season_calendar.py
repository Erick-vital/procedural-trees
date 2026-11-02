import copy
import json
import math
from pathlib import Path
import unittest

from treegen.season_calendar import build_calendar, validate_profile, validate_groups, validate_calendar, weight

ROOT = Path(__file__).resolve().parents[1]


def profile():
    return json.loads((ROOT/'configs/seasons/roble-calendario-v1.json').read_text())


def volumes():
    return [{'id': name, 'center_m': [x, 0, 0], 'size_m': [2, 2, 2],
             'axes': [[1, 0, 0], [0, 1, 0], [0, 0, 1]]} for name, x in [('a', 0), ('b', .5), ('c', 2)]]


class CalendarTests(unittest.TestCase):
    def test_profile_resources_and_hashes(self):
        p = profile()
        validate_profile(p)
        p['resources']['summer']['sha256'] = '0'*64
        with self.assertRaises(ValueError): validate_profile(p)
        p = profile()
        p['resources']['summer']['path'] = '../outside.png'
        with self.assertRaises(ValueError): validate_profile(p)

    def test_profile_rejects_unknown_species_phase_and_fields(self):
        for k, v in [('species', 'pino'), ('phase', 'winter'), ('seed', True),
                     ('seed', -1), ('extra', 1)]:
            p = profile()
            p[k] = v
            with self.subTest(key=k), self.assertRaises(ValueError): validate_profile(p)

    def test_intervals_and_sampling_limits(self):
        for section, key, value in [('calendar', 'duration_min', 0), ('calendar', 'duration_max', .8),
                                    ('calendar', 'start_min', .9), ('calendar', 'correlation', math.nan),
                                    ('exposure', 'rays', 13), ('exposure', 'neighbors', 25),
                                    ('exposure', 'neighbors', 24.0), ('limits', 'triangles', 7000)]:
            p = profile()
            p[section][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): validate_profile(p)

    def test_determinism_and_input_order(self):
        p, g = profile(), volumes()
        a = build_calendar(g, p)
        self.assertEqual(a, build_calendar(copy.deepcopy(g), p))
        self.assertEqual(a, build_calendar(list(reversed(g)), p))

    def test_seed_is_independent_and_not_modulo_8191(self):
        p, g = profile(), volumes()
        before = copy.deepcopy(g)
        a = build_calendar(g, p)
        p['seed'] += 8191
        b = build_calendar(g, p)
        self.assertNotEqual(a['groups'], b['groups'])
        self.assertEqual([r['exposure'] for r in a['groups']], [r['exposure'] for r in b['groups']])
        self.assertEqual(g, before)

    def test_exposed_group_changes_before_buried_group(self):
        p = profile()
        p['calendar']['exposure_weight'] = 1
        lone = build_calendar(volumes()[:1], p)['groups'][0]
        covered = build_calendar(volumes(), p)['groups'][0]
        self.assertEqual(lone['exposure'], 1)
        self.assertLess(covered['exposure'], lone['exposure'])
        self.assertLess(lone['start'], covered['start'])

    def test_work_is_bounded(self):
        g = volumes()[0]
        many = [{**copy.deepcopy(g), 'id': f'g{i}'} for i in range(30)]
        data = build_calendar(many, profile())
        self.assertTrue(all(len(r['neighbors']) == 24 for r in data['groups']))
        with self.assertRaises(ValueError): validate_groups(many*13)

    def test_geometry_validation(self):
        g = volumes()
        with self.assertRaises(ValueError): validate_groups(g+[g[0]])
        for key, value in [('center_m', [math.inf, 0, 0]), ('size_m', [0, 1, 1]),
                           ('axes', [[1, 0, 0]]*3)]:
            bad = volumes()
            bad[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): validate_groups(bad)

    def test_weight_endpoints_monotonicity_and_random_access(self):
        for r in build_calendar(volumes(), profile())['groups']:
            values = [weight(i/120, r['start'], r['duration']) for i in range(121)]
            self.assertEqual(values[0], 0)
            self.assertEqual(values[-1], 1)
            self.assertEqual(values, sorted(values))
            self.assertEqual(values, list(reversed([weight(i/120, r['start'], r['duration']) for i in reversed(range(121))])))
        for args in [(math.nan, .2, .2), (.5, .2, 0), (1.1, .2, .2), (.5, .9, .2)]:
            with self.assertRaises(ValueError): weight(*args)

    def test_output_contract_rejects_corruption(self):
        data = build_calendar(volumes(), profile())
        bad = copy.deepcopy(data)
        bad['groups'][0]['duration'] = 1
        with self.assertRaises(ValueError): validate_calendar(bad)
        bad = copy.deepcopy(data)
        bad['groups'][0]['neighbors'] = ['missing']
        with self.assertRaises(ValueError): validate_calendar(bad)
        bad = copy.deepcopy(data)
        bad['groups'].append(bad['groups'][0])
        with self.assertRaises(ValueError): validate_calendar(bad)
