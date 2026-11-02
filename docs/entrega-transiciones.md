# Entrega de transiciones del roble — T6

2026-11-02. **T0–T6 cerradas y lote aprobado**. Variante explícita
`season-bundle-0.1.0`, basada en roble 2.2.0. Pintura compatible y calendario del
piloto aprobados; normales .35 elegidas/aprobadas por delegación. El lote de cuatro
casos fue **aprobado artísticamente por el usuario** después del cierre T6.
[Aceptación final](evidence/estaciones/cierre-t6/user-acceptance.json); los informes
y paquetes congelados conservan su estado anterior por trazabilidad.
[Decisiones separadas](evidence/estaciones/cierre-t6/decisions.json).

## Abrir la entrega

[Galería de cierre](../artifacts/estaciones/cierre-t6-02/index.html), con secuencias
fija/orbital de ida y vuelta y comparación de cinco fases/cuatro casos.
Los siguientes archivos se conservan en `artifacts/`, ignorados por Git:

| Entrega | Archivo |
| --- | --- |
| Proyecto Godot y 16 extremos GLB | [roble-estacional-0.1.0.zip](../artifacts/estaciones/integracion-t5-03/roble-estacional-0.1.0.zip) |
| Fuentes y entradas congeladas T5 | [fuentes-y-entradas-t5.zip](../artifacts/estaciones/cierre-t6-02/fuentes-y-entradas-t5.zip) |
| Visor disponible en el workspace | [project.godot](../artifacts/estaciones/integracion-t5-03/godot/project.godot) |
| Secuencia fija | [fixed.webp](../artifacts/estaciones/cierre-t6-02/fixed.webp) |
| Secuencia orbital | [orbit.webp](../artifacts/estaciones/cierre-t6-02/orbit.webp) |
| Auditoría y hashes T6 | [verification.json](evidence/estaciones/cierre-t6/verification.json) |

Descomprimir el paquete Godot conservando las carpetas `godot/` y `portable/`.
Abrir `godot/project.godot` con Godot 4.7.2 y ejecutar. El visor permite escoger
cuatro casos, normales .35/originales, fase, pausa, retroceso, órbita y suelo;
los cinco modos comparan calendario, mezcla uniforme, verano, otoño y tinte
histórico. Arrastrar gira; rueda acerca; R restablece cámara.

Los extremos estándar están en
`portable/cases/<id>/{summer,autumn}-{selected,original}.glb`:
`selected` usa .35; `original` conserva las normales iniciales. Cada GLB embebe
dos PNG y se puede importar por separado. `portable/manifest.json` registra
semillas, versión, calendarios, campos, rutas y hashes. La transición entre
pinturas requiere el adaptador; no hay animación glTF ni exportación estática
de fases intermedias a un atlas único. UV2 contiene inicio/duración del calendario,
no lightmap. [API e integración](contrato-integracion-estacional.md).

## Resultado y verificación de cierre

Cuatro casos: **6812/3132/5820/6900 triángulos**, 264 grupos/792 láminas y dos
materiales por árbol. Materiales compartidos y tres texturas de hasta 2000².
T5: 194 pruebas, 16 extremos Blender/Godot, 2377 capturas más cuatro en copia
limpia; reversión, extremos y máscaras exactos bajo el protocolo.
[Informe, revisión visual y límites T5](evidence/estaciones/integracion-t5/informe.md).

T6 comprueba hashes de fuentes/entradas, catálogo histórico, proyecto, extremos,
2377 PNG y ZIP; verifica las decisiones contra sus informes congelados. Archiva
**266 archivos** de fuentes y entradas. Extrae ese ZIP en carpeta temporal y
ejecuta el constructor con límite de 120 s y sin `PYTHONPATH` heredado: manifiesto,
proyecto y 16 extremos iguales a T5. Esta prueba es de reconstrucción y entrega;
la validación visual nativa es la de T5, conservada por hash. No se vuelven a
presentar nuevas capturas ni pruebas unitarias por un cambio de documentación.

El primer archivo de fuentes ensayado omitía dos pinturas históricas que valida
T1; la reconstrucción aislada lo rechazó. La entrega `cierre-t6-02` las incluye y
pasa. No se modifica el paquete ni el manifiesto T5 para cerrar T6.

## Reproducir

Desde este repositorio, con entradas T1/T2/T4/T5 disponibles:

```sh
python3 scripts/close_season_transition.py --output artifacts/estaciones/otro-cierre-t6
```

El cierre requiere carpeta nueva. Comprueba integridad, empaqueta fuentes y prueba
reconstrucción, sin ejecutar Blender/Godot. `--trial` permite elegir otra salida
T5 cuya verificación coincida con la evidencia seleccionada. Un nuevo ensayo T5
requiere su evidencia correspondiente; no se elige “latest”.

Para reconstruir desde `fuentes-y-entradas-t5.zip`, extraerlo y ejecutar desde
su raíz, con Python y las dependencias de `requirements.txt` instaladas:

```sh
python3 scripts/build_season_bundle.py --output rebuilt
# Opcional: repetir la revisión nativa sobre la reconstrucción.
BLENDER_BIN=/ruta/a/blender GODOT_BIN=/ruta/a/godot python3 scripts/verify_season_bundle.py --output rebuilt --stage review
python3 scripts/season_bundle_evidence.py --output rebuilt
```

Blender 5.2.1 LTS y Godot 4.7.2 fueron los motores comprobados. No se incluyen
los ejecutables ni dependencias Python dentro del archivo. La copia reproduce T5
**desde referencias congeladas**, no rehace toda la historia T0–T4 ni constituye
un snapshot completo de todos los experimentos del repositorio.

## Decisión de continuación

Conservar la variante explícita aprobada y los controles originales; recetas/alias
históricos intactos. La aprobación artística no acredita mejoras de FPS.
La próxima fase posible sería un **estudio separado de caída del roble**:
granularidad por grupos, máscaras internas, conexiones visibles y presupuesto de
madera con copa parcial. Su alcance requiere decisión del usuario; este cierre
no inicia esa fase. Caída, invierno, brotación, marcescencia, partículas, viento,
LOD y otras especies siguen fuera de esta entrega.
