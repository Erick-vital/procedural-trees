#!/usr/bin/env python3
"""Ensayo acotado: dos/tres láminas por grupo frente al roble pintado aprobado."""
import argparse
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.runner import BLENDER
from treegen.oak_crossed import GRID,TILE
from review_pine_painted import read,write,run,sha
from verify_foliage_unit import GODOT
from oak_painted_sample import inspect
from oak_sample_evidence import channel
from verify_painted_oak import mask_metrics
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source',type=Path,default=ROOT/'artifacts/roble-pintado/piloto-completo-01')
    p.add_argument('--stage',choices=['all','generate','review'],default='all');a=p.parse_args();out=a.output.resolve();source=a.source.resolve()
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    if a.stage in ('all','generate'):
        out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
        baseline=read(source/'manifest.json');assert baseline['passed'] and sha(source/'painted/tree.glb')==baseline['variants']['painted']['glb_sha256']
        for name in ('main','repeat'):
            target=out if name=='main' else out/'repeat'
            if name=='repeat':target.mkdir()
            cmd=[os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',ROOT/'blender/oak_crossed_trial.py','--',source,target]
            # Repetir geometría y exportación con atlas congelado; horneado separado.
            if name=='repeat':cmd.append(out/'crossed-atlas.png')
            run(cmd,out/'logs'/(name+'.log'),env)
            print(name+': exportado',flush=True)
        report=read(out/'manifest.json');assert report['groups']==264
        report['export_validation']={};report['repeat_glb_identical']={}
        bark=baseline['resources']['bark.png']['sha256'];leaf=baseline['resources']['foliage.png']['sha256']
        for name,row in report['variants'].items():
            report['export_validation'][name]=inspect(out/name/'asset.glb',[bark,leaf if name.endswith('reference') else report['atlas_sha256']])
            report['repeat_glb_identical'][name]=sha(out/name/'asset.glb')==sha(out/'repeat'/name/'asset.glb')
        assert all(report['repeat_glb_identical'].values())
        assert channel(source/'painted/tree.glb','Painted_Bark')==channel(out/'tree-reference/asset.glb','Painted_Bark')
        assert channel(source/'painted/tree.glb','Painted_Foliage')==channel(out/'tree-reference/asset.glb','Painted_Foliage')
        for scope in ('tree','branch'):
            expected=channel(out/(scope+'-reference')/'asset.glb','Painted_Bark')
            for mode in ('cross2','cross3'):assert channel(out/(scope+'-'+mode)/'asset.glb','Painted_Bark')==expected
        assert report['variants']['tree-cross2']['metrics']['triangles']==7308
        assert report['variants']['tree-cross3']['metrics']['triangles']==7836
        files=[Path(__file__),ROOT/'blender/oak_crossed_trial.py',ROOT/'src/treegen/oak_crossed.py',ROOT/'src/treegen/oak_painted_tree.py',ROOT/'src/treegen/oak_painted_sample.py',ROOT/'blender/oak_painted_sample.py',ROOT/'blender/pine_painted_sample.py',ROOT/'blender/foliage_lab.py',ROOT/'scripts/oak_painted_sample.py',ROOT/'scripts/oak_sample_evidence.py',ROOT/'scripts/review_pine_painted.py',ROOT/'scripts/verify_painted_oak.py',ROOT/'scripts/foliage_evidence.py',ROOT/'godot/review_painted_pine.gd',ROOT/'godot/review_painted_oak_pilot.gd',ROOT/'godot/verify_oak.gd',ROOT/'godot/project.godot',*sorted((ROOT/'assets/roble-pintado/v0.2.0').glob('*'))]
        report['source_lock']={str(f.relative_to(ROOT)):sha(f) for f in files if f.is_file()}
        report['input_lock']={n:sha(source/n) for n in ('manifest.json','protocol.json','source/base-reference.json','source/manifest.json','painted/tree.glb')}
        write(out/'manifest.json',report)
    if a.stage=='generate':return
    report=read(out/'manifest.json');assert all(sha(ROOT/f)==h for f,h in report['source_lock'].items())
    assert all(sha(source/f)==h for f,h in report['input_lock'].items())
    project=out/'godot';project.mkdir(exist_ok=False);captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    # Adaptación local del revisor: solo añade 2000² como dimensión del atlas de ensayo.
    script=project/'review_painted_pine.gd';code=script.read_text();old="im.get_width()==1254 and im.get_height()==1254"
    assert code.count(old)==1;code=code.replace(old,'(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()=='+str(GRID*TILE)+' and im.get_height()=='+str(GRID*TILE)+')');script.write_text(code)
    entries={}
    for name,row in report['variants'].items():
        shutil.copy2(out/name/'asset.glb',project/(name+'.glb'))
        entries[name]={'id':name,'resource':'res://'+name+'.glb','metrics':row['metrics']}
    protocol=read(source/'protocol.json');tree_shots=protocol['shots'];branch_protocol=read(ROOT/'artifacts/roble-pintado/rama-muestra-01/protocol.json')
    branch_shots=[s for s in branch_protocol['shots'] if not s.get('only')]
    godot=os.environ.get('GODOT_BIN',GODOT);run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/import.log',env)
    reviews=[]
    for scope,shots in [('tree',tree_shots),('branch',branch_shots)]:
        for mode in ('color','mask'):
            selected=shots if mode=='color' else [{**s,'id':'mask-'+s['id'],'background':'#FFFFFF'} for s in shots[:9]]
            for names in [('reference','cross2'),('cross3',)]:
                name=scope+'-'+mode+'-'+names[0];config=out/(name+'-input.json');result=out/(name+'-report.json')
                write(config,{'output':str(captures),'report':str(result),'center':protocol['center'],'span':protocol['span'],'original_low':[0,0,0],
                    'assets':[entries[scope+'-'+m] for m in names],'shots':selected,'mask_pass':mode=='mask'})
                run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],out/'logs'/(name+'.log'),env)
                r=read(result);assert r['passed'];reviews.append(r)
            print(scope+' '+mode+': capturas OK',flush=True)
    report['godot']=reviews;report['mask_metrics']={}
    for scope,shots in [('tree',tree_shots[:9]),('branch',branch_shots[:9])]:
        for mode in ('cross2','cross3'):
            report['mask_metrics'][scope+'-'+mode]={s['id']:mask_metrics(captures/(scope+'-reference--mask-'+s['id']+'.png'),captures/(scope+'-'+mode+'--mask-'+s['id']+'.png')) for s in shots}
    report['capture_sha256']={f.name:sha(f) for f in captures.glob('*.png')}
    for filename,scope,views in [('tree','tree',('front','side','perspective','back','top','below')),('branch','branch',('front','side','perspective','back','top','below')),
        ('distances','tree',('near','medium','far')),('close','tree',('branch-close','trunk-close')),('masks','tree',('mask-front','mask-perspective','mask-far'))]:
        if filename=='distances':views=('near','medium','far')
        sheet(out,out/(filename+'.jpg'),3,[[(f'captures/{scope}-{m}--{v}.png',m+' | '+v) for m in ('reference','cross2','cross3')] for v in views])
    report['local_reviewer_sha256']=sha(script);write(out/'manifest.json',report)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Roble · ensayo de cruzadas</title><style>body{font:18px sans-serif;background:#eee9df;margin:28px}img{width:100%;max-width:1200px}</style><h1>Ensayo de láminas cruzadas</h1><p>Izquierda: pintura aprobada (9420 tris). Centro: dos láminas por grupo (7308). Derecha: tres láminas (7836). Madera idéntica. Aproximación experimental; revisar plenitud y volumen.</p><a href="crossed-atlas.png">Atlas horneado desde la pintura aprobada</a>'+''.join('<h2>'+n+'</h2><a href="'+n+'.jpg"><img src="'+n+'.jpg"></a>' for n in ('branch','tree','distances','close','masks'))+'<h2>Capturas individuales</h2>'+''.join('<a href="captures/'+n+'">'+n+'</a><br>' for n in sorted(report['capture_sha256'])))
    print('Ensayo listo: '+str(len(report['capture_sha256']))+' capturas; comparar máscaras antes de adoptar.',flush=True)


if __name__=='__main__':main()
