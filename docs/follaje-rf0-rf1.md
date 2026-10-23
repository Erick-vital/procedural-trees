# Ficha visual y contrato experimental RF0/RF1

Fecha: 2026-10-22. Ficha de las dos primeras fases del [plan activo](../plans/rediseno-follaje.md). La propuesta dio paso a RF2 por autorización posterior del usuario: [rama y límites observados](evidence/rf2/informe.md). No establece una estética definitiva ni aceptación de una copa. [Resultados RF0/RF1](evidence/rf0-rf1/informe.md).

## Objetivo visual

Mantener el carácter geométrico y el verde opaco de Q3, pero construir el detalle con superficies de hoja orientadas, abiertas y pequeñas. De cerca deben distinguirse raíz, punta y pliegue; a media distancia interesa la organización en conjuntos y el aire entre ellos. A distancia lejana se juzgará la lectura de la copa completa cuando exista RF3, sin exigir reconocer cada hoja.

| Referencia visual | Procedencia | Rasgo que guía la propuesta | Lo que no se toma como objetivo |
| --- | --- | --- | --- |
| [Q3 viejo-09](evidence/rf0-rf1/rf0-views.jpg) | Generador propio 0.4.0, lote aprobado; especificación/hash en el [bloqueo](evidence/rf0-rf1/reference-lock.json) | Escala general, madera y paleta compatibles con la familia aprobada | Repetir masas cerradas o conservar un IoU casi idéntico |
| [Hojas y bellotas de Q. robur](evidence/rf0-rf1/robur-mpf.jpg) | Foto de MPF, [ficha original](https://commons.wikimedia.org/wiki/File:Quercus_robur.jpg), [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/); descarga sin cambios, 701×948 | Lámina ancha, unión basal identificable y hojas que se solapan alrededor de un recorrido | Bellotas, nervaduras, daños y reproducción botánica de cada lóbulo |
| [Rama de Tuntorp](evidence/rf0-rf1/tuntorp-wcarter.jpg) | W.carter, 2022-10-02; [ficha original](https://commons.wikimedia.org/wiki/File:Oak_leaves_on_a_branch_in_Tuntorp.jpg), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); miniatura del servidor 960×640 | Hojas de varias orientaciones; pequeños huecos y contorno que procede de láminas superpuestas | Color otoñal, contraluz y transmisión de luz de una hoja real |

Las tres referencias tienen responsabilidades distintas dentro de una sola dirección: roble estilizado de hojas anchas. Las fotografías guían organización y escala relativa; Q3 guía estilo y estructura. Son referencias observadas, no imágenes generadas ni una promesa de fotorealismo. Las fotos no ofrecen malla/material neutro: no se puede separar su iluminación por una prueba 3D. No se atribuye su transmisión al prototipo opaco. Las observaciones de Easy Tree/Sapling se conservan como investigación técnica, no se usa una captura texturizada de esos addons como meta geométrica.

Se desean pliegues suaves y cambios de plano legibles, uniones organizadas y variación acotada. Se evitarán pompones cerrados, hojas enormes que oculten el soporte y ruido sin dirección. Por ejemplo: aumentar largo de .18 a .27 m debe agrandar las mismas hojas; bajar separación de .09 a .06 m aumenta su cantidad; cambiar inclinación de 65° a 105° cambia su dirección, sin cambiar el recorrido virtual.

La primera hipótesis sigue siendo geometría opaca de doble cara. Se comparan **exactamente tres formas**: rombo mínimo, hexágono plano y el mismo hexágono plegado. Estas siluetas son simplificaciones de coste bajo; todavía no representan el contorno lobulado de una hoja de roble. No se introduce una cuarta forma ni tarjetas texturizadas en RF1.

## Referencia y escenas congeladas

Se lee `artifacts/q3/acceptance/lote/viejo-09/`, siempre versión 0.4.0. Se registran hashes de `tree.blend`, `tree.glb` y `manifest.json`, especificación, streams, normalización final y hash de madera. El archivo fuente no se escribe.

Rama seleccionada antes de probar unidades: `q3:primary:100`, índice 0 del canal `Primary` de la estructura guardada. Su malla tiene 72 vértices/140 triángulos. El diagnóstico reconstruido identifica los índices de la referencia dentro de 10 µm; la selección final copia los **polígonos y coordenadas originales**, sin redondearlos ni remodelarlos. El bloqueo guarda índices fuente, posiciones, polígonos, sombreado, recorrido de 64 muestras en metros finales, matriz y material. Esto es una rama primaria; las secundarias y su follaje asociado se resolverán en RF2.

Las cámaras son ortográficas a 900×900, con frontal, lateral, superior, inferior oblicua, perspectiva oblicua y reverso. El nombre `perspective` identifica una vista oblicua, **no** proyección perspectiva. Se conservan posición, rotación, base completa, escala ortográfica y focal nominal de 50 mm, que no afecta la proyección ortográfica. No se usa FOV para estas cámaras.

Las tomas de juego son un protocolo inicial de ocupación de pantalla, no distancias físicas de una cámara de juego: frontal cercana/media/lejana con altura proyectada de 50/25/10 %, respectivamente 450/225/90 píxeles. Se elige ortográfica para fijar la escala sin introducir perspectiva todavía. Para 9 m, sus escalas verticales son 18/36/90 m. Los valores realmente proyectados se comprueban y guardan; todas las cámaras proceden solo de Q3. RF3 deberá reutilizarlas, sin reencuadrar su candidato.

Las unidades comparten otra escena de detalle, centrada en `(0,0,.325)` m y escala vertical .936 m. Tampoco se recalcula por forma ni tamaño. La presentación ampliada de unidades no demuestra su legibilidad a escala de árbol; esa comprobación queda para RF3.

Blender usa Workbench, estudio `paint.sl` rotado .5 rad, color de material, sombras activas y cavity desactivado; fondo RGB (.09,.11,.14), Standard/None, exposición 0 y gamma 1. Se añade una toma de unidad con estudio rotado 2 rad. Godot usa Compatibility, luz direccional a (-35,-25,0)°, energía 1.2 y ambiente blanco .5. Las luces se mantienen entre variantes de cada renderizador; no se compara su luminosidad como métrica. Las bases de cámara se convierten completas a Godot para evitar diferencias de orden de Euler y conservar cenitales/reverso.

## Contrato de unidad 0.1.0

[Esquema](../schemas/foliage-unit.schema.json), [preset](../presets/foliage-unit.json), [validación y colocación](../src/treegen/foliage.py). Se mantiene fuera de `TreeSpec` y de los presets históricos. El manifiesto identifica `foliage-unit-0.1.0`; no lo etiqueta como salida Q3.

| Datos | Convención y límites |
| --- | --- |
| Espacio | Metros finales Blender, Z arriba. Godot: `(x,y,z) → (x,z,−y)` |
| Portador | Id y rama padre explícitos; inserción `parent_t` en [0,1], contexto `terminal` y región. Polilínea de 2–16 puntos, sin segmentos nulos ni reversión próxima a 180°, longitud total ≤2 m |
| Recorrido | Orden desde su raíz; coordenada longitudinal por longitud de arco. Marco transportado entre segmentos, sin elegir un nuevo eje global en cada hoja |
| Colocación | Id estable por soporte/índice, `support_t`, raíz de unión en el recorrido, largo efectivo y base ortonormal dextrógira. +X largo, +Y ancho, +Z normal |
| Tamaño | Largo .03–.5 m; ancho/largo .2–1; variación de tamaño 0–.3 |
| Disposición | Separación .03–.5 m; incremento azimutal 0–360°; inclinación 15–150° respecto a la tangente; roll -90–90° alrededor del largo; perturbación angular 0–25° |
| Forma | `diamond`: 2 triángulos; `hex`: 4, ambos con fold=0; `folded-hex`: 4, pliegue 0–55° por ala alrededor del eje longitudinal |
| Aleatoriedad | Semilla entera explícita 0–2147483646. SHA-256 por versión, semilla, id y canal; independiente de la forma. Cambiar semilla no cambia recorridos ni raíces |
| Trabajo | 1–32 hojas, máximo 128 triángulos, un material y ningún soporte visible. Subprocesos limitados a 120 s. No se interpreta cantidad cero en este experimento; esa prueba corresponde a RF4 |

La fase RF1 usa padre `rf1:synthetic`, un recorrido de .65 m y siete hojas. No pretende que este soporte proceda de la rama congelada: conectarlo a ella es RF2. La raíz de cada lámina está en el recorrido; no se añaden pecíolos ni madera. Las muestras se colocan a media separación y sucesivos múltiplos sobre el soporte; reducir separación cambia posiciones y cantidad. Los ids conservan índices, sin prometer posiciones invariantes al redistribuir densidad.

El adaptador Blender crea mallas desde cuatro o seis vértices por hoja y conserva normales planas por ala. El material mantiene alfa 1, sin texturas, transparencia ni descarte del reverso. El GLB usa `doubleSided=true`; esto no duplica sus triángulos, aunque tampoco demuestra coste de renderizado idéntico al de una cara. La inspección independiente comprueba normales unitarias/orientadas y áreas válidas, y admite una hoja matemáticamente plana. Blender valida con su `fastjsonschema` incluido el mismo subconjunto del esquema que valida `jsonschema` en el ejecutor; finitud, booleanos y límites geométricos se comprueban además en Python.

## Criterio de revisión

La unidad completa debe verse en varias direcciones y con ambas iluminaciones, sin pérdida por culling. Un plano aislado sigue pudiendo quedar de canto; el plegado tampoco garantiza área proyectada positiva en todos los ángulos. Las seis vistas muestreadas no prueban una rotación continua completa.

El plegado a 25° es un candidato de trabajo por su lectura de planos al mismo coste que el hexágono plano. No se promueve aún como representación final: algunas hojas siguen muy estrechas y el conjunto sin soporte visible parece suspendido. La aceptación estética de la ficha y de la unidad queda pendiente de revisión. RF2 deberá evaluar organización, vínculo con la rama y posibilidad de soportes invisibles antes de ampliar a copa.
