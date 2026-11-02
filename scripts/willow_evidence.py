#!/usr/bin/env python3
"""Seleccionar evidencia de los cuatro sauces y comprobar sus hashes."""
import argparse
from pathlib import Path
import shutil

from foliage_evidence import sheet
from review_pine_painted import read, write, sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cli', required=True, type=Path)
    parser.add_argument('--defects', required=True, type=Path)
    args = parser.parse_args()
    study, out = args.study.resolve(), args.output.resolve()
    report = read(study/'verification.json')
    assert report['passed'] and len(report['captures']) == report.get('capture_count_expected', 120)
    assert all(sha(ROOT/p) == digest for p, digest in report['source_lock'].items())
    assert all(sha(study/'captures'/p) == digest for p, digest in report['captures'].items())
    assert all(sha(study/name/'tree.glb') == info['glb_sha256'] for name, info in report['cases'].items())
    cli = read(args.cli/'manifest.json')
    assert cli['status'] == 'completed' and cli['glb_sha256'] == report['cases']['pilot']['glb_sha256']
    assert all((args.cli/(name+'.png')).is_file() for name in cli['required_views'])
    defects = read(args.defects/'report.json')
    assert defects['passed'] and defects['source_glb_sha256'] == report['cases']['pilot']['glb_sha256']
    out.mkdir(parents=True, exist_ok=True)
    for name in ('tree-views.jpg', 'tree-distances.jpg', 'wood-views.jpg', 'wood-distances.jpg'):
        shutil.copy2(study/name, out/name)
    if (study/'comparison.jpg').exists():
        shutil.copy2(study/'comparison.jpg', out/'comparison.jpg')
    for kind in ('tree', 'wood'):
        sheet(study, out/(kind+'-details.jpg'), 4,
              [[(f'captures/{kind}-{row["id"]}--{view}.png', row['id']+' | '+view)
                for row in report['matrix']['cases']]
               for view in ('lateral', 'backlit', 'shadow', 'fork-close', 'canopy-close')])
    shutil.copy2(study/'captures/tree-pilot--perspective.png', out/'sauce.png')
    shutil.copy2(study/'captures/tree-pilot--fork-close.png', out/'bifurcacion.png')
    report['study'] = str(study.relative_to(ROOT))
    report['evidence_script_sha256'] = sha(Path(__file__))
    report['cli'] = {'glb_identical_to_pilot': True, 'required_views': cli['required_views'],
                     'generation_seconds': cli['duration_seconds'], 'glb_sha256': cli['glb_sha256']}
    report['defect_audit'] = defects
    report['selected_images_sha256'] = {p.name: sha(p) for p in sorted(out.iterdir()) if p.suffix in ('.jpg', '.png')}
    write(out/'verification.json', report)
    print('Evidencia seleccionada:', out)


if __name__ == '__main__':
    main()
