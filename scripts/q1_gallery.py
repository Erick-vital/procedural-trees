#!/usr/bin/env python3
"""Galerías Q1 con pares renderizados a igual escala/cámara. Requiere Pillow."""
import argparse
import html
import json
from pathlib import Path
from PIL import Image, ImageDraw

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('acceptance',type=Path)
args=parser.parse_args()
root=args.acceptance
comparison=root/'comparison'
cases=['viejo-00','viejo-03','viejo-09','adulto-00','joven-00']
for view in ('branches','front','perspective','branches-top'):
    sheet=Image.new('RGB',(1440,1320),(235,237,240))
    draw=ImageDraw.Draw(sheet)
    for i,case in enumerate(cases):
        col,row=i%3,i//3
        draw.text((col*480+10,row*660+10),case+' | base 0.1.0 / Q1 0.2.0',fill='black')
        for j,label in enumerate(('base','candidate')):
            with Image.open(comparison/case/label/f'{view}.png') as source:
                image=source.convert('RGB')
            image.thumbnail((470,300))
            sheet.paste(image,(col*480+(480-image.width)//2,row*660+35+j*305))
    sheet.save(root/f'comparison-{view}.jpg',quality=92)
rows=[]
for case in cases:
    for view in ('branches','branches-front','branches-side','branches-top','front','side','top','perspective'):
        cells=''.join(f'<td><img width="430" src="{case}/{label}/{view}.png" alt="{case} {label} {view}"></td>' for label in ('base','candidate'))
        rows.append(f'<tr><th>{html.escape(case)}<br>{view}</th>{cells}</tr>')
(comparison/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Q1: comparación de ramas</title>'
    '<h1>Q1: referencia y candidato</h1><p>Semillas y parámetros conservados; versión 0.1.0 frente a 0.2.0. '
    'Cada pareja comparte cámara y escala de encuadre. La copa y el ajuste de altura siguen pendientes de Q2.</p>'
    '<table><tr><th>Caso/vista</th><th>Base 0.1.0</th><th>Q1 0.2.0</th></tr>'+''.join(rows)+'</table>')
