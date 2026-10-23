#!/usr/bin/env python3
"""Galerías Q1b/Q2 control/Q2 presets con cámaras compartidas; requiere Pillow."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('acceptance', type=Path)
args = parser.parse_args()
root, comparison = args.acceptance, args.acceptance/'comparison'
cases = ['viejo-00', 'viejo-03', 'viejo-09', 'adulto-00', 'joven-00']
labels = [('base', 'Q1b 0.2.1 aprobado'), ('reference', 'Q2: parametros de Q1b'), ('candidate', 'Q2: copa ajustada')]
for filename, view in [('front', 'front'), ('branches', 'branches-front'), ('top', 'top'), ('perspective', 'perspective')]:
    sheet = Image.new('RGB', (1500, 1605), (235,237,240))
    draw = ImageDraw.Draw(sheet)
    for row, case in enumerate(cases[:3]):
        for col, (label, title) in enumerate(labels):
            draw.text((500*col+10,535*row+10),case+' | '+title,fill='black')
            with Image.open(comparison/case/label/f'{view}.png') as source:
                image = source.convert('RGB')
            image.thumbnail((490,490))
            sheet.paste(image,(500*col+(500-image.width)//2,535*row+35))
    sheet.save(root/f'comparison-{filename}.jpg',quality=92)
sections=[]
for case in cases:
    rows=[]
    for view in ('front','side','top','perspective','branches-front','branches','branches-side','branches-top'):
        cells=''.join(f'<td><a href="{case}/{label}/{view}.png"><img src="{case}/{label}/{view}.png" alt="{case} {title} {view}"></a></td>' for label,title in labels)
        rows.append(f'<tr><th>{view}</th>{cells}</tr>')
    sections.append(f'<h2>{case}</h2><table><tr><th>Vista</th>'+''.join(f'<th>{title}</th>' for label,title in labels)+'</tr>'+''.join(rows)+'</table>')
(comparison/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Q2: copa y proporciones</title>'
    '<style>body{font:16px sans-serif;margin:24px;background:#ebeef1;color:#20242a}table{width:100%;table-layout:fixed}th:first-child{width:105px}img{width:100%;height:auto}td,th{vertical-align:top}</style>'
    '<h1>Q1b aprobado → Q2: copa y proporciones</h1>'
    '<p>Las tres columnas comparten semilla y cámara por caso. El control Q2 conserva todos los parámetros Q1b; '
    'la última columna ajusta solo densidad/escala de follaje. La estructura nativa y la madera X/Y son idénticas.</p>'
    '<p>Q2 ajusta Z según la madera y sitúa el follaje dentro de la altura pedida. Cambiar la copa deja intacta la madera Q2. '
    'El perfil vertical difiere del aprobado en Q1b y se muestra sin hojas para revisarlo. Valoración estética Q2 pendiente del usuario.</p>'
    '<p>Pulsa una imagen para verla completa.</p>'+''.join(sections))
