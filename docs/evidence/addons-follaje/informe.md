# Easy Tree y Sapling: análisis para el rediseño de follaje

Fecha: 2026-10-22. Instalaciones locales **Easy Tree 1.0.1** y **Sapling Tree Gen 0.3.7**; Blender **5.2.1 LTS**, build `9e2066aef7ef`.

Se inspeccionaron las fuentes Python, presets y grafos realmente instalados, y se ejecutaron pruebas pequeñas en Blender con configuración de fábrica. No se modificaron addons, preferencias ni generadores del proyecto. Las pruebas son de funcionamiento y geometría, **sin comparación estética ni exportación/importación Godot de los addons**. No equivalen a implementar RF0–RF5.

## Conclusión que afecta al plan

La hoja individual no es el único nivel que conviene rediseñar. Ambos addons organizan el follaje a partir de soportes y reglas locales: Easy Tree combina varias hojas en una ramilla e instancia esa unidad; Sapling calcula puntos de inserción con contexto del tallo y genera hojas orientadas a partir de ellos. Es importante concretar en nuestro plan la organización del soporte, el origen de unión y el patrón local, además de su representación.

Se ajusta el [plan de rediseño](../../../plans/rediseno-follaje.md) en esos puntos. Se mantiene Q3 como referencia y su madera intacta. No se importan estos algoritmos ni se adopta ninguno como dependencia. Tampoco se concluye que los addons sean visualmente mejores dentro de nuestros límites: no se hizo esa comparación.

## Fuentes y trazabilidad

Raíz instalada: `/home/tao/.config/blender/5.2/extensions/blender_org/`.

| Componente local | Qué se inspeccionó |
| --- | --- |
| `easy_tree/operators.py:89–168` | Carga del grafo, presets, asignación de sockets y semilla elegida al añadir |
| `easy_tree/assets/assets.blend` | Los 16 grupos cargados y sus enlaces, especialmente `Make Leaf`, `Make Twig & Leaf`, `Instance onto Tree` y `Tree Height` |
| `sapling_tree_gen/utils.py:30–135` | Datos de tallo/punto hijo y perfiles de forma |
| `sapling_tree_gen/utils.py:213–308` | Interpolación de posición, tangente/orientación, radio y ubicación longitudinal |
| `sapling_tree_gen/utils.py:566–710` | Geometría, escala, giro e inclinación de hojas |
| `sapling_tree_gen/utils.py:1043–1215` | Contexto de rama y cantidad de hijos/hojas |
| `sapling_tree_gen/utils.py:1460–1780` | Semilla, generación por niveles y construcción final de hojas |
| `sapling_tree_gen/__init__.py:594–703` | Controles expuestos de follaje |
| Presets `small_maple`, `weeping_willow`, `small_pine` | Diferencias coordinadas de estructura y follaje; no se generaron árboles completos con esos presets |

Los hashes de fuentes y asset, las versiones y resultados están en el [resumen seleccionado](summary.json). El asset Easy Tree actual tiene SHA-256 `7a9febfb39c78e80af2cb88424d1fd23dbd5c6b8a44626b41369efcc7941eeca`: difiere del registrado en F0 (`2feada…5b66`), por lo que se inspeccionó de nuevo. No se atribuye una causa a esa diferencia.

Contexto oficial consultado: [repositorio de Easy Tree](https://github.com/jacobcjohnston/Easy-Tree), [ficha de Sapling 0.3.7](https://extensions.blender.org/add-ons/sapling-tree-gen/) y [manual histórico de Sapling](https://docs.blender.org/manual/en/3.6/addons/add_curve/sapling.html). El manual describe su base Weber–Penn y categorías de controles; las observaciones técnicas siguientes proceden de la instalación local. Las páginas directas de documentación reciente/Sapling no pudieron recuperarse por la herramienta web, así que no se asumió una API reciente a partir de ellas.

## Cómo funciona Easy Tree

El Python del addon es principalmente interfaz y carga de activos. Añade un objeto con el grupo `Simple Tree Generator`, conecta presets mediante identificadores de sockets y elige una semilla aleatoria desde la interfaz. El algoritmo principal está en `assets.blend`.

1. **Esqueleto:** `Make Tree Skeleton`, `Add Branches` y `Make Branch` construyen una red con ramificación, desviación, longitud y gravedad. Mantienen atributos como `tip`, `forward`, `startHeight` y `basePos`.
2. **Madera:** `Tree to Mesh` procesa el esqueleto para producir su volumen y material.
3. **Hoja:** `Make Leaf` construye una lámina con divisiones, perfiles de contorno/deformación, UV y elección de material. Los tres materiales de hojas inspeccionados conectan una textura de opacidad al alfa del shader.
4. **Unidad intermedia:** `Make Twig & Leaf` coloca por defecto siete hojas a lo largo de una línea, con incremento angular de 137.5° y variación de inclinación, y añade un tallo de sección de cuatro lados con estrechamiento.
5. **Colocación:** `Instance onto Tree` convierte aristas en curvas y muestrea por longitud; el espaciado se calcula como `1 / Density`. Orienta las instancias usando tangentes y un vector aleatorio, y controla escala mínima/máxima. Permite sustituir la unidad completa por un objeto personalizado.
6. **Elegibilidad:** el control llamado `Min Height` no compara directamente coordenadas Z. Consume `Tree Height`, una medida derivada de caminos de aristas hacia puntos marcados como puntas, con coste unitario por arista y transformación del resultado. Es contexto topológico del esqueleto; su umbral no significa metros de altura.

Esto permite cambiar la hoja o la unidad de ramilla sin rehacer todo el árbol. También muestra límites que no conviene copiar: el addon usa un único Seed expuesto, ciertos valores internos son constantes y el operador de interfaz cambia la semilla al añadir. No sustituye nuestros manifiestos, límites y separación de semillas.

### Comprobaciones locales

| Prueba | Resultado realizado |
| --- | --- |
| `Make Leaf`, divisiones 2×2 | 4 vértices, 1 cara, 2 triángulos |
| `Make Leaf`, divisiones 3×4 | 12 vértices, 6 caras, 12 triángulos |
| `Make Twig & Leaf`, siete hojas | 136 triángulos: 84 de hojas y 52 del tallo; dos evaluaciones idénticas |
| Árbol pequeño explícitamente acotado | 2184 triángulos: 1176 con material Bark y 1008 con Beech Leaves, tras realizar instancias |
| API histórica de asignación `modifier['Socket_16']` | Falla con `TypeError` en Blender 5.2.1 |
| API actual de entradas del modificador | El grafo mínimo sin hojas evalúa a 552 triángulos |

La prueba de asignación reproduce la forma utilizada por `operators.py`; no se afirma haber verificado toda su interfaz. El fallo no demuestra que el algoritmo geométrico sea incompatible: se pudo evaluar tanto el esqueleto como un árbol pequeño por acceso directo al grafo. No se reparó el addon.

El número de instancias por sí solo no mide el coste: una instancia de esa unidad lleva siete hojas y un tallo. Copiar su resultado como una hoja simple o asumir que sus texturas no influyen falsearía la comparación con nuestro estilo opaco.

## Cómo funciona Sapling

Sapling construye curvas Bézier mediante Python. `stemSpline` conserva el estado del tallo que crece y `childPoint` conserva punto de inserción, orientación, radios y posición sobre el padre. Construye niveles sucesivos con longitudes, curvaturas, inclinaciones y giros; perfiles de forma y opciones de poda influyen en la estructura.

El follaje se genera a partir de los puntos hijos del último nivel de tallos. La cantidad tiene relación con la longitud de la rama y un perfil `leafDist`; no es simplemente una cantidad global de hojas repartidas por el árbol.

`genLeafMesh` puede generar una forma hexagonal de seis vértices y dos quads —cuatro triángulos— o un rectángulo —dos triángulos—, además de soportes para instanciar otro objeto. Las coordenadas de la hoja parten de su base, no de su centro. Luego aplica escala/proporción, giro, inclinación y la orientación heredada del tallo. Hay controles de variación y cambio de escala hacia la base/punta, orientación hacia arriba y ajuste de dirección.

La distribución tiene dos comportamientos distintos. Con `leaves` positivo, distribuye puntos sobre los tallos finales. Con un valor negativo, restringe los puntos a sus extremos y construye un abanico de hojas allí. Esa codificación mediante un signo es una interfaz que no necesitamos copiar; la distinción entre patrones sí es útil.

Los presets examinados cambian conjuntamente perfiles, cantidades/longitudes/direcciones de ramas, curvaturas, proporciones y distribución de hojas. Por ejemplo, el sauce usa hojas más estrechas y atracción descendente de tallos; no se limita a sustituir la forma de hoja sobre el mismo esqueleto. Esto respalda preparar perfiles separados sin declarar implementadas más especies.

### Pruebas pequeñas de Sapling

Se ejecutó el operador en una sesión aislada con tres niveles, ramificación baja, semilla 17, sin poda, división de tallos, animación ni armadura. Produjo once curvas. Los valores efectivos completos se conservan en el resumen; `leaves=12` es un control local, no el conteo final de todo el árbol.

| Variante | Hojas generadas | Triángulos de hojas | Curvas de madera |
| --- | --- | --- | --- |
| Base, hexagonal | 33 | 132 | 11 |
| Repetición | 33 | 132 | Idénticas |
| Otra escala de hoja | 33 | 132 | Idénticas |
| `leaves=24` | 68 | 272 | Idénticas |
| Abanico terminal `leaves=-5` | 35 | 140 | Idénticas |
| Rectangular | 33 | 66 | Idénticas |
| Otra inclinación/giro | 33 | 132 | Idénticas |

La base y repetición tienen el mismo hash de hojas; cambiar escala o dirección cambia el hash. Las siete pruebas conservan el mismo hash de coordenadas, manejadores y radios de las curvas. Esto acredita separación en esos casos, no una garantía para todos los parámetros. Sapling inicializa el generador aleatorio global con `seed(props.seed)`; no aporta automáticamente nuestra separación de flujos e identificadores estables.

## Comparación con el generador propio

| Aspecto | Q3 actual | Aprendizaje útil |
| --- | --- | --- |
| Unidad visible | Poliedros deformados de 20/80 triángulos | Una hoja barata puede ser suficiente como unidad; el estilo depende también de su organización |
| Distribución | Tramos distales y pocas masas por curva | Introducir portadores finos y distribución longitudinal/local antes de poblar la copa |
| Soporte | Referencias de rama y anclajes para masas grandes | Conservar inserción, recorrido, longitud, marco local y contexto terminal de cada grupo |
| Giro/forma | Giros y deformación de masas cerradas | Separar azimut alrededor del soporte, inclinación y origen de unión de la hoja |
| Densidad | Control cuantizado de masas, modulado por longitud/nivel | Separar cantidad de portadores, hojas por longitud y escala visible |
| Otros árboles | Una estructura de roble y sus presets de edad | Cambiar arquitectura y distribución además de la unidad de hoja |
| Reproducción/evaluación | Contrato, semillas separadas, manifiestos, GLB/Godot y límites | Conservar esta infraestructura; los addons no la reemplazan por disponer de más controles |

## Cambios concretos en el plan

1. **RF0:** distinguir material/recortes de geometría y organización al estudiar una referencia texturizada.
2. **Arquitectura/RF1:** concretar portadores como recorridos finos con longitud, base de unión y contexto de rama; empezar comparando láminas muy baratas antes de añadir subdivisiones.
3. **RF2:** probar hojas a lo largo del portador frente a grupos terminales; separar densidad de portadores y hojas por longitud. Verificar giro/inclinación y estabilidad del marco local.
4. **RF2 y viabilidad de copa:** comprobar si portadores invisibles bastan para evitar apariencia de hojas flotantes. La madera Q3 sigue intacta; si se necesitan ramillas visibles, habrá que registrar y evaluar ese cambio de alcance, no introducirlas disimuladamente.
5. **Presupuesto:** contar el contenido real de la unidad instanciada. En viejo-09 la madera Q3 tiene 5292 triángulos y deja 4708 bajo el límite de 10 000; una unidad de 136 triángulos consumiría ese margen en solo 34 instancias. Es una cuenta de viabilidad, no una predicción estética ni de FPS.

No se cambia el orden RF0–RF5 ni se añaden fases de especies, viento o migración estructural. La evidencia apoya concretar el plan existente; no justifica sustituir el generador por uno de estos addons o importar todo su sistema.

## Reproducción

Desde el repositorio, con la ruta local de Blender fijada y una carpeta de salida nueva:

```sh
/home/tao/repos/blender/.tools/blender-5.2.1-linux-x64/blender --background --factory-startup --threads 1 --python-exit-code 1 --python scripts/review_tree_addons.py -- --output artifacts/addon-review/otra-revision
```

El script permite `--addons /ruta/a/extensions/blender_org` para otra instalación. Usar el límite de 120 s del entorno de ejecución si se automatiza como subproceso. Por diseño, los parámetros de las pruebas son pequeños; no se ejecutan los presets completos.

Resultados de esta revisión: `artifacts/addon-review/final/summary.json` y `easy-tree-graphs.json`. El resumen seleccionado se conserva aquí; el volcado completo de grafos es regenerable y está ignorado. Se verifican hashes de fuentes antes/después. Las gráficas, perfiles y fórmulas se consultan como referencia; no se copia código de implementación ni activos al generador propio.
