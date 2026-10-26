# Texturas de la rama de muestra del roble

Dirección de pintura aprobada el 2026-10-25; aplicación real a la rama pendiente
de revisión. Recursos propios generados con `image_gen.imagegen`, usando como
referencia el concepto aprobado; sin fotografías externas ni retoque de píxeles.

- `foliage.png`: RGBA 1254², cuatro hojas lobuladas en cuadrícula 2×2, con
  pincelada mate verde/oliva/salvia y acentos dorados. Alfa generado conservado.
- `bark.png`: RGB 1254², corteza cálida de placas irregulares. Se solicitó
  repetición sin costura; no se certifica continuidad matemática de los bordes.
- `manifest.json`: hashes, dimensiones, cajas alfa y punto del pecíolo por sprite.
  Las UV usan estas regiones sin recortar ni remuestrear el PNG.
- `prompts.json`: prompts completos y referencia artística de ambos recursos.

Los PNG son las fuentes de pintura disponibles; no existen capas previas.
Regenerar con el mismo prompt no asegura la misma imagen: reproducir exige estos
PNG congelados. Guardar nuevas revisiones en otro directorio. Se usan únicamente
en la muestra aislada, no en las recetas del árbol completo ni el ensayo 0.1.0.
