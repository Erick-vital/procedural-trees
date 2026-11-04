"""J1: etapa joven fija, reserva completa y reutilización sin mutar históricos."""
import copy
import json
from pathlib import Path
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_young_sample import validate_sample, build
from treegen.oak_foliage_chains import build as historical
from treegen.oak_foliage_cards import prepare_templates

ROOT = Path(__file__).resolve().parents[1]


class YoungSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((ROOT/'configs/oak-foliage/young-sample-v1.json').read_text())
        cls.preset = load_growth_preset(ROOT/cls.spec['preset'])
        cls.structure = generate(cls.preset,3100)
        cls.templates = json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        cls.prepared = prepare_templates(cls.templates,Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA'))
        cls.result = build(cls.structure,cls.spec,cls.templates,prepared=cls.prepared)

    def test_fixed_profile_rejects_bad_inputs(self):
        for key, value in [('tree_groups',True),('tree_groups',216),('preset','presets/oak-growth/0.5.0/maduro.json'),
                           ('span_over_height',float('nan')),('span_over_height',.12),('mass_variant','A'),
                           ('branch_id','p:1'),('seed',-1),('extra',1)]:
            with self.subTest(key=key),self.assertRaises(ValueError):validate_sample({**self.spec,key:value})

    def test_mature_or_wrong_seed_structure_rejected(self):
        for structure in ({**self.structure,'seed':3101},
                          {**self.structure,'preset':{**self.preset,'stage':'maduro'}},
                          {**self.structure,'preset':{**self.preset,'height_m':12}}):
            with self.assertRaises(ValueError):build(structure,self.spec,self.templates,prepared=self.prepared)

    def test_budget_scope_and_wood_unchanged(self):
        r=self.result
        self.assertEqual(r['ledger']['foliage_triangles'],864)
        self.assertEqual(r['ledger']['family_complete_upper_bound'],6279)
        self.assertLessEqual(r['ledger']['tree_projected_triangles'],6999)
        self.assertEqual(len(r['groups']),r['ledger']['primary_quotas']['p:0'])
        self.assertEqual(len(r['foliage']),3*len(r['groups']))
        self.assertEqual(sum(len(f)-2 for mesh in r['foliage'] for f in mesh['polygons']),6*len(r['groups']))
        self.assertEqual(r['wood'],[b for b in self.structure['branches'] if b['id']=='p:0' or b['id'].startswith('p:0/')])
        self.assertEqual(r['diagnostics']['materialized_scope'],'young branch only; full-tree foliage not integrated')

    def test_same_geometry_as_reused_distribution_and_deterministic(self):
        before=copy.deepcopy((self.structure,self.spec,self.templates))
        again=build(self.structure,self.spec,self.templates,prepared=self.prepared)
        self.assertEqual(again,self.result)
        old=historical(self.structure,{**self.spec,'version':'oak-foliage-sample-0.2.0'},self.templates,prepared=self.prepared)
        for key in ('wood','groups','foliage','axis_quotas','masses'):self.assertEqual(again[key],old[key])
        self.assertEqual(before,(self.structure,self.spec,self.templates))

    def test_controls_budget_and_surface_frames(self):
        for seed in range(3101,3104):
            r=build(generate(self.preset,seed),{**self.spec,'seed':seed},self.templates,prepared=self.prepared)
            self.assertLessEqual(r['ledger']['tree_projected_triangles'],6999)
            self.assertLessEqual(max(r['axis_quotas'].values()),12)
            self.assertTrue(all(min(v[2] for c in r['foliage'] for v in c['vertices'])>=0 for _ in [0]))
            for g in r['groups']:
                for axis in g['axes']:self.assertAlmostEqual(sum(x*x for x in axis),1)
                self.assertGreaterEqual(min(self.prepared[g['template_index']]['root_alpha']),192)


if __name__=='__main__': unittest.main()
