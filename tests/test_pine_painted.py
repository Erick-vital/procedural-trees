"""PP4: contratos nuevos, recursos congelados, anclajes y semillas independientes."""
import copy
import unittest
from unittest.mock import patch
from treegen.contracts import ROOT
from treegen.blueprints import load_blueprint,load_instance,resolve_blueprint,validate_blueprint
from treegen.pine_painted import build,validate_resources,check_parameters
from treegen.pine import build_pine,point_on

class PaintedPineTests(unittest.TestCase):
    def setUp(self):
        self.b=load_blueprint(ROOT/'blueprints/pino_conico/2.0.0.json')
        self.i=load_instance(ROOT/'presets/blueprints/pino-pintado/pilot.json')
    def resolve(self):return resolve_blueprint(self.b,self.i)
    def test_four_cases_retain_paths(self):
        for name in ('pilot','control-01','control-02','control-03'):
            self.i=load_instance(ROOT/f'presets/blueprints/pino-pintado/{name}.json')
            r=self.resolve();branches,wood,groups=build(r)
            old=resolve_blueprint(load_blueprint(ROOT/'blueprints/pino_conico/1.1.0.json'),load_instance(ROOT/f'presets/blueprints/pino-v2/{name}.json'))
            self.assertEqual(branches,build_pine(old)[0])
            self.assertEqual((len(wood),len(groups)),(49,241))
            self.assertEqual(len({g['support_id'] for g in groups}),241)
            for b,g in zip(branches,groups):
                self.assertEqual(g['origin_m'],point_on(b,g['anchor_t']))
                self.assertEqual(len(g['polygons']),12)
                self.assertTrue(all(0<=v<=1 for uv in g['uv'] for v in uv))
            self.assertEqual(r['budget_upper_bound']['triangles_max'],5192)
    def test_paint_seed_does_not_move_geometry(self):
        a=build(self.resolve());self.i['seeds']['paint']+=1;b=build(self.resolve())
        self.assertEqual(a[:2],b[:2]);self.assertEqual([g['vertices'] for g in a[2]],[g['vertices'] for g in b[2]])
        self.assertNotEqual([g['atlas_variant'] for g in a[2]],[g['atlas_variant'] for g in b[2]])
    def test_repeat(self):self.assertEqual(build(self.resolve()),build(self.resolve()))
    def test_missing_or_invalid_paint_seed(self):
        for value in (None,True,-1,2147483647):
            i=copy.deepcopy(self.i)
            if value is None:i['seeds'].pop('paint')
            else:i['seeds']['paint']=value
            with self.assertRaises(ValueError):resolve_blueprint(self.b,i)
    def test_incompatible_components(self):
        self.b['components']['representation']='pine-needle-pairs@0.1.0'
        with self.assertRaises(ValueError):validate_blueprint(self.b)
    def test_invalid_resources(self):
        for field,value in [('sha256','0'*64),('path','../../missing.png')]:
            r=copy.deepcopy(self.b['resources']);r['foliage'][field]=value
            with self.assertRaises(ValueError):validate_resources(r)
        with patch('pathlib.Path.is_file',return_value=False):
            with self.assertRaises(ValueError):validate_resources(self.b['resources'])
    def test_unsupported_material_and_height(self):
        for field,value in [('height_m',10),('roughness',.3)]:
            b=copy.deepcopy(self.b)
            if field=='height_m':b['parameters']['base'][field]=value
            else:b['appearance']['leaf'][field]=value
            with self.assertRaises(ValueError):validate_blueprint(b)
    def test_budget_rejected(self):
        for limits in ({'triangles':5191,'materials':3},{'triangles':12500,'materials':1}):
            with self.assertRaises(ValueError):check_parameters(self.b['parameters'],limits)
    def test_historical_contract_rejects_painted(self):
        b=load_blueprint(ROOT/'blueprints/pino_conico/1.1.0.json')
        b['components']['representation']='pine-painted-crossed@0.1.0'
        with self.assertRaises(ValueError):validate_blueprint(b)

if __name__=='__main__':unittest.main()
