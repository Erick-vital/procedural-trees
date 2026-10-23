# Contrato del ensayo RF2 con moldes Q3

Versión inicial `foliage-molds-0.1.0`; revisión acotada `0.1.1`, separada de RF1,
RF2 previas y TreeSpec.
Fijado antes de generar candidatos, por autorización del usuario tras revisar
la falta de volumen de las ramillas cortas.

- Entrada: madera final RF2 congelada y masas Q3 asociadas, extraídas de sus
  polígonos originales. Cada molde identifica su rama padre y componente.
  Máximo 64 moldes, 4096 triángulos guía y cuatro ramas de referencia.
- Muestreo de superficie proporcional al área, determinista por semilla e id.
  Pool de 2048 intentos, sin reintentos automáticos. Descartar muestras dentro
  de otro molde; seleccionar grupos separados por distancia entre muestras.
  Las partes solapadas quedan como guía y no se exportan.
- 4–24 grupos, 1–8 hojas por grupo, máximo 96 hojas. Recorridos compartidos de
  tres puntos: inserción sobre madera padre, inicio y fin de un tramo cercano
  a la superficie Q3. Hasta ocho direcciones para hallar un tramo válido.
- Alcance máximo de 4 m por conexión, medido en coordenadas finales. Se levanta
  el límite previo de .8 m solo en este ensayo. Franja interior de .02–.3 m y
  tramo superficial de .2–.8 m, independientes del tamaño de hoja.
- Radio basal de .008–.03 m, punta .2–.5 veces el basal; perfil triangular de
  tres anillos y dos tapas, 14 triángulos por conexión. La raíz penetra .04 m
  en la madera. Sin nuevos niveles de bifurcación ni remallado Q3.
- Hojas RF1 hexagonales plegadas, cuatro triángulos, largo .2–1 m, proporción
  .6, pliegue 25°. Orientación tangente al molde con variación de inclinación
  de ±30°, giro por id y escala de ±10 %. Las raíces se colocan en el segundo
  tramo del recorrido y quedan dentro de su tubo visible.
- Caso inicial: 16 grupos × 3 hojas, tamaños .45/.8 m, semilla 17. Mismos
  recorridos, raíces, ejes y cantidades entre tamaños. Se comprueba repetición
  y otra semilla, sin calibrar el método en otros árboles.
- Techo previo a mallar: 428 triángulos añadidos por rama, incluidos hojas y
  conexiones; máximo 10000 por árbol y tres materiales. El caso inicial cuesta
  416: proyección `5292 + 11*416 = 9868` en viejo-09. Esa proyección no demuestra
  una asignación viable por masa/árbol; se mide la cobertura bajo este límite.
- El GLB contiene solo base Q3, conexiones `RF2_Twig` y hojas `RF1_Leaf`.
  Copia exacta de las propiedades de corteza, hojas opacas de doble cara.
  Los moldes solo existen como datos separados, nunca como relleno visible.
- Cámaras y luces de RF2 anterior, incluidas escalas 50/25/10 % de la rama Q3;
  generación ≤120 s y verificaciones/capturas ≤180 s por subproceso terminable.
- Manifiesto: hashes de fuentes, moldes, geometría base y añadida, colocaciones,
  semillas, transformación, parámetros, coste, tiempos y tamaño GLB. Verificar
  contactos sobre mallas y exportación por canal, además de revisar capturas.

El área de molde es una guía de reparto. La cobertura se compara mediante
proyecciones ortográficas comunes de hojas/Q3 y revisión visual; ninguna cifra
de ocupación constituye aceptación estética. El ensayo puede fallar por hojas
aisladas, apariencia de placas pegadas, conexiones excesivas o pérdida de
presencia a distancia. Se registra el fallo antes de ampliar a RF3.

Revisión tras inspeccionar el ensayo inicial, antes de generar el segundo:

- El primer par .45/.8 m se conserva con sus resultados y fuentes en
  `artifacts/rediseno-follaje/rf2-moldes-01/`. La variante grande todavía deja
  huecos; 224 de 416 triángulos añadidos pertenecen a conexiones acodadas.
- `connection_shape`: `elbow` mantiene la primera regla; `straight` usa tubo
  triangular recto de dos anillos y tapas, ocho triángulos. Las raíces de hoja
  se reparten entre 75 y 98 % del recorrido, dentro de la madera visible.
- `variant`: `folded-hex` conserva cuatro triángulos/pliegue 25°; `diamond`
  reutiliza el rombo RF1 de dos triángulos/pliegue 0°. Ambos opacos y doble cara.
- Se añade una pareja de coste menor: 24 grupos × 4 hojas en rombo y conexiones
  rectas, 192 triángulos de madera + 192 de hojas, 384 añadidos; proyección 9516.
  Tamaños .8/1 m, con iguales soportes/raíces/ejes/conteos entre esos dos.
- El contraste con la primera pareja cambia conjuntamente forma, conexión,
  cantidad y organización; no se atribuye el resultado a una sola variable.
  Se mantienen el máximo 428 por rama, 10000 por árbol, 96 hojas y alcance 4 m.

Revisión aditiva `foliage-molds-0.1.2`, autorizada el 2026-10-23:

- Contrato exterior separado: `base` conserva el contrato 0.1.1 y
  `extra_leaf_count` añade hasta seis hojas por conexión recta. Se admite solo
  el rombo de dos triángulos; máximo 231 hojas y 655 triángulos añadidos.
- Caso base: 24 conexiones y cuatro hojas por conexión, tamaño nominal 1 m.
  Las 96 hojas originales conservan ids, raíces, ejes, tamaños y geometría.
  Las adiciones no participan en muestreo ni selección de soportes.
- Ordenar grupos por hash de semilla/id/canal y tomar un prefijo. La hoja
  añadida tiene id propio, raíz entre 80.75 y 92.25 % del recorrido y variación
  de tamaño/orientación según el mismo protocolo. Aumentar cantidad no altera
  las hojas añadidas supervivientes. El orden recorre todos los grupos antes
  de añadir otro nivel de hojas. Máximo 144 candidatas adicionales.
- Antes de generar, el usuario eleva el techo del rediseño a 12500 triángulos
  por árbol, conservando tres materiales. El tope derivado de rama es
  `floor((12500-5292)/11)=655`; con hojas de dos triángulos y 192 de conexiones
  caben hasta 231 hojas. Las versiones 0.1.0/0.1.1 conservan sus límites.
- Comparación 96/120/144/192 hojas, con 384/432/480/576 triángulos añadidos.
  Proyecciones a once primarias: 9516/10044/10572/11628. La última es un control
  de densidad alta, sin asignación global ni copa generada.
- Mantener molde, base Q3, madera añadida, materiales, luces y cámaras. Verificar
  contactos de las raíces nuevas y repetición; revisar el aumento de presencia
  junto con solapamiento y apariencia de láminas. El usuario ha expresado gusto
  por el ensayo mostrado; sigue pendiente una aceptación de copa completa.
