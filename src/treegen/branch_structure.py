"""F5: esqueleto Python experimental; no sustituye recetas históricas."""
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math

from pathlib import Path
from .seeds import derive_seed

VERSION = 'branch-structure-0.1.0'
RULE_VERSION = 'space-secondary-yaw-0.1.0'
YAW_OFFSETS_DEG = (0, -15, 15, -30, 30, -45, 45, -60, 60)


def add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def mul(a, s):
    return tuple(x*s for x in a)


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def length(a):
    return math.sqrt(dot(a, a))


@dataclass(frozen=True)
class Branch:
    id: str
    parent_id: str | None
    level: int
    points: tuple
    radii: tuple


@dataclass(frozen=True)
class BranchStructure:
    version: str
    seed: int
    branches: tuple

    def document(self):
        return asdict(self)

    def digest(self):
        return hashlib.sha256(json.dumps(self.document(), sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sample(branch, factor):
    """Interpolación por longitud, coincidente con Sample Curve de nodos."""
    sizes = [length(sub(b, a)) for a, b in zip(branch.points, branch.points[1:])]
    target = factor*sum(sizes)
    for i, size in enumerate(sizes):
        if target <= size or i == len(sizes)-1:
            t = min(1., max(0., target/size))
            return (add(branch.points[i], mul(sub(branch.points[i+1], branch.points[i]), t)),
                    branch.radii[i]*(1-t)+branch.radii[i+1]*t,
                    mul(sub(branch.points[i+1], branch.points[i]), 1/size))
        target -= size
    raise ValueError('Rama vacía')


def generate_structure(spec):
    # Blender incluye fastjsonschema; el orquestador usa jsonschema.
    schema = json.loads((Path(__file__).resolve().parents[2]/'schemas/tree-spec.schema.json').read_text())
    try:
        from .contracts import validate_spec
    except ModuleNotFoundError as exc:
        if exc.name != 'jsonschema':
            raise
        import fastjsonschema
        try:
            fastjsonschema.compile(schema)(spec)
        except fastjsonschema.JsonSchemaException as error:
            raise ValueError(str(error)) from error
    else:
        validate_spec(spec)
    for value in spec['parameters'].values():
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('Parámetros numéricos finitos obligatorios')
    if spec['algorithm_version'] != '0.4.0':
        raise ValueError('F5 parte de parámetros Q3 explícitos')
    p, seed = spec['parameters'], derive_seed(spec['seed'], 'structure')

    def random(identity, stream, low, high):
        fraction = derive_seed(seed, f'f5:{identity}:{stream}') / 2147483647
        return low+(high-low)*fraction

    h, radius = p['height_m'], p['base_radius_m']
    trunk = Branch('q3:trunk:0', None, 0,
        tuple((h*p['curvature']*(i/11)**2, 0., h*i/11) for i in range(12)),
        tuple(radius*(1-.93*i/11) for i in range(12)))
    branches = [trunk]

    def branch(identity, parent, level, root, r, size, yaw, tilt, bend, count):
        theta = math.radians(tilt)
        points = []
        for i in range(count):
            t = i/(count-1)
            outward = size*math.sin(theta)*(t-.22*t*t)
            up = size*(math.cos(theta)*t+bend*t*t)
            points.append(add(root, (outward*math.cos(yaw), outward*math.sin(yaw), up)))
        return Branch(identity, parent, level, tuple(points), tuple(r*(1-.93*i/(count-1)) for i in range(count)))

    n = p['primary_branches']
    phase = random('tree', 11, -math.pi, math.pi)
    primary_lengths = []
    for i in range(n):
        identity = f'q3:primary:{100+i}'
        step = i/max(n-1, 1)
        root, parent_radius, _ = sample(trunk, .33+.53*step)
        sector = i//2+(i%2)*math.ceil(n/2)
        yaw = phase+2*math.pi/n*(sector+p['asymmetry']*random(identity, 12, -.16, .16))
        size = h*p['branch_length_ratio']*(1.60-.42*step)*(1+p['asymmetry']*random(identity, 13, -.18, .12))
        tilt = max(18, min(96, p['inclination_deg']+8-12*step+random(identity, 14, -8, 8)))
        branches.append(branch(identity, trunk.id, 1, root, parent_radius*random(identity, 15, .72, .84),
            size, yaw, tilt, random(identity, 16, -.02, .12), 9))
        primary_lengths.append(size)
    if p['max_depth'] == 2:
        for i, parent in enumerate(branches[1:]):
            for k in range(3):
                index = 3*i+k
                identity = f'q3:secondary:{200+index}'
                root, parent_radius, tangent = sample(parent, .38+.46*k/2)
                side = -1 if index%2 == 0 else 1
                yaw = math.atan2(tangent[1], tangent[0])+side*random(identity, 21, .60, 1.05)
                tilt = max(20, min(92, math.degrees(math.acos(max(-1, min(1, tangent[2]))))+random(identity, 22, -14, 8)))
                branches.append(branch(identity, parent.id, 2, root, parent_radius*random(identity, 23, .58, .70),
                    primary_lengths[i]*(.50-.20*k/2), yaw, tilt, random(identity, 24, .04, .16), 7))
    result = BranchStructure(VERSION, seed, tuple(branches))
    validate_structure(result)
    return result


def validate_structure(structure):
    if structure.version != VERSION or type(structure.seed) is not int or not 0 <= structure.seed < 2147483647:
        raise ValueError('Versión o semilla inválida')
    if not 2 <= len(structure.branches) <= 49:
        raise ValueError('Cantidad de ramas fuera de límites')
    seen = {}
    for b in structure.branches:
        if b.id in seen or type(b.level) is not int or b.level not in (0, 1, 2):
            raise ValueError('ID o nivel inválido')
        if not 2 <= len(b.points) <= 12 or len(b.radii) != len(b.points):
            raise ValueError('Muestras inválidas')
        if any(len(v) != 3 or any(type(x) not in (float, int) or not math.isfinite(x) for x in v) for v in b.points):
            raise ValueError('Coordenadas inválidas')
        if any(type(r) not in (float, int) or not math.isfinite(r) or not 0 < r <= 5 for r in b.radii):
            raise ValueError('Radios inválidos')
        if any(length(sub(v, u)) <= 1e-8 for u, v in zip(b.points, b.points[1:])):
            raise ValueError('Segmento degenerado')
        if b.level == 0:
            if seen or b.parent_id is not None:
                raise ValueError('Raíz inválida')
        else:
            if b.parent_id not in seen or seen[b.parent_id].level != b.level-1:
                raise ValueError('Jerarquía inválida')
            parent = seen[b.parent_id]
            if min(segment_distance(b.points[0], b.points[0], u, v)[0] for u, v in zip(parent.points, parent.points[1:])) > 1e-7:
                raise ValueError('Unión separada')
        seen[b.id] = b
    return structure


def segment_distance(a, b, c, d):
    """Distancia exacta entre segmentos finitos, incluidos puntos y paralelos."""
    u, v, w = sub(b, a), sub(d, c), sub(a, c)
    aa, bb, cc, dd, ee = dot(u, u), dot(u, v), dot(v, v), dot(u, w), dot(v, w)
    if aa <= 1e-20:
        s, t = 0., max(0., min(1., ee/cc)) if cc > 1e-20 else 0.
    elif cc <= 1e-20:
        s, t = max(0., min(1., -dd/aa)), 0.
    else:
        denominator = aa*cc-bb*bb
        s = max(0., min(1., (bb*ee-cc*dd)/denominator)) if denominator > 1e-20 else 0.
        t = (bb*s+ee)/cc
        if t < 0:
            t, s = 0., max(0., min(1., -dd/aa))
        elif t > 1:
            t, s = 1., max(0., min(1., (bb-dd)/aa))
    return length(sub(add(a, mul(u, s)), add(c, mul(v, t)))), s, t
