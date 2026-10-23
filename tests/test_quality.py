import copy
import unittest
from treegen.quality import validate_q1


def case():
    primary = [{'channel':'Primary','radius_ratio_to_parent':.65,'inclination_final_deg':a} for a in (20,30,40,50)]
    secondary = [{'channel':'Secondary','radius_ratio_to_parent':.55} for _ in range(8)]
    return {'curves':primary+secondary, 'spec':{'parameters':{'primary_branches':4,'max_depth':2,'inclination_deg':60}},
            'summary':{'primary_azimuth_min_gap_deg':80,'primary_azimuth_max_gap_deg':100},'final_z_scale':.8}


class QualityTest(unittest.TestCase):
    def test_accept_coherent_structure(self):
        self.assertEqual(validate_q1(case())['secondary_count'],8)

    def test_reject_thickness_grouping_and_flatness(self):
        invalid=[]
        c=case();c['curves'][0]['radius_ratio_to_parent']=1.1;invalid.append(c)
        c=case();c['summary']['primary_azimuth_min_gap_deg']=.4;invalid.append(c)
        c=case()
        for p in c['curves'][:4]:p['inclination_final_deg']=70
        invalid.append(c)
        c=case();c['curves'].pop();invalid.append(c)
        for c in invalid:
            with self.assertRaises(ValueError):validate_q1(c)

    def test_q1b_requires_three_secondary_branches(self):
        for version in ('0.2.1','0.3.0','0.4.0','0.4.1'):
            c=case();c['spec']['algorithm_version']=version
            with self.assertRaises(ValueError):validate_q1(c)
            c['curves'] += [{'channel':'Secondary','radius_ratio_to_parent':.65} for _ in range(4)]
            self.assertEqual(validate_q1(c)['secondary_count'],12)
            c['curves'][-1]['radius_ratio_to_parent']=1
            with self.assertRaises(ValueError):validate_q1(c)
