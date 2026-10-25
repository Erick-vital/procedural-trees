"""Reimporta GLB: verifica triángulos de cada soporte y raíces dentro del padre."""
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from foliage_lab import write


def key(points):
    return tuple(sorted(tuple(p) for p in points))


def inside(bvh, point):
    for direction in ((.31,.79,.53),(-.67,.23,.71),(.53,-.82,-.19)):
        ray=Vector(direction).normalized()
        hit,normal,_,distance=bvh.ray_cast(Vector(point),ray)
        assert hit is not None and distance > 0 and normal.dot(ray)>0, ('Raíz fuera de soporte',point)


def check(folder):
    m=json.loads((folder/'manifest.json').read_text())
    ref=json.loads((folder/'base-reference.json').read_text())
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(folder/'tree.glb'))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(objects)==1
    obj=objects[0];mesh=obj.data;mesh.calc_loop_triangles()
    wood=[]
    needles=[]
    for t in mesh.loop_triangles:
        coords=[obj.matrix_world@mesh.vertices[i].co for i in t.vertices]
        (wood if mesh.materials[t.material_index].name.startswith('Pine_Bark') else needles).append(coords)
    vertices=[p for tri in wood for p in tri]
    kd=KDTree(len(vertices))
    for i,p in enumerate(vertices):kd.insert(p,i)
    kd.balance()
    triangles={key(p) for p in wood}
    bvhs={};max_error=0
    for b in ref['branches']:
        matched=[]
        for p in b['mesh']['vertices']:
            co,_,error=kd.find(Vector(p));max_error=max(max_error,error)
            assert error<.00001
            matched.append(co)
        for face in b['mesh']['polygons']:
            assert key([matched[i] for i in face]) in triangles, 'Triángulo de soporte ausente'
        bvhs[b['id']]=BVHTree.FromPolygons(matched,b['mesh']['polygons'],all_triangles=True)
    for b in ref['branches']:
        if b['parent_id'] is not None:inside(bvhs[b['parent_id']],b['points_m'][0])
    for n in m['placements']:inside(bvhs[n['support_id']],n['origin_m'])
    # Cada origen declarado también debe existir como raíz de una lámina exportada.
    kd_leaf=KDTree(len(needles)*3)
    for i,p in enumerate(p for tri in needles for p in tri):kd_leaf.insert(p,i)
    kd_leaf.balance()
    assert all(kd_leaf.find(Vector(n['origin_m']))[2]<.00001 for n in m['placements'])
    return {'passed':True,'branch_insertions':len(ref['branches'])-1,'needle_roots':len(m['placements']),
            'all_parent_triangles_found_in_glb':True,'max_vertex_error_m':max_error,
            'method':'GLB reimportado; triángulos reales por soporte, tres rayos con salida orientada'}


if __name__=='__main__':
    source,destination=sys.argv[sys.argv.index('--')+1:]
    results={str(folder):check(Path(folder)) for folder in json.loads(Path(source).read_text())}
    write(Path(destination),{'passed':all(r['passed'] for r in results.values()),'cases':results})
