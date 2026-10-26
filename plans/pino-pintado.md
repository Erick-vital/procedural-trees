# Pino pintado: dirección artística, muestra e integración

Fecha: 2026-10-25. Estado: **PP1–PP4 cerradas; pino completo 2.3.0 aprobado por el usuario**.
Solicitud: desarrollar las prioridades 1–4 acordadas con el usuario.
Marco: [blueprints](sistema-blueprints.md).
Base técnica: [pino 1.1.0](blueprint-pino.md).

## Objetivo y cambio de alcance

Crear una alternativa de pino estilizado con pintura de corteza y follaje,
mayor riqueza visual y menor cantidad de triángulos. El cambio de representación
artística es deliberado: no se exige reproducir exactamente la apariencia actual.
Se conserva la identidad estructural del pino: eje dominante, copa cónica,
huecos, ramas desfasadas e inclinaciones variadas.

El usuario plantea resolver pintura y reducción geométrica conjuntamente.
Este plan sustituye, para este experimento, la restricción anterior de conservar
acículas geométricas sin texturas. Las recetas históricas y los robles aprobados
siguen siendo referencias conservadas, sin modificación de sus resultados.
La aprobación artística del pino 1.1.0 continúa pendiente; autorizar esta
dirección no equivale a aceptar una muestra o un árbol todavía inexistentes.

## Alcance y exclusiones

1. Definir dirección artística y referencias.
2. Crear una rama completa como muestra de madera y follaje.
3. Resolver volumen, iluminación, transparencia y exportación en Godot.
4. Integrar la representación elegida en un pino procedural completo.

No incluye el estudio de rendimiento del punto 5, optimización general de madera
del punto 6, adaptación a roble del punto 7 ni LOD del punto 8. Tampoco bosque,
viento, nuevas edades, nuevas alturas ni fases F4–F6 de IA. Registrar conteos,
materiales y tamaños de textura forma parte del control técnico de este plan;
no constituye un benchmark ni demuestra una mejora de rendimiento.

## Referencia reproducible y propuesta técnica

- Base: `pino_conico` 1.1.0 y estructura `pine-whorls@0.2.0`, 12 m.
- Entradas: `presets/blueprints/pino-v2/` y
  `configs/verification/pine-v2.json`; piloto 5100/97 y controles
  5101/98, 5102/99 y 5103/100, sin ajustes individuales.
- Referencia: 11924 triángulos, 6140 de madera y 5784 de acículas.
  [Informe y evidencia](../docs/evidence/blueprints/pino-revision/informe.md).
- Conservar geometría de tronco y ramas principales inicialmente; añadir UV
  y pintura. Sustituir las ramillas secundarias con sus acículas por pequeñas
  mallas texturizadas dobladas o cruzadas, ancladas a los recorridos existentes.
- Resolver explícitamente las acículas del eje y ramas principales: pueden
  conservarse y recibir el nuevo material o sustituirse por grupos equivalentes.
  No dejarlas con un estilo residual incoherente ni duplicar follaje al integrar.
- Una textura por hoja no es el objetivo. La unidad de representación es la
  ramilla con su follaje, compartiendo atlas y materiales entre grupos.
- Combinar pintura con relieve geométrico; las láminas no siguen la cámara.
  Normales, reversos y orientación deben evaluarse como parte de la apariencia.

El cálculo preliminar de 8–12 triángulos por ramilla secundaria daría unos
5012–5780 triángulos por árbol, manteniendo el resto. Es una hipótesis de
presupuesto, no un compromiso de calidad ni un resultado verificado.

## PP1 — Dirección artística

Preparar una selección breve de referencias con autor, enlace y procedencia.
Las imágenes de referencia orientan el estilo; no se incorporan como texturas
sin derechos de uso. Proponer dos direcciones acotadas de pintura y recomendar
una para la muestra, con paleta común de madera y follaje.

Definir antes de producir el atlas:

- Grado de estilización, contraste, detalle y tamaño aparente de acículas.
- Corteza con tonos, nudos y marcas que acompañen el crecimiento; evitar
  patrones repetidos muy evidentes y sombras direccionales pintadas fuertes.
- Variación entre brotes, caras iluminadas y zonas interiores sin simular
  iluminación fija incompatible con la luz del motor.
- Vistas de evaluación: rama cercana y árbol completo; fijar cámaras,
  resolución, encuadre y distancia en una configuración reproducible.

Entregable: ficha artística y comparación visual de las dos propuestas.
Criterio de salida: dirección seleccionada y criterios observables para juzgar
color, lectura de la madera, agrupación y profundidad del follaje. Distinguir
selección del agente de aceptación artística explícita del usuario.

## PP2 — Rama completa de muestra

Seleccionar una rama primaria del piloto mediante identificador estable y
registrarlo antes de comparar alternativas. Usar la misma rama y semillas
en todas las variantes, incluyendo referencia original.

Crear una muestra con madera pintada y varios grupos de acículas. Comparar
dos construcciones pequeñas: láminas dobladas y láminas cruzadas. Compartir
la misma pintura inicial para distinguir el efecto de la geometría.

Partir de proyecciones de las ramillas propias si ayudan a preservar estructura,
y retocar pintura y silueta. Incluir al menos tres variantes de ramilla en el
atlas para evitar una repetición obvia. Ajustar el contorno geométrico para no
cubrir grandes áreas transparentes; más triángulos pueden ser preferibles a
rectángulos con demasiado espacio vacío.

Presupuesto inicial: atlas de follaje y textura de corteza de hasta 2048×2048
cada uno, máximo tres materiales por árbol. Registrar mapas adicionales,
resoluciones, canales y tamaño; cualquier ampliación debe justificarse antes
de integrarla. Conservar fuentes editables, texturas finales y procedencia.

Entregable: rama original y dos alternativas exportables, texturas y ficha
de conteos. Criterio de salida: muestra coherente de madera/follaje, anclajes
sin desconexiones visibles y potencial de reducción medido sobre la muestra.

## PP3 — Apariencia y materiales en Godot

Reutilizar el entorno de revisión real de Godot y registrar versión, renderizador
y ajustes. Empezar con Alpha Scissor y evaluar antialiasing de los bordes;
comparar otra modalidad solo si existe un defecto concreto que resolver.
Configurar reversos, normales, rugosidad y sombras de forma explícita.

Evaluar rama y alternativas con cámaras comunes: frente, perfil, perspectiva,
arriba, abajo y de canto; incluir giro para detectar desapariciones y cambios
bruscos. Probar luz frontal, lateral y contraluz con exposiciones registradas,
y fondos claro/oscuro. Revisar cerca y a la distancia de árbol completo.

Comprobar silueta, profundidad, uniones, repetición de pintura, costuras UV,
reversos, sombras y estabilidad de los bordes al alejarse. Revisar filtrado y
mipmaps para detectar pérdida de acículas, halos o parpadeo. Comprobar que GLB
reimportado conserva UV, texturas, recorte alfa y materiales esperados.

Entregable: galería comparativa y decisión de representación/materiales con
defectos pendientes explícitos. Criterio de salida: ninguna vista prevista
pierde de forma evidente el volumen del grupo ni presenta fallos técnicos
de material; revisión visual real realizada y muestra lista para elección
artística. No presentar una comprobación sin interfaz como validación visual.
Integrar la variante elegida; si el usuario no la ha revisado, conservar su
condición de propuesta provisional y no declarar aprobación.

## PP4 — Integración en un pino completo

Separar recorridos y anclajes, representación de ramillas, materiales/pintura,
adaptador Blender y evaluación Godot. Reutilizar el ejecutor y los contratos
comunes, ampliando solo lo necesario para recursos texturizados y estrategias
compatibles. No forzar la nueva representación a fingir contactos por acícula:
validar anclajes, límites y cobertura de los grupos que realmente se exportan.

Registrar receta y componentes nuevos con versiones explícitas; determinar
sus identificadores al definir el contrato. Conservar 1.0.0 y 1.1.0 ejecutables.
Registrar semilla para selección de variantes del atlas sin modificar la semilla
ni los recorridos estructurales; separar variación de pintura y distribución.
Registrar hashes de texturas, atlas, parámetros y versiones en el manifiesto;
la repetición debe usar esos mismos recursos y no regenerar pintura libremente.

Generar piloto y tres controles con parámetros comunes. Repetir piloto con
entradas y recursos congelados y comprobar resultados deterministas. El piloto
es el caso de trabajo; los controles comprueban generalización de la receta.
Los cuatro ya son conocidos y no se presentan como casos reservados inéditos.

Validación técnica: geometría finita, sin triángulos degenerados, UV válidas,
texturas presentes y acotadas, altura de 12 m, anclajes consistentes, sin follaje
duplicado y máximo tres materiales. Conservar límites de generación ≤120 s y
subprocesos de comprobación/captura ≤180 s, sin reintentos ilimitados.

El objetivo inicial es aproximadamente 6000 triángulos; la condición de reducción
es menos de 11924 en cada caso, con resultado visual revisable. Si no se alcanza
el objetivo inicial, registrar el coste y la razón artística, sin ocultarlo ni
reducir calidad automáticamente para cumplirlo. El techo contractual de 12500
no sustituye a la condición de reducción de este experimento.

Actualizar verificadores para aceptar texturas/recorte solo en la ruta nueva,
conservando comprobaciones históricas de materiales opacos sin textura. Probar
contratos, presupuestos, recursos ausentes, semillas y repetición. Comprobar
regresión exacta del pino 1.1.0 y de referencias roble B0 y columnar B4 si se
modifica infraestructura compartida.

Entregable: receta ejecutable, cuatro GLB autocontenidos con texturas embebidas,
galería Godot original/nuevo, manifiestos y guía de reproducción. Revisar los
cuatro árboles desde varias vistas y al menos dos distancias con luz común;
incluir una vista de madera para distinguir estructura de pintura/follaje.
Criterio de salida: nueva representación integrada, reducción comprobada,
exportación y repetición verificadas; aceptación artística registrada aparte.
Si un criterio falla, cerrar el intento con resultado parcial y defecto concreto.

## Evidencia y cierre

Rutas previstas, todavía no creadas: `artifacts/pino-pintado/` para resultados
regenerables y `docs/evidence/pino-pintado/` para ficha artística, decisiones,
informe y selección de imágenes útiles. Las texturas de producción y sus fuentes
editables son recursos necesarios, no simples capturas; acordar su ubicación
versionada al implementar PP2 y referenciarlas desde recetas/manifiestos.

Actualizar `ESTADO.md` al cerrar avances relevantes y distinguir planificado,
implementado, verificado y aceptado. La solicitud inicial autorizó planificación;
el usuario solicitó después comenzar PP1. No se inician otras etapas por rutina.

## Resultado PP1, 2026-10-25

[Ficha artística y comparación](../docs/evidence/pino-pintado/pp1/direccion-artistica.md):
dos conceptos generados con la captura propia como referencia, paletas, fuentes
atribuidas, criterios observables y configuración de cámaras para evaluación
futura. El agente selecciona **A — Pincelada amplia** como dirección provisional;
aceptación artística del usuario pendiente. Estrechar algunas puntas y suavizar
claros direccionales de corteza al producir la muestra. Imágenes inspeccionadas;
no se han creado texturas de producción, atlas ni GLB. Sin validación Godot nueva
ni reducción de triángulos demostrada. PP2–PP4 permanecen sin iniciar.

## Resultado PP2, 2026-10-25

El usuario elige A y autoriza la rama, estrechando puntas:
[selección](../docs/evidence/pino-pintado/pp2/user-selection.json).
[Informe de muestra](../docs/evidence/pino-pintado/pp2/informe.md): rama
`pine:p:2:0`, piloto 5100/97, atlas de tres ramillas y corteza versionados,
original/dobladas/cruzadas exportables. 244→104 triángulos por rama, dos
materiales, 99 pruebas y 21 renders Blender revisados; repetición de tres GLB
idéntica. Cruzadas conserva más presencia en perfil/canto; preferencia del agente,
aceptación de la muestra pendiente. Ambas alternativas tienen menos volumen
que el original. No hay validación Godot ni integración; PP3–PP4 no iniciadas.

Ubicación acordada por implementación PP2: `assets/pino-pintado/v0.1.0/`,
PNG fuente/final con prompts, procedencia y hashes. Resultados regenerables en
`artifacts/pino-pintado/pp2-sample-02/`; `.blend` con UV/nodos editables y PNG
empaquetados. No existen capas de pintura anteriores a los PNG generados.

## Resultado PP3, 2026-10-25

El usuario elige cruzadas y autoriza revisión Godot:
[selección](../docs/evidence/pino-pintado/pp3/user-selection.json).
[Informe PP3](../docs/evidence/pino-pintado/pp3/informe.md): 282 capturas reales
Godot 4.7.2 Compatibility, 101 pruebas y auditoría de importación/capturas.
Se conserva geometría y PNG de PP2; material propuesto Alpha Scissor .5, doble
cara, rugosidad .95, mipmaps anisotrópicos, sombras de ambas caras y MSAA 4×.
El giro revisado mantiene los grupos. Cobertura alfa ensayada sin diferencias
de píxeles en este entorno; no se atribuye mejora. Persisten dentado fino y
pérdida de agujas lejanas. Resultado del motor disponible para revisión artística.
PP4 no iniciada. Decisión de material en
`configs/inspection/pine-painted-pp3-v1.json`; galería y secuencias en
`artifacts/pino-pintado/pp3-review-02/`.


## Resultado PP4, 2026-10-25

El usuario autoriza integrar las cruzadas y los materiales revisados en piloto
y tres controles. Se registra `pino_conico` **2.0.0**, contrato 1.2,
`pine-path-groups@0.1.0` y `pine-painted-crossed@0.1.0`; conserva la estructura
0.2.0 y todas sus rutas. Tronco/primarias intactos, secundarias/acículas
sustituidas por 241 grupos cruzados, incluido el ápice. Atlas/corteza 0.1.0
congelados; semilla de pintura independiente 2718. Sin retoques por caso.

**11924 → 5192 triángulos por caso (−56,46 %)**, 12 m, dos materiales,
cuatro GLB autocontenidos y escenas Godot reutilizables. Repetición exacta,
referencias 1.1.0/roble B0/columnar B4 idénticas, reimportación y auditoría de
anclajes/UV/PNG. 110 pruebas; 108 capturas reales Godot con cámaras y luz comunes,
seis vistas y tres distancias por referencia/nuevo/madera. Revisión visual del
agente realizada; copa bastante más abierta y ápice fino, dentado residual y
pérdida de detalle a distancia. GLB más grandes por PNG; sin benchmark.
[Informe y reproducción PP4](../docs/evidence/pino-pintado/pp4/informe.md).
Aceptación artística pendiente. No se inician LOD, optimización de madera,
roble, benchmark ni fases de IA. La receta inicial solo expone los cuatro casos
de 12 m, sin overrides; los contratos/recetas históricos se conservan.


## Revisión PP4 de volumen, 2026-10-25

El usuario considera demasiado rala la copa 2.0.0 y solicita más volumen,
sobre todo arriba, manteniendo cruzadas y el mismo ajuste en los cuatro casos.
Esta corrección permanece en PP4: **2.1.0**, distribución/representación **0.2.0**,
ensanchamiento y longitud mínima crecientes con altura, segunda cruzada por
secundaria y tres grupos del eje. Madera, atlas y materiales conservados;
435 grupos, **7520 triángulos**, 12 m/dos materiales en cada caso. Se supera
el objetivo inicial aproximado de 6000 por la petición de volumen; conserva
reducción del 36,93 % frente al pino geométrico. Sin ajustes individuales.
113 pruebas, 43 comprobaciones, repetición y regresiones 2.0.0/B0/B4 exactas,
108 capturas Godot reales revisadas. [Informe y reproducción](../docs/evidence/pino-pintado/pp4-volumen/informe.md).
2.0.0 se conserva como referencia técnica con la objeción artística del usuario;
aprobación artística de 2.1.0 pendiente. No amplía el alcance a otras fases.

## Ampliación solicitada: optimización de madera y ajuste leve de copa

El usuario solicita optimizar tronco/primarias en los cuatro casos conservando
el follaje durante esa operación, y reducir después ligeramente la plenitud de
la copa. Se autoriza así la parte de optimización de madera antes excluida,
limitada al pino pintado y estas cuatro semillas. Recorridos/anclajes separados
de la malla simplificada; no desplazar follaje por simplificar madera.
Usar tolerancia geométrica explícita y comparación visual de madera/copa.
El ajuste leve de copa debe ser una regla común, separada y registrable.
Conservar 2.1.0 ejecutable. Sin LOD, benchmark, bosque ni adaptación a roble.


Resultado de la ampliación: **2.2.0**, representación 0.3.0 y optimizador de
anillos 0.1.0, tolerancia 5 mm. Madera 2300→1908–1944 triángulos; total
7128–7164, manteniendo 435 grupos. Después de simplificar madera se aplica
longitud .98/anchura .94 a cada grupo, sin mover anclajes ni cambiar el atlas.
Cobertura proyectada 4,1–4,7 % menor, ajuste leve común. 116 pruebas,
51 comprobaciones, regresiones 2.1.0/B0/B4 exactas y 144 capturas reales revisadas.
[Informe y reproducción](../docs/evidence/pino-pintado/pp4-madera/informe.md).
Aprobación artística pendiente. Las exclusiones originales de madera se amplían
solo por esta solicitud; LOD, benchmark, roble y bosque siguen fuera.

## Ampliación solicitada: reducir tris de las cruzadas

El usuario solicita optimizar láminas sin cambiar silueta/volumen de 2.2.0,
con regla común para piloto/tres controles. Durante la ejecución autoriza además
adelgazar levemente la copa, aproximadamente un 10 %. Se separan ambas operaciones:
soporte pentagonal sobre transparencia, 12→6 tris por cruzada, y anchura sqrt(.9)
con longitud y anclajes fijos (−10 % de envolvente por grupo, no de la unión física).
Receta **2.3.0**, representación **0.4.0**; madera, guías y PNG de 2.2.0 idénticos.
435 grupos/2610 tris de follaje; totales 4518–4554. 119 pruebas, 51 comprobaciones,
repetición/regresiones exactas y 144 capturas reales. Referencia aislada con igual
anchura: diferencia de máscara ≤0,151 % del área proyectada en 36 pares;
conservación perceptual revisada, sin identidad absoluta de píxeles.
[Informe y reproducción](../docs/evidence/pino-pintado/pp4-laminas/informe.md).
Aceptación artística pendiente; sin benchmark ni LOD.

## Aprobación del resultado 2.3.0, 2026-10-25

El usuario aprueba esta versión y solicita commit. Se cierra PP1–PP4 para el
piloto y tres controles de 12 m, sin extender la aceptación a otras semillas,
alturas/edades ni iniciar fases adicionales.
[Aceptación y hashes](../docs/evidence/pino-pintado/pp4-laminas/user-acceptance.json).

## Ampliación solicitada: prueba de rendimiento 2.3.0 frente a 1.1.0

El usuario solicita ahora el benchmark antes excluido. Alcance: Godot real con
GPU, mismo equipo/renderizador, 1920×1080, materiales PP3, MSAA 4× y sombras;
1, 128 y 512 instancias estáticas, mismas posiciones/cámaras por pareja, cuatro
mediciones por versión con orden alternado ABBA/BAAB y calentamiento previo.
Comparar tiempo por cuadro/FPS, percentiles, CPU/GPU de render cuando disponibles,
draw calls/primitivas y contexto de hardware. Desactivar VSync, límite de FPS y
LOD automático para comparar la geometría completa. No modificar assets ni recetas.
Las cargas múltiples son escenas sintéticas de estrés, no un sistema de bosque.
La comparación incluye el estrechamiento de copa de 2.3.0: no atribuir el resultado
exclusivamente al recuento de tris. Repetición independiente es la unidad de
comparación; registrar dispersión y no confundir FPS sin límite con fluidez
visible o rendimiento garantizado en otros equipos.

Corrección explícita del usuario: la referencia principal es **1.1.0 geométrica,
anterior a texturas y optimización**, no 2.2.0. El ensayo iniciado con 2.2.0
solo completó 1 y 128 árboles; 512 fue interrumpido y no es resultado válido.
Se conserva como diagnóstico parcial regenerable. La comparación solicitada
se ejecutará de nuevo con 1.1.0 y 2.3.0 en las mismas condiciones; se conservan
los materiales propios de cada asset (opacos sin textura frente a pintura/recorte).

Resultado: comparación **1.1.0/2.3.0 implementada y verificada**. 24 mediciones,
cuatro repeticiones por versión/carga, RTX 5060/1080p/MSAA4/sombras, sin cap/LOD:
128 árboles 353→589 FPS y 512 árboles 126→228 FPS; tiempo por cuadro −40,0/−44,9 %,
consistente en las cuatro parejas. Un árbol: sin ganancia útil. Tres pruebas de
análisis, auditoría y seis capturas revisadas. Mide el rediseño completo, no aísla
solo tris; sin cambios en assets. [Informe y límites](../docs/evidence/pino-pintado/rendimiento-v11/informe.md).
