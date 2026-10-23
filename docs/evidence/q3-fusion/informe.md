# Ensayo Q3: fusión parcial de superficies de follaje

Fecha: 2026-10-22. Posprocesado **`q3-partial-fusion-0.2.1`** sobre Q3 0.4.0. Cuatro casos verificados técnicamente y revisados mediante capturas reales de Blender y Godot. **El usuario considera Q3/fusión casi iguales y acepta cerrar esta familia como aprobada para su estilo, sin atribuir mejora a la fusión ni extenderla al lote.**

## Alcance y referencia congelada

El usuario identifica Q3 como última iteración buena y rechaza Q3b. Autorizó guardar primero el estado del proyecto en Git y probar una fusión parcial sin cambiar madera, semillas, densidad, distribución ni tamaños de las masas de entrada. Commit inicial `fbe87a4`; etiqueta `q3-referencia-0.4.0`. Ese commit incluye también Q3b como ensayo histórico, sin promoverla visualmente.

La comparación empieza con `viejo-09`, semilla 3009. El primer piloto por primaria conserva el contorno, pero cambia poco la lectura de piezas independientes. El segundo agrupa hasta tres subárboles vecinos; tras revisar sus seis vistas se amplía a `viejo-00`, `viejo-03` y `adulto-00`, con la misma regla y sin ajustar parámetros por caso.

[Bloqueos de referencia](reference-locks.json): hashes de `.blend`, GLB, manifiesto y fuentes históricas; especificaciones, semillas efectivas, cámaras e iluminación. Los cuatro archivos originales permanecen intactos. Se conservan exactamente las cuatro cámaras históricas Q3 de frente, perfil, arriba y perspectiva. Se fijan antes de fusionar una toma inferior y otra distante. Las parejas mantienen materiales e iluminación; Blender y Godot tienen entornos de iluminación propios, iguales dentro de cada pareja.

## Método

- Reutiliza la malla Q3 guardada y sus atributos de pertenencia a ramas. No vuelve a distribuir las masas ni modifica la estructura.
- Agrupa cada primaria con sus secundarias y une hasta tres subárboles por proximidad de sus centros geométricos. No une toda la copa en una única superficie.
- Remalla cada grupo con vóxel de `0.09 × escala efectiva de follaje`, suaviza seis iteraciones con factor 0.5 y reduce caras al presupuesto de entrada del grupo. Conserva las hojas del tronco y los polígonos y sombreado originales de madera.
- Limpia aristas menores que `0.01 × vóxel`, mantiene el follaje dentro de la altura y usa sombreado plano en sus superficies.
- Limita antes de remallar a dos millones de celdas estimadas por grupo y doce millones en total; también limita geometría intermedia, triángulos finales y duración del subproceso a 180 s.

La densidad, tamaños y posiciones **de entrada** son idénticos. La superficie final se aproxima mediante remallado y simplificación; no se promete conservar exactamente volumen, contorno ni todos los huecos. Menos componentes topológicos es una consecuencia de unir superficies, no una eliminación de masas de entrada.

La especificación del candidato sigue describiendo Q3; `postprocess` registra explícitamente versión y configuración de la modificación. El `.blend` conserva además la malla Q3 original, incluidos sus atributos, como datablock con usuario ficticio. El generador de producción, el esquema y los presets principales no cambian.

## Resultados

| Caso | Masas de entrada → componentes finales | Triángulos de follaje Q3 → fusión | Triángulos totales finales | IoU mínima de silueta |
| --- | --- | --- | --- | --- |
| viejo-09 | 89 → 8 | 3220 → 3220 | 8512 | 98.48 % |
| viejo-00 | 89 → 7 | 3220 → 3216 | 8508 | 98.40 % |
| viejo-03 | 85 → 6 | 3140 → 3140 | 8432 | 98.69 % |
| adulto-00 | 71 → 7 | 2620 → 2618 | 6982 | 98.33 % |

IoU: intersección/unión de máscaras de follaje obtenidas con 192×192 rayos ortográficos; mínimo de frente, perfil, arriba y abajo. No mide volumen, naturalidad, detalle interno ni aceptación estética. Las reducciones de dos/cuatro triángulos corresponden a limpieza residual; este ensayo no demuestra optimización ni mejora de FPS.

Comprobaciones completadas:

- Madera idéntica en X/Y/Z y en polígonos/sombreado; malla Q3 de entrada y todos sus atributos `q3_*` conservados dentro de cada candidato guardado.
- Parámetros, semillas, estructura nativa y normalización idénticos. Cámaras y ajustes de iluminación/materiales compartidos por pareja.
- Cuatro GLB válidos, coincidentes con la malla evaluada en triángulos, materiales y límites. Dos materiales; alturas de 9/10 m según edad; follaje dentro de altura.
- Q3 `viejo-09` reconstruye la geometría original. La fusión del mismo caso se repite con métricas y configuración idénticas.
- Ocho GLB —cuatro bases y cuatro candidatos— importados en Godot 4.7.2 con escala, orientación, materiales y triángulos coincidentes. Capturas reales cercanas y distantes; cámaras iguales por pareja.
- Las 18 pruebas existentes pasan. La prueba nueva de integración inspecciona independientemente las mallas guardadas; no se ejecuta el lote ni extremos del contrato, porque el ensayo no amplía el generador de producción.

Una versión intermedia perdió un triángulo residual al exportar el adulto; falló la validación y se descartó. La limpieza de aristas corrige esa discrepancia en los cuatro resultados finales. Los pilotos y controles intermedios no son la evidencia seleccionada.

## Revisión visual y límites

[Piloto: seis vistas](pilot-all-views.jpg), [frente de los cuatro controles](controls-front.jpg), [desde abajo](controls-below.jpg), [Godot](controls-godot.jpg) y [Godot a distancia](controls-godot-game.jpg). Siempre Q3 a la izquierda y fusión a la derecha.

El agente revisó las seis vistas de los cuatro casos y las capturas Godot. Algunas separaciones entre piezas desaparecen y hay transiciones más continuas, sin vaciar la copa como Q3b. El efecto es moderado: persisten lóbulos reconocibles y separaciones entre los grupos que no se fusionan; algunas facetas alargadas y diagonales de simplificación resultan más visibles. La fusión conserva parte del aspecto de roca porque hereda la forma y disposición de Q3.

La toma distante está a 101–108 m del centro del árbol, con focal equivalente de 50 mm y resolución 900×900. Es una referencia de lectura lejana; no constituye una cámara de juego aprobada ni un ensayo de LOD/rendimiento. A esa distancia la diferencia visual es pequeña.

La prueba **no demuestra un salto de calidad suficiente para sustituir Q3**. El usuario acepta cerrar esta familia y pide pensar un rediseño más completo: [dirección de diseño](../../diseno-follaje.md). La aprobación se limita al estilo y resultados mostrados, sin aprobar un lote fusionado inexistente. No se afirma mejora de IA, rendimiento, naturalidad general ni agotamiento absoluto de métodos con esferas. No se inicia otra implementación por esta revisión.

## Reproducción

Partir del lote Q3 y sus cámaras históricas, cuya reproducción está documentada en el [informe Q3](../q3/informe.md). Usar una carpeta nueva; las galerías requieren Pillow, y las capturas requieren sesión gráfica local.

```sh
# Primero el piloto; revisar las imágenes antes de ejecutar los controles.
python3 scripts/preview_fusion.py --output artifacts/q3-fusion/otro-piloto

# Si el piloto promete, misma regla sobre los cuatro casos seleccionados.
python3 scripts/preview_fusion.py --output artifacts/q3-fusion/otros-controles --cases viejo-09 viejo-00 viejo-03 adulto-00
python3 scripts/verify_fusion.py --study artifacts/q3-fusion/otros-controles --visual
python3 scripts/fusion_evidence.py --study artifacts/q3-fusion/otros-controles --output artifacts/q3-fusion/otra-evidencia
```

`--base` y `--cameras-root` permiten indicar otra reconstrucción de Q3. Los controles finales de esta sesión están en `artifacts/q3-fusion/acceptance/`, comparación `index.html`, modelos `<caso>/candidate/tree.glb`, verificaciones en `verification/summary.json`. El validador también compara las cámaras Godot por pareja. Los modelos copiados a `godot/q3-fusion/` y todas las salidas regenerables están ignorados por Git.

Implementación: `blender/foliage_fusion.py` (algoritmo), `blender/experiment_fusion.py` (adaptador/comparación), `blender/verify_fusion.py` (inspección guardada), `scripts/preview_fusion.py` y `scripts/verify_fusion.py` (ejecución), `godot/verify_fusion.gd` (inspección del destino). Versiones de Blender/Python/Godot: las fijadas en el README. [Resumen y hashes](summary.json).
