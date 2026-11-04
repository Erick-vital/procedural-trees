"""Auditar raíces de redes dentro de su madera principal y exportar modos R4."""
import json
from pathlib import Path
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from branch_variants import main as export


def main(path):
    job=json.loads(Path(path).read_text());majors={b['id']:b['mesh'] for b in job['majors']};records=[]
    for part in job['root_networks']:
        parent=majors[part['id']];bvh=BVHTree.FromPolygons(parent['vertices'],parent['polygons'])
        for edge in part['edges']:
            if edge['parent'] is not None:continue
            for point in edge['mesh']['vertices'][:3]:
                position,normal,_,distance=bvh.find_nearest(Vector(point))
                signed=(Vector(point)-position).dot(normal)
                if signed>1e-5:raise ValueError(f'Raíz fuera de madera {part["id"]}: {signed}')
                records.append({'major':part['id'],'edge':edge['id'],'signed_distance_m':signed})
    out=Path(job['output']);(out/'roots-audit.json').write_text(json.dumps({'passed':True,'records':records,'max_outside_m':max([0.]+[r['signed_distance_m'] for r in records])},indent=2)+'\n')
    export(path)


if __name__=='__main__':main(sys.argv[sys.argv.index('--')+1])
