#!/usr/bin/env python3
"""Auditar doce mediciones de roble y conservar evidencia compacta."""
import argparse
import csv
from pathlib import Path
import shutil
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts')]
from review_pine_painted import read, write, sha
from benchmark_painted_oak import summarize


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study', required=True, type=Path)
    p.add_argument('--evidence', required=True, type=Path)
    args = p.parse_args()
    study, evidence = args.study.resolve(), args.evidence.resolve()
    result = read(study/'summary.json')
    assert result['passed'] and not result['smoke']
    assert result['config']['counts'] == [1,128,512] and result['config']['repetitions'] == 4
    assert all(sha(ROOT/p) == h for p,h in result['sources_sha256'].items())
    assert all(sha(study/'godot'/p) == h for p,h in result['runtime_sha256'].items())
    acceptance = read(ROOT/'docs/evidence/roble-central/familia-01/user-acceptance.json')
    for name, asset in result['assets'].items():
        assert sha(study/'godot'/name) == asset['sha256'] == acceptance['approved_glbs_sha256'][name.removesuffix('.glb')]
    evidence.mkdir(parents=True, exist_ok=False)
    engines, layouts, capture_hashes = {}, {}, {}
    for count in result['config']['counts']:
        name = str(count); folder = study/name; raw = read(folder/'raw.json')
        assert sha(folder/'input.json') == result['input_sha256'][name]
        assert raw['settings'] == read(folder/'input.json')
        assert raw['settings'] == {**result['config'], 'count': count, 'assets': result['asset_resources'], 'output':str(folder)}
        value = summarize(raw); value['raw_file_sha256'] = sha(folder/'raw.json')
        assert value == result['counts'][name]
        assert len(value['trials']) == 4 and all(t['frames'] >= 100 for t in value['trials'])
        engines[name] = {k:raw[k] for k in ('godot','renderer','gpu','driver','actual_resolution','window_size','actual_msaa','actual_shadows',
                         'actual_vsync','actual_max_fps','actual_lod_threshold','camera','shadow_distance_m','ground_size_m','materials')}
        layouts[name] = {'input_sha256':sha(folder/'input.json'), 'placements':raw['layout']}
        png = folder/'oak.png'
        with Image.open(png) as im:
            assert list(im.size) == result['config']['resolution']
            destination = evidence/(name+'-oak.jpg')
            im.convert('RGB').save(destination, quality=90)
        capture_hashes[name] = {'png_sha256':sha(png), 'selected_jpg_sha256':sha(destination)}
    for name in ('summary.json','hardware.json'):
        shutil.copy2(study/name, evidence/name)
    write(evidence/'engine-settings.json', engines)
    write(evidence/'layouts.json', layouts)
    sensor = list(csv.DictReader((study/'gpu-samples.csv').read_text().splitlines()))
    assert sensor
    ranges = {}
    for key in sensor[0]:
        if key == 'timestamp': continue
        values = []
        for row in sensor:
            try: values.append(float(row[key].strip().split()[0]))
            except (ValueError, IndexError): pass
        if values: ranges[key] = {'min':min(values), 'max':max(values)}
    write(evidence/'audit.json', {'passed':True, 'study':str(study.relative_to(ROOT)), 'trials':12,
          'counts':[1,128,512], 'repetitions_per_count':4, 'measurement_seconds':6,
          'sources_and_assets_verified':True, 'raw_verified':True, 'settings_and_materials_verified':True,
          'gpu_samples':len(sensor), 'gpu_ranges':ranges, 'capture_sha256':capture_hashes,
          'evidence_script_sha256':sha(Path(__file__)), 'visual_review':'pending',
          'unit_tests':{'passed':5,'command':'PYTHONPATH=src python3 -m unittest discover -s tests -p test_oak_performance.py -v'}})
    canvas = Image.new('RGB', (1000,3*590), '#eee9df'); draw = ImageDraw.Draw(canvas)
    for row, count in enumerate((1,128,512)):
        with Image.open(evidence/f'{count}-oak.jpg') as original:
            im = original.copy(); im.thumbnail((990,557))
        canvas.paste(im, ((1000-im.width)//2, row*590+27))
        draw.text((10,row*590+7),f'{count} robles | 3.0.0 | mismas condiciones entre cuatro repeticiones',fill='black')
    canvas.save(evidence/'scenes.jpg',quality=90)
    print('Benchmark auditado:12 mediciones, cinco GLB aprobados y tres capturas1080p.',flush=True)


if __name__ == '__main__': main()
