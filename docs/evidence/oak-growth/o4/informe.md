# O4: desarrollar la periferia y aliviar el núcleo

Implementado y verificado el 2026-11-03. O3 recibió una valoración positiva
pero con cambios pendientes; **no se interpreta como aprobación final**.
[Revisión recibida](feedback-o3.json). O4 sigue pendiente de valoración artística.
[Galería O3/O4](../../../../artifacts/oak-growth/o4-validacion-01/index.html).

## Cambio de reglas

La base O2 conserva cantidades y resoluciones. Las laterales nacen más
repartidas sobre sus padres; los planos y recorridos penalizan volver hacia
el núcleo. Las curvas evitan concentrar giros al comienzo y desarrollan más
la trayectoria después del nacimiento. El cupo antes dedicado a once abanicos
finos se redistribuye: seis unidades secundaria/terciaria/terminal de 100 tris
sobre primarias con separación disponible y una unidad terciaria/terminales
de 60 en una secundaria exterior. Se buscan huecos locales; no se rellena toda
la copa ni se impone igualdad entre sectores.

Cada brazo hereda un hábito determinista: lateral, pesado, ascendente o sinuoso;
los hijos conservan esa respuesta con variación menor por eje. La intensidad
se mezcla por madurez, sin un tropismo ascendente uniforme. En centenarios
la extensión tiene asimetría regional adicional. Son reglas gráficas, no
simulación física del peso, iluminación o calibración botánica.

## Presupuesto y validación

**No se suma otro cupo sobre O3:** los diez maduros/centenarios mantienen sus
mismos triángulos, +660 frente a O2. Joven 3100 usa 40 menos que O3 (+620 frente
a O2). El máximo sigue siendo +700 frente a O2 y madera 5415 + reserva 1584 =6999.
El refuerzo se reduce con entradas densas; las unidades son indivisibles.
Los controles de frecuencia por orden gobiernan la base; el refuerzo tiene
cupo global. Un material de corteza y atlas compartido, sin follaje integrado.

| Caso | O3 | O4 | Longitud interna/H, O3→O4 | Longitud periférica/H, O3→O4 |
|---|---:|---:|---:|---:|
| maduro-3100 | 3714 | 3714 | 2.39→1.83 | 1.87→1.60 |
| maduro-3101 | 4209 | 4209 | 4.16→2.56 | 1.74→1.85 |
| maduro-3102 | 3484 | 3484 | 4.01→2.49 | 0.62→0.68 |
| maduro-3103 | 4122 | 4122 | 5.69→3.34 | 0.83→1.34 |
| maduro-3104 | 4089 | 4089 | 3.78→1.88 | 1.50→2.03 |
| centenario-3100 | 4281 | 4281 | 2.08→0.26 | 6.99→10.06 |
| centenario-3101 | 4867 | 4867 | 3.88→0.85 | 6.25→9.50 |
| centenario-3102 | 4022 | 4022 | 1.70→0.80 | 5.90→6.55 |
| centenario-3103 | 4156 | 4156 | 1.45→1.30 | 7.48→9.84 |
| centenario-3104 | 4389 | 4389 | 2.94→0.46 | 5.32→10.56 |
| joven-3100 | 2992 | 2952 | 3.30→3.27 | 0.00→0.00 |

**269 pruebas y 154 comprobaciones de cierre**, todas correctas.
Once parejas O3/O4, cinco maduros y cinco centenarios 3100–3104 más joven 3100,
mismos parámetros salvo versión. Las 22 exportaciones O3 coinciden exactamente
con sus hashes históricos. Estructura y dos GLB O4 repetidos por CLI idénticos.
Todos los nacimientos y anillos iniciales pasan la auditoría; son piezas
solapadas, no malla soldada. Texturas idénticas a O3, primarias aisladas como
subconjunto exacto de la malla completa. Mayor caso 4867, con reserva 6451.
Generación O4 1.374–1.693 s. [Datos/hashes](verification.json), [pruebas](tests.txt).

## Qué miden los indicadores

Para órdenes ≥2, integrar longitud de ejes por segmentos con 16 muestras:
núcleo con radio horizontal <.30H, franja media .30–.50H, periferia ≥.50H.
Contar nacimientos y celdas de lado .10H por región. No medir follaje, área
ocupada real, intersecciones de ramas gruesas ni volumen físico de la copa.
La métrica central excluye tronco y primarias; revisar estos en las imágenes.
No deducir naturalidad, reconocimiento de especie o FPS a partir de ellas.

En las diez parejas adultas la longitud interna cae 10.4–87.4 %;
los nacimientos internos también bajan en las diez y los de secundarias se
desplazan hacia afuera. Longitud y celdas periféricas aumentan en 9/10.
La longitud periférica cambia -14.6–+98.4 % según caso.
**Maduro 3100 es la excepción:** la longitud periférica baja de 1.87H a 1.60H
y las celdas de 39 a 31; despeja el centro, pero no acredita mejor llenado exterior.
No se retocó esa semilla individualmente.

## Revisión visual

Godot: 188 capturas, cámaras/luz comunes O3/O4, escala 1 por pareja y edades
a altura normalizada. Se inspeccionaron 132: once árboles en cuatro vistas
(88), primarias aisladas de maduro 3100/3103 y centenario 3100/3103 (32), edades
(12). Otras 56 capturas de primarias quedan disponibles sin afirmar inspección.

Las secundarias intermedias se leen mejor sobre los brazos y varias regiones
exteriores tienen más ramificación útil. El centro queda menos enredado y
se conserva variedad de trayectorias y vacíos. Los centenarios distribuyen
su estructura a mayor distancia del tronco, con sectores extendidos y otros
menos desarrollados; las etapas conservan siluetas distintas.

**Límites visibles:** sigue siendo madera desnuda y algunas zonas continúan
esqueléticas. Persisten uniones por solapamiento, cruces en proyección, largos
segmentos expuestos y transiciones grueso-fino. Algunas trayectorias superiores
siguen ascendiendo; ya no tienen respuesta uniforme. El centenario no queda
certificado como convincente por estas métricas. No se declara resuelta la
densidad de toda la copa ni aceptado el arte; se presenta para valorar.

## Reproducción

```sh
python3 scripts/verify_oak_volume.py --output artifacts/mi-o4
python3 scripts/verify_oak_volume.py --output artifacts/mi-o4 --stage review
python3 scripts/verify_oak_volume.py --output artifacts/mi-o4 --stage ages
PYTHONPATH=src python3 -m treegen generate-oak-growth \
  presets/oak-growth/0.4.0/maduro.json --seed 3100 --output artifacts/mi-o4-repeat
PYTHONPATH=src python3 -m unittest discover -s tests > /tmp/mi-o4-tests.txt 2>&1
python3 scripts/close_oak_volume.py --study artifacts/mi-o4 \
  --repeat artifacts/mi-o4-repeat --tests /tmp/mi-o4-tests.txt
```

La revisión automática deja inspección visual pendiente hasta abrir imágenes.
Blender/Godot y prueba API se ejecutaron fuera del sandbox, según el entorno
documentado. El proceso de capturas se interrumpió después de guardar las 16
imágenes y cuatro informes correctos de centenario 3103; se reconstruyeron sus
láminas con esos archivos y se completaron los otros casos por separado.
Sin fallos nuevos de generación en este lote. O1/O2/O3 y recetas
históricas conservadas. Sin integrar follaje ni iniciar F6, LOD o viento.
