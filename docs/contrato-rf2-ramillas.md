# Contrato experimental de la revisión RF2

Versión `foliage-branch-0.2.0`. Se fija antes de generar candidatos; no modifica
`TreeSpec`, RF1 ni `foliage-branch-0.1.0`. Alcance: primaria 100 y secundarias
200–202 congeladas, sin iniciar RF3.

- `base` contiene el contrato RF2 original: 4–24 recorridos de tres puntos,
  .2–.8 m, hasta 192 hojas; unidad RF1 y semilla explícitas.
- `twigs` controla solo el mallado visible. Radio basal .003–.03 m, radio final
  .15–.6 veces el basal, perfil de 3–4 lados y penetración de raíz .005–.05 m.
  Tres anillos y dos tapas: `4*sides + 2*(sides-2)` triángulos por ramilla
  (14 con tres lados, 20 con cuatro). El primer anillo se prolonga dentro de la
  madera; no se desplazan las hojas ni los recorridos de la pareja.
- La madera nueva usa `RF2_Twig`, copia de las propiedades de `Oak_Bark`, para
  identificarla por separado. Base, ramillas y hojas suman como máximo tres
  materiales opacos. No se sueldan ni remallan los polígonos Q3.
- `distribution.mode`: `original` reproduce los recorridos RF2; `target`
  selecciona recorridos hacia una región elipsoidal congelada desde la caja del
  follaje Q3 asociado, antes de generar candidatos. No es una copa completa.
- La región usa una rejilla fija de 8×8×4 centros interiores al elipsoide. Cada
  candidato aporta celdas a distancia menor que `influence_radius_m` (.1–.5 m)
  de su recorrido. Es una aproximación espacial independiente del mallado de
  hojas, no una medición de cobertura visual. Se conserva una medida aparte
  de ocupación real por las hojas y de región alcanzable.
- Pool máximo: 24 inserciones × 8 direcciones, tres puntos por recorrido.
  Selección voraz por celdas nuevas y desempate estable por id; una dirección
  por inserción. El conteo toma un prefijo de esa selección. Densidad, tamaño y
  orientación de hoja no cambian las ramillas. La semilla sí puede cambiarlas.
- Techo previo al mallado: 768 triángulos añadidos por rama, incluidas hojas y
  ramillas. Este techo experimental **no** autoriza repetirlo en todo el árbol.
  Se informa también `5292 + 11*coste_añadido`, proyección aritmética conservada
  solo como diagnóstico de viejo-09. RF3 tendrá que asignar su presupuesto real.
- Generación ≤120 s; verificación/captura ≤180 s por proceso, lotes gráficos
  pequeños. Sin reintentos automáticos; máximo 192 candidatos y 256 celdas.
- Se comparan sin/con ramillas con recorridos, hojas, materiales de base y
  cámaras iguales; después distribución dirigida con igual conteo y un control
  de menor conteo. Se conservan hashes de fuentes, referencia, base Q3,
  ramillas, colocaciones, materiales y cámaras; tiempos y tamaño GLB explícitos.
- Tras inspeccionar el primer ensayo se añaden controles de alcance .8 m:
  uno conserva 9 hojas/m y registra el aumento de conteo; otro usa 6 hojas/m
  para mantener cuatro hojas por recorrido y el mismo coste. Esta segunda
  pareja modifica recorrido, elección espacial y separación; no aísla longitud
  con posiciones fijas. La unidad visible no cambia.

Conexión geométrica: inserción sobre la superficie Q3 y dentro del volumen de
la ramilla; raíz de cada hoja dentro de su ramilla cerrada. Se comprueba sobre
las mallas, además del recorrido. Esto prueba contacto geométrico, no legibilidad
en pantalla. La lectura se revisa con capturas Godot frontales, laterales,
superiores/inferiores, detalle y escalas comunes, sin aceptar RF3 por métricas.
