"""Cruces reproducibles, cobertura geométrica local y presupuesto acotado."""
import copy
import unittest
from treegen.oak_crossed import groups,fit_templates,panels,dot,sub,USABLE


class OakCrossedTests(unittest.TestCase):
    def test_panels_preserve_center_axes_and_visible_box(self):
        g={'id':'s','center_m':[1,2,3],'size_m':[2,3,4],'axes':[[1,0,0],[0,1,0],[0,0,1]]}
        old=copy.deepcopy(g)
        for count in (2,3):
            ps=panels(g,7,count)
            self.assertEqual(sum(len(p['polygons']) for p in ps),2*count)
            for p in ps:
                for axis in range(3):
                    values=[dot(sub(v,g['center_m']),g['axes'][axis]) for v in p['vertices']]
                    self.assertAlmostEqual(min(values)+max(values),0)
                    self.assertLessEqual(max(values),g['size_m'][axis]/(2*USABLE)+1e-9)
                self.assertTrue(all(0<=x<=1 for uv in p['uv'] for x in uv))
        self.assertEqual(g,old)
        with self.assertRaises(ValueError):panels(g,0,4)

    def test_template_fit_is_stable_and_rejects_excess_work(self):
        items=[{'id':str(i),'descriptor':[i,i*.2]} for i in range(12)]
        self.assertEqual(fit_templates(items),fit_templates(list(reversed(items))))
        with self.assertRaises(ValueError):fit_templates(items,9)
        with self.assertRaises(ValueError):groups({'supports':[{}]*361,'placements':[]},[])


if __name__=='__main__':unittest.main()
