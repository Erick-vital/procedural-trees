"""R3: ramas con follaje y madera descubierta explícita; materiales compartidos."""
import json
from pathlib import Path
import sys
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from pine_painted_sample import create
from oak_painted_sample import painted
from oak_crossed_trial import atlas_material
from generate_oak import mesh_report
from foliage_canopy_lab import export_tree
from foliage_lab import write,sha


def main(path):
    job=json.loads(Path(path).read_text());out=Path(job['output']);reports={}
    for name,data in job['variants'].items():
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        for mesh in list(bpy.data.meshes):
            if mesh.users==0:bpy.data.meshes.remove(mesh)
        for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
        bark=painted('Painted_Bark','bark.png');leaf=atlas_material(ROOT/'assets/roble-pintado/v0.3.0/foliage.png');leaf.name='Painted_Foliage'
        mats=([bark] if data['wood'] else [])+([leaf] if data['foliage'] else [])
        pieces=[(m,0,m['uv']) for m in data['wood']]+[(m,1 if data['wood'] else 0,m['uv']) for m in data['foliage']]
        obj=create('BranchSample',pieces,mats)
        flags=[f for m,_,_ in pieces for f in m.get('smooth',[False]*len(m['polygons']))]
        for polygon,flag in zip(obj.data.polygons,flags):polygon.use_smooth=flag
        for im in bpy.data.images:
            if im.source=='FILE':im.pack()
        folder=out/name;folder.mkdir();metrics=mesh_report(obj.data,triangle_limit=6999);export_tree(obj,folder)
        reports[name]={'metrics':metrics,'glb_sha256':sha(folder/'tree.glb'),'blend_sha256':sha(folder/'tree.blend')}
    write(out/'exports.json',{'blender':bpy.app.version_string,'build':bpy.app.build_hash.decode(),'variants':reports})


if __name__=='__main__':main(sys.argv[sys.argv.index('--')+1])
