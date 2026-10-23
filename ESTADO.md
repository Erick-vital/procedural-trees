# Estado del proyecto

Última actualización: 2026-10-22.

## Situación actual

Fase: F0–F2 verificadas; ramas Q1b 0.2.1 y copa ajustada Q2 0.3.0 aprobadas por el usuario. El usuario identifica Q3 0.4.0 como última iteración buena y rechaza estéticamente Q3b 0.4.1, aunque pasó la verificación técnica. F4–F6 pendientes; F3 diferida.

Objetivo v1: 30 robles low-poly reproducibles y exportables a GLB, inspeccionados en Godot; evaluar IA para parámetros, reglas espaciales y simplificación. Bosque, mapa y terrenos variados se reservan para otro proyecto.

## Avances verificados

- Entorno: Blender 5.2.1 LTS `9e2066aef7ef`, Python Blender 3.13.13, ejecutor 3.14.4, jsonschema 4.19.2, Godot 4.7.2 `ed1daf0bf`.
- F0–F2: contrato estricto, grafos propios, CLI/API local, timeout, manifiestos, GLB y comparaciones. Q1 fue rechazada por estrecha; Q1b recuperó extensión/grosor y tres secundarias por primaria, con ramas aprobadas.
- Q2 conserva estructura nativa Q1b y geometría X/Y; normaliza Z usando solo madera. Semilla, densidad y escala de follaje no alteran la madera final. Copa ajustada aprobada por el usuario.
- Q3 añadió seis familias deformadas y tamaños/cantidades variables; el usuario pidió menos compacidad, alturas distintas, huecos con ramas visibles desde abajo y relación entre grosor y follaje. Q3b implementa esa revisión conservando las seis formas.
- Los treinta Q3b conservan exactamente el hash completo de madera Q2/Q3 en X/Y/Z, normalización, parámetros, semillas y diagnóstico estructural nativo. Cinco fuentes históricas intactas; Q3 viejo-09 reconstruye geometría idéntica.
- Q3b usa radios nativos de primaria/secundaria para graduar grupos, con tramos más cortos y una secundaria sin hojas por primaria. Varía posición, espesor vertical y margen superior. Con poca densidad, sitúa grupos hacia las puntas y reduce escala un 10 %.
- Dieciocho pruebas aprobadas; repetición Q3b viejo-09/adulto-00, efecto de diez parámetros, independencia de madera ante cambios de copa y seis extremos. Máximo observado: 8116 triángulos/55 masas/dos materiales.
- Treinta Q3b válidos, distintos e importados/capturados en Godot. Jóvenes: 2604 triángulos/13 masas; adultos: 5784–5924/32–33; viejos: 7032–7212/39–42. Dos materiales; alturas 4/10/9 m; follaje dentro de altura.
- En los treinta aumenta la dispersión vertical entre grupos y la madera visible en la vista inferior medida frente a Q3. Correlación radio de primaria/volumen sumado de follaje 0.832–0.995. No implica mejora en todas las vistas ni aceptación estética.
- Comparaciones Q3/Q3b para viejo-00/03/09 y controles, con cámaras compartidas y vistas inferiores. El agente revisó controles, comparaciones y galerías completas de copa, madera y Godot.
- Informes: [Q3b](docs/evidence/q3b/informe.md), [Q3](docs/evidence/q3/informe.md), [Q2 aprobada](docs/evidence/q2/informe.md), [Q1b aprobado](docs/evidence/q1b/informe.md), [F2](docs/evidence/f2/informe.md). Reproducción en [README](README.md).

## Decisiones vigentes

- Un único [plan v1](plans/v1-generador-arboles.md). Q3 es la referencia visual vigente; Q3b queda como ensayo rechazado estéticamente. Se discute mejorar el follaje actual o ensayar otra representación; aún no se elige ni implementa la alternativa. F4–F6 siguen pendientes.
- Q3b en `blender/oak_nodes_v41.py`, reutiliza formas Q3 y ensamblado Q2. Fuentes 0.1.0/0.2.0/0.2.1/0.3.0/0.4.0 congeladas. Grafos Python/bpy como fuente; resultados en carpetas nuevas sin sobrescribir referencias.
- Presets principales: candidato Q3b 0.4.1, mismos parámetros/semillas Q3/Q2. Históricos en `presets/v0.1.0/` a `v0.4.0/`. Lotes Q2/Q3 conservados; `presets/q3b-cases.json` cambia solo versión sobre Q3.
- Densidad Q3b: control cuantizado modulado por longitud/radio; máximos tronco/primaria/secundaria 1/3/2, con dos secundarias foliadas de tres por padre. Hasta 85 masas/25 de detalle alto; límite derivado 8956 triángulos/dos materiales. Presupuesto contractual 10 000/3.
- Dos niveles, hasta 12 primarias/36 secundarias. Presets follaje (escala/densidad): joven 0.45 m/0.5, adulto 1.15 m/0.75, viejo 1.30 m/0.75. Escala efectiva acotada a `min(foliage_scale_m,0.24*height_m)`; densidad cero sin hojas.
- Separar contratos, algoritmos, ejecución, evaluación y adaptadores. Radio relativo al basal como regla artística; no es modelo de carga biológica. Volúmenes sumados cuentan solapamientos; rayos 128×128 y dispersión de alturas no miden naturalidad ni IoU.
- F5 debe usar la transformación registrada: normalización solo en Z, radios finales posiblemente elípticos. Comparar estructura Python base/con regla conservando >=90 % de longitud; no exigir space colonization. Q3b no es ese experimento.
- Cámaras compartidas por caso; congelarlas para F6. API solo loopback, un servidor por carpeta, sin reintentos automáticos. Semillas/procedencia explícitas; elegir proveedor/modelo en F4.

## Siguiente paso

Definir la siguiente prueba de follaje sobre Q3, conservando la madera y comparaciones reproducibles; no hay nueva implementación autorizada en esta revisión. Referencia: `artifacts/q3/acceptance/lote/`; base Q2: `artifacts/q2/acceptance/lote/`. Ensayo Q3b rechazado: `artifacts/q3b/acceptance-final/`, con [comparación frontal](docs/evidence/q3b/comparison-front.jpg) y [desde abajo](docs/evidence/q3b/comparison-below.jpg). Los presets principales aún apuntan a Q3b; no se han revertido.

## Bloqueos y pendientes

- Sin bloqueos de ejecución fuera del sandbox. Dentro, Blender puede bloquearse al cerrar por audio y HTTP no admite loopback; usar ejecución autorizada fuera y tiempos límite.
- Q3b rechazada por el usuario por empeorar el árbol; no confundir sus verificaciones técnicas con aceptación visual. Q3 conserva margen de mejora en piezas reconocibles, solapamientos y transiciones entre masas. Extremos sin aprobación estética general.
- Sin fusión, tercer nivel ni anticolisiones. Menos triángulos no demuestra mejora de FPS o IA; F4–F6 y rendimiento del bosque siguen pendientes/diferidos.
