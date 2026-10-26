"""Reimportar PP4 y referencias: comprobar mallas/materiales/UV en Blender."""
import json
import sys
from pathlib import Path
import bpy
rows=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text());result=[]
for row in rows:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=row['path'])
    objects=[o for o in bpy.context.selected_objects if o.type=='MESH']
    assert len(objects)==1
    mesh=objects[0].data;mesh.calc_loop_triangles()
    assert len(mesh.loop_triangles)==row['triangles']
    if row['painted']:
        assert len(mesh.uv_layers)==1
        assert all(v.uv.x==v.uv.x and v.uv.y==v.uv.y for v in mesh.uv_layers.active.data)
        for m in mesh.materials:
            textures=[n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE']
            assert textures and all(list(im.size)==[1254,1254] for im in textures)
    result.append({'path':row['path'],'triangles':len(mesh.loop_triangles),'materials':len(mesh.materials),'uv_layers':len(mesh.uv_layers)})
Path(sys.argv[sys.argv.index('--')+2]).write_text(json.dumps({'passed':True,'cases':result},indent=2)+'\n')
