#!/usr/bin/env python3
"""Comparación original/Q1/Q1b a cámara compartida; miniaturas con Pillow."""
import argparse
import html
from pathlib import Path
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('acceptance', type=Path)
args = parser.parse_args()
root = args.acceptance
comparison = root/'comparison'
cases = ['viejo-00', 'viejo-03', 'viejo-09', 'adulto-00', 'joven-00']
labels = [('base', 'Original 0.1.0'), ('reference', 'Q1 0.2.0'), ('candidate', 'Candidato Q1b 0.2.1')]
for filename, view in [('branches', 'branches-front'), ('front', 'front'), ('top', 'branches-top')]:
    sheet = Image.new('RGB', (1500, 1605), (235, 237, 240))
    draw = ImageDraw.Draw(sheet)
    for row, case in enumerate(cases[:3]):
        for col, (label, title) in enumerate(labels):
            draw.text((500*col+10, 535*row+10), case+' | '+title, fill='black')
            with Image.open(comparison/case/label/f'{view}.png') as source:
                image = source.convert('RGB')
            image.thumbnail((490, 490))
            sheet.paste(image, (500*col+(500-image.width)//2, 535*row+35))
    sheet.save(root/f'comparison-{filename}.jpg', quality=92)
sections = []
for case in cases:
    rows = []
    for view in ('branches-front', 'branches', 'branches-side', 'branches-top', 'front', 'side', 'top', 'perspective'):
        cells = ''.join(f'<td><a href="{case}/{label}/{view}.png"><img src="{case}/{label}/{view}.png" '
                        f'alt="{html.escape(case)} {title} {view}"></a></td>' for label,title in labels)
        rows.append(f'<tr><th>{view}</th>{cells}</tr>')
    sections.append(f'<h2>{case}</h2><table><tr><th>Vista</th>'+''.join(f'<th>{title}</th>' for label,title in labels)
                    +'</tr>'+''.join(rows)+'</table>')
(comparison/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Ramas Q1b</title>'
    '<style>body{font:16px sans-serif;margin:24px;background:#ebeef1;color:#20242a}table{width:100%;table-layout:fixed}'
    'th:first-child{width:105px}img{width:100%;height:auto}td,th{vertical-align:top}</style>'
    '<h1>Revisión de ramas: original → Q1 → candidato Q1b</h1>'
    '<p>Las tres versiones comparten semilla, parámetros, cámara y escala de encuadre por caso. '
    'Q1b recupera longitud y grosor, con tres secundarias por primaria. Mantiene el follaje y el ajuste Z anteriores.</p>'
    '<p>La valoración estética del usuario sigue pendiente. Q2 está detenida hasta aceptar la estructura. '
    'Pulsa una imagen para verla completa.</p>'+''.join(sections))
