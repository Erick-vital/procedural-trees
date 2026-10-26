"""Regla de poda por jerarquía, sin modificar la distribución de hojas."""
import copy
import json
from pathlib import Path
import unittest
from treegen.oak_painted_tree import retained_supports,build

ROOT=Path(__file__).resolve().parents[1]


class PaintedTreeTests(unittest.TestCase):
    def fixture(self):
        branches=[{'id':'a','parent_id':None},{'id':'b','parent_id':'a'},{'id':'c','parent_id':'b'}]
        supports=[{'id':str(i),'parent_branch_id':b['id'],'points_m':[[0,0,0],[0,0,1]],
                   'normal_start':[1,0,0],'normal_end':[1,0,0],'length_m':1} for i,b in enumerate(branches)]
        mesh={'vertices':[[0,0,0]]*8,'polygons':[],'smooth':[]}
        for b in branches:b['mesh']=copy.deepcopy(mesh)
        leaves=[{'id':s['id']+':'+str(i),'support_id':s['id'],'variant':'diamond','fold_deg':0,'origin_m':[i,0,0],
                 'axes':[[0,0,1],[1,0,0],[0,1,0]],'length_m':1} for s in supports for i in range(6)]
        source={'supports':supports,'placements':leaves,'canopy_spec':{'twig_radius_m':.02,'tip_radius_ratio':.25}}
        atlas=json.loads((ROOT/'assets/roble-pintado/v0.2.0/manifest.json').read_text())
        return {'branches':branches},source,atlas

    def test_only_secondary_supports_and_all_leaf_cards_retained(self):
        ref,src,atlas=self.fixture();frozen=copy.deepcopy((ref,src,atlas))
        parts,cards,kept=build(ref,src,atlas,2718)
        self.assertEqual([s['id'] for s in kept],['2'])
        self.assertEqual(len(cards),18)
        self.assertEqual(parts['painted'][-18:],parts['painted-full'][-18:])
        self.assertEqual(len(parts['wood-full'])-len(parts['wood']),2)
        self.assertEqual(len(cards[0]['polygons']),2)
        self.assertEqual((ref,src,atlas),frozen)
        self.assertEqual(build(ref,src,atlas,2718),(parts,cards,kept))

    def test_invalid_hierarchy_or_work_rejected_before_geometry(self):
        ref,src,_=self.fixture()
        ref['branches'][0]['parent_id']='c'
        with self.assertRaises(ValueError):retained_supports(ref,src['supports'])
        ref,src,_=self.fixture();src['supports'][0]['parent_branch_id']='missing'
        with self.assertRaises(ValueError):retained_supports(ref,src['supports'])
        ref,src,_=self.fixture()
        with self.assertRaises(ValueError):retained_supports(ref,src['supports']*121)


if __name__=='__main__':unittest.main()
