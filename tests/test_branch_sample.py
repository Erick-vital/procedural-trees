import math
import unittest
from treegen.branch_sample import make_network


class BranchSampleTests(unittest.TestCase):
    def fixture(self):
        return [(0,0,0),(0,0,1),(0,0,2)], [.18,.12,.02], [
            {'id':str(i),'point':(math.sin(i*2.4)*.6,math.cos(i*2.4)*.6,.7+i*.09)} for i in range(20)]

    def test_frozen_targets_determinism_and_connections(self):
        p,r,t=self.fixture();a=make_network(p,r,t,13)
        self.assertEqual(a,make_network(p,r,list(reversed(t)),13))
        self.assertEqual(set(a['connections']),{row['id'] for row in t})
        for row in t:
            self.assertLess(math.dist(row['point'],a['connections'][row['id']]['point']),1e-12)
        edges={e['id']:e for e in a['edges']};counts={}
        for edge in edges.values():
            if edge['parent'] is not None:
                parent=edges[edge['parent']]
                self.assertEqual(edge['points'][0],parent['points'][-1])
                self.assertLess(edge['radii'][0],parent['radii'][-1])
                counts[edge['parent']]=counts.get(edge['parent'],0)+1
            mesh=edge['mesh']
            self.assertTrue(all(0<=i<len(mesh['vertices']) for f in mesh['polygons'] for i in f))
        self.assertLessEqual(max(counts.values()),2)
        self.assertLessEqual(a['triangles'],12*len(t)+18)

    def test_limits_and_invalid_geometry(self):
        p,r,t=self.fixture()
        for bad in ([],t+[t[0]],[{'id':'a','point':(float('nan'),0,0)}],t*19):
            with self.assertRaises(ValueError):make_network(p,r,bad,13)
        for seed in (-1,True,float('inf')):
            with self.assertRaises(ValueError):make_network(p,r,t,seed)
        with self.assertRaises(ValueError):make_network([(0,0,0)]*3,r,t,13)
