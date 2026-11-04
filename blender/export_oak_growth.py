"""Adaptador de exportación O1: auditar uniones reales y reutilizar corteza pintada."""
from pathlib import Path
import json
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from branch_variants import main as export


def main(path):
    job=json.loads(Path(path).read_text());by_id={b['id']:b for b in job['branches']};audits=[]
    for b in job['branches']:
        if b['parent_id'] is None:continue
        parent=by_id[b['parent_id']]['mesh'];tree=BVHTree.FromPolygons(parent['vertices'],parent['polygons'])
        sides=b['sides'];worst=-1e9
        for point in b['mesh']['vertices'][:sides]:
            position,normal,_,distance=tree.find_nearest(Vector(point));signed=(Vector(point)-position).dot(normal);worst=max(worst,signed)
        if worst>1e-5:raise ValueError(f'Anillo hijo fuera de su padre: {b["id"]} ({worst})')
        audits.append({'id':b['id'],'max_signed_distance_m':worst})
    out=Path(job['output']);(out/'joins-audit.json').write_text(json.dumps({'passed':True,'joins':audits},indent=2)+'\n')
    export(path)

if __name__=='__main__':main(sys.argv[sys.argv.index('--')+1])
