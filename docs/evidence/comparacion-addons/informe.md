# Comparación acotada: Q3, Easy Tree y Sapling

Fecha: 2026-10-22. Ensayo solicitado por el usuario antes de RF3: un adulto y un viejo por addon, comparación con Q3 bajo requisitos comunes y evaluación del trabajo de ajuste. Los seis modelos finales cumplen técnicamente; su aceptación artística queda pendiente. No se inicia RF3 ni se sustituye el generador de producción.

## Entregables

- [Comparación en Godot](godot-perspective.jpg), [frontal](godot-front.jpg), [superior](godot-top.jpg) y [desde abajo](godot-below.jpg).
- [Comparación en Blender](blender-perspective.jpg) y [madera sin follaje](wood-only.jpg).
- [Resultados y verificaciones](summary.json), [catorce configuraciones e intentos](attempts.json), [cámaras](cameras.json), [versiones y fuentes de addons](addon-sources.json) y [30 pruebas](unit-tests.txt).

Galería completa: `artifacts/addon-comparison/acceptance-final/index.html`. Modelos finales: `comparison/<generador>-<edad>/tree.glb`, con `.blend`, manifiesto y vistas. Generadores: `q3`, `easy`, `sapling`; edades: `adulto`, `viejo`. `attempts/` conserva las salidas y configuraciones de ajuste; `repeats/`, las cuatro repeticiones independientes.

## Protocolo fijado

Referencias Q3 0.4.0: **adulto-00**, altura 10 m/semilla 2000, y **viejo-09**, altura 9 m/semilla 3009. Se emplean esos números también en los addons para fijar entradas; no se presupone que signifiquen árboles equivalentes entre algoritmos. Los archivos originales Q3 y las instalaciones de addons permanecen intactos, con hashes comprobados.

Requisitos comunes:

- Altura final de 10/9 m, base Z=0 y coordenadas en metros. Los addons reciben escala uniforme de la malla completa y traslación de base; no se deforma Z por separado ni se conserva su madera al modificar follaje. Q3 mantiene su geometría histórica.
- Máximo **10 000 triángulos/3 materiales**; los seis finales usan dos materiales. Sin texturas ni transparencia: corteza RGB (.24,.105,.045) y hojas (.23,.43,.065), alfa 1 y rugosidad .88. Las hojas son de doble cara.
- Caras facetadas. La **copia de presentación Q3** convierte 1 960/2 376 caras suaves a planas para compartir ese criterio; no mueve vértices ni cambia polígonos y no sobrescribe la referencia. Esta presentación no es idéntica en sombreado al GLB histórico aprobado.
- Cámaras ortográficas a 900×900, frontal, lateral, superior, inferior oblicua, oblicua y reverso. El nombre `perspective` identifica una toma oblicua ortográfica. Centro común `(0,0,height/2)` y escala vertical `2*height`: altura frontal aproximada del 50 % del cuadro. Se fijan desde las alturas de referencia antes de leer candidatos y se comparten por edad, sin reencuadrar por resultado.
- Blender Workbench y Godot Compatibility con la misma configuración entre generadores de cada renderizador. En Godot: luz a (-35,-25,0)°, energía 1.2, ambiente blanco .5; en Blender: estudio `paint.sl` rotado .5 rad y sin cavity. No se compara luminosidad entre renderizadores como puntuación.

El requisito estilístico común es **árbol de hoja ancha, geométrico, opaco y facetado**. No se exige copiar las masas Q3 ni su silueta exacta. Tampoco se certifica una especie botánica o una simulación de envejecimiento: adulto/viejo son perfiles artísticos con diferente grosor, extensión y ramificación. Sapling parte del preset `small_maple` adaptado, no de un supuesto preset nativo de roble.

El protocolo favorece estudiar la alternativa geométrica que se pidió para este proyecto. No evalúa la estética de Easy Tree con sus recortes y texturas originales; un mal resultado opaco no demuestra que su presentación texturizada sea mala.

## Resultados finales

| Generador | Adulto: triángulos | Viejo: triángulos | Ancho máximo/altura adulto–viejo |
| --- | ---: | ---: | ---: |
| Q3, presentación facetada | 6 984 | 8 512 | 1.327 / 1.461 |
| Easy Tree adaptado | 7 472 | 9 022 | .735 / 1.113 |
| Sapling ajustado | 7 764 | 9 048 | 1.188 / 1.385 |

El ancho se obtiene de la mayor extensión X/Y de la malla completa; no mide calidad, cobertura ni parecido botánico. Los seis tienen altura correcta dentro de 1 mm y pasan validación independiente del GLB: áreas, finitud, índices, materiales, escala, ejes y presupuesto.

Godot importa y comprueba los seis modelos, materiales y cajas. Se obtienen **36 capturas**, seis por modelo, todas con geometría visible. Los cuatro candidatos de addons se reconstruyen en nuevas sesiones Blender con las mismas métricas y hash de geometría nativa y final. Pasan las 30 pruebas existentes; estas son regresión de infraestructura y contratos, no una prueba de superioridad de los addons.

Versiones: Easy Tree **1.0.1**, Sapling **0.3.7**, Blender **5.2.1 LTS** `9e2066aef7ef` y Godot **4.7.2** `ed1daf0bf`. Sus fuentes instaladas y los adaptadores quedan identificados por hashes. No se modifican operadores, grafos ni presets en las instalaciones; los cambios de Easy Tree se aplican solo a los grupos cargados en la sesión de prueba.

## Ajustes y esfuerzo observado

Se conservan **14 configuraciones de geometría**: cuatro por perfil Easy Tree y tres por perfil Sapling. Trece producen una malla medida; el Easy Tree viejo inicial se descarta al obtener 574 760 triángulos, por encima del límite de aceptación intermedia de 300 000. Ese límite se comprueba después de evaluar la malla, no evita su construcción. Cada Blender tiene timeout de 120 s. Los intentos de integración fallidos durante el desarrollo del adaptador se explican aparte; no se ocultan ni se cuentan como candidatos estéticos.

| Familia | Recorrido de ajuste | Trabajo específico para este ensayo |
| --- | --- | --- |
| Q3 | Referencias ya existentes | Validar/copiar, compartir paleta y facetado. El desarrollo histórico de Q3 no está cronometrado y no se compara con este ajuste corto |
| Easy Tree adulto | Inicial 282 312 triángulos brutos → versión acotada 5 801 limpios → hoja geométrica 6 172 → densidad final 7 472 | Cargar grupos y realizar instancias; reducir niveles 5→3 y perfil de madera 12→6; ramilla de 7→3 hojas; sustituir la hoja texturizada por geometría opaca RF1; ajustar densidad |
| Easy Tree viejo | Inicial 574 760 brutos, rechazado → acotado 11 908, fuera de presupuesto → geométrico 10 582, fuera → densidad final 9 022 | Niveles 6→4, perfil 12→4 y la misma sustitución de hoja; bajar densidad 2→1.6 para cumplir el límite |
| Sapling adulto | Inicial acotado 6 592 → copa ajustada 5 692 → densidad final 7 764 | Parámetros del operador: perfil esférico, longitudes/ángulos, tamaño de hoja .18→.65 y cantidad 32→60. Se conserva su hoja hexagonal nativa de cuatro triángulos |
| Sapling viejo | Inicial acotado 9 312 → copa ajustada 6 624 → densidad final 9 048 | Cambios equivalentes, hoja .18→.75 y cantidad 32→60; ramas principales/secundarias 22/7→20/6 |

Las cifras de los distintos escalones son las mallas finales limpias, excepto donde se indica «brutos». El primer adulto Easy Tree queda en 234 601 tras limpiar, todavía muy por encima del presupuesto. No se ha aplicado Decimate ni simplificación para ocultar el exceso. Se triangulan las mallas de addons y eliminan caras degeneradas/de área ≤1e-10 m² y vértices sueltos: Easy Tree final elimina 996/1 098 triángulos, Sapling ninguno. Los conteos brutos y la limpieza constan por intento.

**La versión Easy Tree final es una adaptación híbrida.** Usa el esqueleto, mallado, ramillas visibles e inserciones del addon; reemplaza `Make Leaf` en memoria por el hexágono plegado RF1. El largo local de esa hoja es .35 m antes de la escala de instancia y la normalización del árbol. El ajuste inicial de divisiones 2×3 se conserva en la configuración, pero deja de definir la forma al sustituir la salida de `Make Leaf`. No se presenta ese aspecto como el resultado original de un clic del addon.

Sapling usa su representación de hoja y sus controles públicos. El punto de partida ya estaba acotado respecto a `small_maple`: menos ramas, divisiones de tallo desactivadas, curvas y bevel de menor resolución, tamaño/ángulos para copa ancha. Por tanto, tampoco se presenta como el preset sin cambios. El manifiesto registra los parámetros efectivos y las diferencias respecto al archivo instalado.

En este ensayo, **Sapling exigió menos intervención en el generador**: ajustes de parámetros y conversión/exportación, sin sustitución de geometría ni edición de grafos. Easy Tree requirió además cuatro clases de adaptación: API de acceso, resolución interna, contenido de ramilla y representación de hoja. Contar configuraciones no equivale a medir horas ni facilidad de uso para cualquier artista.

El tiempo interno de generación/preparación/exportación de los cuatro candidatos ronda medio segundo en este equipo; los valores exactos están en el resumen. Excluye el arranque completo de Blender y no es una medición de autoría, calidad, FPS ni generación dentro del juego. El tiempo histórico de Q3 pertenece a otro ejecutor y alcance y se excluye de esa comparación.

## Revisión visual y lectura del experimento

Se revisaron imágenes reales en Blender y Godot, incluidas las vistas frontal, lateral, superior, inferior y reverso, además de la estructura sin hojas. La comparación muestra:

- **Q3** conserva el carácter de copa compacta y masas grandes aprobadas, con mayor cobertura visual. Sigue mostrando piezas reconocibles; este ensayo no intenta corregirlas.
- **Easy Tree adaptado** presenta grupos de hojas y ramillas en una copa más estrecha en el adulto. El viejo se extiende más, pero exhibe agrupaciones de madera gruesa, cruces y cambios angulosos al reducir el perfil a cuatro lados. La densidad final aporta follaje sin recuperar el volumen Q3.
- **Sapling ajustado** ofrece ramas secundarias y hojas organizadas a lo largo de tallos, con una copa más abierta y disposición por brazos/pisos. Aumentar hojas mejora su presencia respecto al primer intento escaso, pero persisten huecos y una arquitectura distinta del roble Q3; no se declara conseguida una copa de roble convincente por pasar las pruebas.

Las ramillas visibles de los addons ayudan a explicar la unión de las hojas en estas vistas, en comparación con los soportes invisibles de RF2. Es una observación de sistemas completos que difieren en más variables; no prueba que añadir ramillas por sí solo resuelva el generador propio.

El ensayo demuestra que **ambos addons pueden producir assets opacos, reproducibles y exportables a Godot dentro del presupuesto**, con los ajustes documentados. No demuestra que sustituyan el estilo Q3 sin trabajo adicional. Para seguir explorando follaje de hojas, Sapling es el punto de partida de menor adaptación observado; Easy Tree mantiene interés si se quieren editar componentes Geometry Nodes y proporcionar una unidad propia. La elección artística y cualquier promoción quedan pendientes de revisión del usuario.

Esto no compara generación procedural durante la partida: todos son pipelines Blender → GLB. No se han implementado mapas, bosques, generación por sectores, portado de algoritmos a Godot, LOD o rendimiento de un mundo. Tampoco se afirma mejora de IA ni generalización a otras semillas, presets o especies a partir de estos cuatro candidatos.

## Incidencias y procedencia

Easy Tree conserva la incompatibilidad ya documentada de asignación histórica `modifier['Socket_*']` en Blender 5.2.1; el ensayo carga el grupo y asigna sus entradas por nombre mediante un wrapper, sin reparar el addon instalado. La gran complejidad inicial y los intentos fuera de presupuesto quedan registrados.

El primer adaptador Sapling convirtió erróneamente `handleType` a entero al leer una declaración previa del módulo; existe una segunda declaración efectiva como enum. El preset ya proporcionaba la cadena correcta. Se corrigió el adaptador para consultar RNA: **no era un fallo del addon ni una reparación necesaria de sus presets**. Las configuraciones finales no requieren conversiones adicionales y su registro `rna_type_adaptations` está vacío.

Fuentes: [Easy Tree del autor](https://github.com/jacobcjohnston/Easy-Tree) y [Sapling Tree Gen](https://extensions.blender.org/add-ons/sapling-tree-gen/); se ejecutan las instalaciones locales cuyos hashes figuran en [addon-sources.json](addon-sources.json). Los assets/grafos de los addons solo aparecen en resultados regenerables ignorados por Git, no como fuentes nuevas del generador propio. La hoja geométrica de sustitución procede de RF1 del repositorio.

## Reproducción

Desde la raíz y con los addons ya instalados en `~/.config/blender/5.2/extensions/blender_org/`:

```sh
python3 scripts/verify_addon_comparison.py --output artifacts/addon-comparison/otra-comparacion --visual
python3 scripts/addon_comparison_evidence.py --study artifacts/addon-comparison/otra-comparacion --output artifacts/addon-comparison/evidencia
```

Usar carpeta nueva. El primer comando reproduce los catorce intentos, repite los cuatro seleccionados, prepara seis presentaciones y verifica GLB/Godot. El intento inicial Easy Tree viejo se espera rechazado y no detiene los candidatos válidos. Cada Blender/Godot tiene 120 s; el supervisor de intentos tiene un límite agregado finito. Las capturas se dividen en lotes de dos modelos. BLENDER_BIN/GODOT_BIN permiten cambiar rutas, manteniendo las versiones comprobadas. Sin `--visual` se verifica importación pero no se genera la evidencia gráfica necesaria para el segundo comando.

Configuraciones: [addon-comparison.json](../../../presets/addon-comparison.json). El ensayo no requiere credenciales, descargas ni instalaciones automáticas. No modifica los presets de producción ni convierte un resultado de comparación en la nueva opción predeterminada.
