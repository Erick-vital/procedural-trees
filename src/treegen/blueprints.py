"""B1: contratos y resolución de recetas; no ejecuta Blender ni carga plugins."""
import copy
import hashlib
import json
import math
from pathlib import Path
from types import MappingProxyType

from jsonschema import Draft202012Validator
from jsonschema.validators import extend

from .contracts import ROOT, validate_spec
from .foliage_canopy import validate_canopy
from .seeds import derive_seed

MAX_DOCUMENT_BYTES = 65536
SCHEMA = json.loads((ROOT / 'schemas/tree-blueprint.schema.json').read_text())
INSTANCE_SCHEMA = json.loads((ROOT / 'schemas/tree-instance.schema.json').read_text())
PINE_SCHEMA = json.loads((ROOT / 'schemas/tree-blueprint-pine.schema.json').read_text())
PINE_INSTANCE_SCHEMA = json.loads((ROOT / 'schemas/tree-instance-pine.schema.json').read_text())
StrictValidator = extend(Draft202012Validator, type_checker=Draft202012Validator.TYPE_CHECKER.redefine(
    'integer', lambda checker, value: type(value) is int))
VALIDATOR = StrictValidator(SCHEMA)
INSTANCE_VALIDATOR = StrictValidator(INSTANCE_SCHEMA)
PARAMETERS_VALIDATOR = StrictValidator(SCHEMA['$defs']['parameters'])


def _schema(document):
    return PINE_SCHEMA if document.get('schema_version') == '1.1' else SCHEMA


def _instance_validator(document):
    return StrictValidator(PINE_INSTANCE_SCHEMA) if document.get('schema_version') == '1.1' else INSTANCE_VALIDATOR

# Identificadores de capacidades, no rutas de importación ni código desde JSON.
COMPONENTS = MappingProxyType({
    'base': ('oak_geometry_nodes@0.4.0', 'pine-whorls@0.1.0', 'pine-whorls@0.2.0'),
    'distribution': ('foliage-canopy@0.1.0', 'foliage-canopy@0.1.1', 'pine-distal@0.1.0'),
    'representation': ('rf3-diamond-six@0.1.0', 'pine-needle-pairs@0.1.0'),
})


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _finite(value):
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    return type(value) is not float or math.isfinite(value)


def _validate(validator, value):
    if not _finite(value):
        raise ValueError('Valores no finitos en la receta o el ejemplar')
    error = next(validator.iter_errors(value), None)
    if error:
        raise ValueError(f'{list(error.path)}: {error.message}')


def _load(path):
    # Leer como máximo el límite + 1, también si el archivo cambia de tamaño.
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_DOCUMENT_BYTES + 1)
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise ValueError('Documento mayor de 64 KiB')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Campo repetido: {key}')
            result[key] = value
        return result

    def invalid(value):
        raise ValueError(f'Constante JSON inválida: {value}')

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError('Documento JSON inválido') from exc


def _leaves(value, prefix=''):
    for key, item in value.items():
        path = f'{prefix}.{key}' if prefix else key
        if isinstance(item, dict):
            yield from _leaves(item, path)
        else:
            yield path, item


def _rule(path, schema=SCHEMA):
    rule = schema['$defs']['parameters']
    for part in path.split('.'):
        rule = rule['properties'][part]
    return rule


def _in_range(value, interval):
    return interval['minimum'] <= value <= interval['maximum']


def _patch(parameters, overrides, ranges):
    result = copy.deepcopy(parameters)
    for path, value in _leaves(overrides):
        if path not in ranges:
            raise ValueError(f'Parámetro fijo; cambio no permitido: {path}')
        if not _in_range(value, ranges[path]):
            raise ValueError(f'Cambio fuera del rango permitido: {path}')
        target = result
        parts = path.split('.')
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = value
    return result


def _check_parameters(parameters, blueprint):
    if blueprint['schema_version'] == '1.1':
        _validate(StrictValidator(PINE_SCHEMA['$defs']['parameters']), parameters)
        from .pine import check_parameters
        for path, value in _leaves(parameters):
            if path in blueprint['editable_ranges'] and not _in_range(value, blueprint['editable_ranges'][path]):
                raise ValueError(f'Valor fuera del rango declarado: {path}')
        return check_parameters(parameters, blueprint['limits'])
    _validate(PARAMETERS_VALIDATOR, parameters)
    for path, value in _leaves(parameters):
        interval = blueprint['editable_ranges'].get(path)
        if interval and not _in_range(value, interval):
            raise ValueError(f'Valor fuera del rango declarado: {path}')
    base, canopy = parameters['base'], parameters['canopy']
    # RF3 necesita moldes, una región ocupada y >=24 grupos. Copa vacía no
    # soportada en esta versión; no reinterpretar el cero de versiones antiguas.
    if math.floor(4 * base['foliage_density'] + .5) == 0:
        raise ValueError('RF3 requiere moldes Q3: foliage_density debe ser al menos 0.125')
    if sum(canopy['region_weights'].values()) <= 0:
        raise ValueError('RF3 requiere al menos una región ocupada')
    # Cota de la madera Q3: perfiles de ocho lados, 12/9/7 anillos y tapas.
    # T = 2*8*(anillos-1) + 2*(8-2), tres secundarias por primaria.
    primary = base['primary_branches']
    wood = 188 + primary * 140 + (primary * 3 * 108 if base['max_depth'] == 2 else 0)
    total = wood + canopy['group_count'] * 20  # ocho de conexión + seis hojas de dos.
    if total > blueprint['limits']['triangles']:
        raise ValueError(f'Presupuesto previo excedido: {total} triángulos')
    if blueprint['limits']['materials'] < 3:
        raise ValueError('Los componentes RF3 requieren tres materiales')
    return {'wood_triangles': wood, 'added_triangles_max': canopy['group_count'] * 20,
            'triangles_max': total, 'materials_max': 3,
            'surface_samples_max': 8192, 'support_attempts_max': 2048,
            'groups_max': canopy['group_count'], 'leaves_max': canopy['group_count'] * 6}


def validate_blueprint(blueprint):
    schema = _schema(blueprint)
    _validate(StrictValidator(schema), blueprint)
    for role, identifier in blueprint['components'].items():
        if identifier not in COMPONENTS[role]:
            raise ValueError(f'Componente o versión no registrado: {role}={identifier}')
    pine = blueprint['schema_version'] == '1.1'
    expected = ({'base': blueprint['components']['base'], 'distribution': 'pine-distal@0.1.0',
                 'representation': 'pine-needle-pairs@0.1.0'} if pine else None)
    if (pine and (blueprint['components'] != expected or blueprint['components']['base'] not in
                 ('pine-whorls@0.1.0', 'pine-whorls@0.2.0'))) or (not pine and any(
            identifier.startswith('pine-') for identifier in blueprint['components'].values())):
        raise ValueError('Combinación de componentes incompatible con el contrato')
    if blueprint['default_profile'] not in blueprint['profiles']:
        raise ValueError('Perfil predeterminado inexistente')
    for path, interval in blueprint['editable_ranges'].items():
        rule = _rule(path, schema)
        low, high = interval['minimum'], interval['maximum']
        if low > high or low < rule['minimum'] or high > rule['maximum']:
            raise ValueError(f'Rango inválido o fuera del contrato del componente: {path}')
        if rule['type'] == 'integer' and any(type(v) is not int for v in (low, high)):
            raise ValueError(f'El rango debe usar enteros: {path}')
    _check_parameters(blueprint['parameters'], blueprint)
    for profile in blueprint['profiles'].values():
        parameters = _patch(blueprint['parameters'], profile['overrides'], blueprint['editable_ranges'])
        _check_parameters(parameters, blueprint)
    return blueprint


def load_blueprint(path):
    return validate_blueprint(_load(path))


def load_instance(path):
    value = _load(path)
    _validate(_instance_validator(value), value)
    return value


def registered_blueprints():
    """Catálogo local de recetas versionadas, sin imports desde sus datos."""
    entries = []
    for path in sorted((ROOT / 'blueprints').glob('*/*.json')):
        definition = load_blueprint(path)
        if path.parent.name != definition['id'] or path.stem != definition['version']:
            raise ValueError(f'Identidad distinta de la ruta del catálogo: {path}')
        entries.append({'id': definition['id'], 'version': definition['version'],
                        'name': definition['name'], 'default_profile': definition['default_profile'],
                        'path': str(path.relative_to(ROOT)), 'sha256': canonical_hash(definition)})
    return entries


def resolve_blueprint(blueprint, instance):
    """Resuelve valores y procedencia sin mutar entradas ni invocar un motor 3D."""
    validate_blueprint(blueprint)
    _validate(_instance_validator(instance), instance)
    if instance['schema_version'] != blueprint['schema_version']:
        raise ValueError('Versión de contrato distinta entre receta y ejemplar')
    if (instance['blueprint_id'], instance['blueprint_version']) != (blueprint['id'], blueprint['version']):
        raise ValueError('Identidad o versión del blueprint distinta de la solicitada')
    name = instance.get('profile', blueprint['default_profile'])
    if name not in blueprint['profiles']:
        raise ValueError(f'Perfil inexistente: {name}')
    profile = blueprint['profiles'][name]
    defaults = _patch(blueprint['parameters'], profile['overrides'], blueprint['editable_ranges'])
    parameters = _patch(defaults, instance.get('overrides', {}), blueprint['editable_ranges'])
    budget = _check_parameters(parameters, blueprint)
    base_seed, canopy_seed = instance['seeds']['base'], instance['seeds']['canopy']
    if blueprint['schema_version'] == '1.1':
        from .pine import resolve_pine
        return resolve_pine(blueprint, instance, name, profile, defaults, parameters, budget)
    base_spec = {'schema_version': '1.0', 'algorithm': 'oak_geometry_nodes',
                 'algorithm_version': '0.4.0', 'seed': base_seed, 'parameters': parameters['base']}
    validate_spec(base_spec)
    canopy = parameters['canopy']
    canopy_spec = {k: v for k, v in canopy.items() if k != 'layout_leaf_length_m'}
    canopy_spec.update(version='foliage-canopy-' + blueprint['components']['distribution'].split('@')[1], seed=canopy_seed)
    validate_canopy(canopy_spec)
    result = {
        'resolved_version': '1.0', 'blueprint_id': blueprint['id'], 'blueprint_version': blueprint['version'],
        'blueprint_sha256': canonical_hash(blueprint), 'blueprint_definition': copy.deepcopy(blueprint),
        'instance_request': copy.deepcopy(instance), 'profile': name, 'parameters': parameters,
        'profile_validation_claim': copy.deepcopy(profile['validation']),
        'parameters_differ_from_profile': parameters != defaults,
        'base_spec': base_spec, 'canopy_spec': canopy_spec,
        'base_seeds': {stream: derive_seed(base_seed, stream) for stream in ('structure', 'foliage')},
        'layout_leaf_length_m': canopy['layout_leaf_length_m'],
        'appearance': copy.deepcopy(blueprint['appearance']), 'limits': copy.deepcopy(blueprint['limits']),
        'budget_upper_bound': budget,
    }
    result['resolved_sha256'] = canonical_hash(result)
    return result
