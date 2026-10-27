"""Receta registrada, recursos congelados y presupuesto de tres láminas."""
import copy
from pathlib import Path
import unittest
from treegen.blueprints import load_blueprint,load_instance,resolve_blueprint,validate_blueprint
from treegen.oak_crossed_production import validate_resources
ROOT=Path(__file__).resolve().parents[1]


class OakCrossedProductionTests(unittest.TestCase):
    def recipe(self):return load_blueprint(ROOT/'blueprints/roble_copa_ancha/2.1.0.json')
    def test_profiles_resolve_with_frozen_resources_and_historical_inputs(self):
        b=self.recipe()
        for name in ('pilot','joven-07','adulto-00','viejo-00'):
            instance=load_instance(ROOT/f'presets/blueprints/roble-cruzado/{name}.json');r=resolve_blueprint(b,instance)
            self.assertEqual(r['resolved_version'],'1.4')
            self.assertEqual(r['parameters'],r['source_resolved_blueprint']['parameters'])
            self.assertEqual(r['base_seeds'],r['source_resolved_blueprint']['base_seeds'])
            self.assertEqual(r['budget_upper_bound']['panels_max'],792)
            self.assertEqual(r['budget_upper_bound']['materials_max'],2)
            self.assertEqual(resolve_blueprint(b,instance),r)

    def test_resource_hashes_paths_and_component_mix_are_rejected(self):
        b=self.recipe();resources=copy.deepcopy(b['resources']);resources['templates']['sha256']='0'*64
        with self.assertRaises(ValueError):validate_resources(resources)
        resources['templates']['path']='../templates.json'
        with self.assertRaises(ValueError):validate_resources(resources)
        b['components']['representation']='oak-painted-single@0.1.0'
        with self.assertRaises(ValueError):validate_blueprint(b)

    def test_selective_recipe_is_explicit_and_keeps_historical_inputs(self):
        b=load_blueprint(ROOT/'blueprints/roble_copa_ancha/2.2.0.json')
        for name in ('pilot','joven-07','adulto-00','viejo-00'):
            instance=load_instance(ROOT/f'presets/blueprints/roble-madera/{name}.json')
            r=resolve_blueprint(b,instance)
            old=resolve_blueprint(self.recipe(),load_instance(ROOT/f'presets/blueprints/roble-cruzado/{name}.json'))
            self.assertEqual(r['source_resolved_blueprint'],old['source_resolved_blueprint'])
            self.assertEqual(r['resources'],old['resources'])
            self.assertEqual(r['blueprint_definition']['components']['representation'],'oak-painted-crossed@0.2.0')
            self.assertEqual(r,resolve_blueprint(b,instance))
        b['components']['distribution']='foliage-canopy@0.1.0'
        with self.assertRaises(ValueError):validate_blueprint(b)

    def test_wood_export_rejects_changed_vertices_uv_or_duplicate_triangles(self):
        from treegen.oak_crossed_evaluation import validate_wood_faces
        wood=[({'vertices':[[0,0,0],[1,0,0],[1,1,0],[0,1,0]],'polygons':[[0,1,2,3]]},0,[[0,0]]*4)]
        points=[(0.,0.,0.,0.,1.),(1.,0.,0.,0.,1.),(1.,0.,-1.,0.,1.),(0.,0.,-1.,0.,1.)]
        rows=[tuple(sorted(points[i] for i in tri)) for tri in ((0,1,2),(0,2,3))]
        validate_wood_faces(rows,wood)
        with self.assertRaises(ValueError):validate_wood_faces([rows[0],rows[0]],wood)
        with self.assertRaises(ValueError):validate_wood_faces(rows+rows,wood)
        for index in (0,4):
            bad=copy.deepcopy(wood);bad[0][0]['vertices'][0][0]+=.01 if index==0 else 0
            if index==4:bad[0][2][0][1]+=.01
            with self.assertRaises(ValueError):validate_wood_faces(rows,bad)


if __name__=='__main__':unittest.main()
