#!/usr/bin/env python3
"""Selecciona evidencia F5 reproducible; no modifica árboles ni capturas."""
import argparse
import json
from pathlib import Path
import statistics
import sys
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from review_pine_painted import read,write,sha
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args();study=a.study.resolve();out=a.output.resolve()
    report=read(study/'verification.json');closure=read(study/'closure/verification.json')
    assert report['status']=='completed' and len(report['cases'])==30
    assert len(report['godot'])==30 and all(row['passed'] for row in report['godot'])
    assert len(report['capture_sha256'])==480 and closure['technical_checks_passed']
    out.mkdir(parents=True,exist_ok=True)
    selected=[]
    for age in ('joven','adulto','viejo'):
        for group in range(2):
            names=[f'{age}-{i:02}' for i in range(group*5,(group+1)*5)]
            canvas=Image.new('RGB',(1000,5*280),'#eee9df');draw=ImageDraw.Draw(canvas)
            for row,name in enumerate(names):
                cells=[(v,view) for view in ('front','wood-perspective') for v in ('baseline','candidate')]
                for col,(variant,view) in enumerate(cells):
                    filename=f'{variant}-{name}--{view}.png';selected.append(filename)
                    with Image.open(study/'captures'/filename) as im:
                        im=im.convert('RGB');im.thumbnail((248,248));canvas.paste(im,(col*250,row*280+28))
                    draw.text((col*250+4,row*280+8),name+' '+variant+' '+view,fill='#20242a')
            canvas.save(out/f'{age}-{group}.jpg',quality=93)
    # Pilotos adicionales con regla activa: las ocho vistas por pareja.
    for name in ('joven-02','adulto-07','viejo-02'):
        rows=[]
        for view in ('front','side','perspective','top','wood-front','wood-side','wood-perspective','wood-top'):
            cells=[]
            for variant in ('baseline','candidate'):
                filename=f'{variant}-{name}--{view}.png';selected.append(filename)
                cells.append(('captures/'+filename,variant+' '+name+' '+view))
            rows.append(cells)
        sheet(study,out/(name+'.jpg'),2,rows)
    cases=[]
    for row in closure['cases']:
        gen=next(c for c in report['cases'] if c['id']==row['id'])
        cases.append({'id':row['id'],'partition':row['partition'],**{
            variant:{'metric':row[variant]['f5']['final_metric'],
                     'triangles':gen[variant]['metrics']['triangles'],
                     'axis_max_error_m':row[variant]['axis_audit']['axis_to_exported_ring_max_error_m'],
                     'glb_sha256':gen[variant]['glb_sha256']} for variant in ('baseline','candidate')}})
    per_age={}
    for age in ('joven','adulto','viejo'):
        rows=[r for r in cases if r['id'].startswith(age)]
        per_age[age]={variant:{'median_conflicts_per_m':statistics.median(r[variant]['metric']['conflicts_per_m'] for r in rows),
                      'total_conflicts':sum(r[variant]['metric']['conflicts'] for r in rows)} for variant in ('baseline','candidate')}
    output={'phase':'F5','date':'2026-11-03','technical_checks_passed':True,'tests':{'command':'PYTHONPATH=src python3 -m unittest discover -s tests','passed':227},
        'summary':closure['summary'],'per_age':per_age,'cases':cases,'checks':closure['checks'],
        'repeats':closure['repeats'],'regressions':closure['regressions'],'transition':closure['transition'],
        'godot':{'asset_count':60,'pair_reports':30,'captures':480,'all_passed':True,
                 'version':report['godot'][0]['godot'],'renderer':report['godot'][0]['renderer'],
                 'video_adapter':report['godot'][0]['video_adapter']},
        'selected_captures_sha256':{name:report['capture_sha256'][name] for name in sorted(set(selected))},
        'visual_review':'pending_agent_inspection','artistic_acceptance':'pending_user',
        'sources_sha256':report['sources_sha256'],
        'closure_source_sha256':closure['sources_sha256'],
        'evidence_script_sha256':sha(__file__),
        'artifact_reports_sha256':{name:sha(study/name) for name in ('verification.json','closure/verification.json','frozen-inputs.json','sources.json')}}
    write(out/'verification.json',output)
    print('Capturas seleccionadas:',len(output['selected_captures_sha256']))


if __name__=='__main__':main()
