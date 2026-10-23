"""Inspección Q3: madera final idéntica a Q2 y formas no equivalentes a transformaciones afines."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import bpy
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'blender'))
from inspect_q2 import read
from generate_oak import evaluated_output, foliage_report


def wrapper(tree):
    return SimpleNamespace(tree=tree,sockets={s.name:s.identifier for s in tree.interface.items_tree
        if s.item_type=='SOCKET' and s.in_out=='INPUT'})


def shapes(seed):
    result=[]
    for family in range(6):
        group=next(g for g in bpy.data.node_groups if g.name.startswith(f'Oak_FoliageShape_{family}_v0.4.0'))
        meshes=[evaluated_output(wrapper(group),{'Foliage Seed':seed},channel) for channel in ('Raw Geometry','Geometry')]
        raw,mesh=meshes
        p=[v.co.copy() for v in raw.vertices];q=[v.co.copy() for v in mesh.vertices]
        assert len(p)==len(q)
        mp=sum(p,Vector())/len(p);mq=sum(q,Vector())/len(q)
        covariance=Matrix([[sum((v[i]-mp[i])*(v[j]-mp[j]) for v in p) for j in range(3)] for i in range(3)])
        cross=Matrix([[sum((b[i]-mq[i])*(a[j]-mp[j]) for a,b in zip(p,q)) for j in range(3)] for i in range(3)])
        affine=cross@covariance.inverted()
        error=math.sqrt(sum((b-mq-affine@(a-mp)).length_squared for a,b in zip(p,q))/len(p))
        mesh.calc_loop_triangles()
        assert len(mesh.loop_triangles)==(80 if family<4 else 20)
        assert all(t.area>1e-10 for t in mesh.loop_triangles)
        assert error>.005, 'La forma se reduce a una transformación afín'
        coords=sorted(tuple(round(c,6) for c in v.co) for v in mesh.vertices)
        faces=sorted(sorted(tuple(round(c,6) for c in mesh.vertices[i].co) for i in t.vertices) for t in mesh.loop_triangles)
        result.append({'family':family,'vertices':len(q),'triangles':len(mesh.loop_triangles),
                       'non_affine_rms_unit':error,'geometry_sha256':hashlib.sha256(json.dumps([coords,faces]).encode()).hexdigest()})
        for m in meshes:bpy.data.meshes.remove(m)
    assert len({r['geometry_sha256'] for r in result})==6
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cases',nargs='+',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True,exist_ok=False)
    reports={}
    for name in args.cases:
        base,before=read(args.base/name)
        candidate,after=read(args.candidate/name)
        assert base['spec']['parameters']==candidate['spec']['parameters']
        assert base['seeds']==candidate['seeds']
        assert base['structure_checks']==candidate['structure_checks']
        assert base['normalization']==candidate['normalization']
        assert before['wood_geometry_sha256']==after['wood_geometry_sha256'],'Cambió la madera final Q2'
        assert after==candidate['crown_checks']
        height=candidate['spec']['parameters']['height_m']
        bounds=after['leaf_bounds_blender']
        if bounds:assert bounds[0][2]>=-1e-5 and bounds[1][2]<=height+1e-5
        generator=next(g for g in bpy.data.node_groups if g.name.startswith('Oak_Generator_v'))
        graph=wrapper(generator)
        checks=foliage_report(graph,candidate['socket_values'],candidate['spec']['parameters'],after)
        assert checks==candidate['foliage_checks']
        coords={}
        for channel in ('Anchors','Centers'):
            mesh=evaluated_output(graph,candidate['socket_values'],channel)
            coords[channel]=[tuple(v.co) for v in mesh.vertices]
            bpy.data.meshes.remove(mesh)
        assert len(coords['Anchors'])==len(coords['Centers'])==after['leaf_mass_count']
        distance=max((math.dist(a,b) for a,b in zip(coords['Anchors'],coords['Centers'])),default=0)
        effective=min(candidate['spec']['parameters']['foliage_scale_m'],.24*height)
        assert distance<=2*effective+1e-4
        reports[name]={'same_final_wood':True,'same_normalization':True,'same_native_structure':True,
            'same_parameters_and_seeds':True,'base':before,'candidate':after,'foliage_checks':checks,
            'max_anchor_center_distance_m':distance,'prototypes':shapes(candidate['seeds']['foliage']),
            'base_manifest_sha256':hashlib.sha256((args.base/name/'manifest.json').read_bytes()).hexdigest(),
            'candidate_manifest_sha256':hashlib.sha256((args.candidate/name/'manifest.json').read_bytes()).hexdigest()}
        print(name+': madera final idéntica; seis formas no afines y jerarquía verificadas',flush=True)
    (args.output/'report.json').write_text(json.dumps({'blender':bpy.app.version_string,'cases':reports},indent=2)+'\n')


if __name__=='__main__':main()
