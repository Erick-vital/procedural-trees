# Plan: rediseño del follaje procedural

Fecha: 2026-10-22.
Estado: plan creado y revisado tras analizar las instalaciones locales de Easy Tree 1.0.1 y Sapling Tree Gen 0.3.7; RF0–RF5 pendientes. Las pruebas acotadas de esos addons son investigación, no implementación de este rediseño.

## 1. Objetivo y relación con v1

Construir una segunda familia de follaje con una lectura visual claramente distinta de las masas poligonales actuales y controles más precisos sobre forma, distribución y orientación. La primera aplicación será un roble sobre la madera Q3 aprobada. La arquitectura debe permitir investigar otros tipos de árbol posteriormente, sin prometer representarlos cambiando únicamente las hojas.

Este documento dirige el rediseño del follaje. El [plan v1](v1-generador-arboles.md) conserva los contratos y la infraestructura ya implementada; F4–F6 continúan pendientes durante este trabajo y F3/bosques sigue diferida. Es un cambio explícito respecto a mantener todas las revisiones Q en un único plan: el usuario solicita ahora un plan separado para una nueva familia de follaje. No se declara terminada v1 ni se ejecutan sus experimentos de IA por este cambio.

Fundamento: [dirección de diseño](../docs/diseno-follaje.md). Evidencia anterior: [Q3](../docs/evidence/q3/informe.md) y [fusión parcial](../docs/evidence/q3-fusion/informe.md).

### Revisión importante a partir de los addons instalados

El [análisis local reproducible](../docs/evidence/addons-follaje/informe.md) confirma que la forma de la hoja y la colocación no bastan como dos bloques genéricos. Easy Tree construye una unidad de ramilla con varias hojas y después la coloca sobre el esqueleto; Sapling conserva contexto del tallo, orientación y posición longitudinal para distribuir y orientar hojas. Se concretan tres decisiones del plan:

- Los portadores deben describir recorridos finos, origen de inserción y contexto terminal, no solo puntos y vectores sin organización. Evaluar la lectura de esos portadores invisibles en RF2, antes de suponer que bastan para llenar una copa.
- Separar el patrón local de hojas —distribuidas a lo largo del portador o agrupadas en su punta— de su geometría, con controles de separación, azimut e inclinación. No fijar un ángulo universal ni esconder modos distintos en el signo de un número.
- Comparar prototipos de coste mínimo y distinguir el efecto de geometría, orientación y material. Sapling produce hojas hexagonales de cuatro triángulos; Easy Tree combina hojas y texturas con recortes. El éxito de una referencia texturizada no prueba la estética de una lámina opaca equivalente.

Estas precisiones no incorporan código/activos de los addons ni los convierten en dependencias. Tampoco autorizan rehacer la madera. Las pruebas de carga/generación realizadas no acreditan exportación Godot ni calidad estética de esos addons bajo nuestro presupuesto.

## 2. Punto de partida y decisiones

- La familia de masas poligonales se conserva como estilo aprobado. Q3 0.4.0 es la referencia reconstruible; Q3b 0.4.1 permanece rechazada. La aprobación de la fusión se limita a los cuatro casos mostrados, sin superioridad atribuida ni lote fusionado completo.
- Referencia Git previa: `fbe87a4`, etiqueta `q3-referencia-0.4.0`; ensayo de fusión en `4fa3d8c`. Las fuentes históricas y sus resultados no se sobrescriben.
- El resultado de fusión no demuestra un límite absoluto de métodos basados en esferas. Mantener su composición inicial restringía el cambio estético. Este plan cambia la unidad de representación y su organización.
- Primera hipótesis: conjuntos pequeños de hojas geométricas opacas, orientados sobre portadores virtuales. Es una hipótesis por evaluar, no una representación definitiva aprobada. Tarjetas texturizadas quedan como alternativa si la primera hipótesis falla artística o técnicamente.
- Se conservará exactamente la madera Q3 final durante este plan. Las nuevas ramillas describirán soportes y orientaciones virtuales; añadir madera visible o sustituir la arquitectura del árbol requerirá registrar un cambio de alcance separado.
- Los presets principales aún apuntan a Q3b. Para toda referencia de este plan se cargarán explícitamente `presets/v0.4.0/` o `presets/q3-cases.json`. La promoción de una variante se resuelve en RF5, no alterando silenciosamente la referencia.

## 3. Alcance

Incluye:

- Dirección visual, unidad de hoja/grupo pequeño, disposición en una rama y construcción de una copa completa.
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

Flujo conceptual: `madera Q3 + perfil de copa → soportes virtuales → disposición de follaje → representación → malla evaluada → GLB → Godot`.

| Componente | Responsabilidad | Invariante o separación |
| --- | --- | --- |
| Referencia estructural | Leer curvas, relaciones y transformación final Q3 | Madera exportada idéntica, sin nueva normalización dependiente del follaje |
| Perfil de copa | Expresar contorno objetivo por altura, base de copa, anchura y asimetría | Es una guía espacial; no se exporta como un sólido visible |
| Soportes virtuales | Definir recorridos finos, inserción, longitud y marco local de los grupos | Referencia a rama padre y contexto terminal; sin añadir geometría de madera |
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

Salida: objetivo suficientemente concreto para distinguir un nuevo follaje útil de otro conjunto de poliedros, sin exigir parecido casi idéntico a Q3. La ficha se revisa visualmente antes de escalar los prototipos.

### RF1. Unidad de follaje y contrato experimental

Trabajo:

1. Definir el contrato mínimo de soportes y colocaciones: unidades, identificadores, ejes locales, rangos, controles, semillas y límites. Mantenerlo experimental y versionado, separado de los presets históricos.
2. Construir una unidad pequeña sobre un portador virtual: una hoja simplificada o un grupo reducido de hojas, con contornos que no partan de una esfera cerrada. Comparar como máximo tres variantes iniciales de forma/plegado, incluyendo una lámina de coste mínimo y una forma hexagonal simple antes de añadir subdivisiones.
3. Controlar tamaño, proporción, separación, orientación y variación acotada. Definir origen de unión, eje longitudinal y normal de la hoja; separar giro alrededor del soporte e inclinación respecto a él. Resolver normales y lectura de frente/reverso en el GLB y en Godot, además de la vista Blender.
4. Registrar triángulos por unidad, materiales y un cálculo de cuántas unidades caben en el presupuesto del árbol. No multiplicar instancias antes de comprobar esa viabilidad.
5. Comprobar reconstrucción con semilla fija, efectos visibles de controles y rechazo de entradas inválidas.

Entregable: unidad reproducible, pequeña galería de variantes y contrato experimental documentado.

Salida técnica: geometría válida, exportable y con límites de trabajo; ninguna dependencia del generador de ramas nuevo. Salida visual: lectura convincente de hoja/grupo desde varias vistas, sin desaparecer al girar ni depender de una sola iluminación favorable. Si no se consigue, iterar esta unidad antes de construir la copa.

### RF2. Follaje sobre una rama aprobada

Trabajo:

1. Construir recorridos virtuales finos a partir de la rama congelada, con un origen de inserción y marco local estables. Orientar las unidades a lo largo de ellos y comprobar que no haya giros bruscos al cambiar la dirección del soporte. Mantener la geometría de madera seleccionada exactamente igual.
2. Distribuir grupos sobre zonas portadoras, con transiciones y variación reproducible. Separar cantidad de soportes, hojas por longitud de soporte y escala de hoja. Comparar un patrón a lo largo de una ramilla y otro agrupado en su punta para elegir el objetivo visual; no asumir que son intercambiables ni implementar un catálogo de especies. Evitar filas rígidas y ruido que destruya la organización, sin rechazar una disposición regular cuando sea parte del patrón elegido.
3. Probar tres niveles de densidad y al menos dos orientaciones de soporte con la misma regla; no confundir esos ejemplos con especies ya implementadas.
4. Revisar relación con la rama, repetición, acumulación en puntas y huecos desde abajo/lados. Comparar con el follaje Q3 asociado a la misma rama bajo las mismas condiciones. Evaluar explícitamente si los soportes invisibles hacen que las hojas parezcan flotar: si no se resuelve con su organización, registrar el problema y revisar el alcance de ramillas visibles antes de ampliar, sin afirmar que la restricción de madera ya funciona artísticamente.
5. Hacer variaciones de un control a la vez. Registrar el efecto buscado y los efectos secundarios, en vez de prometer independencia perfecta entre controles geométricos.

Entregable: rama con follaje nuevo y una matriz pequeña de densidad/orientación.

Salida: lectura visual distinta y útil frente a Q3, soporte claro y paso entre zonas densas y abiertas sin producir pompones aislados. Si el resultado vuelve a depender de volúmenes grandes cerrados, reconsiderar la unidad o distribución antes de ampliar.

### RF3. Primera copa completa sobre viejo-09

Trabajo:

1. Definir un perfil de copa para el objetivo RF0 y construir soportes a partir de las ramas Q3 finales. Elegir zonas portadoras y ocupación global antes de llenar de unidades.
2. Generar una primera copa, respetando altura y presupuesto. Controlar por separado escala de detalle, cantidad, orientación y perfil; mantener explícitas sus interacciones.
3. Verificar hash completo de madera, parámetros/semillas estructurales, transformación y materiales de corteza conservados. Mantener el follaje dentro de la altura solicitada sin mover ni renormalizar la madera.
4. Comparar con Q3 en todas las vistas y distancias RF0; inspeccionar el GLB en Godot. La composición del follaje puede cambiar: no se impone un IoU de 98 % con Q3.
5. Revisar tanto legibilidad de la copa como bordes, huecos y detalle intermedio. Distinguir una mejora de representación de simplemente aumentar tamaño, tapar ramas o cambiar iluminación.
6. Si las hojas opacas no permiten la lectura buscada dentro del presupuesto, documentar el fallo. Elegir entre revisar la unidad o ensayar tarjetas; no aumentar límites ni desarrollar otro método completo sin registrar la decisión.

Entregable: un roble completo reproducible, GLB válido, manifiesto y comparación contra Q3.

Salida: diferencia estética clara en distancias cercana/media, copa legible desde varios ángulos y capacidad de dirigir al menos un cambio de perfil y uno de ocupación. La revisión visual del resultado determina si se amplía a controles; pasar métricas no basta.

### RF4. Controles y estabilidad

Trabajo:

1. Congelar la regla elegida en RF3 y aplicarla a `viejo-00`, `viejo-03`, `adulto-00` y `joven-00`, sin ajustes particulares ocultos. Mantener `viejo-09` como piloto de ajuste.
2. Añadir tres semillas no usadas para ajustar el método: una por edad, seleccionadas de los casos Q3 existentes y registradas antes de generar. Identificarlas como controles reservados; no presentar como reservados casos ya inspeccionados para calibrar el método.
3. Comprobar reproducibilidad, densidad cero, extremos del contrato nuevo y altura/escala difíciles. Verificar por separado el efecto de semilla estructural y de follaje; variar esta última debe conservar la madera.
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
| Densidad de colocaciones | Cambiar cantidad/ocupación; distinguir soportes de hojas por metro de portador | Tamaño de unidad y madera; conservar ids de colocaciones supervivientes cuando corresponda |
| Patrón local | Repartir hojas a lo largo del portador o en su extremo | Mismo soporte y presupuesto de comparación; origen y reglas de orientación explícitos |
| Orientación | Cambiar lectura/dirección local | Soportes, conteo, tamaños y madera |
| Perfil de copa | Cambiar contorno y regiones portadoras | Madera, representación y semilla de variación |
| Peso de una región | Abrir/cerrar una zona identificable | Perfil objetivo y controles de otras zonas; medir los efectos de solapamiento |
| Semilla de follaje | Producir otra distribución dentro de los mismos controles | Estructura y madera final |

No todos los controles requieren independencia exacta en el resultado visible. Sí requieren una intención verificable, datos intermedios inspeccionables y efectos secundarios registrados.

Validación técnica:

- Números finitos, índices y materiales válidos, ausencia de triángulos degenerados y alturas correctas.
- Madera Q3 completa idéntica en coordenadas, polígonos/sombreado y transformación. Validar sobre la salida final, no solo sobre las curvas previas a normalización.
- GLB concordante con la malla evaluada e importación Godot con escala/orientación/materiales coincidentes.
- Repetición con mismas versiones, parámetros, semillas y entorno; manifiestos con hashes de todas las fuentes ejecutadas.
- Pruebas pequeñas de contrato, semillas y cambios de controles; integración con Blender/Godot cuando cambie la geometría. No escribir pruebas que solo repitan la implementación.

Validación visual:

- Comparaciones con cámara, luz, materiales de referencia y resolución congelados por pareja. Documentar cambios de material necesarios para la nueva representación como parte del algoritmo, sin esconderlos como cambios de iluminación.
- Revisar frente, perfil, arriba, abajo y perspectiva, además de distancias de lectura. Mantener evidencia seleccionada y un recorrido de inspección del asset en Godot.
- Evaluar lectura de follaje, continuidad de copa, variedad controlada, relación con ramas y defectos de normales/repetición. Explicar qué mejoró y qué empeoró.
- Las máscaras y la ocupación sirven de diagnóstico. No se fijan porcentajes de huecos o cobertura como garantía de naturalidad sin calibración visual previa.

## 7. Presupuestos, tiempos y procedencia

- Hasta **10 000 triángulos y 3 materiales por árbol exportado**, incluidos madera y follaje. Presupuesto de follaje disponible: `10 000 − triángulos de madera Q3 del caso`. Medir tras realizar instancias, aplicar modificadores y exportar.
- Antes de poblar una copa, calcular un límite de unidades y de soportes a partir de su coste máximo; limitar también intentos de colocación y datos intermedios. Contar hojas por unidad: una ramilla de siete hojas no cuesta lo mismo que una sola hoja, aunque ambas se instancien una vez. Un tallo visible opcional tampoco sería gratis ni estaría aprobado por este plan. No confiar solo en detectar el exceso al finalizar.
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
| Introducir arquitectura de especies antes de tiempo | Mantener soportes virtuales y perfiles separados; documentar la extensión sin rehacer madera |
| Mezclar mejoras geométricas con cambios de cámara/luz | Congelar escenas y registrar cambios de representación por separado |
| Romper referencias al integrar nuevos contratos | Versionar; conservar hashes, presets y reconstrucción histórica |

No se promete un resultado mejor antes de compararlo. Si una etapa no ofrece un avance visual útil, se itera en esa escala o se registra la hipótesis descartada antes de avanzar. Las revisiones visuales se hacen sobre entregables concretos; los ajustes rutinarios dentro de una fase no requieren pedir confirmación para cada parámetro.

## 9. Estado inicial y siguiente acción

| Fase | Estado al crear el plan |
| --- | --- |
| RF0: objetivo visual y comparación | Pendiente |
| RF1: unidad y contrato | Pendiente |
| RF2: rama | Pendiente |
| RF3: copa piloto | Pendiente |
| RF4: controles | Pendiente |
| RF5: integración y lote | Pendiente |

Próximo paso al iniciar la ejecución: RF0, preparar referencias y una ficha visual concreta usando la hipótesis de hojas geométricas opacas como punto de partida. Este plan no equivale a haber elegido una estética final, implementado el rediseño ni autorizado fases ajenas a su alcance.
