"""Revisión común de volumen: anclajes, presupuesto y conservación histórica."""
import copy
import unittest
from treegen.blueprints import load_blueprint,load_instance,resolve_blueprint,validate_blueprint
from treegen.pine_painted import build,check_parameters
from treegen.pine import point_on

class VolumeTests(unittest.TestCase):
    def resolved(self,name,version):
        folder='pino-pintado-volumen' if version=='2.1.0' else 'pino-pintado'
        return resolve_blueprint(load_blueprint(f'blueprints/pino_conico/{version}.json'),load_instance(f'presets/blueprints/{folder}/{name}.json'))
    def test_common_rule_and_anchors(self):
        for name in ('pilot','control-01','control-02','control-03'):
            r=self.resolved(name,'2.1.0');a=build(r);old=build(self.resolved(name,'2.0.0'))
            self.assertEqual(a[:2],old[:2])
            self.assertEqual(len(a[2]),435);self.assertEqual(r['budget_upper_bound']['triangles_max'],7520)
            self.assertEqual(len({g['group_id'] for g in a[2]}),435)
            supports={b['id']:b for b in a[0]}
            for g in a[2]:
                self.assertEqual(g['origin_m'],point_on(supports[g['support_id']],g['anchor_t']))
                self.assertEqual(len(g['polygons']),12)
                self.assertLessEqual(max(v[2] for v in g['vertices']),11.970001)
            self.assertEqual(sum(g['support_id']=='pine:trunk' for g in a[2]),3)
            self.assertGreater(a[2][-1]['volume_rule']['width_gain'],a[2][3]['volume_rule']['width_gain'])
    def test_repeat_and_paint(self):
        r=self.resolved('pilot','2.1.0');a=build(r);self.assertEqual(a,build(r))
        r['paint_seed']+=1;b=build(r)
        self.assertEqual([g['vertices'] for g in a[2]],[g['vertices'] for g in b[2]])
        self.assertNotEqual([g['uv'] for g in a[2]],[g['uv'] for g in b[2]])
    def test_budget_and_mixed_components(self):
        r=self.resolved('pilot','2.1.0')
        with self.assertRaises(ValueError):check_parameters(r['parameters'],{'triangles':7519,'materials':2},representation='pine-painted-crossed@0.2.0')
        b=copy.deepcopy(r['blueprint_definition']);b['components']['distribution']='pine-path-groups@0.1.0'
        with self.assertRaises(ValueError):validate_blueprint(b)

if __name__=='__main__':unittest.main()
