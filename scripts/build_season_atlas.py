#!/usr/bin/env python3
"""T2: derivar atlas compatibles desde los horneados históricos congelados."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from treegen.season_atlas import VERSION, compatible_pair, extend_rgb

SUMMER = ROOT/'assets/roble-pintado/v0.3.0/foliage.png'
AUTUMN = ROOT/'assets/roble-otono-pintado/v0.1.0/crossed-atlas.png'
TEMPLATES = ROOT/'assets/roble-pintado/v0.3.0/templates.json'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def count(mask): return sum(mask.histogram()[1:])
def write(p, value): p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def build(output):
    templates = json.loads(TEMPLATES.read_text())
    sm = json.loads((SUMMER.parent/'manifest.json').read_text())
    am = json.loads((AUTUMN.parent/'manifest.json').read_text())
    if (sha(SUMMER) != sm['atlas_sha256'] or sha(AUTUMN) != am['files']['crossed-atlas.png']['sha256'] or
            sha(TEMPLATES) != am['templates']['sha256'] or sha(TEMPLATES) != sm['templates_sha256'] or
            (templates['grid'],templates['tile_px'],templates['usable'],len(templates['templates'])) != (5,400,.92,8)):
        raise ValueError('Fuentes/plantillas históricas incompatibles')
    summer, autumn = Image.open(SUMMER), Image.open(AUTUMN)
    if summer.size != (2000,2000): raise ValueError('Resolución histórica distinta')
    pair = compatible_pair(summer, autumn)
    output.mkdir(parents=True, exist_ok=False)
    files = {}
    for season, im in zip(('summer','autumn'), pair):
        for treatment, result in [('common',im),('padded',extend_rgb(im,400,16))]:
            name = season+'-'+treatment+'.png'
            result.save(output/name, compress_level=9)
            assert result.getchannel('A').tobytes() == summer.getchannel('A').tobytes()
            visible = im.getchannel('A').point(lambda a: 255 if a else 0)
            delta = ImageChops.difference(result.convert('RGB'), im.convert('RGB'))
            assert not ImageChops.multiply(delta, Image.merge('RGB',(visible,)*3)).getbbox()
            files[name] = {'sha256':sha(output/name), 'bytes':(output/name).stat().st_size,
                           'rgba_sha256':hashlib.sha256(result.tobytes()).hexdigest()}
    sa, aa = summer.getchannel('A'), autumn.getchannel('A')
    missing = ImageChops.multiply(sa.point(lambda a:255 if a else 0), aa.point(lambda a:0 if a else 255))
    visible = ImageChops.multiply(sa.point(lambda a:255 if a>=128 else 0), aa.point(lambda a:0 if a else 255))
    # Demostrar identidad RGB sobre toda pintura originalmente no transparente.
    keep = aa.point(lambda a:255 if a else 0)
    diff = ImageChops.difference(pair[1].convert('RGB'),autumn.convert('RGB'))
    assert not ImageChops.multiply(diff,Image.merge('RGB',(keep,)*3)).getbbox()
    report = {'version':VERSION, 'status':'experimental_art_pending', 'species':'roble_copa_ancha@2.2.0',
              'grid':5,'tile_px':400,'used_cells':24,'size':[2000,2000],'usable':.92,
              'mask_source':'summer','alpha_sha256':hashlib.sha256(sa.tobytes()).hexdigest(),
              'alpha_different_texels':count(ImageChops.difference(sa,aa)),
              'cutoff_mask_different_texels':count(ImageChops.difference(sa.point(lambda a:255 if a>=128 else 0),aa.point(lambda a:255 if a>=128 else 0))),
              'newly_exposed_rgb_repaired':count(missing),'newly_exposed_rgb_at_cutoff':count(visible),
              'paint_rgb_preserved_where_original_alpha_nonzero':True,
              'padding':{'radius_px':16,'connectivity':8,'cell_bounded':True,'alpha_unchanged':True,'visible_rgb_unchanged':True,
                         'selection':'pending_visual_review','implementation':'original; Pillow public operations; no copied MIT code'},
              'inputs':{str(p.relative_to(ROOT)):sha(p) for p in (SUMMER,AUTUMN,TEMPLATES,SUMMER.parent/'manifest.json',AUTUMN.parent/'manifest.json')},
              'sources':{str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),ROOT/'src/treegen/season_atlas.py')},
              'files':files,'memory':{'rgba8_two_atlases_bytes':32000000,'rgba8_two_atlases_with_mips_bytes':2*4*sum(max(1,2000//(2**level))**2 for level in range(11)),
                                    'foliage_texture_samples_future_blend':2,'note':'Estimación RGBA8 sin compresión; no medida GPU. Corteza aparte e intacta.'}}
    write(output/'manifest.json',report)
    return report

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(build(args.output.resolve()),ensure_ascii=False,indent=2))
