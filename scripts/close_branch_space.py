#!/usr/bin/env python3
"""Auditoría F5 de ejes finales simplificados, repetición y regresiones históricas."""
import argparse
from dataclasses import replace
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.branch_structure import Branch, BranchStructure, validate_structure, length, sub
from treegen.branch_space import measure
from treegen.oak_wood import optimize
from treegen.runner import execute_blueprint, BLENDER
from treegen.evaluation import validate_result
from verify_branch_space import run, summary
from review_pine_painted import read,write,sha


def exported_axes(folder):
    manifest=read(folder/'manifest.json');ref=read(folder/'base-reference.json')
    doc=manifest['f5']['structure'];branches=[];maximum_error=0.
    scale=ref['normalization']['scale'][2];shift=ref['normalization']['translation'][2]
    original={b['id']:b for b in ref['branches']}
    optimizations={b['id']:b for b in manifest['wood_optimization']}
    for b in doc['branches']:
        before=original[b['id']];opt=optimizations[b['id']]
        indices=opt['retained_rings']
        # Derivar ejes de las caras de madera realmente usadas por el procesador.
        vertices=before['mesh']['vertices']
        points=[]
        for i in indices:
            ring=vertices[8*i:8*(i+1)]
            center=tuple(sum(v[k] for v in ring)/8 for k in range(3))
            expected=b['points'][i];expected=(expected[0],expected[1],expected[2]*scale+shift)
            maximum_error=max(maximum_error,length(sub(center,expected)))
            points.append(tuple(b['points'][i]))
        branches.append(Branch(b['id'],b['parent_id'],b['level'],tuple(points),tuple(b['radii'][i] for i in indices)))
        if b['level']==2:
            actual=optimize(before,.02)
            assert actual['optimization']['retained_rings']==indices
    assert maximum_error<1e-5,maximum_error
    structure=BranchStructure(doc['version'],doc['seed'],tuple(branches));validate_structure(structure)
    return {'metric':measure(structure,scale),'axis_to_exported_ring_max_error_m':maximum_error,
            'simplification_max_correspondence_error_m':max(o['max_correspondence_error_m'] for o in optimizations.values()),
            'export_validation':validate_result(folder)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True,type=Path)
    a=p.parse_args();out=a.study.resolve();folder=out/'closure';folder.mkdir()
    (folder/'logs').mkdir();env=dict(os.environ)
    report=read(out/'verification.json')
    closure={'sources_sha256':{str(Path(__file__).relative_to(ROOT)):sha(__file__)},'checks':{},'cases':[],
             'repeats':{},'regressions':{},'transition':{}}
    for row in report['cases']:
        item={'id':row['id'],'partition':row['partition'],'status':row['status']}
        if row['status']=='completed':
            for variant in ('baseline','candidate'):
                audit=exported_axes(out/variant/row['id'])
                item[variant]={'f5':{'final_metric':audit['metric']},'axis_audit':{k:v for k,v in audit.items() if k!='export_validation'}}
            b,c=[read(out/v/row['id']/'structure.json')['structure']['branches'] for v in ('baseline','candidate')]
            closure['checks'][row['id']+'-structure-invariants']=len(b)==len(c) and all(
                all(x[k]==y[k] for k in ('id','parent_id','level','radii')) and x['points'][0]==y['points'][0] and
                [p[2] for p in x['points']]==[p[2] for p in y['points']] and
                (x==y if x['level']<2 else True) for x,y in zip(b,c))
            closure['checks'][row['id']+'-budget']=all(row[v]['metrics']['triangles']<7000 and len(row[v]['metrics']['triangles_by_material'])==2 for v in ('baseline','candidate'))
        closure['cases'].append(item)
    closure['summary']=summary(closure['cases']);write(folder/'verification.json',closure)
    # Repetir ambos miembros por edad desde entradas congeladas, sin modelo.
    for name in ('joven-00','adulto-00','viejo-00'):
        closure['repeats'][name]={}
        for variant in ('baseline','candidate'):
            destination=folder/'repeat'/variant/name;destination.mkdir(parents=True)
            job=read(out/variant/name/'input.json');job['output']=str(destination)
            write(destination/'input.json',job)
            run([BLENDER,'--background','--factory-startup','--threads','1','--python-exit-code','1',
                 '--python',ROOT/'blender/f5_structure.py','--',destination/'input.json'],
                folder/'logs'/f'{name}-{variant}.log',env,timeout=120)
            manifest=read(destination/'manifest.json');manifest['required_views']=[];write(destination/'manifest.json',manifest)
            validate_result(destination)
            same=sha(destination/'tree.glb')==sha(out/variant/name/'tree.glb')
            closure['repeats'][name][variant]=same
            closure['checks'][name+'-'+variant+'-repeat']=same
        write(folder/'verification.json',closure)
    # Referencias históricas: identidad exacta del GLB, no de fuentes cambiadas.
    matrix=read(ROOT/'configs/verification/oak-wood-v1.json')
    for case in matrix['cases']:
        name=case['id']
        if name=='pilot':continue
        manifest=execute_blueprint(ROOT/matrix['blueprint'],case['instance'],folder/'historical'/name,render=False)
        reference=ROOT/'artifacts/roble-pintado/integracion-madera-01'/name/'tree.glb'
        same=manifest['glb_sha256']==sha(reference)
        closure['regressions'][name]={'glb_identical':same,'reference':str(reference),'sha256':sha(reference)}
        closure['checks'][name+'-historical-regression']=same
        baseline=read(out/'baseline'/name/'manifest.json')
        closure['transition'][name]={'historical_triangles':manifest['metrics']['triangles'],
            'python_triangles':baseline['metrics']['triangles'],
            'geometry_identical':manifest['metrics']['geometry_sha256']==baseline['metrics']['geometry_sha256'],
            'same_processor_recipe':manifest['resolved_blueprint']==baseline['resolved_blueprint'],
            'historical_glb_sha256':manifest['glb_sha256'],'python_glb_sha256':baseline['glb_sha256']}
        write(folder/'verification.json',closure)
    closure['technical_checks_passed']=all(closure['checks'].values()) and all(r['status']=='completed' for r in closure['cases'])
    write(folder/'verification.json',closure)
    print(closure['summary'],flush=True)


if __name__=='__main__':main()
