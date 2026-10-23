#!/usr/bin/env python3
"""Selecciona evidencia compacta de RF0/RF1; no altera modelos ni capturas."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw


def sheet(study, output, columns, rows):
    canvas = Image.new('RGB', (400*columns, 435*len(rows)), '#e9edf1')
    draw = ImageDraw.Draw(canvas)
    for row, cells in enumerate(rows):
        for col, (path, label) in enumerate(cells):
            with Image.open(study/path) as original:
                image = original.convert('RGB')
                image.thumbnail((394, 394))
            canvas.paste(image, (col*400+(400-image.width)//2, row*435+32))
            draw.text((col*400+8, row*435+10), label, fill='#20242a')
    canvas.save(output, quality=92)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--references', type=Path, default=Path('artifacts/foliage-references'))
    args = parser.parse_args()
    study, output = args.study.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    summary = json.loads((study/'summary.json').read_text())
    assert summary['godot']['passed'] and summary['visual_captures_generated']
    selected = {key: value for key, value in summary.items() if key not in ('godot', 'export_validation')}
    selected['study'] = str(study)
    selected['export_validation'] = summary['export_validation']
    selected['godot'] = {key: value for key, value in summary['godot'].items() if key != 'assets'}
    selected['godot']['asset_triangles'] = {name: value['triangles'] for name, value in summary['godot']['assets'].items()}
    selected['evidence_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (output/'summary.json').write_text(json.dumps(selected, indent=2)+'\n')
    shutil.copy2(study/'reference/reference-lock.json', output/'reference-lock.json')
    shutil.copy2(study/'folded-hex/manifest.json', output/'folded-hex-manifest.json')
    shutil.copy2(study/'logs/tests.log', output/'unit-tests.txt')
    for name in ('robur-mpf.jpg', 'tuntorp-wcarter.jpg'):
        shutil.copy2(args.references/name, output/name)
    sheet(study, output/'variants.jpg', 3, [[(f'{name}/{view}.png', name+' | '+label)
        for name in ('diamond', 'hex', 'folded-hex')] for view, label in
        [('perspective', 'Blender'), ('side', 'Perfil'), ('godot-perspective', 'Godot'), ('godot-reverse', 'Godot reverso')]])
    sheet(study, output/'controls.jpg', 4, [[(f'{name}/perspective.png', label) for name, label in
        [('folded-hex', 'Base: .18m / .09m / 65 grados'), ('control-length', 'Largo .27m'),
         ('control-spacing', 'Separacion .06m'), ('control-inclination', 'Inclinacion 105 grados')]]])
    sheet(study, output/'rf0-views.jpg', 3, [[(f'reference/tree/{view}.png', label) for view, label in
        [('near', 'Q3 cerca: 50% del cuadro'), ('medium', 'Q3 media: 25%'), ('far', 'Q3 lejos: 10%')]],
        [('reference/tree/top.png', 'Copa desde arriba'), ('reference/tree/below.png', 'Copa desde abajo'),
         ('reference/branch/perspective.png', 'Rama q3:primary:100 congelada')]])
    print(output)


if __name__ == '__main__':
    main()
