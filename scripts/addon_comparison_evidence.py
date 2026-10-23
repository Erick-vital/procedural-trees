#!/usr/bin/env python3
"""Galería y evidencia seleccionada de seis árboles bajo el mismo protocolo."""
import argparse
import json
from pathlib import Path
import shutil

from foliage_evidence import sheet


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    study, output = args.study.resolve(), args.output.resolve()
    summary = json.loads((study/'summary.json').read_text())
    assert summary['godot']['passed'] and summary['visual_captures_generated']
    output.mkdir(parents=True, exist_ok=True)
    rows = [[(f'comparison/{engine}-{age}/godot-perspective.png', f'{engine} | {age}')
        for engine in ('q3', 'easy', 'sapling')] for age in ('adulto', 'viejo')]
    sheet(study, output/'godot-perspective.jpg', 3, rows)
    for view, name in [('godot-front', 'godot-front.jpg'), ('godot-below', 'godot-below.jpg'),
                        ('godot-top', 'godot-top.jpg'), ('perspective', 'blender-perspective.jpg'),
                        ('wood-only/perspective', 'wood-only.jpg')]:
        sheet(study, output/name, 3, [[(f'comparison/{engine}-{age}/{view}.png', f'{engine} | {age}')
            for engine in ('q3', 'easy', 'sapling')] for age in ('adulto', 'viejo')])
    selected = {}
    for age in ('adulto', 'viejo'):
        for engine in ('q3', 'easy', 'sapling'):
            name = engine+'-'+age
            m = json.loads((study/'comparison'/name/'manifest.json').read_text())
            original = m['original_manifest']
            selected[name] = {'engine': engine, 'age': age, 'metrics': m['metrics'],
                'projected_height_fractions': m['projected_height_fractions'],
                'presentation_smooth_faces_flattened': m['presentation_smooth_faces_flattened'],
                'source_files_sha256': m['source_files_sha256'],
                # Q3 conserva un tiempo histórico de otro ejecutor/alcance;
                # no mezclarlo con el cronómetro interno de estos adaptadores.
                'generation_seconds': original.get('duration_seconds') if engine != 'q3' else None,
                'normalization': original.get('normalization'),
                'attempt_id': original.get('attempt', {}).get('id'),
                'repeat_matches': engine == 'q3' or summary['config']['selection'][age][engine] in summary['repeat_checks']}
    attempts = []
    for attempt in summary['config']['attempts']:
        name = attempt['id']
        status = summary['attempts'][name]
        row = {**attempt, 'status': status['status']}
        if status['status'] == 'generated':
            m = json.loads((study/'attempts'/name/'manifest.json').read_text())
            row.update(raw=m['raw'], metrics=m['metrics'], within_budget=m['within_budget'],
                removed_degenerate_triangles=m['removed_degenerate_faces'],
                details=m['details'], normalization=m['normalization'],
                adapter_sources_sha256=m['adapter_sources_sha256'],
                generation_seconds=m['duration_seconds'])
        else:
            row['reason'] = next((line for line in status['reason'].splitlines() if line.startswith('ValueError:')), status['reason'][-500:])
        attempts.append(row)
    write(output/'attempts.json', attempts)
    sample = json.loads((study/'attempts'/summary['config']['selection']['adulto']['easy']/'manifest.json').read_text())
    write(output/'addon-sources.json', {'versions': sample['addon_versions'], 'sources_sha256': sample['sources_sha256'],
        'unchanged': all(json.loads((study/'attempts'/n/'manifest.json').read_text())['addon_sources_unchanged']
                         for n, status in summary['attempts'].items() if status['status'] == 'generated')})
    result = {'version': summary['version'], 'study': str(study), 'sources_sha256': summary['sources_sha256'],
        'runner_python': summary['runner_python'], 'selected': selected, 'repeat_checks': summary['repeat_checks'],
        'q3_sources_sha256': summary['q3_sources_sha256'], 'q3_sources_unchanged': summary['q3_sources_unchanged'],
        'same_cameras_per_age': summary['same_cameras_per_age'], 'exports': summary['exports'],
        'capture_count': len(summary['capture_visible_pixels']), 'minimum_visible_pixels': min(summary['capture_visible_pixels'].values()),
        'godot': {k: v for k, v in summary['godot'].items() if k != 'assets'},
        'visual_acceptance': 'pending', 'runtime_generation_tested': False, 'rf3_started': False}
    write(output/'summary.json', result)
    shutil.copy2(study/'comparison/cameras.json', output/'cameras.json')
    shutil.copy2(study/'logs/tests.log', output/'unit-tests.txt')
    sections = []
    for age in ('adulto', 'viejo'):
        rows = []
        for view in ('godot-perspective', 'godot-front', 'godot-side', 'godot-top', 'godot-below', 'godot-reverse', 'wood-only/perspective'):
            rows.append('<tr><th>'+view+'</th>'+''.join(f'<td><a href="comparison/{engine}-{age}/{view}.png"><img src="comparison/{engine}-{age}/{view}.png" alt="{engine} {age} {view}"></a></td>' for engine in ('q3', 'easy', 'sapling'))+'</tr>')
        sections.append(f'<h2>{age}</h2><table><tr><th>Vista</th><th>Q3, presentación facetada</th><th>Easy Tree adaptado</th><th>Sapling ajustado</th></tr>'+''.join(rows)+'</table>')
    (study/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Q3, Easy Tree y Sapling</title>'
        '<style>body{font:16px sans-serif;background:#e9edf1;margin:24px}table{width:100%;table-layout:fixed}img{width:100%}th:first-child{width:140px}</style>'
        '<h1>Comparación de generadores: adulto y viejo</h1><p>Alturas 10/9 m; máximo 10000 triángulos y 3 materiales. '
        'Dos materiales opacos de paleta compartida y caras facetadas. Cámaras e iluminación iguales por edad. '
        'Easy Tree usa hoja geométrica RF1 en lugar de su recorte texturizado; conserva ramillas y distribución del addon. '
        'Sapling usa su hoja hexagonal. La copia de presentación Q3 recibe el mismo facetado, sin sobrescribir su referencia.</p>'
        '<p>No se ha probado generación durante el juego ni se declara aceptación artística.</p>'+''.join(sections))
    print(output)


if __name__ == '__main__':
    main()
