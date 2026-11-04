"""Receta3.0.0: contrato fijo, selección explícita y reproducción OF11."""
import copy
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator
from treegen.blueprints import load_blueprint,load_instance,resolve_blueprint,validate_blueprint,registered_blueprints
ROOT=Path(__file__).resolve().parents[1]


class OakCentralBlueprintTests(unittest.TestCase):
    def setUp(self):
        self.b=load_blueprint(ROOT/'blueprints/roble_copa_ancha/3.0.0.json')
        self.i=load_instance(ROOT/'presets/blueprints/roble-central/maduro-3100.json')

    def test_contract_schemas_and_catalog(self):
        for n in ('tree-blueprint-central-oak.schema.json','tree-instance-central-oak.schema.json'):
            Draft202012Validator.check_schema(json.loads((ROOT/'schemas'/n).read_text()))
        self.assertIn(('roble_copa_ancha','3.0.0'),[(b['id'],b['version']) for b in registered_blueprints()])
        self.assertEqual(load_blueprint(ROOT/'blueprints/roble_copa_ancha/2.2.0.json')['schema_version'],'1.4')

    def test_exact_approved_inputs_and_reproducibility(self):
        before=copy.deepcopy((self.b,self.i))
        r=resolve_blueprint(self.b,self.i)
        self.assertEqual(r,resolve_blueprint(self.b,self.i))
        self.assertEqual(r['canopy_spec'],json.loads((ROOT/'configs/oak-foliage/central-B.json').read_text()))
        self.assertEqual(r['base_seeds'],{'structure':3100,'foliage':17})
        self.assertEqual((self.b,self.i),before)

    def test_unknown_keys_components_and_nonfinite_are_rejected(self):
        for update in ({'schema_version':'1.6'},{'limits':{**self.b['limits'],'triangles':7000}},
                       {'parameters':{**self.b['parameters'],'canopy':{**self.b['parameters']['canopy'],'tree_groups':215}}},
                       {'components':{**self.b['components'],'base':'oak_geometry_nodes@0.4.0'}},
                       {'extra':1}):
            with self.assertRaises(ValueError):validate_blueprint({**self.b,**update})
        for seeds in ({**self.i['seeds'],'base':True},{**self.i['seeds'],'paint':float('nan')}):
            with self.assertRaises(ValueError):resolve_blueprint(self.b,{**self.i,'seeds':seeds})

    def test_profile_version_and_overrides_are_not_silently_changed(self):
        for update in ({'profile':'joven'},{'blueprint_version':'2.2.0'},
                       {'overrides':{'base':{'height_m':10}}}):
            with self.assertRaises(ValueError):resolve_blueprint(self.b,{**self.i,**update})

    def test_independent_seed_streams(self):
        first=resolve_blueprint(self.b,self.i)
        second=resolve_blueprint(self.b,{**self.i,'seeds':{**self.i['seeds'],'canopy':18}})
        self.assertEqual(first['base_spec'],second['base_spec'])
        self.assertEqual(first['paint_seed'],second['paint_seed'])
        self.assertNotEqual(first['canopy_spec']['layout_seed'],second['canopy_spec']['layout_seed'])

if __name__=='__main__':unittest.main()
