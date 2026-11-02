"""Contrato, presupuesto, determinismo y separación de semillas del sauce."""
import copy
import unittest
from unittest.mock import patch

from treegen.blueprints import ROOT, load_blueprint, load_instance, resolve_blueprint, validate_blueprint
from treegen.willow import build, validate_resources, budget, TOLERANCE_M
from treegen.pine import point_on, cross, sub


class WillowTests(unittest.TestCase):
    def setUp(self):
        self.b = load_blueprint(ROOT/'blueprints/sauce_colgante/1.0.0.json')
        self.i = load_instance(ROOT/'presets/blueprints/sauce-pintado/pilot.json')

    def resolve(self):
        return resolve_blueprint(self.b, self.i)

    def test_four_seeds_and_prior_budget(self):
        for name in ('pilot', 'control-01', 'control-02', 'control-03'):
            self.i = load_instance(ROOT/f'presets/blueprints/sauce-pintado/{name}.json')
            r = self.resolve()
            branches, wood, groups = build(r)
            self.assertEqual((len(branches), len(groups)), (113, 423))
            actual = sum(len(b['mesh']['polygons']) for b in wood)+sum(len(g['polygons']) for g in groups)
            self.assertLessEqual(actual, r['budget_upper_bound']['triangles_max'])
            self.assertLess(r['budget_upper_bound']['triangles_max'], 7000)
            self.assertEqual(len({g['id'] for g in groups}), 423)
            supports = {b['id']: b for b in branches}
            for group in groups:
                self.assertEqual(group['origin_m'], point_on(supports[group['support_id']], group['anchor_t']))
                self.assertEqual(len(group['polygons']), 6)
                self.assertTrue(all(0 <= v <= 1 for uv in group['uv'] for v in uv))
                # Bounds completos incluyen márgenes transparentes; la altura
                # nominal se certifica sobre madera, como en el contrato.
                self.assertLessEqual(group['origin_m'][2], 10)
                self.assertLess(group['axis'][2], -.95)
                self.assertGreater(min(v[2] for v in group['vertices']), .05)

    def test_determinism_and_seed_separation(self):
        a = build(self.resolve())
        self.assertEqual(a, build(self.resolve()))
        self.i['seeds']['canopy'] += 1
        b = build(self.resolve())
        self.assertEqual(a[:2], b[:2])
        self.assertNotEqual(a[2], b[2])
        self.i['seeds']['canopy'] -= 1
        self.i['seeds']['paint'] += 1
        c = build(self.resolve())
        self.assertEqual(a[:2], c[:2])
        self.assertEqual([g['origin_m'] for g in a[2]], [g['origin_m'] for g in c[2]])
        self.assertNotEqual([g['atlas_variant'] for g in a[2]], [g['atlas_variant'] for g in c[2]])

    def test_wood_error_endpoints_uv_and_non_degeneracy(self):
        original, wood, groups = build(self.resolve())
        for a, b in zip(original, wood):
            info = b['wood_optimization']
            self.assertLessEqual(info['ring_correspondence_error_m'], TOLERANCE_M)
            kept, sides = info['retained_rings'], b['sides']
            self.assertEqual((kept[0], kept[-1]), (0, len(a['points_m'])-1))
            self.assertEqual(a['mesh']['vertices'][:sides], b['mesh']['vertices'][:sides])
            self.assertEqual(a['mesh']['vertices'][-sides:], b['mesh']['vertices'][-sides:])
            self.assertEqual(len(b['uv']), len(b['mesh']['vertices']))
        for mesh in [b['mesh'] for b in wood]+groups:
            for i, j, k in mesh['polygons']:
                a, b, c = [mesh['vertices'][v] for v in (i, j, k)]
                normal = cross(sub(b, a), sub(c, a))
                self.assertGreater(sum(v*v for v in normal), 4e-20)

    def test_reject_budget_and_historical_techo(self):
        for triangles in (6477, 7000, 12500):
            with self.assertRaises(ValueError):
                budget(self.b['parameters'], {'triangles': triangles, 'materials': 2})
        p = copy.deepcopy(self.b['parameters'])
        p['base'].update(primary_count=14, secondary_count=10)
        p['canopy']['groups_per_secondary'] = 5
        with self.assertRaises(ValueError):
            budget(p, self.b['limits'])

    def test_preflight_prevents_geometric_work(self):
        resolved = self.resolve()
        resolved['parameters']['base'].update(primary_count=14, secondary_count=10)
        resolved['parameters']['canopy']['groups_per_secondary'] = 5
        with patch('treegen.willow.structure') as geometry:
            with self.assertRaises(ValueError):
                build(resolved)
            geometry.assert_not_called()

    def test_architecture_and_nominal_height(self):
        branches, _, groups = build(self.resolve())
        self.assertAlmostEqual(max(v[2] for b in branches for v in b['mesh']['vertices']), 10)
        self.assertAlmostEqual(min(v[2] for b in branches for v in b['mesh']['vertices']), 0)
        main = [b for b in branches if b['parent_id'] == 'willow:trunk' and ':p:' in b['id']]
        self.assertEqual(len(main), 12)
        for branch in main:
            z = [p[2] for p in branch['points_m']]
            self.assertGreater(max(z), z[-1])
            self.assertGreater(max(z), z[0])
        # Las hojas cuelgan incluso en primarias ascendentes.
        self.assertTrue(all(g['axis'][2] < -.95 for g in groups))

    def test_contract_rejects_unknown_values_and_overrides(self):
        for key, value in (('height_m', 12), ('primary_count', True), ('secondary_count', 1000), ('droop_ratio', float('nan'))):
            b = copy.deepcopy(self.b)
            b['parameters']['base'][key] = value
            with self.assertRaises(ValueError):
                validate_blueprint(b)
        self.i['overrides'] = {'base': {'height_m': 12}}
        with self.assertRaises(ValueError):
            self.resolve()

    def test_reject_seed_version_material_and_component_mismatch(self):
        for seed in (True, -1, 2147483647):
            i = copy.deepcopy(self.i)
            i['seeds']['paint'] = seed
            with self.assertRaises(ValueError):
                resolve_blueprint(self.b, i)
        for field, value in (('schema_version', '1.2'), ('blueprint_version', '9.0.0')):
            i = copy.deepcopy(self.i)
            i[field] = value
            with self.assertRaises(ValueError):
                resolve_blueprint(self.b, i)
        for role in self.b['components']:
            b = copy.deepcopy(self.b)
            b['components'][role] = 'pine-whorls@0.2.0'
            with self.assertRaises(ValueError):
                validate_blueprint(b)
        old = load_blueprint(ROOT/'blueprints/roble_copa_ancha/1.0.0.json')
        old['components']['base'] = 'willow-weeping@0.1.0'
        with self.assertRaises(ValueError):
            validate_blueprint(old)

    def test_reject_resources_and_missing_atlas(self):
        for role in self.b['resources']:
            for field, value in (('sha256', '0'*64), ('path', '../../missing')):
                resources = copy.deepcopy(self.b['resources'])
                resources[role][field] = value
                with self.assertRaises(ValueError):
                    validate_resources(resources)
