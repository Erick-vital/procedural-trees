# RF5: treinta robles con follaje RF3

Fecha: 2026-10-23. **Lote ejecutado y verificado técnicamente: 30/30 correctos,
sin fallos ni reintentos.** Matriz `passed=true`, 74 comprobaciones correctas,
88 pruebas Python, regresión adicional Blender y tres repeticiones idénticas.
Se revisaron imágenes reales de Godot. **El usuario aprueba artísticamente el
lote completo el 2026-10-23:** le gustó la mayoría y no observó ejemplares que
se desvirtuaran. [Aceptación vinculada a los treinta GLB](user-acceptance.json).
Su [aprobación B3](../../blueprints/b3-revision/user-acceptance.json) autorizó
esta ejecución, incluida la hoja joven de .45 m. La verificación y matriz
conservan sus menciones históricas de aprobación pendiente; la decisión es posterior.

## Entradas y alcance

- [Matriz congelada](frozen-matrix.json), idéntica a
  `configs/verification/rf5-v1.json`, fijada antes de generar.
- Receta exacta `roble_copa_ancha` 1.2.0, sin modificar componentes, parámetros,
  geometría, materiales ni límites. Los estados `experimental` de esa receta
  son metadatos históricos conservados; la aprobación B3 posterior está aparte.
- Treinta casos de `presets/q3-cases.json`: diez por edad, semillas base
  1000–1009, 2000–2009 y 3000–3009; semilla de copa 17 común. Sin overrides
  individuales. No se presentan como treinta casos inéditos o reservados.
- Se usa el ejecutor compartido de blueprints; `batch` sigue siendo TreeSpec
  histórico y no se reinterpreta como lote RF3. Las referencias Q3 sirven solo
  para comparación: no suministran geometría a los blueprints.
- Se conserva RF3 como alternativa explícita. Los alias TreeSpec y el inicio
  rápido histórico permanecen en sus selecciones aprobadas. Las treinta semillas
  reciben aprobación explícita posterior del usuario; los predeterminados se conservan.

## Resultados

| Perfil | Casos | Altura | Hoja nominal | Triángulos por árbol | Materiales |
| --- | ---: | ---: | ---: | ---: | ---: |
| Joven | 10 | 4 m | .45 m | 7324 | 3 |
| Adulto | 10 | 10 m | 1 m | 9644 | 3 |
| Viejo | 10 | 9 m | 1 m | 10572 | 3 |

Cada árbol contiene 264 conexiones y 1584 hojas. La hoja joven conserva
planificación de 1 m y conteos: su reducción es de tamaño, sin cambiar madera
ni cantidad de hojas. Treinta firmas geométricas distintas; ningún caso supera
12500 triángulos. No hay entradas geométricas externas al generar.

Generación por árbol: **2.584–3.994 s**, mediana **3.140 s**; suma de treinta
generaciones **93.195 s**. GLB de **353248–434292 bytes**, total **12016588 bytes**.
Ejecución completa del verificador: 209.437 s, incluidas pruebas, comparación,
repeticiones, contactos, exportaciones de inspección y Godot; los límites son
por subproceso, no por lote. No son mediciones de FPS ni pruebas de mejora IA.

- Los treinta GLB fueron validados contra sus manifiestos y límites: geometría
  finita, índices, degeneraciones, dimensiones, materiales, normales y hashes.
- [Comparación Q3](q3-comparison.json): en los treinta casos coinciden la
  especificación base, geometría y normales exportadas de madera, y corteza.
- Viejo-09 conserva el **GLB exacto de B0**. Repeticiones fijadas previamente
  de joven-00, adulto-00 y viejo-09: GLB, madera, soportes, ramillas y colocaciones
  idénticos. Las recetas y fuentes comprobadas no cambiaron durante la ejecución.
- Treinta GLB reimportados en Blender, **7920 inserciones**, error máximo
  **0.0000930764 m** frente al límite de .0001 m. Se conservan las comprobaciones
  de raíces de hojas dentro de sus propias conexiones.
- **60 escenas verificadas en Godot:** treinta árboles completos y treinta
  exportaciones de madera para inspección. **360 capturas reales:** nueve
  vistas por árbol completo y tres por madera. Dos escenas por proceso;
  dos dibujos completados después de cambiar cámara o asset.
- Entorno: Blender 5.2.1 LTS `9e2066aef7ef`, Python Blender 3.13.13,
  orquestación Python 3.14.4, Godot 4.7.2 `ed1daf0bf`, compatibilidad GL.
  Versiones y procedencia por ejemplar en sus manifiestos.

[Verificación y estadísticas](verification.json), [pruebas](unit-tests.txt).

## Revisión visual del agente

Se inspeccionaron las seis láminas de cinco árboles y cuatro vistas por árbol
(near, perfil, arriba y abajo), además del resumen de treinta, la escala física
común y la comparación de madera de tres representantes. También se abrieron
capturas individuales de joven-05 y adulto-05. Esto es revisión de capturas
reales Godot, no una sesión interactiva de recorrido ni aprobación del usuario.

Los jóvenes mantienen copas pequeñas agrupadas, con bifurcaciones visibles;
adultos y viejos conservan copas más anchas y ramas ascendentes visibles entre
hojas. Se aprecian diferencias de silueta entre semillas sin ajustes particulares.
No se observaron pérdidas de materiales o partes ausentes en las vistas
revisadas. Persisten hojas angulosas, concentración, placas solapadas y patrones
repetidos; esta revisión no demuestra ausencia de todas las intersecciones.

Las vistas generales usan cámara y escala física común para toda la familia,
sin recortar su caja global. Por eso los jóvenes aparecen pequeños en perfil,
arriba y abajo; sirven para revisar silueta y escala, no detalles locales.
Near/medium/far usan altura al 50/25/10 % del encuadre, centradas por ejemplar;
no permiten comparar tamaño físico entre edades. Luz y materiales son comunes.

- [Resumen de treinta](overview.jpg) · [escala física común](physical-scale.jpg).
- Jóvenes: [00–04](joven-00-views.jpg) · [05–09](joven-05-views.jpg).
- Adultos: [00–04](adulto-00-views.jpg) · [05–09](adulto-05-views.jpg).
- Viejos: [00–04](viejo-00-views.jpg) · [05–09](viejo-05-views.jpg).
- [Madera y copa, tres representantes](wood-comparison.jpg).

Galería completa regenerable:
`artifacts/rediseno-follaje/rf5-lote-01/index.html`.
GLB por caso: `artifacts/rediseno-follaje/rf5-lote-01/<caso>/tree.glb`.

## Reproducción

Desde la raíz, con las herramientas fijadas y directorios de salida nuevos:

```sh
python3 scripts/verify_rf5.py --output artifacts/rediseno-follaje/otro-rf5 --visual
python3 scripts/rf5_evidence.py --study artifacts/rediseno-follaje/otro-rf5 --output artifacts/rediseno-follaje/otra-evidencia-rf5
```

El primer comando compara por defecto con `artifacts/q3/acceptance/lote`.
Si no existe, generar una referencia desde fuentes y pasar su ruta:

```sh
PYTHONPATH=src python3 -m treegen batch --cases presets/q3-cases.json --output artifacts/rf5-base-q3
python3 scripts/verify_rf5.py --q3-reference artifacts/rf5-base-q3 --output artifacts/rediseno-follaje/otro-rf5 --visual
```

La copia de evidencia es independiente de la generación y no copia modelos,
logs voluminosos ni cachés. Conserva nueve imágenes seleccionadas, matriz,
pruebas y verificación compactada. El reporte registra hashes de las 360
capturas originales y de las imágenes seleccionadas. Blender ≤120 s por
generación; pruebas/capturas/contactos ≤180 s por subproceso terminable.
Fuera del sandbox cuando sea necesario por sesión gráfica, audio o loopback.

## Cierre y límites

RF5 queda cerrada: ejecutada, verificada y aprobada artísticamente por el usuario
para estos treinta casos. No se cambió ningún algoritmo para salvar semillas. RF3 continúa como alternativa explícita a Q3; no se promueve a estilo
predeterminado ni se borra la familia poligonal. La guía documenta cómo añadir
[perfiles, tipos y representaciones](../../../uso-blueprints.md).

La copa columnar no forma parte de este lote ni de la aprobación B3. No se
acreditan todos los rangos de parámetros. Sin viento, LOD, bosque, terreno,
rendimiento gráfico ni experimentos IA F4–F6 en esta fase.
