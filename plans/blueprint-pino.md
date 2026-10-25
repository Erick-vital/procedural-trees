# Blueprint experimental de pino cónico

Fecha: 2026-10-23. Inicio autorizado por el usuario al pedir reproducir un pino.
Amplía el catálogo posterior a B5; no inicia F4–F6 ni altera RF5 aprobado.
Plan marco: [sistema de blueprints](sistema-blueprints.md).

## Objetivo antes de generar

Pino low-poly estilizado de 12 m: eje central dominante, copa cónica con huecos,
pisos de ramas casi horizontales, extremos ascendentes y ramillas laterales.
Acículas agrupadas sobre los tramos distales, verde oscuro; madera marrón.
Referencia de organización: [Pinus, Gymnosperm Database](https://www.conifers.org/pi/Pinus.php),
consultada el 2026-10-23: copa normalmente cónica en juventud, ramas en
pseudovérticilos y acículas en fascículos. Es una interpretación artística del
género, sin atribución de especie, escala botánica exacta ni simulación de edad.
Las acículas se exageran para lectura low-poly; no se sustituyen por conos sólidos.

## Alcance de este intento

1. Contrato de receta/ejemplar 1.1 separado del histórico 1.0, con parámetros
   propios de pino; rechazar cruces de componentes. Conservar recetas existentes.
2. Estrategias explícitas `pine-whorls@0.1.0`, `pine-distal@0.1.0` y
   `pine-needle-pairs@0.1.0`. Reutilizar CLI, ejecutor, materiales, exportación y
   protocolo Godot; separar algoritmo sin bpy y adaptador Blender.
3. Piloto base5100/copa97 y controles base5101/98,5102/99,5103/100, fijados aquí
   antes de generar. Parámetros comunes; sin arreglos por semilla. Repetir piloto.
4. Geometría finita, sin triángulos degenerados, altura exacta, raíces de ramillas
   dentro de su padre y raíces de acículas dentro de su soporte; reimportar GLB.
   Máximo 12500 triángulos, 3 materiales y 120 s; trabajo sin reintentos:
   ≤10 pisos ×8 ramas, cuatro ramillas por rama, ≤20 acículas por soporte.
   Rechazar combinaciones fuera de presupuesto antes de Blender.
5. Importación y capturas Godot reales de copa/madera en varias vistas con luz
   y cámaras comunes. Revisión visual del agente, aceptación artística pendiente
   del usuario. Conservar evidencia seleccionada y comando reproducible.
6. Regenerar roble de referencia y comprobar GLB idéntico a B0 tras cambios
   compartidos; no promover automáticamente el pino como predeterminado.

## Criterio de salida

Receta ejecutable, piloto y tres controles con la identidad propuesta, repetición,
exportación y regresión verificadas, o informe explícito del límite encontrado.
Único perfil experimental; sin edades adicionales, bosque, LOD, viento ni FPS.

## Resultado del intento, 2026-10-24

Implementado y verificado: receta `pino_conico` 1.0.0, contratos 1.1,
algoritmo sin bpy y adaptador Blender. Cuatro semillas con parámetros comunes,
piloto repetido idéntico, controles de follaje, contactos GLB y regresiones
exactas de roble B0/columnar B4. 94 pruebas, 27 comprobaciones de integración,
ocho escenas Godot y 72 capturas reales; revisión visual realizada.
Cada principal: 12 m, 11924 triángulos y dos materiales.
[Informe y evidencia seleccionada](../docs/evidence/blueprints/pino/informe.md).

Durante el desarrollo se revisó la primera distribución plana y rala a acículas
en pares alrededor de las ramillas, conservando las semillas y el presupuesto.
La longitud relativa de las ramillas pertenece a `base`; cambiar el tamaño de
acícula o semilla de copa conserva madera. No se ajustaron casos individuales.
Aceptación artística pendiente del usuario; perfil aún experimental.

## Revisión estructural autorizada, 2026-10-24

El usuario prefiere las vistas con ramas desfasadas y mayor sensación de
ramificación y autoriza implementar la recomendación: variar alturas,
inclinaciones y longitudes, y hacer menos simétricas las ramillas laterales.
Se conserva eje central, silueta cónica, cantidad de ramas/acículas y follaje
actual. El refinado de acículas queda para otra revisión.

Receta nueva `pino_conico` 1.1.0 con estructura `pine-whorls@0.2.0`;
1.0.0 y estructura 0.1.0 conservadas. Mismos parámetros y cuatro pares de
semillas de `pine-v1.json`, sin ajustes individuales. Comparar antes/después
con cámaras y luz idénticas en copa y madera, frente/perfil/perspectiva y
vistas adicionales; repetir piloto y comprobar contactos y presupuesto.
Regenerar los cuatro anteriores y contrastar sus GLB con la evidencia 1.0.0,
además del roble B0 y columnar B4. Conservar entrada y evidencia seleccionada.
No se declara aceptación artística anticipada.

Resultado: receta 1.1.0 implementada y verificada con los mismos cuatro pares
de semillas. 97 pruebas, 51 comprobaciones, trece generaciones, once pinos
reimportados para contactos, 16 escenas Godot y 144 capturas reales.
Comparación visual antes/después realizada con cámaras/luz comunes; cantidades
y presupuesto conservados. Piloto nuevo repetido idéntico; cuatro anteriores,
roble B0 y columnar B4 idénticos a sus referencias. Sin refinado de acículas.
[Informe de revisión](../docs/evidence/blueprints/pino-revision/informe.md).
Aceptación artística de 1.1.0 pendiente del usuario.
