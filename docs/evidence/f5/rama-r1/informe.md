# R1: rama jerárquica con follaje congelado

Fecha: 2026-11-03. **Muestra implementada y verificada; aceptación artística pendiente.**
Autorización: «ok continua con esa rama de muestra, quiero ver una ramificacion
mas natural sin perder la copa que ya me gusta». Durante el trabajo el usuario
pregunta por qué se migró desde nodos; se añade esa referencia y se conserva
el generador histórico. [Alcance](../../../../plans/f5-estructura-espacial.md).

## Qué comparar

[Vista breve](comparacion.jpg), [madera: seis vistas](wood.jpg),
[con follaje: seis vistas](tree.jpg), [máscaras](mascaras.jpg),
[auditoría y hashes](verification.json).
Galería local: `artifacts/f5/rama-r1-03/index.html`.

Columnas de izquierda a derecha:

1. **Anterior F5**: primaria 100 y sus tres secundarias del `candidate/joven-03`,
   más los conectores conservados por la representación pintada.
2. **Nueva R1**: mismo eje principal y los mismos 87 grupos de follaje. Reemplaza
   secundarias/conectores por una red de ramillas con recorridos compartidos,
   tres nacimientos escalonados y bifurcaciones de dos salidas.
3. **Nodos**: rama del mismo perfil y semilla base 1003, regenerada con receta
   aprobada `roble_copa_ancha@2.2.0`, sin sustitución de estructura. Tiene su propio
   follaje; se alinea rígidamente al origen/dirección principal de F5 para revisar
   forma y escala. No se escala ni se compara su copa como si fuera idéntica.
   Transformación explícita en `nodes-presentation.json` del resultado local.

La referencia por nodos también muestra haces radiales de soportes. Este caso
sitúa parte del problema en la representación compartida de conexiones; no
prueba que una base sea artísticamente superior en todo el catálogo. La migración
Python de F5 facilitaba el experimento espacial; no era requisito para producir
árboles ni una mejora artística demostrada. Las recetas de producción siguen
usando sus bases registradas y no se promueve Python por este ensayo.

## Cambio e invariantes

`branch-sample-network-0.1.0`, semilla **1003**. Ordena los destinos por posición
longitudinal respecto al eje y los reparte en tres cupos. Sus nacimientos están
al 32/56/79 % de longitud. Cada subred divide espacialmente los destinos, avanza
hacia sus centros y bifurca en dos con grosor proporcional a la cantidad de
extremos sostenidos; los terminales se afinan hasta una punta. Curvatura suave en
los tres tramos iniciales; el resto son segmentos facetados con radios decrecientes.

**87 grupos / 261 láminas / 522 triángulos de follaje exactamente conservados**:
posiciones, caras, UV, normales, plantillas, pintura y materiales. La madera
principal de la muestra se conserva. La red alcanza el centro geométrico de cada
cruzada, sin recolocar hojas para acomodar la madera. Hay 171 tramos nuevos,
profundidad máxima 6, dos hijos como máximo por bifurcación.

La conservación visual se verifica con dos GLB de follaje aislado binariamente
idénticos y seis pares de máscaras Godot idénticas píxel por píxel, no vacías.
Esto acredita el follaje aislado; la imagen completa puede cambiar por madera
visible y sombras. No certifica que cada terminal coincida con un píxel opaco
de una ramilla pintada ni una soldadura topológica de la madera: las uniones
comparten centros y superficies en contacto/solapadas, con mallas independientes.

## Resultados y presupuesto

| Muestra | Madera | Follaje | Total | Materiales |
| --- | ---: | ---: | ---: | ---: |
| Anterior F5 | 536 | 522 | 1058 | 2 |
| Nueva R1 | 1178 | 522 | 1700 | 2 |
| Nodos (follaje propio) | 464 | 534 | 998 | 2 |

La red nueva cuesta 1038 triángulos; otros 140 son el eje principal conservado.
Esta muestra añade madera para compartir ramillas y alcanzar también grupos
nacidos de primarias que antes no conservaban conectores individuales visibles.
No se presenta como una optimización de triángulos ni de FPS.

Proyección conservadora para una integración futura: `madera principal +
18 × grupos + 18 × (primarias + 1)`. Incluye tronco/primarias existentes,
6 tris por grupo de follaje y hasta 12 tris por destino para la red, más margen
de curvatura por nacimiento. **5590/6380/6696 tris** en fuentes joven-03,
adulto-07/viejo-02 respectivamente. Son cotas de coste, no árboles completos
implementados/verificados ni una certificación de todos los rangos admitidos.
El límite de una futura integración sigue siendo **6999 tris y dos materiales**.

**229 pruebas correctas**, dos de ellas nuevas de R1; validan destinos congelados,
determinismo frente al orden de entrada, jerarquía, radios, límites e inválidos.
**25 comprobaciones de muestra correctas**: exportación, contactos de terminales,
normales, pinturas, proyecciones, máscaras no vacías/idénticas y cinco repeticiones
GLB idénticas desde el trabajo congelado. Error máximo de posición de terminales
tras exportación: **0,122 µm**. Cinco GLB reimportados/auditados y **48 capturas
Godot reales**, todas inspeccionadas en láminas. Se revisaron seis orientaciones,
con/sin follaje y máscaras, con luz/cámaras comunes. Texturas originales embebidas,
RGBA y normales/UV finitas, sin triángulos degenerados ni transformaciones ocultas.

En la selección final se ve una transición más distribuida entre eje, ramas
intermedias y ramillas; los abanicos de conectores independientes se sustituyen
por bifurcaciones pequeñas. Persisten puntas muy finas, cruces en proyección y
ángulos facetados. Con hojas, la silueta y plenitud de la muestra anterior se
mantienen. **La valoración de naturalidad corresponde al usuario**; no se declara
aprobación artística por la prueba de máscaras o por cumplir presupuesto.

## Reproducción

Requiere Blender/Godot fijados y las entradas F5 de `artifacts/f5/ensayo-01/`.
En una copia sin esos resultados, regenerarlos primero con
`python3 scripts/verify_branch_space.py --stage generate --output artifacts/f5/ensayo-01`.
Desde la raíz, usando un directorio nuevo para la muestra:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
python3 scripts/verify_branch_sample.py --stage generate --output artifacts/f5/otra-rama-r1
python3 scripts/verify_branch_sample.py --stage review --output artifacts/f5/otra-rama-r1
```

La generación congela `frozen-branch.json`, `network.json`, la referencia por nodos,
transformación de presentación e `input.json` con todas las piezas. Los scripts
usan directorios nuevos, timeout de 120 s al generar y 180 s al revisar, con
terminación del grupo de procesos. Para repetir solamente los GLB, copiar
`input.json` a una carpeta nueva, cambiar únicamente `output` y ejecutar
`blender/branch_sample.py` con Blender sobre ese trabajo; contrastar los hashes
contra `exports.json`. El algoritmo puro permite además regenerar la red desde
los destinos/eje congelados sin Blender, pero las capturas requieren escritorio.

La evidencia se selecciona con `scripts/branch_sample_evidence.py`, tras guardar
la repetición en `repeat/` y la suite en `logs/tests.log`. Las fuentes/hashes y
las semillas están conservadas en la auditoría; no hay inferencia nueva al repetir.
Las capturas y `.blend`/GLB editables permanecen en el resultado local, sin
incorporar esos archivos regenerables voluminosos al repositorio.

Intentos previos conservados: R1-01 rechazó identidad binaria de controles por
nombres internos de malla, aunque la geometría de hojas coincidía; se limpian
mallas huérfanas entre variantes. R1-02 pasó técnicamente, pero concentraba destinos
en el extremo y producía ramillas demasiado finas; R1-03 reparte cupos y mejora
el encuadre de nodos mediante transformación rígida explícita. La primera suite
bajo sandbox tuvo 228/229 por bloqueo de socket loopback; fuera pasó 229/229,
incluida la ejecución final. No se cambió el follaje para corregir esos ensayos.

Integración completa, otras semillas/edades, extremos de parámetros, mallas
soldadas, sombras a otras luces/distancias y rendimiento quedan sin verificar.
R1 se entrega para valoración de la rama antes de ampliar el árbol; F6 sigue sin iniciar.
