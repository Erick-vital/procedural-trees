"""Distribución 0.1.1: corrige proyecciones fuera de la superficie Q3 real."""
from foliage_branch_lab import mesh_from
from mesh_contacts import TriangleSurface, CONTACT_TOLERANCE_M

MAX_CORRECTION_M = .001


def corrected_parent_surface(ref, legacy):
    surfaces = {b['id']: TriangleSurface(mesh_from(b['mesh'], 'B3_Surface')) for b in ref['branches']}
    audit = {'version': 'q3-loop-triangles-projection-0.1.1', 'queries': 0, 'corrected_queries': 0,
             'max_correction_m': 0., 'correction_limit_m': MAX_CORRECTION_M,
             'unchanged_below_m': CONTACT_TOLERANCE_M}

    def project(branch_id, point):
        insertion, normal = legacy(branch_id, point)
        closest, distance = surfaces[branch_id].nearest(insertion)
        audit['queries'] += 1
        if distance >= CONTACT_TOLERANCE_M:
            if distance > MAX_CORRECTION_M:
                raise ValueError(f'Proyección Q3 requiere corrección excesiva: {distance} m')
            audit['corrected_queries'] += 1
            audit['max_correction_m'] = max(audit['max_correction_m'], distance)
            # La normal de corteza describe la misma cara. Se conserva para no
            # introducir otro cambio en la representación/orientación de hojas.
            return closest, normal
        return insertion, normal

    return project, audit
