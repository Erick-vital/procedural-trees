"""F0: curva e instancia nativas → copia evaluada → GLB. No genera robles."""
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy

OUT = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
assert bpy.app.version[:3] == (5, 2, 1), bpy.app.version_string
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = 0.85
    return mat


bark = material('Probe_Bark', (0.24, 0.09, 0.025))
leaf = material('Probe_Foliage', (0.13, 0.45, 0.055))
curve = bpy.data.curves.new('ProbeCurve', 'CURVE')
curve.dimensions = '3D'
spline = curve.splines.new('POLY')
spline.points.add(2)
for point, coord in zip(spline.points, [(0, 0, 0, 1), (0.1, 0, 1, 1), (0.35, 0.2, 2, 1)]):
    point.co = coord
source = bpy.data.objects.new('ProbeProcedural', curve)
bpy.context.collection.objects.link(source)
group = bpy.data.node_groups.new('F0_Probe_v1', 'GeometryNodeTree')
group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
radius = group.interface.new_socket(name='Radius', in_out='INPUT', socket_type='NodeSocketFloat')
radius.default_value = 0.05
nodes, links = group.nodes, group.links


def node(kind):
    return nodes.new(kind)


inp, out = node('NodeGroupInput'), node('NodeGroupOutput')
profile = node('GeometryNodeCurvePrimitiveCircle')
profile.inputs['Resolution'].default_value = 8
links.new(inp.outputs['Radius'], profile.inputs['Radius'])
tube = node('GeometryNodeCurveToMesh')
tube.inputs['Fill Caps'].default_value = True
links.new(inp.outputs['Geometry'], tube.inputs['Curve'])
links.new(profile.outputs['Curve'], tube.inputs['Profile Curve'])
bark_node = node('GeometryNodeSetMaterial')
bark_node.inputs['Material'].default_value = bark
links.new(tube.outputs['Mesh'], bark_node.inputs['Geometry'])
ico = node('GeometryNodeMeshIcoSphere')
ico.inputs['Radius'].default_value = 0.6
ico.inputs['Subdivisions'].default_value = 1
leaf_node = node('GeometryNodeSetMaterial')
leaf_node.inputs['Material'].default_value = leaf
links.new(ico.outputs['Mesh'], leaf_node.inputs['Geometry'])
point = node('GeometryNodeMeshLine')
point.inputs['Count'].default_value = 1
point.inputs['Start Location'].default_value = (0.35, 0.2, 2)
instance = node('GeometryNodeInstanceOnPoints')
links.new(point.outputs['Mesh'], instance.inputs['Points'])
links.new(leaf_node.outputs['Geometry'], instance.inputs['Instance'])
realize = node('GeometryNodeRealizeInstances')
links.new(instance.outputs['Instances'], realize.inputs['Geometry'])
join = node('GeometryNodeJoinGeometry')
links.new(bark_node.outputs['Geometry'], join.inputs['Geometry'])
links.new(realize.outputs['Geometry'], join.inputs['Geometry'])
links.new(join.outputs['Geometry'], out.inputs['Geometry'])
modifier = source.modifiers.new('ProbeNodes', 'NODES')
modifier.node_group = group
modifier.properties.inputs[radius.identifier]['value'] = 0.12
bpy.context.view_layer.update()
evaluated = source.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=bpy.context.evaluated_depsgraph_get())
mesh.calc_loop_triangles()
assert len(mesh.vertices) == 36, len(mesh.vertices)
assert len(mesh.loop_triangles) == 64, len(mesh.loop_triangles)
assert all(math.isfinite(c) for v in mesh.vertices for c in v.co)
assert all(t.area > 1e-10 for t in mesh.loop_triangles)
materials = {m.name: sum(1 for t in mesh.loop_triangles if t.material_index == i)
             for i, m in enumerate(mesh.materials) if m is not None}
assert materials == {'Probe_Bark': 44, 'Probe_Foliage': 20}, materials
vertices = sorted([list(round(c, 6) for c in v.co) for v in mesh.vertices])
triangles = sorted((mesh.materials[t.material_index].name,
                    sorted(tuple(round(c, 6) for c in mesh.vertices[i].co) for i in t.vertices))
                   for t in mesh.loop_triangles)
minimum = [min(v[i] for v in vertices) for i in range(3)]
maximum = [max(v[i] for v in vertices) for i in range(3)]
export = bpy.data.objects.new('ProbeMesh', mesh)
bpy.context.collection.objects.link(export)
bpy.ops.object.select_all(action='DESELECT')
export.select_set(True)
bpy.context.view_layer.objects.active = export
bpy.ops.export_scene.gltf(filepath=str(OUT / 'probe.glb'), export_format='GLB',
                          use_selection=True, export_yup=True, export_materials='EXPORT')
source.hide_render = True
source.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'probe.blend'))
report = {
    'probe_version': '1', 'seed': 0, 'blender': bpy.app.version_string,
    'blender_build_hash': bpy.app.build_hash.decode(), 'python': sys.version,
    'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'socket_mapping': {'Radius': radius.identifier},
    'vertices': len(mesh.vertices), 'triangles': len(mesh.loop_triangles),
    'triangles_by_material': materials, 'bounds_blender': [minimum, maximum],
    'geometry_sha256': hashlib.sha256(json.dumps({'vertices': vertices, 'triangles': triangles}).encode()).hexdigest(),
    'glb_sha256': hashlib.sha256((OUT / 'probe.glb').read_bytes()).hexdigest(),
    'units': 'meters', 'axis_conversion': '(x,y,z) Blender -> (x,z,-y) Godot',
    'nodes': [n.bl_idname for n in nodes],
}
(OUT / 'blender-report.json').write_text(json.dumps(report, indent=2) + '\n')
