#!/usr/bin/env python3
"""Evidencia seleccionada de moldes Q3, con capturas Godot originales."""
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
    s = json.loads((study/'summary.json').read_text())
    assert s['godot']['passed'] and s['visual_captures_generated']
    output.mkdir(parents=True, exist_ok=True)
    selected = {k: v for k, v in s.items() if k not in ('exports', 'godot', 'capture_visible_pixels')}
    selected['study'] = str(study)
    selected['evidence_script_sha256'] = sha(Path(__file__))
    selected['exported_wood_sha256'] = s['exports']['reference']['exported_wood_sha256']
    selected['bark_material_sha256'] = s['exports']['reference']['bark_material_sha256']
    selected['godot'] = {k: v for k, v in s['godot'].items() if k != 'assets'}
    selected['godot']['asset_triangles'] = {k: v['triangles'] for k, v in s['godot']['assets'].items()}
    selected['capture_count'] = len(s['capture_visible_pixels'])
    selected['capture_min_visible_pixels'] = min(s['capture_visible_pixels'].values())
    (output/'summary.json').write_text(json.dumps(selected, indent=2, allow_nan=False)+'\n')
    if s['version'] == 'foliage-molds-0.1.2':
        for source, dest in [('molds/molds.json', 'molds-lock.json'), ('logs/tests.log', 'unit-tests.txt'),
                             ('leaves-144.json', 'density-144-spec.json'), ('leaves-192.json', 'density-192-spec.json')]:
            shutil.copy2(study/source, output/dest)
        names = ('base-96', 'leaves-120', 'leaves-144', 'leaves-192')
        views = ('perspective', 'top', 'below', 'detail-perspective', 'detail-below')
        sheet(study, output/'density.jpg', 4, [[(f'{name}/godot-{view}.png', name+' | '+view)
            for name in names] for view in views])
        sheet(study, output/'angles.jpg', 4, [[(f'{name}/godot-{view}.png', name+' | '+view)
            for name in names] for view in ('front', 'side', 'reverse')])
        sheet(study, output/'scales.jpg', 3, [[(f'{name}/godot-{view}.png', name+' | '+view)
            for view in ('near', 'medium', 'far')] for name in names])
        sheet(study, output/'masks.jpg', 4, [[(f'{name}/masks/{view}.png', name+' | '+view)
            for name in names] for view in ('front', 'side', 'top')])
        print(output)
        return
    for source, dest in [('molds/molds.json', 'molds-lock.json'), ('logs/tests.log', 'unit-tests.txt'),
                         ('large.json', 'hex-spec.json'), ('efficient-100.json', 'diamond-spec.json')]:
        shutil.copy2(study/source, output/dest)
    views = ['perspective', 'top', 'below', 'detail-perspective', 'detail-below']
    sheet(study, output/'hexagons.jpg', 3, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for name in ('reference', 'small', 'large')] for view in views])
    sheet(study, output/'diamonds.jpg', 3, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for name in ('reference', 'efficient-080', 'efficient-100')] for view in views])
    sheet(study, output/'angles.jpg', 4, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for name in ('reference', 'previous', 'large', 'efficient-100')]
        for view in ('front', 'side', 'reverse')])
    sheet(study, output/'scales.jpg', 3, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for view in ('near', 'medium', 'far')]
        for name in ('reference', 'previous', 'large', 'efficient-100')])
    sheet(study, output/'masks.jpg', 4, [[(f'{name}/masks/{view}.png', name+' | '+view)
        for name in ('reference', 'previous', 'large', 'efficient-100')]
        for view in ('front', 'side', 'top')])
    print(output)


if __name__ == '__main__':
    main()
