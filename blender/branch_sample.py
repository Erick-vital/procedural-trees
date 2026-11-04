"""R1: exportar piezas congeladas; las recetas de árbol permanecen intactas."""
import json
from pathlib import Path
import sys
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'blender'),str(ROOT/'src')]
from pine_painted_sample import create
from oak_painted_sample import painted
from oak_crossed_trial import atlas_material
from generate_oak import mesh_report
from foliage_canopy_lab import export_tree
from foliage_lab import write,sha


def main(path):
    job=json.loads(Path(path).read_text());out=Path(job['output'])
    reports={}
    for name,data in job['variants'].items():
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        for mesh in list(bpy.data.meshes):
            if mesh.users==0:bpy.data.meshes.remove(mesh)
        for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
        bark=painted('Painted_Bark','bark.png')
        leaf=atlas_material(ROOT/'assets/roble-pintado/v0.3.0/foliage.png');leaf.name='Painted_Foliage'
        pieces=[]
        for mesh in data['wood']:pieces.append((mesh,0,mesh['uv']))
        for mesh in data['foliage']:pieces.append((mesh,1,mesh['uv']))
        obj=create('BranchSample',pieces,[bark,leaf])
        flags=[flag for mesh,_,_ in pieces for flag in mesh.get('smooth',[False]*len(mesh['polygons']))]
        for polygon,flag in zip(obj.data.polygons,flags):polygon.use_smooth=flag
        # Materiales no usados se eliminan para que el GLB y métricas coincidan.
        if not data['wood']:
            for p in obj.data.polygons:p.material_index=0
            obj.data.materials.clear();obj.data.materials.append(leaf)
        for image in bpy.data.images:
            if image.source=='FILE':image.pack()
        folder=out/name;folder.mkdir()
        metrics=mesh_report(obj.data,triangle_limit=6999)
        export_tree(obj,folder)
        reports[name]={'metrics':metrics,'glb_sha256':sha(folder/'tree.glb'),'blend_sha256':sha(folder/'tree.blend')}
    write(out/'exports.json',{'blender':bpy.app.version_string,'build':bpy.app.build_hash.decode(),'variants':reports})


if __name__=='__main__':main(sys.argv[sys.argv.index('--')+1])
