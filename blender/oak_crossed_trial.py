"""Hornear grupos sin iluminación y exportar dos ensayos de láminas cruzadas."""
import json
from pathlib import Path
import sys
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from treegen.oak_painted_tree import build
from treegen.oak_crossed import groups,fit_templates,panels,PLANES,GRID,TILE,USABLE,VERSION
from treegen.oak_painted_sample import select
from treegen.pine_painted_sample import canonical_hash
from oak_painted_sample import painted,save,ASSETS
from pine_painted_sample import create
from foliage_lab import write,sha


def bake(templates,path):
    mat=bpy.data.materials.new('BakeEmission');mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
    output=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission')
    texture=nodes.new('ShaderNodeTexImage');texture.image=bpy.data.images.load(str(ASSETS/'foliage.png'))
    alpha=nodes.new('ShaderNodeMath');alpha.operation='GREATER_THAN';alpha.inputs[1].default_value=.5
    transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
    links.new(texture.outputs['Color'],emission.inputs['Color']);links.new(texture.outputs['Alpha'],alpha.inputs[0])
    links.new(alpha.outputs[0],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
    pieces=[]
    for i,g in enumerate(templates):
        for plane,(a,b) in enumerate(PLANES):
            tile=i*3+plane;col,row=tile%GRID,tile//GRID;depth=({0,1,2}-{a,b}).pop()
            for card,vertices in zip(g['source_cards'],g['normalized_vertices']):
                projected=[[col+.5+v[a]*USABLE,row+.5+v[b]*USABLE,v[depth]*.02] for v in vertices]
                pieces.append(({'vertices':projected,'polygons':card['polygons']},0,card['uv']))
    obj=create('Original',pieces,[mat]);scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.cycles.seed=2718
    scene.render.resolution_x=scene.render.resolution_y=GRID*TILE;scene.render.resolution_percentage=100
    scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
    camera=bpy.data.objects.new('AtlasCamera',bpy.data.cameras.new('AtlasCamera'));bpy.context.collection.objects.link(camera)
    camera.location=(GRID/2,GRID/2,10);camera.rotation_euler=(0,0,0);camera.data.type='ORTHO';camera.data.ortho_scale=GRID;scene.camera=camera
    scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(obj,do_unlink=True);bpy.data.objects.remove(camera,do_unlink=True)


def atlas_material(path):
    mat=bpy.data.materials.new('Crossed_Foliage_Storage');mat.use_nodes=True;mat.use_backface_culling=False
    shader=mat.node_tree.nodes['Principled BSDF'];shader.inputs['Roughness'].default_value=.95
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True)
    mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
    threshold=mat.node_tree.nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.5
    mat.node_tree.links.new(tex.outputs['Alpha'],threshold.inputs[0]);mat.node_tree.links.new(threshold.outputs[0],shader.inputs['Alpha'])
    mat.surface_render_method='DITHERED';mat.alpha_threshold=.5
    return mat


def main(source,out,atlas_source=None):
    ref=json.loads((source/'source/base-reference.json').read_text());old=json.loads((source/'source/manifest.json').read_text())
    atlas=json.loads((ASSETS/'manifest.json').read_text());base,cards,kept=build(ref,old,atlas,2718)
    items=groups(old,cards);templates,assignment=fit_templates(items)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
    texture=out/'crossed-atlas.png'
    if atlas_source is None:bake(templates,texture)
    else:
        import shutil
        shutil.copy2(atlas_source,texture)
    bark=painted('Painted_Bark','bark.png');foliage=atlas_material(texture)
    branch_wood,branch_supports,branch_leaves=select(ref,old)
    branch_ids={b['id'] for b in branch_wood};branch_support_ids={s['id'] for s in branch_supports}
    variants={}
    # Selección por canal preserva exactamente la madera del piloto aprobado.
    full_wood=base['wood'];wood_count=len(ref['branches']);kept_ids={s['id'] for s in kept}
    branch_parts=[p for b,p in zip(ref['branches'],full_wood[:wood_count]) if b['id'] in branch_ids]
    branch_parts += [p for s,p in zip(kept,full_wood[wood_count:]) if s['id'] in branch_support_ids]
    branch_card_ids={l['id'] for l in branch_leaves}
    for scope,wood_parts in [('tree',full_wood),('branch',branch_parts)]:
        subset=items if scope=='tree' else [g for g in items if g['id'] in branch_support_ids]
        original=cards if scope=='tree' else [c for c in cards if c['source_leaf_id'] in branch_card_ids]
        for mode in ('reference','cross2','cross3'):
            name=scope+'-'+mode
            if mode=='reference':parts=wood_parts+[(c,1,c['uv']) for c in original];leaf_mat=painted('Reference_Foliage','foliage.png',True)
            else:
                count=int(mode[-1]);parts=wood_parts+[(p,1,p['uv']) for g in subset for p in panels(g,assignment[g['id']],count)];leaf_mat=foliage
            # El revisor reconoce el canal pintado de follaje en las tres versiones.
            leaf_mat.name='Painted_Foliage'
            obj=create('PaintedOakCrossed',parts,[bark,leaf_mat])
            flags=[f for b in ref['branches'] if scope=='tree' or b['id'] in branch_ids for f in b['mesh']['smooth']]
            for polygon,flag in zip(obj.data.polygons,flags):polygon.use_smooth=flag
            variants[name]=save(obj,out/name);(out/name/'branch.glb').rename(out/name/'asset.glb');(out/name/'branch.blend').rename(out/name/'asset.blend')
            bpy.data.objects.remove(obj,do_unlink=True)
            leaf_mat.name='Unused_'+name
    template_manifest=[{'id':g['id'],'normalized_vertices':g['normalized_vertices'],'source_leaf_ids':[c['source_leaf_id'] for c in g['source_cards']]} for g in templates]
    write(out/'groups.json',[{k:v for k,v in g.items() if k not in ('source_cards','descriptor')} for g in items])
    write(out/'manifest.json',{'passed':True,'version':VERSION,'paint_seed':2718,'variants':variants,'groups':len(items),'templates':template_manifest,
        'assignments':assignment,'grid':GRID,'tile_px':TILE,'usable':USABLE,'atlas_sha256':sha(texture),'source_cards_sha256':canonical_hash(cards),
        'source':str(source.relative_to(ROOT)),'source_glb_sha256':sha(source/'painted/tree.glb'),'blender':bpy.app.version_string,
        'wood_unchanged':True,'claim':'Cruces aproximan los grupos; no conservan planos individuales ni garantizan plenitud.',
        'bake':'Cycles CPU, 8 muestras, seed 2718, emisión sin iluminación, proyecciones ortográficas, pintura 0.2.0 sin repintar.'})


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:];main(Path(args[0]),Path(args[1]),Path(args[2]) if len(args)>2 else None)
