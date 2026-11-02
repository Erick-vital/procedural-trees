"""Contrato de integración T5: variante explícita, sin cambiar recetas históricas."""
import copy
import hashlib
import json
from pathlib import Path
from .season_transition import validate_profile as validate_paint

VERSION='season-bundle-0.1.0'
ROOT=Path(__file__).resolve().parents[2]
CASE_IDS=('pilot','joven-07','adulto-00','viejo-00')
FIXED={'version':VERSION,'blueprint':'blueprints/roble_copa_ancha/2.2.0.json',
       'matrix':'configs/verification/oak-wood-v1.json','paint_profile':'configs/seasons/roble-mezcla-v1.json',
       'calendar_profile':'configs/seasons/roble-calendario-v1.json','normal_algorithm':'canopy-local-normals-0.1.0',
       'normal_approval':'docs/evidence/estaciones/normales-t4/user-acceptance.json','phase':'summer_to_autumn_full_canopy',
       'max_triangles':6999,'max_materials':2}


def validate_profile(value,*,resources=True):
    if not isinstance(value,dict) or set(value)!=set(FIXED)|{'normal_strength'}:
        raise ValueError('Perfil de integración incompleto o desconocido')
    if any(value[k]!=v or type(value[k]) is not type(v) for k,v in FIXED.items()):
        raise ValueError('Variante de integración fuera del catálogo')
    if type(value['normal_strength']) is not float or value['normal_strength']!=.35:
        raise ValueError('Solo se admite la candidata .35 seleccionada')
    if resources:
        approval=json.loads((ROOT/value['normal_approval']).read_text())
        verification=ROOT/approval['verification']
        if approval['decision']!='approved' or approval['strength']!=.35 or hashlib.sha256(verification.read_bytes()).hexdigest()!=approval['verification_sha256']:
            raise ValueError('Selección de normales no aprobada o verificación alterada')
        validate_paint(json.loads((ROOT/value['paint_profile']).read_text()))
    return copy.deepcopy(value)


def validate_portable(folder):
    """Auditar rutas/hashes autocontenidos antes de abrir/importar el paquete."""
    folder=Path(folder).resolve();manifest=json.loads((folder/'manifest.json').read_text())
    if manifest.get('version')!=VERSION or tuple(c.get('id') for c in manifest.get('cases',[]))!=CASE_IDS:
        raise ValueError('Paquete portable desconocido')
    files=manifest.get('files_sha256',{})
    if not 1<=len(files)<=100:raise ValueError('Número de archivos portable excesivo')
    for name,expected in files.items():
        path=folder/name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.resolve().parent!=folder and folder not in path.resolve().parents:
            raise ValueError('Ruta portable fuera de la carpeta')
        if not path.is_file() or path.stat().st_size>64*1024*1024 or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('Recurso portable ausente o alterado')
    for item in manifest['cases']:
        if not 0<item['triangles']<=6999 or item['materials']!=2 or item['groups']!=264:
            raise ValueError('Presupuesto portable incorrecto')
        if set(item['exports'])!={'summer-original','autumn-original','summer-selected','autumn-selected'}:
            raise ValueError('Extremos/controles portables incompletos')
        for name in item['exports'].values():
            if name not in files:raise ValueError('Exportación portable sin hash')
    return manifest
