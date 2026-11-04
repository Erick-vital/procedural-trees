"""R2: oclusión acotada de madera contra láminas con alfa real."""
import json
import math
from pathlib import Path
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src')]
from treegen.branch_visibility import surface_samples,directions


def main(path):
    job=json.loads(Path(path).read_text());folder=Path(job['output']);network=job['network'];foliage=job['foliage']
    assert len(network['edges'])<=720 and len(foliage)<=1080
    alpha=Path(job['alpha_path']).read_bytes();w,h=job['alpha_size'];assert len(alpha)==w*h and w<=2048 and h<=2048
    vertices=[];faces=[];uvs=[]
    for mesh in foliage:
        offset=len(vertices);vertices.extend(mesh['vertices'])
        for face in mesh['polygons']:
            assert len(face)==3
            faces.append(tuple(offset+i for i in face));uvs.append([mesh['uv'][i] for i in face])
    bvh=BVHTree.FromPolygons(vertices,faces,all_triangles=True,epsilon=0.)
    vectors=[Vector(p) for p in vertices];rays=hits=0

    def opaque(face,location):
        a,b,c=[vectors[i] for i in faces[face]];v0=b-a;v1=c-a;v2=location-a
        d00=v0.dot(v0);d01=v0.dot(v1);d11=v1.dot(v1);d20=v2.dot(v0);d21=v2.dot(v1)
        denom=d00*d11-d01*d01
        if abs(denom)<1e-16:return False
        t=(d11*d20-d01*d21)/denom;s=(d00*d21-d01*d20)/denom
        uvs_face=uvs[face];uv=[uvs_face[0][k]*(1-t-s)+uvs_face[1][k]*t+uvs_face[2][k]*s for k in range(2)]
        x=max(0,min(w-1,uv[0]*(w-1)));y=max(0,min(h-1,(1-uv[1])*(h-1)))
        x0=int(x);y0=int(y)
        # Exigir cobertura fuerte en cuatro texeles; las dudas conservan madera.
        return min(alpha[yy*w+xx] for yy in (y0,min(h-1,y0+1)) for xx in (x0,min(w-1,x0+1)))>=217

    def hidden(point,direction):
        nonlocal rays,hits
        rays+=1;d=Vector(direction);origin=Vector(point)+d*.00002
        for _ in range(64):
            location,normal,index,distance=bvh.ray_cast(origin,d,100.)
            if index is None:return False
            hits+=1
            if opaque(index,location):return True
            origin=location+d*.00002
        # Una consulta truncada no permite eliminar madera.
        return False

    exposed=[];records={};training=directions();reserved=directions(15.)
    for edge in network['edges']:
        samples=surface_samples(edge['mesh']);visible=None
        for p in samples:
            for d in training:
                if not hidden(p,d):visible={'point':p,'direction':d};break
            if visible:break
        records[edge['id']]={'sample_count':len(samples),'exposed':visible is not None,'witness':visible}
        if visible:exposed.append(edge['id'])
    result={'version':'alpha-bvh-visibility-0.1.0','alpha_cutoff_conservative':217/255,
            'alpha_image_origin':'top_left','training_directions':training,'reserved_directions':reserved,
            'exposed_ids':exposed,'edges':records,'rays':rays,'foliage_hits':hits}
    # Verificación angular independiente para todos los tramos inicialmente ocultos.
    # Si aparece exposición, protegerlo también; registrar promoción explícita.
    promoted=[]
    for edge in network['edges']:
        if edge['id'] in exposed:continue
        found=False
        for p in surface_samples(edge['mesh']):
            for d in reserved:
                if not hidden(p,d):found=True;break
            if found:break
        if found:promoted.append(edge['id'])
    result.update(reserved_promoted_ids=promoted,protected_exposed_ids=sorted(exposed+promoted),
                  total_rays=rays,total_foliage_hits=hits)
    (folder/'visibility.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Visibles:',len(exposed),'promovidos:',len(promoted),'total:',len(network['edges']),flush=True)


if __name__=='__main__':main(sys.argv[sys.argv.index('--')+1])
