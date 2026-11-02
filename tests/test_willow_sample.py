"""Anclajes superiores, caída, límites y recursos de la rama de sauce."""
import copy
import hashlib
import json
import math
from pathlib import Path
import unittest

from PIL import Image

from treegen.willow_sample import build_sample, hanging_group, validate_atlas
from treegen.pine import cross, sub, point_on

ASSETS = Path(__file__).resolve().parents[1]/'assets/sauce-pintado/v0.1.0'
ATLAS = json.loads((ASSETS/'manifest.json').read_text())


class WillowSampleTests(unittest.TestCase):
    def test_repeat_and_seed_separation(self):
        data = build_sample(ATLAS)
        self.assertEqual(data, build_sample(ATLAS))
        repaint = build_sample(ATLAS, paint_seed=9)
        self.assertEqual(data['wood'], repaint['wood'])
        self.assertEqual([g['origin_m'] for g in data['groups']], [g['origin_m'] for g in repaint['groups']])
        self.assertEqual([g['length_m'] for g in data['groups']], [g['length_m'] for g in repaint['groups']])
        self.assertNotEqual(data['groups'], repaint['groups'])
        self.assertNotEqual(data['wood'], build_sample(ATLAS, seed=7101)['wood'])

    def test_contacts_and_downward_growth(self):
        data = build_sample(ATLAS)
        wood = {b['id']: b for b in data['wood']}
        for b in data['wood'][1:]:
            parent = wood[b['parent_id']]
            # Anclaje de secundaria sobre el eje de la primaria.
            self.assertLess(min(math.dist(b['points_m'][0], point_on(parent, t))
                                for t in (.20, .28, .36, .44, .52, .60, .68, .76, .84, .92)), 1e-12)
        for g in data['groups']:
            self.assertAlmostEqual(math.dist(g['origin_m'], wood[g['support_id']]['points_m'][-1]), .012)
            self.assertLess(g['axis'][2], -.65)
            region = ATLAS['regions'][g['atlas_variant']]
            width, height = ATLAS['atlas_size']
            ax, ay = region['anchor']
            for offset in range(0, 12, 4):
                p0, p1, _, p3 = g['vertices'][offset:offset+4]
                u0, v0 = g['uv'][offset]; u1, _ = g['uv'][offset+1]; _, v3 = g['uv'][offset+3]
                a = (ax/width-u0)/(u1-u0)
                b = ((1-ay/height)-v0)/(v3-v0)
                anchor = [p0[j]+a*(p1[j]-p0[j])+b*(p3[j]-p0[j]) for j in range(3)]
                self.assertLess(math.dist(anchor, g['origin_m']), 1e-12)
                # Avanzar hacia el extremo pintado hace descender cada plano.
                self.assertLess(p3[2], p0[2])

    def test_budget_uv_and_valid_geometry(self):
        data = build_sample(ATLAS)
        meshes = [b['mesh'] for b in data['wood']]+data['groups']
        self.assertEqual(data['triangles'], sum(len(m['polygons']) for m in meshes))
        self.assertLess(data['triangles'], 7000)
        for g in data['groups']:
            self.assertEqual(len(g['polygons']), 6)
            self.assertTrue(all(0 < c < 1 for uv in g['uv'] for c in uv))
            for face in g['polygons'][::2]:
                a, b, c = [g['vertices'][j] for j in face]
                n = cross(sub(b, a), sub(c, a))
                self.assertGreater(abs(sum(x*y for x, y in zip(n, g['axis']))), .01)
        for mesh in meshes:
            self.assertTrue(all(math.isfinite(v) for p in mesh['vertices'] for v in p))
            for a, b, c in mesh['polygons']:
                n = cross(sub(mesh['vertices'][b], mesh['vertices'][a]), sub(mesh['vertices'][c], mesh['vertices'][a]))
                self.assertGreater(sum(v*v for v in n), 1e-14)

    def test_resources_match_measured_anchors(self):
        for name, record in ATLAS['files'].items():
            self.assertEqual(hashlib.sha256((ASSETS/name).read_bytes()).hexdigest(), record['sha256'])
            with Image.open(ASSETS/name) as image:
                self.assertEqual(list(image.size), record['size'])
                self.assertLessEqual(max(image.size), 2048)
        with Image.open(ASSETS/'foliage.png') as image:
            self.assertEqual(image.mode, 'RGBA')
            alpha = image.getchannel('A')
            self.assertEqual(alpha.getextrema(), (0, 255))
            for region in ATLAS['regions']:
                x, y = region['anchor']
                self.assertGreaterEqual(alpha.getpixel((int(x), int(y))), 128)
                x0, y0, x1, y1 = region['box']
                for x, y in ((x0, y0), (x1-1, y0), (x0, y1-1), (x1-1, y1-1)):
                    self.assertLess(alpha.getpixel((x, y)), 128)

    def test_reject_invalid_inputs(self):
        for seed in (-1, True, 1.5, 2147483648):
            with self.assertRaises(ValueError):
                build_sample(ATLAS, seed=seed)
            with self.assertRaises(ValueError):
                build_sample(ATLAS, paint_seed=seed)
        for key, value in [('atlas_size', [4096, 1254]), ('regions', []), ('version', 'other')]:
            bad = {**ATLAS, key: value}
            with self.assertRaises(ValueError):
                validate_atlas(bad)
        for key, value in [('anchor', [1, float('nan')]), ('tip_y', 1), ('box', [-1, 0, 500, 620])]:
            bad = copy.deepcopy(ATLAS); bad['regions'][0][key] = value
            with self.assertRaises(ValueError):
                validate_atlas(bad)
        for axis, length in (([0, 0, 0], 1), ([0, 0, -1], float('nan')), ([0, 0, -1], 10)):
            with self.assertRaises(ValueError):
                hanging_group([0, 0, 0], axis, length, ATLAS['regions'][0], ATLAS['atlas_size'])
