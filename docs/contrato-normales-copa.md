# Normales locales de copa — ensayo T4 0.1.0

Implementación `canopy-local-normals-0.1.0`, separada del calendario y de la mezcla
pintada. Se limita a rama/piloto de roble 2.2.0 con pinturas T2 fijas.
[Plan](../plans/transiciones-estacionales.md).

## Entradas y campos locales

`src/treegen/canopy_normals.py` recibe los 264 volúmenes y la vecindad T1 del
piloto. Contrasta el hash canónico de volúmenes ordenados y los IDs del calendario;
conserva sus validaciones de finitud, ejes ortonormales y máximo 360 grupos/24 vecinos.
No usa fase, cámara, luz ni nuevos números aleatorios.

Cada grupo define un campo local, no una esfera global de toda la copa:

1. Semieje mayor `r=max(size)/2`. Incluye el propio elipsoide con peso 1 y hasta
   24 vecinos existentes si su centro queda a distancia ≤2.5r.
2. Vecinos con peso `.5*exp(-(distancia/(1.5r))²)`; empate/recorrido por ID.
3. Centro ponderado y covarianza de centros más los segundos momentos del
   elipsoide de cada miembro: `Σ eje⊗eje * semieje²/3`.
4. Regularización `.04r² I` para evitar matriz singular. Cambio de base
   Blender→glTF/Godot `(x,z,-y)` e inversión simétrica 3×3.
5. Normal objetivo proporcional a `C⁻¹(position-center)`; centro degenerado
   conserva la normal original. Se elige el hemisferio de la normal original.
6. Se limita primero el ángulo objetivo a 60° y después se interpola angularmente
   con intensidad `s`. Ensayos `s=.35/.65`: desviación máxima **21°/39°**.
   `s=0` conserva literalmente el GLB original. Se admite `0≤s≤.75` y se rechazan
   booleanos, NaN/Inf, normales no unitarias y posiciones inválidas.

La rama usa un subconjunto de vértices, pero el **mismo contexto de 264 grupos**
que el piloto, incluidos sus vecinos externos. No se recalculan campos usando
solo los 32 grupos visibles de la rama. Se guardan `fields.json`, hash del campo,
intensidades y versiones. No se sustituye ninguna receta o alias histórico.

## GLB y auditoría

`src/treegen/canopy_normals_glb.py` asocia por posición+UV0 float32 al binding
congelado T1; rechaza grupos desconocidos, bindings ambiguos y caras que mezclen
IDs. Exige seis triángulos por grupo de follaje.

Solo escribe float32 `NORMAL` de follaje, sin reexportar mallas:

- Documento JSON/cabecera y longitud GLB exactos, cero bytes añadidos.
- Posiciones, UV0, UV2/calendario, índices, madera completa y sus normales,
  imágenes, materiales y escena exactos byte a byte.
- Rechazo de vistas de normales compartidas/solapadas con otro atributo o imagen.
- Normales finales finitas y unitarias con error cuadrático ≤2e−6.
- Para auditar, se restituyen únicamente los bytes permitidos y se exige igualdad
  de todo el binario con el original. Una alteración ajena a NORMAL se rechaza.

Blender importa seis GLB de verano, compara normales de esquina por geometría/UV
y reexporta material estándar. No se supone que su representación interna conserve
cada float. La lectura tiene cota angular **.6°** y cota por componente **.01**;
se registra el error observado. API: [normales de esquina de Mesh](https://docs.blender.org/api/current/bpy.types.Mesh.html).

Godot verifica posiciones/UV0 con cota y grupo único antes de contrastar normales.
Límite de diferencia vectorial **.003** en importación directa y **.012** tras
Blender, más normal finita/unitaria y conteos completos. La vuelta de Blender no
se declara idéntica a los bytes fuente ni representa una edición geométrica nueva.

## Revisión

Todos los renders usan `StandardMaterial3D`: las normales proceden del GLB,
sin shader que las simule. Pinturas fijas y recorte .5/doble cara/mipmaps comunes;
no se conecta el calendario animado T3 durante el ensayo.

Seis orientaciones × tres distancias × tres luces × dos pinturas × rama/piloto
× original/.35/.65. Sombras propias y suelo en tomas separadas, con normal bias
0 y 1 para distinguir el efecto de iluminación del desplazamiento de sombra que
puede introducir el sesgo basado en normales. Máscaras negras sin luz para
comprobar que no cambia el recorte proyectado. Verificación técnica y adopción
artística son decisiones separadas: las normales originales siguen vigentes
hasta que el usuario elija una candidata o rechace el ensayo.

```sh
python3 scripts/verify_canopy_normals.py --output artifacts/estaciones/otra-t4
# O preparación y revisión por separado:
python3 scripts/verify_canopy_normals.py --output artifacts/estaciones/otra-t4 --stage build
python3 scripts/verify_canopy_normals.py --output artifacts/estaciones/otra-t4 --stage review
env PYTHONPATH=src python3 -m unittest discover -s tests
```

Elegir una modalidad; `build` exige carpeta nueva. Requiere referencias T1/T2/T3
y la decisión de aprobación T3. Cada subproceso es terminable y tiene límite de
180 s; `BLENDER_BIN` y `GODOT_BIN` permiten seleccionar los ejecutables.
Los GLB, roundtrips, capturas completas y proyecto Godot quedan en `artifacts/`.
Conservar evidencia seleccionada y comandos, no todos los resultados regenerables.
