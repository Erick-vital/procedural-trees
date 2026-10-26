#!/usr/bin/env python3
"""PP3: detalles de costura de corteza y uniones de la rama cruzada elegida."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from review_pine_painted import read, write, camera, run, GODOT
from treegen.blueprints import load_blueprint, load_instance, resolve_blueprint
from treegen.pine_painted_sample import select
from treegen.pine import point_on, unit, sub, cross, add, mul

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('study',type=Path)
    args=parser.parse_args();out=args.study.resolve();lock=read(out/'source-lock.json');source=Path(lock['source'])
    manifest=read(source/'manifest.json');ref=read(source/'reference-lock.json')
    resolved=resolve_blueprint(load_blueprint(ROOT/'blueprints/pino_conico/1.1.0.json'),load_instance(ROOT/'presets/blueprints/pino-v2/pilot.json'))
    branches,_,selection=select(resolved)
    assert selection['source_geometry_sha256']==ref['source_geometry_sha256']
    main=branches[0];axis=unit(sub(main['points_m'][-1],main['points_m'][0]));side=unit(cross(axis,[0,0,1]));up=cross(axis,side)
    shots=[]
    for i in range(8):
        angle=math.tau*i/8
        d=add(add(mul(side,math.cos(angle)),mul(up,math.sin(angle))),mul(axis,.15))
        shots.append({'id':f'bark-{i:02}','camera':camera(point_on(main,.18),.8,d,.7),'background':'#EEE9DF','light':[-35,-25,0]})
    for i,branch in enumerate(branches[1:]):
        center=branch['points_m'][0]
        shots.append({'id':f'join-{i:02}','camera':camera(center,.8,[1,-1,.6],.7),'background':'#1E2A35','light':[-35,-25,0]})
    folder=out/'captures/details';folder.mkdir(exist_ok=False)
    config=out/'inputs/details.json';report=out/'details.json'
    write(config,{'output':str(folder),'report':str(report),'span':.8,'center':point_on(main,.18),'original_low':ref['original_bounds_m'][0],
        'assets':[{'id':'crossed','resource':'res://crossed.glb','metrics':manifest['variants']['crossed']['metrics']}],'shots':shots})
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    run([os.environ.get('GODOT_BIN',GODOT),'--path',out/'godot','--audio-driver','Dummy','--script','res://review_pine_painted.gd','--',config,'--visual'],out/'logs/details.log',env)
    result=read(report);assert result['passed'] and len(result['captures'])==12
    print('Detalles: 12 capturas reales')
