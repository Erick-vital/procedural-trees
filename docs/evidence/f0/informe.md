# F0 — entorno y contrato mínimo

Fecha: 2026-10-22. Alcance: F0 del [plan v1](../../../plans/v1-generador-arboles.md). No se adelantó F1.

## Resultado de integración

Ejecución: `python3 scripts/verify_f0.py --visual` desde la raíz. Versiones fijadas en el [README](../../../README.md). Prueba con Geometry Nodes reconstruidos mediante `bpy`, sin conexiones manuales.

- Curva poligonal de tres puntos → `Curve to Mesh`, perfil de ocho lados y tapas.
- Icosfera de 20 triángulos → `Instance on Points` → `Realize Instances`.
- Dos materiales Principled simples → unión → `new_from_object` evaluado → exportador GLB con selección y conversión Y arriba.
- Resultado evaluado: 36 vértices, 64 triángulos; 44 de corteza y 20 de follaje. Coordenadas finitas y áreas no degeneradas.
- Dos sesiones limpias producen el mismo hash de geometría normalizada, con posiciones, triángulos y asignaciones de materiales. No se exige igualdad binaria del GLB.
- Godot importa el GLB como `PackedScene`; comprueba 64 triángulos, dos materiales y caja transformada con tolerancia de 0.1 mm. Conserva curva y follaje.
- Caja Blender aproximada: mínimo `(-0.186655,-0.310384,-0.011940)`, máximo `(0.886655,0.710384,2.6)` m. La pequeña extensión bajo Z=0 pertenece al perfil del primer segmento inclinado, no a un error de escala.
- Revisión visual de la captura de Godot con interfaz: curva marrón y copa verde facetada visibles, unidas y completas. La escala y los ejes se verifican numéricamente; la captura por sí sola no demuestra metros.

La [captura seleccionada](godot-preview.png) corresponde a Godot Compatibility/OpenGL en NVIDIA RTX 5060. No constituye evaluación visual de un roble ni medición de rendimiento. Informes compactos: [integración](summary.json) e [inspección Easy Tree](easy-tree-review.json). Salidas completas regenerables en `artifacts/f0/`.

Las pruebas del contrato cubren ambos presets y rechazo de profundidad no soportada, exceso de ramas, NaN/Inf, booleanos como números, densidad negativa, semilla inválida y campos/algoritmos desconocidos. El límite de trabajo de la sonda es fijo y cada proceso tiene timeout de 120 s.

## Revisión y decisión de reutilización

**Decisión: construir grupos mínimos propios, sin copiar componentes ni adoptar estas extensiones como dependencias.** Se necesita una estructura de dos niveles, semillas explícitas, masas low-poly e interfaces reconstruibles. Ambos candidatos incorporan más funciones de las necesarias para esta fase.

### Easy Tree

Fuente primaria: [repositorio del autor](https://github.com/jacobcjohnston/Easy-Tree), commit `ff95ef5ab04358978b8d0863c1c2256951359fc0`; [versión publicada 1.0.1](https://extensions.blender.org/add-ons/easy-tree/versions/). El repositorio inspeccionado declara 1.0.0; no se trató como el paquete publicado 1.0.1.

Se clonó y se cargó localmente `assets/assets.blend` en Blender 5.2.1. El grupo principal `Simple Tree Generator` contiene 16 nodos; hay grupos separados para esqueleto, ramas, mallado y hojas, entre otros. La inspección JSON conserva nombres y sockets. Tiene socket Seed; el operador elige una semilla aleatoria y accede a identificadores `Socket_*` fijos. Se puede controlar el grafo desde Python adaptando el acceso, pero no se probó generación completa ni exportación de sus árboles.

Se reprodujo una incompatibilidad concreta: `modifier['Socket_16'] = 17`, empleado por el operador, falla en Blender 5.2.1 con `TypeError: id properties not supported for this type`. El `.blend` carga, pero eso no demuestra que la extensión funcione sin cambios. La sonda propia verifica en cambio `modifier.properties.inputs[socket.identifier]['value'] = valor`, con `interface.new_socket`. El valor de radio enviado es 0.12 m, distinto al predeterminado 0.05 m.

Manifest y `LICENCE.txt` indican GPLv3; algunos encabezados de Python dicen MIT, una inconsistencia del repositorio inspeccionado. La ficha de versiones declara GPL-3.0-or-later y texturas CC0. No se reutilizaron código, grafos ni texturas; si cambia la decisión habrá que identificar las condiciones del recurso exacto.

Reproducción de la inspección (clon fuera del repositorio):

```sh
git clone https://github.com/jacobcjohnston/Easy-Tree.git /tmp/arboles-f0-easy-tree
git -C /tmp/arboles-f0-easy-tree checkout ff95ef5ab04358978b8d0863c1c2256951359fc0
blender --background --factory-startup --threads 1 --python-exit-code 1 --python scripts/inspect_easy_tree.py -- /tmp/arboles-f0-easy-tree artifacts/f0/easy-tree-review.json
```

### Modular Tree / MTree

Fuente primaria: [fork mantenido GoodPie](https://github.com/GoodPie/modular_tree), commit `ab71f84106fc28c3c5e6c7c92c2e404ab2f785be`; [versiones de la extensión](https://extensions.blender.org/add-ons/modular-tree/versions/). Se clonó e inspeccionó código localmente; no se instaló ni ejecutó su generación ni se comprobó compatibilidad efectiva con Blender 5.2.1.

`python_classes/nodes/base_types/node_tree.py` define `mt_MtreeNodeTree`: su estructura usa nodos propios, no grupos Geometry Nodes intercambiables. `operators.py` genera mediante `m_tree.Tree`, `TrunkFunction`, `BranchFunction` y `ManifoldMesher`; `m_tree_wrapper.py` carga una biblioteca nativa distribuida en wheels. El código permite semillas para tronco y ramas; Quick Generate interpreta 0 como aleatoria. `resources/node_groups.py` construye Geometry Nodes para distribución de hojas, con socket Seed. El README presenta exportación Pivot Painter para Unreal; no aporta prueba local de GLB/Godot.

La documentación del proyecto distingue addon GPLv3 y núcleo MIT. La ficha 5.5.2 anuncia Blender 5.1, con mínimo 4.3.1; no se asumió que eso probara 5.2.1. Integrar su núcleo, adaptar el mallado y verificar wheels ampliaría el alcance sin resolver una necesidad de F0.

Revisión reproducible: clonar el repositorio indicado, checkout del commit y leer los archivos citados. Es una revisión de fuentes, no una prueba de la extensión.

## Incidencias y pendientes

Una primera ejecución dentro del sandbox bloqueó el cierre de Blender: `pa_write() ... Operation not permitted`; las ejecuciones afectadas agotaron el timeout. La ejecución fuera del sandbox completó la ruta y la captura. El acceso antiguo a sockets falló y fue sustituido por la API comprobada. Hay aviso de deprecación de `Material.use_nodes` para Blender 6.0, sin fallo en 5.2.1.

F0 deja un contrato y dos presets válidos; todavía no hay un algoritmo que los transforme en robles. F1 debe implementar el mapeo de todos los parámetros, grupos separados, semillas de estructura/follaje y validación visual del árbol completo. No se ha calibrado el presupuesto de 10 000 triángulos ni evaluado una mejora de IA.
