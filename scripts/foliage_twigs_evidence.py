#!/usr/bin/env python3
"""Selecciona capturas reales de la revisión RF2, sin modificar los modelos."""
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
    selected = {key: value for key, value in summary.items() if key not in ('exports', 'godot', 'capture_visible_pixels')}
    selected['study'] = str(study)
    selected['evidence_script_sha256'] = sha(Path(__file__))
    selected['exports'] = {name: {key: item[key] for key in ('triangles', 'materials', 'exported_wood_sha256',
        'bark_material_sha256', 'channel_sha256', 'material_properties_sha256')} for name, item in summary['exports'].items()}
    selected['godot'] = {key: value for key, value in summary['godot'].items() if key != 'assets'}
    selected['godot']['asset_triangles'] = {name: value['triangles'] for name, value in summary['godot']['assets'].items()}
    selected['capture_count'] = len(summary['capture_visible_pixels'])
    selected['capture_min_visible_pixels'] = min(summary['capture_visible_pixels'].values())
    (output/'summary.json').write_text(json.dumps(selected, indent=2, allow_nan=False)+'\n')
    shutil.copy2(study/'reference/target.json', output/'target-lock.json')
    shutil.copy2(study/'logs/tests.log', output/'unit-tests.txt')
    shutil.copy2(study/'directed-12.json', output/'directed-12-spec.json')
    sheet(study, output/'connection.jpg', 3, [[(f'{name}/godot-{view}.png', label+' | '+name)
        for name in ('reference', 'without-twigs', 'with-twigs')] for view, label in
        [('detail-perspective', 'Detalle Godot'), ('detail-below', 'Desde abajo'), ('perspective', 'Escala general')]])
    sheet(study, output/'distribution.jpg', 4, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for name in ('reference', 'with-twigs', 'directed-16', 'directed-12')]
        for view in ('front', 'side', 'top', 'below', 'perspective', 'reverse')])
    sheet(study, output/'controls.jpg', 4, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for name in ('directed-12', 'control-size', 'control-density', 'control-radius')]
        for view in ('detail-perspective', 'perspective')])
    sheet(study, output/'reach.jpg', 3, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for name in ('directed-12', 'control-length', 'control-reach-same-count')]
        for view in ('top', 'below', 'detail-perspective')])
    sheet(study, output/'scales.jpg', 3, [[(f'{name}/godot-{view}.png', name+' | '+view)
        for view in ('near', 'medium', 'far')]
        for name in ('reference', 'with-twigs', 'directed-12', 'control-reach-same-count')])
    print(output)


if __name__ == '__main__':
    main()
