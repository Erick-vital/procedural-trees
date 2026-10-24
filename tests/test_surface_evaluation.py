"""Distancias para contacto: interiores, bordes y caras largas/estrechas."""
import math
import unittest

from treegen.surface_evaluation import point_triangle_distance


class SurfaceDistanceTests(unittest.TestCase):
    def test_plane_and_edges_have_known_distances(self):
        triangle = ((0,0,0), (2,0,0), (0,2,0))
        self.assertAlmostEqual(point_triangle_distance((.5,.5,.001), *triangle), .001)
        self.assertAlmostEqual(point_triangle_distance((2,2,0), *triangle), math.sqrt(2))
        self.assertAlmostEqual(point_triangle_distance((-1,0,0), *triangle), 1)

    def test_thin_translated_triangle_keeps_contact_and_separation(self):
        a,b,c = (10.,-3.,20.),(10.+1e-6,-3.,20.),(10.,-3.,30.)
        p = (10.+2e-7,-3.,22.)
        self.assertLess(point_triangle_distance(p,a,b,c), 1e-12)
        self.assertAlmostEqual(point_triangle_distance((p[0],p[1]+.001,p[2]),a,b,c), .001)
        self.assertAlmostEqual(point_triangle_distance((p[0],p[1]-.001,p[2]),a,c,b), .001)

    def test_degenerate_triangle_uses_real_segments(self):
        self.assertAlmostEqual(point_triangle_distance((.5,1,0),(0,0,0),(1,0,0),(2,0,0)),1)
        self.assertAlmostEqual(point_triangle_distance((0,0,1),(0,0,0),(0,0,0),(0,0,0)),1)
