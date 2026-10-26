"""Conservar plano/rombo/distribución al pasar de dos a un triángulo."""
import copy
import math
from pathlib import Path
import unittest
from treegen.blueprints import load_blueprint,load_instance,resolve_blueprint,validate_blueprint
from treegen.foliage_canopy import diamond_vertices
from treegen.oak_painted import card,validate_resources,OUTLINE
ROOT=Path(__file__).resolve().parents[1]

class OakPaintedTests(unittest.TestCase):
    def recipe(self):return load_blueprint(ROOT/'blueprints/roble_copa_ancha/2.0.0.json')
    def test_four_profiles_keep_parameters_seeds_and_budget(self):
        for name in ('pilot','joven-07','adulto-00','viejo-00'):
            request=load_instance(ROOT/f'presets/blueprints/roble-pintado/{name}.json');r=resolve_blueprint(self.recipe(),request);old=r['source_resolved_blueprint']
            self.assertEqual(r['parameters'],old['parameters']);self.assertEqual(r['base_spec'],old['base_spec'])
            self.assertEqual(r['canopy_spec'],old['canopy_spec']);self.assertEqual(r['base_seeds'],old['base_seeds'])
            self.assertEqual(r['budget_upper_bound']['triangles_max'],old['budget_upper_bound']['triangles_max']-1584)
    def leaf(self):
        return {'id':'leaf:0','support_id':'support:0','origin_m':[1,2,3],'length_m':.9,'axes':[[1,0,0],[0,.8,.6],[0,-.6,.8]],'variant':'diamond','fold_deg':0}
    def test_same_visible_vertices_and_plane(self):
        leaf=self.leaf();g=card(leaf,2718)
        self.assertEqual(g['visible_vertices_m'],diamond_vertices(leaf));self.assertEqual(len(g['polygons']),1)
        n=leaf['axes'][2]
        for v in g['vertices']:
            self.assertAlmostEqual(sum((v[k]-leaf['origin_m'][k])*n[k] for k in range(3)),0)
        for u,v in g['uv']:self.assertTrue(0<u<1 and 0<v<1)
    def test_enclosing_triangle_contains_original_diamond(self):
        def signed(a,b,p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        for p in ((0,0),(.48,-.3),(1,0),(.48,.3)):
            self.assertTrue(all(signed(OUTLINE[i],OUTLINE[(i+1)%3],p)>0 for i in range(3)))
    def test_paint_seed_preserves_geometry(self):
        a=card(self.leaf(),2718);variants=set()
        for seed in range(12):
            b=card(self.leaf(),seed);self.assertEqual(a['vertices'],b['vertices']);self.assertEqual(a['visible_vertices_m'],b['visible_vertices_m']);variants.add(b['atlas_variant'])
        self.assertEqual(variants,{0,1,2,3})
    def test_resources_and_mixing_rejected(self):
        b=self.recipe();r=copy.deepcopy(b['resources']);r['foliage']['sha256']='0'*64
        with self.assertRaises(ValueError):validate_resources(r)
        r['foliage']['path']='../foliage.png'
        with self.assertRaises(ValueError):validate_resources(r)
        b['components']['distribution']='pine-path-groups@0.2.0'
        with self.assertRaises(ValueError):validate_blueprint(b)
    def test_folded_leaf_not_silently_flattened(self):
        leaf=self.leaf();leaf['fold_deg']=10
        with self.assertRaises(ValueError):card(leaf,1)

if __name__=='__main__':unittest.main()
