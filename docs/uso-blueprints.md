# Uso del sistema de blueprints

Comandos desde la raíz del repositorio, con el entorno de [README](../README.md).
Cada salida de generación debe ser una carpeta nueva, incluso después de un
fallo. La CLI termina con código 1 ante errores y conserva manifiesto/log.

## Seleccionar una receta y un ejemplar

```sh
PYTHONPATH=src python3 -m treegen blueprints
```

La respuesta lista `id`, `version`, nombre, perfil predeterminado, ruta y hash
canónico de cada receta registrada en `blueprints/<id>/<versión>.json`.
Hay tres tipos y nueve versiones registradas. No hay selección “latest”.
El perfil predeterminado no elige el tipo: se aplica dentro de una receta
seleccionada explícitamente.

| Objetivo | Receta | Ejemplar existente |
| --- | --- | --- |
| Reproducir viejo-09 aprobado | `blueprints/roble_copa_ancha/1.0.0.json` | `presets/blueprints/roble-copa-ancha-viejo-09.json` |
| Joven revisado | `blueprints/roble_copa_ancha/1.2.0.json` | `presets/blueprints/b3-v2/joven-00.json` |
| Adulto revisado | `blueprints/roble_copa_ancha/1.2.0.json` | `presets/blueprints/b3-v2/adulto-00.json` |
| Segundo tipo columnar | `blueprints/arbol_copa_columnar/1.0.0.json` | `presets/blueprints/columnar/pilot.json` |
| Pino cónico experimental | `blueprints/pino_conico/1.0.0.json` | `presets/blueprints/pino/pilot.json` |
| Pino con estructura revisada | `blueprints/pino_conico/1.1.0.json` | `presets/blueprints/pino-v2/pilot.json` |
| Pino pintado con madera optimizada | `blueprints/pino_conico/2.2.0.json` | `presets/blueprints/pino-pintado-madera/pilot.json` |
| Pino pintado con volumen reforzado | `blueprints/pino_conico/2.1.0.json` | `presets/blueprints/pino-pintado-volumen/pilot.json` |
| Pino pintado con cruzadas | `blueprints/pino_conico/2.0.0.json` | `presets/blueprints/pino-pintado/pilot.json` |

`roble_copa_ancha` 1.1.0 y `presets/blueprints/b3/` conservan el ensayo inicial
con fallos documentados; para los controles corregidos usar 1.2.0. El nombre de
carpeta `b3-v2` de los ejemplares revisados no es una versión de receta: su JSON
solicita explícitamente 1.2.0. `configs/verification/b3-v3.json` es la matriz
final correspondiente. El cierre no renombra esas entradas históricas.

## Generar y validar

Referencia aprobada:

```sh
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/roble_copa_ancha/1.0.0.json --instance presets/blueprints/roble-copa-ancha-viejo-09.json --output artifacts/blueprints/roble-a --no-render
PYTHONPATH=src python3 -m treegen validate artifacts/blueprints/roble-a
```

Joven revisado y segundo tipo:

```sh
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/roble_copa_ancha/1.2.0.json --instance presets/blueprints/b3-v2/joven-00.json --output artifacts/blueprints/joven-a --no-render
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/arbol_copa_columnar/1.0.0.json --instance presets/blueprints/columnar/pilot.json --output artifacts/blueprints/columna-a --no-render
PYTHONPATH=src python3 -m treegen validate artifacts/blueprints/columna-a
```

Omitir `--no-render` añade vistas Blender. `--timeout` puede reducir el tiempo;
para blueprints nunca supera el límite de la receta (actualmente 120 s), aunque
se solicite un valor mayor. No hay reintentos ni sobrescritura automática.
La validación se ejecuta también al generar y comprueba el GLB y su concordancia
con el manifiesto. No equivale a una aceptación artística.

Resultados: `tree.glb`, `tree.blend`, entrada y resolución congeladas en
`input.json`/`manifest.json`, cámaras, datos base de inspección y log. El GLB usa
metros, Y arriba en Godot; Blender usa Z arriba. La conversión exportada es
`(x,y,z) → (x,z,−y)`. Las guías invisibles no forman parte del GLB.

## Perfil, semillas y cambios permitidos

Un ejemplar es un JSON independiente. Ejemplo columnar, con campos reales:

```json
{
  "schema_version": "1.0",
  "blueprint_id": "arbol_copa_columnar",
  "blueprint_version": "1.0.0",
  "profile": "columna",
  "seeds": {"base": 4100, "canopy": 73},
  "overrides": {"canopy": {"leaf_length_m": 0.35}}
}
```

Guardar una copia en una ruta nueva y pasarla con `--instance`; no es necesario
modificar el catálogo. La precedencia es receta → perfil → cambios del ejemplar.
Solo se aceptan campos de `editable_ranges`, sus intervalos y las restricciones
conjuntas de componentes/presupuesto. Una combinación permitida por intervalos
puede fallar al intentar construir su geometría.

`seeds.base` deriva streams de estructura y moldes Q3; `seeds.canopy` dirige
la distribución y variación del follaje RF3. Ambas quedan registradas, junto
con las semillas efectivas. Cambiar exclusivamente la semilla de copa conserva
la madera base. Cambiar tamaño de hoja con planificación fija conserva soportes,
raíces y ejes en los controles verificados. No confundir `base.foliage_scale_m`
(tamaño de moldes) con `canopy.leaf_length_m` (hoja visible).

Viejo-09 y los perfiles joven/adulto/viejo B3 revisados están aprobados por el
usuario desde el 2026-10-23. [Decisión posterior a B5](evidence/blueprints/b3-revision/user-acceptance.json).
Se conserva la receta 1.2.0 exacta y su metadato histórico `experimental`; la
aprobación queda documentada aparte y abarca los casos revisados. `columna`
continúa experimental. Cambios o nuevas semillas no heredan aprobación
artística. [Contrato completo](contrato-blueprints.md).

## Repetir y comparar

Con las mismas recetas/ejemplares del catálogo, generar en otra carpeta:

```sh
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/roble_copa_ancha/1.0.0.json --instance presets/blueprints/roble-copa-ancha-viejo-09.json --output artifacts/blueprints/roble-b --no-render
PYTHONPATH=src python3 -m treegen compare artifacts/blueprints/roble-a artifacts/blueprints/roble-b --output artifacts/blueprints/comparacion-roble
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/arbol_copa_columnar/1.0.0.json --instance presets/blueprints/columnar/pilot.json --output artifacts/blueprints/columna-b --no-render
PYTHONPATH=src python3 -m treegen compare artifacts/blueprints/columna-a artifacts/blueprints/columna-b --output artifacts/blueprints/comparacion-columna
```

`compare` produce `comparison.json` y `index.html`: distingue igualdad de
especificación, entorno, fuentes, cámaras y geometría. **No falla por encontrar
una diferencia**: hay que revisar `same_spec`, `same_environment`, `same_sources`,
`same_cameras` y `same_geometry`. Con `--no-render`, el HTML indica vistas no
generadas; siguen disponibles los diagnósticos geométricos.

Para repetir las entradas exactas guardadas aunque cambie el catálogo, extraer
receta y petición del manifiesto a una carpeta separada:

```sh
python3 - <<'PYREPEAT'
import json
from pathlib import Path
manifest = json.loads(Path('artifacts/blueprints/roble-a/manifest.json').read_text())
resolved = manifest['resolved_blueprint']
destination = Path('artifacts/blueprints/entradas-congeladas')
destination.mkdir(parents=True, exist_ok=False)
for filename, key in [('recipe.json', 'blueprint_definition'), ('instance.json', 'instance_request')]:
    (destination / filename).write_text(json.dumps(resolved[key], indent=2) + '\n')
PYREPEAT
PYTHONPATH=src python3 -m treegen generate-blueprint artifacts/blueprints/entradas-congeladas/recipe.json --instance artifacts/blueprints/entradas-congeladas/instance.json --output artifacts/blueprints/roble-congelado --no-render
PYTHONPATH=src python3 -m treegen compare artifacts/blueprints/roble-a artifacts/blueprints/roble-congelado --output artifacts/blueprints/comparacion-congelada
```

Esto congela **datos de entrada**, no instala código ni herramientas antiguos.
Para reproducibilidad completa también deben coincidir fuentes y entorno
registrados. No se ejecuta código contenido en recetas ni se carga un plugin
arbitrario desde el JSON.

## Predeterminados e historial

La ruta de uso actual es `generate-blueprint` con receta y ejemplar explícitos.
El inicio rápido conserva 1.0.0 y viejo-09 como referencia aprobada; no hay
promoción automática a 1.2.0 ni al segundo tipo.

Los comandos `generate`, `batch` y la API histórica reciben **TreeSpec**,
un contrato diferente, y mantienen disponibles sus versiones:

| Ruta | Significado tras B5 |
| --- | --- |
| `presets/joven.json`, `adulto.json`, `viejo.json` | Alias TreeSpec de Q3 0.4.0 aprobada, idénticos a `v0.4.0/` |
| `presets/v0.4.0/` y `presets/q3-cases.json` | Familia poligonal Q3 explícita |
| `presets/v0.4.1/` y `presets/q3b-cases.json` | Q3b rechazada, acceso histórico explícito |
| `presets/v0.1.0/` … `v0.3.0/` | Fases anteriores, sin reinterpretación |
| `presets/f2-cases.json` | Lote F2 histórico 0.1.0; valor por defecto conservado de `batch` |

Ejemplo individual del contrato antiguo, ahora sin selección accidental de Q3b:

```sh
PYTHONPATH=src python3 -m treegen generate presets/adulto.json --output artifacts/q3/adulto-alias --no-render
PYTHONPATH=src python3 -m treegen generate presets/v0.4.0/adulto.json --output artifacts/q3/adulto-explicito --no-render
PYTHONPATH=src python3 -m treegen compare artifacts/q3/adulto-alias artifacts/q3/adulto-explicito --output artifacts/q3/comparacion-alias
```

Para reconstruir deliberadamente Q3b, pasar `presets/v0.4.1/adulto.json`.
Esto no la convierte en una opción recomendada. Los tres archivos Q3b que
ocupaban las rutas sin versión se archivaron byte por byte antes del cambio.
No se modificaron algoritmos, parámetros, semillas ni recetas de blueprint.

La API local sigue aceptando `POST /jobs` con `{spec, render}` de TreeSpec;
no incorpora entrada blueprint. `GET /jobs/<id>` consulta estado y
`GET /jobs/<id>/manifest.json` devuelve metadatos. Un servidor por carpeta,
solo loopback, sin reanudación/reintentos. [Comandos de API e historia](operacion-historica.md).
No se anuncia un endpoint que no existe.

`batch` conserva su compatibilidad F2 y requiere treinta TreeSpec; no es una
interfaz de lote RF3/blueprints. Consultar [operación histórica](operacion-historica.md)
para sus verificadores. Ninguna orden de B5 lanza ese lote.

## Evaluar o añadir una receta

B3 y B4 incluyen verificadores con capturas Godot reales:

```sh
python3 scripts/verify_blueprint_controls.py --matrix configs/verification/b3-v3.json --output artifacts/blueprints/otra-matriz-b3 --visual
python3 scripts/verify_second_blueprint.py --output artifacts/blueprints/otra-matriz-b4 --visual
```

Esas matrices comparan con referencias/evidencia histórica; la generación
individual no las necesita. El verificador de cierre comprueba dos tipos y
la selección de Q3 desde una copia sin `docs/`/`artifacts/` previos:

```sh
python3 scripts/verify_blueprint_closure.py --output artifacts/blueprints/otro-cierre
```

Añadir un perfil de desarrollo mediante `profiles` y sus `overrides`, declarando
los parámetros editables en `editable_ranges` y fijando controles por semilla.
Si cambian los resultados de una receta publicada, crear otra versión; conservar
la referencia anterior. Para otra representación del follaje, registrar una
estrategia versionada en código y su compatibilidad en los contratos; verificar
presupuesto previo al mallado, contactos, exportación y regresión del roble.
Cambiar solo el identificador en JSON no implementa una representación.

Añadir un tipo mediante `blueprints/<id>/<versión>.json` y ejemplares separados,
reutilizando solo componentes registrados. Definir objetivo y controles antes
de generar; no inventar un identificador de componente para activar código
arbitrario. Si la arquitectura requiere otra estrategia, implementarla y
versionarla explícitamente, con límites y regresión de los tipos anteriores.
[Ejemplo de reutilización B4](evidence/blueprints/b4/informe.md).

## Pino experimental

```sh
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/pino_conico/1.0.0.json --instance presets/blueprints/pino/pilot.json --output artifacts/blueprints/pino-a --no-render
PYTHONPATH=src python3 -m treegen validate artifacts/blueprints/pino-a
python3 scripts/verify_pine.py --output artifacts/blueprints/pino-matriz --visual
```

La receta y sus ejemplares usan contrato **1.1**, perfil `conico`, componentes
propios de estructura por pisos, distribución distal y acículas radiales.
No acepta parámetros de roble, ni se pueden mezclar sus componentes.
Sus controles están en `presets/blueprints/pino/`; la matriz fija cuatro semillas
con parámetros comunes y comprueba repetición, controles de follaje, contactos
en GLB reimportados, regresión del roble/columnar y vistas reales Godot.

`base` incluye altura/radio, inicio de copa, pisos, ramas por piso, anchura,
ascenso, irregularidad y longitud relativa de ramillas. `canopy` controla
cantidad par de acículas por soporte y sus dimensiones. Semilla de copa y
tamaño de acícula conservan madera; cambiar estructura o longitud de ramilla
puede cambiarla. La repetición desde manifiesto usa el mismo procedimiento
de extracción de `blueprint_definition` e `instance_request` descrito arriba.
El `base_spec` de pino es un dato interno del blueprint, **no un TreeSpec**
para `generate`, `batch` o API histórica.

[Resultado y límites](evidence/blueprints/pino/informe.md): 12 m, 11924 triángulos,
dos materiales, cuatro semillas verificadas y aceptación artística pendiente.
No se garantizan todas las combinaciones de rangos ni otras edades.

La revisión estructural **1.1.0** conserva el follaje y los parámetros, con
estructura `pine-whorls@0.2.0`: salidas desfasadas, inclinaciones variadas y
ramillas menos simétricas. [Comparación y resultados](evidence/blueprints/pino-revision/informe.md).

```sh
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/pino_conico/1.1.0.json --instance presets/blueprints/pino-v2/pilot.json --output artifacts/blueprints/pino-revisado --no-render
python3 scripts/verify_pine.py --matrix configs/verification/pine-v2.json --output artifacts/blueprints/comparacion-pino --visual
```

En la galería comparativa, `pilot` y `control-01/02/03` son la revisión 1.1.0;
`before-` indica 1.0.0 y `-wood` muestra madera sin follaje. Los números de
control identifican semillas. Ambas recetas siguen experimentales.

## Lote RF5 de treinta robles

Matriz explícita `configs/verification/rf5-v1.json`: los treinta casos Q3, diez
por edad, receta 1.2.0 y copa 17 común. Usa el ejecutor de blueprints, no `batch`.

```sh
python3 scripts/verify_rf5.py --output artifacts/rediseno-follaje/otro-rf5 --visual
python3 scripts/rf5_evidence.py --study artifacts/rediseno-follaje/otro-rf5 --output artifacts/rediseno-follaje/otra-evidencia-rf5
```

[RF5 ejecutada y verificada](evidence/rediseno-follaje/rf5/informe.md): treinta
GLB correctos, sin ajustes por semilla, regresión contra Q3 y galería Godot.
El informe incluye reconstrucción de referencias si falta `artifacts/` y
distingue las vistas de escala física común de las relativas a la altura.
El usuario aprobó el lote completo el 2026-10-23: [aceptación RF5](evidence/rediseno-follaje/rf5/user-acceptance.json).
Se conserva como alternativa explícita; los predeterminados TreeSpec permanecen.

## Cierre y pendientes separados

B5 cierra la infraestructura mínima y su documentación, no la aceptación de
todos los assets. Se conserva el límite de 12500 triángulos/3 materiales para
blueprints y el valor histórico 10000 para TreeSpec. Las conexiones tienen
cota de 2048 intentos y el muestreo 8192 candidatos. Sin viento, LOD, bosque,
mediciones FPS ni generalización garantizada a todo el rango de parámetros.

B5 no ejecutó el lote RF5. Después del cierre, el usuario aprobó B3 revisada y
autorizó su ejecución el 2026-10-23. El lote ya está ejecutado/verificado y
aprobado artísticamente; la aceptación posterior se registra aparte. [Cierre histórico B5](evidence/blueprints/b5/informe.md).

## Pino pintado PP4

La alternativa `pino_conico` **2.0.0** usa el contrato 1.2, el atlas/corteza
versionados y la estructura 0.2.0. Piloto y tres controles conocidos de 12 m,
sin overrides ni ajustes por semilla; aceptación artística pendiente.

```sh
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/pino_conico/2.0.0.json --instance presets/blueprints/pino-pintado/pilot.json --output artifacts/pino-pintado/mi-piloto --no-render
python3 scripts/verify_painted_pine.py --output artifacts/pino-pintado/mi-pp4 --visual
```

La primera orden produce `tree.glb` autocontenido, `.blend` con pintura
empaquetada, manifiesto, recursos resueltos y `placements.json`. La segunda
genera cuatro pinos, cuatro referencias 1.1.0, repetición y cambio de semilla
de pintura; comprueba también regresiones roble B0 y columnar B4. No necesita
resultados anteriores en `artifacts/`. `BLENDER_BIN` y `GODOT_BIN` permiten
seleccionar ejecutables; se mantienen límites 120/180 s. Las capturas requieren
escritorio real. Sin `--visual` solo hay comprobación técnica.

La galería muestra `before-` (1.1.0), `new-` (2.0.0) y `wood-` (madera retenida).
Nueve cámaras comunes por asset, incluyendo escalas 24/48/120 m.
En su proyecto Godot se incluyen escenas `new-pilot.tscn` y
`new-control-01/02/03.tscn`, con `painted_pine_asset.gd` para aplicar filtrado
anisotrópico y sombras dobles fuera del visor. Se pueden copiar las escenas,
sus GLB y el script juntos. Para un GLB generado con la primera orden, copiar
el script desde `godot/` y adjuntarlo a la raíz importada. Configurar MSAA 4×
en el viewport de destino para reproducir las capturas. El GLB por sí mismo
conserva PNG, UV, rugosidad, doble cara y MASK .5.

La semilla `paint=2718` selecciona variantes sin mover geometría; `canopy`
conserva la identidad histórica del caso y no añade aleatoriedad a los anclajes.
Repetir desde manifiesto exige conservar los PNG con sus hashes registrados;
no se regenera la pintura. Extracción de receta/petición igual al procedimiento
común. [Informe, comparación y límites](evidence/pino-pintado/pp4/informe.md).


Revisión de volumen solicitada: **2.1.0**, mismos recursos y madera, 435 grupos
cruzados/7520 triángulos. Refuerzo creciente arriba, segunda cruzada por
secundaria y tres grupos en el eje, sin cambios por caso. Para generar usar
`blueprints/pino_conico/2.1.0.json` y
`presets/blueprints/pino-pintado-volumen/pilot.json`. Comparación contra 2.0.0:

```sh
python3 scripts/verify_painted_pine.py --matrix configs/verification/pine-painted-volume-v1.json --output artifacts/pino-pintado/mi-volumen --visual
python3 scripts/pine_volume_evidence.py --study artifacts/pino-pintado/mi-volumen --evidence artifacts/pino-pintado/mi-evidencia-volumen
```

En esta matriz `before-` es 2.0.0 y `new-` es 2.1.0. La matriz PP4 inicial
sigue predeterminada para conservar su reproducción. [Resultados y límites](evidence/pino-pintado/pp4-volumen/informe.md).


La revisión **2.2.0** optimiza la madera con anillos adaptativos a 5 mm y tapas
interiores verificadas; conserva los recorridos. Aplica después un ajuste leve
de copa (longitud .98/anchura .94), común a los cuatro casos, conservando los
435 grupos y anclajes. Generar con `blueprints/pino_conico/2.2.0.json` y
`presets/blueprints/pino-pintado-madera/pilot.json`.

```sh
python3 scripts/verify_painted_pine.py --matrix configs/verification/pine-painted-wood-v1.json --output artifacts/pino-pintado/mi-madera --visual
python3 scripts/pine_wood_evidence.py --study artifacts/pino-pintado/mi-madera --evidence artifacts/pino-pintado/mi-evidencia-madera
```

En esta matriz `before-` = 2.1.0, `new-` = 2.2.0, `wood-` = madera nueva y
`before-wood-` = madera anterior. [Resultados, tolerancias y límites](evidence/pino-pintado/pp4-madera/informe.md).

La revisión **2.3.0** reduce cada cruzada de 12 a 6 tris, con la misma madera
y pintura 2.2.0, y estrecha cada grupo por sqrt(.9): −10 % de envolvente por grupo,
longitud/anclajes fijos. Piloto y tres controles: 4518–4554 tris, regla común.

```sh
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/pino_conico/2.3.0.json --instance presets/blueprints/pino-pintado-laminas/pilot.json --output artifacts/pino-pintado/mi-pino-laminas --no-render
```

Verificación: `configs/verification/pine-painted-cards-v1.json` mediante
`scripts/verify_painted_pine.py --visual`; aislamiento de topología mediante
`scripts/verify_pine_cards_topology.py --study RUTA`. Galería seleccionada:
`artifacts/pino-pintado/pp4-cards-02/index.html`. `before-` = 2.2.0;
`new-` = 2.3.0; `topology-` = soporte anterior con igual anchura nueva.
[Resultados, reproducción y límites](evidence/pino-pintado/pp4-laminas/informe.md).

### Comparación de rendimiento 1.1.0/2.3.0 en Godot

El benchmark compara el pino geométrico anterior al pintado con el pino pintado
aprobado. Configuración explícita: `configs/verification/pine-performance-v1.json`;
no cambia materiales, mallas ni recetas de producción.

```sh
python3 scripts/benchmark_painted_pine.py --output artifacts/pino-pintado/mi-benchmark
python3 scripts/pine_performance_evidence.py --study artifacts/pino-pintado/mi-benchmark --evidence artifacts/pino-pintado/mi-evidencia-rendimiento
```

Requiere sesión gráfica/GPU; no se acepta llvmpipe ni un render headless como
medición. Por defecto reutiliza los GLB históricos con hashes verificados en
`artifacts/blueprints/pine-v1.1-review-01/` y `artifacts/pino-pintado/pp4-cards-02/`.
Si faltan, los regenera con recetas/semillas congeladas y Blender. Rutas alternativas
mediante `--baseline-source` y `--source`. Calentamiento y captura se excluyen;
VSync/límite FPS/LOD automático desactivados, render interno 1080p y ventana 720p.
`--smoke` comprueba el arnés con cuatro árboles y tiempos breves, sin constituir
benchmark. `--analyze-only` recalcula los resúmenes de una ejecución ya terminada.

[Resultado medido, condiciones y límites](evidence/pino-pintado/rendimiento-v11/informe.md):
128 árboles 353→589 FPS; 512, 126→228 FPS en RTX 5060/1080p/MSAA4/sombras.
