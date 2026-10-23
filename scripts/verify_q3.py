#!/usr/bin/env python3
"""Aceptación Q3: formas, jerarquía, cantidad por rama y madera final Q2 intacta."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
from treegen.contracts import load_spec, SCHEMA
from treegen.runner import BLENDER, batch, execute, write_json
from treegen.evaluation import validate_result
from treegen.quality import validate_q1
from generate_f1 import generate

FOCUS=['viejo-00','viejo-03','viejo-09','adulto-00','joven-00']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/q3/acceptance')
    parser.add_argument('--base',type=Path,default=ROOT/'artifacts/q2/acceptance/lote')
    parser.add_argument('--visual',action='store_true')
    args=parser.parse_args()
    output,base=args.output.resolve(),args.base.resolve()
    output.mkdir(parents=True,exist_ok=False)
    blender=os.environ.get('BLENDER_BIN',BLENDER)
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))

    def run(label,command):
        with (output/f'{label}.log').open('w') as log:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
        if result.returncode:
            raise RuntimeError(label+': '+(output/f'{label}.log').read_text()[-5000:])
        print(label+': OK',flush=True)

    def command(script,*arguments):
        return [blender,'--background','--factory-startup','--threads','1','--python-exit-code','1',
                '--python',str(ROOT/script),'--',*arguments]

    run('unit-tests',[sys.executable,'-m','unittest','discover','-s','tests','-v'])
    cases=json.loads((ROOT/'presets/q3-cases.json').read_text())
    for c in cases:
        validate_result(base/c['id'])
        before=json.loads((base/c['id']/'manifest.json').read_text())
        assert before['spec']['algorithm_version']=='0.3.0'
        assert before['spec']['seed']==c['spec']['seed'] and before['spec']['parameters']==c['spec']['parameters']
    report=batch(ROOT/'presets/q3-cases.json',output/'lote')
    assert report['status']=='completed'
    reference=json.loads((base/'viejo-09/manifest.json').read_text())
    legacy=execute(reference['spec'],output/'q2-repeat',render=False)
    assert legacy['metrics']['geometry_sha256']==reference['metrics']['geometry_sha256']
    for path in ('blender/oak_nodes.py','blender/oak_nodes_v2.py','blender/oak_nodes_v21.py','blender/oak_nodes_v3.py'):
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==reference['sources_sha256'][path]
    reference=json.loads((output/'lote/viejo-09/manifest.json').read_text())
    repeated=execute(reference['spec'],output/'repeat',render=False)
    assert repeated['metrics']['geometry_sha256']==reference['metrics']['geometry_sha256']
    assert repeated['crown_checks']==reference['crown_checks'] and repeated['foliage_checks']==reference['foliage_checks']
    effects=generate(ROOT/'presets/v0.4.0/adulto.json',output/'parameter-effects',render=False,check_parameters=True)
    seed=generate(ROOT/'presets/v0.4.0/adulto.json',output/'foliage-seed',render=False,foliage_seed=12345)
    assert effects['crown_checks']['wood_geometry_sha256']==seed['crown_checks']['wood_geometry_sha256']
    assert effects['metrics']['geometry_sha256']!=seed['metrics']['geometry_sha256']
    independence={'seed':True}
    for label,changes in [('density-zero',{'foliage_density':0}),('density-full',{'foliage_density':1}),('scale',{'foliage_scale_m':2.2})]:
        spec=load_spec(ROOT/'presets/v0.4.0/adulto.json');spec['parameters'].update(changes)
        changed=execute(spec,output/f'foliage-{label}',render=False)
        assert changed['normalization']==effects['normalization']
        assert changed['crown_checks']['wood_geometry_sha256']==effects['crown_checks']['wood_geometry_sha256']
        independence[label]=True
    edges={}
    for label in ('minimum','maximum','thin-many','bare-depth1','one-primary-depth2','short-big-crown'):
        spec=load_spec(ROOT/'presets/v0.4.0/adulto.json')
        if label in ('minimum','maximum'):
            spec['parameters']={k:r[label] for k,r in SCHEMA['properties']['parameters']['properties'].items()}
        elif label=='thin-many':
            spec['parameters'].update(height_m=2,base_radius_m=.05,primary_branches=12,branch_length_ratio=.1,foliage_density=0)
        elif label=='bare-depth1':
            spec['parameters'].update(max_depth=1,foliage_density=0)
        elif label=='one-primary-depth2':
            spec['parameters'].update(primary_branches=1,max_depth=2)
        else:
            spec['parameters'].update(height_m=2,foliage_scale_m=3,foliage_density=1)
        m=execute(spec,output/label,render=False)
        edges[label]={'metrics':m['metrics'],'crown_checks':m['crown_checks'],'foliage_checks':m['foliage_checks']}
        bounds=m['crown_checks']['leaf_bounds_blender']
        if bounds:assert bounds[0][2]>=-1e-5 and bounds[1][2]<=spec['parameters']['height_m']+1e-5
    print('base Q2, repetición Q3, diez parámetros, independencia y seis extremos: OK',flush=True)
    run('diagnosis',command('scripts/diagnose_structure.py','--batch',str(output/'lote'),'--output',str(output/'diagnosis'),'--cases',*[c['id'] for c in cases]))
    measures={c['id']:validate_q1(c) for c in json.loads((output/'diagnosis/diagnosis.json').read_text())['cases']}
    run('diagnosis-edges',command('scripts/diagnose_structure.py','--batch',str(output),'--output',str(output/'diagnosis-edges'),'--cases',*edges))
    edge_measures={c['id']:validate_q1(c) for c in json.loads((output/'diagnosis-edges/diagnosis.json').read_text())['cases']}
    run('inspection',command('blender/inspect_q3.py','--base',str(base),'--candidate',str(output/'lote'),
        '--output',str(output/'inspection'),'--cases',*[c['id'] for c in cases]))
    inspection=json.loads((output/'inspection/report.json').read_text())
    for name,values in inspection['cases'].items():
        after,before=values['candidate'],values['base']
        assert after['mass_bbox_diagonal']['coefficient_of_variation']>before['mass_bbox_diagonal']['coefficient_of_variation']
        assert after['leaf_mass_count']<before['leaf_mass_count']
        if not name.startswith('joven'):
            assert set(values['foliage_checks']['counts_by_role'])=={'dominant','medium','small'}
            assert min(values['foliage_checks']['counts_by_role'].values())>0
    run('comparison',command('blender/render_comparison.py','--base',str(base),'--candidate',str(output/'lote'),
        '--output',str(output/'comparison'),'--cases',*FOCUS))
    run('shapes',command('blender/render_q3_shapes.py','--asset',str(output/'lote/viejo-09'),'--output',str(output/'shapes')))
    godot=[sys.executable,str(ROOT/'scripts/verify_f2.py'),'--batch',str(output/'lote'),'--output',str(output/'godot'),'--asset-dir','q3']
    if args.visual:godot.append('--visual')
    run('godot',godot)
    write_json(output/'summary.json',{'stage':'Q3','algorithm_version':'0.4.0','technical_passed':True,'user_visual_acceptance':'pending',
        'base_version':'0.3.0','same_final_wood':True,'same_parameters_and_seeds':True,'base_reproduced':True,'repeated_geometry':True,
        'foliage_changes_preserve_wood':independence,'parameter_effects':effects['parameter_effect_checks'],'edges':edges,'edge_structure':edge_measures,
        'cases':measures,'inspection':inspection,'batch':report,'godot':json.loads((output/'godot/summary.json').read_text())['godot'],
        'visual_captures_generated':args.visual,
        'shared_cameras':{c:json.loads((output/'comparison'/c/'cameras.json').read_text())['same_cameras'] for c in FOCUS}})
    print('Q3: verificación técnica completada; apariencia pendiente del usuario.',flush=True)


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,AssertionError,RuntimeError,subprocess.TimeoutExpired) as exc:
        print('Q3 FALLÓ: '+str(exc),file=sys.stderr);sys.exit(1)
