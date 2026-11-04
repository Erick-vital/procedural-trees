"""Invariantes de arquitectura, madurez, presupuesto y determinismo O1."""
import copy
import math
from pathlib import Path
import unittest
from treegen.oak_growth_contract import load_preset,validate_preset,validate_seed,triangle_bound
from treegen.oak_growth import generate,sample
from treegen.oak_growth_mesh import meshes
from treegen.oak_growth_runner import architecture_metrics
from treegen.branch_structure import length,sub
ROOT=Path(__file__).resolve().parents[1]

class OakGrowthTests(unittest.TestCase):
    def setUp(self):self.p=load_preset(ROOT/'presets/oak-growth/0.1.0/maduro.json')

    def test_determinism_independent_of_execution_order(self):
        a=generate(self.p,3100);generate(self.p,3101)
        self.assertEqual(a,generate(self.p,3100))

    def test_seed_changes_architecture_and_branch_frequency(self):
        values=[generate(self.p,seed) for seed in range(3100,3105)]
        self.assertEqual(len({str(v['branches'][1]['points']) for v in values}),5)
        self.assertGreater(len({len(v['branches']) for v in values}),1)

    def test_same_seed_maturity_changes_rules_beyond_scale(self):
        values=[generate({**self.p,'maturity':m},3100) for m in (.15,.65,.95)]
        metrics=[architecture_metrics(s) for s in values]
        self.assertGreater(values[0]['apical_dominance'],values[-1]['apical_dominance'])
        self.assertGreater(metrics[0]['axis_height_over_H'],metrics[-1]['axis_height_over_H'])
        self.assertLess(len(values[0]['branches']),len(values[-1]['branches']))
        self.assertLess(values[0]['branches'][0]['radii'][0],values[-1]['branches'][0]['radii'][0])

    def test_all_orders_connected_and_staggered(self):
        for seed in range(3100,3105):
            s=generate(self.p,seed);index={b['id']:b for b in s['branches']}
            self.assertEqual({b['order'] for b in s['branches']},{0,1,2,3,4})
            for b in s['branches'][1:]:
                parent=index[b['parent_id']];point,_=sample(parent['points'],b['parent_t'])
                self.assertLess(length(sub(point,b['points'][0])),1e-8)
                self.assertEqual(parent['order']+1,b['order'])
            heights=[b['points'][0][2] for b in s['branches'] if b['order']==1]
            self.assertEqual(len(heights),len(set(heights)));self.assertGreater(max(heights)-min(heights),self.p['height_m']*.15)

    def test_triangle_budget_includes_reserved_foliage_for_all_presets(self):
        for stage in ('joven','maduro','centenario'):
            p=load_preset(ROOT/f'presets/oak-growth/0.1.0/{stage}.json')
            self.assertEqual(triangle_bound(p),5156);self.assertLess(triangle_bound(p)+1584,7000)
            pieces=meshes(generate(p,3100));actual=sum(len(face)-2 for b in pieces for face in b['mesh']['polygons'])
            self.assertLessEqual(actual,triangle_bound(p))

    def test_geometry_has_finite_uv_positive_radii_and_valid_topology(self):
        s=generate(self.p,3100)
        for b in s['branches']:
            self.assertTrue(all(r>0 and math.isfinite(r) for r in b['radii']))
            self.assertTrue(all(max(x/y,y/x)<=1.550001 for x,y in zip(b['radii'],b['radii'][1:])))
        for item in meshes(s):
            mesh=item['mesh'];self.assertEqual(len(mesh['vertices']),len(mesh['uv']))
            self.assertTrue(all(math.isfinite(x) for row in mesh['vertices']+mesh['uv'] for x in row))
            self.assertTrue(all(len(set(face))==len(face) and all(0<=i<len(mesh['vertices']) for i in face) for face in mesh['polygons']))

    def test_spatial_rule_has_effect_without_mutating_inputs(self):
        before=copy.deepcopy(self.p);a=generate(self.p,3100);b=generate(self.p,3100,spatial=False)
        self.assertEqual(self.p,before);self.assertNotEqual(a['branches'][1]['points'],b['branches'][1]['points'])

    def test_ablation_preserves_primary_paths(self):
        a=generate(self.p,3100);b=generate(self.p,3100,max_order=1)
        for u,v in zip([r for r in a['branches'] if r['order']<=1],b['branches']):
            for x,y in zip(u['points'],v['points']):
                for c,d in zip(x,y):self.assertAlmostEqual(c/a['uniform_scale'],d/b['uniform_scale'])
        self.assertEqual({r['order'] for r in b['branches']},{0,1})

    def test_primary_controls_change_birth_and_direction(self):
        base=generate(self.p,3100)
        changed=copy.deepcopy(self.p);changed['orders'][0]['fork_angle_deg']=45
        self.assertNotEqual(base['branches'][1]['points'],generate(changed,3100)['branches'][1]['points'])
        changed=copy.deepcopy(self.p);changed['orders'][0]['attachment_min']=.45
        self.assertNotAlmostEqual(base['branches'][1]['points'][0][2],generate(changed,3100)['branches'][1]['points'][0][2])

    def test_strict_input_limits(self):
        for key,value in [('height_m',math.inf),('maturity',True),('competition',-1),('vigor',2),('unknown',1)]:
            with self.assertRaises(ValueError):validate_preset({**self.p,key:value})
        for seed in (True,-1,2147483647,1.2):
            with self.assertRaises(ValueError):validate_seed(seed)
        p=copy.deepcopy(self.p);p['orders'][1]['max_children']=4
        with self.assertRaises(ValueError):validate_preset(p)
        p=copy.deepcopy(self.p);p['orders'][3]['points']=9
        with self.assertRaises(ValueError):validate_preset(p)

if __name__=='__main__':unittest.main()
