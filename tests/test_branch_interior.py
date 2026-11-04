import unittest
from treegen.branch_sample import make_network
from treegen.branch_interior import proposals,apply_proposals


class InteriorTests(unittest.TestCase):
    def network(self):
        targets=[{'id':str(i),'point':(i*.05,(-1)**i*.2,1+i*.06)} for i in range(36)]
        return make_network([(0,0,0),(0,0,1),(0,0,2)],[.2,.12,.04],targets,13)

    def test_hidden_contractions_preserve_tree_and_protected_mesh(self):
        n=self.network();protected={e['id'] for e in n['edges'] if e['terminal'] or e['parent'] is None}
        options=proposals(n,protected);self.assertTrue(options)
        ids=[o['removed']+'>'+e['id'] for o in options for e in o['replacements']]
        result,audit=apply_proposals(n,options,ids)
        self.assertGreater(audit['removed_triangles'],0)
        self.assertLess(result['triangles'],n['triangles'])
        by_id={e['id']:e for e in result['edges']}
        for edge in n['edges']:
            if edge['id'] in protected:self.assertEqual(edge['mesh'],by_id[edge['id']]['mesh'])
        self.assertEqual(result['connections'],n['connections'])
        self.assertEqual((result,audit),apply_proposals(n,options,ids))

    def test_visible_replacements_reject_and_roots_protected(self):
        n=self.network();options=proposals(n,set())
        self.assertTrue(all(next(e for e in n['edges'] if e['id']==o['removed'])['parent'] is not None for o in options))
        self.assertEqual(apply_proposals(n,options,[])[0],n)
        with self.assertRaises(ValueError):proposals(n,{'absent'})
