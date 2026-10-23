"""Medidas Q1 de las curvas evaluadas por Blender; no genera geometría."""
import math


def measure_structure(case):
    groups = {name: [r for r in case['curves'] if r['channel'] == name]
              for name in ('Primary', 'Secondary')}
    primary, secondary = groups['Primary'], groups['Secondary']
    tilts = [r['inclination_final_deg'] for r in primary]
    return {'primary_count': len(primary), 'secondary_count': len(secondary),
            'max_primary_radius_ratio': max(r['radius_ratio_to_parent'] for r in primary),
            'max_secondary_radius_ratio': max((r['radius_ratio_to_parent'] for r in secondary), default=0),
            'primary_inclination_range_deg': max(tilts)-min(tilts),
            'primary_azimuth_min_gap_deg': case['summary']['primary_azimuth_min_gap_deg'],
            'primary_azimuth_max_gap_deg': case['summary']['primary_azimuth_max_gap_deg'],
            'z_scale': case['final_z_scale']}


def validate_q1(case):
    m = measure_structure(case)
    p = case['spec']['parameters']
    secondary_per_primary = 3 if case['spec'].get('algorithm_version') in ('0.2.1', '0.3.0', '0.4.0', '0.4.1') else 2
    if m['primary_count'] != p['primary_branches'] or m['secondary_count'] != (secondary_per_primary*p['primary_branches'] if p['max_depth'] == 2 else 0):
        raise ValueError('Cambió el número de ramas esperado')
    if not all(math.isfinite(v) for v in m.values()):
        raise ValueError('Medida estructural no finita')
    if m['max_primary_radius_ratio'] >= 1 or m['max_secondary_radius_ratio'] >= 1:
        raise ValueError('Una rama no es más delgada que su padre local')
    if p['primary_branches'] >= 4:
        width = 360/p['primary_branches']
        if not .65*width <= m['primary_azimuth_min_gap_deg'] <= m['primary_azimuth_max_gap_deg'] <= 1.35*width:
            raise ValueError('Reparto angular fuera de los sectores previstos')
        # Los límites mínimos del contrato pueden saturar la inclinación. El
        # objetivo de variedad se exige a los presets, no a esos extremos.
        if p['inclination_deg'] >= 30 and m['primary_inclination_range_deg'] < 5:
            raise ValueError('Inclinaciones principales prácticamente idénticas')
    return m
