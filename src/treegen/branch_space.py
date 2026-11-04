"""Regla espacial F5 y métrica versionada de proximidad de ejes con radio."""
from dataclasses import replace
import math
from .branch_structure import (BranchStructure, RULE_VERSION, YAW_OFFSETS_DEG,
                              add, sub, length, segment_distance, validate_structure)

METRIC_VERSION = 'branch-capsule-pairs-0.1.0'


def segments(branch, scale_z=1.):
    points = [(v[0], v[1], v[2]*scale_z) for v in branch.points]
    radius_scale = max(1., scale_z)
    rows, distance = [], 0.
    for i, (a, b) in enumerate(zip(points, points[1:])):
        size = length(sub(b, a))
        r = max(branch.radii[i:i+2])*radius_scale
        rows.append((a, b, r, distance, size,
                     tuple(min(x, y)-r for x, y in zip(a, b)),
                     tuple(max(x, y)+r for x, y in zip(a, b))))
        distance += size
    return rows


def conflict(a, b, sa=None, sb=None, scale_z=1.):
    """Una pareja de ramas = un conflicto; excluye solo la zona de unión legítima.

    Cápsulas con radio máximo por segmento y cota max(1,sz) para las secciones
    elípticas Q2. Es proximidad conservadora, no intersección de mallas.
    """
    sa = segments(a, scale_z) if sa is None else sa
    sb = segments(b, scale_z) if sb is None else sb
    worst = 0.
    for x in sa:
        for y in sb:
            if any(x[5][k] > y[6][k] or y[5][k] > x[6][k] for k in range(3)):
                continue
            dist, t, u = segment_distance(x[0], x[1], y[0], y[1])
            threshold = x[2]+y[2]
            # Zona local medida a lo largo del hijo, no exclusión del padre completo.
            if a.parent_id == b.id and x[3]+t*x[4] <= 2*(a.radii[0]*max(1., scale_z)+y[2]):
                continue
            if b.parent_id == a.id and y[3]+u*y[4] <= 2*(b.radii[0]*max(1., scale_z)+x[2]):
                continue
            worst = max(worst, threshold-dist)
    return worst


def measure(structure, scale_z=1.):
    validate_structure(structure)
    if type(scale_z) not in (float, int) or not math.isfinite(scale_z) or not 0 < scale_z <= 10:
        raise ValueError('Escala Z inválida')
    cached = [segments(b, scale_z) for b in structure.branches]
    pairs = []
    for i, a in enumerate(structure.branches):
        for j in range(i+1, len(cached)):
            penetration = conflict(a, structure.branches[j], cached[i], cached[j], scale_z)
            if penetration > 1e-8:
                pairs.append({'branches': [a.id, structure.branches[j].id], 'capsule_overlap_m': penetration})
    total = sum(s[4] for rows in cached for s in rows)
    return {'version': METRIC_VERSION, 'scale_z': scale_z, 'branch_count': len(cached),
            'length_m': total, 'conflicts': len(pairs), 'conflicts_per_m': len(pairs)/total,
            'pairs': pairs, 'radius_model': 'max_segment_radius_times_max_1_scale_z'}


def rotated(branch, angle):
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    root = branch.points[0]
    points = []
    for p in branch.points:
        x, y, z = sub(p, root)
        points.append(add(root, (x*c-y*s, x*s+y*c, z)))
    return replace(branch, points=tuple(points))


def separate(structure):
    """Dos barridos, nueve direcciones por secundaria; sin poda ni reintentos.

    Troncales/primarias, raíces, radios y Z permanecen iguales. La elección incluye
    la dirección actual y solo acepta mejora estricta de conflictos incidentes.
    """
    validate_structure(structure)
    branches = list(structure.branches)
    cached = [segments(b) for b in branches]
    decisions = []
    for sweep in range(2):
        for i, branch in enumerate(branches):
            if branch.level != 2:
                continue

            def score(candidate, rows):
                overlaps = [conflict(candidate, b, rows, cached[j]) for j, b in enumerate(branches) if j != i]
                return sum(v > 1e-8 for v in overlaps), sum(v for v in overlaps if v > 1e-8)

            best, best_rows, angle = branch, cached[i], 0
            initial = best_score = score(best, best_rows)
            for offset in YAW_OFFSETS_DEG[1:]:
                candidate = rotated(branch, offset)
                rows = segments(candidate)
                value = score(candidate, rows)
                # No aceptar una mejora numérica minúscula en la penetración.
                if value[0] < best_score[0] or (value[0] == best_score[0] and value[1] < best_score[1]-1e-7):
                    best, best_rows, best_score, angle = candidate, rows, value, offset
            branches[i], cached[i] = best, best_rows
            decisions.append({'sweep': sweep, 'branch': branch.id, 'yaw_delta_deg': angle,
                              'before': initial, 'after': best_score})
    result = BranchStructure(structure.version, structure.seed, tuple(branches))
    validate_structure(result)
    return result, {'version': RULE_VERSION, 'sweeps': 2, 'offsets_deg': YAW_OFFSETS_DEG,
                    'evaluated_candidates': len(decisions)*len(YAW_OFFSETS_DEG), 'decisions': decisions}
