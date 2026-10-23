#!/usr/bin/env python3
"""Selecciona evidencia compacta de un ensayo ya verificado; no genera árboles."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw
from preview_fusion import gallery


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    study, output = args.study.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    reports = json.loads((study/'summary.json').read_text())
    verification = json.loads((study/'verification/summary.json').read_text())
    cases = list(reports)
    gallery(study, cases)
    shutil.copy2(study/'viejo-09-comparison.jpg', output/'pilot-all-views.jpg')
    for view, filename in [('front', 'controls-front'), ('below', 'controls-below'),
                           ('godot-perspective', 'controls-godot'), ('godot-game', 'controls-godot-game')]:
        sheet = Image.new('RGB', (1200, 635*len(cases)), (235, 237, 240))
        draw = ImageDraw.Draw(sheet)
        for row, case in enumerate(cases):
            for col, (label, caption) in enumerate((('base', 'Q3 congelada'), ('fused', 'Fusión parcial'))):
                draw.text((col*600+10, row*635+10), f'{case} | {caption}', fill='black')
                with Image.open(study/case/label/f'{view}.png') as source:
                    image = source.convert('RGB')
                image.thumbnail((590, 590))
                sheet.paste(image, (col*600+(600-image.width)//2, row*635+35))
        sheet.save(output/f'{filename}.jpg', quality=92)
    locks = {case: json.loads((study/case/'reference-lock.json').read_text()) for case in cases}
    (output/'reference-locks.json').write_text(json.dumps(locks, indent=2)+'\n')
    summary = {'experiment': reports[cases[0]]['experiment'], 'reference_commit': 'fbe87a4',
               'reference_tag': 'q3-referencia-0.4.0', 'cases': {},
               'q3_reproduced': verification['q3_reproduced'], 'fusion_reproduced': verification['fusion_reproduced'],
               'godot': verification['godot'], 'godot_same_cameras_per_pair': verification['godot_same_cameras_per_pair'],
               'saved_meshes': verification['saved_meshes'],
               'godot_visual_captures_generated': verification['godot_visual_captures_generated'],
               'user_visual_acceptance': 'pending', 'full_batch_generated': False}
    for case, report in reports.items():
        m = json.loads((study/case/'candidate/manifest.json').read_text())
        summary['cases'][case] = {'input_spec': locks[case]['spec'], 'seeds': locks[case]['seeds'],
            'input_masses': report['before']['leaf_mass_count'], 'output_components': report['after']['leaf_mass_count'],
            'input_leaf_triangles': report['before']['leaf_triangles'], 'output_leaf_triangles': report['after']['leaf_triangles'],
            'total_triangles': m['metrics']['triangles'], 'wood_geometry_sha256': report['after']['wood_geometry_sha256'],
            'input_geometry_sha256': locks[case]['input_geometry_sha256'], 'output_geometry_sha256': m['metrics']['geometry_sha256'],
            'glb_sha256': m['glb_sha256'], 'silhouette': report['silhouette'], 'fusion': report['fusion'],
            'game_camera_distance_m': locks[case]['framing']['span']*7.5,
            'sources_sha256': m['sources_sha256']}
    summary['verification_sources_sha256'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (Path('scripts/verify_fusion.py'), Path('blender/verify_fusion.py'), Path('godot/verify_fusion.gd'))}
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    rows = ''.join(f'<tr><th>{case}</th><td><a href="{case}/base/godot-perspective.png"><img src="{case}/base/godot-perspective.png"></a></td>'
                   f'<td><a href="{case}/fused/godot-perspective.png"><img src="{case}/fused/godot-perspective.png"></a></td></tr>' for case in cases)
    with (study/'index.html').open('a') as page:
        page.write('<h2>Godot: cámaras y luces compartidas por pareja</h2><table><tr><th>Caso</th><th>Q3 congelada</th><th>Fusión parcial</th></tr>'+rows+'</table>')


if __name__ == '__main__':
    main()
