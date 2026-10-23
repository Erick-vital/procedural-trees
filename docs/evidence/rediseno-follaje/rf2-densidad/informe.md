# RF2: aumento de hojas con techo de 12500 triángulos

Fecha: 2026-10-23. El usuario expresa gusto por el ensayo de moldes, solicita
algo más de volumen y eleva el máximo del rediseño a **12500 triángulos por
árbol**, conservando tres materiales. Ensayo `foliage-molds-0.1.2`, implementado
y verificado; revisión de capturas reales realizada. RF3 sin iniciar.

El usuario aprueba el 2026-10-23 la recomendación de **144 hojas** como
referencia de rama para RF3. [Aceptación vinculada al GLB, manifiesto y
parámetros](aceptacion.json). Esta decisión posterior a la ejecución actualiza
la elección visual; el resumen técnico conserva el estado que tenía al generarse.

[Comparación de densidades](density.jpg), [ángulos](angles.jpg),
[escalas](scales.jpg), [máscaras](masks.jpg), [resumen](summary.json),
[45 pruebas](unit-tests.txt), [preset 144](density-144-spec.json) y
[preset 192](density-192-spec.json).
Galería completa: `artifacts/rediseno-follaje/rf2-densidad-01/index.html`.
Modelos `<caso>/branch.glb`, escenas `<caso>/scene.blend`.

## Comparación y coste

Se mantiene el rombo de tamaño nominal 1 m, los nueve moldes Q3 invisibles,
la semilla 17 y las 24 conexiones del candidato anterior `efficient-100`.
Las **96 hojas originales se conservan exactamente**: ids, raíces, ejes,
tamaños y geometría. Las nuevas se añaden por rondas de grupos ordenados por
hash, con ids propios. Aumentar cantidad conserva también las adiciones previas.
Las raíces nuevas quedan dentro de los tubos, sin madera añadida adicional.

| Hojas | Aumento | Triángulos de hojas | Total de rama¹ | Proyección de árbol² |
| --- | ---: | ---: | ---: | ---: |
| 96 | Base | 192 | 848 | 9516 |
| 120 | +25 % | 240 | 896 | 10044 |
| 144 | +50 % | 288 | 944 | 10572 |
| 192 | +100 % | 384 | 1040 | 11628 |

¹ Incluye 464 de madera Q3 y 192 de conexiones, idénticas en los cuatro casos.
² `5292 + 11 × (conexiones + hojas)`, proyección aritmética para viejo-09;
ninguna es una copa completa generada. El nuevo techo permite 655 triángulos
añadidos por rama en esa distribución uniforme; sobre estas conexiones caben
hasta 231 hojas antes de superar la cota. Se ensaya hasta 192 para evaluar el
efecto de compactación, sin agotar el presupuesto.

La madera Q3, materiales, luces y doce cámaras son las mismas del
[ensayo anterior](../rf2-moldes/informe.md). Las escalas siguen siendo
ortográficas 50/25/10 % de la rama Q3, con detalles recortados deliberadamente.
No se agrandan las hojas existentes ni se mueve su distribución para tapar
huecos. Los moldes siguen excluidos del GLB.

## Cobertura y revisión visual

Máscaras de follaje a 256×256 calculadas desde el GLB final, con cámaras comunes
y sin oclusión de madera. El porcentaje es área proyectada de Q3 coincidente
con hojas, no volumen ni aceptación artística. Se conservan IoU y área fuera
de Q3 en el resumen.

| Hojas | Frente | Lateral | Arriba | Abajo | Oblicua | Reverso |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 96 | 57.5 % | 63.4 % | 54.2 % | 58.6 % | 64.1 % | 64.1 % |
| 120 | 66.9 % | 69.7 % | 60.5 % | 65.6 % | 71.2 % | 71.2 % |
| 144 | 74.4 % | 75.1 % | 64.6 % | 71.9 % | 75.5 % | 75.5 % |
| 192 | 83.8 % | 81.2 % | 73.6 % | 77.3 % | 84.2 % | 84.2 % |

Se revisaron las capturas Godot de las cuatro densidades desde ángulos
generales, detalles superiores/inferiores y las tres escalas. 120 aporta un
aumento moderado; 144 cierra más huecos conservando separación entre grupos.
192 tiene mayor presencia y tapa más madera, pero acumula más láminas en
detalle y resulta más compacto. La forma grande y angular de las hojas sigue
presente; añadirlas no cambia esa representación.

**Variante aprobada: 144 hojas**, tras la recomendación para el aumento pedido;
192 se conserva como alternativa comparada, sin selección. No se cambia el
generador predeterminado ni se declara aceptada una copa completa. Sigue RF3:
asignar coste por región y considerar interiores entre todas las masas del árbol.

## Verificación y reproducción

Pasaron **45 pruebas**, incluidas dos nuevas para adición anidada, raíces,
ejes, preservación de hojas/conexiones y extremos del nuevo presupuesto.
**Nueve GLB** válidos e importados en Godot; la reconstrucción de 96 hojas
coincide con la versión 0.1.1 y con el resultado histórico. Las variantes 144
y 192 se repiten en sesiones Blender independientes con geometría idéntica.
Otra semilla cambia distribución sin alterar la madera Q3.

Se verifican hashes de la base, polígonos/sombreado, transformación y corteza;
posiciones/normales exportadas por canal; misma geometría de conexiones y
propiedades de materiales en las densidades. Las raíces nuevas se comprueban
en la malla real de sus tubos. El máximo error de inserción es .000343 mm.
Toda la geometría queda entre Z=0 y Z=9 m, sin renormalizar la base.

Cinco escenas × doce vistas: **60 capturas Godot**, todas con geometría visible
(mínimo 5789 píxeles según el detector). Entorno fijado: Blender 5.2.1 LTS
`9e2066aef7ef`, Python Blender 3.13.13, ejecutor 3.14.4 y Godot 4.7.2
`ed1daf0bf`. GLB de 36–47 kB; generación antes de render/exportación .08–.10 s
para las cuatro densidades, sin incluir arranque, Godot ni ajuste humano.
No se mide rendimiento durante el juego.

```sh
python3 scripts/verify_foliage_molds.py --density --output artifacts/rediseno-follaje/otra-densidad --visual
python3 scripts/foliage_molds_evidence.py --study artifacts/rediseno-follaje/otra-densidad --output artifacts/rediseno-follaje/evidencia-densidad
```

Usar una carpeta nueva. `--preset` permite otro contrato exterior 0.1.2; la
matriz fija sus cantidades y semillas. Generación ≤120 s, Godot/verificaciones
≤180 s por proceso terminable y lotes de dos escenas, sin reintentos automáticos.
Sin `--visual` se verifican geometría/importación, sin capturas para seleccionar
evidencia. Las fuentes ejecutadas de 0.1.1 se preservaron en
`artifacts/rediseno-follaje/rf2-moldes-final/sources/` antes de adaptar el flujo
compartido. Las versiones históricas conservan su techo de 10000; el nuevo
12500 está versionado para este rediseño. La integración normal sigue en RF5.
