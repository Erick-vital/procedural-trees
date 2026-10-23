#!/usr/bin/env python3
"""Galerías de revisión del lote F2. Requiere Pillow solo para estas miniaturas."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('batch', type=Path)
parser.add_argument('--godot', action='store_true')
args = parser.parse_args()
root = args.batch
for view in (['godot'] if args.godot else ['perspective', 'front', 'side', 'top', 'branches']):
    sheet = Image.new('RGB', (1500, 1050), (235, 237, 240))
    draw = ImageDraw.Draw(sheet)
    for i, case in enumerate(json.loads((root / 'cases.json').read_text())):
        with Image.open(root / case['id'] / f'{view}.png') as source:
            im = source.convert('RGB')
        im.thumbnail((195, 185))
        x, y = (i % 6)*250, (i // 6)*210
        sheet.paste(im, (x+(250-im.width)//2, y))
        draw.text((x+10, y+188), case['id'], fill='black')
    sheet.save(root / f'gallery-{view}.jpg', quality=90)
