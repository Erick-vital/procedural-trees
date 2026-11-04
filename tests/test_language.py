"""F4: contratos, lotes, trazabilidad y fallos antes de generar geometría."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from treegen.blueprints import ROOT, load_blueprint, canonical_hash
from treegen.language import prepare_plan, load_plan, resolve_plan, execute_plan


class LanguageTests(unittest.TestCase):
    def setUp(self):
        self.blueprint = load_blueprint(ROOT / 'blueprints/roble_copa_ancha/2.2.0.json')
        self.request = json.loads((ROOT / 'configs/language/f4-responses-v1.json').read_text())
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)

    def test_six_responses_select_parameters_without_mutating_recipe(self):
        before = canonical_hash(self.blueprint)
        rows = resolve_plan(self.blueprint, self.request)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]['instance']['profile'], 'joven')
        self.assertEqual(rows[3]['instance']['overrides']['canopy']['group_count'], 300)
        self.assertEqual(canonical_hash(self.blueprint), before)
        self.assertEqual(rows[2]['instance']['seeds'], self.request['cases'][2]['seeds'])

    def test_ten_trees_roundtrip_and_replay_are_exact(self):
        template = self.request['cases'][0]
        self.request['cases'] = []
        for i in range(10):
            row = copy.deepcopy(template)
            row.update(id=f'joven-{i:02}', seeds={**row['seeds'], 'base': 1000 + i})
            self.request['cases'].append(row)
        report = prepare_plan(self.blueprint, self.request, self.out / 'plan')
        blueprint, document, cases = load_plan(self.out / 'plan')
        self.assertEqual(report['count'], 10)
        self.assertFalse(report['independent_model_call'])
        self.assertEqual(cases, resolve_plan(blueprint, document))
        document['origin'] = 'saved-response'
        replay = prepare_plan(blueprint, document, self.out / 'replay')
        self.assertEqual(report['resolved_sha256'], replay['resolved_sha256'])
        with self.assertRaises(FileExistsError):
            prepare_plan(blueprint, document, self.out / 'plan')

    def test_invalid_proposals_fail_before_blender(self):
        mutations = [
            lambda d: d.update(provider='external'),
            lambda d: d['cases'][0].update(id='../escape'),
            lambda d: d['cases'].append(copy.deepcopy(d['cases'][0])),
            lambda d: d['cases'][0]['seeds'].update(base=True),
            lambda d: d['cases'][0]['seeds'].update(secret=1),
            lambda d: d['cases'][0]['proposal'].update(profile='missing'),
            lambda d: d['cases'][0]['proposal'].update(code='print(1)'),
            lambda d: d['cases'][0]['proposal'].update(changes=[{'path': 'base.height_m', 'value': 100}]),
            lambda d: d['cases'][0]['proposal'].update(changes=[{'path': 'base.primary_branches', 'value': 4.5}]),
            lambda d: d['cases'][0]['proposal'].update(changes=[{'path': 'base.height_m', 'value': True}]),
            lambda d: d['cases'][0]['proposal'].update(changes=[{'path': 'base.height_m', 'value': float('nan')}]),
            lambda d: d['cases'][0]['proposal'].update(changes=[{'path': 'canopy.layout_leaf_length_m', 'value': .5}]),
            lambda d: d['cases'][0]['proposal'].update(changes=[{'path': 'base.height_m', 'value': 5}] * 2),
            lambda d: d.update(cases=[]),
            lambda d: d.update(cases=d['cases'] * 6),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                document = copy.deepcopy(self.request)
                mutate(document)
                with patch('treegen.language.execute_blueprint') as generate:
                    with self.assertRaises(ValueError):
                        resolve_plan(self.blueprint, document)
                    generate.assert_not_called()

    def test_all_cases_checked_before_any_generation(self):
        self.request['cases'][-1]['proposal']['changes'][0]['value'] = -1
        with self.assertRaises(ValueError):
            prepare_plan(self.blueprint, self.request, self.out / 'bad')
        self.assertEqual(json.loads((self.out / 'bad/plan.json').read_text())['status'], 'failed')
        self.assertFalse((self.out / 'bad/resolved.json').exists())

    def test_tampering_prevents_generation(self):
        prepare_plan(self.blueprint, self.request, self.out / 'plan')
        p = self.out / 'plan/request.json'
        data = json.loads(p.read_text())
        data['cases'][0]['seeds']['base'] = 10
        p.write_text(json.dumps(data))
        with patch('treegen.language.execute_blueprint') as generate:
            with self.assertRaisesRegex(ValueError, 'alterado'):
                execute_plan(self.out / 'plan', self.out / 'batch')
            generate.assert_not_called()
        self.assertFalse((self.out / 'batch').exists())

    def test_recomputed_file_hash_cannot_hide_stale_resolution(self):
        prepare_plan(self.blueprint, self.request, self.out / 'plan')
        p = self.out / 'plan/resolved.json'
        rows = json.loads(p.read_text())
        rows[0]['instance']['seeds']['base'] = 10
        p.write_text(json.dumps(rows))
        m = self.out / 'plan/plan.json'
        report = json.loads(m.read_text())
        report['files_sha256']['resolved.json'] = hashlib.sha256(p.read_bytes()).hexdigest()
        m.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'Resolución'):
            load_plan(self.out / 'plan')

    def test_budget_failure_is_persisted_and_stops_batch(self):
        prepare_plan(self.blueprint, self.request, self.out / 'plan')
        result = {'metrics': {'triangles': 7000, 'triangles_by_material': {'bark': 1, 'leaf': 1}},
                  'glb_sha256': 'test'}
        with patch('treegen.language.execute_blueprint', return_value=result) as generate:
            with self.assertRaisesRegex(ValueError, 'presupuesto F4'):
                execute_plan(self.out / 'plan', self.out / 'batch')
        self.assertEqual(generate.call_count, 1)
        report = json.loads((self.out / 'batch/batch.json').read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['cases'][0]['status'], 'failed')
        self.assertFalse(report['model_called'])

    def test_duplicate_json_keys_and_oversized_input_are_rejected(self):
        p = self.out / 'bad.json'
        for content in ('{"version":"1.0.0","version":"1.0.0"}', ' ' * 65537):
            p.write_text(content)
            with self.assertRaises(ValueError):
                prepare_plan(self.blueprint, p, self.out / f'bad-{len(content)}')


if __name__ == '__main__':
    unittest.main()
