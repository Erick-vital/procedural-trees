#!/usr/bin/env python3
"""Prueba acotada de fusión Q3; seleccionar controles después de revisar el piloto."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from treegen.runner import BLENDER
from treegen.evaluation import validate_result


def gallery(output, cases):
    sections = []
    names = {'front': 'Frente', 'side': 'Perfil', 'top': 'Arriba', 'below': 'Abajo',
             'perspective': 'Perspectiva', 'game': 'Distancia de juego'}
    for case in cases:
        rows = []
        sheet = Image.new('RGB', (1200, 6*635), (235, 237, 240))
        draw = ImageDraw.Draw(sheet)
        for row, (view, title) in enumerate(names.items()):
            cells = []
            for col, (label, caption) in enumerate((('base', 'Q3 congelada'), ('fused', 'Fusión parcial'))):
                path = f'{case}/{label}/{view}.png'
                cells.append(f'<td><a href="{path}"><img src="{path}" alt="{case} {caption}: {title}"></a></td>')
                draw.text((col*600+10, row*635+10), f'{case} | {title} | {caption}', fill='black')
                with Image.open(output/path) as source:
                    image = source.convert('RGB')
                image.thumbnail((590, 590))
                sheet.paste(image, (col*600+(600-image.width)//2, row*635+35))
            rows.append('<tr><th>'+title+'</th>'+''.join(cells)+'</tr>')
        sheet.save(output/f'{case}-comparison.jpg', quality=92)
        sections.append(f'<h2>{case}</h2><table><tr><th>Vista</th><th>Q3 congelada</th><th>Fusión parcial</th></tr>'+''.join(rows)+'</table>')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Q3: fusión parcial</title>'
        '<style>body{font:16px sans-serif;background:#ebeef1;color:#20242a;margin:24px}table{width:100%;table-layout:fixed}th:first-child{width:130px}img{width:100%}</style>'
        '<h1>Q3: prueba de fusión parcial</h1><p>Madera, masas de entrada, semillas, materiales, cámaras e iluminación conservados. '
        'Solo cambia la superficie del follaje dentro de cada subárbol. La vista distante usa perspectiva y focal de 50 mm. '
        'Valoración estética pendiente.</p>'+''.join(sections))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base', type=Path, default=ROOT/'artifacts/q3/acceptance/lote')
    parser.add_argument('--cameras-root', type=Path, default=ROOT/'artifacts/q3/acceptance/comparison')
    parser.add_argument('--cases', nargs='+', choices=('viejo-09', 'viejo-00', 'viejo-03', 'adulto-00'), default=['viejo-09'])
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    reports = {}
    for case in args.cases:
        validate_result(args.base/case)
        command = [os.environ.get('BLENDER_BIN', BLENDER), '--background', '--factory-startup', '--threads', '1',
                   '--python-exit-code', '1', '--python', str(ROOT/'blender/experiment_fusion.py'), '--',
                   '--source', str((args.base/case).resolve()), '--output', str(output/case),
                   '--cameras', str((args.cameras_root/case/'cameras.json').resolve())]
        with (output/f'{case}.log').open('w') as log:
            result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        if result.returncode:
            raise RuntimeError((output/f'{case}.log').read_text()[-3500:])
        validate_result(output/case/'candidate')
        reports[case] = json.loads((output/case/'report.json').read_text())
        print(case+': GLB válido, Q3 intacta, madera y condiciones compartidas', flush=True)
    (output/'summary.json').write_text(json.dumps(reports, indent=2)+'\n')
    gallery(output, args.cases)


if __name__ == '__main__':
    main()
