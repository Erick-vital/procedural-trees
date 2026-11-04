# F4: variaciones desde el chat de Codex

Fecha: 2026-11-02. **F4 adaptada implementada y verificada técnicamente**, con
revisión visual del agente. Aceptación artística del usuario pendiente.
[Auditoría seleccionada](verification.json), [variantes](variantes.jpg) y
[ocupación de copa](ocupacion.jpg).

El usuario pidió continuar F4 y precisó conservar el flujo de abrir Codex en este
repositorio y pedir árboles, por ejemplo diez variantes. No se añade proveedor
externo, cuenta, clave ni otro proceso de Codex. La interpretación ocurre en el
chat; las propuestas JSON son la frontera con el ejecutor. Este cambio frente
al adaptador de proveedor del F4 original está registrado en el
[plan vigente](../../../../plans/f4-lenguaje-blueprints.md).

## Resultado

Seis solicitudes interpretadas en esta sesión y conservadas antes de generar en
`configs/language/f4-responses-v1.json`; solicitudes y expectativas en
`configs/verification/f4-v1.json`. Receta `roble_copa_ancha@2.2.0` intacta.
Cada candidato se compara con perfil adulto de la misma receta y mismas semillas
base/copa/pintura. No se retocaron parámetros después de inspeccionar resultados.

| Solicitud | Cambio respecto a la base adulta | Tris base → candidato |
| --- | --- | --- |
| Joven de 4 m y tronco fino | Perfil joven: 4 m, radio .12 m, grupo .45 m | 5804 → 3132 |
| Adulto de 11 m y radio .55 m | Altura 10→11 m, radio .5→.55 m | 5820 → 6124 |
| Viejo de tronco grueso/asimétrico | Perfil viejo: radio .8 m, asimetría .85 | 5868 → 6812 |
| Copa densa | Grupos 264→300 | 5820 → 6196 |
| Copa abierta | Grupos 264→180 | 5820 → 5044 |
| Ramas más asimétricas | Asimetría .6→.8 | 5820 → 5996 |

Los doce árboles tienen **menos de 7000 tris y dos materiales**. Las semillas
varían entre casos de edad, pero son idénticas dentro de cada pareja. El número
de la semilla no implica equivalencia geométrica entre perfiles.

**28 comprobaciones correctas**: dirección de parámetros, presupuestos,
fuentes/entorno comunes, geometrías diferentes, madera base conservada al cambiar
ocupación, resolución idéntica desde respuestas guardadas y repetición con GLB
idéntico de copa densa. La conservación de madera usa malla/ramas base reales,
normalización y auditoría de simplificación idénticas; los conectores de los
grupos cambian con su cantidad y no están incluidos en esa afirmación.

Tres regresiones exactas contra la evidencia del roble 2.2.0: joven=`joven-07`,
viejo=`pilot` y base adulta=`adulto-00`. Se ejecutaron también los dos comandos
CLI reales sobre una respuesta guardada de copa densa: mismo hash GLB.

**222 pruebas correctas**, incluidas ocho pruebas nuevas F4 (con quince variantes
de entrada inválida), contrato y reproducción de un plan de diez árboles,
alteración de archivos, límites de lote, fallo geométrico/presupuesto y parada
sin generar el siguiente ejemplar. El plan de diez se prueba sin Blender; este
ensayo geométrico contiene seis candidatos, seis bases y una repetición, más la
repetición CLI. No se presenta como lote artístico validado de diez variantes.

## Inspección visual

Godot 4.7.2 importó los doce GLB, comprobó triángulos, materiales, UV, normales,
texturas/mipmaps y recorte alfa. **48 capturas reales**: frente, perfil,
perspectiva y superior de cada pareja. Cámaras calculadas desde la unión de
bounds y compartidas por pareja, misma luz/fondo, MSAA4 y filtrado anisotrópico.
Las cámaras Blender de cada generación pueden diferir; no se usan para esta
comparación visual. No hay comparabilidad de escala común entre todas las
parejas; la galería de variantes es un resumen de sus capturas individuales.

El agente abrió las seis láminas, con las 48 vistas, e inspeccionó:

- Joven: reducción clara de escala, tronco y copa. El encuadre físico común limita
  la lectura de detalle del candidato pequeño.
- Adulto/viejo: cambios visibles de altura/grosor y proporción de copa; mismo
  estilo de pintura y familias de ramificación.
- Densa: ganancia moderada de plenitud, más perceptible en perspectiva/arriba.
- Abierta: huecos mayores y más madera visible; diferencia clara arriba.
- Asimétrica: cambia el recorrido de ramas y reparto de copa; efecto sutil en
  perfil, más claro de frente y arriba.

Sin pérdida evidente de materiales o partes completas en las láminas revisadas.
No certifica todas las conexiones, sombras en otras condiciones, rangos completos
ni aceptación artística. Ninguna métrica demuestra naturalidad, mejora de IA o FPS.

## Contrato y uso futuro

`plan-blueprints` valida **todo el lote antes de Blender** y congela solicitud,
respuestas, receta, semillas, resolución y hashes. `generate-blueprint-plan`
verifica esas entradas y genera sin consultar modelos. Máximo treinta árboles,
identificadores únicos sin rutas, campos cerrados y tipos/rangos estrictos.
F4 impone 6999 tris/dos materiales sobre el resultado exportado, conservando el
contrato histórico de cada receta; no puede garantizar el coste final solo por
la cota previa conservadora. Ante un fallo se detiene y se conserva su estado.

Las instrucciones permanentes están en AGENTS y la [guía de uso](../../../uso-lenguaje-natural.md).
El origen `codex-session` es declarado: el JSON no autentica inferencias. Esta
sesión produjo las interpretaciones reales; repetirlas como `saved-response`
no es otra llamada ni otra evaluación de un modelo. No se ha validado una API
externa ni un adaptador de proveedor independiente.

## Reproducción

Desde la raíz; carpetas nuevas, entorno fijado y escritorio real para Godot:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
python3 scripts/verify_language.py --output artifacts/f4/otra-evaluacion --stage generate
python3 scripts/verify_language.py --output artifacts/f4/otra-evaluacion --stage review
```

El verificador no consulta modelos; regenera desde las respuestas conservadas.
Resultado revisado: `artifacts/f4/ensayo-03/index.html`, capturas y protocolos
`*-input.json` en esa carpeta. Hashes de fuentes, respuestas y capturas en la
[verificación](verification.json); manifiestos completos en cada árbol.

Intentos anteriores conservados localmente: `ensayo-01` falló por timeout de
120 s al cerrar Blender dentro del sandbox; grupo terminado y lote fallido.
`ensayo-02` exportó los casos pero dos checks comparaban el GLB de referencia
completo en lugar de su madera base; se corrigió la auditoría y se repitió sin
cambiar geometría ni parámetros. La primera suite dentro del sandbox tuvo
221/222 por bloqueo de sockets; fuera pasó 222/222. No se ocultan como éxitos.

Pendientes: valoración artística del usuario y pedidos de variación nuevos con
sus validaciones propias. F5/F6 permanecen sin iniciar. No se amplían especies,
componentes geométricos, estaciones, LOD, bosque ni mediciones de rendimiento.
