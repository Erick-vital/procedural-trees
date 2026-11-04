# Arquitectura de roble de crecimiento libre — O1

Autorizado el 2026-11-03 por petición de mejorar el generador tomando *Quercus
robur* como referencia. Ampliación expresa de F5/R4: ahora se permite cambiar
tronco, primarias y volumen de copa; no se exige congelar el follaje anterior.
R4/recetas/nodos siguen disponibles. No se inicia F6, viento, LOD o simulación
biológica completa. La madurez afecta reglas de crecimiento y no solo tamaño.

## Diagnóstico del código existente

`branch_structure.generate_structure`: nacimientos `.33+.53*step`, sectores
`2*pi/n`, curvas con la misma parábola y tres secundarias en `.38/.61/.84`.
El cambio espacial posterior solo gira secundarias alrededor de Z. R4 conserva
tronco/primarias y `branch_sample.make_network` divide destinos de follaje en
cubos longitudinales con tres anclajes fijos, fracción .48–.60 hacia centroides
y partición binaria por eje cartesiano. Es útil para conservar la copa aprobada,
pero no constituye una arquitectura de crecimiento de cuatro órdenes. Q2 ajusta
solo Z y puede aplanar la lectura; no reutilizar esa normalización anisótropa.

## Etapas y contrato

1. Tronco con base ensanchada y primarias escalonadas; eje central decreciente
   con madurez, ramas bajas extensas y líderes superiores competidores.
2. Secundarias, terciarias y terminales con frecuencias, longitudes, ángulos y
   resoluciones distintas. Continuaciones y laterales desiguales/escalonadas.
3. Vigor regional suave, exposición y competencia por espacio; curvas correladas,
   candidatos de dirección deterministas, sin repartir radios uniformes.
4. Engrosamiento por demanda distal, transición de radios suave, anillos con
   transporte de marco y nacimientos embebidos. Auditar continuidad y contactos;
   indicar las uniones por solapamiento, sin prometer malla soldada.
5. Presets versionados joven/maduro/centenario, parámetros documentados y CLI
   explícito. Edad estructural normalizada; “centenario” es referencia de etapa,
   no simulación ni datación/calibración biológica. Vigor separado de madurez.

Separar contrato, esqueleto, malla, ejecución, auditoría y adaptador Blender.
Semillas estables por rama y stream. Entradas estrictas/acotadas, hasta ocho
primarias, tres secundarias por primaria, dos terciarias y dos terminales.
Cota máxima de madera por resoluciones 5156 tris; reservar 1584 para follaje
posterior (6740 total). La petición actual valida madera desnuda: no integrar
follaje nuevo ni declarar su arte aprobado. Corteza pintada existente compartida.
Generación ≤120 s, procesos de revisión ≤180 s; salidas con hashes/procedencia.

## Validación fijada antes de generar

Mismo preset **maduro**, semillas **3100, 3101, 3102, 3103, 3104**. Comparación con
R4 `viejo` con las mismas semillas/copa17/pintura2718: alturas y encuadres comunes
por pareja, frente/lado/arriba/perspectiva; normalizar la referencia uniformemente
para presentación si difiere la altura nominal, registrarlo sin alterar assets.
Ablación de tronco/primarias de la candidata en las mismas cámaras: distinguir
mejor arquitectura de más ramillas. Controles joven y centenario con semilla3100
y parámetros comunes de la familia; mostrar también escala normalizada por
altura para ver siluetas, además de sus dimensiones reales. Repetición desde
CLI, cambio de orden de ejecución, regresión R4 histórica y pruebas de límites.

Revisar imágenes reales Godot de los cinco individuos; registrar silueta,
profundidad vertical, jerarquía, asimetría, uniones y variación. Ningún aumento
de ramas, suma de métricas o aprobado técnico sustituye ese juicio. Conservar
intentos fallidos y no declarar reconocimiento botánico demostrado universalmente.

## Referencias de forma

- [JRC, European Atlas: Quercus robur](https://forest.jrc.ec.europa.eu/en/european-atlas/qr-trees/pedunculate-oak/):
  ejemplar aislado, tronco grande, copa expandida y primarias horizontales.
- [Forest Research](https://www.forestresearch.gov.uk/tools-and-resources/tree-species-database/131559-pedunculate-oak-pok-2/):
  baja dominancia apical y forma arbustiva al crecer libre.
- [RHS](https://www.rhs.org.uk/plants/14294/quercus-robur/details): copa amplia y
  ramas robustas. Los coeficientes del algoritmo son decisiones gráficas
  simplificadas, no medidas botánicas tomadas de estas fuentes.


## Resultado O1

Implementado/verificado en `oak-growth-0.1.0`; arte pendiente. [Informe](../docs/evidence/oak-growth/o1/informe.md),
[uso y controles](../docs/uso-arquitectura-roble.md). CLI `generate-oak-growth`,
cuatro órdenes, presets joven/maduro/centenario y factor de madurez continuo.
Las cinco etapas del plan se implementaron como módulos/pases separados; la
validación se limita a madera descubierta, sin promover recetas históricas.

Lote `artifacts/oak-growth/validacion-03`: cinco maduros3100–3104, mismo preset,
3041/3648/2777/3475/3429 tris; joven3100 2358, centenario3100 3634. Cota analítica
5156 de madera +1584 reservados para follaje =6740. Radios por demanda,
transporte de anillos y raíces embebidas; piezas solapadas, no malla soldada.
Generación0.921–1.066 s, 249 pruebas, 51 checks, estructura y dos GLB repetidos
idénticos; regresión de cinco GLB R4 exacta. 88 capturas Godot; 72 revisadas en
seis láminas, incluyendo cinco seeds/cuatro vistas y etapas a altura normalizada.

Desarrollo sobre seed3100: dos fallos de unión guardados, correcciones de taper,
cobertura angular, curvas y crecimiento lateral de secundarios; ensayos y lotes
previos conservados. La comparación final añade los otros cuatro individuos sin
retoques por semilla. La competencia usa exposición/ocupación aproximadas, no
luz física; ablación algorítmica registrada sin afirmar mejora universal de
colisiones. Las referencias R4 se presentan con escala uniforme registrada.

La revisión identifica mayor sinuosidad y jerarquía, diferencias de porte por
madurez, pero también brazos largos y regiones abiertas. No certificar por
métricas la copa redondeada ni reconocimiento inequívoco como especie: queda
valoración artística del usuario antes de integrar nuevo follaje o promoverla.

## O2 — equilibrar copa y contener brazos, autorizado 2026-11-03

Petición: corregir brazos demasiado largos, equilibrar copa, conservar huecos y
madurez; nueva comparación desnuda con las mismas semillas3100–3104. Alternativa
versionada0.2.0; conservar0.1.0 y sus presets/GLB. Semillas de crecimiento mantienen
el namespace0.1.0 para comparar reglas con la misma variación inicial.

Diagnóstico: continuación por fracciones acumuladas y premio exterior positivo
en todos los órdenes; penalización radial anterior demasiado débil, sin freno
de longitud. Aplicar presupuesto longitudinal por brazo, desaceleración gradual
en una envolvente irregular dependiente de altura/madurez y elección de planos
que penalice prolongaciones fuera de esa envolvente. No proyectar vértices sobre
una esfera, distribuir ramas equidistantes, rellenar todos los vacíos ni aumentar
frecuencias por equilibrar. Mantener cuatro órdenes y recalcular radios/uniones.

Antes/después O1/O2 de las cinco seeds maduras; cámaras/luz comunes, frontal,
lateral, superior y perspectiva, incluyendo primarias solas. Controles joven y
centenario3100 y comparación normalizada por altura para conservar diferencias
de porte. Registrar extensión horizontal, sesgo del centro de copa, desigualdad
entre sectores y huecos angulares sin confundirlos con juicio artístico. Cota
geométrica5156+1584reservados=6740; repetir GLB y regresión0.1.0. Conservar fallos.


### Resultado O2

`oak-growth-0.2.0` implementado/verificado. [Informe](../docs/evidence/oak-growth/o2/informe.md).
Cinco maduros3100–3104, cámaras comunes sin hojas: alcance horizontal extremo
−35.87–47.69 %, centro de copa menos desplazado en cinco casos. No se fuerzan
sectores iguales: variación sectorial mejora en4/5, aumenta en3100 por conservar
una región abierta. Los huecos y las distintas siluetas de edad se revisaron en
imágenes, sin deducir aceptación artística de las métricas.

Maduros **3054/3549/2824/3462/3429** tris; joven/centenario3100 **2332/3621**.
Cota5156+1584reservados=6740. Generación1.001–1.108 s,257 pruebas,78 checks;
14 GLB O1 históricos exactos y estructura/dos GLB O2 repetidos idénticos.
124 capturas Godot,108 inspeccionadas en13 láminas. Lote
`artifacts/oak-growth/o2-validacion-01/index.html`. Presets0.1.0 conservados;
0.2.0 añade freno de extensión y envolvente suave, mantiene namespace aleatorio
0.1.0 para comparar reglas. Cuatro órdenes, pintura y parámetros previos intactos.
Arte pendiente; no se integra follaje ni se amplía a F6 por este cierre.

## O3 — ramificación y porte libre, autorizado 2026-11-03

El usuario pide reducir aspecto podado (A), separar brazos estructurales de
secundarias ascendentes (B) y representar un centenario extendido e irregular
(C). A tiene aumento máximo **700 triángulos**; no es permiso para superar6999
con follaje. Alternativa explícita0.3.0, conservando O1/O2. Sin integrar hojas.

B/C conservan cantidades y resoluciones de la topología O2 de la misma entrada
(altura, madurez, semilla, ablación y competencia). Se recalculan trayectorias y
radios; los brazos reciben menor tropismo y descenso persistente por peso;
secundarias buscan altura. Madurez alta reduce eje y verticalidad superior,
extiende brazos bajos y aumenta sinuosidad; es un arquetipo gráfico, no una
regla sobre todos los robles viejos. A añade abanicos cortos terciarios con dos
terminales, **60 tris por grupo**, con cupo global min(700,5415−maderaO2).
No se subdividen los tubos existentes. Máximo añadido660 por grupos enteros;
reserva futura1584, cota completa6999. Con pocos padres se añade menos.

Verificar mismos cinco maduros3100–3104, cinco centenarios3100–3104 y joven3100;
O2/O3 sin hojas y primarias solas con cámaras/luz comunes; edades a altura
normalizada. Medir triángulos de GLB, uniones, tendencia de primarias y extensión
relativa; repetir CLI y verificar regresión O2 con evidencia histórica. Revisar
imágenes Godot antes de describir el resultado visual. Aceptación del usuario
pendiente; no promover recetas anteriores ni iniciar follaje/F6.

### Resultado O3

0.3.0 implementado y verificado; aceptación artística pendiente. Once parejas
O2/O3, cinco maduros y cinco centenarios3100–3104 más joven3100: +660 tris en
cada caso, máximo de madera4867. Cota de contrato5415 + reserva1584 =6999;
prueba densa obliga a reducir relleno. 263 pruebas,124 checks,14 GLB históricos
O2 exactos y repetición CLI de estructura/dos GLB O3 idéntica. 188 capturas Godot,
132 inspeccionadas; mejora visual moderada de densidad y porte centenario más
extendido. Fallo de encaje en ensayo02 corregido por distancia a la superficie
del padre; lote03 completo pasa. [Informe y límites](../docs/evidence/oak-growth/o3/informe.md).
No se integra follaje ni se promueven recetas históricas.

## O4 — desarrollo periférico y hábitos por brazo

Continuación autorizada por la revisión del usuario: O3 progresa pero no está
resuelta ni aprobada. Reducir congestión central, repartir secundarios a lo
largo de los brazos y tejer la periferia; ascenso, peso y torsión distintos por
brazo. Preservar identidad por etapa, huecos y asimetría de alcance en centenarios.

Alternativa 0.4.0, O1/O2/O3 conservadas. Mantener el cupo original de A:
**máximo +700 respecto a O2, sin otro incremento acumulado sobre O3**, y 6999
con reserva futura 1584. Redistribuir los 660 tris de O3: priorizar secundarios
ramificados intermedios en primarias (100 tris por unidad), después terciarias
periféricas (60 tris); reducir trabajo si falta cupo. Cantidades/resoluciones de
la base O2 conservadas, cambiando nacimientos, planos, recorridos y demanda.

Misma comparación: maduros/centenarios 3100–3104, joven3100, cuatro vistas y
primarias aisladas O3/O4, edades normalizadas. Evaluar longitud de ejes internos
frente a periféricos, ocupación espacial, tendencias por brazo y distribución
sectorial sin equiparar métricas a naturalidad. Repetir CLI, auditar GLB/uniones,
regresión O3 histórica, pruebas de límites y revisión visual Godot antes del
cierre. No integrar follaje ni promover recetas por esta iteración.

### Resultado O4

0.4.0 implementado/verificado. Diez maduros/centenarios conservan triángulos O3
(+660 frente a O2), joven3100 reduce40 (+620); reserva1584 y cota6999 conservadas.
269 pruebas y 154 checks,22 GLB O3 históricos exactos, estructura y dos GLB O4
repetidos idénticos. 188 capturas Godot,132 inspeccionadas. Núcleo de órdenes≥2
menos desarrollado en10/10; periferia aumenta en9/10. Maduro3100 pierde longitud
periférica: excepción registrada, sin retoque por semilla. Mayor reparto a lo
largo de brazos y respuestas por brazo distintas, pero lectura esquelética aún
parcial y aceptación artística pendiente. [Informe](../docs/evidence/oak-growth/o4/informe.md).
No se promueve la receta ni se integra follaje por este cierre.

## O5 — llenar huecos periféricos sin aumentar geometría

Petición vigente: seguir refinando la periferia, especialmente maduro3100,
con reglas generales, centro despejado y mismo presupuesto de triángulos.
Alternativa 0.5.0; conservar O4 y referencias anteriores. Sin follaje nuevo.

Proteger curvas y diámetros de tronco/primarias de O4 y conservar exactamente
su topología completa. Reubicar y orientar subárboles secundarios existentes
sobre sus primarias, con candidatos acotados de nacimiento, giro y longitud.
Priorizar espacio exterior sin ocupar y conservar altura y extensión global;
rechazar candidatos que aumenten longitud/nacimientos internos o reduzcan
longitud/celdas periféricas. Son reglas geométricas para todas las entradas,
sin condiciones por semilla ni edición de ejemplares. Recalcular secundarios
y encajes; registrar candidatos y aceptación determinista.

Comparar O4/O5 en los once casos previos: cinco maduros y cinco centenarios
3100–3104, joven3100; cuatro vistas, primarias aisladas y edades normalizadas.
Añadir semillas de control no usadas para desarrollo. Exigir mismos tris por
entrada, reserva1584 y máximo6999; no acumular otro cupo. Verificar uniones,
repetición CLI, regresión O4 y scaffold protegido. Revisar imágenes Godot y
registrar mejoras y límites sin equiparar ocupación de celdas a copa resuelta.

### Resultado O5

0.5.0 implementado/verificado: once casos conservan tris O4 exactamente; en los
diez adultos aumentan longitud/celdas exteriores y no crece actividad interna.
Maduro3100: periferia1.60→5.36H,31→97 celdas; núcleo1.83→1.44H,3714 tris.
275 pruebas,195 checks;22 GLB O4 históricos exactos, once scaffold idénticos
y repetición CLI O5 idéntica. Diez controles5000–5004 geométricos, sin nuevas
capturas/exportaciones, también cumplen presupuesto y protección regional.
188 capturas Godot,132 inspeccionadas; arte pendiente y sin prometer copa
completa por métricas. [Informe y límites](../docs/evidence/oak-growth/o5/informe.md).
No se integra follaje ni se promueve receta histórica.

### Valoración del usuario de O5

El 2026-11-03 expresa conformidad con el aspecto actual y deja posibles mejoras
para más adelante. O5 queda aceptada como referencia de madera desnuda, sin
aprobar follaje ni extender la validación a entradas no revisadas.
[Decisión](../docs/evidence/oak-growth/o5/user-acceptance.json).
Consulta posterior: valorar si las reglas de follaje se adaptan a O5 o requieren
otra estrategia. La consulta autoriza análisis, sin iniciar integración nueva.

## OF1 — rama O5 con follaje, autorizado 2026-11-03

El usuario autoriza preparar una rama de muestra con la pintura actual y nueva
distribución antes de integrar el árbol completo. Selección explícita: maduro
O5, semilla3100, primaria lateral inferior `p:0` con todos sus descendientes;
semillas de distribución17 y pintura2718. Madera y atlas conservados exactamente.
Sin integrar follaje completo ni promover recetas históricas por este ensayo.

Presupuesto desde la muestra: reparto de máximo264 grupos (tres láminas/seis
tris cada uno) entre primarias según longitud/vigor/exposición de sus ejes
terciarios/terminales elegibles. Solo materializar el cupo de la rama elegida;
libro de cupos completo para no gastar la reserva1584 en una sola rama. Cota de
familia madera5415 +1584 =6999. Sin conectores geométricos añadidos.

Distribuir grupos sobre ramificaciones reales, con desarrollo longitudinal y
variación por conjuntos, evitando primarias y núcleo. Atlas0.3.0 de follaje y
corteza0.2.0 intactos. Anclar raíz pintada de cada plantilla a superficie real
de madera y pasar las tres láminas por ella; registrar coordenadas/UV y contacto.
Distinguir contacto geométrico, alfa pintada y aceptación visual.

Separar contrato, planificación/distribución, representación, exportación y
revisión. Entradas estrictas, semillas explícitas y trabajo acotado. Exportar
muestra desnuda, muestra con follaje y follaje aislado; validar GLB, materiales,
UV/PNG, madera idéntica y contactos; repetir y verificar regresión O5. Revisar
Godot en varias orientaciones, fondos, distancias y sombras. Pintura reutilizada;
aceptación artística de la rama pendiente antes de cualquier árbol completo.

### Resultado OF1

Muestra `oak-foliage-sample-0.1.0` implementada/verificada: rama p:0 de maduro3100,
646 tris de madera idéntica O5 y64 grupos/192 láminas/384 tris de follaje:
**1030 tris, dos materiales**. Pintura y corteza históricas exactas. Cupo global
revisado216 grupos/1296 tris, proyección5010 para ese árbol; solo la rama tiene
follaje materializado. Sin nuevos conectores geométricos; anclajes a superficie
y alfa opaca verificados sobre GLB. 281 pruebas,32 checks, repetición de cuatro
GLB/layout/estructura idéntica, testigo O5 histórico exacto. Godot36 capturas,
23 inspeccionadas; agrupaciones compactas/cruces visibles en algunas vistas.
[Aceptación de rama pendiente](../docs/evidence/oak-foliage/of1/informe.md).
No se integra la copa completa hasta la revisión solicitada por el usuario.

## OF2 — cadenas de masas sobre la misma rama

Petición del usuario mediante texto adjunto: OF1 sigue pareciendo grupos pegados,
con puntas/nodos congestionados y un racimo inferior aislado. Comparar A terminal/
lateral, B continuidad media y C fragmentada sobre la misma rama, conservando
pintura y presupuesto. OF1 queda como ensayo revisado con cambios pendientes,
sin aceptación de rama ni integración de copa.

Congelar O5 maduro3100/p:0, semillas17/2718, madera646 tris, cupo64 grupos/384 tris
(1030 totales), atlas idénticos. Nuevos candidatos por segmentos, preferencia
terciarias/terminales vigorosas/secundarias exteriores y puentes intermedios;
excluir desarrollo inferior aislado mediante regla geométrica general.
Organizar candidatos en2–5 masas por brazo, con papeles terminal/lateral/puente,
cadenas relacionadas y huecos. Orientaciones coherentes arriba/afuera, grupos
más anchos y menos profundos. Misma secuencia de tamaños y plantillas en A/B/C
para comparar distribución/orientación sin variar pintura, área ni tris.

Contrato0.2.0 independiente; conservar OF1. Registrar masas, asignaciones,
descartes y semillas. Validar presupuesto, superficies/UV/alfa, madera intacta,
repetición y regresiones. Godot con cámaras/luz/escala comunes entre tres variantes,
fondos, distancias, sombras y follaje aislado. Comparar continuidad, huecos y
lectura de madera; métricas de máscara no sustituyen valoración artística.
Solo muestra madura; reglas por madurez son preparatorias, otras etapas y copa
completa sin certificar ni integrar en esta iteración.

### Resultado OF2

0.2.0 implementado/verificado: A/B/C sobre p:0 de maduro3100, tres/cuatro/cinco
masas lógicas. Cada una1030 tris/dos materiales/64 grupos; madera, atlas, tamaños
y secuencia de plantillas comunes. Candidato inferior aislado excluido por regla
geométrica. 287 pruebas,99 checks, doce GLB/layouts repetidos idénticos y O5/OF1
madera exacta. Godot68 capturas y20 máscaras;44+16 inspeccionadas. B enlaza mejor
el recorrido, A concentra extremos y C deja huecos mayores; preferencia del agente
por B sin aprobación del usuario. Persisten cruces y tarjetas de canto arriba.
[Informe y comparación](../docs/evidence/oak-foliage/of2/informe.md).
Muestra madura exclusivamente, sin integrar árbol completo ni promover receta.

## OF3 — copa madura B revisada, autorizada 2026-11-03

El usuario elige B y autoriza probarla en el maduro O5 3100 completo, conservando
pintura, centro despejado y presupuesto. Solicita tres mejoras: expansión lateral,
arriba/abajo del eje real; reparto entre bifurcaciones según vigor/exposición;
masas alargadas, anchas y pequeñas de enlace. Esta autorización sustituye la
restricción previa de solo rama para este piloto; otras edades y promoción de
recetas siguen fuera del alcance. La elección de B no aprueba la copa resultante.

OF3 independiente, conserva OF1/OF2: 216 grupos/1296 tris de follaje, madera O5
3714 intacta y 5010 tris completos, dos materiales. Mantener cupos por primaria;
repartir por subárbol secundario con longitud expuesta sublineal, vigor y exposición.
Masas vinculadas a bifurcaciones reales, orientaciones coherentes por masa pero
variadas entre masas; alternancia alrededor de ejes y tres proporciones. No añadir
madera ni mover contactos para rellenar volumen. Excluir toda lámina del cilindro
central de radio 0.30H, comprobando caras completas antes y después de exportar.
Intentos acotados; rechazar entradas sin candidatos, nunca aumentar presupuesto.

Comparar con B original aplicada al mismo árbol, misma cámara/luz/escala y pintura,
y comparar la rama p:0 original/revisada. Validar GLB, madera/atlas históricos,
contactos UV/alfa/superficies, topología, determinismo y presupuesto. Revisar Godot
frente/perfil/arriba/abajo/perspectivas, fondos, distancias y sombras; registrar
huecos, repetición y límites sin equiparar métricas a aceptación artística.

### Resultado OF3

0.3.0 implementado/verificado: maduro 3100 completo, 216 grupos y 5010 tris/dos
materiales; madera O5 y pintura exactas. Reparto p:0 secundarias 26/38/0 →25/26/13;
28 masas lógicas, proporciones anchas/alargadas/puentes y orientaciones variables.
Cilindro de radio 3.6 m sin follaje, caras completas auditadas sobre GLB.
293 pruebas, 48 checks, seis GLB/layout/estructura repetidos idénticos; testigos
O5 completo y OF2 B de rama exactos. 46 capturas Godot inspeccionadas. Copa aún
rala, algunas columnas y tarjetas de canto arriba: arte pendiente, sin promoción
ni edades adicionales. [Informe](../docs/evidence/oak-foliage/of3/informe.md).

## OF4 — llenado periférico con 5010 tris, autorizado 2026-11-03

El usuario considera OF3 demasiado rala y solicita mayor llenado periférico y
continuidad, con madera, pintura, centro despejado y 5010 tris intactos, sin
retoques por semilla. Revisar reglas generales en versión independiente 0.4.0;
conservar OF3 como comparación y registrar que requiere revisión artística.

Redistribuir 216 grupos hacia ramas menos cubiertas, suavizar el peso de las
primarias dominantes y desarrollar segmentos descendentes portantes: la altura
de una primaria no debe excluir un subárbol periférico vigoroso entero. Descartar
solo ramillas inferiores muy cortas, manteniendo contactos sobre madera real.
Ampliar alcance de masas anchas/alargadas y orientar parte hacia sus vecinas;
espaciado entre grupos de todo el brazo, no solo dentro de cada masa. Acotar
extensión cerca del cilindro central 0.30H, sin invadirlo ni mover anclajes.
Comparación OF3/OF4 con cámaras/luz/escala comunes, alfa, sombras y distancias;
repetición GLB, madera/atlas exactos y presupuesto completo fijo. Esta revisión
no promueve recetas ni amplía edades. Métricas de cobertura/continuidad 2D son
diagnósticos; comprobar apariencia en Godot antes de describir mejoras.

### Resultado OF4

0.4.0 implementado/verificado: 216 grupos y 5010 tris/dos materiales, pintura y
madera exactas. Reparto entre primarias menos concentrado, desarrollo de brazos
periféricos descendentes y espaciado global por brazo; masas más extensas con
límite junto al núcleo. Cilindro 3.6 m despejado en caras completas GLB.
299 pruebas, 55 checks, seis GLB/layout/estructura repetidos exactos; OF3 anterior
completa/rama y O5 históricos exactos. Tres controles geométricos 3101–3103 y
semilla de distribución 18, sin arte/exportación de controles. 46 capturas y ocho
máscaras inspeccionadas: follaje visible ~1.9–2.15 veces OF3 en cuatro vistas,
continuidad local mejor frente/perfil pero no uniforme desde arriba. Mayor área
de láminas/escala aparente de hojas, sin benchmark. Arte pendiente; huecos entre
brazos, parches bajos y láminas de canto persisten. [Informe](../docs/evidence/oak-foliage/of4/informe.md).

## OF5 — continuidad fina y macromasas, revisión del usuario 2026-11-03

El usuario valora cantidad/periferia/lectura de madera de OF4 y solicita pocos
puentes, menos capuchones, aliviar ruido interior y organizar masas en volúmenes
mayores. Conservar OF4, 216 grupos/5010 tris, madera y pintura; sin retoques por
semilla. Refinamiento independiente 0.5.0: agrupación espacial de masas en tres
conjuntos, enlaces entre vecinas y reasignación de máximo 18 grupos existentes,
hasta diez puentes pequeños sobre ramas reales próximas a huecos. Retrasar algunos
anclajes terminales y mover redundancias interiores solo si no invaden el núcleo.
No vaciar ni rellenar todo el centro; cilindro 0.30H conservado. Comparar OF4/OF5
con cámaras comunes, misma pintura y tamaño del resto; validar contactos, GLB,
repetición, continuidad y límites visuales. No implica aceptación final ni nuevas
edades/recetas. Un agrupamiento lógico por sí solo no demuestra macromasas visibles.

### Resultado OF5

0.5.0 implementado/verificado: tres conjuntos espaciales de 10/12/8 masas dirigen
la selección de enlaces. Dieciocho reasignaciones: diez puentes pequeños, seis
retrocesos terminales y dos redundancias interiores hacia afuera; 198 grupos
geométricamente exactos. Mantiene 216 grupos/5010 tris/dos materiales, madera,
pintura y cilindro 3.6 m. Anclajes después de 0.82 del eje: 54→38.
305 pruebas, 59 checks, seis GLB repetidos idénticos y referencias OF4/O5 exactas;
controles geométricos 3101–3103 y distribución 18, sin nueva aprobación de rango.
46 capturas + ocho máscaras inspeccionadas. Cobertura varía menos de 1.5 %, efecto
visual discreto; continuidad uniforme y macromasas más fuertes no demostradas.
OF4 permanece referencia valorada; OF5 candidata sin promover ni aprobar arte.
[Informe, límites y reproducción](../docs/evidence/oak-foliage/of5/informe.md).

## OF6 — volúmenes geométricos compartidos, autorizado 2026-11-03

El usuario solicita que las macromasas se lean como volúmenes mayores en maduro
3100, manteniendo 216 grupos/5010 tris, madera, pintura y núcleo despejado, sin
retoques por semilla. OF5 conserva su función histórica; nueva ruta 0.6.0.
La jerarquía debe modificar geometría: envolventes desde anclajes reales,
orientaciones coherentes por conjunto y alcance mayor en interfaces entre masas.
Conservar anclajes/plantillas/madera; ampliar selectivamente láminas existentes,
no añadir grupos ni llenar el núcleo. Núcleo protegido prevalece sobre extensión;
marcos fijos con intentos acotados y fallback a OF5. Evaluar transparencias/escala
aparente/solapamiento además de tris. Comparar OF5/OF6 en Godot con cámaras comunes,
varias vistas, distancias y sombras; comprobar contactos, repetición y controles
geométricos, sin promover receta ni edades por esta prueba.

Ajuste tras ensayo OF6-01: orientar el eje más largo hacia vecinas y estirarlo
produjo tiras/penachos y perdió carácter de pintura. Se conserva como intento.
La siguiente candidata mantiene proporciones de plantilla y marco mayoritariamente
original: aumento uniforme moderado en interfaces, giro suave hacia el eje común
y puntas sin aumento. Se conserva anclaje y el núcleo prevalece sobre escala.

### Resultado OF6

0.6.0 final: ejes comunes de tres conjuntos influyen suavemente en los marcos;
63 grupos de interfaz ampliados uniformemente, 105 con escala moderada, 34 puntas
sin aumentar y 14 limitados por núcleo. Proporciones de pintura, 216 anclajes,
madera y atlas intactos; **216 grupos/5010 tris/dos materiales**, cilindro 3.6 m.
310 pruebas, 59 checks; seis GLB/layout/estructura repetidos exactos, OF5/O5
históricos reproducidos. Controles geométricos 3101–3103/distribución 18, sin
exportaciones/revisión artística de controles. 46 capturas + ocho máscaras
inspeccionadas: volúmenes más unidos frente/perspectiva (componente mayor
0.422→0.642 / 0.280→0.452), superior aún fragmentada. Más área alfa y escala
aparente de hojas; sin benchmark ni aceptación artística. Primer estiramiento
anisótropo descartado por tiras/penachos; final conserva proporciones. OF4/OF5
conservadas, sin promover receta/edades. [Informe](../docs/evidence/oak-foliage/of6/informe.md).

## OF7 — continuidad superior y láminas de canto, autorizado 2026-11-03

El usuario valora el avance y solicita mejorar unión de masas desde arriba y
reducir cantos, manteniendo centro, 216 grupos/5010 tris, madera y pintura, sin
retoques por semilla. Nueva ruta 0.7.0 conserva OF6 como referencia.
Ensayar tríadas cruzadas inclinadas: ninguna lámina vertical de partida, marcos
fijos guiados por vertical física y vecindad de masas, sin billboards ni cámara.
Elegir entre ocho orientaciones por grupo mediante muestras opacas del PNG hacia
huecos periféricos XY. Conservar tamaños/anclajes/UV/PNG/madera y rechazar marcos
que invadan núcleo 0.30H; fallback a OF6. Comparar arriba y vistas oblicuas/Godot,
además de frente/perfil/distancias/sombras para no aplanar copa o perder madera.
Auditar contactos, presupuesto, área, marcos y determinismo; controles geométricos
con reglas comunes. Sin nuevas edades ni promoción de receta por esta prueba.

Ajuste tras OF7-02: la inclinación general mejora arriba pero fragmenta una unión
frontal. Limitar nuevos marcos a grupos con normal casi horizontal (|Nz|<0.15),
conservar marcos que ya aportan espesor y puntuar también centro opaco/continuidad
3D previos. No introducir cámaras laterales en el algoritmo. Verificar arriba y
oblicuas además del coste en frente/perfil, con muestras alfa UV correctas.

Refinamiento final OF7: conservar también marcos de puentes y correcciones OF5,
para no debilitar conexiones previas al corregir cantos de los grupos grandes.
Añadir dos vistas superiores oblicuas comunes a OF6/OF7 al protocolo de revisión.

### Resultado OF7

0.7.0 final: reorienta 63 grupos con cantos pronunciados, conserva 153 grupos
geométricamente exactos y todos los tamaños/anclajes/UV/PNG/madera. Protege puentes,
marcos ya útiles y núcleo 3.6 m; 216 grupos/5010 tris/dos materiales, área constante.
Muestreo alfa 16×16 por plano, ocho candidatos y puntuación XY/3D; 520 intentos.
316 pruebas, 61 checks, seis GLB repetidos exactos y referencias OF6/O5 idénticas.
Controles geométricos 3101–3103/distribución 18, sin revisión artística de controles.
50 capturas + ocho máscaras inspeccionadas, incluidas dos superiores oblicuas.
Láminas casi verticales 129→56; arriba componente mayor 0.205→0.277. **Coste frontal**:
componente mayor 0.642→0.445 con área casi igual; no mejora uniforme. Arte pendiente,
sin promover recetas/edades y con OF6 conservada. [Informe](../docs/evidence/oak-foliage/of7/informe.md).

## OF8 — recuperar continuidad lateral, autorizado 2026-11-03

El usuario pide recuperar frontal sin perder OF7 superior, conservando centro,
216 grupos, madera/pintura y reglas generales. Después autoriza un pequeño aumento
de tris si es necesario, con techo global 7k: aplicar máximo6999. Cambio de alcance
expreso: 5010 deja de ser techo estricto; no gastar margen sin una mejora revisable.

Ensayar una lámina complementaria inclinada en grupos OF7 que perdieron huella
opaca lateral respecto a OF6. Medir ocho azimuts iguales, no una cámara/semilla;
una lámina por grupo, máximo64/128tris extra, dentro de cada grupo existente.
Conservar OF7 completo, tamaños, anclajes, atlas y madera; contacto pintado real,
normal complementaria con componente vertical ≥0.24 y núcleo 0.30H protegido.
Validar presupuesto real, transparencia, contactos y área añadida. Comparar OF6,
OF7 y candidata con cámaras comunes, arriba/oblicuas y frontal/perfil/sombras.
No promover recetas/edades ni inferir FPS por recuento geométrico.

### Resultado OF8

0.8.0 final: 63 complementarias inclinadas, una en cada grupo con pérdida lateral
significativa en muestreo de ocho azimuts. OF7 íntegra como subconjunto geométrico
exportado; 216 grupos/711 láminas/dos materiales. **5136 tris: +126 (+2.5 %)**,
autorizado por el usuario; follaje1422 dentro de reserva1584 y máximo6999 intacto.
Madera, pintura, tamaños/anclajes y núcleo3.6 m conservados. 322 pruebas,69 checks,
siete GLB repetidos exactos; referencias OF6 completa/OF7 completa-rama/O5 exactas.
63 capturas +12 máscaras inspeccionadas. Frontal mayor componente OF6/OF7/OF8:
0.642/0.445/0.645; superior0.205/0.277/0.275, con OF7 preservada y área visible
superior creciente. Sin nuevos planos casi verticales; aumenta área alfa13.2 %,
sin benchmark ni aceptación artística. Reglas comunes en controles geométricos
3101–3103/distribución18; sin promoción de receta/edades.
[Informe, autorización y reproducción](../docs/evidence/oak-foliage/of8/informe.md).


### OF9: organización de regiones de copa, autorizada 2026-11-03

OF8 queda como **base aprobada provisionalmente** por el usuario. OF9 mantiene
216 grupos y láminas laterales; reorganiza soportes y orientaciones sobre madera
real de cada brazo para ampliar transversalmente las masas, conectar algunas
interfaces intermedias/exteriores y aliviar la proyección de follaje central.
Regiones lógicas tridimensionales, sin mallas adicionales, relleno uniforme ni
conexión obligatoria de todos los brazos. Cupos por longitud/vigor/exposición
heredados; madera, pintura y recetas históricas conservadas.

El usuario autoriza después **hasta +700 tris de follaje si hace falta**, siempre
con techo6999 total. Primera candidata mantiene exactamente5136 tris OF8, sin
ampliar tamaños ni añadir láminas. Reubicar contactos sobre tubos existentes
está autorizado por esta organización espacial; no se permiten hojas flotantes.
Comparar arriba/frente/perfil/perspectiva con cámaras y presupuesto comunes,
rotación360° a distancia media explícita y controles geométricos3101–3103/layout18.
La distancia habitual del juego no está especificada: no declarar aceptación
a esa distancia por usar una escala de captura. Siluetas alternativas quedan
pendientes; no repintar ahora. Aceptación artística OF9 pendiente.
[Dirección y margen autorizados](../docs/evidence/oak-foliage/of9/user-direction.json).

Resultado OF9: implementada/verificada en0.9.0, **216 grupos/5136 tris exactos**;
siete regiones por brazo,177 contactos desplazados>1 cm. 65 checks, siete GLB
repetidos idénticos;328 casos de prueba cubiertos mediante suite y repeticiones
OF9/HTTP (la suite en sandbox falló solo por sockets).135 capturas Godot,101
inspeccionadas y doce máscaras; giro24 azimuts. Perspectiva gana continuidad;
arriba+7.94 % de área visible, sin resolver la estrella ni mejorar todas las
regiones; conectividad frontal/perfil menor. OF8 permanece base provisional,
OF9 pendiente del usuario; margen+700 sin usar. [Informe y límites](../docs/evidence/oak-foliage/of9/informe.md).


### OF10: expansión hacia huecos entre brazos, autorizada 2026-11-03

El usuario rechaza como resuelta la organización superior OF9: sigue pareciendo
estrella. Pide expandir más las masas hacia huecos entre brazos y usar hasta
**+700 tris de follaje respecto a5136**, manteniendo216 grupos y bifurcaciones
visibles. No es autorización acumulativa por iteración: máximo5836 en este
piloto y6999 en cualquier caso. OF8 permanece base provisional.

Alternativa0.10.0 conserva OF9 íntegra y prueba láminas inclinadas en abanico,
con la misma raíz opaca sobre el portador existente. Se permite más alcance
en estas láminas, registrado como cambio de escala; atlas/pintura y madera
intactos, sin nuevos grupos ni mallas de macro-masa. Interfaces seleccionadas
entre regiones cercanas, manteniendo grandes separaciones y núcleo3.6 m.
Verificar añadidos y contactos exportados, comparar OF8/OF9/OF10 arriba/frente/
lado/perspectiva, giro y distancias; no declarar bifurcaciones despejadas solo
por cumplir el cilindro central. Controles geométricos3101–3103/layout18.
[Dirección autorizada](../docs/evidence/oak-foliage/of10/user-direction.json).

Resultado OF10:0.10.0 verificada, **5270 tris (+134 de700),216 grupos/778 láminas**.
67 láminas añadidas en46 grupos; OF9 íntegra, contactos opacos/madera/atlas
conservados. Arriba+20.26 % de área, cinco→tres componentes; madera central
visible≥99.54 % de OF9 en cuatro vistas.73 checks,seis pruebas nuevas,siete GLB
repetidos exactos; referencias OF8/OF9/O5 exactas.135 capturas,101 inspeccionadas
y24 máscaras; giro24 azimuts. Lectura radial parcial y hojas ampliadas persisten;
OF8 provisional, OF10 pendiente de arte. [Informe y reproducción](../docs/evidence/oak-foliage/of10/informe.md).


### OF11 / rama central: más soportes ascendentes, autorizada 2026-11-03

El usuario identifica falta de ramas centrales y precisa que necesita varias
ramas de dirección más vertical cerca de la copa. Cambio expreso: se permite
añadir madera, congelada en OF8–OF10. Ensayar un eje central ascendente y dos
brotes altos desde primarias, con bifurcaciones menores; conservar todos los
ejes O5 exactos, atlas/pintura,216 grupos y máximo6999 tris. Reserva de madera
nueva≤600 tris; no acumular otros700 de follaje por esta petición.

Diagnóstico: el cilindro vacío0.30H se aplicaba a todas las alturas, impidiendo
follaje central incluso junto a ramas altas. Proteger el cilindro solo hasta
0.62H (7.44 m en piloto), manteniendo las horquillas inferiores legibles; permitir
una copa interior alta con contactos reales. Reasignar24 grupos existentes a
terminales de los tres ejes nuevos, conservando el resto y todos los complementos
OF10. Es una nueva alternativa experimental, no modificación de recetas O5/OF10.

Comparar madera antes/después y árbol completo, arriba/frente/perfil/perspectiva,
giro y distancias en Godot. Auditar encajes, contactos exportados, protección
inferior mediante caras recortadas en Z y presupuesto; repetir GLB y controles
geométricos3101–3103. Arte pendiente; sin otras edades o promoción automática.
[Dirección y alcance](../docs/evidence/oak-foliage/of11/user-direction.json).

Resultado OF11: tres ejes ascendentes con bifurcaciones menores (21 piezas),
**+475 tris de madera;5745 totales/216 grupos/778 láminas/dos materiales**. O5
exacta como subconjunto;24 grupos trasladados a terminales nuevos y192 intactos.
Protección inferior hasta7.44 m, centro superior habilitado; contactos y encajes
exportados pasan.70 checks,seis pruebas nuevas,tres controles geométricos,
siete GLB repetidos exactos y O5/OF10 históricos exactos.135 capturas,101
inspeccionadas y8 máscaras. Desde arriba+13.53 % de área, pero tres→cinco
componentes por los grupos centrales; no se declara unión superior resuelta.
Madera aceptada para vestir y árbol completo aprobado posteriormente; ver registro3.0.0. [Informe y reproducción](../docs/evidence/oak-foliage/of11/informe.md).

Revisión del usuario: «bien ahora vuelve a agregar el follaje». Se entrega la
variante completa OF11 ya verificada, con216 grupos/5745 tris; sin nueva generación
ni modificación geométrica. [Aceptación de madera y alcance](../docs/evidence/oak-foliage/of11/wood-acceptance.json).


### Aprobación OF11 y registro como blueprint3.0.0 — 2026-11-03

El usuario aprueba el árbol completo mostrado y pide guardar el blueprint,
commit y push. Registrar `roble_copa_ancha@3.0.0`, contrato1.7, con perfil maduro
fijo y semillas base/distribución/pintura explícitas. Componentes nuevos
identifican O5 con extensión central, distribución OF11 y representación pintada
conservada. Recetas previas y predeterminados históricos intactos. Aprobación
artística limitada a3100/17/2718; otras semillas se validan o rechazan, sin ampliar
edades o rangos de parámetros. [Aceptación](../docs/evidence/oak-foliage/of11/user-acceptance.json).

Integración en el ejecutor/CLI/API compartidos: preparación geométrica derivada
en Python anfitrión, exportador Blender sin dependencias adicionales y auditoría
del GLB. CLI3.0.0 reproduce el GLB aprobado byte por byte (5745 tris); repetición
sin renders idéntica. [Auditoría de entrega](../docs/evidence/oak-foliage/of11/blueprint-release.json).

Entrega3.0.0 verificada: **345 pruebas en73 archivos y15 comprobaciones** de
receta, resolución, exportación y repetición. CLI con nueve vistas23.607 s y
repetición sin vistas15.073 s; GLB idéntico al piloto aprobado. Suite ejecutada
por archivos con cota180 s, reanudada por lotes tras interrupción del coordinador;
sin repetir archivos ya aprobados. Commit y push solicitados por el usuario.

### Validación de familia 3.0.0 — autorizada 2026-11-03

El usuario autoriza comprobar cinco maduros con las mismas reglas y pintura,
sin retoques individuales: estructura3100–3104, distribución17 y pintura2718.
3100 es el control aprobado;3101–3104 amplían la revisión a árboles completos.
Usar F4 (`plan-blueprints` / `generate-blueprint-plan`) para congelar entradas,
exportar el lote y repetirlo. No ampliar edades ni controles de la receta.
Conservar fallos; máximo6999 tris y dos materiales, auditoría de contactos y
GLB repetido idéntico por caso, sin duplicados exactos entre estructuras.

Cámara elegida por el usuario: perspectiva provisional. Fijar antes de capturar
un encuadre común en metros para todo el lote, tres distancias, vistas de giro,
superior y madera sola, fondos claro/oscuro y sombras. Registrar FOV, posiciones,
luz, resolución y motor. Inspeccionar capturas reales Godot: variedad, plenitud,
contactos aparentes, cantos, transparencias y sombras. La revisión del agente
no equivale a aceptación artística del usuario ni certifica todo el rango.
Entregar galería e informe seleccionado. Benchmark, viento, LOD y nuevas edades
quedan fuera de esta validación.

Resultado: cinco maduros completos **5745/6158/5447/6087/6006 tris**, dos
materiales,216 grupos; cinco repeticiones GLB idénticas, piloto igual al aprobado
y cinco firmas geométricas distintas.38 condiciones de auditoría y13 pruebas
existentes;115 capturas reales Godot, cinco láminas inspeccionadas y siete
originales. Perspectiva provisional FOV50° con posiciones comunes congeladas.
Variación visible, pero radialidad superior y masas separadas persisten; sombras
con extremos recortados. Lote3100–3104 aprobado artísticamente por el usuario.
Intento sandbox agotó120 s al cerrar audio; conservado, mismo plan ejecutado y
repetido fuera correctamente. Receta/algoritmos intactos, sin ampliar edades.
[Informe y reproducción](../docs/evidence/roble-central/familia-01/informe.md).

Aceptación posterior del lote el2026-11-03: «ok, lo apruebo, que sigue ?».
[Decisión y hashes](../docs/evidence/roble-central/familia-01/user-acceptance.json).
La aprobación mantiene los límites observados y no amplía edades o semillas.
Siguiente recomendado: benchmark acotado Godot; aún no autorizado ni iniciado.

### Benchmark del roble3.0.0 — autorizado 2026-11-03

El usuario autoriza ejecutar la recomendación:1/128/512 árboles, cuatro
repeticiones por carga,1080p/MSAA4/sombras y condiciones congeladas. Medir el
asset aprobado, sin comparación de versiones/especies ni atribuir optimización.
Usar los cinco GLB3100–3104 aprobados, distribución17/pintura2718; una instancia
usa3100, cargas múltiples alternan variantes por índice. Rejilla18 m y giros
deterministas, sin MultiMesh, LOD, viento ni un nuevo sistema de bosque.

Configuración `configs/verification/oak-performance-v1.json`: cámara ortográfica
estática común entre repeticiones de cada carga; cambia el encuadre entre cargas
para mostrar toda la rejilla. Separar resultados por cantidad: no extrapolar
FPS linealmente ni presentarlos como FPS de un juego. Sombras hasta1500 m para
cubrir la rejilla más extensa. Tres segundos de calentamiento y seis de muestra;
captura fuera de muestra más un segundo adicional de calentamiento. Verificar
GPU real, resolución efectiva, alfa, filtrado, sombras, instancias y ausencia de
VSync/cap/LOD. Congelar hashes de recursos/fuentes/entradas antes de medir.
Prueba corta del arnés antes de las12 mediciones principales; conservar fallos,
raw regenerable y evidencia seleccionada. Cada subproceso termina antes de180 s.

Resultado: **12 mediciones completas y auditadas**, cuatro por carga. Medianas
1/128/512: **0.660/1.671/4.139 ms por cuadro**,1514/598/242 FPS; P95
0.860/1.955/4.746 ms. Godot4.7.2/RTX5060/1080p/MSAA4/sombras, cinco GLB
aprobados intactos, hashes/ajustes/instancias/layouts correctos; cinco pruebas
del arnés. Tres capturas1080p inspeccionadas: rejillas y sombras presentes,
árboles pequeños al alejarse la cámara entre cantidades. No son FPS de un juego
ni mejora frente a otra versión; no aislar causalidad de alfa/sombras/geometría.
Primer smoke falló al leer un entero JSON como float; conservado, corregido y
segundo smoke correcto antes de medir. Ningún ensayo principal descartado.
[Informe, condiciones y reproducción](../docs/evidence/roble-central/rendimiento-01/informe.md).
Benchmark cerrado; conservar geometría y definir cámara/escena representativa
antes de nuevas decisiones de optimización. No se inician LOD, viento o bosque.

Decisión2026-11-04 del usuario: «por ahora no haremos mas pruebas de rendimiento».
No continuar benchmarks. Siguiente propuesta: desarrollar perfil joven de la
familia nueva, partiendo de la madera O5 joven y revisando rama/follaje antes
del árbol completo; propuesta sin iniciar, no ampliación ya implementada de3.0.0.

### J1 — perfil joven, autorizado 2026-11-04

El usuario autoriza la propuesta de perfil joven: revisar madera, preparar rama
con follaje reutilizando pintura aprobada y, después de aprobar la muestra,
integrar piloto y tres variantes. Se conserva3.0.0 y toda receta histórica.
No hacer más pruebas de rendimiento. Centenario, viento, LOD y bosque fuera.

Primera entrega: O5 joven de5 m/madurez.15, semillas3100–3103, sin escalar
simplemente el maduro. Revisar madera completa y primarias solas en Godot,
incluida comparación de porte normalizada con O5 maduro3100. Reutilizar los
algoritmos existentes; corregir reglas solo si aparece un defecto demostrado,
con alternativa versionada y sin ajustes por semilla.

Muestra inicial: joven3100, primaria `p:0` y descendientes; distribución17 y
pintura2718. Pintura/corteza0.3.0/0.2.0 aprobadas e intactas. Contrato experimental
`oak-young-sample-0.1.0`, perfil fijo:144 grupos por árbol, tres planos/seis tris
por grupo, span/H.10, región de anclaje radial.25H y cadenasB existentes. No
imponer al joven los tres ejes centrales ni el cilindro del maduro3.0.0.
Solo materializar el cupo de esta rama;864 tris reservados de follaje completo,
madera O5≤5415 y techo conjunto6279≤6999, dos materiales. Cupos calculados desde
la madera real antes de exportar; reservar no certifica una copa aún sin construir.

Validar contratos, contactos/UV/alfa sobre GLB, madera idéntica con/sin follaje,
uniones, determinismo, regresiones maduras y presupuesto. Preparar repetición y
capturas Godot de madera, rama vestida y follaje aislado, varias vistas/fondos/
distancias y sombras. Presentar resultado concreto para aprobación artística
de muestra antes de integrar follaje del árbol completo, según política vigente.
Piloto completo/tres controles y registro de receta nueva quedan posteriores;
no declarar integración ni aprobación de edades por validar solo la muestra.

Resultado J1: madera O5 joven conservada, cuatro casos3100–3103 de5 m:
2952/3233/2672/3258 tris, auditorías y cuatro siluetas distintas. Piloto y
primarias repetidos idénticos; dos GLB de joven3100 y dos de maduro3100 exactos
a O5 histórico. Muestra p:0:71 grupos/213 láminas,620 madera+426 follaje=
**1046 tris/dos materiales**, pintura exacta. Cuatro GLB/layout/estructura
repetidos;23 checks de exportación/contactos/uniones y11 pruebas correctas.
Godot:48 capturas de madera y36 de muestra,84 miniaturas y tres originales
inspeccionados. Porte joven más esbelto; rama compacta de perfil, cantos arriba
y ramilla inferior desnuda. Árbol completo con follaje no integrado; proyecciones
3816/4097/3536/4122 son reservas aritméticas, no copas verificadas.
Aceptación artística de madera/muestra pendiente, antes de integrar piloto y
tres controles completos. No se hicieron nuevas pruebas de rendimiento.
[Informe, galería y reproducción](../docs/evidence/roble-joven/j1/informe.md).

### J2 — copa joven completa, autorizada 2026-11-04

El usuario responde «si» a la aprobación de madera y rama J1 para continuar.
[Aceptación y hashes](../docs/evidence/roble-joven/j1/user-acceptance.json).
Integrar piloto3100 y controles3101–3103,5 m,144 grupos,distribución17/pintura2718,
madera y pintura exactas, dos materiales y6999 tris máximo. La aceptación J1
no aprueba por adelantado el árbol completo. Sin nuevos benchmarks.

Preflight conservado: cadenaB recibe dos grupos en p:4 de3102, pero no tiene
segmentos elegibles. Ampliación necesaria del reparto para la copa joven:
calcular capacidades con los mismos candidatos geométricos, limitar cupos y
redistribuir excedentes entre ramas con capacidad. Regla común, sin ajustes por
semilla, sin cambiar cadenasB históricas ni el aspecto de p:0 del piloto aprobado.
Registrar cupos iniciales/finales, descartes y cotas; rechazar si no hay capacidad
global suficiente. No añadir madera central ni relajar contactos por completar.

Contrato1.8 y receta nueva `roble_copa_ancha@3.1.0` de perfil joven fijo,
conservando3.0.0 y versiones históricas. Separar distribución, resolución,
exportación y evaluación. Integrar CLI/F4 con entradas congeladas y repetición;
auditar GLB, contactos, texturas, presupuesto y madera exacta de los cuatro casos.
Comprobar identidad de la muestra piloto en la copa completa y regresiones de
maduro3.0.0 y O5. Revisar capturas Godot de todos los casos con cámaras comunes,
giros, distancias, fondos y sombras; aceptación artística completa pendiente.

Resultado J2: `roble_copa_ancha@3.1.0` experimental integrado en CLI/API/F4,
contrato1.8. Cuatro jóvenes3100–3103: **3816/4097/3536/4122 tris**,144 grupos,
432 láminas, dos materiales. Cuatro GLB repetidos idénticos; madera aprobada
exacta en posiciones/normales/UV. Grupos de p:0 piloto y caras/atributos de su
muestra aprobada exactos dentro del GLB completo. Maduro3.0.0 regenerado idéntico.
30 checks de cierre y360 pruebas en76 archivos correctos. Godot:92 capturas
inspeccionadas en láminas y cuatro frentes originales; copas muy abiertas,
ápices desnudos y cantos visibles. No se declara plenitud suficiente ni arte
completo aprobado; siguiente paso es valoración artística del lote.
3102 redistribuye dos grupos de p:4, cero en los demás casos; rechazos/test de
serialización conservados. Sin nuevas mediciones de rendimiento.
[Informe J2 y reproducción](../docs/evidence/roble-joven/j2/informe.md).

### J3 — cobertura de ramas y volumen joven, autorizado 2026-11-04

El usuario señala falta de follaje en varias ramas y pide más volumen. J2/3.1.0
queda como referencia técnicamente válida, sin aprobación artística completa.
Se autoriza cambiar distribución, cantidad, tamaño y orientación del follaje;
conservar madera O5 y pintura aprobadas. La muestra J1 histórica sigue íntegra,
pero su distribución exacta no restringe esta corrección explícita de cobertura.

Nueva alternativa `roble_copa_ancha@3.2.0`, contrato1.8 ampliado para componentes
jóvenes0.2.0, sin alterar la resolución de3.1.0.264 grupos/1584 tris de follaje;
cota madera5415+1584=6999. Grupos más amplios, span/H.16 y profundidad recuperada,
marcos inclinados fijos en espacio. Sin filtro radial para ejes superiores y
ramas cortas; conservar madera de unión visible sin imponer el cilindro maduro.

Garantizar cupo al extremo de cada eje real y al líder superior; repartir el
resto por longitud/vigor y capacidad acotada, sin retoques por semilla. Anclar
siempre sobre madera y pintura opaca, sin conectores flotantes. Registrar
cobertura de ejes, grupos, descartes, área/tamaño y triángulos sin equiparar
métricas a plenitud artística. Comparar3.1.0/3.2.0 en3100–3103 con cámaras/luz
comunes, giros, arriba, distancias y sombras. Repetición, madera/PNG exactos,
contactos/UV y regresiones de3.1.0/3.0.0. No hacer nuevos benchmarks.

Resultado J3:3.2.0 experimental implementado y verificado. Cuatro casos
4536/4817/4256/4842 tris,264 grupos/792 láminas/dos materiales, madera/PNG
exactos a J2. Ejes con follaje24→83,36→92,17→71 y34→89: todos los ejes reales
con cupo distal, incluido líder.35 checks y365 pruebas/77 archivos correctos;
cuatro GLB repetidos idénticos y regresiones3.1.0/3.0.0 idénticas. Repetición
recuperada tras SIGTERM externo del cuarto caso, con intentos e inventario
compuesto registrados.120 capturas Godot inspeccionadas con cámaras comunes;
mayor cobertura y volumen aparente, cantos/repetición aún visibles. Sin nuevos
benchmarks; aceptación artística pendiente del usuario.
[Informe, comparación y reproducción](../docs/evidence/roble-joven/j3/informe.md).

Cierre J3,2026-11-04: el usuario declara «mucho mejor lo apruebo». Aceptación
artística de los cuatro jóvenes3100–3103 registrada con hashes de GLB y
comparación; copa J3 cerrada y aprobada. Receta congelada sin cambios de
metadatos/hashes; nuevas semillas no heredan aprobación. Sin nuevos benchmarks.
[Aceptación J3](../docs/evidence/roble-joven/j3/user-acceptance.json).
