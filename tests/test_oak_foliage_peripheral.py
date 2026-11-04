"""OF4: cobertura sin ampliar cupo ni invadir núcleo o cambiar madera."""
import copy
import json
import math
from collections import Counter
from pathlib import Path
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_foliage_canopy import build as build_v3,minimum_radius
from treegen.oak_foliage_peripheral import build
from treegen.oak_foliage_peripheral_contract import validate_canopy
from treegen.oak_foliage_cards import prepare_templates
ROOT=Path(__file__).resolve().parents[1]


class OakFoliagePeripheralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'configs/oak-foliage/peripheral-B.json').read_text())
        cls.s=generate(load_growth_preset(ROOT/cls.p['preset']),cls.p['seed'])
        cls.t=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        cls.g=prepare_templates(cls.t,Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA'))
        cls.r=build(cls.s,cls.p,cls.t,prepared=cls.g)
        cls.old=build_v3(cls.s,{**cls.p,'version':'oak-foliage-canopy-0.3.0'},cls.t,prepared=cls.g)

    def test_budget_and_wood_exact(self):
        r=self.r
        self.assertEqual(r['wood'],self.old['wood']);self.assertEqual(len(r['groups']),216)
        self.assertEqual(len(r['foliage']),648)
        self.assertEqual(sum(len(f)-2 for c in r['foliage'] for f in c['polygons']),1296)
        self.assertEqual(r['ledger']['tree_projected_triangles'],5010)
        self.assertGreaterEqual(minimum_radius(r['foliage']),3.6)
        self.assertEqual(len({g['candidate_id'] for g in r['groups']}),216)
        self.assertLessEqual(max(r['axis_quotas'].values()),12)

    def test_less_concentration_and_real_descending_supports(self):
        r=self.r;old=self.old
        self.assertLess(max(r['ledger']['primary_quotas'].values()),max(old['ledger']['primary_quotas'].values()))
        self.assertEqual(sum(r['fork_quotas'].values()),216)
        self.assertGreater(r['fork_quotas']['p:3/0'],old['fork_quotas']['p:3/0'])
        self.assertGreater(r['fork_quotas']['p:0/infill'],0)
        counts=Counter('/'.join(g['parent_branch_id'].split('/')[:2]) for g in r['groups'])
        self.assertEqual(dict(counts),r['fork_quotas'])
        self.assertEqual(sum(r['ledger']['primary_quotas'].values()),216)

    def test_frames_roots_and_bounded_geometry(self):
        index={b['id']:b for b in self.s['branches']}
        for g in self.r['groups']:
            self.assertGreaterEqual(index[g['parent_branch_id']]['order'],2)
            self.assertGreaterEqual(min(self.g[g['template_index']]['root_alpha']),192)
            self.assertTrue(.45<=g['boundary_scale']<=1)
            self.assertLess(g['orientation_attempt'],10)
            for a in g['axes']:self.assertAlmostEqual(sum(x*x for x in a),1)
            for i,j in [(0,1),(0,2),(1,2)]:self.assertAlmostEqual(sum(x*y for x,y in zip(g['axes'][i],g['axes'][j])),0)
            self.assertTrue(all(math.isfinite(v) for v in g['size_m']))

    def test_determinism_separate_seed_and_input_immutability(self):
        p=copy.deepcopy(self.p);s=copy.deepcopy(self.s)
        self.assertEqual(build(s,p,self.t,prepared=self.g),self.r)
        self.assertEqual(p,self.p);self.assertEqual(s,self.s)
        p['layout_seed']=18;r=build(s,p,self.t,prepared=self.g)
        self.assertEqual(r['wood'],self.r['wood']);self.assertEqual(r['ledger'],self.r['ledger'])
        self.assertNotEqual(r['groups'],self.r['groups']);self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)

    def test_other_structure_seeds_same_rules(self):
        # Controles geométricos; no equivalen a revisión artística ni exportación.
        for seed in (3101,3102,3103):
            p={**self.p,'seed':seed};s=generate(load_growth_preset(ROOT/p['preset']),seed)
            r=build(s,p,self.t,prepared=self.g)
            self.assertEqual(r['wood'],s['branches']);self.assertEqual(len(r['groups']),216)
            self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)
            self.assertLessEqual(r['ledger']['tree_projected_triangles'],6999)

    def test_strict_contract_historical_versions_preserved(self):
        for k,v in [('version','oak-foliage-canopy-0.3.0'),('tree_groups',265),('preset','presets/oak-growth/0.5.0/joven.json'),('extra',1),('span_over_height',float('nan'))]:
            with self.assertRaises(ValueError):validate_canopy({**self.p,k:v})

if __name__=='__main__':unittest.main()
