import unittest
from PIL import Image, ImageChops
from treegen.season_atlas import compatible_pair, extend_rgb


class AtlasTests(unittest.TestCase):
    def test_padding_preserves_alpha_visible_rgb_and_stops_at_cell(self):
        im = Image.new('RGBA', (8, 4))
        im.putpixel((3, 1), (190, 30, 10, 255))
        im.putpixel((1, 1), (30, 80, 10, 1))
        out = extend_rgb(im, 4, 3)
        self.assertEqual(out.getchannel('A').tobytes(), im.getchannel('A').tobytes())
        self.assertEqual(out.getpixel((3,1)), im.getpixel((3,1)))
        self.assertEqual(out.getpixel((1,1)), im.getpixel((1,1)))
        self.assertEqual(out.getpixel((4,1)), (0,0,0,0))
        self.assertEqual(out.tobytes(), extend_rgb(im, 4, 3).tobytes())

    def test_radius_limit(self):
        im = Image.new('RGBA', (8,8)); im.putpixel((3,3), (150,80,20,255))
        out = extend_rgb(im, 8, 1)
        self.assertEqual(out.getpixel((2,2)), (150,80,20,0))
        self.assertEqual(out.getpixel((1,1)), (0,0,0,0))

    def test_pair_repairs_only_newly_exposed_transparent_rgb(self):
        s = Image.new('RGBA', (4,4)); a = s.copy()
        s.putpixel((1,1), (10,60,10,255)); s.putpixel((2,1), (20,60,10,128))
        a.putpixel((1,1), (150,80,20,255))
        summer, autumn = compatible_pair(s,a,4,2)
        self.assertEqual(summer.tobytes(), s.tobytes())
        self.assertEqual(autumn.getchannel('A').tobytes(), s.getchannel('A').tobytes())
        self.assertEqual(autumn.getpixel((1,1)), a.getpixel((1,1)))
        self.assertEqual(autumn.getpixel((2,1)), (150,80,20,128))
        self.assertEqual(a.getpixel((2,1)), (0,0,0,0))

    def test_black_paint_is_valid_coverage(self):
        s = Image.new('RGBA',(4,4),(0,0,0,0)); a = s.copy()
        s.putpixel((1,1),(10,50,10,255)); a.putpixel((2,1),(0,0,0,255))
        _, out = compatible_pair(s,a,4,2)
        self.assertEqual(out.getpixel((1,1)),(0,0,0,255))

    def test_uncovered_mask_and_bad_inputs_rejected(self):
        s = Image.new('RGBA',(4,4),(0,120,0,255)); a = Image.new('RGBA',(4,4))
        with self.assertRaises(ValueError): compatible_pair(s,a,4,2)
        for tile, radius in [(0,2),(3,2),(4,33),(4,-1),(True,2),(4,1.2)]:
            with self.assertRaises(ValueError): extend_rgb(s,tile,radius)
        with self.assertRaises(ValueError): compatible_pair(s,a.resize((2,2)),4,2)
        with self.assertRaises(ValueError): extend_rgb(s.convert('RGB'),4,2)
        with self.assertRaises(ValueError): extend_rgb(Image.new('RGBA',(100,100)),1,2)
        with self.assertRaises(ValueError): extend_rgb(Image.new('RGBA',(2049,1)),1,2)
