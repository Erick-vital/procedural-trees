"""Pino: contratos, límites y separación entre estructura y representación."""
import copy
import json
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from pathlib import Path

from treegen.blueprints import ROOT, load_blueprint, load_instance, resolve_blueprint, validate_blueprint
from treegen.pine import build_pine
from treegen.runner import execute_blueprint


class PineTests(unittest.TestCase):
    def setUp(self):
        self.recipe = load_blueprint(ROOT/'blueprints/pino_conico/1.0.0.json')
        self.request = load_instance(ROOT/'presets/blueprints/pino/pilot.json')

    def resolve(self):
        return resolve_blueprint(self.recipe,self.request)

    def test_reproducible_geometry_and_height_four_reserved_seeds(self):
        matrix = json.loads((ROOT/'configs/verification/pine-v1.json').read_text())
        for row in matrix['cases']:
            r = resolve_blueprint(self.recipe,row['instance'])
            a = build_pine(r)
            self.assertEqual(a,build_pine(r))
            branches,leaves = a
            self.assertEqual(len(branches),241)
            self.assertEqual(len(leaves),2892)
            points = [v for b in branches for v in b['mesh']['vertices']] + [v for n in leaves for v in n['vertices']]
            self.assertAlmostEqual(min(v[2] for v in points),0)
            self.assertAlmostEqual(max(v[2] for v in points),12)
            self.assertEqual(r['budget_upper_bound']['triangles_max'],11924)

    def test_canopy_seed_and_needle_size_preserve_wood(self):
        a = build_pine(self.resolve())
        self.request['seeds']['canopy'] += 1
        b = build_pine(self.resolve())
        self.assertEqual(a[0],b[0])
        self.assertNotEqual(a[1],b[1])
        self.request['overrides'] = {'canopy':{'needle_length_m':.4,'needle_width_m':.06}}
        c = build_pine(self.resolve())
        self.assertEqual(b[0],c[0])
        self.assertEqual([n['origin_m'] for n in b[1]],[n['origin_m'] for n in c[1]])

    def test_budget_rejects_joint_cost_before_blender(self):
        self.request['overrides'] = {'base':{'whorl_count':10,'branches_per_whorl':8}}
        with TemporaryDirectory() as temp, patch('treegen.runner.subprocess.Popen') as process:
            with self.assertRaisesRegex(ValueError,'Presupuesto'):
                execute_blueprint(self.recipe,self.request,Path(temp)/'job',render=False)
            process.assert_not_called()

    def test_rejects_incompatible_components_unknown_parameters_and_odd_pairs(self):
        for change in ({'canopy':{'needles_per_twig':11}}, {'base':{'whorl_count':True}},
                       {'base':{'primary_branches':6}}, {'canopy':{'needle_length_m':float('nan')}}):
            with self.subTest(change=change):
                self.request['overrides'] = change
                with self.assertRaises(ValueError):self.resolve()
        self.recipe['components']['base'] = 'oak_geometry_nodes@0.4.0'
        with self.assertRaisesRegex(ValueError,'incompatible'):validate_blueprint(self.recipe)

    def test_contract_versions_and_frozen_resolution(self):
        r = self.resolve()
        self.assertEqual(r,resolve_blueprint(r['blueprint_definition'],r['instance_request']))
        self.request['schema_version'] = '1.0'
        with self.assertRaisesRegex(ValueError,'contrato'):self.resolve()

    def test_branch_topology_is_acyclic_and_whorls_narrow_upwards(self):
        branches,_ = build_pine(self.resolve())
        seen = set()
        for b in branches:
            if b['parent_id'] is not None:self.assertIn(b['parent_id'],seen)
            seen.add(b['id'])
        widths = [max(sum(v[k]**2 for k in (0,1))**.5 for b in branches if b['whorl']==level
                      for v in b['mesh']['vertices']) for level in range(8)]
        self.assertTrue(all(a>b for a,b in zip(widths,widths[1:])))
