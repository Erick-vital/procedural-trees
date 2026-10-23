# Q1: jerarquía y reparto de ramas

Fecha: 2026-10-22. Primera etapa de la revisión de calidad dentro del [plan v1](../../../plans/v1-generador-arboles.md). Implementada y verificada técnica y visualmente por el agente; pendiente de valoración estética del usuario. Q2 (copa y proporciones), F4–F6 y el proyecto de terrenos/bosque no se implementaron.

## Cambio y límites

`oak_geometry_nodes` **0.2.0** conserva el contrato de diez parámetros, las semillas y dos niveles de ramas. En Geometry Nodes cada nacimiento lleva atributos de posición, radio local del padre, longitud, orientación e inclinación. Tras realizar las instancias se deforma cada curva según esos atributos. No se introdujo una estructura de ramas calculada en Python ni un algoritmo de prevención de cruces.

- Primarias: radio del 58–70 % del padre en la unión; longitud menor hacia la parte superior; inclinación y elevación de puntas variadas por altura/semilla.
- Reparto horizontal: sectores completos, alturas alternadas entre lados y perturbación máxima del 16 % del ancho de sector multiplicada por asimetría. La fase global también depende de la semilla. Así se conserva variación sin cancelar el reparto angular con giros independientes de ±180°.
- Secundarias: radio del 50–60 % del padre local, longitud del 38 %/26 % de la primaria y orientación hacia ambos lados con elevación. Se conservan exactamente dos nacimientos al 48 %/78 % de cada primaria y las cantidades originales.
- Muestreo de volumen: nueve puntos por primaria y siete por secundaria, frente a siete/cinco en la base, para representar las nuevas curvaturas. Se conserva el perfil de ocho lados.
- El follaje y el ajuste vertical de altura reutilizan las reglas de 0.1.0. Cambia dónde queda el follaje porque cambian las puntas. No se retocaron los diez valores de los presets ni se añadieron hojas para ocultar defectos.

La implementación está en `blender/oak_nodes_v2.py`; la fuente 0.1.0 de `blender/oak_nodes.py` conserva exactamente su hash anterior. El adaptador selecciona por `algorithm_version`; el esquema admite ambas versiones. Los presets principales apuntan a 0.2.0; los históricos están en `presets/v0.1.0/`. Los casos F2 permanecen en 0.1.0 y `presets/q1-cases.json` conserva sus treinta semillas/parámetros con versión 0.2.0. La verificación histórica F1 usa los presets congelados.

## Comparación reproducible

Se generaron treinta candidatos con las mismas semillas y parámetros del lote F2. Para los tres viejos rechazados por el usuario y los controles `adulto-00`/`joven-00` se renderizaron ambos `.blend` con un encuadre común calculado a partir de la unión de sus cajas. Cámara, proyección, escala de encuadre, resolución y sombreado coinciden por pareja, tanto con follaje como sin él. Los `.blend` y GLB de referencia no se sobrescribieron. Se reconstruyó además el viejo-09 0.1.0 y se obtuvo la misma geometría normalizada que antes.

| Medida | viejo-00, base → Q1 | viejo-03, base → Q1 | viejo-09, base → Q1 |
| --- | ---: | ---: | ---: |
| Menor separación horizontal entre primarias | 0.42° → 26.03° | 5.23° → 27.16° | 0.39° → 26.53° |
| Mayor hueco entre direcciones principales | 93.29° → 40.00° | 91.96° → 39.24° | 120.45° → 38.28° |
| Máxima relación de radio primaria/padre local | 1.64 → 0.698 | 1.64 → 0.692 | 1.64 → 0.700 |
| Rango de inclinaciones finales de primarias | ~0° → 28.94° | ~0° → 31.31° | ~0° → 30.75° |
| Primarias/secundarias | 11/22 → 11/22 | 11/22 → 11/22 | 11/22 → 11/22 |

Las treinta variantes cumplen los controles estructurales: hijo más delgado que padre local, conteos esperados, inclinaciones variadas en presets y límites del reparto por sectores. No se midieron ocupación volumétrica, conflictos o realismo botánico; estas medidas comprueban las causas específicas del diagnóstico.

Q1 también cambia la longitud total y la anchura de la estructura. En los tres viejos la longitud nativa sumada de las curvas baja aproximadamente un 35 % (122.34 → 80.16 m, 117.72 → 76.98 m y 121.68 → 79.62 m, incluido tronco). Se conserva el número de ramas, pero estas son más cortas y ascendentes. No es una comparación del experimento B y no cumple su condición de conservar el 90 % de longitud; no se declara una reducción de cruces ni una mejora general de IA.

Evidencia seleccionada, base arriba y Q1 abajo en cada pareja:

- [Ramas sin follaje](comparison-branches.jpg).
- [Copa en vista frontal](comparison-front.jpg).
- [Treinta candidatos en Godot](gallery-godot.jpg).
- [Resumen, métricas y hashes](summary.json), [manifiesto viejo-09](viejo-09-manifest.json) y [pruebas unitarias](unit-tests.txt).

Comparación completa con ocho vistas por pareja: `artifacts/q1/acceptance/comparison/index.html`. Cada pareja comparte cámara; el tamaño de encuadre entre casos distintos no tiene por qué ser igual. Las miniaturas reducen detalle: los PNG completos quedan junto al HTML.

## Verificación

Entorno: Blender 5.2.1 LTS `9e2066aef7ef`, Python de Blender 3.13.13, Python ejecutor 3.14.4, jsonschema 4.19.2 y Godot 4.7.2 `ed1daf0bf`.

- **14 pruebas unitarias pasaron**, incluidos versiones admitidas/rechazo de versión desconocida y controles estructurales frente a grosores excesivos, agrupación, inclinaciones idénticas y pérdida de ramas.
- **30 candidatos exportados, válidos y distintos**, dentro del presupuesto de 10 000 triángulos/3 materiales. Joven: 2132 triángulos; adulto: 5632; viejo: 6144. Dos materiales por árbol; alturas finales 4/10/9 m dentro del error flotante. Son más triángulos que en 0.1.0; la simplificación corresponde a F6.
- Repetición de viejo-09 y adulto-00 desde sesiones limpias: geometría normalizada reproducible; la repetición del adulto conserva fuentes/entorno y cámaras. Base 0.1.0 también reconstruida con geometría idéntica a la referencia.
- Efecto de los diez parámetros comprobado. Cambiar solo la semilla de follaje conserva las curvas nativas y cambia el resultado completo.
- Mínimos, máximos, ramas finas numerosas y profundidad 1 sin follaje: geometría y jerarquía estructural válidas. Máximo observado en extremos: **7420 triángulos/2 materiales**. El diagnóstico admite canales vacíos cuando no hay secundarias.
- Los treinta GLB importados y comprobados en Godot; coinciden cajas, triángulos y materiales. Se generaron capturas con sesión gráfica.
- Se revisaron las galerías de los treinta árboles y las parejas con encuadre común, sin declarar aceptación estética del usuario. No se observaron piezas flotantes en las imágenes revisadas. Las uniones siguen siendo piezas superpuestas; no se obtuvo una malla orgánica continua.

## Revisión visual y trabajo pendiente

Las vistas de madera muestran una jerarquía de grosores más clara y elevaciones distintas de las primarias. Los tres viejos ya no presentan el mismo patrón de barras gruesas casi horizontales que motivó el diagnóstico. La estructura resultante es más estrecha y ascendente, con repetición aún visible de las horquillas; puede requerir ajustes de estilo antes de considerarla una familia convincente de robles viejos.

El follaje sigue siendo grueso y puede agruparse u ocultar ramas. El ajuste Z sigue comprimiendo la estructura: en estos tres candidatos multiplica Z por 0.714–0.748, frente a 0.770–0.832 en sus referencias. Es decir, esta etapa no resolvió el aplastamiento y en esos casos aumenta su magnitud. Q2 deberá estudiar copa, proporciones y presets sobre una estructura revisada por el usuario. Pasar las pruebas no cierra esa valoración.

## Reproducción

Con el lote base F2 disponible en `artifacts/f2/lote-final/`, ejecutar desde la raíz con una carpeta nueva:

```sh
python3 scripts/verify_q1.py --visual --output artifacts/repro-q1
python3 scripts/q1_gallery.py artifacts/repro-q1
python3 scripts/make_gallery.py artifacts/repro-q1/lote
python3 scripts/make_gallery.py artifacts/repro-q1/lote --godot
```

La primera orden ejecuta pruebas, lote, referencias, repetición, parámetros, extremos, diagnósticos, cámaras compartidas e importación Godot. Requiere sesión gráfica con `--visual` y ejecutar fuera del sandbox en este equipo para evitar el bloqueo de audio conocido al cerrar Blender. Las miniaturas requieren Pillow 12.1.1; no es dependencia de generación. Puede elegirse otro lote base con `--base`.

Resultados completos: `artifacts/q1/acceptance/`; GLB importados en `godot/q1/`, ignorados. El diagnóstico de extremos se añadió al script después de la primera aceptación y se ejecutó como paso incremental sobre los mismos assets; su resultado está incluido en el resumen. No se regeneró geometría para ese control adicional.
