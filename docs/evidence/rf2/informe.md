# RF2 — follaje sobre una rama Q3

Fecha: 2026-10-22. Continuación autorizada por el usuario tras RF0/RF1, conforme al [plan activo](../../../plans/rediseno-follaje.md). RF2 implementada y verificada técnicamente. **La salida visual no está conseguida:** los portadores invisibles todavía dejan hojas suspendidas. RF3 no se ha iniciado.

## Resultado revisable

- [Q3 frente a longitudinal y terminal, con detalle Blender/Godot](comparison.jpg).
- [Matriz de tres densidades y dos orientaciones por patrón](matrix.jpg).
- [Controles aislados](controls.jpg) y [recorridos virtuales superpuestos para diagnóstico](supports.jpg).
- [Resumen técnico](summary.json), [bloqueo de referencia](reference-lock.json), [configuración base](longitudinal-medium-spec.json) y [30 pruebas](unit-tests.txt).

Galería completa: `artifacts/foliage/rf2-acceptance-final/index.html`. Cada caso contiene `branch.glb`, `scene.blend`, cámaras, manifiesto, soportes/colocaciones y capturas. La referencia está en `reference/`; el candidato longitudinal medio, en `longitudinal-r0-medium/`.

## Referencia y condiciones

Se conserva exactamente `q3:primary:100`, seleccionada en RF0, y se incorporan **sus tres secundarias Q3 originales**, `200`, `201` y `202`, para inspeccionar el follaje con contexto. Son las curvas 0–2 del canal `Secondary` de la estructura guardada. No se generan nuevas ramas de madera. Se extraen los polígonos originales y se registran sus índices; la primaria conserva el hash RF0.

La madera conjunta tiene **464 triángulos**. El follaje Q3 asociado se selecciona por los atributos guardados `q3_level`/`q3_branch`, no por proximidad espacial: 300 triángulos. La referencia completa suma 764 triángulos. Se mantienen especificación Q3, semillas, normalización y archivos fuente intactos.

Las seis vistas generales se fijan desde la caja de esa referencia Q3: frontal, lateral, superior, inferior oblicua, oblicua y reverso. Se añaden tres acercamientos comunes, centrados en el 82 % de la longitud de la primaria RF0 y con escala vertical de 2.34 m. El encuadre de detalle es deliberadamente un recorte; no se reajusta al candidato ni se exige que contenga todo el follaje Q3. Las nueve cámaras son ortográficas a 900×900. La iluminación mantiene los ajustes de RF0/RF1 por renderizador; los cambios de brillo entre Blender y Godot no son una métrica.

## Contrato y algoritmo experimental

Versión **`foliage-branch-0.1.0`**, separada de `TreeSpec` y de RF1. [Esquema](../../../schemas/foliage-branch.schema.json), [preset](../../../presets/foliage-branch.json), reglas espaciales en [foliage_branch.py](../../../src/treegen/foliage_branch.py) y adaptador en [foliage_branch_lab.py](../../../blender/foliage_branch_lab.py). No se migra ni modifica el generador estructural Q3.

La unidad visible sigue siendo el hexágono plegado RF1: cuatro triángulos por hoja, pliegue 25°, material verde opaco de doble cara. Se fija largo .24 m para este ensayo de rama, frente a .18 m de la unidad RF1; es una elección explícita dentro del contrato, no una equivalencia oculta. El tamaño se conserva en toda la matriz y tiene un control separado a .32 m.

Se construye un conjunto ordenado de hasta 24 portadores virtuales, repartidos entre las cuatro curvas originales. Cada uno tiene id estable, rama padre, posición longitudinal, punto de inserción en la superficie de madera y recorrido de tres puntos. Las posiciones candidatas recorren gradualmente la zona distal —58–96 % de longitud de arco, con perturbación de ±1.2 puntos porcentuales—, sin usar altura Z como sustituto de contexto de rama. Los primeros 16 permanecen idénticos si se aumenta la cantidad a 20.

La dirección combina la tangente de la rama con una dirección transversal; el ángulo respecto a ella es 50°. El giro de soporte alrededor de la rama toma 0° o 70°. Ese giro cambia el punto angular de inserción y el recorrido, conservando rama padre y posición longitudinal; no se presenta como una rotación de hojas sobre recorridos idénticos. Los marcos se transportan entre segmentos mediante la regla RF1, sin elegir nuevos ejes globales en cada punto.

La matriz usa **16 soportes de .55 m**. La densidad son hojas por metro de portador, separada de su cantidad y del tamaño de hoja. Los patrones comparten recorridos, conteos, tamaños y ejes:

- **Longitudinal:** raíces distribuidas a media separación y múltiplos sucesivos a lo largo del recorrido.
- **Terminal:** esas mismas hojas se trasladan al último 15 % del recorrido; no se cambia simultáneamente su orientación o cantidad para favorecer el resultado.

Los portadores se insertan mediante rayos contra la superficie de su propia rama, sin retocar la madera. La distancia de inserción a la malla conjunta se comprueba con tolerancia de 0.1 mm. Las líneas magenta de diagnóstico muestran los soportes; se crean después de guardar el GLB y la escena, y **no forman parte del asset**. No se añade madera visible ni se representa una especie distinta por cambiar el patrón.

Límites RF2: 4–24 portadores, largo .2–.8 m, 5–20 hojas/m y máximo total de **192 hojas/768 triángulos de follaje** antes de mallar. Se heredan los límites de cada unidad RF1. La matriz usa menos trabajo. El límite de 10 000 triángulos/3 materiales por árbol sigue vigente; este experimento aislado no asigna automáticamente su máximo a todas las primarias.

## Resultados técnicos

Los dos patrones y los dos giros producen los siguientes conteos, con madera idéntica:

| Densidad | Hojas/m | Hojas del subárbol | Triángulos de follaje | Total con madera |
| --- | ---: | ---: | ---: | ---: |
| Baja | 6 | 48 | 192 | 656 |
| Media | 9 | 64 | 256 | 720 |
| Alta | 12 | 96 | 384 | 848 |

Hay doce casos de matriz. Se añaden cinco controles aislados —tamaño, inclinación de hoja, cantidad de soportes, largo de soporte y semilla—, repetición independiente y referencia: **19 GLB exportados/importados en Godot**. Todos pasan geometría válida, presupuesto, materiales, normales, escala y ejes. La inspección independiente del GLB compara posiciones y normales de cada triángulo de madera, además del material de corteza: sus firmas son idénticas en referencia y candidatos. No basta con que coincidan los conteos de madera.

La repetición en una nueva sesión de Blender conserva métricas y colocaciones. Densidad y patrón conservan los recorridos; tamaño e inclinación conservan recorridos y raíces; el control de cantidad conserva los primeros 16 soportes. Cambiar largo de soporte sí cambia recorrido y número de hojas: a .35 m y 9 hojas/m hay tres por soporte, 48 en total. Aumentar tamaño conserva las distancias de raíz a madera; cubrir visualmente un hueco no crea un soporte.

Pasaron **30 pruebas**, incluidas seis nuevas para recorridos anidados, patrones comparables, raíces sobre recorridos, marcos, límites/entradas inválidas y firmas de madera del GLB. Las 17 escenas capturadas suman **153 capturas Godot**, con nueve cámaras cada una; cada archivo pasa el detector de capturas vacías. Las dos restantes —otra semilla y repetición— se verifican sin nuevas capturas. Esto no equivale a aceptación estética ni a una prueba de FPS.

El techo aritmético de la densidad alta, repetido once veces, sería 4 224 triángulos de follaje y 9 516 con la madera del árbol. No se ha generado esa copa, ni se supone que todas las primarias tengan iguales necesidades o que esa cantidad dé cobertura suficiente.

## Revisión visual y decisión de salida

Se revisaron la matriz en Blender, acercamientos, vistas superiores/inferiores, reversos y las capturas Godot seleccionadas, además de los controles y superposiciones de soporte. La lectura es claramente distinta de las masas Q3. Longitudinal organiza pequeñas hojas a lo largo de recorridos; terminal concentra abanicos separados, con huecos mayores entre grupos. El mayor giro desplaza la lectura de esos conjuntos, sin resolver su unión visible.

**Los soportes invisibles no bastan en este ensayo.** En detalle, las hojas siguen pareciendo suspendidas; el patrón terminal acentúa el problema. Para giro 0 y densidad media, las raíces distan de la superficie de madera una media de **.176 m** en longitudinal y **.405 m** en terminal. Son distancias geométricas a la madera visible más cercana; no una métrica de naturalidad. Las inserciones de los portadores sí están sobre la madera, pero ese recorrido intermedio no se ve en el asset.

El control de soporte corto reduce la media a **.131 m** y sigue dejando separaciones perceptibles. Aumentar la hoja a .32 m tapa más espacio, sin cambiar sus raíces. Subir densidad aporta más láminas, pero no incorpora los elementos visibles que explicarían su conexión. Algunas hojas continúan de canto. Los pequeños abanicos terminales también pueden volver a leerse como grupos aislados; no se eligen como solución por su organización regular.

La cobertura a escala de rama es mucho menor que Q3, aunque el caso alto tiene más triángulos de follaje que su referencia. El presupuesto por sí solo no produce la composición buscada. No se atribuye mejora estética, de rendimiento ni de IA; tampoco se declara imposible resolver el estilo con otra organización.

RF2 queda como **experimento técnicamente completo, con criterio visual de salida pendiente**. No se inicia RF3. La siguiente decisión debe revisar la restricción de portadores invisibles: una prueba de ramillas visibles sería un cambio de alcance explícito, todavía sin implementar. También puede iterarse la organización en esta misma escala; no se amplía a copa para ocultar el fallo observado.

## Incidencias y reproducción

Una inserción mostró una diferencia numérica de 12 µm entre las consultas BVH de la rama y de la malla conjunta. Se fijó una tolerancia de comprobación de 0.1 mm, sin desplazar los vértices de madera. El máximo real de cada caso consta en el resumen. Las primeras capturas gráficas agotaron los 120 s al esperar ocho dibujos por vista; no se usan como resultado final. El ejecutor espera ahora dos dibujos completados después de cada cambio de cámara y reparte las capturas en lotes de seis escenas, conservando **120 s por proceso**. Cada lote se verifica contra el informe numérico completo y se comprueba el contenido de sus imágenes.

Desde la raíz, en una carpeta nueva, con Blender/Godot y dependencias fijados en el README:

```sh
python3 scripts/verify_foliage_branch.py --output artifacts/foliage/otra-rama-rf2 --visual
python3 scripts/foliage_branch_evidence.py --study artifacts/foliage/otra-rama-rf2 --output artifacts/foliage/evidencia-rf2
```

`--visual` abre Godot brevemente por lote; sin esa opción solo se verifican geometría e importación y no se puede seleccionar esta evidencia visual. `--rf0` permite indicar otro bloqueo RF0 con los archivos originales disponibles y sus hashes coincidentes. `--preset` cambia la configuración base, pero la matriz conserva sus valores fijos para reproducir este ensayo. BLENDER_BIN/GODOT_BIN permiten cambiar rutas de herramientas; se mantienen las versiones comprobadas. Los resultados y la caché Godot permanecen ignorados por Git; se conserva aquí solo evidencia seleccionada.
