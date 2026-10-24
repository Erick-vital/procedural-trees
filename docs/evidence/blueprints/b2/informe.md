# B2: primer blueprint integrado y RF3 conservada

Fecha: 2026-10-23. Implementada y verificada. El usuario autorizó B2 para
registrar el primer blueprint y conservar el resultado RF3 aprobado en B0.
No se inicia B3 ni se amplía la aprobación a otras edades o semillas.

## Resultado

Primer blueprint: [roble_copa_ancha 1.0.0](../../../../blueprints/roble_copa_ancha/1.0.0.json),
**Roble estilizado de copa ancha**, sin atribución botánica específica.
Único perfil publicado: `viejo_referencia`. Ejemplar aprobado:
[petición viejo-09](../../../../presets/blueprints/roble-copa-ancha-viejo-09.json).
Mantiene base Q3 0.4.0, semilla 3009, semillas efectivas 669423365/927115663,
RF3 `foliage-canopy-0.1.0` con semilla 17 y planificación de hoja de 1 m.

Se conservan **9 m, 10572 triángulos, 1584 hojas, 264 conexiones y tres
materiales**. Madera base de 5292 triángulos, hojas 3168 y conexiones 2112.
Los 89 moldes no se exportan. Límites actuales: 12500 triángulos y tres materiales.

El GLB de ambos trabajos nuevos es **idéntico byte por byte al RF3 aprobado**:

`759f18aa259decf34dc6135000b07560eb730eacb29b001517deaf12f5876b5b`.

También coinciden las firmas normalizadas de posiciones, normales, sentido de
caras, materiales, escena, transformación, madera, moldes, soportes y hojas.
La integración no cambia la geometría, la escala ni la interpretación de semillas.

[Comparación real en Godot](comparison.jpg) y [verificación seleccionada](verification.json).
Se generaron 24 capturas nuevas, doce por modelo; cada pareja tiene píxeles
idénticos, diferencia máxima por canal cero. Revisión real de las doce vistas
en dos hojas de contacto: misma copa y sombreado, huecos e intersecciones;
persisten las hojas grandes/angulosas y solapamientos del resultado aprobado.
No se atribuye una mejora artística o de rendimiento a esta integración.

## Generación autónoma y arquitectura

`blender/generate_blueprint.py` construye en memoria el grafo Q3 usando sus
fuentes históricas. Evalúa madera y moldes, reconstruye relaciones de ramas y
aplica las reglas RF3 con sus identificadores y orden originales. Los materiales
proceden de la receta. La configuración de inspección queda versionada en
`configs/inspection/rf3-v1.json`, con las cámaras y condiciones RF3 congeladas.

Se reutilizan helpers geométricos puros de los adaptadores de laboratorio. No se
invocan sus funciones de preparación ni se leen sus resultados: la nueva ruta
no abre referencias RF0/RF2, un `.blend` previo ni carpetas de ensayos. Las fuentes
algorítmicas históricas no se modifican. `base-reference.json` se produce dentro
del trabajo como dato intermedio regenerable, sin depender de otro trabajo.

El ejecutor `runner.execute` conserva directorio nuevo por trabajo, estados de
fallo, procesos terminables y validación. `execute_blueprint` añade la resolución
B1 y selecciona el adaptador nuevo; el timeout efectivo es el menor entre el
solicitado y el límite de receta, nunca más de 120 s para este blueprint.
La API histórica sigue aceptando `TreeSpec`; esta fase no amplía su contrato HTTP.

`validate_result` reconoce trabajos `kind=blueprint`, vuelve a resolver la receta
congelada y verifica sus entradas, firmas exportadas y presupuesto explícito.
Los trabajos históricos mantienen el techo predeterminado de 10000 triángulos.
El manifiesto conserva definición completa, versión/hash de blueprint, petición,
perfil, parámetros, semillas, versiones, fuentes y hashes de entradas/salidas.
`compare` distingue cambios de resolución aunque la especificación base coincida.

## Uso

Desde la raíz del repositorio:

```sh
PYTHONPATH=src python3 -m treegen blueprints
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/roble_copa_ancha/1.0.0.json --instance presets/blueprints/roble-copa-ancha-viejo-09.json --output artifacts/blueprints/mi-primer-roble
PYTHONPATH=src python3 -m treegen validate artifacts/blueprints/mi-primer-roble
```

Usar una carpeta de salida nueva. `--no-render` omite doce vistas Blender;
siempre se guardan `.blend`, GLB, entrada, referencia intermedia, cámaras, log y
manifiesto. El JSON del ejemplar permite cambios solo dentro de los rangos de
la receta. Las semillas se declaran en ese JSON y no forman parte del blueprint.

Para repetir exactamente un trabajo después de cambiar el catálogo, usar la
definición de `resolved_blueprint.blueprint_definition` y la petición de
`resolved_blueprint.instance_request` de su manifiesto con `execute_blueprint`.
La identidad/versionado y el hash completo quedan ligados al resultado.

Los comandos `generate`, `batch`, `serve` y presets históricos permanecen
disponibles. Los presets principales Q3b no se promueven ni sobrescriben: la
entrada nueva selecciona explícitamente Q3 + RF3. Así se evita su elección
accidental al usar el blueprint, conservando la historia reconstruible.

## Comprobaciones realizadas

- Seis pruebas B2 nuevas; **70 pruebas totales correctas** fuera del sandbox.
  Cubren registro, entradas exactas, fallos previos a Blender, timeout, resolución
  congelada y distinción de límites 12500/10000 según tipo de trabajo.
- Generación mediante la CLI pública: `artifacts/blueprints/b2-pilot-02`.
- Verificación integral en `artifacts/blueprints/b2-acceptance-01/`.
  El script copia fuentes, esquemas, configuración, blueprint y petición a
  `isolated-source/`, **sin `artifacts/` ni `docs/`**. Desde allí genera el piloto
  y una repetición sin render en procesos nuevos; ambas coinciden con B0.
- Importación y comprobación Godot 4.7.2 en un proyecto propio con solo los dos
  GLB. Cámaras/luz comunes; doce vistas por modelo y comparación exacta de píxeles.
- Duraciones observadas del proceso CLI: piloto 5.631 s y repetición 3.129 s,
  en este equipo. No equivalen a FPS ni a tiempos generales de otros árboles.
- Primer intento dentro del sandbox: exportó correctamente pero Blender no
  terminó al cerrar por el audio; timeout a 120 s y estado `failed`. La ejecución
  autorizada fuera del sandbox terminó y validó. No se cuenta el intento fallido
  como generación correcta.

Reproducción de esta verificación, con sesión gráfica y las herramientas fijadas:

```sh
python3 scripts/verify_blueprint_generation.py --output artifacts/blueprints/otra-verificacion-b2 --visual
```

Sin `--visual` se verifican generación, repetición e importación, sin revisión
de imágenes. La copia aislada demuestra independencia de datos de ensayos,
no instala Blender/Godot ni dependencias Python en otra máquina.

La auditoría estricta B0 del árbol de fuentes señalará los cambios intencionados
en ejecutor/CLI/evaluación. El lock no se actualiza: conserva la referencia
histórica y su commit de recuperación. B2 compara el nuevo resultado contra
esas firmas y mantiene intactos los archivos geométricos aprobados.

## Límites y siguiente fase

Solo se registra el perfil de referencia. Rangos editables y semillas nuevas
siguen siendo entradas permitidas, no combinaciones artísticamente aprobadas.
Copa vacía continúa rechazada según B1. No hay prueba de otras edades, viento,
LOD, bosque ni rendimiento de integración en juego. El siguiente paso es B3:
variación del primer tipo y controles RF4, sin ajustes ocultos por ejemplar.
