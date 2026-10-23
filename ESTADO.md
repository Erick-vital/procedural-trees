# Estado del proyecto

Última actualización: 2026-10-22.

## Situación actual

Fase activa: planificación del [rediseño de follaje](plans/rediseno-follaje.md); RF0–RF5 pendientes, sin implementación nueva. F0–F2 verificadas; ramas Q1b y copa Q2 aprobadas. Familia de masas poligonales cerrada como aprobada: Q3 de referencia y fusión parcial en los cuatro casos mostrados, sin superioridad atribuida. Q3b rechazada. F4–F6 pendientes durante el rediseño; F3 diferida.

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
- IoU mínima de silueta 98.33 % sobre cuatro vistas a 192×192 rayos. El usuario considera Q3/fusión casi iguales y acepta cerrar esta familia como aprobada para su estilo. No demuestra un límite absoluto del método, mejora de rendimiento/IA ni aceptación de un lote fusionado completo.
- Addons instalados analizados: Easy Tree 1.0.1 y Sapling 0.3.7, con grafos/código y pruebas pequeñas reproducibles. Sapling: hojas de 4/2 triángulos; siete casos conservan once curvas. Easy Tree: siete hojas y tallo suman 136 triángulos. Sin comparación estética ni validación Godot de esos addons; [informe](docs/evidence/addons-follaje/informe.md).
- Evidencia y reproducción: [fusión Q3](docs/evidence/q3-fusion/informe.md), [Q3](docs/evidence/q3/informe.md), [Q2](docs/evidence/q2/informe.md), [Q1b](docs/evidence/q1b/informe.md), [F2](docs/evidence/f2/informe.md), [README](README.md).

## Decisiones vigentes

- Por solicitud del usuario, el [nuevo plan activo](plans/rediseno-follaje.md) dirige el follaje; el [plan v1](plans/v1-generador-arboles.md) conserva infraestructura/fases pendientes. Familia poligonal aprobada y conservada; sin extender la fusión al lote. [Fundamento del diseño](docs/diseno-follaje.md).
- Secuencia prevista RF0–RF5: objetivo visual → unidad/contrato → rama → copa viejo-09 → controles → integración/lote. Cada ampliación depende de la calidad del resultado anterior. Hipótesis inicial: hojas geométricas opacas; tarjetas solo como alternativa por evaluar. Nada de ello está implementado.
- Madera final Q3 idéntica durante el rediseño; portadores nuevos virtuales, sin madera adicional. Preparar extensibilidad no añade especies a v1. Presupuesto inicial: 10 000 triángulos/3 materiales por árbol; generación y datos intermedios acotados.
- Revisión del plan por addons: portadores con recorrido/inserción/contexto terminal; patrón longitudinal o terminal separado de geometría; densidad por longitud y orientación explícitas. RF2 debe comprobar si el soporte invisible basta; no se aprueban ramillas visibles por esta revisión. Distinguir efectos de textura/recorte y geometría en RF0.
- Política de este archivo actualizada por el usuario: máximo 200 líneas y 16 KiB (16 384 bytes); síntesis vigente, sin acumular bitácora.
- Q3b en `blender/oak_nodes_v41.py`, reutiliza formas Q3 y ensamblado Q2. Fuentes 0.1.0/0.2.0/0.2.1/0.3.0/0.4.0 congeladas. Grafos Python/bpy como fuente; resultados en carpetas nuevas sin sobrescribir referencias.
- Presets principales aún Q3b 0.4.1; no se modifican en este ensayo. Para Q3 usar `presets/v0.4.0/` y `presets/q3-cases.json`. Lotes Q2/Q3 conservados.
- Densidad Q3b: control cuantizado modulado por longitud/radio; máximos tronco/primaria/secundaria 1/3/2, con dos secundarias foliadas de tres por padre. Hasta 85 masas/25 de detalle alto; límite derivado 8956 triángulos/dos materiales. Presupuesto contractual 10 000/3.
- Dos niveles, hasta 12 primarias/36 secundarias. Presets follaje (escala/densidad): joven 0.45 m/0.5, adulto 1.15 m/0.75, viejo 1.30 m/0.75. Escala efectiva acotada a `min(foliage_scale_m,0.24*height_m)`; densidad cero sin hojas.
- Separar contratos, algoritmos, ejecución, evaluación y adaptadores. Radio relativo al basal como regla artística; no es modelo de carga biológica. Volúmenes sumados cuentan solapamientos; rayos 128×128 y dispersión de alturas no miden naturalidad ni IoU.
- F5 debe usar la transformación registrada: normalización solo en Z, radios finales posiblemente elípticos. Comparar estructura Python base/con regla conservando >=90 % de longitud; no exigir space colonization. Q3b no es ese experimento.
- Cámaras compartidas por caso; congelarlas para F6. API solo loopback, un servidor por carpeta, sin reintentos automáticos. Semillas/procedencia explícitas; elegir proveedor/modelo en F4.

## Siguiente paso

Al iniciar ejecución, RF0 del [plan de rediseño](plans/rediseno-follaje.md): referencias/ficha visual y vistas cercana, media y lejana. Aplicar las precisiones del [análisis de addons](docs/evidence/addons-follaje/informe.md). Referencia aprobada: `artifacts/q3/acceptance/lote/`; comparación fusionada: `artifacts/q3-fusion/acceptance/index.html`. RF0–RF5 siguen sin implementar.

## Bloqueos y pendientes

- Sin bloqueos de ejecución fuera del sandbox. Dentro, Blender puede bloquearse al cerrar por audio y HTTP no admite loopback; usar ejecución autorizada fuera y tiempos límite.
- Aprobación visual limitada al estilo/resultados mostrados; extremos sin aprobación estética general. El rediseño no tiene representación ni objetivo visual definitivo elegidos. Diferenciar otros árboles requerirá considerar arquitectura, no solo cambiar hojas.
- Easy Tree usa asignación histórica de sockets que falla en Blender 5.2.1; el grafo evaluó con API actual. No se reparó ni se incorpora como dependencia. Addons intactos; reproducir inspección con `scripts/review_tree_addons.py`.
- Una discrepancia intermedia de un triángulo GLB se corrigió limpiando aristas residuales; los cuatro finales pasan. Sin bloqueos actuales. No se validan extremos ni lote para la fusión; tercer nivel y anticolisiones siguen sin implementar. F4–F6 y rendimiento del bosque pendientes/diferidos.
