import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

from treegen.foliage import (cross, digest, dot, load_unit, placements, support_frames,
                             validate_unit)

ROOT = Path(__file__).resolve().parents[1]


class FoliageTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_unit(ROOT/'presets/foliage-unit.json')

    def test_determinism_frames_and_insertion(self):
        leaves = placements(self.spec)
        self.assertEqual(digest(leaves), digest(placements(copy.deepcopy(self.spec))))
        self.assertEqual(len(leaves), 7)
        for leaf in leaves:
            x, y, z = leaf['axes']
            self.assertAlmostEqual(dot(x, y), 0)
            self.assertAlmostEqual(dot(x, z), 0)
            self.assertAlmostEqual(dot(y, z), 0)
            for axis in (x, y, z):
                self.assertAlmostEqual(dot(axis, axis), 1)
            self.assertAlmostEqual(dot(cross(x, y), z), 1)
            self.assertAlmostEqual(leaf['origin_m'][2], leaf['support_t']*.65)
        # Una edición de forma no desplaza ni rota hojas supervivientes.
        self.spec['parameters'].update(variant='diamond', fold_deg=0)
        for before, after in zip(leaves, placements(self.spec)):
            for key in ('id', 'origin_m', 'axes', 'length_m'):
                self.assertEqual(before[key], after[key])

    def test_parameter_separation_and_seed(self):
        before = placements(self.spec)
        for key, value in [('leaf_length_m', .3), ('width_ratio', .9), ('fold_deg', 40),
                           ('inclination_deg', 100), ('azimuth_step_deg', 90), ('spacing_m', .06),
                           ('roll_deg', -35), ('jitter_deg', 0), ('scale_jitter', 0)]:
            changed = copy.deepcopy(self.spec)
            changed['parameters'][key] = value
            after = placements(changed)
            self.assertNotEqual(digest(before), digest(after), key)
            if key != 'spacing_m':
                self.assertEqual([v['origin_m'] for v in before], [v['origin_m'] for v in after])
        self.spec['seed'] += 1
        after = placements(self.spec)
        self.assertNotEqual(digest(before), digest(after))
        self.assertEqual([v['origin_m'] for v in before], [v['origin_m'] for v in after])

    def test_invalid_and_bounded_work(self):
        bad = []
        for key, value in [('leaf_length_m', float('nan')), ('roll_deg', float('inf')),
                           ('spacing_m', 0), ('variant', 'sphere'), ('jitter_deg', True)]:
            spec = copy.deepcopy(self.spec)
            spec['parameters'][key] = value
            bad.append(spec)
        for key, value in [('seed', True), ('extra', 1)]:
            spec = copy.deepcopy(self.spec)
            spec[key] = value
            bad.append(spec)
        for points in ([[0, 0, 0], [0, 0, 0]], [[0, 0, 0], [0, 0, 3]],
                       [[0, 0, 0], [0, 0, 1], [0, 0, 0]],
                       [[0, 0, 0], [float('nan'), 0, 1]]):
            spec = copy.deepcopy(self.spec)
            spec['support']['points_m'] = points
            bad.append(spec)
        spec = copy.deepcopy(self.spec)
        spec['support']['points_m'][-1][-1] = 1.1
        spec['parameters']['spacing_m'] = .03
        bad.append(spec)  # >32 hojas, antes de construir malla.
        for spec in bad:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                validate_unit(spec)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'bad.json'
            path.write_text('{"seed": 1, "seed": 2}')
            with self.assertRaises(ValueError):
                load_unit(path)

    def test_transported_frame_crosses_axis_tie_without_flip(self):
        # Una selección independiente del eje global saltaría cerca de x=y.
        points = [(0, 0, 0), (.2, .19, .3), (.39, .39, .6), (.57, .60, .9)]
        frames = support_frames(points)
        for previous, current in zip(frames, frames[1:]):
            self.assertGreater(dot(previous[1], current[1]), .99)
        self.spec['support']['points_m'] = [list(p) for p in points]
        self.assertTrue(all(math.isfinite(x) for p in placements(self.spec) for axis in p['axes'] for x in axis))


if __name__ == '__main__':
    unittest.main()
