# F2: ejecución, exportación y evaluación

Fecha: 2026-10-22. F2 implementada y verificada, sin ampliar alcance a F3. Comandos completos en el [README](../../../README.md#f2-ejecución-lote-y-evaluación).

## Implementación

- `src/treegen/runner.py`: trabajos secuenciales en directorios nuevos, validación de entrada, semillas explícitas, invocación acotada de Blender y manifiestos atómicos de éxito/fallo. Timeout por defecto 120 s, configurable hasta 600 s; termina el grupo de procesos si vence. Conserva logs y salidas parciales como evidencia de un trabajo fallido.
- `cli.py`/`__main__.py`: `generate`, `batch`, `validate`, `compare` y `serve`. Las entradas inválidas también producen manifiesto fallido cuando se solicita un trabajo individual; no se sobrescriben resultados anteriores.
- `evaluation.py`: lectura independiente de posiciones/índices del GLB final, validación numérica y presupuestos; contraste de triángulos, materiales, dimensiones, orientación y hashes con la malla evaluada. Verifica los hashes de los artefactos y las vistas requeridas.
- `api.py`: HTTP en loopback, un trabajador y cola de 32 pendientes. Crear trabajo devuelve 202 sin esperar a Blender; consultas de estado/manifiesto, rechazo de contrato con 400 y cola llena con 503. Detecta estados interrumpidos al reiniciar. No sirve binarios ni reanuda trabajos; un servidor por carpeta.
- `presets/f2-cases.json`: 30 especificaciones congeladas, diez por edad, semillas 1000–1009, 2000–2009 y 3000–3009.
- Adaptador Blender: registra cámaras y ofrece perspectiva real además de tres ortográficas. Conserva una vista de ramas para revisar uniones. El generador de nodos sigue en 0.1.0, sin modificar su geometría.
- Comparación: JSON de métricas/condiciones y HTML con imágenes de referencia y candidato. No incluye IoU, reglas espaciales ni optimización, que corresponden a fases posteriores.

## Resultados automáticos

Entorno fijado: Blender 5.2.1 LTS `9e2066aef7ef`, Python Blender 3.13.13, Python ejecutor 3.14.4, jsonschema 4.19.2 y Godot 4.7.2 `ed1daf0bf`. Fuentes y métricas en [summary.json](summary.json); ejemplo completo en [adulto-manifest.json](adulto-manifest.json).

| Conjunto | Casos | Triángulos por GLB | Materiales | Altura final |
| --- | ---: | ---: | ---: | ---: |
| Joven | 10 | 1748 | 2 | 4 m |
| Adulto | 10 | 4768 | 2 | 10 m |
| Viejo | 10 | 5088 | 2 | 9 m |

Los 30 GLB son válidos y geométricamente distintos. No se detectaron NaN/Inf, índices inválidos, triángulos degenerados ni dimensiones nulas. La altura exportada coincide con la solicitada dentro del error de coma flotante. Todas las variantes conservan corteza y follaje al importarse en Godot; coinciden conteos por material y cajas transformadas.

`adulto-00` se repitió desde una nueva sesión Blender, con render. Coinciden especificación, entorno, fuentes, cámaras y resumen geométrico normalizado; diferencia de triángulos 0. [Comparación](comparison.json), con HTML e imágenes en `artifacts/f2/verification-final/comparison/index.html`. También se ejercitó una comparación entre semillas distintas: detecta geometría y cámaras diferentes, aun con igual número de triángulos.

Once pruebas unitarias pasaron: contratos/semillas, GLB sintético válido y rechazo de NaN, degeneración, índices fuera de rango, truncamiento y altura incorrecta; manifiestos de entrada inválida, timeout y fallo de exportación; rechazo de sobrescritura; API asíncrona y contrato inválido. El timeout unitario simula el subproceso y verifica la terminación del grupo. La CLI se ejercitó además con JSON truncado: código 1 y estado `failed`, documentados en [cli-errors.json](cli-errors.json).

La integración HTTP real generó un adulto sin vistas, consultó su manifiesto validado y verificó un segundo trabajo con ejecutable inexistente (`failed`), además del rechazo de especificación inválida con 400. Véase [api-summary.json](api-summary.json). El servidor de prueba se cerró al terminar; no queda un servicio permanente.

El primer ensayo dentro del sandbox exportó y renderizó, pero Blender se bloqueó al cerrar con un fallo de audio. El ejecutor lo terminó a los 120 s y lo registró como fallo, sin contarlo en el lote: [timeout-manifest.json](timeout-manifest.json). El lote y las integraciones correctas se ejecutaron fuera del sandbox.

Tiempo observado del lote final: suma de duraciones de trabajos 48.965 s, mediana 1.669 s por trabajo, incluidas cinco vistas por árbol; no incluye importación/capturas Godot. Es un dato operativo de esta ejecución, no un benchmark ni un presupuesto de rendimiento para F3.

## Revisión visual

Se revisaron las galerías frontal, lateral, superior, perspectiva y ramas de los 30 casos; también la galería de capturas producidas en una sesión gráfica de Godot con los GLB importados. Las siluetas varían entre semillas y mantienen la familia facetada de F1; jóvenes estrechos y adultos/viejos de copa ancha. La corteza y el follaje son visibles con escala y orientación coherentes. En las vistas revisadas no se observaron ramas flotantes. Existen cruces, uniones superpuestas y copas con distribución radial o huecos centrales, especialmente en viejos; siguen admitidos y no se atribuye ninguna mejora espacial a F2. Las miniaturas no sustituyen una futura inspección cercana del bosque.

Evidencia seleccionada:

- [Perspectiva Blender](gallery-perspective.jpg).
- [Ramas sin follaje](gallery-branches.jpg).
- [GLB en Godot, sesión gráfica](gallery-godot.jpg).

Las galerías encuadran cada árbol individualmente; no comparan tamaño absoluto entre edades. El encuadre automático puede variar al cambiar geometría: `compare` informa `same_cameras`, y no debe interpretarse una comparación con cámaras distintas como una medida de silueta. La repetición comprobada conserva cámaras idénticas; F6 deberá congelarlas antes de optimizar.

## Reproducción y límites

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m treegen batch --output artifacts/repro-f2
python3 scripts/verify_f2.py --visual --batch artifacts/repro-f2 --output artifacts/repro-f2-check
python3 scripts/verify_api.py --output artifacts/repro-f2-api
python3 scripts/make_gallery.py artifacts/repro-f2
python3 scripts/make_gallery.py artifacts/repro-f2 --godot
```

Usar carpetas nuevas; `make_gallery.py` requiere Pillow 12.1.1 para las miniaturas, sin introducir esa dependencia en el generador. Salidas completas de esta verificación: `artifacts/f2/lote-final/`, `artifacts/f2/verification-final/` y `artifacts/f2/api-final/`; son regenerables y no se versionan. Los 30 GLB de importación están en `godot/f2/`, también ignorado. Los resúmenes seleccionados conservan hashes para comprobar reproducción sin exigir identidad binaria de GLB o píxeles entre entornos.

El validador GLB cubre el formato emitido por este adaptador (una malla, coordenadas realizadas, materiales simples); rechaza transformaciones de nodo y accessors no soportados. No es un validador glTF universal. La API es local, secuencial, sin persistencia de cola ejecutable tras reinicio ni descarga de binarios. No se construyó bosque, no se midió rendimiento gráfico y no se integró IA. El siguiente paso es F3.
