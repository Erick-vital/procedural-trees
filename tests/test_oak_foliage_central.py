"""OF11: ramas verticales reales, cupo fijo y protección inferior recortada."""
import copy
import json
import math
from pathlib import Path
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_growth_central import add_central_branch
from treegen.oak_foliage_central import build,minimum_radius_below
from treegen.oak_foliage_central_contract import validate_canopy
from treegen.oak_foliage_gaps import build as build_v10
from treegen.oak_foliage_top import prepare_opaque_samples
from treegen.oak_foliage_cards import prepare_templates,rooted_panels
from treegen.oak_growth_mesh import tube
ROOT=Path(__file__).resolve().parents[1]


class OakFoliageCentralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'configs/oak-foliage/central-B.json').read_text())
        cls.s=generate(load_growth_preset(ROOT/cls.p['preset']),cls.p['seed'])
        cls.t=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        image=Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA')
        cls.g=prepare_opaque_samples(prepare_templates(cls.t,image),image)
        cls.r=build(cls.s,cls.p,cls.t,prepared=cls.g)
        cls.old=build_v10(cls.s,{**cls.p,'version':'oak-foliage-canopy-0.10.0'},cls.t,prepared=cls.g)

    def test_original_wood_and_three_real_ascending_axes(self):
        r=self.r;new=r['structure']['branches'][len(self.s['branches']):]
        self.assertEqual(r['wood'][:len(self.s['branches'])],self.s['branches'])
        self.assertEqual(len(new),21);self.assertEqual(r['central_extension']['structural_axes'],3)
        for bid in ('central','upright:0','upright:1'):
            b=next(b for b in new if b['id']==bid);a,z=b['points'][0],b['points'][-1]
            self.assertGreater(z[2]-a[2],math.dist(z[:2],a[:2]))
        self.assertLessEqual(r['central_extension']['added_wood_triangles'],600)
        self.assertEqual(r['ledger']['tree_projected_triangles'],5270+r['central_extension']['added_wood_triangles'])
        self.assertLessEqual(r['ledger']['tree_projected_triangles'],6999)

    def test_fixed_groups_and_actual_upper_contacts(self):
        self.assertEqual(len(self.r['groups']),216);self.assertEqual(len(self.r['central_changes']),24)
        self.assertEqual(len(self.r['foliage']),len(self.old['foliage']))
        old={g['id']:g for g in self.old['groups']};moved={q['id'] for q in self.r['central_changes']}
        from treegen.surface_evaluation import point_triangle_distance
        index={b['id']:b for b in self.r['wood']}
        for g in self.r['groups']:
            for k in ('size_m','template_index','root_normalized'):self.assertEqual(g[k],old[g['id']][k])
            if g['id'] not in moved:self.assertEqual(g,old[g['id']]);continue
            mesh=tube(index[g['parent_branch_id']]);error=min(point_triangle_distance(g['anchor_m'],*(mesh['vertices'][i] for i in (f[0],f[j],f[j+1]))) for f in mesh['polygons'] for j in range(1,len(f)-1))
            self.assertLess(error,1e-8)
            self.assertGreaterEqual(min(v[2] for c in rooted_panels(g,g['template_index']) for v in c['vertices']),7.44)
        self.assertEqual(self.r['foliage'][648:],self.old['foliage'][648:])
        self.assertGreaterEqual(self.r['minimum_lower_card_radius_m'],3.6)
        self.assertLess(self.r['minimum_card_radius_m'],3.6)
        self.assertLessEqual(self.r['central_attempts'],24*12)

    def test_height_clipping_protects_intersections_not_only_vertices(self):
        card={'vertices':[(0,0,9),(5,0,6),(0,5,6)],'polygons':[[0,1,2]]}
        self.assertAlmostEqual(minimum_radius_below([card],7),math.sqrt(50/9))
        self.assertEqual(minimum_radius_below([card],5),float('inf'))

    def test_determinism_and_immutable_inputs(self):
        s=copy.deepcopy(self.s);p=copy.deepcopy(self.p);g=copy.deepcopy(self.g)
        self.assertEqual(build(s,p,self.t,prepared=g),self.r)
        self.assertEqual(s,self.s);self.assertEqual(p,self.p);self.assertEqual(g,self.g)

    def test_three_structure_controls(self):
        for seed in (3101,3102,3103):
            p={**self.p,'seed':seed};s=generate(load_growth_preset(ROOT/p['preset']),seed)
            r=build(s,p,self.t,prepared=self.g)
            self.assertEqual(len(r['groups']),216);self.assertEqual(r['wood'][:len(s['branches'])],s['branches'])
            self.assertEqual(len(r['central_changes']),24);self.assertGreaterEqual(r['minimum_lower_card_radius_m'],3.6)
            self.assertLessEqual(r['ledger']['tree_projected_triangles'],6999)

    def test_contract(self):
        for k,v in [('version','oak-foliage-canopy-0.10.0'),('tree_groups',215),('extra',1),('preset','presets/oak-growth/0.5.0/joven.json')]:
            with self.assertRaises(ValueError):validate_canopy({**self.p,k:v})

if __name__=='__main__':unittest.main()
