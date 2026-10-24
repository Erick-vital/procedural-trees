# B3 / RF4: variación y controles del primer tipo

Este informe conserva el ensayo inicial y su fallo. Los pendientes se resolvieron
en la [revisión posterior](../b3-revision/informe.md), sin sobrescribir esta evidencia.

Fecha: 2026-10-23. **Matriz implementada y ejecutada; salida de B3 parcial.**
19 generaciones válidas (incluidas tres repeticiones), tres rechazos previstos
antes de Blender y un fallo geométrico conservado. `verification.json.passed`
es **false** por ese fallo. No se da por comprobado todo el rango permitido.
B4 y lote RF5 no se han iniciado. Aceptación artística del usuario pendiente;
solo el piloto viejo-09 conserva su aprobación previa.

## Receta y protocolo congelados

Se conserva sin modificaciones `blueprints/roble_copa_ancha/1.0.0.json`.
La receta `1.1.0` añade perfiles **experimentales** `joven`, `adulto` y `viejo`,
con los parámetros de edad de `presets/q3-cases.json`. Su perfil predeterminado
sigue siendo `viejo_referencia`: genera el GLB aprobado idéntico byte por byte.
Peticiones reutilizables de los siete casos: `presets/blueprints/b3/`.
Componentes, materiales y algoritmos permanecen en las versiones B2/RF3.
No se han reducido polígonos ni retocado troncos/ramas.

[La matriz](frozen-matrix.json) se fijó antes de generar: cuatro casos RF4,
reservados joven-07/adulto-07/viejo-07 (semillas 1007/2007/3007), controles
individuales y extremos. Estos reservados no se usaron para ajustar RF3;
son casos existentes de Q3, cuya geometría histórica sí pudo haberse visto.
No se afirma una reserva frente a toda inspección histórica del proyecto.

**Regla común**, sin correcciones individuales: 264 grupos, seis hojas por
conexión, hoja nominal de 1 m, planificación de 1 m, anchura y pesos ×1,
semilla de copa 17. Esto prueba la transferencia literal de RF3 a otras edades,
no una calibración específica de hoja por edad. Los parámetros Q3 cambian por
perfil explícito; las semillas no llevan parches particulares.

## Resultados técnicos

| Caso | Altura | Grupos / hojas | Triángulos | Resultado |
| --- | ---: | ---: | ---: | --- |
| Piloto viejo-09 | 9 m | 264 / 1584 | 10572 | GLB idéntico a B0 |
| viejo-00 / viejo-03 / viejo-07 | 9 m | 264 / 1584 | 10572 | Válidos |
| adulto-00 / adulto-07 | 10 m | 264 / 1584 | 9644 | Válidos |
| joven-00 / joven-07 | 4 m | 264 / 1584 | 7324 | Válidos técnicamente |
| Hoja mínima 0,2 m | 9 m | 264 / 1584 | 10572 | Soportes, raíces, ejes y conexiones intactos |
| Cantidad mínima | 9 m | 24 / 144 | 5772 | Válido, copa muy abierta |
| Cantidad máxima | 9 m | 360 / 2160 | 12492 | Válido, 8 triángulos de margen |
| Anchura ×0,85 / ×1,15 | 9 m | 264 / 1584 | 10572 | Madera base intacta |
| Peso este = 0 | 9 m | 194 / 1164 | 9172 | Suprime 70 grupos, otras regiones intactas |
| Semilla de copa 1701 | 9 m | 264 / 1584 | 10572 | Cambia distribución, conserva madera |
| Altura 2 m + moldes 3 m | 2 m | 264 / 1584 | 10572 | Técnico válido, lectura visual inadecuada |
| Altura 20 m + moldes 0,2 m | 20 m | — | — | **Falla contacto; no exporta GLB** |
| Cero grupos / cuatro pesos cero / 361 grupos | — | — | — | Rechazados antes de Blender |

- **75 pruebas** correctas en comprobación final fuera del sandbox. La matriz
  inicial ejecutó las 70 preexistentes; las cinco nuevas comprueban preservación,
  perfiles Q3, reserva, rechazo y extremo presupuestario. La combinación
  individualmente válida de 12 primarias + 360 grupos sigue rechazada por la
  prueba B1 de presupuesto conjunto; la receta 1.1.0 limita a 11 primarias.
- Repeticiones de viejo-00, adulto-00 y joven-00 idénticas en GLB.
- En los siete controles de edad/reservados, posiciones y normales exportadas
  de madera y propiedades de corteza coinciden con sus **GLB Q3 históricos**;
  también coinciden los parámetros/semillas base. [Comparación](q3-comparison.json).
- Los siete controles exclusivos de follaje conservan el canal exportado de
  madera y material del piloto. El control de tamaño conserva también las
  conexiones, raíces, ejes y conteos. El cambio de semilla estructural sí cambia
  la madera; la semilla de copa cambia follaje sin alterarla.
- 25 GLB importados/inspeccionados en Godot: 16 copas únicas y nueve derivados
  de madera desnuda; las tres repeticiones se comparan por hash sin recaptura.
  **225 capturas reales**, nueve por GLB, en lotes de dos escenas.
- Tres materiales por copa, moldes no exportados, altura y contactos comprobados
  por el adaptador. Error máximo de inserción en los 19 éxitos: 0,000004055 m.
  Generación sin render Blender: 1,873–2,636 s; GLB 145804–546284 bytes.
  No es una medición de FPS.

## Fallo del extremo alto

En 20 m/0,2 m, el comprobador final de contacto detecta una de 264 inserciones
a **0,000241903 m** de la madera, frente a tolerancia de 0,0001 m.
Rama `q3:primary:110`; [diagnóstico](height-high-scale-low-diagnostic.json) y
[manifiesto fallido](height-high-scale-low-failure.json).
La inserción procede de la proyección sobre la rama extraída; la comprobación
usa el BVH de toda la madera. No se ha demostrado la causa de esa discrepancia
ni se ha relajado la tolerancia, movido la inserción o exportado un éxito.
Debe investigarse la proyección/triangulación antes de admitir esa combinación.
El diagnóstico se repitió sin mallar/exportar y reprodujo el error.

## Revisión de imágenes reales

Se inspeccionaron [estructura y copa](ages.jpg), [vistas por edad](age-views.jpg),
[controles](controls.jpg) y [resumen](overview.jpg), construidos con capturas Godot.

Viejos y adultos conservan una copa extendida con ramas legibles por debajo;
las semillas cambian la distribución y el contorno. Persisten láminas angulosas
y solapamientos, sin una nueva aprobación artística automática.
En los dos jóvenes, la hoja de 1 m ocupa una fracción grande de la altura:
se percibe una copa compacta, con placas dominantes y menos lectura de ramas.
No se promueve el perfil joven con esta escala común; conviene revisar **un
perfil común de edad**, no corregir cada semilla. Los dos casos reservados se
mantendrán identificados como ya evaluados en una revisión posterior.

La hoja de 0,2 m abre mucho la copa, sin alterar sus soportes; 24 grupos dejan
ramas muy expuestas; 360 grupos aumentan continuidad y solapamiento. Reducir el
peso este abre ese lado y cambiar anchura sí cambia el contorno. El caso de
2 m/3 m está dentro del presupuesto y altura, pero resulta aplanado y dominado
por hojas: se registra como técnico válido y visualmente inadecuado.

Las seis vistas generales comparten cámara y escala global entre toda la
matriz (esfera de la caja conjunta, incluidos los extremos), con iluminación
Godot congelada de B2. `near/medium/far` usan altura al 50/25/10 % y centro del
árbol completo; la pareja madera/copa comparte el mismo encuadre. Por eso
`near` permite comparar lectura, **no tamaño físico entre edades**. En el
extremo de 2 m, `near` corta deliberadamente la anchura; las vistas generales
muestran el árbol completo. No se usó un encuadre nuevo para ocultar ese defecto.

## Reproducción y continuidad

```sh
python3 scripts/verify_blueprint_controls.py --output artifacts/blueprints/otro-b3 --visual
python3 scripts/blueprint_controls_evidence.py --study artifacts/blueprints/otro-b3 --output artifacts/blueprints/evidencia-b3 --q3-reference artifacts/q3/acceptance/lote
# Diagnóstico adicional del caso fallido; sin exportación de éxito:
timeout 180 /home/tao/repos/blender/.tools/blender-5.2.1-linux-x64/blender --background --factory-startup --threads 1 --python-exit-code 1 --python blender/diagnose_blueprint_contacts.py -- artifacts/blueprints/otro-b3/height-high-scale-low
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Usar carpeta de matriz nueva. Blender/Godot y entorno: los de B2.
Generación ≤120 s; pruebas, inspecciones y capturas ≤180 s por subproceso.
Ejecutar fuera del sandbox si bloquea sockets loopback/audio/interfaz.
El script termina la matriz y escribe `passed=false` cuando un caso falla;
terminar el proceso no significa que toda la matriz pasó. La evidencia conserva
fallos y no exige `passed=true`. Sin `--visual` no se generan las láminas.
La comparación Q3 es opcional y requiere conservar el lote histórico; generar
blueprints sigue sin depender de ese lote ni de `docs/`/`artifacts/` previos.

Resultado local: `artifacts/blueprints/b3-controls-02/index.html`.
Los manifiestos originales de generación permanecen intactos; los GLB de madera
y las cámaras de evaluación están separados bajo `inspection/`.
La receta experimental expone rangos de entrada, **no un rango completamente
verificado**. B3 queda abierta para resolver el contacto del extremo y el perfil
joven; los casos adulto/viejo y sus controles ya tienen evidencia técnica y visual.
