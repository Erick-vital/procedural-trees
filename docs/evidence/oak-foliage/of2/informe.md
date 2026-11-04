# OF2: comparar cadenas de masas en la rama O5

Preparado el 2026-11-03 a partir de la revisión del usuario de OF1.
[Petición y alcance](feedback-of1.json). **Aceptación artística pendiente.**
[Galería OF1/A/B/C](../../../../artifacts/oak-foliage/of2-variantes-02/index.html).

## Comparación controlada

Misma madera O5 maduro3100/p:0, distribución17 y pintura2718. OF1 se conserva
como referencia anterior y se vuelve a capturar con las mismas cámaras que las
variantes. Contrato nuevo `oak-foliage-sample-0.2.0`; contratos y recetas previos
intactos. No se integra follaje en el árbol completo.

| Variante | Masas lógicas | Intención |
|---|---:|---|
| A | 3 | Terminales y laterales, concentración distal |
| B | 4 | Continuidad media, puentes y recorrido longitudinal |
| C | 5 | Centros separados, masas fragmentadas y más huecos |

**Las tres conservan 646 tris de madera +384 de follaje =1030**, dos materiales,
64 grupos/192 láminas. Misma secuencia de tamaños y plantillas y misma área de
láminas:180.66585–180.66586 m² en GLB (incluye transparencia; no área real de
hojas). A/B/C cambian colocación y orientación, no el número de grupos ni el
área disponible. Respecto a OF1 también se cambia la forma relativa del grupo
(más ancho/menos profundo), por lo que esa pareja no aísla solo distribución.

Los atlas0.3.0 de follaje y0.2.0 de corteza son idénticos. Se conserva el libro
de cupos OF1 para controlar presupuesto:216 grupos globales/1296 tris,64 grupos
en esta rama. Solo se materializa la muestra. Proyección aritmética5010 para
el maduro; cota5415+1296=6711, dentro de6999 y reserva1584. No es una copa
completa generada ni una garantía artística o de contacto para otros brazos.

## Reglas nuevas

- Pool de segmentos sobre secundarias exteriores, terciarias y terminales.
  Vigor, orden, recorrido y exposición radial aproximada ponderan la selección.
- Descartar candidatos bajos con trayectoria descendente mediante altura
  relativa al brazo; en esta rama se excluyen96 candidatos que alimentaban
  el satélite inferior. No se borra ni desplaza esa madera.
- Elegir centros de masa desde el propio esqueleto. B usa estratos sucesivos
  de recorrido; A prioriza extremos; C maximiza separación espacial.
- Asignar cupos a las masas y segmentos cercanos. B prioriza más separación
  entre inserciones dentro de sus puentes, para extenderlos sobre el recorrido.
- Registrar funciones terminal/lateral/puente, pertenencia de cada grupo y
  enlaces entre masas ordenados por recorrido. Los enlaces son relaciones de
  planificación; no añaden tubos o superficies artificiales entre ramas.
- Orientar conjuntos con la dirección del brazo, componente exterior y arriba.
  Reducir profundidad relativa de grupos y variar escala con madurez.
  No se usa billboard orientado a cámara ni un nuevo atlas.

La madurez prepara entre2 y5 masas y escalas distintas, pero **solo se revisa
esta rama madura**. Jóvenes, centenarios, otros brazos y el árbol completo
quedan sin certificar. No se activan masas colgantes ni se rellena el núcleo.
Los centros de masa no garantizan un número idéntico de componentes en2D.

## Verificación

**287 pruebas y99 comprobaciones correctas.** Repetición de los doce GLB
(cuatro por variante) y layouts exacta. Madera de las tres idéntica a OF1/O5;
el testigo O5 completo sin hojas coincide con su hash histórico. Texturas,
UV, normales, alfa recortada .5, doble cara, mipmaps y materiales revisados.
Los anclajes opacos pasan sobre GLB; máximo error ≤0.000000419 m. La auditoría
certifica esos puntos, no la conectividad de cada hoja pintada ni ausencia de
cruces entre todas las láminas. [Datos/hashes](verification.json), [pruebas](tests.txt).

Godot produjo **68 capturas a color y20 máscaras**, todas con informes correctos.
Se inspeccionaron44 capturas a color (OF1/A/B/C en11 tomas) y16 máscaras de
follaje (cuatro variantes, cuatro vistas). Las otras28 imágenes diagnósticas
quedan disponibles sin afirmar inspección individual. Cámaras/luz/escala comunes,
fondos claro/oscuro, distancias, reverso, vista superior/inferior y sombras reales.

## Lectura visual

**B es la base que recomiendo para continuar**, pendiente del usuario: conecta
mejor el desarrollo intermedio con los extremos, mantiene la primaria gruesa
visible y evita el conjunto inferior decorativo de OF1. En algunas vistas las
cuatro masas se unen en proyección; conserva huecos dentro de su contorno.

A deja mucha madera expuesta pero sigue concentrando grupos en los destinos
distales. C introduce separaciones claras, aunque vuelve a sentirse más escasa
y puede recuperar cierta lectura de grupos adheridos. Ambas son controles útiles,
no se declaran fallidas por preferir B ni quedan aceptadas automáticamente.

Persisten compactación local, tramos desnudos y tarjetas de canto visibles,
especialmente desde arriba. La dirección mejora la relación de masas con madera,
pero no se declara reconocimiento inequívoco de roble, copa resuelta o mejor FPS.
No se promueve variante ni se integra copa por este cierre.

## Indicadores de máscaras

Umbral128, conectividad8, sin dilatación. Componente significativo ≥1 % del
primer plano y ≥32 píxeles. La fracción de madera sin solapamiento compara
máscaras proyectadas: **el follaje detrás de la madera también cuenta como
solapamiento**. No es una medición directa de madera visible, volumen o calidad.

Perspectiva, cámaras comunes:

| Caso | Componentes grandes | Mayor componente / follaje | Madera sin solapamiento proyectado |
|---|---:|---:|---:|
| OF1 | 2 | 82.6 % | 74.8 % |
| A | 2 | 52.7 % | 92.2 % |
| B | 1 | 100.0 % | 73.7 % |
| C | 4 | 33.6 % | 91.1 % |

B forma un componente proyectado principal en las cuatro vistas medidas; C
presenta2–4 componentes grandes según cámara. Las masas lógicas pueden tocarse
en proyección o contener varias islas de textura. Los indicadores acompañan
la inspección y no determinan por sí solos una aceptación artística.

## Reproducción

```sh
python3 scripts/compare_oak_foliage_chains.py --output artifacts/mi-of2
python3 scripts/compare_oak_foliage_chains.py --output artifacts/mi-of2-repeat --stage generate
PYTHONPATH=src python3 -m unittest discover -s tests > /tmp/mi-of2-tests.txt 2>&1
python3 scripts/close_oak_foliage_chains.py --study artifacts/mi-of2 \
  --repeat artifacts/mi-of2-repeat --tests /tmp/mi-of2-tests.txt
```

La comparación requiere el testigo OF1 en `artifacts/oak-foliage/of1-rama-04`.
Si falta, regenerarlo primero con `prepare_oak_foliage_sample.py`, configuración
`configs/oak-foliage/sample-v1.json`, esa salida y `--stage generate`.
Cada directorio debe ser nuevo. Blender/Godot usan el entorno externo al sandbox
documentado, con subprocesos acotados. La primera prueba01 dejó B/C demasiado
similares; se conservaron sus capturas. El lote02 separa C y extiende B con las
mismas condiciones para todas las semillas, sin retoque de geometría por ejemplar.

## Elección posterior del usuario

El usuario elige B como base y autoriza probar la copa completa del maduro 3100
con expansión lateral, reparto entre bifurcaciones y variedad de siluetas.
[Dirección registrada](../of3/user-direction.json) y [piloto OF3](../of3/informe.md).
La elección de B no constituye aceptación de la nueva copa completa.
