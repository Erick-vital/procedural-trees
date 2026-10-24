"""Superficies trianguladas Blender con proyección/distancia en doble precisión."""
import math

from mathutils import Vector
from mathutils.bvhtree import BVHTree
from treegen.surface_evaluation import closest_point_on_triangle

CONTACT_TOLERANCE_M = .0001


class TriangleSurface:
    def __init__(self, mesh):
        mesh.calc_loop_triangles()
        if not 1 <= len(mesh.loop_triangles) <= 12500:
            raise ValueError('Superficie fuera del trabajo acotado')
        self.triangles = [tuple(tuple(mesh.vertices[i].co) for i in t.vertices) for t in mesh.loop_triangles]
        self.boxes = [tuple((min(v[k] for v in t), max(v[k] for v in t)) for k in range(3)) for t in self.triangles]
        self.bvh = BVHTree.FromPolygons([v.co for v in mesh.vertices],
            [tuple(t.vertices) for t in mesh.loop_triangles], all_triangles=True)

    def nearest(self, point):
        if len(point) != 3 or not all(math.isfinite(v) for v in point):
            raise ValueError('Inserción no finita o inválida')
        _, _, index, _ = self.bvh.find_nearest(Vector(point))
        if index is None:
            raise ValueError('Superficie sin triángulo próximo')
        closest = closest_point_on_triangle(point, *self.triangles[index])
        distance = math.dist(point, closest)
        # El BVH float32 elige candidato; la aceptación y el descarte de otras
        # caras se hacen en float64. Máximo 360 * 12500 cajas en evaluación.
        for i, (triangle, box) in enumerate(zip(self.triangles, self.boxes)):
            if i != index and all(low-distance <= point[k] <= high+distance for k,(low,high) in enumerate(box)):
                candidate = closest_point_on_triangle(point, *triangle)
                error = math.dist(point, candidate)
                if error < distance:
                    closest, distance = candidate, error
        return closest, distance


def triangle_surface(mesh):
    return TriangleSurface(mesh).bvh


def insertion_errors(mesh, points, *, tolerance_m=CONTACT_TOLERANCE_M):
    if not math.isfinite(tolerance_m) or not 0 < tolerance_m <= CONTACT_TOLERANCE_M:
        raise ValueError('Tolerancia de contacto inválida')
    if not 1 <= len(points) <= 360:
        raise ValueError('Cantidad de inserciones inválida')
    surface = TriangleSurface(mesh)
    errors = []
    for point in points:
        _, distance = surface.nearest(point)
        if not math.isfinite(distance) or distance >= tolerance_m:
            raise ValueError(f'Inserción fuera de la madera triangulada: {distance} m')
        errors.append(distance)
    return errors
