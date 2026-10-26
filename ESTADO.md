# Estado del proyecto

Última actualización: 2026-10-26.

## Situación actual

[Sistema de blueprints](plans/sistema-blueprints.md): **B0–B5 cerrado técnicamente**.
Dos tipos al cierre B5; catálogo ampliado ahora a tres con pino experimental.
Plan activo: [roble pintado](plans/roble-pintado.md): **pintura aprobada; rama
y tres láminas aprobadas; receta 2.1.0 integrada**. Cuatro casos verificados:
piloto/joven/adulto/viejo: 7836/3996/6812/7780 tris.
[Resultado y reproducción](docs/evidence/roble-pintado/implementacion-01/informe.md).
Pino [PP1–PP4](plans/pino-pintado.md) cerrado: **2.3.0 aprobado**, cuatro casos.
Base: [blueprint de pino](plans/blueprint-pino.md), implementado y revisado en
**1.1.0**; revisión artística del usuario pendiente, acículas conservadas allí.
[Comparación y resultados](docs/evidence/blueprints/pino-revision/informe.md).
[Guía de uso](docs/uso-blueprints.md), [cierre B5](docs/evidence/blueprints/b5/informe.md).
Viejo-09 RF3 y perfiles joven/adulto/viejo de B3 revisada aprobados por el usuario.
Aprobación B3 del 2026-10-23, incluida hoja joven .45 m: [decisión](docs/evidence/blueprints/b3-revision/user-acceptance.json).
Copa columnar sigue experimental. **RF5 ejecutada y verificada: 30/30**, receta
1.2.0, diez por edad; **aprobación artística del lote registrada** el 2026-10-23.
[Aceptación RF5](docs/evidence/rediseno-follaje/rf5/user-acceptance.json).
[Informe y galería seleccionada](docs/evidence/rediseno-follaje/rf5/informe.md).

Objetivo v1: treinta robles low-poly reproducibles/exportables a GLB y evaluación
IA para parámetros/reglas/simplificación. Infraestructura F0–F2 verificada;
F4–F6 IA pendientes. F3/bosques, mapa y terreno diferidos.
El [plan v1](plans/v1-generador-arboles.md) conserva ese alcance separado.
[Rediseño de follaje](plans/rediseno-follaje.md): RF3 aprobada; integración B2 y
controles RF4/B3 y lote RF5 verificados y aprobados. **Rediseño cerrado para
la familia ensayada**, como alternativa explícita a Q3.

## Avances verificados

- Pino PP1–PP3: dirección A y cruzadas elegidas; atlas/corteza 0.1.0 y
  materiales Godot verificados. [Pintura](docs/evidence/pino-pintado/pp2/informe.md),
  [materiales](docs/evidence/pino-pintado/pp3/informe.md).
- Roble **2.1.0** integrado: contrato 1.4, tres láminas/6 tris por grupo; atlas
  0.3.0 (2000²)/ocho plantillas fijas, corteza/fuente de pintura 0.2.0 aprobadas.
  Cuatro casos: **7836/3996/6812/7780 tris**, dos materiales, 264 grupos/792 láminas.
  Piloto coincide con candidato aprobado en geometría/UV/normales; GLB repetido
  idéntico. 139 pruebas, regresiones pino/columnar exactas, rehorneado RGBA idéntico
  (metadatos PNG distintos), 144 capturas reales y cinco láminas inspeccionadas.
  Altura nominal sobre madera, bounds completos incluyen márgenes transparentes.
  [Informe, métricas y límites](docs/evidence/roble-pintado/implementacion-01/informe.md).
- PP4 inicial 2.0.0: 241 grupos/5192 triángulos, 110 pruebas y 108 capturas.
  El usuario considera la copa demasiado rala; referencia técnica conservada.
  [PP4 inicial](docs/evidence/pino-pintado/pp4/informe.md).
- PP4 volumen **2.1.0**, distribución/cruzadas 0.2.0: misma regla creciente
  arriba para piloto/tres controles, 435 grupos/**7520 triángulos**, 12 m/dos
  materiales. Madera, atlas y materiales idénticos. 113 pruebas, 43 comprobaciones,
  repetición y regresiones 2.0.0/B0/B4 exactas; 108 capturas reales revisadas.
  Más masa superior y ápice; aprobación artística pendiente.
  [Informe y reproducción](docs/evidence/pino-pintado/pp4-volumen/informe.md).
- Madera/copa **2.2.0**, representación 0.3.0: anillos adaptativos a 5 mm y
  tapas interiores verificadas. Madera **1908–1944**, total **7128–7164** tris.
  435 grupos conservados; ajuste leve posterior .98 longitud/.94 anchura,
  sin mover anclajes; cobertura proyectada 4,1–4,7 % menor. 116 pruebas,
  51 comprobaciones, repetición/regresiones 2.1.0/B0/B4 exactas y 144 capturas
  reales y láminas revisadas. [Informe](docs/evidence/pino-pintado/pp4-madera/informe.md).
- Cruzadas **2.3.0**, representación 0.4.0: **12→6 tris/grupo**, 435 grupos,
  follaje 5220→2610 y total **4518–4554**. Madera/PNG/guías 2.2.0 idénticos.
  Petición posterior: anchura sqrt(.9), longitud/anclajes fijos; −10 % de
  envolvente por grupo (no volumen físico de unión). 119 pruebas y 51 checks;
  repetición y regresiones exactas, 144 capturas reales revisadas. Topología
  aislada: diferencia de máscara ≤0,151 % del área en 36 pares; sin identidad
  absoluta de píxeles. [Informe](docs/evidence/pino-pintado/pp4-laminas/informe.md).
- Benchmark **1.1.0 → 2.3.0**: 24 mediciones Godot/RTX 5060, 1080p/MSAA4/sombras,
  1/128/512 instancias, cuatro repeticiones. 128: 353→589 FPS; 512: 126→228 FPS,
  tiempo por cuadro −40,0/−44,9 %, consistente en cuatro parejas. Un árbol sin
  ganancia útil. Tres pruebas del arnés, auditoría y seis capturas revisadas.
  [Informe, condiciones y reproducción](docs/evidence/pino-pintado/rendimiento-v11/informe.md).
- Pino geométrico 1.0.0/1.1.0: cuatro semillas/12 m, 11924 tris y dos
  materiales, 2892 acículas. Revisión 1.1.0 conserva costes y parámetros con
  raíces desfasadas e inclinaciones mixtas; repetición/regresiones exactas,
  97 pruebas y 144 capturas reales. Aprobación artística pendiente.
  [Base](docs/evidence/blueprints/pino/informe.md),
  [revisión](docs/evidence/blueprints/pino-revision/informe.md).
- B0: referencia RF3 aprobada, congelada y reproducida. 133 archivos auditados,
  105 fuentes recuperables de Git. [Informe](docs/evidence/blueprints/b0/informe.md).
- B1/B2: contratos estrictos, registro, resolución determinista y ejecución
  integrada desde fuentes sin ensayos previos. `roble_copa_ancha` 1.0.0 reproduce
  GLB B0 idéntico y doce vistas Godot idénticas; 70 pruebas.
  [Contrato](docs/contrato-blueprints.md), [B2](docs/evidence/blueprints/b2/informe.md).
- B3 revisada: receta 1.2.0, joven .45 m sin cambiar soportes/raíces; contactos
  contra triángulos reales en float64 y proyección 0.1.1 acotada. 22 éxitos,
  tres rechazos previstos, cuatro repeticiones idénticas, 80 pruebas;
  22 GLB reimportados y 270 capturas reales. Madera/normales/corteza iguales
  a siete Q3; piloto intacto. [Informe](docs/evidence/blueprints/b3-revision/informe.md).
- B4: `arbol_copa_columnar` 1.0.0, 12 m, piloto 4100/controles 4101–4103 y copa 73.
  Reutiliza los tres componentes y ejecutor, sin algoritmo geométrico nuevo.
  Diez generaciones, cuatro repeticiones idénticas, 83 pruebas, 12 GLB Godot
  y 108 capturas. Primer GLB idéntico a B0.
  [Identidad/reutilización](docs/evidence/blueprints/b4/informe.md).
- B5: guía, catálogo y selección histórica explícitos. 85 pruebas y siete
  generaciones CLI en copia sin resultados/evidencia previos; cuatro
  comparaciones exactas, incluida repetición desde manifiesto. Roble/columnar
  idénticos a B0/B4. Alias Q3 y versión explícita idénticos. Sin capturas nuevas.
  [Cierre](docs/evidence/blueprints/b5/informe.md).
- B5: finalización TreeSpec inicializa `files_sha256`; regresión probada y GLB idéntico.
- RF5: treinta casos Q3 con follaje RF3, sin retoques por semilla ni fallos;
  88 pruebas, 74 comprobaciones, tres repeticiones idénticas y viejo-09 igual a B0.
  Madera/normales/corteza iguales a Q3 en treinta GLB; 7920 inserciones válidas
  sobre GLB reimportados. 60 escenas Godot (30 copas/30 maderas), 360 capturas;
  láminas de todos los casos revisadas. Joven/adulto/viejo: 7324/9644/10572
  triángulos. Generación 2.584–3.994 s; receta y componentes intactos.
  Lote completo aprobado por el usuario: conserva su identidad entre semillas.
  [RF5](docs/evidence/rediseno-follaje/rf5/informe.md).
- Base previa: Q1b y Q2 aprobadas; Q2 normaliza solo Z desde madera y conserva
  X/Y/radios. Q3 aprobada; Q3b rechazada. Fusión/addons comparados, sin ganador
  general ni sustitución del generador propio.
  [Q2](docs/evidence/q2/informe.md), [Q3](docs/evidence/q3/informe.md),
  [fusión](docs/evidence/q3-fusion/informe.md), [addons](docs/evidence/comparacion-addons/informe.md).
- RF2/RF3: rama de 144 hojas aprobada; piloto de 9 m, 264 conexiones,
  1584 hojas/10572 tris/3 materiales. [RF2](docs/evidence/rediseno-follaje/rf2-densidad/informe.md), [RF3](docs/evidence/rediseno-follaje/rf3/informe.md).
- Entorno: Blender 5.2.1 LTS `9e2066aef7ef`, Python Blender 3.13.13,
  orquestación 3.14.4, jsonschema 4.19.2, Pillow 12.1.1 y Godot 4.7.2 `ed1daf0bf`.

## Decisiones vigentes

- Receta/perfil/ejemplar separados; semillas explícitas y componentes registrados.
  CLI exige receta y petición; sin selección “latest”. Inicio rápido: roble 1.0.0
  y viejo-09 aprobado. Recetas 1.0.0/1.1.0/1.2.0 del primero conservadas;
  aprobación B3 posterior documentada aparte sin alterar hashes de recetas.
  Columnar y pino geométrico pendientes; pino pintado 2.3.0 aprobado. Contratos 1.1/1.2;
  contratos y recetas históricas 1.0 conservados, componentes no intercambiables.
- B5 resuelve los alias TreeSpec `presets/{joven,adulto,viejo}.json`: ahora
  idénticos a Q3 `presets/v0.4.0/`. Sus contenidos Q3b previos se conservaron
  byte por byte en `presets/v0.4.1/`; `q3b-cases.json` histórico intacto.
  [Decisión y hashes](docs/evidence/blueprints/b5/defaults-decision.json).
- `generate` y API siguen recibiendo TreeSpec; `generate-blueprint`, receta y
  ejemplar. API solo loopback, un servidor por carpeta, sin reintentos.
  `batch` conserva F2 histórico como predeterminado; no es lote RF3/blueprint.
- Techo blueprint: **12500 triángulos/3 materiales**; TreeSpec conserva 10000.
  RF3: hasta 360 grupos/2160 hojas, 8192 muestras y 2048 intentos antes de mallar.
  Columnar declara máximo 337 grupos; solo 300 comprobados geométricamente en B4.
  Generación ≤120 s; pruebas/capturas ≤180 s por subproceso terminable.
- Pino pintado: nuevo alcance permite texturas y sustituir ramillas
  completas para cambiar estilo y reducir triángulos. Conservar recetas históricas;
  madera/benchmark autorizados después; roble 2.1.0 con tres láminas integrado/aprobado; LOD fuera.
  PP4 usa contrato 1.2 y semilla paint separada; canopy identifica el caso histórico
  pero no aleatoriza anclajes. Filtrado/sombras Godot en `painted_pine_asset.gd`.
  Menos triángulos por sí solo no demuestra mejora de rendimiento.
- Referencia RF3: moldes Q3 invisibles, seis rombos por conexión, hoja nominal 1 m.
  Joven 1.2.0 usa .45 m con planificación 1 m y soportes conservados. Columnar
  usa .45 m y planificación .45 m. Sin cambios por semilla ni atribución botánica.
- Perfil/ocupación separados: anchura modifica guías X/Y; peso regional reduce
  su cupo sin reasignación. Rechazar colocaciones fuera de altura no renormaliza
  ni recorta madera. Copa vacía se rechaza (≥24 grupos y una región positiva).
- Contactos: distribución 0.1.1 evalúa triángulos reales en float64; conserva
  proyección dentro de .1 mm, corrige fuera con cota de 1 mm. Mayor corrección B3:
  .534 mm. Ruta 0.1.0 histórica conservada. Semiespacios para raíces en tubos.
- Fuentes/contratos históricos reconstruibles; resultados regenerables ignorados,
  evidencia seleccionada y comandos conservados. Git Q3 `fbe87a4`, etiqueta
  `q3-referencia-0.4.0`; fusión `4fa3d8c`.
- No atribuir mejoras IA sin entradas/condiciones reproducibles. Las métricas de
  ocupación o silueta no acreditan naturalidad, rendimiento o aprobación estética.

## Siguiente paso y pendientes

**Tres láminas implementadas en receta 2.1.0; verificación de cuatro casos terminada.**
La instrucción «ok implementalo con 3 laminas» aprueba la variante del piloto.
Generación por CLI sin resultados previos; plantillas y atlas congelados.

- Galería: `artifacts/roble-pintado/implementacion-02/index.html`; cada caso contiene
  `tree.glb`/`tree.blend`. [Informe](docs/evidence/roble-pintado/implementacion-01/informe.md).
- Usar `blueprints/roble_copa_ancha/2.1.0.json` con ejemplares de
  `presets/blueprints/roble-cruzado/`. [Guía](docs/uso-blueprints.md).
- Piloto aprobado; controles revisados técnicamente/por el agente, sin atribuir
  aprobación artística del usuario. No hay pendientes de integración de esta receta.
- Cambio de representación autorizado: no conserva planos de hojas individuales
  ni identidad IoU .99; copa más tupida. Persisten repetición, trazos de canto,
  costuras de corteza y posibles conexiones ausentes. Sin benchmark de roble.
- Históricos/pino/alias conservados; 2.0.0 es ensayo técnico previo, no pintura aprobada.
- Cambios de roble aún **sin commit**. No iniciar fases adicionales por rutina.

Pino **2.3.0 aprobado y benchmark cerrado**; galería `artifacts/pino-pintado/pp4-cards-02/index.html`.
Base geométrica 1.1.0 en `artifacts/blueprints/pine-v1.1-review-01/`, aceptación pendiente.

RF5 cerrado con aprobación artística del lote completo. Matriz
`configs/verification/rf5-v1.json`; galería
`artifacts/rediseno-follaje/rf5-lote-01/index.html`. RF3 aprobada como alternativa
explícita a Q3; predeterminados conservados. F4 (lenguaje natural a parámetros)
sigue pendiente de decisión de inicio y adaptación a blueprints.
F4–F6 IA pendientes; elegir proveedor/modelo al retomarlas. F5 conserva Q2 solo Z
y radios posiblemente elípticos; comparar con/sin regla conservando ≥90 % de longitud.

Límites: B4 solo ensaya columna de 12 m/cuatro semillas; intervalos completos y otras
edades no garantizados. Caso 2 m/moldes 3 m técnicamente válido pero visualmente
inadecuado. Extremo de 20 m completa 2021/2048 intentos, cerca del límite de trabajo.
Conexiones superpuestas a Q3, sin soldar ni resolver todas las intersecciones;
hojas angulosas/solapadas. FPS solo medidos para pinos; sin viento, LOD ni bosque.

Sin bloqueos técnicos fuera del sandbox. Dentro pueden fallar audio al cerrar
Blender y sockets loopback; ejecución autorizada fuera. Capturas Godot en lotes
de dos escenas, dos dibujos completados por vista.

Referencias regenerables: [operación histórica](docs/operacion-historica.md); evidencia en informes enlazados.
