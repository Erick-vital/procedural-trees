"""B2: catálogo, fallos y procedencia del ejecutor compartido, sin Blender."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from treegen.blueprints import ROOT, load_blueprint, load_instance, registered_blueprints, resolve_blueprint
from treegen.evaluation import validate_result
from treegen.runner import execute_blueprint

BLUEPRINT = ROOT / 'blueprints/roble_copa_ancha/1.0.0.json'
INSTANCE = ROOT / 'presets/blueprints/roble-copa-ancha-viejo-09.json'


class BlueprintExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'job'
        self.blueprint = load_blueprint(BLUEPRINT)
        self.instance = load_instance(INSTANCE)

    def test_registered_first_blueprint_selects_approved_reference(self):
        entries = registered_blueprints()
        self.assertIn(('roble_copa_ancha', '1.0.0'), [(e['id'], e['version']) for e in entries])
        resolved = resolve_blueprint(self.blueprint, self.instance)
        baseline = json.loads((ROOT / 'docs/evidence/blueprints/b0/reference-lock.json').read_text())
        self.assertEqual(resolved['base_spec'], baseline['base_spec'])
        self.assertEqual(resolved['canopy_spec'], baseline['canopy_spec'])
        self.assertEqual(list(self.blueprint['profiles']), ['viejo_referencia'])

    def test_invalid_instance_fails_before_blender_and_persists_failure(self):
        self.instance['overrides'] = {'base': {'height_m': 10}}
        with patch('treegen.runner.subprocess.Popen') as process:
            with self.assertRaises(ValueError):
                execute_blueprint(self.blueprint, self.instance, self.output)
            process.assert_not_called()
        self.assertEqual(json.loads((self.output / 'manifest.json').read_text())['status'], 'failed')

    def test_timeout_cap_and_failure_keep_frozen_resolution(self):
        self.blueprint['limits']['generation_seconds'] = 3
        process = MagicMock(pid=12345)
        process.wait.side_effect = [subprocess.TimeoutExpired('blender', 3), -9]
        with patch('treegen.runner.subprocess.Popen', return_value=process) as popen, \
                patch('treegen.runner.os.killpg') as kill:
            with self.assertRaises(TimeoutError):
                execute_blueprint(self.blueprint, self.instance, self.output, timeout=60)
        self.assertEqual(process.wait.call_args_list[0].kwargs['timeout'], 3)
        kill.assert_called_once()
        self.assertIn('generate_blueprint.py', str(popen.call_args.args[0]))
        manifest = json.loads((self.output / 'manifest.json').read_text())
        self.assertEqual(manifest['kind'], 'blueprint')
        self.assertEqual(manifest['resolved_blueprint']['instance_request'], self.instance)
        self.assertEqual(manifest['error']['type'], 'TimeoutError')
        with self.assertRaises(FileExistsError):
            execute_blueprint(self.blueprint, self.instance, self.output)

    def test_blender_failure_does_not_complete_job(self):
        with patch('treegen.runner.subprocess.Popen') as popen:
            popen.return_value.wait.return_value = 1
            with self.assertRaises(RuntimeError):
                execute_blueprint(BLUEPRINT, INSTANCE, self.output)
        manifest = json.loads((self.output / 'manifest.json').read_text())
        self.assertEqual(manifest['status'], 'failed')
        self.assertEqual(manifest['resolved_blueprint']['blueprint_id'], 'roble_copa_ancha')

    def test_revalidation_rejects_mutated_resolution_before_reading_glb(self):
        resolved = resolve_blueprint(self.blueprint, self.instance)
        manifest = {'status': 'completed', 'kind': 'blueprint', 'resolved_blueprint': resolved,
                    'spec': resolved['base_spec'], 'canopy_spec': resolved['canopy_spec'],
                    'base_seeds': resolved['base_seeds']}
        self.output.mkdir()
        manifest['resolved_blueprint']['parameters']['canopy']['group_count'] = 100
        (self.output / 'manifest.json').write_text(json.dumps(manifest))
        with patch('treegen.evaluation.validate_glb') as validate:
            with self.assertRaisesRegex(ValueError, 'alterada'):
                validate_result(self.output)
            validate.assert_not_called()

    def test_blueprint_validation_selects_explicit_budget_only_for_blueprint(self):
        resolved = resolve_blueprint(self.blueprint, self.instance)
        manifest = {'status': 'completed', 'kind': 'blueprint', 'resolved_blueprint': resolved,
                    'spec': resolved['base_spec'], 'canopy_spec': resolved['canopy_spec'],
                    'base_seeds': resolved['base_seeds'], 'metrics': {
                        'triangles': 10572, 'triangles_by_material': {'Oak_Bark': 5292, 'RF1_Leaf': 3168, 'RF2_Twig': 2112},
                        'bounds_blender': [[-1, -1, 0], [1, 1, 9]]}, 'glb_sha256': 'test'}
        report = {'triangles': 10572, 'materials': manifest['metrics']['triangles_by_material'],
                  'bounds_gltf': [[-1, 0, -1], [1, 9, 1]], 'glb_sha256': 'test'}
        self.output.mkdir()
        (self.output / 'manifest.json').write_text(json.dumps(manifest))
        with patch('treegen.evaluation.validate_glb', return_value=report) as check, \
                patch('treegen.foliage_twigs_evaluation.inspect_twigs_glb', return_value=report):
            validate_result(self.output)
            self.assertEqual(check.call_args.kwargs['triangle_limit'], 12500)
            manifest.pop('kind')
            (self.output / 'manifest.json').write_text(json.dumps(manifest))
            validate_result(self.output)
            self.assertEqual(check.call_args.kwargs['triangle_limit'], 10000)
