# RF0/RF1 — referencia visual y unidad experimental

Fecha: 2026-10-22. Alcance: primeras dos fases del [rediseño de follaje](../../../plans/rediseno-follaje.md). RF0 preparado y RF1 implementada/verificada técnicamente; aceptación artística pendiente. RF2–RF5 no se han iniciado.

La [ficha visual y contrato](../../follaje-rf0-rf1.md) define tres referencias con procedencia/licencia, el objetivo de hojas opacas, la rama Q3 congelada y cámaras compartidas. El [bloqueo](reference-lock.json) conserva datos fuente, transformaciones, material y muestras. La madera y los archivos Q3 originales permanecen intactos; no cambian presets históricos ni el generador de producción.

## Entregables revisables

- [Tres unidades en Blender y Godot, incluidos reversos](variants.jpg).
- [Cambios aislados de tamaño, separación e inclinación](controls.jpg).
- [Referencia Q3: vistas y ocupación de pantalla](rf0-views.jpg).
- [Manifiesto del hexágono plegado](folded-hex-manifest.json), [resumen verificable](summary.json) y [24 pruebas](unit-tests.txt).

Galería completa local: `artifacts/foliage/rf0-rf1-acceptance/index.html`. En cada carpeta de variante, `unit.glb`, `scene.blend`, manifiesto y capturas. La referencia Q3 completa se conserva en su ruta original; la escena RF0 añade una copia de su rama para inspección.

## Resultados técnicos

| Forma | Hojas/unidad | Triángulos/hoja | Triángulos/unidad | Máximo teórico de hojas / unidades de siete en viejo-09 |
| --- | ---: | ---: | ---: | ---: |
| Rombo | 7 | 2 | 14 | 2 354 / 336 |
| Hexágono plano | 7 | 4 | 28 | 1 177 / 168 |
| Hexágono plegado | 7 | 4 | 28 | 1 177 / 168 |

La madera Q3 de viejo-09 suma 5 292 triángulos y deja 4 708 dentro de 10 000. La cuenta es un techo aritmético: no se han instanciado esas cantidades ni se demuestra que basten para una copa convincente. Cada unidad usa un material opaco; con la corteza serían dos, por debajo del máximo tres. No se mide FPS.

Se exportaron e importaron **16 GLB**: tres formas, repetición, diez cambios aislados —nueve parámetros y semilla— y dos casos de borde. El máximo genera 32 hojas/128 triángulos; el mínimo comprueba una sola lámina sin espesor. Cada GLB pasa inspección independiente de coordenadas, áreas, normales, material, escala y ejes. Godot comprueba cantidad de triángulos, caja, material opaco sin texturas y culling desactivado en los 16. Las seis unidades con capturas suman 36 imágenes Godot; todas contienen más de 100 píxeles diferenciados del fondo. Eso detecta encuadres vacíos, no calidad estética.

Sesiones nuevas de Blender reconstruyen el candidato plegado con el mismo hash geométrico y las mismas colocaciones. Los diez cambios aislados alteran su geometría; largo, forma, giro y semilla conservan raíces mientras no cambia la separación. Todas las formas y controles conservan las cámaras de detalle.

Pasaron 24 pruebas unitarias, incluidas entradas inválidas, límite de trabajo previo al mallado, ortonormalidad, orientación dextrógira, transporte del marco al cruzar un cambio de eje preferente, separación entre controles y rechazos de GLB con normales invertidas, culling, transparencia o truncamiento. El resumen registra hashes de las fuentes ejecutadas y las versiones del entorno.

## Revisión visual realizada y límites

Se inspeccionaron imágenes reales de las tres formas en Blender —frente, perfil, superior, inferior, oblicua, reverso y segunda iluminación— y sus capturas Godot, además de los controles seleccionados. Se revisaron las vistas RF0 del árbol y de la rama. Las hojas permanecen visibles como conjunto en las vistas muestreadas; el plegado añade dos planos perceptibles al mismo coste del hexágono plano. El reverso Godot se conserva sin duplicar la geometría. Esta revisión del agente no equivale a aceptación del usuario.

La simplificación conserva un contorno ancho, pero no lóbulos de roble. Las hojas planas se afinan hasta casi desaparecer de canto y también ocurre en algunos ángulos del plegado. Siete hojas sobre una línea virtual todavía pueden parecer suspendidas. No se ha demostrado que una rama o una copa resuelva esos límites, ni que 1 177 hojas basten para el objetivo. No se ha cambiado a tarjetas, añadido ramillas visibles ni elevado el presupuesto para ocultarlos.

La ficha usa ortográficas con ocupación 50/25/10 % como protocolo inicial de juego; no se han medido distancias de una cámara perspectiva real. RF3 deberá juzgar las hojas en una copa desde esas cámaras. El candidato técnico propuesto para la siguiente revisión es el hexágono plegado; la elección visual definitiva permanece abierta.

## Incidencias resueltas

La normalización registrada de Q3 usa una caja redondeada: reconstruir la rama difirió 0.238 µm de la malla guardada. Se usó solo para localizar la rama; sus 72 vértices/140 triángulos finales se extrajeron exactamente del original, con índices y sombreado conservados.

La primera importación Godot verificó mallas pero sus capturas estaban vacías por interpretar rotaciones de Euler con otra convención. La revisión de imágenes detectó el fallo. Se sustituyó por conversión de las bases completas y se repitió el ensayo; la evidencia seleccionada corresponde únicamente al resultado corregido. El ejecutor comprueba ahora que las capturas contienen geometría visible.

## Reproducción

Desde la raíz, con las herramientas y dependencias del README, en una carpeta nueva:

```sh
python3 scripts/verify_foliage_unit.py --output artifacts/foliage/otra-revision --visual
python3 scripts/foliage_evidence.py --study artifacts/foliage/otra-revision --output artifacts/foliage/evidencia
```

`--visual` abre Godot brevemente; cada subproceso tiene timeout de 120 s. Sin esa opción se verifican mallas/importación, pero no se pueden producir estas capturas ni afirmar revisión visual. Para seleccionar evidencia, el segundo comando requiere una ejecución con `--visual` y las dos referencias fotográficas en `artifacts/foliage-references/`:

```sh
mkdir -p artifacts/foliage-references
curl -fL 'https://upload.wikimedia.org/wikipedia/commons/a/af/Quercus_robur.jpg' -o artifacts/foliage-references/robur-mpf.jpg
curl -fL 'https://thumb.wikimedia.org/wikipedia/commons/thumb/1/13/Oak_leaves_on_a_branch_in_Tuntorp.jpg/960px-Oak_leaves_on_a_branch_in_Tuntorp.jpg' -o artifacts/foliage-references/tuntorp-wcarter.jpg
```

La procedencia/licencias de las fotos se enlaza en la ficha; no son texturas del modelo. `--source` permite indicar una reconstrucción explícita de viejo-09 Q3; `--preset` cambia el experimento de unidad, no los presets de producción. Los valores de la matriz de verificación son fijos para reproducir el ensayo, sin pretender validar cualquier preset personalizado. BLENDER_BIN/GODOT_BIN pueden cambiar rutas; se exige Blender 5.2.1/Godot 4.7.2.

Siguiente paso: revisar esta ficha y las tres unidades; resolver lectura de perfil y dirección estética antes de poblar la rama congelada en RF2. No se declara RF1 cerrada artísticamente ni se inicia una copa por pasar las pruebas.
