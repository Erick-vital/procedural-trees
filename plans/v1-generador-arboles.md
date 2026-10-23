# Plan v1: generación procedural de robles y evaluación de cambios por IA

Fecha: 2026-10-22  
Revisión: foco en assets de árboles; arquitectura híbrida con Geometry Nodes, automatización con `bpy` y reglas espaciales en Python.  
Estado: F0–F2 verificadas; Q1 0.2.0 rechazada estéticamente por el usuario. Q1b 0.2.1 y copa ajustada Q2 0.3.0 aprobadas por el usuario. En la revisión posterior, el usuario identifica Q3 0.4.0 como última iteración buena y rechaza estéticamente Q3b 0.4.1, que permanece verificada técnicamente. Se discuten alternativas de follaje sin autorizar una nueva implementación. F4–F6 pendientes; F3 diferida fuera del alcance activo. Informes [F0](../docs/evidence/f0/informe.md), [F1](../docs/evidence/f1/informe.md), [F2](../docs/evidence/f2/informe.md) y [Q3b](../docs/evidence/q3b/informe.md).

## Cambio de alcance vigente — 2026-10-22

Por decisión del usuario tras F2, este proyecto se concentra en generar, evaluar y mejorar árboles. La distribución de bosques (F3), el mapa y el terreno se difieren; se estudiarán en un proyecto posterior de terrenos variados y no son requisitos para cerrar esta v1. La generación de terreno no estaba implementada ni formaba parte del generador actual.

Se conservan F0–F2 y los experimentos A/B/C. Godot continúa como destino de los GLB y herramienta de inspección de árboles individuales. El orden activo es Q1 → revisión de sus resultados → Q2 → Q3 → F4 → F5 → F6; la numeración se conserva para no confundir la evidencia previa. El cambio de alcance del bosque no implementó funciones nuevas; la revisión Q autorizada posteriormente se detalla más abajo. La sección F3 queda únicamente como referencia del alcance diferido. Los informes F0–F2 mantienen el contexto histórico de sus verificaciones.

## Revisión de calidad posterior a F2 — 2026-10-22

El usuario señala `viejo-00`, `viejo-03` y `viejo-09` como ejemplos malos de ramificación: haces de piezas gruesas, direcciones repetidas y poco volumen convincente. F2 permanece verificada técnicamente; eso no supone aprobación estética. El [diagnóstico reproducible](../docs/evidence/revision-viejos/informe.md) identifica causas en las reglas actuales, y el [informe Q1](../docs/evidence/q1/informe.md) registra la primera etapa implementada, cuya forma estrecha fue rechazada después por el usuario.

Se prioriza refinar la estructura del árbol dentro del alcance de F1 antes de F4: grosores coherentes con el padre, inclinaciones/curvaturas variadas y reparto espacial. No se inicia la migración Python ni se atribuye una mejora al experimento B por este diagnóstico. Conservar la base 0.1.0 y asignar nueva versión a cambios geométricos; contrastar primero los casos señalados y controles, con semillas/cámaras compartidas, y después el lote completo. La revisión del usuario seguirá siendo necesaria para valorar la calidad.

## Revisión del generador Q, dentro de v1 — 2026-10-22

Se mantiene un único plan: estas correcciones completan la calidad del árbol de F1 y aprovechan la infraestructura F2. No necesitan un proyecto nuevo. Se dividen en dos etapas para comprobar la estructura antes de cambiar la copa y el ajuste de proporciones. La autorización inicial cubrió Q1. Tras revisar y aprobar Q1b, el usuario autorizó continuar con Q2 sobre esa estructura; F4–F6 siguen fuera de esta iteración.

### Q1. Jerarquía y distribución de ramas — verificada técnicamente; forma rechazada por el usuario

- Conservar `oak_geometry_nodes` 0.1.0 reconstruible, los casos F2 y los assets base; añadir 0.2.0 con el mismo contrato de parámetros y semillas explícitas.
- Calcular el radio de primarias y secundarias a partir del radio del padre en el nacimiento; exigir que el hijo sea más delgado. Mantener los conteos de ramas para que la corrección no consista en eliminarlas.
- Variar la inclinación, longitud y elevación de las puntas con altura y semilla. Repartir primarias por sectores con perturbación acotada, sin grupos de direcciones casi idénticas ni grandes huecos accidentales.
- Abrir las secundarias a ambos lados de su padre y derivar longitud/grosor del padre; conservar dos nacimientos por primaria y dos niveles de ramificación.
- Mantener el follaje y el ajuste vertical de F1 para aislar esta revisión; registrar su efecto final, que sigue siendo una limitación pendiente de Q2.
- Verificar los tres viejos señalados y controles de otras edades con semillas conservadas y cámaras/escala compartidas por pareja. Revisar madera sin hojas y copa completa, después los 30 casos, repetición, extremos y exportación/importación Godot.

Aceptación mecánica: ningún hijo con radio mayor que el padre local; conteos originales; inclinaciones principales no idénticas en los presets de cuatro o más primarias; reparto angular acotado por el ancho de sector; geometría válida dentro de 10 000 triángulos/3 materiales; altura válida y reproducibilidad. Estas condiciones comprueban las causas del diagnóstico, sin reemplazar la valoración estética del usuario. No se mide ni se declara lograda la reducción de cruces de F5.

### Q1b. Extensión y carácter de las ramas — verificada y aceptada por el usuario

La revisión visual del usuario rechaza 0.2.0: resuelve grosores incoherentes y agrupaciones, pero los viejos resultan estrechos y ascendentes. Esa revisión motivó Q1b: recuperar ramas largas, gruesas y extendidas como la base, conservando jerarquía y mejor distribución, y añadir ramificación secundaria. Comparar primero los viejos 00/03/09 sin hojas contra 0.1.0 y 0.2.0, con semillas, parámetros y cámaras compartidos. Mantener controles de otras edades y comprobar después lote/extremos.

Cambio explícito del alcance Q1: 0.2.1 admite tres secundarias por primaria en vez de dos, conservando dos niveles y el contrato JSON. No se exige conservar los conteos antiguos ni se atribuye una mejora al experimento B. Se mantienen el follaje y el ajuste Z de Q1 para aislar la estructura. La extensión, longitud y grosor se medirán frente a ambas referencias, sin reemplazar la aprobación visual del usuario.

Q1b produjo treinta candidatos 0.2.1 válidos e importados en Godot; pasaron quince pruebas unitarias y cinco extremos (máximo 9676 triángulos/dos materiales). Los tres viejos señalados recuperan al menos el 95 % de anchura del esqueleto, longitud nativa de primarias y radio medio de las tres primarias inferiores de 0.1.0, con más secundarias y cámaras compartidas. Este criterio nuevo no reemplaza la valoración visual. Los otros siete viejos se midieron sin reajustar la regla: viejo-06/07 conservan el 92.1/88.5 % de anchura; no se afirma recuperación >=95 % en los diez. Véase el [informe Q1b](../docs/evidence/q1b/informe.md).

Q2 se detuvo al recibir esta revisión: su primer borrador y una previsualización quedaron en `artifacts/q2/`, sin aceptación ni promoción. El usuario dio su visto bueno a las ramas Q1b 0.2.1 el 2026-10-22. Quedan aceptadas como referencia estructural para Q2; la aprobación no se extiende al follaje ni a todas las combinaciones extremas del contrato.

### Q2. Copa y proporciones — verificada y copa ajustada aprobada

- Conservar Q1b 0.2.1 como referencia reconstruible de ramas. Retomar el borrador Q2 adaptándolo a esta estructura; el borrador previo usaba Q1 0.2.0 y no constituye una implementación aceptada.
- Revisar la distribución de follaje a partir de la estructura aceptada y la ocupación de alturas/sectores de copa.
- Revisar el ajuste global de altura para evitar deformar accidentalmente la ramificación; conservar unidades y la relación entre ejes medidos y geometría final. La anchura y el grosor aprobados de Q1b forman parte de la referencia: comprobarlos al cambiar follaje o normalización, evitando perder el carácter ancho recuperado.
- Ajustar presets de edad tras revisión visual y repetir las comparaciones con cámaras fijas y la aceptación del lote.

Q2 0.3.0 reutiliza la estructura nativa Q1b y mantiene exactamente su geometría de madera en X/Y. Ajusta Z con la caja de madera, y sitúa el follaje dentro de la altura solicitada; cambiar la copa conserva la madera final Q2. La madera alcanza ahora toda la altura pedida, con cambios de inclinación final de hasta 4.051° frente a Q1b: esta diferencia se presenta sin hojas y requiere valoración visual. No se afirma eliminación de toda deformación anisotrópica.

La copa se distribuye por tramos distales con tamaños/giros por masa; los presets solo ajustan follaje. La escala efectiva se acota a `min(foliage_scale_m,0.24*height_m)` para combinaciones extremas. Se mantienen límites de profundidad y conteos Q1b. Los controles Q2 con todos los parámetros Q1b aíslan el cambio de algoritmo de los presets ajustados; la comparación tiene tres columnas a cámara compartida, usando únicamente Q1b como base.

Pasaron diecisiete pruebas unitarias, treinta GLB distintos/importados/capturados en Godot, repetición, diez parámetros, independencia de madera ante cambios de copa y seis extremos (máximo 9676 triángulos/dos materiales). Véase el [informe Q2](../docs/evidence/q2/informe.md). El usuario aprobó explícitamente la variante de copa ajustada el 2026-10-22. Señala que las masas siguen siendo demasiado similares y solicita propuestas para refinarlas; esto no revoca la aprobación de Q2.

Q1 produjo treinta candidatos 0.2.0 válidos e importados en Godot, con comparaciones a cámara compartida y catorce pruebas unitarias aprobadas. Véase el [informe Q1](../docs/evidence/q1/informe.md). La revisión del usuario rechazó la forma estrecha de Q1 y posteriormente aceptó Q1b. Q2 ya está implementada, verificada técnicamente y aprobada en su variante ajustada. F4–F6 continúan pendientes; Q no introduce mapa, bosque, terreno ni la migración estructural Python de F5.

### Q3. Formas y agrupación del follaje — verificada técnicamente; valoración estética pendiente

El usuario aprueba la copa ajustada Q2, pero señala repetición entre grupos. Q2 instancia una única icosfera de veinte triángulos, solo escalada/girada, y usa la misma cantidad de masas por curva dentro del preset. El usuario autorizó implementar estos tres puntos, conservando Q2 ajustada como referencia:

- Formas asimétricas y contornos distintos por masa, con deformación suave y acotada; evitar ruido fino que solo vuelva más dentadas las facetas.
- Jerarquía de masas dominantes, medianas y pequeñas según nivel y posición sobre cada tramo de rama, con tamaños claramente diferenciados.
- Cantidad y agrupación ligadas a longitud/nivel de rama, con variación acotada y tramos distales distintos.

Autorización del usuario el 2026-10-22: implementar formas asimétricas, jerarquía y agrupación ligada a ramas. La fusión parcial queda como posible ensayo posterior; no se implementa en esta iteración. Comparar viejo-00/03/09 y controles contra Q2 aprobada, con semillas/cámaras compartidas, madera final idéntica y presupuesto de 10 000 triángulos/3 materiales; revisar visualmente y comprobar los treinta casos.

Q3 0.4.0 implementa seis familias deformadas y variación continua por masa. Conserva exactamente la madera final Q2 en X/Y/Z, su normalización, parámetros y semillas. Cambian los conteos y la interpretación de densidad de forma versionada: el control cuantizado se modula por longitud/nivel, con máximos tronco/primaria/secundaria 2/3/2, hasta 110 masas. Se reservan 80 triángulos para hasta 26 masas principales y 20 para las demás; límite derivado y extremo máximo comprobado de 9516 triángulos/dos materiales.

Pasaron dieciocho pruebas, repetición Q2/Q3, efecto de diez parámetros, independencia de madera ante cambios de follaje y seis extremos. Los treinta modelos son válidos/distintos e importados/capturados en Godot; se verifican familias distintas y deformaciones no afines. El agente revisó comparaciones y galerías; la valoración estética del usuario sigue pendiente. Véase el [informe Q3](../docs/evidence/q3/informe.md). F4–F6 continúan pendientes; no se atribuye una mejora de IA ni de rendimiento.

### Q3b. Copa abierta y follaje ligado al grosor — verificada técnicamente; valoración estética pendiente

El usuario valora el volumen Q3, pero pide reducir la compacidad que oculta la estructura: grupos grandes y pequeños entre ramas principales, mayor variación vertical, ramas atravesando huecos visibles desde abajo y una relación clara entre grosor de rama y follaje sostenido. Esta revisión conserva las formas Q3 y la madera Q2 aprobada. Se registra 0.4.1 sin modificar los algoritmos ni lotes anteriores; no se inicia F4–F6.

Implementar grupos con escala/cantidad derivadas del radio nativo de cada rama y su padre, tramos de follaje más cortos y secundarias sin hojas. Comparar primero viejo-00/03/09 y controles, con los mismos parámetros, semillas y cámaras, incluyendo vistas inferiores. Comprobar madera idéntica, altura y presupuesto; medir distribución vertical y visibilidad sin confundirlas con aprobación estética. Verificar después lote, repetición, extremos e importación Godot.

Q3b conserva la madera completa Q2/Q3 y las seis formas Q3. Los radios reales modulan tamaño/cantidad y posición; varían espesor vertical y margen superior. Una secundaria por primaria queda sin hojas; con poca densidad, los grupos se desplazan hacia las puntas y su escala baja un 10 %. Máximos 1/3/2 masas por tronco/primaria/secundaria y dos secundarias foliadas por padre: hasta 85 masas y límite derivado de 8956 triángulos/dos materiales.

Pasaron dieciocho pruebas, repetición, diez parámetros y seis extremos (máximo observado 8116 triángulos). Los treinta modelos son válidos/distintos e importados/capturados en Godot. Los treinta muestran mayor dispersión vertical de grupos y más madera visible en la vista inferior medida; la correlación entre radio de primaria y volumen sumado de follaje es 0.832–0.995. Son diagnósticos reproducibles con límites de vista/resolución, no aceptación estética ni mejora de FPS. El agente revisó comparaciones y galerías; el usuario aún debe valorar Q3b. Véase el [informe Q3b](../docs/evidence/q3b/informe.md).

## 1. Objetivo y demostración final

Construir una infraestructura reproducible donde una IA pueda parametrizar y mejorar un generador de árboles low-poly. El primer algoritmo producirá robles estilizados; la inversión reutilizable será el contrato de generación, ejecución, validación, comparación y exportación.

La demostración final será una colección de 30 robles distintos, exportados a GLB y comprobados en Godot. Se podrá describir un cambio en lenguaje natural, obtener parámetros validados y regenerar los assets. También se compararán versiones del algoritmo con semillas y cámaras fijas.

La v1 debe demostrar tres capacidades distintas:

| Experimento | Intervención de la IA | Evidencia esperada |
| --- | --- | --- |
| A. Parámetros | Convertir una descripción en JSON sin editar código | Solicitud, respuesta validada, árbol y comparación con el preset base |
| B. Reglas | Implementar una regla geométrica mediante un cambio de código revisable | Comparación de la versión base y la nueva con los mismos casos |
| C. Optimización | Proponer e implementar una reducción de complejidad | Menos triángulos, silueta comparable y exportación válida |

Estos experimentos serán acotados y supervisados. La v1 no incluye un agente autónomo que modifique y publique código continuamente.

## 2. Alcance y límites

Incluye:

- Una especie: roble estilizado, con tronco curvo, ramas jerárquicas y masas de follaje low-poly.
- Semillas explícitas, presets y parámetros con unidades y límites.
- Geometry Nodes para el primer generador y el procesamiento geométrico; Python con `bpy` para configurar, ejecutar, renderizar y exportar GLB.
- Módulos Python independientes para las reglas espaciales que se incorporarán en el experimento B.
- CLI y API local mínima que compartan la misma lógica de ejecución.
- Adaptador de IA para convertir texto a parámetros estructurados.
- Validación automática, manifiestos y comparación visual reproducible.
- Inspección de assets individuales en Godot para comprobar escala, materiales, orientación y detalle.
- Un experimento de reglas espaciales y otro de simplificación.

Fuera del alcance activo: mapa, terreno, distribución de bosques (F3), múltiples especies, rigging, viento, simulación física o biológica, texturas complejas, editor visual propio, servicio público, ejecución distribuida, entrenamiento de modelos y sustitución por generación 3D neuronal.

## 3. Decisiones iniciales

- El repositorio parte sin implementación; este documento define el trabajo pendiente.
- El núcleo de contratos, semillas y métricas geométricas será Python sin dependencia de Blender cuando sea viable.
- El primer árbol se construirá con Geometry Nodes: tronco, dos niveles de ramificación y masas de follaje. Se aprovecharán curvas, perfiles e instancias nativos de Blender.
- Python con `bpy` expondrá parámetros, semillas, construcción/carga de grupos, evaluación, materiales, render y exportación. Las búsquedas espaciales y reglas de crecimiento complejas pasarán a módulos Python cuando llegue B.
- Los grupos de estructura, conversión de curvas a mallas y follaje tendrán interfaces separadas. Así podremos reemplazar el cálculo de ramas conservando su procesamiento geométrico.
- La estructura intermedia de ramas se formalizará al introducir el algoritmo Python; no se construirá un motor propio de mallado. Space colonization queda como alternativa futura, sin ser requisito inicial.
- Se explorarán Easy Tree y Modular Tree antes de decidir qué construir o reutilizar. No son dependencias obligatorias ni se presupone que sus grafos puedan editarse con la misma API.
- La geometría será estática y dependiente de semillas, sin necesitar avanzar fotogramas ni conservar cachés de simulación. Repeat Zones o For Each Element se usarán solo si simplifican un grupo en la versión elegida.
- La integración de IA devolverá datos estructurados. El proceso normal de generación no ejecutará código recibido del modelo.
- Los cambios de código de B y C seguirán un ciclo explícito de edición, ejecución, evaluación y revisión.
- Se fijarán versiones concretas de Blender, Godot, Python y dependencias al preparar el entorno. Sus comandos y compatibilidad se verificarán antes de cerrar esa fase.
- El proveedor y modelo de IA se elegirán al integrar A; el contrato permitirá reemplazarlos y usar respuestas guardadas para pruebas sin red.

## 4. Arquitectura y contratos

Flujo inicial, F1–F4:

`texto → adaptador IA → TreeSpec validado → bpy → generador Geometry Nodes → malla evaluada → GLB + capturas + métricas → Godot`

Flujo híbrido al incorporar reglas espaciales en F5:

`TreeSpec → algoritmo Python → estructura de ramas → bpy (curvas/atributos) → grupos Geometry Nodes de procesamiento → malla evaluada → exportación y evaluación`

La orquestación y los contratos de resultados permanecerán estables. La sustitución futura de Blender o la entrada de assets generados por otros medios será posible mediante adaptadores, pero no se implementarán proveedores adicionales en v1.

Componentes separados:

| Componente | Responsabilidad |
| --- | --- |
| Contratos | Esquemas, unidades, rangos, versiones y errores |
| Algoritmos | Generar ramas inicialmente en nodos; después admitir reglas Python reemplazables |
| Ejecutor | Crear trabajos, invocar Blender, gestionar tiempos límite y resultados |
| Adaptador Blender / bpy | Conectar datos y sockets, construir curvas, gestionar materiales, evaluar, renderizar y exportar |
| Grupos Geometry Nodes | Convertir curvas en volumen, colocar follaje, deformar y asignar materiales |
| Evaluación | Validar assets, calcular métricas y comparar versiones |
| Adaptador IA | Traducir solicitudes a especificaciones y registrar procedencia |
| Inspección Godot | Importar variantes y revisar los árboles individualmente |

Estructura propuesta, que se creará conforme se implemente cada fase:

```text
src/treegen/             # Contratos, algoritmos, ejecución y evaluación
blender/                # Entrada, adaptadores y construcción de grupos Geometry Nodes
api/                    # API local sobre el ejecutor
godot/                  # Proyecto y escena de demostración
presets/                # Especificaciones JSON
tests/                  # Casos geométricos, contratos e integración
scripts/                # Comandos reproducibles de generación y verificación
plans/                  # Planes y decisiones de alcance
docs/evidence/          # Informes pequeños y comparaciones seleccionadas
artifacts/              # Salidas regenerables; ignoradas por control de versiones
```

### Especificación y resultados

`TreeSpec` contendrá versión de esquema, identificador y versión del algoritmo, semilla y parámetros. El identificador distinguirá el generador inicial en nodos del generador estructural Python. Parámetros iniciales: altura en metros, radio basal, curvatura, cantidad de ramas primarias, profundidad máxima, proporción de longitud de ramas, inclinación, asimetría, densidad y escala del follaje. Los rangos se publicarán en el esquema; el primer generador admitirá hasta dos niveles de ramas y rechazará profundidades no soportadas. La densidad usará una escala normalizada con conversión documentada a cantidad de masas de copa.

Al introducir Python se definirá `BranchStructure`: identificadores de rama y padre, puntos ordenados, radios y puntos candidatos de follaje en coordenadas locales y metros. Este contrato no contendrá objetos `bpy`. La conversión a curvas y sus atributos será responsabilidad del adaptador; las métricas de conflictos usarán esa estructura antes del mallado.

Las variantes de materiales pertenecerán a un conjunto pequeño y estable. La resolución de malla y los límites geométricos serán controles explícitos del preset técnico. No se confundirá longitud solicitada con tamaño final medido.

Cada trabajo guardará:

- Especificación normalizada y hash; semilla y estado final.
- Versiones de esquema, algoritmo, grupos de nodos, adaptador, código, herramientas y dependencias relevantes.
- Hash de los scripts que construyen los grupos y de cualquier recurso `.blend` utilizado; parámetros y semillas efectivos enviados a los nodos.
- `tree.glb`, vistas fijas, métricas, registro de ejecución y manifiesto.
- En F5: estructura de ramas usada para generar y evaluar el asset.
- Para A: solicitud, proveedor/modelo, configuración y respuesta original, sin credenciales.
- En el proyecto futuro de terrenos/bosques: lista de variantes, semilla de distribución, transformaciones y configuración de sectores; diferido fuera del alcance activo.

La reproducibilidad se evaluará con estructura y geometría normalizadas en el entorno fijado. No se exigirá identidad binaria de archivos GLB ni píxeles idénticos entre distintas GPU o versiones.

### Grupos de nodos y preparación para exportación

Los grupos propios se construirán mediante scripts `bpy` versionados como fuente de verdad; un `.blend` generado será una salida de trabajo. Si se adopta un recurso de terceros que necesite un `.blend` fuente, se identificará ese recurso, su versión y sus condiciones de reutilización. Antes de F2 debe poder reconstruirse o cargarse todo lo necesario desde una sesión limpia, sin conexiones manuales pendientes.

La relación entre campos `TreeSpec` y sockets será explícita y versionada, sin depender del orden visual de los sockets. Las semillas de estructura y follaje se derivarán por separado y se pasarán a los grupos correspondientes. Los cambios de grafo que alteren resultados requerirán nueva versión y regeneración de las referencias.

Se usará la conversión nativa [Curve to Mesh](https://docs.blender.org/manual/en/4.4/modeling/geometry_nodes/curve/operations/curve_to_mesh.html) para dar volumen a las ramas. El follaje reutilizará primitivas low-poly mediante instancias. La distribución y los materiales se mantendrán simples; no se añadirán hojas individuales detalladas como requisito de esta v1.

La salida de exportación será una copia evaluada del árbol: curvas convertidas, instancias necesarias realizadas y mallas con materiales compatibles con glTF. [Realize Instances](https://docs.blender.org/manual/en/4.5/modeling/geometry_nodes/instances/realize_instances.html) convierte las instancias a geometría y puede elevar su coste, por lo que se medirá el presupuesto sobre la malla final. El [exportador glTF de Blender](https://docs.blender.org/manual/es/4.5/addons/import_export/scene_gltf2.html) admite mallas evaluadas al aplicar modificadores; la v1 verificará esa ruta sin depender de exportar instancias de Geometry Nodes mediante funciones experimentales.

Godot recibirá GLB con mallas y materiales; la lógica procedural se ejecutará en Blender antes de exportar. Cada árbol será una variante reutilizable, sin exportar cada ejemplar del bosque como una malla única. La instanciación interna del follaje en Blender y la instanciación de árboles en Godot se medirán por separado.

### Interfaz de ejecución

La CLI ofrece `generate`, `batch`, `validate`, `compare` y `serve`. `build-forest` queda diferido con F3. Los nombres exactos y ejemplos ejecutables quedarán en el README al implementarse.

La API local ofrecerá crear un trabajo y consultar su estado/resultados. La generación será un trabajo con identificador y tiempo límite, no una petición HTTP bloqueada durante todo el render. La primera versión podrá procesar trabajos secuencialmente, sin infraestructura de colas externa.

## 5. Fases de implementación

### F0. Entorno y contrato mínimo

1. Registrar versiones disponibles y fijar las elegidas. Verificar los nodos y la API de sockets en esa versión; no asumir compatibilidad por una referencia al manual de Blender 5.4.
2. Revisar Easy Tree y Modular Tree: estructura de grupos, control por Python, semillas, exportación, compatibilidad y condiciones de reutilización. Registrar una decisión breve: reutilizar un componente o construir grupos mínimos propios. Evitar mantener dos generadores completos para cubrir el mismo objetivo.
3. Crear estructura mínima, esquema `TreeSpec` y dos presets de contraste.
4. Definir unidades, orientación y escala con un asset de prueba que incluya una curva, una instancia de follaje y material simple.
5. Probar evaluación → realización/conversión a malla → GLB → importación Godot desde un script sin interfaz. Comprobar que ninguna parte desaparece al exportar.

Salida: versiones y decisión de reutilización registradas, comandos reproducibles y asset visible a escala correcta en Godot. Esta fase resuelve el riesgo de integración antes de desarrollar el árbol completo. Consultar un catálogo no equivale a haber probado la extensión localmente.

### F1. Primer árbol con Geometry Nodes y control bpy

1. Construir un árbol en Geometry Nodes con tronco, dos niveles de ramificación, estrechamiento y masas de copa facetadas. La exploración visual inicial queda acotada a ese árbol.
2. Separar grupos de estructura, volumen de ramas y follaje, con entradas documentadas. Usar herramientas nativas de curvas e instancias antes de implementar operaciones equivalentes en Python.
3. Construir/cargar los grupos mediante `bpy` y mapear los parámetros JSON a sus sockets; mantener una única fuente de verdad reproducible.
4. Separar semillas de estructura y follaje, fijar límites de elementos y crear presets joven, adulto y viejo.
5. Regenerar desde una sesión limpia, renderizar y verificar uniones, ausencia de piezas flotantes y exportación de la geometría completa.

Salida: un árbol en nodos controlable por JSON y `bpy`, exportable sin intervención manual, y una colección inicial de semillas de referencia. No se exige una malla orgánica única y estanca; las uniones superpuestas deben verse aceptables.

### F2. Ejecución, exportación y evaluación

1. Implementar CLI, trabajos, manifiestos y fallos con mensajes útiles sobre la automatización `bpy` de F1.
2. Generar un lote fijo de 30 variantes desde nodos y vistas frontal, lateral, superior y perspectiva.
3. Validar presupuesto geométrico sobre las mallas realizadas/exportadas, dimensiones, materiales, archivos y geometría numéricamente válida.
4. Implementar comparación entre dos ejecuciones y un informe con métricas e imágenes.
5. Añadir API local mínima reutilizando el ejecutor.

Salida: lote completo exportado con trazabilidad; los fallos quedan identificados sin aparecer como resultados correctos.

### F3. Bosque en Godot — diferida, fuera del alcance activo

Referencia del alcance original; no implementar ni exigir para cerrar la v1 actual. La importación y captura de los 30 assets ya está verificada en F2.

1. Importar las 30 variantes y comprobar materiales, escala y orientación.
2. Distribuir al menos 300 instancias con semilla, distancia mínima y variación de giro/escala limitada.
3. Agrupar instancias por sector, variante de malla y superficie/material según corresponda; no asumir que un solo MultiMesh contiene árboles de mallas distintas.
4. Usar `MultiMeshInstance3D`, límites espaciales correctos y sectores configurables para permitir culling.
5. Añadir cámara general, inspección cercana y procedimiento fijo de medición.

Salida: bosque regenerable y recorrido de demostración. La revisión visual se hará además de las verificaciones sin interfaz.

### F4. Experimento A: lenguaje natural a parámetros

1. Integrar un proveedor/modelo mediante un adaptador reemplazable y configuración externa.
2. Validar el JSON antes de generar; rechazar campos desconocidos y valores inválidos con errores claros.
3. Preparar seis solicitudes: árbol joven, adulto, viejo, copa densa, copa abierta y ramas asimétricas.
4. Guardar respuestas y compararlas con el preset base usando las mismas semillas.
5. Verificar al menos una ejecución real del modelo; distinguirla de las pruebas con respuestas guardadas.

Salida: el usuario puede pedir un roble viejo de tronco grueso y ramas asimétricas, inspeccionar los parámetros y regenerar el árbol.

### F5. Estructura Python y experimento B de competencia por espacio

1. Introducir `BranchStructure` y un generador Python base con la misma familia de parámetros y dos niveles de ramas. Reutilizar los grupos de volumen y follaje de F1 mediante curvas/atributos creados con `bpy`; no rehacer el mallado.
2. Verificar que el cambio de representación conserva los contratos, presupuestos, escala y estilo previstos. Registrar la transición nodos → Python por separado; no exigir igualdad de árboles entre algoritmos ni atribuir diferencias de esa transición a una mejora espacial. El generador inicial en nodos quedará como referencia congelada, sin exigir evolucionar dos generadores de estructura en paralelo.
3. Congelar el generador Python base, el procesador Geometry Nodes y el conjunto de evaluación. Esta versión Python sin separación será la referencia del experimento B. Las curvas medidas deberán coincidir con los ejes usados para mallar; evitar deformaciones posteriores que desplacen esos ejes sin reflejarse en las métricas.
4. Definir antes de comparar qué se cuenta como cruce: proximidad entre segmentos no adyacentes, excluyendo uniones padre-hijo y usando radios coherentes.
5. Pedir a la IA un cambio acotado e implementar una nueva versión Python con separación: consultar proximidad, probar direcciones alternativas y limitar reintentos.
6. Comparar las dos versiones Python con los mismos 30 casos, semillas y grupos de procesamiento. Revisar que la mejora no provenga de eliminar casi todas las ramas. Luz y gravedad podrán investigarse después; el objetivo medido de B sigue siendo evitar cruces.

Salida: cambio de código revisable, métricas, capturas y registro de iteraciones. El objetivo inicial será reducir al menos 25 % la mediana de conflictos por unidad de longitud de rama, conservando al menos 90 % de longitud total y sin nuevos fallos de validación. Si el objetivo no se alcanza, registrar el resultado como experimento no logrado; no declarar demostrada la mejora.

### F6. Experimento C y cierre

1. Congelar como referencia las mallas de mayor detalle y cámaras de comparación.
2. Aplicar simplificación nativa de Blender o reducir resolución de perfiles y primitivas de follaje. Mantener fija la estructura de ramas de cada caso para aislar el efecto de C.
3. Comparar triángulos y máscaras de silueta con escala, cámara y encuadre idénticos.
4. Reexportar y verificar los 30 assets en Godot; comparar tamaño de archivos y coste de generación con la referencia. La medición del bosque queda diferida con F3.
5. Documentar reproducción completa, resultados y limitaciones.

Salida: una variante optimizada con al menos 30 % menos triángulos y una intersección sobre unión de silueta de al menos 0.90 en cada una de las tres vistas ortográficas. Validar los 30 árboles y revisar visualmente detalle y uniones; la silueta por sí sola no mide toda la calidad.

Las fases activas son secuenciales (F0–F2 → F4 → F5 → F6), salvo preparación de casos/documentación que no dependa de implementación; F3 está diferida. No se estima duración hasta completar F0 y medir un primer ciclo de generación y render.

## 6. Presupuestos y criterios de aceptación

Presupuestos iniciales propuestos, sujetos a una única calibración documentada tras F1 y antes de evaluar B/C:

| Aspecto | Criterio |
| --- | --- |
| Variedad | 30 semillas distintas, sin duplicados geométricos exactos y reconocibles como robles de una misma familia visual |
| Complejidad base | Hasta 10 000 triángulos y 3 materiales por árbol exportado |
| Integridad | Sin NaN/Inf, índices inválidos, triángulos degenerados ni dimensiones nulas |
| Escala | Altura final dentro de ±10 % de la solicitada para presets admitidos |
| Reproducibilidad | Mismo contrato, semilla, algoritmo y entorno producen el mismo resumen geométrico normalizado |
| Automatización de nodos | Los grupos se reconstruyen/cargan y reciben parámetros desde una sesión limpia sin edición manual |
| Interoperabilidad | Los 30 GLB se importan en Godot sin errores; revisión visual de materiales y orientación |
| Bosque | Diferido a otro proyecto; no es criterio de aceptación de la v1 actual |
| IA | Las seis solicitudes producen especificaciones válidas y cambios visuales coherentes, con revisión registrada |
| Regla espacial | Cumplir la comparación definida en F5 |
| Optimización | Cumplir reducción y silueta definidas en F6 |

En el alcance activo se registrarán tiempos de generación, tamaños de archivos y complejidad de los assets bajo condiciones reproducibles. El presupuesto de tiempo de cuadro, memoria y culling de un bosque queda diferido con F3 al proyecto posterior; los conteos de triángulos no demuestran por sí solos una mejora de FPS. Cuando se mida rendimiento gráfico deberán registrarse equipo, sistema, renderizador, resolución, calidad, cámaras y calentamiento.

La revisión visual usará una galería fija: silueta legible, proporción de tronco/copa, ramas conectadas, asimetría controlada y diferencias entre semillas. Las capturas son evidencia, no sustituyen la inspección del asset en Godot.

Se considerará terminada la v1 cuando funcione el recorrido completo, se cumplan los criterios y otra ejecución pueda reproducirlo siguiendo la documentación. Si B o C no cumplen, el prototipo puede seguir siendo útil, pero la v1 quedará parcial respecto de esas hipótesis.

## 7. Verificación y riesgos

- Pruebas unitarias de contratos, semillas, límites de crecimiento y métricas de proximidad.
- Prueba de construcción/carga de grupos, correspondencia de sockets y regeneración con `bpy` sin interfaz.
- Integración de un árbol completo para exportar, recargar y verificar geometría/materiales.
- Verificar que las capturas y el GLB contienen todo el follaje tras realizar instancias y que las métricas corresponden al resultado exportado.
- Lote de regresión de 30 semillas y casos extremos de los rangos admitidos.
- Prueba de importación de los assets en Godot, seguida de revisión visual; construcción de bosque diferida con F3.
- Casos de error de API/CLI: especificación inválida, timeout de Blender, fallo de exportación y respuesta IA inválida.
- Comparaciones B/C con entradas congeladas; separar el conjunto usado para ajustar reglas de algunos casos reservados para comprobar generalización.

Riesgos principales y respuesta:

| Riesgo | Respuesta |
| --- | --- |
| Follaje costoso o silueta genérica | Empezar con masas opacas simples y revisar la galería desde F1 |
| Ramas separadas o uniones visibles | Verificar extremos y radios; inspeccionar primeros planos |
| Explosión de ramas o tiempos | Límites de profundidad, elementos, reintentos y tiempo por trabajo |
| Métrica de cruces engañosa | Normalizar por longitud, conservar estructura y acompañar con imágenes |
| Simplificación que destruye detalles | Comparar varias vistas y revisar materiales/uniones además de silueta |
| Sectores o agrupaciones ineficientes (F3 diferida) | Evaluar en el proyecto posterior de terrenos/bosques |
| Dependencia del proveedor IA | Adaptador, respuestas guardadas y especificaciones ejecutables sin modelo |
| Variación del entorno | Fijar versiones y registrar cambios; no comparar como equivalentes entornos distintos |
| Cambios en nodos o sockets | Versionar grupos y mapeos; verificarlos al cargar en la versión fijada |
| Crecimiento del grafo o pérdida de trazabilidad | Grupos pequeños con interfaces explícitas y construcción/carga reproducible |
| Migración que confunde la mejora de B | Separar transición técnica y comparación Python base vs. Python con regla |

## 8. Primer paso ejecutable

Comenzar por F0: comprobar herramientas locales, revisar los generadores existentes y verificar el recorrido de curvas/instancias a GLB y Godot. Después construir un único roble con Geometry Nodes y automatizarlo con `bpy` antes de ampliar el lote o conectar la IA. Reservar la lógica espacial Python para F5.

## 9. Referencias y alcance de la revisión

Documentación consultada el 2026-10-22. Las versiones enlazadas documentan capacidades de referencia; la versión local y sus APIs se comprobarán en F0.

- [Modificador Geometry Nodes](https://docs.blender.org/manual/en/4.5/modeling/modifiers/generate/geometry_nodes.html): grupos e inputs parametrizables del modificador.
- [Curve to Mesh](https://docs.blender.org/manual/en/4.4/modeling/geometry_nodes/curve/operations/curve_to_mesh.html), [Realize Instances](https://docs.blender.org/manual/en/4.5/modeling/geometry_nodes/instances/realize_instances.html) y [exportación glTF](https://docs.blender.org/manual/es/4.5/addons/import_export/scene_gltf2.html): base de la ruta geométrica y de exportación propuesta.
- [Easy Tree](https://extensions.blender.org/add-ons/easy-tree/): su ficha describe un generador con Geometry Nodes y componentes modulares. Candidato para estudiar grupos y presets.
- [Modular Tree / MTree](https://extensions.blender.org/add-ons/modular-tree/): su ficha describe un flujo de nodos, ramificación multinivel y controles de crecimiento. Su sistema de nodos no se asumirá equivalente a Geometry Nodes; habrá que inspeccionar la integración antes de reutilizarlo.

La revisión inicial se amplió en F0 con inspección de fuentes y carga local del grafo Easy Tree. No se validaron ambas extensiones completas. Se eligieron grupos propios; detalle en el informe F0. F1 implementa esa decisión sin incorporar dependencias de estos generadores.
