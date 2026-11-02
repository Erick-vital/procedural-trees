"""Contratos geométricos de la muestra aislada, sin Blender."""
import json
import math
from pathlib import Path
import unittest

from treegen.birch_sample import build_sample, crossed_group
from treegen.pine import cross, sub

ATLAS = json.loads((Path(__file__).resolve().parents[1]/'assets/abedul-pintado/v0.1.0/manifest.json').read_text())


class BirchSampleTests(unittest.TestCase):
    def test_repeat_and_paint_do_not_move_wood(self):
        first = build_sample(ATLAS)
        self.assertEqual(first, build_sample(ATLAS))
        self.assertEqual(first['wood'], build_sample(ATLAS, paint_seed=1)['wood'])

    def test_contacts_budget_and_non_degenerate(self):
        data = build_sample(ATLAS)
        wood = {b['id']: b for b in data['wood']}
        self.assertLess(data['triangles'], 7000)
        for group in data['groups']:
            self.assertAlmostEqual(math.dist(group['origin_m'], wood[group['support_id']]['points_m'][-1]), .012)
            self.assertEqual(len(group['polygons']), 6)
            self.assertTrue(all(0 <= c <= 1 for uv in group['uv'] for c in uv))
            for face in group['polygons'][::2]:
                a, b, c = [group['vertices'][j] for j in face]
                normal = cross(sub(b, a), sub(c, a))
                # Área proyectada no nula desde el eje de la ramilla.
                self.assertGreater(abs(sum(x*y for x, y in zip(normal, group['axis']))), .01)
        for mesh in [b['mesh'] for b in data['wood']]+data['groups']:
            for a, b, c in mesh['polygons']:
                area = cross(sub(mesh['vertices'][b], mesh['vertices'][a]), sub(mesh['vertices'][c], mesh['vertices'][a]))
                self.assertGreater(sum(v*v for v in area), 1e-14)

    def test_reject_bad_inputs(self):
        for seed in (-1, True, 1.5, 2147483648):
            with self.assertRaises(ValueError):
                build_sample(ATLAS, seed=seed)
        for axis, length in (([0, 0, 0], .5), ([1, 0, 0], float('nan')), ([1, 0, 0], 20)):
            with self.assertRaises(ValueError):
                crossed_group([0, 0, 0], axis, length, ATLAS['regions'][0], ATLAS['atlas_size'])
