# Plan: rediseño del follaje procedural

Fecha: 2026-10-22.
Estado actualizado el 2026-10-23: RF3 aprobada como referencia del primer tipo; [B0 de blueprints](../docs/evidence/blueprints/b0/informe.md) conserva el piloto y [B2](../docs/evidence/blueprints/b2/informe.md) integra su generación, con GLB idéntico. RF4/B3 y su revisión están verificadas técnicamente: [informe B3](../docs/evidence/blueprints/b3-revision/informe.md). Sistema de blueprints cerrado técnicamente en B5; perfiles nuevos aún experimentales y lote RF5 pendiente.

Estado técnico previo a esta adopción: RF3 implementada y verificada técnicamente, con revisión de imágenes reales Godot y aprobación artística de copa pendiente; [informe](../docs/evidence/rediseno-follaje/rf3/informe.md). Viejo-09 completo: 10572 triángulos/1584 hojas/9 m, techo 12500. RF4/RF5 sin iniciar. Referencia: [rama RF2 de 144 aprobada](../docs/evidence/rediseno-follaje/rf2-densidad/aceptacion.json). Se conservan revisiones anteriores y addons como referencias: [moldes](../docs/evidence/rediseno-follaje/rf2-moldes/informe.md), [ramillas](../docs/evidence/rediseno-follaje/rf2-ramillas/informe.md), [RF2 original](../docs/evidence/rf2/informe.md) y [addons](../docs/evidence/comparacion-addons/informe.md).

## Comparación acotada antes de RF3 — autorizada el 2026-10-22

El usuario solicita obtener un adulto y un viejo con Easy Tree y Sapling, compararlos con Q3 bajo requisitos comunes y evaluar el trabajo de ajuste. Se añade este ensayo previo a RF3 sin implementar esa fase, un bosque ni un generador durante el juego. Los addons se ejecutan aislados como herramientas de comparación, sin modificar sus instalaciones ni incorporarlos al generador de producción.

Casos de referencia fijados antes del ajuste: Q3 `adulto-00` (10 m, semilla 2000) y `viejo-09` (9 m, semilla 3009). Los candidatos registrarán sus propias semillas; el mismo número no supone geometrías equivalentes entre algoritmos. Límite final común: 10 000 triángulos/3 materiales, materiales opacos de paleta compartida y sombreado facetado. Altura final de los addons mediante escala uniforme y base en Z=0, sin imponerles la madera Q3. Cámaras e iluminación compartidas por edad, congeladas antes de comparar; registrar recortes si los hay. Conservar configuraciones iniciales, intentos rechazados, cambios de controles/grafos/posprocesado y tiempos de generación. El esfuerzo humano de ajuste se documentará por intervenciones concretas, sin presentar tiempos de subproceso como horas de autoría ni generalizar desde cuatro candidatos.

Resultado: catorce configuraciones, cuatro candidatos de addons y dos referencias Q3 válidos en Godot; cuatro repeticiones idénticas y 36 capturas. Easy Tree adaptado 7472/9022 triángulos, Sapling ajustado 7764/9048, Q3 6984/8512. Se documentan intentos fuera de presupuesto, hoja RF1 de sustitución en Easy Tree, controles nativos Sapling y facetado de las copias Q3. Sapling requirió menos intervención interna en este ensayo, sin ganador artístico ni promoción. No se ha probado generación durante el juego ni se inicia RF3 por pasar las métricas. [Comparación, esfuerzo y reproducción](../docs/evidence/comparacion-addons/informe.md).

## Decisión tras la comparación — 2026-10-22

El usuario decide continuar con la implementación propia. Q3 aporta volumen y una silueta legible dentro del presupuesto, mientras que las configuraciones ensayadas de los addons muestran hojas y conexiones más explícitas sin conseguir conjuntamente esa ocupación de copa. Esta evidencia justifica seguir investigando una solución dirigida a nuestros requisitos; no demuestra una incapacidad general de Easy Tree o Sapling. Los addons siguen como referencias de arquitectura y herramientas de comparación.

Se adoptan estas tres directrices:

- **Conservar de Q3 el control del volumen y la silueta.** Usar su presencia visual como referencia, permitiendo un contorno y una representación nuevos; no exigir copiar sus masas ni su silueta exacta.
- **Incorporar ramillas y conexiones visibles para sostener las hojas.** Comprobar una unión continua entre madera base, ramilla y origen de cada hoja. Su efecto sobre la apariencia suspendida sigue siendo una hipótesis que debe contrastarse.
- **Evaluar la distribución por cuánto contribuye a formar la copa deseada.** Definir regiones y volumen objetivo antes de poblar; revisar cobertura, huecos, borde y lectura a varias escalas junto con el coste de madera nueva y follaje.

**Cambio de alcance registrado:** se levanta la restricción de usar exclusivamente portadores invisibles. La revisión de RF2 podrá añadir ramillas y conexiones de madera visibles, identificadas y contabilizadas por separado, conservando intacta la madera Q3 base y los archivos históricos. No incluye remodelar el tronco ni las ramas Q3 existentes. El límite total sigue en 10 000 triángulos/3 materiales por árbol; la madera añadida consume ese mismo presupuesto.

La revisión acotada RF2 se ejecutó sobre la rama congelada: pareja con/sin ramillas separada del ajuste posterior de distribución. Contrato, límites y manifiestos se versionaron antes de generar candidatos. Las conexiones se leen en detalle, pero todavía no se obtiene el volumen buscado dentro de una proyección viable; RF3 sigue pendiente. Resultados en la sección RF2 y su informe.

## 1. Objetivo y relación con v1

Construir una segunda familia de follaje con una lectura visual claramente distinta de las masas poligonales actuales y controles más precisos sobre forma, distribución y orientación. La primera aplicación será un roble sobre la madera Q3 aprobada, ampliada con ramillas visibles según la revisión de RF2. La arquitectura debe permitir investigar otros tipos de árbol posteriormente, sin prometer representarlos cambiando únicamente las hojas.

Este documento dirige el rediseño del follaje. El [plan v1](v1-generador-arboles.md) conserva los contratos y la infraestructura ya implementada; F4–F6 continúan pendientes durante este trabajo y F3/bosques sigue diferida. Es un cambio explícito respecto a mantener todas las revisiones Q en un único plan: el usuario solicita ahora un plan separado para una nueva familia de follaje. No se declara terminada v1 ni se ejecutan sus experimentos de IA por este cambio.

Fundamento: [dirección de diseño](../docs/diseno-follaje.md). Evidencia anterior: [Q3](../docs/evidence/q3/informe.md) y [fusión parcial](../docs/evidence/q3-fusion/informe.md).

### Revisión importante a partir de los addons instalados

El [análisis local reproducible](../docs/evidence/addons-follaje/informe.md) confirma que la forma de la hoja y la colocación no bastan como dos bloques genéricos. Easy Tree construye una unidad de ramilla con varias hojas y después la coloca sobre el esqueleto; Sapling conserva contexto del tallo, orientación y posición longitudinal para distribuir y orientar hojas. Se concretan tres decisiones del plan:

- Los portadores deben describir recorridos finos, origen de inserción y contexto terminal, no solo puntos y vectores sin organización. Evaluar la lectura de esos portadores invisibles en RF2, antes de suponer que bastan para llenar una copa.
- Separar el patrón local de hojas —distribuidas a lo largo del portador o agrupadas en su punta— de su geometría, con controles de separación, azimut e inclinación. No fijar un ángulo universal ni esconder modos distintos en el signo de un número.
- Comparar prototipos de coste mínimo y distinguir el efecto de geometría, orientación y material. Sapling produce hojas hexagonales de cuatro triángulos; Easy Tree combina hojas y texturas con recortes. El éxito de una referencia texturizada no prueba la estética de una lámina opaca equivalente.

Aquella revisión inicial no incorporó código/activos de los addons ni los convirtió en dependencias, y mantuvo los portadores invisibles. La decisión posterior descrita arriba permite añadir ramillas visibles conservando la madera Q3 base. Las pruebas de carga/generación de la investigación inicial no acreditaban exportación Godot ni calidad estética bajo nuestro presupuesto; la comparación posterior verifica la exportación de cuatro candidatos adaptados, cuya aceptación artística sigue pendiente.

## 2. Punto de partida y decisiones

- Decisión del usuario del 2026-10-23: conservar la geometría actual, incluido
  el tronco, sin reducir polígonos ni convertir el follaje a tarjetas texturizadas
  por ahora. La optimización se evaluará al integrar los árboles en el motor,
  mediante mediciones; un menor conteo de triángulos no demuestra por sí solo
  más rendimiento. No se inicia un sistema LOD ni un ensayo de bosque, y la
  aprobación artística de la copa RF3 sigue pendiente.
- La familia de masas poligonales se conserva como estilo aprobado. Q3 0.4.0 es la referencia reconstruible; Q3b 0.4.1 permanece rechazada. La aprobación de la fusión se limita a los cuatro casos mostrados, sin superioridad atribuida ni lote fusionado completo.
- Referencia Git previa: `fbe87a4`, etiqueta `q3-referencia-0.4.0`; ensayo de fusión en `4fa3d8c`. Las fuentes históricas y sus resultados no se sobrescriben.
- El resultado de fusión no demuestra un límite absoluto de métodos basados en esferas. Mantener su composición inicial restringía el cambio estético. Este plan cambia la unidad de representación y su organización.
- Primera hipótesis: conjuntos pequeños de hojas geométricas opacas, orientados sobre portadores virtuales. Es una hipótesis por evaluar, no una representación definitiva aprobada. Tarjetas texturizadas quedan como alternativa si la primera hipótesis falla artística o técnicamente.
- Se conservará exactamente la madera Q3 base final. La revisión de RF2 añade ramillas y conexiones visibles como geometría separada con coste, procedencia y límites explícitos; sustituir o remodelar el tronco y las ramas Q3 queda fuera del alcance.
- Los presets principales aún apuntan a Q3b. Para toda referencia de este plan se cargarán explícitamente `presets/v0.4.0/` o `presets/q3-cases.json`. La promoción de una variante se resuelve en RF5, no alterando silenciosamente la referencia.

## 3. Alcance

Incluye:

- Dirección visual, unidad de hoja/grupo pequeño, disposición en una rama y construcción de una copa completa.
- Ramillas y conexiones visibles añadidas a la base Q3, primero en una revisión de RF2 y después, si su resultado es satisfactorio, en la copa RF3.
- Controles separados de copa objetivo, soportes, ocupación y representación; variación reproducible con semillas.
- Reutilizar la estructura, el ejecutor y la exportación Blender → GLB → Godot, añadiendo solo los contratos y adaptadores necesarios.
- Comparaciones visuales y técnicas por etapas; piloto, controles y lote final condicionados a la calidad de la etapa anterior.
- Separar perfiles y representación para facilitar futuras arquitecturas, dejando documentados los requisitos que una nueva especie exigiría.

Fuera del alcance:

- Un generador multiespecie completo, reglas botánicas o simulación de crecimiento.
- Rehacer tronco y ramas Q3, introducir el generador estructural Python de F5 o adjudicar este trabajo al experimento B.
- Viento, rigging, estaciones, bosque, terreno, editor propio, API pública o integración de un modelo IA.
- Un sistema LOD o una optimización de FPS. Las vistas a distancia comprueban lectura, no rendimiento de un bosque.
- Desarrollar simultáneamente varias representaciones completas. Se prueba una hipótesis; si no sirve, se registra por qué y se decide la alternativa.

## 4. Arquitectura prevista

Flujo conceptual: `madera Q3 base + perfil de copa → recorridos portadores → ramillas visibles + disposición de follaje → representación → malla evaluada → GLB → Godot`.

| Componente | Responsabilidad | Invariante o separación |
| --- | --- | --- |
| Referencia estructural | Leer curvas, relaciones y transformación final Q3 | Madera Q3 base exportada idéntica, sin nueva normalización dependiente del follaje |
| Perfil de copa | Expresar contorno objetivo por altura, base de copa, anchura y asimetría | Es una guía espacial; no se exporta como un sólido visible |
| Recorridos portadores | Definir recorridos finos, inserción, longitud y marco local de los grupos | Datos de soporte separados del mallado, con referencia a rama padre y contexto terminal |
| Ramillas visibles | Convertir recorridos y conexiones en madera que sostenga las hojas | Geometría nueva separada de la base Q3, con radios, resolución y trabajo acotados |
| Ocupación | Distribuir unidades y controlar zonas densas, transiciones y huecos | No depende de una icosfera ni de un material concreto |
| Representación | Convertir unidades colocadas en hojas/grupos visibles | Consume posiciones, giros, escalas e identificadores estables |
| Evaluación | Medir malla final y cambios visuales bajo condiciones congeladas | Sin usar una métrica de silueta como sustituto de estética |
| Adaptadores | Construir/evaluar en Blender y exportar/importar en Godot | Contratos y reglas espaciales separados de `bpy` cuando sea práctico |

No se construye un motor propio de mallado. Blender y Geometry Nodes siguen siendo herramientas de procesamiento. La distribución puede calcularse en Python sin migrar ni reconstruir el algoritmo de ramas.

Los nombres de datos siguientes son provisionales, no clases ya disponibles:

- `CrownProfile`: límites, perfil de anchura por altura, desplazamientos y pesos por zona.
- `FoliageSupport`: id estable, rama padre, origen de inserción, recorrido/longitud en coordenadas finales, posición longitudinal, tangente, marco local, contexto terminal y región de copa. Puede agrupar ramillas virtuales con profundidad y conteos acotados; no es un nuevo generador global de ramas.
- `FoliagePlacement`: soporte, coordenada longitudinal/local, origen de unión de hoja, orientación, escala y variante de representación. El origen de inserción se distingue del centro geométrico de la hoja o grupo.
- `FoliageSpec`: versiones, controles, semillas y límites de trabajo. No se introducirán campos nuevos en el `TreeSpec` histórico sin versionarlos.

La rama de origen debe poder inspeccionarse desde cada unidad. El manifiesto conservará la especificación Q3 base y la configuración/versiones del follaje nuevo, sin etiquetar una malla modificada como si fuera una salida Q3 sin cambios.

La elegibilidad de una zona portadora puede depender de su relación con extremos y del tramo de rama, además de altura global. Se documentará la unidad de cada control: longitud/altura en metros finales, posición normalizada sobre el portador o contexto topológico. No confundir un umbral de distancia en el grafo con altura Z. El perfil de copa debe contrastarse con la región alcanzable desde esos soportes: una envolvente incompatible con la estructura fija se registra como tal, en lugar de compensarla con hojas enormes o desconectadas.

## 5. Fases y criterios de salida

### RF0. Objetivo visual y protocolo de comparación

Trabajo:

1. Seleccionar 3–5 referencias visuales coherentes, registrar procedencia y explicar qué rasgos se buscan: borde, huecos, organización, escala del detalle y sombreado. Evitar mezclar estilos incompatibles en una misma meta.
2. Definir una ficha breve: rasgos deseados, rasgos a evitar y ejemplos de cambios concretos. Resolver si se mantiene la hipótesis de geometría opaca para el primer prototipo.
   Cuando una referencia use hojas texturizadas, distinguir lo que aporta su recorte/material de su malla y colocación mediante una inspección con material neutro si está disponible. No atribuir ese aspecto a geometría opaca que aún no lo reproduce.
3. Congelar Q3 `viejo-09` y una rama identificable de ese árbol, incluidos datos, transformaciones, materiales y hashes. La rama debe proceder de la referencia, sin remodelarla para favorecer el candidato.
4. Preparar vistas frontal, lateral, superior, inferior y perspectiva. Para el árbol, fijar tomas cercana, media y lejana a partir de la referencia: objetivo inicial de altura proyectada de aproximadamente 50 %, 25 % y 10 % de un cuadro de 900×900. Ajustar estos objetivos al uso de juego y registrarlos antes de comparar.
5. Registrar proyección, focal/FOV, resolución, encuadre, iluminación y renderizador. Las cámaras se fijan desde la referencia, sin reencuadrar cada candidato. La unidad pequeña tendrá además vistas de detalle compartidas.

Entregable: ficha visual y configuración reproducible de las escenas de inspección.

Ejecución inicial: tres referencias con procedencia; viejo-09 y su primaria `q3:primary:100` congelados. Se elige protocolo ortográfico a 900×900 y altura proyectada 50/25/10 % para fijar ocupación de pantalla, sin atribuirle distancias físicas de una cámara perspectiva. Vistas y luces registradas en la [ficha RF0](../docs/follaje-rf0-rf1.md). Es una propuesta revisable, no un objetivo artístico aprobado por el usuario.

Salida: objetivo suficientemente concreto para distinguir un nuevo follaje útil de otro conjunto de poliedros, sin exigir parecido casi idéntico a Q3. La ficha se revisa visualmente antes de escalar los prototipos.

### RF1. Unidad de follaje y contrato experimental

Trabajo:

1. Definir el contrato mínimo de soportes y colocaciones: unidades, identificadores, ejes locales, rangos, controles, semillas y límites. Mantenerlo experimental y versionado, separado de los presets históricos.
2. Construir una unidad pequeña sobre un portador virtual: una hoja simplificada o un grupo reducido de hojas, con contornos que no partan de una esfera cerrada. Comparar como máximo tres variantes iniciales de forma/plegado, incluyendo una lámina de coste mínimo y una forma hexagonal simple antes de añadir subdivisiones.
3. Controlar tamaño, proporción, separación, orientación y variación acotada. Definir origen de unión, eje longitudinal y normal de la hoja; separar giro alrededor del soporte e inclinación respecto a él. Resolver normales y lectura de frente/reverso en el GLB y en Godot, además de la vista Blender.
4. Registrar triángulos por unidad, materiales y un cálculo de cuántas unidades caben en el presupuesto del árbol. No multiplicar instancias antes de comprobar esa viabilidad.
5. Comprobar reconstrucción con semilla fija, efectos visibles de controles y rechazo de entradas inválidas.

Entregable: unidad reproducible, pequeña galería de variantes y contrato experimental documentado.

Ejecución inicial `foliage-unit-0.1.0`: rombo de dos triángulos y hexágonos plano/plegado de cuatro, siete hojas sobre un portador sintético; 24 pruebas y 16 GLB verificados/importados en Godot. Contrato separado de TreeSpec; Q3 intacta. El usuario autoriza después continuar con RF2 sobre esta unidad; se mantiene el plegado como candidato técnico, sin promover una copa ni suponer resueltos los límites de perfil y soporte. [Resultados RF0/RF1](../docs/evidence/rf0-rf1/informe.md).

Salida técnica: geometría válida, exportable y con límites de trabajo; ninguna dependencia del generador de ramas nuevo. Salida visual: lectura convincente de hoja/grupo desde varias vistas, sin desaparecer al girar ni depender de una sola iluminación favorable. Si no se consigue, iterar esta unidad antes de construir la copa.

### RF2. Follaje sobre una rama aprobada

Trabajo inicial, ejecutado con portadores invisibles:

1. Construir recorridos virtuales finos a partir de la rama congelada, con un origen de inserción y marco local estables. Orientar las unidades a lo largo de ellos y comprobar que no haya giros bruscos al cambiar la dirección del soporte. Mantener la geometría de madera seleccionada exactamente igual.
2. Distribuir grupos sobre zonas portadoras, con transiciones y variación reproducible. Separar cantidad de soportes, hojas por longitud de soporte y escala de hoja. Comparar un patrón a lo largo de una ramilla y otro agrupado en su punta para elegir el objetivo visual; no asumir que son intercambiables ni implementar un catálogo de especies. Evitar filas rígidas y ruido que destruya la organización, sin rechazar una disposición regular cuando sea parte del patrón elegido.
3. Probar tres niveles de densidad y al menos dos orientaciones de soporte con la misma regla; no confundir esos ejemplos con especies ya implementadas.
4. Revisar relación con la rama, repetición, acumulación en puntas y huecos desde abajo/lados. Comparar con el follaje Q3 asociado a la misma rama bajo las mismas condiciones. Evaluar explícitamente si los soportes invisibles hacen que las hojas parezcan flotar: si no se resuelve con su organización, registrar el problema y revisar el alcance de ramillas visibles antes de ampliar, sin afirmar que la restricción de madera ya funciona artísticamente.
5. Hacer variaciones de un control a la vez. Registrar el efecto buscado y los efectos secundarios, en vez de prometer independencia perfecta entre controles geométricos.

Entregable: rama con follaje nuevo y una matriz pequeña de densidad/orientación.

Ejecución `foliage-branch-0.1.0`: primaria 100 congelada más sus secundarias Q3 originales 200–202. Se comparan doce casos: patrones longitudinal/terminal, densidades 6/9/12 hojas por metro y giros de soporte 0/70°, con madera y cámaras compartidas. Pasaron 30 pruebas y 19 GLB, repetición, controles y comparación de madera/sombreado exportados. La revisión visual detecta hojas suspendidas incluso en controles de tamaño, cantidad y largo: **no se da por conseguido el criterio visual ni se inicia RF3**. Este ensayo original se conserva como referencia de portadores invisibles. [Informe y reproducción](../docs/evidence/rf2/informe.md).

#### Revisión de RF2: ramillas visibles y contribución a la copa — ejecutada, salida artística pendiente

1. Versionar el contrato experimental para separar madera Q3 base, recorridos portadores, ramillas nuevas y hojas. Fijar cotas de cantidad, longitud, radio, resolución, triángulos y tiempo antes de construir geometría; registrar el presupuesto de esta rama y su proyección al árbol completo.
2. Sobre la misma primaria 100 y secundarias 200–202, comparar una pareja con/sin ramillas visibles manteniendo recorridos, hojas, colocaciones, materiales, semillas y cámaras comunes. Contar por separado la geometría añadida y comprobar las conexiones. Cualquier corrección de posición necesaria se documentará y comparará aparte.
3. En un segundo ensayo, ajustar la organización de grupos hacia una región de copa definida desde la referencia antes del ajuste. Mantener fijos la unidad de hoja y los controles ajenos a la distribución; registrar cambios de conteo, extensión, cobertura y coste. El objetivo es formar volumen legible con hojas conectadas.
4. Comprobar la base Q3 por hash, la nueva geometría por separado, repetición, límites y exportación/importación Godot. Revisar vistas laterales e inferiores y escalas de lectura con las escenas congeladas; las métricas de ocupación acompañan la inspección visual.
5. Registrar qué aporta la conexión visible y qué aporta la distribución, con sus límites. Ampliar a RF3 solo cuando la rama ofrezca soporte visual claro y una organización viable dentro del presupuesto del árbol.

Entregable implementado: contrato `foliage-branch-0.2.0`, ramillas triangulares de tres anillos (14 triángulos), pareja con/sin madera nueva, selección espacial hacia una región Q3 congelada y cálculo de viabilidad. Pasaron 37 pruebas, 13 GLB importados y 120 capturas Godot; madera Q3 base/material intactos y dos repeticiones idénticas. [Contrato](../docs/contrato-rf2-ramillas.md) e [informe](../docs/evidence/rediseno-follaje/rf2-ramillas/informe.md).

La pareja mantiene hojas y recorridos históricos exactos y hace visible su conexión en detalle. La selección de 16 soportes duplica de 6 a 12 las celdas próximas a centros de hojas en el diagnóstico, pero su proyección aritmética a once primarias da 10572 triángulos. El caso de 12 soportes da 9252 y sigue despoblado. El pool de 192 recorridos solo alcanza 24 de 152 celdas objetivo a .55 m. Tras la primera inspección se añadieron controles de .8 m: alcanzan 33 celdas; a igual conteo/coste, las celdas próximas a hojas pasan de 10 a 13 sin resolver el volumen. No son porcentajes de aceptación estética ni una copa generada.

Decisión técnica de salida: conservar la conexión demostrada y continuar iterando alcance, inserciones y reparto de área foliar sobre esta rama. La lectura general y a distancia todavía no satisface RF2; RF3 no se inicia. Si el siguiente ensayo requiere otro nivel, mayores longitudes o representación distinta, versionar contrato y registrar el cambio antes de generar. La revisión actual no eleva los 10000 triángulos/3 materiales por árbol ni demuestra un límite general de las hojas opacas.

Salida: lectura visual distinta y útil frente a Q3, soporte claro y paso entre zonas densas y abiertas sin producir pompones aislados. Si el resultado vuelve a depender de volúmenes grandes cerrados, reconsiderar la unidad o distribución antes de ampliar.

#### Ensayo RF2 con moldes Q3 — ejecutado, aprobación artística pendiente

El usuario propone reutilizar los volúmenes poligonales Q3 y autoriza comenzar
el ensayo: masas como moldes invisibles, hojas en una franja de superficie,
descarte de superficies interiores entre masas solapadas y conexiones por
grupos. Se mantiene la misma rama congelada y las cámaras de la revisión RF2.
No se inicia RF3 ni se conserva un núcleo sólido visible para dar cobertura.

Cambio de alcance explícito: se sustituye la guía elipsoidal por las superficies
Q3 finales y se construyen recorridos desde la madera hacia ellas. Contrato
separado `foliage-molds-0.1.0`, fijado antes de generar; conexiones de hasta 4 m
frente a los .8 m de la revisión anterior, sin bifurcaciones nuevas ni cambios
en la base Q3. La forma de hoja RF1 se conserva y se permite escala estilizada
de hasta 1 m. [Contrato del ensayo](../docs/contrato-rf2-moldes.md).

Primera pareja: 16 grupos de tres hojas; 224 triángulos de conexiones y 192 de
hojas, 416 añadidos por rama. Proyección aritmética para viejo-09: 9868; no es
una copa generada. Dos tamaños (.45/.8 m) con igual distribución, orientaciones,
conteo y presupuesto. Pool máximo de 2048 muestras y búsqueda espacial acotada.
Comparar lectura y cobertura con Q3 y la revisión previa en Godot, comprobar
contactos y madera intacta, y registrar resultados antes de ampliar el ensayo.

Tras inspeccionar la primera pareja, se añade una segunda prueba acotada
`foliage-molds-0.1.1`: conexiones rectas de ocho triángulos y rombo RF1 de dos,
24 grupos × 4 hojas, 384 triángulos añadidos y proyección 9516. Comparar .8/1 m
con igual distribución dentro de esta pareja. Se conserva la primera pareja
con fuentes ejecutadas; el contraste entre parejas cambia varias variables y
no demuestra qué componente causa una diferencia. Presupuesto y fase iguales.

Resultado verificado: nueve moldes originales y 300 triángulos guía, 43 pruebas,
11 GLB importados, 72 capturas Godot y cuatro repeticiones idénticas. Los dos
hexágonos reconstruyen la geometría inicial; los moldes no se exportan. En
seis vistas generales la cobertura proyectada frente a Q3 pasa de 4–6 % del
ensayo previo a 22–31 % con hexágono .8 m y 54–64 % con rombo 1 m. Esta última
variante tiene mayor presencia a distancia, pero piezas grandes y angulosas;
la de .8 m reduce su tamaño y deja más huecos. La cobertura no determina la
aceptación estética. Revisar tamaño/forma y continuidad sobre la rama antes
de RF3; una copa necesitaría asignación global por área y descarte de
interiores entre todas las primarias. [Informe y reproducción](../docs/evidence/rediseno-follaje/rf2-moldes/informe.md).

#### Aumento aditivo de hojas sobre moldes — autorizado el 2026-10-23

El usuario considera que le gusta el resultado, pero pide algo más de volumen
añadiendo hojas. Se mantiene la escala de 1 m del rombo, las 24 conexiones y
las 96 hojas originales. Ensayo separado `foliage-molds-0.1.2`: añadir 24 o
48 hojas y un control de 96 adicionales, sin desplazar ni reorientar las previas.
Selección estable por grupo; las primeras adiciones sobreviven al aumentarlas.

Antes de generar, el usuario aumenta el presupuesto del rediseño a **12500
triángulos por árbol**, conservando tres materiales. La cota derivada de rama
es 655 añadidos; hasta 231 hojas sobre las conexiones actuales. Las versiones
previas conservan sus límites históricos. Casos 96/120/144/192: 384/432/480/576
añadidos y proyecciones 9516/10044/10572/11628 por árbol. Probar repetición,
contactos y cobertura; comparar en Godot bajo las mismas cámaras y luces.
No se inicia RF3 ni se interpreta la proyección como una copa generada.
Las fuentes 0.1.1 se conservan junto al resultado anterior antes de modificar
el adaptador compartido. [Contrato](../docs/contrato-rf2-moldes.md).

Resultado: 45 pruebas, nueve GLB importados, 60 capturas Godot, reconstrucción
de 0.1.1 idéntica y repetición de 144/192. Las 96 hojas y todas las conexiones
quedan intactas; las adiciones sobreviven al aumentar cantidad. Cobertura en
seis vistas: 120 hojas 60–71 %, 144 hojas 65–76 %, 192 hojas 74–84 %. Revisión
real: mayor continuidad; 192 más compacto y con más láminas solapadas en detalle.
El usuario aprueba la recomendación de 144 el 2026-10-23; se congela como
referencia de rama para RF3, sin aceptación de una copa completa ni promoción
a presets normales. [Aceptación y hashes](../docs/evidence/rediseno-follaje/rf2-densidad/aceptacion.json).
Galería: `artifacts/rediseno-follaje/rf2-densidad-01/index.html`.

### RF3. Primera copa completa sobre viejo-09 — verificada y aprobada como referencia

Implementación iniciada por autorización del usuario el 2026-10-23.
[Contrato RF3](../docs/contrato-rf3-copa.md): hasta 128 moldes y 49 ramas;
pool de 8192 muestras, reparto regional por superficie expuesta y máximo 2048
intentos de conexión. Piloto de 264 grupos × seis hojas, conservando la regla
RF2 aprobada; controles de perfil ancho y ocupación este reducida. Evaluación
con techo explícito 12500, manteniendo el valor histórico 10000 por defecto.
Estos controles son del piloto; no se inicia RF4 ni el lote.

Resultado implementado `foliage-canopy-0.1.0`: 45 piezas de madera Q3 intactas,
89 moldes y descarte de interiores global. De 8192 muestras, 2948 expuestas
en el piloto; reparto norte/este/sur/oeste 66/70/65/63 grupos. 264 conexiones y
1584 hojas, 10572 triángulos, tres materiales y altura 9 m. Perfil ×1.12 mantiene
coste y cambia extensión; este ×.4 baja su cupo 70→28 y total 9732, dejando las
otras regiones intactas. Control de hoja .75 m conserva soportes/raíces/ejes.

Verificación: 51 pruebas, siete GLB importados, repetición idéntica y 60
capturas Godot. Madera exportada/normales/corteza coinciden con el GLB Q3
original. Sin recortes en vistas generales; detalles deliberadamente recortados.
Revisión real: copa legible con lectura de hojas distinta de las masas, pero
láminas grandes y solapamientos persisten en detalle. No se aprueba por métricas.
El comprobador de contactos RF2 produjo un falso rechazo en el perfil ancho;
se sustituyó en RF3 por semiespacios de tubos convexos, sin mover geometría.
[Informe, límites y reproducción](../docs/evidence/rediseno-follaje/rf3/informe.md).

Trabajo:

1. Definir un perfil de copa para el objetivo RF0 y construir soportes y ramillas a partir de las ramas Q3 finales, usando la regla validada en la revisión de RF2. Elegir zonas portadoras y ocupación global antes de llenar de unidades.
   Referencia aprobada: rombo nominal de 1 m, conexiones rectas y configuración
   `leaves-144` de RF2 0.1.2. Usar los moldes Q3 de todo viejo-09, descartar sus
   superficies interiores y asignar hojas/conexiones por región y área expuesta;
   el presupuesto global prevalece sobre repetir el conteo de la rama aislada.
2. Generar una primera copa, respetando altura y presupuesto. Controlar por separado escala de detalle, cantidad, orientación y perfil; mantener explícitas sus interacciones.
3. Verificar hash completo de madera Q3 base, parámetros/semillas estructurales, transformación y materiales de corteza conservados. Registrar por separado hashes y coste de ramillas/conexiones nuevas. Mantener toda la geometría añadida dentro de la altura solicitada sin mover ni renormalizar la base.
4. Comparar con Q3 en todas las vistas y distancias RF0; inspeccionar el GLB en Godot. La composición del follaje puede cambiar: no se impone un IoU de 98 % con Q3.
5. Revisar tanto legibilidad de la copa como bordes, huecos y detalle intermedio. Distinguir una mejora de representación de simplemente aumentar tamaño, tapar ramas o cambiar iluminación.
6. Si las hojas opacas no permiten la lectura buscada dentro del presupuesto, documentar el fallo. Elegir entre revisar la unidad o ensayar tarjetas; no aumentar límites ni desarrollar otro método completo sin registrar la decisión.

Entregable: un roble completo reproducible, GLB válido, manifiesto y comparación contra Q3.

Salida: diferencia estética clara en distancias cercana/media, copa legible desde varios ángulos y capacidad de dirigir al menos un cambio de perfil y uno de ocupación. La revisión visual del resultado determina si se amplía a controles; pasar métricas no basta.

### RF4. Controles y estabilidad

Trabajo:

1. Congelar la regla elegida en RF3 y aplicarla a `viejo-00`, `viejo-03`, `adulto-00` y `joven-00`, sin ajustes particulares ocultos. Mantener `viejo-09` como piloto de ajuste.
2. Añadir tres semillas no usadas para ajustar el método: una por edad, seleccionadas de los casos Q3 existentes y registradas antes de generar. Identificarlas como controles reservados; no presentar como reservados casos ya inspeccionados para calibrar el método.
3. Comprobar reproducibilidad, densidad cero, extremos del contrato nuevo y altura/escala difíciles. Verificar por separado el efecto de semilla estructural y de follaje; variar esta última debe conservar la madera Q3 base. Hacer explícito si cambia recorridos o ramillas; los controles exclusivos de hojas deben conservar también la madera añadida.
4. Medir conteos, ocupación por zonas y resultados de cambios aislados de parámetros. Revisar todo junto con imágenes reales; no convertir porosidad o visibilidad de ramas en objetivos a maximizar.
5. Exportar e importar todos los controles en Godot. Registrar rechazos y las condiciones en que falla un estilo/preset, sin corregir cada semilla a mano.

Entregable: galería y tabla de resultados, incluidas fallas y límites conocidos.

Salida: el resultado no depende solo de viejo-09; conserva el objetivo visual entre edades y semillas. Si necesita ajustes de regla, repetir los casos afectados y mantener identificada la revisión del algoritmo. La prueba reservada mide ese conjunto acotado, no demuestra generalización a todos los árboles.

### RF5. Integración, lote y cierre de la nueva familia

Trabajo condicionado a RF4 satisfactoria:

1. Integrar la versión de follaje elegida en la ejecución normal con contrato y versión explícitos. Mantener las versiones históricas reconstruibles. No es necesario un editor ni un selector visual de estilos.
2. Resolver la representación del estilo en el contrato y el destino de presets antes de promoverlo. Dejar claro cómo generar Q3 y el nuevo estilo; no dejar Q3b como opción predeterminada accidental.
3. Generar los treinta casos con parámetros/semillas base Q3 y ajustes de follaje nuevos explícitos. Si cambia la interpretación de un parámetro, versionarla y documentarla; no fingir equivalencia numérica entre controles distintos.
4. Ejecutar regresión de madera, repetición, límites, validación de exportación, importación y revisión visual en Godot. Ningún caso puede figurar como aceptado si está incompleto o falló.
5. Registrar diferencias, coste de generación, complejidad final y límites. Determinar si la nueva familia se aprueba como alternativa o como predeterminada, sin borrar la familia poligonal.
6. Documentar cómo añadir después otro perfil de arquitectura y otra representación. Separar los datos reutilizables de las reglas propias del roble; no implementar especies adicionales para cerrar este plan.

Entregable: nueva familia de follaje reproducible, lote validado, documentación y decisión de promoción explícita.

Salida: criterios técnicos cumplidos y aceptación visual registrada para la nueva familia. Si el resultado no supera la hipótesis visual, el plan puede cerrar con un experimento no logrado y Q3 conservada; el volumen de código o las pruebas aprobadas no constituyen éxito estético.

## 6. Controles y verificación

| Control | Cambio buscado | Lo que debe permanecer fijo durante la prueba |
| --- | --- | --- |
| Tamaño de hoja/unidad | Cambiar escala del detalle | Madera, soportes, conteo y orientaciones |
| Densidad de colocaciones | Cambiar cantidad/ocupación; distinguir soportes de hojas por metro de portador | Tamaño de unidad y madera Q3 base; hojas por metro conserva ramillas, variar soportes registra cambios de madera añadida; conservar ids supervivientes cuando corresponda |
| Patrón local | Repartir hojas a lo largo del portador o en su extremo | Mismo soporte y presupuesto de comparación; origen y reglas de orientación explícitos |
| Orientación | Cambiar lectura/dirección local | Soportes, conteo, tamaños y madera |
| Perfil de copa | Cambiar contorno y regiones portadoras | Madera Q3 base, representación y semilla de variación; registrar cambios de ramillas |
| Peso de una región | Abrir/cerrar una zona identificable | Perfil objetivo y controles de otras zonas; medir los efectos de solapamiento |
| Semilla de follaje | Producir otra distribución dentro de los mismos controles | Estructura y madera Q3 base; registrar si modifica recorridos o ramillas |

No todos los controles requieren independencia exacta en el resultado visible. Sí requieren una intención verificable, datos intermedios inspeccionables y efectos secundarios registrados.

Validación técnica:

- Números finitos, índices y materiales válidos, ausencia de triángulos degenerados y alturas correctas.
- Madera Q3 base completa idéntica en coordenadas, polígonos/sombreado y transformación. Validar sobre la salida final, no solo sobre las curvas previas a normalización. Identificar y validar por separado las ramillas/conexiones nuevas, sus uniones, conteos y límites.
- GLB concordante con la malla evaluada e importación Godot con escala/orientación/materiales coincidentes.
- Repetición con mismas versiones, parámetros, semillas y entorno; manifiestos con hashes de todas las fuentes ejecutadas.
- Pruebas pequeñas de contrato, semillas y cambios de controles; integración con Blender/Godot cuando cambie la geometría. No escribir pruebas que solo repitan la implementación.

Validación visual:

- Comparaciones con cámara, luz, materiales de referencia y resolución congelados por pareja. Documentar cambios de material necesarios para la nueva representación como parte del algoritmo, sin esconderlos como cambios de iluminación.
- Revisar frente, perfil, arriba, abajo y perspectiva, además de distancias de lectura. Mantener evidencia seleccionada y un recorrido de inspección del asset en Godot.
- Evaluar lectura de follaje, continuidad de copa, variedad controlada, relación con ramas y defectos de normales/repetición. Explicar qué mejoró y qué empeoró.
- Las máscaras y la ocupación sirven de diagnóstico. No se fijan porcentajes de huecos o cobertura como garantía de naturalidad sin calibración visual previa.

## 7. Presupuestos, tiempos y procedencia

- Desde la autorización del 2026-10-23, hasta **12 500 triángulos y 3 materiales por árbol exportado** del rediseño, incluidos madera base, ramillas/conexiones y follaje. Presupuesto disponible: `12 500 − triángulos de madera Q3 base − triángulos de ramillas/conexiones nuevas`. Medir tras realizar instancias, aplicar modificadores y exportar. Referencias y contratos históricos conservan su techo de 10000; la integración normal del estilo se resuelve en RF5.
- Antes de poblar una copa, calcular un límite de unidades, soportes y madera nueva a partir de su coste máximo; limitar también intentos de colocación y datos intermedios. Contar hojas por unidad: una ramilla de siete hojas no cuesta lo mismo que una sola hoja, aunque ambas se instancien una vez. Tallos y conexiones visibles consumen el mismo presupuesto total. No confiar solo en detectar el exceso al finalizar.
- Como punto de partida, generación con límite de 120 s por trabajo y capturas/verificaciones con 180 s por subproceso, usando procesos terminables y sin reintentos automáticos. Registrar cualquier modificación necesaria; no permitir crecimiento o esperas sin cota.
- Mantener el entorno fijado en [README](../README.md), salvo incompatibilidad comprobada y registrada. Medir tiempo de generación y tamaño de GLB; no inferir FPS solo de triángulos.
- Semillas estructural y de follaje separadas; usar identificadores estables para evitar reordenar toda la distribución al variar la cantidad. Registrar versión de perfil y de representación.
- Fuentes en el repositorio; resultados nuevos bajo `artifacts/rediseno-follaje/` y evidencia seleccionada en `docs/evidence/rediseno-follaje/` cuando exista. Son destinos previstos, no carpetas con resultados ya disponibles.
- Cada informe debe distinguir planeado, implementado, verificado técnicamente y aprobado visualmente. Conservar manifiestos de fallos útiles y comandos de reproducción reales cuando se creen; no inventar scripts aún inexistentes.

## 8. Riesgos y decisiones de salida

| Riesgo | Respuesta prevista |
| --- | --- |
| Hojas opacas forman placas, erizos o patrones repetidos | Resolver orientación y agrupación en RF1/RF2, sin ocultarlo aumentando densidad |
| Un detalle atractivo no llena una copa dentro del presupuesto | Estimar viabilidad en RF1 y comprobarla en RF3; reconsiderar representación antes del lote |
| Perder volumen al buscar huecos | Usar un perfil de copa y revisar varias vistas; no maximizar ramas visibles |
| Volver a un aspecto de rocas con otra topología | Exigir diferencia de lectura en RF2/RF3; no evaluar solo componentes conectados |
| Una representación depende de texturas o transparencia | Comparar esa alternativa de forma acotada; medir el material en Godot y registrar el cambio artístico |
| Introducir arquitectura de especies antes de tiempo | Mantener recorridos, ramillas y perfiles separados; acotar la madera añadida y conservar la base Q3 |
| Mezclar mejoras geométricas con cambios de cámara/luz | Congelar escenas y registrar cambios de representación por separado |
| Romper referencias al integrar nuevos contratos | Versionar; conservar hashes, presets y reconstrucción histórica |

No se promete un resultado mejor antes de compararlo. Si una etapa no ofrece un avance visual útil, se itera en esa escala o se registra la hipótesis descartada antes de avanzar. Las revisiones visuales se hacen sobre entregables concretos; los ajustes rutinarios dentro de una fase no requieren pedir confirmación para cada parámetro.

## 9. Estado y siguiente acción

| Fase | Estado actual |
| --- | --- |
| RF0: objetivo visual y comparación | Preparado; usuario autoriza continuar desde RF0/RF1 |
| RF1: unidad y contrato | Verificada técnicamente; unidad usada para RF2 por autorización del usuario |
| RF2 original: portadores invisibles | Verificada técnicamente; criterio visual no conseguido |
| Comparación de addons previa a RF3 | Seis modelos verificados en Godot; decisión de continuar con el generador propio registrada |
| Revisión de RF2 con ramillas visibles | Implementada y verificada: conexiones legibles en detalle; volumen insuficiente, salida artística pendiente |
| Ensayo RF2 con moldes Q3 invisibles | Implementado/verificado, mayor presencia y cobertura; tamaño/forma por revisar, aprobación artística pendiente |
| Aumento aditivo de hojas RF2 | 96/120/144/192 verificados; rama de 144 aprobada el 2026-10-23, referencia para RF3 |
| RF3: copa piloto | Implementada/verificada en Godot: 10572 triángulos; aprobada como referencia del primer tipo el 2026-10-23 |
| RF4: controles | B3 revisada: 22 éxitos, tres rechazos; joven .45 m y contacto de 20 m resueltos. Aceptación artística pendiente |
| RF5: integración y lote | Primer blueprint integrado en B2; perfiles/promoción de familia y lote pendientes |

El [sistema de blueprints](sistema-blueprints.md) queda cerrado técnicamente en
B5. B2 integra la generación y B3 cubre los controles RF4 de los casos ensayados;
la revisión resuelve tamaño joven y contacto de 20 m. B4 aporta un segundo tipo
para comprobar reutilización. La referencia RF3 permanece aprobada; perfiles
nuevos y tipo columnar siguen experimentales. **No se ejecuta ni promueve el lote
RF5 al cerrar B5**: queda para una decisión posterior separada.
Galería RF3 conservada: `artifacts/rediseno-follaje/rf3-acceptance-02/index.html`.
