"""OF10: presupuesto real, expansión anclada y conservación de OF9."""
import copy
import json
import math
from pathlib import Path
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_foliage_gaps import build
from treegen.oak_foliage_gaps_contract import validate_canopy
from treegen.oak_foliage_regions import build as build_v9
from treegen.oak_foliage_top import prepare_opaque_samples
from treegen.oak_foliage_cards import prepare_templates,rooted_panels
from treegen.oak_crossed import PLANES
ROOT=Path(__file__).resolve().parents[1]


class OakFoliageGapsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'configs/oak-foliage/gaps-B.json').read_text())
        cls.s=generate(load_growth_preset(ROOT/cls.p['preset']),cls.p['seed'])
        cls.t=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        im=Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA')
        cls.g=prepare_opaque_samples(prepare_templates(cls.t,im),im)
        cls.r=build(cls.s,cls.p,cls.t,prepared=cls.g)
        cls.old=build_v9(cls.s,{**cls.p,'version':'oak-foliage-canopy-0.9.0'},cls.t,prepared=cls.g)

    def test_same_groups_and_exact_base_geometry(self):
        self.assertEqual(self.r['groups'],self.old['groups'])
        self.assertEqual(self.r['wood'],self.old['wood'])
        self.assertEqual(self.r['foliage'][:len(self.old['foliage'])],self.old['foliage'])
        self.assertEqual(len(self.r['groups']),216)

    def test_authorized_budget_and_bounded_work(self):
        r=self.r;n=len(r['gap_fans']);self.assertGreater(n,0);self.assertLessEqual(n,350)
        self.assertEqual(r['ledger']['tree_projected_triangles'],5136+2*n)
        self.assertLessEqual(r['ledger']['tree_projected_triangles'],min(5836,6999))
        self.assertLessEqual(r['gap_attempts'],216*2*3*3*3)
        self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)
        self.assertLessEqual(len(r['gaps']),5)

    def test_new_planes_have_real_root_and_upward_normal(self):
        old={g['id']:g for g in self.old['groups']}
        for q in self.r['gap_fans']:
            g=q['group'];ref=old[q['group_id']]
            for k in ('anchor_m','parent_branch_id','parent_t','template_index','root_normalized'):
                self.assertEqual(g[k],ref[k])
            a,b=PLANES[q['plane']];depth=({0,1,2}-{a,b}).pop()
            self.assertGreaterEqual(abs(g['axes'][depth][2]),.5)
            # La transformación afín de la raíz coincide con el contacto real.
            root=[g['center_m'][k]+sum(g['root_normalized'][a]*g['size_m'][a]*g['axes'][a][k] for a in range(3)) for k in range(3)]
            self.assertLess(math.dist(root,g['anchor_m']),1e-10)
            self.assertLessEqual(q['scale'],1.55)

    def test_determinism_and_immutable_inputs(self):
        p=copy.deepcopy(self.p);s=copy.deepcopy(self.s);g=copy.deepcopy(self.g)
        self.assertEqual(build(s,p,self.t,prepared=g),self.r)
        self.assertEqual(p,self.p);self.assertEqual(s,self.s);self.assertEqual(g,self.g)

    def test_structure_and_distribution_controls(self):
        for seed,layout in ((3101,17),(3102,17),(3103,17),(3100,18)):
            p={**self.p,'seed':seed,'layout_seed':layout};s=generate(load_growth_preset(ROOT/p['preset']),seed)
            r=build(s,p,self.t,prepared=self.g)
            self.assertEqual(len(r['groups']),216);self.assertEqual(r['wood'],s['branches'])
            self.assertLessEqual(r['ledger']['tree_projected_triangles']-r['ledger']['of9_tree_triangles'],700)
            self.assertLessEqual(r['ledger']['tree_projected_triangles'],6999)
            self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)

    def test_strict_contract(self):
        for k,v in [('version','oak-foliage-canopy-0.9.0'),('extra',1),('tree_groups',265),('preset','presets/oak-growth/0.5.0/joven.json')]:
            with self.assertRaises(ValueError):validate_canopy({**self.p,k:v})

if __name__=='__main__':unittest.main()
