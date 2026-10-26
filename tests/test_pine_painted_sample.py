"""Contratos acotados de la muestra PP2; no acreditan calidad visual."""
import unittest
import math
from pathlib import Path
from treegen.blueprints import load_blueprint, load_instance, resolve_blueprint
from treegen.pine_painted_sample import select, sample_panels, panels

ROOT = Path(__file__).resolve().parents[1]

class PaintedSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolved = resolve_blueprint(load_blueprint(ROOT/'blueprints/pino_conico/1.1.0.json'),
                                        load_instance(ROOT/'presets/blueprints/pino-v2/pilot.json'))

    def test_selection_and_repetition(self):
        wood, needles, lock = select(self.resolved)
        self.assertEqual((len(wood),len(needles)), (5,60))
        self.assertEqual(select(self.resolved), (wood,needles,lock))
        self.assertEqual(lock['seeds'], {'base':5100,'canopy':97})
        for mode in ('folded','crossed'):
            result=sample_panels(wood,mode)
            self.assertEqual(result,sample_panels(wood,mode))
            self.assertEqual(sum(len(p['polygons']) for p in result),60)
            for b,p in zip(wood,result):
                if b != wood[0]: self.assertEqual(p['origin_m'],b['points_m'][0])
                self.assertTrue(all(math.isfinite(v) for xyz in p['vertices'] for v in xyz))
                self.assertTrue(all(0<=v<=1 for uv in p['uv'] for v in uv))
                for a,c,d in p['polygons']:
                    from treegen.pine import cross, sub
                    self.assertGreater(sum(x*x for x in cross(sub(p['vertices'][c],p['vertices'][a]),sub(p['vertices'][d],p['vertices'][a]))),1e-14)

    def test_invalid_input(self):
        with self.assertRaises(ValueError): select(self.resolved,'pine:trunk')
        b=select(self.resolved)[0][0]
        for mode,index in [('billboard',0),('folded',3),('folded',-1)]:
            with self.assertRaises(ValueError): panels(b,mode,index)

if __name__=='__main__': unittest.main()
