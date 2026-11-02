"""Contratos de variantes estacionales; independientes de generación y Godot."""
import hashlib
import math
import re

VERSION = 'tree-seasons-1.0.0'


def validate_profile(profile):
    fields = {'version', 'species', 'blueprint_version', 'season', 'phase',
              'foliage_material', 'amount', 'seed', 'patch_scale_m',
              'green_retention', 'palette_srgb', 'limits'}
    if not isinstance(profile, dict) or set(profile) != fields:
        raise ValueError('Contrato estacional incompleto o con campos desconocidos')
    if (profile['version'], profile['species'], profile['blueprint_version'],
        profile['season'], profile['phase'], profile['foliage_material']) != (
        '1.0.0', 'roble_copa_ancha', '2.2.0', 'autumn', 'full_canopy', 'Painted_Foliage'):
        raise ValueError('Perfil de especie/fase todavía no implementado')
    for key, low, high in [('amount', 0, 1), ('patch_scale_m', .1, 10), ('green_retention', 0, .3)]:
        value = profile[key]
        if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError('Parámetro estacional inválido: '+key)
    if type(profile['seed']) is not int or not 0 <= profile['seed'] <= 2147483647:
        raise ValueError('Semilla estacional inválida')
    colors = profile['palette_srgb']
    if not isinstance(colors, list) or len(colors) != 3 or any(
        not isinstance(c, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in colors):
        raise ValueError('Se requieren tres colores sRGB')
    if profile['limits'] != {'triangles': 6999, 'materials': 2}:
        raise ValueError('Límites estacionales incompatibles con producción')
    return profile


def validate_source(manifest, profile, glb_bytes):
    validate_profile(profile)
    resolved = manifest['resolved_blueprint']
    definition = resolved['blueprint_definition']
    if (definition['id'], definition['version']) != (profile['species'], profile['blueprint_version']):
        raise ValueError('El árbol no corresponde al perfil estacional')
    if hashlib.sha256(glb_bytes).hexdigest() != manifest['glb_sha256']:
        raise ValueError('GLB distinto del manifiesto de origen')
    metrics = manifest['metrics']
    if not 0 < metrics['triangles'] <= profile['limits']['triangles']:
        raise ValueError('Árbol fuera del presupuesto estacional')
    if len(metrics['triangles_by_material']) != 2 or profile['foliage_material'] not in metrics['triangles_by_material']:
        raise ValueError('Materiales incompatibles')
    return metrics
