# T2 — Atlas compatibles y ensayo de halos

Fecha: 2026-11-01. Alcance autorizado: T2 del
[plan de transiciones](../../../../plans/transiciones-estacionales.md).
No se integra un árbol nuevo ni se implementa la mezcla de T3.

## Compatibilidad y máscara

Los dos horneados originales comparten plantillas por hash, cuadrícula 5×5,
24 celdas de 400², área útil .92, UV y resolución 2000². Se mantienen las ocho
plantillas históricas y sus tres proyecciones. Se conservan los PNG originales.
No se reinterpreta el calendario UV2 ni se modifican los perfiles T0/T1.

Alfa histórico distinto en **68 286 texeles**, con **20 641** diferencias de
máscara al recorte .5. La nueva variante otoñal usa exactamente los cuatro
millones de valores alfa del verano, incluida la franja antialias; no interpola
la cobertura entre estaciones. Hash del canal común:
`4fa2953118643986aaf2e2de55b8dd7a310733e2e4e54d8eae6dd3c112d36c7b`.

Bajo esa máscara aparecen **151 texeles** originalmente transparentes en otoño;
**dos** alcanzan el umbral .5. Se completa únicamente su RGB desde vecinos de la
misma celda, con radio máximo 16. El RGB con alfa otoñal original >0 queda exacto.
La cobertura se comprueba con la máscara de procedencia, no por luminancia:
el negro pintado también es color válido. No hay repintado ni recoloración.

## Ensayo de extensión de RGB

Algoritmo `season-atlas-0.1.0`: propagación determinista de ocho vecinos,
16 pasos como máximo, prioridad fija; cada paso lee el frente anterior. Trabaja
por celda, sin envolver bordes ni tomar colores de plantillas vecinas. Solo
cambia RGB con alfa cero; conserva exactos alfa y todos los texeles no transparentes.
Implementación propia con operaciones públicas de Pillow; sin código MIT copiado.

La comparación conserva verano/otoño históricos, variantes de máscara común y
variantes con padding. Mismo material estándar .95, recorte .5, doble cara,
anisotropía, luz/ambiente 1.2/.5 y tonemapping lineal. Godot 4.7.2, Compatibility,
RTX 5060, capturas 700²/MSAA4; fondos `#EEE9DF` y `#182027`. Tres escalas
ortográficas: 1.15/2.8/6 veces la envolvente. Sin animación.

Mipmaps activados **explícitamente** en importación de los seis PNG externos;
relleno automático `process/fix_alpha_border=false`, premultiplicación desactivada
y almacenamiento sin pérdida, para aislar el tratamiento. La prueba verifica
que el recurso importado contiene mipmaps. No basta con elegir filtro con mipmaps
en el material si el importador no los genera.

## Reproducción

```sh
python3 scripts/verify_season_atlas.py --output artifacts/estaciones/otra-t2
PYTHONPATH=src python3 -m unittest discover -s tests
```

Cada salida exige carpeta nueva; el verificador repite atlas/manifiestos en un
directorio temporal, exporta la rama con Blender y captura Godot con interfaz.
Cada subproceso queda limitado a 180 s. `BLENDER_BIN` y `GODOT_BIN` permiten
seleccionar ejecutables. No se invoca ImageGen al reproducir: se parte de los
horneados fuente congelados, comprobados por hash. T2 no altera sus píxeles.

## Resultados y decisión técnica

**T2 verificada técnicamente.** Se conserva el tratamiento `padded` como candidato
en `assets/roble-estacional/v0.1.0/`: solo `summer.png`, `autumn.png` y manifiesto.
Los controles `common` y originales se regeneran en el ensayo, sin acumular
cuatro atlas derivados en assets. [Manifiesto y hashes](atlas-manifest.json).

[Comparación breve de hojas y rama](comparison.jpg),
[tablero claro](board-light.jpg), [tablero oscuro](board-dark.jpg),
[rama clara](branch-light.jpg), [rama oscura](branch-dark.jpg).
Las cuatro láminas se inspeccionaron visualmente. El padding reduce modestamente
el borde oscuro al minificar; el efecto es más claro en verano. No se detectaron
costuras nuevas entre las 24 celdas en estas vistas. El recorte otoñal común resulta
cercano al original, con diferencias pequeñas visibles al comparar bordes. Esto
no equivale a una aceptación artística del usuario ni a garantizar toda cámara,
luz o escala. No se atribuye una ganancia de FPS.

- **181 pruebas** del repositorio pasan fuera del sandbox, incluidas cinco nuevas de atlas: máscara,
  RGB, cobertura negra válida, límites de radio/resolución/celdas, determinismo,
  entradas inválidas y separación entre celdas. Límite de trabajo: ≤2048²,
  ≤64 celdas y radio ≤32; este ensayo usa 25 celdas y radio 16.
- **Dos ejecuciones completas de preparación** producen manifiestos y PNG
  idénticos. Verificación de alfa común, RGB original no transparente y RGB visible
  después del padding. Entradas históricas comprobadas por hash.
- Rama primaria `q3:primary:100` del piloto 3009/17/2718, **32 grupos/96 láminas,
  696 tris (504 madera + 192 follaje), dos materiales**. Madera y cruzadas son
  subconjuntos exactos de la construcción 2.2.0; sin optimización nueva ni normales
  de volumen. [Datos de rama](branch-report.json).
- **Cuatro GLB derivados de rama auditados**: solo cambia el PNG embebido;
  geometría, UV, normales, índices, materiales, escena y corteza permanecen
  binariamente exactos respecto a la rama exportada. Las capturas cargan esa
  misma rama y sustituyen la textura desde recursos externos para aislar importación.
- **72 capturas reales** Godot: seis pinturas/tratamientos × tablero/rama × dos
  fondos × tres distancias. Todas con mipmaps comprobados. La ejecución 05 produce
  las mismas 72 capturas por hash que el ensayo válido 04; no se repitieron para
  buscar una variante visual distinta. [Verificación](verification.json).

Las dos texturas candidatas suman **6 080 799 bytes PNG**. Memoria estimada sin
compresión: **32 000 000 bytes RGBA8** para los dos atlas sin mipmaps,
**42 665 712 bytes** con cadena completa. Corteza histórica 1254² aparte,
6 290 064 bytes sin mipmaps; no cambia. La mezcla futura necesitará dos muestras
RGB de follaje por evaluación del material, frente a una de un extremo fijo.
Estos números describen recursos/cadena convencional, no memoria GPU medida,
tráfico real ni rendimiento del shader futuro.

Salida final: `artifacts/estaciones/atlas-t2-05/`, con galería `index.html`,
proyecto `godot/`, controles `atlas/`, cuatro GLB compatibles en `branch/`, logs
acotados y hashes de fuentes/entradas/capturas. Para conservar los dos candidatos:

```sh
python3 scripts/publish_season_atlas.py --trial artifacts/estaciones/otra-t2 --output /tmp/atlas-candidato --treatment padded
```

El empaquetado exige verificación válida y fuentes/atlas sin alterar. El estado
sigue siendo experimental y la adopción del árbol completo está marcada como falsa.

Ensayos fallidos: 01 terminó por timeout de cierre de audio de Blender dentro del
sandbox; 02 detectó mipmaps ausentes; 03 encontró una precondición demasiado
restrictiva del comprobador (algún recurso ya tenía mipmaps). Se corrigió para
forzar el valor requerido. 04 pasa; 05 repite después de acotar también la cantidad
de celdas admitidas. No se presentan esos intentos fallidos como verificaciones. Una repetición final
de pruebas dentro del sandbox bloqueó el socket loopback de la API; repetidas
fuera, pasan las 181. [Comprobaciones finales](additional-checks.json).

**Siguiente: T3**, material de mezcla lineal y visor del piloto. Pintura y rama
presentadas aquí para valoración; no se adopta un árbol en producción ni se cierra
su aceptación artística. Calendario, animación y normales se evaluarán por separado.
