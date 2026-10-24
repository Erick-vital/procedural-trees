# Dirección de rediseño del follaje

Fecha de fundamento: 2026-10-22; avance actualizado el 2026-10-23. RF0/RF1 dieron paso a RF2: [ficha](follaje-rf0-rf1.md), [unidad](evidence/rf0-rf1/informe.md), [rama RF2](evidence/rf2/informe.md). Tras comparar addons se continuó con el generador propio. El usuario propuso moldes Q3 invisibles y aprobó la rama de 144 hojas. La [primera copa RF3](evidence/rediseno-follaje/rf3/informe.md) está implementada y verificada en Godot: mayor presencia y lectura distinta de masas cerradas, aprobada por el usuario el 2026-10-23 como referencia del primer tipo; [conservación B0](evidence/blueprints/b0/informe.md). Las fases y el alcance se concretan en el [plan activo](../plans/rediseno-follaje.md). El [plan v1](../plans/v1-generador-arboles.md) conserva la infraestructura; F4–F6 y especies adicionales siguen fuera de este ensayo.

## Decisión de partida

El usuario considera casi iguales Q3 y la fusión parcial y propone cerrar esta familia como aprobada, conservándola para su estilo de masas poligonales. Se registra la aprobación del resultado mostrado: Q3 como referencia y la variante fusionada sobre los cuatro controles, sin atribuir superioridad a esta última ni aprobar un lote fusionado que no existe. Q3b sigue rechazada. La siguiente dirección es diseñar un follaje más controlable y con una estética diferente, preparado para admitir otras arquitecturas de árbol en el futuro.

La evidencia acredita un límite práctico de las revisiones ensayadas, no un máximo demostrado de todo método basado en esferas. La fusión conserva las formas, tamaños y distribución Q3 de entrada; por construcción, hereda buena parte de su carácter visual. Más continuidad topológica no implica otra composición ni otro aspecto de superficie. Véase el [informe del ensayo](evidence/q3-fusion/informe.md).

La [comparación posterior con Easy Tree y Sapling](evidence/comparacion-addons/informe.md) conduce a continuar con tres directrices: conservar de Q3 el control del volumen y la silueta; incorporar ramillas y conexiones visibles para sostener las hojas; evaluar la distribución por cuánto contribuye a formar la copa deseada. Las configuraciones ensayadas de los addons no alcanzan conjuntamente estos objetivos; siguen como referencias, sin atribuirles una incapacidad general.

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

La madera Q3 base aprobada se conserva exactamente. La revisión de RF2 podrá añadir ramillas/conexiones visibles como geometría identificada por separado y contada en el mismo presupuesto total. Más adelante, una arquitectura distinta podrá requerir otras reglas de ramas y disposición de hojas; remodelar tronco o ramas Q3 queda fuera del alcance vigente, limitado al roble.

## Secuencia propuesta y avance

1. Elegir unas pocas referencias visuales coherentes y fijar cómo debe leerse el follaje de cerca y a una distancia representativa del juego. Las capturas previas a 101–108 m no cubren todos los usos posibles.
2. Construir una sola ramilla y un grupo pequeño con hojas geométricas opacas. Variar parámetros explícitos de orientación, separación y tamaño; revisar varias vistas con cámara y luz fijas.
3. Si ofrece una lectura claramente distinta y útil, repetir esa unidad sobre una rama aprobada. Comprobar que puede crear tanto zonas densas como huecos sin depender de objetos grandes cerrados.
4. Solo después producir la copa de un roble, conservando inicialmente su madera. Evaluar silueta contra la intención artística acordada, no exigir una coincidencia del 98 % con Q3: el rediseño debe poder cambiar la forma visible.

Comparar bajo condiciones reproducibles: claridad del cambio visual, control de parámetros, relación de soporte, huecos desde varios ángulos, facetas/normales, triángulos, materiales y exportación/importación Godot. El usuario eleva el presupuesto del rediseño a 12500 triángulos/3 materiales el 2026-10-23; los contratos históricos conservan 10000. Si se estudian tarjetas, medir también el coste de su cobertura de pantalla, sin inferirlo solo del número de triángulos.

La unidad RF1 se aplicó en RF2 sobre la primaria congelada y sus tres secundarias originales: hojas distintas de las masas, pero suspendidas y con escasa cobertura. La revisión 0.2.0 aísla conexiones visibles con hojas idénticas y luego dirige la distribución hacia una región Q3. Las conexiones se leen en detalle; el alcance .55/.8 m sigue sin formar el volumen buscado. El caso de doce soportes tiene una proyección presupuestaria viable, pero poca presencia a distancia. Se itera en la escala de rama antes de RF3; la representación definitiva sigue pendiente y la familia aprobada se conserva.

Por propuesta del usuario se prueban las masas Q3 originales como moldes invisibles: muestreo de superficie por área, descarte de zonas interiores solapadas y conexiones hacia grupos situados cerca del contorno. Dos parejas aíslan tamaño de hoja: hexágonos .45/.8 m y rombos .8/1 m. El rombo de 1 m recupera 54–64 % de cobertura proyectada Q3 en seis vistas, con 96 hojas/384 triángulos añadidos; conserva más presencia, pero sus piezas se ven grandes y angulosas. La comparación entre parejas cambia varias variables y no atribuye la diferencia a una sola. Revisar forma/escala y continuidad antes de RF3; el volumen de una copa completa sigue sin probarse.

El usuario expresa gusto por el resultado y pide más hojas. El ensayo aditivo 0.1.2 conserva las 96 originales, tamaño y conexiones, y compara 120/144/192. Con el nuevo techo, sus proyecciones 10044/10572/11628 son aritméticamente viables. La revisión Godot muestra más continuidad y mayor compactación con 192; el usuario aprueba la recomendación de 144 el 2026-10-23 como referencia de rama para RF3. Esa aprobación permite construir la copa, que requiere una revisión propia. [Comparación, aceptación y reproducción](evidence/rediseno-follaje/rf2-densidad/informe.md).

RF3 aplica esa representación a toda la copa de viejo-09: 89 moldes con descarte global de interiores y reparto por área expuesta, 264 grupos/1584 hojas y 10572 triángulos. Madera Q3 y altura 9 m intactas. Los controles muestran que anchura y ocupación de una zona cambian con efectos registrados; las escalas de lectura mantienen presencia. La copa es un entregable real revisado en Godot, todavía pendiente de aprobación artística antes de contrastar otras edades/semillas en RF4. [Resultados y límites](evidence/rediseno-follaje/rf3/informe.md).
