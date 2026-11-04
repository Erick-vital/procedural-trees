"""J3: cobertura completa sin vaciar ramas, volumen y presupuesto de producción."""
import copy
from pathlib import Path
import unittest
from treegen.blueprints import load_blueprint,load_instance,resolve_blueprint,validate_blueprint
from treegen.oak_young_production import prepare
from treegen.oak_young_volume import validate_canopy

ROOT=Path(__file__).resolve().parents[1]


class YoungVolumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=load_blueprint(ROOT/'blueprints/roble_copa_ancha/3.2.0.json')
        cls.instances={s:load_instance(ROOT/f'presets/blueprints/roble-joven-volumen/joven-{s}.json') for s in range(3100,3104)}
        cls.resolved={s:resolve_blueprint(cls.b,i) for s,i in cls.instances.items()}
        cls.data={s:prepare(r) for s,r in cls.resolved.items()}

    def test_all_axes_and_leader_receive_distal_groups(self):
        for d in self.data.values():
            expected={b['id'] for b in d['structure']['branches']}
            self.assertEqual({g['parent_branch_id'] for g in d['groups']},expected)
            self.assertEqual(set(d['diagnostics']['axis_coverage']),expected)
            self.assertTrue(all(x['distal_t']>.88 for x in d['diagnostics']['axis_coverage'].values()))
            self.assertTrue(any(g['role']=='leader' and g['parent_t']>.88 for g in d['groups']))

    def test_counts_caps_orthonormal_frames_and_budget(self):
        for d in self.data.values():
            self.assertEqual(len(d['groups']),264);self.assertEqual(len(d['foliage']),792)
            self.assertEqual(len({g['id'] for g in d['groups']}),264)
            self.assertEqual(sum(d['ledger']['axis_quotas'].values()),264)
            self.assertLessEqual(max(d['ledger']['axis_quotas'].values()),12)
            self.assertEqual(sum(len(f)-2 for m in d['foliage'] for f in m['polygons']),1584)
            self.assertLessEqual(d['ledger']['tree_projected_triangles'],6999)
            self.assertTrue(all(v[2]>=0 for m in d['foliage'] for v in m['vertices']))
            for g in d['groups']:
                self.assertTrue(all(abs(a[2])>.35 for a in g['axes']))
                for a in g['axes']:self.assertAlmostEqual(sum(v*v for v in a),1)
                self.assertAlmostEqual(sum(x*y for x,y in zip(g['axes'][0],g['axes'][1])),0)

    def test_old_contract_and_geometry_stay_separate(self):
        old_b=load_blueprint(ROOT/'blueprints/roble_copa_ancha/3.1.0.json')
        for seed in (3100,3102):
            old=prepare(resolve_blueprint(old_b,load_instance(ROOT/f'presets/blueprints/roble-joven/joven-{seed}.json')))
            self.assertEqual(old['wood'],self.data[seed]['wood'])
            self.assertEqual(len(old['groups']),144)
            self.assertEqual(old['ledger']['tree_projected_triangles']+720,self.data[seed]['ledger']['tree_projected_triangles'])
            self.assertGreater(max(max(g['size_m']) for g in self.data[seed]['groups']),max(max(g['size_m']) for g in old['groups']))

    def test_reject_mixed_components_and_invalid_parameters(self):
        for comp in ({**self.b['components'],'representation':'oak-young-crossed@0.1.0'},
                     {**self.b['components'],'distribution':'oak-young-chains@0.1.0'}):
            with self.assertRaises(ValueError):validate_blueprint({**self.b,'components':comp})
        for key,value in [('tree_groups',True),('tree_groups',265),('span_over_height',.1),
                          ('core_radius_over_height',False),('seed',-1),('extra',1)]:
            with self.subTest(key=key),self.assertRaises(ValueError):validate_canopy({**self.resolved[3100]['canopy_spec'],key:value})

    def test_repeat_input_immutability_and_distribution_seed(self):
        before=copy.deepcopy(self.resolved[3100]);again=prepare(before)
        self.assertEqual(before,self.resolved[3100]);self.assertEqual(again,self.data[3100])
        inst=copy.deepcopy(self.instances[3100]);inst['seeds']['canopy']=18
        changed=prepare(resolve_blueprint(self.b,inst))
        self.assertEqual(changed['wood'],again['wood']);self.assertNotEqual(changed['groups'],again['groups'])

if __name__=='__main__':unittest.main()
