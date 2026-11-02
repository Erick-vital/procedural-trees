# Variantes estacionales

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
