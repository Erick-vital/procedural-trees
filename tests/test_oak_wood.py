"""Cotas de error, extremos, UV y validación de tubos del ensayo."""
import copy
import math
import unittest
from treegen.oak_wood import optimize, build
from treegen.oak_painted_sample import wood_uv


def branch():
    vertices = [[math.cos(j*math.pi/4), math.sin(j*math.pi/4), float(r)] for r in range(6) for j in range(8)]
    polygons = [[r*8+j,r*8+(j+1)%8,(r+1)*8+(j+1)%8,(r+1)*8+j] for r in range(5) for j in range(8)]
    polygons += [list(reversed(range(8))), list(range(40,48))]
    return {'id':'test','parent_id':None,'mesh':{'vertices':vertices,'polygons':polygons,'smooth':[True]*40+[False]*2}}


class OakWoodTests(unittest.TestCase):
    def test_straight_tube_preserves_ends_caps_uv_and_source(self):
        b=branch(); frozen=copy.deepcopy(b); result=optimize(b,.005)
        self.assertEqual(b,frozen)
        self.assertEqual(result['optimization']['retained_rings'],[0,5])
        self.assertEqual(result['mesh']['vertices'],b['mesh']['vertices'][:8]+b['mesh']['vertices'][-8:])
        self.assertEqual(result['uv'],wood_uv(b)[:8]+wood_uv(b)[-8:])
        self.assertEqual(result['mesh']['smooth'],[True]*8+[False]*2)

    def test_whole_span_error_prevents_accumulated_drift(self):
        b=branch()
        for i,v in enumerate(b['mesh']['vertices']): v[0]+=.03*math.sin((i//8)*math.pi/5)
        result=optimize(b,.005); self.assertGreater(len(result['optimization']['retained_rings']),2)
        self.assertLessEqual(result['optimization']['max_correspondence_error_m'],.005)
        self.assertEqual(result,optimize(b,.005))

    def test_validation_and_supports_remain_exact(self):
        for t in (0,-1,.03,float('nan'),float('inf')):
            with self.assertRaises(ValueError): optimize(branch(),t)
        invalid=branch();invalid['mesh']['polygons'][0].reverse()
        with self.assertRaises(ValueError): optimize(invalid)
        b=branch();support=({'vertices':[[0,0,0]],'polygons':[]},0,[[0,0]])
        wood=[(b['mesh'],0,wood_uv(b)),support]
        parts,_=build(wood,[b],.005);self.assertEqual(parts[-1],support)

    def test_selective_preserves_trunk_and_primary(self):
        branches=[branch() for _ in range(3)]
        for i,b in enumerate(branches):
            b['id']=str(i);b['parent_id']=None if i==0 else str(i-1)
        wood=[(b['mesh'],0,wood_uv(b)) for b in branches]
        parts,bs=build(wood,branches,.02,secondary_only=True)
        self.assertEqual(parts[:2],wood[:2])
        self.assertEqual(bs[2]['optimization']['retained_rings'],[0,5])


if __name__=='__main__': unittest.main()
