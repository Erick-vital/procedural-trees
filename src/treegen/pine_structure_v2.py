"""pine-whorls@0.2.0: pseudovérticilos desfasados y ramificación asimétrica."""
import math
import random

from .pine import add, mul, sub, unit, cross, tube, point_on


def structure(parameters, structure_seed):
    b = parameters['base']
    rng = random.Random(structure_seed)
    h, radius = b['height_m'], b['base_radius_m']
    phase = rng.uniform(0, 2*math.pi)
    strength = b['irregularity']/.16

    def center(z):
        sway = math.sin(z/h*math.pi)*h*.012*b['irregularity']
        return [sway*math.cos(phase), sway*math.sin(phase), z]

    branches = []

    def branch(identifier, parent, points, radii, sides, whorl=None):
        item = {'id': identifier, 'parent_id': parent, 'points_m': points, 'radii_m': radii,
                'whorl': whorl, 'mesh': tube(points, radii, sides, vertical=parent is None)}
        branches.append(item)
        return item

    trunk = branch('pine:trunk', None, [center(h*i/11) for i in range(12)],
                   [radius*(1-i/11)*.97+radius*.03 for i in range(12)], 8)
    step = h*(.88-b['crown_base_ratio'])/(b['whorl_count']-1)
    count = b['branches_per_whorl']
    for level in range(b['whorl_count']):
        t = level/(b['whorl_count']-1)
        nominal_z = h*(b['crown_base_ratio']+(.88-b['crown_base_ratio'])*t)
        floor_offset = rng.uniform(-.10,.10)*step*strength
        offsets = [(2*j/(count-1)-1)*.38+rng.uniform(-.035,.035) for j in range(count)]
        rng.shuffle(offsets)
        rotation = phase+level*2.399963229728653
        for j in range(count):
            z = nominal_z+floor_offset+offsets[j]*step*strength
            root = point_on(trunk,z/h)
            # La envolvente usa la altura efectiva de inserción, no solo el piso.
            crown_t = max(0,min(1,(z/h-b['crown_base_ratio'])/(.88-b['crown_base_ratio'])))
            length = h*b['crown_radius_ratio']*(1-.88*crown_t)**.95
            length *= 1+rng.uniform(-1,1)*b['irregularity']*1.25
            angle = rotation+2*math.pi*j/count+rng.uniform(-.9,.9)*b['irregularity']
            direction = [math.cos(angle),math.sin(angle),0]
            side = [-direction[1],direction[0],0]
            pitch = b['branch_rise_ratio']+rng.uniform(-.28,.22)*strength+.04*t
            bend = rng.uniform(-.12,.12)*strength
            points = [add(root,add(add(mul(direction,length*s),mul(side,length*bend*s*s)),
                                  [0,0,length*(pitch*s+.06*strength*s*s)])) for s in (0,1/3,2/3,1)]
            r = radius*.24*(1-.72*t)
            main = branch(f'pine:p:{level}:{j}',trunk['id'],points,[r,r*.72,r*.38,r*.12],6,level)
            signs = [-1,1,-1,1]
            rng.shuffle(signs)
            for k, (nominal,sign) in enumerate(zip((.30,.47,.65,.82),signs)):
                along = nominal+rng.uniform(-.055,.055)*strength
                origin = point_on(main,along)
                tangent = unit(sub(point_on(main,min(.99,along+.04)),point_on(main,max(.01,along-.04))))
                lateral = unit(cross([0,0,1],tangent))
                spread = .92+rng.uniform(-.27,.27)*strength
                axis = unit(add(mul(tangent,math.cos(spread)),mul(lateral,sign*math.sin(spread))))
                extent = length*b['secondary_length_ratio']*(1.25-.4*along)
                extent *= 1+rng.uniform(-.25,.25)*strength
                rise = .20+rng.uniform(-.38,.38)*strength
                curve = rng.uniform(-.10,.10)*strength
                points = [add(origin,add(add(mul(axis,extent*s),mul(lateral,extent*curve*s*s)),
                                        [0,0,extent*rise*s*s])) for s in (0,.5,1)]
                branch(f'{main["id"]}:s:{k}',main['id'],points,[r*.38,r*.20,r*.065],4,level)
    return branches


def diagnostics(branches):
    """Describe el desfase y la inclinación; no acredita naturalidad visual."""
    primary = [b for b in branches if b['parent_id']=='pine:trunk']
    levels = sorted({b['whorl'] for b in primary})
    spreads = []
    for level in levels:
        heights = [b['points_m'][0][2] for b in primary if b['whorl']==level]
        spreads.append(max(heights)-min(heights))
    slopes = []
    for b in primary:
        a,z = b['points_m'][0],b['points_m'][-1]
        slopes.append((z[2]-a[2])/math.hypot(z[0]-a[0],z[1]-a[1]))
    return {'root_height_spread_by_level_m':spreads,'primary_slope_min':min(slopes),
            'primary_slope_max':max(slopes),'descending_primaries':sum(s<0 for s in slopes),
            'ascending_primaries':sum(s>0 for s in slopes)}
