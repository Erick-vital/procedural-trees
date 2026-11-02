# T3 — Transición pintada del piloto en Godot

Fecha: 2026-11-02. **T3 implementada y verificada técnicamente** por solicitud
del usuario. [Plan](../../../../plans/transiciones-estacionales.md).
Pintura, aplicación y calendario siguen pendientes de aceptación artística.
T4–T6 pendientes; sin nuevas normales, caída ni integración de cuatro árboles.

## Resultado revisable

Piloto viejo-09 **3009/17/2718**, semilla estacional **1101**; roble 2.2.0,
**6812 triángulos, 264 grupos, 792 láminas y dos materiales**. Shader nuevo
`paint_transition.gdshader`, adaptador `paint_transition_tree.gd` y visor
`paint_transition_viewer.gd`. Perfil separado `roble-mezcla-v1.json` 0.1.0:
resuelve atlas T2 por hash, sin cambiar el perfil ni los contratos T0/T1.

[Comparación de cinco fases/modos](comparison.jpg), [visor](viewer.png),
[secuencia con cámara fija](fixed.webp). Galería completa con ambas animaciones:
`artifacts/estaciones/mezcla-t3-04/index.html`.

El visor tiene deslizador de fase, reproducir/pausar, cambio de sentido y órbita;
arrastrar gira, rueda acerca y **R** restablece cámara. Modos: calendario por grupo,
mezcla uniforme, verano fijo, otoño fijo y tinte experimental anterior. Un recorrido
manual puede empezar desde cualquier fase, sin reconstruir la malla. El control
anterior usa una copia del shader con rugosidad .95 y la misma pintura/máscara de
verano T2; su fuente histórica .88 permanece intacta.

## Mezcla y recursos

Los dos atlas T2 comparten alfa exacta y extensión RGB de 16 px por celda. El
material obtiene `(inicio,duración)` de UV2 y calcula `smoothstep` por grupo;
las tres láminas conservan el mismo calendario importado. No usa el tiempo global
ni números aleatorios en el shader. El alfa procede siempre del verano, con
recorte .5, doble cara, filtro anisotrópico y mipmaps activados explícitamente.
Se mantienen los ajustes de importación sin relleno automático ni premultiplicación.

Los RGB se mezclan en **espacio lineal**. Compatibility entrega/recibe color sRGB
para el shader: se decodifica antes de mezclar y se codifica el resultado. En
Forward+/Mobile se deja la conversión de muestras al hint `source_color`; esos
renderizadores no se certifican en este ensayo. En los extremos se devuelve la
muestra original directamente para evitar redondeos de ida/vuelta.
Referencias oficiales: [uniformes y source_color](https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/shading_language.html),
[OUTPUT_IS_SRGB](https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/spatial_shader.html).

Un `ShaderMaterial` y dos texturas compartidos entre los árboles ensayados;
fase/modo son `instance uniform` de cada `GeometryInstance3D`. El adaptador solo
actualiza parámetros al avanzar. El control de tinte anterior usa un material
propio por árbol porque su contrato histórico tiene un uniforme ordinario.
No se crean materiales por grupo, ni texturas/mallas por cuadro. El material del
tronco y sus datos quedan intactos.

El GLB T1 del piloto solo sustituye el PNG de verano por su versión compatible:
auditoría binaria confirma posiciones, normales, UV0/UV2, índices, corteza,
materiales y escena exactos. La extracción glTF y el nuevo material apuntan al
mismo `pilot_foliage.png`, evitando duplicar la textura de verano. En el proyecto
solo se importan tres rutas de textura: verano, otoño y corteza.

Dos atlas RGBA8: **32 000 000 bytes** sin mipmaps y **42 665 712** con cadena
completa. Sumando corteza como RGBA8: **38 290 064 / 51 049 784 bytes**. Son
estimaciones sin compresión, no medición GPU. Follaje: dos muestras por evaluación
del fragmento, incluso en extremos; corteza: su textura habitual. Sombras y
sobrepintado pueden repetir trabajo. Dos materiales no significan dos texturas
ni demuestran una ganancia de FPS; no se hizo benchmark.

## Verificación

- **185 pruebas Python pasan**, incluidas cuatro nuevas de perfil/recursos,
  mezcla lineal, extremos, reversión, acceso directo e invalidación de entradas.
  Se ejecutan fuera del sandbox por el socket loopback de la prueba de API.
- Preparación repetida en carpeta temporal: manifiestos y archivos del paquete
  idénticos; repetición GLB exacta. Recursos y datos T1/T2 congelados por hash.
- Importación Godot: **264 grupos**, cero vértices ambiguos/sin grupo, seis caras
  por grupo; UV2 contrastado con datos por geometría/UV0, sin usar el calendario
  para deducir el grupo. La compresión del importador conserva las cotas T1.
- Dos árboles usan el mismo material. Se cambia la fase de A y se comprueba que
  el render de B no varía. Salto .9→.2 y acceso directo a .2 dan píxeles idénticos.
  Rechazo de fase NaN/fuera de rango y modos inexistentes; extremos fijos no
  cambian al mover la fase.
- Prueba GPU con dos colores conocidos, calendario controlado y otro UV2 leído
  de la malla importada. Seis muestras frente a mezcla CPU sRGB→lineal→sRGB,
  pintada con material estándar sin luz para atravesar la misma salida del motor.
  Error máximo **1/255** por canal frente a ese oráculo. El motor introduce su
  propio redondeo en tonos oscuros: no se compara solo contra el byte sRGB ideal.
- **Ambos extremos coinciden píxel a píxel** con material estándar que usa la
  correspondiente pintura compatible, bajo cámara/luz/filtrado comunes.
- Cinco capturas de máscara en p=0/.25/.5/.75/1 son exactamente idénticas.
- Secuencias **0→1→0 en pasos de 1/120**, 241 cuadros con cámara fija y 241 con
  cámara orbital que recorre/retraza 360°. Los 120 cuadros de vuelta de cada
  secuencia coinciden por hash con sus correspondientes cuadros de ida.
  Malla, material y texturas conservan sus RID al terminar cada secuencia.
- Visor probado en escena independiente: deslizador, avance, pausa, retroceso,
  cinco modos y órbita. Captura con su iluminación real, sin luces del arnés.

En total, **517 capturas reales**: 34 estáticas, 482 cuadros de secuencia y un
visor. Godot **4.7.2**, Compatibility/OpenGL, RTX 5060; 600²/MSAA4 para revisión,
1000×900 para visor, sol 1.2 a −35/−25°, ambiente .5, exposición 1, tonemapping
lineal y fondo `#EEE9DF`. [Verificación completa](verification.json),
[manifiesto](manifest.json), [comprobaciones finales](additional-checks.json).

## Revisión visual y límites

Se inspeccionaron la comparación, el visor y los **121 cuadros de ida de cada
recorrido**, mediante [lámina fija](fixed-timeline.jpg) y
[lámina orbital](orbit-timeline.jpg). La vuelta repite esos mismos píxeles.
Se revisaron a mayor tamaño los vecinos del mayor cambio entre cuadros:
[fija p=.4667/.475/.4833](fixed-largest-change.jpg),
[órbita p=.6917/.7/.7083](orbit-largest-change.jpg).

Con cámara fija, el pigmento cambia progresivamente por grupos; no se detectaron
saltos grandes ni cambio de recorte en esa revisión por cuadros. El periodo más
visible se concentra aproximadamente en p=.3–.7, conforme al calendario T1; no
se retocó por semilla. El máximo cambio medio entre cuadros es **.323/255** sobre
el cuadro completo reducido a 480². En órbita sube a **10.860/255**: cambian
visibilidad de láminas, silueta, iluminación y sombras. Se observan cantos y
cambios de visibilidad propios de las cruzadas al girar. No se certifica ausencia
de centelleo fino en movimiento continuo, otras luces o distancias; las láminas
no se transforman en volúmenes físicos por aplicar esta mezcla.

Las métricas acompañan capturas de una secuencia renderizada; no son por sí
solas aceptación artística ni prueba universal contra parpadeos. Las animaciones
WebP son vistas previas con pérdida, 480²/67 ms por cuadro; los hashes y auditorías
usan PNG originales de 600². Se conserva una animación fija seleccionada en la
evidencia; la órbita completa queda en la salida regenerable.

## Reproducción y continuación

```sh
python3 scripts/verify_paint_transition.py --output artifacts/estaciones/otra-t3
# O separar las etapas (no repetir build sobre una carpeta existente):
python3 scripts/verify_paint_transition.py --output artifacts/estaciones/otra-t3 --stage build
python3 scripts/verify_paint_transition.py --output artifacts/estaciones/otra-t3 --stage review
python3 scripts/paint_transition_evidence.py --output artifacts/estaciones/otra-t3
env PYTHONPATH=src python3 -m unittest discover -s tests
# Visor real:
/home/tao/repos/godot/openworld-forever/.tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64 --path artifacts/estaciones/otra-t3/godot --audio-driver Dummy
```

Cada subproceso de revisión/importación tiene un límite de 180 s y se termina
si lo supera. Requiere interfaz y acceso GPU; `GODOT_BIN` permite seleccionar el
ejecutable. La generación utiliza las referencias T1 existentes y atlas T2; si
faltan, regenerarlos mediante los comandos de [estaciones](../../../estaciones.md).
El material animado requiere el proyecto/adaptador Godot: el GLB solo representa
verano compatible con atributos de calendario, no una animación portable.

Ensayo 01 detectó inversión duplicada de reversos y una comparación de píxeles
que no aislaba el redondeo de salida del motor. Se corrigieron ambos puntos;
02 valida mezcla/secuencias, 03 añade controles del visor y 04 lo captura aparte
para evitar sumar luces de prueba a las del visor. Los PNG de las secuencias
02/03/04 se conservan para comparar reproducibilidad. No se contabiliza 01 como éxito.

**Siguiente: T4**, ensayo aislado de normales de volumen con verano/otoño fijos.
T3 no adopta arte en producción ni adelanta integración/exportaciones de T5.
