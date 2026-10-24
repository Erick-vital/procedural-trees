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
Hay dos tipos y cuatro versiones registradas. No hay selección “latest”.
El perfil predeterminado no elige el tipo: se aplica dentro de una receta
seleccionada explícitamente.

| Objetivo | Receta | Ejemplar existente |
| --- | --- | --- |
| Reproducir viejo-09 aprobado | `blueprints/roble_copa_ancha/1.0.0.json` | `presets/blueprints/roble-copa-ancha-viejo-09.json` |
| Joven revisado | `blueprints/roble_copa_ancha/1.2.0.json` | `presets/blueprints/b3-v2/joven-00.json` |
| Adulto revisado | `blueprints/roble_copa_ancha/1.2.0.json` | `presets/blueprints/b3-v2/adulto-00.json` |
| Segundo tipo columnar | `blueprints/arbol_copa_columnar/1.0.0.json` | `presets/blueprints/columnar/pilot.json` |

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

Solo viejo-09 de referencia está aprobado por el usuario. Otros perfiles de
roble 1.2.0 y `columna` tienen comprobaciones técnicas y revisión de capturas,
pero siguen `experimental`. La petición con cambios no hereda una aprobación
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

Añadir un tipo mediante `blueprints/<id>/<versión>.json` y ejemplares separados,
reutilizando solo componentes registrados. Definir objetivo y controles antes
de generar; no inventar un identificador de componente para activar código
arbitrario. Si la arquitectura requiere otra estrategia, implementarla y
versionarla explícitamente, con límites y regresión de los tipos anteriores.
[Ejemplo de reutilización B4](evidence/blueprints/b4/informe.md).

## Cierre y pendientes separados

B5 cierra la infraestructura mínima y su documentación, no la aceptación de
todos los assets. Se conserva el límite de 12500 triángulos/3 materiales para
blueprints y el valor histórico 10000 para TreeSpec. Las conexiones tienen
cota de 2048 intentos y el muestreo 8192 candidatos. Sin viento, LOD, bosque,
mediciones FPS ni generalización garantizada a todo el rango de parámetros.

**Decisión RF5 en B5: no ejecutar el lote de treinta.** Su generación, promoción
y aceptación quedan para una solicitud y decisión posterior, separadas de este
cierre y de las decisiones artísticas pendientes. [Informe B5](evidence/blueprints/b5/informe.md).
