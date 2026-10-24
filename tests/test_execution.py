"""Fallos persistidos y contrato HTTP sin lanzar Blender en pruebas unitarias."""
import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch, MagicMock
import subprocess
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from treegen.contracts import load_spec, ROOT
from treegen.runner import execute
from treegen.api import make_server


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'job'
        self.spec = load_spec(ROOT / 'presets/adulto.json')

    def test_invalid_spec_records_failure(self):
        self.spec['parameters']['height_m'] = -1
        with self.assertRaises(ValueError):
            execute(self.spec, self.path)
        self.assertEqual(json.loads((self.path / 'manifest.json').read_text())['status'], 'failed')

    def test_invalid_file_records_failure(self):
        bad = Path(self.temp.name) / 'bad.json'
        bad.write_text('{')
        with self.assertRaises(ValueError):
            execute(bad, self.path)
        self.assertEqual(json.loads((self.path / 'manifest.json').read_text())['status'], 'failed')

    def test_timeout_kills_process_group(self):
        process = MagicMock(pid=12345)
        process.wait.side_effect = [subprocess.TimeoutExpired('blender', .01), -9]
        with patch('treegen.runner.subprocess.Popen', return_value=process), patch('treegen.runner.os.killpg') as kill:
            with self.assertRaises(TimeoutError):
                execute(self.spec, self.path, timeout=.01)
        kill.assert_called_once()
        manifest = json.loads((self.path / 'manifest.json').read_text())
        self.assertEqual(manifest['error']['type'], 'TimeoutError')
        self.assertEqual(manifest['status'], 'failed')

    def test_export_failure_not_completed(self):
        with patch('treegen.runner.subprocess.Popen') as popen:
            popen.return_value.wait.return_value = 1
            with self.assertRaises(RuntimeError):
                execute(self.spec, self.path)
        self.assertEqual(json.loads((self.path / 'manifest.json').read_text())['status'], 'failed')
        with self.assertRaises(FileExistsError):
            execute(self.spec, self.path)

    def test_legacy_success_initializes_artifact_hashes(self):
        def start(*args, **kwargs):
            job = json.loads((self.path / 'input.json').read_text())
            # Forma del manifiesto histórico: sin files_sha256.
            (self.path / 'manifest.json').write_text(json.dumps({
                'status': 'completed', 'spec': self.spec, 'spec_sha256': job['spec_sha256'],
                'cameras': {}, 'sources_sha256': {}, 'metrics': {'triangles': 1}}))
            (self.path / 'tree.glb').write_bytes(b'exported-glb')
            (self.path / 'tree.blend').write_bytes(b'exported-blend')
            process = MagicMock()
            process.wait.return_value = 0
            return process
        with patch('treegen.runner.subprocess.Popen', side_effect=start), \
                patch('treegen.runner.validate_result', return_value={'triangles': 1}):
            result = execute(self.spec, self.path, render=False)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(set(result['files_sha256']), {'tree.glb', 'tree.blend'})
        self.assertTrue(all(len(value) == 64 for value in result['files_sha256'].values()))
        self.assertEqual(json.loads((self.path / 'manifest.json').read_text())['status'], 'completed')

    def test_api_async_and_invalid_input(self):
        release, entered = threading.Event(), threading.Event()
        def fake_execute(*args, **kwargs):
            entered.set()
            release.wait(5)
        with patch('treegen.api.execute', side_effect=fake_execute):
            server = make_server(Path(self.temp.name) / 'api', 0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f'http://127.0.0.1:{server.server_port}'
            try:
                request = Request(base + '/jobs', data=json.dumps({'spec': self.spec, 'render': False}).encode(),
                                  headers={'Content-Type': 'application/json'})
                with urlopen(request, timeout=2) as response:
                    self.assertEqual(response.status, 202)
                    job = json.load(response)
                self.assertTrue(entered.wait(2))
                state = json.load(urlopen(base + job['status_url'], timeout=2))
                self.assertEqual(state['status'], 'running')
                invalid = copy.deepcopy(self.spec)
                invalid['unknown'] = True
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(base + '/jobs', data=json.dumps({'spec': invalid}).encode()), timeout=2)
                self.assertEqual(error.exception.code, 400)
                error.exception.close()
            finally:
                release.set()
                server.shutdown()
                server.server_close()
                thread.join()
