# B5: documentación y cierre del sistema de blueprints

Fecha: 2026-10-23. **B0–B5 cerradas técnicamente.** Dos tipos documentados,
primer tipo preservado y reutilización demostrada en B4. La documentación y
las interfaces se verificaron mediante la CLI real. La matriz de cierre termina
con `passed=true`: 85 pruebas, siete generaciones y 19 comprobaciones correctas.
La aprobación artística de perfiles nuevos/columnar y el lote RF5 son decisiones
separadas de este cierre.

## Documentación vigente

- [README](../../../../README.md): punto de entrada breve, catálogo, inicio
  rápido seguro, entorno, estado de aprobación y alcance abierto.
- [Guía de uso](../../../uso-blueprints.md): listar/seleccionar versiones,
  generar/validar, perfiles y semillas, repetir/comparar y extraer receta y
  petición congeladas del manifiesto. Distingue la API TreeSpec de la CLI
  blueprint y explica qué entradas históricas siguen disponibles.
- [Operación histórica](../../../operacion-historica.md): comandos y enlaces
  F0–RF3 que ocupaban el README, con rutas ajustadas a su nueva ubicación y
  selección explícita de versiones en los ejemplos históricos.
- [Contrato](../../../contrato-blueprints.md),
  [plan cerrado](../../../../plans/sistema-blueprints.md) y
  [estado vigente](../../../../ESTADO.md) coordinados con estos resultados.

Catálogo real: [cuatro versiones, dos tipos](catalog.json).
`roble_copa_ancha` 1.0.0 conserva viejo-09 aprobado;
1.1.0 conserva el ensayo inicial; 1.2.0 incorpora los controles corregidos y
hojas jóvenes de .45 m. `arbol_copa_columnar` 1.0.0 conserva el segundo tipo B4.
No se editó ni promovió ninguna receta/perfil para cerrar B5.

## Decisión explícita de predeterminados

La CLI blueprint exige ruta de receta y ejemplar; no existe resolución “latest”.
El perfil predeterminado se aplica dentro de una receta ya elegida. El inicio
rápido usa explícitamente el roble 1.0.0 y viejo-09 aprobado, evitando promoción
automática de los perfiles experimentales.

Los alias TreeSpec sin versión todavía apuntaban a Q3b rechazada. B5 cambia
`presets/joven.json`, `adulto.json` y `viejo.json` para que sean **idénticos a
sus archivos Q3 0.4.0**, previamente aprobados, en `presets/v0.4.0/`.
Antes de sustituirlos se guardaron sus contenidos Q3b **byte por byte** en
`presets/v0.4.1/`. También se conserva el lote `presets/q3b-cases.json`.
[Decisión y hashes antes/después](defaults-decision.json).

No se convierten TreeSpec en blueprint, ni se cambia el contrato de `generate`
o de la API. Sus peticiones siguen siendo explícitas. `batch` conserva su
valor histórico `presets/f2-cases.json` (0.1.0), documentado como lote F2 y no
como lote de blueprints/RF5. Los algoritmos históricos siguen seleccionables
por su versión y ruta, incluida Q3b deliberadamente.

Esta corrección de alias selecciona una familia ya aprobada; no acredita ni
promueve las demás edades/semillas RF3 ni el segundo tipo artístico.

## Regresión detectada durante el cierre

El primer ensayo `artifacts/blueprints/b5-closure-01` pasó las cinco generaciones
blueprint y su extracción desde manifiesto, pero la generación TreeSpec se
marcó fallida al finalizar con `KeyError: files_sha256`.
El adaptador histórico no emitía ese campo y el ejecutor compartido intentaba
actualizarlo incondicionalmente al registrar los artefactos.

Se añadió `result.setdefault('files_sha256', {})` antes del registro común,
con una prueba específica de finalización correcta de TreeSpec sin ese campo.
No se cambió generación, geometría, materiales, contratos ni algoritmos.
El GLB exportado antes del fallo es **idéntico byte por byte** al posterior a
la corrección. [Regresión y hashes](legacy-regression.json).
El fallo inicial queda conservado; no se presentó como éxito ni se reintentó
sobre su carpeta. El cierre final usa una copia y resultados nuevos.

## Verificación final reproducible

```sh
python3 scripts/verify_blueprint_closure.py --output artifacts/blueprints/otro-cierre
```

La prueba crea una carpeta nueva y una copia con `src`, `blender`, `schemas`,
`configs`, `blueprints` y `presets`, **sin `docs/` ni `artifacts/` previos**.
Las generaciones se realizan con la CLI y esa copia como raíz. Los informes
B0/B4 intervienen únicamente después, como comparación de hashes; no son
entradas geométricas. Se usa el entorno de herramientas ya fijado en B2–B4.

| Generación | Comprobación |
| --- | --- |
| `roble-a` / `roble-b` | Receta 1.0.0 y ejemplar viejo-09; repetición exacta |
| `columna-a` / `columna-b` | Receta columnar 1.0.0 y piloto B4; repetición exacta |
| `roble-congelado` | Receta/petición extraídas mediante el bloque Python de la guía |
| `q3-alias` / `q3-explicit` | `presets/adulto.json` y `presets/v0.4.0/adulto.json` equivalentes |

Resultados:

- **85 pruebas correctas**, incluida la nueva comprobación de alias Q3/historia
  Q3b y la regresión de finalización de TreeSpec. [Salida](unit-tests.txt).
- Catálogo exacto de cuatro versiones/dos tipos y tres alias apuntando a Q3;
  tres presets Q3b archivados y válidos por versión explícita.
- Siete generaciones y siete validaciones CLI correctas en la copia limpia.
- Cuatro comparaciones CLI: mismo spec/resolución, entorno, fuentes, cámaras
  y geometría; diferencia de triángulos cero y **GLB idéntico byte por byte**.
- Receta y petición extraídas de manifiesto iguales a los datos originales.
  La guía advierte que congelar entradas no instala fuentes/entornos antiguos.
- Roble idéntico al GLB aprobado B0; columnar idéntico al piloto B4.
- Alias TreeSpec Q3 idéntico al archivo explícito Q3; la corrección de metadatos
  del ejecutor no modifica el GLB que se había exportado en el ensayo fallido.

[Informe seleccionado](verification.json). Resultado completo:
`artifacts/blueprints/b5-closure-02/`. Las comparaciones incluyen JSON/HTML;
las vistas no solicitadas se indican como no generadas.

**B5 no genera nuevas capturas ni declara una validación visual nueva.**
Reutiliza las revisiones reales de [B3](../b3-revision/informe.md) y
[B4](../b4/informe.md), con identidad exacta de sus GLB de referencia.
Las validaciones técnicas no sustituyen aprobación estética ni medidas FPS.

Los subprocesos tienen límite: generación blueprint ≤120 s y ejecución de
comandos/cierre ≤180 s por subproceso terminable. Ejecutar fuera del sandbox
cuando bloquee sockets loopback o el cierre de audio de Blender.

## Cierre y decisiones que permanecen separadas

**Decisión RF5 en B5: no ejecutar el lote de treinta.** El usuario solicitó
cerrar el sistema; no generar/promover el lote. Se requiere una decisión futura
separada para ejecutarlo y evaluar sus treinta resultados. Los lotes históricos
F2/Q3 no se reinterpretan como un lote RF3 realizado.

Quedan explícitamente fuera de este cierre:

- Aprobación artística del usuario de perfiles RF3 nuevos y tipo columnar.
- Validación de todas las semillas/intervalos, edades adicionales de columnar
  y generalización botánica. Las recetas nuevas continúan experimentales.
- Lote/promoción RF5, rendimiento en motor, viento, LOD, bosque y terreno.
- Experimentos IA F4–F6 del plan v1: el sistema de recetas no los sustituye.

La referencia aprobada, los contratos, las rutas históricas y la evidencia
seleccionada quedan disponibles sin depender de conversaciones anteriores.
