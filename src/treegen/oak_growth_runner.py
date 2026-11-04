"""Ejecutor acotado y reproducible de arquitectura, independiente de recetas previas."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import hashlib
import math
from collections import Counter
from .contracts import ROOT
from .runner import BLENDER,write_json,timestamp
from .oak_growth_contract import validate_seed,triangle_bound
from .oak_crown_contract import load_growth_preset as load_preset
from .oak_growth import generate,sample
from .oak_growth_mesh import meshes
from .branch_structure import sub,length,dot
from .evaluation import validate_glb
from .oak_growth import unit


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def architecture_metrics(s):
    branches=s['branches'];h=s['preset']['height_m'];index={b['id']:b for b in branches};primary=[b for b in branches if b['order']==1]
    allp=[v for b in branches for v in b['points']];low=[min(v[k] for v in allp) for k in range(3)];high=[max(v[k] for v in allp) for k in range(3)]
    turns=[];sinuosity=[];joins=[]
    for b in branches:
        sizes=[length(sub(y,x)) for x,y in zip(b['points'],b['points'][1:])]
        sinuosity.append(sum(sizes)/length(sub(b['points'][-1],b['points'][0])))
        directions=[unit(sub(y,x)) for x,y in zip(b['points'],b['points'][1:])]
        turns.extend(math.degrees(math.acos(max(-1,min(1,dot(a,c))))) for a,c in zip(directions,directions[1:]))
        if b['parent_id'] is not None:
            root,_=sample(index[b['parent_id']]['points'],b['parent_t']);joins.append(length(sub(root,b['points'][0])))
    return {'counts_by_order':dict(Counter(b['order'] for b in branches)),
        'primary_birth_heights_over_H':[b['points'][0][2]/h for b in primary],
        'primary_birth_span_over_H':(max(b['points'][0][2] for b in primary)-min(b['points'][0][2] for b in primary))/h,
        'axis_height_over_H':branches[0]['points'][-1][2]/h,'width_over_H':(high[0]-low[0])/h,'depth_over_H':(high[1]-low[1])/h,
        'primary_sinuosity':[sum(length(sub(y,x)) for x,y in zip(b['points'],b['points'][1:]))/length(sub(b['points'][-1],b['points'][0])) for b in primary],
        'maximum_segment_turn_deg':max(turns),'maximum_centerline_join_error_m':max(joins),
        'maximum_ring_radius_ratio':max(max(a/b,b/a) for r in branches for a,b in zip(r['radii'],r['radii'][1:])),
        'minimum_join_radius_scale':min(b.get('join_radius_scale',1.) for b in branches),
        'sinuosity_range':[min(sinuosity),max(sinuosity)]}


def execute_growth(preset_path,seed,output):
    preset=load_preset(preset_path);validate_seed(seed)
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
    if preset['version']=='oak-growth-0.5.0':
        from .oak_periphery_contract import triangle_bound as bound
    elif preset['version']=='oak-growth-0.4.0':
        from .oak_volume_contract import triangle_bound as bound
    elif preset['version']=='oak-growth-0.3.0':
        from .oak_branching_contract import triangle_bound as bound
    else:bound=triangle_bound
    started=time.monotonic();sources={str(p.relative_to(ROOT)):sha(p) for p in [*(ROOT/'src/treegen').glob('*.py'),*(ROOT/'blender').glob('*.py')]}
    manifest={'version':preset['version'],'status':'running','started_at':timestamp(),'seed':seed,'preset':preset,'preset_sha256':sha(preset_path),'source_inventory':sources,
        'limits':{'generation_seconds':120,'triangles_wood_upper_bound':bound(preset),'foliage_reserve_triangles':1584,'complete_tree_upper_bound':bound(preset)+1584},
        'scope':'bare_architecture; foliage_integration_pending','artistic_acceptance':'pending_user'}
    write_json(out/'manifest.json',manifest)
    try:
        if preset['version']=='oak-growth-0.5.0':
            from .oak_growth_v5 import generate as generator
        elif preset['version']=='oak-growth-0.4.0':
            from .oak_growth_v4 import generate as generator
        elif preset['version']=='oak-growth-0.3.0':
            from .oak_growth_v3 import generate as generator
        elif preset['version']=='oak-growth-0.2.0':
            from .oak_growth_v2 import generate as generator
        else:generator=generate
        s=generator(preset,seed);pieces=meshes(s);write_json(out/'structure.json',s)
        job={'output':str(out),'branches':[{**b,'sides':next(r['sides'] for r in s['branches'] if r['id']==b['id'])} for b in pieces],
             'variants':{'bare':{'wood':[b['mesh'] for b in pieces],'foliage':[]},'scaffold':{'wood':[b['mesh'] for b in pieces if b['order']<=1],'foliage':[]}}}
        write_json(out/'input.json',job)
        env=dict(os.environ,XDG_DATA_HOME=str(out/'xdg/data'),XDG_CONFIG_HOME=str(out/'xdg/config'),XDG_CACHE_HOME=str(out/'xdg/cache'))
        with (out/'logs/export.log').open('w') as log:
            process=subprocess.Popen([os.environ.get('BLENDER_BIN',BLENDER),'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',str(ROOT/'blender/export_oak_growth.py'),'--',str(out/'input.json')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:code=process.wait(timeout=max(.1,120-(time.monotonic()-started)))
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();raise TimeoutError('Generación excedió 120 segundos')
        if code:raise RuntimeError((out/'logs/export.log').read_text()[-2000:])
        exports=json.loads((out/'exports.json').read_text());checks={}
        for name,item in exports['variants'].items():
            report=validate_glb(out/name/'tree.glb',{'parameters':{'height_m':item['metrics']['height_m']}},triangle_limit=6999)
            checks[name+'-export']=report['triangles']==item['metrics']['triangles'] and set(report['materials'])=={'Painted_Bark'}
        metrics=architecture_metrics(s)
        if 'branching_budget' in s:
            budget=s['branching_budget'];actual=exports['variants']['bare']['metrics']['triangles']
            checks['extra-geometry-budget']=actual-budget['base_triangles']==budget['extra_triangles']<=700
            checks['analytic-wood-bound']=actual<=bound(preset)
        checks['nominal-height']=bool(validate_glb(out/'bare/tree.glb',{'parameters':{'height_m':preset['height_m']}},triangle_limit=6999))
        checks['wood-plus-reserve-budget']=exports['variants']['bare']['metrics']['triangles']+1584<=6999
        checks['joins-embedded']=json.loads((out/'joins-audit.json').read_text())['passed']
        checks['centerlines-connected']=metrics['maximum_centerline_join_error_m']<1e-7
        checks['smooth-ring-radii']=metrics['maximum_ring_radius_ratio']<=1.550001
        checks['four-orders']=set(b['order'] for b in s['branches'])=={0,1,2,3,4}
        manifest.update(status='completed' if all(checks.values()) else 'failed',checks=checks,architecture=metrics,variants=exports['variants'],
            duration_seconds=time.monotonic()-started,finished_at=timestamp(),blender=exports['blender'],blender_build=exports['build'])
        write_json(out/'manifest.json',manifest)
        if not all(checks.values()):raise ValueError('Auditoría fallida: '+str(checks))
        return {'status':'completed','version':preset['version'],'output':str(out),'seed':seed,'stage':preset['stage'],'triangles':exports['variants']['bare']['metrics']['triangles']}
    except Exception as exc:
        manifest.update(status='failed',error={'type':type(exc).__name__,'message':str(exc)},duration_seconds=time.monotonic()-started)
        write_json(out/'manifest.json',manifest);raise
