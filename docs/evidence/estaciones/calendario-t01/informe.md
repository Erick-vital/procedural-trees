# T0/T1 — referencias congeladas y calendario por grupo

Fecha: 2026-11-01. **T0 y T1 implementadas y verificadas** por solicitud del
usuario. T2–T6 pendientes; sin mezcla de pinturas, caída ni cambio de normales.
[Plan](../../../../plans/transiciones-estacionales.md),
[contrato y comandos](../../../contrato-calendario-estacional.md).

## T0: referencias y protocolo

Cuatro casos del roble 2.2.0 auditados contra receta, petición, recursos,
geometría exportada y hashes de grupos/placements. Fuentes presentes, por lo
que no hizo falta regenerar los árboles base. Recursos copiados a `frozen/`;
hashes de fuentes, entradas, datos, GLB y proyecto comprobados antes de revisar.

Se congelan verano, pintura otoñal 0.1.0 y shader experimental. Comparación
Godot con rugosidad **.95** común: el .88 del shader histórico se normaliza solo
en una copia derivada, sin cambiar la fuente. Misma cámara/luz/fondo, exposición
1, tonemapping lineal, 900²/MSAA4, sol 1.2 y ambiente .5; recorte .5, doble cara
y filtro anisotrópico con mipmaps. [Protocolo](protocol.json).

Precisión de alcance: igualar configuración de alfa no iguala las máscaras de
las dos pinturas; se conserva esa diferencia histórica. Preparar máscara común
es trabajo de T2, no adelantado en esta entrega. La fase queda fijada en [0,1]:
verano→otoño de copa llena, sin pretender un año completo.

[Referencias de los cuatro árboles](references.jpg), inspeccionadas visualmente.
Conservar la referencia no constituye aceptación artística de la pintura nueva.

## T1: contrato, algoritmo y transporte

Perfil nuevo `configs/seasons/roble-calendario-v1.json`, contrato 1.0 y receta
de calendario 0.1.0. Validadores/esquemas estrictos, recursos por hash y semilla
estacional 1101. Contratos históricos sin relajar ni modificar.

Algoritmo independiente de Blender/Godot: volúmenes elipsoidales de grupos,
hasta 24 vecinos y 12 rayos; apertura geométrica isotrópica, azar por ID estable
y correlación espacial. Cada grupo obtiene inicio/duración, exposición, orden
y variación; sus tres láminas comparten calendario. Curvas suaves monótonas con
extremos exactos y acceso directo a cualquier fase, sin estado temporal mutable.

Transporte elegido: **TEXCOORD_1 = (inicio, duración)**, accesible como UV2 en
Godot. Resto de campos por ID en JSON. No se usa color de vértices para datos,
ni se añade un material por grupo. UV2 reservado, no válido para lightmap.

Auditoría binaria mantiene todo el buffer histórico como prefijo exacto y
conserva posiciones, UV0, índices, normales, atlas, materiales y escena. Sin
separar vértices ni añadir caras. Rechaza correspondencias ambiguas, vértices
sin grupo, planos duplicados y caras que mezclen IDs.

| Caso | Base/copa/pintura | Tris | Grupos | Datos de atributo añadidos |
| --- | --- | ---: | ---: | ---: |
| Piloto | 3009/17/2718 | 6812 | 264 | 25504 bytes |
| Joven-07 | 1007/17/2718 | 3132 | 264 | 25440 bytes |
| Adulto-00 | 2000/17/2718 | 5820 | 264 | 25376 bytes |
| Viejo-00 | 3000/17/2718 | 6900 | 264 | 25520 bytes |

Todos: **dos materiales y 792 láminas**. Los tamaños anteriores solo cuentan
float32 UV2; el GLB también añade pequeños bloques JSON/metadatos.
Preparación de cada caso más auditoría/reexportación Blender: 2.997–3.160 s
observados, sin equipararlo a benchmark de ejecución ni a generación original.

## Verificaciones

**27 pruebas pasan:** 21 de estaciones/pintura/calendario y seis de cruzadas
históricas. Las nuevas pruebas cubren entradas inválidas, recursos/hash, límites,
determinismo, reordenación, semilla independiente, apertura frente a ocupación,
extremos/monotonía y rechazo de corrupción de datos/geometría/materiales.

**37 comprobaciones pasan:** nueve por caso y una global. Incluyen exactitud de
grupos/placements, repetición de calendario y GLB, independencia de semilla,
curvas, importación Blender, importación Godot y ausencia de cambio visible.

- Cuatro importaciones Blender 5.2.1: 264 grupos cada una, UV2 auditados por
  geometría y caras, sin confiar en índices. Cuatro reexportaciones GLB.
- Godot 4.7.2 importa directamente los derivados y esas cuatro reexportaciones:
  **264/264 grupos**, cero vértices sin correspondencia, seis caras por grupo.
- Godot comprime atributos: diferencia máxima de posición frente al float32
  de origen **.23973 mm por coordenada** y de UV2 **1.52439e−5**. Auditoría con
  cotas de .5 mm, 5e−5 UV0 y 3e−4 UV2; requiere ID único antes de comparar datos.
  No se decide identidad mirando los propios valores del calendario.
- **80 capturas reales**, cuatro casos, verano/pintura/shader/datos y cinco
  vistas. Las **20 parejas verano original/con datos son píxel a píxel idénticas**.
  Selecciones `references.jpg` y `transport.jpg` inspeccionadas por el agente.
- Fuentes y artefactos congelados coinciden también después de la revisión.
  `git diff --check` sin errores. Sin cambios en infraestructura histórica común.

[Verificación con hashes](verification.json),
[comprobaciones adicionales](additional-checks.json),
[comparación del transporte](transport.jpg).

## Observaciones y límites

El joven tiene exposición calculada .00245–.33346 frente a .23025–.83652 del
piloto: sus grupos pequeños y densos quedan más ocluidos en esta aproximación.
En la fase normalizada sus inicios son más tardíos (.42387–.63647 frente a
.22673–.52516). Es un resultado de reglas comunes, **no una afirmación botánica**;
su conveniencia artística se juzgará al animar en T3, sin retoque por semilla.

No se revisó una animación inexistente ni se preparó máscara común. Tampoco se
ensayó luz solar física, otra especie, normales de volumen, sombra de suelo
separada, FPS ni todas las alturas admitidas por la receta histórica. El aspecto
actual con datos es intencionalmente el del verano original.

Ensayo 01 falló por una importación innecesaria de jsonschema en Blender y su
cierre de audio bloqueado dentro del sandbox; el subproceso se terminó a 180 s.
Ensayo 02 reveló que comparar claves de coordenadas redondeadas no toleraba la
compresión de Godot. Se corrigió la auditoría; **03 es la ejecución final válida**.
No se contaron esos fallos como verificaciones exitosas.

## Reproducción y siguiente paso

Salida final: `artifacts/estaciones/calendario-t01-03/`; cada carpeta de caso
contiene `calendar.json`, `volumes.json`, `binding.json`, `tree.glb` y reportes.
Proyecto de comprobación en `godot/`, recursos en `frozen/` y entradas en `inputs/`.
Los reportes guardan semillas, versiones, hashes y significado del atributo.

```sh
python3 scripts/verify_season_calendar.py --output artifacts/estaciones/otra-t01
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_season*.py'
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_oak_crossed*.py'
```

La comprobación requiere ejecución con acceso a interfaz Godot; en este entorno
se ejecutó fuera del sandbox por las restricciones de audio/sockets. Cada
subproceso está limitado a 180 s. [Contrato completo](../../../contrato-calendario-estacional.md).

**Siguiente paso T2:** atlas compatibles con máscara común y ensayo de halos,
mostrando hojas/rama antes de adoptar el árbol. T3 mezcla los dos RGB usando el
calendario ya preparado. Shader anterior y pintura original siguen experimentales.
