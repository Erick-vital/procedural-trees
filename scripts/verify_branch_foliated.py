#!/usr/bin/env python3
"""R3: madera R2 para rama desnuda y reducción adicional con copa intacta."""
import argparse
from collections import Counter
import copy
import os
from pathlib import Path
import sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.branch_visibility import prune_network
from treegen.branch_interior import proposals,apply_proposals
from treegen.evaluation import validate_glb
from treegen.oak_crossed_evaluation import channels
from treegen.runner import BLENDER
from review_pine_painted import read,write,sha
from verify_branch_space import run
from verify_branch_simplification import snapshot,review,matrix


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--stage',choices=('generate','review'),default='generate');p.add_argument('--cutoff',type=int,choices=(128,160),default=128)
    a=p.parse_args();out=a.output.resolve()
    env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
    if a.stage=='review':
        review(out,env);return
    out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
    source=ROOT/'artifacts/f5/rama-r2-03';source_job=read(source/'input.json');original=source_job['variants']['simple']
    current=read(source/'network-simple.json');frozen=copy.deepcopy(current)
    write(out/'source-frozen.json',{'source':str(source),'source_input_sha256':sha(source/'input.json'),
                                  'network_sha256':sha(source/'network-simple.json'),'original':original,'network':current})
    alpha=Image.open(ROOT/'assets/roble-pintado/v0.3.0/foliage.png').getchannel('A')
    raw_alpha=alpha.tobytes();binary_alpha=bytes(255 if value>=a.cutoff else 0 for value in raw_alpha)
    alpha_path=out/'alpha-thresholded.bin';alpha_path.write_bytes(binary_alpha)
    write(out/'alpha-profile.json',{'version':'alpha-threshold-preprocess-0.1.0','raw_cutoff_u8':a.cutoff,'output_values':[0,255],
        'underlying_classifier_cutoff_u8':217,'source_png_sha256':sha(ROOT/'assets/roble-pintado/v0.3.0/foliage.png'),
        'derived_alpha_sha256':sha(alpha_path),'changes_rendered_alpha':False})
    lo,hi=read(source/'exports.json')['variants']['simple']['metrics']['bounds_blender'];center=[(x+y)/2 for x,y in zip(lo,hi)];span=max(y-x for x,y in zip(lo,hi))
    write(out/'view-matrix.json',{'center':center,'span':span,'shots':matrix(center,span)})
    sources=snapshot();write(out/'sources.json',sources)

    def classify(edges,label):
        folder=out/label;folder.mkdir()
        job={'output':str(folder),'network':{'edges':edges},'foliage':original['foliage'],
             'alpha_path':str(alpha_path),'alpha_size':list(alpha.size)}
        write(folder/'input.json',job)
        run([BLENDER,'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',
             ROOT/'blender/classify_branch_visibility.py','--',folder/'input.json'],out/'logs'/(label+'.log'),env,120)
        return read(folder/'visibility.json')

    visibility=classify(current['edges'],'visibility-initial');protected=set(visibility['protected_exposed_ids'])
    current,pruning=prune_network(current,protected);write(out/'selection.json',pruning)
    rounds=[]
    for i in range(3):
        options=proposals(current,protected)
        if not options:break
        candidates=[]
        for option in options:
            for edge in option['replacements']:
                candidates.append({**edge,'id':option['removed']+'>'+edge['id']})
        assert len(candidates)<=720
        classification=classify(candidates,f'visibility-collapse-{i}')
        hidden={e['id'] for e in candidates}-set(classification['protected_exposed_ids'])
        current,audit=apply_proposals(current,options,hidden);rounds.append(audit)
        if not audit['accepted']:break
    write(out/'collapse-rounds.json',rounds);write(out/'network-simple.json',current)
    variants={'full':original,'simple':{'wood':[original['wood'][0]]+[e['mesh'] for e in current['edges']],'foliage':original['foliage']},
              'bare':{'wood':original['wood'],'foliage':[]},
              'foliage-before':{'wood':[],'foliage':original['foliage']},'foliage-after':{'wood':[],'foliage':original['foliage']}}
    job={'output':str(out),'variants':variants};write(out/'input.json',job)
    for label,folder in [('export',out),('repeat',out/'repeat')]:
        if label=='repeat':folder.mkdir();write(folder/'input.json',{**job,'output':str(folder)})
        run([BLENDER,'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',
             ROOT/'blender/branch_variants.py','--',folder/'input.json'],out/'logs'/(label+'.log'),env,120)
    report=read(out/'exports.json');repeat=read(out/'repeat/exports.json');checks={};data={}
    for name,item in report['variants'].items():
        metrics=item['metrics'];v=validate_glb(out/name/'tree.glb',{'parameters':{'height_m':metrics['height_m']}},triangle_limit=6999)
        checks[name+'-export']=v['triangles']==metrics['triangles'] and len(v['materials'])<=2
        checks[name+'-repeat-exact']=item['glb_sha256']==repeat['variants'][name]['glb_sha256']
        data[name]=channels(out/name/'tree.glb')
    checks['foliage_positions_faces_uv_exact']=sorted(data['full'][1]['Painted_Foliage'])==sorted(data['simple'][1]['Painted_Foliage'])
    checks['foliage_normals_exact']=sorted(data['full'][2]['Painted_Foliage'])==sorted(data['simple'][2]['Painted_Foliage'])
    checks['foliage_only_glb_exact']=sha(out/'foliage-before/tree.glb')==sha(out/'foliage-after/tree.glb')
    checks['full_reference_glb_exact']=sha(out/'full/tree.glb')==sha(source/'simple/tree.glb')
    checks['bare_wood_r2_exact']=sorted(data['bare'][1]['Painted_Bark'])==sorted(data['full'][1]['Painted_Bark'])
    checks['textures_exact']=data['full'][3]==data['simple'][3]
    old={e['id']:e for e in frozen['edges']};now={e['id']:e for e in current['edges']}
    checks['exposed_meshes_exact']=all(identifier in now and now[identifier]['mesh']==old[identifier]['mesh'] for identifier in protected)
    checks['roots_exact']=all(e['id'] in now and now[e['id']]['mesh']==e['mesh'] for e in frozen['edges'] if e['parent'] is None)
    checks['extra_reduction']=report['variants']['simple']['metrics']['triangles']<report['variants']['full']['metrics']['triangles']
    report.update(phase='R3',cutoff_u8=a.cutoff,passed=all(checks.values()),checks=checks,source=str(source),sources_sha256=sources,
                  selection=pruning,collapse_rounds=rounds,exposed_ids=sorted(protected),bare_artistic_acceptance='approved_user_r2',
                  artistic_acceptance='pending_for_new_foliated_variant')
    write(out/'verification.json',report);assert report['passed'],checks
    print('Alfa',a.cutoff,'R2',report['variants']['full']['metrics']['triangles'],'R3',report['variants']['simple']['metrics']['triangles'],
          'sin follaje',report['variants']['bare']['metrics']['triangles'],flush=True)


if __name__=='__main__':main()
