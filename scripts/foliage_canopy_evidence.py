#!/usr/bin/env python3
"""Selecciona evidencia RF3 de capturas reales y referencias reproducibles."""
import argparse
import json
from pathlib import Path
import shutil

from foliage_evidence import sheet
from verify_foliage_branch import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    study, output = args.study.resolve(), args.output.resolve()
    summary = json.loads((study/'summary.json').read_text())
    assert summary['godot']['passed'] and summary['visual_captures_generated']
    output.mkdir(parents=True, exist_ok=True)
    selected = {k: v for k, v in summary.items() if k not in ('godot', 'capture_visible_pixels')}
    selected['study'] = str(study)
    selected['evidence_script_sha256'] = sha(Path(__file__))
    selected['godot'] = {k: v for k, v in summary['godot'].items() if k != 'assets'}
    selected['godot']['asset_triangles'] = {k: v['triangles'] for k, v in summary['godot']['assets'].items()}
    selected['capture_count'] = len(summary['capture_visible_pixels'])
    selected['capture_min_visible_pixels'] = min(summary['capture_visible_pixels'].values())
    (output/'summary.json').write_text(json.dumps(selected, indent=2, allow_nan=False)+'\n')
    ref = json.loads((study/'reference/reference.json').read_text())
    lock = {k: ref[k] for k in ('version', 'case', 'source', 'source_files_sha256', 'rf0_sha256',
        'rf2_acceptance_sha256', 'accepted_rf2_spec', 'spec', 'seeds', 'normalization', 'matrix_world',
        'wood_sha256', 'wood_material', 'wood_triangles', 'molds_sha256', 'profile_center_m',
        'profile_bounds_m', 'height_m', 'max_reconstruction_error_m', 'cameras', 'lighting')}
    lock.update(branch_count=len(ref['branches']), mold_count=len(ref['molds']),
                guide_triangles=sum(len(m['triangles']) for m in ref['molds']))
    (output/'reference-lock.json').write_text(json.dumps(lock, indent=2, allow_nan=False)+'\n')
    for name in ('pilot', 'wider', 'open-east', 'leaf-size'):
        shutil.copy2(study/(name+'.json'), output/(name+'-spec.json'))
    shutil.copy2(study/'logs/tests.log', output/'unit-tests.txt')
    sheet(study, output/'comparison.jpg', 2, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for name in ('reference', 'pilot')] for view in ('front', 'perspective', 'top', 'below')])
    sheet(study, output/'controls.jpg', 3, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for name in ('pilot', 'wider', 'open-east')] for view in ('front', 'top', 'below', 'perspective')])
    sheet(study, output/'scales.jpg', 3, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for view in ('near', 'medium', 'far')] for name in ('reference', 'pilot')])
    sheet(study, output/'detail.jpg', 2, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for name in ('reference', 'pilot')] for view in ('detail-top', 'detail-below', 'detail-perspective')])
    sheet(study, output/'leaf-size.jpg', 2, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for name in ('pilot', 'leaf-size')] for view in ('perspective', 'detail-perspective')])
    sheet(study, output/'masks.jpg', 2, [[(f'{name}/masks/{view}.png', name+' | '+view)
        for name in ('reference', 'pilot')] for view in ('front', 'side', 'top')])
    print(output)


if __name__ == '__main__':
    main()
