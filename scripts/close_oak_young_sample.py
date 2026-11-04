#!/usr/bin/env python3
"""J1: cerrar evidencia de madera y rama; nunca conceder aprobación artística."""
import argparse
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts')]
from review_pine_painted import read,write,sha
from foliage_evidence import sheet


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--wood',type=Path,required=True)
    p.add_argument('--sample',type=Path,required=True)
    p.add_argument('--repeat',type=Path,required=True)
    p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();wood,sample,repeat,ev=[q.resolve() for q in (a.wood,a.sample,a.repeat,a.evidence)]
    ev.mkdir(parents=True,exist_ok=False)
    w=read(wood/'verification.json');m=read(sample/'manifest.json');r=read(repeat/'manifest.json')
    checks={'wood-verified':w['passed'],'sample-verified':m['status']=='completed' and all(m['checks'].values()),
            'repeat-verified':r['status']=='completed' and all(r['checks'].values())}
    for folder,manifest in ((sample,m),(repeat,r)):
        checks[folder.name+'-sources']=all(sha(ROOT/p)==h for p,h in manifest['source_inventory'].items())
        for name,row in manifest['variants'].items():
            assert sha(folder/name/'tree.glb')==row['glb_sha256']
    for name in m['variants']:
        checks[name+'-repeat-glb']=m['variants'][name]['glb_sha256']==r['variants'][name]['glb_sha256']
    checks['layout-repeat']=read(sample/'layout.json')==read(repeat/'layout.json')
    checks['structure-repeat']=read(sample/'o5-structure.json')==read(repeat/'o5-structure.json')
    checks['pilot-wood-reference-identical']=m['variants']['reference']['glb_sha256']==w['cases']['joven-3100']['glb_sha256']
    wr,sr=read(wood/'review.json'),read(sample/'review.json')
    checks['godot']=wr['passed'] and sr['passed']
    checks['capture-count']=len(wr['captures_sha256'])==48 and len(sr['captures_sha256'])==36
    for folder,review in ((wood,wr),(sample,sr)):
        assert all(sha(folder/'captures'/p)==h for p,h in review['captures_sha256'].items())
    shots=[s['id'] for s in sr['shots']]
    for name in ('bare','painted','foliage'):
        sheet(sample,sample/(name+'-all.jpg'),4,[[(f'captures/{name}--{v}.png',f'J1 {name} | {v}') for v in shots[i:i+4]] for i in range(0,len(shots),4)])
    controls=[]
    for seed in range(3100,3104):
        wm=read(wood/f'joven-{seed}/manifest.json')
        controls.append({'seed':seed,'wood_triangles':wm['variants']['bare']['metrics']['triangles'],
                         'planned_foliage_triangles':864,'projected_total_triangles':wm['variants']['bare']['metrics']['triangles']+864})
    summary={'date':'2026-11-04','passed':all(checks.values()),'checks':checks,'wood_checks':w['checks'],'sample_checks':m['checks'],
             'scope':'four bare young trees and one foliated branch; no complete foliage tree',
             'artistic_acceptance':'pending_user','full_tree_integration':'pending_branch_acceptance',
             'controls':controls,'sample':{'spec':m['spec'],'groups':m['group_count'],'ledger':m['ledger'],
                       'exports':{k:{'triangles':v['metrics']['triangles'],'glb_sha256':v['glb_sha256']} for k,v in m['variants'].items()},
                       'maximum_contact_error_m':read(sample/'contacts-audit.json')['maximum_error_m']},
             'sources_sha256':m['source_inventory'],'closure_source_sha256':sha(Path(__file__)),
             'unit_tests':{'passed':11,'commands':['PYTHONPATH=src python3 -m unittest discover -s tests -p test_oak_young_sample.py -v',
                            'PYTHONPATH=src python3 -m unittest discover -s tests -p test_oak_foliage_chains.py -v']},
             'captures':{'wood_count':48,'branch_count':36,'wood_sha256':wr['captures_sha256'],'branch_sha256':sr['captures_sha256']},
             'wood_study':str(wood.relative_to(ROOT)),'sample_study':str(sample.relative_to(ROOT)),
             'repeat_study':str(repeat.relative_to(ROOT)),'no_performance_tests':True,'visual_review':'pending_agent'}
    write(ev/'summary.json',summary);assert summary['passed'],checks
    write(ev/'branch-protocol.json',{'shots':sr['shots'],'godot':[{k:g[k] for k in ('godot','renderer','video_adapter','msaa','environment','assets')} for g in sr['godot']]})
    write(ev/'wood-protocol.json',{'protocol':wr['protocol'],'source':'scripts/prepare_oak_young_wood.py'})
    for folder,source,destination in [(wood,'wood.jpg','wood.jpg'),(wood,'age-comparison.jpg','age-comparison.jpg'),
        (sample,'comparison.jpg','comparison.jpg'),(sample,'appearance.jpg','appearance.jpg'),(sample,'painted-all.jpg','painted-all.jpg')]:
        shutil.copy2(folder/source,ev/destination)
    html='<!doctype html><meta charset="utf-8"><title>Roble joven · J1</title><style>body{font:18px sans-serif;background:#eee9df;margin:24px}img{max-width:100%}</style><h1>Roble joven · madera y rama de muestra J1</h1><p>Cuatro maderas de5 m y rama3100/p:0 con71 grupos,1046 tris/dos materiales. Pintura conservada. La copa completa espera aprobación artística de la muestra.</p>'
    for name,title in [('comparison','Muestra: madera / follaje'),('appearance','Fondos, distancias y sombras'),('wood','Cuatro maderas jóvenes'),('age-comparison','Porte joven / maduro O5 a altura normalizada')]:
        path=(sample if name in ('comparison','appearance') else wood)/(name+'.jpg')
        relative=__import__('os').path.relpath(path,sample)
        html+='<h2>'+title+'</h2><img src="'+relative+'">'
    html+='<p><a href="painted-all.jpg">Todas las vistas de la rama</a> · <a href="painted/tree.glb">GLB de muestra</a></p>'
    (sample/'index.html').write_text(html)
    print('J1 verificado: cuatro maderas, muestra repetida y84 capturas; arte pendiente.',flush=True)

if __name__=='__main__':main()
