# OF1: rama O5 con pintura actual y nueva distribución

Preparada el 2026-11-03 para revisión artística **antes de integrar una copa**.
Maduro O5, semilla 3100, primaria lateral inferior `p:0` y sus 20 descendientes;
distribución 17, pintura 2718. [Galería](../../../../artifacts/oak-foliage/of1-rama-04/index.html).
[GLB de rama](../../../../artifacts/oak-foliage/of1-rama-04/painted/tree.glb),
[fuente Blender](../../../../artifacts/oak-foliage/of1-rama-04/painted/tree.blend).

## Resultado y alcance

Se conserva exactamente la madera O5. La distribución usa ejes reales y reparte
grupos sobre terciarias, terminales y tramos exteriores de secundarias, sin hojas
en la primaria gruesa. Cada grupo son tres láminas cruzadas fijas, seis triángulos.
Las inserciones se extienden longitudinalmente; longitud, vigor y proporción
exterior de cada eje determinan cupos. Variación de tamaño, giro y plantilla con
semillas explícitas. No se usan moldes Q3 ni soportes geométricos nuevos.

Se reutilizan **sin modificar** el atlas de follaje 0.3.0 y corteza 0.2.0, incluidos
sus hashes históricos. Las tres láminas pasan por un punto opaco del tallo pintado,
anclado a triángulos reales de madera. El punto se obtiene de raíces originales
de hojas de cada plantilla y una búsqueda acotada en su vecindad de proyección;
no se repinta el PNG. El máximo ajuste es .04032 de coordenada normalizada de grupo.

| Geometría exportada | Triángulos | Materiales |
|---|---:|---:|
| Madera de la rama O5, sin cambios | 646 | 1 |
| Follaje: 64 grupos/192 láminas | 384 | 1 |
| Rama con follaje | **1030** | **2** |
| Testigo de madera completa O5, sin follaje | 3714 | 1 |

El libro de cupos asigna 216 grupos al árbol: `p:0..6` → 64/20/14/39/27/28/24.
**Solo se materializan los 64 de la muestra.** El total de follaje planificado es
1296 tris, dentro de la reserva 1584; quedan 288 sin asignar. Proyección aritmética
para este maduro: 3714+1296=5010. Cota de familia: 5415+1296=6711 (<6999).
**No es un árbol completo con hojas generado ni validado**. La proyección no
certifica cobertura, contactos o presupuesto de perfiles modificados futuros.

## Verificación

**281 pruebas y 32 comprobaciones de cierre correctas.** Repetición desde fuentes:
cuatro GLB y `layout.json`/estructura O5 idénticos. GLB testigo O5 completo idéntico
a la referencia aceptada. Madera de muestra con/sin follaje idéntica, subconjunto
exacto del testigo; sin añadir, podar o desplazar madera. Uniones internas pasan.
PNG embebidos idénticos al catálogo, UV y normales válidas, dos materiales en rama,
alfa recortada .5, doble cara, mipmaps y filtro anisotrópico en revisión Godot.
[Datos/hashes](verification.json), [pruebas](tests.txt).

Para cada grupo se reconstruye el contacto mediante UV interpoladas en los
triángulos float32 del GLB y se mide su distancia a la madera real. Error máximo
**0.000000387 m**; alfa en el punto elegido ≥192/255 en las tres proyecciones.
Esto acredita el anclaje elegido, no la conectividad física de cada hoja pintada,
ni que todas las mipmaps conserven ese píxel. No se certifican intersecciones
entre todas las láminas ni ausencia universal de halos.

Godot produjo 36 capturas: 12 por madera, rama con follaje y follaje aislado.
Se inspeccionaron 23: doce de la rama con hojas (seis orientaciones, dos escalas,
fondo oscuro, luz alternativa, sombra con receptor y acercamiento); cinco de
madera y seis de follaje aislado. Las otras 13 se conservan sin afirmar inspección.

## Lectura visual y límites

La pintura conserva su estilo y los conjuntos acompañan ramificaciones reales.
La base gruesa queda visible y los tramos exteriores muestran continuidad con
huecos entre conjuntos. La rama mantiene presencia a escala media y el receptor
muestra sombras recortadas. El acercamiento permite ver tallos pintados junto a
madera, pero también cruces de láminas y tarjetas vistas de canto.

**Siguen existiendo grupos compactos en ciertas vistas**, zonas de secundarias
expuestas y superposición de tarjetas en detalle. No se da por resuelta la
plenitud de una copa ni por aprobada la rama. Es el resultado para que el usuario
valore tamaño de hojas, densidad, continuidad y cantidad de madera visible.
Sin benchmark, viento, LOD o integración al árbol completo.

## Iteraciones conservadas

- Ensayo 01: no encontraba contacto opaco común cerca de la primera raíz de una
  plantilla. Se permitió elegir otra raíz del mismo tallo pintado y se mantuvo
  la búsqueda local acotada. Sin cambiar pintura.
- Ensayo 02: 84 grupos solo en terciarias/terminales, demasiado compactos en
  extremos. Se conservaron sus capturas, sin aceptación artística.
- Ensayo 03: 64 grupos y secundarias exteriores. La toma inicial llamada sombra
  tenía iluminación con sombras, pero no activaba el receptor; no se usa como
  evidencia de sombra proyectada. El lote 04 activa el receptor y añade detalle.
- Lote 04 final: misma geometría 03, fuentes/protocolo congelados y repetición
  independiente. No se borran las iteraciones para ocultar límites.

## Reproducción

```sh
python3 scripts/prepare_oak_foliage_sample.py \
  --config configs/oak-foliage/sample-v1.json --output artifacts/mi-rama-of1
python3 scripts/prepare_oak_foliage_sample.py \
  --config configs/oak-foliage/sample-v1.json --output artifacts/mi-rama-of1-repeat --stage generate
PYTHONPATH=src python3 -m unittest discover -s tests > /tmp/mi-rama-of1-tests.txt 2>&1
python3 scripts/close_oak_foliage_sample.py --study artifacts/mi-rama-of1 \
  --repeat artifacts/mi-rama-of1-repeat --tests /tmp/mi-rama-of1-tests.txt
```

Salidas nuevas por ejecución, generación ≤120 s y subprocesos de revisión ≤180 s.
Blender/Godot y API usan el entorno externo al sandbox documentado. Configuración,
semillas, cupos, contactos, versiones y procedencia quedan en los manifiestos.
La aceptación artística del usuario es el siguiente paso antes de integrar copa.
