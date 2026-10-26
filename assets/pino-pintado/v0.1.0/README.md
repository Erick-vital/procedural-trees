# Pintura del pino, muestra PP2 0.1.0

Recursos de producción experimental versionados, generados con `image_gen.imagegen`.
`prompts.json` conserva las instrucciones completas; `manifest.json`, los hashes,
dimensiones y canales. Única referencia de imagen: concepto propio A de PP1.
No se han utilizado fotografías o imágenes externas como texturas.

- `foliage.png`: RGBA, tres ramillas horizontales en filas, raíz a la izquierda.
  Variantes compartidas por láminas dobladas y cruzadas. Transparencia original
  conservada; recorte propuesto .5. Acículas estrechas, agrupación pintada amplia.
- `bark.png`: RGB, placas verticales mates; no hay mapas de normales,
  rugosidad ni iluminación adicionales. La rugosidad es constante .95.

Ambos PNG son las fuentes editables conservadas y los mapas finales de esta
muestra; no existen capas de pintura previas, pues el generador entrega un PNG.
Los `.blend` regenerables contienen UV, nodos editables y texturas empaquetadas.
Regenerar imágenes con los prompts no garantiza igualdad: reproducir la rama
requiere estos mismos PNG y sus hashes. No modificar estos recursos para una
nueva revisión; crear otro directorio de versión.

La corteza se solicitó repetible, pero aún debe comprobarse la costura y la
repetición en el motor durante PP3. Las láminas no se orientan hacia la cámara.
