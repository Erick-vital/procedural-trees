"""O3: presupuesto contra O2, jerarquía y trayectorias con semillas fijas."""
import copy
import math
from pathlib import Path
import unittest
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_branching_contract import validate_preset,triangle_bound
from treegen.oak_growth_v2 import generate as before
from treegen.oak_growth_v3 import generate
from treegen.oak_growth_mesh import meshes
from treegen.oak_growth import sample
from treegen.oak_growth_runner import architecture_metrics
from treegen.branch_structure import sub,length
ROOT=Path(__file__).resolve().parents[1]


def preset(stage='maduro'):
    return load_growth_preset(ROOT/f'presets/oak-growth/0.3.0/{stage}.json')


def triangles(s):
    return sum(len(f)-2 for b in meshes(s) for f in b['mesh']['polygons'])


class OakBranchingTests(unittest.TestCase):
    def test_extra_budget_against_identical_o2_inputs_and_base_topology(self):
        for stage in ('joven','maduro','centenario'):
            for seed in range(3100,3105):
                p=preset(stage);s=generate(p,seed);old=before({**p,'version':'oak-growth-0.2.0'},seed)
                base=[b for b in s['branches'] if '/infill' not in b['id']]
                self.assertEqual([(b['id'],len(b['points']),b['sides']) for b in base],[(b['id'],len(b['points']),b['sides']) for b in old['branches']])
                delta=triangles(s)-triangles(old)
                self.assertGreater(delta,0);self.assertLessEqual(delta,700)
                self.assertEqual(delta,s['branching_budget']['extra_triangles'])
                self.assertLessEqual(triangles(s),triangle_bound(p));self.assertLess(triangles(s)+1584,7000)

    def test_dense_boundary_reduces_infill_instead_of_exceeding_full_budget(self):
        p=preset();p.update(maturity=1,competition=0,vigor=1.2)
        for row in p['orders']:row['branching_probability']=1
        s=generate(p,0,spatial=False)
        self.assertLessEqual(triangles(s)+1584,6999)
        self.assertLess(s['branching_budget']['extra_triangles'],660)
        self.assertGreater(s['branching_budget']['base_triangles'],4755)

    def test_primaries_less_upswept_and_centennial_spread_is_distinct(self):
        def rise(s):
            return sum((b['points'][-1][2]-b['points'][0][2])/sum(length(sub(y,x)) for x,y in zip(b['points'],b['points'][1:])) for b in s['branches'] if b['order']==1)
        for seed in range(3100,3105):
            p=preset();s=generate(p,seed);old=before({**p,'version':'oak-growth-0.2.0'},seed)
            self.assertLess(rise(s),rise(old))
            p=preset('centenario');s=generate(p,seed);old=before({**p,'version':'oak-growth-0.2.0'},seed)
            a=architecture_metrics(s);b=architecture_metrics(old)
            self.assertGreater(a['width_over_H']*a['depth_over_H'],b['width_over_H']*b['depth_over_H'])

    def test_continuity_positive_radii_and_four_orders(self):
        s=generate(preset('centenario'),3103);index={b['id']:b for b in s['branches']}
        self.assertEqual({b['order'] for b in s['branches']},{0,1,2,3,4})
        for b in s['branches']:
            self.assertTrue(all(math.isfinite(r) and r>0 for r in b['radii']))
            if b['parent_id']:
                root,_=sample(index[b['parent_id']]['points'],b['parent_t'])
                self.assertLess(length(sub(root,b['points'][0])),1e-8)
        self.assertLessEqual(architecture_metrics(s)['maximum_ring_radius_ratio'],1.550001)

    def test_reproducible_without_mutation_and_ablations(self):
        p=preset();original=copy.deepcopy(p);s=generate(p,3100);generate(p,3104)
        self.assertEqual(s,generate(p,3100));self.assertEqual(p,original)
        core=generate(p,3100,max_order=1)
        for a,b in zip(core['branches'],[b for b in s['branches'] if b['order']<=1]):
            for x,y in zip(a['points'],b['points']):
                self.assertLess(length(sub([v/core['uniform_scale'] for v in x],[v/s['uniform_scale'] for v in y])),1e-8)
        self.assertEqual(core['branching_budget']['extra_triangles'],0)

    def test_strict_contract(self):
        for key,value in [('unexpected',1),('maturity',True),('gravity',float('nan')),('version','oak-growth-0.2.0')]:
            p=preset();p[key]=value
            with self.assertRaises(ValueError):validate_preset(p)
        p=preset();p['orders'][0]['points']=10
        with self.assertRaises(ValueError):validate_preset(p)

if __name__=='__main__':unittest.main()
