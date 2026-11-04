"""OF1: exportación de rama y testigo O5; sin follaje en el árbol completo."""
import json
from pathlib import Path
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
from branch_variants import main as export


def main(path):
    job=json.loads(Path(path).read_text());index={b['id']:b for b in job['branches']};records=[]
    for branch in job['branches']:
        if branch['parent_id'] not in index:continue
        parent=index[branch['parent_id']]['mesh'];tree=BVHTree.FromPolygons(parent['vertices'],parent['polygons']);worst=-1e9
        for point in branch['mesh']['vertices'][:branch['sides']]:
            q,n,_,_=tree.find_nearest(Vector(point));worst=max(worst,(Vector(point)-q).dot(n))
        if worst>1e-5:raise ValueError('Anillo O5 fuera de padre')
        records.append({'id':branch['id'],'max_signed_distance_m':worst})
    (Path(job['output'])/'wood-joins.json').write_text(json.dumps({'passed':True,'joins':records},indent=2)+'\n')
    export(path)

if __name__=='__main__':main(sys.argv[sys.argv.index('--')+1])
