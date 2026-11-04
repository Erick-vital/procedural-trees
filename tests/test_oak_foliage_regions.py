"""OF9: conservación de presupuesto/pintura, anclajes y reglas reproducibles."""
import copy
import json
from pathlib import Path
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_foliage_regions import build, centroid
from treegen.oak_foliage_regions_contract import validate_canopy
from treegen.oak_foliage_balance import build as build_v8
from treegen.oak_foliage_top import prepare_opaque_samples
from treegen.oak_foliage_cards import prepare_templates
from treegen.oak_foliage_layout import surface_point
from treegen.branch_structure import sub, length
ROOT = Path(__file__).resolve().parents[1]


class OakFoliageRegionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = json.loads((ROOT/'configs/oak-foliage/regions-B.json').read_text())
        cls.s = generate(load_growth_preset(ROOT/cls.p['preset']), cls.p['seed'])
        cls.t = json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        image = Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA')
        cls.g = prepare_opaque_samples(prepare_templates(cls.t, image), image)
        cls.old = build_v8(cls.s, {**cls.p, 'version':'oak-foliage-canopy-0.8.0'}, cls.t, prepared=cls.g)
        cls.r = build(cls.s, cls.p, cls.t, prepared=cls.g)

    def test_exact_budget_wood_paint_and_primary_quotas(self):
        r = self.r
        self.assertEqual(r['wood'], self.old['wood'])
        self.assertEqual(r['ledger'], self.old['ledger'])
        self.assertEqual(len(r['foliage']), 711)
        self.assertEqual(len(r['groups']), 216)
        self.assertEqual(r['ledger']['tree_projected_triangles'], 5136)
        old = {g['id']:g for g in self.old['groups']}
        for g in r['groups']:
            ref = old[g['id']]
            for k in ('size_m','template_index','root_normalized'):
                self.assertEqual(g[k], ref[k])
            self.assertEqual(g['parent_branch_id'].split('/')[0], ref['parent_branch_id'].split('/')[0])
        self.assertEqual(sum(x['group_count'] for x in r['regions']), 216)
        self.assertLessEqual(r['region_attempts'], 216*9*12)

    def test_real_supports_and_protected_core(self):
        from treegen.oak_growth import sample, unit
        index = {b['id']:b for b in self.s['branches']}
        for g in self.r['groups']:
            b = index[g['parent_branch_id']]
            self.assertGreaterEqual(b['order'], 2)
            from treegen.oak_growth_mesh import tube
            from treegen.surface_evaluation import point_triangle_distance
            mesh = tube(b)
            distances = [point_triangle_distance(g['anchor_m'], *(mesh['vertices'][i] for i in (face[0], face[j], face[j+1])))
                         for face in mesh['polygons'] for j in range(1,len(face)-1)]
            self.assertLess(min(distances), 1e-8)
        self.assertGreaterEqual(self.r['minimum_card_radius_m'], 3.6)

    def test_spatial_change_without_scaling(self):
        self.assertGreater(sum(c['anchor_shift_m']>.01 for c in self.r['region_changes']), 50)
        self.assertTrue(any(r['neighbor_id'] for r in self.r['regions']))
        # No plano nuevo vertical: las rotaciones conservan elevación de normales.
        old = {g['id']:g for g in self.old['groups']}
        for g in self.r['groups']:
            self.assertEqual([a[2] for a in g['axes']], [a[2] for a in old[g['id']]['axes']])

    def test_determinism_and_immutable_inputs(self):
        p = copy.deepcopy(self.p); s = copy.deepcopy(self.s); geometry = copy.deepcopy(self.g)
        self.assertEqual(build(s,p,self.t,prepared=geometry), self.r)
        self.assertEqual(s,self.s); self.assertEqual(p,self.p); self.assertEqual(geometry,self.g)

    def test_structure_and_distribution_controls(self):
        for seed,layout in ((3101,17),(3102,17),(3103,17),(3100,18)):
            p = {**self.p,'seed':seed,'layout_seed':layout}
            s = generate(load_growth_preset(ROOT/p['preset']),seed)
            r = build(s,p,self.t,prepared=self.g)
            old = build_v8(s,{**p,'version':'oak-foliage-canopy-0.8.0'},self.t,prepared=self.g)
            self.assertEqual(r['ledger'],old['ledger']); self.assertEqual(len(r['foliage']),len(old['foliage']))
            self.assertEqual(r['wood'],s['branches']); self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)

    def test_contract(self):
        for k,v in [('version','oak-foliage-canopy-0.8.0'),('extra',1),('tree_groups',265),('preset','presets/oak-growth/0.5.0/joven.json')]:
            with self.assertRaises(ValueError): validate_canopy({**self.p,k:v})

if __name__=='__main__': unittest.main()
