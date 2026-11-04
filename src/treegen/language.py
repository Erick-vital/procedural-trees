"""F4: planes propuestos por Codex en el chat, inspeccionables y reproducibles."""
import copy
import hashlib
from pathlib import Path

from .blueprints import (ROOT, StrictValidator, _load, _rule, canonical_hash,
                         load_blueprint, resolve_blueprint, _schema, _validate)
from .runner import timestamp, write_json, execute_blueprint

VERSION = '1.0.0'
MAX_TREES = 30


def response_schema(blueprint):
    """Contrato derivado de la receta explícita, nunca de texto del modelo."""
    return {
        'type': 'object', 'additionalProperties': False,
        'required': ['profile', 'changes', 'explanation'],
        'properties': {
            'profile': {'type': 'string', 'enum': list(blueprint['profiles'])},
            'changes': {'type': 'array', 'maxItems': len(blueprint['editable_ranges']),
                        'items': {'type': 'object', 'additionalProperties': False,
                                  'required': ['path', 'value'], 'properties': {
                                      'path': {'type': 'string', 'enum': list(blueprint['editable_ranges'])},
                                      'value': {'type': 'number'}}}},
            'explanation': {'type': 'string', 'minLength': 1, 'maxLength': 4000}}}


def resolve_response(blueprint, seeds, response):
    _validate(StrictValidator(response_schema(blueprint)), response)
    overrides, seen = {}, set()
    for change in response['changes']:
        path, value = change['path'], change['value']
        if path in seen:
            raise ValueError(f'Parámetro duplicado: {path}')
        seen.add(path)
        _validate(StrictValidator(_rule(path, _schema(blueprint))), value)
        target = overrides
        parts = path.split('.')
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    instance = {'schema_version': blueprint['schema_version'], 'blueprint_id': blueprint['id'],
                'blueprint_version': blueprint['version'], 'profile': response['profile'],
                'seeds': copy.deepcopy(seeds), 'overrides': overrides}
    return instance, resolve_blueprint(blueprint, instance)


def plan_schema(blueprint):
    return {
        'type': 'object', 'additionalProperties': False,
        'required': ['version', 'request', 'origin', 'cases'],
        'properties': {
            'version': {'const': VERSION},
            'request': {'type': 'string', 'minLength': 1, 'maxLength': 8192},
            'origin': {'enum': ['codex-session', 'saved-response']},
            'cases': {'type': 'array', 'minItems': 1, 'maxItems': MAX_TREES,
                      'items': {'type': 'object', 'additionalProperties': False,
                                'required': ['id', 'seeds', 'proposal'], 'properties': {
                                    'id': {'type': 'string', 'pattern': '^[a-z][a-z0-9-]{0,63}$'},
                                    'seeds': {'type': 'object'},
                                    'proposal': response_schema(blueprint)}}}}}


def resolve_plan(blueprint, document):
    _validate(StrictValidator(plan_schema(blueprint)), document)
    if not document['request'].strip():
        raise ValueError('Solicitud vacía')
    cases, seen = [], set()
    for row in document['cases']:
        if row['id'] in seen:
            raise ValueError(f'Identificador repetido: {row["id"]}')
        seen.add(row['id'])
        instance, resolved = resolve_response(blueprint, row['seeds'], row['proposal'])
        cases.append({'id': row['id'], 'instance': instance,
                      'resolved_sha256': resolved['resolved_sha256']})
    return cases


def prepare_plan(blueprint, document, output):
    """Valida TODOS los ejemplares antes de Blender y congela entradas/procedencia."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {'version': VERSION, 'status': 'running', 'started_at': timestamp(),
              'workflow': 'codex-in-repository', 'independent_model_call': False}
    write_json(output / 'plan.json', report)
    try:
        blueprint = load_blueprint(blueprint) if isinstance(blueprint, (str, Path)) else blueprint
        document = _load(document) if isinstance(document, (str, Path)) else document
        write_json(output / 'blueprint.json', blueprint)
        write_json(output / 'request.json', document)
        cases = resolve_plan(blueprint, document)
        write_json(output / 'resolved.json', cases)
        report.update(status='completed', count=len(cases), origin=document['origin'],
                      origin_is_declared=True, blueprint_sha256=canonical_hash(blueprint),
                      request_sha256=canonical_hash(document), resolved_sha256=canonical_hash(cases))
    except Exception as exc:
        report.update(status='failed', error={'type': type(exc).__name__, 'message': str(exc)})
        raise
    finally:
        report['finished_at'] = timestamp()
        report['files_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in output.iterdir() if p.is_file() and p.name != 'plan.json'}
        report['sources_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in (Path(__file__), ROOT / 'src/treegen/blueprints.py')}
        write_json(output / 'plan.json', report)
    return report


def load_plan(directory):
    directory = Path(directory)
    report = _load(directory / 'plan.json')
    if report.get('status') != 'completed' or report.get('version') != VERSION:
        raise ValueError('Plan F4 no completado o versión desconocida')
    for name in ('blueprint.json', 'request.json', 'resolved.json'):
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != report['files_sha256'][name]:
            raise ValueError(f'Plan F4 alterado: {name}')
    blueprint, document = _load(directory / 'blueprint.json'), _load(directory / 'request.json')
    cases = resolve_plan(blueprint, document)
    if cases != _load(directory / 'resolved.json') or canonical_hash(cases) != report['resolved_sha256']:
        raise ValueError('Resolución F4 distinta de las entradas')
    if canonical_hash(blueprint) != report['blueprint_sha256'] or canonical_hash(document) != report['request_sha256']:
        raise ValueError('Entradas F4 distintas del manifiesto')
    return blueprint, document, cases


def execute_plan(directory, output, render=False, timeout=120):
    """Reproduce un plan congelado sin consultar ningún modelo; fallo detiene el lote."""
    blueprint, document, cases = load_plan(directory)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {'version': VERSION, 'status': 'running', 'started_at': timestamp(),
              'request_sha256': canonical_hash(document), 'cases': [],
              'triangle_limit': 6999, 'material_limit': 2, 'model_called': False}
    write_json(output / 'batch.json', report)
    try:
        for row in cases:
            case = {'id': row['id'], 'status': 'running', 'instance': row['instance']}
            report['cases'].append(case)
            write_json(output / 'batch.json', report)
            result = execute_blueprint(blueprint, row['instance'], output / row['id'], render, timeout)
            case.update(triangles=result['metrics']['triangles'], glb_sha256=result['glb_sha256'],
                        materials=len(result['metrics']['triangles_by_material']))
            if case['triangles'] > 6999 or case['materials'] > 2:
                raise ValueError(f'{row["id"]}: excede presupuesto F4 (6999 tris/dos materiales)')
            case['status'] = 'completed'
            write_json(output / 'batch.json', report)
        report['status'] = 'completed'
    except Exception as exc:
        if report['cases'] and report['cases'][-1]['status'] == 'running':
            report['cases'][-1]['status'] = 'failed'
        report.update(status='failed', error={'type': type(exc).__name__, 'message': str(exc)})
        raise
    finally:
        report['finished_at'] = timestamp()
        write_json(output / 'batch.json', report)
    return report
