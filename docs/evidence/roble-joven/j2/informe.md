# J2 — joven completo, piloto y tres controles

Fecha: 2026-11-04. El usuario aprobó madera y rama J1 con «si» y autorizó
continuar: [aceptación y hashes](../j1/user-acceptance.json).
**Cuatro árboles completos integrados y verificados técnicamente**.
El usuario solicitó más cobertura y volumen: [revisión](user-review.json).
La corrección posterior está en [J3](../j3/informe.md); J2 se conserva como
referencia técnicamente válida con cambios artísticos solicitados. No se hicieron pruebas de rendimiento.

## Entrega y entradas

Nueva receta `roble_copa_ancha@3.1.0`, contrato1.8, **perfil joven fijo de5 m**.
Maduros3.0.0 y recetas históricas conservados;3.1.0 no es una receta de maduros.
Madera O5 joven aprobada,144 grupos/432 láminas cruzadas/864 tris de follaje,
distribución17, pintura2718, mismos atlas/corteza y dos materiales.

Petición F4 versionada `configs/language/roble-joven-j2-v1.json`. Interpretación
hecha por Codex en este chat, sin otro modelo; `plan-blueprints` validó los cuatro
ejemplares antes de Blender, congeló receta/petición/resoluciones/hashes y
`generate-blueprint-plan` generó y repitió el mismo lote. No hubo retoques por
semilla ni selección de controles después de ver sus resultados.

| Semilla | Madera tris | Follaje tris | Total | Materiales | Grupos |
|---|---:|---:|---:|---:|---:|
| 3100 | 2952 | 864 | **3816** | 2 | 144 |
| 3101 | 3233 | 864 | **4097** | 2 | 144 |
| 3102 | 2672 | 864 | **3536** | 2 | 144 |
| 3103 | 3258 | 864 | **4122** | 2 | 144 |

Presupuesto de diseño: madera≤5415 +864 =6279, bajo6999. Las cotas, candidatos
máximos y entradas fijas se validan antes de mallar; semillas sin capacidad o
colocaciones válidas se rechazan. Cuatro casos no certifican todas las semillas.
Se mantienen perfiles y contratos históricos, sin selección implícita de versión.

## Reparto por capacidad y fallos conservados

El preflight con las cadenas B originales detectó que p:4 de3102 recibía dos
grupos por peso de ejes, pero no tenía segmentos válidos después de los filtros
radial/altura. Rechazo conservado en `artifacts/roble-joven/j2-preflight-01/` y
`preflight-rejected.json`. La muestra p:0 no podía detectar esa limitación.

J2 introduce un compositor joven separado que usa las mismas reglas de
candidatos/cadenas B y cuenta la capacidad real:32 estaciones por eje y hasta12
grupos por eje. Limita los cupos iniciales y redistribuye excedentes entre ramas
con peso y capacidad disponible. Rechaza si no hay capacidad global o no puede
componer una masa válida; no añade madera ni relaja los contactos para completar.
Las cadenas históricas y J1 se conservan sin modificaciones.

En3102 se reasignan exactamente dos grupos desde p:4 a ramas con capacidad.
Los demás casos no requieren reasignación. p:0 del piloto mantiene sus71 grupos
**exactamente**, incluida posición, tamaño, plantilla y orientación. La elección
se basa en candidatos, no en una condición por semilla. Los libros de reparto
inicial/final y capacidades están en cada `prepared-canopy.json`; el resumen
conserva los cupos finales. Una primaria con cupo0 queda desnuda y se registra.

Una prueba inicial de identidad comparó tuplas Python con listas del JSON
guardado: falló aunque los valores coincidían. Se corrigió para comparar el
hash canónico de los grupos aprobados, conservando la exigencia de identidad.
El fallo está en `test-serialization-failure.json`. La prueba corregida y sus
comprobaciones geométricas pasan; no se descartó un árbol ni se sustituyó una
semilla para hacer pasar el lote.

## Auditoría, repetición y regresiones

- Cuatro GLB completos repetidos byte por byte idénticos y cuatro firmas
  geométricas diferentes. El piloto generado por la CLI individual y por F4 es
  idéntico: `39748089ade57d937f684dbc6e6de569310e2e6b7521709aec0e3cdb3756e1b3`.
- Madera de los cuatro árboles idéntica a los GLB desnudos aprobados en J1,
  incluyendo posiciones, normales y UV float32. Madera y follaje de la rama
  piloto aprobada son subconjuntos exactos de los atributos del GLB completo.
- Caras/UV reales de madera y follaje contrastadas con la geometría preparada;
  triángulos no degenerados, altura, orientación, recursos embebidos, doble cara,
  rugosidad.95 y recorte alfa.5 auditados. Anillos de nacimiento embebidos en los
  padres, con uniones por solapamiento, sin prometer una malla soldada.
- Contactos de los144 grupos por caso sobre triángulos/UV del GLB y alfa opaca
  pasan. Máximo error del lote **0.000234 mm**, tolerancia.01 mm. No certifica
  cada conexión de cada hoja dibujada dentro de la pintura.
- Madura3.0.0 regenerada con el ejecutor actualizado: GLB idéntico al OF11
  aprobado. O5 y las recetas/PNG existentes no se modifican.
- **30 condiciones de cierre correctas**, además de diez comprobaciones de
  exportación por caso. Entradas, fuentes, recursos, repetición, madera y muestra
  contrastados. **Suite completa:360 pruebas en76 archivos correctas**, detalle por archivo
  en `tests.json`.

Preparación algorítmica en Python anfitrión, exportador Blender separado y
verificador independiente del GLB. Blender5.2.1 LTS y Godot4.7.2 de este entorno;
versiones/hashes completos en los manifiestos y protocolos. Generación y
subprocesos acotados a120/180 s. Los tiempos de generación no se interpretan
como rendimiento gráfico y no se abren nuevos benchmarks.

## Revisión visual Godot

**92 capturas reales,23 por árbol**,900×900,MSAA4,Compatibility/RTX5060,
materiales/filtrado/sombras explícitos. Se inspeccionaron las92 como miniaturas
mediante cuatro láminas, además de los cuatro frentes originales900×900.

Cámaras comunes en metros para todo el lote: seis orientaciones ortográficas,
tres perspectivas provisionales FOV50° a11.428/19.428/38.856 m del centro común,
fondo oscuro, luz alternativa, sombra, ocho azimuts y tres vistas de madera
sola. Distancias provisionales; no son la cámara definitiva del juego ni un
benchmark. Protocolo congelado antes de capturar en `review-protocol.json`.

Hallazgos que deben juzgarse artísticamente:

- Porte esbelto y asimetrías visibles entre los cuatro individuos. La pintura
  y la rama J1 se conservan y no aparecen grandes rectángulos alfa evidentes.
- **La copa completa resulta muy abierta**, con grupos pequeños separados y
  bastante madera visible. Algunos ápices permanecen desnudos, especialmente
 3101; las ramas sin cupo no reciben relleno artificial. No se declara plenitud
  visual suficiente ni aspecto definitivo de roble joven por pasar las métricas.
- Desde arriba persiste lectura radial y se ven láminas de canto. La sensación
  de volumen cambia con el giro; de lejos se pierde detalle y parte del follaje
  resulta difícil de leer. No se midió movimiento o parpadeo subpíxel.
- Hay sombras de madera y follaje, pero sus extremos quedan fuera de cuadro en
  algunas tomas. No se certifica la proyección completa de sombras ni todas
  las conexiones aparentes desde cualquier punto de vista.

[Comparación de copa](overview.jpg), [distancias](distance.jpg), [madera](wood.jpg).
Galería y PNG originales: `artifacts/roble-joven/j2-completo-01/index.html`.
Los cuatro GLB y sus fuentes Blender están en `trees/joven-3100` a `joven-3103`.

**Revisión recibida: aumentar follaje en ramas y volumen.** La iteración
[J3](../j3/informe.md) implementa esa corrección. La receta queda marcada experimental; aún no
se promociona como resultado artístico aprobado. Cualquier corrección posterior
se hará con reglas comunes y manteniendo reproducibles la muestra y esta entrega.

## Reproducción

Usar carpeta nueva y entorno con Blender/Godot permitidos fuera del sandbox:

```sh
PYTHONPATH=src python3 -m treegen plan-blueprints blueprints/roble_copa_ancha/3.1.0.json --request configs/language/roble-joven-j2-v1.json --output artifacts/roble-joven/mi-j2/plan
PYTHONPATH=src python3 -m treegen generate-blueprint-plan artifacts/roble-joven/mi-j2/plan --output artifacts/roble-joven/mi-j2/trees
PYTHONPATH=src python3 -m treegen generate-blueprint-plan artifacts/roble-joven/mi-j2/plan --output artifacts/roble-joven/mi-j2/repeat
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/roble_copa_ancha/3.1.0.json --instance presets/blueprints/roble-joven/joven-3100.json --output artifacts/roble-joven/mi-j2-piloto --no-render
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/roble_copa_ancha/3.0.0.json --instance presets/blueprints/roble-central/maduro-3100.json --output artifacts/roble-joven/mi-j2/mature-regression --no-render
python3 scripts/verify_oak_young_canopy.py --output artifacts/roble-joven/mi-j2 --stage review
python3 scripts/run_tests_bounded.py --output artifacts/roble-joven/mi-j2/tests
```

El cierre `--stage audit` usa además los testigos aprobados J1 (ver reproducción
J1), y el testigo CLI individual del estudio seleccionado
`artifacts/roble-joven/j2-piloto-01/`. Estos son comparaciones de evidencia, no
entradas de generación de la receta; la CLI genera desde sus fuentes sin ellos.
Para reproducir el cierre exacto, conservar/recrear esas rutas con sus comandos
J1/CLI y ejecutar:

```sh
python3 scripts/verify_oak_young_canopy.py --output artifacts/roble-joven/mi-j2 --stage audit
```

Las muestras por caso,logs,GLB/blend y PNG completos permanecen regenerables en
`artifacts/`. Git conserva solo evidencia seleccionada y fuentes.
