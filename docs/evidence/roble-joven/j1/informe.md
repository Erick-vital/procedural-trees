# J1 — madera joven y rama con follaje

Fecha: 2026-11-04. Primera entrega del perfil joven autorizado: revisión de
madera y muestra antes de integrar el árbol completo. **Implementada, verificada técnicamente y aprobada por el usuario**
el2026-11-04: [aceptación y hashes](user-acceptance.json).
No se hicieron pruebas de rendimiento.

## Alcance e identidad

Se reutiliza O5 `oak-growth-0.5.0`, preset joven de5 m y madurez.15. Semillas
3100–3103; distribución17 y pintura2718. No se reduce el maduro mediante escala:
el preset cambia madurez, dominancia del eje, crecimiento y ramificación. No
se modificaron los algoritmos históricos ni se añadieron los tres ejes de OF11.
La comparación de edad usa **O5 maduro desnudo**, no el maduro3.0.0 con extensión
central. Su función es comprobar diferencias de porte a altura nominal común.

La muestra usa joven3100, primaria `p:0` y todos sus descendientes. Contrato
experimental `oak-young-sample-0.1.0`, distribución B de cadenas histórica
reutilizada, span/H.10 y región radial de anclajes.25H. Tres láminas fijas/seis
triángulos por grupo. Pintura, recortes y corteza aprobados conservados byte
por byte: follaje0.3.0 de2000² y corteza0.2.0 de1254²; máximo dos materiales.
El contrato joven solo admite este perfil fijo y valida semillas/estructura.
No concede aceptación artística ni publica todavía una receta joven de producción.

## Madera y presupuesto desde el inicio

| Semilla | Madera completa tris | Reserva de follaje | Proyección aritmética completa |
|---|---:|---:|---:|
| 3100 | 2952 | 864 | 3816 |
| 3101 | 3233 | 864 | 4097 |
| 3102 | 2672 | 864 | 3536 |
| 3103 | 3258 | 864 | 4122 |

**Esta tabla no representa cuatro árboles completos con follaje.** La reserva
es144 grupos×6 tris. Solo se ha materializado el cupo de la rama piloto.
Cota de diseño: madera O5≤5415 +864 de follaje =**6279**, bajo6999. El resto
de la copa necesita planificación, exportación y revisión tras aprobar la muestra;
no queda validada por sumar una reserva. En3100,p:0 recibe71 de144 grupos por
peso de ejes elegibles, sin aumentar el cupo por tratarse de la muestra.
La cobertura del resto de las ramas y del eje superior queda pendiente de
la futura integración; no se deduce de este cupo de muestra.

Cuatro maderas y cuatro primarias aisladas exportadas, con uniones embebidas,
radios y altura auditados; todos los casos pasan. Repetición de joven3100:
GLB de madera y primarias idénticos. Joven3100 y maduro3100 reproducen sus dos
GLB históricos O5. Cuatro firmas jóvenes distintas. La geometría y reglas de
madera existentes no necesitaron cambios para preparar esta entrega.

## Rama exportada y repetición

| Variante | Triángulos | Materiales |
|---|---:|---:|
| Testigo: madera del joven completo | 2952 | 1 |
| Madera de la rama p:0 | 620 | 1 |
| Rama con follaje | **1046** | **2** |
| Follaje aislado | 426 | 1 |

**71 grupos/213 láminas**, tres masas lógicas.71×6 =426 tris de follaje.
Madera de la rama idéntica con/sin hojas y subconjunto exacto de la madera
completa. Testigo completo idéntico al generado por la CLI O5 de joven3100.
Cuatro GLB de muestra, layout y estructura repetidos exactamente. El contacto
sobre los GLB reimportados y la alfa opaca de las raíces pintadas pasan; máximo
error **0.000134 mm**, frente a tolerancia.01 mm. Se auditan uniones de toda la
madera del testigo, incluido el nacimiento de p:0 en su padre.

23 comprobaciones de muestra correctas: texturas embebidas, materiales/doble
cara, alfa MASK.5, triángulos, madera idéntica, reserva/cupo, contactos y uniones.
El cierre comprueba además repetición, hashes, testigos, fuentes y capturas;
detalles en `summary.json`. **11 pruebas correctas**: cinco del contrato joven
y seis de la distribución histórica B. No se declaran mejoras de IA ni cambios
artísticos aprobados por los resultados numéricos.

## Revisión visual Godot

Godot4.7.2, Compatibility/RTX5060,900×900, MSAA4, mipmaps/anisotropía, materiales
y sombras dobles explícitos. **84 capturas reales:48 de madera y36 de muestra**.
Inspeccionadas las84 como miniaturas en láminas, además de los originales
`painted--front.png`, `painted--perspective.png` y `painted--contact-close.png`. Esto no equivale a
inspeccionar cada captura a resolución original ni certifica todas las uniones.

Madera: cuatro orientaciones de cada joven y de primarias solas con cámaras
métricas comunes; joven3100/maduro3100 con encuadres relativos a su altura para
comparar porte. No se alteraron las mallas ni se aplicó escala anisótropa.
Muestra: frente, perfil, perspectiva oblicua, reverso, arriba, abajo, dos
encuadres lejanos, fondo oscuro, luz alternativa, sombra y detalle de contacto.
Son vistas ortográficas de inspección, sin cámara definitiva del juego.
Protocolos exactos y motor en `wood-protocol.json` y `branch-protocol.json`.

Observaciones del agente conservadas tras la aceptación artística del usuario:

- Las cuatro maderas jóvenes son más esbeltas, con eje principal más dominante
  y brazos proporcionalmente menos extendidos que la referencia madura O5.
  Se observa variación de inclinación/asimetría; no es solo cambio de tamaño.
- La muestra conserva pintura y uniones legibles; aparecen dos desarrollos
  foliares principales conectados por la madera y una ramilla inferior desnuda.
  Las masas se ven compactas desde perfil y abajo; arriba se notan láminas de
  canto y trazos finos. No se declara continuidad visual uniforme.
- No se ven grandes rectángulos opacos evidentes en fondos claro/oscuro. Las
  sombras de follaje y madera aparecen. En algunas vistas la base de la rama
  roza o queda recortada por el marco; el detalle de contacto recorta de forma
  intencional. La auditoría geométrica se hace sobre el GLB completo.
- El detalle de contacto es consistente con los anclajes auditados, pero no
  acredita cada conexión de cada hoja pintada ni una malla soldada. A distancia
  se pierde detalle; no se hicieron pruebas de movimiento, aliasing ni rendimiento.

[Comparación de muestra](comparison.jpg), [fondos y distancias](appearance.jpg),
[cuatro maderas](wood.jpg), [comparación de porte](age-comparison.jpg).
Galería local: `artifacts/roble-joven/j1-rama-01/index.html`.

## Punto de revisión requerido

La [política del repositorio](../../../politica-arboles-optimizados.md) establece:
«Presentar primero pintura y una rama representativa para aprobación artística
del usuario, antes de integrar el árbol completo». El usuario aceptó la madera y
esta aplicación de la pintura al joven con «si». Los estados pendientes de los
JSON de auditoría describen el momento previo; la decisión posterior está en
`user-acceptance.json` y no altera sus mediciones.

La fase posterior ya integró piloto y tres controles completos:
[resultado J2](../j2/informe.md). La aceptación del árbol completo sigue pendiente,
separada de esta aprobación de muestra. Sin nuevas pruebas de rendimiento.

## Reproducción

Fuera del sandbox en esta máquina, por bloqueo conocido del cierre de audio de
Blender y por capturas gráficas Godot. No hubo intentos fallidos de este estudio.
Usar carpetas nuevas para no sobrescribir resultados:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p test_oak_young_sample.py -v
PYTHONPATH=src python3 -m unittest discover -s tests -p test_oak_foliage_chains.py -v
python3 scripts/prepare_oak_young_wood.py --output artifacts/roble-joven/mi-madera --stage generate
python3 scripts/prepare_oak_young_wood.py --output artifacts/roble-joven/mi-madera --stage review
python3 scripts/prepare_oak_young_sample.py --output artifacts/roble-joven/mi-rama --stage generate
python3 scripts/prepare_oak_young_sample.py --output artifacts/roble-joven/mi-rama-repeat --stage generate
python3 scripts/prepare_oak_young_sample.py --output artifacts/roble-joven/mi-rama --stage review
python3 scripts/close_oak_young_sample.py --wood artifacts/roble-joven/mi-madera --sample artifacts/roble-joven/mi-rama --repeat artifacts/roble-joven/mi-rama-repeat --evidence artifacts/roble-joven/mi-evidencia
```

Config:`configs/oak-foliage/young-sample-v1.json`; madera O5 joven versionada
existente. Salidas voluminosas en `artifacts/`; evidencia seleccionada en esta
carpeta. Generación≤120 s y subprocesos de revisión≤180 s. Muestras3.29/3.12 s
aproximadamente según manifiestos; estos tiempos no son benchmark gráfico.
