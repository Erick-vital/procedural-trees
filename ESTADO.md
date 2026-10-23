# Estado del proyecto

Última actualización: 2026-10-22.

## Situación actual

Fase: F0–F2 verificadas; ramas Q1b 0.2.1 y copa ajustada Q2 0.3.0 aprobadas. Q3 0.4.0 es la última iteración buena según el usuario; Q3b 0.4.1 rechazada estéticamente. Ensayo de fusión parcial Q3 verificado en cuatro casos; valoración del usuario pendiente. F4–F6 pendientes; F3 diferida.

Objetivo v1: 30 robles low-poly reproducibles y exportables a GLB, inspeccionados en Godot; evaluar IA para parámetros, reglas espaciales y simplificación. Bosque, mapa y terrenos variados se reservan para otro proyecto.

## Avances verificados

- Entorno: Blender 5.2.1 LTS `9e2066aef7ef`, Python Blender 3.13.13, ejecutor 3.14.4, jsonschema 4.19.2, Godot 4.7.2 `ed1daf0bf`.
- F0–F2: contrato estricto, grafos propios, CLI/API local, timeout, manifiestos, GLB y comparaciones. Q1 fue rechazada por estrecha; Q1b recuperó extensión/grosor y tres secundarias por primaria, con ramas aprobadas.
- Q2 conserva estructura nativa Q1b y geometría X/Y; normaliza Z usando solo madera. Semilla, densidad y escala de follaje no alteran la madera final. Copa ajustada aprobada por el usuario.
- Q3 tiene seis familias deformadas y tamaños/cantidades variables. Q3b conserva su madera y formas, pero reduce/aparta follaje y deja una secundaria sin hojas por primaria; su apertura fue rechazada. Sus treinta GLB, repetición, parámetros y extremos pasaron técnicamente: [informe Q3b](docs/evidence/q3b/informe.md).
- Git inicializado: commit previo al ensayo `fbe87a4`, etiqueta `q3-referencia-0.4.0`; fuentes y evidencia seleccionada versionadas. `.gitignore` excluye resultados regenerables, cachés y configuración privada.
- Fusión `q3-partial-fusion-0.2.1`: piloto viejo-09 y controles viejo-00/03 y adulto-00. Unión por vóxeles de hasta tres subárboles vecinos, suavizado y simplificación con presupuesto de entrada; sin cambiar distribución ni tamaños iniciales.
- Los cuatro conservan madera X/Y/Z, polígonos/sombreado y malla Q3 de entrada completa con atributos, parámetros, semillas, estructura y normalización. Archivos originales y fuentes históricas intactos; cámaras históricas y nuevas tomas inferiores/distantes congeladas, iluminación compartida por pareja.
- Cuatro candidatos GLB válidos: 6982–8512 triángulos/dos materiales. Ocho bases/candidatos importados y capturados en Godot. Q3 y fusión viejo-09 se repiten con geometría idéntica. Dieciocho pruebas existentes aprobadas y verificación independiente de mallas guardadas.
- IoU mínima de silueta 98.33 % sobre cuatro vistas a 192×192 rayos. El agente revisó las seis vistas y capturas Godot: cambio moderado, persisten lóbulos/piezas reconocibles; diferencia lejana pequeña. No implica aceptación estética ni mejora de rendimiento/IA.
- Evidencia y reproducción: [fusión Q3](docs/evidence/q3-fusion/informe.md), [Q3](docs/evidence/q3/informe.md), [Q2](docs/evidence/q2/informe.md), [Q1b](docs/evidence/q1b/informe.md), [F2](docs/evidence/f2/informe.md), [README](README.md).

## Decisiones vigentes

- Un único [plan v1](plans/v1-generador-arboles.md). Q3 sigue como referencia visual; Q3b rechazada. La fusión es un ensayo acotado sin promoción ni extensión al lote; F4–F6 siguen pendientes.
- Q3b en `blender/oak_nodes_v41.py`, reutiliza formas Q3 y ensamblado Q2. Fuentes 0.1.0/0.2.0/0.2.1/0.3.0/0.4.0 congeladas. Grafos Python/bpy como fuente; resultados en carpetas nuevas sin sobrescribir referencias.
- Presets principales aún Q3b 0.4.1; no se modifican en este ensayo. Para Q3 usar `presets/v0.4.0/` y `presets/q3-cases.json`. Lotes Q2/Q3 conservados.
- Densidad Q3b: control cuantizado modulado por longitud/radio; máximos tronco/primaria/secundaria 1/3/2, con dos secundarias foliadas de tres por padre. Hasta 85 masas/25 de detalle alto; límite derivado 8956 triángulos/dos materiales. Presupuesto contractual 10 000/3.
- Dos niveles, hasta 12 primarias/36 secundarias. Presets follaje (escala/densidad): joven 0.45 m/0.5, adulto 1.15 m/0.75, viejo 1.30 m/0.75. Escala efectiva acotada a `min(foliage_scale_m,0.24*height_m)`; densidad cero sin hojas.
- Separar contratos, algoritmos, ejecución, evaluación y adaptadores. Radio relativo al basal como regla artística; no es modelo de carga biológica. Volúmenes sumados cuentan solapamientos; rayos 128×128 y dispersión de alturas no miden naturalidad ni IoU.
- F5 debe usar la transformación registrada: normalización solo en Z, radios finales posiblemente elípticos. Comparar estructura Python base/con regla conservando >=90 % de longitud; no exigir space colonization. Q3b no es ese experimento.
- Cámaras compartidas por caso; congelarlas para F6. API solo loopback, un servidor por carpeta, sin reintentos automáticos. Semillas/procedencia explícitas; elegir proveedor/modelo en F4.

## Siguiente paso

Revisión del usuario de [piloto en seis vistas](docs/evidence/q3-fusion/pilot-all-views.jpg) y [controles Godot](docs/evidence/q3-fusion/controls-godot.jpg). Comparación completa: `artifacts/q3-fusion/acceptance/index.html`; candidatos `<caso>/candidate/tree.glb`. Referencia: `artifacts/q3/acceptance/lote/`. No iniciar otra técnica ni el lote antes de valorar este resultado.

## Bloqueos y pendientes

- Sin bloqueos de ejecución fuera del sandbox. Dentro, Blender puede bloquearse al cerrar por audio y HTTP no admite loopback; usar ejecución autorizada fuera y tiempos límite.
- Q3b rechazada por el usuario por empeorar el árbol; no confundir sus verificaciones técnicas con aceptación visual. Q3 conserva margen de mejora en piezas reconocibles, solapamientos y transiciones entre masas. Extremos sin aprobación estética general.
- Una discrepancia intermedia de un triángulo GLB se corrigió limpiando aristas residuales; los cuatro finales pasan. Sin bloqueos actuales. No se validan extremos ni lote para la fusión; tercer nivel y anticolisiones siguen sin implementar. F4–F6 y rendimiento del bosque pendientes/diferidos.
