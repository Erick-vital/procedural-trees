# Operación y ensayos históricos F0–RF3

Comandos desde la raíz del repositorio. Los informes conservan el alcance y
las decisiones de cada ensayo; para el sistema vigente consultar la
[guía de blueprints](uso-blueprints.md), el [README](../README.md) y
[ESTADO.md](../ESTADO.md). Los contratos/algoritmos antiguos siguen disponibles
por rutas y versiones explícitas. El lote F2 de 0.1.0 no equivale al lote RF5.

## Entorno fijado

| Herramienta | Versión comprobada |
| --- | --- |
| Blender | 5.2.1 LTS, build `9e2066aef7ef` |
| Python de Blender | 3.13.13 |
| Python de contratos/orquestación | 3.14.4 |
| jsonschema | 4.19.2 |
| Pillow (galerías y capturas) | 12.1.1 |
| Godot | 4.7.2 stable official, `ed1daf0bf` |

Los ejecutables locales por defecto están en `scripts/generate_f1.py` y `scripts/verify_f1.py`; pueden sustituirse con `BLENDER_BIN` y `GODOT_BIN`. Las pruebas rechazan otras versiones de Blender/Godot. No descargan herramientas ni modifican otros proyectos.

Si faltan dependencias:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

En el entorno actual `jsonschema` ya está instalado. Desde la raíz:

```sh
python3 scripts/verify_f0.py
python3 scripts/verify_f0.py --visual
python3 scripts/generate_f1.py --preset presets/v0.1.0/adulto.json --output artifacts/f1/adulto
python3 scripts/generate_f1.py --preset presets/v0.1.0/viejo.json --output artifacts/f1/viejo
python3 scripts/verify_f1.py --visual
```

Con un entorno virtual, sustituir `python3` por `.venv/bin/python`. Las órdenes con `--visual` necesitan sesión gráfica; abren Godot brevemente y guardan capturas. Cada subproceso tiene un límite de 120 segundos. En este equipo Blender ejecutado como subproceso en el sandbox produjo un bloqueo de audio al cerrar; la ejecución fuera del sandbox pasó. El límite evita esperas indefinidas.

Resultados regenerables en `artifacts/f0/`: `probe.blend`, `probe.glb`, informes JSON, logs, captura y hashes. La prueba copia el GLB a `godot/probe.glb` e importa desde una sesión nueva. Godot escribe su caché en `godot/.godot/`; ambas rutas están ignoradas. La prueba no crea un bosque ni una API de trabajos.

F1 guarda `tree.blend`, `tree.glb`, `input.json`, `manifest.json`, log y vistas en la carpeta indicada. `--no-render` omite las vistas. El manifiesto registra especificación, semillas efectivas, sockets, versiones, métricas y hashes. En el `.blend`, `Oak` es la malla exportada y `OakProcedural` conserva el modificador oculto; para editar los controles, mostrar este último y ocultar `Oak`.

`verify_f1.py` reconstruye los tres presets históricos de `presets/v0.1.0/`, repite el adulto, cambia semillas, prueba límites y profundidad 1 sin hojas, y comprueba el efecto de los diez parámetros. Importa los tres GLB en `godot/f1/` y verifica materiales, triángulos, escala y ejes sin interfaz; `--visual` añade capturas en Godot. Son casos fijos de aceptación, sin el lote de 30 variantes de F2.

## Contrato y coordenadas

[TreeSpec](../schemas/tree-spec.schema.json) rechaza campos desconocidos, valores fuera de rango, profundidad mayor de 2 y números no finitos. Altura, radio y escala de follaje se expresan en metros; inclinación en grados desde la vertical; curvatura como fracción de altura; asimetría y densidad en `[0,1]`. F1 aplica `floor(4*density+0.5)` masas por extremo (0 permite copa vacía); precisa el redondeo propuesto en F0 para implementarlo directamente en nodos.

La altura solicitada es la altura final de la caja del árbol. Hasta 0.2.1, un ajuste vertical de toda la geometría lleva la base a Z=0 y la altura al valor solicitado; X/Y conservan sus medidas y el follaje puede alterar las ramas finales. En Q2 0.3.0 se ajusta Z usando solo la caja de madera y se coloca el follaje dentro de `[0,height_m]`: cambiar semilla, densidad o escala de la copa conserva también la madera final. X/Y y radios nativos Q1b se mantienen; el perfil vertical difiere de Q1b. El radio basal controla la curva antes del ajuste. Véanse las interfaces y límites en el [informe F1](evidence/f1/informe.md).

Blender: metros, Z arriba, +X derecha, −Y frente. Godot: metros, Y arriba, +X derecha, +Z frente. Conversión glTF: `(x,y,z) → (x,z,−y)`. La sonda tiene una curva de 2 m y una esfera facetada de radio 0.6 m en `(0.35,0.2,2)`; se comprueba la caja real, no una altura nominal de TreeSpec.

Separación actual: `src/treegen/` contiene contratos y derivación de semillas; `blender/oak_nodes.py` los grafos congelados 0.1.0 y `blender/oak_nodes_v2.py` la revisión estructural 0.2.0 y `blender/oak_nodes_v21.py` la estructura Q1b 0.2.1 aceptada y `blender/oak_nodes_v3.py` la copa/normalización Q2 0.3.0; `blender/generate_oak.py` la adaptación, diagnóstico, render y exportación; `godot/` la importación y captura; `scripts/` la ejecución acotada. F2 añade `runner.py`, `evaluation.py`, `cli.py` y `api.py` al núcleo sin dependencia de Blender.

## Evidencia y decisión

[Informe F0](evidence/f0/informe.md): revisión de Easy Tree/MTree, incompatibilidad de sockets detectada, decisión de grupos propios, comprobaciones y límites.

[Informe F1](evidence/f1/informe.md): controles del generador, casos de aceptación, capturas revisadas y semillas de referencia.

## F2: ejecución, lote y evaluación

Desde la raíz, usar directorios de salida nuevos: el ejecutor rechaza sobrescribir un trabajo, incluso uno fallido. Los resultados completos quedan bajo `artifacts/`, ignorado por control de versiones.

```sh
PYTHONPATH=src python3 -m treegen generate presets/v0.1.0/adulto.json --output artifacts/mi-arbol
PYTHONPATH=src python3 -m treegen validate artifacts/mi-arbol
PYTHONPATH=src python3 -m treegen batch --cases presets/f2-cases.json --output artifacts/mi-lote
python3 scripts/verify_f2.py --visual --batch artifacts/mi-lote --output artifacts/mi-verificacion
PYTHONPATH=src python3 -m treegen compare artifacts/mi-lote/adulto-00 artifacts/mi-verificacion/repeat --output artifacts/mi-comparacion
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/verify_api.py --output artifacts/mi-prueba-api
```

`presets/f2-cases.json` congela diez jóvenes (semillas 1000–1009), diez adultos (2000–2009) y diez viejos (3000–3009). Cada trabajo produce GLB, `.blend`, entrada normalizada, log, métricas y manifiesto; por defecto también frontal, lateral, superior, perspectiva y ramas sin follaje. Las cámaras quedan registradas; `perspective` usa proyección perspectiva y las otras tres ortográfica. Para un árbol individual, `--no-render` permite omitir vistas. El timeout por Blender es 120 s; `--timeout` admite hasta 600 s y mata el grupo de procesos si vence. Ese lote F2 conserva el algoritmo 0.1.0; el lote Q1 usa 0.2.0.

`manifest.json` distingue `running`, `completed` y `failed`, registra identificador, versiones, semillas, parámetros efectivos, hashes de código/artefactos, fechas UTC y duración. La validación lee los buffers GLB exportados: coordenadas finitas, índices, áreas, presupuesto de 10 000 triángulos/3 materiales, dimensiones y altura ±10 %. Comprueba que materiales, triángulos, caja y hash coinciden con la malla evaluada y que existen las vistas pedidas. La CLI termina con código 1 ante error; un fallo conserva su manifiesto y log. Un lote continúa tras fallos individuales y solo termina como `completed` con 30 resultados válidos y únicos.

`compare` genera JSON y una página HTML con copias de las imágenes de ambos trabajos. Distingue igualdad de especificación, entorno, fuentes, cámaras y geometría normalizada; informa diferencias de triángulos y dimensiones de ambos. Cada árbol se encuadra automáticamente: entre geometrías distintas puede cambiar el encuadre; `same_cameras` lo señala. Esta comparación permite inspección y regresión; no mide IoU de silueta (F6) ni demuestra una mejora de IA. El caso repetido usa cámaras idénticas.

`verify_f2.py` valida el lote, repite `adulto-00` desde una sesión limpia, crea la comparación e importa los 30 GLB en Godot. `--visual` abre Godot y guarda una captura por variante. El equipo actual necesita ejecutar Blender fuera del sandbox para evitar el bloqueo de audio al cerrar; no se considera correcto un proceso que exportó pero no terminó antes del timeout. Las pruebas HTTP también necesitan permiso de loopback.

Las miniaturas de revisión son opcionales y requieren Pillow (`python3 -m pip install Pillow==12.1.1` en el entorno elegido):

```sh
python3 scripts/make_gallery.py artifacts/mi-lote
python3 scripts/make_gallery.py artifacts/mi-lote --godot
```

## API local F2

```sh
PYTHONPATH=src python3 -m treegen serve --port 8765 --jobs artifacts/api
python3 - <<'PYAPI'
import json
from pathlib import Path
from urllib.request import Request, urlopen
body = {'spec': json.loads(Path('presets/v0.1.0/adulto.json').read_text()), 'render': True}
request = Request('http://127.0.0.1:8765/jobs', data=json.dumps(body).encode(),
                  headers={'Content-Type': 'application/json'})
with urlopen(request) as response:
    print(response.status, response.read().decode())
PYAPI
```

`POST /jobs` responde 202 con `job_id` y `status_url`; `GET /jobs/<id>` consulta `queued/running/completed/failed`; `GET /jobs/<id>/manifest.json` devuelve el resultado o fallo cuando existe. Las especificaciones inválidas reciben 400 y la cola llena 503. La API escucha únicamente en `127.0.0.1`, admite cuerpos de hasta 64 KiB, tiene cola de 32 pendientes y procesa secuencialmente con el mismo ejecutor y límite de 120 s. Los archivos están en `<jobs>/<id>/result/`; la API mínima expone metadatos, sin servir binarios. Al reiniciar marca como fallidos los trabajos interrumpidos; no reanuda ni reintenta automáticamente. Usar un solo servidor por carpeta de trabajos.

[Informe F2](evidence/f2/informe.md): lote, repetición, pruebas de fallos, API y revisión visual. Salidas verificadas en este equipo: `artifacts/f2/lote-final/` y `artifacts/f2/verification-final/`.

Revisión de calidad posterior a F2: [diagnóstico de los viejos 00, 03 y 09](evidence/revision-viejos/informe.md). Ese informe describe la base 0.1.0; Q1 implementó una primera corrección estructural, posteriormente rechazada por su forma estrecha; Q1b fue aceptada después por el usuario como base para Q2.

## Q1: primera etapa de calidad de ramas

La revisión permanece en el plan v1. Q1 0.2.0 fue verificada técnicamente, pero el usuario rechazó la estructura estrecha y ascendente. El usuario aprobó las ramas Q1b 0.2.1 y Q2 en su variante de copa ajustada. Los presets históricos están en `presets/v0.1.0/`, `v0.2.0/`, `v0.2.1/`, `v0.3.0/` y `v0.4.0/`; sus lotes quedan congelados. La base Q2 aprobada está en `presets/q2-cases.json`; Q3, en `presets/q3-cases.json`; Q3b `algorithm_version: "0.4.1"` se conserva explícitamente en `presets/v0.4.1/` y `presets/q3b-cases.json`. Desde B5, los tres presets sin versión apuntan a Q3 0.4.0.

Q1 calcula grosores a partir del padre local, distribuye ramas por sectores con variación acotada, varía inclinaciones/curvaturas y abre las secundarias a ambos lados. Conserva el número de ramas, el procesamiento de follaje y el ajuste vertical. Usa 2132/5632/6144 triángulos para joven/adulto/viejo y dos materiales; el máximo de extremos comprobado es 7420. No demuestra una reducción de cruces de F5 ni una optimización de F6.

```sh
PYTHONPATH=src python3 -m treegen generate presets/v0.2.0/viejo.json --output artifacts/mi-viejo-q1
PYTHONPATH=src python3 -m treegen batch --cases presets/q1-cases.json --output artifacts/mi-lote-q1
python3 scripts/verify_q1.py --visual --output artifacts/mi-aceptacion-q1
python3 scripts/q1_gallery.py artifacts/mi-aceptacion-q1
python3 scripts/make_gallery.py artifacts/mi-aceptacion-q1/lote --godot
```

`verify_q1.py` genera su propio lote, verifica referencias/repetición, efecto de parámetros, semillas, extremos, medidas estructurales e importación Godot. Necesita la base F2 en `artifacts/f2/lote-final/` o una ruta mediante `--base`. Las comparaciones de los viejos 00/03/09 y controles usan encuadre/cámaras compartidos por pareja; el HTML queda en `<output>/comparison/index.html`. Las galerías requieren Pillow.

[Informe Q1](evidence/q1/informe.md), [ramas comparadas](evidence/q1/comparison-branches.jpg) y [copas comparadas](evidence/q1/comparison-front.jpg). Resultados comprobados: `artifacts/q1/acceptance/`; GLB importados en `godot/q1/`. Pasaron catorce pruebas unitarias y los treinta candidatos son válidos y únicos. El usuario rechazó su apariencia: los viejos son demasiado estrechos/ascendentes. Q1b corrigió las ramas y fue aceptada por el usuario; Q2 revisó después el follaje y la dependencia del ajuste vertical, y su variante ajustada también fue aprobada.

## Q1b: ramas más largas, gruesas y ramificadas

La versión 0.2.1, aceptada por el usuario para la estructura, conserva las fuentes y referencias 0.1.0/0.2.0. Mantiene parámetros, semillas, sectores angulares, grosores ligados al padre local y dos niveles; alarga y abre las primarias, aumenta su radio local y añade una tercera secundaria escalonada. Conserva el follaje y el ajuste Z para comparar la estructura. El cambio de conteos está registrado en el plan: máximo 12 primarias, 36 secundarias y 196 masas. El límite sigue siendo 10 000 triángulos/3 materiales.

```sh
PYTHONPATH=src python3 -m treegen generate presets/v0.2.1/viejo.json --output artifacts/mi-viejo-q1b
PYTHONPATH=src python3 -m treegen batch --cases presets/q1b-cases.json --output artifacts/mi-lote-q1b
python3 scripts/verify_q1b.py --visual --output artifacts/mi-aceptacion-q1b
python3 scripts/q1b_gallery.py artifacts/mi-aceptacion-q1b
python3 scripts/make_gallery.py artifacts/mi-aceptacion-q1b/lote
python3 scripts/make_gallery.py artifacts/mi-aceptacion-q1b/lote --godot
```

El verificador usa las referencias en `artifacts/f2/lote-final/` y `artifacts/q1/acceptance/lote/` (opciones `--base` y `--q1`). Genera su propio lote y contrasta los viejos 00/03/09 y controles a cámara compartida entre las tres versiones; mide además los otros siete viejos sin ajustar las reglas a ellos. Comprueba repetición de las tres versiones, diez parámetros, separación de streams, cinco extremos e importación Godot. Cada subproceso tiene timeout; `--visual` requiere sesión gráfica. Las galerías requieren Pillow.

El usuario dio su visto bueno a las ramas el 2026-10-22. La estructura Q1b queda como referencia para Q2, donde se revisarán el follaje y el ajuste de proporciones. Su borrador inicial se retiró del contrato/ejecutor y se conservó en `artifacts/q2/draft/`, junto a su primera previsualización en `artifacts/q2/preview-viejo/`; no constituye una etapa verificada.

[Informe Q1b](evidence/q1b/informe.md), [ramas frontales](evidence/q1b/comparison-branches.jpg) y [vista superior](evidence/q1b/comparison-top.jpg). Resultados comprobados: `artifacts/q1b/acceptance/`; comparación completa en `comparison/index.html`, modelos en `lote/` e importados en `godot/q1b/`. Quince pruebas y treinta GLB válidos/únicos, repetibles e importados; máximo en extremos 9676 triángulos/dos materiales. Los viejos 00/03/09 recuperan anchura y longitud originales; entre las otras siete semillas hay variación y dos quedan por debajo del 95 % de anchura base. Las ramas Q1b están aprobadas por el usuario; Q2 está implementada, verificada técnicamente y aprobada en la variante de copa ajustada.

## Q2: copa y proporciones sobre Q1b

La versión 0.3.0 reutiliza la estructura 0.2.1 aprobada y conserva su geometría de madera en X/Y. Normaliza la madera a la altura pedida y lleva los apoyos de follaje al mismo marco; distribuye las masas sobre tramos distales variables de cada curva. Sus tamaños y giros cambian por masa usando la semilla de follaje. Las masas se desplazan para quedar dentro de la altura, sin reajustar las ramas.

La normalización sigue siendo solo en Z: corrige la dependencia accidental del follaje y conserva la anchura aprobada. La madera alcanza ahora la altura pedida incluso con densidad cero; el perfil vertical cambia respecto a Q1b y se compara sin hojas. La escala efectiva de follaje queda acotada a `min(foliage_scale_m, 0.24*height_m)` para combinaciones extremas de poca altura y masas grandes. La densidad conserva `floor(4*density+0.5)` masas por curva, ahora distribuidas sobre ella; presupuesto máximo 9676 triángulos/dos materiales en los extremos comprobados.

Los presets solo ajustan follaje: joven escala 0.45 m/densidad 0.5; adulto 1.15 m/0.75; viejo 1.30 m/0.75. Parámetros estructurales y semillas Q1b conservados. `presets/q2-cases.json` contiene el lote ajustado y `presets/q2-controlled-cases.json` conserva todos los parámetros de Q1b con versión 0.3.0 para aislar el algoritmo.

```sh
PYTHONPATH=src python3 -m treegen generate presets/v0.3.0/viejo.json --output artifacts/mi-viejo-q2
PYTHONPATH=src python3 -m treegen batch --cases presets/q2-cases.json --output artifacts/mi-lote-q2
python3 scripts/verify_q2.py --visual --output artifacts/mi-aceptacion-q2
python3 scripts/q2_gallery.py artifacts/mi-aceptacion-q2
python3 scripts/make_gallery.py artifacts/mi-aceptacion-q2/lote
python3 scripts/make_gallery.py artifacts/mi-aceptacion-q2/lote --godot
```

El verificador usa exclusivamente Q1b como referencia (`--base`, por defecto `artifacts/q1b/acceptance/lote/`). Reconstruye viejo-09 Q1b, repite Q2, prueba los diez parámetros, independencia de madera ante tres parámetros de follaje y seis extremos. Mide las treinta maderas/copas guardadas y genera cinco controles con parámetros idénticos a Q1b. La comparación tiene Q1b aprobado / Q2 con parámetros Q1b / Q2 ajustado, con semillas y cámaras compartidas y vistas con/sin hojas. La API/CLI admiten las versiones registradas en el esquema; las fuentes históricas quedan congeladas.

`crown_checks` registra hashes de madera completa y proyectada en X/Y, masas como componentes topológicas, ocupación de centros en cinco bandas de altura y ocho sectores, y cajas por material. Estas medidas no calculan volumen ocupado, continuidad de copa ni IoU de silueta. `normalization` registra caja nativa de madera, escala y traslación usadas. El GLB final sigue validándose contra la malla evaluada.

El usuario aprobó la copa ajustada Q2 el 2026-10-22. Señala grupos de follaje todavía demasiado similares y solicita propuestas de refinamiento; el usuario autorizó después Q3 para abordar formas, jerarquía y cantidad por rama. F4–F6 siguen pendientes.

[Informe Q2](evidence/q2/informe.md), [copas comparadas](evidence/q2/comparison-front.jpg), [ramas comparadas](evidence/q2/comparison-branches.jpg) y [vista superior](evidence/q2/comparison-top.jpg). Resultados comprobados: `artifacts/q2/acceptance/`, comparación completa en `comparison/index.html`, nuevos modelos en `lote/` e importados en `godot/q2/`. Pasaron diecisiete pruebas y treinta modelos válidos/distintos; máximo de extremos 9676 triángulos/dos materiales. El cambio máximo de inclinación final respecto a Q1b es 4.051°; la copa ajustada Q2 está aprobada por el usuario. Q3 implementa después el refinamiento de formas y agrupación; su valoración estética sigue pendiente.

## Q3: formas, jerarquía y cantidad de follaje por rama

El candidato 0.4.0 conserva los parámetros/semillas de Q2 ajustada y reutiliza su ensamblado de madera sin modificar las fuentes históricas. Cambia solo follaje: seis familias procedurales asimétricas, deformación continua por masa, tres tamaños y cantidad dependiente de longitud/nivel. Los presets aprobados están en `presets/v0.3.0/`; `presets/q3-cases.json` cambia únicamente la versión del algoritmo sobre los treinta casos Q2.

Las masas principales tienen 80 triángulos; las pequeñas/secundarias 20. Los máximos por curva son tronco/primaria/secundaria 2/3/2; como máximo 110 masas. Hasta dos masas de detalle alto por primaria y dos en tronco dan un límite derivado de 9516 triángulos para el árbol completo con perfil de ocho lados. La densidad se cuantiza en `floor(4*density+0.5)` como control de cantidad, después modulado por longitud/nivel; densidad cero elimina la copa. Esta interpretación 0.4.0 está versionada, no cambia las versiones anteriores.

Las seis formas se generan con deformaciones espaciales suaves y lóbulos, luego se deforman también por masa en X/Y. Sus cotas Z exactas permiten colocar cada masa dentro de la altura solicitada, manteniendo la transformación y el hash completo de madera Q2. Se usan semillas enteras para diferenciar streams sin perder precisión al sumar constantes grandes en float32. El follaje conserva un único material.

```sh
PYTHONPATH=src python3 -m treegen generate presets/viejo.json --output artifacts/mi-viejo-q3
PYTHONPATH=src python3 -m treegen batch --cases presets/q3-cases.json --output artifacts/mi-lote-q3
python3 scripts/verify_q3.py --visual --output artifacts/mi-aceptacion-q3
python3 scripts/q3_gallery.py artifacts/mi-aceptacion-q3
python3 scripts/make_gallery.py artifacts/mi-aceptacion-q3/lote
python3 scripts/make_gallery.py artifacts/mi-aceptacion-q3/lote --godot
```

El verificador usa la base Q2 aprobada (`--base`, por defecto `artifacts/q2/acceptance/lote/`). Comprueba madera final completa idéntica, mismos parámetros/semillas, repetición Q2/Q3, diez parámetros, independencia respecto al follaje y seis extremos. Inspecciona los treinta modelos guardados, verifica familias distintas y una deformación que no puede explicarse como transformación afín, y genera comparaciones con cámara compartida e imágenes de las seis familias a igual escala. `--visual` captura Godot; las galerías requieren Pillow y cada subproceso tiene timeout de 120 s.

`foliage_checks` registra cantidades por nivel/rol/familia, detalle alto y distribución de conteos por rama. `crown_checks` añade distribución de triángulos por masa y variación de tamaño usando la diagonal de sus cajas. Son diagnósticos de geometría y jerarquía; no miden naturalidad, volumen de copa ni silueta.

Pasaron dieciocho pruebas unitarias y los treinta modelos son válidos, distintos e importados/capturados en Godot. Jóvenes: 2684 triángulos/17 masas; adultos: 6864–6984/65–71; viejos: 8432–8532/85–90. Los treinta conservan exactamente la madera final Q2; máximo de extremos 9516 triángulos/dos materiales. El agente revisó comparaciones y galerías. Menos masas no implica menos triángulos: algunas ahora tienen mayor detalle; no se declara una optimización ni mejora de FPS.

[Informe Q3](evidence/q3/informe.md), [comparación frontal Q2/Q3](evidence/q3/comparison-front.jpg), [vista superior](evidence/q3/comparison-top.jpg), [familias de formas](evidence/q3/shape-families.jpg) y [galería Godot](evidence/q3/gallery-godot.jpg). Resultados completos: `artifacts/q3/acceptance/`; comparación en `comparison/index.html`, modelos en `lote/` e importados en `godot/q3/`.

El usuario identifica posteriormente Q3 como última iteración buena y rechaza la apertura Q3b. Q3 queda como referencia del ensayo de fusión parcial descrito abajo; F4–F6 siguen pendientes.

## Q3b: copa abierta y grupos según grosor

El usuario valora el volumen de Q3, pero pide menos compacidad, distintos tamaños entre ramas principales, variación vertical y huecos visibles desde abajo. El candidato 0.4.1 conserva las seis familias de formas y la madera Q2; revisa la distribución del follaje. `presets/q3b-cases.json` mantiene parámetros y semillas Q3, cambiando solo versión. Los presets Q3 previos quedan en `presets/v0.4.0/`.

La escala/cantidad de cada grupo usa el radio nativo de la rama y el de su padre, relativos al radio basal. Los grupos se concentran en tramos más cortos; la secundaria intermedia de cada primaria queda sin hojas. Las ramas gruesas sostienen grupos mayores y con más masas; las delgadas, menores. La posición sobre la curva y el espesor vertical varían por rama; un margen superior variable permite encajar los grupos conservando espesor y altura final. Con poca densidad se colocan más hacia las puntas y su escala baja un 10 % para conservar la apertura. La madera mantiene su transformación completa.

Los máximos tronco/primaria/secundaria son 1/3/2 masas, con dos secundarias foliadas de las tres de cada primaria: hasta 85 masas, 25 de detalle alto y 60 de detalle bajo. El límite derivado para perfil de ocho lados es 8956 triángulos/dos materiales; no constituye una medida de FPS.

```sh
PYTHONPATH=src python3 -m treegen generate presets/viejo.json --output artifacts/mi-viejo-q3b
python3 scripts/verify_q3b.py --preview --output artifacts/mi-preview-q3b
python3 scripts/q3b_gallery.py artifacts/mi-preview-q3b
python3 scripts/verify_q3b.py --visual --output artifacts/mi-aceptacion-q3b
python3 scripts/q3b_gallery.py artifacts/mi-aceptacion-q3b
python3 scripts/make_gallery.py artifacts/mi-aceptacion-q3b/lote
python3 scripts/make_gallery.py artifacts/mi-aceptacion-q3b/lote --godot
```

`--preview` produce cinco controles con comparaciones, sin declarar aceptación técnica. La verificación completa usa Q3 como referencia (`--base`, por defecto `artifacts/q3/acceptance/lote/`), repite ambos algoritmos, comprueba los diez parámetros, independencia de madera y seis extremos e importa los treinta modelos en Godot. Se añaden vistas inferiores con cámara compartida. El inspector mide radio/follaje, alturas de grupos y madera visible mediante rayos sobre la malla guardada; estas medidas no sustituyen la valoración estética.

Pasaron dieciocho pruebas y treinta modelos válidos/distintos e importados/capturados en Godot. Los treinta conservan la madera completa Q2/Q3 y muestran mayor dispersión vertical de grupos y más madera visible en la vista inferior medida; no se afirma mejora en todos los ángulos. Jóvenes: 2604 triángulos/13 masas; adultos: 5784–5924/32–33; viejos: 7032–7212/39–42. Máximo de extremos: 8116 triángulos/dos materiales. No se declara mejora de FPS ni aceptación estética.

[Informe Q3b](evidence/q3b/informe.md), [comparación frontal](evidence/q3b/comparison-front.jpg), [desde abajo](evidence/q3b/comparison-below.jpg), [vista superior](evidence/q3b/comparison-top.jpg) y [galería Godot](evidence/q3b/gallery-godot.jpg). Lote final: `artifacts/q3b/acceptance-final/`; comparación en `comparison/index.html`, modelos en `lote/` e importados en `godot/q3b/`. El usuario rechazó posteriormente su resultado estético; las verificaciones técnicas se conservan como evidencia histórica.

## Ensayo de fusión parcial desde Q3

Referencia en Git: commit inicial `fbe87a4`, etiqueta `q3-referencia-0.4.0`. Se probó primero `viejo-09` y, tras revisar el piloto, `viejo-00`, `viejo-03` y `adulto-00`. El posprocesado `q3-partial-fusion-0.2.1` fusiona superficies por grupos de hasta tres subárboles vecinos. Conserva exactamente madera y sombreado, masas Q3 de entrada, parámetros, semillas, cámaras y materiales. Los generadores históricos y presets no cambian.

```sh
python3 scripts/preview_fusion.py --output artifacts/q3-fusion/mi-piloto
# Revisar el piloto antes de ampliar los controles.
python3 scripts/preview_fusion.py --output artifacts/q3-fusion/mis-controles --cases viejo-09 viejo-00 viejo-03 adulto-00
python3 scripts/verify_fusion.py --study artifacts/q3-fusion/mis-controles --visual
python3 scripts/fusion_evidence.py --study artifacts/q3-fusion/mis-controles --output artifacts/q3-fusion/mi-evidencia
```

Requiere el lote Q3 y sus cámaras históricas; `--base` y `--cameras-root` permiten indicar otra reconstrucción. Pillow 12.1.1 está instalado en el entorno usado para las galerías. Usar carpetas nuevas; cada subproceso de este ensayo tiene límite de 180 s. Las capturas necesitan sesión gráfica; `--visual` abre Godot brevemente.

Resultados seleccionados: `artifacts/q3-fusion/acceptance/index.html`; modelos `<caso>/candidate/tree.glb`. Cuatro candidatos GLB válidos, ocho importaciones/capturas Godot, reproducción idéntica de Q3 y del ensayo sobre viejo-09, y entrada Q3 completa conservada en cada `.blend`. IoU mínima de silueta 98.33 % en cuatro vistas a 192×192 rayos; no mide naturalidad. [Informe](evidence/q3-fusion/informe.md), [piloto en seis vistas](evidence/q3-fusion/pilot-all-views.jpg) y [comparación Godot](evidence/q3-fusion/controls-godot.jpg). El usuario considera Q3/fusión casi iguales y acepta cerrar esta familia como aprobada para su estilo. No se extiende la fusión al lote ni se atribuye superioridad. [Dirección de rediseño](diseno-follaje.md) y avance RF0/RF1 abajo.

## Rediseño: referencia y unidad de hojas RF0/RF1

[Ficha visual/contrato](follaje-rf0-rf1.md) e [informe](evidence/rf0-rf1/informe.md). RF0 congela viejo-09 Q3 y la primaria 100, con cámaras ortográficas compartidas y tomas al 50/25/10 % del cuadro. RF1 compara siete hojas sobre un portador virtual: rombo de 2 triángulos y hexágonos plano/plegado de 4, un material opaco de doble cara. Contrato experimental separado en `schemas/foliage-unit.schema.json`, preset en `presets/foliage-unit.json`; los generadores y presets históricos no cambian.

```sh
python3 scripts/verify_foliage_unit.py --output artifacts/foliage/otra-revision --visual
python3 scripts/foliage_evidence.py --study artifacts/foliage/otra-revision --output artifacts/foliage/evidencia
```

Usar carpeta nueva. Cada subproceso tiene timeout de 120 s. `--visual` abre Godot y captura las unidades; sin él solo se verifican geometría/importación. El selector de evidencia requiere esas capturas y las referencias fotográficas indicadas en el informe. Se pueden sustituir rutas con BLENDER_BIN/GODOT_BIN.

Resultado seleccionado: `artifacts/foliage/rf0-rf1-acceptance/index.html`, con modelos `<variante>/unit.glb`. Pasaron 24 pruebas y 16 GLB, repetición, diez controles aislados y límites de 32 hojas/128 triángulos. [Comparación Blender/Godot](evidence/rf0-rf1/variants.jpg) y [controles](evidence/rf0-rf1/controls.jpg). El usuario autorizó continuar con RF2 sobre el hexágono plegado; los límites de perfil y soporte se evalúan en esa escala. No se ha construido una copa nueva.

## RF2: hojas sobre rama Q3

La primaria 100 de RF0 y sus tres secundarias Q3 originales conservan los mismos polígonos y sombreado. El contrato `foliage-branch-0.1.0` separa cantidad de soportes, hojas por metro y tamaño; se comparan doce casos longitudinal/terminal × densidad × orientación. [Informe](evidence/rf2/informe.md), [comparación](evidence/rf2/comparison.jpg), [matriz](evidence/rf2/matrix.jpg) y [diagnóstico de soportes](evidence/rf2/supports.jpg).

```sh
python3 scripts/verify_foliage_branch.py --output artifacts/foliage/otra-rama-rf2 --visual
python3 scripts/foliage_branch_evidence.py --study artifacts/foliage/otra-rama-rf2 --output artifacts/foliage/evidencia-rf2
```

Usar carpeta nueva. Cada proceso tiene límite de 120 s; las capturas Godot se dividen en lotes. Sin `--visual` se comprueba la importación pero no se generan las capturas necesarias para el segundo comando. Resultado seleccionado: `artifacts/foliage/rf2-acceptance-final/index.html`, modelos `<caso>/branch.glb`. Pasaron 30 pruebas y 19 GLB; las firmas exportadas de madera/normales y material de corteza coinciden con Q3.

La lectura cambia respecto a las masas, pero los soportes invisibles dejan hojas suspendidas. Terminal concentra abanicos; longitudinal reparte mejor las hojas, sin resolver la conexión. Esta versión original se conserva sin madera visible; las líneas magenta son solo diagnóstico y no están en los modelos. La revisión siguiente añade ramillas como geometría separada.

## Revisión RF2: ramillas y región objetivo

`foliage-branch-0.2.0` conserva la madera Q3 base y separa ramillas nuevas y hojas. Compara una pareja con/sin conexiones con colocaciones idénticas; después selecciona recorridos hacia una región congelada desde Q3. [Contrato](contrato-rf2-ramillas.md), [informe](evidence/rediseno-follaje/rf2-ramillas/informe.md), [conexiones](evidence/rediseno-follaje/rf2-ramillas/connection.jpg) y [distribución](evidence/rediseno-follaje/rf2-ramillas/distribution.jpg).

```sh
python3 scripts/verify_foliage_twigs.py --output artifacts/rediseno-follaje/otra-rama --visual
python3 scripts/foliage_twigs_evidence.py --study artifacts/rediseno-follaje/otra-rama --output artifacts/rediseno-follaje/evidencia
```

Usar carpeta nueva. Generación ≤120 s; Godot/verificación ≤180 s por proceso, capturas en lotes de tres. Sin `--visual` no se genera la evidencia gráfica del segundo comando. Galería seleccionada: `artifacts/rediseno-follaje/rf2-ramillas-final/index.html`, GLB en `<caso>/branch.glb`. Pasaron 37 pruebas, 13 GLB importados y 120 capturas Godot; base Q3 intacta y dos repeticiones idénticas.

Las ramillas se leen en detalle, pero incluso a .8 m persiste poco volumen y el follaje pierde presencia a distancia. El caso dirigido de doce soportes añade 360 triángulos; su proyección aritmética al árbol da 9252, sin copa generada. Dieciséis soportes darían 10572, fuera del límite. RF2 sigue con salida artística pendiente; toca revisar organización/alcance por coste antes de RF3.

## Ensayo RF2: masas Q3 como moldes invisibles

`foliage-molds-0.1.1` extrae nueve masas Q3 originales de la rama congelada, muestrea su superficie por área y descarta muestras interiores entre ellas. Los moldes guían grupos de hojas conectados y quedan excluidos del GLB. [Contrato](contrato-rf2-moldes.md), [informe](evidence/rediseno-follaje/rf2-moldes/informe.md), [hexágonos](evidence/rediseno-follaje/rf2-moldes/hexagons.jpg) y [rombos](evidence/rediseno-follaje/rf2-moldes/diamonds.jpg).

```sh
python3 scripts/verify_foliage_molds.py --output artifacts/rediseno-follaje/otros-moldes --visual
python3 scripts/foliage_molds_evidence.py --study artifacts/rediseno-follaje/otros-moldes --output artifacts/rediseno-follaje/evidencia-moldes
```

Usar carpeta nueva. Generación ≤120 s y verificación/capturas ≤180 s por proceso terminable. Sin `--visual` se verifica GLB/Godot, pero no se generan capturas para el segundo comando. Galería: `artifacts/rediseno-follaje/rf2-moldes-final/index.html`, modelos `<caso>/branch.glb`. Pasaron 43 pruebas, 11 GLB y 72 capturas Godot; base Q3 intacta y cuatro repeticiones idénticas.

Hexágonos .45/.8 m: 48 hojas y 416 triángulos añadidos; rombos .8/1 m con conexiones rectas: 96 hojas y 384 añadidos. Cada pareja aísla tamaño; entre parejas cambian varias variables. El rombo de 1 m cubre 54–64 % de la proyección Q3 en seis vistas, frente a 4–6 % de la revisión previa; conserva más presencia a distancia, pero se ve grande y anguloso. Proyección presupuestaria 9516 por árbol, sin copa generada. Aprobación artística pendiente.

## RF2: más hojas sobre las mismas conexiones

El usuario solicita más volumen y eleva el techo del rediseño a 12500 triángulos/3 materiales por árbol. `foliage-molds-0.1.2` añade hojas al rombo de 1 m conservando todas las originales y la madera. [Comparación](evidence/rediseno-follaje/rf2-densidad/density.jpg) e [informe](evidence/rediseno-follaje/rf2-densidad/informe.md).

```sh
python3 scripts/verify_foliage_molds.py --density --output artifacts/rediseno-follaje/otra-densidad --visual
python3 scripts/foliage_molds_evidence.py --study artifacts/rediseno-follaje/otra-densidad --output artifacts/rediseno-follaje/evidencia-densidad
```

Mismas condiciones y límites de ejecución del ensayo anterior, carpeta nueva. Galería: `artifacts/rediseno-follaje/rf2-densidad-01/index.html`, modelos `<caso>/branch.glb`. Pasaron 45 pruebas, nueve GLB y 60 capturas Godot; dos repeticiones y reconstrucción de 0.1.1 idénticas. 120/144/192 hojas proyectan 10044/10572/11628 triángulos por árbol, sin copa generada. El usuario aprueba 144 como referencia de rama para RF3 el 2026-10-23; [aceptación](evidence/rediseno-follaje/rf2-densidad/aceptacion.json). Los contratos y presets históricos conservan su límite de 10000; integración normal del estilo pendiente de RF5.

## RF3: primer árbol completo

`foliage-canopy-0.1.0` conserva exactamente la madera Q3 de viejo-09, usa sus 89 moldes invisibles y reparte grupos por superficie expuesta de toda la copa. Continúa la regla RF2 de rombo nominal 1 m y seis hojas por conexión. [Contrato](contrato-rf3-copa.md), [informe](evidence/rediseno-follaje/rf3/informe.md), [Q3 frente al piloto](evidence/rediseno-follaje/rf3/comparison.jpg) y [controles](evidence/rediseno-follaje/rf3/controls.jpg).

```sh
python3 scripts/verify_foliage_canopy.py --output artifacts/rediseno-follaje/otra-copa --visual
python3 scripts/foliage_canopy_evidence.py --study artifacts/rediseno-follaje/otra-copa --output artifacts/rediseno-follaje/evidencia-copa
```

Usar carpeta nueva, mismas versiones de Blender/Godot. Generación ≤120 s y capturas/verificaciones ≤180 s por proceso terminable, en lotes de dos escenas. Sin `--visual` solo se comprueban geometría/importación. La referencia RF0 y la aceptación RF2 deben conservar sus archivos y hashes.

Galería: `artifacts/rediseno-follaje/rf3-acceptance-02/index.html`. Árbol: `pilot/tree.glb` y `pilot/tree.blend`. Piloto de 264 conexiones y 1584 hojas, 10572 triángulos/3 materiales, altura 9 m. Pasaron 51 pruebas, siete GLB y 60 capturas Godot; repetición idéntica y madera/normales/corteza coincidentes con el GLB Q3 original.

Perfil ×1.12 cambia anchura con igual coste; ocupación este ×.4 abre esa zona y reduce a 9732 triángulos, conservando las otras regiones. Hojas .75 m conservan soportes/raíces/ejes. La copa mantiene presencia a distancia y lectura distinta de las masas; siguen láminas grandes y solapamientos en detalle. El usuario aprueba el piloto RF3 como referencia del primer tipo el 2026-10-23; [adopción y conservación B0](evidence/blueprints/b0/informe.md). Los controles B3 y su revisión están verificados; [informe vigente](evidence/blueprints/b3-revision/informe.md). Los validadores usan 12500 explícitamente en RF3 y mantienen 10000 como valor histórico por defecto; el estilo está integrado en la CLI mediante `generate-blueprint` (B2); la API histórica conserva TreeSpec.

## Comparación de Easy Tree y Sapling con Q3

Un adulto de 10 m y un viejo de 9 m por generador, máximo 10000 triángulos/3 materiales, paleta opaca y facetado comunes, cámaras compartidas en Godot. [Informe de resultados y esfuerzo](evidence/comparacion-addons/informe.md), [comparación gráfica](evidence/comparacion-addons/godot-perspective.jpg) y [madera](evidence/comparacion-addons/wood-only.jpg).

```sh
python3 scripts/verify_addon_comparison.py --output artifacts/addon-comparison/otra-comparacion --visual
python3 scripts/addon_comparison_evidence.py --study artifacts/addon-comparison/otra-comparacion --output artifacts/addon-comparison/evidencia
```

Requiere los addons locales Easy Tree 1.0.1 y Sapling 0.3.7 en `~/.config/blender/5.2/extensions/blender_org/`; no los instala ni modifica. El ensayo reproduce catorce configuraciones, con un rechazo esperado de Easy Tree viejo inicial por complejidad, y repite los cuatro candidatos seleccionados. Cada Blender/Godot tiene timeout de 120 s y las capturas se dividen en lotes. Sin `--visual` no se genera la evidencia gráfica para el segundo comando.

Galería seleccionada: `artifacts/addon-comparison/acceptance-final/index.html`; GLB en `comparison/<generador>-<edad>/tree.glb`. Q3 usa copias facetadas de adulto-00/viejo-09 sin sobrescribir sus fuentes. Easy Tree adaptado: 7472/9022 triángulos, con hoja geométrica RF1 y cambios de resolución interna; Sapling ajustado: 7764/9048, con hoja hexagonal y controles nativos. Los seis modelos pasan GLB/Godot; hay 36 capturas, repeticiones idénticas y 30 pruebas existentes aprobadas.

Sapling requirió menos intervención interna en esta comparación; Q3 conserva la copa más compacta y los addons muestran otra arquitectura y ocupación. No se declara ganador artístico ni se cambia el generador predeterminado. El ensayo no acredita generación durante el juego y no inicia RF3.
