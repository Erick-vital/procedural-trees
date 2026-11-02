# Integración estacional del roble — candidata 0.1.0

T5 del [plan de transiciones](../plans/transiciones-estacionales.md). Perfil
explícito `configs/seasons/roble-integracion-v1.json`, versión
`season-bundle-0.1.0`. No sustituye la receta roble 2.2.0 ni selecciona “latest”.

## Selección y entradas

El usuario autorizó cualquiera de las dos normales T4 y delegó la elección. Se
selecciona **.35**, desviación máxima 21°, por ser la opción más conservadora.
[Decisión](evidence/estaciones/normales-t4/user-acceptance.json).
No se afirma mejora artística o de rendimiento a partir de esa elección.

Cuatro casos de `configs/verification/oak-wood-v1.json`: piloto 3009, joven-07
1007, adulto-00 2000 y viejo-00 3000; semillas copa/pintura 17/2718 y estacional
1101. Contratos/calendario T1, atlas compatibles T2, shader lineal T3 y algoritmo
local T4 se conservan. Misma intensidad y reglas para todos, sin retoques por semilla.

`src/treegen/season_bundle.py` valida campos/versiones/rutas/selección y límites:
**6999 tris y dos materiales**. Contrasta la aprobación contra el hash del ensayo
T4. El constructor verifica los hashes T1 y recalcula cada calendario desde los
volúmenes/perfil: exige igualdad exacta. Genera campos locales y normales .35,
conservando también originales como control.

## Paquete y extremos

`portable/manifest.json` registra semillas, calendario, campos, intensidad,
versiones, recursos/hashes y cuatro exportaciones por caso:

- `summer-selected.glb`, `autumn-selected.glb`: normales .35.
- `summer-original.glb`, `autumn-original.glb`: normales originales como control.

Todos los extremos contienen dos PNG embebidos y materiales glTF estándar;
no necesitan el adaptador para conservar el color. JSON de calendario, binding
y campos en `portable/cases/<id>/`; pinturas/corteza en `portable/resources/`.
Las rutas son relativas y verificadas por hash; se rechazan escapes y casos,
presupuestos o exportaciones incompletos. Se valida la geometría de los 16 GLB
antes de revisar las importaciones.

Posiciones, UV0/UV2, índices y madera exactos frente a T1; solo cambian las
normales de follaje seleccionadas y el PNG estacional. Los originales permanecen
como referencias. El piloto seleccionado debe coincidir literalmente con la
candidata .35 de T4. No se reexporta geometría para producir estos extremos.

**Un estado intermedio con mezcla distinta por grupo requiere el adaptador**.
No es una animación glTF ni se exporta estáticamente a un atlas único. El paquete
no añade materiales por grupo ni texturas mayores de 2048² para ocultarlo.

## Godot

Proyecto autónomo en `godot/`, con visor de los cuatro ejemplares, selección de
normales .35/originales, fase, pausa, sentido, órbita, suelo y modos de comparación.
Cada ejemplar conserva su fase al cambiar de selección. Durante el avance se
actualizan parámetros por instancia; no se reconstruyen mallas ni texturas.

Shader `paint_transition.gdshader` conservado de T3. Material pintado, material
de corteza y tres texturas compartidos. El adaptador T5 libera las referencias
de material del mesh importado sustituyéndolas por estos recursos compartidos
solo en las mallas de ejecución propias del paquete. Los GLB estáticos y los
archivos históricos no cambian. El control de tinte anterior conserva su material
por instancia; nunca añade una tercera superficie o material activo al árbol.

El proyecto usa rutas `res://` desde su raíz. Para integrar los scripts en una
subcarpeta de otro proyecto, adaptar esas rutas o conservar la estructura de raíz.
No se modifica automáticamente ningún proyecto Godot externo.

```gdscript
var tree = load("res://pilot-selected.tscn").instantiate()
add_child(tree)
tree.set_phase(0.5)  # calendario por grupo, acceso directo y reversible
```

`set_mode(0/1/2/3/4)` corresponde a calendario/uniforme/verano/otoño/tinte anterior.
UV2 sigue reservado a `(inicio,duración)`, no a lightmap.

## Verificación y reproducción

```sh
python3 scripts/verify_season_bundle.py --output artifacts/estaciones/otra-t5
# Modalidad alternativa, separar construcción y revisión:
python3 scripts/verify_season_bundle.py --output artifacts/estaciones/otra-t5 --stage build
python3 scripts/verify_season_bundle.py --output artifacts/estaciones/otra-t5 --stage review
env PYTHONPATH=src python3 -m unittest discover -s tests
```

Elegir una modalidad. La construcción requiere carpeta nueva y las referencias
T1/T2/T4 documentadas; `BLENDER_BIN`/`GODOT_BIN` seleccionan ejecutables.
Cada subproceso tiene límite de 180 s y puede terminarse. Se revisan nativamente
los extremos estándar y sus reexportaciones Blender, UV2 por grupo, secuencias,
saltos/reversión, instancias, luces, distancias, fondos y sombras. Después se copia
el proyecto sin cachés a otra carpeta y se vuelve a importar/ejecutar sin rutas de
vuelta al repositorio. El ZIP excluye cachés e imports regenerables.

Las importaciones no se declaran exactas en luz o representación interna de
normales: se mantienen las cotas observadas de T4 y se registra cada error.
La exactitud binaria fuera de normales/PNG se comprueba antes de importar.
Memoria de imágenes/recursos y estimación RGBA8 se distinguen de VRAM/FPS; no se
hace benchmark. La aprobación del piloto y las normales no aprueba por anticipado
el aspecto de todos los controles integrados.
