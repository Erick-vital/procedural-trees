#!/usr/bin/env python3
"""Construye, importa, captura y audita cuatro variantes estacionales en Godot."""
import argparse
import os
from pathlib import Path
import tempfile
from PIL import Image, ImageChops, ImageDraw

from build_seasonal_oak import ROOT, build, read, sha, write
from review_pine_painted import run
from verify_foliage_unit import GODOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT/'artifacts/roble-pintado/integracion-madera-01')
    args = parser.parse_args()
    output = args.output.resolve()
    manifest = build(args.source.resolve(), output, ROOT/'configs/seasons/roble-otono-v1.json')
    captures = output/'captures'
    captures.mkdir()
    logs = output/'logs'
    logs.mkdir()
    project = output/'godot'
    godot = os.environ.get('GODOT_BIN', GODOT)
    run([godot, '--headless', '--path', project, '--editor', '--import'], logs/'import.log', os.environ)
    run([godot, '--path', project, '--audio-driver', 'Dummy', '--script', 'res://review_seasonal_tree.gd', '--', captures], logs/'review.log', os.environ)
    report = read(captures/'godot-report.json')
    checks = {'godot': report['passed'], '64-captures': len(report['captures']) == 64}
    for item in manifest['cases']:
        name = item['id']
        checks[name+'-base-exact'] = sha(project/(name+'.glb')) == item['base_glb_sha256']
        for season in ('summer', 'autumn'):
            a = Image.open(captures/f'{name}-{season}-perspective.png').convert('RGB')
            b = Image.open(captures/f'{name}-{season}-repeat.png').convert('RGB')
            checks[name+'-'+season+'-repeat-exact'] = ImageChops.difference(a, b).getbbox() is None
        a = Image.open(captures/f'{name}-summer-perspective.png').convert('RGB')
        b = Image.open(captures/f'{name}-autumn-perspective.png').convert('RGB')
        checks[name+'-visible-change'] = ImageChops.difference(a, b).getbbox() is not None
    with tempfile.TemporaryDirectory(prefix='oak-season-', dir='/tmp') as tmp:
        repeated = build(args.source.resolve(), Path(tmp)/'repeat', ROOT/'configs/seasons/roble-otono-v1.json')
        checks['package-deterministic'] = repeated == manifest
    # Láminas de comparación; imágenes fuente son renders reales, sin retoque.
    for title, views, names in [('comparison', ['perspective'], ['pilot']),
                                ('controls', ['perspective', 'back'], [x['id'] for x in manifest['cases']]),
                                ('distances', ['below', 'medium', 'far'], ['pilot'])]:
        sheet = Image.new('RGB', (900, 480*len(views)*len(names)), '#EEE9DF')
        draw = ImageDraw.Draw(sheet)
        for row, (name, view) in enumerate((n, v) for n in names for v in views):
            for column, season in enumerate(('summer', 'autumn')):
                im = Image.open(captures/f'{name}-{season}-{view}.png').convert('RGB')
                im.thumbnail((450, 450))
                sheet.paste(im, (column*450, row*480+30))
                draw.text((column*450+10, row*480+9), f'{name} | {season} | {view}', fill='#29221B')
        sheet.save(output/(title+'.jpg'), quality=93)
    report.update({'checks': checks, 'passed': all(checks.values()),
                   'capture_sha256': {n: sha(captures/n) for n in report['captures']}})
    write(output/'verification.json', report)
    assert report['passed'], [k for k, v in checks.items() if not v]
    print(f'{len(checks)} comprobaciones; 64 capturas. {output}')


if __name__ == '__main__':
    main()
