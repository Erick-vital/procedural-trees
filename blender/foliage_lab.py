"""RF0/RF1: escenas congeladas y hojas pequeñas, sin alterar el generador Q3."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'blender')]
from generate_oak import material, mesh_report
from oak_nodes import Graph, GEO
from treegen.foliage import digest, load_unit, placements, MAX_TRIANGLES


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    return {name: sha(ROOT/name) for name in ('blender/foliage_lab.py', 'src/treegen/foliage.py',
        'schemas/foliage-unit.schema.json', 'blender/generate_oak.py', 'blender/oak_nodes.py')}


def configure():
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.studio_light = 'paint.sl'
    scene.display.shading.studiolight_rotate_z = .5
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = False
    scene.display.shading.background_type = 'WORLD'
    scene.world.color = (.09, .11, .14)
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1


def rig(center, span, height=None):
    center = Vector(center)
    camera = bpy.data.objects.new('RFInspectionCamera', bpy.data.cameras.new('RFInspectionCamera'))
    bpy.context.collection.objects.link(camera)
    result = {}
    directions = {'front': (0, -1, 0), 'side': (1, 0, 0), 'top': (0, 0, 1),
                  'below': (1.3, -1.8, -.8), 'perspective': (1.3, -1.8, .8),
                  'reverse': (-1.3, 1.8, -.8)}
    for name, direction in directions.items():
        camera.location = center + Vector(direction).normalized()*span*3
        camera.rotation_euler = (center-camera.location).to_track_quat('-Z', 'Y').to_euler()
        result[name] = {'type': 'ORTHO', 'location': list(camera.location),
                        'rotation_euler': list(camera.rotation_euler), 'ortho_scale': span*1.3,
                        'basis_columns': [list(column) for column in camera.rotation_euler.to_matrix().col],
                        'lens_mm': 50, 'resolution': [900, 900]}
    if height is not None:
        # Distancias calculadas solo con la referencia. RF0 registra además la
        # altura realmente proyectada, sin usar el tamaño del candidato.
        for name, fraction in [('near', .5), ('medium', .25), ('far', .1)]:
            camera.location = center+Vector((0, -1, 0))*span*5
            camera.rotation_euler = (center-camera.location).to_track_quat('-Z', 'Y').to_euler()
            result[name] = {'type': 'ORTHO', 'location': list(camera.location),
                            'rotation_euler': list(camera.rotation_euler), 'ortho_scale': height/fraction,
                            'basis_columns': [list(column) for column in camera.rotation_euler.to_matrix().col],
                            'lens_mm': 50, 'resolution': [900, 900], 'target_height_fraction': fraction}
    bpy.data.objects.remove(camera, do_unlink=True)
    return result


def render(obj, folder, cameras):
    folder.mkdir(parents=True, exist_ok=True)
    configure()
    scene = bpy.context.scene
    for other in scene.objects:
        if other.type == 'MESH':
            other.hide_render = other != obj
    obj.hide_set(False)
    camera = bpy.data.objects.new('RFRenderCamera', bpy.data.cameras.new('RFRenderCamera'))
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    projections = {}
    for name, settings in cameras.items():
        camera.data.type = settings['type']
        camera.location = settings['location']
        camera.rotation_euler = settings['rotation_euler']
        camera.data.ortho_scale = settings['ortho_scale']
        camera.data.lens = settings['lens_mm']
        bpy.context.view_layer.update()
        coords = [world_to_camera_view(scene, camera, obj.matrix_world@v.co) for v in obj.data.vertices]
        projections[name] = max(v.y for v in coords)-min(v.y for v in coords)
        scene.render.filepath = str(folder/f'{name}.png')
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    return projections


def export(obj, folder):
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(folder/'unit.glb'), export_format='GLB',
                              use_selection=True, export_yup=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/'scene.blend'))


def evaluated(graph):
    obj = bpy.data.objects.new('RFProbe', bpy.data.meshes.new('RFProbe'))
    bpy.context.collection.objects.link(obj)
    mod = obj.modifiers.new('RFProbe', 'NODES')
    mod.node_group = graph.tree
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph), depsgraph=depsgraph)
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.node_groups.remove(graph.tree)
    return mesh


def reference(source, folder):
    files = {name: sha(source/name) for name in ('tree.blend', 'tree.glb', 'manifest.json')}
    manifest = json.loads((source/'manifest.json').read_text())
    assert manifest['spec']['algorithm_version'] == '0.4.0'
    bpy.ops.wm.open_mainfile(filepath=str(source/'tree.blend'), load_ui=False)
    obj = bpy.data.objects['Oak']
    assert mesh_report(obj.data) == manifest['metrics']
    generator = bpy.data.objects['OakProcedural'].modifiers[0].node_group
    structure = next(n.node_tree for n in generator.nodes if n.type == 'GROUP' and n.node_tree.name.startswith('Oak_Structure'))
    volume = next(n.node_tree for n in generator.nodes if n.type == 'GROUP' and n.node_tree.name.startswith('Oak_Volume'))

    def branch_graph(sample=False):
        graph = Graph('RF0_BranchSnapshot', [], [('Geometry', GEO)])
        node = graph.group(structure)
        for item in structure.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                graph.set(node, item.name, manifest['socket_values'][item.name])
        select = graph.node('GeometryNodeSeparateGeometry', domain='CURVE')
        graph.set(select, 'Geometry', node.outputs['Primary'])
        graph.set(select, 'Selection', graph.op('LESS_THAN', graph.node('GeometryNodeInputIndex').outputs['Index'], .5))
        geometry = select.outputs['Selection']
        if sample:
            points = graph.node('GeometryNodeCurveToPoints', mode='COUNT')
            graph.set(points, 'Curve', geometry)
            graph.set(points, 'Count', 64)
            vertices = graph.node('GeometryNodePointsToVertices')
            graph.set(vertices, 'Points', points.outputs['Points'])
            geometry = vertices.outputs['Mesh']
        else:
            node = graph.group(volume, Curves=geometry, Bark=bpy.data.materials['Oak_Bark'])
            graph.set(node, 'Profile Resolution', 8)
            geometry = node.outputs['Mesh']
        transform = graph.node('GeometryNodeTransform')
        graph.set(transform, 'Geometry', geometry)
        graph.set(transform, 'Scale', manifest['normalization']['scale'])
        graph.set(transform, 'Translation', manifest['normalization']['translation'])
        graph.set(graph.output, 'Geometry', transform.outputs['Geometry'])
        return graph

    branch_mesh = evaluated(branch_graph())
    curve = evaluated(branch_graph(True))
    assert len(curve.vertices) == 64
    points = [list(v.co) for v in curve.vertices]
    bpy.data.meshes.remove(curve)
    # Comparar los triángulos reconstruidos contra la madera realmente guardada.
    def triangles(mesh):
        mesh.calc_loop_triangles()
        return Counter(tuple(sorted(tuple(round(c, 5) for c in mesh.vertices[i].co) for i in t.vertices))
                       for t in mesh.loop_triangles if mesh.materials[t.material_index].name == 'Oak_Bark')
    # El manifiesto redondea la caja usada para registrar scale_z. Reconstruir
    # con ese valor puede diferir unos micrómetros; seleccionar por cercanía y
    # extraer después exclusivamente las coordenadas originales sin redondear.
    wood_indices = sorted({i for p in obj.data.polygons
        if obj.data.materials[p.material_index].name == 'Oak_Bark' for i in p.vertices})
    kd = KDTree(len(wood_indices))
    for i in wood_indices:
        kd.insert(obj.data.vertices[i].co, i)
    kd.balance()
    matches = [kd.find(v.co) for v in branch_mesh.vertices]
    reconstruction_error = max(item[2] for item in matches)
    assert reconstruction_error < .00001, f'Rama distinta de la guardada: {reconstruction_error}'
    # Extraer los polígonos originales de esa componente, conservando precisión,
    # normales, materiales y orden de vértices del árbol de referencia.
    chosen = {item[1] for item in matches}
    original_faces = [p for p in obj.data.polygons if obj.data.materials[p.material_index].name == 'Oak_Bark'
                      and all(i in chosen for i in p.vertices)]
    from foliage_fusion import extract
    frozen = extract(obj.data, original_faces, 'RF0_OriginalBranch')
    frozen.materials.append(bpy.data.materials['Oak_Bark'])
    assert len(frozen.vertices) == len(branch_mesh.vertices)
    assert len(frozen.polygons) == len(branch_mesh.polygons)
    assert sum(triangles(frozen).values()) == sum(triangles(branch_mesh).values())
    bpy.data.meshes.remove(branch_mesh)
    branch = bpy.data.objects.new('RF0_Primary_100', frozen)
    bpy.context.collection.objects.link(branch)
    branch.matrix_world = obj.matrix_world.copy()
    bounds = manifest['metrics']['bounds_blender']
    center = [(a+b)/2 for a, b in zip(*bounds)]
    tree_rig = rig(center, max(b-a for a, b in zip(*bounds)), height=manifest['spec']['parameters']['height_m'])
    tree_projection = render(obj, folder/'tree', tree_rig)
    for name, fraction in [('near', .5), ('medium', .25), ('far', .1)]:
        assert abs(tree_projection[name]-fraction) < .001
    coords = [v.co for v in branch.data.vertices]
    low, high = [[fn(v[k] for v in coords) for k in range(3)] for fn in (min, max)]
    branch_rig = rig([(a+b)/2 for a, b in zip(low, high)], max(b-a for a, b in zip(low, high)))
    render(branch, folder/'branch', branch_rig)
    export(branch, folder)
    branch_geometry = {'vertices': [list(v.co) for v in frozen.vertices],
        'polygons': [list(p.vertices) for p in frozen.polygons], 'smooth': [p.use_smooth for p in frozen.polygons]}
    lock = {'version': 'rf0-reference-0.1.0', 'case': source.name, 'source': str(source),
        'source_files_sha256': files, 'sources_sha256': sources(), 'spec': manifest['spec'],
        'seeds': manifest['seeds'], 'normalization': manifest['normalization'],
        'metrics': manifest['metrics'], 'tree_matrix_world': [list(row) for row in obj.matrix_world],
        'wood_geometry_sha256': manifest['crown_checks']['wood_geometry_sha256'],
        'branch': {'id': 'q3:primary:100', 'channel': 'Primary', 'curve_index': 0,
                   'mesh': branch_geometry, 'mesh_sha256': digest(branch_geometry),
                   'source_vertex_indices': sorted(chosen),
                   'source_polygon_indices': [p.index for p in original_faces],
                   'reconstruction_selection_tolerance_m': .00001,
                   'reconstruction_max_error_m': reconstruction_error,
                   'points_final_m': points, 'metrics': mesh_report(frozen),
                   'matrix_world': [list(row) for row in branch.matrix_world]},
        'materials': {m.name: {'diffuse': list(m.diffuse_color),
            'backface_culling': m.use_backface_culling,
            'principled_base': list(m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value),
            'roughness': m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value}
            for m in obj.data.materials if m},
        'tree_cameras': tree_rig, 'branch_cameras': branch_rig, 'tree_projected_height': tree_projection,
        'lighting': {'engine': 'BLENDER_WORKBENCH', 'studio': 'paint.sl', 'rotation_z': .5,
            'cavity': False, 'shadows': True, 'world_color': list(bpy.context.scene.world.color),
            'view_transform': 'Standard', 'look': 'None', 'exposure': 0, 'gamma': 1},
        'blender': bpy.app.version_string, 'blender_build': bpy.app.build_hash.decode(),
        'blender_python': sys.version, 'source_unchanged': files == {name: sha(source/name) for name in files}}
    assert lock['source_unchanged']
    write(folder/'reference-lock.json', lock)


def leaf_geometry(placement):
    length = placement['length_m']
    width = length*placement['width_ratio']
    fold = math.radians(placement['fold_deg'])
    if placement['variant'] == 'diamond':
        shape = [(0, 0), (.48, -.5), (1, 0), (.48, .5)]
        faces = [(0, 1, 2), (0, 2, 3)]
    else:
        shape = [(0, 0), (.28, -.38), (.72, -.5), (1, 0), (.72, .5), (.28, .38)]
        faces = [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 5)]
    axes = [Vector(v) for v in placement['axes']]
    origin = Vector(placement['origin_m'])
    coords = [origin+axes[0]*x*length+axes[1]*y*width*math.cos(fold)
              +axes[2]*abs(y)*width*math.sin(fold) for x, y in shape]
    return coords, faces


def unit(spec_path, cameras_path, folder, no_render=False):
    spec = load_unit(spec_path)
    leaves = placements(spec)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    vertices, triangles = [], []
    for leaf in leaves:
        coords, faces = leaf_geometry(leaf)
        offset = len(vertices)
        vertices.extend(coords)
        triangles.extend(tuple(i+offset for i in face) for face in faces)
    assert len(triangles) <= MAX_TRIANGLES
    mesh = bpy.data.meshes.new('RF1_Leaves')
    mesh.from_pydata(vertices, [], triangles)
    leaves_mat = material('RF1_Leaf', (.23, .43, .065))
    leaves_mat.use_backface_culling = False
    mesh.materials.append(leaves_mat)
    mesh.update()
    obj = bpy.data.objects.new('RF1_Unit', mesh)
    bpy.context.collection.objects.link(obj)
    metrics = mesh_report(mesh)
    # No cambiar cámaras por variante, semilla ni tamaño.
    if cameras_path:
        cameras = json.loads(cameras_path.read_text())
    else:
        cameras = rig([0, 0, .325], .72)
    write(folder/'cameras.json', cameras)
    if not no_render:
        render(obj, folder, cameras)
    # Un segundo ángulo de iluminación comprueba que el plegado no dependa de uno.
    scene = bpy.context.scene
    camera = bpy.data.objects.new('RFAlternateCamera', bpy.data.cameras.new('RFAlternateCamera'))
    bpy.context.collection.objects.link(camera)
    settings = cameras['perspective']
    camera.location, camera.rotation_euler = settings['location'], settings['rotation_euler']
    camera.data.type, camera.data.ortho_scale = 'ORTHO', settings['ortho_scale']
    scene.camera = camera
    scene.display.shading.studiolight_rotate_z = 2.0
    scene.render.filepath = str(folder/'alternate-light.png')
    if not no_render:
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    configure()
    export(obj, folder)
    per_leaf = 2 if spec['parameters']['variant'] == 'diamond' else 4
    manifest = {'version': spec['version'], 'spec': spec, 'spec_sha256': digest(spec),
        'placements': leaves, 'placements_sha256': digest(leaves), 'metrics': metrics,
        'leaf_count': len(leaves), 'triangles_per_leaf': per_leaf, 'materials': 1,
        'limits': {'max_leaves': 32, 'max_triangles': MAX_TRIANGLES},
        'material': {'opaque': True, 'double_sided': True, 'alpha': 1, 'textures': False},
        'cameras_sha256': digest(cameras), 'sources_sha256': sources(),
        'blender': bpy.app.version_string, 'blender_build': bpy.app.build_hash.decode(),
        'blender_python': sys.version, 'files_sha256': {n: sha(folder/n) for n in ('unit.glb', 'scene.blend')}}
    assert metrics['triangles'] == per_leaf*len(leaves)
    write(folder/'manifest.json', manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('reference', 'unit'))
    parser.add_argument('--source', type=Path)
    parser.add_argument('--spec', type=Path)
    parser.add_argument('--cameras', type=Path)
    parser.add_argument('--no-render', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert bpy.app.version[:3] == (5, 2, 1)
    args.output.mkdir(parents=True, exist_ok=False)
    if args.mode == 'reference':
        reference(args.source.resolve(), args.output.resolve())
    else:
        unit(args.spec.resolve(), args.cameras, args.output.resolve(), args.no_render)


if __name__ == '__main__':
    main()
