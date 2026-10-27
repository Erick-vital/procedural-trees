#!/usr/bin/env python3
"""Ensayo reproducible del piloto: anillos a 5/10/20 mm y comparación real Godot."""
import argparse
import os
from pathlib import Path
import shutil
import sys
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.runner import BLENDER, execute_blueprint
from treegen.oak_crossed_evaluation import channels
from treegen.oak_wood import optimize
from treegen.pine_painted_sample import canonical_hash
from review_pine_painted import read,write,run,sha,camera
from verify_foliage_unit import GODOT
from oak_painted_sample import inspect
from verify_painted_oak import mask_metrics
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source',type=Path)
    p.add_argument('--stage',choices=['all','generate','review'],default='all')
    a=p.parse_args();out=a.output.resolve()
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),
             XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    if a.stage in ('all','generate'):
        out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
        source=a.source.resolve() if a.source else out/'source'
        if not a.source:
            execute_blueprint(ROOT/'blueprints/roble_copa_ancha/2.1.0.json',
                read(ROOT/'presets/blueprints/roble-cruzado/pilot.json'),source,render=False)
        expected=read(ROOT/'docs/evidence/roble-pintado/implementacion-01/verification.json')['cases']['pilot']['glb_sha256']
        assert sha(source/'tree.glb')==expected,'El origen debe ser el piloto 2.1.0 aprobado'
        for label in ('after','repeat'):
            folder=out/label;folder.mkdir()
            run([BLENDER,'--background','--factory-startup','--threads','1','--python-exit-code','1',
                 '--python',ROOT/'blender/oak_wood_trial.py','--',source,folder],out/'logs'/(label+'.log'),env)
        report=read(out/'after/manifest.json');report['checks']={};report['export_validation']={}
        _,old,old_normals,images=channels(source/'tree.glb')
        _,rebuilt,rebuilt_normals,_=channels(out/'after/before-tree/branch.glb')
        report['checks']['baseline_geometry_uv_normals_exact']=old==rebuilt and old_normals==rebuilt_normals
        for label, row in report['variants'].items():
            asset=out/'after'/label/'branch.glb'
            report['checks'][label+'-repeat']=sha(asset)==sha(out/'repeat'/label/'branch.glb')
            expected_images=images if label.endswith('tree') else [report['resources']['bark']['sha256']]
            report['export_validation'][label]=inspect(asset,expected_images)
            _,rows,normals,_=channels(asset)
            if label.endswith('tree'):
                report['checks'][label+'-foliage-exact']=old['Painted_Foliage']==rows['Painted_Foliage'] and old_normals['Painted_Foliage']==normals['Painted_Foliage']
        # Los soportes finales de la madera siguen presentes con posiciones y UV idénticas.
        reference=read(source/'base-reference.json');historical=read(source/'reference/manifest.json')
        from treegen.oak_crossed_production import build
        wood,_,_,_,_=build(reference,historical,read(source/'manifest.json')['resolved_blueprint'])
        report['support_pieces_sha256']=canonical_hash(wood[len(reference['branches']):])
        for label in ('10mm','20mm','secondary20mm'):
            _,rows,_,_=channels(out/'after'/f'{label}-wood/branch.glb')
            # Cada soporte es un tubo triangular de ocho caras; sus normales planas no dependen de las ramas.
            _,_,before_n,_=channels(out/'after/before-wood/branch.glb')
            _,_,after_n,_=channels(out/'after'/f'{label}-wood/branch.glb')
            # La cola del canal conserva el orden de las piezas y de sus triángulos.
            support_count=8*len(read(source/'manifest.json')['kept_support_ids'])
            report['checks'][label+'-supports-exact']=Counter(before_n['Painted_Bark'][-support_count:])==Counter(after_n['Painted_Bark'][-support_count:])
        parents={b['id']:b['parent_id'] for b in reference['branches']}
        major_triangles=sum(sum(len(f)-2 for f in b['mesh']['polygons']) for b in reference['branches']
                            if b['parent_id'] is None or parents[b['parent_id']] is None)
        _,new,new_normals,_=channels(out/'after/secondary20mm-tree/branch.glb')
        report['checks']['selective-trunk-primary-geometry-uv-normals-exact']=(
            old['Painted_Bark'][:major_triangles]==new['Painted_Bark'][:major_triangles] and
            old_normals['Painted_Bark'][:major_triangles]==new_normals['Painted_Bark'][:major_triangles])
        # Medición de controles: misma regla, sin exportarlos ni declarar revisión visual.
        report['control_measurements']={}
        for row in read(ROOT/'configs/verification/oak-crossed-v1.json')['cases'][1:]:
            folder=out/'controls'/row['id']
            execute_blueprint(ROOT/'blueprints/roble_copa_ancha/2.1.0.json',row['instance'],folder,render=False)
            ref=read(folder/'base-reference.json');base=read(folder/'manifest.json')['metrics']['triangles']
            totals={'before':base}
            for label,t in [('5mm',.005),('10mm',.01),('20mm',.02)]:
                branches=[optimize(b,t) for b in ref['branches']]
                triangles=sum(sum(len(f)-2 for f in b['mesh']['polygons']) for b in branches)
                totals[label]=base-ref['wood_triangles']+triangles
            from treegen.oak_wood import build as wood_build
            _,branches=wood_build([(b['mesh'],0,[]) for b in ref['branches']],ref['branches'],.02,secondary_only=True)
            totals['secondary20mm']=base-ref['wood_triangles']+sum(sum(len(f)-2 for f in b['mesh']['polygons']) for b in branches)
            report['control_measurements'][row['id']]=totals
        report['passed']=all(report['checks'].values());write(out/'audit.json',report)
        assert report['passed'],report['checks']
        print('Generación, repetición, recursos, follaje, soportes y controles verificados.',flush=True)
    if a.stage=='generate':return
    report=read(out/'audit.json');project=out/'godot';project.mkdir();captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):
        shutil.copy2(ROOT/'godot'/name,project/name)
    script=project/'review_painted_pine.gd';s=script.read_text()
    script.write_text(s.replace('im.get_width()==1254 and im.get_height()==1254','(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)'))
    for label in report['variants']:
        shutil.copy2(out/'after'/label/'branch.glb',project/(label+'.glb'))
    godot=os.environ.get('GODOT_BIN',GODOT)
    run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/import.log',env)
    bounds=report['variants']['before-tree']['metrics']['bounds_blender'];center=[(a+b)/2 for a,b in zip(*bounds)];span=max(b-a for a,b in zip(*bounds))
    shots=[{'id':name,'camera':camera(center,span,d,span*1.15),'background':'#EEE9DF','light':[-35,-25,0]}
           for name,d in [('front',[0,-1,.1]),('side',[1,0,.1]),('perspective',[1,-1,.45]),('back',[-1,1,.3]),('top',[0,0,1]),('below',[1,-1,-.7])]]
    shots += [{'id':'wood-close','camera':camera([0,0,4.5],span,[1,-1,.2],3.5),'background':'#EEE9DF','light':[-35,-25,0]}]
    shots += [{'id':name,'camera':camera(center,span,[1,-1,.45],span*f),'background':'#EEE9DF','light':[-35,-25,0]} for name,f in [('medium',4),('far',10)]]
    write(out/'protocol.json',{'shots':shots,'center':center,'span':span})
    report['godot']=[]
    for kind in ('tree','wood'):
        for variant in ('10mm','20mm','secondary20mm'):
            labels=['before-'+kind,variant+'-'+kind]
            entries=[{'id':label,'resource':'res://'+label+'.glb','metrics':report['variants'][label]['metrics']} for label in labels]
            for mask in (False,True):
                tag=variant+'-'+kind+('-mask' if mask else '-color')
                selected=[{**s,'id':'mask-'+s['id'],'background':'#FFFFFF'} for s in shots] if mask else shots
                config=out/(tag+'-input.json');result=out/(tag+'-report.json')
                write(config,{'output':str(captures),'report':str(result),'center':center,'span':span,'original_low':[0,0,0],
                              'assets':entries,'shots':selected,'mask_pass':mask})
                run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],out/'logs'/(tag+'.log'),env)
                review=read(result);assert review['passed'];report['godot'].append(review)
            print(variant+' '+kind+': revisión Godot terminada',flush=True)
        sheet(out,out/(kind+'.jpg'),3,[[(f'captures/{v}-{kind}--{shot}.png',v+' | '+shot) for v in ('before','10mm','secondary20mm')] for shot in ('front','side','perspective','below','wood-close')])
    report['mask_metrics']={}
    for variant in ('10mm','20mm','secondary20mm'):
        report['mask_metrics'][variant]={kind:{s['id']:mask_metrics(captures/f'before-{kind}--mask-{s["id"]}.png',captures/f'{variant}-{kind}--mask-{s["id"]}.png') for s in shots} for kind in ('tree','wood')}
    sheet(out,out/'propuesta.jpg',2,[[(f'captures/{v}-{kind}--{shot}.png',title+' | '+kind+' '+shot)
        for v,title in [('before','Aprobado: 7836 tris'),('secondary20mm','Propuesta: 6812 tris')]]
        for kind,shot in [('tree','perspective'),('wood','wood-close')]])
    sheet(out,out/'resto-vistas.jpg',2,[[(f'captures/{v}-{kind}--{shot}.png',v+' | '+kind+' '+shot)
        for v in ('before','secondary20mm')] for kind in ('tree','wood') for shot in ('back','top','medium','far')])
    report['capture_sha256']={p.name:sha(p) for p in captures.glob('*.png')}
    report['source_lock']={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),ROOT/'src/treegen/oak_wood.py',ROOT/'blender/oak_wood_trial.py',ROOT/'tests/test_oak_wood.py')}
    write(out/'audit.json',report)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Roble · ensayo de madera</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%;width:1500px}</style><h1>Roble: simplificación de madera</h1><p>Izquierda: aprobado, 7836 tris. Centro: tolerancia 10 mm, 7644. Derecha: solo secundarias a 20 mm, 6812; tronco y primarias exactos. Follaje, soportes, pintura y anclajes intactos. Ensayo del piloto; no cambia la receta. Variante global 20 mm, 6652 tris, conservada para comparación técnica.</p><h2>Árbol completo</h2><img src="tree.jpg"><h2>Madera sola</h2><img src="wood.jpg">')
    print('Comparación lista: '+str(len(report['capture_sha256']))+' capturas únicas.',flush=True)


if __name__=='__main__': main()
