"""Pruebas analíticas de oclusión alfa para el clasificador R2."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'blender')]
from classify_branch_visibility import main as classify


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    # Una caja cerrada envuelve toda la pequeña superficie de madera.
    v=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]]
    faces=[[0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
    triangles=[]
    for a,b,c,d in faces:triangles.extend([[a,b,c],[a,c,d]])
    mesh={'vertices':[[0,0,0],[.1,0,0],[0,.1,0]],'polygons':[[0,1,2]]}
    network={'edges':[{'id':'test','mesh':mesh}]}
    foliage=[{'vertices':v,'polygons':triangles,'uv':[[.5,.5]]*8}]
    results={}
    for label,alpha,expected in [('opaque',255,False),('transparent',0,True),('uncertain_coverage',200,True)]:
        folder=output/label;folder.mkdir();path=folder/'alpha.bin';path.write_bytes(bytes([alpha]*4))
        job={'output':str(folder),'network':network,'foliage':foliage,'alpha_path':str(path),'alpha_size':[2,2]}
        input_path=folder/'input.json';input_path.write_text(json.dumps(job));classify(input_path)
        report=json.loads((folder/'visibility.json').read_text());actual=bool(report['protected_exposed_ids'])
        assert actual==expected,(label,actual,expected)
        results[label]={'expected_exposed':expected,'actual_exposed':actual,'passed':True}
    (output/'verification.json').write_text(json.dumps({'passed':True,'cases':results},indent=2)+'\n')


if __name__=='__main__':main(sys.argv[sys.argv.index('--')+1])
