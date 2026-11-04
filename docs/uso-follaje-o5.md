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
