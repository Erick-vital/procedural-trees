#!/usr/bin/env python3
"""R2: simplificar solo madera ocluida y comparar en Godot con copa congelada."""
import argparse
from collections import Counter
import copy
import math
import os
from pathlib import Path
import shutil
import sys
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.branch_visibility import prune_network
from treegen.pine_painted_sample import canonical_hash
from treegen.evaluation import validate_glb
from treegen.oak_crossed_evaluation import channels
from treegen.runner import BLENDER
from verify_foliage_unit import GODOT
from verify_branch_space import run
from review_pine_painted import read,write,sha,camera
from foliage_evidence import sheet


def snapshot():
    return {str(p.relative_to(ROOT)):sha(p) for folder in ('src/treegen','blender','scripts','godot')
            for p in (ROOT/folder).glob('*') if p.suffix in ('.py','.gd','.godot')}


def matrix(center,span):
    basic=[('front',[0,-1,.1]),('side',[1,0,.1]),('perspective',[1,-1,.45]),
           ('top',[0,0,1]),('below',[1,-1,-.5]),('back',[-1,1,.3])]
    shots=[]
    for distance,scale in [('near',.8),('medium',1.4),('far',2.5)]:
        for view,direction in basic:
            shots.append({'id':distance+'-'+view,'camera':camera(center,span,direction,span*scale),
                          'background':'#EEE9DF','light':[-35,-25,0]})
    # Giro de inspección independiente de los azimuts 0/15° de la clasificación.
    for i in range(8):
        angle=math.radians(7.5+45*i)
        shots.append({'id':f'orbit-{i:02}','camera':camera(center,span,[math.cos(angle),math.sin(angle),-.25],span),
                      'background':'#EEE9DF','light':[-35,-25,0]})
    for i,light in enumerate(([-35,-25,0],[-35,-90,0],[-35,155,0])):
        shots.append({'id':f'shadow-{i}','camera':camera(center,span,[1,-1,.45],span*1.2),
                      'background':'#EEE9DF','light':light,'receiver':True})
    return shots


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--source',type=Path,default=ROOT/'artifacts/f5/rama-r1-03')
    p.add_argument('--stage',choices=('generate','review'),default='generate')
    a=p.parse_args();out=a.output.resolve();source=a.source.resolve()
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    if a.stage=='generate':
        out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
        original=read(source/'input.json')['variants']['candidate'];network=read(source/'network.json')
        write(out/'source-frozen.json',{'source':str(source),'source_input_sha256':sha(source/'input.json'),
            'source_network_sha256':sha(source/'network.json'),'original':original,'network':network})
        alpha=Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').getchannel('A');alpha_path=out/'alpha.bin';alpha_path.write_bytes(alpha.tobytes())
        classify={'output':str(out),'network':network,'foliage':original['foliage'],'alpha_path':str(alpha_path),
                  'alpha_size':list(alpha.size),'alpha_sha256':sha(alpha_path)}
        write(out/'visibility-input.json',classify)
        # Congelar vistas/condiciones antes de conocer el ahorro.
        old=read(source/'exports.json')['variants']['candidate']['metrics'];lo,hi=old['bounds_blender']
        center=[(a+b)/2 for a,b in zip(lo,hi)];span=max(b-a for a,b in zip(lo,hi))
        write(out/'view-matrix.json',{'center':center,'span':span,'shots':matrix(center,span)})
        sources=snapshot();write(out/'sources.json',sources)
        run([BLENDER,'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',
             ROOT/'blender/classify_branch_visibility.py','--',out/'visibility-input.json'],out/'logs/classify.log',env,120)
        visibility=read(out/'visibility.json');simple,audit=prune_network(network,visibility['protected_exposed_ids'])
        write(out/'selection.json',audit);write(out/'network-simple.json',simple)
        variants={'full':original,'simple':{'wood':[original['wood'][0]]+[e['mesh'] for e in simple['edges']],'foliage':original['foliage']},
                  'foliage-before':{'wood':[],'foliage':original['foliage']},'foliage-after':{'wood':[],'foliage':original['foliage']}}
        job={'output':str(out),'variants':variants};write(out/'input.json',job)
        run([BLENDER,'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',
             ROOT/'blender/branch_sample.py','--',out/'input.json'],out/'logs/export.log',env,120)
        repeat=out/'repeat';repeat.mkdir();write(repeat/'input.json',{**job,'output':str(repeat)})
        run([BLENDER,'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',
             ROOT/'blender/branch_sample.py','--',repeat/'input.json'],out/'logs/repeat.log',env,120)
        report=read(out/'exports.json');checks={};channel_data={};repeated=read(repeat/'exports.json')
        for name,item in report['variants'].items():
            metrics=item['metrics'];inspection=validate_glb(out/name/'tree.glb',{'parameters':{'height_m':metrics['height_m']}},triangle_limit=6999)
            checks[name+'-export']=inspection['triangles']==metrics['triangles'] and len(inspection['materials'])<=2
            channel_data[name]=channels(out/name/'tree.glb')
            checks[name+'-repeat-exact']=item['glb_sha256']==repeated['variants'][name]['glb_sha256']
        full=channel_data['full'];simple_data=channel_data['simple']
        checks['foliage_positions_faces_uv_exact']=sorted(full[1]['Painted_Foliage'])==sorted(simple_data[1]['Painted_Foliage'])
        checks['foliage_normals_exact']=sorted(full[2]['Painted_Foliage'])==sorted(simple_data[2]['Painted_Foliage'])
        checks['wood_is_exact_subset']=not (Counter(simple_data[1]['Painted_Bark'])-Counter(full[1]['Painted_Bark']))
        checks['textures_exact']=full[3]==simple_data[3]
        checks['foliage_only_glb_exact']=sha(out/'foliage-before/tree.glb')==sha(out/'foliage-after/tree.glb')
        checks['full_reference_glb_exact']=sha(out/'full/tree.glb')==sha(source/'candidate/tree.glb')
        checks['exposed_meshes_retained_exact']=all(e['id'] in audit['kept_ids'] for e in network['edges'] if e['id'] in visibility['protected_exposed_ids'])
        checks['work_reduced']=report['variants']['simple']['metrics']['triangles']<1700
        report.update(checks=checks,passed=all(checks.values()),source=str(source),selection=audit,
            sources_sha256=sources,alpha_png_sha256=sha(ROOT/'assets/roble-pintado/v0.3.0/foliage.png'),
            artistic_acceptance='pending',geometry_claim='visible_source_meshes_and_ancestors_retained_exact_finite_sampling')
        write(out/'verification.json',report);assert report['passed'],checks
        print('Tris:',report['variants']['full']['metrics']['triangles'],'→',report['variants']['simple']['metrics']['triangles'],flush=True)
        return
    review(out,env)


def compare_images(a,b):
    with Image.open(a) as ia,Image.open(b) as ib:
        ia=ia.convert('RGB');ib=ib.convert('RGB');diff=ImageChops.difference(ia,ib)
        changed=sum(any(channel for channel in pixel) for pixel in diff.get_flattened_data())
        return {'changed_pixels':changed,'total_pixels':ia.width*ia.height,'changed_fraction':changed/(ia.width*ia.height),
                'max_channel_delta':max(hi for lo,hi in diff.getextrema())}


def wood_pixels(path):
    with Image.open(path) as im:return [r>g+32 and r>b+32 for r,g,b in im.convert('RGB').get_flattened_data()]


def review(out,env):
    report=read(out/'verification.json');assert report['sources_sha256']==snapshot(),'Fuentes cambiadas'
    project=out/'godot';project.mkdir();captures=out/'captures';captures.mkdir()
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd','review_branch_visibility.gd'):
        shutil.copy2(ROOT/'godot'/name,project/name)
    path=project/'review_painted_pine.gd';text=path.read_text().replace('im.get_width()==1254 and im.get_height()==1254',
        '(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)')
    text=text.replace("if mat.resource_name=='Painted_Foliage':","if mat.resource_name=='Painted_Foliage':\n\t\t\t\t\tmat.albedo_color.a=0.0 if shot.get('wood_only',false) else 1.0")
    path.write_text(text)
    entries=[]
    for name,item in report['variants'].items():
        shutil.copy2(out/name/'tree.glb',project/(name+'.glb'))
        entries.append({'id':name,'resource':'res://'+name+'.glb','metrics':item['metrics']})
    view=read(out/'view-matrix.json');shots=view['shots'];basic=[s for s in shots if s['id'].startswith('medium-')]
    run([GODOT,'--headless','--path',project,'--editor','--import'],out/'logs/import.log',env)
    report['godot']={}
    for mode,names,script,selected_shots in [
        ('color',('full','simple'),'review_painted_oak_pilot.gd',shots+[{**s,'id':'wood-'+s['id'],'wood_only':True} for s in basic]),
        ('visible-wood',('full','simple'),'review_branch_visibility.gd',[s for s in shots if not s.get('receiver')]),
        ('mask',('foliage-before','foliage-after'),'review_painted_oak_pilot.gd',basic)]:
        folder=captures/mode;folder.mkdir();config=out/(mode+'-input.json');result=out/(mode+'-godot.json')
        write(config,{'output':str(folder),'report':str(result),'center':view['center'],'span':view['span'],'original_low':[0,0,0],
                      'assets':[e for e in entries if e['id'] in names],'shots':selected_shots,'mask_pass':mode=='mask'})
        run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://'+script,'--',config,'--visual'],out/'logs'/(mode+'.log'),env)
        data=read(result);assert data['passed'];report['godot'][mode]=data
    report['image_comparison']={};report['visible_wood_comparison']={}
    for shot in shots:
        name=shot['id'];report['image_comparison'][name]=compare_images(captures/'color'/('full--'+name+'.png'),captures/'color'/('simple--'+name+'.png'))
        if shot.get('receiver'):continue
        before=wood_pixels(captures/'visible-wood'/('full--'+name+'.png'));after=wood_pixels(captures/'visible-wood'/('simple--'+name+'.png'))
        report['visible_wood_comparison'][name]={'reference_pixels':sum(before),'lost_pixels':sum(a and not b for a,b in zip(before,after)),
                                               'gained_pixels':sum(b and not a for a,b in zip(before,after))}
    report['checks']['visible_wood_masks_exact']=all(v['lost_pixels']==0 and v['gained_pixels']==0 for v in report['visible_wood_comparison'].values())
    for shot in basic:
        name=shot['id'];result=compare_images(captures/'mask'/('foliage-before--'+name+'.png'),captures/'mask'/('foliage-after--'+name+'.png'))
        report['checks']['foliage-mask-'+name+'-exact']=result['changed_pixels']==0
    for distance in ('near','medium','far'):
        sheet(out,out/(distance+'.jpg'),2,[[(f'captures/color/{name}--{s["id"]}.png',name+' '+s['id']) for name in ('full','simple')]
            for s in shots if s['id'].startswith(distance+'-')])
    sheet(out,out/'wood.jpg',2,[[(f'captures/color/{name}--wood-{s["id"]}.png',name+' '+s['id']) for name in ('full','simple')] for s in basic])
    sheet(out,out/'visible-wood.jpg',2,[[(f'captures/visible-wood/{name}--{s["id"]}.png',name+' '+s['id']) for name in ('full','simple')] for s in basic])
    report.update(passed=all(report['checks'].values()),captures_sha256={str(p.relative_to(captures)):sha(p) for p in captures.rglob('*.png')},visual_review='pending_agent')
    write(out/'verification.json',report)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>R2: rama simplificada</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}</style><h1>R2: completa izquierda / simplificada derecha</h1><p>Mismo follaje. Madera visible protegida por muestreo alfa y ancestros. Comparación artística pendiente.</p>'+''.join('<h2>'+label+'</h2><img src="'+name+'.jpg">' for name,label in [('near','Cerca'),('medium','Media'),('far','Lejos'),('wood','Madera descubierta'),('visible-wood','Madera visible a través de la copa')]))
    print('Máximo de píxeles de madera perdidos:',max(v['lost_pixels'] for v in report['visible_wood_comparison'].values()),flush=True)


if __name__=='__main__':main()
