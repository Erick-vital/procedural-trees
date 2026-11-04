# F5: estructura Python y competencia por espacio

Inicio autorizado el 2026-11-03: «ok apruebo f4 y continua con f5».
Desarrolla F5 del [plan v1](v1-generador-arboles.md); F6 no se inicia.

## Protocolo fijado antes de la comparación

- Separar transición Geometry Nodes → Python de la regla espacial. La base Python
  conserva la familia Q1b/Q3 de parámetros y dos niveles, sin exigir geometrías
  iguales entre algoritmos. Cambia el PRNG: SHA256 por rama/stream explícitos.
- `BranchStructure` 0.1.0 contiene IDs, jerarquía, polilíneas y radios. Adaptador
  experimental independiente inyecta curvas en una copia en memoria del grafo
  Q3 y reutiliza su volumen, normalización Q2 (solo Z), moldes y ruta pintada
  2.2.0. No modifica contratos, recetas ni alias aprobados. No es receta nueva
  de producción: resultados experimentales, cruzadas, atlas conservados,
  dos materiales y máximo 6999 tris comprobados al exportar.
- Base y candidata: mismos 30 IDs/semillas Q3 (diez por edad), parámetros del
  perfil pintado 2.2.0, copa=17/pintura=2718. Los doce IDs terminados 00–03
  son diagnóstico; los dieciocho 04–09 son reservados. No ajustar la regla
  después de ver los reservados. Registrar ambos grupos y el conjunto.
- Regla 0.1.0: solo rotar secundarias alrededor de Z en su nacimiento. Dos
  barridos y nueve alternativas: 0, ±15°, ±30°, ±45°, ±60°. Incluir posición
  actual; aceptar reducción de conflictos incidentes y después penetración.
  Tronco/primarias, raíces, Z, radios, cantidad y longitud conservados. No poda,
  reintentos aleatorios, luz, gravedad ni reubicación de nacimientos.
- Métrica 0.1.0: parejas de ramas distintas con cápsulas de segmentos solapadas,
  normalizadas por longitud total. Radios máximos por segmento; tras Q2,
  multiplicar por max(1, escala Z): cota conservadora de secciones elípticas,
  no intersección exacta de mallas. Excluir zona legítima padre–hijo solo hasta
  dos veces la suma de radios desde el inicio del hijo, no toda la pareja.
  La regla evalúa coordenadas crudas; el resultado final se mide también con
  la escala Z real del mallador y verifica los ejes usados por Blender.
- Objetivo original: mediana de conflictos/m −25 %, longitud ≥90 % en cada
  pareja, sin nuevos fallos. Mediana base cero: mejora relativa indefinida,
  no declarar éxito. Conservar fallos y denominadores; resultado negativo válido.
- Validación: casos analíticos de distancia/unión/radios, entradas y determinismo;
  sesenta exportaciones reimportadas, repetición y regresión histórica;
  capturas Godot comunes por pareja, copa y madera, revisión de imágenes reales.
  Medir coste/triángulos, no FPS. Arte de la nueva estructura pendiente del usuario.
- Generación ≤120 s por subproceso; revisión ≤180 s, procesos terminables.
  Fallos persistidos y fuentes/entradas/hashes congelados antes del lote.

## Estado

**Cerrada técnicamente el 2026-11-03; arte pendiente.**
[Informe y reproducción](../docs/evidence/f5/espacio-01/informe.md),
[auditoría seleccionada](../docs/evidence/f5/espacio-01/verification.json).
Treinta parejas, 3044–6772 tris/dos materiales; 227 pruebas, 69 checks, seis
repeticiones GLB idénticas y tres regresiones históricas exactas. 480 capturas
Godot y 156 imágenes seleccionadas inspeccionadas, cubriendo las treinta parejas.

La métrica definitiva utiliza anillos retenidos por el simplificador, auditados
contra la madera exportada (error de centro ≤1,15 µm), no solo curvas iniciales.
Se conserva la medición previa a simplificar como diagnóstico separado. Dos
barridos pueden acumular ±120° de giro de secundarias; no cambian alturas/radios.

Objetivo mediano cumplido: −86,49 % global y −93,43 % en 18 reservados, longitud
final conservada en todas las parejas. La mejora no es uniforme: mediana joven
−100 %, adulta sin cambio y vieja −2,92 %. Suma de conflictos 109→98 (−10,09 %).
No afirmar que el porcentaje de mediana representa una reducción igual de todos
los conflictos ni una mejora general de árboles adultos/viejos o del arte.

La aceptación artística de la base Python y candidata queda pendiente. Las
recetas, alias y atlas aprobados siguen conservados; no se registra receta nueva,
no hay benchmark de FPS y F6 sigue sin iniciar. No quedan bloqueos técnicos.


## Valoración artística posterior — 2026-11-03

El usuario valora muy positivamente el resultado con follaje y considera
insatisfactoria la madera descubierta: lectura de troncos con picos de estrella,
sin una ramificación convincente. [Valoración literal y alcance](../docs/evidence/f5/espacio-01/user-review.json).
No constituye aceptación artística integral de F5 ni promoción de su base Python.

El diagnóstico distingue las ramas del esqueleto de los soportes independientes
que conectan grupos de follaje. La regla de separación ensayada no modifica
la jerarquía ni convierte esos soportes en una red de ramillas compartidas.
El éxito de proximidad no resuelve este criterio artístico.

Siguiente paso propuesto: revisar una rama de muestra sin follaje, con
bifurcaciones escalonadas, continuidad de grosor y ramillas conectadas; usar
la copa y pintura actuales como referencia que conservar. La futura integración
requiere comparación con/sin follaje y presupuesto total ≤6999 tris/dos materiales.
Esta anotación registra la valoración y la dirección propuesta; no implementa
la revisión, no cambia los resultados congelados ni inicia F6.

## Rama de muestra R1 — autorizada el 2026-11-03

El usuario solicita continuar con una rama más natural sin perder la copa que le
ha gustado. También pregunta por conservar la estructura por nodos: la migración
Python fue una decisión experimental de F5, no una mejora artística demostrada.
El generador por nodos sigue disponible y no se sustituye en producción.

R1 toma `candidate/joven-03`, primaria 100 y sus tres secundarias como referencia.
Congelar exactamente posiciones, UV, índices, atlas y grupos de follaje de esa
muestra. Conservar el eje principal y sustituir secundarias/conectores radiales
por una red jerárquica: tres nacimientos escalonados, bifurcaciones binarias,
grosores decrecientes y terminales que llegan al centro de cada grupo cruzado.
Semilla explícita, IDs estables, ≤360 destinos y profundidad acotada. Las uniones
son superficies solapadas continuas; no se promete soldadura topológica.

Exportar rama anterior/candidata con follaje idéntico; comprobar también máscaras
sin madera y mostrar ambas descubiertas en Godot. Añadir una rama histórica por
nodos del mismo perfil/semilla como referencia independiente, con su propio
follaje: cambia el algoritmo de estructura, no es la comparación de copa congelada.
Proyectar presupuesto de integración desde el comienzo (<7000 tris/dos materiales)
para fuentes joven/adulto/viejo, sin construir ni adoptar árboles nuevos completos.
No modificar atlas/recetas ni los resultados F5; no iniciar F6. Entregar muestra,
capturas, reproducción y limitaciones. Arte R1 pendiente del usuario.


### Resultado R1

**Implementada/verificada; muestra artística pendiente.**
[Informe y comparación](../docs/evidence/f5/rama-r1/informe.md),
[auditoría](../docs/evidence/f5/rama-r1/verification.json).
87 grupos congelados: coordenadas, UV, normales y pintura exactas al exportar;
seis pares de máscaras Godot idénticas. Tres nacimientos al 32/56/79 % del eje,
171 tramos y profundidad 6, máximo dos hijos por bifurcación.
Muestra nueva 1700 tris/dos materiales frente a 1058 anterior. No es ahorro de
geometría; proyección de integración 5590/6380/6696 tris para las tres fuentes
ensayadas, sin construir árboles completos ni certificar rangos.
229 pruebas, 25 checks, cinco repeticiones GLB idénticas; 48 capturas reales
Godot inspeccionadas. Resultado: `artifacts/f5/rama-r1-03/index.html`.

Referencia nodal regenerada, mismo perfil/semilla, con su propio follaje y
alineación rígida explícita para presentación. Sus soportes también forman
abanicos. La revisión de ramillas está separada de la base: no exige abandonar
Geometry Nodes ni decide por anticipado qué estructura debe adoptarse.
El generador nodal y las recetas aprobadas siguen conservados.

Se ajustó la distribución inicial de destinos por cupos para evitar concentrar
ramillas finas en la punta; intentos anteriores conservados. Persisten puntas
muy finas, ángulos facetados y uniones sin soldar. Siguiente: valoración de la
rama con/sin follaje antes de una integración completa; F6 sin iniciar.

## Comparación R2 — autorizada el 2026-11-03

El usuario valora positivamente la ramificación R1 y solicita compararla con una
versión simplificada, conservando copa y ramas visibles. Se autoriza únicamente
la comparación de la muestra, sin integración completa ni comienzo de F6.

Referencia congelada: `artifacts/f5/rama-r1-03/`, variante `candidate`, 1700 tris,
87 grupos de follaje. Conservar exactamente eje principal, atlas, láminas, UV y
normales. Selección determinista de madera a partir de visibilidad contra las
láminas y su alfa real, con trabajo acotado y direcciones de inspección fijadas.
Proteger los tramos expuestos y todos sus ancestros; conservar los tres nacimientos.
Eliminar solo subárboles sin exposición detectada, sin dejar ramas visibles
flotantes ni cambiar topología de los tramos conservados. La clasificación es
conservadora pero finita: no garantiza invisibilidad desde cualquier cámara.
La variante simplificada se destina al uso con copa llena; no representa un
árbol desnudo con todos los soportes físicos de las láminas.

Comparar en Godot cámaras comunes, seis orientaciones, cerca/media/lejos,
vistas desde abajo, giro con direcciones reservadas y sombras. Verificar hojas
exportadas idénticas y máscaras de follaje; registrar diferencia de imagen completa
y madera visible por separado. Mostrar también madera descubierta para explicar
qué se ha eliminado. Si la protección impide un ahorro útil, registrar ese resultado
sin podar partes visibles para forzar una reducción. No afirmar mejora de FPS.
Conservar R1 y recetas históricas. Arte de la nueva simplificación pendiente.


### Resultado R2

**Comparación implementada/verificada; aceptación artística pendiente.**
[Informe y reproducción](../docs/evidence/f5/rama-r2/informe.md),
[auditoría](../docs/evidence/f5/rama-r2/verification.json).
R1 1700 → R2 1416 tris (−16,71 % total / −24,11 % madera), dos materiales.
Follaje exacto: 87 grupos; eje principal y 113 de 171 tramos conservados sin
modificar sus mallas, incluyendo todos los expuestos y sus ancestros.
58 tramos ocultos eliminados. Selección conservadora con alfa real y 74 direcciones;
las direcciones intermedias actúan como protección, no como conjunto reservado.

231 pruebas, tres casos alfa analíticos y 23 checks correctos; cuatro repeticiones
GLB idénticas. 26 máscaras de madera visible exactas; 25/26 imágenes normales
idénticas y una cambia un píxel (máximo 13/255). Tres sombras en suelo idénticas.
140 capturas finales, 94 seleccionadas inspeccionadas; seis encuadres preliminares
adicionales conservados. Galería: `artifacts/f5/rama-r2-03/index.html`.

Uso propuesto solo con copa llena estática: no quedan todas las conexiones físicas
originales a cada grupo oculto. Sin certificación universal de visibilidad ni
integración completa; no extrapolar el ahorro a todo el árbol. R1 y nodos
conservados, F6 sin iniciar. Siguiente: valoración de la comparación R2.

## Decisión de uso y revisión R3 — 2026-11-03

El usuario elige R2 también sin follaje: «ok pero usa la simplificada tambien
incluso cuando no tiene follaje apenas noto diferencia». Queda aprobada como
rama de referencia descubierta; la restricción artística propuesta de usarla
solo con copa llena se sustituye por esta decisión. Se conserva la geometría R2
y sus límites técnicos; no es una validación de todo el árbol ni de todos los rangos.
[Decisión](../docs/evidence/f5/rama-r2/user-acceptance.json).

A continuación solicita: «y la con follaje simplificala aun mas». R3 mantiene R2
para madera descubierta y prepara una variante adicional con follaje idéntico.
Probar alfa mínimo 160/255 y 128/255 como candidatos, manteniendo sin cambios el
clasificador R2 y su resultado histórico. El alfa de entrada se preprocesa de
forma explícita y versionada. Conservar tramos expuestos bajo ese umbral y sus
ancestros; después proponer contracciones de bifurcaciones ocultas (máximo tres
rondas, grado resultante ≤3), verificando que los segmentos sustitutos también
queden ocultos. Los tramos expuestos y nacimientos conservan malla exacta.

Elegir el candidato de menor coste que preserve las máscaras de copa/madera
visible en el protocolo Godot R2. Los cambios de topología interior deben mantener
la conexión de la madera visible a su eje principal. No forzar ahorro si aparece
pérdida visible; registrar candidatos y rechazos. Exportar también R2 sin follaje
como asset explícito. No alterar recetas, atlas ni la copa, no integrar árboles
completos ni iniciar F6. La variante nueva con follaje queda por valorar.


### Resultado R3

**R2 elegida sin follaje; R3 nueva con follaje verificada, arte pendiente.**
[Informe](../docs/evidence/f5/rama-r3/informe.md),
[registro de variantes](../docs/evidence/f5/rama-r3/chosen-variants.json).
Asset R2 desnudo: 894 tris/un material, madera exacta de R2. Con copa:
R3 1324 tris/dos materiales, frente a R2 1416 (−6,50 % adicional) y R1 1700
(−22,12 % acumulado). 87 grupos intactos; 802 tris de madera y 522 de follaje.

Alfa 128 seleccionado por menor coste y prueba de visibilidad correcta; alfa 160
respaldo geométrico de 1328 tris, sin revisión visual porque no fue necesario.
Un terminal oculto adicional eliminado y once contracciones interiores aceptadas:
101 tramos de red, conectados al eje principal. Mallas expuestas/nacimientos exactos.
233 pruebas, 26 checks, cinco repeticiones GLB idénticas; 26 máscaras de madera
visible y seis de copa exactas; tres sombras idénticas. 146 capturas, 88 seleccionadas
inspeccionadas. Solo una vista normal cambia un píxel de 810 000 (13/255 máximo).

Galería `artifacts/f5/rama-r3-128-01/index.html`. Sin árbol completo, conmutación
por estaciones ni garantía universal. R2 sin hojas está aceptada; R3 con hojas
queda para valoración antes de integrar. Recetas y nodos conservados; F6 sin iniciar.

## Integración R4 — autorizada el 2026-11-03

Petición: «continua con la inteegracion en arboles». Llevar R2 sin hojas y R3 con
hojas a árboles completos, manteniendo copa/pintura y recetas históricas. Primera
salida explícita `branch-tree-0.1.0`, con generador reproducible y CLI propio;
no promover alias existentes ni ampliar F4/F6 por esta integración.

Matriz inicial congelada: joven-03 (1003), adulto-00 (2000), viejo-00 (3000) y
viejo-09 (3009); perfiles de la receta pintada 2.2.0, copa 17/pintura 2718. Base
Python F5 candidata regenerada desde fuentes, sin depender de ensayos guardados.
Mantener tronco/primarias y construir redes hacia los grupos de cada rama principal
(incluidas sus antiguas secundarias). Los grupos ligados al tronco reciben una
red en su tramo alto, con nacimientos dentro de esa madera. Semilla de primaria
100 conserva la base; otras primarias usan base+1009×índice módulo 2147483647,
tronco usa stream separado. La primera primaria del joven-03 debe reproducir R2/R3.

Clasificar cada red contra su propio follaje para mantener el criterio de la
muestra y ser conservador respecto a la oclusión extra del resto de la copa.
R2: alfa 217, protección de ancestros. R3: alfa 128 y hasta tres rondas de
contracciones interiores verificadas. Exportar estado con/sin follaje, referencias
de comparación y controles de máscara. Tronco/primarias, follaje, UV y atlas exactos.

Presupuesto previo conservador: 206+158×primarias+18×grupos; con 264 grupos y los
perfiles admitidos, máximo 6696 tris en los cuatro casos. Auditar el GLB final
(<7000 tris/dos materiales), raíces de redes dentro de madera y continuidad de
las redes. Generación total ≤120 s por árbol; pruebas/capturas ≤180 s por proceso.
Revisar en Godot edades, semilla vieja alternativa, cerca/media/lejos, abajo,
giro, madera descubierta, sombras y diferencias con la copa congelada. Conservar
fallos; no certificar rangos/semillas no ensayados ni prometer soldadura o FPS.

Ajuste de verificación R4: primer lote `integracion-r4-01` cumplió geometría,
pero el joven añadió un píxel a la máscara de madera en `orbit-06` (ninguno
perdido); dos píxeles normales cambiaron, delta máximo 17/255. La comprobación
estricta de máscaras no pasó y se conserva ese intento. Añadir a R3 catorce
ángulos de protección de inspección (`branch-tree-guard-angles-0.1.0`), también
para contracciones; R2 no cambia. Adaptador separado: clasificador histórico
intacto. Regenerar/revisar lote `integracion-r4-02`; no dar por corregido sin captura.

### Resultado R4

**Integración explícita `branch-tree-0.1.0` implementada y verificada.**
[Informe](../docs/evidence/f5/integracion-r4/informe.md),
[uso](../docs/uso-arboles-ramificados.md). Lote final `integracion-r4-04`:
joven/adulto/viejo/viejo-09 con hojas **4874/6140/6408/6408**, sin hojas
**3426/4556/4824/4824**; dos/un material y 264 grupos exactos. Generación
19,60–47,97 s por árbol. CLI nuevo, sin modificar recetas/alias históricos.

Alfa 217 y catorce ángulos adicionales en R3 integrada: algo más conservadora
que la muestra alfa 128; R2 desnuda intacta y primera primaria joven idéntica
a la muestra aprobada. R3 ahorra 136 tris en joven; en adulto/viejos conserva
R2 completa. Redes continuas, nacimientos dentro de sus ejes; tronco/primarias
y follaje exactos en atributos float32, atlas intactos. Sin promesa de soldadura.

239 pruebas, 33 checks de cierre y 19 por árbol; cinco GLB repetidos idénticos,
fuente repetida e histórica 2.2.0 idénticas. 608 capturas reales Godot;
104 máscaras de madera, 24 de copa, 116 pares normales y doce sombras exactos.
240 capturas únicas inspeccionadas en 22 láminas. El arnés compartido variaba
hasta dos píxeles incluso con GLB idéntico; procesos separados corrigieron la
comparación. Intentos -01/-02/-03 retenidos y documentados, sin rebajar criterios.

Integración autorizada; **aceptación artística de los árboles completos pendiente**.
No ampliar a F6/F4, estaciones, LOD ni nuevos lotes por este cierre. Siguiente:
valoración del árbol completo; copa conservada y recetas históricas disponibles.

## Continuación O1 — arquitectura y madurez

Nueva petición del usuario: sustituir las reglas radiales y priorizar la arquitectura
de *Quercus robur* libre, incluyendo diferencias entre joven, maduro y centenario.
Se permite cambiar tronco/primarias y volumen: ya no rige congelar la copa de R4
para esta alternativa. [Plan activo y resultados O1](arquitectura-roble.md).
R4, recetas/nodos y su evidencia permanecen disponibles. F6 no se inicia.
