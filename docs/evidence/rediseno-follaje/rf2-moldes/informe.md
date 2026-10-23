# RF2: hojas sobre moldes Q3 invisibles

Fecha: 2026-10-22. Ensayo solicitado por el usuario tras revisar la rama
despoblada. [Plan](../../../../plans/rediseno-follaje.md) y
[contrato versionado antes de generar](../../../contrato-rf2-moldes.md).
Implementado y verificado técnicamente; revisión de imágenes reales realizada.
**Aprobación artística pendiente; RF3 sin iniciar.**

## Resultado revisable

- [Q3 frente a hexágonos .45/.8 m](hexagons.jpg).
- [Q3 frente a rombos .8/1 m](diamonds.jpg).
- [Ángulos y revisión anterior](angles.jpg), [escalas](scales.jpg) y
  [máscaras de follaje](masks.jpg).
- [Resumen técnico](summary.json), [moldes congelados](molds-lock.json),
  [preset hexagonal](hex-spec.json), [preset en rombo](diamond-spec.json),
  [43 pruebas](unit-tests.txt).

Galería completa: `artifacts/rediseno-follaje/rf2-moldes-final/index.html`.
Modelos `<caso>/branch.glb`, escenas `<caso>/scene.blend`, manifiestos y capturas
originales de 900×900. Candidato con más cobertura: `efficient-100`;
alternativa de menor escala: `efficient-080`. Son nombres del ensayo, sin
afirmación de rendimiento durante el juego ni promoción a producción.

## Construcción y condiciones

Se conserva la primaria 100 y secundarias 200–202: **464 triángulos de madera**
Q3 final, misma transformación, polígonos, sombreado y material. Se extraen
los componentes conectados de sus polígonos de follaje originales:
**nueve moldes y 300 triángulos guía**, con rama padre e índices fuente.
No se reconstruyen como esferas ni como un elipsoide aproximado.

El pool contiene 2048 muestras deterministas, proporcionales al área de los
triángulos. El área sumada de moldes es 127.70 m², incluyendo solapamientos;
no es el área de la unión exterior. En semilla 17, **977 muestras se descartan**
por estar dentro de otro molde y 1071 permanecen. Una selección progresiva por
distancia reparte los grupos sobre esa superficie expuesta. El tamaño de hoja
no participa en el muestreo ni en la elección de conexiones.

Cada grupo se conecta a la superficie de su propia rama Q3. La primera regla
usa un recorrido acodado hacia un tramo superficial interior al molde, con
hojas sobre ese tramo. La segunda usa un recorrido recto y coloca sus hojas
entre 75 y 98 % del mismo. El inset superficial es .08 m; las hojas se orientan
aproximadamente tangentes al molde, con giro y variación de inclinación ±30°.
Los tamaños tienen variación ±10 % por id. Las raíces permanecen dentro de
su tubo visible y las inserciones están sobre madera base.

**Los moldes no se exportan.** El GLB contiene solo madera Q3, conexiones
`RF2_Twig` y hojas `RF1_Leaf`: tres materiales opacos, hojas de doble cara,
propiedades de corteza iguales a la referencia. No hay núcleo verde ocultando
huecos ni cambio de iluminación para aparentar cobertura.

Se conservan las doce cámaras de la revisión RF2: seis ángulos generales,
tres detalles y tres escalas frontales fijadas desde la rama Q3 para ocupar
50/25/10 % del cuadro. Los acercamientos son recortes deliberados. Todas las
vistas son ortográficas; no equivalen a distancias físicas en perspectiva.
Godot mantiene luz (-35, -25, 0), energía 1.2 y ambiente .5; Blender mantiene
Workbench y el estudio RF0. No se reencuadran candidatos.

## Dos parejas y coste

La primera pareja conserva la hoja hexagonal plegada de cuatro triángulos:
16 grupos de tres hojas y tubos triangulares de tres anillos, 14 triángulos
por conexión. Solo cambia el tamaño nominal .45/.8 m. En Godot aún deja huecos
grandes y los codos de las conexiones son perceptibles. Esta ejecución inicial
`0.1.0`, con sus fuentes exactas, se conserva en
`artifacts/rediseno-follaje/rf2-moldes-01/sources/`.

Tras inspeccionarla se registra la revisión acotada `0.1.1`: tubo recto de
dos anillos y tapas (ocho triángulos) y rombo plano RF1 de dos triángulos.
Permite 24 grupos de cuatro hojas. La pareja .8/1 m conserva entre sí
recorridos, raíces, orientaciones, cantidad y coste. No cambia los límites
428 añadidos por rama, 10000 por árbol ni tres materiales.

| Caso | Hojas | Conexiones, triángulos | Hojas, triángulos | Total con base | Proyección de árbol¹ |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q3 de referencia | — | 0 | 300 | 764 | 8512, árbol Q3 existente |
| RF2 anterior, dirigido 12 | 48 | 168 | 192 | 824 | 9252 |
| Hexágonos .45/.8 m | 48 | 224 | 192 | 880 | 9868 |
| Rombos .8/1 m | 96 | 192 | 192 | 848 | 9516 |

¹ Para candidatos: `5292 + 11 × (conexiones + hojas)`, proyección aritmética
de viejo-09. No es un árbol generado ni asignación definitiva entre primarias.
RF3 deberá repartir por región/área y resolver solapamientos entre todas las
masas del árbol. El descarte actual solo considera los nueve moldes de esta rama.

La comparación entre parejas cambia forma, conexión, cantidad y organización:
no aísla la causa individual del resultado. Dentro de cada pareja el efecto
del tamaño sí está separado. El protocolo de ruido inicial se mantiene;
los dos hexágonos finales reconstruyen exactamente las métricas y recorridos
del ensayo inicial pese a ampliar el contrato.

## Cobertura proyectada y lectura

Máscaras de follaje a 256×256, calculadas desde posiciones/índices del GLB y
cámaras comunes, excluyendo madera. Cada porcentaje indica cuántos píxeles
del follaje Q3 coinciden con hojas del candidato. Se registra también IoU y
píxeles fuera de Q3 en el resumen. Se cuentan áreas unidas de triángulos,
sin iluminar, sin oclusión por madera y con cuantización de raster. No es
densidad volumétrica ni una nota de naturalidad.

| Caso | Frente | Lateral | Arriba | Abajo | Oblicua | Reverso |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RF2 anterior | 5.0 % | 5.5 % | 4.2 % | 3.9 % | 5.1 % | 5.1 % |
| Hexágono .45 m | 12.0 % | 13.5 % | 9.4 % | 10.8 % | 11.8 % | 11.8 % |
| Hexágono .8 m | 29.0 % | 30.7 % | 21.7 % | 27.1 % | 29.7 % | 29.7 % |
| Rombo .8 m | 42.8 % | 49.7 % | 40.3 % | 44.5 % | 49.6 % | 49.6 % |
| Rombo 1 m | 57.5 % | 63.4 % | 54.2 % | 58.6 % | 64.1 % | 64.1 % |

Se revisaron capturas Godot reales de los pares, detalles de conexiones,
ángulos generales y escalas. El método recupera extensión del volumen Q3 y
el rombo de 1 m conserva más presencia a media/lejana escala que las revisiones
previas. No requiere mostrar los moldes y tiene menor coste añadido que la
primera pareja. Esa diferencia observada queda limitada a esta rama.

Persisten huecos, hojas de canto y una lectura de láminas grandes. La variante
de 1 m parece más llena, pero sus piezas son grandes y angulosas; en detalle
algunas agrupaciones se leen como rombos o cometas superpuestas. La de .8 m
reduce ese tamaño y deja más huecos. Los tubos rectos evitan los codos largos,
pero siguen formando grupos radiales y pueden cruzarse visualmente. No se
declara resuelta la estética ni se elige una representación definitiva.

Siguiente paso: revisar tamaño/forma y continuidad de estos grupos sobre la
rama, conservando las comparaciones. La cobertura por sí sola no autoriza
RF3. Una eventual copa deberá distribuir el presupuesto global y considerar
las superficies interiores entre todas las primarias.

## Verificación y reproducción

Pasaron **43 pruebas**, seis nuevas para muestreo proporcional al área,
rechazo de superficie interior, independencia del tamaño, raíces/ejes,
semilla/selección anidada, límites, tubos cerrados y conteo de cobertura sin
confundir intensidad de píxel con cantidad. **11 GLB** se verificaron e
importaron en Godot; cuatro repeticiones en sesiones Blender independientes
conservan geometría, conexiones y colocaciones. Otra semilla modifica la
distribución y conserva la madera base; no es un control reservado de RF4.

La inspección independiente de GLB comprueba posiciones/normales de cada
triángulo de madera y material de corteza, firmas separadas de conexiones y
hojas, materiales, degenerados, ejes, cajas y escala. Las parejas conservan
también la firma exportada de sus conexiones. Las raíces se comprueban dentro
de sus tubos cerrados sobre mallas reales; el mayor error de inserción de los
casos nuevos es .000343 mm. La continuidad es geométrica, sin soldar Q3.
Las conexiones originales miden .65–2.27 m; las rectas, .38–1.74 m en semilla 17,
por debajo del nuevo máximo 4 m. Toda la geometría añadida queda en Z=0–9 m.

Seis escenas × doce vistas: **72 capturas Godot**, todas con geometría visible,
mínimo 1678 píxeles según el detector. Las demás escenas verifican repetición
o semilla sin capturas nuevas. No se mide FPS ni coste durante el juego.

Entorno: Blender 5.2.1 LTS `9e2066aef7ef`, Python Blender 3.13.13 y ejecutor
3.14.4; Godot 4.7.2 `ed1daf0bf`. Los manifiestos registran tiempos internos
y GLB de aproximadamente 36–40 kB para los casos nuevos. Generación antes de
render/exportación alrededor de .08 s, sin incluir arranque de Blender,
Godot ni ajuste humano. Generación ≤120 s, verificaciones/capturas ≤180 s
por subproceso terminable, lotes de dos escenas y sin reintentos automáticos.

```sh
python3 scripts/verify_foliage_molds.py --output artifacts/rediseno-follaje/otros-moldes --visual
python3 scripts/foliage_molds_evidence.py --study artifacts/rediseno-follaje/otros-moldes --output artifacts/rediseno-follaje/evidencia-moldes
```

Usar una carpeta nueva. `--rf0` cambia la ruta del bloqueo original;
`--preset` la configuración base experimental. La matriz fija explícitamente
sus tamaños, formas y conteos. BLENDER_BIN/GODOT_BIN permiten otras rutas de
las versiones fijadas. Sin `--visual` solo se comprueba geometría/importación;
el segundo comando requiere las capturas. Las fuentes y resultados históricos
Q3 y RF2 permanecen intactos. No se promocionan presets ni se inicia RF3.
