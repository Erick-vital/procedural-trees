import copy
import math
from pathlib import Path
import unittest

from treegen.foliage import digest, dot, cross
from treegen.foliage_branch import (branch_placements, load_branch, path_sample,
                                    supports, validate_branch)

ROOT = Path(__file__).resolve().parents[1]


class BranchFoliageTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_branch(ROOT/'presets/foliage-branch.json')
        self.branches = [{'id': f'q3:test:{i}', 'points_final_m': [[0, i, 0], [2, i, .2], [4, i+.2, .7]]} for i in range(4)]
        self.surface = lambda branch, point, direction: [x+.05*y for x, y in zip(point, direction)]

    def test_nested_supports_and_density_independence(self):
        base = supports(self.spec, self.branches, self.surface)
        changed = copy.deepcopy(self.spec)
        changed['support_count'] = 20
        more = supports(changed, self.branches, self.surface)
        self.assertEqual(base, more[:16])
        changed['support_count'] = 16
        changed['leaves_per_m'] = 12
        self.assertEqual(base, supports(changed, self.branches, self.surface))
        self.assertEqual(len(branch_placements(self.spec, base)), 64)
        self.assertEqual(len(branch_placements(changed, base)), 96)
        self.assertEqual(digest(base), digest(supports(self.spec, self.branches, self.surface)))

    def test_terminal_same_size_orientation_and_count(self):
        carriers = supports(self.spec, self.branches, self.surface)
        longitudinal = branch_placements(self.spec, carriers)
        self.spec['pattern'] = 'terminal'
        terminal = branch_placements(self.spec, carriers)
        self.assertEqual(len(longitudinal), len(terminal))
        for a, b in zip(longitudinal, terminal):
            for key in ('id', 'axes', 'length_m', 'width_ratio', 'fold_deg'):
                self.assertEqual(a[key], b[key])
            self.assertGreaterEqual(b['support_t'], .85)
        self.assertNotEqual(digest(longitudinal), digest(terminal))

    def test_roots_on_path_and_frame_smoothness(self):
        carriers = supports(self.spec, self.branches, self.surface)
        lookup = {c['id']: c for c in carriers}
        for leaf in branch_placements(self.spec, carriers):
            point = path_sample(lookup[leaf['support_id']]['points_m'], leaf['support_t'])[0]
            self.assertLess(math.dist(point, leaf['origin_m']), 1e-10)
            x, y, z = leaf['axes']
            self.assertAlmostEqual(dot(cross(x, y), z), 1)
        changed = copy.deepcopy(self.spec)
        changed['leaf']['leaf_length_m'] = .3
        self.assertEqual(carriers, supports(changed, self.branches, self.surface))
        for a, b in zip(branch_placements(self.spec, carriers), branch_placements(changed, carriers)):
            self.assertEqual(a['origin_m'], b['origin_m'])
            self.assertEqual(a['axes'], b['axes'])

    def test_reject_work_nonfinite_and_unknown_fields(self):
        for key, value in [('support_count', 25), ('support_count', True), ('seed', 17.),
                           ('leaves_per_m', float('nan')), ('support_length_m', float('inf')),
                           ('pattern', 'sphere'), ('unknown', 1)]:
            changed = copy.deepcopy(self.spec)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_branch(changed)
        changed = copy.deepcopy(self.spec)
        changed.update(support_count=24, support_length_m=.8, leaves_per_m=20)
        with self.assertRaises(ValueError):
            validate_branch(changed)


if __name__ == '__main__':
    unittest.main()
