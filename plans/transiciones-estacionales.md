# Transiciones pintadas y normales de copa

Fecha: 2026-11-01; actualización 2026-11-02. **T0–T6 cerradas y aprobadas artísticamente en sus ámbitos; lote aprobado.**
Continuación del [plan de estaciones](estaciones.md), con ideas del
[estudio de just-a-simple-tree](../docs/evidence/estaciones/referencia-just-a-simple-tree/informe.md).
El usuario autorizó T0–T3; el 2026-11-02 aprobó la valoración artística de T3
y pidió continuar con T4. Después autorizó cualquiera de sus candidatas y T5;
se seleccionó .35 por menor desviación. El usuario solicitó T6, cerrada con
[entrega y decisiones separadas](../docs/entrega-transiciones.md).

## Objetivo y alcance

Crear una transición continua verano–otoño que conserve la pintura y cambie
progresivamente entre grupos de follaje. Evaluar por separado normales de volumen
para mejorar la lectura de copa sin aumentar triángulos. Primera especie: roble
pintado 2.2.0; arquitectura reutilizable, comportamiento de especie explícito.

La primera entrega mantiene la copa completa. Brotación, invierno, marcescencia,
caída, partículas, viento, LOD y otras especies quedan diferidos. Tampoco se
traslada el barrido en pantalla de la demo ni se cambia el estilo a cel shading.
Las normales pueden rechazarse y cerrarse como ensayo sin impedir las estaciones.

## Referencias y límites que se conservan

- Piloto viejo-09, semillas base/copa/pintura **3009/17/2718**. Controles:
  joven-07 **1007/17/2718**, adulto-00 **2000/17/2718**, viejo-00 **3000/17/2718**.
- 264 grupos, tres láminas por grupo; **6812/3132/5820/6900 tris** respectivamente.
  Máximo **6999 tris y dos materiales** por árbol: madera y follaje compartido.
- Receta base `blueprints/roble_copa_ancha/2.2.0.json`, atlas de verano 0.3.0,
  pintura otoñal experimental `assets/roble-otono-pintado/v0.1.0/` y corteza 0.2.0.
- Preservar versiones, recursos y GLB históricos; shader de tinte 1.0.0 como
  control experimental. Commit previo a la pintura: `4187776`.
- Pintura compatible/aplicación/calendario del piloto T3 **aprobados artísticamente**
  el 2026-11-02: [decisión](../docs/evidence/estaciones/mezcla-t3/user-acceptance.json).
  No aprueba por anticipado normales T4 ni la integración de cuatro casos T5.
- Madera, posiciones de follaje, índices, UV, soportes, tamaño y distribución
  permanecen iguales. Solo el ensayo de normales puede cambiar normales de follaje.
- Dos materiales no significa dos texturas: medir el coste de los dos atlas de
  follaje más corteza, memoria/mipmaps y muestras de textura. Recursos ≤2048².
- Generación ≤120 s; cada subproceso de revisión/prueba ≤180 s y terminable.

## Arquitectura prevista

| Capa | Responsabilidad |
| --- | --- |
| Contratos | Perfil estacional versionado, recursos/hashes, límites y datos por grupo. |
| Algoritmo puro | Orden, exposición aproximada, vecindad, curvas y normales candidatas. |
| Ejecución | Resolver receta/semillas, generar datos y empaquetar variante derivada. |
| Blender/GLB | Transportar atributos, atlas y normales; auditar exportación reimportada. |
| Godot | Mezclar pinturas y aplicar fase; visor y estado por instancia. |
| Evaluación | Determinismo, invariantes geométricos y revisión visual reproducible. |

Crear contrato nuevo en lugar de relajar `seasons.py` 1.0.0, que actualmente
valida un perfil fijo de tinte. `seasonal_paint.py` conserva su operación histórica
de sustituir PNG. Nombres/rutas nuevas se fijarán al cerrar T1; no se presuponen
archivos implementados por aparecer en este plan.

## T0 — Congelar referencias y protocolo

1. Auditar fuentes, recetas y recursos disponibles; regenerar referencias si
   faltan. Guardar hashes, versiones, semillas y comandos de reproducción.
2. Registrar estado visual base, ambas pinturas y shader experimental con igual
   cámara, exposición, luz, filtrado, alfa y rugosidad. El ensayo anterior tenía
   rugosidades .88/.95: esta comparación aislará esa variable.
3. Fijar fase `p∈[0,1]`: **solo verano→otoño con copa llena**, no año completo.

**Salida/aceptación:** referencias reproducibles para los cuatro casos y protocolo
de comparación. Sin declarar aprobada la pintura ni modificar históricos.

## T1 — Contrato y calendario determinista por grupo

1. Perfil de roble explícito: extremos pintados, semilla estacional separada,
   distribución de inicios/duraciones, pesos de exposición y correlación local.
   Admitir únicamente especie/fase implementadas; rechazar NaN, rangos inválidos,
   hashes erróneos, grupos duplicados y presupuestos excesivos antes de mallar.
2. Calcular exposición una vez por ejemplar, mediante vecindad de los volúmenes
   existentes y muestreo acotado. Primera cota: ≤360 grupos, ≤24 vecinos y ≤12
   direcciones por grupo; registrar versión. No depende de la cámara ni de cada
   cuadro. Es una aproximación artística, no una simulación de radiación solar.
3. Derivar azar del hash de semilla+ID estable, separado de estructura/pintura.
   Combinar exposición y variación correlacionada por vecindad. Evitar que
   reordenar entradas cambie el resultado; desempatar por ID.
4. Cada grupo recibe `start`, `duration` y datos de exposición/variación; sus
   tres láminas comparten calendario. Mezcla local:
   `w = smoothstep(start, start + duration, p)` con `0≤start<start+duration≤1`.
   En p=0 todos muestran verano; en p=1 todos alcanzan la pintura otoñal elegida.
5. Prototipar atributos de vértice para transportar esos valores, manteniendo
   UV de pintura. Verificar identidad grupo→vértices tras exportar/reimportar;
   no confiar en el orden interno de vértices de Blender/glTF/Godot. No agregar
   superficies ni un material por grupo. Si hace falta separar vértices, registrar
   su coste sin cambiar caras. No usar datos de calendario como tinte accidental.

**Salida/aceptación:** contrato, datos y pruebas de determinismo, extremos,
monotonía, límites, orden de entradas y coherencia de tres láminas. Atributos
importados y correspondencias auditados antes de animar.

## T2 — Preparar atlas compatibles y ensayar prevención de halos

1. Comprobar que los dos atlas comparten cuadrícula, plantillas, UV y resolución.
   Registrar diferencias actuales de máscara: el atlas otoñal no tiene alfa idéntica.
2. Preparar recursos nuevos compatibles, sin sobrescribir pintura original:
   usar **una máscara común derivada del verano** para toda la transición. Mantener
   los RGB de ambas pinturas y comprobar cobertura de color bajo esa máscara.
   El extremo otoñal compatible es una variante nueva, no idéntica al PNG 0.1.0.
3. Ensayar extensión de RGB bajo transparencia, sin alterar alfa ni texeles
   visibles. Acotar padding por celda para no contaminar plantillas vecinas.
   Comparar con/sin tratamiento en minificación y fondos claro/oscuro; conservar
   solo si evita halos sin costuras nuevas. No copiar código sin registrar MIT.
4. Mostrar las hojas y una rama del piloto con ambos extremos compatibles;
   conservar vista del otoño 0.1.0 para juzgar el pequeño cambio de recorte.

**Salida/aceptación:** atlas/manifiestos versionados, alfa común exacta y hashes;
rehorneado repetible. Presentar pintura/rama antes de adoptar el árbol en producción.
Una corrección artística importante vuelve a esta fase, sin ajustar por semilla.

## T3 — Mezcla pintada en Godot y piloto

1. Nuevo material de follaje mezcla **RGB de los dos atlas en espacio lineal**
   con `w`; usa alfa común, recorte .5, doble cara y mipmaps explícitos. Corteza
   intacta. No sustituir la pintura por otra recoloración del shader antiguo.
2. Actualizar solo fase/tiempo durante la animación; no reconstruir mallas,
   texturas ni vecindad cada cuadro. Fase determinista, reversible y consultable
   directamente: saltar de .9 a .2 debe dar el mismo estado que empezar en .2.
3. Mantener fase independiente por árbol. Compartir material cuando el transporte
   lo permita; no hacer que mover un deslizador cambie otros ejemplares por error.
4. Visor con deslizador, reproducción/pausa, avance inverso y comparación entre
   pinturas fijas, mezcla uniforme, calendario por grupo y shader antiguo.

**Salida/aceptación:** piloto revisable, ambos extremos correctos y pintados;
transición sin saltos evidentes, sin desarmar cruzadas ni hacer variar alfa.
Capturas de p=0/.25/.5/.75/1 y secuencia a pasos 1/120, ida y vuelta, con cámara
fija y orbital. Registrar cualquier parpadeo; métricas estáticas no bastan.

## T4 — Normales de volumen, ensayo aislado

1. Comparar normales originales con normales de volúmenes locales de copa,
   obtenidos de grupos y vecindad existentes. Evaluar mezcla acotada con la normal
   original. Evitar una esfera global que borre lóbulos/asimetría del roble.
2. Generar normales finitas/unitarias con tratamiento de centros degenerados y
   reversos. No doblar/subdividir láminas. Madera, posiciones, UV e índices exactos.
3. Primero rama/piloto con verano fijo; después pintura otoñal fija. Comparar
   normales y calendario por separado antes de combinarlos, con igual material.
4. Revisar seis orientaciones, cerca/media/lejos y tres direcciones de luz;
   incluir sombras sobre suelo y propias. Revisar también normales exportadas
   con material estándar, sin depender del shader para simularlas.

**Salida/aceptación:** candidata opcional con evidencia geométrica y visual.
La adopción exige valoración artística: si aplana la copa, muestra reversos
extraños o no convence, conservar normales originales y registrar el rechazo.

## T5 — Cuatro casos, portabilidad e integración candidata

1. Aplicar reglas comunes al piloto y tres controles, sin retoques por semilla.
   Probar estados/saltos/reversión, luz, sombras, distancias y fondos; auditar
   grupos, caras, materiales y recursos sobre GLB reimportados y escena Godot.
2. Exportar extremos estáticos con pinturas compatibles embebidas y materiales
   estándar. Usar normales originales o candidata explícita; conservar ambos
   ensayos. Verificar resultados en Godot y Blender, sin prometer identidad de luz.
3. Mantener calendario/semillas en manifiesto portable; explicar que la transición
   requiere adaptador de ejecución. **Un estado intermedio con mezcla distinta
   por grupo no cabe automáticamente en un atlas único compartido.** Exportarlo
   estáticamente sin shader requiere un diseño adicional, fuera de esta entrega;
   no crear materiales por grupo ni exceder 2048² para ocultar esa limitación.
4. Comparar hashes de rutas históricas al tocar infraestructura compartida.
   Integrar solo como variante explícita versionada, sin sustituir alias o receta
   aprobada. Separar candidatas técnicas de la adopción artística del usuario.

**Salida/aceptación:** cuatro casos <7000 tris y dos materiales, datos y extremos
reproducibles, memoria/texturas registradas, exportaciones auditadas, visor común
y selección visual revisada. No atribuir mejora de FPS sin benchmark separado.

## T6 — Cierre y decisión de continuación

Entregar informe, galería/secuencia, comandos reales, perfiles, fuentes/hashes,
GLB de extremos y paquete Godot. Actualizar `docs/estaciones.md`, este plan y
`ESTADO.md` dentro de 200 líneas/16 KiB. Registrar aceptación/rechazo de pintura,
calendario y normales por separado; no deducir una de otra.

La siguiente fase posible es estudiar caída del roble: granularidad de grupos,
máscaras internas, conexiones visibles y presupuesto de madera cuando falte copa.
Se definirá aparte; este plan no implementa caída, partículas ni un año completo.

## Orden de trabajo y estado

**T0–T6 cerradas técnicamente.** La selección artística de
T4 es **.35**, autorizada por delegación del usuario; T5 conserva originales como control.
[Resultado T0/T1](../docs/evidence/estaciones/calendario-t01/informe.md): cuatro
referencias, contrato 1.0, calendario 0.1.0 y transporte UV2. 27 pruebas, 37
comprobaciones y 80 capturas reales; 20 pares original/con datos idénticos.
[Resultado T2](../docs/evidence/estaciones/atlas-t2/informe.md): atlas 0.1.0
con alfa común exacta y padding RGB de 16 px por celda; 181 pruebas y 72
capturas Godot. Hojas y rama primaria 100 del piloto revisadas técnicamente;
en ese momento pintura/rama pendientes de aceptación artística; la pintura
compatible y aplicación del piloto fueron aprobadas después en T3.
[Resultado T3](../docs/evidence/estaciones/mezcla-t3/informe.md): piloto con mezcla
lineal, alfa común y fase/modo por instancia; visor con pausa/retroceso y cinco
comparaciones. 185 pruebas/517 capturas, extremos estándar y reversión exactos.
Secuencias fija/orbital revisadas por cuadros; cantos/cambios de visibilidad al
girar conservados. **Arte T3 aprobado** por el usuario el 2026-11-02;
[decisión](../docs/evidence/estaciones/mezcla-t3/user-acceptance.json). No aprueba T4/T5 por anticipado.
[Resultado T4](../docs/evidence/estaciones/normales-t4/informe.md): campos locales,
originales/.35/.65; geometría intacta y material estándar. 191 pruebas, 16 checks,
793 capturas; seis orientaciones, tres distancias/luces, verano/otoño y sombras.
Blender introduce hasta .469° de desviación de normales; vuelta aproximada auditada.
Normales **.35 seleccionadas/aprobadas** por delegación del usuario:
[decisión](../docs/evidence/estaciones/normales-t4/user-acceptance.json). Originales conservadas como control.
[Resultado T5](../docs/evidence/estaciones/integracion-t5/informe.md): candidata
0.1.0, reglas comunes, cuatro presupuestos intactos; 194 pruebas y 2377 capturas
más cuatro en copia limpia. 16 extremos estándar Blender/Godot, visor común y
ZIP autocontenido; dos materiales y tres texturas compartidas. Máscaras,
extremos y reversión exactos bajo protocolo. Revisión visual técnica completa;
aceptación artística del conjunto separada, sin ampliar especies, estaciones
o caída de hojas.

Precisiones de T0/T1: se igualan ajustes de alfa pero se conservan máscaras
históricas distintas hasta T2. Exposición inicial es apertura geométrica
isotrópica, no iluminación solar. La compresión del importador Godot exige
asociación por geometría/UV con cota y unicidad; no igualdad de índices.
Rutas y codificación definitivas en el
[contrato de calendario](../docs/contrato-calendario-estacional.md).


## Cierre T6 — 2026-11-02

[Entrega y uso](../docs/entrega-transiciones.md),
[auditoría](../docs/evidence/estaciones/cierre-t6/informe.md),
[decisiones separadas](../docs/evidence/estaciones/cierre-t6/decisions.json).
Fuentes y entradas congeladas archivadas (266 archivos); reconstrucción en copia
aislada produce manifiesto, proyecto Godot y 16 extremos idénticos a T5.
Galería/secuencias, perfil, inventario/hashes y paquetes disponibles. T5 y sus
referencias históricas conservados. ESTADO dentro de 200 líneas/16 KiB.

Pintura compatible/calendario del piloto aprobados en T3 y normales .35 aprobadas
por delegación en T4. Posteriormente el usuario **aprueba los cuatro casos**:
[aceptación final](../docs/evidence/estaciones/cierre-t6/user-acceptance.json).
Decisión operativa: conservar variante explícita 0.1.0 aprobada sin cambiar
alias ni iniciar otra fase. Caída del roble queda como estudio posible sujeto a
nuevo alcance; no se implementa por el cierre. Sin benchmark de FPS.
