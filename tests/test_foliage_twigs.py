import copy
from pathlib import Path
import tempfile
import unittest

from treegen.foliage import cross, dot, sub
from treegen.foliage_twigs import (budget, build_layout, load_twigs, target_region,
                                  twig_geometry, validate_twigs)

ROOT = Path(__file__).resolve().parents[1]


class TwigFoliageTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_twigs(ROOT/'presets/foliage-twigs.json')
        self.branches = [{'id': f'q3:test:{i}', 'points_final_m': [[0, i*.2, 0], [2, i*.2, .2], [4, i*.2, .7]]} for i in range(4)]
        self.surface = lambda branch, point, direction: [x+.05*y for x, y in zip(point, direction)]
        self.target = target_region([[1, -.8, -.5], [4.6, 1.2, 1.5]], 'frozen-test')

    def test_pair_preserves_every_placement(self):
        original = build_layout(self.spec, self.branches, self.surface, self.target)
        changed = copy.deepcopy(self.spec)
        changed['twigs']['enabled'] = False
        self.assertEqual(original, build_layout(changed, self.branches, self.surface, self.target))
        self.assertEqual(budget(self.spec)['added_triangles'], 480)
        self.assertEqual(budget(changed)['added_triangles'], 256)

    def test_directed_selection_repeat_nested_and_leaf_independent(self):
        self.spec['distribution']['mode'] = 'target'
        carriers, leaves, diagnostics = build_layout(self.spec, self.branches, self.surface, self.target)
        self.assertEqual(diagnostics['candidate_count'], 192)
        self.assertLessEqual(diagnostics['selected_cells'], diagnostics['reachable_cells'])
        self.assertEqual((carriers, leaves, diagnostics), build_layout(self.spec, self.branches, self.surface, self.target))
        changed = copy.deepcopy(self.spec)
        changed['base']['support_count'] = 12
        self.assertEqual(carriers[:12], build_layout(changed, self.branches, self.surface, self.target)[0])
        changed['base'].update(support_count=16, leaves_per_m=12)
        changed['base']['leaf']['leaf_length_m'] = .3
        self.assertEqual(carriers, build_layout(changed, self.branches, self.surface, self.target)[0])
        changed['base']['seed'] = 18
        self.assertNotEqual(carriers, build_layout(changed, self.branches, self.surface, self.target)[0])

    def test_guidance_changes_spatial_contribution(self):
        original = build_layout(self.spec, self.branches, self.surface, self.target)[2]
        self.spec['distribution']['mode'] = 'target'
        guided = build_layout(self.spec, self.branches, self.surface, self.target)[2]
        self.assertGreater(guided['selected_cells'], original['selected_cells'])
        self.assertLessEqual(len(self.target['cells_m']), 256)
        for cell in self.target['cells_m']:
            self.assertLessEqual(sum(((x-c)/r)**2 for x, c, r in zip(cell, self.target['center_m'], self.target['radii_m'])), 1)

    def test_tube_is_closed_outward_and_bounded(self):
        carrier = {'points_m': [[0, 0, 0], [.3, 0, 0], [.6, 0, 0]]}
        for sides in (3, 4):
            twig = dict(self.spec['twigs'], profile_sides=sides)
            vertices, faces = twig_geometry(carrier, twig)
            edges = {}
            volume = 0
            for a, b, c in faces:
                normal = cross(sub(vertices[b], vertices[a]), sub(vertices[c], vertices[a]))
                self.assertGreater(dot(normal, normal), 1e-15)
                volume += dot(vertices[a], cross(vertices[b], vertices[c]))/6
                for u, v in ((a, b), (b, c), (c, a)):
                    edges[(u, v)] = edges.get((u, v), 0)+1
            self.assertGreater(volume, 0)
            self.assertTrue(all(count == 1 and edges.get((v, u)) == 1 for (u, v), count in edges.items()))
            self.assertEqual(len(faces), 4*sides+2*(sides-2))
            self.assertEqual(len(vertices), 3*sides)
            self.assertAlmostEqual(sum(vertices[i][0] for i in range(sides))/sides, -.025)

    def test_reject_budget_invalid_numbers_and_unknown_fields(self):
        for key, value in [('radius_m', 0), ('radius_m', float('nan')), ('profile_sides', 3.),
                           ('profile_sides', True), ('enabled', 1), ('extra', 1)]:
            changed = copy.deepcopy(self.spec)
            changed['twigs'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_twigs(changed)
        changed = copy.deepcopy(self.spec)
        changed['base'].update(support_count=24, support_length_m=.8, leaves_per_m=10)
        with self.assertRaises(ValueError):
            validate_twigs(changed)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'duplicate.json'
            path.write_text('{"version":1,"version":2}')
            with self.assertRaises(ValueError):
                load_twigs(path)
        for cells in ([[0, 0, 0]]*257, [[float('nan'), 0, 0]], [[0, 0]], [[True, 0, 0]]):
            with self.assertRaises(ValueError):
                build_layout(self.spec, self.branches, self.surface, dict(self.target, cells_m=cells))


if __name__ == '__main__':
    unittest.main()
