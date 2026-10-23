import unittest
from treegen.crown import measure_crown


class CrownTests(unittest.TestCase):
    def test_overlapping_components_remain_separate_and_wood_hash_isolated(self):
        vertices = [(0,0,0), (1,0,0), (0,1,2), (0,0,1), (1,0,1), (0,1,1)]
        triangles = [('Oak_Bark', (0,1,2)), ('Oak_Leaves', (3,4,5))]
        first = measure_crown(vertices, triangles, 2)
        vertices += vertices[3:]
        triangles += [('Oak_Leaves', (6,7,8))]
        second = measure_crown(vertices, triangles, 2)
        self.assertEqual(second['leaf_mass_count'], 2)
        self.assertEqual(sum(second['center_height_bins']), 2)
        self.assertEqual(first['wood_geometry_sha256'], second['wood_geometry_sha256'])
        vertices[2] = (0,1,3)
        changed = measure_crown(vertices, triangles, 3)
        self.assertNotEqual(second['wood_geometry_sha256'], changed['wood_geometry_sha256'])
        self.assertEqual(second['wood_xy_sha256'], changed['wood_xy_sha256'])

    def test_bare_tree_and_invalid_basis(self):
        vertices = [(0,0,0), (1,0,0), (0,0,2)]
        result = measure_crown(vertices, [('Oak_Bark', (0,1,2))], 2)
        self.assertEqual(result['leaf_mass_count'], 0)
        self.assertIsNone(result['leaf_bounds_blender'])
        for triangles, height in [([], 2), ([('Oak_Bark', (0,1,2))], 0)]:
            with self.assertRaises(ValueError):measure_crown(vertices, triangles, height)

    def test_mass_size_variation_ignores_group_translation(self):
        wood=[(0,0,0),(1,0,0),(0,0,2)]
        leaf=[(0,0,1),(1,0,1),(0,1,1)]
        vertices=wood+leaf+[(x+20,y,z) for x,y,z in leaf]
        triangles=[('Oak_Bark',(0,1,2)),('Oak_Leaves',(3,4,5)),('Oak_Leaves',(6,7,8))]
        result=measure_crown(vertices,triangles,2)
        self.assertEqual(result['mass_bbox_diagonal']['coefficient_of_variation'],0)
        self.assertEqual(result['mass_triangle_histogram'],{'1':2})
        vertices[7]=(23,0,1);vertices[8]=(20,3,1)
        changed=measure_crown(vertices,triangles,2)
        self.assertAlmostEqual(changed['mass_bbox_diagonal']['coefficient_of_variation'],.5)
