"""API HTTP de loopback, cola acotada y un único trabajador Blender."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from queue import Queue, Full
import threading
import uuid

from .contracts import validate_spec
from .runner import execute, write_json


def make_server(jobs, port):
    jobs = Path(jobs).resolve()
    jobs.mkdir(parents=True, exist_ok=True)
    # Tras reiniciar no se presentan trabajos interrumpidos como activos.
    for p in jobs.glob('*/status.json'):
        status = json.loads(p.read_text())
        if status['status'] in ('queued', 'running'):
            status.update(status='failed', error='Servidor interrumpido; crear un trabajo nuevo')
            write_json(p, status)
    queue = Queue(maxsize=32)

    def worker():
        while True:
            item = queue.get()
            if item is None:
                queue.task_done()
                return
            job_id, spec, render = item
            folder = jobs / job_id
            write_json(folder / 'status.json', {'job_id': job_id, 'status': 'running'})
            try:
                execute(spec, folder / 'result', render=render, job_id=job_id)
                state = {'job_id': job_id, 'status': 'completed', 'result': f'/jobs/{job_id}/manifest.json'}
            except Exception as exc:
                state = {'job_id': job_id, 'status': 'failed', 'error': str(exc)}
            write_json(folder / 'status.json', state)
            queue.task_done()

    class Handler(BaseHTTPRequestHandler):
        def respond(self, code, value):
            data = json.dumps(value, allow_nan=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if self.path != '/jobs':
                return self.respond(404, {'error': 'Ruta desconocida'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 65536:
                    return self.respond(413, {'error': 'Cuerpo requerido; máximo 64 KiB'})
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict) or set(body) - {'spec', 'render'}:
                    raise ValueError('Campos admitidos: spec, render')
                validate_spec(body['spec'])
                render = body.get('render', True)
                if type(render) is not bool:
                    raise ValueError('render debe ser booleano')
                job_id = str(uuid.uuid4())
                folder = jobs / job_id
                folder.mkdir()
                write_json(folder / 'status.json', {'job_id': job_id, 'status': 'queued'})
                try:
                    queue.put_nowait((job_id, body['spec'], render))
                except Full:
                    write_json(folder / 'status.json', {'job_id': job_id, 'status': 'failed', 'error': 'Cola llena'})
                    return self.respond(503, {'error': 'Cola llena'})
                self.respond(202, {'job_id': job_id, 'status_url': f'/jobs/{job_id}'})
            except (ValueError, KeyError, TypeError) as exc:
                self.respond(400, {'error': str(exc)})

        def do_GET(self):
            parts = self.path.strip('/').split('/')
            if len(parts) not in (2, 3) or parts[0] != 'jobs':
                return self.respond(404, {'error': 'Ruta desconocida'})
            try:
                if str(uuid.UUID(parts[1])) != parts[1]:
                    raise ValueError('Id inválido')
            except ValueError:
                return self.respond(404, {'error': 'Id inválido'})
            folder = jobs / parts[1]
            filename = folder / 'status.json'
            if len(parts) == 3:
                if parts[2] != 'manifest.json':
                    return self.respond(404, {'error': 'Resultado desconocido'})
                filename = folder / 'result/manifest.json'
            if not filename.is_file():
                return self.respond(404, {'error': 'Trabajo o resultado no disponible'})
            self.respond(200, json.loads(filename.read_text()))

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return server


def serve(jobs, port=8765):
    server = make_server(jobs, port)
    print(f'API local: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
