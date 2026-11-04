"""O2: límites de crecimiento, huecos, madurez, continuidad y reproducción."""
import copy
import math
from pathlib import Path
import unittest
from treegen.oak_crown_contract import load_growth_preset,validate_preset
from treegen.oak_crown_balance import CrownField
from treegen.oak_crown_evaluation import crown_metrics
from treegen.oak_growth import generate as old,sample
from treegen.oak_growth_v2 import generate
from treegen.oak_growth_contract import triangle_bound
from treegen.oak_growth_mesh import meshes
from treegen.branch_structure import sub,length
ROOT=Path(__file__).resolve().parents[1]

class OakCrownTests(unittest.TestCase):
    def setUp(self):
        self.p=load_growth_preset(ROOT/'presets/oak-growth/0.2.0/maduro.json')
        self.old=load_growth_preset(ROOT/'presets/oak-growth/0.1.0/maduro.json')

    def test_five_paired_seeds_reduce_extreme_reach_and_center_bias(self):
        for seed in range(3100,3105):
            a=crown_metrics(old(self.old,seed));b=crown_metrics(generate(self.p,seed))
            self.assertLess(b['max_horizontal_reach_over_H'],a['max_horizontal_reach_over_H']*.85)
            self.assertLess(b['crown_center_offset_over_H'],a['crown_center_offset_over_H'])

    def test_not_a_spherical_shell_or_identical_seeds(self):
        signatures=set()
        for seed in range(3100,3105):
            s=generate(self.p,seed);metrics=crown_metrics(s)
            self.assertGreater(max(metrics['sector_reach_over_H'])-min(metrics['sector_reach_over_H']),.1)
            self.assertGreater(metrics['largest_endpoint_angular_gap_deg'],20)
            signatures.add(str(s['branches'][1]['points']))
        self.assertEqual(len(signatures),5)

    def test_maturity_preserves_different_relative_habits(self):
        values=[generate(load_growth_preset(ROOT/f'presets/oak-growth/0.2.0/{stage}.json'),3100) for stage in ('joven','maduro','centenario')]
        extent=[crown_metrics(s)['max_horizontal_reach_over_H'] for s in values]
        self.assertLess(extent[0],extent[1]);self.assertLess(extent[1],extent[2])
        self.assertGreater(values[0]['apical_dominance'],values[1]['apical_dominance'])
        self.assertGreater(values[1]['apical_dominance'],values[2]['apical_dominance'])

    def test_determinism_does_not_depend_on_generation_order(self):
        a=generate(self.p,3100);generate(self.p,3104)
        self.assertEqual(a,generate(self.p,3100))
        self.assertEqual(a['balance']['random_namespace'],'oak-growth-0.1.0')

    def test_root_attachments_and_thickness_are_continuous(self):
        s=generate(self.p,3100);index={b['id']:b for b in s['branches']}
        for b in s['branches'][1:]:
            point,_=sample(index[b['parent_id']]['points'],b['parent_t'])
            self.assertLess(length(sub(point,b['points'][0])),1e-8)
            self.assertTrue(all(0<r and math.isfinite(r) for r in b['radii']))
            self.assertTrue(all(max(a/c,c/a)<=1.550001 for a,c in zip(b['radii'],b['radii'][1:])))

    def test_reservation_and_orders_remain_within_budget(self):
        for stage in ('joven','maduro','centenario'):
            p=load_growth_preset(ROOT/f'presets/oak-growth/0.2.0/{stage}.json');s=generate(p,3100)
            self.assertEqual({b['order'] for b in s['branches']},{0,1,2,3,4})
            tris=sum(len(face)-2 for b in meshes(s) for face in b['mesh']['polygons'])
            self.assertLessEqual(tris,triangle_bound(p));self.assertLess(triangle_bound(p)+1584,7000)

    def test_zero_strength_disables_field_braking_and_path_cap(self):
        p=copy.deepcopy(self.p);p['crown_balance']['strength']=0;field=CrownField(p,1.)
        outside=(100,100,100)
        self.assertEqual(field.growth_factor(outside),1)
        self.assertEqual(field.penalty(outside),0)
        self.assertEqual(field.axis_budget(3,outside,100,3),3)

    def test_strict_contract_and_legacy_input_unchanged(self):
        before=copy.deepcopy(self.p);generate(self.p,3100);self.assertEqual(self.p,before)
        for key,value in [('strength',True),('radius_ratio',math.inf),('path_ratio',2),('unknown',1)]:
            p=copy.deepcopy(self.p);p['crown_balance'][key]=value
            with self.assertRaises(ValueError):validate_preset(p)
        self.assertEqual(self.old['version'],'oak-growth-0.1.0')
        self.assertNotIn('crown_balance',self.old)

if __name__=='__main__':unittest.main()
