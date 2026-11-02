# Calendario estacional por grupo — contrato 1.0

Implementación T1, algoritmo `season-calendar-0.1.0`, transporte
`season-calendar-uv2-0.1.0`. [Plan](../plans/transiciones-estacionales.md).
Esta entrega genera datos; todavía no mezcla pinturas ni modifica normales.

## Perfil y recursos

Perfil explícito: `configs/seasons/roble-calendario-v1.json`, versión 0.1.0.
Esquema: `schemas/tree-season-calendar-profile.schema.json`.

- Única combinación admitida: `roble_copa_ancha@2.2.0`, fase
  `summer_to_autumn_full_canopy`. **p=0 verano, p=1 otoño de copa completa**.
  No representa un año completo ni una regla botánica universal.
- Semilla estacional 1101, independiente de base/copa/pintura. Entero 0–2³¹−1.
  No usa el módulo 8191 del shader experimental de tinte.
- Recursos verano/otoño/corteza por ruta versionada y SHA-256; validar antes de
  generar. Máximo 16 MiB por PNG y dimensiones verificadas: follaje 2000²,
  corteza 1254². Se mantienen las pinturas existentes, incluida su diferencia
  de alfa; la máscara común corresponde a T2.
- Techo fijo: 360 grupos, 6999 tris y dos materiales. Especie/fase desconocidas,
  campos extra, NaN/Inf, booleanos como números y rangos inválidos se rechazan.
  Los contratos de tinte 1.0.0 y de sustitución de pintura quedan intactos.

## Volúmenes de entrada

El algoritmo puro recibe una lista de objetos con exactamente:
`id`, `center_m`, `size_m`, `axes`. La reconstrucción desde la receta usa los
grupos históricos de tres láminas; sus hashes se contrastan con el manifiesto.

ID único de hasta 200 caracteres; centro finito dentro de ±100 m; tres tamaños
de .01–40 m y tres ejes unitarios/ortogonales, tolerancia 1e−5. Se ordena por ID.
Los límites son de validación, no una certificación artística de esos rangos.

Cada volumen es un elipsoide con centro/ejes del grupo y semiejes `size_m/2`.
Su radio conservador es el mayor semieje. Es una aproximación de ocupación, no
una esfera sólida ni una medición de cobertura de las hojas pintadas.

## Exposición y calendario

`src/treegen/season_calendar.py` calcula todo una vez por ejemplar:

1. Selecciona hasta 24 vecinos en un alcance acotado, por distancia a su esfera
   envolvente; desempata por ID. No incluye el propio grupo.
2. Usa hasta 12 direcciones de una esfera de Fibonacci. Interseca cada rayo con
   los elipsoides vecinos; limita longitud por alcance y normaliza las cuerdas
   por el tamaño del vecino. Exposición es la media de una atenuación exponencial.
3. Deriva valores pseudoaleatorios de SHA-256 de versión, semilla, ID y dominio
   (`order`, `duration`, `variation`). Flujos separados, sin azar global mutable.
4. Correlaciona el azar de orden con vecinos, ponderando por distancia. Mezcla
   ese valor con `1-exposure`: los grupos abiertos tienden a empezar antes.
5. Produce inicio y duración dentro de intervalos del perfil; por grupo:
   `w(p)=smoothstep(start, start+duration, p)`.

Perfil inicial: peso de exposición .60, correlación .50, inicios .06–.70,
duraciones .16–.26, alcance 4 radios y densidad artística 1.15. No se afirman
tiempos del mundo real. Exposición es **apertura geométrica isotrópica**: no
depende de cámara, tiempo ni orientación del sol. No se modifica al cambiar
semilla estacional; sí lo hacen los tiempos/variación.

Reordenar los volúmenes no cambia los resultados. La curva puede evaluarse
directamente en cualquier fase, sin historial de animación. `weight()` rechaza
fases fuera de [0,1]; los extremos son 0/1 y la evolución es monótona.

## Datos generados

Esquema `schemas/tree-season-calendar-data.schema.json`:

- Versión de contrato/algoritmo, especie/fase, semilla, hash canónico del perfil
  y hash canónico de los volúmenes ordenados.
- Filas por ID con `start`, `duration`, `exposure`, `variation`, `order` y vecinos.
- IDs únicos, duración positiva, `start+duration≤1`, vecinos existentes y sin
  autoreferencias. Las tres láminas usan la misma fila, no calendarios propios.

Los hashes canónicos usan JSON con claves ordenadas y sin espacios; se distinguen
de hashes de archivo, que también se registran para congelar artefactos.

## Transporte y auditoría

`src/treegen/season_calendar_glb.py` crea una variante GLB, sin modificar la fuente:

- Añade **TEXCOORD_1 = (start, duration)**, float32 por vértice de follaje.
  En Godot se obtiene mediante `Mesh.ARRAY_TEX_UV2`; UV0 conserva la pintura.
  Exposición/variación/vecindad permanecen en el JSON por ID para futuras fases.
- Reserva UV2: rechaza un canal previamente ocupado o materiales que lo usen.
  No es un canal de lightmap. No regenerar UV de lightmap sobre este atributo;
  una necesidad futura de lightmaps requerirá otro transporte versionado.
- No añade `COLOR_0`, caras, superficies, materiales ni separaciones de vértices.
  No modifica normales. Los bytes de todo el bloque binario previo se conservan
  como prefijo exacto; posiciones, UV0, índices y PNG históricos quedan intactos.
- La asociación inicial usa posición+UV0 float32 de las láminas reconstruidas.
  Rechaza coincidencias entre IDs distintos, grupos incompletos, planos duplicados,
  vértices desconocidos y triángulos que mezclen grupos; exige seis tris por grupo.
- Metadatos GLB registran versión, hash del calendario y significado de UV2.
  Auditoría independiente contrasta atributos, estructura y binario histórico.

La comprobación de importación no supone índices/orden estables. Godot comprime
atributos: busca candidatos por posición y UV0, con cotas de .5 mm por coordenada
y 5e−5 UV, y exige **un solo ID**. Solo después compara UV2 con la fila del grupo,
tolerancia 3e−4, y seis caras por grupo. Nunca usa el calendario para adivinar
identidad geométrica. Se registran los errores máximos observados.

Blender invierte V al representar UV de glTF: su segundo canal se lee como
`(start, 1-duration)`. Se comprueba al importar y se reexporta otra prueba GLB,
que también se audita en Godot. No se exige igualdad binaria del reexportador.

Referencia del API de mallas:
[Mesh de Godot](https://docs.godotengine.org/en/stable/classes/class_mesh.html).

## Ejecución reproducible de T0/T1

```sh
python3 scripts/verify_season_calendar.py --output artifacts/estaciones/mi-calendario
# O separar preparación/Blender y revisión Godot:
python3 scripts/verify_season_calendar.py --output artifacts/estaciones/mi-calendario --stage build
python3 scripts/verify_season_calendar.py --output artifacts/estaciones/mi-calendario --stage review
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_season*.py'
```

Elegir una modalidad; `build` requiere carpeta nueva. `--source` permite seleccionar
la matriz de cuatro robles base, predeterminada en
`artifacts/roble-pintado/integracion-madera-01/`. Si falta, regenerarla con el
verificador histórico de madera como explica `docs/estaciones.md`.
`BLENDER_BIN` y `GODOT_BIN` permiten cambiar ejecutables compatibles.

Salida: referencias/recursos congelados, protocolo visual, calendarios/volúmenes,
bindings, GLB derivados, prueba de ida/vuelta Blender, informes de ambos motores,
capturas y láminas. Se verifican hashes de fuentes, recursos, proyecto e inputs
antes de revisar. Cada subproceso tiene un máximo de 180 s y puede terminarse.

T0 usa pintura fija de verano, otoño fijo, shader experimental normalizado a
roughness .95 en una copia y verano con atributos T1. Cinco vistas por versión
y cuatro árboles: 80 capturas. Alfa original por versión; no anticipa T2.
La variante con datos debe ser visualmente idéntica al verano en esas vistas.
Esta comprobación no evalúa una transición aún inexistente ni acepta la pintura.
