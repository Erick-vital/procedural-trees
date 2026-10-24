#!/usr/bin/env python3
"""B5: cierre CLI, entradas congeladas y selección Q3 desde una copia limpia."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from treegen.blueprints import load_blueprint
from treegen.evaluation import validate_result


def read(path):
    return json.loads(path.read_text())


def write(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);(out/'logs').mkdir()
    report={'phase':'B5','passed':False,'checks':{},'jobs':{},'visual_validation':'Reutiliza B3/B4; sin capturas nuevas en B5.'}
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))

    def run(name,command,*,cwd=ROOT,environment=None,as_json=False,timeout=180):
        with (out/'logs'/(name+'.log')).open('w') as log:
            p=subprocess.Popen(list(map(str,command)),cwd=cwd,env=environment or env,stdout=log,
                stderr=subprocess.STDOUT,start_new_session=True)
            try:code=p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGKILL);p.wait();raise TimeoutError(name)
        content=(out/'logs'/(name+'.log')).read_text()
        if code:raise RuntimeError(name+': '+content[-1800:])
        print(name+': OK',flush=True)
        return json.loads(content) if as_json else content

    try:
        log=run('tests',[sys.executable,'-m','unittest','discover','-s','tests','-v'])
        report['unit_tests']=int(re.search(r'Ran (\d+) tests',log).group(1))
        isolated=out/'isolated-source';isolated.mkdir()
        for folder in ('src','blender','schemas','configs','blueprints','presets'):
            shutil.copytree(ROOT/folder,isolated/folder,
                ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.blend','*.glb'))
        assert not (isolated/'docs').exists() and not (isolated/'artifacts').exists()
        checks=report['checks'];checks['clean_source_has_no_prior_results_or_evidence']=True
        isolated_env=dict(env,PYTHONPATH=str(isolated/'src'))

        def cli(name,*arguments):
            return run(name,[sys.executable,'-m','treegen',*arguments],cwd=isolated,
                environment=isolated_env,as_json=True,timeout=150)

        catalog=cli('catalog','blueprints');report['catalog']=catalog
        identities={(r['id'],r['version']) for r in catalog['blueprints']}
        checks['catalog_exact_versions']=identities=={('roble_copa_ancha','1.0.0'),('roble_copa_ancha','1.1.0'),('roble_copa_ancha','1.2.0'),('arbol_copa_columnar','1.0.0')}
        for age in ('joven','adulto','viejo'):
            current=read(isolated/'presets'/(age+'.json'))
            checks[age+'-alias-is-q3']=current==read(isolated/'presets/v0.4.0'/(age+'.json')) and current['algorithm_version']=='0.4.0'
            checks[age+'-q3b-still-explicit']=read(isolated/'presets/v0.4.1'/(age+'.json'))['algorithm_version']=='0.4.1'
        requests={
            'roble-a':('blueprints/roble_copa_ancha/1.0.0.json','presets/blueprints/roble-copa-ancha-viejo-09.json'),
            'roble-b':('blueprints/roble_copa_ancha/1.0.0.json','presets/blueprints/roble-copa-ancha-viejo-09.json'),
            'columna-a':('blueprints/arbol_copa_columnar/1.0.0.json','presets/blueprints/columnar/pilot.json'),
            'columna-b':('blueprints/arbol_copa_columnar/1.0.0.json','presets/blueprints/columnar/pilot.json')}

        def record(name,result):
            validate_result(out/name)
            report['jobs'][name]={k:result[k] for k in ('kind','spec','glb_sha256','metrics','duration_seconds','sources_sha256')} if 'kind' in result else {k:result[k] for k in ('spec','glb_sha256','metrics','duration_seconds','sources_sha256')}
            write(out/'verification.json',report)

        for name,(recipe,instance) in requests.items():
            m=cli(name,'generate-blueprint',recipe,'--instance',instance,'--output',out/name,'--no-render')
            record(name,m)
            cli('validate-'+name,'validate',out/name)
        # Ejecutar el bloque de extracción documentado, con destinos de este ensayo.
        guide=(ROOT/'docs/uso-blueprints.md').read_text()
        snippet=re.search(r"python3 - <<'PYREPEAT'\n(.*?)\nPYREPEAT",guide,re.S).group(1)
        snippet=snippet.replace('artifacts/blueprints/roble-a/manifest.json',str(out/'roble-a/manifest.json'))
        snippet=snippet.replace('artifacts/blueprints/entradas-congeladas',str(out/'frozen-inputs'))
        run('extract-documented-inputs',[sys.executable,'-c',snippet],cwd=isolated,environment=isolated_env)
        frozen=load_blueprint(out/'frozen-inputs/recipe.json')
        stored=read(out/'roble-a/manifest.json')['resolved_blueprint']
        checks['documented-frozen-inputs-exact']=frozen==stored['blueprint_definition'] and read(out/'frozen-inputs/instance.json')==stored['instance_request']
        m=cli('roble-congelado','generate-blueprint',out/'frozen-inputs/recipe.json','--instance',out/'frozen-inputs/instance.json','--output',out/'roble-congelado','--no-render')
        record('roble-congelado',m);cli('validate-roble-congelado','validate',out/'roble-congelado')
        for name,spec in (('q3-alias','presets/adulto.json'),('q3-explicit','presets/v0.4.0/adulto.json')):
            m=cli(name,'generate',spec,'--output',out/name,'--no-render');record(name,m)
            cli('validate-'+name,'validate',out/name)
        report['comparisons']={}
        for label,left,right in (('roble','roble-a','roble-b'),('columnar','columna-a','columna-b'),('frozen','roble-a','roble-congelado'),('q3-default','q3-alias','q3-explicit')):
            comparison=cli('compare-'+label,'compare',out/left,out/right,'--output',out/('compare-'+label))
            report['comparisons'][label]={k:comparison[k] for k in ('same_spec','same_environment','same_sources','same_cameras','same_geometry','triangle_delta')}
            checks[label+'-comparison-identical']=all(comparison[k] for k in ('same_spec','same_environment','same_sources','same_cameras','same_geometry')) and comparison['triangle_delta']==0
            checks[label+'-glb-byte-identical']=report['jobs'][left]['glb_sha256']==report['jobs'][right]['glb_sha256']
        lock=read(ROOT/'docs/evidence/blueprints/b0/reference-lock.json')
        checks['roble-matches-approved-b0']=report['jobs']['roble-a']['glb_sha256']==lock['files_sha256'][lock['pilot_directory']+'/tree.glb']
        columnar=read(ROOT/'docs/evidence/blueprints/b4/verification.json')['cases']['pilot']['glb_sha256']
        checks['columnar-matches-b4']=report['jobs']['columna-a']['glb_sha256']==columnar
        report['passed']=all(checks.values());report['matrix_executed']=True
    finally:write(out/'verification.json',report)
    print('B5 cierre verificado; passed='+str(report['passed']),flush=True)


if __name__=='__main__':
    main()
