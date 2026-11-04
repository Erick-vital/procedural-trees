import unittest
from treegen.branch_visibility import prune_network,directions,surface_samples


class VisibilityTests(unittest.TestCase):
    def network(self):
        mesh={'vertices':[[0,0,0],[1,0,0],[0,1,0]],'polygons':[[0,1,2]]}
        edges=[{'id':i,'parent':p,'mesh':mesh} for i,p in [('root',None),('a','root'),('b','a'),('hidden','a')]]
        return {'edges':edges,'connections':{'leaf':{'edge_id':'b'},'hiddenleaf':{'edge_id':'hidden'}},'triangles':4}

    def test_ancestors_and_geometry_preserved(self):
        n=self.network();result,audit=prune_network(n,['b'])
        self.assertEqual(audit['kept_ids'],['root','a','b'])
        self.assertEqual(audit['removed_ids'],['hidden'])
        self.assertEqual(result['edges'],n['edges'][:3])
        self.assertEqual(len(n['edges']),4)
        self.assertEqual(list(result['connections']),['leaf'])
        self.assertEqual(prune_network(n,['b']),prune_network(n,['b']))

    def test_root_and_validation(self):
        n=self.network();self.assertEqual(prune_network(n,[])[1]['kept_ids'],['root'])
        with self.assertRaises(ValueError):prune_network(n,['absent'])
        n['edges'][0]['parent']='b'
        with self.assertRaises(ValueError):prune_network(n,[])
        self.assertEqual(len(directions()),38);self.assertEqual(len(directions(15)),36)
        self.assertTrue(all(abs(sum(x*x for x in v)-1)<1e-12 for v in directions()))
        self.assertGreater(len(surface_samples(self.network()['edges'][0]['mesh'])),3)
