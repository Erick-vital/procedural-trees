"""B3: preservación de referencia y matriz de edades sin retoques por semilla."""
import copy
import json
import unittest

from treegen.blueprints import ROOT, load_blueprint, load_instance, resolve_blueprint


class BlueprintControlTests(unittest.TestCase):
    def setUp(self):
        self.blueprint = load_blueprint(ROOT / 'blueprints/roble_copa_ancha/1.1.0.json')
        self.matrix = json.loads((ROOT / 'configs/verification/b3-v1.json').read_text())

    def test_new_recipe_preserves_reference_parameters_and_seeds(self):
        old = load_blueprint(ROOT / 'blueprints/roble_copa_ancha/1.0.0.json')
        instance = load_instance(ROOT / 'presets/blueprints/roble-copa-ancha-viejo-09.json')
        before = resolve_blueprint(old, instance)
        instance['blueprint_version'] = '1.1.0'
        after = resolve_blueprint(self.blueprint, instance)
        for key in ('base_spec', 'canopy_spec', 'base_seeds', 'appearance', 'layout_leaf_length_m'):
            self.assertEqual(before[key], after[key])

    def test_age_profiles_reuse_q3_parameters_with_common_canopy(self):
        q3 = {c['id']:c['spec'] for c in json.loads((ROOT / 'presets/q3-cases.json').read_text())}
        for case in self.matrix['cases']:
            if case['kind'] not in ('age', 'reserved'):
                continue
            self.assertNotIn('overrides', case['instance'])
            resolved = resolve_blueprint(self.blueprint, case['instance'])
            self.assertEqual(resolved['base_spec'], q3[case['id']])
            self.assertEqual(resolved['parameters']['canopy'], self.matrix['common_canopy'])
            self.assertEqual(resolved['profile_validation_claim']['status'], 'experimental')

    def test_reserved_cases_are_distinct_from_adjustment_and_required_cases(self):
        reserved = [c for c in self.matrix['cases'] if c['kind']=='reserved']
        self.assertEqual({c['instance']['seeds']['base'] for c in reserved}, {1007,2007,3007})
        self.assertEqual({c['instance']['profile'] for c in reserved}, {'joven','adulto','viejo'})
        required = {'viejo-00','viejo-03','adulto-00','joven-00'}
        self.assertTrue(required <= {c['id'] for c in self.matrix['cases']})

    def test_empty_canopy_and_out_of_contract_fail_before_generation(self):
        for case in self.matrix['cases']:
            if case['expect']=='reject':
                with self.subTest(case=case['id']), self.assertRaises(ValueError):
                    resolve_blueprint(self.blueprint, case['instance'])

    def test_maximum_groups_stays_under_budget_without_clamping(self):
        case = next(c for c in self.matrix['cases'] if c['id']=='groups-max')
        resolved = resolve_blueprint(self.blueprint, case['instance'])
        self.assertEqual(resolved['budget_upper_bound']['triangles_max'], 12492)
        self.assertEqual(resolved['canopy_spec']['group_count'], 360)


class BlueprintRevisedControlTests(unittest.TestCase):
    def test_revised_young_profile_changes_only_leaf_size(self):
        before_bp = load_blueprint(ROOT / 'blueprints/roble_copa_ancha/1.1.0.json')
        after_bp = load_blueprint(ROOT / 'blueprints/roble_copa_ancha/1.2.0.json')
        for name in ('joven-00', 'joven-07', 'adulto-00', 'viejo-00'):
            before_i = load_instance(ROOT / 'presets/blueprints/b3' / (name+'.json'))
            after_i = load_instance(ROOT / 'presets/blueprints/b3-v2' / (name+'.json'))
            a = resolve_blueprint(before_bp, before_i)
            b = resolve_blueprint(after_bp, after_i)
            self.assertEqual(a['base_spec'], b['base_spec'])
            self.assertEqual(a['layout_leaf_length_m'], b['layout_leaf_length_m'])
            expected = copy.deepcopy(a['canopy_spec'])
            if name.startswith('joven'):
                expected['leaf_length_m'] = .45
            expected['version'] = 'foliage-canopy-0.1.1'
            self.assertEqual(expected, b['canopy_spec'])
            self.assertEqual(a['budget_upper_bound'], b['budget_upper_bound'])

    def test_previous_failed_extreme_remains_requested_for_generation(self):
        before = json.loads((ROOT / 'configs/verification/b3-v1.json').read_text())
        after = json.loads((ROOT / 'configs/verification/b3-v3.json').read_text())
        a = next(c for c in before['cases'] if c['id']=='height-high-scale-low')
        b = next(c for c in after['cases'] if c['id']=='height-high-scale-low')
        self.assertEqual(b['expect'], 'generate')
        self.assertEqual(a['instance']['overrides'], b['instance']['overrides'])
        self.assertEqual(a['instance']['seeds'], b['instance']['seeds'])
        bp = load_blueprint(ROOT / after['blueprint'])
        resolved = resolve_blueprint(bp, b['instance'])
        self.assertEqual(resolved['base_spec']['parameters']['height_m'], 20)
        self.assertEqual(resolved['base_spec']['parameters']['foliage_scale_m'], .2)
