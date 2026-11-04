"""Encaje O3: esfera interior conservadora frente a caras y extremos del padre."""
from .oak_growth_mesh import tube
from .surface_evaluation import point_triangle_distance


def fit_root_rings(branches):
    index={b['id']:b for b in branches};surfaces={}
    # Orden topológico, también para los abanicos añadidos después de la base.
    for branch in sorted(branches,key=lambda b:b['order']):
        if branch['parent_id'] is not None:
            parent=index[branch['parent_id']];mesh=surfaces[parent['id']];root=branch['points'][0]
            distances=[]
            for face in mesh['polygons']:
                for j in range(1,len(face)-1):
                    distances.append(point_triangle_distance(root,*(mesh['vertices'][k] for k in (face[0],face[j],face[j+1]))))
            # El centro nace dentro del tubo. La esfera de radio a la superficie
            # también queda dentro, incluida la tapa; margen por triangulación.
            limit=min(distances)*.85
            scale=min(1.,limit/branch['radii'][0])
            branch['radii']=[r*scale for r in branch['radii']]
            branch['join_radius_scale']*=scale
            branch['surface_join_radius_scale']=scale
        surfaces[branch['id']]=tube(branch)
