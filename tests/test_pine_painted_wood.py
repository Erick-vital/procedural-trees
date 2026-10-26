"""Madera optimizada desacoplada de guías, follaje y ajuste leve de copa."""
import unittest
from treegen.blueprints import load_blueprint,load_instance,resolve_blueprint
from treegen.pine_painted import build
from treegen.pine_painted_wood import optimize,root_cap_inside,sampled_surface_error
from treegen.pine_painted_sample import canonical_hash
from treegen.pine import sub,unit,point_on

class WoodTests(unittest.TestCase):
    def resolve(self,n,version):
        folder='pino-pintado-madera' if version=='2.2.0' else 'pino-pintado-volumen'
        return resolve_blueprint(load_blueprint(f'blueprints/pino_conico/{version}.json'),load_instance(f'presets/blueprints/{folder}/{n}.json'))
    def test_four_cases_geometry_and_foliage(self):
        for n in ('pilot','control-01','control-02','control-03'):
            old=build(self.resolve(n,'2.1.0'));new=build(self.resolve(n,'2.2.0'))
            self.assertEqual(old[0],new[0]);self.assertEqual(len(new[2]),435)
            self.assertLess(sum(len(b['mesh']['polygons']) for b in new[1]),2000)
            for before,after in zip(old[1],new[1]):
                self.assertEqual(after['wood_optimization']['sides_unchanged'],8 if before['parent_id'] is None else 6)
                self.assertLessEqual(after['wood_optimization']['ring_correspondence_error_m'],.005)
                self.assertEqual(after['wood_optimization']['root_cap_removed'],before['parent_id'] is not None)
            lookup={b['id']:b for b in old[0]}
            for a,b in zip(old[2],new[2]):
                self.assertEqual(b['crown_tuning']['before_tuning_sha256'],canonical_hash(a))
                self.assertEqual(a['uv'],b['uv']);self.assertEqual(a['origin_m'],b['origin_m'])
                axis=unit(sub(lookup[a['support_id']]['points_m'][-1],a['origin_m']))
                for va,vb in zip(a['vertices'],b['vertices']):
                    delta=sub(va,a['origin_m']);along=sum(x*y for x,y in zip(delta,axis))
                    expected=[a['origin_m'][i]+along*axis[i]*.98+(delta[i]-along*axis[i])*.94 for i in range(3)]
                    self.assertEqual(expected,vb)
    def test_sampled_surface_and_uv(self):
        old=build(self.resolve('pilot','2.1.0'));new=build(self.resolve('pilot','2.2.0'))
        for a,b in zip(old[1],new[1]):
            self.assertLessEqual(sampled_surface_error(a,b),.005001)
            self.assertEqual(len(b['uv']),len(b['mesh']['vertices']))
    def test_cap_guard_and_repeat(self):
        r=self.resolve('pilot','2.2.0');self.assertEqual(build(r),build(r))
        old=build(self.resolve('pilot','2.1.0'));branch=old[1][1]
        import copy
        detached=copy.deepcopy(branch);detached['mesh']['vertices'][0][0]+=2
        self.assertFalse(root_cap_inside(detached,old[1][0]))
        self.assertFalse(optimize(detached,old[1][0])['wood_optimization']['root_cap_removed'])

if __name__=='__main__':unittest.main()
