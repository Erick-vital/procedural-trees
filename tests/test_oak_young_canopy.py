"""J2: contratos, capacidad real, presupuesto y conservación de muestra aprobada."""
import copy
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator
from treegen.blueprints import load_blueprint,load_instance,resolve_blueprint,validate_blueprint,canonical_hash
from treegen.oak_young_production import prepare
from treegen.oak_young_canopy import validate_canopy
from treegen.oak_young_sample import build as sample_build
from treegen.oak_foliage_cards import prepare_templates
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]


class YoungCanopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blueprint=load_blueprint(ROOT/'blueprints/roble_copa_ancha/3.1.0.json')
        cls.instances={s:load_instance(ROOT/f'presets/blueprints/roble-joven/joven-{s}.json') for s in range(3100,3104)}
        cls.resolved={s:resolve_blueprint(cls.blueprint,i) for s,i in cls.instances.items()}
        cls.data={s:prepare(r) for s,r in cls.resolved.items()}

    def test_schemas_and_fixed_contract(self):
        for name in ('tree-blueprint-young-oak.schema.json','tree-instance-young-oak.schema.json'):
            Draft202012Validator.check_schema(json.loads((ROOT/'schemas'/name).read_text()))
        for update in ({'schema_version':'1.7'}, {'limits':{**self.blueprint['limits'],'triangles':7000}},
                       {'components':{**self.blueprint['components'],'base':'oak-growth-central@0.1.0'}},
                       {'parameters':{**self.blueprint['parameters'],'base':{'height_m':12,'preset':'presets/oak-growth/0.5.0/maduro.json'}}}):
            with self.assertRaises(ValueError):validate_blueprint({**self.blueprint,**update})
        for update in ({'profile':'maduro'},{'seeds':{'base':True,'canopy':17,'paint':2718}}, {'overrides':{'canopy':{'tree_groups':100}}}):
            with self.assertRaises(ValueError):resolve_blueprint(self.blueprint,{**self.instances[3100],**update})
        for key,val in [('tree_groups',True),('branch_id','p:0'),('mass_variant','A'),('span_over_height',float('nan'))]:
            with self.assertRaises(ValueError):validate_canopy({**self.resolved[3100]['canopy_spec'],key:val})

    def test_full_budget_ids_and_caps(self):
        for s,d in self.data.items():
            self.assertEqual(len(d['groups']),144);self.assertEqual(len(d['foliage']),432)
            self.assertEqual(len({g['id'] for g in d['groups']}),144)
            self.assertEqual(sum(d['ledger']['primary_quotas'].values()),144)
            self.assertEqual(sum(len(f)-2 for m in d['foliage'] for f in m['polygons']),864)
            self.assertLessEqual(d['ledger']['tree_projected_triangles'],6279)
            self.assertTrue(all(n<=d['ledger']['capacities'][bid]['groups_max'] for bid,n in d['ledger']['primary_quotas'].items()))
            self.assertTrue(all(v[2]>=0 for m in d['foliage'] for v in m['vertices']))

    def test_capacity_rejection_is_corrected_by_common_reallocation(self):
        d=self.data[3102]['ledger']
        self.assertEqual(d['initial_primary_quotas']['p:4'],2)
        self.assertEqual(d['capacities']['p:4']['groups_max'],0)
        self.assertEqual(d['primary_quotas']['p:4'],0)
        self.assertEqual(d['redistributed_groups'],2)
        self.assertEqual(self.data[3100]['ledger']['redistributed_groups'],0)

    def test_approved_pilot_branch_is_exact(self):
        d=self.data[3100]
        spec=json.loads((ROOT/'configs/oak-foliage/young-sample-v1.json').read_text())
        templates=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        pre=prepare_templates(templates,Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA'))
        branch=sample_build(d['structure'],spec,templates,prepared=pre)
        selected=[g for g in d['groups'] if g['parent_branch_id'].split('/')[0]=='p:0']
        self.assertEqual(selected,branch['groups'])
        accepted=json.loads((ROOT/'docs/evidence/roble-joven/j1/user-acceptance.json').read_text())
        self.assertEqual(canonical_hash(selected),accepted['approved_branch_groups_sha256'])

    def test_inputs_not_mutated_and_preparation_repeats(self):
        before=copy.deepcopy(self.resolved[3100]);again=prepare(self.resolved[3100])
        self.assertEqual(again,self.data[3100]);self.assertEqual(before,self.resolved[3100])
        with self.assertRaises(ValueError):prepare({**before,'paint_seed':4})
        instance=copy.deepcopy(self.instances[3100]);instance['seeds']['canopy']=18
        changed=prepare(resolve_blueprint(self.blueprint,instance))
        self.assertEqual(changed['wood'],self.data[3100]['wood'])
        self.assertNotEqual(changed['groups'],self.data[3100]['groups'])

if __name__=='__main__':unittest.main()
