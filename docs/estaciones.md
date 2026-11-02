# Variantes estacionales

Estado vigente: **T0–T6 cerradas y lote aprobado artísticamente**.
[Entrega 0.1.0, paquetes y decisiones](entrega-transiciones.md).

Primera implementación: roble pintado **2.2.0**, perfil estacional **1.0.0**,
otoño de copa llena. [Plan y alcance](../plans/estaciones.md).

## Qué se reutiliza

`src/treegen/seasons.py` valida contrato, identidad del árbol y presupuesto.
`godot/seasonal_foliage.gdshader` aplica una paleta a los pigmentos verdes del
atlas, conserva modulación de luminancia y protege trazos pardos. El campo de
variación es continuo en coordenadas locales: no depende de cámara, tiempo ni
posición global. Intensidad 0 recupera la pintura original; intensidad 1 aplica
el perfil. La semilla estacional se registra aparte de las de base/copa/pintura.
Su fase se reduce módulo 8191: semillas separadas por ese valor coinciden.

`godot/seasonal_tree.gd` aplica un material de follaje compartido por árbol;
la madera mantiene su material. Alfa .5, doble cara, sombras dobles, rugosidad
.88 y filtrado anisotrópico con mipmaps; no se añaden texturas ni superficies.
La transformación trabaja en espacio lineal; los colores del perfil son sRGB.

## Qué pertenece al roble

`configs/seasons/roble-otono-v1.json` declara especie/versión/material, paleta
de ocres, fase con follaje completo, verde residual y escala espacial de manchas.
El verde residual es un control del campo de color, **no un porcentaje medido
de hojas verdes**. No se presenta esta familia artística como una especie
botánica exacta. Por ahora se rechazan otras especies/fases: añadirlas requiere
su propio perfil y validación; el pino no debe heredar estas reglas por defecto.

No hay caída de hojas, marcescencia, hojas de suelo ni cambios de arquitectura.
Los mismos 264 grupos y tres láminas por grupo conservan la copa aprobada.
El presupuesto se comprueba sobre cada GLB fuente y nuevamente al importarlo en
Godot. Solo se certifican los cuatro ejemplares ensayados, no todos los rangos.

## Construcción y uso

Requiere los cuatro robles originales generados. Si no están disponibles,
reproducirlos con el verificador existente:

```sh
python3 scripts/verify_oak_wood.py --output artifacts/roble-base-estaciones --stage generate
python3 scripts/verify_seasons.py --source artifacts/roble-base-estaciones --output artifacts/estaciones/mi-otono
```

Con la referencia local existente:

```sh
python3 scripts/verify_seasons.py --output artifacts/estaciones/mi-otono
PYTHONPATH=src python3 -m unittest discover -s tests -p test_seasons.py
```

Solo empaquetar, sin abrir Godot:

```sh
python3 scripts/build_seasonal_oak.py --output artifacts/estaciones/mi-paquete
```

Cada salida exige carpeta nueva. `GODOT_BIN` permite cambiar el ejecutable.
El verificador limita cada subproceso a 180 s y rechaza errores de script/shader;
compara repeticiones de render y reconstrucción determinista del paquete.

Abrir `godot/project.godot` en Godot y ejecutar. Arrastrar gira, rueda acerca,
**O** alterna verano/otoño, **N** cambia árbol y **R** restablece cámara.
Para integrar una variante en otro proyecto, copiar los archivos del paquete
Godot e instanciar `pilot.tscn` o el control correspondiente. Si se cambia la
carpeta de destino, ajustar las rutas `res://` y `profile_path`.

La variante otoñal es una **escena Godot con shader**. El GLB incorporado sigue
siendo el original verde: exportarlo solo no conserva el otoño. Hornear atlas
estacionales y exportar un GLB otoñal independiente quedan fuera de esta entrega.

La pintura anterior ya estaba aprobada; esta aplicación estacional necesita
valoración artística propia. Menos cambios de recursos no demuestra mejora de FPS.

## Alternativa desde pintura — experimento 0.1.0

El shader anterior se conserva como experimental. Punto previo a la nueva
pintura: commit `4187776`, solicitado por el usuario. Recursos nuevos en
`assets/roble-otono-pintado/v0.1.0/`: hojas RGBA editadas con ImageGen, prompt,
procedencia, atlas proyectado y comparación de alfa. Corteza histórica intacta.

`src/treegen/seasonal_paint.py` sustituye únicamente el PNG de follaje embebido
del GLB; recoloca los bloques binarios sin reexportar mallas ni alterar materiales,
escena, UV, índices o normales. Auditoría binaria conserva todos los demás
recursos. No es un filtro de color horneado del shader: el contenido de la pintura
es nuevo. La silueta pintada varía ligeramente y se mide por separado.

```sh
# Rehornear desde la pintura ya guardada, sin volver a invocar ImageGen:
/home/tao/repos/blender/.tools/blender-5.2.1-linux-x64/blender --background --factory-startup --threads 2 --python-exit-code 1 --python blender/bake_autumn_oak.py -- assets/roble-otono-pintado/v0.1.0 /tmp/roble-otono-atlas.png
# Exportar cuatro GLB y comparar contra shader/verano en Godot:
python3 scripts/verify_autumn_paint.py --output artifacts/estaciones/mi-pintura-otono
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_season*.py'
```

El verificador usa el atlas versionado `crossed-atlas.png`, no el rehorneado de
`/tmp`. Cada salida exige carpeta nueva; `--source` selecciona los cuatro robles
base y `GODOT_BIN` cambia el ejecutable. Procesos de revisión separados por árbol,
cada uno limitado a 180 s. El visor compara pintura/shader/verano con **O**;
**N** cambia árbol. Geometría/cámara/luz comunes; se conserva rugosidad .95 del
material estándar frente a .88 del shader experimental, por lo que se comparan
las dos implementaciones completas, no solo pigmentos aislados.

Los archivos `artifacts/estaciones/roble-pintura-01/{pilot,joven-07,adulto-00,viejo-00}/tree.glb`
sí contienen el otoño y usan materiales estándar glTF con PNG embebidos. No
necesitan el script Godot para conservar el color; al importar en otro motor se
deben respetar recorte alfa y doble cara del material. No se ha probado otro motor.
[Comparación y resultados](evidence/estaciones/roble-pintura-01/informe.md).

## Calendario por grupo — T0/T1

T0 congela cuatro referencias con ajustes comunes; T1 añade contrato/calendario
0.1.0 y transporte UV2 sin cambiar pintura, geometría o normales. **No hay mezcla
animada todavía**. 27 pruebas y 37 comprobaciones pasan; 80 capturas Godot y 20
pares original/con datos idénticos. Importación directa y tras Blender auditadas.

[Contrato, archivos y ejecución](contrato-calendario-estacional.md),
[resultado seleccionado](evidence/estaciones/calendario-t01/informe.md).
Perfil `configs/seasons/roble-calendario-v1.json`; datos derivados en
`artifacts/estaciones/calendario-t01-03/{pilot,joven-07,adulto-00,viejo-00}/`.
UV2 contiene inicio/duración, **no UV de lightmap**. T2 ya prepara máscara común;
T3 ya conecta los datos a la mezcla de pinturas; el shader antiguo se conserva como control.

## Atlas compatibles — T2

Recursos candidatos `assets/roble-estacional/v0.1.0/{summer,autumn}.png`, con
alfa común derivada del verano y extensión RGB de 16 px acotada por celda.
Plantillas/UV originales conservadas; no se sustituye pintura histórica ni se
integra todavía el árbol en esa fase. Pintura compatible y aplicación del piloto
aprobadas posteriormente en T3; manifiestos T2 históricos conservados.
[Informe y comparación](evidence/estaciones/atlas-t2/informe.md).

```sh
# Repetir atlas, cuatro GLB de rama y capturas Godot (carpeta nueva):
python3 scripts/verify_season_atlas.py --output artifacts/estaciones/otra-t2
# Conservar solo los dos recursos candidatos después de revisar las capturas:
python3 scripts/publish_season_atlas.py --trial artifacts/estaciones/otra-t2 --output /tmp/atlas-candidato --treatment padded
```

La galería final está en `artifacts/estaciones/atlas-t2-05/index.html`.
72 capturas: tablero de 24 proyecciones y rama primaria 100 del piloto,
seis variantes, dos fondos y tres distancias. Mipmaps activados y relleno
RGB automático del importador desactivado para aislar el ensayo. T3 conserva esos ajustes al conectar la mezcla; filtrar con mipmaps no los
genera por sí solo. Calendario T0/T1 y su perfil siguen apuntando a referencias
históricas: T3 resuelve estos nuevos recursos en un perfil separado, sin relajarlos.

## Transición pintada del piloto — T3

**T3 verificada técnicamente**, perfil `configs/seasons/roble-mezcla-v1.json` y
adaptador Godot 0.1.0. Dos atlas T2 mezclados en espacio lineal con calendario UV2;
material/texturas compartidos, fase por instancia. Madera y normales originales.
185 pruebas y 517 capturas; extremos estándar, máscara constante y reversión
comprobados. **Valoración artística T3 aprobada** el 2026-11-02: [decisión](evidence/estaciones/mezcla-t3/user-acceptance.json).
[Resultado, límites y secuencias](evidence/estaciones/mezcla-t3/informe.md).

```sh
python3 scripts/verify_paint_transition.py --output artifacts/estaciones/otra-t3
python3 scripts/paint_transition_evidence.py --output artifacts/estaciones/otra-t3
```

La salida requiere carpeta nueva y las referencias T1/T2; `GODOT_BIN` selecciona
el ejecutable y cada subproceso tiene un límite de 180 s. Para separar las etapas,
usar `--stage build` seguido de `--stage review` sobre esa misma carpeta.
Salida final: `artifacts/estaciones/mezcla-t3-04/`; abrir `godot/project.godot`
y ejecutar. El visor ofrece deslizador, reproducir/pausar, avance/retroceso,
órbita y modos calendario/uniforme/verano/otoño/tinte anterior. Galería de
comparación y animaciones en `index.html`.

El GLB del paquete contiene verano compatible y UV2; la mezcla animada necesita
el shader/adaptador. No exportar ese GLB como si contuviera una animación glTF.
UV2 sigue reservado al calendario, no a lightmap. Sin benchmark ni integración
de los cuatro controles (T5); las normales de volumen corresponden a T4.

## Normales locales de copa — T4

T3 aprobada artísticamente; ensayo T4 técnicamente verificado con **originales,
intensidad .35 y .65** en rama/piloto, pinturas fijas y material estándar. No se
cambia la transición aprobada. Posteriormente se seleccionó .35 por delegación.
191 pruebas y 793 capturas; seis orientaciones, tres distancias y tres luces,
sombras propias/suelo y máscaras exactas. Blender puede alterar ligeramente
las normales al importar/reexportar (máximo .469° observado); se registra aparte
de la exactitud binaria del GLB generado fuera de las normales de follaje.
[Informe y comparación](evidence/estaciones/normales-t4/informe.md),
[contrato](contrato-normales-copa.md).

```sh
python3 scripts/verify_canopy_normals.py --output artifacts/estaciones/otra-t4
python3 scripts/canopy_normals_evidence.py --output artifacts/estaciones/otra-t4
```

Salida final `artifacts/estaciones/normales-t4-06/`: galería `index.html`,
visor `godot/project.godot`, 12 GLB estáticos y seis pruebas de vuelta Blender.
El visor alterna originales/.35/.65, pinturas, rama/piloto, tres luces y suelo;
arrastrar gira, rueda acerca y R restablece cámara. La elección **.35 está aprobada** por delegación: [decisión](evidence/estaciones/normales-t4/user-acceptance.json). T5 conserva originales como control.


## Integración de cuatro casos — T5

**T5 implementada y verificada**, candidata explícita `season-bundle-0.1.0`;
normal .35, reglas comunes y recetas históricas conservadas. 194 pruebas,
2377 capturas más cuatro en copia limpia. Cuatro casos 6812/3132/5820/6900 tris,
dos materiales y tres texturas compartidas; 16 extremos GLB estándar embebidos
verificados en Blender/Godot. Fase independiente y reversible, visor común y
paquete probado fuera del repositorio sin cachés. Sin benchmark de FPS.
[Informe y comparación](evidence/estaciones/integracion-t5/informe.md),
[contrato/API](contrato-integracion-estacional.md). T6 cerrada; [entrega](entrega-transiciones.md).

```sh
python3 scripts/verify_season_bundle.py --output artifacts/estaciones/otra-t5
python3 scripts/season_bundle_evidence.py --output artifacts/estaciones/otra-t5
```

Salida final `artifacts/estaciones/integracion-t5-03/`: `index.html`,
`godot/project.godot`, extremos en `portable/cases/` y ZIP autocontenido.
Los GLB contienen pinturas fijas; la mezcla intermedia por grupo requiere el
adaptador. El visor recuerda fase por caso/normales y ofrece los cinco modos T3.
La integración de cuatro casos tiene revisión visual técnica y aprobación
artística posterior explícita: [aceptación final](evidence/estaciones/cierre-t6/user-acceptance.json).


## Cierre de entrega — T6

Solicitado y completado el 2026-11-02. [Guía final](entrega-transiciones.md),
[informe de cierre](evidence/estaciones/cierre-t6/informe.md). Galería y paquetes
T5 conservados; nuevo inventario/ZIP de 266 fuentes y entradas congeladas probado
mediante reconstrucción en carpeta aislada: manifiesto, proyecto y 16 extremos
idénticos. No cambia geometría, algoritmo ni shader; revisión visual T5 conservada.

Pintura y calendario del piloto aprobados en T3; normales .35 en T4 por delegación.
[Decisiones separadas](evidence/estaciones/cierre-t6/decisions.json). La adopción
artística del lote de cuatro casos fue aprobada posteriormente por el usuario:
[aceptación final](evidence/estaciones/cierre-t6/user-acceptance.json). Sin fases adicionales en
curso; una posible investigación de caída del roble se definirá por separado.
