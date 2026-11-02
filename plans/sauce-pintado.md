# Sauce pintado de copa colgante

Fecha: 2026-11-02. Nuevo alcance solicitado por el usuario: ampliar el catálogo
con un sauce de copa colgante, empezando por su pintura. **F4 queda pendiente
para después de terminar esta variante**, sin iniciarla automáticamente.
Las transiciones T0–T6 del roble permanecen cerradas y aprobadas.

## Dirección artística y fase actual

Pintura de aspecto manual, mate y de pincelada amplia, coherente con el catálogo.
Hojas largas, estrechas, lanceoladas y puntiagudas; verdes salvia/oliva con luces
amarillo verdosas contenidas y reversos gris verdosos. Ramillas pardo ocre finas,
arqueadas y descendentes. Corteza parda grisácea cálida con surcos longitudinales
irregulares. Copa ancha con cortinas colgantes, profundidad y claros legibles.

[Propuesta de pintura](../docs/evidence/sauce-pintado/pintura-01/ficha.md)
generada y **aprobada por el usuario**; [decisión](../docs/evidence/sauce-pintado/pintura-01/user-acceptance.json). No es un
atlas de producción ni geometría implementada. La silueta ilustrada orienta el
carácter, sin fijar medidas, densidad ni presupuesto geométrico aprobado.

## Secuencia y criterios

1. Presentar follaje, ramilla y corteza para valoración de pintura.
2. Tras aprobar la dirección, preparar atlas versionados con fuente, prompt,
   procedencia y hashes. Construir una rama representativa con láminas cruzadas
   fijas, número y contorno elegidos para conservar el volumen colgante.
   Verificar exportación y revisar alfa, sombras, cantos y contactos en Godot;
   presentar la rama para aceptación artística antes del árbol completo.
3. Tras aprobar la rama, integrar estructura propia de sauce, con ramas de
   sostén arqueadas y ramificación descendente. Definir perfil inicial acotado,
   semillas explícitas y presupuesto previo antes de mallar. Conservar recetas
   históricas; separar contratos, algoritmos, ejecución y adaptadores.
4. Validar piloto y tres controles reproducibles: GLB reimportados, integridad,
   determinismo, regresiones y revisión visual de copa/madera en Godot con luz,
   cámaras y distancias comunes. Aceptación artística del árbol separada.
5. Cerrar informe, reproducción y estado; dejar F4 como siguiente trabajo
   pendiente de definición/adaptación a blueprints y decisión de inicio.

Aplicar la [política de producción](../docs/politica-arboles-optimizados.md):
**máximo 6999 triángulos totales y dos materiales**, atlas compartidos ≤2048²,
madera simplificada sin perder conexiones o carácter, generación ≤120 s y cada
subproceso de prueba/captura ≤180 s. No trasladar el techo histórico de 12500.
La lámina no acredita estas condiciones; se comprobarán en la geometría real.

Sin otras edades, estaciones, caída, viento, LOD, bosque ni benchmark en este
alcance. No declarar mejoras de rendimiento sin medición. Abedul completo
conserva su aceptación artística pendiente, independiente del sauce.

## Resultado de la rama — 2026-11-02

Checkpoint previo solicitado por el usuario: commit `daae751`, enviado a
`origin/main` (`Erick-vital/procedural-trees`) antes de implementar la rama.
Pintura aprobada y continuación del nuevo blueprint autorizada; se respeta el
paso de aceptación de rama antes de integrar el árbol completo.

Recursos `assets/sauce-pintado/v0.1.0/`: atlas RGBA de cuatro ramillas colgantes
y corteza RGB, ambos 1254², generados con ImageGen a partir del concepto aprobado.
PNG sin retoques, prompts y hashes conservados. Anclajes superiores medidos con
alfa .5, regiones UV ajustadas sin modificar píxeles. Tres planos fijos por grupo,
inclinados .22 rad para conservar presencia desde la punta.

Rama `willow-branch-sample-0.1.0`: primaria arqueada, diez secundarias y once
grupos, **718 tris (652 madera + 66 follaje), dos materiales**. Semillas de
estructura/pintura 7100/2718. Contratos geométricos puros y adaptadores separados;
sin cambios en recetas ni catálogo histórico. En esa entrega aún no había
blueprint completo; integración posterior descrita abajo.

199 pruebas pasan fuera del sandbox; dentro falla únicamente el socket loopback
de la API. Dos exportaciones repetidas idénticas, GLB reimportados y auditados,
37 capturas reales de Godot inspeccionadas. Generación/repetición .816/.766 s,
límites 120 s de generación y 180 s por subproceso de revisión.
[Informe, galería y reproducción](../docs/evidence/sauce-pintado/rama-01/informe.md).

**Rama aprobada por el usuario**, que indica «ok, continua»;
[decisión](../docs/evidence/sauce-pintado/rama-01/user-acceptance.json). Integrar perfil
completo y piloto/tres controles con presupuesto previo ≤6999 tris. La muestra
no acredita el presupuesto ni la plenitud de un árbol entero; no se aprueban por
anticipado el volumen de copa o nuevas edades. F4 sigue pendiente tras el sauce.

## Integración autorizada

Primer perfil adulto de 10 m, semillas base 7100–7103, copa 17 y pintura 2718.
Receta nueva `sauce_colgante@1.0.0`, contrato 1.6 y componentes de estructura,
distribución y representación explícitos. Parámetros cerrados inicialmente.
Madera propia: tronco irregular, primarias anchas arqueadas a diferentes alturas
y secundarias descendentes; follaje en cortinas de tres planos por grupo,
construcción .22 rad y pintura 0.1.0 conservadas de la rama aprobada.

Presupuesto inicial previo a mallar: tronco de doce anillos/ocho lados (188 tris),
cuatro raíces de tres anillos/cinco lados (104), doce primarias de siete
anillos/seis lados (960), 96 secundarias de cuatro anillos/cuatro lados (2688),
423 grupos × seis tris (2538): **cota 6478 tris**, dos materiales. La receta
debe rechazar combinaciones que excedan el límite antes de crear tubos;
la cota no depende de simplificar después ni de retirar grupos por semilla.

Reutilizar infraestructura sin cambiar contratos ni recetas históricas. Medir
desviación de simplificación de primarias con cota de 5 mm, conservar extremos
y UV; secundarias finas, tronco y raíces mantienen sus anillos. Revisar conexiones
y copa/madera reimportadas en Godot. Verificar regresiones de roble, pino,
abedul y columnar, repetición y CLI, entradas inválidas y defectos de exportación.
Entregar piloto y tres controles con visor; no atribuir aprobación artística
al árbol completo por esta autorización. F4 queda pendiente al terminar.

## Resultado del árbol completo — 2026-11-02

`sauce_colgante@1.0.0` integrado en catálogo, resolución, ejecutor, CLI y auditoría;
contrato 1.6, componentes 0.1.0. Adulto 10 m, cuatro semillas 7100–7103 con
copa 17/pintura 2718: **6478 tris cada uno, dos materiales**, 113 recorridos y
423 grupos/1269 planos. Cota previa 6478; no se eliminaron anillos en estos casos.
Recursos y construcción de la rama aprobada conservados.

La revisión inicial de copa completa resultó demasiado escalonada. Ajuste común
de bifurcaciones/arqueado y longitud de grupos a 1.8 m, sin retoques por semilla,
conserva conteos y pintura; copa final ancha y continua. Normalización Z común
fija 10 m sobre madera, sin alterar XY/radios nominales. Vértices/ejes de grupos
a doce decimales evitan diferencias de último bit entre Pythons; auditoría GLB
float32 exacta conservada. Intentos rechazados y límites visuales en el informe.

**208 pruebas**, ocho defectos rechazados, piloto repetido y CLI real con nueve
vistas/GLB idéntico; regresiones roble/pino/abedul/columnar exactas. Generación
1.230–1.286 s sin render. **120 capturas reales Godot inspeccionadas**, con copa,
madera, luces/sombras, distancias y acercamientos. Visor para cuatro semillas.
[Informe, evidencia y reproducción](../docs/evidence/sauce-pintado/arbol-01/informe.md).

**Integración técnica terminada; aceptación artística del árbol completo pendiente.**
Solo perfil adulto de 10 m y cuatro casos verificados. Sin garantía de todas las
semillas/contactos, sin nuevas edades ni benchmark. **F4 queda como pendiente
después de cerrar esta variante**, sujeto a definición/adaptación y decisión de
inicio; no se inicia automáticamente por esta entrega.

## Revisión solicitada tras rechazo artístico — 2026-11-02

El usuario rechaza el árbol completo 1.0.0: eje central extraño, primarias de
forma repetida y copa desnuda arriba. Aporta dos imágenes y solicita inspirarse
en `MikeFernandez-Pro/just-a-simple-tree`, conservando nuestra infraestructura
si es posible. Pintura/rama permanecen aprobadas; el árbol 1.0.0 no se considera
artísticamente aceptado. **F4 sigue pendiente tras cerrar el sauce.**

Nueva receta 1.1.0/componentes 0.2.0 dentro del contrato de sauce 1.6: conservar
receta/algoritmo 1.0.0, PNG, representación de tres planos fijos y ejecución
Python/Blender/Godot. Tronco corto bifurcado sin prolongación central, brazos
con distintas inclinaciones, torsión, longitudes y alturas, ramificación superior
que sostenga masas de follaje y hebras de caída irregular con longitud propia.
Separar relleno de copa y cortinas en la distribución, sin materiales nuevos.

Referencia técnica: `willow.js` del repositorio consultado, brazos que nacen de
tronco corto, masas superiores y sucesión de masas alargadas descendentes. Se
adaptan ideas de estructura/distribución a nuestros atlas; no se traslada su
motor, shader, instanciación, recursos o presupuesto de geometría. No se copia
literalmente código externo. El color cel de las imágenes no implica sustituir
la pintura aprobada ni introducir otro estilo de sombreado en esta revisión.

Perfil propuesto: adulto 10 m, ocho primarias, diez secundarias por primaria,
cinco grupos por secundaria. La fórmula previa compartida da **5734 tris**:
3172 de madera + 427 grupos × 6 (2562), dos materiales. Revisar piloto y tres
controles con semillas originales 7100–7103/17/2718, repetir y comparar con
1.0.0 a igual cámara/luz; no ajustar por semilla. Regresiones históricas y del
propio sauce 1.0.0, auditoría y aceptación artística separadas.

Delegación posterior del usuario: «tal vez sea necesario incluso modificar la
aprobacion anterior de las ramas y crear una nueva, ya lo dejo a tu consideracion».
Se sustituye la muestra para la receta revisada por una rama 0.2.0 seleccionada
por el agente; no se atribuye aprobación explícita del árbol al usuario.

La comparación de las primeras candidatas mostró prolongaciones de follaje como
plumas y una copa aún abierta. Representación 0.2.0: orientación volumétrica,
ancho afín ×1.75–2 en copa y ×.75–1 en hebras, UV/tallo conservados. Se refuerza
la copa con cinco grupos más por primaria y por secundaria de copa: **307 grupos
de copa + 280 de cortina = 587**, 3522 tris de follaje + 3172 de madera =
**6694 tris de cota previa**, dos materiales. Versión de presupuesto 0.2.0
separada; fórmula/receta 1.0.0 permanecen idénticas. Sin cambios de pintura,
motor, ejecutor, API o exportador: solo componentes de especie, su registro y
herramientas de revisión; el adaptador registra la representación versionada.

## Resultado de revisión 1.1.0

Receta 1.1.0/componentes 0.2.0, perfil nominal de madera 10 m, ocho primarias y
ochenta secundarias: **6694 tris/dos materiales en cuatro semillas**, 587 grupos
de tres planos. Tronco corto bifurcado, brazos de controles distintos, 24 ramas
de copa y 56 hebras con caídas diferentes. No se borra la versión 1.0.0, cuyo
resultado artístico quedó rechazado por el usuario.

Nueva rama 0.2.0 elegida por el agente bajo delegación: **804 tris, 74 grupos**,
37 capturas y GLB repetidos idénticos. Sustituye la muestra anterior en esta
receta; no se atribuye aprobación artística explícita del árbol a la delegación.
[Selección y verificación](../docs/evidence/sauce-pintado/rama-02/informe.md).

**214 pruebas**, ocho defectos de exportación rechazados, repetición y CLI real
con nueve vistas/GLB idéntico. Regresiones roble/pino/abedul/columnar y sauce
1.0.0 exactas. **150 capturas Godot**, 120 nuevas inspeccionadas más 30 anteriores
idénticas, comparación a cámara/luz comunes y visor con cuatro semillas.
Generación 1.279–1.433 s sin render, sin benchmark. Se conservan motores,
ejecutor, API, exportador y PNG 0.1.0; componentes/registro y revisión ampliados.
[Resultado, referencia y reproducción](../docs/evidence/sauce-pintado/revision-01/informe.md).

**Revisión 1.1.0 aprobada por el usuario y variante cerrada**: «ok lo apruebo».
[Aceptación final](../docs/evidence/sauce-pintado/revision-01/user-acceptance.json).
Incluye la aplicación al árbol de la rama seleccionada por delegación, en el
perfil y casos presentados; no revierte el rechazo de 1.0.0 ni aprueba abedul.
Se conservan receta, hashes y límites ensayados. **F4 queda como siguiente
pendiente**, sujeto a definición/adaptación a blueprints y decisión de inicio;
no se implementa por esta aprobación. Sin nuevas edades, viento, LOD o estaciones.
