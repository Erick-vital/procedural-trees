# Robles con ramificación integrada

`branch-tree-0.1.0` reconstruye un árbol completo desde fuentes y conserva la copa
pintada de la base Python F5. Sustituye secundarias y soportes radiales por redes
bifurcadas conectadas al tronco y a sus ramas principales. No cambia recetas ni
alias históricos, ni activa F6 o transiciones estacionales.

```sh
PYTHONPATH=src python3 -m treegen generate-branch-tree \
  configs/branch-tree/0.1.0.json \
  --profile joven --base-seed 1003 --canopy-seed 17 --paint-seed 2718 \
  --output artifacts/mi-roble-ramificado
```

El directorio debe ser nuevo. Perfiles admitidos: `joven`, `adulto`, `viejo` y
`viejo_referencia`. Las tres semillas son obligatorias; se rechazan controles
extra y entradas incompatibles antes de generar geometría. Blender debe estar
instalado en la ruta del ejecutor o indicado por `BLENDER_BIN`.

- `simple/tree.glb`: árbol con follaje y madera interior simplificada R3.
- `bare/tree.glb`: árbol sin hojas, con la simplificación R2 elegida por el usuario.
- `full/tree.glb`: control R2 con hojas, para comparar la reducción adicional.
- `source/`: fuente F5 regenerada; `foliage-before/` y `foliage-after/`: controles.
- `manifest.json`: entradas resueltas, versiones, hashes, métricas y auditorías.
- `networks/`: decisiones de poda, contracciones y muestras de oclusión por rama.

No basta con ocultar las hojas de `simple`: para el estado desnudo se elige `bare`.
Ambos son GLB independientes; no hay conmutación automática entre estaciones.
La generación completa se limita a 120 segundos y cada exportación a 6999 tris.
264 grupos de tres láminas, dos materiales con follaje y uno sin hojas; atlas
compartidos y pintura conservada. Las raíces de las redes quedan dentro de sus
ejes principales; las piezas se superponen, sin prometer una malla soldada.

R3 integrada usa cobertura alfa 217 y catorce ángulos adicionales conservadores,
además de los 74 del clasificador de la muestra. La muestra R3 previa usaba alfa
128: se conserva como experimento histórico; el árbol completo puede retener
algo más de madera para proteger los huecos visibles. No se cambian las texturas
ni el umbral de renderizado .5. No se atribuyen mejoras de FPS sin medición.

## Reproducir la matriz y sus capturas

```sh
python3 scripts/verify_branch_trees.py --output artifacts/mi-lote-r4
python3 scripts/verify_branch_trees.py --output artifacts/mi-lote-r4 --stage review
```

Matriz: `configs/verification/branch-tree-v1.json`; se puede elegir `--case joven-03`.
La revisión requiere Godot con interfaz gráfica. Compara R2/R3 con copa, estructura
anterior/nueva sin hojas, fuente/candidata con copa y máscaras de follaje/madera.
Las métricas y los pases automáticos no sustituyen la valoración artística.
