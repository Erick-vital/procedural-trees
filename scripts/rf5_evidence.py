#!/usr/bin/env python3
"""Conserva evidencia RF5 seleccionada, sin duplicar modelos regenerables."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_blueprint_reference import read, write, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    study, output = args.study.resolve(), args.output.resolve()
    report = read(study / 'verification.json')
    output.mkdir(parents=True, exist_ok=False)
    report['study'] = str(study.relative_to(ROOT))
    report['evidence_script_sha256'] = sha(Path(__file__))
    report['case_counts'] = dict(Counter(c['status'] for c in report['cases'].values()))
    report['godot_asset_count'] = sum(len(g['assets']) for g in report['godot'])
    report['godot'] = [{**{k: v for k, v in g.items() if k != 'assets'},
                       'assets': {n: {k: v for k, v in c.items() if k != 'cameras'}
                                  for n, c in g['assets'].items()}} for g in report['godot']]
    for comparison in report['q3_comparison'].values():
        comparison['source'] = str(Path(comparison['source']).relative_to(ROOT))
    generated = [c for c in report['cases'].values() if c['status'] == 'generated']
    stats = {}
    for key in ('duration_seconds', 'glb_bytes', 'support_count', 'leaf_count'):
        values = [c[key] for c in generated]
        if values:
            stats[key] = {'min': min(values), 'median': statistics.median(values), 'max': max(values), 'sum': sum(values)}
    stats['triangles'] = {age: sorted({c['metrics']['triangles'] for c in generated if c['profile'] == age})
                          for age in ('joven', 'adulto', 'viejo')}
    report['summary_statistics'] = stats
    for filename in ('frozen-matrix.json',):
        shutil.copy2(study / filename, output / filename)
    for file in study.glob('*.jpg'):
        shutil.copy2(file, output / file.name)
    shutil.copy2(study / 'logs/tests.log', output / 'unit-tests.txt')
    write(output / 'q3-comparison.json', report.pop('q3_comparison'))
    report['selected_images_sha256'] = {p.name: sha(p) for p in sorted(output.glob('*.jpg'))}
    write(output / 'verification.json', report)
    print(report['case_counts'], report['godot_asset_count'], 'GLB Godot,',
          len(report.get('capture_files_sha256', {})), 'capturas', stats, flush=True)


if __name__ == '__main__':
    main()
