# R2: rama completa frente a madera oculta simplificada

Fecha: 2026-11-03. **Comparación verificada; R2 elegida también sin follaje por el usuario.**
El usuario valora positivamente la ramificación R1 y solicita conservar la copa
y las ramas que se alcanzan a ver al simplificar. [Alcance](../../../../plans/f5-estructura-espacial.md),
[valoración de R1](../rama-r1/user-review.json).

## Resultado

[Comparación breve](comparacion.jpg), [cerca](near.jpg), [media](medium.jpg),
[lejos](far.jpg), [sin follaje](wood.jpg), [madera visible en rojo](visible-wood.jpg),
[giro 1](orbit-0.jpg), [giro 2](orbit-1.jpg), [sombras](shadows.jpg),
[máscaras de copa](masks.jpg), [auditoría](verification.json).
Galería local: `artifacts/f5/rama-r2-03/index.html`.
En todas las láminas: **completa a la izquierda, simplificada a la derecha**.

| Componente | Completa R1 | Simplificada R2 | Ahorro |
| --- | ---: | ---: | ---: |
| Eje principal | 140 | 140 | 0 |
| Red de ramillas | 1038 | 754 | 284 |
| Madera total | 1178 | 894 | 24,11 % |
| Follaje | 522 | 522 | 0 |
| **Rama completa** | **1700** | **1416** | **16,71 %** |

Se conservan dos materiales y los atlas originales. De 171 tramos de red se
retienen 113 y se eliminan 58 completamente ocluidos según el protocolo.
Se preservan exactamente los tramos expuestos, sus ancestros y los tres
nacimientos, sin cambiar sus vértices, caras o UV. El eje principal queda intacto.
No se retoca la forma de la madera que sí se conserva.

**87 grupos / 261 láminas de follaje intactos**: mismas posiciones, caras, UV,
normales, plantillas y pintura. Dos controles de follaje aislado producen GLB
binariamente idénticos; seis pares de máscaras Godot son idénticas.
El GLB completo de referencia reproduce exactamente el `candidate` de R1.
La madera simplificada exportada es un subconjunto exacto de las caras/UV de R1.

## Cómo se selecciona la madera

`branch-visibility-prune-0.1.0`, sin nuevo azar; conserva semillas y procedencia
R1 (base 1003, copa 17, pintura 2718). Usa sus geometrías y alfa congelados.
El clasificador `alpha-bvh-visibility-0.1.0` lanza rayos desde vértices,
centros de caras y fracciones de aristas de la madera hacia las láminas cruzadas.
La oclusión considera el alfa real interpolado sobre los triángulos y cuatro
texeles vecinos. Exige alfa ≥217/255 para usar una hoja como oclusor, siendo
conservador respecto al corte de representación .5. Las consultas inciertas o
truncadas conservan madera; no trata una caja opaca como si fuera todo el follaje.

Son 38 direcciones iniciales (doce azimuts por tres elevaciones más arriba/abajo)
y otras 36 direcciones intermedias que también actúan como salvaguarda. Se detectan
53 tramos expuestos inicialmente y se protegen otros 11 al comprobar las direcciones
intermedias. Estas 36 direcciones intervienen en la selección: no se presentan
como validación reservada independiente. Después se conservan todos los ancestros
necesarios; así la poda no deja ramillas visibles separadas de su eje principal.

Solo se eliminan subárboles sin exposición detectada. Desaparecen 45 extremos
ocultos; quedan 42 conexiones terminales de madera para 87 grupos, con toda la
geometría de hojas conservada. Por diseño, **R2 está pensada para copa llena**.
La estructura descubierta deja de representar cada soporte de la versión completa.
No es una solución para invierno, pérdida de hojas o movimiento del follaje.

## Verificación geométrica y visual

- **231 pruebas** correctas; dos pruebas R2 comprueban protección de ancestros,
  geometría retenida, determinismo, raíces, IDs inválidos y ciclos.
- **Tres casos analíticos en Blender**: una caja opaca oculta madera interior;
  la misma caja transparente no la oculta; cobertura incierta conserva madera.
- **23 comprobaciones de integración** correctas: cuatro GLB auditados y cuatro
  repeticiones binariamente idénticas; referencia R1 exacta; caras de madera como
  subconjunto exacto; follaje/texturas; máscaras y protección de madera visible.
- **26 parejas de máscaras de madera visible idénticas**: cero píxeles rojos
  perdidos o ganados. Cada referencia tiene 274–18 412 píxeles de madera, de modo
  que la comprobación no es vacía. Incluye cerca/media/lejos, seis orientaciones
  y ocho posiciones de giro desde abajo con azimuts distintos del clasificador.
- En las **26 parejas con materiales normales**, 25 imágenes son idénticas. Solo
  `orbit-04` cambia **un píxel de 810 000**, diferencia máxima de canal 13/255.
  No se observa una diferencia de copa o de lectura de ramas en las láminas.
- **Tres parejas de sombra proyectada en suelo** idénticas con luces distintas,
  encuadrando la proyección completa de la referencia. Sombras propias activadas
  en los pases con materiales normales. Mismos ajustes por pareja.

Se han generado **140 capturas finales**: 134 del protocolo principal y seis de
sombras encuadradas. Se conservaron además seis capturas preliminares de sombras
con encuadre menos adecuado; no forman parte de esas 140 finales. El agente
inspeccionó una selección de **94 capturas únicas** en las láminas enlazadas,
no todas las capturas como inspección exhaustiva. Los recuentos de píxeles
cubren todas las comparaciones declaradas arriba.

En rojo se muestra solo la madera que queda visible a través de la copa; el
follaje blanco conserva su alfa real. Es un shader auxiliar de diagnóstico,
no modifica los materiales exportados. Las vistas cercanas amplían el detalle y
recortan intencionalmente algunos bordes; las vistas media/lejos y las máscaras
permiten examinar la rama y la copa completas. Cámara/luz/escala idénticas dentro
de cada pareja, sin autoencuadrar por separado la versión simplificada.

La silueta y plenitud del follaje permanecen iguales. Bajo la copa se mantiene el
eje visible, y por los huecos se conserva la madera muestreada. Sin hojas se aprecia
la reducción de las ramillas más finas dentro del volumen de copa. El resultado
es una candidata adecuada para valorar su uso con copa llena; su aceptación
artística corresponde al usuario, sin deducirla de la similitud de imágenes.

## Reproducción y límites

Requiere la muestra R1 en `artifacts/f5/rama-r1-03/`; si falta, seguir la
[reproducción R1](../rama-r1/informe.md). Desde la raíz, con una carpeta nueva:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
python3 scripts/verify_branch_simplification.py --stage generate --output artifacts/f5/otra-rama-r2
python3 scripts/verify_branch_simplification.py --stage review --output artifacts/f5/otra-rama-r2
python3 scripts/branch_simplification_shadows.py --study artifacts/f5/otra-rama-r2
```

`generate` congela la referencia R1, alfa y matriz de cámaras antes de clasificar;
registra selección, grupos, fuentes/hashes y repite los GLB desde el mismo trabajo.
La generación usa procesos terminables de 120 s; cada revisión Godot, 180 s.
No hay llamadas nuevas a modelos ni un proveedor adicional. Semillas y recetas
históricas no cambian. `.blend`, GLB, entradas completas y capturas se conservan
localmente en el resultado, fuera de la evidencia seleccionada del repositorio.

Pruebas alfa analíticas: ejecutar con Blender
`blender/verify_branch_visibility.py -- DIRECTORIO_NUEVO`; el script requiere
Blender y escribe sus tres casos/resultados. Selección de evidencia:
`scripts/branch_simplification_evidence.py --study RUTA --output DESTINO`, con
la suite guardada en `logs/tests.log` y los resultados analíticos en
`artifacts/f5/rama-r2-alpha-tests/`. Fuentes, matriz, alfa y capturas seleccionadas
tienen hashes en la auditoría. `visibility.json` conserva testigos de exposición.

Intentos: R2-01 fue una exploración de clasificación; R2-02 generó la misma selección
y primera comparación. R2-03 mantiene la geometría y añade el recuento RGB exacto
y la comprobación estricta de máscara de madera visible. El encuadre auxiliar de
sombras se corrigió para incluir sus extremos y se conservaron las capturas previas.
No se reajustó la selección tras observar las imágenes de giro ni para forzar ahorro.

La visibilidad es un muestreo finito de **una rama de una semilla**; no garantiza
invisibilidad universal ni el mismo ahorro en otras copas, filtros, distancias,
luces o estados de follaje. No se extrapola el −16,71 % a un árbol completo.
No se integran árboles nuevos ni se inicia F6; no hay benchmark de FPS.
R1 completa queda conservada. Siguiente: valorar esta comparación antes de ampliar
la simplificación al árbol completo con controles por edad/semilla.


## Decisión posterior de uso — 2026-11-03

El usuario [elige R2 también sin follaje](user-acceptance.json), al considerar
pequeña la diferencia descubierta. Se amplía así el uso artístico inicialmente
propuesto, sin modificar los resultados congelados ni certificar otros casos.
Posteriormente solicita mayor reducción con follaje: [R3](../rama-r3/informe.md)
entrega R2 como asset desnudo explícito y una nueva variante más reducida con copa.
