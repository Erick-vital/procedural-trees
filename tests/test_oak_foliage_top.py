"""OF7: marcos inclinados, muestras alfa reales y presupuesto intacto."""
import copy
import json
import math
from pathlib import Path
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_foliage_volume import build as build_v6
from treegen.oak_foliage_top import build,prepare_opaque_samples,balanced_basis
from treegen.oak_foliage_top_contract import validate_canopy
from treegen.oak_foliage_cards import prepare_templates
from treegen.oak_foliage_canopy import minimum_radius
from treegen.oak_crossed import GRID,USABLE,PLANES
ROOT=Path(__file__).resolve().parents[1]


class OakFoliageTopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'configs/oak-foliage/top-B.json').read_text())
        cls.s=generate(load_growth_preset(ROOT/cls.p['preset']),cls.p['seed'])
        cls.t=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        cls.image=Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA')
        cls.g=prepare_opaque_samples(prepare_templates(cls.t,cls.image),cls.image)
        cls.r=build(cls.s,cls.p,cls.t,prepared=cls.g)
        cls.old=build_v6(cls.s,{**cls.p,'version':'oak-foliage-canopy-0.6.0'},cls.t,prepared=cls.g)

    def test_same_geometry_budget_anchor_sizes_and_paint(self):
        self.assertEqual(self.r['wood'],self.old['wood']);self.assertEqual(len(self.r['groups']),216)
        self.assertEqual(len(self.r['foliage']),648);self.assertEqual(self.r['ledger'],self.old['ledger'])
        for a,b in zip(self.old['groups'],self.r['groups']):
            for k in ('id','anchor_m','parent_branch_id','parent_t','size_m','template_index','root_normalized'):
                self.assertEqual(a[k],b[k])
            if a['role'] in ('bridge','macro_bridge','tip_retreat','inner_redundancy'):self.assertEqual(a['axes'],b['axes'])
        self.assertGreaterEqual(minimum_radius(self.r['foliage']),3.6)
        self.assertEqual(sum(len(f)-2 for c in self.r['foliage'] for f in c['polygons']),1296)

    def test_opaque_samples_project_back_to_correct_atlas_tiles(self):
        for ti,g in enumerate(self.g):
            self.assertTrue(g['opaque_samples']);self.assertLessEqual(len(g['opaque_samples']),3*256)
            for q in g['opaque_samples']:
                # La profundidad identifica el plano; comprobar todas las
                # coincidencias posibles contra las coordenadas UV reales.
                matched=False
                for plane,(a,b) in enumerate(PLANES):
                    depth=({0,1,2}-{a,b}).pop()
                    if abs(q[depth]-g['root_normalized'][depth])>1e-10:continue
                    col,row=(ti*3+plane)%GRID,(ti*3+plane)//GRID
                    x=round((col+.5+q[a]*USABLE)/GRID*self.image.width)
                    y=round((1-(row+.5+q[b]*USABLE)/GRID)*self.image.height)
                    if self.image.getpixel((x,y))[3]>=192:matched=True
                self.assertTrue(matched)

    def test_edge_on_reduction_and_bounded_orthonormal_frames(self):
        r=self.r
        self.assertLess(r['top_edge_fraction_after'],r['top_edge_fraction_before'])
        self.assertLessEqual(r['top_attempts'],216*8)
        self.assertGreater(len(r['top_changes']),50)
        for g in r['groups']:
            for a in g['axes']:self.assertAlmostEqual(sum(x*x for x in a),1)
            for i,j in ((0,1),(0,2),(1,2)):self.assertAlmostEqual(sum(x*y for x,y in zip(g['axes'][i],g['axes'][j])),0)
            if g['top_role']=='inclined_crosses':self.assertGreater(min(abs(v[2]) for v in g['axes']),.45)

    def test_deterministic_seed_stream_and_no_input_mutation(self):
        p=copy.deepcopy(self.p);s=copy.deepcopy(self.s);g=copy.deepcopy(self.g)
        self.assertEqual(build(s,p,self.t,prepared=g),self.r)
        self.assertEqual(p,self.p);self.assertEqual(s,self.s);self.assertEqual(g,self.g)
        r=build(s,{**p,'layout_seed':18},self.t,prepared=g)
        self.assertEqual(r['wood'],self.r['wood']);self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)

    def test_three_structure_controls(self):
        for seed in (3101,3102,3103):
            p={**self.p,'seed':seed};s=generate(load_growth_preset(ROOT/p['preset']),seed)
            r=build(s,p,self.t,prepared=self.g)
            self.assertEqual(len(r['groups']),216);self.assertEqual(r['wood'],s['branches'])
            self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)
            self.assertLess(r['top_edge_fraction_after'],r['top_edge_fraction_before'])

    def test_contract_and_missing_paint_samples_rejected(self):
        for k,v in [('version','oak-foliage-canopy-0.6.0'),('extra',1),('tree_groups',265),('preset','presets/oak-growth/0.5.0/joven.json')]:
            with self.assertRaises(ValueError):validate_canopy({**self.p,k:v})
        with self.assertRaises(ValueError):build(self.s,self.p,self.t)

if __name__=='__main__':unittest.main()
