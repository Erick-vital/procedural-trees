# Contrato B1: blueprints y ejemplares, versión 1.0

Fecha: 2026-10-23. Implementado en `src/treegen/blueprints.py`, sin `bpy`,
sin generación de geometría ni ejecución de scripts desde las recetas.
[Plan](../plans/sistema-blueprints.md), [referencia B0](evidence/blueprints/b0/informe.md).

## Documentos e identidad

- [TreeBlueprint](../schemas/tree-blueprint.schema.json) describe una familia:
  `schema_version`, `id`, `version`, nombre/descripción, componentes, parámetros,
  apariencia, rangos editables, perfiles, perfil predeterminado y límites.
- [TreeInstance](../schemas/tree-instance.schema.json) pide resolver un ejemplar:
  identidad y versión exactas de blueprint, semillas explícitas `base` y `canopy`,
  perfil opcional y cambios opcionales de parámetros.
- No hay semillas en el blueprint ni en sus perfiles. La repetición de un
  ejemplar usa la receta exacta y las semillas de su petición.
- `id` usa minúsculas, dígitos y guion bajo; la versión usa `mayor.menor.parche`.
  No hay resolución implícita de una versión «latest».
- Los documentos no admiten campos desconocidos. Los cargadores rechazan claves
  repetidas, números no finitos y archivos mayores de 64 KiB. Semillas, conteos,
  profundidad y límites enteros requieren enteros reales, no booleanos ni `24.0`.

## Registro de componentes

El registro inicial solo acepta esta combinación existente:

| Responsabilidad | Identificador |
| --- | --- |
| Base, madera y moldes Q3 | `oak_geometry_nodes@0.4.0` |
| Ocupación, muestreo y soportes RF3 | `foliage-canopy@0.1.0` |
| Representación de seis rombos por conexión | `rf3-diamond-six@0.1.0` |

Son identificadores de capacidades de resolución. No son rutas de archivos,
imports dinámicos ni un nuevo motor de generación. La representación identifica
la regla RF3 existente; no crea un algoritmo adicional con geometría distinta.
Un nuevo componente requiere una estrategia explícita en código y pruebas de
compatibilidad; introducir otro texto en el JSON causa un rechazo.

La integración B2 está implementada en `blender/generate_blueprint.py` y el
ejecutor compartido. [Registro y reproducción](evidence/blueprints/b2/informe.md).
Los contratos históricos `TreeSpec` y `foliage-canopy` permanecen intactos.

## Parámetros, unidades y precedencia

`parameters.base` contiene los diez parámetros históricos Q3. Altura, radio y
escala de masas están en metros; inclinación en grados desde la vertical;
curvatura, asimetría y densidad son adimensionales. Incluye `foliage_density` y
`foliage_scale_m` porque **la base Q3 también define moldes invisibles**: esos
controles no son tamaño ni cantidad de las hojas RF3 finales.

`parameters.canopy` contiene los parámetros RF3 sin semilla ni versión:
`group_count`, `leaf_length_m`, `shell_depth_m`, `twig_radius_m`,
`tip_radius_ratio`, `profile_width_scale` y los cuatro `region_weights`.
Las longitudes son metros, los pesos y razones adimensionales. Añade
`layout_leaf_length_m`, en metros: escala explícita usada al planificar soportes.
Esto permite reducir la representación de hoja conservando la planificación.
Al resolver se separa de `canopy_spec`; no se añade al contrato RF3 histórico.

Orden de aplicación:

1. Parámetros predeterminados del blueprint.
2. `overrides` del perfil elegido, o `default_profile` si se omite la selección.
3. `overrides` de la petición del ejemplar.

Los cambios son parciales por campo, incluidos los pesos regionales: cambiar
solo `canopy.region_weights.east` conserva norte, sur y oeste.

Cada cambio de perfil o ejemplar debe figurar en `editable_ranges`, indexado por
ruta, por ejemplo `base.height_m` o `canopy.region_weights.east`. Se valida su
intervalo contra el contrato del componente, sus valores por defecto y los
valores resueltos. Un campo ausente de esa lista es fijo para el ejemplar;
editarlo exige una revisión de la receta. No hay cambios de componentes,
materiales ni límites desde una petición de ejemplar.

Los rangos declarados son **rangos permitidos de entrada**. No garantizan que
todas sus combinaciones sean viables o visualmente aprobadas. Cada perfil incluye
`validation.status` (`reference_only`, `experimental` o `verified_cases`) y enlaces
de evidencia. Son declaraciones de procedencia, no una certificación del cargador.
El resultado registra esa declaración y si los parámetros difieren del perfil;
un nuevo valor o semilla no hereda automáticamente la aprobación del piloto.

## Apariencia y límites conjuntos

`appearance` fija dos roles: `bark` y `leaf`, cada uno con `color_rgba`,
`roughness`, `metallic` y `double_sided`. Son factores de material, sin texturas;
alfa debe ser 1 y esta versión conserva los materiales de doble cara. La madera
de conexión usa las propiedades de `bark` como tercer material, igual que RF3.
La iluminación y las cámaras de evaluación pertenecen al protocolo de evidencia,
no a cambios de apariencia de un ejemplar.

RF3 en este contrato requiere:

- De 24 a 360 grupos, seis hojas por grupo y al menos una región con peso positivo.
- Densidad Q3 suficiente para producir moldes: `floor(4*density + .5) >= 1`,
  es decir, al menos 0.125. Un valor positivo menor también deja la copa sin guías.
- Techo de receta de hasta 12500 triángulos, tres materiales y hasta 120 s por
  generación. Un límite menor de tres materiales es incompatible con RF3.
- Cotas de componente: 8192 muestras y 2048 intentos de conexión. No son controles
  editables del ejemplar. La planificación seguirá fallando explícitamente si no
  puede completar las conexiones, aunque el presupuesto aritmético permita el caso.

Se calcula una cota antes de abrir Blender. Con sección de ocho lados y los
12/9/7 anillos actuales, madera Q3:

`188 + primarias × 140 + (primarias × 3 × 108 si profundidad = 2)`.

Se suman `group_count × 20`: ocho triángulos de conexión y doce de seis hojas.
Los pesos regionales pueden reducir el coste efectivo; la cota no anticipa ese
ahorro. Con once primarias y 264 grupos da 10572; doce primarias y 360 grupos
dan 12956 y se rechazan, aunque cada uno de esos cambios aislado sí quepa.

**Copa vacía no está soportada en la versión 1.0 de esta combinación.** Cero
grupos, cuatro pesos cero o ausencia de moldes se rechazan. No se cambia la
semántica de cero en algoritmos históricos. Admitir una copa vacía requerirá
una revisión explícita del contrato y pruebas de integración antes de B3.
Los cálculos previos no sustituyen la validación de la malla y del GLB final.

## Resultado de resolución y repetición

`resolve_blueprint(blueprint, instance)` no modifica las entradas y produce:

- Definición completa de blueprint, hash canónico, petición original, perfil y
  parámetros resueltos. Cambiar el catálogo después no pierde los valores usados.
- `base_spec` Q3 0.4.0 y `base_seeds` derivadas mediante el protocolo histórico
  `oak-v1`; `canopy_spec` RF3 con su semilla independiente.
- Escala de planificación, apariencia, límites y cota geométrica.
- Declaración de validación del perfil y hash canónico de toda la resolución.

El hash canónico ignora el orden de claves JSON, preserva valores y rechaza
números no finitos. Este resultado es un dato de resolución; todavía no es un
manifiesto de generación terminada. B2 añade ejecución, fuentes/entorno,
artefactos y validación final al manifiesto compartido `kind=blueprint`.

Uso de biblioteca con la receta y el ejemplar registrados en B2:

```python
from treegen.blueprints import load_blueprint, load_instance, resolve_blueprint

blueprint = load_blueprint("blueprints/roble_copa_ancha/1.0.0.json")
instance = load_instance("presets/blueprints/roble-copa-ancha-viejo-09.json")
resolved = resolve_blueprint(blueprint, instance)
```

`resolve_blueprint` sigue siendo una operación de datos. Para generar se usa
`runner.execute_blueprint` o la CLI `generate-blueprint`, documentada en el
[informe B2](evidence/blueprints/b2/informe.md). Los ejemplos de B1 en
`tests/test_blueprints.py` siguen siendo fixtures separados de la receta registrada.

## Validación B1

Las pruebas cubren la correspondencia exacta de entradas RF3, semillas,
precedencia, cambios regionales parciales, inmutabilidad, repetición desde una
definición congelada, cambios no permitidos y versiones desconocidas. Incluyen
una combinación que excede presupuesto aunque sus cambios aislados quepan,
copa vacía, guías ausentes, enteros estrictos y carga JSON inválida.

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p test_blueprints.py -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

La suite completa contiene una prueba histórica de socket loopback que requiere
ejecución autorizada fuera del sandbox. B1 no genera geometría y sus pruebas
no constituyen validación visual ni generalización del primer tipo de árbol.

## Revisión B3: distribución 0.1.1 y receta 1.2.0

`foliage-canopy@0.1.1` conserva el muestreo, reparto y representación RF3, y
corrige las proyecciones que se separan al menos 0,1 mm de la triangulación real
Blender. Proyecta sobre la misma rama, con desplazamiento máximo de 1 mm; por
encima falla. La evaluación usa triángulos reales y distancia float64, con
la misma tolerancia final de 0,1 mm. La madera base permanece intacta.
El registro acepta explícitamente ambas versiones; la resolución guarda en
`canopy_spec.version` la seleccionada. Las recetas anteriores siguen en 0.1.0.

`roble_copa_ancha` 1.2.0 selecciona 0.1.1 y usa hoja joven de 0,45 m,
con planificación de 1 m, mismos soportes y conteos en los dos jóvenes de
control. No altera los perfiles de edad de las recetas 1.0.0/1.1.0.
[Resultados, límites y conservación del piloto](evidence/blueprints/b3-revision/informe.md).


## Uso y cierre B5

[Guía de uso](uso-blueprints.md): catálogo, rutas/ejemplares exactos, repetición,
comparación y extracción de entradas desde manifiesto. La selección no resuelve
“latest”. Los alias TreeSpec sin versión seleccionan Q3 0.4.0; Q3b se conserva
por rutas explícitas `presets/v0.4.1/`, sin alterar estos contratos de blueprint.
[Decisiones y verificación de cierre](evidence/blueprints/b5/informe.md).

## Ampliación 1.1: pino experimental

El 2026-10-24 se añade `pino_conico` 1.0.0. Los esquemas
`tree-blueprint-pine.schema.json` y `tree-instance-pine.schema.json` usan
`schema_version=1.1` y conservan la identidad, precedencia, semillas explícitas,
límites, carga estricta y resolución congelada del sistema. El contrato 1.0
y las recetas anteriores permanecen intactos. Receta y petición deben usar la
misma versión de contrato; 1.1 admite únicamente la combinación registrada
`pine-whorls@0.1.0` / `pine-distal@0.1.0` / `pine-needle-pairs@0.1.0`.

Parámetros de estructura en `base`: `height_m`, `base_radius_m`,
`crown_base_ratio` (altura relativa del primer piso), `whorl_count`,
`branches_per_whorl`, `crown_radius_ratio` (radio inferior relativo a altura),
`branch_rise_ratio`, `irregularity` y `secondary_length_ratio` (relativa a
la longitud de la primaria). Parámetros `canopy`: `needles_per_twig` (par),
`needle_length_m` y `needle_width_m`. Metros para dimensiones, enteros para
conteos y razones adimensionales para el resto. No hay moldes RF3 en esta ruta.

Con `N = whorl_count × branches_per_whorl`, la cota exacta actual es
`188 + N×124 + (N×5+1)×needles_per_twig×2`. Incluye tronco 12×8,
primarias 4×6, cuatro ramillas 3×4 por primaria, tapas y dos triángulos por
acícula. No hay muestreo por rechazo ni reintentos. Se rechaza superar el
presupuesto, cantidad impar, anchura de acícula mayor del 25 % de su longitud
o radio basal mayor del 4 % de la altura. Necesita dos materiales y mantiene
los techos globales 12500 triángulos/3 materiales/120 s.

La resolución 1.1 registra `base_spec` interno `pine-whorls@0.1.0`,
`canopy_spec`, semillas derivadas por SHA256 con prefijo explícito `pine-v1`,
parámetros y receta completos. No amplía TreeSpec ni la API histórica.
`seed(base,'foliage')` se conserva como procedencia de la base; la distribución
de acículas usa exclusivamente la semilla `canopy` explícita. La generación
valida el resultado con los roles `Pine_Bark` y `Pine_Needles`; las funciones
de evaluación conservan los roles históricos como predeterminados.

[Plan](../plans/blueprint-pino.md), [guía](uso-blueprints.md#pino-experimental),
[verificación y revisión visual](evidence/blueprints/pino/informe.md).

Revisión estructural posterior: el contrato 1.1 también admite
`pine-whorls@0.2.0` con la misma distribución/representación 0.1.0.
`pino_conico` 1.1.0 lo selecciona explícitamente; 1.0.0 conserva la estructura
0.1.0. La resolución registra la versión efectiva en `base_spec.algorithm_version`
y el adaptador despacha únicamente estrategias registradas. Mismos parámetros,
cota y semillas; no amplía los rangos ni incorpora otra representación de hoja.
[Comparación reproducible y límites](evidence/blueprints/pino-revision/informe.md).
