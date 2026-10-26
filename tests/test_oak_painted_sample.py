"""La muestra artística conserva raíz/plano y no reduce tris por hoja."""
import json
from pathlib import Path
import unittest
from treegen.oak_painted_sample import leaf_card,variant_for,select,twig_spec,secondary_supports
from treegen.foliage_molds import connection_geometry
ROOT=Path(__file__).resolve().parents[1]

class OakSampleTests(unittest.TestCase):
    def test_secondary_support_filter_uses_parent_hierarchy(self):
        wood=[{'id':'q3:primary:100','parent_id':'trunk'},
              {'id':'child','parent_id':'q3:primary:100'}]
        supports=[{'id':'direct','parent_branch_id':'q3:primary:100'},
                  {'id':'keep','parent_branch_id':'child'}]
        self.assertEqual(secondary_supports(wood,supports),[supports[1]])
        self.assertEqual(len(supports),2)
        with self.assertRaises(ValueError):secondary_supports(wood,[{'parent_branch_id':'missing'}])

    def test_fuller_twigs_preserve_centers_topology_and_source(self):
        import copy
        import math
        spec={'twig_radius_m':.02,'tip_radius_ratio':.25}
        for points in ([[0,0,0],[0,0,1]],[[0,0,0],[0,0,.5],[0,0,1]]):
            support={'points_m':points,'normal_start':[1,0,0],'normal_end':[1,0,0]}
            frozen=copy.deepcopy([support,spec])
            old,faces=connection_geometry(support,spec)
            new,new_faces=connection_geometry(support,twig_spec(spec,'fuller-v1'))
            self.assertEqual(faces,new_faces)
            self.assertEqual(len(old),len(new))
            for i in range(0,len(old),3):
                a=[sum(v[k] for v in old[i:i+3])/3 for k in range(3)]
                b=[sum(v[k] for v in new[i:i+3])/3 for k in range(3)]
                for x,y in zip(a,b):self.assertAlmostEqual(x,y)
                t=i/(len(old)-3)
                self.assertAlmostEqual(math.dist(new[i],b),.025*(1-.5*t))
            self.assertEqual([support,spec],frozen)
        self.assertEqual(twig_spec(spec),spec)
        with self.assertRaises(ValueError):twig_spec(spec,'unknown')

    def test_uv_root_and_plane_for_four_atlas_variants(self):
        atlas=json.loads((ROOT/'assets/roble-pintado/v0.2.0/manifest.json').read_text());width,height=atlas['files']['foliage.png']['size']
        leaf={'id':'sample:leaf','origin_m':[1,2,3],'length_m':.8,'axes':[[1,0,0],[0,.8,.6],[0,-.6,.8]]}
        for region in atlas['leaf_regions']:
            mesh=leaf_card(leaf,region,[width,height]);self.assertEqual(len(mesh['polygons']),2)
            for vertex,uv in zip(mesh['vertices'],mesh['uv']):
                self.assertAlmostEqual(sum((vertex[k]-leaf['origin_m'][k])*leaf['axes'][2][k] for k in range(3)),0)
                self.assertTrue(0<=uv[0]<=1 and 0<=uv[1]<=1)
                px,py=uv[0]*width,(1-uv[1])*height
                expected_along=(region['root_px'][1]-py)/(region['opaque_bbox_px'][3]-region['opaque_bbox_px'][1])*.8
                self.assertAlmostEqual(vertex[0]-leaf['origin_m'][0],expected_along)
    def test_seed_is_stable_and_select_rejects_incomplete_groups(self):
        leaf={'id':'sample:leaf'};self.assertEqual(variant_for(leaf),variant_for(leaf));self.assertIn(variant_for(leaf),range(4))
        reference={'branches':[{'id':'q3:primary:100','parent_id':'q3:trunk:0'}]}
        with self.assertRaises(ValueError):select(reference,{'supports':[],'placements':[]})

if __name__=='__main__':unittest.main()
