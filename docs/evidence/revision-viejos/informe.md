# Diagnóstico de ramificación: viejos 00, 03 y 09

Fecha: 2026-10-22. Investigación posterior a F2 a partir de la revisión del usuario. Casos señalados como malos: `viejo-00`, `viejo-03` y `viejo-09` (semillas 3000, 3003 y 3009). El usuario describe muchos troncos pegados y dirigidos de forma parecida, con poco volumen construido mediante ramificación; considera los viejos la familia más débil. No son ejemplos aprobados estéticamente por haber pasado la validación técnica de F2.

Se inspeccionaron capturas Godot y vistas de ramas sin hojas. Después se midieron los `.blend` originales con `scripts/diagnose_structure.py`, sin regenerar ni modificar los árboles. Se añadieron `adulto-00` y `joven-00` como controles técnicos; el usuario no los ha elegido como ejemplos buenos. No se implementó una corrección ni se declara mejora.

[Casos con y sin follaje](cases.jpg) · [Resumen reproducible](summary.json).

## Hallazgos comprobados

1. **Las primarias repiten una única forma e inclinación.** `blender/oak_nodes.py:150` construye una sola curva y la instancia con giro en Z y escala uniforme. No cambia su inclinación con la altura de nacimiento ni curva las puntas hacia regiones diferentes de copa. En los tres viejos las 11 direcciones base→punta tienen 73.616° respecto de la vertical antes del ajuste final. Cambiar la semilla modifica el reparto horizontal y longitudes, pero mantiene esa inclinación.
2. **La aleatoriedad horizontal puede agrupar ramas y dejar huecos grandes.** Al patrón de giro por índice se le suma un giro independiente de ±180° (`oak_nodes.py:152`), sin separación angular mínima. En los tres casos aparecen direcciones próximas y sectores grandes sin direcciones principales. La tabla mide direcciones, no ocupación real de follaje ni colisiones.
3. **Los grosores no dependen del padre en la unión.** Primarias: radio fijo de `base_radius × 0.42`; secundarias: `base_radius × 0.15`. El padre se estrecha a lo largo de su curva, pero el hijo conserva ese grosor fijo. En cada uno de los tres viejos, 5/11 primarias superan el radio local del tronco y 11/22 secundarias superan el radio local de su primaria. La relación máxima hijo/padre es aproximadamente 1.64 en primarias y 1.30 en secundarias. Son radios nativos usados para mallar, antes del ajuste Z. Esto contribuye al aspecto de tubos o troncos injertados.
4. **El preset viejo acentúa el patrón.** Usa once primarias, radio basal 0.8 m e inclinación nominal de 72° desde la vertical; las ramas principales resultan largas, gruesas y casi horizontales. El adulto comparte las limitaciones, y en el control joven también se detectan hijos más gruesos que el padre local. El defecto no se limita a tres semillas.
5. **El ajuste de altura aplasta más la estructura.** El generador conserva X/Y y reduce Z para incluir el follaje en la altura final (`oak_nodes.py:272`). En estos viejos comprime Z un 17–23 %. Las primarias quedan finalmente a unos 13–14° sobre la horizontal. También se reduce su separación vertical, reforzando los haces de ramas apiladas.
6. **La jerarquía es repetitiva.** Se colocan exactamente dos secundarias por primaria, al 48 % y 78 % de su recorrido, con una plantilla común de longitud, grosor e inclinación relativa. Hay variación de giro; no todas las secundarias son paralelas. Sin embargo, no se adapta la longitud o grosor al nacimiento ni se decide cómo desarrollar distintos sectores y alturas de copa. El follaje se concentra en extremos y hereda esa estructura, favoreciendo acumulaciones periféricas y huecos centrales.

| Caso | Separación horizontal mínima entre primarias | Hueco angular máximo entre direcciones | Inclinación final sobre horizontal | Escala Z final |
| --- | ---: | ---: | ---: | ---: |
| viejo-00 | 0.42° | 93.29° | 12.76° | 0.7702 |
| viejo-03 | 5.23° | 91.96° | 13.74° | 0.8318 |
| viejo-09 | 0.39° | 120.45° | 12.89° | 0.7786 |

La observación «misma dirección» tiene dos componentes medibles: inclinaciones principales idénticas y agrupación de algunos giros horizontales. No significa que las once ramas compartan exactamente el mismo azimut. La falta de volumen convincente es una valoración visual apoyada por esas reglas, no una métrica volumétrica ya implementada.

## Por qué pasó F2

Los controles comprueban exportación, coordenadas, presupuestos, escala, materiales, reproducibilidad y continuidad de uniones. No rechazan la repetición de inclinaciones, una mala jerarquía de grosores, la agrupación angular ni una copa visualmente pobre. Que una rama esté unida al tronco no garantiza que su unión tenga una proporción aceptable. La revisión del usuario añade una evaluación estética más exigente y deja pendiente la calidad de la familia vieja; los éxitos técnicos de F2 se mantienen.

## Correcciones propuestas; todavía no implementadas

- Hacer depender el radio de cada rama del radio real de su padre en el nacimiento, con disminución jerárquica y transición visual coherente.
- Variar inclinación, curvatura y longitud por altura y función de la rama; desarrollar también la parte superior e interior de la copa.
- Conservar una distribución horizontal controlada con perturbaciones acotadas, verificando agrupaciones y huecos sin imponer simetría perfecta.
- Ajustar las secundarias según la primaria, el nacimiento y el espacio que deben ocupar; evitar copiar el mismo patrón mecánicamente.
- Revisar el ajuste de altura para que no deforme de forma accidental el estilo de la ramificación. Separar siempre las métricas nativas de las finales.

Conviene corregir primero la estructura y juzgarla sin follaje. Después se evaluará la copa completa. Más masas de hojas podrían ocultar la causa sin corregirla. Estos refinamientos permanecen dentro del árbol de F1; no requieren bosque/terreno, ni equivalen a implementar la migración Python o demostrar el experimento B de F5.

Antes de una nueva versión se conservarán los assets actuales como referencia; cualquier cambio geométrico exigirá versión nueva. La comparación usará inicialmente estos tres casos y controles de las otras edades, semillas conservadas, cámaras y escala compartidas entre referencia/candidato, más revisión posterior de los treinta casos. Pasar las validaciones técnicas seguirá siendo necesario, además de la revisión visual del usuario. No se fijan umbrales estéticos arbitrarios a partir de estos tres casos.

## Reproducción y límites

Desde la raíz, con los assets F2 ya generados:

```sh
timeout 120s /home/tao/repos/blender/.tools/blender-5.2.1-linux-x64/blender \
  --background --factory-startup --threads 1 --python-exit-code 1 \
  --python scripts/diagnose_structure.py -- \
  --output artifacts/repro-diagnostico-viejos \
  --cases viejo-00 viejo-03 viejo-09 adulto-00 joven-00
```

Usar una carpeta de salida nueva. Entorno: Blender 5.2.1 LTS `9e2066aef7ef`. La ejecución comprobada fue fuera del sandbox; dentro se repitió el bloqueo de audio al cerrar, y ese proceso fue terminado. Diagnóstico completo en `artifacts/diagnosis-viejos-final/diagnosis.json`; el resumen seleccionado conserva semillas, parámetros, hashes de `.blend`, manifiestos y scripts.

El script evalúa Trunk/Primary/Secondary de los grafos guardados, muestrea cada curva en 64 puntos y recupera su atributo de radio. Identifica el padre más próximo al nacimiento y exige error menor de 0.003 m. Comprueba cantidades de curvas y que la caja previa al ajuste Z reproduce la caja final exportada con tolerancia de 0.0001 m. Los hashes originales de GLB y `.blend` se comprobaron intactos después de la inspección. No se añadieron métricas de conflictos, ocupación volumétrica o calidad estética automática; tampoco se renderizó una corrección.
