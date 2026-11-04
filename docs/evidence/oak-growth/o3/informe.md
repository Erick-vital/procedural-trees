# O3: ramificación y porte libre del roble

Implementado y verificado el 2026-11-03, por petición de corregir A/B/C.
**Aceptación artística pendiente del usuario.** Madera sin hojas; O1/O2 y
recetas históricas conservadas. [Galería](../../../../artifacts/oak-growth/o3-validacion-03/index.html).

## Cambios y presupuesto

- A: once abanicos cortos terciarios con dos terminales: **660 triángulos**
  añadidos por caso, por debajo de los 700 autorizados. Su aporte es moderado:
  no se pretende reproducir una red botánica completa. Los límites por orden
  del preset gobiernan la topología base; este pase adicional tiene cupo global.
- B: brazos con 10 % del tropismo ascendente previo durante el recorrido y
  descenso por peso persistente. Las secundarias reciben búsqueda ascendente
  propia. Las cantidades/resoluciones de ramas base son las de O2 de la misma
  entrada; B/C no añaden triángulos.
- C: madurez alta acorta el eje, reduce la inclinación de los brazos superiores,
  extiende los inferiores y aumenta su sinuosidad. No se impone simetría ni se
  rellenan todos los sectores. Es un arquetipo gráfico de crecimiento libre.
- Cupo efectivo de A: min(700, 5415 − madera base), en grupos de 60 tris.
  Se conserva una reserva de 1584: cota analítica **6999**. La prueba de límite
  con madurez1/vigor1.2/competencia0/seed0 obliga a reducir el relleno a600
  (base4798, total5398; con reserva6982). No hay follaje integrado todavía.

## Comparación reproducible

Mismos presets salvo versión, semillas 3100–3104 para maduros y centenarios;
joven3100 como control. Cámaras, luz y escala comunes por pareja, cuatro vistas
del árbol desnudo y de tronco/primarias. Edades a altura visual normalizada.

| Caso | O2 | O3 | Incremento |
|---|---:|---:|---:|
| maduro-3100 | 3054 | 3714 | +660 |
| maduro-3101 | 3549 | 4209 | +660 |
| maduro-3102 | 2824 | 3484 | +660 |
| maduro-3103 | 3462 | 4122 | +660 |
| maduro-3104 | 3429 | 4089 | +660 |
| centenario-3100 | 3621 | 4281 | +660 |
| centenario-3101 | 4207 | 4867 | +660 |
| centenario-3102 | 3362 | 4022 | +660 |
| centenario-3103 | 3496 | 4156 | +660 |
| centenario-3104 | 3729 | 4389 | +660 |
| joven-3100 | 2332 | 2992 | +660 |

Un material de corteza compartida. El mayor caso del lote, 4867, más la
reserva da6451. Las cotas no certifican una copa futura ni rendimiento.

**263 pruebas, 124 comprobaciones de cierre**. Once pares exportados/reimportados,
centros de nacimiento conectados y todos los anillos iniciales embebidos según
la auditoría Blender. Estructura y ambos GLB repetidos por CLI idénticos.
Catorce GLB O2 coinciden con los hashes históricos de siete casos O2.
Generación O3 1.328–1.752 s por caso. [Datos y hashes](verification.json),
[pruebas](tests.txt).

Godot produjo **188 capturas**; se inspeccionaron **132**: once parejas completas
en cuatro vistas (88), primarias aisladas de maduro3100/3103 y centenario3100/3103
(32) y edades normalizadas (12). Las otras56 capturas de primarias quedaron
disponibles en la galería, sin afirmar inspección individual.

## Lectura visual y límites

Los abanicos agregan laterales intermedias y terminales visibles, conservando
huecos y variación. La reducción del aspecto podado es parcial: persisten
transiciones de brazos gruesos a ejes delgados y zonas abiertas. En maduros
3100/3103 el cambio de trayectoria es sutil; se conservan líderes superiores
ascendentes. En los cinco centenarios el porte se extiende claramente, con
brazos bajos más horizontales y eje más corto. Se mantienen tramos angulosos
propios de la malla y algunas superposiciones en proyección; las uniones son
piezas solapadas, no una malla soldada.

La elevación neta media de primarias / recorrido baja de .482–.544 a .436–.502
en maduros y de .510–.579 a .281–.387 en centenarios. El producto anchura×profundidad
normalizado aumenta 26.8–141.6 % en centenarios; describe la caja horizontal,
no el volumen ocupado ni acredita naturalidad o aprobación artística.

## Fallos conservados

El ensayo `o3-validacion-01` agotó120 s por cierre de audio Blender dentro
del sandbox. En `o3-validacion-02`, centenario3103 falló por un anillo de
primaria fuera de la tapa del tronco (12.74 mm). O3 incorpora un encaje
conservador por distancia del nacimiento a triángulos reales del padre,
procesando padres antes que hijos; limita radios sin añadir polígonos.
El lote03 repite todos los casos y pasa. La suite inicial dentro del sandbox
falló únicamente por el socket local de API; la ejecución final externa pasa.
Los intentos y logs regenerables permanecen en artifacts y /tmp.

## Reproducción

```sh
python3 scripts/verify_oak_branching.py --output artifacts/mi-o3
python3 scripts/verify_oak_branching.py --output artifacts/mi-o3 --stage review
python3 scripts/verify_oak_branching.py --output artifacts/mi-o3 --stage ages
PYTHONPATH=src python3 -m treegen generate-oak-growth \
  presets/oak-growth/0.3.0/maduro.json --seed 3100 --output artifacts/mi-o3-repeat
PYTHONPATH=src python3 -m unittest discover -s tests > /tmp/mi-o3-tests.txt 2>&1
python3 scripts/close_oak_branching.py --study artifacts/mi-o3 \
  --repeat artifacts/mi-o3-repeat --tests /tmp/mi-o3-tests.txt
```

El cierre automático deja la inspección visual pendiente; la revisión humana
o del agente se registra después de abrir las imágenes. Blender/Godot requieren
el entorno gráfico y permisos locales documentados. El siguiente paso es la
valoración del usuario antes de promover esta arquitectura o integrar follaje.
