"""Revisión 1.1.0: comparación controlada y estructura irregular reproducible."""
import copy
import json
import unittest

from treegen.blueprints import ROOT,load_blueprint,resolve_blueprint
from treegen.pine import build_pine
from treegen.pine_structure_v2 import diagnostics


class PineRevisionTests(unittest.TestCase):
    def setUp(self):
        self.old=load_blueprint(ROOT/'blueprints/pino_conico/1.0.0.json')
        self.new=load_blueprint(ROOT/'blueprints/pino_conico/1.1.0.json')
        self.matrix=json.loads((ROOT/'configs/verification/pine-v2.json').read_text())

    def test_comparison_keeps_seeds_parameters_foliage_palette_and_cost(self):
        previous=json.loads((ROOT/'configs/verification/pine-v1.json').read_text())
        self.assertEqual(self.old['parameters'],self.new['parameters'])
        self.assertEqual(self.old['appearance'],self.new['appearance'])
        for a,b in zip(previous['cases'],self.matrix['cases']):
            self.assertEqual(a['instance']['seeds'],b['instance']['seeds'])
            self.assertNotIn('overrides',b['instance'])
            old=resolve_blueprint(self.old,a['instance']);new=resolve_blueprint(self.new,b['instance'])
            self.assertEqual(old['canopy_spec'],new['canopy_spec'])
            self.assertEqual(old['budget_upper_bound'],new['budget_upper_bound'])

    def test_four_seeds_have_staggered_roots_and_mixed_slopes_with_same_counts(self):
        for row in self.matrix['cases']:
            with self.subTest(seed=row['instance']['seeds']):
                r=resolve_blueprint(self.new,row['instance'])
                branches,leaves=build_pine(r)
                self.assertEqual((branches,leaves),build_pine(r))
                self.assertEqual((len(branches),len(leaves)),(241,2892))
                d=diagnostics(branches)
                self.assertGreater(min(d['root_height_spread_by_level_m']),.7)
                self.assertGreater(d['descending_primaries'],0)
                self.assertGreater(d['ascending_primaries'],0)
                points=[v for b in branches for v in b['mesh']['vertices']]+[v for n in leaves for v in n['vertices']]
                self.assertEqual(min(v[2] for v in points),0)
                self.assertEqual(max(v[2] for v in points),12)

    def test_trunk_preserved_and_canopy_seed_does_not_change_structure(self):
        request=copy.deepcopy(self.matrix['cases'][0]['instance'])
        branches,_=build_pine(resolve_blueprint(self.new,request))
        request['seeds']['canopy']+=1
        changed,_=build_pine(resolve_blueprint(self.new,request))
        self.assertEqual(branches,changed)
        request['blueprint_version']='1.0.0'
        original,_=build_pine(resolve_blueprint(self.old,request))
        self.assertEqual(branches[0],original[0])
