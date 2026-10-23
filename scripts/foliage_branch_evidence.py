#!/usr/bin/env python3
"""Selecciona comparaciones RF2 y conserva evidencia compacta reproducible."""
import argparse
import json
from pathlib import Path
import shutil

from foliage_evidence import sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    study, output = args.study.resolve(), args.output.resolve()
    summary = json.loads((study/'summary.json').read_text())
    assert summary['godot']['passed'] and summary['visual_captures_generated']
    output.mkdir(parents=True, exist_ok=True)
    reduced = {key: value for key, value in summary.items() if key not in ('godot', 'exports', 'capture_visible_pixels')}
    reduced['study'] = str(study)
    reduced['exported_wood_sha256'] = summary['exports']['reference']['exported_wood_sha256']
    reduced['bark_material_sha256'] = summary['exports']['reference']['bark_material_sha256']
    reduced['godot'] = {key: value for key, value in summary['godot'].items() if key != 'assets'}
    reduced['godot']['asset_triangles'] = {name: item['triangles'] for name, item in summary['godot']['assets'].items()}
    reduced['capture_count'] = len(summary['capture_visible_pixels'])
    reduced['capture_min_visible_pixels'] = min(summary['capture_visible_pixels'].values())
    (output/'summary.json').write_text(json.dumps(reduced, indent=2)+'\n')
    shutil.copy2(study/'reference/reference.json', output/'reference-lock.json')
    shutil.copy2(study/'longitudinal-r0-medium.json', output/'longitudinal-medium-spec.json')
    shutil.copy2(study/'logs/tests.log', output/'unit-tests.txt')
    names = ['reference', 'longitudinal-r0-medium', 'terminal-r0-medium']
    sheet(study, output/'comparison.jpg', 3, [[(f'{name}/{view}.png', label+' | '+name)
        for name in names] for view, label in [('perspective', 'Blender'), ('below', 'Desde abajo'),
            ('detail-perspective', 'Detalle'), ('godot-detail-perspective', 'Godot detalle')]])
    sheet(study, output/'matrix.jpg', 3, [[(f'{pattern}-r{roll}-{density}/perspective.png', f'{pattern} giro {roll} | {density}')
        for density in ('low', 'medium', 'high')] for roll in (0, 70) for pattern in ('longitudinal', 'terminal')])
    sheet(study, output/'controls.jpg', 4, [[(f'{name}/detail-perspective.png', label) for name, label in
        [('longitudinal-r0-medium', 'Base .24m / 16 soportes / .55m'), ('control-size', 'Largo de hoja .32m'),
         ('control-count', '20 soportes'), ('control-length', 'Largo de soporte .35m')]]])
    sheet(study, output/'supports.jpg', 2, [[(f'{name}/{suffix}/detail-perspective.png' if suffix else f'{name}/detail-perspective.png', name+' | '+label)
        for suffix, label in [('', 'Exportado'), ('supports-debug', 'Recorridos: solo diagnostico')]]
        for name in ('longitudinal-r0-medium', 'control-length')])
    print(output)


if __name__ == '__main__':
    main()
