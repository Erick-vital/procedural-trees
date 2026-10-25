# Primer blueprint experimental de pino

Fecha: 2026-10-24. [Objetivo y alcance autorizado](../../../../plans/blueprint-pino.md).
Receta `pino_conico` 1.0.0, contratos 1.1. **Implementado y verificado
técnicamente; aceptación artística del usuario pendiente.**

## Resultado

Piloto base5100/copa97 y controles base5101/copa98, base5102/copa99 y
base5103/copa100. Parámetros comunes, sin ajustes por semilla. Copa cónica,
eje dominante, ocho pisos de seis ramas, cuatro ramillas por rama y acículas
agrupadas en pares alrededor de los tramos distales. Un único perfil `conico`.

| Medida | Cuatro ejemplares principales |
| --- | --- |
| Altura | 12 m |
| Ramas | 241 tubos: tronco, 48 primarias y 192 ramillas |
| Acículas | 2892 láminas opacas de dos triángulos |
| Triángulos | 11924: 6140 madera y 5784 acículas |
| Materiales | 2: `Pine_Bark` y `Pine_Needles` |
| Generación sin vistas Blender | 1.275–1.372 s, incluido exportar/validar |
| Tamaño GLB | 790012–790784 bytes |

Referencia de organización: [Pinus, Gymnosperm Database](https://www.conifers.org/pi/Pinus.php),
consultada el 2026-10-23. Se toman la copa juvenil cónica, pseudovérticilos
y acículas en fascículos. La receta es una interpretación artística del género,
con acículas exageradas para lectura low-poly; no representa una especie ni
una edad botánica determinada. No se copiaron fotografías a los materiales.

## Arquitectura y comprobaciones

- `src/treegen/pine.py` separa estructura, distribución distal y representación,
  sin `bpy`. Adaptador `blender/generate_pine.py`; mismo ejecutor, CLI, fallos,
  límites, materiales, exportador y protocolo Godot del proyecto.
- Componentes registrados `pine-whorls@0.1.0`, `pine-distal@0.1.0` y
  `pine-needle-pairs@0.1.0`. Contratos nuevos en esquemas `*-pine.schema.json`,
  sin reinterpretar el contrato 1.0 ni TreeSpec. Mezclas incompatibles se rechazan.
- **94 pruebas correctas y 27 comprobaciones de integración correctas**.
  Nueve generaciones: cuatro principales, repetición del piloto, cambio de
  semilla de copa, cambio de tamaño de acícula y dos regresiones históricas.
- Piloto repetido: GLB idéntico byte por byte. SHA256
  `79b26566cb4a4711109f67039662d46e7fa86b2de7617d546f20b1d0c34f7497`.
  Cuatro semillas principales producen cuatro geometrías distintas.
- Los controles de semilla de copa y tamaño conservan geometría, normales y
  material de madera en el GLB y cambian el canal de acículas.
- Siete GLB de pino reimportados en Blender: todos los triángulos de cada
  soporte presentes, 240 inserciones de ramas y 2892 raíces de acículas por caso.
  Las raíces están dentro del padre, comprobadas mediante tres rayos con salida
  orientada sobre sus triángulos reimportados. También se comprueba que cada
  origen declarado corresponde a un vértice de acícula exportado.
- GLB validado independientemente: finitud, índices, áreas, altura/ejes,
  presupuesto, materiales opacos de doble cara y normales unitarias/orientadas.
- **Regresiones exactas**: roble 1.0.0 idéntico a B0 y columnar 1.0.0 idéntico
  a B4. Recetas y algoritmos geométricos históricos conservados.
- Ocho escenas Godot: cuatro copas y cuatro maderas. **72 capturas reales**,
  nueve vistas por escena, cámaras comunes entre ejemplares y luz RF3/B2:
  rotación [-35,-25,0], energía 1.2 y ambiente .5. Sin compensación por semilla.

## Revisión visual y límites

Revisadas las láminas de cuatro copas en frente, perfil, perspectiva y superior;
las cuatro maderas en tres vistas; las distancias al 50/25/10 % de altura de
cuadro; y el piloto en seis vistas, incluidas inferior y reverso.

La revisión del agente observa una silueta cónica y follaje con volumen en las
cuatro semillas. Persisten pisos bastante regulares, huecos entre niveles y
acículas grandes y angulosas. La punta conserva un tramo de eje visible. El
intento inicial local tenía follaje plano y ralo y se revisó durante el desarrollo;
esta evidencia corresponde a la receta final radial. No es una medición de
mejora IA ni una aceptación artística del usuario.

Los rangos son límites de entrada, no combinaciones visualmente garantizadas.
Solo se verifican las cuatro semillas de 12 m y los controles documentados.
Las ramas se insertan geométricamente sin soldar tubos; no se resuelven todas
las intersecciones. Sin viento, LOD, bosque ni medición FPS. No se han creado
perfiles joven/adulto/viejo ni se han cambiado los predeterminados.

## Reproducir y revisar

Desde la raíz, usando directorios nuevos y el entorno fijado en README:

```sh
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/pino_conico/1.0.0.json --instance presets/blueprints/pino/pilot.json --output artifacts/blueprints/mi-pino --no-render
PYTHONPATH=src python3 -m treegen validate artifacts/blueprints/mi-pino
python3 scripts/verify_pine.py --output artifacts/blueprints/otro-pino --visual
python3 scripts/pine_evidence.py --study artifacts/blueprints/otro-pino --output artifacts/blueprints/evidencia-pino
```

La generación individual solo usa fuentes versionadas. La matriz usa las
referencias B0/B4 del repositorio para comprobar conservación; no necesita
resultados regenerables previos. Blender/Godot fuera del sandbox si este
bloquea audio o sesión gráfica. Generación ≤120 s y verificaciones ≤180 s
por subproceso terminable.

Ejecución local seleccionada: `artifacts/blueprints/pine-attempt-02/index.html`;
modelo `pilot/tree.glb`, editable `pilot/tree.blend` dentro de esa carpeta.
En `verification.json` están hashes de fuentes, receta/matriz resueltas,
métricas, comprobaciones y resultados de contactos; los manifiestos completos
permanecen en la salida regenerable. Evidencia seleccionada:
[piloto](pilot.png), [seis vistas](pilot-views.jpg), [cuatro semillas](controls.jpg),
[madera](wood.jpg), [distancias](distances.jpg), [pruebas](unit-tests.txt).
