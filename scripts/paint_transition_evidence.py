#!/usr/bin/env python3
"""Láminas de revisión temporal desde capturas T3 existentes, sin render nuevo."""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw


def build(output):
    r=json.loads((output/'verification.json').read_text())
    if not r['passed']:raise ValueError('Ensayo no verificado')
    for stage in ('fixed','orbit'):
        sheet=Image.new('RGB',(11*150,11*170),'#eee9df');draw=ImageDraw.Draw(sheet)
        for i in range(121):
            with Image.open(output/'captures'/stage/f'{stage}-{i:03}.png') as source:
                im=source.convert('RGB');im.thumbnail((150,150))
            x=(i%11)*150;y=(i//11)*170
            sheet.paste(im,(x,y+20));draw.text((x+4,y+4),f'{i:03} p={i/120:.3f}',fill='#29221b')
        sheet.save(output/(stage+'-timeline.jpg'),quality=93)
        deltas=r['sequence_metrics'][stage]['adjacent_mean_abs_rgb_0_255']
        i=max(range(len(deltas)),key=deltas.__getitem__)+1
        sheet=Image.new('RGB',(1260,450),'#eee9df');draw=ImageDraw.Draw(sheet)
        for col,j in enumerate((i-1,i,i+1)):
            with Image.open(output/'captures'/stage/f'{stage}-{j:03}.png') as source:
                im=source.convert('RGB');im.thumbnail((420,420))
            sheet.paste(im,(420*col,30))
            draw.text((420*col+5,9),f'{stage}: cuadro {j} | p={r["godot"][stage]["frames"][j]["phase"]:.4f}',fill='#29221b')
        sheet.save(output/f'{stage}-largest-change.jpg',quality=94)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();build(a.output.resolve())
