"""Proyección punto/triángulo en doble precisión, independiente de Blender."""
import math

from .foliage import add, cross, dot, mul, sub


def closest_point_on_triangle(point, a, b, c):
    """Plano interior o segmento más próximo; admite triángulos degenerados."""
    normal = cross(sub(b, a), sub(c, a))
    norm2 = dot(normal, normal)
    if norm2 > 0:
        signed = dot(sub(point, a), normal)
        projected = sub(point, mul(normal, signed / norm2))
        if all(dot(cross(sub(v, u), sub(projected, u)), normal) >= 0
               for u, v in ((a, b), (b, c), (c, a))):
            return projected
    nearest = []
    for u, v in ((a, b), (b, c), (c, a)):
        edge = sub(v, u)
        length2 = dot(edge, edge)
        fraction = max(0., min(1., dot(sub(point, u), edge)/length2)) if length2 else 0.
        nearest.append(add(u, mul(edge, fraction)))
    return min(nearest, key=lambda p: math.dist(point, p))


def point_triangle_distance(point, a, b, c):
    return math.dist(point, closest_point_on_triangle(point, a, b, c))
