#!/usr/bin/env python3
"""Selecciona evidencia B4, sin alterar modelos ni escenas verificadas."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'),str(ROOT/'scripts')]
from PIL import Image, ImageChops
from treegen.foliage_canopy import diamond_vertices
from treegen.evaluation import validate_result
from verify_blueprint_reference import read, write, sha
from foliage_evidence import sheet


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    study,output=args.study.resolve(),args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    report=read(study/'verification.json')
    assert report['matrix_executed'] and report['visual_requested']
    report['study']=str(study.relative_to(ROOT))
    report['case_counts']=dict(Counter(c['status'] for c in report['cases'].values()))
    manifests={}
    for n,c in report['cases'].items():
        if c['status']=='generated':
            validate_result(study/n)
            manifests[n]=read(study/n/'manifest.json')
            points=[v for leaf in manifests[n]['placements'] for v in diamond_vertices(leaf)]
            report['cases'][n]['foliage_span_m']=[max(v[k] for v in points)-min(v[k] for v in points) for k in range(3)]
    names=['pilot','control-01','control-02','control-03']
    report['control_glb_hashes_distinct']=len({manifests[n]['glb_sha256'] for n in names})==4
    report['control_wood_hashes_distinct']=len({manifests[n]['wood_sha256'] for n in names})==4
    report['godot_asset_count']=sum(len(g['assets']) for g in report['godot'])
    report['godot']=[{k:v for k,v in g.items() if k!='assets'} for g in report['godot']]
    captures=sorted((study/'inspection').glob('*/godot-*.png'))
    report['capture_count']=len(captures)
    margins=[]
    for path in captures:
        with Image.open(path) as original:
            image=original.convert('RGB')
            box=ImageChops.difference(image,Image.new('RGB',image.size,image.getpixel((0,0)))).getbbox()
            assert box is not None, 'Captura vacía: '+str(path)
            margins.append(min(box[0],box[1],image.width-box[2],image.height-box[3]))
    assert min(margins)>0, 'Captura con objeto cortado en el borde'
    report['capture_content_checks']={'all_nonblank':True,'minimum_background_margin_px':min(margins)}
    report['captures_sha256']={str(p.relative_to(study)):sha(p) for p in captures}
    report['evidence_script_sha256']=sha(Path(__file__))
    for filename in ('frozen-matrix.json','comparison.jpg','controls.jpg','wood.jpg','export-contacts.json'):
        shutil.copy2(study/filename,output/filename)
    shutil.copy2(study/'logs/tests.log',output/'unit-tests.txt')
    sheet(study,output/'identity.jpg',2,[[(f'inspection/{n}/godot-{v}.png',n+' | '+v)
        for n in ('first-reference','pilot')] for v in ('front','side','below','perspective')])
    sheet(study,output/'same-seed.jpg',2,[[(f'inspection/{n}/godot-{v}.png',n+' | '+v)
        for n in ('wide-same-seed','pilot')] for v in ('front','side','top','below')])
    sheet(study,output/'scales.jpg',4,[[(f'inspection/{n}/godot-{v}.png',n+' | '+v)
        for n in names] for v in ('near','medium','far')])
    sheet(study,output/'wood-comparison.jpg',2,[[(f'inspection/{n}-wood/godot-{v}.png',n+' madera | '+v)
        for n in ('wide-same-seed','pilot')] for v in ('front','side','perspective')])
    report['images_sha256']={p.name:sha(p) for p in output.glob('*.jpg')}
    write(output/'generation-provenance.json',{n:{k:m[k] for k in (
        'resolved_blueprint','adapter_version','sources_sha256','glb_sha256','duration_seconds','glb_bytes',
        'surface_projection','contacts','base_generation','external_geometry_inputs')} for n,m in manifests.items()})
    write(output/'verification.json',report)
    print(report['case_counts'],report['capture_count'],'capturas; passed='+str(report['passed']))


if __name__=='__main__':
    main()
