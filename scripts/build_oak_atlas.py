#!/usr/bin/env python3
"""Atlas procedural RGBA: cuatro pinturas de rombo RF3, máscara analítica fija."""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SIZE=1024
TILE=512
PAD=8


def alpha_at(x,y):
    # Intersección de cuatro semiplanos: rombo (0,0),(.48,±.3),(1,0).
    distance=min(x,1-x,.625*x-abs(y),(.3/.52)*(1-x)-abs(y))
    return max(0,min(255,round(127.5+distance*(TILE-2*PAD)/1.2*255)))


def main():
    out=ROOT/'assets/roble-pintado/v0.1.0';out.mkdir(parents=True,exist_ok=True)
    im=Image.new('RGBA',(SIZE,SIZE));pixels=im.load()
    for variant in range(4):
        col,row=variant%2,variant//2
        for py in range(TILE):
            y=(.5-(py-PAD)/(TILE-2*PAD))*1.2
            for px in range(TILE):
                x=-.04+(px-PAD)/(TILE-2*PAD)*1.08
                if not PAD<=px<=TILE-PAD or not PAD<=py<=TILE-PAD:continue
                broad=.04*math.sin(18*x+variant)+.025*math.sin(54*x+31*y+variant*2)
                brush=.018*math.sin(171*x+46*y)+.012*math.cos(119*x-67*y+variant)
                vein=math.exp(-((y-.004*math.sin(x*5))/.006)**2)
                side=0
                for k in range(5):
                    origin=.13+k*.15
                    along=x-origin
                    if 0<along<.32:side=max(side,math.exp(-((abs(y)-along*.67)/.0035)**2))
                factor=1+broad+brush+.055*math.sin(math.pi*x)-.10*vein+.055*side
                # Colores sRGB próximos al verde lineal .23/.43/.065 aprobado.
                color=[round(max(0,min(255,c*factor))) for c in (130+variant,175-variant,72+variant)]
                pixels[col*TILE+px,row*TILE+py]=(*color,alpha_at(x,y))
    path=out/'foliage.png';im.save(path)
    manifest={'version':'oak-painted-atlas-0.1.0','source':'scripts/build_oak_atlas.py','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'method':'Procedural propio: rombo analítico RF3, cuatro variantes de pintura/nervaduras; sin IA ni recursos externos.',
        'size':[SIZE,SIZE],'tiles':4,'tile_size':TILE,'padding_px':PAD,
        'shape_local':[[0,0],[.48,-.3],[1,0],[.48,.3]],'local_extent':[[-.04,-.6],[1.04,.6]],
        'foliage_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(path,flush=True)

if __name__=='__main__':main()
