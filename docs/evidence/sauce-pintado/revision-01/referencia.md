# Referencia y alcance de la revisión del sauce

2026-11-02. El usuario aporta dos imágenes para corregir el resultado 1.0.0 y
pide inspirarse en [just-a-simple-tree](https://github.com/MikeFernandez-Pro/just-a-simple-tree).
Se conservan como entradas de evaluación [frontal](referencia-frontal.png) y
[lateral](referencia-lateral.png), sin retocar. No son resultados propios.

Fuentes inspeccionadas: README público y
[`willow.js`](https://github.com/MikeFernandez-Pro/just-a-simple-tree/blob/8fd94b8edc7ef1b87c086694382a0808c059971c/willow.js),
revisión `8fd94b8edc7ef1b87c086694382a0808c059971c` del clon de lectura ya
disponible en `/tmp/just-a-simple-tree-review/`. Contrastado con el fichero
público de `main`. No se instalaron dependencias ni se ejecutó código externo.

Ideas transferidas: tronco corto que se abre en brazos, ramificación superior
que sostiene masas de copa y hebras largas con agrupaciones sucesivas más
estrechas hacia sus extremos. Allí la geometría, los volúmenes y el sombreado
cel trabajan juntos; no se deduce que su árbol quepa en nuestro presupuesto.

Implementación propia en Python con recorridos Bézier, semillas separadas,
atlas existentes y grupos de tres planos fijos. Variación propia de alcance,
altura, giro y puntos de control por brazo. Distribución diferenciada de copa y
cortina, escalas afines de ancho con UV/tallo conservados. No se copia literalmente
el código externo ni se importan recursos, dependencias, motor, shader, LOD,
viento o estaciones de esa aplicación. Su [licencia MIT](https://github.com/MikeFernandez-Pro/just-a-simple-tree/blob/8fd94b8edc7ef1b87c086694382a0808c059971c/LICENSE)
se comprobó; no hay código vendorizado que requiera añadir un aviso a producción.

La referencia guía estructura y plenitud, sin atribuir equivalencia visual o de
rendimiento entre motores. Pintura de follaje/corteza 0.1.0 conservada, por lo que
paleta y acabado mate difieren de las imágenes cel aportadas. Se mantiene
Python/Blender/Godot, ejecutor, API y exportador; solo se amplían componentes del
sauce, registro de versiones y herramientas de revisión. Resultado a valorar
en [informe](informe.md), comparado con 1.0.0 a cámara/luz comunes.
