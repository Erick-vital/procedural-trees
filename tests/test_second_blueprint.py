"""B4: reutilización sin nuevos componentes y condiciones fijadas antes del ensayo."""
import copy
import json
import unittest

from treegen.blueprints import ROOT, load_blueprint, resolve_blueprint, registered_blueprints


class SecondBlueprintTests(unittest.TestCase):
    def setUp(self):
        self.blueprint = load_blueprint(ROOT / 'blueprints/arbol_copa_columnar/1.0.0.json')
        self.matrix = json.loads((ROOT / 'configs/verification/b4-v1.json').read_text())

    def test_second_type_reuses_components_and_materials_but_changes_architecture(self):
        first = load_blueprint(ROOT / 'blueprints/roble_copa_ancha/1.2.0.json')
        self.assertEqual(self.blueprint['components'], first['components'])
        self.assertEqual(self.blueprint['appearance'], first['appearance'])
        self.assertNotEqual(self.blueprint['parameters']['base'], first['parameters']['base'])
        self.assertLess(self.blueprint['parameters']['base']['inclination_deg'],
                        first['parameters']['base']['inclination_deg'])
        self.assertIn(('arbol_copa_columnar', '1.0.0'), [(x['id'], x['version']) for x in registered_blueprints()])

    def test_four_seeds_use_identical_profile_parameters_and_canopy_seed(self):
        cases = [c for c in self.matrix['cases'] if c['kind'] in ('pilot', 'reserved')]
        self.assertEqual([c['instance']['seeds']['base'] for c in cases], [4100,4101,4102,4103])
        resolved = [resolve_blueprint(self.blueprint, c['instance']) for c in cases]
        for c,r in zip(cases,resolved):
            self.assertNotIn('overrides', c['instance'])
            self.assertEqual(r['parameters'], resolved[0]['parameters'])
            self.assertEqual(r['canopy_spec']['seed'], 73)
            self.assertEqual(r['budget_upper_bound']['triangles_max'],11756)

    def test_budget_boundary_fails_before_geometry_without_clamping(self):
        request = copy.deepcopy(self.matrix['cases'][0]['instance'])
        request['overrides'] = {'canopy': {'group_count':337}}
        result = resolve_blueprint(self.blueprint,request)
        self.assertEqual(result['budget_upper_bound']['triangles_max'],12496)
        request['overrides']['canopy']['group_count'] = 338
        with self.assertRaises(ValueError):
            resolve_blueprint(self.blueprint,request)
