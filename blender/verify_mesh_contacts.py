"""Regresión Blender del falso rechazo B3 y rechazo de separaciones reales."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1] / 'src')]
from mesh_contacts import insertion_errors, triangle_surface

# Cara y punto mínimos extraídos del caso fallido antes de cambiar el evaluador.
vertices = [(-4.857959270477295, 1.055238127708435, 17.97821617126465),
            (-4.848083019256592, 1.0596736669540405, 17.98701286315918),
            (-5.605328559875488, 1.1802746057510376, 18.536407470703125),
            (-5.609558582305908, 1.1784353256225586, 18.532800674438477)]
point = (-5.039996147155762, 1.089943528175354, 18.12546730041504)
mesh = bpy.data.meshes.new('B3_ContactRegression')
mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
mesh.update()
before = ([tuple(v.co) for v in mesh.vertices], [tuple(p.vertices) for p in mesh.polygons])
legacy = BVHTree.FromPolygons(vertices, [(0, 1, 2, 3)]).find_nearest(Vector(point))[3]
actual = insertion_errors(mesh, [point])[0]
assert legacy >= .0001 and actual < .000001, (legacy, actual)
_, normal, _, _ = triangle_surface(mesh).find_nearest(Vector(point))
for offset in (.001, -.001):
    separated = Vector(point) + offset * normal
    try:
        insertion_errors(mesh, [separated])
    except ValueError:
        pass
    else:
        raise AssertionError('Se aceptó una separación real de 1 mm')
for points in ([], [(float('nan'), 0, 0)]):
    try:
        insertion_errors(mesh, points)
    except ValueError:
        pass
    else:
        raise AssertionError('Se aceptó una entrada inválida')
assert before == ([tuple(v.co) for v in mesh.vertices], [tuple(p.vertices) for p in mesh.polygons])
print(json.dumps({'passed': True, 'legacy_distance_m': legacy, 'triangle_distance_m': actual,
                  'real_separation_rejected_m': .001, 'tolerance_m': .0001,
                  'mesh_unchanged': True}))

# La estrategia nueva corrige solo desviaciones reales, con cota y sin cambiar
# las proyecciones ya válidas. Un desplazamiento excesivo debe fallar.
from blueprint_surfaces import corrected_parent_surface
ref = {'branches': [{'id': 'test', 'mesh': {
    'vertices': vertices, 'polygons': [[0, 1, 2, 3]], 'smooth': [False]}}]}
for offset, expected in ((.00005, False), (.0002, True)):
    insertion = tuple(Vector(point) + offset * normal)
    project, audit = corrected_parent_surface(ref, lambda branch, target: (insertion, tuple(normal)))
    fixed, kept_normal = project('test', (0, 0, 0))
    assert (fixed != insertion) == expected
    assert audit['corrected_queries'] == int(expected)
    assert kept_normal == tuple(normal)
    insertion_errors(mesh, [fixed])
project, _ = corrected_parent_surface(ref, lambda branch, target: (tuple(Vector(point)+.002*normal), tuple(normal)))
try:
    project('test', (0,0,0))
except ValueError:
    pass
else:
    raise AssertionError('Se aceptó una corrección >1 mm')
print('Regresión de proyección acotada: OK')
