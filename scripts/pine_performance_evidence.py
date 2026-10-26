#!/usr/bin/env python3
"""Auditar mediciones y conservar resumen, contexto y capturas seleccionadas."""
import argparse
import csv
import io
from pathlib import Path
import shutil
import sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts')]
from review_pine_painted import read,write,sha
from benchmark_painted_pine import summarize


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True,type=Path);p.add_argument('--evidence',required=True,type=Path)
    a=p.parse_args();study=a.study.resolve();ev=a.evidence.resolve();r=read(study/'summary.json')
    assert r['passed'] and not r['smoke']
    assert all(sha(ROOT/path)==digest for path,digest in r['sources_sha256'].items())
    ev.mkdir(parents=True,exist_ok=True);capture_hashes={};engines={};layouts={}
    for count in r['config']['counts']:
        n=str(count);raw=read(study/n/'raw.json');engines[n]={k:raw[k] for k in ('godot','renderer','gpu','driver','actual_resolution','window_size','actual_msaa','actual_shadows','actual_vsync','actual_max_fps','actual_lod_threshold','camera','materials')}
        value=summarize(raw);value['raw_file_sha256']=sha(study/n/'raw.json');assert value==r['counts'][n]
        assert len(value['trials'])==8 and all(t['frames']>=100 and t['elapsed_s']>=r['config']['measurement_seconds']-.05 for t in value['trials'])
        assert [t['version'] for t in raw['trials']]==r['config']['order']
        assert all(t['mesh_instances']==count for t in raw['trials'])
        # Primitivas incluyen cámara y pasadas de sombra; no confundirlas con GLB.
        baseline_calls=value['aggregate']['baseline']['draw_calls'];candidate_calls=value['aggregate']['candidate']['draw_calls']
        assert baseline_calls>0 and candidate_calls>0
        assert abs(candidate_calls-baseline_calls)/baseline_calls<.01, 'Cambio inesperado de cantidad de llamadas'
        assert all(not m['textured'] and m['transparency']==0 for case in raw['materials']['baseline'] for m in case)
        assert all(m['textured'] for case in raw['materials']['candidate'] for m in case)
        layouts[n]={'sha256':sha(study/n/'input.json'),'positions':raw['layout']}
        for version in ('baseline','candidate'):
            path=study/n/(version+'.png');im=Image.open(path);assert list(im.size)==r['config']['resolution']
            destination=ev/(n+'-'+version+'.jpg');im.convert('RGB').save(destination,quality=88)
            capture_hashes[str(destination.name)]=sha(destination)
    hardware=read(study/'hardware.json');write(ev/'hardware.json',hardware)
    write(ev/'summary.json',r);write(ev/'engine-settings.json',engines);write(ev/'layouts.json',layouts)
    # Solo resumen del muestreo GPU; CSV completo permanece regenerable.
    sensor=list(csv.DictReader((study/'gpu-samples.csv').read_text().splitlines()))
    gpu={}
    for key in sensor[0]:
        if key=='timestamp':continue
        values=[]
        for row in sensor:
            try:values.append(float(row[key].strip().split()[0]))
            except (ValueError,IndexError):pass
        if values:gpu[key]={'min':min(values),'max':max(values)}
    write(ev/'audit.json',{'passed':True,'study':str(study.relative_to(ROOT)),'counts':r['config']['counts'],
        'trials':24,'repetitions_per_version_and_count':4,'measurement_seconds':r['config']['measurement_seconds'],
        'gpu_samples':len(sensor),'gpu_ranges':gpu,'capture_sha256':capture_hashes,'sources_verified':True,'raw_verified':True,
        'evidence_script_sha256':sha(Path(__file__))})
    # Lámina de las tres escenas, dos versiones, mismos encuadres por pareja.
    canvas=Image.new('RGB',(1280,3*390),(238,235,227));draw=ImageDraw.Draw(canvas)
    for row,count in enumerate(r['config']['counts']):
        for col,version in enumerate(('baseline','candidate')):
            im=Image.open(ev/f'{count}-{version}.jpg');im.thumbnail((630,355));x=col*640+5;y=row*390+25
            canvas.paste(im,(x,y));draw.text((x,row*390+5),f'{count} árboles | {r["config"][version]}',fill='black')
    canvas.save(ev/'scenes.jpg',quality=90)
    print('Benchmark auditado: 24 mediciones, 6 capturas y fuentes congeladas.',flush=True)

if __name__=='__main__':main()
