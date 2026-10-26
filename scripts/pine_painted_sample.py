#!/usr/bin/env python3
"""Generar muestra PP2 con entradas propias y plazo de 180 s por proceso."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from treegen.blueprints import load_blueprint, load_instance, resolve_blueprint
from treegen.runner import BLENDER

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--no-render',action='store_true')
    args=parser.parse_args()
    out=args.output.resolve()
    if out.exists():raise SystemExit('El directorio de salida ya existe')
    out.parent.mkdir(parents=True,exist_ok=True)
    resolved=resolve_blueprint(load_blueprint(ROOT/'blueprints/pino_conico/1.1.0.json'),load_instance(ROOT/'presets/blueprints/pino-v2/pilot.json'))
    job=out.with_suffix('.input.json');job.write_text(json.dumps(resolved,indent=2)+'\n')
    command=[os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','4','--python-exit-code','1','--python',str(ROOT/'blender/pine_painted_sample.py'),'--',str(out),str(job)]
    if args.no_render:command.append('--no-render')
    with out.with_suffix('.log').open('w') as log:
        proc=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=proc.wait(timeout=180)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL);proc.wait();raise SystemExit('Tiempo límite de 180 s excedido; revisar salida parcial')
    if code:raise SystemExit('Blender falló; revisar '+str(out.with_suffix('.log')))
    print(out/'manifest.json')
