# Árboles procedurales con blueprints

Python/Blender → GLB → Godot. El sistema mínimo de blueprints está cerrado
**técnicamente en B5**: dos tipos, recetas versionadas, semillas explícitas,
ejecutor común, manifiestos y repetición comprobada. La referencia RF3
viejo-09 está aprobada por el usuario; los perfiles nuevos y el tipo columnar
siguen experimentales. El lote de treinta RF5 no se ejecutó.

[Estado vigente](ESTADO.md) · [Guía de uso](docs/uso-blueprints.md) ·
[Contrato](docs/contrato-blueprints.md) · [Plan y cierre](plans/sistema-blueprints.md)

## Inicio rápido: referencia aprobada

Desde la raíz, con el entorno fijado disponible, usar carpetas de salida nuevas:

```sh
PYTHONPATH=src python3 -m treegen blueprints
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/roble_copa_ancha/1.0.0.json --instance presets/blueprints/roble-copa-ancha-viejo-09.json --output artifacts/blueprints/mi-roble --no-render
PYTHONPATH=src python3 -m treegen validate artifacts/blueprints/mi-roble
```

`--no-render` omite vistas Blender; el GLB y los controles técnicos se generan
igual. Omitirlo produce las vistas de inspección. Las capturas reales Godot
pertenecen a los verificadores de cada fase.

## Dos tipos y versiones explícitas

| Receta | Uso y estado |
| --- | --- |
| `roble_copa_ancha` 1.0.0 | Referencia viejo-09 aprobada: 9 m, 10572 triángulos, 1584 hojas |
| `roble_copa_ancha` 1.1.0 | Ensayo B3 inicial conservado, con fallo extremo registrado; no es la revisión recomendada |
| `roble_copa_ancha` 1.2.0 | Controles B3 corregidos y hoja joven .45 m; perfiles experimentales |
| `arbol_copa_columnar` 1.0.0 | Segundo tipo, 12 m y 11756 triángulos; cuatro semillas verificadas, experimental |

La CLI requiere **ruta exacta de receta y JSON de ejemplar**. No selecciona
“latest” ni cambia a un tipo experimental al omitir una versión. Las semillas,
perfil y cambios permitidos están en el ejemplar; el perfil predeterminado se
aplica únicamente dentro de la receta elegida.

Segundo tipo:

```sh
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/arbol_copa_columnar/1.0.0.json --instance presets/blueprints/columnar/pilot.json --output artifacts/blueprints/mi-columnar --no-render
PYTHONPATH=src python3 -m treegen validate artifacts/blueprints/mi-columnar
```

La [guía](docs/uso-blueprints.md) explica los perfiles, cambios, repetición desde
entradas o manifiesto, comparación, errores, API y acceso a versiones históricas.

## Predeterminados resueltos en B5

- Los alias TreeSpec `presets/joven.json`, `adulto.json` y `viejo.json` apuntan
  ahora a **Q3 0.4.0**, la familia poligonal previamente aprobada.
- Sus contenidos Q3b anteriores se conservaron byte por byte en
  `presets/v0.4.1/`. Q3b 0.4.1 continúa accesible como versión histórica rechazada.
- `generate` y la API reciben TreeSpec explícito; `generate-blueprint` recibe
  receta y ejemplar. Los alias TreeSpec no se convierten en documentos blueprint.
- `batch` conserva el lote F2 histórico como valor por defecto; los lotes
  históricos se seleccionan con `--cases`. Esa interfaz no ejecuta RF5/RF3.

No se promueven perfiles nuevos por cerrar la infraestructura. Tampoco se
modifican recetas, geometría, presupuestos o límites de trabajo de B2–B4.

## Entorno y resultados

| Herramienta | Versión comprobada |
| --- | --- |
| Blender | 5.2.1 LTS, build `9e2066aef7ef`; Python 3.13.13 |
| Python de orquestación | 3.14.4 |
| jsonschema / Pillow | 4.19.2 / 12.1.1 |
| Godot | 4.7.2 stable official, `ed1daf0bf` |

Dependencias Python en [requirements.txt](requirements.txt). Rutas locales en
`src/treegen/runner.py` y `scripts/verify_foliage_unit.py`; se pueden sustituir
con `BLENDER_BIN` y `GODOT_BIN`. Generación de blueprint ≤120 s; pruebas y
capturas ≤180 s por subproceso terminable. Fuera del sandbox cuando bloquee
API loopback, audio de Blender o sesión gráfica Godot.

Cada trabajo conserva `tree.glb`, `tree.blend`, `input.json`, `manifest.json`,
log, cámaras y referencia base regenerable. El manifiesto fija receta completa,
versión/hash, perfil, semillas, parámetros, entorno y hashes de fuentes/artefactos.
`artifacts/` está ignorado; evidencia seleccionada en `docs/evidence/`.

## Verificación y evidencia

| Fase | Evidencia y alcance |
| --- | --- |
| B0–B2 | [Referencia y migración](docs/evidence/blueprints/b0/informe.md), [generación integrada](docs/evidence/blueprints/b2/informe.md) |
| B3 revisada | [Edades, controles y contactos](docs/evidence/blueprints/b3-revision/informe.md); 80 pruebas y 270 capturas |
| B4 | [Reutilización en copa columnar](docs/evidence/blueprints/b4/informe.md), [comparación visual](docs/evidence/blueprints/b4/identity.jpg); 83 pruebas y 108 capturas |
| B5 | [Cierre, predeterminados y reproducción](docs/evidence/blueprints/b5/informe.md) |

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/verify_blueprint_closure.py --output artifacts/blueprints/otro-cierre
```

El cierre comprueba catálogo, generación, validación y repetición de los dos
tipos desde copia sin resultados/evidencia previos, y equivalencia del alias
Q3 con su archivo versionado. Reutiliza las revisiones visuales B3/B4; no crea
un lote ni declara una nueva aprobación artística.

## Alcance que permanece abierto

La decisión actual es **no ejecutar RF5 como parte de B5**. Su ejecución y
aceptación requieren una decisión posterior separada. Tampoco se incorporan
viento, LOD, bosque, terreno o los experimentos IA F4–F6 del
[plan v1](plans/v1-generador-arboles.md). Las edades son perfiles artísticos;
los rangos permitidos no acreditan todas sus combinaciones ni rendimiento FPS.

[Operación histórica F0–RF3](docs/operacion-historica.md) conserva comandos,
contratos y enlaces de las fases anteriores. [Rediseño de follaje](plans/rediseno-follaje.md)
conserva el marco RF0–RF5; la integración y controles se coordinaron con B2/B3.
