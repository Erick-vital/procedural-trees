#!/usr/bin/env python3
"""Seleccionar evidencia R2 sin alterar sus modelos o capturas."""
import argparse
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
from review_pine_painted import read,write,sha
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args();study=a.study.resolve();out=a.output.resolve()
    r=read(study/'verification.json');shadows=read(study/'shadows-framed-verification.json')
    tests=(study/'logs/tests.log').read_text();assert 'Ran 231 tests' in tests and tests.rstrip().endswith('OK')
    alpha_tests=read(ROOT/'artifacts/f5/rama-r2-alpha-tests/verification.json')
    assert r['passed'] and alpha_tests['passed'] and len(r['captures_sha256'])==134
    assert len(shadows['captures_sha256'])==6
    assert all(v['reference_pixels']>100 and v['lost_pixels']==0 and v['gained_pixels']==0 for v in r['visible_wood_comparison'].values())
    out.mkdir(parents=True,exist_ok=True)
    selected=[]
    for name in ('near','medium','far','wood','visible-wood'):
        shutil.copy2(study/(name+'.jpg'),out/(name+'.jpg'))
    shutil.copy2(study/'shadows-framed.jpg',out/'shadows.jpg')
    for distance in ('near','medium','far'):
        selected += [f'color/{variant}--{distance}-{view}.png' for variant in ('full','simple') for view in ('front','side','perspective','top','below','back')]
    selected += [f'color/{variant}--wood-medium-{view}.png' for variant in ('full','simple') for view in ('front','side','perspective','top','below','back')]
    selected += [f'visible-wood/{variant}--medium-{view}.png' for variant in ('full','simple') for view in ('front','side','perspective','top','below','back')]
    for group in range(2):
        shots=[f'orbit-{i:02}' for i in range(group*4,(group+1)*4)]
        rows=[[(f'captures/color/{name}--{shot}.png',name+' '+shot) for name in ('full','simple')] for shot in shots]
        sheet(study,out/f'orbit-{group}.jpg',2,rows)
        selected += [f'color/{name}--{shot}.png' for name in ('full','simple') for shot in shots]
    mask_rows=[[(f'captures/mask/{name}--medium-{view}.png',name+' '+view) for name in ('foliage-before','foliage-after')]
               for view in ('front','side','perspective','top','below','back')]
    sheet(study,out/'masks.jpg',2,mask_rows)
    selected += [f'mask/{name}--medium-{view}.png' for name in ('foliage-before','foliage-after') for view in ('front','side','perspective','top','below','back')]
    selected += ['shadows-framed/'+name for name in shadows['captures_sha256']]
    rows=[]
    for shot,suffix in [('medium-perspective','con follaje'),('wood-medium-perspective','madera descubierta')]:
        rows.append([(f'captures/color/{name}--{shot}.png',label+' | '+suffix) for name,label in [('full','Completa: 1700 tris'),('simple','Simplificada: 1416 tris')]])
    sheet(study,out/'comparacion.jpg',2,rows)
    godot={name:{'passed':data['passed'],'captures':len(data['captures']),'godot':data['godot'],
                  'renderer':data['renderer'],'video_adapter':data['video_adapter'],'environment':data['environment']} for name,data in r['godot'].items()}
    report={k:v for k,v in r.items() if k not in ('godot','captures_sha256','visual_review')}
    report.update(phase='R2',date='2026-11-03',study=str(study.relative_to(ROOT)),godot=godot,
        final_capture_count=140,selected_capture_count=len(set(selected)),
        selected_capture_sha256={name:sha(study/'captures'/name) for name in sorted(set(selected))},
        shadows=shadows,tests={'passed':231,'log_sha256':sha(study/'logs/tests.log'),'alpha_analytic_cases':alpha_tests},
        source_frozen_sha256=sha(study/'source-frozen.json'),visibility_sha256=sha(study/'visibility.json'),
        view_matrix_sha256=sha(study/'view-matrix.json'),alpha_input_sha256=sha(study/'alpha.bin'),
        qa_sources_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'scripts/branch_simplification_shadows.py',ROOT/'tests/test_branch_visibility.py']},
        visual_review='pending_agent',artistic_acceptance='pending_user')
    report['selected_sheets_sha256']={p.name:sha(p) for p in out.glob('*.jpg')}
    write(out/'verification.json',report)
    for name in ('comparacion','orbit-0','orbit-1'):
        shutil.copy2(out/(name+'.jpg'),study/(name+'.jpg'))
    sections=[('near','Cerca: detalles (encuadre ampliado)'),('medium','Distancia media'),('far','Lejos'),
              ('orbit-0','Giro desde abajo: primera mitad'),('orbit-1','Giro desde abajo: segunda mitad'),
              ('wood','Madera descubierta: qué se elimina'),('visible-wood','Diagnóstico: madera visible en rojo'),
              ('shadows-framed','Sombras con tres direcciones de luz')]
    (study/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>R2: completa y simplificada</title>'
        '<style>body{font:18px sans-serif;background:#eee9df;margin:24px;max-width:1200px}img{max-width:100%}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #aaa}</style>'
        '<h1>Rama completa / rama simplificada</h1><p>Izquierda: R1 completa. Derecha: simplificada. Mismo follaje; se conserva la madera visible y sus conexiones principales.</p>'
        '<table><tr><th></th><th>Completa</th><th>Simplificada</th></tr><tr><td>Madera</td><td>1178 tris</td><td>894 tris</td></tr>'
        '<tr><td>Follaje</td><td>522 tris</td><td>522 tris</td></tr><tr><td>Total</td><td>1700 tris</td><td>1416 tris</td></tr></table>'
        '<p>16,7 % menos en total; 24,1 % menos de madera. Comparación de una rama con copa llena, pendiente de valoración artística.</p><img src="comparacion.jpg">'
        +''.join('<h2>'+title+'</h2><img src="'+name+'.jpg">' for name,title in sections))
    print('Selección:',report['selected_capture_count'],'de',report['final_capture_count'],'capturas finales.')


if __name__=='__main__':main()
