# Estado del proyecto

Última actualización: 2026-10-23.

## Situación actual

Fase activa: RF3 del [rediseño de follaje](plans/rediseno-follaje.md).
Primera copa completa de viejo-09 implementada y verificada técnicamente en
Godot; revisión de imágenes reales realizada y **aprobación artística pendiente**.
RF4/RF5 sin iniciar. La rama RF2 de 144 hojas está aprobada por el usuario.
Techo del rediseño: 12500 triángulos y tres materiales por árbol.

Objetivo v1: treinta robles low-poly reproducibles y exportables a GLB, con
inspección Godot y evaluación de IA para parámetros/reglas/simplificación.
F0–F2 verificadas; experimentos IA F4–F6 pendientes. F3/bosques, mapa y terreno
siguen diferidos. El [plan v1](plans/v1-generador-arboles.md) conserva su alcance.

## Avances verificados

- Entorno: Blender 5.2.1 LTS `9e2066aef7ef`, Python Blender 3.13.13, ejecutor
  3.14.4, jsonschema 4.19.2 y Godot 4.7.2 `ed1daf0bf`.
- Infraestructura F0–F2: contratos estrictos, grafos propios, CLI/API local,
  timeout, manifiestos con parámetros/semillas/hashes y exportación GLB/Godot.
  [Informe F2](docs/evidence/f2/informe.md), comandos en [README](README.md).
- Estructura Q1b y copa Q2 aprobadas. Q2 conserva madera X/Y y normaliza Z
  usando solo madera: semilla/densidad/escala de follaje no alteran su geometría.
  [Q1b](docs/evidence/q1b/informe.md), [Q2](docs/evidence/q2/informe.md).
- Familia poligonal aprobada: Q3 y fusión parcial en cuatro casos, sin
  superioridad atribuida ni aprobación de lote fusionado. Q3b rechazada.
  La fusión conserva base/distribución y verifica GLB/Godot/repetición/silueta,
  sin demostrar un límite general de métodos basados en esferas.
  [Q3](docs/evidence/q3/informe.md), [fusión](docs/evidence/q3-fusion/informe.md),
  [Q3b](docs/evidence/q3b/informe.md).
- Easy Tree 1.0.1 y Sapling 0.3.7 se compararon con Q3: seis modelos, 36
  capturas y repeticiones idénticas. El usuario decidió continuar con el
  generador propio: volumen Q3, conexiones y hojas. Addons intactos, sin
  dependencia de producción ni ganador artístico general.
  [Comparación y esfuerzo](docs/evidence/comparacion-addons/informe.md).
- RF0/RF1 fijaron referencias, viejo-09, primaria 100, cámaras, materiales,
  procedencia y contrato de unidades. RF2 original y revisión de ramillas
  verificaron hojas/conexiones, pero su volumen fue insuficiente.
  [RF0/RF1](docs/evidence/rf0-rf1/informe.md), [RF2 original](docs/evidence/rf2/informe.md),
  [ramillas](docs/evidence/rediseno-follaje/rf2-ramillas/informe.md).
- Moldes RF2 0.1.1: nueve masas Q3 invisibles, muestreo por área y descarte
  de interiores. Hexágonos .45/.8 m y rombos .8/1 m; 43 pruebas, once GLB y
  72 capturas. [Informe](docs/evidence/rediseno-follaje/rf2-moldes/informe.md).
- Densidad RF2 0.1.2: 96/120/144/192 hojas de 1 m, originales y conexiones
  intactas; 45 pruebas, nueve GLB, 60 capturas y dos repeticiones. El usuario
  aprueba 144 como referencia para RF3. [Aceptación con hashes](docs/evidence/rediseno-follaje/rf2-densidad/aceptacion.json),
  [informe](docs/evidence/rediseno-follaje/rf2-densidad/informe.md).
- RF3 `foliage-canopy-0.1.0`: madera Q3 completa, 45 piezas/5292 triángulos,
  y 89 moldes/3220 triángulos guía. Pool global de 8192 muestras: 2948 expuestas,
  5244 interiores descartadas en el piloto. Reparto por área expuesta
  norte/este/sur/oeste: 66/70/65/63 grupos. Moldes excluidos del GLB.
- Piloto RF3: **264 conexiones, 1584 hojas, 10572 triángulos, tres materiales,
  altura 9 m**. Madera, polígonos/sombreado, transformación, parámetros base,
  semillas y corteza conservados. Posiciones/normales exportadas de madera y
  material coinciden con el GLB Q3 original; repetición idéntica.
- RF3: 51 pruebas, siete GLB y 60 capturas Godot. Perfil ×1.12 cambia anchura
  con igual coste; ocupación este ×.4 baja 70→28 grupos y total 9732, conservando
  las otras regiones. Hoja .75 m conserva conexiones, raíces, ejes y conteo.
  Otra semilla cambia follaje sin alterar la base.
- Revisión real RF3: copa con presencia y lectura distinta de masas cerradas,
  legible a varias escalas; persisten hojas grandes/angulosas y solapamientos.
  Cobertura proyectada Q3 91.7–94.0 %, IoU 83.9–87.6 %: diagnósticos, sin
  aprobación estética automática. Sin recortes en nueve vistas generales;
  tres detalles intencionadamente recortados. [Informe](docs/evidence/rediseno-follaje/rf3/informe.md).

## Decisiones vigentes

- Conservar por ahora la geometría actual de los árboles, incluido el tronco,
  sin reducción de polígonos ni sustitución de hojas por tarjetas texturizadas.
  Evaluar la optimización al integrar en el motor, con mediciones de rendimiento;
  reducir triángulos por sí solo no acredita una mejora. Decisión del usuario
  del 2026-10-23; no cambia la aprobación artística pendiente de la copa RF3.
- Seguir RF0–RF5: objetivo → unidad → rama → copa → controles → integración/lote.
  La aprobación RF2 es de rama; la copa necesita revisión propia antes de RF4.
  No promover presets ni generar lote por pasar métricas.
- Regla RF3: moldes Q3 invisibles, rombo opaco nominal de 1 m (±10 %), seis
  hojas por conexión recta, protocolo RF2 de raíces/giro/inclinación.
  Madera Q3 inmutable; no remodelar tronco/ramas ni añadir especies.
  Identificar y contar por separado las conexiones nuevas.
- Techo autorizado: 12500 triángulos/3 materiales. Los 7208 disponibles de
  viejo-09 se reparten globalmente; no copiar el límite de rama RF2 en cada
  rama. RF3: máximo 360 grupos/2160 hojas, 8192 muestras y 2048 intentos de
  conexión antes de mallar. [Contrato RF3](docs/contrato-rf3-copa.md).
- Perfil/ocupación separados: anchura transforma solo guías X/Y; peso regional
  reduce su cupo sin reasignarlo. Rechazar grupos fuera de altura conserva
  base y hojas, sin recortar ni renormalizar. El control exclusivo de tamaño
  usa escala piloto congelada para planificar y conservar soportes.
- `mesh_report`/validación GLB aceptan techo RF3 explícito; **10000 sigue como
  valor por defecto histórico**, con regresión. Contratos RF1/RF2 y TreeSpec/
  presets históricos intactos; integración normal del estilo en RF5.
- Para Q3 0.4.0 usar `presets/v0.4.0/` o `presets/q3-cases.json`. Los presets
  principales aún usan Q3b 0.4.1 rechazada; resolver promoción en RF5.
  Fuentes algorítmicas históricas congeladas, resultados en carpetas nuevas.
  Git previo: `fbe87a4`, etiqueta `q3-referencia-0.4.0`; fusión en `4fa3d8c`.
- Fuentes ejecutadas RF2 0.1.0/0.1.1/0.1.2 conservadas junto a sus ensayos en
  `artifacts/rediseno-follaje/`, además de hashes. Conservar referencias y
  evidencia seleccionada; resultados regenerables ignorados.
- Separar contratos, algoritmos, ejecución, evaluación y adaptadores.
  Semillas estructural/follaje separadas; no atribuir mejoras IA sin entradas
  comparables. Ocupación/silueta no prueban naturalidad ni FPS.
- F5 futuro: conservar normalización solo Z de Q2 y radios finales posiblemente
  elípticos; comparar estructura Python con/sin regla manteniendo al menos
  90 % de longitud. Q3b y este rediseño no sustituyen ese experimento.
- API solo loopback, un servidor por carpeta, sin reintentos automáticos.
  Generación ≤120 s; verificaciones/capturas ≤180 s por proceso terminable.
  Elegir proveedor/modelo al retomar F4 de infraestructura.

## Siguiente paso

Revisar la copa piloto RF3 y fijar configuración antes de RF4. Galería:
`artifacts/rediseno-follaje/rf3-acceptance-02/index.html`. GLB:
`artifacts/rediseno-follaje/rf3-acceptance-02/pilot/tree.glb`.
Si se aprueba, RF4 comprobará viejo-00/03, adulto-00, joven-00 y tres semillas
reservadas por edad, elegidas antes de generar, sin ajustes ocultos por caso.
La aceptación del árbol completo y su extensión a otras edades están pendientes.

## Bloqueos y pendientes

- Sin bloqueos de ejecución fuera del sandbox. Dentro pueden fallar audio al
  cerrar Blender y sockets loopback; usar ejecución autorizada fuera. Capturas
  en lotes de dos escenas, dos dibujos completados por vista.
- Primera verificación RF3 detenida en perfil ancho por falso rechazo RF2:
  rayo casi paralelo >.15 m dentro del tubo. RF3 comprueba semiespacios de sus
  ocho caras convexas; todas las raíces quedan dentro. La geometría del piloto
  antes/después es idéntica. Detalle en el informe.
- RF3 solo ensaya viejo-09. Conexiones superpuestas a Q3, sin soldar ni resolver
  todas las intersecciones; hojas grandes/angulosas en detalle. Sin prueba de
  FPS, viento, LOD, bosque ni generalización a otras edades.
- RF4: extremos/densidad cero, controles reservados y otras edades pendientes.
  RF5: contrato integrado, promoción explícita y lote de treinta. F4–F6 de
  infraestructura y F3/bosques siguen pendientes/diferidos.
- `ESTADO.md` es síntesis vigente, máximo 200 líneas y 16384 bytes. Mantener
  detalle en planes/informes, sin acumular bitácora ni conversaciones.
