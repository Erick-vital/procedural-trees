"""O5: cobertura exterior, protección del centro y presupuesto O4 exacto."""
import copy
import unittest
from pathlib import Path
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_periphery_contract import validate_preset
from treegen.oak_growth_v4 import generate as old
from treegen.oak_growth_v5 import generate
from treegen.oak_volume_evaluation import volume_metrics
from treegen.oak_growth_mesh import meshes
from treegen.oak_growth import sample
from treegen.branch_structure import sub,length
ROOT=Path(__file__).resolve().parents[1]


def preset(stage='maduro'):
    return load_growth_preset(ROOT/f'presets/oak-growth/0.5.0/{stage}.json')


def triangles(s):
    return sum(len(f)-2 for b in meshes(s) for f in b['mesh']['polygons'])


class OakPeripheryTests(unittest.TestCase):
    def pair(self,stage,seed):
        p=preset(stage)
        return old({**p,'version':'oak-growth-0.4.0'},seed),generate(p,seed)

    def check_distribution(self,a,b):
        x=volume_metrics(a);y=volume_metrics(b)
        self.assertLessEqual(y['axis_length_over_H']['core'],x['axis_length_over_H']['core']+1e-8)
        self.assertLessEqual(y['inner_births_order_ge_2'],x['inner_births_order_ge_2'])
        self.assertGreaterEqual(y['axis_length_over_H']['periphery'],x['axis_length_over_H']['periphery']-1e-8)
        self.assertGreaterEqual(y['occupied_cells_0_10H']['periphery'],x['occupied_cells_0_10H']['periphery'])
        return x,y

    def test_original_cohort_and_previously_underfilled_mature(self):
        for stage in ('maduro','centenario'):
            for seed in range(3100,3105):
                a,b=self.pair(stage,seed);x,y=self.check_distribution(a,b)
                self.assertGreater(y['axis_length_over_H']['periphery'],x['axis_length_over_H']['periphery'])
                self.assertGreater(y['occupied_cells_0_10H']['periphery'],x['occupied_cells_0_10H']['periphery'])

    def test_held_out_seeds_same_rule_no_core_or_budget_regression(self):
        # Estos controles no participan en la elección de coeficientes/reglas.
        for stage in ('maduro','centenario'):
            for seed in range(5000,5005):
                a,b=self.pair(stage,seed);self.check_distribution(a,b)
                self.assertEqual(triangles(a),triangles(b));self.assertLess(triangles(b)+1584,7000)

    def test_exact_scaffold_and_topology_and_bounded_search(self):
        for stage in ('joven','maduro','centenario'):
            a,b=self.pair(stage,3100)
            self.assertEqual([p for p in a['branches'] if p['order']<=1],[p for p in b['branches'] if p['order']<=1])
            self.assertEqual(triangles(a),triangles(b))
            signature=lambda s:[(p['id'],p['parent_id'],p['sides'],len(p['points'])) for p in s['branches']]
            self.assertEqual(signature(a),signature(b))
            self.assertLessEqual(b['periphery']['tested_candidates'],27*sum(p['order']==2 for p in b['branches']))
            reach=lambda s:max((p[0]**2+p[1]**2)**.5 for branch in s['branches'] for p in branch['points'])
            self.assertLessEqual(reach(b),reach(a)*1.030001)
            self.assertAlmostEqual(max(p[2] for q in b['branches'] for p in q['points']),b['preset']['height_m'])

    def test_reproducible_with_connected_positive_rings(self):
        p=preset();initial=copy.deepcopy(p);s=generate(p,3100)
        self.assertEqual(s,generate(p,3100));self.assertEqual(p,initial)
        index={b['id']:b for b in s['branches']}
        for b in s['branches'][1:]:
            root,_=sample(index[b['parent_id']]['points'],b['parent_t'])
            self.assertLess(length(sub(root,b['points'][0])),1e-8)
            self.assertTrue(all(r>0 for r in b['radii']))
            self.assertTrue(all(max(a/c,c/a)<=1.550001 for a,c in zip(b['radii'],b['radii'][1:])))

    def test_dense_controls_and_ablations(self):
        p=preset();p.update(maturity=1,competition=0,vigor=1.2)
        for row in p['orders']:row['branching_probability']=1
        for order in (1,2,3,4):
            a=old({**p,'version':'oak-growth-0.4.0'},0,max_order=order,spatial=False)
            b=generate(p,0,max_order=order,spatial=False)
            self.assertEqual(triangles(a),triangles(b));self.assertLess(triangles(b)+1584,7000)
            self.assertEqual({p['order'] for p in a['branches']},{p['order'] for p in b['branches']})

    def test_strict_version_and_input(self):
        for key,value in [('extra',1),('version','oak-growth-0.4.0'),('maturity',True),('curvature',float('inf'))]:
            p=preset();p[key]=value
            with self.assertRaises(ValueError):validate_preset(p)

if __name__=='__main__':unittest.main()
