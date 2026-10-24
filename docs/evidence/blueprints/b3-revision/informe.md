# B3: hojas jóvenes y contacto de 20 m resueltos

Fecha: 2026-10-23. **Revisión implementada y verificada técnicamente.**
La matriz termina con `passed=true`: 22 generaciones válidas, tres rechazos
previstos, cuatro repeticiones idénticas y 84 comprobaciones de invariantes.
80 pruebas Python correctas y regresión adicional ejecutada en Blender.
Los dos pendientes de la [matriz inicial](../b3/informe.md) quedan resueltos.
La aceptación artística del usuario de los perfiles nuevos sigue pendiente;
solo viejo-09 conserva su aprobación previa. B4 y lote RF5 no se iniciaron.

## Cambio de tamaño en jóvenes

Receta nueva: `blueprints/roble_copa_ancha/1.2.0.json`. Las recetas 1.0.0 y
1.1.0 permanecen intactas. El perfil `joven` usa hoja nominal **0,45 m**, antes
1 m, con la misma variación ±10 %, seis hojas por grupo y 264 grupos.
La escala de planificación sigue en 1 m. En joven-00 y joven-07 se verificó:

- Igual madera base, soportes, conexiones, raíces, ejes y conteos.
- Todas las longitudes de hoja son exactamente ×0,45 respecto a B3 inicial.
- 1584 hojas, 7324 triángulos y tres materiales por árbol, igual coste anterior.
- Una sola configuración de edad para ambas semillas, sin ajustes particulares.

La semilla 1007 ya fue inspeccionada en B3 inicial; **no es una nueva reserva**.
También se conservaron los controles 2007/3007 como casos reutilizados.

[Antes/después](young-before-after.jpg), [resumen de jóvenes](young-summary.jpg).
Se volvieron a capturar los dos GLB anteriores usando **exactamente las cámaras
de los nuevos**, con la misma iluminación y resolución Godot. La copa queda
más contenida y las bifurcaciones se leen mejor; disminuye el dominio de placas
grandes. Persisten concentración de hojas, láminas angulosas y solapamientos.
La revisión no afirma una aprobación artística ni una mejora botánica.

## Causa del contacto fallido y corrección

La consulta BVH de polígonos daba **0,000241903 m** para una inserción del caso
20 m/moldes 0,2 m. Sobre los triángulos reales de Blender, el punto está a
**0,000000409 m** usando doble precisión. La distancia de la consulta anterior
produjo un falso rechazo. [Diagnóstico mínimo](initial-surface-diagnostic.json)
y [regresión Blender](contact-regression.txt).

Evaluar toda la matriz contra la triangulación real también descubrió pequeñas
desviaciones auténticas en otras proyecciones que el comprobador anterior no
advertía. Cambiar solo la distancia BVH por triángulos no bastó: los ensayos
provisionales `b3-controls-03` y `b3-controls-04` conservaron esos fallos y no se
usan como aceptación. Se separaron dos responsabilidades:

1. **Evaluación:** distancias y proyecciones punto/triángulo en float64 sobre
   `mesh.loop_triangles`, con búsqueda acotada por cajas. El BVH solo acelera la
   selección inicial de cara; su distancia float32 no decide la aceptación.
2. **Distribución `foliage-canopy@0.1.1`:** conserva la proyección histórica si
   está a menos de 0,1 mm de la rama triangulada. En caso contrario, proyecta
   sobre esa superficie real, con corrección máxima **1 mm**. Una corrección
   mayor sigue siendo un error explícito. No mueve vértices de madera.

La tolerancia final continúa en **0,1 mm**, sin ampliarla. Cada manifiesto
registra versión, consultas corregidas, desplazamiento máximo y cota de
corrección. El adaptador es `blueprint-blender-1.1.0`; distribución 0.1.0
conserva su ruta histórica. El esquema admite explícitamente 0.1.0 y 0.1.1;
la resolución selecciona la versión a partir del componente registrado.
No se interpreta silenciosamente una receta antigua como distribución nueva.

| Caso | Consultas corregidas* | Soportes finales desplazados | Mayor desplazamiento |
| --- | ---: | ---: | ---: |
| Piloto viejo-09 | 0 | 0 | 0 |
| viejo-00 | 2 | 2 | 0,104491 mm |
| viejo-03 | 1 | 1 | 0,101237 mm |
| viejo-07 | 1 | 1 | 0,149372 mm |
| adulto-00 / adulto-07 | 0 | 0 | 0 |
| joven-00 / joven-07 | 0 | 0 | 0 |
| 2 m / moldes 3 m | 35 | 10 | 0,533882 mm |
| 20 m / moldes 0,2 m | 0 | —** | 0 |

\* Incluye intentos descartados por altura/longitud. No equivale al número final
de soportes modificados. ** El ensayo anterior no exportó; se comprobaron la
referencia base idéntica y la inserción que había fallado, conservada exactamente.
La nueva regla es común para todas las semillas; no usa identificadores de caso.

El caso de 20 m genera **264 conexiones, 1584 hojas, 10572 triángulos y tres
materiales**, con altura solicitada conservada. Usa 2021 de 2048 intentos:
1727 rechazos por longitud y 30 por altura. Sigue cerca de la cota de trabajo;
no demuestra que cualquier combinación vecina complete su cupo.
[Vista de madera y copa](extreme-20m.jpg).

## Verificación y conservación

- **80 pruebas Python** correctas. Incluyen perfiles por edad, versiones,
  rechazo de entradas, presupuesto, distancias a plano/bordes y triángulos
  largos/estrechos/degenerados. [Salida](unit-tests.txt).
- Regresión Blender del punto original: acepta contacto real; rechaza una
  separación de 1 mm a ambos lados; comprueba la cota de corrección de 1 mm,
  conservación por debajo de 0,1 mm y malla intacta.
- Piloto 1.2.0 **idéntico byte por byte** al GLB B0 aprobado. Ninguna consulta
  suya necesita corrección. Adultos de control también conservan GLB idéntico.
- Madera, normales exportadas y material de corteza iguales a los siete Q3
  históricos, incluso donde cambian mínimamente las inserciones añadidas.
  [Comparación](q3-comparison.json). No se redujeron polígonos.
- Repeticiones de viejo-00, adulto-00, joven-00 y extremo de 20 m idénticas.
  Semilla de copa conserva madera; semilla base separada cambia estructura.
- Los 22 GLB de generación se reimportaron en Blender: todas sus inserciones
  cumplen la tolerancia sobre la **madera importada del GLB**, además de sobre
  la malla previa. Máximo exportado de toda la matriz: **0,0000980403 m**;
  extremo de 20 m: **0,0000550085 m**. [Informe](export-contacts.json).
- 28 GLB Godot de la matriz: 18 copas únicas y diez derivados de madera.
  252 capturas de matriz y 18 de comparación anterior: **270 capturas reales**.
  Los dos GLB de antes/después son adicionales a los 28 de la matriz.
  Se revisaron láminas seleccionadas de jóvenes, edades, controles y extremo.
- Generación sin render Blender: 2,078–4,491 s; GLB 145804–546284 bytes.
  Presupuesto máximo observado: 12492 triángulos/3 materiales. No son FPS.

Los controles originales, incluyendo el extremo y el rechazo de copa vacía,
continúan presentes. No se convirtió el fallo anterior en rechazo esperado ni
se recortaron rangos para hacerlo pasar. El caso 2 m/moldes 3 m sigue siendo
visualmente inadecuado pese a su validez técnica. Los perfiles continúan
`experimental`; los rangos permitidos no son una certificación de todas sus
combinaciones. [Matriz e invariantes](verification.json),
[contactos y procedencia](contact-and-provenance.json).

## Reproducción

```sh
python3 scripts/verify_blueprint_controls.py --matrix configs/verification/b3-v3.json --output artifacts/blueprints/otro-b3-revisado --visual
python3 scripts/blueprint_revision_evidence.py --study artifacts/blueprints/otro-b3-revisado --previous artifacts/blueprints/b3-controls-02 --output artifacts/blueprints/evidencia-revision
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/roble_copa_ancha/1.2.0.json --instance presets/blueprints/b3-v2/joven-00.json --output artifacts/blueprints/otro-joven --no-render
```

Usar carpeta nueva para cada matriz y para la comparación visual. Mismos Blender
5.2.1/Godot 4.7.2 de B2; generación ≤120 s y pruebas/capturas ≤180 s por
subproceso terminable. La revisión visual requiere interfaz real fuera del
sandbox si este bloquea audio/sockets. La generación individual sigue siendo
autónoma; la matriz usa B0 y el ensayo anterior **solo como comparación**.
La segunda orden requiere los GLB anteriores y el lote Q3 histórico conservados.

Galería local: `artifacts/blueprints/b3-controls-05/index.html`.
Capturas anteriores recapturadas: `inspection/joven-00-before/` y
`inspection/joven-07-before/`, con cámaras idénticas a sus parejas.
Los originales de B3 inicial y su fallo permanecen conservados.
