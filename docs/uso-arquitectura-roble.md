# Roble por etapa de madurez — O1

Esta alternativa genera y exporta **madera sin hojas**. Cambia la arquitectura
principal del árbol y preserva el generador R4, los blueprints y los presets
históricos. Usa la corteza pintada aprobada; integrar una copa nueva es un trabajo
posterior. El objetivo de este hito es evaluar el árbol desnudo.

```sh
PYTHONPATH=src python3 -m treegen generate-oak-growth \
  presets/oak-growth/0.1.0/maduro.json --seed 3100 \
  --output artifacts/mi-roble-maduro
```

El directorio debe ser nuevo. Salidas: `bare/tree.glb` y `.blend` para el árbol
con cuatro órdenes; `scaffold/tree.glb` y `.blend` solo tronco/primarias, conservando
sus diámetros del árbol completo. `structure.json` contiene jerarquía, curvas,
radios, vigor, rol y demanda distal; `manifest.json`, versiones, hashes, límites
y métricas; `joins-audit.json`, comprobaciones de las uniones en Blender.

## Presets y madurez

`presets/oak-growth/0.1.0/{joven,maduro,centenario}.json` contiene etapas de referencia:
5/12/15 m y madurez .15/.65/.95. **Centenario no significa que el algoritmo simule
cien años**, ni que todo roble de esa edad tenga el mismo porte. Son perfiles de
estructura; vigor y madurez son variables separadas. No se fuerza senescencia,
huecos, poda o pérdida de ramas por cumplir una edad.

La madurez modifica dominancia apical, altura relativa del tronco, primeros
nacimientos, cantidad y direcciones de primarias, extensión de las órdenes
siguientes, sinuosidad, gravedad y diámetro basal. No se limita a escalar un
árbol. La etapa es una etiqueta descriptiva; `maturity` gobierna las reglas.

Se puede copiar un preset y ajustar sus controles explícitos, dentro del contrato:

| Control | Función / intervalo |
|---|---|
| `height_m` | Altura nominal 3–20 m; escala uniforme de los tres ejes |
| `maturity` | Etapa estructural continua 0–1 |
| `vigor` | Vigor general .65–1.2; combinado con campo regional y espacio |
| `crown_spread` | Extensión de ejes principales .8–1.4 |
| `curvature` | Amplitud de curvas correladas .08–.4 |
| `light_tropism` | Tendencia direccional a zonas altas/libres 0–.4; sin trazado de luz |
| `gravity` | Tendencia de descenso de brazos extendidos 0–.25 |
| `competition` | Peso de disponibilidad espacial 0–1 |
| `pipe_exponent` | Exponente de demanda distal a radio 2–3 |
| `basal_flare` | Ensanchamiento de la base 1–1.7 |
| `orders[].max_children` | Límite por orden: 8/3/2/2; frecuencias efectivas dependen del vigor/espacio |
| `orders[].branching_probability` | Frecuencia de desarrollo por orden .3–1 |
| `orders[].length_ratio` | Longitud respecto a altura o padre .25–.85 |
| `orders[].fork_angle_deg` | Ángulo de referencia 10–80°, variado suavemente; primarias respecto al eje vertical |
| `orders[].attachment_min` | Inicio de nacimientos laterales .2–.5 de longitud; primarias desplazan el inicio sobre tronco |
| `orders[].curvature_scale` | Intensidad relativa de curvatura .2–1.5 |
| `orders[].demand_weight` | Demanda propia adimensional .00005–.2; la carga de hijos también engrosa al padre |

Los límites `sides` y `points` son fijos por versión: primarias 6/9, secundarias
5/6, terciarias 4/5, terminales 3/3; tronco 8/13. No son un control libre de
subdivisión. Cota geométrica máxima **5156 tris de madera**; con una reserva
futura de 1584 tris de follaje, **6740**. Esta reserva no certifica todavía un
árbol con hojas. Un material en esta entrega, atlas compartido, generación
máxima 120 s. No se afirma mejora de FPS.

## Revisión reproducible

```sh
python3 scripts/verify_oak_growth.py --output artifacts/mi-estudio --stage generate
python3 scripts/verify_oak_growth.py --output artifacts/mi-estudio --stage references
python3 scripts/verify_oak_growth.py --output artifacts/mi-estudio --stage review
python3 scripts/verify_oak_growth.py --output artifacts/mi-estudio --stage ages
```

Matriz `configs/verification/oak-growth-v1.json`: cinco maduros, semillas3100–3104,
mismo preset; joven/centenario3100. `--case maduro-3100` selecciona un caso.
La referencia R4 usa las mismas semillas, perfil viejo, copa17/pintura2718. Solo
para presentar la comparación, su altura se ajusta uniformemente a la nominal
nueva, con factor registrado. La lámina de edades usa altura visual normalizada
y cámaras comunes. Los GLB guardados mantienen sus dimensiones reales.

Se requieren Blender y Godot según las rutas de los ejecutores; `BLENDER_BIN`
permite indicar Blender. La revisión exige interfaz gráfica. Semillas enteras
explícitas 0–2147483646; se rechazan campos desconocidos, no finitos y resoluciones
fuera del presupuesto. Las uniones son piezas solapadas con anillos iniciales
contenidos en el padre; no una superficie topológicamente soldada ni un cálculo
físico de cargas. El modelo es una aproximación gráfica, no un simulador botánico.

## Revisión O2: extensión y equilibrio de copa

La versión explícita **0.2.0** añade un freno de crecimiento por envolvente suave
y un presupuesto de recorrido por brazo. Conservar0.1.0 permite repetir la
comparación anterior. El mismo CLI acepta ambos contratos:

```sh
PYTHONPATH=src python3 -m treegen generate-oak-growth \
  presets/oak-growth/0.2.0/maduro.json --seed 3100 \
  --output artifacts/mi-roble-equilibrado
```

Los controles anteriores y la madurez siguen vigentes. `crown_balance` añade:

| Campo | Función / rango |
|---|---|
| `strength` | Fuerza de freno por extensión, 0–1; predeterminado .85 |
| `radius_ratio` | Radio horizontal de referencia / altura, .5–.9; .70 |
| `vertical_ratio` | Semialtura de la envolvente / altura, .38–.6; .48 |
| `path_ratio` | Presupuesto de recorrido por brazo / altura, .75–1.25; 1.0 |
| `irregularity` | Variación regional suave de la envolvente, .03–.18; .10 |

El radio y el recorrido efectivos también dependen de madurez. No se recortan ni
proyectan vértices sobre un contorno: cambia la longitud de crecimiento y la
preferencia de dirección. La envolvente limita excesos; no coloca ramas para
rellenar sectores. Las frecuencias, jerarquía, corteza y presupuesto geométrico
son los mismos que0.1.0. La disponibilidad espacial puede cambiar cuántas ramas
se desarrollan dentro de esos límites. El namespace aleatorio se mantiene0.1.0
expresamente; la versión del algoritmo/resultado se registra0.2.0.

```sh
python3 scripts/verify_oak_crown.py --output artifacts/mi-comparacion-o2
python3 scripts/verify_oak_crown.py --output artifacts/mi-comparacion-o2 --stage review
python3 scripts/verify_oak_crown.py --output artifacts/mi-comparacion-o2 --stage ages
```

La generación reconstruye **ambas versiones desde fuentes**, con el mismo preset
maduro salvo los controles de equilibrio nuevos, y las semillas3100–3104.
Incluye joven/centenario3100. Antes/después usan cámaras/luz comunes y escala1;
la lámina de edades normaliza únicamente la altura de presentación.

## Revisión O3: ramificación con presupuesto y brazos libres

`presets/oak-growth/0.3.0/{joven,maduro,centenario}.json` conserva controles O2,
con nuevas reglas de trayectoria por orden. Los brazos principales reciben una
fracción de la influencia ascendente y mantienen la caída por peso hasta el
extremo; las secundarias tienen mayor búsqueda ascendente. Con madurez alta se
acorta el eje y se extienden los brazos bajos, reduciendo la verticalidad de los
superiores. El perfil centenario es un arquetipo extendido de crecimiento libre.

Se conserva la topología base de O2 para la misma entrada. Se añaden abanicos
terciarios cortos con dos terminales, de60 triángulos cada uno, como máximo660
(once grupos), dentro del incremento autorizado de700. El límite efectivo es
min(700,5415−madera_base): con topología densa se reduce el relleno. Cota de
madera5415 + reserva1584 =6999. La reserva no es follaje ya implementado.
`structure.json.branching_budget` registra base, aumento y límites; el ejecutor
contrasta ese aumento con los triángulos reales del GLB.

```sh
PYTHONPATH=src python3 -m treegen generate-oak-growth \
  presets/oak-growth/0.3.0/centenario.json --seed 3100 \
  --output artifacts/mi-roble-extendido
python3 scripts/verify_oak_branching.py --output artifacts/mi-comparacion-o3
python3 scripts/verify_oak_branching.py --output artifacts/mi-comparacion-o3 --stage review
python3 scripts/verify_oak_branching.py --output artifacts/mi-comparacion-o3 --stage ages
```

La comparación reconstruye O2/O3: maduros y centenarios3100–3104 y joven3100,
cuatro vistas y primarias aisladas, cámaras/luz compartidas por pareja; etapas
a altura normalizada. O1/O2 siguen reproducibles. Aceptación artística pendiente.

## Revisión O4: distribución del volumen leñoso

`presets/oak-growth/0.4.0/{joven,maduro,centenario}.json` usa los controles de
O2/O3 con nuevas reglas de distribución. Los nacimientos laterales se separan
longitudinalmente sobre sus padres; los planos de bifurcación penalizan regresar
al núcleo. El cupo adicional se destina primero a secundarias ramificadas en
huecos intermedios de las primarias y después a ramillas más exteriores.

Seis unidades secundaria/terciaria/terminal de 100 tris más una unidad de 60
mantienen **660 tris respecto a O2** en los diez adultos ensayados; el joven
3100 usa 620. No se acumula otro incremento sobre O3. La reserva sigue siendo
1584 y el máximo completo 6999; el pase reduce sus unidades al faltar cupo.
Los límites por orden describen la base O2; el refuerzo usa el cupo global.

Cada brazo recibe un hábito reproducible: lateral, pesado, ascendente o sinuoso.
Sus descendientes heredan el hábito con variación menor. La madurez mezcla su
intensidad y añade asimetría de extensión por región; el ascenso deja de tener la
misma intensidad para todos. No son simulación física de cargas ni controles
botánicos calibrados. Los parámetros, atlas y versiones históricas se conservan.

```sh
PYTHONPATH=src python3 -m treegen generate-oak-growth \
  presets/oak-growth/0.4.0/centenario.json --seed 3100 \
  --output artifacts/mi-roble-o4
python3 scripts/verify_oak_volume.py --output artifacts/mi-comparacion-o4
python3 scripts/verify_oak_volume.py --output artifacts/mi-comparacion-o4 --stage review
python3 scripts/verify_oak_volume.py --output artifacts/mi-comparacion-o4 --stage ages
```

La evaluación distingue longitud de ejes secundarios y órdenes superiores en
núcleo (radio <.30H), franja media (.30–.50H) y periferia (≥.50H), además de
nacimientos y celdas ocupadas. Se integra longitud por segmentos con 16 muestras;
no cuenta vértices ni estima volumen de follaje. Las medidas describen esta
cohorte y no sustituyen revisar las capturas: maduro3100 pierde algo de longitud
periférica aunque despeja el centro. O3 permanece disponible para comparar.

## Revisión O5: aprovechar huecos exteriores con la misma malla

`presets/oak-growth/0.5.0/{joven,maduro,centenario}.json` conserva los controles
O4 y su topología completa. Un pase geométrico determinista examina hasta 27
candidatos por subárbol secundario: desplazar el nacimiento hasta .14 del
recorrido de su primaria, girar ±.28 radianes y escalar su recorrido hasta 1.24.
El movimiento es rígido con escala uniforme dentro del subárbol; los hijos
mantienen su relación con el padre. Se recalculan radios y encajes secundarios.
Tronco/primarias conservan puntos, diámetros y demás datos O4 exactamente.

La selección usa espacio ocupado en tres dimensiones. Rechaza aumentar longitud
o nacimientos del núcleo (<.30H), perder longitud/celdas periféricas (≥.50H),
superar altura nominal o exceder en más del 3 % el alcance horizontal máximo de los ejes O4.
Conserva el subárbol original si no hay ganancia; no añade ramas ni polígonos.
Los límites y decisiones se guardan en `structure.json.periphery`.

La regla se aplica a cualquier semilla: no contiene una excepción para 3100.
El criterio geométrico no garantiza naturalidad ni llenado visual completo;
comprobar capturas y posibles cruces sigue siendo necesario. El presupuesto
coincide exactamente con O4 para la misma entrada; reserva 1584 intacta.

```sh
PYTHONPATH=src python3 -m treegen generate-oak-growth \
  presets/oak-growth/0.5.0/maduro.json --seed 3100 \
  --output artifacts/mi-roble-o5
python3 scripts/verify_oak_periphery.py --output artifacts/mi-comparacion-o5
python3 scripts/verify_oak_periphery.py --output artifacts/mi-comparacion-o5 --stage review
python3 scripts/verify_oak_periphery.py --output artifacts/mi-comparacion-o5 --stage ages
```

`--case maduro-3100` permite generar o capturar por ejemplar. El cierre añade
controles geométricos 5000–5004, maduros y centenarios, sin usarlos para ajustar
reglas. Las capturas nuevas corresponden a los once casos históricos; distinguir
esos controles geométricos de validación visual y de exportación.
