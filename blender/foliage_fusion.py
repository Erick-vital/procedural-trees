"""Ensayo Q3: unir superficies de follaje por subárbol sin redistribuir masas."""
import math

import bpy
import bmesh
from mathutils import Vector

VERSION = 'q3-partial-fusion-0.2.1'
SETTINGS = {'voxel_scale_ratio': .09, 'smooth_iterations': 6, 'smooth_factor': .5,
            'max_primary_subtrees_per_group': 3,
            'cleanup_edge_voxel_ratio': .01,
            'max_grid_cells_per_group': 2000000, 'max_total_grid_cells': 12000000}


def extract(mesh, triangles, name):
    indices = sorted({v for t in triangles for v in t.vertices})
    mapping = {v: i for i, v in enumerate(indices)}
    result = bpy.data.meshes.new(name)
    result.from_pydata([tuple(mesh.vertices[i].co) for i in indices], [],
                       [tuple(mapping[i] for i in t.vertices) for t in triangles])
    for face, source in zip(result.polygons, triangles):
        face.use_smooth = source.use_smooth if hasattr(source, 'use_smooth') else False
    result.update()
    return result


def apply(obj, modifier):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def fuse(mesh, effective_scale, height):
    """Remalla grupos de hasta tres subárboles vecinos; conserva el tronco.

    No se añaden masas ni se modifican sus parámetros. Los vecinos se agrupan
    por proximidad de sus centros, sin moverlos ni cerrar toda la copa a la vez.
    """
    if not math.isfinite(effective_scale) or effective_scale <= 0:
        raise ValueError('Escala de follaje inválida')
    mesh.calc_loop_triangles()
    if len(mesh.loop_triangles) > 10000:
        raise ValueError('Entrada fuera del presupuesto v1')
    groups, wood, trunk = {}, [], []
    for t in mesh.loop_triangles:
        material = mesh.materials[t.material_index].name
        if material == 'Oak_Bark':
            wood.append(t)
            continue
        if material != 'Oak_Leaves':
            raise ValueError('Material no reconocido')
        v = t.vertices[0]
        level = mesh.attributes['q3_level'].data[v].value
        branch = mesh.attributes['q3_branch'].data[v].value
        owner = branch - 100 if level == 1 else (branch - 200)//3 if level == 2 else -1
        (groups.setdefault(owner, []) if owner >= 0 else trunk).append(t)
    centers = {}
    for owner, triangles in groups.items():
        indices = sorted({v for t in triangles for v in t.vertices})
        centers[owner] = sum((mesh.vertices[i].co for i in indices), Vector())/len(indices)
    remaining, merged, members = set(groups), {}, {}
    while remaining:
        first = min(remaining)
        neighbors = sorted(remaining, key=lambda k: ((centers[k]-centers[first]).length_squared, k))[:SETTINGS['max_primary_subtrees_per_group']]
        merged[first] = [t for k in neighbors for t in groups[k]]
        members[first] = neighbors
        remaining.difference_update(neighbors)
    groups = merged
    # Limitar el trabajo antes de crear las cuadrículas de remallado.
    voxel = effective_scale * SETTINGS['voxel_scale_ratio']
    grids = {}
    for owner, triangles in sorted(groups.items()):
        points = [mesh.vertices[i].co for t in triangles for i in t.vertices]
        cells = math.prod(math.ceil((max(v[k] for v in points)-min(v[k] for v in points))/voxel)+6 for k in range(3))
        if cells > SETTINGS['max_grid_cells_per_group']:
            raise ValueError(f'Cuadrícula de subárbol {owner} demasiado grande: {cells}')
        grids[owner] = cells
    if sum(grids.values()) > SETTINGS['max_total_grid_cells']:
        raise ValueError('Trabajo total de remallado excesivo')
    # Conservar polígonos y sombreado de madera, además de sus triángulos.
    wood_polygons = [p for p in mesh.polygons if mesh.materials[p.material_index].name == 'Oak_Bark']
    parts = [(extract(mesh, wood_polygons, 'FrozenWood'), 'Oak_Bark')]
    if trunk:
        parts.append((extract(mesh, trunk, 'UnchangedTrunkLeaves'), 'Oak_Leaves'))
    reports = []
    for owner, triangles in sorted(groups.items()):
        part = extract(mesh, triangles, f'Subtree_{owner}')
        obj = bpy.data.objects.new(f'Fusion_{owner}', part)
        bpy.context.collection.objects.link(obj)
        remesh = obj.modifiers.new('Union', 'REMESH')
        remesh.mode = 'VOXEL'
        remesh.voxel_size = voxel
        remesh.adaptivity = 0
        remesh.use_remove_disconnected = False
        remesh.use_smooth_shade = False
        apply(obj, remesh)
        smooth = obj.modifiers.new('Transition', 'SMOOTH')
        smooth.factor = SETTINGS['smooth_factor']
        smooth.iterations = SETTINGS['smooth_iterations']
        apply(obj, smooth)
        obj.data.calc_loop_triangles()
        intermediate = len(obj.data.loop_triangles)
        if not intermediate or intermediate > 300000:
            raise ValueError('Remallado vacío o excesivo')
        decimate = obj.modifiers.new('FacetBudget', 'DECIMATE')
        decimate.ratio = min(1., len(triangles)/intermediate)
        decimate.use_collapse_triangulate = True
        apply(obj, decimate)
        # Eliminar aristas residuales diminutas antes de exportar; glTF puede
        # descartar sus caras y provocar discrepancias entre malla y archivo.
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=voxel*SETTINGS['cleanup_edge_voxel_ratio'])
        bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=voxel*SETTINGS['cleanup_edge_voxel_ratio'])
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.calc_loop_triangles()
        for v in obj.data.vertices:
            v.co.z = min(height, max(0., v.co.z))
        result = obj.data
        parts.append((result, 'Oak_Leaves'))
        reports.append({'primary_indices': members[owner], 'input_triangles': len(triangles),
                        'remeshed_triangles': intermediate, 'output_triangles': len(result.loop_triangles),
                        'estimated_grid_cells': grids[owner]})
        bpy.data.objects.remove(obj, do_unlink=True)
    coords, faces, materials, smoothing = [], [], [], []
    for part, material in parts:
        part.calc_loop_triangles()
        offset = len(coords)
        coords.extend(tuple(v.co) for v in part.vertices)
        faces.extend(tuple(i+offset for i in p.vertices) for p in part.polygons)
        materials.extend([0 if material == 'Oak_Bark' else 1]*len(part.polygons))
        smoothing.extend(p.use_smooth for p in part.polygons)
    result = bpy.data.meshes.new('OakPartialFusion')
    result.from_pydata(coords, [], faces)
    for name in ('Oak_Bark', 'Oak_Leaves'):
        result.materials.append(bpy.data.materials[name])
    for polygon, material, smooth in zip(result.polygons, materials, smoothing):
        polygon.material_index = material
        polygon.use_smooth = smooth
    result.update()
    for part, _ in parts:
        bpy.data.meshes.remove(part)
    return result, {'version': VERSION, 'settings': SETTINGS, 'voxel_size_m': voxel,
                    'groups': reports, 'trunk_leaf_triangles_unchanged': len(trunk)}
