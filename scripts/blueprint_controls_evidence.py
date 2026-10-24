#!/usr/bin/env python3
"""B3: evidencia compacta y comparación opcional contra los GLB Q3 históricos."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from treegen.foliage_twigs_evaluation import inspect_twigs_glb
from treegen.evaluation import validate_result
from verify_blueprint_reference import read, write, sha
from foliage_evidence import sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--q3-reference', type=Path)
    args = parser.parse_args()
    study, output = args.study.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = read(study / 'verification.json')
    # No exige passed: preservar fallos es parte del entregable B3.
    assert report['matrix_executed'] and report['visual_requested']
    report['case_counts'] = dict(Counter(c['status'] for c in report['cases'].values()))
    report['study'] = str(study.relative_to(ROOT))
    report['evidence_script_sha256'] = sha(Path(__file__))
    report['godot'] = [{k:v for k,v in g.items() if k!='assets'} for g in report['godot']]
    report['capture_count'] = len(list((study/'inspection').glob('*/godot-*.png')))
    report['capture_files_sha256'] = {str(p.relative_to(study)):sha(p) for p in sorted((study/'inspection').glob('*/godot-*.png'))}
    names = ['viejo-00','viejo-03','adulto-00','joven-00','viejo-07','adulto-07','joven-07']
    historical = {}
    for name,c in report['cases'].items():
        if c['status']=='generated':
            validate_result(study/name)
    if args.q3_reference:
        for name in names:
            original = args.q3_reference.resolve() / name
            a,b = read(original/'manifest.json'),read(study/name/'manifest.json')
            x = inspect_twigs_glb(original/'tree.glb', a['metrics'])
            y = b['export_validation']
            historical[name] = {'source':str(original.relative_to(ROOT)), 'glb_sha256':sha(original/'tree.glb'),
                'same_base_spec':a['spec']==b['base_spec'],
                'geometry_normals_equal':x['channel_sha256']['Oak_Bark']==y['channel_sha256']['Oak_Bark'],
                'bark_material_equal':x['material_properties_sha256']['Oak_Bark']==y['material_properties_sha256']['Oak_Bark']}
        assert all(all(row[k] for k in ('same_base_spec','geometry_normals_equal','bark_material_equal')) for row in historical.values())
        write(output/'q3-comparison.json',historical)
    for name in ('frozen-matrix.json','ages.jpg','controls.jpg'):
        shutil.copy2(study/name,output/name)
    sheet(study,output/'age-views.jpg',4,[[(f'inspection/{n}/godot-{v}.png',n+' | '+v)
        for v in ('side','top','below','medium')] for n in names])
    # Perfiles de edad y escala común; ampliación seleccionada de la generación real.
    sheet(study,output/'overview.jpg',4,[[(f'inspection/{n}/godot-{v}.png',n+' | '+v)
        for n in ('pilot','viejo-00','adulto-00','joven-00')] for v in ('near','top','below')])
    for name,c in report['cases'].items():
        if c['status']=='failed':
            folder = study/name
            diagnostic=folder/'contact-diagnostic.json'
            if diagnostic.exists(): shutil.copy2(diagnostic,output/(name+'-diagnostic.json'))
            shutil.copy2(folder/'manifest.json',output/(name+'-failure.json'))
    report['godot_asset_count']=sum(len(g['assets']) for g in read(study/'verification.json')['godot'])
    report['selected_images_sha256'] = {p.name:sha(p) for p in output.glob('*.jpg')}
    write(output/'verification.json', report)
    print(report['case_counts'],report['capture_count'],'capturas')


if __name__ == '__main__':
    main()
