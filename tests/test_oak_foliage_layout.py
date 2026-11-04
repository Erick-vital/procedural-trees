"""OF1: cupo global, pintura existente y anclaje sin conectores nuevos."""
import copy
import json
import math
from pathlib import Path
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_foliage_contract import validate_sample
from treegen.oak_foliage_layout import build,plan,allocate
from treegen.oak_foliage_cards import template_geometry,prepare_templates
from treegen.oak_crossed import PLANES
from treegen.surface_evaluation import point_triangle_distance
from treegen.oak_growth_mesh import tube
ROOT=Path(__file__).resolve().parents[1]


class OakFoliageLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'configs/oak-foliage/sample-v1.json').read_text())
        cls.s=generate(load_growth_preset(ROOT/cls.p['preset']),cls.p['seed'])
        cls.templates=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        cls.prepared=prepare_templates(cls.templates,Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA'))
        cls.result=build(cls.s,cls.p,cls.templates,prepared=cls.prepared)

    def test_ledger_charges_only_sample_share_and_full_reserve(self):
        r=self.result;l=r['ledger'];count=len(r['groups'])
        self.assertEqual(sum(l['primary_quotas'].values()),self.p['tree_groups'])
        self.assertEqual(count,l['primary_quotas']['p:0']);self.assertLess(count,264)
        tris=sum(len(face)-2 for m in r['foliage'] for face in m['polygons'])
        self.assertEqual(tris,6*count);self.assertLessEqual(l['foliage_triangles'],1584)
        self.assertLessEqual(l['tree_projected_triangles'],6999)
        self.assertLessEqual(5415+l['foliage_triangles'],6999)

    def test_wood_is_exact_subset_and_contains_real_hierarchy(self):
        self.assertEqual(self.result['wood'],[b for b in self.s['branches'] if b['id']=='p:0' or b['id'].startswith('p:0/')])
        self.assertEqual({b['order'] for b in self.result['wood']},{1,2,3,4})
        self.assertTrue(all(g['parent_branch_id'] in {b['id'] for b in self.result['wood'] if b['order']>=2} for g in self.result['groups']))

    def test_contacts_on_actual_faces_and_opaque_all_projections(self):
        index={b['id']:b for b in self.s['branches']}
        for g in self.result['groups']:
            mesh=tube(index[g['parent_branch_id']]);point=g['anchor_m']
            distance=min(point_triangle_distance(point,*(mesh['vertices'][k] for k in (f[0],f[j],f[j+1]))) for f in mesh['polygons'] for j in range(1,len(f)-1))
            self.assertLess(distance,1e-8)
            self.assertGreaterEqual(min(self.prepared[g['template_index']]['root_alpha']),192)
        self.assertTrue(all(t['affine_error']<1e-6 for t in self.prepared))
        self.assertTrue(all(t['paint_root_shift_normalized']<=math.sqrt(3)*.04+1e-9 for t in self.prepared))

    def test_longitudinal_spread_core_and_fixed_crossed_planes(self):
        r=self.result;h=self.s['preset']['height_m']
        self.assertLess(min(g['parent_t'] for g in r['groups']),.5)
        self.assertGreater(max(g['parent_t'] for g in r['groups']),.8)
        self.assertEqual(len(r['foliage']),3*len(r['groups']))
        self.assertGreaterEqual(min(math.hypot(v[0],v[1])/h for m in r['foliage'] for v in m['vertices']),.30)
        for m in r['foliage']:
            self.assertEqual(len(m['vertices']),4);self.assertEqual(len(m['polygons']),2)
            self.assertTrue(all(0<=u<=1 and 0<=v<=1 for u,v in m['uv']))

    def test_determinism_and_separate_seeds_without_mutation(self):
        s=copy.deepcopy(self.s);p=copy.deepcopy(self.p)
        again=build(s,p,self.templates,prepared=self.prepared)
        self.assertEqual(self.result,again);self.assertEqual(s,self.s);self.assertEqual(p,self.p)
        p['paint_seed']+=1;b=build(s,p,self.templates,prepared=self.prepared)
        self.assertEqual(b['ledger'],again['ledger']);self.assertEqual(b['wood'],again['wood'])
        self.assertNotEqual([g['template_index'] for g in b['groups']],[g['template_index'] for g in again['groups']])

    def test_strict_inputs_and_limited_work(self):
        for key,value in [('tree_groups',265),('tree_groups',True),('seed',-1),('span_over_height',float('nan')),('branch_id','trunk'),('extra',1)]:
            p=copy.deepcopy(self.p);p[key]=value
            with self.assertRaises(ValueError):validate_sample(p)
        self.assertEqual(sum(allocate(17,{'a':1.,'b':2.,'c':3.}).values()),17)
        with self.assertRaises(ValueError):allocate(17,{'a':0})

if __name__=='__main__':unittest.main()
