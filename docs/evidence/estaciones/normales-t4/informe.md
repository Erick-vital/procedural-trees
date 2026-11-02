# T4 — Ensayo de normales locales de copa

Fecha: 2026-11-02. **T4 implementada y verificada técnicamente**. Se registra
por separado la [aprobación artística de T3](../mezcla-t3/user-acceptance.json).
Las normales T4 **no están adoptadas**: originales vigentes, candidatas .35/.65
listas para valoración. [Decisión actual](decision.json),
[plan](../../../../plans/transiciones-estacionales.md),
[contrato y algoritmo](../../../contrato-normales-copa.md).

## Resultado

[Comparación de rama/piloto, verano/otoño](comparison.jpg), [visor](viewer.png).
Galería y proyecto completos: `artifacts/estaciones/normales-t4-06/`,
`index.html` y `godot/project.godot`.

Piloto 3009/17/2718 y vecindad T1/semilla 1101. Rama primaria 100 con 32 grupos;
ambas muestras usan el mismo contexto local de **264 grupos**, sin reajuste por
muestra o semilla. Algoritmo `canopy-local-normals-0.1.0` con campos elipsoidales
locales de centros/ejes/tamaños y hasta 24 vecinos ya existentes.

Se comparan originales y dos intensidades angulares **.35/.65**, con desviación
máxima **21°/39°** respecto a cada normal original. La covarianza regularizada
conserva anisotropía/localidad; no se sustituye la copa por una esfera única.
Hemisferio original, normales unitarias y caso de centro degenerado explícitos.
El reverso lo resuelve el material estándar doble cara del motor.

| Muestra | Grupos/láminas | Triángulos | Materiales | Normales de vértice de follaje |
| --- | ---: | ---: | ---: | ---: |
| Rama | 32/96 | 696 | 2 | 386 |
| Piloto | 264/792 | 6812 | 2 | 3188 |

Las tres variantes tienen exactamente la misma topología. Cambian únicamente
las normales de follaje; no se doblan/subdividen láminas ni se toca la madera.
Posiciones, UV0, UV2/calendario, índices, imágenes, materiales, escena y longitud
GLB se conservan **byte a byte**. Cero vértices/características geométricas ni bytes
añadidos. `s=0` reproduce literalmente las referencias de rama T2 y piloto T3.
[Manifiesto, hashes y auditorías](manifest.json).

## Revisión visual

Las comparaciones usan exclusivamente **StandardMaterial3D** y normales leídas
del GLB. Verano fijo y después otoño fijo; calendario sin animar. Mismos ajustes
para todas las normales: recorte .5, doble cara, rugosidad .95, mipmaps y filtro
anisotrópico, exposición 1 y tonemapping lineal.

Se inspeccionaron **12 láminas de orientaciones** (seis por muestra/pintura/luz),
**12 de distancias**, cuatro de sombras y el visor. Selección conservada:

- Verano: [rama, luz de referencia](branch-summer-light-0.jpg),
  [rama, luz lateral](branch-summer-light-1.jpg),
  [piloto, referencia](pilot-summer-light-0.jpg),
  [piloto, contraluz](pilot-summer-light-2.jpg).
- Otoño: [rama, contraluz](branch-autumn-light-2.jpg),
  [piloto, luz lateral](pilot-autumn-light-1.jpg).
- Distancias: [rama verano](branch-summer-distances-0.jpg),
  [piloto otoño](pilot-autumn-distances-0.jpg).
- Suelo/sombras: [rama verano](branch-summer-shadows.jpg),
  [rama otoño](branch-autumn-shadows.jpg), [piloto verano](pilot-summer-shadows.jpg),
  [piloto otoño](pilot-autumn-shadows.jpg).

Lectura del agente: el cambio es **leve/moderado**, principalmente en la
repartición de luz dentro de las láminas y sus bordes. .35 conserva más la lectura
original; .65 modifica más luces y reversos. No se detecta pérdida geométrica de
lóbulos ni una inversión general de iluminación en estas vistas, pero siguen
visibles planos, cantos y zonas con iluminación plana. A distancia, la pintura
del atlas sigue dominando; no se afirma que estas normales solucionen la lectura
de copa o sean artísticamente mejores. Se mantienen ambos candidatos para juzgar.

Se revisan sombras propias y sobre suelo con tres luces y normal bias 0/1. El
control sin normal bias muestra bandas/acné en el suelo **también en originales**;
no se presenta como defecto creado por las candidatas ni como configuración de
producción aceptada. Algunas sombras exceden el encuadre lateral. El sesgo 1
reduce ese artefacto, aunque puede desplazar detalles de sombra según las normales.
No se certifica identidad de sombras, ausencia universal de costuras, movimiento,
otras luces o todas las alturas/semillas admitidas por el árbol.

La diferencia media del cuadro cercano frente al original es **.68–.75/255**
para .35 y **1.26–1.44/255** para .65, promediando 18 pares por muestra/pintura.
Estos números describen cambios RGB bajo este protocolo; no prueban volumen,
naturalidad, preferencia estética ni FPS.

## Verificaciones

**191 pruebas Python pasan**, incluidas seis nuevas de campos deterministas,
vecindad/hash, normales unitarias, centros degenerados, hemisferios/reversos,
cotas angulares, parámetros inválidos, exactitud/repetición GLB y rechazo de
corrupción ajena a NORMAL o almacenamiento solapado. Se ejecutan fuera del
sandbox por la prueba de API loopback.

**16 comprobaciones del arnés pasan** y **793 capturas reales** Godot:

- 648: seis orientaciones × tres distancias × tres luces × dos pinturas ×
  rama/piloto × tres variantes de normales.
- 72: tres luces × normal bias 0/1 × dos pinturas × dos muestras × tres variantes.
- 72: seis máscaras sin luz × dos pinturas × dos muestras × tres variantes.
- Una captura del visor, con controles de normal/pintura/muestra/luz/suelo probados.

Las **48 parejas de máscaras** original/candidata son píxel a píxel idénticas:
seis vistas × dos pinturas × dos muestras × dos candidatas. Mismo recorte/silueta
proyectada en ese ensayo; geometría exacta acreditada también por auditoría binaria.

Preparación repetida en carpeta temporal: archivos/manifiesto idénticos;
repetición con binding reordenado y GLB exactos. **Seis importaciones Blender**
y seis reexportaciones estándar verificadas; **12 importaciones directas Godot**
y seis tras Blender, con todos los grupos completos. Se asocia por geometría/UV0
antes de comparar normales, sin confiar en el orden de vértices del importador.

La lectura de esquina de Blender difiere hasta **.46872°** del float fuente
(cota de auditoría .6°, componente .01); no se declara vuelta exacta. La API de
[Mesh y normales de esquina](https://docs.blender.org/api/current/bpy.types.Mesh.html)
distingue estas normales de las normales geométricas de cara. En Godot, diferencia
vectorial máxima **.0002503** directa y **.0081848** después de Blender, frente
a cotas .003/.012; todas las normales finitas/unitarias. La auditoría binaria del
GLB generado sigue siendo exacta fuera de sus normales de follaje.
[Importación Blender](blender-report.json), [verificación completa](verification.json),
[comprobaciones finales](additional-checks.json).

Condiciones: Blender 5.2.1 LTS y Godot 4.7.2, Compatibility/OpenGL, RTX 5060;
600²/MSAA4, sol 1.2, ambiente .5, fondo `#EEE9DF`. Luces −35/−25°, −35/−90° y
−35/155°; escalas ortográficas 1.15/2.8/6 veces la envolvente, tomas de suelo 1.75.
Cámaras frente/lateral/perspectiva/dorso/arriba/abajo. Visor 1000×900; atlas T2 y
corteza histórica conservados. No se hizo benchmark ni comparación de mezcla
animada con las nuevas normales.

## Reproducción y continuación

```sh
python3 scripts/verify_canopy_normals.py --output artifacts/estaciones/otra-t4
python3 scripts/canopy_normals_evidence.py --output artifacts/estaciones/otra-t4
env PYTHONPATH=src python3 -m unittest discover -s tests
/home/tao/repos/godot/openworld-forever/.tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64 --path artifacts/estaciones/otra-t4/godot --audio-driver Dummy
```

Cada salida exige carpeta nueva. También se puede separar `--stage build` y
`--stage review`; rutas y requisitos en el [contrato](../../../contrato-normales-copa.md).
Cada subproceso tiene límite de 180 s y puede terminarse. La salida conserva
12 GLB estáticos, seis pruebas reexportadas, campos, normales esperadas, datos,
proyecto, reportes, 793 PNG y láminas. La evidencia versionada selecciona vistas;
no incorpora todos los GLB/capturas regenerables.

Los ensayos 01–03 detuvieron la auditoría Blender por cotas iniciales demasiado
estrictas. Un diagnóstico completo midió la desviación y se fijó una cota angular
explícita, sin editar las normales para ocultarla. 04–05 usaron un nombre inválido
del parámetro de sesgo de sombras; se descartaron/detuvieron y se corrigió a
`shadow_normal_bias`. **06 es la ejecución final válida**; los fallos no cuentan
como verificaciones exitosas.

**Pendiente: elegir originales, .35 o .65 artísticamente**. T5 podrá continuar con
originales si se rechaza este ensayo. No se adelanta la integración de cuatro
casos ni se modifica la transición T3 aprobada.
