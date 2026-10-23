# Revisión RF2: ramillas visibles y región de copa

Fecha: 2026-10-22. [Plan activo](../../../../plans/rediseno-follaje.md).
Implementada y verificada técnicamente como `foliage-branch-0.2.0`.
La conexión se lee en el detalle de Godot; la organización todavía no forma el
volumen buscado. **Salida artística pendiente; RF3 sin iniciar.**

## Entregables y comparación

- [Pareja con/sin ramillas](connection.jpg): hojas y recorridos idénticos.
- [Distribución y seis ángulos](distribution.jpg), [controles](controls.jpg),
  [alcance de .55/.8 m](reach.jpg) y [escalas de lectura](scales.jpg).
- [Resumen técnico y firmas](summary.json), [región congelada](target-lock.json),
  [preset dirigido](directed-12-spec.json) y [37 pruebas](unit-tests.txt).

Galería completa: `artifacts/rediseno-follaje/rf2-ramillas-final/index.html`.
Modelos `<caso>/branch.glb`, escenas `<caso>/scene.blend`; manifiestos con
soportes, colocaciones, hashes, versiones, semillas, tiempos y tamaño GLB.
Las capturas originales de 900×900 permiten inspeccionar uniones a mayor escala
que estas láminas. El contrato se fijó antes de generar:
[contrato RF2 revisado](../../../contrato-rf2-ramillas.md),
[esquema](../../../../schemas/foliage-twigs.schema.json).

## Condiciones y separación de efectos

Se reconstruyen la primaria 100 y secundarias 200–202 desde los mismos polígonos
Q3 finales: **464 triángulos de madera**, conservando coordenadas, polígonos,
sombreado, transformación, corteza y normalización. El Q3 asociado contiene
300 triángulos de follaje: referencia de 764 en total. Los archivos históricos
`.blend`, GLB y manifiesto conservan sus hashes.

La pareja `without-twigs`/`with-twigs` tiene 16 soportes de .55 m y 64 hojas
hexagonales plegadas de .24 m, patrón longitudinal, semilla 17 y giro 0°.
El caso invisible coincide además con las métricas, soportes, colocaciones y
hash de madera del `longitudinal-r0-medium` histórico. No hay corrección oculta
de posiciones. Las hojas mantienen el material opaco de doble cara de RF1.

Cada ramilla es un tubo triangular cerrado de tres anillos: **14 triángulos**,
radio basal .012 m, final .003 m y prolongación de raíz .025 m dentro de la
madera. El recorrido permanece fijo; las raíces de hoja quedan dentro del tubo.
`RF2_Twig` copia las propiedades de `Oak_Bark` y permite identificar esta madera
por separado. Tres materiales en los candidatos visibles, dos en el invisible.
Se conservan los polígonos Q3 sin soldar ni remallar sus uniones.

Las nueve cámaras originales RF2 se conservan. Se añaden tres tomas frontales
comunes con escala ortográfica calculada desde la altura de la rama Q3 para
ocupar 50/25/10 % del cuadro; los candidatos no se reencuadran. Son escalas de
pantalla de una rama aislada, sin equivalencia con distancia perspectiva ni
prueba de una copa. Luz Godot: dirección (-35, -25, 0), energía 1.2 y ambiente
.5, como RF2; Blender conserva Workbench y su estudio original.

La distribución se prueba después de aislar la conexión. Antes de generar
candidatos se congela un elipsoide desde la caja del follaje Q3 asociado:
centro (4.1794, .5670, 3.3950) m y radios (3.0089, 2.3709, 1.9296) m.
No copia los sólidos Q3 ni exige su silueta exacta; sirve como primera guía
espacial explícita. Puede ser incompatible con el alcance de las ramillas.

Una rejilla 8×8×4 tiene **152 centros interiores**. Se consideran 24 inserciones
distales y ocho direcciones por inserción: 192 recorridos candidatos, sin
bifurcaciones adicionales. La selección voraz premia celdas nuevas a menos de
.28 m de los recorridos, una dirección por inserción, con desempate estable.
El conteo elige un prefijo; tamaño, densidad y orientación de hoja no cambian
los soportes. La semilla puede cambiarlos. La ocupación medida por centros
reales de hoja dentro de .28 m se registra aparte: ninguna cifra representa
cobertura proyectada, volumen foliar ni naturalidad.

## Coste y contribución espacial

| Caso | Soportes | Hojas | Ramillas, triángulos | Follaje, triángulos | Total con base | Proyección de árbol¹ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sin ramillas, original | 16 | 64 | 0 | 256 | 720 | 8108 |
| Con ramillas, original | 16 | 64 | 224 | 256 | 944 | 10572 |
| Dirigido, 16 | 16 | 64 | 224 | 256 | 944 | 10572 |
| Dirigido, 12 | 12 | 48 | 168 | 192 | 824 | 9252 |
| Densidad 12 hojas/m | 12 | 72 | 168 | 288 | 920 | 10308 |
| Largo .8 m, 9 hojas/m | 12 | 84 | 168 | 336 | 968 | 10836 |
| Largo .8 m, igual conteo | 12 | 48 | 168 | 192 | 824 | 9252 |

¹ `5292 + 11 × (triángulos de ramillas + hojas)`: cálculo aritmético para
viejo-09, no una copa generada ni una asignación válida para cada primaria.
El árbol dispone de 4708 triángulos para toda la geometría añadida; el máximo
de 768 añadidos por ensayo de rama no autoriza repetirlo once veces.

| Organización | Celdas alcanzables por el pool | Celdas del barrido seleccionado | Celdas próximas a centros reales de hojas |
| --- | ---: | ---: | ---: |
| Original, 16, .55 m | — | 7 | 6 |
| Dirigido, 16, .55 m | 24 | 15 | 12 |
| Dirigido, 12, .55 m | 24 | 14 | 10 |
| Dirigido, 12, .8 m, 9 hojas/m | 33 | 16 | 15 |
| Dirigido, 12, .8 m, igual conteo | 33 | 16 | 13 |

Las tres columnas son diagnósticos sobre las mismas 152 celdas, sin objetivo
porcentual de aceptación. La selección dirige mejor esa contribución dentro
de este pool, pero el conjunto alcanzable sigue siendo pequeño. La prueba de
.8 m fue añadida tras inspeccionar el primer ensayo; no es un control reservado.
El control de igual conteo usa 6 hojas/m para conservar cuatro hojas por
soporte: cambia recorrido, elección espacial y separación, conservando unidad,
cantidad, coste y región objetivo.

## Verificación y revisión visual

Pasaron **37 pruebas**, siete nuevas: pareja idéntica, selección reproducible
y anidada, independencia de controles, contribución espacial, trabajo acotado,
tubos cerrados con caras exteriores y firmas/normales de ramillas exportadas.
Hay **13 GLB válidos e importados en Godot 4.7.2**, y dos repeticiones en nuevas
sesiones Blender con geometría, ramillas y colocaciones idénticas. Los controles
de tamaño/densidad conservan la madera nueva; radio conserva las hojas; semilla
cambia recorridos sin alterar la base. El control de conteo conserva los doce
primeros soportes de la selección de dieciséis.

La inspección independiente del GLB conserva las posiciones y normales de
madera Q3 por triángulo, además de la firma del material de corteza. Ramillas y
hojas tienen firmas propias; la pareja conserva también la firma exportada de
las hojas. Se comprueban ejes, cajas, altura, materiales, números finitos,
índices y degenerados. La base sigue con transformación identidad y toda la
geometría añadida permanece entre Z=0 y Z=9 m sin renormalización.

Se comprueba cada inserción sobre Q3 y dentro de su tubo cerrado, y cada raíz
de hoja dentro de su propia ramilla usando cruces de la malla real. El mayor
error de inserción es **12.13 µm**, menor que la tolerancia de .1 mm. Las
intersecciones prueban continuidad geométrica de los sólidos/láminas; no son
una unión topológica soldada ni una validación estética automática.

Diez escenas tienen doce vistas: **120 capturas Godot**, todas con geometría
visible (mínimo 1678 píxeles según el detector). Se revisaron las imágenes reales
de la pareja en detalle, vistas inferiores, distribución desde seis ángulos,
controles de alcance, tamaño/radio/densidad y las tres escalas. Observaciones:

- Las ramillas hacen visible el trayecto desde Q3 a las hojas. En detalle la
  pareja deja de mostrar las mismas hojas como piezas suspendidas.
- Persisten hojas de canto y grupos pequeños separados. El dirigido redistribuye
  detalle, pero sigue concentrado alrededor de las ramas, con amplias zonas del
  objetivo vacías. La comparación general tiene mucha menos presencia que Q3.
- Alargar a .8 m extiende algunos grupos sin resolver el volumen. Conservar
  densidad añade hojas y supera la proyección de presupuesto; igualar conteo
  recupera el coste, pero tampoco da una copa legible. A media/lejana escala
  domina la madera y el follaje casi desaparece.
- Aumentar radio hace más visibles las conexiones sin ampliar el volumen; tamaño
  .32 m aporta placas mayores y densidad 12 más hojas. Ninguno demuestra por sí
  solo una solución artística viable.

La hipótesis de conexión visible tiene apoyo en este detalle acotado. La regla
de distribución ensayada **no cumple la salida visual RF2**: no se promueve a
RF3 ni se genera un árbol completo para disimular el fallo. El siguiente paso
es revisar alcance, zonas de inserción y reparto de área foliar por coste en
esta misma rama, contrastando la región objetivo con lo alcanzable. Si requiere
otro nivel de ramillas, mayores longitudes o una representación distinta, se
debe versionar y registrar ese cambio antes de generar. No se deduce un límite
general de las hojas opacas ni una mejora de IA o rendimiento.

## Entorno y reproducción

Blender 5.2.1 LTS `9e2066aef7ef`, Python Blender 3.13.13, ejecutor 3.14.4;
Godot 4.7.2 `ed1daf0bf`. Generación antes de render/exportación: .29–.72 s;
tiempo interno total .40–2.27 s según capturas; GLB 27–45 kB. No incluyen
arranque de Blender, importación/capturas Godot ni trabajo humano de ajuste.
No son medidas de FPS.

```sh
python3 scripts/verify_foliage_twigs.py --output artifacts/rediseno-follaje/otra-rama --visual
python3 scripts/foliage_twigs_evidence.py --study artifacts/rediseno-follaje/otra-rama --output artifacts/rediseno-follaje/evidencia
```

Usar una carpeta nueva. `--rf0` permite cambiar la ruta del bloqueo original y
`--preset` la configuración experimental; la matriz fija explícitamente los
valores de sus comparaciones. BLENDER_BIN/GODOT_BIN permiten cambiar rutas,
manteniendo las versiones verificadas. Sin `--visual` solo hay verificación
técnica/importación y el segundo comando no genera esta evidencia visual.

Generación limitada a 120 s; verificaciones/capturas a 180 s por subproceso,
grupos terminables y lotes de tres escenas, sin reintentos automáticos. Una
primera ejecución falló en el sandbox al abrir el socket de la prueba API;
se repitió con autorización fuera, donde pasaron las verificaciones. Un primer
ensayo completo sirvió para añadir los controles de alcance; la carpeta final
reproduce todos los casos y conserva hashes de las fuentes ejecutadas. Las
fuentes Q3/RF1/RF2 originales y sus resultados permanecen intactos.
