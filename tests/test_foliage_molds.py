import copy
from pathlib import Path
import unittest

from treegen.foliage import cross, dot, norm, sub
from treegen.foliage_molds import (budget, load_mold_spec, mold_placements,
    sample_surface, select_supports, validate_mold_spec, validate_molds, connection_geometry)

ROOT = Path(__file__).resolve().parents[1]


class MoldFoliageTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_mold_spec(ROOT/'presets/foliage-molds.json')
        self.molds = [{'id': 'small', 'parent_branch_id': 'branch',
            'vertices': [[0, 0, 0], [1, 0, 0], [0, 1, 0]], 'triangles': [[0, 1, 2]]},
            {'id': 'large', 'parent_branch_id': 'branch',
            'vertices': [[2, 0, 0], [4, 0, 0], [2, 2, 0]], 'triangles': [[0, 1, 2]]}]
        self.exposed = lambda mold_id, point: True
        self.project = lambda mold_id, point: ((point[0], point[1], 0), (0, 0, 1))
        self.parent = lambda branch_id, point: ((point[0], point[1], -.7), (0, 0, 1))

    def layout(self, spec):
        candidates, diagnostics = sample_surface(spec, self.molds, self.exposed)
        carriers, selection = select_supports(spec, candidates, self.project, self.parent, self.exposed)
        return carriers, mold_placements(spec, carriers), diagnostics

    def test_area_sampling_and_interior_rejection(self):
        candidates, diagnostics = sample_surface(self.spec, self.molds, self.exposed)
        large = sum(c['mold_id'] == 'large' for c in candidates)
        self.assertLess(abs(large/2048-.8), .035)
        filtered, report = sample_surface(self.spec, self.molds, lambda m, p: m != 'small')
        self.assertEqual(len(filtered)+report['interior_rejected'], 2048)
        self.assertTrue(all(c['mold_id'] == 'large' for c in filtered))
        self.assertEqual(diagnostics['attempts'], 2048)
        self.assertEqual(candidates, sample_surface(self.spec, self.molds, self.exposed)[0])

    def test_size_pair_keeps_supports_roots_axes_and_budget(self):
        carriers, leaves, _ = self.layout(self.spec)
        changed = dict(self.spec, leaf_length_m=.8)
        other_carriers, other_leaves, _ = self.layout(changed)
        self.assertEqual(carriers, other_carriers)
        self.assertEqual(budget(self.spec), budget(changed))
        self.assertEqual(budget(self.spec)['added_triangles'], 416)
        for a, b in zip(leaves, other_leaves):
            for key in ('id', 'origin_m', 'axes', 'support_id'):
                self.assertEqual(a[key], b[key])
            self.assertAlmostEqual(b['length_m']/a['length_m'], .8/.45)
            x, y, z = a['axes']
            self.assertAlmostEqual(dot(cross(x, y), z), 1)
            self.assertAlmostEqual(dot(x, x), 1)

    def test_connections_nested_seed_and_roots(self):
        carriers, leaves, _ = self.layout(self.spec)
        fewer, _, _ = self.layout(dict(self.spec, group_count=12))
        self.assertEqual(carriers[:12], fewer)
        self.assertNotEqual(carriers, self.layout(dict(self.spec, seed=18))[0])
        lookup = {c['id']: c for c in carriers}
        for leaf in leaves:
            a, b = lookup[leaf['support_id']]['points_m'][1:]
            direction = norm(sub(b, a))
            self.assertLess(dot(cross(sub(leaf['origin_m'], a), direction), cross(sub(leaf['origin_m'], a), direction)), 1e-20)
        self.assertTrue(all(c['length_m'] <= 4 for c in carriers))

    def test_reject_bad_work_and_geometry(self):
        for key, value in [('group_count', 24), ('group_count', True), ('seed', 17.),
                           ('leaf_length_m', float('nan')), ('twig_radius_m', 0), ('extra', 1)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_mold_spec(dict(self.spec, **{key: value}))
        for face in ([0, 0, 1], [0, 1, 5], [False, 1, 2]):
            changed = copy.deepcopy(self.molds)
            changed[0]['triangles'] = [face]
            with self.assertRaises(ValueError):
                validate_molds(changed)
        with self.assertRaises(ValueError):
            sample_surface(self.spec, self.molds, lambda m, p: False)

    def test_efficient_pair_closed_tubes_and_budget(self):
        spec = dict(self.spec, connection_shape='straight', variant='diamond', group_count=24, leaves_per_group=4)
        carriers, leaves, _ = self.layout(spec)
        self.assertEqual(budget(spec)['added_triangles'], 384)
        self.assertEqual(len(leaves), 96)
        for carrier in carriers:
            vertices, faces = connection_geometry(carrier, spec)
            self.assertEqual(len(faces), 8)
            edges = {(u, v) for a, b, c in faces for u, v in ((a, b), (b, c), (c, a))}
            self.assertTrue(all((v, u) in edges for u, v in edges))
            volume = sum(dot(vertices[a], cross(vertices[b], vertices[c]))/6 for a, b, c in faces)
            self.assertGreater(volume, 0)
        self.assertTrue(all(leaf['variant'] == 'diamond' and leaf['fold_deg'] == 0 for leaf in leaves))


if __name__ == '__main__':
    unittest.main()
