"""Adaptador Blender para rama aislada de sauce pintado."""
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
from treegen.willow_v2 import build_sample
from treegen.pine_painted_sample import canonical_hash
from pine_painted_sample import create
from generate_oak import mesh_report
from foliage_lab import write, sha

ASSETS = ROOT/'assets/sauce-pintado/v0.1.0'


def painted(name, filename, alpha=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = False
    shader = mat.node_tree.nodes['Principled BSDF']
    shader.inputs['Roughness'].default_value = .95
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(ASSETS/filename), check_existing=True)
    mat.node_tree.links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    if alpha:
        threshold = mat.node_tree.nodes.new('ShaderNodeMath')
        threshold.operation = 'GREATER_THAN'
        threshold.inputs[1].default_value = .5
        mat.node_tree.links.new(tex.outputs['Alpha'], threshold.inputs[0])
        mat.node_tree.links.new(threshold.outputs[0], shader.inputs['Alpha'])
        mat.surface_render_method = 'DITHERED'
        mat.alpha_threshold = .5
    return mat


def main(out):
    # Blender puede crear primero los directorios XDG bajo esta salida.
    # El orquestador ya exige que la carpeta de salida sea nueva.
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    atlas = json.loads((ASSETS/'manifest.json').read_text())
    for name in ('foliage.png', 'bark.png'):
        if sha(ASSETS/name) != atlas['files'][name]['sha256']:
            raise ValueError('Recurso de pintura alterado: '+name)
    resolved = json.loads(Path(sys.argv[sys.argv.index('--')+2]).read_text())
    frozen = dict(resolved)
    assert frozen.pop('resolved_sha256') == canonical_hash(frozen)
    data = build_sample(resolved)
    wood = [(b['mesh'], 0, b['uv']) for b in data['wood']]
    leaves = [(g, 1, g['uv']) for g in data['groups']]
    mats = [painted('Painted_Bark', 'bark.png'), painted('Painted_Foliage', 'foliage.png', True)]
    variants = {}
    for name, pieces, materials in (('crossed', wood+leaves, mats), ('wood', wood, mats[:1])):
        folder = out/name
        folder.mkdir()
        obj = create('WillowBranch', pieces, materials)
        for polygon in obj.data.polygons:
            polygon.use_smooth = polygon.material_index == 0
        metrics = mesh_report(obj.data, triangle_limit=6999)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        for image in bpy.data.images:
            if image.source == 'FILE':
                image.pack()
        bpy.ops.export_scene.gltf(filepath=str(folder/'branch.glb'), export_format='GLB',
                                  use_selection=True, export_yup=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(folder/'branch.blend'))
        variants[name] = {'metrics': metrics, 'glb_sha256': sha(folder/'branch.glb')}
        bpy.data.objects.remove(obj, do_unlink=True)
    assert variants['crossed']['metrics']['triangles'] == data['triangles']
    for name in variants:
        bpy.ops.import_scene.gltf(filepath=str(out/name/'branch.glb'))
        imported = [o for o in bpy.context.selected_objects if o.type == 'MESH']
        count = sum(len(o.data.polygons) for o in imported)
        assert count == variants[name]['metrics']['triangles']
        assert all(o.data.uv_layers for o in imported)
        variants[name]['reimport_triangles'] = count
        for obj in imported:
            bpy.data.objects.remove(obj, do_unlink=True)
    write(out/'placements.json', data)
    write(out/'manifest.json', {'version': data['version'], 'seeds': data['seeds'],
          'scope': data['scope'], 'variants': variants, 'groups': len(data['groups']),
          'planes_per_group': 3, 'blender': bpy.app.version_string,
          'resources': {p.name: sha(p) for p in ASSETS.iterdir() if p.is_file()}})


if __name__ == '__main__':
    main(Path(sys.argv[sys.argv.index('--')+1]).resolve())
