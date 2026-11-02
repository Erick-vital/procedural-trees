"""Revisión de sauce: bifurcación baja, diversidad de brazos y doble follaje."""
import copy
import math
import unittest

from treegen.blueprints import ROOT, load_blueprint, load_instance, resolve_blueprint, validate_blueprint
from treegen.willow import build, budget
from treegen.willow_v2 import build_sample
from treegen.pine import point_on, sub, cross


class WillowRevisionTests(unittest.TestCase):
    def resolve(self, name='pilot'):
        return resolve_blueprint(load_blueprint(ROOT/'blueprints/sauce_colgante/1.1.0.json'),
                                 load_instance(ROOT/f'presets/blueprints/sauce-revision/{name}.json'))

    def test_four_seeds_budget_height_and_roles(self):
        for name in ('pilot', 'control-01', 'control-02', 'control-03'):
            resolved = self.resolve(name)
            branches, wood, groups = build(resolved)
            self.assertEqual(len(branches), 93)
            self.assertEqual(len(groups), 587)
            self.assertEqual(resolved['budget_upper_bound']['triangles_max'], 6694)
            self.assertLessEqual(sum(len(b['mesh']['polygons']) for b in wood)+6*len(groups), 6694)
            trunk = branches[0]
            self.assertLess(trunk['points_m'][-1][2], 4.5)
            self.assertAlmostEqual(max(v[2] for b in branches for v in b['mesh']['vertices']), 10)
            self.assertEqual(sum(g['foliage_role'] == 'crown' for g in groups), 307)
            self.assertEqual(sum(g['foliage_role'] == 'curtain' for g in groups), 280)
            self.assertGreater(min(v[2] for g in groups for v in g['vertices']), .05)

    def test_unequal_limb_shapes_and_curtain_lengths(self):
        branches, _, _ = build(self.resolve())
        limbs = [b for b in branches if b['role'] == 'limb']
        # Comparar perfiles normalizados, independientes de giro/longitud.
        profiles = []
        for branch in limbs:
            p = branch['points_m']; origin, end = p[0], p[-1]
            rise = end[2]-origin[2]
            profiles.append(tuple(round((v[2]-origin[2])/rise, 3) for v in p))
        self.assertGreaterEqual(len(set(profiles)), 6)
        strands = [b for b in branches if b['role'] == 'strand']
        falls = [b['points_m'][0][2]-b['points_m'][-1][2] for b in strands]
        self.assertGreater(max(falls)-min(falls), 1)
        # Una primaria continúa el extremo del tronco; no queda un poste libre.
        self.assertTrue(any(b['points_m'][0] == branches[0]['points_m'][-1] for b in limbs))

    def test_supports_geometry_and_sample(self):
        resolved = self.resolve()
        branches, wood, groups = build(resolved)
        by_id = {b['id']: b for b in branches}
        for group in groups:
            self.assertLess(math.dist(group['origin_m'], point_on(by_id[group['support_id']], group['anchor_t'])), 1e-10)
            self.assertEqual(len(group['polygons']), 6)
        for mesh in [b['mesh'] for b in wood]+groups:
            for a, b, c in mesh['polygons']:
                normal = cross(sub(mesh['vertices'][b], mesh['vertices'][a]), sub(mesh['vertices'][c], mesh['vertices'][a]))
                self.assertGreater(sum(v*v for v in normal), 4e-20)
        sample = build_sample(resolved)
        self.assertEqual(len(sample['wood']), 11)
        self.assertEqual(len(sample['groups']), 74)
        self.assertEqual(sample['triangles'], 804)

    def test_determinism_and_independent_seeds(self):
        r = self.resolve(); first = build(r)
        self.assertEqual(first, build(self.resolve()))
        for seed in ('canopy', 'paint'):
            blueprint = load_blueprint(ROOT/'blueprints/sauce_colgante/1.1.0.json')
            request = copy.deepcopy(r['instance_request']); request['seeds'][seed] += 1
            changed = build(resolve_blueprint(blueprint, request))
            self.assertEqual(first[:2], changed[:2])
            self.assertNotEqual(first[2], changed[2])
            if seed == 'paint':
                self.assertEqual([g['origin_m'] for g in first[2]], [g['origin_m'] for g in changed[2]])

    def test_reject_mixed_versions(self):
        b = load_blueprint(ROOT/'blueprints/sauce_colgante/1.1.0.json')
        b['components']['distribution'] = 'willow-hanging-groups@0.1.0'
        with self.assertRaises(ValueError):
            validate_blueprint(b)

    def test_revised_budget_rejects_one_triangle_less(self):
        r = self.resolve()
        self.assertEqual(budget(r['parameters'], r['limits'], version='0.2.0')['triangles_max'], 6694)
        with self.assertRaises(ValueError):
            budget(r['parameters'], {**r['limits'], 'triangles': 6693}, version='0.2.0')
