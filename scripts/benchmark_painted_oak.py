#!/usr/bin/env python3
"""Medir la familia aprobada de roble3.0.0 en Godot real, sin cambiar assets."""
import argparse
import csv
import math
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts')]
from review_pine_painted import read, write, run, sha
from verify_foliage_unit import GODOT
from benchmark_painted_pine import percentile


def summarize(report):
    config = report['settings']
    count = int(config['count'])
    assert count > 0 and count == config['count']
    assert report['renderer'] == config['renderer'] == 'gl_compatibility'
    assert report['gpu'] and not any(v in report['gpu'].lower() for v in ('llvmpipe', 'softpipe', 'software'))
    assert report['actual_vsync'] == 0 and report['actual_max_fps'] == 0 and report['actual_lod_threshold'] == 0
    assert report['actual_resolution'] == config['resolution'] == [1920, 1080]
    assert report['actual_msaa'] == 2 and report['actual_shadows'] is True
    assert report['shadow_distance_m'] == config['shadow_distance_m']
    assert report['camera']['projection'] == 1 and report['camera']['far'] == config['camera_far_m']
    assert len(report['layout']) == config['count']
    assert [p['case'] for p in report['layout']] == [i % 5 for i in range(count)]
    cols = math.ceil(math.sqrt(config['count']))
    rows = math.ceil(config['count']/cols)
    for i, placement in enumerate(report['layout']):
        expected = [(i % cols - (cols-1)*.5)*config['spacing_m'], 0,
                    (i // cols - (rows-1)*.5)*config['spacing_m']]
        assert all(abs(a-b) < 1e-4 for a, b in zip(placement['position'], expected))
        assert abs(placement['rotation_y'] - (i*2.399963229728653) % math.tau) < 1e-5
    assert len(report['materials']['oak']) == 5
    for case in report['materials']['oak']:
        assert len(case) == 2 and {m['name'] for m in case} == {'Painted_Bark', 'Painted_Foliage'}
        for mat in case:
            assert mat['textured'] and mat['mipmaps'] and mat['cull_mode'] == 2 and mat['shadow_casting'] == 2 and mat['filter'] == 5
            assert abs(mat['roughness'] - .95) < .001
            if mat['name'] == 'Painted_Foliage':
                assert mat['transparency'] == 2 and abs(mat['alpha_cutoff'] - .5) < .001 and mat['alpha_aa'] == 0
            else:
                assert mat['transparency'] == 0
    trials = []
    columns = report['columns']
    assert columns == ['frame_ms', 'render_cpu_ms', 'render_gpu_ms', 'render_setup_cpu_ms', 'draw_calls', 'primitives', 'objects']
    assert len(report['trials']) == config['repetitions']
    for index, trial in enumerate(report['trials']):
        assert trial['trial'] == index and trial['version'] == 'oak' and trial['mesh_instances'] == config['count']
        samples = trial['samples']
        assert len(samples) >= 10 and all(len(row) == len(columns) and all(math.isfinite(x) and x >= 0 for x in row) and row[0] > 0 for row in samples)
        times = [row[0] for row in samples]
        assert sum(times)/1000 >= config['measurement_seconds'] - .05
        entry = {k: v for k, v in trial.items() if k != 'samples'}
        entry.update(frames=len(times), elapsed_s=sum(times)/1000,
                     frame_mean_ms=statistics.mean(times), frame_median_ms=statistics.median(times),
                     frame_p95_ms=percentile(times, .95), frame_p99_ms=percentile(times, .99),
                     fps=1000/statistics.mean(times))
        for i, name in enumerate(columns[1:], 1):
            values = [row[i] for row in samples]
            entry[name] = statistics.mean(values) if max(values) > 0 else None
        assert entry['draw_calls'] and entry['primitives'] and entry['objects']
        trials.append(entry)
    aggregate = {k: statistics.median(t[k] for t in trials) for k in
                 ('frame_mean_ms', 'frame_median_ms', 'frame_p95_ms', 'frame_p99_ms', 'fps')}
    aggregate['run_frame_mean_range_ms'] = [min(t['frame_mean_ms'] for t in trials), max(t['frame_mean_ms'] for t in trials)]
    for name in columns[1:]:
        values = [t[name] for t in trials if t[name] is not None]
        aggregate[name] = statistics.median(values) if values else None
    return {'trials': trials, 'aggregate': aggregate}


def analyze(out):
    result = read(out / 'summary.json')
    assert all(sha(ROOT / p) == h for p, h in result['sources_sha256'].items())
    assert all(sha(out / 'godot' / p) == h for p, h in result['runtime_sha256'].items())
    for count in result['config']['counts']:
        folder = out / str(count)
        raw = read(folder / 'raw.json')
        assert raw['settings'] == read(folder / 'input.json')
        assert result['input_sha256'][str(count)] == sha(folder / 'input.json')
        assert raw['settings'] == {**result['config'], 'count': count, 'assets': result['asset_resources'], 'output': str(folder)}
        result['counts'][str(count)] = summarize(raw)
        result['counts'][str(count)]['raw_file_sha256'] = sha(folder / 'raw.json')
    result['passed'] = True
    write(out / 'summary.json', result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--source', type=Path, default=ROOT/'artifacts/roble-central/familia-01/trees')
    p.add_argument('--smoke', action='store_true')
    p.add_argument('--analyze-only', action='store_true')
    args = p.parse_args()
    out = args.output.resolve()
    if args.analyze_only:
        analyze(out)
        return
    config_path = ROOT/'configs/verification/oak-performance-v1.json'
    config = read(config_path)
    if args.smoke:
        config.update(counts=[5], repetitions=1, warmup_seconds=.3, measurement_seconds=.7)
    out.mkdir(parents=True, exist_ok=False)
    project = out/'godot'; project.mkdir(); (out/'logs').mkdir()
    env = dict(os.environ, XDG_DATA_HOME=str(out/'xdg/data'), XDG_CONFIG_HOME=str(out/'xdg/config'),
               XDG_CACHE_HOME=str(out/'xdg/cache'), __GL_SYNC_TO_VBLANK='0', vblank_mode='0')
    for name in ('benchmark_painted_oak.gd', 'painted_pine_asset.gd', 'project.godot'):
        shutil.copy2(ROOT/'godot'/name, project/name)
    acceptance_path = ROOT/'docs/evidence/roble-central/familia-01/user-acceptance.json'
    expected = read(acceptance_path)
    assert expected['status'] == 'accepted'
    resources, assets = [], {}
    for seed in config['seeds_base']:
        name = f'maduro-{seed}'
        source = args.source/name/'tree.glb'
        assert sha(source) == expected['approved_glbs_sha256'][name]
        filename = name+'.glb'
        shutil.copy2(source, project/filename)
        resources.append('res://'+filename)
        manifest = read(args.source/name/'manifest.json')
        assert manifest['glb_sha256'] == sha(source) and manifest['status'] == 'completed'
        assets[filename] = {'sha256': sha(source), 'triangles': manifest['metrics']['triangles'],
                            'seeds': manifest['resolved_blueprint']['instance_request']['seeds']}
    sources = [Path(__file__), config_path, acceptance_path, ROOT/'godot/benchmark_painted_oak.gd',
               ROOT/'godot/painted_pine_asset.gd', ROOT/'godot/project.godot',
               ROOT/'scripts/review_pine_painted.py', ROOT/'scripts/verify_foliage_unit.py', ROOT/'scripts/benchmark_painted_pine.py']
    summary = {'passed': False, 'smoke': args.smoke, 'config': config, 'assets': assets, 'asset_resources': {'oak': resources},
               'counts': {}, 'input_sha256': {}, 'sources_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sources},
               'runtime_sha256': {p.name: sha(p) for p in project.iterdir() if p.is_file()},
               'study_type': 'single-version-static-load; no optimization claim'}
    # Todas las entradas y fuentes se congelan antes de importar/medir.
    for count in config['counts']:
        folder = out/str(count); folder.mkdir()
        write(folder/'input.json', {**config, 'count': count, 'assets': {'oak': resources}, 'output': str(folder)})
        summary['input_sha256'][str(count)] = sha(folder/'input.json')
    write(out/'summary.json', summary)
    godot = os.environ.get('GODOT_BIN', GODOT)
    run([godot, '--headless', '--path', project, '--editor', '--import'], out/'logs/import.log', env)
    write(out/'hardware.json', {'platform': platform.platform(),
          'cpu': subprocess.run(['lscpu'], capture_output=True, text=True, check=True).stdout,
          'gpu_before': subprocess.run(['nvidia-smi'], capture_output=True, text=True, check=True).stdout})
    with (out/'gpu-samples.csv').open('w') as stream:
        sensor = subprocess.Popen(['nvidia-smi', '--query-gpu=timestamp,temperature.gpu,utilization.gpu,clocks.gr,clocks.mem,power.draw,memory.used', '--format=csv', '--loop=1'], stdout=stream, stderr=subprocess.STDOUT)
        try:
            for count in config['counts']:
                folder = out/str(count)
                run([godot, '--path', project, '--audio-driver', 'Dummy', '--disable-vsync', '--max-fps', '0',
                     '--script', 'res://benchmark_painted_oak.gd', '--', folder/'input.json'], out/f'logs/{count}.log', env)
                raw = read(folder/'raw.json')
                summary['counts'][str(count)] = summarize(raw)
                summary['counts'][str(count)]['raw_file_sha256'] = sha(folder/'raw.json')
                write(out/'summary.json', summary)
                print(f'{count} árboles: '+str(summary['counts'][str(count)]['aggregate']), flush=True)
        finally:
            sensor.terminate(); sensor.wait(timeout=5)
    analyze(out)
    print('Benchmark completo; smoke='+str(args.smoke), flush=True)


if __name__ == '__main__':
    main()
