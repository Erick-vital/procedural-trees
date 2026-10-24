# B0: referencia RF3 del primer tipo de árbol

Fecha: 2026-10-23. Referencia adoptada por aprobación explícita del usuario:
«RF3 queda aprobada como referencia de nuestro primer tipo de arbol».
El resultado adoptado es el **piloto RF3 viejo-09**, no los controles de anchura,
ocupación o tamaño de hoja. Nombre artístico provisional: Roble estilizado de
copa ancha; identificador futuro `roble_copa_ancha`. No existe aún un blueprint
ejecutable ni se atribuye una especie botánica concreta.

## Referencia congelada

[reference-lock.json](reference-lock.json) registra la decisión, entradas,
semillas, versiones, materiales, cámaras, iluminación, firmas normalizadas y
SHA-256 de 133 archivos. Incluye las 105 fuentes registradas en el ensayo RF3,
que coinciden con las disponibles al congelar. Es un registro de conservación,
no el contrato funcional de blueprint de B1.
Las 105 fuentes también coinciden con sus objetos en el commit indicado en
`git_head_at_freeze`: se pueden recuperar desde Git sin guardar otro archivo de
fuentes completo. Si B2 modifica una de ellas, la auditoría estricta señalará
la diferencia; la comparación de la nueva ejecución usará las firmas congeladas.

| Dato | Valor adoptado |
| --- | --- |
| Ejemplar | `viejo-09`, Q3 `oak_geometry_nodes` 0.4.0 |
| Semilla base / efectiva estructura / efectiva follaje Q3 | 3009 / 669423365 / 927115663 |
| Follaje nuevo / semilla | `foliage-canopy-0.1.0` / 17 |
| Altura / triángulos / materiales | 9 m / 10572 / 3 |
| Madera base / conexiones / hojas | 5292 / 2112 / 3168 triángulos |
| Conexiones / hojas | 264 / 1584 |
| Guías invisibles | 89 moldes Q3; excluidos del GLB |
| Representación | Rombo opaco de 1 m ±10 %, seis hojas por conexión |
| Perfil / ocupación | Anchura 1; pesos norte/este/sur/oeste todos 1 |
| Presupuesto autorizado | 12500 triángulos / tres materiales |

Los parámetros completos están embebidos en el lock. No sustituir la semilla
de follaje nueva por la semilla efectiva de follaje Q3: esta última determina
los moldes originales. El ajuste vertical usa la caja de madera, escala Z
0.8185054999022341 y traslación Z 0.009523311491362494; la matriz del objeto
es identidad. Blender 5.2.1 LTS, build `9e2066aef7ef`.

Los archivos aprobados permanecen en
`artifacts/rediseno-follaje/rf3-acceptance-02/pilot/`: `tree.glb`, `tree.blend`,
`manifest.json`, `cameras.json` y doce capturas `godot-*.png` de 900×900.
El lock conserva sus hashes sin copiar grandes salidas regenerables a Git.
Las [comparaciones RF3](../../rediseno-follaje/rf3/informe.md) conservan imágenes
seleccionadas. La decisión nueva complementa sus resúmenes técnicos históricos,
que no se reescriben para cambiar un hash de evidencia pasada.

## Inventario y frontera de migración

| Dependencia actual | Uso real | Tratamiento al integrar en B2 |
| --- | --- | --- |
| `docs/evidence/rf0-rf1/reference-lock.json` | `prepare` lee ruta Q3, hashes, materiales, cámaras y luz | Conservar como evidencia; trasladar configuración necesaria a datos versionados |
| `artifacts/q3/acceptance/lote/viejo-09/tree.blend` | `prepare` abre madera, atributos, grafo y canales; reconstruye ramas y moldes | Generar Q3 desde especificación/fuentes, sin exigir el archivo previo |
| GLB y manifiesto del mismo Q3 | Comprobación de hashes, métricas y lectura de especificación/semillas/normalización | Mantenerlos para comparación histórica; producir entradas nuevas durante la ejecución |
| `docs/evidence/rediseno-follaje/rf2-densidad/aceptacion.json` | `prepare` comprueba aprobación y hashes de rama | Mantener procedencia; no convertir la aceptación documental en dependencia de producción |
| `artifacts/rediseno-follaje/rf2-densidad-01/leaves-144/` | Manifiesto aporta receta RF2; `branch.glb` se verifica; cámaras aportan tres detalles | Expresar receta y cámaras como datos; GLB de rama solo como referencia de comparación |
| `reference/reference.json` de RF3 | `candidate` consume madera, ramas, moldes, materiales, cámaras y verifica archivos Q3 | Construir el equivalente como datos intermedios en cada ejecución |
| `pilot.json` y `presets/foliage-canopy.json` | Parámetros RF3 idénticos; el preset actual puede cambiar después | Mantener copia exacta y hash del piloto; resolver parámetros explícitos desde blueprint |
| Helpers `foliage_*_lab.py`, `foliage_fusion.py`, `generate_oak.py`, `oak_nodes*.py` y núcleo `treegen` | Construcción, consultas BVH, materiales, mallado, validación y exportación | Extraer/reutilizar solo lo requerido, con versiones explícitas y regresión |
| Capturas, galería, informes y resumen RF3 | Comparación y procedencia; no generan el árbol | Evidencia seleccionada y firmas conservadas; no entradas geométricas de producción |

La lista exacta de archivos y sus hashes está en el lock. Las rutas absolutas
persistentes en RF0, aceptación RF2 y referencia RF3 funcionan en este equipo;
la auditoría expresa sus archivos con rutas relativas al repositorio. Reubicar
el proyecto requiere regenerar/resolver esos enlaces; la portabilidad autónoma
es trabajo de B2, no un resultado de B0.

## Contrato de conservación para B2

- Conservar madera completa, polígonos y sombreado de Blender, coordenadas,
  transformación, normalización, semilla estructural y propiedades de corteza.
- Conservar para el ejemplar de referencia los moldes, identificadores y asignación
  de rama padre, soportes, colocaciones, semillas y parámetros RF3. Sus hashes
  exactos están en `snapshot.manifest_invariants` del lock.
- Conservar altura y conteos por material; no reducir geometría ni reemplazar
  hojas por tarjetas. Separar siempre madera base, conexiones y hojas.
- Comparar posiciones/normales exportadas por material redondeadas a seis
  decimales, con las firmas existentes y una firma adicional que conserva el
  sentido de cada triángulo. Tolera reordenar índices/triángulos y rotaciones
  cíclicas de sus esquinas; invertir una cara cambia la firma.
- Conservar propiedades completas de materiales, nodos/transformaciones y escena
  glTF. Las firmas de nodos actuales son estrictas; cualquier reorganización
  deberá justificarse mediante equivalencia de transformaciones efectivas.
- Los hashes binarios sirven para integridad del archivo aprobado. Una diferencia
  binaria tras exportar exige comparar contenido; por sí sola no demuestra cambio
  geométrico. En el entorno fijado se exige igualdad de firmas normalizadas.
- Acompañar B2 con revisión de imágenes reales en Godot bajo las doce cámaras
  congeladas, misma luz, paleta y renderer. Nueve vistas generales sin recorte;
  los tres detalles tienen recorte intencionado. No reencuadrar para ocultar cambios.
- Registrar diferencias y revisión si se modifica la geometría para integrar.
  La migración equivalente y una iteración artística tienen criterios distintos.

## Reproducción y comprobación

Auditoría de archivos, integridad y GLB sin lanzar Blender:

```sh
python3 scripts/verify_blueprint_reference.py --output artifacts/blueprints/mi-auditoria-b0
```

Reconstrucción desde las dependencias históricas: `prepare` reconstruye la
referencia Q3 y `candidate` genera otra copa sin render; procesos nuevos,
120 s por proceso, carpetas nuevas y sin reintentos automáticos:

```sh
python3 scripts/verify_blueprint_reference.py --output artifacts/blueprints/mi-reproduccion-b0 --reproduce
```

El verificador compara entradas/salidas con el lock, comprueba GLB y firma de
referencia reconstruida, y escribe `verification.json`, incluso ante fallo.
Los logs y archivos nuevos quedan en la carpeta elegida. B0 no crea la ruta de
generación desde una copia limpia: todavía necesita los archivos históricos
inventariados. Una ausencia o modificación causa error explícito, sin actualizar
el lock automáticamente.

Resultados de esta sesión: ver [verification.json](verification.json).
Auditoría de 133 archivos correcta; referencia reconstruida idéntica y copa
reproducida con iguales firmas de geometría, orientación, materiales, soportes
y colocaciones. Un control negativo invirtió una cara en una copia temporal
del GLB y la firma adicional detectó el cambio. El primer intento dentro del
sandbox exportó la referencia, pero quedó bloqueado al cerrar por audio y fue
terminado a los 120 s: se conserva como fallo. El segundo intento autorizado
fuera del sandbox completó ambos procesos y las comparaciones.
Esta fase no añade una nueva validación artística ni una nueva importación Godot;
adopta la revisión RF3 existente y la aprobación del usuario. B1 se implementó
a continuación por petición del usuario; B2–B5, RF4 y el lote de RF5 siguen pendientes.
