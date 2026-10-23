import copy
from pathlib import Path
import unittest

from treegen.foliage import digest
from treegen.foliage_canopy import (budget, diamond_vertices, group_placements, load_canopy,
    profile_molds, region_quotas, sample_exposed, select_canopy, validate_canopy)
from treegen.foliage_mold_density import density_placements, load_density

ROOT = Path(__file__).resolve().parents[1]


class CanopyTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_canopy(ROOT/'presets/foliage-canopy.json')
        self.regions = ('north', 'east', 'south', 'west')

    def test_representation_matches_approved_rf2(self):
        approved = load_density(ROOT/'presets/foliage-mold-density.json')
        carriers = [{'id': f'carrier:{i}', 'parent_branch_id': 'branch', 'mold_id': 'mold',
            'points_m': [[0, i*.1, 0], [.2, i*.1, 1]],
            'normal_start': [.6, 0, .8], 'normal_end': [.6, 0, .8]} for i in range(24)]
        old = {leaf['id']: leaf for leaf in density_placements(approved, carriers)}
        new = {leaf['id']: leaf for carrier in carriers for leaf in group_placements(self.spec, carrier)}
        self.assertEqual(old, new)

    def test_region_allocation_and_budget(self):
        counts = dict(zip(self.regions, (10, 20, 30, 40)))
        initial, full = region_quotas(264, counts, self.spec['region_weights'])
        self.assertEqual(sum(full.values()), 264)
        _, opened = region_quotas(264, counts, dict(self.spec['region_weights'], east=.4))
        self.assertLess(opened['east'], full['east'])
        for region in ('north', 'south', 'west'):
            self.assertEqual(opened[region], full[region])
        self.assertEqual(budget(5292, 264)['triangles'], 10572)
        self.assertEqual(budget(5292, 360)['triangles'], 12492)
        for args in [(5292, 361), (10000, 264), (True, 24)]:
            with self.assertRaises(ValueError):
                budget(*args)

    def test_profile_sampling_and_interior_rejection(self):
        molds = [{'id': str(i), 'parent_branch_id': 'branch',
            'vertices': [[i*2, 0, 2], [i*2+1, 0, 2], [i*2, 1, 2]], 'triangles': [[0, 1, 2]]} for i in range(4)]
        original = digest(molds)
        wider = profile_molds(dict(self.spec, profile_width_scale=1.12), molds, [0, 0, 0])
        self.assertEqual(original, digest(molds))
        self.assertAlmostEqual(wider[1]['vertices'][0][0], 2.24)
        self.assertEqual(wider[1]['vertices'][0][2], 2)
        pool, report = sample_exposed(self.spec, molds, [0, 0, 0], lambda identifier, point: identifier != '0')
        self.assertEqual(report['attempts'], 8192)
        self.assertGreater(report['interior_rejected'], 0)
        self.assertTrue(all(c['mold_id'] != '0' for c in pool))
        self.assertEqual(pool, sample_exposed(self.spec, molds, [0, 0, 0], lambda identifier, point: identifier != '0')[0])

    def test_height_rejection_and_isolated_region_change(self):
        spec = dict(self.spec, group_count=24)
        pool = []
        for region, x, y in [('north', 0, 3), ('east', 3, 0), ('south', 0, -3), ('west', -3, 0)]:
            for i in range(24):
                pool.append({'id': f'{region}:{i:02d}', 'region': region, 'mold_id': region,
                    'parent_branch_id': 'branch', 'normal': [0, 0, 1],
                    'surface_m': [x+i*.01, y+i*.01, 9.2 if i < 6 else 2.]})
        parent = lambda branch, p: ([p[0], p[1], p[2]-.6], [0, 0, 1])
        carriers, leaves, report = select_canopy(spec, pool, parent, 9)
        self.assertEqual(len(carriers), 24)
        self.assertGreater(report['rejected_connections']['height'], 0)
        self.assertTrue(all(0 <= p[2] <= 9 for leaf in leaves for p in diamond_vertices(leaf)))
        opened = copy.deepcopy(spec)
        opened['region_weights']['east'] = .4
        changed, _, _ = select_canopy(opened, pool, parent, 9)
        for region in ('north', 'south', 'west'):
            self.assertEqual([c for c in carriers if c['region'] == region], [c for c in changed if c['region'] == region])
        smaller = dict(spec, leaf_length_m=.75)
        self.assertEqual(carriers, select_canopy(smaller, pool, parent, 9, layout_leaf_length_m=1.)[0])

    def test_reject_invalid_controls(self):
        for key, value in [('group_count', 361), ('group_count', 264.), ('seed', True),
                           ('profile_width_scale', float('nan')), ('leaf_length_m', 0), ('extra', 1)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_canopy(dict(self.spec, **{key: value}))
        with self.assertRaises(ValueError):
            validate_canopy(dict(self.spec, region_weights={r: 0 for r in self.regions}))
