"""OF2: comparar masas y huecos sin cambiar madera, pintura o presupuesto."""
import copy
import json
import math
from pathlib import Path
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_foliage_cards import prepare_templates
from treegen.oak_foliage_chains import build
from treegen.oak_foliage_chain_contract import validate_sample
from treegen.branch_structure import length,sub
ROOT=Path(__file__).resolve().parents[1]


class OakFoliageChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=generate(load_growth_preset(ROOT/'presets/oak-growth/0.5.0/maduro.json'),3100)
        cls.templates=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        cls.prepared=prepare_templates(cls.templates,Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA'))
        cls.specs={v:json.loads((ROOT/f'configs/oak-foliage/chains-{v}.json').read_text()) for v in 'ABC'}
        cls.results={v:build(cls.s,cls.specs[v],cls.templates,prepared=cls.prepared) for v in 'ABC'}

    def test_equal_budget_wood_and_group_sequence(self):
        a=self.results['A']
        for r in self.results.values():
            self.assertEqual(r['wood'],a['wood']);self.assertEqual(len(r['groups']),64)
            self.assertEqual(len(r['foliage']),192);self.assertEqual(sum(len(f)-2 for p in r['foliage'] for f in p['polygons']),384)
            self.assertEqual([(g['size_m'],g['template_index']) for g in r['groups']],[(g['size_m'],g['template_index']) for g in a['groups']])
            self.assertEqual(r['ledger'],a['ledger']);self.assertLessEqual(r['ledger']['tree_projected_triangles'],6999)

    def test_coherent_mass_links_and_distinct_variants(self):
        signatures=set()
        for v,count in [('A',3),('B',4),('C',5)]:
            r=self.results[v];self.assertEqual(len(r['masses']),count);self.assertEqual(len(r['mass_links']),count-1)
            self.assertEqual(sum(m['group_count'] for m in r['masses']),64)
            self.assertTrue(all(g['mass_id'] in {m['id'] for m in r['masses']} for g in r['groups']))
            self.assertEqual(len({g['candidate_id'] for g in r['groups']}),64)
            signatures.add(str([(g['parent_branch_id'],g['parent_t']) for g in r['groups']]))
        self.assertEqual(len(signatures),3)

    def test_lower_cluster_is_rejected_by_geometry_and_center_kept_clear(self):
        for r in self.results.values():
            self.assertGreater(r['diagnostics']['rejected_lower_segments'],0)
            self.assertLessEqual(r['diagnostics']['candidate_count'],32*len(r['wood']))
            for g in r['groups']:
                self.assertGreaterEqual(g['anchor_m'][2],r['diagnostics']['lower_height_limit_m']-.10)
            self.assertGreater(min(math.hypot(*v[:2])/12 for p in r['foliage'] for v in p['vertices']),.30)
            self.assertLessEqual(max(r['axis_quotas'].values()),12)

    def test_frames_are_fixed_orthonormal_and_mass_depth_is_reduced(self):
        for r in self.results.values():
            for g in r['groups']:
                a,b,c=g['axes']
                self.assertAlmostEqual(sum(x*x for x in a),1);self.assertAlmostEqual(sum(x*x for x in b),1);self.assertAlmostEqual(sum(x*x for x in c),1)
                self.assertAlmostEqual(sum(x*y for x,y in zip(a,b)),0)
                self.assertLess(g['size_m'][2],max(g['size_m'][:2]))
                self.assertGreaterEqual(min(self.prepared[g['template_index']]['root_alpha']),192)

    def test_reproducibility_separate_seed_and_input_immutability(self):
        p=copy.deepcopy(self.specs['B']);s=copy.deepcopy(self.s)
        self.assertEqual(build(s,p,self.templates,prepared=self.prepared),self.results['B'])
        self.assertEqual(s,self.s);self.assertEqual(p,self.specs['B'])
        p['layout_seed']=18;r=build(s,p,self.templates,prepared=self.prepared)
        self.assertEqual(r['wood'],self.results['B']['wood']);self.assertEqual(r['ledger'],self.results['B']['ledger'])
        self.assertNotEqual(r['groups'],self.results['B']['groups'])

    def test_strict_contract_preserves_old_version(self):
        for key,value in [('mass_variant','D'),('version','oak-foliage-sample-0.1.0'),('tree_groups',True),('extra',1)]:
            p=copy.deepcopy(self.specs['B']);p[key]=value
            with self.assertRaises(ValueError):validate_sample(p)

if __name__=='__main__':unittest.main()
