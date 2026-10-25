"""RF5 conserva la cohorte Q3 completa y evita ajustes por ejemplar."""
import copy
import json
import sys
import unittest

from treegen.blueprints import ROOT, load_blueprint

sys.path.insert(0, str(ROOT / 'scripts'))
from verify_rf5 import validate_matrix


class RF5MatrixTests(unittest.TestCase):
    def setUp(self):
        self.matrix = json.loads((ROOT / 'configs/verification/rf5-v1.json').read_text())
        self.blueprint = load_blueprint(ROOT / self.matrix['blueprint'])
        self.q3 = json.loads((ROOT / 'presets/q3-cases.json').read_text())

    def test_complete_q3_cohort_is_accepted(self):
        validate_matrix(self.matrix, self.blueprint, self.q3)

    def test_omitted_or_duplicated_case_is_rejected(self):
        for duplicate in (False, True):
            altered = copy.deepcopy(self.matrix)
            altered['cases'].pop()
            if duplicate:
                altered['cases'].append(copy.deepcopy(altered['cases'][0]))
            with self.assertRaises(ValueError):
                validate_matrix(altered, self.blueprint, self.q3)

    def test_individual_tuning_and_changed_seeds_are_rejected(self):
        for changes in ({'overrides': {'canopy': {'leaf_length_m': .3}}},
                        {'seeds': {'base': 9999, 'canopy': 17}},
                        {'seeds': {'base': 1000, 'canopy': 18}}):
            altered = copy.deepcopy(self.matrix)
            altered['cases'][0]['instance'].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_matrix(altered, self.blueprint, self.q3)
