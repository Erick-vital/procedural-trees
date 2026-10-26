#!/usr/bin/env python3
"""Piloto completo: generar, repetir, auditar y revisar pintura/poda por separado."""
import argparse
from collections import Counter
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.runner import execute_blueprint,BLENDER
from treegen.pine_painted_sample import canonical_hash
from treegen.oak_painted_sample import select
from treegen.foliage_canopy import diamond_vertices
from treegen.foliage_molds import connection_geometry
from review_pine_painted import read,write,run,sha,camera
from verify_foliage_unit import GODOT
from oak_painted_sample import inspect
from oak_sample_evidence import channel
from verify_painted_oak import mask_metrics
from foliage_evidence import sheet


def triangles(path,name):return Counter(tuple(tuple(v) for v in t) for t in channel(path,name))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--stage',choices=['all','generate','review'],default='all')
    a=p.parse_args();out=a.output.resolve()
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    if a.stage in ('all','generate'):
        out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
        request=read(ROOT/'configs/verification/b3-v2.json')['cases'][0]['instance']
        source=execute_blueprint(ROOT/'blueprints/roble_copa_ancha/1.2.0.json',request,out/'source',render=False)
        expected=read(ROOT/'docs/evidence/blueprints/b3-revision/verification.json')['cases']['pilot']['glb_sha256']
        assert source['glb_sha256']==expected
        for name in ('main','repeat'):
            target=out if name=='main' else out/'repeat'
            if name=='repeat':
                target.mkdir();shutil.copytree(out/'source',target/'source')
            run([os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1',
                '--python',ROOT/'blender/oak_painted_tree_pilot.py','--',target],out/'logs'/(name+'.log'),env)
        report=read(out/'manifest.json');variants=report['variants'];hashes=report['resources']
        report['export_validation']={}
        report['repeat_glb_identical']={}
        for name in variants:
            images=[hashes['bark.png']['sha256']]+([hashes['foliage.png']['sha256']] if name.startswith('painted') else [])
            report['export_validation'][name]=inspect(out/name/'tree.glb',images)
            report['repeat_glb_identical'][name]=sha(out/name/'tree.glb')==sha(out/'repeat'/name/'tree.glb')
        assert all(report['repeat_glb_identical'].values())
        assert len(report['kept_support_ids'])==120 and len(report['removed_support_ids'])==144 and report['leaf_count']==1584
        assert canonical_hash(source['placements'])==report['source_placements_sha256']
        assert canonical_hash(source['supports'])==report['source_supports_sha256']
        assert variants['painted-full']['metrics']['triangles']==10572 and variants['painted']['metrics']['triangles']==9420
        full=triangles(out/'wood-full/tree.glb','Painted_Bark');pruned=triangles(out/'wood/tree.glb','Painted_Bark')
        original=triangles(out/'source/tree.glb','Oak_Bark')
        assert not (pruned-full) and sum((full-pruned).values())==1152
        assert not (original-pruned) and sum(original.values())==5292
        assert triangles(out/'painted-full/tree.glb','Painted_Foliage')==triangles(out/'painted/tree.glb','Painted_Foliage')
        report['geometry_audit']={'remaining_wood_positions_normals_exact':True,'historical_main_wood_positions_normals_exact':True,
            'main_wood_triangles':5292,'removed_twig_triangles':1152,'painted_leaf_geometry_normals_exact_across_pruning':True,
            'all_placements_unchanged':True,'known_leaf_groups_without_original_support':144}
        files=[ROOT/'scripts/oak_painted_tree_pilot.py',ROOT/'scripts/oak_painted_sample.py',ROOT/'scripts/oak_sample_evidence.py',ROOT/'scripts/verify_painted_oak.py',ROOT/'scripts/review_pine_painted.py',ROOT/'scripts/foliage_evidence.py',
               ROOT/'blender/oak_painted_tree_pilot.py',ROOT/'blender/oak_painted_sample.py',ROOT/'blender/pine_painted_sample.py',ROOT/'blender/foliage_lab.py',
               ROOT/'src/treegen/oak_painted_tree.py',ROOT/'src/treegen/oak_painted_sample.py',ROOT/'src/treegen/foliage_molds.py',
               ROOT/'godot/review_painted_oak_pilot.gd',ROOT/'godot/review_painted_pine.gd',ROOT/'godot/verify_oak.gd',ROOT/'godot/project.godot',*sorted((ROOT/'assets/roble-pintado/v0.2.0').glob('*'))]
        report['source_lock']={str(f.relative_to(ROOT)):sha(f) for f in files if f.is_file()}
        write(out/'manifest.json',report);print('Piloto generado: 9420 tris; 1584 hojas; cuatro GLB repetidos idénticos.',flush=True)
    if a.stage=='generate':return
    report=read(out/'manifest.json');assert all(sha(ROOT/f)==h for f,h in report['source_lock'].items())
    source=read(out/'source/manifest.json');variants=report['variants']
    project=out/'godot';project.mkdir(exist_ok=False);captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):shutil.copy2(ROOT/'godot'/name,project/name)
    entries=[]
    for name in ('historical','painted-full','painted','wood-full','wood'):
        path=out/'source/tree.glb' if name=='historical' else out/name/'tree.glb'
        shutil.copy2(path,project/(name+'.glb'))
        entries.append({'id':name,'resource':'res://'+name+'.glb','metrics':source['metrics'] if name=='historical' else variants[name]['metrics']})
    bounds=source['metrics']['bounds_blender'];center=[(a+b)/2 for a,b in zip(*bounds)];span=max(b-a for a,b in zip(*bounds))
    views=[('front',[0,-1,.1]),('side',[1,0,.1]),('perspective',[1,-1,.45]),('back',[-1,1,.3]),('top',[0,0,1]),('below',[1,-1,-.7])]
    shots=[{'id':n,'camera':camera(center,span,d,span*1.15),'background':'#EEE9DF','light':[-35,-25,0]} for n,d in views]
    shots += [{'id':n,'camera':camera(center,span,[1,-1,.45],span*factor),'background':'#EEE9DF','light':[-35,-25,0]} for n,factor in [('near',2),('medium',4),('far',10)]]
    # Mismo encuadre sobre el grupo de rama usado en la muestra aprobada.
    ref=read(out/'source/base-reference.json');branch_wood,branch_supports,branch_leaves=select(ref,source)
    wood_vertices=[v for b in branch_wood for v in b['mesh']['vertices']]
    wood_vertices += [v for s in branch_supports for v in connection_geometry(s,source['canopy_spec'])[0]]
    all_vertices=wood_vertices+[v for leaf in branch_leaves for v in diamond_vertices(leaf)]
    branch_span=max(max(v[k] for v in all_vertices)-min(v[k] for v in all_vertices) for k in range(3))
    branch_center=[(max(v[k] for v in wood_vertices)+min(v[k] for v in wood_vertices))/2 for k in range(3)]
    shots.append({'id':'branch-close','camera':camera(branch_center,branch_span,[1,-1,.45],branch_span*.6),'background':'#EEE9DF','light':[-35,-25,0]})
    shots.append({'id':'trunk-close','camera':camera([0,0,1.7],span,[1,-1,.2],3.2),'background':'#EEE9DF','light':[-35,-25,0]})
    write(out/'protocol.json',{'center':center,'span':span,'shots':shots})
    godot=os.environ.get('GODOT_BIN',GODOT);run([godot,'--headless','--path',project,'--editor','--import'],out/'logs/import.log',env)
    reviews=[]
    for mode in ('color','mask'):
        mode_entries=entries if mode=='color' else entries[:3]
        selected=shots if mode=='color' else [{**s,'id':'mask-'+s['id'],'background':'#FFFFFF'} for s in shots[:9]]
        for i in range(0,len(mode_entries),2):
            name=mode+'-'+str(i);config=out/(name+'-input.json');result=out/(name+'-report.json')
            write(config,{'output':str(captures),'report':str(result),'center':center,'span':span,'original_low':[0,0,0],
                'assets':mode_entries[i:i+2],'shots':selected,'mask_pass':mode=='mask'})
            run([godot,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],out/'logs'/(name+'.log'),env)
            review=read(result);assert review['passed'];reviews.append(review);print(name+': capturas OK',flush=True)
    report['godot']=reviews;report['mask_metrics']={}
    for comparison,a_name,b_name in [('painting','historical','painted-full'),('pruning','painted-full','painted')]:
        report['mask_metrics'][comparison]={s['id']:mask_metrics(captures/(a_name+'--mask-'+s['id']+'.png'),captures/(b_name+'--mask-'+s['id']+'.png')) for s in shots[:9]}
    report['capture_sha256']={f.name:sha(f) for f in captures.glob('*.png')}
    assert len(report['capture_sha256'])==82
    for filename,names,selected in [('painting',('historical','painted-full','painted'),('front','side','perspective','back','top','below')),
         ('pruning',('painted-full','painted'),('front','perspective','below','branch-close')),
         ('distances',('historical','painted-full','painted'),('near','medium','far')),
         ('bark',('wood-full','wood'),('branch-close','trunk-close','below')),
         ('masks',('historical','painted-full','painted'),('mask-front','mask-perspective','mask-far'))]:
        sheet(out,out/(filename+'.jpg'),len(names),[[(f'captures/{n}--{v}.png',n+' | '+v) for n in names] for v in selected])
    write(out/'manifest.json',report)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Roble pintado · piloto completo</title><style>body{font:18px sans-serif;background:#eee9df;margin:28px}img{width:100%;max-width:1200px}figure{margin:0 0 30px}</style><h1>Roble completo · piloto 3009 / 17 / 2718</h1><p>historical: original aprobado. painted-full: pintura nueva con todas las ramillas. painted: propuesta con ramillas solo en secundarias. 1584 hojas conservadas. 10572 → 9420 tris; aceptación artística pendiente.</p>'+''.join('<h2>'+title+'</h2><a href="'+n+'.jpg"><img src="'+n+'.jpg"></a>' for n,title in [('painting','Original / pintura / propuesta'),('pruning','Efecto de quitar ramillas'),('distances','Distancias'),('bark','Madera y corteza'),('masks','Contorno sin iluminación')])+'<h2>Capturas individuales</h2>'+''.join('<a href="captures/'+n+'">'+n+'</a><br>' for n in sorted(report['capture_sha256'])))
    print('Piloto listo: 82 capturas reales; métricas de pintura y poda separadas.',flush=True)


if __name__=='__main__':main()
