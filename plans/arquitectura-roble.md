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
