"""Carga estricta del contrato v1; no depende de Blender."""
import hashlib
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / 'schemas/tree-spec.schema.json').read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def load_spec(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Campo repetido: {key}')
            result[key] = value
        return result

    spec = json.loads(Path(path).read_text(), object_pairs_hook=unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    validate_spec(spec)
    return spec


def validate_spec(spec):
    errors = sorted(VALIDATOR.iter_errors(spec), key=lambda e: str(list(e.path)))
    if errors:
        raise ValueError('; '.join(f'{list(e.path)}: {e.message}' for e in errors))
    for value in spec['parameters'].values():
        if isinstance(value, (float, int)) and not math.isfinite(value):
            raise ValueError('Los parámetros deben ser finitos')
    return spec


def spec_hash(spec):
    validate_spec(spec)
    return hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()
