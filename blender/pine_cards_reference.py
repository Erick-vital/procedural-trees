"""Referencia de evaluación: topología 2.2.0 con solo el estrechamiento nuevo."""
import json
import math
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.pine_painted import build
from treegen.pine import sub,unit
from generate_oak import mesh_report
from pine_painted_sample import create,painted,bark_uv

study=Path(sys.argv[sys.argv.index('--')+1])
for name in ('pilot','control-01','control-02','control-03'):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    r=json.loads((study/('before-'+name)/'manifest.json').read_text())['resolved_blueprint']
    _,wood,groups=build(r)
    for g in groups:
        a,b,c=[g['vertices'][i] for i in (0,1,2)]
        transverse=[(b[k]-a[k])/.09 for k in range(3)]
        axis=unit([(c[k]-a[k]+.110*transverse[k])/.18 for k in range(3)])
        origin=g['origin_m'];vertices=[]
        for v in g['vertices']:
            delta=sub(v,origin);along=sum(delta[k]*axis[k] for k in range(3))
            vertices.append([origin[k]+along*axis[k]+math.sqrt(.9)*(delta[k]-along*axis[k]) for k in range(3)])
        g['vertices']=vertices
    bark=painted('Painted_Bark','bark.png');leaf=painted('Painted_Foliage','foliage.png',True)
    pieces=[(b['mesh'],0,b.get('uv') or bark_uv(b)) for b in wood]+[(g,1,g['uv']) for g in groups]
    obj=create('PaintedPine',pieces,[bark,leaf])
    (study/('topology-'+name+'-metrics.json')).write_text(json.dumps(mesh_report(obj.data,triangle_limit=12500)))
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(study/'godot'/('topology-'+name+'.glb')),export_format='GLB',use_selection=True,export_yup=True)
