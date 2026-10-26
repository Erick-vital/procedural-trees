#!/usr/bin/env python3
"""Benchmark pareado de pino 1.1.0/2.3.0 en Godot real, con fuentes congeladas."""
import argparse
import json
import math
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from review_pine_painted import run,read,write,sha
from verify_foliage_unit import GODOT


def percentile(values,p):
    values=sorted(values);index=(len(values)-1)*p
    a=math.floor(index);b=math.ceil(index)
    return values[a]+(values[b]-values[a])*(index-a)


def summarize(report):
    assert report['renderer']=='gl_compatibility' and 'llvmpipe' not in report['gpu'].lower()
    assert report['actual_vsync']==0 and report['actual_max_fps']==0 and report['actual_lod_threshold']==0
    assert report['actual_resolution']==report['settings']['resolution']
    assert report['actual_msaa']==2 and report['actual_shadows']==report['settings']['shadows']
    trials=[]
    for trial in report['trials']:
        samples=trial['samples'];assert len(samples)>=10
        times=[row[0] for row in samples];assert all(t>0 for t in times)
        entry={k:v for k,v in trial.items() if k!='samples'}
        entry.update(frames=len(times),elapsed_s=sum(times)/1000,frame_mean_ms=statistics.mean(times),frame_median_ms=statistics.median(times),
                     frame_p95_ms=percentile(times,.95),frame_p99_ms=percentile(times,.99),fps=1000/statistics.mean(times))
        for i,name in enumerate(report['columns'][1:],1):
            values=[r[i] for r in samples]
            entry[name]=statistics.mean(values) if max(values)>0 else None
        trials.append(entry)
    aggregates={}
    for version in ('baseline','candidate'):
        rows=[t for t in trials if t['version']==version]
        aggregates[version]={key:statistics.median(t[key] for t in rows) for key in ('frame_mean_ms','frame_median_ms','frame_p95_ms','frame_p99_ms','fps')}
        aggregates[version]['run_frame_mean_range_ms']=[min(t['frame_mean_ms'] for t in rows),max(t['frame_mean_ms'] for t in rows)]
        for name in report['columns'][1:]:
            values=[t[name] for t in rows if t[name] is not None]
            aggregates[version][name]=statistics.median(values) if values else None
    paired=[]
    for i in range(0,len(trials),2):
        pair={t['version']:t for t in trials[i:i+2]}
        if len(pair)==2:paired.append(100*(1-pair['candidate']['frame_mean_ms']/pair['baseline']['frame_mean_ms']))
    return {'trials':trials,'aggregate':aggregates,'paired_frame_time_reduction_percent':paired,
            'median_paired_frame_time_reduction_percent':statistics.median(paired),'raw_file_sha256':None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--source',type=Path,default=ROOT/'artifacts/pino-pintado/pp4-cards-02')
    p.add_argument('--baseline-source',type=Path,default=ROOT/'artifacts/blueprints/pine-v1.1-review-01')
    p.add_argument('--smoke',action='store_true')
    p.add_argument('--analyze-only',action='store_true')
    a=p.parse_args();out=a.output.resolve()
    if a.analyze_only:
        result=read(out/'summary.json')
        for count in result['config']['counts']:
            raw=out/str(count)/'raw.json';result['counts'][str(count)]=summarize(read(raw));result['counts'][str(count)]['raw_file_sha256']=sha(raw)
        write(out/'summary.json',result);return
    config=read(ROOT/'configs/verification/pine-performance-v1.json')
    if a.smoke:config.update(counts=[4],warmup_seconds=.3,measurement_seconds=.7,order=['baseline','candidate'])
    out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir();project=out/'godot';project.mkdir()
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'),__GL_SYNC_TO_VBLANK='0',vblank_mode='0')
    def command(name,cmd):run(cmd,out/'logs'/(name+'.log'),env);print(name+': OK',flush=True)
    project_text=(ROOT/'godot/project.godot').read_text().replace('960','1920').replace('720','1080')
    project_text+='\n[application_benchmark]\nprotocol="pine-performance-0.2.0"\n'
    (project/'project.godot').write_text(project_text)
    for name in ('benchmark_painted_pine.gd','painted_pine_asset.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    assets={};lock={}
    for version,number,evidence,preset in [('baseline','1.1.0',None,'pino-v2'),('candidate','2.3.0','pp4-laminas','pino-pintado-laminas')]:
        expected=read(ROOT/f'docs/evidence/pino-pintado/{evidence}/verification.json' if evidence else ROOT/'docs/evidence/blueprints/pino-revision/verification.json')['cases'];assets[version]=[]
        for name in ('pilot','control-01','control-02','control-03'):
            source=(a.baseline_source if version=='baseline' else a.source)/name/'tree.glb'
            if not source.is_file():
                from treegen.runner import execute_blueprint
                directory=out/'generated'/version/name
                execute_blueprint(ROOT/f'blueprints/pino_conico/{number}.json',read(ROOT/f'presets/blueprints/{preset}/{name}.json'),directory,render=False)
                source=directory/'tree.glb'
            assert sha(source)==expected[name]['glb_sha256'],'El asset no coincide con la versión congelada'
            filename=version+'-'+name+'.glb';shutil.copy2(source,project/filename)
            assets[version].append('res://'+filename);lock[filename]={'sha256':sha(source),'triangles':expected[name]['metrics']['triangles']}
    godot=os.environ.get('GODOT_BIN',GODOT)
    command('import',[godot,'--headless','--path',project,'--editor','--import'])
    hardware={'platform':platform.platform(),'cpu':subprocess.run(['lscpu'],capture_output=True,text=True,check=True).stdout}
    hardware['gpu_before']=subprocess.run(['nvidia-smi'],capture_output=True,text=True,check=True).stdout
    write(out/'hardware.json',hardware)
    summary={'passed':False,'smoke':a.smoke,'config':config,'assets':lock,'counts':{},
             'sources_sha256':{str(path.relative_to(ROOT)):sha(path) for path in [Path(__file__),ROOT/'godot/benchmark_painted_pine.gd',ROOT/'godot/painted_pine_asset.gd',ROOT/'configs/verification/pine-performance-v1.json']}}
    write(out/'summary.json',summary)
    sensor_stream=(out/'gpu-samples.csv').open('w')
    sensor=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,temperature.gpu,utilization.gpu,clocks.gr,clocks.mem,power.draw,memory.used','--format=csv','--loop=1'],stdout=sensor_stream,stderr=subprocess.STDOUT)
    try:
        for count in config['counts']:
            folder=out/str(count);folder.mkdir()
            trial_config={**config,'count':count,'assets':assets,'output':str(folder)};write(folder/'input.json',trial_config)
            command(str(count),[godot,'--path',project,'--audio-driver','Dummy','--disable-vsync','--max-fps','0','--script','res://benchmark_painted_pine.gd','--',folder/'input.json'])
            raw=folder/'raw.json';summary['counts'][str(count)]=summarize(read(raw));summary['counts'][str(count)]['raw_file_sha256']=sha(raw)
            write(out/'summary.json',summary)
    finally:
        sensor.terminate();sensor.wait(timeout=5);sensor_stream.close()
    summary['passed']=len(summary['counts'])==len(config['counts'])
    write(out/'summary.json',summary)
    print(json.dumps({n:r['aggregate'] for n,r in summary['counts'].items()},indent=2),flush=True)

if __name__=='__main__':main()
