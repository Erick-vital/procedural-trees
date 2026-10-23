import unittest
from PIL import Image, ImageDraw
from treegen.foliage_molds_evaluation import compare_masks


class MoldProjectionTests(unittest.TestCase):
    def test_mask_coverage_counts_pixels_without_intensity_weighting(self):
        a = Image.new('1', (32, 32))
        b = Image.new('1', (32, 32))
        ImageDraw.Draw(a).rectangle((0, 0, 15, 15), fill=1)
        ImageDraw.Draw(b).rectangle((8, 0, 23, 15), fill=1)
        same = compare_masks({'front': a}, {'front': a})['front']
        shifted = compare_masks({'front': a}, {'front': b})['front']
        self.assertEqual(same['reference_pixels'], 256)
        self.assertEqual(same['q3_coverage'], 1)
        self.assertEqual(shifted['q3_coverage'], .5)
        self.assertAlmostEqual(shifted['iou'], 1/3)
        self.assertEqual(shifted['outside_q3_pixels'], 128)
