"""OF6: volúmenes geométricos, presupuesto/contactos y núcleo protegidos."""
import copy
import json
from pathlib import Path
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_foliage_macro import build as build_v5
from treegen.oak_foliage_volume import build
from treegen.oak_foliage_volume_contract import validate_canopy
from treegen.oak_foliage_cards import prepare_templates
from treegen.oak_foliage_canopy import minimum_radius
ROOT=Path(__file__).resolve().parents[1]


class OakFoliageVolumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'configs/oak-foliage/volume-B.json').read_text())
        cls.s=generate(load_growth_preset(ROOT/cls.p['preset']),cls.p['seed'])
        cls.t=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        cls.g=prepare_templates(cls.t,Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA'))
        cls.r=build(cls.s,cls.p,cls.t,prepared=cls.g)
        cls.old=build_v5(cls.s,{**cls.p,'version':'oak-foliage-canopy-0.5.0'},cls.t,prepared=cls.g)

    def test_fixed_budget_wood_paint_and_contacts(self):
        r=self.r;self.assertEqual(r['wood'],self.old['wood']);self.assertEqual(r['ledger'],self.old['ledger'])
        self.assertEqual(len(r['groups']),216);self.assertEqual(len(r['foliage']),648)
        self.assertEqual(sum(len(f)-2 for pc in r['foliage'] for f in pc['polygons']),1296)
        self.assertEqual(r['ledger']['tree_projected_triangles'],5010)
        for a,b in zip(self.old['groups'],r['groups']):
            for k in ('id','anchor_m','parent_branch_id','parent_t','template_index','root_normalized'):
                self.assertEqual(a[k],b[k])
        self.assertGreaterEqual(minimum_radius(r['foliage']),3.6)

    def test_geometric_volume_effect_and_bounded_work(self):
        r=self.r;self.assertEqual(len(r['envelopes']),3)
        self.assertEqual(sum(e['group_count'] for e in r['envelopes']),216)
        self.assertGreater(len(r['volume_changes']),100)
        self.assertGreater(sum(g['volume_role']=='interface_extension' for g in r['groups']),40)
        self.assertLessEqual(r['volume_attempts'],216*3)
        old={g['id']:g for g in self.old['groups']}
        for g in r['groups']:
            ratios=[x/y for x,y in zip(g['size_m'],old[g['id']]['size_m'])]
            self.assertLess(max(ratios)-min(ratios),1e-10)
            if g['volume_role']=='tip_preserved':self.assertEqual(g['size_m'],old[g['id']]['size_m'])
            if g['volume_role']=='core_protected':
                self.assertEqual(g['size_m'],old[g['id']]['size_m'])
            for a in g['axes']:self.assertAlmostEqual(sum(x*x for x in a),1)
            for i,j in ((0,1),(0,2),(1,2)):self.assertAlmostEqual(sum(x*y for x,y in zip(g['axes'][i],g['axes'][j])),0)

    def test_determinism_seeds_and_immutability(self):
        p=copy.deepcopy(self.p);s=copy.deepcopy(self.s)
        self.assertEqual(build(s,p,self.t,prepared=self.g),self.r)
        self.assertEqual(p,self.p);self.assertEqual(s,self.s)
        r=build(s,{**p,'layout_seed':18},self.t,prepared=self.g)
        self.assertEqual(r['wood'],self.r['wood']);self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)

    def test_three_structure_controls(self):
        for seed in (3101,3102,3103):
            p={**self.p,'seed':seed};s=generate(load_growth_preset(ROOT/p['preset']),seed)
            r=build(s,p,self.t,prepared=self.g)
            self.assertEqual(len(r['groups']),216);self.assertEqual(r['wood'],s['branches'])
            self.assertGreaterEqual(r['minimum_card_radius_m'],3.6);self.assertLessEqual(r['volume_attempts'],648)

    def test_strict_contract(self):
        for k,v in [('version','oak-foliage-canopy-0.5.0'),('extra',1),('tree_groups',265),('preset','presets/oak-growth/0.5.0/joven.json')]:
            with self.assertRaises(ValueError):validate_canopy({**self.p,k:v})

if __name__=='__main__':unittest.main()
