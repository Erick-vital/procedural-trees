# O5: aprovechar la periferia con la misma geometría

Implementado y verificado el 2026-11-03. Petición: refinar el llenado exterior,
especialmente maduro 3100, mediante reglas generales, sin congestionar el núcleo
ni aumentar triángulos. **Estructura desnuda aceptada como referencia actual por el usuario**;
follaje aún sin integrar. [Decisión](user-acceptance.json).
[Galería O4/O5](../../../../artifacts/oak-growth/o5-validacion-02/index.html).

## Regla general

O4 elegía refuerzo principalmente por separación de nacimientos. O5 examina
cómo un subárbol secundario completo aprovecha espacio exterior libre en 3D.
Conserva todas las ramas y polígonos y ensaya hasta 27 candidatos por secundaria:
desplazar el nacimiento 0/.07/.14 de recorrido de la primaria, girar 0/±.28 rad
y escala uniforme 1/1.12/1.24 dentro del subárbol. Rechaza nacimientos demasiado
próximos a otros. Los hijos mantienen sus relaciones y ángulos dentro del grupo.
Un candidato debe mejorar cobertura espacial; los empates conservan el original.

Las restricciones por subárbol impiden aumentar longitud o nacimientos del
núcleo (<.30H), perder longitud periférica o celdas periféricas ocupadas (≥.50H).
Se conserva altura nominal y se limita alcance horizontal de los ejes al 103 % del máximo
O4. Se protege el subárbol que determina la altura. Tronco/primarias conservan
puntos, radios y metadatos completos O4; secundarios recalculan radios y encaje.
Las decisiones quedan en `structure.json.periphery`: candidato, puntuación,
cupo de búsqueda y cambios aceptados. Sin condiciones por semilla, reintentos
con semillas alternativas ni llamadas a otro modelo.

## Comparación y presupuesto

Once parejas con mismos controles salvo versión: maduros y centenarios 3100–3104
y joven 3100. Cámaras y luz comunes, cuatro vistas y primarias aisladas; edades
a altura visual normalizada. **Todos tienen exactamente los mismos triángulos
que O4**, incluidos perfiles con cupo denso o frecuencias mínimas de las pruebas.
No se suman ramas ni otro cupo. Reserva futura 1584 y cota completa 6999 intactas.
Un material de corteza, atlas idéntico y follaje aún sin integrar.

| Caso | Tris O4 = O5 | Ejes internos/H, O4→O5 | Ejes periféricos/H, O4→O5 | Celdas periféricas O4→O5 |
|---|---:|---:|---:|---:|
| maduro-3100 | 3714 | 1.83→1.44 | 1.60→5.36 | 31→97 |
| maduro-3101 | 4209 | 2.56→1.41 | 1.85→4.53 | 40→81 |
| maduro-3102 | 3484 | 2.49→1.74 | 0.68→2.31 | 15→57 |
| maduro-3103 | 4122 | 3.34→2.19 | 1.34→4.11 | 27→91 |
| maduro-3104 | 4089 | 1.88→0.82 | 2.03→5.17 | 39→94 |
| centenario-3100 | 4281 | 0.26→0.17 | 10.06→13.26 | 147→217 |
| centenario-3101 | 4867 | 0.85→0.73 | 9.50→13.84 | 131→214 |
| centenario-3102 | 4022 | 0.80→0.58 | 6.55→11.19 | 101→184 |
| centenario-3103 | 4156 | 1.30→0.26 | 9.84→13.53 | 135→218 |
| centenario-3104 | 4389 | 0.46→0.23 | 10.56→14.51 | 139→224 |
| joven-3100 | 2952 | 3.27→3.03 | 0.00→0.00 | 0→0 |

En **maduro 3100**, longitud periférica **1.60H→5.36H**,
celdas **31→97**, longitud interna **1.83H→1.44H**; conserva 3714 tris.
Los diez adultos de la comparación aumentan longitud y celdas periféricas sin
aumentar actividad interna. No se toma el incremento de celdas como volumen
físico de copa: son indicadores de distribución de los ejes secundarios.

## Verificación y generalidad

**275 pruebas y 195 comprobaciones de cierre**, todas correctas.
Los 22 GLB O4 reconstruidos coinciden con los históricos. Los once GLB de
tronco/primarias O5 son idénticos a O4. Estructura y ambos GLB O5 repetidos
por CLI idénticos; uniones reimportadas pasan, centros conectados y radios
suaves. Se ensayan límites de búsqueda, cotas, etapas, ablaciones, entradas
estrictas y presupuesto denso. [Datos/hashes](verification.json), [pruebas](tests.txt).

Controles adicionales **5000–5004** para maduro y centenario: diez comparaciones
geométricas que no se usaron para ajustar reglas. Todos mantienen triángulos,
cota total y protección de núcleo/periferia. Estos controles no tienen nuevas
exportaciones ni capturas Godot; no se presentan como validación visual. No se
certifica naturalidad o mejora universal de cualquier entrada por esta cohorte.

La evaluación conserva los indicadores O4: 16 muestras por segmento para
longitud y celdas de lado .10H, regiones <.30H, .30–.50H y ≥.50H. Se excluyen
tronco y primarias de esos indicadores; su geometría sí se protege y compara.
El algoritmo usa una señal afín para seleccionar espacio: una subida de esa
señal es esperable y debe contrastarse con exportaciones e imágenes.

## Revisión visual y límites

188 capturas Godot, 132 inspeccionadas: once parejas desnudas en cuatro vistas
(88), tronco/primarias de maduro 3100/3103 y centenario 3100/3103 (32), edades
(12). Las otras 56 capturas de primarias están disponibles, sin afirmar revisión.
Las copas conservan las diferencias de etapa y huecos; las secundarias se leen
más desarrolladas y repartidas en el exterior, particularmente en maduro 3100.
La escala de la silueta sigue próxima y la arquitectura principal es idéntica.

Persisten tramos desnudos, superposiciones en proyección y algunas ramas
delgadas largas. No se auditan universalmente colisiones entre ramas ni se
suelda la malla. El método puede conservar el original si ninguna alternativa
cumple restricciones; no garantiza que cada región quede llena. Sin hojas,
no demuestra todavía plenitud de la copa final, reconocimiento botánico o FPS.
La aceptación actual se limita a madera desnuda; no se promueve receta de follaje.

## Reproducción

```sh
python3 scripts/verify_oak_periphery.py --output artifacts/mi-o5
python3 scripts/verify_oak_periphery.py --output artifacts/mi-o5 --stage review
python3 scripts/verify_oak_periphery.py --output artifacts/mi-o5 --stage ages
PYTHONPATH=src python3 -m treegen generate-oak-growth \
  presets/oak-growth/0.5.0/maduro.json --seed 3100 --output artifacts/mi-o5-repeat
PYTHONPATH=src python3 -m unittest discover -s tests > /tmp/mi-o5-tests.txt 2>&1
python3 scripts/close_oak_periphery.py --study artifacts/mi-o5 \
  --repeat artifacts/mi-o5-repeat --tests /tmp/mi-o5-tests.txt
```

`--case maduro-3100` acota generación/capturas por ejemplar. Las capturas de
esta sesión se ejecutaron en tres grupos para acotar la duración del proceso.
El cierre automático deja la inspección pendiente hasta abrir las imágenes.
Blender/Godot y suite con API usan el entorno externo al sandbox documentado.

El ensayo preliminar 01 detectó un metadato de ajuste añadido al tronco al
recalcular radios. Se corrigió restaurando íntegro el registro protegido;
el lote 02 completo verifica identidad de datos y GLB. La prueba fallida y
salidas preliminares se conservaron en /tmp y artifacts; no son el cierre.
O1–O4 y recetas históricas conservadas. Sin integrar follaje ni iniciar F6.
