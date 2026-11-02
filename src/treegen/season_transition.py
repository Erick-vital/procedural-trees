"""Contrato T3 para resolver las pinturas compatibles, separado del calendario T1."""
import copy
import hashlib
import math
from pathlib import Path
from PIL import Image
from .season_calendar import weight

VERSION = 'paint-transition-0.1.0'
ROOT = Path(__file__).resolve().parents[2]
PATHS = {'summer':'assets/roble-estacional/v0.1.0/summer.png',
         'autumn':'assets/roble-estacional/v0.1.0/autumn.png',
         'bark':'assets/roble-pintado/v0.2.0/bark.png'}


def validate_profile(profile, root=ROOT):
    if (not isinstance(profile,dict) or set(profile) != {'version','species','phase','resources','atlas_manifest'} or
            profile['version'] != VERSION or profile['species'] != 'roble_copa_ancha@2.2.0' or
            profile['phase'] != 'summer_to_autumn_full_canopy' or
            profile['atlas_manifest'] != 'assets/roble-estacional/v0.1.0/manifest.json' or
            not isinstance(profile['resources'],dict) or set(profile['resources']) != set(PATHS)):
        raise ValueError('Perfil de mezcla desconocido o incompleto')
    import json
    manifest=json.loads((root/profile['atlas_manifest']).read_text())
    if manifest['version'] != 'season-atlas-0.1.0' or manifest['padding']['selection'] != 'padded':
        raise ValueError('Atlas de mezcla incompatible')
    masks=[]
    for name,path in PATHS.items():
        item=profile['resources'][name]
        if not isinstance(item,dict) or set(item) != {'path','sha256'} or item['path'] != path:
            raise ValueError('Recurso fuera del catálogo')
        source=root/path
        if not 33 <= source.stat().st_size <= 16*1024*1024:
            raise ValueError('Recurso excesivo o inválido')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Hash de recurso incorrecto')
        with Image.open(source) as image:
            if image.mode not in (('RGB','RGBA') if name=='bark' else ('RGBA',)) or image.size != ((1254,1254) if name=='bark' else (2000,2000)):
                raise ValueError('Resolución/canales incorrectos')
            if name!='bark':
                if item['sha256']!=manifest['files'][name+'.png']['sha256']:
                    raise ValueError('Pintura distinta del manifiesto')
                masks.append(image.getchannel('A').tobytes())
    if masks[0]!=masks[1] or hashlib.sha256(masks[0]).hexdigest()!=manifest['alpha_sha256']:
        raise ValueError('Se requiere alfa común exacta')
    return copy.deepcopy(profile)


def _unit(value):
    if type(value) not in (int,float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('Canal/fase fuera de [0,1]')
    return value


def decode_srgb(value):
    value=_unit(value)
    return value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4


def encode_srgb(value):
    value=_unit(value)
    return 12.92*value if value<=.0031308 else 1.055*value**(1/2.4)-.055


def blend_rgb(summer,autumn,phase,start=0,duration=1,mode='calendar'):
    _unit(phase)
    if mode not in ('calendar','uniform','summer','autumn'):
        raise ValueError('Modo de mezcla desconocido')
    if len(summer)!=3 or len(autumn)!=3:raise ValueError('RGB necesita tres canales')
    w=weight(phase,start,duration) if mode=='calendar' else {'uniform':phase,'summer':0,'autumn':1}[mode]
    return [encode_srgb((1-w)*decode_srgb(a)+w*decode_srgb(b)) for a,b in zip(summer,autumn)]
