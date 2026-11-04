"""O4: redistribuir madera y trayectorias sin acumular presupuesto sobre O3."""
import copy
from pathlib import Path
import unittest
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_volume_contract import validate_preset,triangle_bound
from treegen.oak_growth_v2 import generate as base
from treegen.oak_growth_v3 import generate as previous
from treegen.oak_growth_v4 import generate
from treegen.oak_volume_evaluation import volume_metrics
from treegen.oak_growth_mesh import meshes
from treegen.oak_growth import sample
from treegen.branch_structure import sub,length
ROOT=Path(__file__).resolve().parents[1]


def preset(stage='maduro'):
    return load_growth_preset(ROOT/f'presets/oak-growth/0.4.0/{stage}.json')


def triangles(s):
    return sum(len(f)-2 for b in meshes(s) for f in b['mesh']['polygons'])


class OakVolumeTests(unittest.TestCase):
    def test_fixed_cohort_reduces_inner_activity_and_develops_periphery(self):
        peripheral_improvements=0
        for stage in ('maduro','centenario'):
            for seed in range(3100,3105):
                p=preset(stage);old=volume_metrics(previous({**p,'version':'oak-growth-0.3.0'},seed));new=volume_metrics(generate(p,seed))
                self.assertLess(new['axis_length_over_H']['core'],old['axis_length_over_H']['core'])
                self.assertLess(new['inner_births_order_ge_2'],old['inner_births_order_ge_2'])
                self.assertGreater(new['secondary_mean_birth_radius_over_H'],old['secondary_mean_birth_radius_over_H'])
                peripheral_improvements+=new['axis_length_over_H']['periphery']>old['axis_length_over_H']['periphery']
        # Cohorte de comparación; no garantía de llenado universal por semilla.
        self.assertGreaterEqual(peripheral_improvements,8)

    def test_topology_base_and_original_budget_preserved(self):
        for stage in ('joven','maduro','centenario'):
            p=preset(stage);s=generate(p,3100);old=base({**p,'version':'oak-growth-0.2.0'},3100)
            signature=lambda rows:[(b['id'],len(b['points']),b['sides']) for b in rows]
            self.assertEqual(signature([b for b in s['branches'] if '/infill' not in b['id']]),signature(old['branches']))
            self.assertEqual(triangles(s)-triangles(old),s['branching_budget']['extra_triangles'])
            self.assertLessEqual(triangles(s)-triangles(old),700)
            self.assertLessEqual(triangles(s),triangle_bound(p));self.assertLess(triangles(s)+1584,7000)
            self.assertTrue(any(b['order']==2 and b['role']=='infill' for b in s['branches']))

    def test_dense_input_clamps_supplement_and_respects_small_child_limits(self):
        p=preset();p.update(maturity=1,competition=0,vigor=1.2)
        for r in p['orders']:r['branching_probability']=1
        s=generate(p,0,spatial=False)
        self.assertLessEqual(triangles(s)+1584,6999)
        self.assertLess(s['branching_budget']['extra_triangles'],660)
        # Los ejes añadidos también funcionan con frecuencia base mínima.
        for r in p['orders']:r['max_children']=1
        self.assertLessEqual(triangles(generate(p,0)),triangle_bound(p))

    def test_habits_correlate_with_bough_without_uniform_ascending_response(self):
        s=generate(preset('centenario'),3103);boughs={b['id']:b['growth_habit'] for b in s['branches'] if b['order']==1}
        self.assertGreaterEqual(len(set(boughs.values())),3)
        for b in s['branches'][1:]:self.assertEqual(b['growth_habit'],boughs[b['id'].split('/')[0]])
        responses=[b['light_response'] for b in s['branches'] if b['order']==2]
        self.assertGreater(max(responses)-min(responses),.8)

    def test_reproducibility_connectivity_and_non_mutating_ablations(self):
        p=preset();initial=copy.deepcopy(p);s=generate(p,3100);generate(p,3104)
        self.assertEqual(s,generate(p,3100));self.assertEqual(initial,p)
        index={b['id']:b for b in s['branches']}
        for b in s['branches'][1:]:
            root,_=sample(index[b['parent_id']]['points'],b['parent_t'])
            self.assertLess(length(sub(root,b['points'][0])),1e-8)
        for order in (1,2,3):
            result=generate(p,3100,max_order=order)
            self.assertLessEqual(max(b['order'] for b in result['branches']),order)
            self.assertEqual(result['branching_budget']['extra_triangles'],0)

    def test_strict_contract(self):
        for key,value in [('surprise',1),('maturity',True),('competition',float('nan')),('version','oak-growth-0.3.0')]:
            p=preset();p[key]=value
            with self.assertRaises(ValueError):validate_preset(p)
        p=preset();p['orders'][1]['sides']=6
        with self.assertRaises(ValueError):validate_preset(p)

if __name__=='__main__':unittest.main()
