# R3: dos variantes de rama, con y sin follaje

Fecha: 2026-11-03. **R2 elegida sin follaje; R3 con follaje implementada y verificada,
pendiente de valoración artística.** [Alcance](../../../../plans/f5-estructura-espacial.md),
[decisión del usuario sobre R2](../rama-r2/user-acceptance.json).

## Entrega y comparación

[Selección visual](seleccion.jpg), [rama sin follaje](bare.jpg),
[comparación cercana](near.jpg), [media](medium.jpg), [lejos](far.jpg),
[giro 1](orbit-0.jpg), [giro 2](orbit-1.jpg), [madera visible](visible-wood.jpg),
[máscaras de follaje](masks.jpg), [sombras](shadows.jpg), [auditoría](verification.json).
Galería local: `artifacts/f5/rama-r3-128-01/index.html`.

| Uso de la muestra | Variante | Madera | Follaje | Total | Materiales |
| --- | --- | ---: | ---: | ---: | ---: |
| Sin follaje, elegida por el usuario | R2 | 894 | 0 | **894** | 1 |
| Con follaje, referencia anterior | R2 | 894 | 522 | 1416 | 2 |
| Con follaje, nueva candidata | R3 | 802 | 522 | **1324** | 2 |

La nueva variante reduce **92 triángulos más: −6,50 % total / −10,29 % de madera**
respecto a R2 con follaje. Respecto a R1 de 1700 tris, la reducción total acumulada
es **−22,12 %**. Los porcentajes se refieren a esta rama, no a árboles completos.

Assets autocontenidos:

- Sin follaje: `artifacts/f5/rama-r3-128-01/bare/tree.glb` y `.blend` editable.
- Con follaje: `artifacts/f5/rama-r3-128-01/simple/tree.glb` y `.blend` editable.
- Registro explícito de uso/rutas/hashes: [chosen-variants.json](chosen-variants.json).

La muestra descubierta usa exactamente la madera R2 aceptada; no se sustituye
por la madera interior más reducida de R3. Esa elección amplía el uso artístico
propuesto inicialmente para R2. Las verificaciones históricas no se reescriben ni
se convierte esa aceptación en una validación de otros estados, semillas o edades.
La integración de las variantes en árboles completos sigue pendiente.

## Simplificación adicional

Se mantienen **87 grupos / 261 láminas / 522 triángulos de follaje**: mismas
posiciones, caras, UV, normales, plantilla, pintura y parámetros de material.
El alfa de renderizado tampoco se cambia. Atlas y recetas históricas conservados.
Las semillas/procedencia siguen siendo las de la muestra R1/R2: base 1003, copa 17,
pintura 2718; no se añade una inferencia de modelo al repetir.

La selección usa el clasificador R2 intacto y un preprocesado explícito solo de
su alfa de entrada. Se prueban dos umbrales de cobertura cruda: **160/255** y
**128/255**. La máscara derivada 0/255, su hash y el umbral quedan registrados en
`alpha-profile.json`; esa máscara se usa para rayos, no se incorpora a los GLB.
El clasificador conserva sus cuatro texeles de cobertura y 74 direcciones.

Después de la poda se contraen bifurcaciones interiores que no están expuestas:
se elimina un tramo oculto y sus hijos ocultos se conectan directamente a su
padre. Cada segmento sustituto se vuelve a clasificar contra la copa. Si alguno
asoma se rechaza la propuesta; también se impide tocar las mallas expuestas,
los nacimientos o superar tres hijos en el nuevo nodo. Máximo tres rondas,
selección determinista y sin mover los extremos de las ramas visibles.

Perfil 128: 62 tramos protegidos por exposición; 113→112 tramos tras la poda,
lo que ahorra cuatro triángulos. Se aceptan nueve contracciones en la primera
ronda y dos en la segunda; la tercera no acepta cambios. Las once contracciones
ahorran otros 88 tris. Quedan **101 tramos de red, 662 tris**, más 140 tris del eje
principal intacto: 802 tris de madera. La madera sigue conectada a su eje;
no se eliminan ancestros dejando ramillas visibles flotantes.

| Candidato | Total con follaje | Comprobación geométrica | Comprobación visual |
| --- | ---: | --- | --- |
| Alfa 160 | 1328 | Correcta | No ejecutada; respaldo de mayor coste |
| Alfa 128 | **1324** | Correcta | Correcta bajo el protocolo; seleccionado técnicamente |

Se evalúa primero el de menor coste y solo se adopta técnicamente si conserva
las máscaras de madera visible y follaje en Godot. No fue necesario usar el
respaldo 160 ni ajustar la selección después de mirar el giro.

## Validación

- **233 pruebas** correctas. Las dos nuevas pruebas cubren contracciones,
  conexión a padres, conservación de terminales/mallas protegidas, rechazo de
  segmentos no declarados ocultos, nacimientos, IDs inválidos y determinismo.
- **26 comprobaciones de integración** correctas; cinco GLB auditados y cinco
  repeticiones binariamente idénticas. La referencia con follaje reproduce R2
  exactamente. La exportación sin hojas conserva las caras/UV de madera R2.
- **26 pares de máscaras de madera visible idénticas**, sin pérdida ni ganancia
  de píxeles rojos. Tres distancias, seis orientaciones y ocho posiciones de giro
  desde abajo; el diagnóstico tiene madera visible real, no imágenes vacías.
- **Seis pares de máscaras de follaje idénticas** y GLB de follaje aislado
  binariamente idénticos. Pintura y alfa exportados se conservan.
- **25/26 pares normales idénticos**; `orbit-04` cambia un píxel de 810 000,
  delta máximo por canal 13/255. Tres parejas de sombra en suelo, con luces
  diferentes y encuadre completo, son idénticas.
- El GLB sin follaje se importó y capturó explícitamente en Godot: un material,
  894 tris, texturas/UV/normales y escala verificadas; seis vistas revisadas.

**146 capturas finales**, de las que el agente inspeccionó **88 imágenes únicas
seleccionadas** en las láminas enlazadas. El resto tiene comprobación numérica,
sin presentarlo como inspección visual exhaustiva. En la selección no se aprecia
pérdida de plenitud, silueta o ramas visibles con follaje. R2 descubierta conserva
la lectura elegida por el usuario. Las vistas cercanas amplían detalle y pueden
recortar bordes; media/lejos permiten revisar el conjunto completo. Cámaras y luz
idénticas por pareja, sin autoencuadre independiente para ocultar diferencias.

Este resultado acredita las condiciones ensayadas de una rama, no invisibilidad
universal, rendimiento gráfico ni naturalidad general. R3 nueva sigue pendiente
de valoración artística; no se asume aprobada por la similitud de píxeles.

## Reproducción

Requiere R2 en `artifacts/f5/rama-r2-03/`; seguir primero la
[reproducción de R2](../rama-r2/informe.md) si falta. Desde la raíz:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
python3 scripts/verify_branch_foliated.py --stage generate --cutoff 128 --output artifacts/f5/otra-rama-r3
python3 scripts/verify_branch_foliated.py --stage review --output artifacts/f5/otra-rama-r3
python3 scripts/close_branch_foliated.py --stage render --study artifacts/f5/otra-rama-r3
```

El respaldo 160 se regenera con el mismo comando `generate`, `--cutoff 160` y
otra carpeta nueva. Para seleccionar evidencia, guardar la suite en
`logs/tests.log` de la muestra y ejecutar `close_branch_foliated.py --stage evidence`
con `--study` y `--output`. Esa selección espera el respaldo geométrico en
`artifacts/f5/rama-r3-160-01/`, como en esta ejecución. Las entradas, propuestas,
rechazos, fuentes/hashes y alfa derivado se conservan bajo la carpeta de resultado.
Cada generación se limita a 120 s y cada subproceso de revisión a 180 s, terminables.

La primera prueba unitaria usó una red pequeña sin bifurcaciones interiores
contraíbles; se corrigió el fixture a 36 destinos, manteniendo la protección de
terminales, sin cambiar el algoritmo para el caso real. La suite final pasa 233/233.
No hay fallos de generación/exportación o visibilidad en el candidato elegido.

No se cambian los alias de producción, no se integran árboles completos ni se
inicia F6. R1, R2 y los generadores por nodos siguen conservados. La adaptación
por estados de follaje o su conmutación automática en Godot no se implementa
por entregar estos dos assets explícitos.
