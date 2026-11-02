# Referencia: just-a-simple-tree

Fecha: 2026-11-01. Investigación solicitada por el usuario; **sin implementar
cambios en el generador ni adoptar un diseño nuevo**.

Repositorio: [MikeFernandez-Pro/just-a-simple-tree](https://github.com/MikeFernandez-Pro/just-a-simple-tree).
Revisión inspeccionada: **8fd94b8edc7ef1b87c086694382a0808c059971c**.
Fuentes leídas desde clon superficial en `/tmp/just-a-simple-tree-review/`, sin
instalar dependencias ni ejecutar código del repositorio externo. README público
contrastado con código. Sin benchmark, GLB de ejemplo medido ni revisión visual
de una ejecución propia; conclusiones sobre funcionamiento basadas en fuentes.

## Conclusión

Hay ideas transferibles sin sustituir Python/Blender/Godot ni subir el techo de
6999 tris. La continuidad estacional y parte importante de la dirección artística
dependen de datos, normales y materiales, no de tener más polígonos. Adaptar
algoritmos y representación es viable; trasladar su implementación TSL literalmente
no lo es. Nuestros tres planos por grupo requieren respetar otra granularidad.

## Hallazgos comprobados

1. **Calendario continuo por tarjeta.** `foliage.js:112–163` implementa brotación,
   maduración, cambio de color y retirada mediante `smoothstep`. El parámetro
   global recorre 0–1; cada tarjeta tiene un orden diferente. Cambio de color
   desde `.45 + order*.30`, caída `.19` después y transiciones de ancho `.05`.
   Estos números son decisiones artísticas del proyecto, no fenología botánica.
2. **Orden por exposición y variación correlacionada.** `foliage.js:461–531`
   combina exposición calculada mediante oclusión aproximada (peso .6) con azar
   individual y compartido por masa de follaje. Las tarjetas más expuestas
   empiezan antes, con vecinas que tienden a cambiar juntas. Flujos aleatorios
   separados para distribución, inclinación, orden y tinte mantienen estabilidad.
3. **Transición de tema distinta del ciclo del árbol.** `transition.js` hace
   un barrido diagonal en coordenadas de pantalla con ruido y brillo. Cambia
   fondo, materiales y sombras como presentación de la demo. No es un estado
   estacional persistente independiente de la cámara. `themes.js` además
   coordina paletas de escena; tema visual y fase anual son controles distintos.
4. **Normales de masas, no de planos.** `foliage.js:335–336` ilumina las tarjetas
   con normales del volumen de follaje; posición/orientación real de cada plano
   se guarda aparte. `shading.js` usa rampas de tres bandas y `foliage.js`
   añade gradiente ligado al sol, oclusión y variación por masa. Esa combinación
   explica parte del acabado anime sin requerir hojas geométricas individuales.
   Las tarjetas pueden mostrar racimos completos y están fijas en el espacio.
5. **Geometría configurable y optimizaciones reales.** Tarjetas subdivididas
   de 1×1 a 4×4; predeterminado 2×2: ocho tris por tarjeta. 35 tarjetas por masa
   de área media, escaladas por área; no es equivalente al tamaño de nuestros
   grupos. Normales suaves, orientación y curvatura se controlan separadamente.
   Descarta tarjetas enterradas/oscuras y dispone de LOD/impostores en `lod.js`.
   No concluir rendimiento solo del número de tris. Su contador de interfaz
   (`vertex-count.js`) muestra **vértices exportados**, no triángulos.
6. **Exportación estática separada de la animación.** `glb.js` hornea el estado
   de las tarjetas y colores por vértice, usa materiales estándar y guarda
   rampas cel como metadatos para restaurar ese estilo. No conserva por sí solo
   todo el render de TSL ni el ciclo anual/viento/partículas en un motor genérico.
   Divide follaje normal/joven/otoñal en materiales distintos cuando están
   presentes: adoptar esto literalmente podría superar nuestros dos materiales.
7. **Prevención de halos.** `textures.js` propaga RGB cuatro píxeles bajo zonas
   transparentes, conservando alfa, para evitar bordes negros al filtrar/mipmapeado.
   Idea compatible con nuestros atlas; ensayar antes de modificar históricos.
8. **Especies separadas, ciclo genérico.** `oak.js`, `pine.js`, etc. aportan
   generación propia; el ciclo de `foliage.js` usa constantes comunes. No se debe
   copiar como regla universal de roble/pino/abedul. En particular, una conífera
   perenne requiere su propio comportamiento y no una pérdida completa anual.

## Adaptación propuesta para nuestros árboles — no implementada

- Conservar pinturas de verano y otoño como extremos y añadir una fase continua.
  Interpolar las pinturas con calendario por grupo en un material de follaje
  compartido, conservando material de madera. No volver a un mero tinte uniforme.
- Guardar atributos estacionales por **ID estable de grupo**: orden, fase,
  variación y exposición aproximada. Las tres láminas del mismo grupo deben
  compartir estado para no desarmar visualmente la representación cruzada.
  Atributos de vértice o una tabla de datos permiten esto sin nuevos tris.
- Antes de interpolar atlas, comprobar UV, alineación y máscara: la nueva pintura
  0.1.0 cambia alfa ligeramente. Congelar máscara común o aceptar/medir una
  transición del recorte; no prometer identidad del contorno actual.
- La caída por grupos enteros puede producir huecos grandes. Para un detalle
  menor harían falta máscaras internas de hojas/subgrupos y otro estudio de
  textura/shader. No asumir control independiente sobre hojas ya horneadas.
- Evaluar normales por volumen en una variante aislada del piloto. Conservar
  madera, geometría y pintura; comparar iluminación/sombras, varias direcciones
  y distancias. No aplicar una esfera única a toda la copa ni dar por aprobada
  la estética anime. No exige subdividir las láminas.
- Exportar estados estáticos con textura/material estándar, y mantener reglas
  de animación en Godot. Pintura portable y transiciones de ejecución pueden
  coexistir; un GLB estático no transporta automáticamente el ciclo animado.
- Reglas reutilizables para fases/curvas/semillas/exportación, con parámetros y
  decisiones de especie para tiempos, paleta, retención, caída y brotación.

**Prioridad sugerida:** transición pintada verano–otoño por grupo, después ensayo
de normales de copa; caída/partículas, invierno y LOD siguen siendo trabajo
separado que el usuario aún no ha solicitado implementar en esta investigación.

## Licencia y límites

Código bajo [MIT](https://github.com/MikeFernandez-Pro/just-a-simple-tree/blob/8fd94b8edc7ef1b87c086694382a0808c059971c/LICENSE).
Si se incorpora código, conservar aviso/licencia. Música y otros recursos tienen
créditos propios; no se propone incorporarlos. No se copiaron archivos a producción.
No hay medición comparable de FPS ni conteo de un GLB externo concreto; no se
afirma que su generador completo quepa en nuestro presupuesto o que rinda peor.

Fuentes principales de la revisión:
[foliage.js](https://github.com/MikeFernandez-Pro/just-a-simple-tree/blob/8fd94b8edc7ef1b87c086694382a0808c059971c/foliage.js),
[shading.js](https://github.com/MikeFernandez-Pro/just-a-simple-tree/blob/8fd94b8edc7ef1b87c086694382a0808c059971c/shading.js),
[transition.js](https://github.com/MikeFernandez-Pro/just-a-simple-tree/blob/8fd94b8edc7ef1b87c086694382a0808c059971c/transition.js),
[glb.js](https://github.com/MikeFernandez-Pro/just-a-simple-tree/blob/8fd94b8edc7ef1b87c086694382a0808c059971c/glb.js),
[textures.js](https://github.com/MikeFernandez-Pro/just-a-simple-tree/blob/8fd94b8edc7ef1b87c086694382a0808c059971c/textures.js),
[lod.js](https://github.com/MikeFernandez-Pro/just-a-simple-tree/blob/8fd94b8edc7ef1b87c086694382a0808c059971c/lod.js).
