#!/usr/bin/env python3
"""Selección visual T4 desde PNG auditados; no vuelve a generar mallas."""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw

VARIANTS=['original','n35','n65']
LABELS=['Originales','Volumen local .35','Volumen local .65']


def sheet(output,target,entries,width=350):
    image=Image.new('RGB',(3*width,len(entries)*(width+30)),'#eee9df');draw=ImageDraw.Draw(image)
    for row,(scope,season,shot,label) in enumerate(entries):
        for col,(variant,title) in enumerate(zip(VARIANTS,LABELS)):
            path=output/'captures'/(scope+'-'+season)/f'{scope}-{variant}-{season}-{shot}.png'
            with Image.open(path) as source:
                im=source.convert('RGB');im.thumbnail((width,width))
            image.paste(im,(col*width,row*(width+30)+30))
            draw.text((col*width+4,row*(width+30)+9),f'{title} | {label}',fill='#29221b')
    image.save(target,quality=94)


def build(output):
    if not json.loads((output/'verification.json').read_text())['passed']:raise ValueError('Ensayo sin verificar')
    folder=output/'review';folder.mkdir(exist_ok=True)
    names=['frente','lateral','perspectiva','dorso','arriba','abajo']
    for scope in ['branch','pilot']:
        for season in ['summer','autumn']:
            for light in range(3):
                sheet(output,folder/f'{scope}-{season}-light-{light}.jpg',[(scope,season,f'l{light}-v{v}-d0',f'{names[v]} | luz {light}') for v in range(6)])
                sheet(output,folder/f'{scope}-{season}-distances-{light}.jpg',[(scope,season,f'l{light}-v2-d{d}',f'distancia {d} | luz {light}') for d in range(3)])
    sheet(output,output/'comparison.jpg',[(scope,season,'l0-v2-d0',scope+' | '+season) for scope in ['branch','pilot'] for season in ['summer','autumn']],450)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build(a.output.resolve())
