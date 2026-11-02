#!/usr/bin/env python3
"""T6: cerrar la entrega T5 sin alterar sus recursos ni adoptar fases nuevas."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def close(trial,output):
    trial=trial.resolve();result=read(trial/'verification.json');manifest=result['manifest']
    if not result['passed'] or not all(result['checks'].values()):raise ValueError('T5 sin verificar')
    selected=ROOT/'docs/evidence/estaciones/integracion-t5/verification.json'
    evidence=read(selected)
    if evidence['raw_verification']['sha256']!=sha(trial/'verification.json'):raise ValueError('Evidencia T5 distinta')
    additional=read(trial/'additional-checks.json')
    if not additional['passed'] or additional['verification_sha256']!=sha(trial/'verification.json'):raise ValueError('Auditoría guardada distinta')
    # Conservar los contratos y las decisiones históricas literalmente.
    for rel,expected in {**manifest['source_lock'],**manifest['input_lock'],**result['historical_catalog_sha256']}.items():
        if sha(ROOT/rel)!=expected:raise ValueError('Fuente/entrada histórica modificada: '+rel)
    for rel,expected in manifest['project_lock'].items():
        if sha(trial/'godot'/rel)!=expected:raise ValueError('Proyecto T5 modificado: '+rel)
    for rel,expected in manifest['bundle']['files_sha256'].items():
        if sha(trial/'portable'/rel)!=expected:raise ValueError('Extremo/dato T5 modificado: '+rel)
    if sha(trial/'portable/manifest.json')!=manifest['portable_manifest_sha256']:raise ValueError('Manifiesto portable modificado')
    if sha(ROOT/'scripts/verify_season_bundle.py')!=result['review_source_sha256']:raise ValueError('Arnés T5 distinto')
    for rel,expected in result['capture_sha256'].items():
        if sha(trial/'captures'/rel)!=expected:raise ValueError('Captura T5 modificada: '+rel)
    package=trial/result['archive']['file']
    if sha(package)!=result['archive']['sha256']:raise ValueError('ZIP T5 distinto')
    with zipfile.ZipFile(package) as archive:
        if archive.testzip() is not None:raise ValueError('ZIP T5 corrupto')
        for rel,h in manifest['project_lock'].items():
            if hashlib.sha256(archive.read('godot/'+rel)).hexdigest()!=h:raise ValueError('Proyecto del ZIP distinto')
        for rel,h in manifest['bundle']['files_sha256'].items():
            if hashlib.sha256(archive.read('portable/'+rel)).hexdigest()!=h:raise ValueError('Extremo del ZIP distinto')
    t3path=ROOT/'docs/evidence/estaciones/mezcla-t3/user-acceptance.json'
    t4path=ROOT/'docs/evidence/estaciones/normales-t4/user-acceptance.json'
    t3=read(t3path);t4=read(t4path)
    for decision in (t3,t4):
        if decision['decision']!='approved' or sha(ROOT/decision['verification'])!=decision['verification_sha256']:
            raise ValueError('Aprobación sin evidencia íntegra')
    if t4['selected_variant']!='n35' or t4['strength']!=.35:raise ValueError('Selección de normales distinta')
    output.mkdir(parents=True,exist_ok=False)
    sources=set(manifest['source_lock'])|set(manifest['input_lock'])
    for item in read(ROOT/'configs/seasons/roble-calendario-v1.json')['resources'].values():
        if sha(ROOT/item['path'])!=item['sha256']:raise ValueError('Recurso histórico del calendario distinto')
        sources.add(item['path'])
    # Incluir dependencias Python locales y esquemas; no binarios del motor,
    # cachés ni credenciales. Las entradas de T1/T4 son referencias congeladas.
    for folder,patterns in {'src':('*.py',),'scripts':('*.py',),'blender':('*.py',),
                            'schemas':('*.json',)}.items():
        for pattern in patterns:sources.update(str(p.relative_to(ROOT)) for p in (ROOT/folder).rglob(pattern))
    sources.update(['requirements.txt',t3['verification'],t4['verification'],
                    'docs/contrato-integracion-estacional.md','docs/contrato-calendario-estacional.md',
                    'docs/contrato-normales-copa.md','docs/evidence/estaciones/integracion-t5/verification.json'])
    locks={rel:sha(ROOT/rel) for rel in sorted(sources)}
    source_zip=output/'fuentes-y-entradas-t5.zip'
    with zipfile.ZipFile(source_zip,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for rel in sorted(sources):
            info=zipfile.ZipInfo(rel,date_time=(2026,11,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,(ROOT/rel).read_bytes())
    with tempfile.TemporaryDirectory(prefix='season-t6-rebuild-') as tmp:
        clean=Path(tmp)
        with zipfile.ZipFile(source_zip) as archive:
            if archive.testzip() is not None:raise ValueError('ZIP de fuentes corrupto')
            archive.extractall(clean)
        for rel,h in locks.items():
            if sha(clean/rel)!=h:raise ValueError('Fuente extraída distinta')
        env=os.environ.copy();env.pop('PYTHONPATH',None)
        completed=subprocess.run([sys.executable,'scripts/build_season_bundle.py','--output','rebuilt'],cwd=clean,env=env,capture_output=True,text=True,timeout=120)
        (output/'rebuild.log').write_text(completed.stdout+completed.stderr)
        if completed.returncode:raise RuntimeError('Reconstrucción aislada falló; ver rebuild.log')
        rebuilt=read(clean/'rebuilt/manifest.json')
        if rebuilt!=manifest:raise ValueError('Reconstrucción no idéntica al manifiesto T5')
        for rel,h in manifest['bundle']['files_sha256'].items():
            if sha(clean/'rebuilt/portable'/rel)!=h:raise ValueError('Extremo reconstruido distinto')
        for rel,h in manifest['project_lock'].items():
            if sha(clean/'rebuilt/godot'/rel)!=h:raise ValueError('Proyecto reconstruido distinto')
    decisions={'date':'2026-11-02','authorization':'implementa t6','technical_status':'closed',
               'paint':{'decision':'approved','scope':'Pinturas compatibles y aplicación en piloto T3; no aprobación independiente de la pintura otoñal histórica anterior.', 'evidence':str(t3path.relative_to(ROOT)),'sha256':sha(t3path)},
               'calendar':{'decision':'approved','scope':'Calendario por grupos del piloto T3; misma regla verificada en cuatro casos T5.', 'evidence':str(t3path.relative_to(ROOT)),'sha256':sha(t3path)},
               'normals':{'decision':'approved','selection':'n35','strength':.35,'scope':'Selección del piloto T4 delegada por el usuario; regla común en T5.', 'evidence':str(t4path.relative_to(ROOT)),'sha256':sha(t4path)},
               'four_case_artistic_adoption':{'decision':'pending','scope':'T5 tiene revisión visual técnica; solicitar T6 no constituye aprobación artística del lote.'},
               'continuation':{'decision':'no_additional_phase_started','next_possible_work':'Estudio separado de caída del roble, previa definición de alcance con el usuario.',
                               'deferred':['caída','invierno','brotación','marcescencia','partículas','viento','LOD','otras especies'],
                               'historical_defaults':'conserved'}}
    write(output/'decisions.json',decisions)
    for name in ('comparison.jpg','fixed.webp','orbit.webp'):shutil.copy2(trial/name,output/name)
    t5relative=Path(os.path.relpath(trial,output)).as_posix()
    (output/'index.html').write_text('''<!doctype html><html lang="es"><meta charset="utf-8"><title>Cierre T6 · Roble estacional</title>
<style>body{font:16px sans-serif;background:#eee9df;color:#29221b;max-width:1400px;margin:24px auto;padding:0 20px}img{max-width:100%;height:auto}section{display:flex;flex-wrap:wrap}figure{margin:12px}section img{max-width:640px}</style>
<h1>Roble estacional · T0–T6 cerrado técnicamente</h1><p>Candidata 0.1.0 · copa llena · normales .35 aprobadas. Pintura y calendario del piloto aprobados; adopción artística del conjunto de cuatro casos pendiente.</p>
<section><figure><img src="fixed.webp"><figcaption>Cámara fija · ida/vuelta</figcaption></figure><figure><img src="orbit.webp"><figcaption>Órbita · ida/vuelta</figcaption></figure></section><img src="comparison.jpg" alt="Cinco fases de los cuatro robles">
<p><a href="fuentes-y-entradas-t5.zip">Fuentes y entradas congeladas para reconstruir T5</a> · <a href="verification.json">Hashes y auditoría T6</a> · <a href="decisions.json">Decisiones separadas</a></p>
<p><a href="'''+html.escape(t5relative)+'''/roble-estacional-0.1.0.zip">Paquete Godot y 16 GLB</a> · <a href="'''+html.escape(t5relative)+'''/index.html">Galería T5</a></p>
<p>Descomprimir el paquete Godot, abrir godot/project.godot y ejecutar. Los extremos GLB son estándar; la transición por grupo necesita el adaptador. Sin caída ni año completo; sin benchmark de FPS.</p></html>''')
    report={'version':'season-closeout-0.1.0','date':'2026-11-02','passed':True,
            'checks':{'t5_frozen_inputs_sources_and_outputs':True,'2377_capture_hashes':True,'t5_zip_crc_and_contents':True,
                      'separate_approvals_verified':True,'source_archive_crc_and_contents':True,'isolated_build_under_120_seconds':True,
                      'rebuilt_manifest_project_and_16_endpoints_exact':True},
            't5':{'trial':str(trial.relative_to(ROOT)),'verification_sha256':sha(trial/'verification.json'),
                  'selected_verification_sha256':sha(selected),'archive':result['archive'],'tests':evidence['tests'],'checks':result['checks']},
            'source_archive':{'file':source_zip.name,'sha256':sha(source_zip),'bytes':source_zip.stat().st_size,'files_sha256':locks,
                              'scope':'Reconstrucción T5 desde entradas congeladas T1/T2/T4, no regeneración de todas las fases históricas.'},
            'decisions':decisions,'rebuild_log_sha256':sha(output/'rebuild.log'),
            'gallery_files_sha256':{name:sha(output/name) for name in ('index.html','comparison.jpg','fixed.webp','orbit.webp')},
            'closeout_source_sha256':sha(Path(__file__))}
    write(output/'verification.json',report)
    print(f'T6 verificada: {len(locks)} fuentes/entradas, proyecto y 16 extremos idénticos desde copia aislada.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trial',type=Path,default=ROOT/'artifacts/estaciones/integracion-t5-03')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();close(args.trial,args.output.resolve())
