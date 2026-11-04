"""OF5: cambios acotados, puentes reales y referencias conservadas."""
import copy
import json
from pathlib import Path
from collections import Counter
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_foliage_macro import build
from treegen.oak_foliage_peripheral import build as build_v4
from treegen.oak_foliage_macro_contract import validate_canopy
from treegen.oak_foliage_cards import prepare_templates
ROOT=Path(__file__).resolve().parents[1]


class OakFoliageMacroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'configs/oak-foliage/macro-B.json').read_text())
        cls.s=generate(load_growth_preset(ROOT/cls.p['preset']),cls.p['seed'])
        cls.t=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        cls.g=prepare_templates(cls.t,Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA'))
        cls.r=build(cls.s,cls.p,cls.t,prepared=cls.g)
        cls.old=build_v4(cls.s,{**cls.p,'version':'oak-foliage-canopy-0.4.0'},cls.t,prepared=cls.g)

    def test_same_budget_and_most_geometry_exact(self):
        r=self.r;self.assertEqual(r['wood'],self.old['wood']);self.assertEqual(r['ledger'],self.old['ledger'])
        self.assertEqual(len(r['groups']),216);self.assertEqual(len(r['foliage']),648)
        changed={c['id'] for c in r['refinements']};self.assertLessEqual(len(changed),18)
        for a,b in zip(self.old['groups'],r['groups']):
            self.assertEqual(a['id'],b['id']);self.assertEqual(a['template_index'],b['template_index'])
            if a['id'] not in changed:self.assertEqual(a,{k:v for k,v in b.items() if k!='macro_id'})
        self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)
        self.assertLessEqual(max(r['axis_quotas'].values()),12)

    def test_bridges_and_retreats(self):
        changes=self.r['refinements'];counts=Counter(c['reason'] for c in changes)
        self.assertGreater(counts['macro_bridge'],0);self.assertLessEqual(counts['macro_bridge'],10)
        self.assertGreater(counts['tip_retreat'],0);self.assertGreater(counts['inner_redundancy'],0)
        for c in changes:
            if c['reason']=='tip_retreat':self.assertLess(c['to_t'],c['from_t'])
        self.assertEqual(len({g['candidate_id'] for g in self.r['groups']}),216)
        index={b['id']:b for b in self.s['branches']}
        self.assertTrue(all(index[g['parent_branch_id']]['order']>=2 for g in self.r['groups']))

    def test_macro_partition_and_links(self):
        r=self.r;self.assertEqual(len(r['macros']),3)
        ids=[i for m in r['macros'] for i in m['mass_ids']]
        self.assertEqual(len(ids),len(set(ids)));self.assertEqual(set(ids),{m['id'] for m in r['masses']})
        for a,b in r['macro_links']:
            self.assertTrue(any(a in m['mass_ids'] and b in m['mass_ids'] for m in r['macros']))

    def test_reproducibility_and_no_input_mutation(self):
        p=copy.deepcopy(self.p);s=copy.deepcopy(self.s)
        self.assertEqual(build(s,p,self.t,prepared=self.g),self.r)
        self.assertEqual(p,self.p);self.assertEqual(s,self.s)
        r=build(s,{**p,'layout_seed':18},self.t,prepared=self.g)
        self.assertEqual(r['wood'],self.r['wood']);self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)
        self.assertLessEqual(len(r['refinements']),18)

    def test_three_structure_controls(self):
        for seed in (3101,3102,3103):
            p={**self.p,'seed':seed};s=generate(load_growth_preset(ROOT/p['preset']),seed)
            r=build(s,p,self.t,prepared=self.g)
            self.assertEqual(len(r['groups']),216);self.assertEqual(r['wood'],s['branches'])
            self.assertGreaterEqual(r['minimum_card_radius_m'],3.6);self.assertLessEqual(len(r['refinements']),18)
            self.assertLessEqual(max(r['axis_quotas'].values()),12)

    def test_contract_remains_strict(self):
        for k,v in [('version','oak-foliage-canopy-0.4.0'),('extra',1),('tree_groups',265),('preset','presets/oak-growth/0.5.0/joven.json')]:
            with self.assertRaises(ValueError):validate_canopy({**self.p,k:v})

if __name__=='__main__':unittest.main()
