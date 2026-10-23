"""Mide copa abierta, relación radio/follaje y visibilidad desde abajo en archivos guardados."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'blender'))
sys.path.insert(0,str(ROOT/'scripts'))
from inspect_q2 import read
from inspect_q3 import wrapper, shapes
from generate_oak import foliage_report
from diagnose_structure import curves


def correlation(xs,ys):
    mx,my=sum(xs)/len(xs),sum(ys)/len(ys)
    dx,dy=[x-mx for x in xs],[y-my for y in ys]
    denominator=math.sqrt(sum(x*x for x in dx)*sum(y*y for y in dy))
    return sum(x*y for x,y in zip(dx,dy))/denominator if denominator else None


def group_measurements(mesh,height):
    """Caja y volumen cerrado por grupo; el volumen sumado cuenta solapamientos."""
    mesh.calc_loop_triangles()
    groups=defaultdict(list)
    for t in mesh.loop_triangles:
        if mesh.materials[t.material_index].name!='Oak_Leaves':continue
        k=t.vertices[0]
        level=mesh.attributes['q3_level'].data[k].value
        branch=mesh.attributes['q3_branch'].data[k].value
        owner=branch-100 if level==1 else (branch-200)//3 if level==2 else -1
        if owner>=0:groups[owner].append(t)
    values=[]
    for owner,triangles in sorted(groups.items()):
        ids={v for t in triangles for v in t.vertices}
        origin=mesh.vertices[next(iter(ids))].co
        volume=abs(sum((mesh.vertices[t.vertices[0]].co-origin).dot(
            (mesh.vertices[t.vertices[1]].co-origin).cross(mesh.vertices[t.vertices[2]].co-origin))/6 for t in triangles))
        values.append({'primary_index':owner,'top_m':max(mesh.vertices[k].co.z for k in ids),
                       'bottom_m':min(mesh.vertices[k].co.z for k in ids),'summed_mass_volume_m3':volume})
    tops=[r['top_m'] for r in values]
    mean=sum(tops)/len(tops) if tops else 0
    return {'primary_subtrees':values,'top_range_over_height':(max(tops)-min(tops))/height if tops else 0,
        'top_std_over_height':math.sqrt(sum((z-mean)**2 for z in tops)/len(tops))/height if tops else 0}


def visibility(mesh,framing,height,direction,resolution=128):
    """Rayos ortográficos sobre malla final: primer material visible, sin iluminación."""
    mesh.calc_loop_triangles()
    triangles=[tuple(t.vertices) for t in mesh.loop_triangles]
    materials=[mesh.materials[t.material_index].name for t in mesh.loop_triangles]
    bvh=BVHTree.FromPolygons([v.co for v in mesh.vertices],triangles,all_triangles=True)
    direction=Vector(direction).normalized();forward=-direction
    right=forward.cross(Vector((0,0,1))).normalized();up=right.cross(forward).normalized()
    span=framing['span'];center=Vector(framing['center'])
    counts={'crown_wood_pixels':0,'leaf_pixels':0,'internal_empty_pixels':0,'envelope_pixels':0}
    for row in range(resolution):
        occupied=[];has_leaf=False
        y=((row+.5)/resolution-.5)*span*1.3
        for col in range(resolution):
            x=((col+.5)/resolution-.5)*span*1.3
            origin=center+right*x+up*y+direction*(span*2.5)
            hit,normal,index,distance=bvh.ray_cast(origin,forward,span*5)
            if index is None:continue
            occupied.append(col)
            if materials[index]=='Oak_Leaves':
                counts['leaf_pixels']+=1;has_leaf=True
            elif hit.z>=.33*height:counts['crown_wood_pixels']+=1
        if has_leaf and occupied:
            width=max(occupied)-min(occupied)+1
            counts['envelope_pixels']+=width
            counts['internal_empty_pixels']+=width-len(occupied)
    counts['internal_empty_fraction']=counts['internal_empty_pixels']/max(1,counts['envelope_pixels'])
    counts['resolution']=resolution
    return counts


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ('base','candidate','output'):parser.add_argument('--'+arg,type=Path,required=True)
    parser.add_argument('--cases',nargs='+',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True,exist_ok=False)
    reports={}
    for name in args.cases:
        base,before=read(args.base/name)
        candidate,after=read(args.candidate/name)
        assert base['spec']['parameters']==candidate['spec']['parameters'] and base['seeds']==candidate['seeds']
        assert base['structure_checks']==candidate['structure_checks'] and base['normalization']==candidate['normalization']
        assert before['wood_geometry_sha256']==after['wood_geometry_sha256']
        assert after==candidate['crown_checks']
        height=candidate['spec']['parameters']['height_m']
        bounds=after['leaf_bounds_blender']
        if bounds:assert bounds[0][2]>=-1e-5 and bounds[1][2]<=height+1e-5
        graph=wrapper(next(g for g in bpy.data.node_groups if g.name.startswith('Oak_Generator_v')))
        checks=foliage_report(graph,candidate['socket_values'],candidate['spec']['parameters'],after)
        assert checks==candidate['foliage_checks']
        structure=next(g for g in bpy.data.node_groups if g.name.startswith('Oak_Structure_v'))
        native=curves(structure,candidate['socket_values'],'Primary')
        radii=sorted(r[0] for coords,r in native)
        primary=sorted((b for b in checks['branches'] if b['level']==1),key=lambda b:b['radius_m'])
        assert all(abs(a-b['radius_m'])<1e-6 for a,b in zip(radii,primary)) and len(radii)==len(primary)
        raw_secondary=candidate['structure_checks']['secondary_branches']
        foliated_secondary=sum(b['level']==2 for b in checks['branches'])
        assert foliated_secondary==raw_secondary*2//3
        geometry_bounds=[base['metrics']['bounds_blender'],candidate['metrics']['bounds_blender']]
        low=[min(b[0][k] for b in geometry_bounds) for k in range(3)]
        high=[max(b[1][k] for b in geometry_bounds) for k in range(3)]
        framing={'center':[(a+b)/2 for a,b in zip(low,high)],'span':max(b-a for a,b in zip(low,high))}
        view_directions={'front':(0,-1,0),'below':(1.3,-1.8,-.65),'below-front':(0,-1,-.55)}
        measures={}
        for label,folder in [('candidate',args.candidate/name),('base',args.base/name)]:
            m,c=read(folder);mesh=bpy.data.objects['Oak'].data
            measures[label]=group_measurements(mesh,height)
            measures[label]['visibility']={v:visibility(mesh,framing,height,d) for v,d in view_directions.items()}
            if label=='candidate':
                subtree={r['primary_index']:r for r in measures[label]['primary_subtrees']}
                relation=correlation([b['radius_m'] for b in primary],
                    [subtree[b['branch']-100]['summed_mass_volume_m3'] for b in primary])
                measures[label]['radius_volume_correlation']=relation
                if len(primary)>=4:assert relation>.60,relation
                measures[label]['bare_secondary_branches']=raw_secondary-foliated_secondary
                prototypes=shapes(candidate['seeds']['foliage'])
        reports[name]={'same_final_wood':True,'same_normalization':True,'same_native_structure':True,
            'same_parameters_and_seeds':True,'base':before,'candidate':after,'foliage_checks':checks,
            'distribution':measures,'prototypes':prototypes,'shared_framing':framing,
            'base_manifest_sha256':hashlib.sha256((args.base/name/'manifest.json').read_bytes()).hexdigest(),
            'candidate_manifest_sha256':hashlib.sha256((args.candidate/name/'manifest.json').read_bytes()).hexdigest()}
        print(name+': madera idéntica, radios reales y distribución inspeccionados',flush=True)
    (args.output/'report.json').write_text(json.dumps({'blender':bpy.app.version_string,'cases':reports},indent=2)+'\n')


if __name__=='__main__':main()
