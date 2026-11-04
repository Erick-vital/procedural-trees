# F5: estructura Python y separación espacial

Fecha: 2026-11-03. Ensayo autorizado tras aprobar artísticamente F4.
[Protocolo fijado](../../../../plans/f5-estructura-espacial.md).

## Alcance y reproducción

Este experimento separa dos cambios: transición de la estructura Q1b/Q3 de
Geometry Nodes a Python y regla espacial sobre esa misma estructura Python.
Las diferencias entre la base histórica y la base Python no se atribuyen a la
regla. Las recetas/alias de producción y las fuentes históricas permanecen intactos.

`BranchStructure` guarda jerarquía, IDs, puntos y radios con semillas por rama.
El adaptador `blender/f5_structure.py` hornea sus curvas en un grupo experimental
independiente y reutiliza volumen/moldes Q3, normalización Q2 solo Z y el
procesador pintado/cruzado 2.2.0. Atlas y máximo dos materiales conservados.
Los manifiestos declaran `experimental`, `base_generation=f5_python_experimental`
y `experimental_base_substitution`: **no son ejecuciones sin cambios de la receta
aprobada**, aunque reutilicen sus parámetros/procesadores y conserven su resolución.
Reproducirlos exige el adaptador F5; el CLI de producción sigue generando la base
histórica. No se registra una receta nueva ni se promueve un resultado artístico.

Desde la raíz del repositorio, en directorios nuevos:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
python3 scripts/verify_branch_space.py --stage generate --output artifacts/f5/otra-evaluacion
python3 scripts/close_branch_space.py --study artifacts/f5/otra-evaluacion
python3 scripts/verify_branch_space.py --stage review --output artifacts/f5/otra-evaluacion
python3 scripts/branch_space_evidence.py --study artifacts/f5/otra-evaluacion --output /tmp/f5-evidencia
```

Blender requiere el entorno fijado y Godot un escritorio real. Generación
limitada a 120 s por árbol y revisión a 180 s por subproceso, con terminación del
grupo completo. Entradas resueltas, semillas y hashes se congelan en
`frozen-inputs.json` y `sources.json` antes de generar. Matriz permanente:
`configs/verification/f5-v1.json`. Resultados de esta ejecución:
`artifacts/f5/ensayo-01/`, con galería `index.html` y cierre `closure/verification.json`.

## Regla y métrica

Dos barridos deterministas por secundarias; nueve alternativas por rama:
0, ±15°, ±30°, ±45°, ±60° respecto a su dirección actual. La suma de dos
barridos puede llegar a ±120°. Solo gira alrededor de Z desde el nacimiento:
conserva tronco, primarias, nacimientos, alturas y radios. No poda ni añade ramas.
El desempate minimiza penetración de cápsulas entre opciones con igual cantidad
de parejas conflictivas. La dirección actual siempre participa.

Una pareja de ramas distintas con cápsulas solapadas cuenta como un conflicto,
independientemente de cuántos segmentos se solapen. Se normaliza por longitud
sumada de ejes. Radio máximo por segmento y factor `max(1, escala_Z)` tras Q2:
**proximidad conservadora, no intersección exacta de mallas**. La sección puede
ser elíptica; no se supone un radio circular exacto después de normalizar.
La métrica cubre tronco, primarias y secundarias; los conectores añadidos para
el follaje quedan fuera de ese diagnóstico, pero sí cuentan en el presupuesto
total del árbol. Sus posiciones y selección pueden cambiar al cambiar las guías.
La zona legítima padre–hijo se excluye localmente, hasta dos veces la suma de
radios desde el origen del hijo. El resto de esa pareja sí se evalúa.

La generación conserva métricas sobre curvas completas antes/después de Q2.
El cierre es la comparación definitiva: usa **solo los anillos retenidos por la
simplificación de madera**, comprueba sus centros contra los puntos Python
transformados y vuelve a medir con escala Z real. Así no se atribuyen al asset
exportado distancias calculadas sobre un eje que después fue simplificado.
Las comprobaciones GLB verifican además geometría, materiales, texturas, UV,
normales, presupuesto y correspondencia con el procesador pintado.

Los treinta casos están fijados antes del lote: diez por edad, semillas Q3,
perfiles pintados 2.2.0, copa 17 y pintura 2718. IDs 00–03 de cada edad son
diagnóstico; 04–09 son reservados. No se reajusta la regla al ver reservados.
El objetivo fijado es −25 % de mediana de conflictos/m y ≥90 % de longitud en
cada pareja, sin nuevos fallos. Un denominador cero se conserva como indefinido.

## Resultados

Sesenta árboles finales completos: **3044–6772 triángulos, dos materiales**, atlas
conservados y exportación reimportada válida. Generación por árbol 3,13–5,59 s
bajo las condiciones registradas; no es un benchmark de FPS.

| Conjunto | Casos | Mediana base (conflictos/m) | Mediana candidata | Reducción |
| --- | ---: | ---: | ---: | ---: |
| Todos | 30 | 0,06241149 | 0,00843206 | 86,49 % |
| Diagnóstico | 12 | 0,03500159 | 0,00867576 | 75,21 % |
| Reservados | 18 | 0,06307324 | 0,00414638 | 93,43 % |

**El objetivo de mediana fijado se cumple**, tanto globalmente como en reservados.
Longitud final sumada: **2733,8108 m en ambos conjuntos**; ratio mínimo por pareja
1,0. Ninguna pareja aumenta su recuento final. Diez parejas reducen conflictos.

La mejora tiene un límite importante: **no es uniforme entre edades**.

| Edad | Mediana base → candidata (conflictos/m) | Reducción de mediana | Parejas conflictivas sumadas base → candidata |
| --- | --- | ---: | ---: |
| Joven | 0,06244990 → 0 | 100 % | 9 → 2 |
| Adulto | 0,00832125 → 0,00832125 | 0 % | 6 → 6 |
| Viejo | 0,06583789 → 0,06391771 | 2,92 % | 94 → 90 |

En total son **109 → 98 parejas conflictivas (−10,09 %)**. La gran reducción de
mediana global no equivale a esa reducción de suma: muchos casos jóvenes pasan
a cero y los viejos conservan conflictos. Esta regla solo gira secundarias;
no puede resolver todos los conflictos de tronco/primarias. No se presenta como
una solución general de competencia espacial ni como ausencia de intersecciones.

**227 pruebas** correctas y **69 comprobaciones de cierre** correctas, además de
sesenta auditorías completas de exportación. Error máximo de correspondencia
entre ejes y centros de anillos: **1,15 µm**. Seis repeticiones (ambos miembros de
joven-00/adulto-00/viejo-00) producen GLB idénticos. Tres regresiones históricas
(joven-07/adulto-00/viejo-00) reproducen exactamente los GLB aprobados de madera
2.2.0. La transición histórica → Python cambia geometría y se registra aparte;
no se atribuye a la regla espacial.

La propuesta de regla y su implementación proceden de Codex en esta sesión.
Las repeticiones y el lote usan entradas guardadas, sin llamadas independientes
a modelos. La comparación acredita únicamente las medidas de este protocolo,
no mejora artística, generalización botánica ni rendimiento gráfico.

## Revisión visual y decisión

Godot 4.7.2 importó los sesenta assets y pasó treinta informes técnicos.
**480 capturas reales** con cámaras/luz compartidas por pareja: frente, perfil,
perspectiva y superior, con copa y madera descubierta. El agente inspeccionó
**156 imágenes únicas seleccionadas**: frente de copa y perspectiva de madera
en todas las parejas, más las ocho vistas completas de joven-02/adulto-07/viejo-02.
El resto está disponible en la galería, sin presentarlo como inspección visual
exhaustiva. [Auditoría, selección y hashes](verification.json).

Resúmenes por edad: [jóvenes 00–04](joven-0.jpg), [05–09](joven-1.jpg);
[adultos 00–04](adulto-0.jpg), [05–09](adulto-1.jpg);
[viejos 00–04](viejo-0.jpg), [05–09](viejo-1.jpg).
Parejas completas: [joven-02](joven-02.jpg), [adulto-07](adulto-07.jpg),
[viejo-02](viejo-02.jpg).

No se observan materiales ausentes ni pérdida de partes completas en la selección.
En jóvenes cambian el reparto lateral y algunos huecos, sin una poda del esqueleto;
la plenitud no se acredita por la métrica. Adulto-07 y viejo-02 tienen diferencias
visuales discretas, coherentes con el beneficio limitado por edad. Se conservan
la pintura, lectura de tronco/primarias y carácter general entre ambas variantes.
Persisten cantos de cruzadas y soportes finos difíciles de juzgar a distancia;
no se certifican universalmente todas las uniones, sombras ni orientaciones.

**F5 cerrada técnicamente para este ensayo; aceptación artística pendiente.**
Cumple el objetivo numérico fijado, con alcance limitado y sin adoptar una nueva
receta de producción. Antes de una promoción hace falta valorar la base Python
y la candidata, especialmente el cambio de copa en jóvenes. F6 no se inicia.

## Límites de reproducción y ensayos previos

Los `.blend` F5 contienen curvas horneadas para esa entrada: modificar un socket
no vuelve a ejecutar el algoritmo Python. Para otra semilla o parámetros se
regenera con el adaptador; no se ofrece edición paramétrica interactiva nueva.
Los GLB de `reference/` son intermedios históricos RF3 del procesador, distintos
de los sesenta árboles finales pintados a los que se aplica el presupuesto.

Los intentos de integración `pilot-01`–`pilot-03` se conservan en `artifacts/f5/`:
error de composición de ruta antes de Blender; importación de `jsonschema` no
incluida en Python de Blender, junto al bloqueo de audio al cerrar dentro del
sandbox; y metadatos de resolución alterados que el auditor rechazó. Se corrigió
el adaptador para usar el validador disponible y declarar la sustitución fuera
de la resolución sellada. `pilot-04` pasó la pareja joven-00. La regla espacial,
los ángulos y el protocolo de reservados no se ajustaron a raíz de esos intentos.


## Valoración posterior del usuario — 2026-11-03

[Comentario registrado](user-review.json): el resultado con follaje gusta mucho;
la madera descubierta resulta extraña, con poca lectura de ramificación y haces
que parecen estrellas. La aceptación artística integral sigue sin concederse.
El resultado numérico permanece válido dentro de su métrica; no acredita una
arquitectura de ramas convincente. La dirección propuesta es revisar primero
una rama de muestra y su red de ramillas conservando la copa como referencia.
No se ha implementado esa revisión.
