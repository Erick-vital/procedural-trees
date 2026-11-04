"""OF3: presupuesto completo, bifurcaciones y protección real del núcleo."""
import copy
import json
import math
from collections import Counter
from pathlib import Path
import unittest
from PIL import Image
from treegen.oak_crown_contract import load_growth_preset
from treegen.oak_growth_v5 import generate
from treegen.oak_foliage_canopy import build,minimum_radius
from treegen.oak_foliage_canopy_contract import validate_canopy
from treegen.oak_foliage_cards import prepare_templates
ROOT=Path(__file__).resolve().parents[1]


class OakFoliageCanopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=json.loads((ROOT/'configs/oak-foliage/canopy-B.json').read_text())
        cls.s=generate(load_growth_preset(ROOT/cls.spec['preset']),cls.spec['seed'])
        cls.templates=json.loads((ROOT/'assets/roble-pintado/v0.3.0/templates.json').read_text())['templates']
        cls.prepared=prepare_templates(cls.templates,Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').convert('RGBA'))
        cls.r=build(cls.s,cls.spec,cls.templates,prepared=cls.prepared)

    def test_full_budget_and_historical_wood(self):
        r=self.r;self.assertEqual(r['wood'],self.s['branches']);self.assertEqual(len(r['groups']),216)
        self.assertEqual(sum(len(f)-2 for pc in r['foliage'] for f in pc['polygons']),1296)
        self.assertEqual(r['ledger']['tree_projected_triangles'],5010)
        self.assertLessEqual(r['ledger']['tree_projected_triangles'],6999)
        self.assertEqual(sum(r['fork_quotas'].values()),216)
        self.assertLessEqual(max(r['axis_quotas'].values()),12)

    def test_clear_cylinder_checks_edges_and_interiors(self):
        card=lambda vs:{'vertices':vs,'polygons':[tuple(range(len(vs)))]}
        # Vértices exteriores pero interior/segmento cruza núcleo.
        self.assertEqual(minimum_radius([card([(-4,-4,3),(4,-4,3),(4,4,3),(-4,4,3)])]),0)
        self.assertAlmostEqual(minimum_radius([card([(-4,1,3),(4,1,3),(4,2,3),(-4,2,3)])]),1)
        self.assertGreaterEqual(self.r['minimum_card_radius_m'],3.6)
        self.assertGreaterEqual(minimum_radius(self.r['foliage']),3.6)

    def test_bifurcation_balance_without_equality(self):
        q=self.r['fork_quotas']
        # La lateral corta obtiene desarrollo significativo; no igualar vigor.
        self.assertGreater(q['p:0/2'],8);self.assertLess(q['p:0/2'],q['p:0/1'])
        actual=Counter('/'.join(g['parent_branch_id'].split('/')[:2]) for g in self.r['groups'])
        self.assertEqual(dict(actual),q)
        for bid,n in self.r['ledger']['primary_quotas'].items():
            self.assertEqual(sum(v for k,v in q.items() if k.startswith(bid+'/')),n)

    def test_shapes_and_contacts_remain_on_real_axes(self):
        r=self.r;self.assertEqual({m['shape'] for m in r['masses']},{'broad','elongated','bridge'})
        self.assertEqual(len({g['candidate_id'] for g in r['groups']}),216)
        index={b['id']:b for b in self.s['branches']};deviations=[]
        from treegen.oak_growth import sample
        for g in r['groups']:
            b=index[g['parent_branch_id']];self.assertGreaterEqual(b['order'],2)
            self.assertGreaterEqual(min(self.prepared[g['template_index']]['root_alpha']),192)
            a,y,z=g['axes']
            self.assertAlmostEqual(sum(x*x for x in a),1)
            self.assertAlmostEqual(sum(x*v for x,v in zip(a,y)),0)
            self.assertAlmostEqual(sum(x*v for x,v in zip(a,z)),0)
            tangent=sample(b['points'],g['parent_t'])[1]
            deviations.append(abs(sum(x*v for x,v in zip(a,tangent))))
        self.assertGreater(sum(v<.8 for v in deviations),50)

    def test_deterministic_and_distinct_layout_seed(self):
        p=copy.deepcopy(self.spec);s=copy.deepcopy(self.s)
        self.assertEqual(build(s,p,self.templates,prepared=self.prepared),self.r)
        self.assertEqual(s,self.s);self.assertEqual(p,self.spec)
        p['layout_seed']=18;r=build(s,p,self.templates,prepared=self.prepared)
        self.assertEqual(r['wood'],self.r['wood']);self.assertEqual(r['ledger'],self.r['ledger'])
        self.assertNotEqual(r['groups'],self.r['groups']);self.assertGreaterEqual(r['minimum_card_radius_m'],3.6)

    def test_contract_rejects_unvalidated_ages_and_overbudget(self):
        for key,value in [('version','oak-foliage-sample-0.2.0'),('preset','presets/oak-growth/0.5.0/joven.json'),('tree_groups',265),('branch_id','p:0'),('mass_variant','B'),('span_over_height',float('nan'))]:
            p=copy.deepcopy(self.spec);p[key]=value
            with self.assertRaises(ValueError):validate_canopy(p)

if __name__=='__main__':unittest.main()
