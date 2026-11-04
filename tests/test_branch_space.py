import copy
from dataclasses import replace
import json
from pathlib import Path
import unittest
from treegen.branch_structure import (Branch, generate_structure, validate_structure, segment_distance, length, sub)
from treegen.branch_space import conflict, measure, separate

ROOT = Path(__file__).resolve().parents[1]


class BranchSpaceTests(unittest.TestCase):
    def spec(self):
        return json.loads((ROOT/'presets/v0.4.0/adulto.json').read_text())

    def test_segment_analytic_cases(self):
        for a, b, c, d, expected in [((0,0,0),(2,0,0),(1,-1,0),(1,1,0),0),
            ((0,0,0),(2,0,0),(0,1,0),(2,1,0),1),
            ((0,0,0),(1,0,0),(2,1,0),(2,2,0),2**.5),
            ((0,0,0),(0,0,0),(1,0,0),(2,0,0),1)]:
            self.assertAlmostEqual(segment_distance(a,b,c,d)[0], expected)
            self.assertAlmostEqual(segment_distance(c,d,a,b)[0], expected)

    def test_contact_radius_and_legitimate_junction(self):
        a=Branch('a',None,0,((0,0,0),(0,0,2)),(.2,.2))
        b=Branch('b','a',1,((0,0,1),(2,0,1)),(.1,.05))
        self.assertEqual(conflict(a,b),0)
        c=Branch('c',None,0,((-.5,0,1),(.5,0,1)),(.05,.05))
        self.assertGreater(conflict(a,c),0)
        d=replace(c,points=((-1,.4,1),(1,.4,1)))
        self.assertEqual(conflict(a,d),0)
        self.assertGreater(conflict(a,replace(d,points=((-1,.24,1),(1,.24,1)))),0)

    def test_determinism_and_invariants(self):
        base=generate_structure(self.spec())
        candidate, audit=separate(base)
        self.assertEqual(base,generate_structure(self.spec()))
        self.assertEqual((candidate,audit),separate(base))
        self.assertLessEqual(measure(candidate)['conflicts'],measure(base)['conflicts'])
        self.assertEqual(len(base.branches),len(candidate.branches))
        for a,b in zip(base.branches,candidate.branches):
            self.assertEqual((a.id,a.parent_id,a.radii,a.points[0]),(b.id,b.parent_id,b.radii,b.points[0]))
            self.assertEqual([p[2] for p in a.points],[p[2] for p in b.points])
            self.assertAlmostEqual(sum(length(sub(v,u)) for u,v in zip(a.points,a.points[1:])),
                                   sum(length(sub(v,u)) for u,v in zip(b.points,b.points[1:])))
            if a.level<2:self.assertEqual(a,b)
        self.assertLessEqual(audit['evaluated_candidates'],36*2*9)
        for scale in (.8,1.3):
            self.assertAlmostEqual(measure(base,scale)['length_m'],measure(candidate,scale)['length_m'])

    def test_validation(self):
        base=generate_structure(self.spec())
        for bad in (replace(base,branches=base.branches*2),replace(base,version='unknown'),
                    replace(base,branches=(replace(base.branches[0],radii=(float('nan'),)*12),*base.branches[1:])),
                    replace(base,branches=(base.branches[0],replace(base.branches[1],parent_id='missing'),*base.branches[2:]))):
            with self.assertRaises(ValueError):validate_structure(bad)
        for scale in (0,float('inf'),True,11):
            with self.assertRaises(ValueError):measure(base,scale)
        spec=self.spec();spec['parameters']['height_m']=float('nan')
        with self.assertRaises(ValueError):generate_structure(spec)

    def test_depth_and_seed(self):
        spec=self.spec();spec['parameters']['max_depth']=1
        base=generate_structure(spec)
        self.assertEqual(len(base.branches),1+spec['parameters']['primary_branches'])
        self.assertEqual(separate(base)[0],base)
        spec['seed']+=1
        self.assertNotEqual(base.digest(),generate_structure(spec).digest())
