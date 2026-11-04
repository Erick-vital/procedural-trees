"""OF8: complemento acotado sin perder OF7, presupuesto global y contacto."""
import copy
import json
from pathlib import Path
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_foliage_balance import build
from treegen.oak_foliage_balance_contract import validate_canopy
from treegen.oak_foliage_top import build as build_v7,prepare_opaque_samples
from treegen.oak_foliage_cards import prepare_templates
from treegen.oak_foliage_canopy import minimum_radius
from treegen.oak_crossed import PLANES
ROOT=Path(__file__).resolve().parents[1]


class OakFoliageBalanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'configs/oak-foliage/balance-B.json').read_text())
        cls.s=generate(load_growth_preset(ROOT/cls.p['preset']),cls.p['seed'])
        cls.t=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        image=Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA')
        cls.g=prepare_opaque_samples(prepare_templates(cls.t,image),image)
        cls.r=build(cls.s,cls.p,cls.t,prepared=cls.g)
        cls.old=build_v7(cls.s,{**cls.p,'version':'oak-foliage-canopy-0.7.0'},cls.t,prepared=cls.g)

    def test_of7_geometry_is_exact_subset(self):
        r=self.r;self.assertEqual(r['groups'],self.old['groups']);self.assertEqual(r['wood'],self.old['wood'])
        self.assertEqual(r['foliage'][:len(self.old['foliage'])],self.old['foliage'])
        self.assertEqual(len(r['groups']),216)
        self.assertGreaterEqual(minimum_radius(r['foliage']),3.6)

    def test_global_and_reserve_budget_before_export(self):
        r=self.r;n=len(r['lateral_complements']);self.assertGreater(n,0);self.assertLessEqual(n,64)
        self.assertEqual(len(r['foliage']),648+n)
        tris=sum(len(f)-2 for c in r['foliage'] for f in c['polygons'])
        self.assertEqual(tris,1296+2*n);self.assertLessEqual(tris,1584)
        self.assertEqual(r['ledger']['tree_projected_triangles'],5010+2*n)
        self.assertLessEqual(5415+tris,6999)
        self.assertLessEqual(r['lateral_attempts'],216*3)

    def test_complement_normals_roots_and_significant_gain(self):
        old={g['id']:g for g in self.old['groups']};ids=[]
        for q in self.r['lateral_complements']:
            g=q['group'];ids.append(q['group_id']);source=old[q['group_id']]
            for k in ('anchor_m','parent_branch_id','parent_t','size_m','root_normalized','template_index'):self.assertEqual(g[k],source[k])
            depth=({0,1,2}-set(PLANES[q['plane']])).pop()
            self.assertGreaterEqual(abs(g['axes'][depth][2]),.24-1e-10)
            self.assertGreaterEqual(q['loss'],.18);self.assertGreaterEqual(q['gain'],.10)
        self.assertEqual(len(ids),len(set(ids)))

    def test_determinism_input_immutability_and_layout_seed(self):
        p=copy.deepcopy(self.p);s=copy.deepcopy(self.s);g=copy.deepcopy(self.g)
        self.assertEqual(build(s,p,self.t,prepared=g),self.r)
        self.assertEqual(p,self.p);self.assertEqual(s,self.s);self.assertEqual(g,self.g)
        r=build(s,{**p,'layout_seed':18},self.t,prepared=g)
        self.assertEqual(r['wood'],self.r['wood']);self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)
        self.assertLessEqual(r['ledger']['tree_projected_triangles'],6999)

    def test_three_structure_controls(self):
        for seed in (3101,3102,3103):
            p={**self.p,'seed':seed};s=generate(load_growth_preset(ROOT/p['preset']),seed)
            r=build(s,p,self.t,prepared=self.g)
            self.assertEqual(len(r['groups']),216);self.assertEqual(r['wood'],s['branches'])
            self.assertGreaterEqual(r['minimum_card_radius_m'],3.6);self.assertLessEqual(r['ledger']['tree_projected_triangles'],6999)
            self.assertLessEqual(r['ledger']['foliage_triangles'],1584)

    def test_contract_remains_strict(self):
        for k,v in [('version','oak-foliage-canopy-0.7.0'),('extra',1),('tree_groups',265),('preset','presets/oak-growth/0.5.0/joven.json')]:
            with self.assertRaises(ValueError):validate_canopy({**self.p,k:v})

if __name__=='__main__':unittest.main()
