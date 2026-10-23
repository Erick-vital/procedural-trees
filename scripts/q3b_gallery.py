#!/usr/bin/env python3
"""Comparación Q3/Q3b, con las mismas semillas, parámetros y cámaras."""
import argparse
from pathlib import Path
from PIL import Image,ImageDraw

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('acceptance',type=Path)
parser.add_argument('--comparison',type=Path)
args=parser.parse_args()
root=args.acceptance;comparison=args.comparison or root/'comparison'
cases=['viejo-00','viejo-03','viejo-09','adulto-00','joven-00']
labels=[('base','Q3 0.4.0 referencia'),('candidate','Q3b 0.4.1 copa abierta')]
for filename,view in [('front','front'),('branches','branches-front'),('top','top'),('perspective','perspective'),('below','below'),('below-front','below-front')]:
    sheet=Image.new('RGB',(1200,1905),(235,237,240));draw=ImageDraw.Draw(sheet)
    for row,case in enumerate(cases[:3]):
        for col,(label,title) in enumerate(labels):
            draw.text((600*col+10,635*row+10),case+' | '+title,fill='black')
            with Image.open(comparison/case/label/f'{view}.png') as source:image=source.convert('RGB')
            image.thumbnail((590,590));sheet.paste(image,(600*col+(600-image.width)//2,635*row+35))
    sheet.save(root/f'comparison-{filename}.jpg',quality=92)
sections=[]
for case in cases:
    rows=[]
    for view in ('front','side','top','perspective','branches-front','branches','branches-side','branches-top','below','below-front','branches-below'):
        cells=''.join(f'<td><a href="{case}/{label}/{view}.png"><img src="{case}/{label}/{view}.png" alt="{case} {title} {view}"></a></td>' for label,title in labels)
        rows.append(f'<tr><th>{view}</th>{cells}</tr>')
    sections.append(f'<h2>{case}</h2><table><tr><th>Vista</th>'+''.join(f'<th>{title}</th>' for label,title in labels)+'</tr>'+''.join(rows)+'</table>')
(comparison/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Q3b: copa abierta y grupos por grosor</title>'
    '<style>body{font:16px sans-serif;margin:24px;background:#ebeef1;color:#20242a}table{width:100%;table-layout:fixed}th:first-child{width:105px}img{width:100%;height:auto}td,th{vertical-align:top}</style>'
    '<h1>Q3 → Q3b: copa abierta y grupos por grosor</h1><p>Semillas, parámetros y cámaras compartidos. '
    'La madera final y su altura son idénticas. Q3b liga los grupos al grosor de rama, acorta sus tramos y deja secundarias intermedias sin hojas.</p>'
    '<p>Revisa especialmente las vistas inferiores y la variación de altura entre grupos. '
    'La valoración estética de Q3b está pendiente del usuario. Pulsa una imagen para verla completa.</p>'+''.join(sections))
