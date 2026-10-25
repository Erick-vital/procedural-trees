# Pino 1.1.0: revisión de estructura

Fecha: 2026-10-24. [Plan y autorización](../../../../plans/blueprint-pino.md).
**Implementado y verificado; aceptación artística de la revisión pendiente.**

El usuario prefiere las vistas del primer pino con ramas a distintas alturas y
mayor sensación de ramificación. Autoriza desfasar las inserciones, variar
inclinación/longitud y reducir simetría lateral, conservando la silueta cónica.
Esta preferencia no se registra como aceptación del conjunto de la receta.

## Cambio controlado

Receta nueva `pino_conico` **1.1.0**, estructura `pine-whorls@0.2.0` en
`src/treegen/pine_structure_v2.py`. La receta 1.0.0 y la ruta geométrica 0.1.0
se conservan. Mismos parámetros, paleta, representación y semilla de copa.
Los cuatro pares de semillas siguen siendo 5100/97, 5101/98, 5102/99 y 5103/100;
sin cambios individuales.

- Salidas de ramas desfasadas dentro de cada pseudovérticilo y entre niveles.
  La envolvente usa la altura efectiva de inserción.
- Inclinaciones, longitudes y curvatura lateral variables; algunas primarias
  descienden ligeramente y otras ascienden.
- Ramillas con posiciones, longitudes, direcciones y elevaciones distintas;
  orden de lados variable en cada primaria.
- Tronco conservado exactamente en el algoritmo. Cantidades y topología de
  tubos conservadas: 241 ramas, 2892 acículas, **11924 triángulos/2 materiales**,
  altura de 12 m. El tamaño y la orientación radial de las acículas mantienen
  la estrategia anterior; sus coordenadas acompañan la nueva madera.

## Verificación

**97 pruebas y 51 comprobaciones de integración correctas.**
Trece generaciones: cuatro nuevas, cuatro anteriores regeneradas, repetición
del piloto nuevo, dos controles exclusivos de follaje, roble B0 y columnar B4.

- Los cuatro GLB anteriores son idénticos byte por byte a la evidencia 1.0.0.
  Roble B0 y columnar B4 también conservados exactamente.
- Piloto nuevo repetido idéntico: SHA256
  `b4fa2aa8c4a4c806995281228ef5238aed7cef4d80cf4b887605904d36923601`.
- Mismos parámetros, semillas y cantidades en las parejas antes/después.
  Semilla de copa y tamaño de acícula conservan el canal de madera exportado.
- Once GLB de pino reimportados para comprobar todos los triángulos de los
  soportes, 240 inserciones y 2892 raíces de acículas por caso. Contactos válidos;
  GLB independiente sin áreas degeneradas ni errores de escala, ejes o normales.
- Cuatro nuevos: generación 1.222–1.324 s, GLB 795680–797384 bytes.
  No se infiere rendimiento FPS de estos valores.
- **16 escenas Godot y 144 capturas reales**, nueve por escena: cuatro nuevos,
  cuatro anteriores y sus respectivas maderas. Mismo encuadre físico derivado
  del piloto anterior, luz RF3/B2 y cámaras comunes a todas las parejas.

Diagnósticos de geometría, sin atribuirles naturalidad por sí solos:

| Caso | Desfase entre raíces del mismo nivel, m | Primarias descendentes / 48 |
| --- | --- | --- |
| Piloto | .867–.932 | 7 |
| Control 01 | .868–.913 | 13 |
| Control 02 | .819–.905 | 9 |
| Control 03 | .822–.941 | 10 |

En 1.0.0 los intervalos por nivel estaban entre .047 y .173 m en estos casos;
la comparación usa las mismas entradas. Las pendientes nuevas van de −.091
a .412 (razón ascenso/desplazamiento horizontal). Son comprobaciones del
cambio solicitado, no una medida de realismo ni una mejora atribuida a IA.

## Revisión visual

Revisadas las cuatro copas en frente, perfil, perspectiva y superior; las
comparaciones antes/después de copa y madera en frente/perfil/perspectiva;
las tres distancias y el piloto en seis vistas, incluidas inferior y reverso.
La revisión del agente observa menos alineación horizontal desde frente y
perfil y huecos de tamaños distintos. Se conserva la lectura cónica y del
tronco dominante. Algunas ramas inferiores sobresalen de forma desigual.

Las acículas siguen siendo grandes y angulosas; se conserva el aspecto de
estrella de algunos grupos. Su refinado se dejó expresamente para después de
evaluar esta estructura. Aún hay agrupación por niveles, tubos sin soldar y
solapamientos. Solo se ensayan cuatro semillas de 12 m y dos controles de
follaje; los rangos completos y otras edades no están garantizados.
Sin viento, LOD, bosque ni pruebas FPS.

## Revisar y reproducir

Galería local: `artifacts/blueprints/pine-v1.1-review-01/index.html`.
`pilot`, `control-01`, `control-02` y `control-03` son **1.1.0 a revisar**;
`before-` identifica **1.0.0 anterior**, y `-wood` la madera sin follaje.
Los números 01–03 son semillas de control, no versiones sucesivas.

Evidencia seleccionada: [piloto](pilot.png), [comparación de copas](comparison.jpg),
[comparación de madera](comparison-wood.jpg), [cuatro nuevos](controls.jpg),
[seis vistas](pilot-views.jpg), [distancias](distances.jpg),
[métricas y procedencia](verification.json), [pruebas](unit-tests.txt).

```sh
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/pino_conico/1.1.0.json --instance presets/blueprints/pino-v2/pilot.json --output artifacts/blueprints/mi-pino-revisado --no-render
PYTHONPATH=src python3 -m treegen validate artifacts/blueprints/mi-pino-revisado
python3 scripts/verify_pine.py --matrix configs/verification/pine-v2.json --output artifacts/blueprints/otra-revision-pino --visual
python3 scripts/pine_evidence.py --study artifacts/blueprints/otra-revision-pino --output artifacts/blueprints/evidencia-revision-pino
```

Usar carpetas nuevas y el entorno fijado del proyecto. Generación ≤120 s y
verificaciones/capturas ≤180 s por subproceso terminable. La comparación
regenera las versiones anteriores desde fuentes y usa la evidencia conservada
para contrastar hashes; no depende de resultados regenerables anteriores.
