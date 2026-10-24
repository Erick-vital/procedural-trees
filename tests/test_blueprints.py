import copy
import json
from pathlib import Path
import tempfile
import unittest

from treegen.blueprints import (
    ROOT, SCHEMA, INSTANCE_SCHEMA, canonical_hash, load_blueprint, load_instance,
    resolve_blueprint, validate_blueprint,
)
from jsonschema import Draft202012Validator


def fixture():
    """Datos de contrato para B1; no registra un blueprint de producción B2."""
    lock = json.loads((ROOT / 'docs/evidence/blueprints/b0/reference-lock.json').read_text())
    canopy = {k: v for k, v in lock['canopy_spec'].items() if k not in ('version', 'seed')}
    canopy['layout_leaf_length_m'] = 1.0
    materials = lock['snapshot']['oriented_export']['materials']
    appearance = {}
    for role, index in [('bark', 0), ('leaf', 1)]:
        mat = materials[index]
        pbr = mat['pbrMetallicRoughness']
        appearance[role] = {'color_rgba': pbr['baseColorFactor'], 'roughness': pbr['roughnessFactor'],
                            'metallic': pbr['metallicFactor'], 'double_sided': mat['doubleSided']}
    blueprint = {
        'schema_version': '1.0', 'id': 'b1_fixture', 'version': '0.0.0',
        'name': 'Fixture B1', 'description': 'Prueba del contrato; sin integración de generación.',
        'components': {'base': 'oak_geometry_nodes@0.4.0', 'distribution': 'foliage-canopy@0.1.0',
                       'representation': 'rf3-diamond-six@0.1.0'},
        'parameters': {'base': lock['base_spec']['parameters'], 'canopy': canopy},
        'appearance': appearance,
        'editable_ranges': {
            'base.height_m': {'minimum': 2, 'maximum': 20},
            'base.primary_branches': {'minimum': 1, 'maximum': 12},
            'base.max_depth': {'minimum': 1, 'maximum': 2},
            'base.foliage_density': {'minimum': 0, 'maximum': 1},
            'canopy.group_count': {'minimum': 24, 'maximum': 360},
            'canopy.leaf_length_m': {'minimum': .2, 'maximum': 1},
            **{f'canopy.region_weights.{r}': {'minimum': 0, 'maximum': 1}
               for r in ('north', 'east', 'south', 'west')},
        },
        'default_profile': 'viejo_referencia',
        'profiles': {
            'viejo_referencia': {'description': 'Solo el ejemplar RF3 aprobado', 'overrides': {},
                                'validation': {'status': 'reference_only', 'evidence': [
                                    'docs/evidence/blueprints/b0/reference-lock.json']}},
            'adulto_prueba': {'description': 'Datos sintéticos de prueba, sin validar geometría',
                             'overrides': {'base': {'height_m': 10}, 'canopy': {'group_count': 120}},
                             'validation': {'status': 'experimental', 'evidence': ['tests/test_blueprints.py']}},
        },
        'limits': {'triangles': 12500, 'materials': 3, 'generation_seconds': 120},
    }
    instance = {'schema_version': '1.0', 'blueprint_id': 'b1_fixture', 'blueprint_version': '0.0.0',
                'seeds': {'base': 3009, 'canopy': 17}}
    return blueprint, instance, lock


class BlueprintsTest(unittest.TestCase):
    def setUp(self):
        self.blueprint, self.instance, self.lock = fixture()

    def resolve(self, overrides):
        return resolve_blueprint(self.blueprint, dict(self.instance, overrides=overrides))

    def test_schemas_are_valid(self):
        for schema in (SCHEMA, INSTANCE_SCHEMA):
            Draft202012Validator.check_schema(schema)

    def test_reference_maps_to_exact_historical_inputs(self):
        result = resolve_blueprint(self.blueprint, self.instance)
        self.assertEqual(result['base_spec'], self.lock['base_spec'])
        self.assertEqual(result['canopy_spec'], self.lock['canopy_spec'])
        self.assertEqual(result['base_seeds'], {'structure': 669423365, 'foliage': 927115663})
        self.assertEqual(result['budget_upper_bound']['triangles_max'], 10572)
        self.assertEqual(result['budget_upper_bound']['leaves_max'], 1584)
        self.assertEqual(result['profile_validation_claim']['status'], 'reference_only')

    def test_precedence_and_partial_region_override(self):
        request = dict(self.instance, profile='adulto_prueba', overrides={
            'base': {'height_m': 11}, 'canopy': {'region_weights': {'east': .4}}})
        result = resolve_blueprint(self.blueprint, request)
        self.assertEqual(result['base_spec']['parameters']['height_m'], 11)
        self.assertEqual(result['canopy_spec']['group_count'], 120)
        self.assertEqual(result['canopy_spec']['region_weights'], {'north': 1, 'east': .4, 'south': 1, 'west': 1})
        self.assertTrue(result['parameters_differ_from_profile'])

    def test_deterministic_and_input_not_mutated(self):
        before = copy.deepcopy((self.blueprint, self.instance))
        first = resolve_blueprint(self.blueprint, self.instance)
        second = resolve_blueprint(dict(reversed(list(self.blueprint.items()))), self.instance)
        self.assertEqual(first, second)
        self.assertEqual((self.blueprint, self.instance), before)
        first['blueprint_definition']['name'] = 'Mutación externa'
        first['parameters']['canopy']['region_weights']['east'] = 0
        self.assertEqual((self.blueprint, self.instance), before)

    def test_seeds_and_leaf_scale_keep_structural_inputs(self):
        first = resolve_blueprint(self.blueprint, self.instance)
        request = dict(self.instance, seeds={'base': 3009, 'canopy': 18},
                       overrides={'canopy': {'leaf_length_m': .75}})
        second = resolve_blueprint(self.blueprint, request)
        self.assertEqual(first['base_spec'], second['base_spec'])
        self.assertEqual(first['base_seeds'], second['base_seeds'])
        self.assertEqual(second['layout_leaf_length_m'], 1)
        self.assertEqual(second['canopy_spec']['leaf_length_m'], .75)
        self.assertNotEqual(first['resolved_sha256'], second['resolved_sha256'])

    def test_combined_cost_rejected_even_when_each_change_fits(self):
        self.resolve({'base': {'primary_branches': 12}})
        self.resolve({'canopy': {'group_count': 360}})
        with self.assertRaisesRegex(ValueError, '12956'):
            self.resolve({'base': {'primary_branches': 12}, 'canopy': {'group_count': 360}})

    def test_unsupported_versions_paths_and_identity(self):
        for role in self.blueprint['components']:
            bp = copy.deepcopy(self.blueprint)
            bp['components'][role] = '/tmp/ejecutar.py'
            with self.assertRaisesRegex(ValueError, 'no registrado'):
                validate_blueprint(bp)
        for key, value in [('blueprint_id', 'otro'), ('blueprint_version', '2.0.0'), ('profile', 'ausente')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                resolve_blueprint(self.blueprint, dict(self.instance, **{key: value}))

    def test_unknown_fixed_out_of_range_and_nonfinite(self):
        cases = [
            {'base': {'unknown': 1}}, {'base': {'curvature': .2}},
            {'base': {'height_m': 21}}, {'base': {'height_m': True}},
            {'base': {'height_m': float('nan')}}, {'base': {'height_m': float('inf')}},
            {'canopy': {'group_count': 24.5}}, {'canopy': {'region_weights': {'up': 1}}},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.resolve(overrides)

    def test_empty_crown_and_absent_guides_rejected(self):
        for overrides in [
            {'base': {'foliage_density': 0}}, {'base': {'foliage_density': .12}},
            {'canopy': {'group_count': 0}},
            {'canopy': {'region_weights': {r: 0 for r in ('north', 'east', 'south', 'west')}}},
        ]:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.resolve(overrides)

    def test_seeds_and_counts_require_actual_integers(self):
        for value in (True, 17.0, -1, 2147483647):
            request = dict(self.instance, seeds={'base': 3009, 'canopy': value})
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_blueprint(self.blueprint, request)
        with self.assertRaises(ValueError):
            self.resolve({'base': {'primary_branches': 11.0}})
        with self.assertRaises(ValueError):
            self.resolve({'canopy': {'group_count': 264.0}})

    def test_invalid_ranges_defaults_profiles_and_material_budget(self):
        for edit in ('reversed', 'outside', 'fractional', 'default', 'profile', 'materials', 'opacity'):
            bp = copy.deepcopy(self.blueprint)
            if edit == 'reversed': bp['editable_ranges']['base.height_m'] = {'minimum': 20, 'maximum': 2}
            if edit == 'outside': bp['editable_ranges']['base.height_m']['maximum'] = 40
            if edit == 'fractional': bp['editable_ranges']['canopy.group_count']['minimum'] = 24.5
            if edit == 'default': bp['default_profile'] = 'missing'
            if edit == 'profile': bp['profiles']['adulto_prueba']['overrides']['base']['curvature'] = .1
            if edit == 'materials': bp['limits']['materials'] = 2
            if edit == 'opacity': bp['appearance']['leaf']['color_rgba'][3] = .5
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate_blueprint(bp)

    def test_strict_file_loading_and_no_seed_in_recipe(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'input.json'
            p.write_text(json.dumps(self.blueprint))
            self.assertEqual(load_blueprint(p), self.blueprint)
            p.write_text(json.dumps(self.instance))
            self.assertEqual(load_instance(p), self.instance)
            for invalid in ('{"schema_version":"1.0","schema_version":"1.0"}',
                            '{"x":NaN}', '{"x":1e999}', ' ' * 65537):
                p.write_text(invalid)
                with self.assertRaises(ValueError): load_blueprint(p)
        bp = dict(self.blueprint, seed=3009)
        with self.assertRaises(ValueError): validate_blueprint(bp)

    def test_manifest_can_repeat_with_frozen_definition(self):
        result = resolve_blueprint(self.blueprint, self.instance)
        self.blueprint['parameters']['base']['height_m'] = 12
        replay = resolve_blueprint(result['blueprint_definition'], result['instance_request'])
        self.assertEqual(replay['resolved_sha256'], result['resolved_sha256'])
        self.assertNotEqual(canonical_hash(self.blueprint), result['blueprint_sha256'])
