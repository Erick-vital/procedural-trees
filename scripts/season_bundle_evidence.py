#!/usr/bin/env python3
"""Láminas T5 a partir de capturas verificadas, sin regenerar geometría."""
import argparse
import json
import hashlib
import sys
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from treegen.seasonal_paint import unpack,view_bytes

CASES=('pilot','joven-07','adulto-00','viejo-00')


def sheet(target, rows, width=250):
    cols=max(map(len,rows));height=width+25
    out=Image.new('RGB',(cols*width,len(rows)*height),'#eee9df');draw=ImageDraw.Draw(out)
    for y,row in enumerate(rows):
        for x,(path,label) in enumerate(row):
            with Image.open(path) as source:
                im=source.convert('RGB');im.thumbnail((width,width))
            out.paste(im,(x*width,y*height+25));draw.text((x*width+4,y*height+6),label,fill='#29221b')
    out.save(target,quality=94)


def audit_saved(output, result):
    """Contrastar ZIP y PNG realmente guardados contra las pruebas nativas."""
    sha=lambda data:hashlib.sha256(data).hexdigest()
    checks={}
    checks['2377_capture_files_match']=len(result['capture_sha256'])==2377 and all(sha((output/'captures'/p).read_bytes())==h for p,h in result['capture_sha256'].items())
    for case,stages in result['godot'].items():
        for stage in ('fixed','orbit'):
            for frame in stages[stage]['frames']:
                path=output/'captures'/case/stage/f'{stage}-{frame["frame"]:03}.png'
                with Image.open(path) as im:
                    if sha(im.tobytes())!=frame['pixels_sha256']:raise ValueError('Píxeles guardados distintos')
    checks['1928_png_pixels_match_native_hashes']=True
    for path in (output/'portable/cases').glob('*/*.glb'):
        doc,binary=unpack(path.read_bytes())
        if len(doc['materials'])!=2 or len(doc['images'])!=2:raise ValueError('Extremo sin dos materiales/imágenes')
        if not all('uri' not in im and im['mimeType']=='image/png' and view_bytes(doc,binary,im['bufferView']).startswith(b'\x89PNG\r\n\x1a\n') for im in doc['images']):raise ValueError('PNG externo o ausente')
    checks['16_standard_glbs_two_embedded_pngs']=True
    with zipfile.ZipFile(output/result['archive']['file']) as archive:
        if archive.testzip() is not None:raise ValueError('ZIP corrupto')
        for rel,h in result['manifest']['project_lock'].items():
            if sha(archive.read('godot/'+rel))!=h:raise ValueError('Fuente de ZIP distinta')
        for rel,h in result['manifest']['bundle']['files_sha256'].items():
            if sha(archive.read('portable/'+rel))!=h:raise ValueError('Recurso de ZIP distinto')
        if any(Path(p).is_absolute() or '..' in Path(p).parts for p in archive.namelist()):raise ValueError('Ruta de ZIP inválida')
    checks['zip_crc_paths_and_locked_contents']=True
    record={'passed':all(checks.values()),'checks':checks,'verification_sha256':sha((output/'verification.json').read_bytes())}
    (output/'additional-checks.json').write_text(json.dumps(record,indent=2)+'\n')
    if not record['passed']:raise ValueError('Falló auditoría de archivos guardados')


def build(output):
    result=json.loads((output/'verification.json').read_text())
    if not result['passed']:raise ValueError('T5 aún no verificada')
    audit_saved(output,result)
    root=output/'captures';review=output/'review';review.mkdir(exist_ok=True)
    rows=[]
    for case in CASES:
        rows.append([(root/case/'matrix'/f'{case}-{season}-{kind}.png',f'{case} {season} {kind}')
                     for season in ('summer','autumn') for kind in ('original','selected')])
    sheet(review/'standard-controls.jpg',rows)
    for light in range(3):
        rows=[[(root/case/'matrix'/f'mix-light-l{light}-d0-p{phase}.png',f'{case} luz {light} p={phase/4:g}') for phase in range(5)] for case in CASES]
        sheet(review/f'light-{light}.jpg',rows)
        rows=[[(root/case/'matrix'/f'shadow-l{light}-p{phase}.png',f'{case} luz {light} p={phase/4:g}') for phase in (0,2,4)] for case in CASES]
        sheet(review/f'shadows-{light}.jpg',rows,300)
        rows=[[(root/case/'matrix'/f'mix-{bg}-l{light}-d{distance}-p2.png',f'{case} {bg} distancia {distance}') for bg in ('light','dark') for distance in range(3)] for case in CASES]
        sheet(review/f'distances-{light}.jpg',rows,220)
    for stage in ('fixed','orbit'):
        for case in CASES:
            entries=[(root/case/stage/f'{stage}-{i:03}.png',f'{i:03} p={i/120:.3f}') for i in range(121)]
            sheet(review/f'{case}-{stage}-all-forward.jpg',[entries[i:i+11] for i in range(0,121,11)],120)
    print(review)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    build(parser.parse_args().output.resolve())
