# Roble 3.0.0 — validación de cinco maduros

Fecha: 2026-11-03. Petición: ejecutar la recomendación de validar una familia de
cinco maduros, conservando reglas y pintura, sin ajustes por individuo.
Cámara elegida por el usuario: perspectiva provisional.

## Alcance y entradas

Receta `blueprints/roble_copa_ancha/3.0.0.json`, contrato1.7, perfil `maduro` de
12 m nominales; estructura3100–3104, distribución17 y pintura2718. 3100 es el
control aprobado; los otros cuatro son controles de variación estructural.
No se variaron parámetros, edades ni pintura. La receta y algoritmos históricos
permanecen intactos; solo se añaden petición, arnés de evaluación y evidencia.

Petición versionada: `configs/language/roble-central-familia-v1.json`.
Interpretación realizada por Codex en este chat (`codex-session`), sin llamada a
otro modelo. F4 validó los cinco casos antes de Blender y congeló receta,
petición, instancias resueltas y hashes. Ambos lotes usan ese mismo plan.

## Resultado técnico

| Estructura | Madera | Follaje | Total tris | Materiales | Altura total m | GLB repetido |
|---|---:|---:|---:|---:|---:|---|
| 3100 | 4189 | 1556 | 5745 | 2 | 13.374 | Idéntico |
| 3101 | 4684 | 1474 | 6158 | 2 | 13.998 | Idéntico |
| 3102 | 3959 | 1488 | 5447 | 2 | 12.649 | Idéntico |
| 3103 | 4597 | 1490 | 6087 | 2 | 14.108 | Idéntico |
| 3104 | 4564 | 1442 | 6006 | 2 | 13.822 | Idéntico |

Los cinco mantienen216 grupos y presupuesto <7000; cantidad de láminas varía
según colocación de complementos, sin cambios manuales. La altura visible de
láminas no equivale a la altura nominal de madera. Cinco firmas geométricas
diferentes y cinco repeticiones GLB byte por byte idénticas. 3100 reproduce el
SHA256 aprobado `315943611b884005ea96122d005891b5ee83ca772132bda6c52c412916ad9fde`.

Auditorías del GLB: materiales, texturas embebidas, alfa MASK .5, doble cara,
triángulos no degenerados, altura/orientación,216 anclajes y sus UV opacos,
contactos de láminas complementarias y protección inferior hasta7.44 m.
Mayor error de punto de contacto del lote: **0.000750 mm**, bajo tolerancia
0.01 mm. Esto no certifica todas las uniones de cada hoja pintada ni malla soldada.

El arnés verifica38 condiciones entre presupuesto, exportación, identidad,
entradas, fuentes y entorno. Pruebas existentes: cinco del contrato central y
ocho de F4, **13 correctas**. Blender5.2.1 LTS `9e2066aef7ef`; versiones exactas
Python/jsonschema y hashes en `summary.json`. Duración registrada por el ejecutor:
12.553–15.200 s por caso/repetición, sin renders Blender; excluye la auditoría
final del GLB. No son mediciones de rendimiento gráfico.

## Revisión visual Godot

**115 capturas reales**,23 por árbol, Godot4.7.2 `gl_compatibility`, RTX5060,
900×900, MSAA4, mipmaps y filtrado anisotrópico, recorte alfa .5, sombras y luz
comunes. Adaptador de revisión aislado en el proyecto regenerable: habilita
perspectiva y permite ocultar follaje para inspeccionar la misma madera.
No se alteran verificadores históricos ni GLB para la presentación.

Protocolo congelado antes de capturar: seis vistas ortográficas (frente, perfil,
reverso, perspectiva oblicua, arriba y oblicua superior), tres perspectivas a
distancias43.403/73.786/147.571 m del centro común, fondo oscuro, luz alternativa,
receptor de sombras, ocho azimuts45° y tres vistas de madera sola. Perspectivas:
FOV vertical50°, eje[1,-1,.45]. Son distancias provisionales, no la cámara final
del juego. La fracción.85/.50/.25 se refiere a la esfera envolvente común, no a
la altura ocupada por cada árbol en pantalla. Posiciones exactas, bases, límites
y fuentes en `review-protocol.json`; las cámaras no se reajustan por árbol.

Inspeccionadas las cinco láminas de23 miniaturas (115 capturas distintas), más
siete imágenes originales900×900: frente de los cinco, arriba3102 y oscuro3104.
La lista y observaciones están en `visual-review.json`.

- Hay variación visible de porte, orientación y asimetría con pintura compartida.
  3101 presenta desarrollo más alto;3102 copa más abierta;3103 peso lateral;
  3104 ascenso marcado en perspectiva. No se deduce reconocimiento botánico universal.
- Se conservan horquillas y madera legibles. No aparecen grandes rectángulos
  opacos evidentes en las tomas inspeccionadas. El punto de anclaje auditado y
  la lectura visual de una rama no certifican todas las uniones desde cualquier ángulo.
- **Límite repetido:** organización radial desde arriba y separación entre
  macromasas; no se declara una copa continua/plena en todos los giros. Hay
  puntas y cantos finos visibles y ramillas desnudas en varios sectores.
- Lejos se mantiene una silueta pequeña y se pierde detalle de hojas; no se
  evaluaron movimiento/parpadeo subpíxel ni LOD.
- Las sombras de madera y follaje se proyectan, pero los extremos derechos
  quedan recortados en las tomas de sombra: no se certifica su proyección completa.

Galería local: `artifacts/roble-central/familia-01/index.html`.
[Comparación de copa](overview.jpg), [tres distancias](distance.jpg),
[madera sola](wood.jpg). Las láminas completas y PNG originales permanecen en
la carpeta regenerable; solo se conserva evidencia seleccionada en Git.

## Fallo conservado y decisión

Primer intento dentro del sandbox: Blender guardó GLB/blend y se bloqueó al
cerrar audio (`pa_write ... Operation not permitted`); agotó120 s. Conservado en
`artifacts/roble-central/familia-01/trees-sandbox-failed-01/`. No es un fallo de
presupuesto ni un rechazo geométrico. Después se ejecutaron lote y repetición
fuera del sandbox con **las mismas entradas**, sin reintentos por semilla ni
retoques. No se ocultó ni sobrescribió ese intento. Godot usó escritorio/GPU.

Resultado: cinco casos técnicamente verificados y visualmente revisados con
límites. **Lote3100–3104 aprobado artísticamente por el usuario** el2026-11-03:
«ok, lo apruebo, que sigue ?». [Aceptación y hashes](user-acceptance.json).
No ampliar esta evidencia a todo el dominio de semillas. Los archivos de auditoría
y revisión visual conservan el estado previo a esta aceptación; esta decisión
lo sustituye sin alterar sus mediciones ni hashes.
Después de esta aceptación, el usuario autorizó el benchmark del roble3.0.0:
[medición posterior cerrada](../rendimiento-01/informe.md). No se inicia viento,
LOD ni nuevas especies.

## Reproducción

Usar una carpeta nueva para cada estudio. Blender y revisión Godot requieren
entorno gráfico/audio permitido fuera del sandbox en esta máquina.

```sh
PYTHONPATH=src python3 -m treegen plan-blueprints blueprints/roble_copa_ancha/3.0.0.json --request configs/language/roble-central-familia-v1.json --output artifacts/roble-central/mi-familia/plan
PYTHONPATH=src python3 -m treegen generate-blueprint-plan artifacts/roble-central/mi-familia/plan --output artifacts/roble-central/mi-familia/trees
PYTHONPATH=src python3 -m treegen generate-blueprint-plan artifacts/roble-central/mi-familia/plan --output artifacts/roble-central/mi-familia/repeat
python3 scripts/verify_oak_central_family.py --output artifacts/roble-central/mi-familia --stage audit
python3 scripts/verify_oak_central_family.py --output artifacts/roble-central/mi-familia --stage review
PYTHONPATH=src python3 -m unittest discover -s tests -p test_oak_central_blueprint.py -v
PYTHONPATH=src python3 -m unittest discover -s tests -p test_language.py -v
```

`audit` revalida los GLB y compara instancias, fuentes y exportaciones;
`review` captura e importa en Godot, genera galería y conserva el protocolo.
También se puede capturar mientras se repite el lote, y auditar después: así
se ejecutó este estudio. Ninguna etapa concede aceptación artística automática.
