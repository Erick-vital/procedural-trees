#!/usr/bin/env python3
"""PP3: importar rama PP2 en Godot y capturar una matriz reproducible."""
import argparse
import copy
import hashlib
import html
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_foliage_unit import GODOT
from verify_pine_painted_sample import inspect


def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def unit(v):return [x/math.sqrt(sum(t*t for t in v)) for x in v]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]

def camera(center,span,direction,scale=None):
    z=unit(direction);x=unit(cross([0,0,1] if abs(z[2])<.99 else [0,1,0],z));y=cross(z,x)
    return {'location':[a+b*span*3 for a,b in zip(center,z)],'basis_columns':[x,y,z],'ortho_scale':scale or span*1.3}


def shots_for(stage,lock):
    backgrounds={'light':'#EEE9DF','dark':'#1E2A35'}
    lights={'reference':[-35,-25,0],'side':[-35,-90,0],'back':[-35,155,0]}
    cams=lock['cameras'];lo,hi=lock['original_bounds_m'];center=[(a+b)/2 for a,b in zip(lo,hi)];span=max(b-a for a,b in zip(lo,hi))
    shots=[]
    def add(name,cam,bg='light',light='reference',**kw):
        shots.append({'id':name,'camera':copy.deepcopy(cam),'background':backgrounds[bg],'light':lights[light],**kw})
    if stage=='baseline':
        for name,c in cams.items():add('base-'+name,c)
    elif stage=='full':
        for bg in backgrounds:
            for light in lights:
                for view in ('front','side','three_quarter','top','below','end_on'):
                    if bg=='light' and light=='reference':continue
                    add(bg+'-'+light+'-'+view,cams[view],bg,light)
        for bg in backgrounds:
            for name,scale in [('tree-near',24),('tree-medium',48),('tree-far',120)]:
                c=copy.deepcopy(cams['three_quarter']);c['ortho_scale']=scale
                add(bg+'-'+name,c,bg)
        for light in lights:
            add('shadow-'+light,cams['three_quarter'],light=light,receiver=True)
        for index in range(72):
            angle=2*math.pi*index/72
            add(f'orbit-{index:03}',camera(center,span,[math.cos(angle),math.sin(angle),.25]),only='crossed')
        # Movimiento subpíxel a la escala cercana del árbol, con mipmaps y sin ellos.
        for mips in (True,False):
            for i in range(12):
                c=copy.deepcopy(cams['three_quarter']);c['ortho_scale']=24
                # Recorrido de tres píxeles, paso 1/4 píxel (900 px, ortho 24 m).
                offset=i*24/900*.25
                c['location']=[a+b*offset for a,b in zip(c['location'],c['basis_columns'][0])]
                add(f'motion-{"mips" if mips else "nomips"}-{i:02}',c,only='crossed',no_mips=not mips)
    elif stage=='aa':
        # Comparación solo si la línea base muestra bordes duros/pérdida de agujas.
        for mode,value in [('off',0),('coverage',1),('coverage-one',2)]:
            for bg in backgrounds:
                for view in ('three_quarter','side','end_on'):
                    add(f'aa-{mode}-{bg}-{view}',cams[view],bg,only='crossed',alpha_aa=value)
                for name,scale in [('near',24),('medium',48),('far',120)]:
                    c=copy.deepcopy(cams['three_quarter']);c['ortho_scale']=scale
                    add(f'aa-{mode}-{bg}-{name}',c,bg,only='crossed',alpha_aa=value)
    return shots,center,span


def run(command,log,env):
    with log.open('w') as stream:
        proc=subprocess.Popen(list(map(str,command)),cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=proc.wait(timeout=180)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL);proc.wait();raise RuntimeError('Tiempo límite de 180 s: '+str(log))
    content=log.read_text()
    if code or 'SCRIPT ERROR:' in content or '\nERROR:' in content:raise RuntimeError(str(log)+': '+content[-4000:])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source',type=Path,default=ROOT/'artifacts/pino-pintado/pp2-sample-02')
    parser.add_argument('--stage',choices=['baseline','full','aa'],default='baseline')
    parser.add_argument('--headless',action='store_true',help='Solo inspección técnica, sin capturas visuales')
    args=parser.parse_args();out=args.output.resolve();source=args.source.resolve()
    project=out/'godot';logs=out/'logs';captures=out/'captures';inputs=out/'inputs'
    if args.stage=='baseline':
        out.mkdir(parents=True,exist_ok=False)
        for p in (project,logs,captures,inputs):p.mkdir()
        for f in ('verify_oak.gd','review_pine_painted.gd','project.godot'):shutil.copy2(ROOT/'godot'/f,project/f)
        for name in ('original','folded','crossed'):
            inspect(source/name/'branch.glb')
            shutil.copy2(source/name/'branch.glb',project/(name+'.glb'))
        write(out/'source-lock.json',{'source':str(source),'glbs':{n:sha(source/n/'branch.glb') for n in ('original','folded','crossed')},
            'sources_sha256':{n:sha(ROOT/n) for n in ('godot/review_pine_painted.gd','godot/verify_oak.gd','godot/project.godot','scripts/review_pine_painted.py')},
            'pp2_reference_sha256':sha(source/'reference-lock.json'),'pp2_manifest_sha256':sha(source/'manifest.json')})
    else:
        lock=read(out/'source-lock.json')
        assert lock['glbs']=={n:sha(source/n/'branch.glb') for n in ('original','folded','crossed')}
        assert lock['sources_sha256']=={n:sha(ROOT/n) for n in lock['sources_sha256']},'Fuentes modificadas entre etapas'
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    godot=os.environ.get('GODOT_BIN',GODOT)
    if args.stage=='baseline':run([godot,'--headless','--path',project,'--editor','--import'],logs/'import.log',env)
    lock=read(source/'reference-lock.json');manifest=read(source/'manifest.json')
    shots,center,span=shots_for(args.stage,lock)
    write(out/(args.stage+'-protocol.json'),{'version':'pp3-review-0.1.0','shots':shots,'resolution':[900,900],
        'msaa':'4x','renderer':'gl_compatibility','center':center,'span':span,'distance_scale_reference':'árbol de 12 m al 50/25/10 % de pantalla'})
    # Separar matrices comunes (tres assets) y giro/movimiento (solo cruzadas).
    batches=[]
    common=[s for s in shots if not s.get('only')];single=[s for s in shots if s.get('only')]
    for series,names in ((common,['original','folded','crossed']),(single,['crossed'])):
        for i in range(0,len(series),6 if len(names)==3 else 12):batches.append((series[i:i+(6 if len(names)==3 else 12)],names))
    for index,(group,names) in enumerate(batches):
        label=f'{args.stage}-{index:02}';report=out/(label+'-report.json');config=inputs/(label+'.json')
        write(config,{'output':str(captures),'report':str(report),'span':span,'center':center,'original_low':lock['original_bounds_m'][0],
            'assets':[{'id':n,'resource':'res://'+n+'.glb','metrics':manifest['variants'][n]['metrics']} for n in names],'shots':group})
        command=[godot,'--path',project,'--audio-driver','Dummy','--script','res://review_pine_painted.gd','--',str(config)]
        if args.headless:command.insert(1,'--headless')
        else:command.append('--visual')
        run(command,logs/(label+'.log'),env)
        assert read(report)['passed'];print(label+': OK',flush=True)
    reports=[read(p) for p in sorted(out.glob('*-report.json')) if p.name!='review-report.json']
    all_captures=[r for report in reports for r in report['captures']]
    expected=sum(1 for s in shots for n in ('original','folded','crossed') if not s.get('only') or s['only']==n)
    stage_captures=sum(len(read(out/(f'{args.stage}-{i:02}-report.json'))['captures']) for i in range(len(batches)))
    assert stage_captures==(0 if args.headless else expected)
    result={'passed':all(r['passed'] for r in reports),'visual':not args.headless,'total_captures':len(all_captures),
        'current_stage':args.stage,'stage_expected':expected,'stage_captures':stage_captures,
        'engine':reports[0]['godot'],'renderer':reports[0]['renderer'],'adapter':reports[0]['video_adapter'],
        'assets':reports[0]['assets'],'source_lock':read(out/'source-lock.json'),'captures':all_captures}
    write(out/'review-report.json',result)
    cells=''.join('<figure><a href="captures/'+html.escape(c['path'])+'"><img width="300" src="captures/'+html.escape(c['path'])+'"></a><figcaption>'+html.escape(c['asset']+' | '+c['shot'])+'</figcaption></figure>' for c in all_captures)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>PP3 · Rama pintada en Godot</title><style>body{font:16px sans-serif;background:#eee}main{display:flex;flex-wrap:wrap}figure{margin:8px}figcaption{max-width:300px}</style><h1>PP3 · Rama en Godot</h1><p>Cruzadas elegida por el usuario; original y dobladas como controles. Capturas reales, cámaras comunes. Ver informe para decisión y defectos.</p><a href="review-report.json">Verificación</a><main>'+cells+'</main>')
    print('Total capturas:',len(all_captures))

if __name__=='__main__':main()
