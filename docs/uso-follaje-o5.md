# Muestra de follaje sobre madera O5

OF1 prepara una rama aislada con la pintura existente. No modifica recetas ni
exporta follaje sobre el árbol completo. O5 desnuda sigue como referencia aceptada.
[Resultado, presupuesto y límites](evidence/oak-foliage/of1/informe.md).

```sh
python3 scripts/prepare_oak_foliage_sample.py \
  --config configs/oak-foliage/sample-v1.json --output artifacts/mi-rama-of1
```

El directorio debe ser nuevo. `--stage generate` exporta y verifica geometría;
`--stage review` captura una generación completada en Godot. Se requiere entorno
gráfico; la verificación sin imágenes no acredita aceptación visual.

Configuración estricta `oak-foliage-sample-0.1.0`: preset O5 del catálogo,
semillas `seed`/`layout_seed`/`paint_seed`, primaria `branch_id`, cupo `tree_groups`
24–264, escala de grupo/altura .06–.16 y radio protegido/altura .25–.40.
La configuración revisada es maduro 3100/p:0, 216 grupos globales, escala .10 y
núcleo .30. Cambiar entradas puede provocar un rechazo por capacidad de un eje;
no certifica edades ni semillas nuevas por completar esta muestra.

`layout.json` registra solo los grupos de la rama, anclajes, padre, recorrido,
plantilla y orientación; `ledger` reparte cupos por todas las primarias.
Seis tris por grupo, sin conectores nuevos. La muestra consume su parte del cupo;
la suma proyectada de madera completa y follaje se valida contra 6999 y la reserva
1584 antes de exportar. No es una certificación visual de una copa inexistente.

Salidas: `bare/tree.glb`, `painted/tree.glb`, `foliage/tree.glb` y sus `.blend`;
`reference/tree.glb` es solo el testigo de madera completa O5 sin hojas para
regresión. `contacts-audit.json` mide contacto sobre GLB; PNG/UV del tallo opaco
se conservan. `manifest.json`, `review.json` y `index.html` reúnen procedencia y
capturas. El cierre selecciona evidencia y deja aceptación artística pendiente.

## OF2: tres variantes de masas sobre la misma rama

`oak-foliage-sample-0.2.0` añade `mass_variant` A/B/C; conserva OF1 y usa los
mismos atlas. Configuraciones `configs/oak-foliage/chains-{A,B,C}.json`, misma
rama y64 grupos. A concentra extremos; B usa continuidad intermedia con puentes;
C separa centros y deja más huecos. Candidatos de segmento, masas y descartes se
registran en cada `layout.json`. Los enlaces de masa no son geometría adicional.

```sh
python3 scripts/compare_oak_foliage_chains.py --output artifacts/mi-of2
```

El directorio debe ser nuevo. `--stage generate` prepara las tres exportaciones;
`--stage review` captura ese estudio. La revisión usa el testigo OF1 histórico
en `artifacts/oak-foliage/of1-rama-04`; si falta, generarlo con la configuración
OF1 y `--stage generate` antes de comparar. Cámaras/luz/escala iguales, máscaras
de follaje y madera como indicadores proyectados; no son prueba de naturalidad.
Solo rama madura revisada, sin integrar copa ni certificar otras edades.
[Informe OF2](evidence/oak-foliage/of2/informe.md).

## OF3: piloto de copa madura con B revisada

El usuario eligió B y autorizó probar el maduro 3100 completo con tres cambios:
expansión lateral alrededor de ramas reales, reparto entre bifurcaciones por
vigor/exposición y masas anchas/alargadas/pequeñas de enlace. Nuevo contrato
`oak-foliage-canopy-0.3.0`, separado de OF1/OF2; solo admite el preset maduro O5.
No es promoción de receta ni certificación de otros perfiles.

```sh
python3 scripts/prepare_oak_foliage_canopy.py \
  --config configs/oak-foliage/canopy-B.json --output artifacts/mi-of3
```

Directorio nuevo. También admite `--stage generate` o `--stage review`.
Genera madera completa, B original aplicada, B revisada, follaje aislado y las
dos ramas p:0. `painted/tree.glb` y `painted/tree.blend` son las salidas revisadas;
`index.html` compara cámaras y luz comunes. Blender/Godot requieren el entorno
externo documentado cuando audio/sockets fallan dentro del sandbox.

216 grupos/1296 tris de follaje y 3714 de madera: **5010 tris/dos materiales**.
Conserva madera O5 y atlas; reserva central de radio 0.30H comprobada sobre caras
completas. Configuración estricta: sin `branch_id` ni `mass_variant`; se rechaza
un cupo imposible sin invadir núcleo, cambiar contactos o añadir triángulos.

[Verificación y comandos de repetición](evidence/oak-foliage/of3/informe.md):
293 pruebas, 48 checks, seis GLB repetidos exactos y 46 capturas inspeccionadas.
**Copa todavía rala; arte pendiente del usuario**, con columnas locales y tarjetas
de canto desde arriba. Galería: `artifacts/oak-foliage/of3-maduro-02/index.html`.

## OF4: llenado periférico con 5010 triángulos

El usuario revisó OF3 como demasiado rala. La nueva prueba mantiene madera,
pintura, núcleo de radio 0.30H, 216 grupos y 5010 tris, con reglas generales:
reparto entre primarias menos concentrado, cobertura de segmentos menos poblados,
ramas descendentes portantes y masas de mayor alcance. Cerca del núcleo limita
extensión y comprueba caras completas; no mueve anclajes fuera de madera.

```sh
python3 scripts/prepare_oak_foliage_peripheral.py \
  --config configs/oak-foliage/peripheral-B.json --output artifacts/mi-of4
python3 scripts/oak_foliage_peripheral_masks.py --study artifacts/mi-of4
```

Directorios nuevos. Contrato `oak-foliage-canopy-0.4.0`, solo preset maduro O5;
OF3 permanece disponible con su script/configuración anteriores. Revisión
comparada contra OF3 regenerada, cámaras/luz/escala comunes; `painted/tree.glb`
y `painted/tree.blend` contienen la candidata, `index.html` la comparación.
[Informe con cierre/repetición](evidence/oak-foliage/of4/informe.md): 299 pruebas,
55 checks, seis GLB repetidos exactos, 46 capturas + ocho máscaras inspeccionadas.

La pintura es idéntica pero cambia tamaño aparente de algunas hojas; el área de
rectángulos transparentes crece. Sin medición FPS. Mejora cobertura periférica,
con huecos entre brazos y cantos superiores aún visibles; **arte pendiente**.
Galería: `artifacts/oak-foliage/of4-maduro-01/index.html`.

## OF5: puentes discretos y jerarquía sobre OF4

Tras la valoración favorable de OF4, esta candidata reasigna hasta 18 grupos:
diez puentes pequeños, seis retrocesos de punta y dos ajustes interiores en el
piloto 3100. Tres conjuntos espaciales dirigen qué huecos conectar; 198 grupos
conservan geometría exacta. No añade madera, pintura ni grupos: 216/5010 tris,
dos materiales y núcleo 0.30H. OF4 se conserva y no hay retoques por semilla.

```sh
python3 scripts/prepare_oak_foliage_macro.py \
  --config configs/oak-foliage/macro-B.json --output artifacts/mi-of5
python3 scripts/oak_foliage_macro_masks.py --study artifacts/mi-of5
```

Directorios nuevos; contrato `oak-foliage-canopy-0.5.0`, solo preset maduro O5.
`painted/tree.glb`, `painted/tree.blend` e `index.html` contienen candidata,
fuente y comparación con OF4. [Repetición/cierre](evidence/oak-foliage/of5/informe.md):
305 pruebas, 59 checks, seis GLB repetidos exactos y 46 capturas + ocho máscaras
inspeccionadas. **Cambio visual discreto, macromasas aún no resueltas**; arte
pendiente, densidad casi idéntica. Galería: `artifacts/oak-foliage/of5-maduro-02/index.html`.

## OF6: volúmenes geométricos de copa

El contrato `oak-foliage-canopy-0.6.0` conserva OF5 como referencia. Orienta
suavemente los grupos hacia el eje común de su conjunto y amplía uniformemente
las interfaces entre masas. No mueve los 216 anclajes ni cambia proporciones de
plantillas/PNG/madera; puntas sin aumentar y caras completas fuera del núcleo.
Piloto maduro 3100: 216 grupos/5010 tris/dos materiales.

```sh
python3 scripts/prepare_oak_foliage_volume.py \
  --config configs/oak-foliage/volume-B.json --output artifacts/mi-of6
python3 scripts/oak_foliage_volume_masks.py --study artifacts/mi-of6
```

Directorios nuevos; conserva `--stage generate/review`. `painted/tree.glb`,
`painted/tree.blend` e `index.html` contienen candidata, fuente y comparación con
OF5. [Repetición/cierre y límites](evidence/oak-foliage/of6/informe.md): 310 pruebas,
59 checks, seis GLB repetidos exactos, 46 capturas + ocho máscaras inspeccionadas.
Más unión frente/perspectiva; arriba todavía quedan huecos y cantos. Mayor escala
aparente/área alfa, sin FPS medidos. **Arte pendiente**, sin nuevas edades/recetas.
Galería: `artifacts/oak-foliage/of6-maduro-03/index.html`.

## OF7: vista superior con área de follaje constante

`oak-foliage-canopy-0.7.0` reorienta grupos con láminas casi verticales usando
tríadas inclinadas fijas y muestras opacas del atlas original. Conserva puentes y
marcos previos útiles; no depende de la cámara ni tiene retoques por semilla.
216 grupos/5010 tris/dos materiales, madera, pintura, tamaños y anclajes intactos;
caras completas fuera del núcleo 0.30H. No repinta ni añade hojas.

```sh
python3 scripts/prepare_oak_foliage_top.py \
  --config configs/oak-foliage/top-B.json --output artifacts/mi-of7
python3 scripts/oak_foliage_top_masks.py --study artifacts/mi-of7
```

Directorio nuevo; admite `--stage generate/review`. `painted/tree.glb` y
`painted/tree.blend` contienen candidata y fuente. `index.html` compara OF6/OF7,
incluidas vista superior y dos superiores oblicuas. [Repetición/cierre y límites](evidence/oak-foliage/of7/informe.md):
316 pruebas, 61 checks, seis GLB repetidos exactos, 50 capturas + ocho máscaras
inspeccionadas. Mejora superior con menos cantos, a costa de algunas uniones
frontales. **Arte pendiente**; OF6 sigue disponible. Galería:
`artifacts/oak-foliage/of7-maduro-04/index.html`.

## OF8: recuperar frontal conservando OF7

El usuario autorizó un pequeño aumento de tris si era necesario, con máximo6999.
`oak-foliage-canopy-0.8.0` conserva OF7 y añade una complementaria inclinada solo
en grupos que pierden huella opaca lateral frente a OF6. Selección por ocho
azimuts uniformes, sin retoques por semilla ni consulta de cámara Godot.

```sh
python3 scripts/prepare_oak_foliage_balance.py \
  --config configs/oak-foliage/balance-B.json --output artifacts/mi-of8
python3 scripts/oak_foliage_balance_masks.py --study artifacts/mi-of8
```

Directorios nuevos; `--stage generate/review`. Candidata en `painted/tree.glb` y
`painted/tree.blend`; `index.html` compara OF6/OF7/OF8 con cámaras comunes.
Piloto3100: **216 grupos/5136 tris/dos materiales**, 63 planos nuevos (+126tris),
sin tocar madera/atlas/tamaños/anclajes. Núcleo0.30H preservado, OF7 como subconjunto
exacto del GLB final. Máximo64 complementarias, limitado antes de mallar por
reserva1584, cota de madera5415 y techo6999; no añade grupos.

[Repetición/cierre y límites](evidence/oak-foliage/of8/informe.md): 322 pruebas,
69 checks, siete GLB idénticos y63 capturas +12 máscaras inspeccionadas. Recupera
frontal y mantiene mejora superior; más área alfa, sin medición FPS. **Arte
pendiente**, otras edades y promoción de receta sin iniciar. Galería:
`artifacts/oak-foliage/of8-maduro-02/index.html`.


## OF9: regiones volumétricas por brazo

OF8 es la base aprobada provisionalmente. OF9 `oak-foliage-canopy-0.9.0`
reorganiza 216 grupos sobre soportes reales del mismo brazo, conserva tamaños,
pintura, madera, complementos laterales y **5136 tris exactos**. El margen
autorizado +700 queda sin usar. Regiones lógicas sin mallas añadidas.

```sh
python3 scripts/prepare_oak_foliage_regions.py --output artifacts/mi-of9
python3 scripts/oak_foliage_regions_masks.py --study artifacts/mi-of9
python3 scripts/prepare_oak_foliage_regions.py --output artifacts/mi-of9-repeat --stage generate
PYTHONPATH=src python3 -m unittest discover -s tests > /tmp/mi-of9-tests.txt 2>&1
python3 scripts/close_oak_foliage_regions.py --study artifacts/mi-of9 \
  --repeat artifacts/mi-of9-repeat --tests /tmp/mi-of9-tests.txt
```

Usar directorios nuevos y entorno externo para Blender/Godot y pruebas de sockets.
La galería compara OF6/OF8/OF9 con cámaras comunes; 24 azimuts de OF8/OF9 a
escala ortográfica2.2×span son una prueba explícita a distancia media, no la
cámara habitual de un videojuego aún no especificada. GLB/Blender final en
`painted/tree.glb` / `painted/tree.blend`.
Candidata actual `artifacts/oak-foliage/of9-maduro-03/index.html`.
[Resultados, límites y juicio visual](evidence/oak-foliage/of9/informe.md):
aceptación artística pendiente; no sustituye todavía la referencia provisional.


## OF10: expansión hacia huecos con protección estructural

Versión `oak-foliage-canopy-0.10.0`, entrada `configs/oak-foliage/gaps-B.json`.
Conserva OF9 íntegra y añade67 láminas en46 grupos, con raíces opacas compartidas:
**216 grupos/5270 tris/dos materiales**, +134 de700 autorizados. Las láminas nuevas
pueden aumentar escala1.15–1.55; madera/atlas sin cambios.

```sh
python3 scripts/prepare_oak_foliage_gaps.py --output artifacts/mi-of10
python3 scripts/oak_foliage_gaps_masks.py --study artifacts/mi-of10
python3 scripts/oak_foliage_gap_wood_masks.py --study artifacts/mi-of10
python3 scripts/prepare_oak_foliage_gaps.py --output artifacts/mi-of10-repeat --stage generate
PYTHONPATH=src python3 -m unittest discover -s tests -p test_oak_foliage_gaps.py > /tmp/mi-of10-tests.txt 2>&1
python3 scripts/close_oak_foliage_gaps.py --study artifacts/mi-of10 \
  --repeat artifacts/mi-of10-repeat --tests /tmp/mi-of10-tests.txt
```

Usar directorios nuevos y entorno externo Blender/Godot. Galería actual:
`artifacts/oak-foliage/of10-maduro-05/index.html`; GLB/Blender en `painted/`.
Incluye OF8/OF9/OF10, giro muestreado y máscaras de madera realmente visible.
[Auditoría, alcance y ensayos descartados](evidence/oak-foliage/of10/informe.md).
Aceptación artística pendiente; OF8 continúa como base provisional.


## OF11: tres ejes ascendentes y follaje central alto

Prototipo `oak-foliage-canopy-0.11.0`, extensión de madera
`oak-growth-central-0.1.0`. Añade un eje central y dos brotes altos con hijos:
475 tris nuevos de madera, **5745 totales**,216 grupos y778 láminas. O5 intacta;
24 grupos redistribuidos. La exclusión cilíndrica se limita a0.62H para habilitar
follaje central por encima de las horquillas bajas. No modifica recetas históricas.

```sh
python3 scripts/prepare_oak_foliage_central.py --output artifacts/mi-of11
python3 scripts/oak_foliage_central_masks.py --study artifacts/mi-of11
python3 scripts/prepare_oak_foliage_central.py --output artifacts/mi-of11-repeat --stage generate
PYTHONPATH=src python3 -m unittest discover -s tests -p test_oak_foliage_central.py > /tmp/mi-of11-tests.txt 2>&1
python3 scripts/close_oak_foliage_central.py --study artifacts/mi-of11 \
  --repeat artifacts/mi-of11-repeat --tests /tmp/mi-of11-tests.txt
```

Directorios nuevos y entorno externo Blender/Godot. Galería:
`artifacts/oak-foliage/of11-maduro-03/index.html`, GLB/Blender en `painted/`.
`reference/` conserva O5 desnuda; `bare/` muestra la madera extendida.
[Alcance, límites y revisión pendiente](evidence/oak-foliage/of11/informe.md).
