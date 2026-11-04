#!/usr/bin/env python3
"""R1: rama bifurcada con follaje congelado y referencia Geometry Nodes."""
import argparse
import copy
from collections import Counter
import math
import os
from pathlib import Path
import shutil
import sys
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.branch_sample import make_network,average,ring_axes
from treegen.oak_crossed_production import build
from treegen.oak_painted_sample import wood_uv
from treegen.pine_painted_sample import canonical_hash
from treegen.runner import execute_blueprint,BLENDER
from treegen.evaluation import validate_glb
from treegen.oak_crossed_evaluation import channels
from verify_branch_space import run
from review_pine_painted import read,write,sha,camera
from verify_foliage_unit import GODOT
from foliage_evidence import sheet


def freeze(folder):
    manifest=read(folder/'manifest.json');ref=read(folder/'base-reference.json')
    source=read(folder/'reference/manifest.json')
    wood,panels,_,_,kept=build(ref,source,manifest['resolved_blueprint'])
    ids={'q3:primary:100'}
    ids.update(b['id'] for b in ref['branches'] if b['parent_id']=='q3:primary:100')
    count=len(ref['branches']);parts=[]
    for b,(mesh,_,uv) in zip(ref['branches'],wood[:count]):
        if b['id'] in ids:parts.append({**mesh,'uv':uv})
    for s,(mesh,_,uv) in zip(kept,wood[count:]):
        if s['parent_branch_id'] in ids:parts.append({**mesh,'uv':uv})
    support_ids={s['id'] for s in source['supports'] if s['parent_branch_id'] in ids}
    foliage=[p for p in panels if p['source_support_id'] in support_ids]
    primary=next(b for b in ref['branches'] if b['id']=='q3:primary:100')
    mesh=primary['mesh'];points=[];radii=[]
    for i in range(0,len(mesh['vertices']),8):
        ring=mesh['vertices'][i:i+8];center=average(ring)
        points.append(center);radii.append(min(math.dist(v,center) for v in ring))
    targets=[{'id':identifier,'point':average([v for p in foliage if p['source_support_id']==identifier for v in p['vertices']])}
             for identifier in sorted(support_ids)]
    return {'wood':parts,'foliage':foliage,'primary':{**mesh,'uv':wood_uv(primary)},
            'points':points,'radii':radii,'targets':targets,'source_glb_sha256':sha(folder/'tree.glb'),
            'source_manifest_sha256':sha(folder/'manifest.json')}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--stage',choices=('generate','review'),default='generate')
    a=p.parse_args();out=a.output.resolve()
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    if a.stage=='generate':
        out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
        reference=ROOT/'artifacts/f5/ensayo-01/candidate/joven-03'
        frozen=freeze(reference);write(out/'frozen-branch.json',frozen)
        network=make_network(frozen['points'],frozen['radii'],frozen['targets'],1003)
        write(out/'network.json',network)
        # Regenerar la base histórica por nodos; no extraerla de F5.
        instance=read(ROOT/'presets/blueprints/roble-madera/joven-07.json');instance['seeds']['base']=1003
        execute_blueprint(ROOT/'blueprints/roble_copa_ancha/2.2.0.json',instance,out/'nodes-source',render=False)
        nodes=freeze(out/'nodes-source');write(out/'nodes-branch.json',nodes)
        # Presentación rígida de la referencia: mismo origen/dirección principal,
        # sin escalar ni cambiar su ramificación o su propio follaje.
        def frame(points):
            u,v=ring_axes(points[0],points[-1]);d=[b-a for a,b in zip(points[0],points[-1])]
            size=math.sqrt(sum(x*x for x in d));return [u,v,[x/size for x in d]]
        original_frame=frame(nodes['points']);target_frame=frame(frozen['points'])
        origin=nodes['points'][0];destination=frozen['points'][0]
        def aligned(point):
            local=[sum((x-y)*z for x,y,z in zip(point,origin,axis)) for axis in original_frame]
            return [destination[k]+sum(local[j]*target_frame[j][k] for j in range(3)) for k in range(3)]
        presented=copy.deepcopy(nodes)
        for mesh in presented['wood']+presented['foliage']:
            mesh['vertices']=[aligned(v) for v in mesh['vertices']]
        write(out/'nodes-presentation.json',{'type':'rigid_rotation_translation_no_scale','source_origin':origin,'target_origin':destination,
                                           'source_basis':original_frame,'target_basis':target_frame})
        variants={'baseline':{'wood':frozen['wood'],'foliage':frozen['foliage']},
                  'candidate':{'wood':[frozen['primary']]+[e['mesh'] for e in network['edges']],'foliage':frozen['foliage']},
                  'nodes':{'wood':presented['wood'],'foliage':presented['foliage']},
                  'leaves-before':{'wood':[],'foliage':frozen['foliage']},
                  'leaves-after':{'wood':[],'foliage':frozen['foliage']}}
        write(out/'input.json',{'output':str(out),'variants':variants,'network_version':network['version']})
        # Proyección conservadora de costes, no integración ni certificado de rangos.
        projection={}
        for name in ('joven-03','adulto-07','viejo-02'):
            folder=ROOT/'artifacts/f5/ensayo-01/candidate'/name;ref=read(folder/'base-reference.json');m=read(folder/'manifest.json')
            major=[b for b in ref['branches'] if b['parent_id'] is None or b['parent_id']=='q3:trunk:0']
            triangles=sum(sum(len(f)-2 for f in b['mesh']['polygons']) for b in major)
            groups=m['support_count'];primary=len(major)-1
            bound=triangles+18*groups+18*(primary+1)
            assert bound<7000
            projection[name]={'major_wood_triangles':triangles,'groups':groups,'primary_count':primary,'complete_tree_upper_bound':bound,
                              'status':'cost_projection_only_not_integrated'}
        run([BLENDER,'--background','--factory-startup','--threads','1','--python-exit-code','1',
             '--python',ROOT/'blender/branch_sample.py','--',out/'input.json'],out/'logs/export.log',env,120)
        report=read(out/'exports.json');checks={}
        for name,item in report['variants'].items():
            metrics=item['metrics'];spec={'parameters':{'height_m':metrics['height_m']}}
            inspected=validate_glb(out/name/'tree.glb',spec,triangle_limit=6999)
            assert inspected['triangles']==metrics['triangles']
            doc,rows,_,images=channels(out/name/'tree.glb')
            item['channel_sha256']={name:canonical_hash(sorted(r)) for name,r in rows.items()}
            item['image_sha256']=images
        b=report['variants']['baseline'];c=report['variants']['candidate']
        checks['foliage_export_positions_uv_faces_exact']=b['channel_sha256']['Painted_Foliage']==c['channel_sha256']['Painted_Foliage']
        checks['foliage_only_glb_exact']=sha(out/'leaves-before/tree.glb')==sha(out/'leaves-after/tree.glb')
        checks['textures_exact']=b['image_sha256']==c['image_sha256']
        checks['all_targets_reached']=all(math.dist(t['point'],network['connections'][t['id']]['point'])<1e-10 for t in frozen['targets'])
        children=Counter(e['parent'] for e in network['edges'] if e['parent'] is not None)
        checks['maximum_two_children']=max(children.values(),default=0)<=2
        checks['budget_projections_valid']=all(v['complete_tree_upper_bound']<7000 for v in projection.values())
        report.update(checks=checks,passed=all(checks.values()),projection=projection,source=str(reference),
                      network={'edges':len(network['edges']),'targets':len(frozen['targets']),'triangles':network['triangles'],'maximum_depth':network['max_depth']},
                      artistic_acceptance='pending',sources_sha256={str(f.relative_to(ROOT)):sha(f) for folder in ('src/treegen','blender','scripts')
                          for f in (ROOT/folder).glob('*.py')},frozen_sha256=sha(out/'frozen-branch.json'))
        write(out/'verification.json',report);assert report['passed'],checks
        return
    review(out,env)


def review(out,env):
    report=read(out/'verification.json');project=out/'godot';project.mkdir();captures=out/'captures';captures.mkdir()
    assert all(sha(ROOT/name)==value for name,value in report['sources_sha256'].items())
    for name in ('project.godot','verify_oak.gd','review_painted_pine.gd','review_painted_oak_pilot.gd'):
        shutil.copy2(ROOT/'godot'/name,project/name)
    path=project/'review_painted_pine.gd';text=path.read_text().replace('im.get_width()==1254 and im.get_height()==1254',
        '(im.get_width()==1254 and im.get_height()==1254) or (im.get_width()==2000 and im.get_height()==2000)')
    text=text.replace("if mat.resource_name=='Painted_Foliage':","if mat.resource_name=='Painted_Foliage':\n\t\t\t\t\tmat.albedo_color.a=0.0 if shot.get('wood_only',false) else 1.0")
    path.write_text(text)
    entries=[];lows=[];highs=[]
    for name,item in report['variants'].items():
        shutil.copy2(out/name/'tree.glb',project/(name+'.glb'))
        entries.append({'id':name,'resource':'res://'+name+'.glb','metrics':item['metrics']})
        if name in ('baseline','candidate','nodes'):
            lo,hi=item['metrics']['bounds_blender'];lows.append(lo);highs.append(hi)
    low=[min(v[i] for v in lows) for i in range(3)];high=[max(v[i] for v in highs) for i in range(3)]
    center=[(a+b)/2 for a,b in zip(low,high)];span=max(b-a for a,b in zip(low,high))
    shots=[{'id':name,'camera':camera(center,span,direction,span*1.12),'background':'#EEE9DF','light':[-35,-25,0]}
           for name,direction in [('front',[0,-1,.1]),('side',[1,0,.1]),('perspective',[1,-1,.45]),('top',[0,0,1]),('below',[1,-1,-.5]),('back',[-1,1,.3])]]
    run([GODOT,'--headless','--path',project,'--editor','--import'],out/'logs/import.log',env)
    for mode,names in [('comparison',('baseline','candidate','nodes')),('mask',('leaves-before','leaves-after'))]:
        selected=[e for e in entries if e['id'] in names]
        all_shots=shots+[{**s,'id':'wood-'+s['id'],'wood_only':True} for s in shots] if mode=='comparison' else shots
        config=out/(mode+'-input.json');result=out/(mode+'-godot.json')
        write(config,{'output':str(captures),'report':str(result),'center':center,'span':span,'original_low':[0,0,0],
                      'assets':selected,'shots':all_shots,'mask_pass':mode=='mask'})
        run([GODOT,'--path',project,'--audio-driver','Dummy','--script','res://review_painted_oak_pilot.gd','--',config,'--visual'],
            out/'logs'/(mode+'.log'),env)
        assert read(result)['passed']
    checks=report['checks']
    for s in shots:
        a=Image.open(captures/('leaves-before--'+s['id']+'.png')).convert('RGB')
        b=Image.open(captures/('leaves-after--'+s['id']+'.png')).convert('RGB')
        checks['mask-'+s['id']+'-exact']=ImageChops.difference(a,b).getbbox() is None
    for mode in ('tree','wood'):
        rows=[[(f'captures/{name}--'+('wood-' if mode=='wood' else '')+s['id']+'.png',name+' '+s['id'])
               for name in ('baseline','candidate','nodes')] for s in shots]
        sheet(out,out/(mode+'.jpg'),3,rows)
    report.update(passed=all(checks.values()),captures_sha256={p.name:sha(p) for p in captures.glob('*.png')},visual_review='pending_agent')
    write(out/'verification.json',report)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Rama R1</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}</style><h1>Rama R1</h1><p>Columnas: Python F5 anterior; red jerárquica con follaje idéntico; referencia por nodos con follaje propio, alineada rígidamente al eje principal sin escalar. Cámaras comunes. Arte pendiente.</p><h2>Sin follaje</h2><img src="wood.jpg"><h2>Con follaje</h2><img src="tree.jpg">')
    assert report['passed']


if __name__=='__main__':main()
