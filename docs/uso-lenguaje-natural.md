# Pedir árboles desde Codex — F4

Abrir Codex en este repositorio y pedir, por ejemplo:

- «Créame 10 robles con alturas variadas y copas más abiertas».
- «Crea un roble viejo de tronco grueso y ramas asimétricas».
- «Haz tres variantes de este árbol; conserva su madera y abre la copa».

Codex interpreta la petición en la conversación y ejecuta el flujo local. No
hay que configurar proveedores, claves ni otro proceso de Codex. La interfaz
sigue siendo el chat. La CLI siguiente es una herramienta para el agente y para
reproducir resultados; no es un intérprete de lenguaje natural por sí sola.

## Flujo que debe seguir Codex

1. Leer ESTADO y el plan activo. Seleccionar una receta explícita según el pedido;
   referencia inicial F4: `roble_copa_ancha@2.2.0`, pintado aprobado. Leer perfiles,
   `editable_ranges`, restricciones y ejemplares existentes. Si el usuario indica
   una receta o árbol, conservar esa elección y sus condiciones compatibles.
2. Escribir un plan JSON en una ruta nueva, con la petición original, origen
   `codex-session`, identificadores únicos, semillas explícitas y una propuesta
   por ejemplar. Explicar qué controles expresan cada intención y qué no existe.
3. Para «10 árboles variados», distribuir cambios moderados de altura, radio,
   forma de copa/asimetría y ocupación según lo pedido; variar semillas y conservar
   pintura y representación. No limitarse a copiar diez veces el mismo ejemplar.
   No tocar controles ajenos a una petición más restringida. Si un control no
   representa fielmente la intención, explicarlo y registrar la aproximación.
4. Ejecutar `plan-blueprints`: validar todos los ejemplares antes de Blender.
   Inspeccionar los parámetros resueltos. Preparar el resultado concreto sin
   pedir otra confirmación para generar dentro del alcance autorizado.
5. Ejecutar `generate-blueprint-plan` en otra carpeta nueva. Cada árbol debe
   tener ≤6999 triángulos y ≤2 materiales. Los rangos no garantizan que todas las
   combinaciones generen un árbol válido; ante un fallo, conservarlo y explicar
   cualquier revisión en un plan nuevo. No ocultar fallos ni ajustar por semilla.
6. Revisar los resultados visualmente en Godot, con cámaras compartidas si se
   comparan cambios. Distinguir verificación técnica de aceptación artística.
   Entregar galería/rutas y semillas para continuar desde el mismo ejemplar.

Se pueden variar perfiles, estructura y ocupación usando controles existentes.
`canopy.group_count` y pesos regionales cambian ocupación; `base.foliage_density`
controla moldes históricos, no densidad de tarjetas. `base.asymmetry` modifica
ramas. `canopy.leaf_length_m` es tamaño del grupo pintado; no una hoja botánica.
Cambiar solo `seeds.canopy` conserva madera; cambiar la estructura puede mover
soportes y follaje. La pintura aprobada se reutiliza, no se regenera.

## Formato y reproducción

Ejemplo mínimo de plan (hasta 30 casos), con campos reales:

```json
{
  "version": "1.0.0",
  "request": "Crea un roble adulto de copa más abierta, conservando su madera",
  "origin": "codex-session",
  "cases": [{
    "id": "adulto-abierto",
    "seeds": {"base": 2000, "canopy": 17, "paint": 2718},
    "proposal": {
      "profile": "adulto",
      "changes": [{"path": "canopy.group_count", "value": 180}],
      "explanation": "Menos grupos de follaje con la misma madera y tamaño de grupo."
    }
  }]
}
```

Cada propuesta solo selecciona perfil y diferencias respecto a él. Receta,
recursos, límites y componentes no son campos editables por la propuesta.
Se rechazan claves repetidas, parámetros desconocidos, enteros fraccionarios,
booleanos numéricos, valores no finitos, rangos inválidos y semillas incorrectas.

La matriz incluida sirve también como ejemplo reproducible sin volver a pedir
respuestas a Codex:

```sh
PYTHONPATH=src python3 -m treegen plan-blueprints blueprints/roble_copa_ancha/2.2.0.json --request configs/language/f4-responses-v1.json --output artifacts/f4/mi-plan
PYTHONPATH=src python3 -m treegen generate-blueprint-plan artifacts/f4/mi-plan --output artifacts/f4/mis-arboles
```

Preparar congela `request.json`, `blueprint.json`, `resolved.json` y hashes en
`plan.json`. Generar verifica que no se alteraron, resuelve de nuevo y conserva
`batch.json` con estados por ejemplar; cada carpeta contiene el manifiesto,
GLB, blend, semillas y métricas habituales. No sobrescribir carpetas. `--render`
añade vistas Blender; el tiempo por árbol está limitado por la receta y
`--timeout`. Un fallo detiene el lote y queda registrado, sin reintentos.

`origin` distingue una respuesta producida en el chat de una respuesta guardada;
es procedencia declarada, no una prueba criptográfica de inferencia. El ejecutor
no llama modelos. Para registrar una reproducción nueva, copiar el plan con
`origin: "saved-response"`; receta, semillas y parámetros resueltos no cambian.
Los hashes detectan alteraciones accidentales, no son firmas de autenticidad.

## Evaluación F4

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p test_language.py -v
python3 scripts/verify_language.py --output artifacts/f4/otra-evaluacion --stage generate
python3 scripts/verify_language.py --output artifacts/f4/otra-evaluacion --stage review
```

La segunda etapa requiere escritorio real/Godot. Seis solicitudes, doce árboles,
una repetición, 48 capturas y parámetros comparados con el perfil adulto. Misma
semilla no garantiza geometría equivalente entre perfiles; hace reproducible la
comparación. La revisión de esas imágenes y la aceptación del usuario se
registran aparte. [Plan F4](../plans/f4-lenguaje-blueprints.md).
