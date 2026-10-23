import unittest
from treegen.seeds import derive_seed


class SeedsTest(unittest.TestCase):
    def test_stable_streams(self):
        self.assertEqual(derive_seed(29, 'structure'), 1824590334)
        self.assertEqual(derive_seed(29, 'foliage'), 228031302)
        self.assertNotEqual(derive_seed(29, 'structure'), derive_seed(30, 'structure'))
