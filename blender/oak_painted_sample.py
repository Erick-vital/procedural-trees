"""Rama de muestra con pintura aprobada; no cambia el generador del roble."""
import json
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.oak_painted_sample import select,leaf_card,variant_for,wood_uv,twig_spec,BRANCH_ID,PAINT_SEED
from treegen.pine_painted_sample import canonical_hash
from treegen.foliage_molds import connection_geometry
from foliage_lab import leaf_geometry,write,sha
from pine_painted_sample import create
from generate_blueprint import apply_material
from generate_oak import mesh_report

ASSETS=ROOT/'assets/roble-pintado/v0.2.0'


def painted(name,filename,alpha=False):
    mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_backface_culling=False
    shader=mat.node_tree.nodes['Principled BSDF'];shader.inputs['Roughness'].default_value=.95
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ASSETS/filename),check_existing=True)
    mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
    if alpha:
        threshold=mat.node_tree.nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.5
        mat.node_tree.links.new(tex.outputs['Alpha'],threshold.inputs[0]);mat.node_tree.links.new(threshold.outputs[0],shader.inputs['Alpha'])
        mat.surface_render_method='DITHERED';mat.alpha_threshold=.5
    return mat


def save(obj,folder):
    folder.mkdir()
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    bpy.ops.export_scene.gltf(filepath=str(folder/'branch.glb'),export_format='GLB',use_selection=True,export_yup=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/'branch.blend'))
    return {'metrics':mesh_report(obj.data,triangle_limit=12500),'glb_sha256':sha(folder/'branch.glb'),'bytes':(folder/'branch.glb').stat().st_size}


def main(out,profile='original'):
    reference=json.loads((out/'source/base-reference.json').read_text());source=json.loads((out/'source/manifest.json').read_text());atlas=json.loads((ASSETS/'manifest.json').read_text())
    wood,supports,leaves=select(reference,source)
    adjusted_spec=twig_spec(source['canopy_spec'],profile)
    lock={'version':'oak-painted-branch-0.1.0','branch_id':BRANCH_ID,'source_glb_sha256':source['glb_sha256'],
        'base_blueprint':'roble_copa_ancha@1.2.0','seeds':source['resolved_blueprint']['instance_request']['seeds'],'paint_seed':PAINT_SEED,
        'wood_ids':[b['id'] for b in wood],'support_count':len(supports),'leaf_count':len(leaves),
        'source_subset_sha256':canonical_hash([wood,supports,leaves]),'textures':atlas['files'],
        'twig_profile':profile,'twig_geometry_spec':adjusted_spec}
    write(out/'reference-lock.json',lock)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    bark=painted('Painted_Bark','bark.png');foliage=painted('Painted_Foliage','foliage.png',True)
    old_bark=apply_material('Original_Bark',source['resolved_blueprint']['appearance']['bark']);old_leaf=apply_material('Original_Leaf',source['resolved_blueprint']['appearance']['leaf'])
    old_pieces=[(b['mesh'],0,[[0,0]]*len(b['mesh']['vertices'])) for b in wood]
    new_pieces=[(b['mesh'],0,wood_uv(b)) for b in wood]
    for support in supports:
        v,f=connection_geometry(support,source['canopy_spec']);mesh={'vertices':v,'polygons':f}
        old_pieces.append((mesh,0,[[0,0]]*len(v)))
        v,f=connection_geometry(support,adjusted_spec);mesh={'vertices':v,'polygons':f}
        # Mismos anillos triangulares y ejes; solo cambian radios en fuller-v1.
        length=support['length_m'];uv=[[i%3/3,0 if i<3 else length/1.4] for i in range(len(v))]
        new_pieces.append((mesh,0,uv))
    wood_pieces=new_pieces[:]
    cards=[]
    for leaf in leaves:
        v,f=leaf_geometry(leaf);old_pieces.append(({'vertices':v,'polygons':f},1,[[0,0]]*len(v)))
        g=leaf_card(leaf,atlas['leaf_regions'][variant_for(leaf)],atlas['files']['foliage.png']['size']);cards.append(g);new_pieces.append((g,1,g['uv']))
    variants={}
    for name,pieces,mats in [('original',old_pieces,[old_bark,old_leaf]),('painted',new_pieces,[bark,foliage]),('wood',wood_pieces,[bark])]:
        obj=create('Original' if name=='original' else 'PaintedOakSample',pieces,mats)
        smooth=[flag for b in wood for flag in b['mesh']['smooth']]
        for polygon,flag in zip(obj.data.polygons,smooth):polygon.use_smooth=flag
        variants[name]=save(obj,out/name)
        bpy.data.objects.remove(obj,do_unlink=True)
    swatches=[]
    for i in range(4):
        leaf={'id':f'swatch:{i}','origin_m':[(i%2)*1.0,0,(i//2)*1.2],'length_m':1,'axes':[[0,0,1],[1,0,0],[0,1,0]]}
        g=leaf_card(leaf,atlas['leaf_regions'][i],atlas['files']['foliage.png']['size']);swatches.append((g,0,g['uv']))
    # Nombre Original evita corrección de costura de corteza sobre UV de atlas canal 0.
    obj=create('Original',swatches,[foliage]);variants['swatches']=save(obj,out/'swatches');bpy.data.objects.remove(obj,do_unlink=True)
    assert variants['original']['metrics']['triangles']==variants['painted']['metrics']['triangles']
    write(out/'placements.json',cards)
    write(out/'manifest.json',{'passed':True,'scope':'Solo muestra de pintura; no integra ni optimiza el árbol completo.',
        'reference':lock,'variants':variants,'resources':atlas['files'],'blender':bpy.app.version_string,
        'source_paths_unchanged':True,'leaf_planes_and_origins_unchanged':True,'twig_profile':profile,
        'leaf_contours':'Lobulados del atlas aprobado; no se afirma identidad con rombos anteriores.',
        'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'src/treegen/oak_painted_sample.py']}})

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    main(Path(args[0]),args[1] if len(args)>1 else 'original')
