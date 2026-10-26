# Roble con láminas texturizadas: conservación de copa

Fecha: 2026-10-25. Solicitud del usuario: trasladar al roble el enfoque de láminas
texturizadas y reducción de tris, conservando silueta y volumen. Amplía la exclusión
previa del roble en el plan de pino. Estado vigente: piloto con pintura 0.2.0 y
ajuste de ramillas y tres láminas aprobados; **receta 2.1.0 integrada y cuatro casos
verificados**. Los apartados iniciales conservan el alcance
original; las ampliaciones posteriores documentan las decisiones del usuario.

Referencia: `roble_copa_ancha@1.2.0`, RF3/B3 y RF5 aprobados. Piloto viejo-09
(3009/17) y controles joven-07 (1007/17), adulto-00 (2000/17), viejo-00 (3000/17).
No se retoca distribución, cantidad, longitud, anchura, orientación o anclajes;
se conservan las seis hojas por conexión y toda la madera/ramillas de soporte.
No reducir plenitud ni trasladar el estrechamiento autorizado solo para pino.

El roble ya tiene hojas planas de dos tris. Ensayar un triángulo envolvente por
hoja y atlas RGBA con recorte del rombo aprobado: conservar los planos individuales
evita colapsar volumen por fusionar hojas de orientaciones diferentes. Atlas
procedural nuevo, con nervaduras/pinceladas reproducibles y contorno explícito;
no reutilizar ramillas de conífera. Cuatro variantes, hasta 2048², semilla paint
separada. Madera, corteza y ramillas originales en esta revisión conservadora.
Se acepta un ahorro menor que en pino si es necesario para conservar la copa.

Receta y contrato nuevos explícitos; históricos intactos. Separar algoritmo
puro, recursos, ejecución Blender, evaluación GLB y revisión Godot. GLB con PNG
embebido, ≤12500 tris/3 materiales, semillas y hashes, ≤120 s/generación y
≤180 s/subproceso de comprobación. Soportes transparentes pueden tener bounds
mayores; distinguir bounds geométricos del contorno visible de la pintura.

Comparar cuatro casos con misma cámara/luz, seis orientaciones y tres distancias;
revisar imágenes reales. Medir máscaras negras sin iluminación para aislar el
contorno de los cambios de color: objetivo IoU ≥.99 y cobertura ±1 % en vistas
de forma; documentar aliasing lejano sin confundirlo con volumen físico. Auditar
conservación exacta de placements/madera y geometría de las seis hojas, repetir
piloto, regenerar referencias y comprobar pino/columnar sin regresiones.

Entregables: cuatro árboles exportables, atlas y fuente reproducible, receta,
pruebas, comparación Godot, informe/galería y actualización breve de ESTADO.
Aceptación artística del resultado separada. Sin nuevo benchmark, lote RF5
completo, bosque, viento, LOD ni optimización adicional de madera por rutina.

## Pausa solicitada: aprobar pintura antes de integrar

El usuario pausa expresamente integración/optimización y prioriza aprobar una
pintura atractiva. El atlas procedural 0.1.0 es una prueba técnica del recorte,
**no pintura aprobada ni propuesta de producción final**. Ensayo conservado en
`artifacts/roble-pintado/review-02/`: cuatro casos, repetición/regresiones,
128 pruebas y 144 capturas. Máscaras de forma IoU .9906–.9976, pero con scissor .5
la cobertura lejana cae hasta ~9 %; no presentar conservación visual universal.
Sondeo de umbrales común .3/.35/.4/.45 conservado en `cutoff-probe/`; sin adoptar
nuevo umbral ni cambiar geometría mientras esté pausada esta línea de trabajo.

Primero: muestra artística de pintura de hojas, grupos y corteza, coherente con
la dirección A del pino, presentada como concepto para decisión del usuario.
No aplicar el concepto al árbol ni reanudar optimización hasta aprobación de
pintura e instrucción de continuar. Históricos y roble aprobado permanecen intactos.

Concepto de pintura generado con herramienta integrada y referencias propias:
[ficha para aprobación](../docs/evidence/roble-pintado/pintura-01/ficha.md).
Imagen inspeccionada; no es atlas ni render Godot, no valida silueta. Se mantiene
la pausa de integración/optimización hasta decisión del usuario.

## Rama de muestra autorizada y realizada

El usuario aprueba la dirección para hojas y corteza y solicita una rama antes
de retomar optimización. [Aceptación](../docs/evidence/roble-pintado/pintura-01/user-acceptance.json).
Se producen PNG nuevos 0.2.0 con ImageGen: cuatro hojas lobuladas RGBA y corteza
RGB, 1254², sin retoque de píxeles. Muestra aislada `q3:primary:100`, piloto
3009/17 y paint 2718: primaria/tres secundarias, 32 soportes y 192 hojas.
Dos tris por hoja, sin optimización: original y pintada 1104 tris. Contorno
lobulado nuevo, no identidad con los rombos; envelope nominal y colocaciones
conservados, volumen de copa completa aún sin validar con esta pintura.
Dos pruebas específicas, cuatro GLB repetidos idénticos, madera/normales exactas
y 29 capturas reales Godot revisadas. [Informe y reproducción](../docs/evidence/roble-pintado/rama-01/informe.md).
Aplicación a la rama pendiente de aprobación; integración/optimización del árbol
completo continúan pausadas. No adoptar el ensayo de un triángulo por hoja.

## Ajuste de alcance: ramillas de la muestra (2026-10-26)

El usuario valora favorablemente la rama con follaje, pero pide ensayar más grosor
y un estrechamiento más gradual antes de revisar el árbol completo. Esto autoriza
cambiar radios de soportes en una variante aislada, ampliando la conservación
de madera indicada arriba; no autoriza todavía integración al árbol completo.
Perfil opcional `fuller-v1`: base +25 %, punta al 50 % del radio de base,
sin anillos adicionales ni cambios de ejes, hojas o ramas mayores. 1104 tris
conservados; nueve pruebas, repetición exacta de cuatro GLB y 34 capturas reales
con cámaras comunes. Doce imágenes seleccionadas revisadas por el agente.
[Ensayo y reproducción](../docs/evidence/roble-pintado/ramillas-01/informe.md).
Variante rechazada por el usuario: engrosar no resuelve el salto entre rama gruesa
y ramillas directas. Diagnóstico: 19/32 soportes nacen de la primaria, 13/32 de
secundarias; el radio común no depende del receptor. Eliminar los primeros con
sus hojas perdería 59,4 % del follaje. Siguiente dirección propuesta: revisar
jerarquía/conexiones compartidas conservando plenitud, con coste por medir;
sin implementar ni ampliar aún la conservación de anclajes.
[Diagnóstico](../docs/evidence/roble-pintado/ramillas-01/diagnostico.md).
Integración completa sigue pendiente.

## Ensayo autorizado de jerarquía: madera sola (2026-10-26)

El usuario aclara que el problema son las ramas y autoriza quitar las ramillas
directas de la primaria, conservando las nacidas de secundarias. Esta instrucción
sustituye la propuesta anterior de conexiones compartidas para el siguiente ensayo.
`secondary-only-v1` exporta solo madera: 19 soportes eliminados, 13 conservados,
radios originales, sin tocar follaje ni recetas de árbol completo. 720 → 568 tris
(−152; −21,1 %), geometría/normales conservadas exactas y repetición idéntica.
Diez pruebas y 18 capturas Godot; nueve parejas revisadas visualmente.
[Resultado y reproducción](../docs/evidence/roble-pintado/jerarquia-01/informe.md).
Aceptación artística e integración pendientes; ninguna modificación de copa aplicada.

## Integración autorizada del piloto completo (2026-10-26)

El usuario valora positivamente la madera del ensayo y autoriza continuar con el
piloto completo, conservando las hojas y revisando el conjunto antes de controles.
[Autorización](../docs/evidence/roble-pintado/piloto-01/user-authorization.json).
Esto levanta la pausa para ese piloto y amplía la conservación original de madera:
solo soportes nacidos de secundarias; se retiran 136 de primarias y 8 del tronco,
se conservan 120. Ninguna hoja se elimina ni se mueve, incluso si pierde conexión
de madera. No se adopta el ensayo de un triángulo por hoja: dos por cada una de
las 1584 hojas, mismo atlas/corteza 0.2.0 de la muestra y semilla paint 2718.

Piloto `oak-painted-tree-pilot-0.1.0`: 10572 → 9420 tris, madera estructural intacta,
cuatro GLB repetidos idénticos, doce pruebas y 82 capturas reales. Poda: IoU ≥.99880
en nueve máscaras; pintura: el contorno lobulado **no cumple** la identidad .99/±1 %
con rombos del plan original (cobertura +2,63–3,58 % en seis vistas, −2,21 % lejana).
Se registra la desviación, sin cambiar hojas/alfa para forzar aceptación técnica.
[Informe, limitaciones y reproducción](../docs/evidence/roble-pintado/piloto-01/informe.md).
Aceptación artística del piloto pendiente; controles y catálogo aún sin integrar.

## Pintura aprobada y ensayo autorizado de cruzadas (2026-10-26)

El usuario aprueba explícitamente la pintura del piloto y solicita implementar
optimización por láminas cruzadas. [Aceptación](../docs/evidence/roble-pintado/piloto-01/user-acceptance.json).
Esta petición amplía el alcance inicial: se permite sustituir los seis planos
de hojas por grupo mediante representaciones de grupo, sin exigir identidad de
las hojas individuales. Se conserva madera y se compara plenitud/forma con el
piloto pintado aprobado; no adoptar resultados solo por ahorrar tris.

Ensayo `oak-crossed-trial-0.1.0`: ocho grupos representativos, atlas RGBA 2000²
con tres proyecciones sin iluminación por plantilla, usando la pintura 0.2.0.
264 marcos de grupo conservados; dos láminas (7308 tris) o tres (7836), frente
a 9420. Catorce pruebas, seis GLB repetidos con atlas congelado y 108 capturas.
Dos láminas no recomendadas: copa rala. Tres: candidata más tupida, cobertura de
árbol +2,64–7,01 %, ahorro 16,8 %; **no cumple identidad IoU .99/±1 %**, cambia
distribución interna. Horneado repetido aún no probado; aceptación de cruzadas
pendiente y sin cambio de receta/predeterminados. [Informe](../docs/evidence/roble-pintado/cruzadas-01/informe.md).

## Tres láminas aprobadas e integradas (2026-10-26)

El usuario solicita «ok implementalo con 3 laminas»: se adopta la variante de
tres del ensayo, con su aproximación de forma, atlas y madera. [Aceptación](../docs/evidence/roble-pintado/implementacion-01/user-acceptance.json).
Nueva receta `roble_copa_ancha@2.1.0`, contrato 1.4, componente
`oak-painted-crossed@0.1.0`, recursos 0.3.0 (atlas/plantillas) y pintura/corteza
0.2.0. Catálogo, CLI, resolución, ejecución y evaluación integrados, sin depender
de estudios previos para generar. Se conservan históricos y alias predeterminados.

Cuatro casos: piloto/joven/adulto/viejo 7836/3996/6812/7780 tris, 264 grupos/792
láminas y dos materiales; mismas ocho plantillas fijas. Piloto coincide con ensayo
aprobado en posiciones/UV y normales a seis decimales; repetición GLB exacta.
139 pruebas, regresiones pino/columnar exactas, rehorneado RGBA idéntico y 144
capturas Godot, revisadas en cinco láminas. Se verifica altura sobre madera para
no confundir márgenes transparentes con altura nominal; regla histórica intacta.
[Informe y reproducción](../docs/evidence/roble-pintado/implementacion-01/informe.md).
No se atribuye aprobación artística del usuario a los controles ni garantía
general de rangos; perfiles experimentales. Sin benchmark ni fases adicionales.
