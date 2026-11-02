"""T4: auditar normales importadas con Blender y exportar prueba glTF estándar."""
import json
import math
from pathlib import Path
import sys
import bpy


def key(position,uv):return tuple(round(x*10000) for x in list(position)+list(uv))

def main(config_path):
    config=json.loads(config_path.read_text());reports=[]
    for item in config['cases']:
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        for collection in (bpy.data.meshes,bpy.data.materials,bpy.data.images):
            for block in list(collection):
                if block.users==0:collection.remove(block)
        bpy.ops.import_scene.gltf(filepath=item['glb'])
        bpy.context.view_layer.update()
        expected={}
        for row in json.loads(Path(item['expected']).read_text()):expected.setdefault(key(row['position'],row['uv']),[]).append(row)
        error=0.0;angle_error=0.0;corners=0;triangles=0;groups=set()
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH':continue
            mesh=obj.data;mesh.calc_loop_triangles();triangles+=len(mesh.loop_triangles)
            transform=obj.matrix_world.to_3x3().inverted().transposed()
            for face in mesh.polygons:
                if obj.material_slots[face.material_index].material.name.split('.')[0]!='Painted_Foliage':continue
                for index in face.loop_indices:
                    loop=mesh.loops[index];v=obj.matrix_world@mesh.vertices[loop.vertex_index].co
                    uv=mesh.uv_layers[0].data[index].uv
                    candidates=expected.get(key([v.x,v.z,-v.y],[uv.x,1-uv.y]),[])
                    if not candidates:raise ValueError('Esquina sin correspondencia')
                    n=(transform@mesh.corner_normals[index].vector).normalized()
                    actual=[n.x,n.z,-n.y]
                    delta=min(max(abs(x-y) for x,y in zip(actual,r['normal'])) for r in candidates)
                    angle=min(math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(actual,r['normal']))/math.sqrt(sum(x*x for x in r['normal'])))))) for r in candidates)
                    # La importación/reexportación no se declara exacta: cota angular explícita.
                    if delta>.01 or angle>.6:raise ValueError('Desviación de normal excede .6 grados')
                    angle_error=max(angle_error,angle)
                    error=max(error,delta);corners+=1;groups.update(r['group_id'] for r in candidates)
        if triangles!=item['triangles'] or len(groups)!=item['groups'] or triangles>=7000:raise ValueError('Conteos importados incorrectos')
        bpy.ops.export_scene.gltf(filepath=item['roundtrip'],export_format='GLB',export_normals=True,export_texcoords=True)
        reports.append({'id':item['id'],'triangles':triangles,'groups':len(groups),'corners':corners,'max_normal_error':error,'max_normal_angle_error_deg':angle_error,'normal_angle_limit_deg':.6,'roundtrip':item['roundtrip']})
    Path(config['report']).write_text(json.dumps({'passed':True,'blender':bpy.app.version_string,'cases':reports},indent=2)+'\n')

if __name__=='__main__':main(Path(sys.argv[sys.argv.index('--')+1]))
