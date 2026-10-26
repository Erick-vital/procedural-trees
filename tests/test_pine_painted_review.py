"""PP3: protocolo de cámaras y cobertura de la matriz, sin validación visual."""
import json
import math
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from review_pine_painted import camera, shots_for

class PaintedReviewTests(unittest.TestCase):
    def test_orbit_basis_and_target(self):
        center=[1,2,4]
        for direction in ([1,0,.25],[0,1,.25],[-1,-1,.25],[0,0,1]):
            c=camera(center,3,direction)
            x,y,z=c['basis_columns']
            for v in (x,y,z):self.assertAlmostEqual(sum(t*t for t in v),1)
            for a,b in ((x,y),(y,z),(z,x)):self.assertAlmostEqual(sum(i*j for i,j in zip(a,b)),0)
            self.assertAlmostEqual(math.dist(center,c['location']),9)
            self.assertAlmostEqual(c['ortho_scale'],3.9)

    def test_matrix_and_frozen_framing(self):
        lock=json.loads((ROOT/'docs/evidence/pino-pintado/pp2/reference-lock.json').read_text())
        before=json.dumps(lock,sort_keys=True)
        baseline,_,_=shots_for('baseline',lock)
        full,_,_=shots_for('full',lock)
        aa,_,_=shots_for('aa',lock)
        self.assertEqual(len(baseline),7)
        self.assertEqual(sum(s['id'].startswith('orbit-') for s in full),72)
        self.assertEqual(sum(s['id'].startswith('motion-') for s in full),24)
        self.assertEqual(len(aa),36)
        self.assertEqual(len({s['id'] for s in baseline+full+aa}),len(baseline+full+aa))
        self.assertEqual(json.dumps(lock,sort_keys=True),before)
        distance=[s for s in full if s['id'].startswith('light-tree-')]
        self.assertEqual([s['camera']['ortho_scale'] for s in distance],[24,48,120])
        self.assertTrue(all(s['camera']['basis_columns']==lock['cameras']['three_quarter']['basis_columns'] for s in distance))

if __name__=='__main__':unittest.main()
