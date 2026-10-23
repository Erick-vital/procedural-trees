"""Comparar primitiva base y seis familias Q3 con cámara/escala común."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'blender'))
from inspect_q3 import wrapper
from generate_oak import evaluated_output,render_views

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--asset',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
args.output.mkdir(parents=True,exist_ok=False)
path=(args.asset/'tree.blend').resolve();digest=hashlib.sha256(path.read_bytes()).hexdigest()
manifest=json.loads((args.asset/'manifest.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
for obj in bpy.data.objects:
    if obj.type=='MESH':obj.hide_render=True
cameras=[]
for label,family,channel in [('base',4,'Raw Geometry')]+[(f'family-{k}',k,'Geometry') for k in range(6)]:
    tree=next(g for g in bpy.data.node_groups if g.name.startswith(f'Oak_FoliageShape_{family}_v0.4.0'))
    mesh=evaluated_output(wrapper(tree),{'Foliage Seed':manifest['seeds']['foliage']},channel)
    mesh.materials.append(bpy.data.materials['Oak_Leaves'])
    obj=bpy.data.objects.new('Shape',mesh);bpy.context.collection.objects.link(obj)
    output=args.output/label;output.mkdir()
    rig=render_views(obj,output,[('shape',(1.3,-1.8,.9))],framing={'center':[0,0,0],'span':3.3})
    cameras.append(rig)
    bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
assert all(r==cameras[0] for r in cameras)
assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
(args.output/'cameras.json').write_text(json.dumps({'cameras':cameras[0],'same_cameras':True,
    'source_blend_sha256':digest,'foliage_seed':manifest['seeds']['foliage']},indent=2)+'\n')
