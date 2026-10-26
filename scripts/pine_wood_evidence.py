#!/usr/bin/env python3
"""Evidencia de madera optimizada y ajuste leve de copa 2.2.0."""
import argparse
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from painted_pine_evidence import audit
from pine_volume_evidence import coverage
from review_pine_painted import read,write


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();study=a.study.resolve();evidence=a.evidence.resolve()
    audit(study,evidence);r=read(study/'verification.json');rows={}
    for row in r['matrix']['cases']:
        name=row['id'];m=read(study/name/'manifest.json');old=read(study/('before-'+name)/'manifest.json')
        before_wood=old['metrics']['triangles_by_material']['Painted_Bark'];after_wood=m['metrics']['triangles_by_material']['Painted_Bark']
        entry={'wood_before':before_wood,'wood_after':after_wood,'total_before':old['metrics']['triangles'],'total_after':m['metrics']['triangles'],
               'maximum_sampled_surface_error_m':max(r['wood_surface_error_m'][name].values()),'views':{}}
        for view in ('front','side','perspective'):
            old_path=study/f'captures/before-{name}--{view}.png';new_path=study/f'captures/new-{name}--{view}.png'
            before=coverage(old_path);after=coverage(new_path)
            entry['views'][view]={'before_pixels':before,'after_pixels':after,'ratio':after/before}
            assert .85<after/before<1.01, 'El ajuste proyectado debe ser leve'
        rows[name]=entry
        assert before_wood>after_wood and entry['maximum_sampled_surface_error_m']<=.005001
        assert len(read(study/name/'placements.json'))==435
        assert sha_equal(study/('before-'+name)/'wood.glb',study/'godot'/('before-wood-'+name+'.glb'))
    shutil.copy2(study/'wood-comparison.jpg',evidence/'wood-comparison.jpg')
    write(evidence/'optimization.json',{'passed':True,'length_scale':.98,'width_scale':.94,'ring_tolerance_m':.005,
        'coverage_note':'Máscara RGB >20 del fondo, cámaras comunes; cobertura proyectada, no volumen físico.','cases':rows})
    html=study/'index.html';content=html.read_text()
    content=content.replace('<h1>PP4 · Pino pintado completo</h1>','<h1>Pino 2.2.0 · madera optimizada y copa ligeramente más ligera</h1><p>before-: 2.1.0; new-: 2.2.0; wood-: madera nueva; before-wood-: madera anterior. <a href="wood-comparison.jpg">Comparación de madera</a></p>')
    html.write_text(content)
    print('Optimización y copa leve auditadas en cuatro casos.')


def sha_equal(a,b):
    from review_pine_painted import sha
    return sha(a)==sha(b)

if __name__=='__main__':main()
