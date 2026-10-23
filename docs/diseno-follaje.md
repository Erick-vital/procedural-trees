# Dirección de rediseño del follaje

Fecha: 2026-10-22. Documento de fundamento; ninguna de las propuestas siguientes está implementada. Las fases y criterios se concretan en el [plan activo de rediseño](../plans/rediseno-follaje.md). El [plan v1](../plans/v1-generador-arboles.md) conserva el marco de infraestructura; no se inician F4–F6 ni se añaden especies por crear este diseño.

## Decisión de partida

El usuario considera casi iguales Q3 y la fusión parcial y propone cerrar esta familia como aprobada, conservándola para su estilo de masas poligonales. Se registra la aprobación del resultado mostrado: Q3 como referencia y la variante fusionada sobre los cuatro controles, sin atribuir superioridad a esta última ni aprobar un lote fusionado que no existe. Q3b sigue rechazada. La siguiente dirección es diseñar un follaje más controlable y con una estética diferente, preparado para admitir otras arquitecturas de árbol en el futuro.

La evidencia acredita un límite práctico de las revisiones ensayadas, no un máximo demostrado de todo método basado en esferas. La fusión conserva las formas, tamaños y distribución Q3 de entrada; por construcción, hereda buena parte de su carácter visual. Más continuidad topológica no implica otra composición ni otro aspecto de superficie. Véase el [informe del ensayo](evidence/q3-fusion/informe.md).

## Qué debe poder controlar el nuevo sistema

| Nivel | Decisión artística | Controles propuestos |
| --- | --- | --- |
| Copa global | Forma reconocible y proporciones | Perfil por altura, anchura, base de copa, inclinación y asimetría |
| Arquitectura | Cómo se sostiene y organiza el follaje | Ramas portadoras, ramillas terminales, orientaciones y agrupación |
| Ocupación | Dónde hay follaje y dónde hay aire | Zonas densas, transiciones, corredores y separación entre grupos |
| Representación | Qué geometría y material hacen visible el follaje | Masas facetadas, grupos de hojas geométricas o tarjetas de hojas |

La copa objetivo describe una intención, no una superficie sólida que haya que mostrar. Puede guiar la distribución y el tamaño de grupos sin convertirse en una cúpula. La densidad local y la escala de hojas deben poder ajustarse por separado de la silueta; habrá que medir sus interacciones, no prometer independencia perfecta entre controles geométricos.

La precisión requiere controles observables: al pedir una copa más ancha, ajustar su perfil; al pedir una zona menos densa, actuar sobre esa zona; al pedir hojas mayores, cambiar la unidad de hoja. Evitar que un único parámetro de densidad cambie simultáneamente cantidad, posición y tamaño, como sucedía en Q3b.

## Unidad de construcción que propongo explorar

Una ramilla corta con un pequeño conjunto orientado de hojas o grupos de hojas. Su distribución dependería de la dirección local y de zonas portadoras de follaje. La irregularidad se aplicaría sobre esa organización mediante semillas explícitas y perturbaciones acotadas.

No se propone generar todas las hojas de un árbol desde el principio. Primero hay que comprobar si unas pocas unidades pequeñas pueden mantener una lectura de follaje desde varios ángulos y agruparse sin producir de nuevo pompones aislados.

La representación debería poder sustituirse conservando la misma disposición de ramillas:

- **Geometría opaca estilizada:** hojas simplificadas o pequeñas láminas de varias caras, con orientación y sombreado diseñados. Es la primera hipótesis a probar para conservar una estética geométrica sin introducir texturas de inmediato. Su coste y calidad están por medir.
- **Tarjetas de hojas:** planos o superficies con recortes de textura, como alternativa si se busca más detalle de contorno. Implican otra decisión artística y de materiales; no se dan por necesarias para mejorar. Godot documenta Alpha Scissor como modo apropiado para follaje con bordes recortados; eso no demuestra el rendimiento de nuestro árbol, que tendría que medirse en el motor. [Documentación oficial](https://docs.godotengine.org/en/stable/tutorials/3d/standard_material_3d.html#transparency).
- **Masas actuales:** conservarlas como estilo aprobado y referencia de coste/lectura. Su posible uso futuro a distancia sería otro ensayo, no un LOD ya validado.

El cambio estético buscado debe observarse también en el contorno y los huecos a escala intermedia, además de en las sombras entre piezas. Una nueva malla conectada que siga mostrando las mismas formas Q3 no satisface por sí sola ese objetivo.

## Preparación para otros árboles

Separar perfil de arquitectura, distribución de follaje y representación. Como objetivos artísticos ilustrativos: copa ancha e irregular, copa organizada en pisos o conjuntos colgantes. No prometer distinguir especies cambiando solamente la hoja o el tamaño de los grupos sobre las mismas ramas.

La madera aprobada se conserva para aislar el primer experimento de representación. Más adelante, una arquitectura distinta podrá requerir otras reglas de ramas, ramillas y disposición de hojas. Esto amplía el diseño futuro; la implementación vigente continúa limitada al roble.

## Siguiente experimento propuesto, todavía sin implementar

1. Elegir unas pocas referencias visuales coherentes y fijar cómo debe leerse el follaje de cerca y a una distancia representativa del juego. Las capturas previas a 101–108 m no cubren todos los usos posibles.
2. Construir una sola ramilla y un grupo pequeño con hojas geométricas opacas. Variar parámetros explícitos de orientación, separación y tamaño; revisar varias vistas con cámara y luz fijas.
3. Si ofrece una lectura claramente distinta y útil, repetir esa unidad sobre una rama aprobada. Comprobar que puede crear tanto zonas densas como huecos sin depender de objetos grandes cerrados.
4. Solo después producir la copa de un roble, conservando inicialmente su madera. Evaluar silueta contra la intención artística acordada, no exigir una coincidencia del 98 % con Q3: el rediseño debe poder cambiar la forma visible.

Comparar bajo condiciones reproducibles: claridad del cambio visual, control de parámetros, relación de soporte, huecos desde varios ángulos, facetas/normales, triángulos, materiales y exportación/importación Godot. El presupuesto actual de 10 000 triángulos/3 materiales se mantiene como punto de partida; cualquier cambio requerirá registrarse. Si se estudian tarjetas, medir también el coste de su cobertura de pantalla, sin inferirlo solo del número de triángulos.

El siguiente entregable sería una prueba pequeña de unidad de follaje, no un generador multiespecie completo. No se decide todavía su representación definitiva ni se reemplaza la versión aprobada.
