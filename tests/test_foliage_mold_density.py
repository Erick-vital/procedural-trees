import copy
from pathlib import Path
import unittest

from treegen.foliage import cross, dot, sub
from treegen.foliage_molds import mold_placements
from treegen.foliage_mold_density import budget, density_placements, load_density, validate_density

ROOT = Path(__file__).resolve().parents[1]


class MoldDensityTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_density(ROOT/'presets/foliage-mold-density.json')
        self.carriers = [{'id': f'support:{i}', 'parent_branch_id': 'branch', 'mold_id': 'mold',
            'points_m': [[0, i*.1, 0], [0, i*.1, 1]],
            'normal_start': [0, 0, 1], 'normal_end': [0, 0, 1]} for i in range(24)]

    def test_additions_preserve_every_surviving_leaf_and_connection(self):
        carriers = copy.deepcopy(self.carriers)
        previous = mold_placements(self.spec['base'], carriers)
        for extra, total, triangles in [(0, 96, 384), (24, 120, 432), (48, 144, 480), (96, 192, 576)]:
            spec = dict(self.spec, extra_leaf_count=extra)
            leaves = density_placements(spec, carriers)
            self.assertEqual(leaves[:len(previous)], previous)
            self.assertEqual(len(leaves), total)
            self.assertEqual(len({leaf['id'] for leaf in leaves}), total)
            self.assertEqual(budget(spec)['added_triangles'], triangles)
            self.assertEqual(leaves, density_placements(spec, carriers))
            previous = leaves
        self.assertEqual(carriers, self.carriers)
        for leaf in previous[96:]:
            self.assertTrue(.8075 <= leaf['surface_segment_t'] <= .9225)
            x, y, z = leaf['axes']
            self.assertAlmostEqual(dot(cross(x, y), z), 1)
            self.assertAlmostEqual(dot(x, x), 1)
            origin = leaf['origin_m']
            self.assertAlmostEqual(origin[0], 0)
            self.assertTrue(.8075 <= origin[2] <= .9225)

    def test_budget_ceiling_and_invalid_controls(self):
        edge = dict(self.spec, extra_leaf_count=135)
        validate_density(edge)
        self.assertEqual(budget(edge)['leaves'], 231)
        self.assertLessEqual(budget(edge)['repeated_11_tree_triangles'], 12500)
        for extra in (-1, 136, 144, True, 48., float('nan')):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                validate_density(dict(self.spec, extra_leaf_count=extra))
        with self.assertRaises(ValueError):
            validate_density(dict(self.spec, unknown=1))
        bad = copy.deepcopy(self.spec)
        bad['base']['variant'] = 'folded-hex'
        with self.assertRaises(ValueError):
            validate_density(bad)
