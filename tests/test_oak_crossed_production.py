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


if __name__=='__main__':unittest.main()
