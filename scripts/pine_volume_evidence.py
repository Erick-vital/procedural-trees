#!/usr/bin/env python3
"""Comparación PP4 2.0.0/2.1.0 con cámaras comunes y cobertura proyectada."""
import argparse
from pathlib import Path
import sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from painted_pine_evidence import audit
from review_pine_painted import read,write
from foliage_evidence import sheet


def coverage(path,top=False):
    im=Image.open(path).convert('RGB')
    if top:im=im.crop((0,80,900,340))
    bg=(238,233,223)
    return sum(max(abs(c-b) for c,b in zip(pixel,bg))>20 for pixel in im.getdata())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();study=a.study.resolve();evidence=a.evidence.resolve()
    audit(study,evidence)
    cases=read(study/'verification.json')['matrix']['cases'];rows={}
    for row in cases:
        name=row['id'];rows[name]={}
        for view in ('front','side','perspective'):
            old=study/f'captures/before-{name}--{view}.png';new=study/f'captures/new-{name}--{view}.png'
            before=coverage(old);after=coverage(new)
            entry={'before_pixels':before,'after_pixels':after,'ratio':after/before}
            if view in ('front','side'):
                entry['upper_before_pixels']=coverage(old,True);entry['upper_after_pixels']=coverage(new,True)
                entry['upper_ratio']=entry['upper_after_pixels']/entry['upper_before_pixels']
            rows[name][view]=entry
    assert all(v['ratio']>1 for case in rows.values() for v in case.values())
    assert all(v.get('upper_ratio',2)>1 for case in rows.values() for v in case.values())
    write(evidence/'coverage.json',{'passed':True,'threshold_rgb_max':20,'background_rgb':[238,233,223],
        'upper_roi_pixels':[0,80,900,340],'note':'Cobertura proyectada de madera y follaje, no volumen físico ni aceptación artística. ROI común en frente/perfil, aproximadamente tercio superior.','cases':rows})
    sheet(study,evidence/'upper.jpg',4,[[(f'captures/{kind}-{r["id"]}--{view}.png',kind+' '+r['id']+' | '+view) for r in cases] for view in ('front','side') for kind in ('before','new')])
    print('Cobertura: incremento en los cuatro casos y vistas; consultar coverage.json')

if __name__=='__main__':main()
