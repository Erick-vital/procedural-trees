#!/usr/bin/env python3
"""Seleccionar capturas verificadas de la rama de sauce, sin alterar recursos."""
import argparse
import json
from pathlib import Path
import shutil

from foliage_evidence import sheet
from review_pine_painted import sha, write

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    study, output = args.study.resolve(), args.output.resolve()
    manifest = json.loads((study/'manifest.json').read_text())
    assert manifest['passed'] and len(manifest['captures']) == 37
    assert all(sha(ROOT/p) == digest for p, digest in manifest['source_lock'].items())
    assert all(sha(study/'captures'/p) == digest for p, digest in manifest['captures'].items())
    assert all(sha(study/name/'branch.glb') == info['glb_sha256']
               for name, info in manifest['variants'].items())
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(study/'captures/crossed--perspective.png', output/'rama.png')
    shutil.copy2(study/'captures/wood--bark-close.png', output/'corteza.png')
    shutil.copy2(study/'review.jpg', output/'vistas.jpg')
    sheet(study, output/'orbita.jpg', 4,
          [[(f'captures/crossed--orbit-{i:02}.png', f'Órbita {i:02}') for i in range(j, j+4)]
           for j in range(0, 12, 4)])
    wood = ['front', 'side', 'perspective', 'back', 'top', 'below',
            'medium', 'far', 'dark', 'lateral', 'backlit', 'bark-close']
    sheet(study, output/'madera.jpg', 4,
          [[('captures/wood--'+v+'.png', 'Madera | '+v) for v in wood[j:j+4]] for j in range(0, 12, 4)])
    sheet(study, output/'luces-sombras.jpg', 2,
          [[('captures/crossed--'+v+'.png', v) for v in row]
           for row in [('lateral', 'backlit'), ('shadow-front', 'shadow-back')]])
    manifest['study'] = str(study.relative_to(ROOT))
    manifest['evidence_script_sha256'] = sha(Path(__file__))
    manifest['selected_images'] = {p.name: sha(p) for p in sorted(output.iterdir())
                                   if p.suffix in ('.png', '.jpg')}
    write(output/'verification.json', manifest)
    print('Evidencia seleccionada:', output)


if __name__ == '__main__':
    main()
