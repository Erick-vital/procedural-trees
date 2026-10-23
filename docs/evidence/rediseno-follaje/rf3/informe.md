# RF3: primera copa completa de viejo-09

Fecha: 2026-10-23. `foliage-canopy-0.1.0`, implementada y verificada
técnicamente. Revisión de imágenes reales en Godot realizada; **aprobación
artística de copa pendiente**. RF4/RF5 sin iniciar. Se parte de la
[rama RF2 de 144 hojas aprobada](../rf2-densidad/aceptacion.json), bajo el
[plan activo](../../../../plans/rediseno-follaje.md) y el
[contrato RF3 fijado antes de generar](../../../contrato-rf3-copa.md).

## Entregables

- [Q3 frente al piloto](comparison.jpg), [controles espaciales](controls.jpg),
  [escalas](scales.jpg), [detalle](detail.jpg) y [control de tamaño](leaf-size.jpg).
- [Máscaras de follaje](masks.jpg), [resumen técnico](summary.json),
  [referencia congelada](reference-lock.json), [preset piloto](pilot-spec.json)
  y [51 pruebas](unit-tests.txt).

Galería completa: `artifacts/rediseno-follaje/rf3-acceptance-02/index.html`.
Árbol piloto: `pilot/tree.glb` y `pilot/tree.blend` dentro de esa carpeta.
Cada candidato tiene manifiesto, parámetros, recorridos/colocaciones,
firmas, tiempos y capturas originales 900×900. La referencia es `reference/`.

## Base Q3 y construcción global

Se usa viejo-09 Q3 0.4.0, semilla estructural de entrada 3009, altura 9 m.
La **madera completa de 5292 triángulos** se extrae de los polígonos originales,
conservando coordenadas, orden, polígonos/sombreado, transformación y corteza.
Tres evaluaciones de los canales nativos identifican tronco, once primarias y
33 secundarias. Sus vértices se cotejan con la malla guardada; el mayor error
de reconstrucción auxiliar es .954 µm. Se guardan los índices fuente y se
comprueba que las 45 piezas cubren exactamente toda la madera sin duplicarla.

Se extraen **89 moldes Q3 originales y 3220 triángulos guía**, incluyendo sus
relaciones con la madera. Los moldes quedan fuera del GLB y de la escena final
del candidato. No se añade núcleo verde para tapar huecos ni se remalla Q3.

El muestreo global tiene 8192 intentos proporcionales al área. En el piloto,
5244 muestras se descartan por estar dentro de otro molde y 2948 quedan
expuestas. El descarte considera todas las primarias. El área sumada guía es
1325.41 m², incluyendo solapamientos; no representa el área exterior de la unión.

Se divide la superficie por norte/este/sur/oeste respecto al centro horizontal
de la caja Q3, usando el eje dominante. Se reparten 264 grupos según muestras
expuestas con restos mayores: **66/70/65/63 grupos**. Dentro de cada región,
la selección progresiva por distancia separa los grupos sobre la superficie.
Es una regla artística acotada, sin simulación botánica ni anticolisiones.

Se conserva la representación RF2 aprobada: tubo recto triangular de ocho
triángulos, radio .02→.005 m, penetración de raíz .04 m y seis hojas por grupo.
Las seis posiciones reproducen las cuatro hojas originales y dos adiciones
RF2, mismo protocolo de ruido por id. Rombo opaco de dos triángulos, tamaño
nominal 1 m con ±10 %, giro e inclinación ±30°, doble cara y sin texturas.
La equivalencia de representación con RF2 está comprobada por prueba unitaria;
las colocaciones globales cambian por el nuevo reparto y descarte entre masas.

Se rechazan grupos completos que excederían la altura; no se recortan las
hojas ni se renormaliza la base. El piloto necesita 294 intentos de conexión:
29 rechazados por altura y uno por longitud, hasta completar 264. Toda la
geometría final permanece entre Z=0 y Z=9 m.

## Coste y controles

| Caso | Grupos | Hojas | Madera base | Conexiones | Follaje | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Q3 | — | — | 5292 | 0 | 3220 | 8512 |
| Piloto | 264 | 1584 | 5292 | 2112 | 3168 | **10572** |
| Perfil ancho ×1.12 | 264 | 1584 | 5292 | 2112 | 3168 | 10572 |
| Ocupación este ×.4 | 222 | 1332 | 5292 | 1776 | 2664 | 9732 |
| Hojas .75 m | 264 | 1584 | 5292 | 2112 | 3168 | 10572 |

El presupuesto se limita **antes** del mallado: `5292 + grupos×20 ≤12500`.
El máximo contractual de 360 grupos daría 12492. El piloto deja 1928
triángulos disponibles; no se rellena ese margen automáticamente.
Tres materiales: `Oak_Bark`, `RF2_Twig` y `RF1_Leaf`; corteza y conexiones
tienen iguales propiedades exportadas.

El control ancho transforma X/Y de los moldes alrededor del centro fijo y
recalcula superficies expuestas, reparto y conexiones; conserva Z y toda la
madera base. No es una escala aplicada al árbol completo ni mantiene sus
colocaciones. El control de ocupación baja el cupo este de 70 a 28 grupos,
dejando presupuesto sin usar. **Las otras tres regiones conservan exactamente
sus grupos**, incluidos ids, posiciones y conexiones. Sus pesos permanecen en 1.

El control de tamaño conserva soportes, raíces, orientaciones y conteos.
Planifica altura con la escala piloto congelada de 1 m y representa las hojas
a .75 m para aislar ese efecto; las conexiones exportadas son idénticas.
Otra semilla de follaje modifica la distribución, conservando toda la madera
Q3 y sus parámetros/semillas estructurales. No es un control reservado de RF4.

## Comparación visual

Se conservan las nueve cámaras RF0 del árbol y tres detalles de la rama RF2,
comunes a todos los casos, a 900×900. Las escalas 50/25/10 % son ortográficas,
sin equivalencia con distancias de una cámara perspectiva. No hay vértices
fuera de cuadro en las nueve vistas generales de los candidatos. Los detalles
son recortes intencionados, registrados por separado en cada manifiesto.

Godot mantiene luz (-35, -25, 0), energía 1.2 y ambiente .5. Blender conserva
Workbench y su estudio original. Los brillos de renderizadores distintos no
se usan como métrica. Se revisaron imágenes reales de las parejas, ángulos
superiores/inferiores, detalles, controles y las tres escalas:

- El piloto conserva presencia y organización general de la copa, con contorno
  más fragmentado, hojas reconocibles y huecos. La lectura se diferencia de
  las masas cerradas Q3; a media/lejana escala mantiene una copa legible.
- El perfil ancho extiende la copa sin deformar la madera. Reducir ocupación
  este abre esa zona, visible en frente/arriba y en las tomas inferiores.
- Las hojas siguen siendo grandes y angulosas; en detalle persisten láminas
  superpuestas, cruces de conexiones y algunas hojas de canto. La de .75 m
  muestra más huecos y madera, sin constituir una elección aprobada.
- No se declara superioridad artística ni de rendimiento. La aprobación de
  la rama no se convierte automáticamente en aceptación de este árbol.

Diagnóstico desde los GLB, con máscaras de follaje a 256×256, excluyendo
oclusión por madera: el piloto cubre 91.7–94.0 % de la proyección Q3 en seis
ángulos generales. IoU de 83.9–87.6 %, sin exigir la silueta Q3 exacta. Abrir
este reduce cobertura a 86.0–90.7 %; hojas .75 m a 75.9–83.5 %. Estas cifras
miden proyección, no volumen foliar, naturalidad ni aceptación. Son condiciones
del árbol completo, distintas del ensayo de rama.

## Verificación e incidencia corregida

Pasaron **51 pruebas**, seis nuevas para equivalencia RF2, reparto regional,
perfil, muestreo/rechazos, altura y límite explícito de exportación RF3. El
valor histórico por defecto sigue siendo 10000; RF3 solicita 12500 de forma
explícita, sin cambiar los contratos ni presets históricos.

**Siete GLB** exportados/importados en Godot: referencia, piloto, perfil ancho,
ocupación este, tamaño de hoja, repetición y semilla. Las posiciones y normales
por triángulo de madera y su material coinciden con el **GLB Q3 original**,
además de cotejar la referencia reexportada. Se comprueban polígonos/sombreado,
transformación identidad, parámetros base, semillas, normalización, índices,
áreas, materiales, altura y concordancia entre GLB y malla evaluada.

La repetición independiente conserva geometría, conexiones y colocaciones.
Las fuentes originales y sus tres artefactos de referencia conservan sus
hashes. Cinco escenas con doce vistas suman **60 capturas Godot**, todas con
geometría visible (mínimo 5860 píxeles según el detector). Las otras dos
escenas verifican repetición/semilla sin nuevas capturas.

La primera verificación se detuvo en el control ancho por el comprobador RF2
de raíces: su rayo fijo casi paralelo al tubo recorría más de .15 m desde un
punto interior y lo rechazaba. RF3 usa ahora los semiespacios de las ocho caras
del tubo recto convexo, sobre sus coordenadas de malla, con tolerancia 1 µm.
Todas las raíces tienen distancia firmada negativa a cada cara; la menor
holgura está alrededor de 2.74 mm. Se conserva el caso que exhibe un trayecto
de rayo largo como diagnóstico. La geometría del piloto antes/después de esta
corrección es idéntica: se corrigió la evaluación, sin mover las uniones.

El mayor error de inserción sobre la madera Q3 en los casos finales es 1.22 µm,
menor que la tolerancia .1 mm. Las conexiones son sólidos superpuestos a Q3;
no se sueldan sus topologías ni se afirma ausencia de intersecciones internas.

## Reproducción y siguiente paso

Blender 5.2.1 LTS `9e2066aef7ef`, Python Blender 3.13.13, ejecutor 3.14.4 y
Godot 4.7.2 `ed1daf0bf`. Casos capturados: generación antes de render/exportación
.82–.92 s y total interno 2.86–3.20 s; GLB 382–435 kB. Esos tiempos excluyen
arranque, importación/capturas Godot y ajuste humano; no son FPS del juego.

```sh
python3 scripts/verify_foliage_canopy.py --output artifacts/rediseno-follaje/otra-copa --visual
python3 scripts/foliage_canopy_evidence.py --study artifacts/rediseno-follaje/otra-copa --output artifacts/rediseno-follaje/evidencia-copa
```

Usar una carpeta nueva. `--preset` cambia el contrato piloto; los controles
fijan explícitamente anchura 1.12, peso este .4, tamaño .75 y semilla 18.
`--rf0`/`--acceptance` permiten otras rutas a las referencias congeladas.
Generación ≤120 s, Godot/verificaciones ≤180 s por subproceso terminable,
lotes de dos escenas y sin reintentos automáticos. Sin `--visual` hay
verificación/importación, sin imágenes para el segundo comando.

Siguiente paso: revisión del árbol completo y elección de configuración para
RF4. Solo después se aplicará la regla a otras edades/semillas y controles
reservados. No se ha generado un lote ni promocionado un preset normal.
