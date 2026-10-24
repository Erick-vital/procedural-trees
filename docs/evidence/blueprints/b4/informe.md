# B4: segundo blueprint y reutilización comprobada

Fecha: 2026-10-23. **Implementado y verificado técnicamente**, con revisión de
capturas reales de Godot. Segundo tipo artístico: **Árbol estilizado de copa
columnar**, `arbol_copa_columnar` 1.0.0. Sigue experimental: no se atribuye a una
especie botánica ni se registra una aprobación artística del usuario.
B5 y el lote RF5 no se han iniciado.

## Objetivo fijado y resultado

Antes de generar se fijaron el [objetivo](../../../blueprints/b4-objetivo.md),
el [boceto conceptual propio](../../../blueprints/columnar-concepto.svg), los
parámetros y las semillas. Referencia de contraste: viejo-09 aprobado.
El boceto orienta proporciones; no se presenta como geometría ya generada.

La receta combina tronco esbelto, doce ramas primarias ascendentes a 18° desde
la vertical, secundarias y una copa alargada. Altura 12 m, radio .22 m,
proporción de longitud .22 y asimetría .12. Trescientas conexiones con seis
rombos nominales de .45 m, con planificación de .45 m. Paleta, sombreado e
iluminación iguales al primer tipo. No se estrecha una malla final de copa ancha:
las proporciones proceden de la estructura y sus guías antes de colocar hojas.

[Comparación con el primero](identity.jpg), [misma semilla](same-seed.jpg),
[madera sin hojas](wood-comparison.jpg), [cuatro controles](controls.jpg),
[escalas](scales.jpg).

La revisión visual muestra una identidad distinta en las cuatro semillas:
ramas orientadas hacia arriba, tronco largo y delgado y follaje concentrado
alrededor del eje vertical. Se conserva esa diferencia sin hojas y con la
misma semilla en ambos tipos. El piloto tiene dos agrupaciones visibles y un
estrechamiento intermedio; los controles varían la continuidad y los lóbulos.
El extremo superior se recoge de forma irregular, no reproduce exactamente el
boceto. Persisten agrupaciones densas, hojas angulosas y solapamientos en zonas.
A distancia disminuye la lectura de cada hoja, pero permanece la silueta vertical.
No se eligió un ganador estético ni se cambió el tipo predeterminado.

## Qué se reutilizó

| Capa | Reutilización |
| --- | --- |
| Contrato, catálogo y resolución | TreeBlueprint/TreeInstance 1.0 y registro por carpeta existente |
| Madera y moldes invisibles | `oak_geometry_nodes@0.4.0`, mismos grafos Q3 |
| Distribución y contactos | `foliage-canopy@0.1.1`, mismo muestreo, reparto y proyección acotada |
| Unidad de follaje | `rf3-diamond-six@0.1.0`, seis rombos opacos por conexión |
| Ejecución | CLI `generate-blueprint`, `execute_blueprint`, timeout y manifiestos comunes |
| Exportación y evaluación | Adaptador Blender 1.1.0, GLB, reimportación de contactos y verificador Godot existentes |
| Apariencia | Exactamente los mismos valores de corteza y hoja de `roble_copa_ancha` 1.2.0 |

**No se añadió ni modificó código de producción geométrica, resolución o
adaptadores para B4.** Se añadieron la receta, peticiones, matriz, pruebas de
contrato y herramientas de evaluación del experimento. El catálogo descubre
la receta nueva sin una rama condicional por su identificador.
Las fuentes/recetas permanecieron iguales entre comienzo y fin del ensayo;
la conservación se comprueba también contra los hashes seleccionados de B3
([auditoría de 16 archivos previos](reuse-audit.json)).
No se copió el algoritmo bajo el nombre de otra especie ni se creó un ejecutor
alternativo de trabajos.

Esto demuestra reutilización para una arquitectura columnar expresable mediante
los componentes Q3/RF3 actuales. No prueba cobertura de cualquier árbol,
organización de ramas, representación de hojas o especie.

## Casos congelados y resultados

Semillas base **4100/4101/4102/4103**, la primera como piloto y las otras tres
como controles fijados antes de generar. Semilla de copa **73** para todas.
Un perfil `columna`, sin cambios del ejemplar ni arreglos por semilla.
No hubo ajustes después de inspeccionar estos controles.

| Caso | Semilla base | Anchura X / altura | Anchura Y / altura | Triángulos |
| --- | ---: | ---: | ---: | ---: |
| Piloto | 4100 | .3755 | .4205 | 11756 |
| Control 01 | 4101 | .3835 | .3637 | 11756 |
| Control 02 | 4102 | .3650 | .3700 | 11756 |
| Control 03 | 4103 | .4040 | .3595 | 11756 |
| Copa ancha, misma semilla | 4100 | 1.4656 | 1.6615 | 10572 |

Los cuatro casos cumplen el diagnóstico **≤.5** fijado antes de generar,
y la madera sola también lo cumple: ratios X/Y entre .1748 y .2538.
Los cuatro GLB y las cuatro maderas tienen hashes distintos: hay variación
controlada, no cuatro copias del mismo modelo. Las proporciones son medidas
geométricas; no sustituyen la revisión de identidad visual.

La extensión del follaje del piloto columnar es aproximadamente
**4,51 × 5,05 × 6,36 m**; con la misma semilla, la copa ancha ocupa
**13,19 × 14,95 × 7,43 m**. Son cajas de las hojas, no simulaciones botánicas
ni medidas de naturalidad. El nuevo árbol completo mide 12 m, con tolerancia
de altura de .0001 m.

Por caso columnar: **49 piezas de madera, 300 conexiones, 1800 hojas,
11756 triángulos y tres materiales**. Desglose: 5756 de madera, 2400 de
conexiones y 3600 de hojas. Moldes invisibles excluidos del GLB.
Cota previa idéntica al coste final, por debajo de 12500.
Las peticiones editables limitan a 337 grupos: cota contractual de 12496;
338 se rechaza. Ese extremo se prueba al resolver, no se declara verificado
geométricamente en este experimento.

## Validación y conservación del primero

- **83 pruebas** correctas, incluidas tres nuevas sobre reutilización de
  componentes/paleta, parámetros comunes entre semillas y frontera de presupuesto.
  [Salida de pruebas](unit-tests.txt).
- **Diez generaciones válidas**, sin casos fallidos: cuatro columnarios,
  sus cuatro repeticiones, referencia aprobada del primero y copa ancha con
  semilla 4100. Veintisiete comprobaciones del verificador correctas;
  matriz `passed=true`.
- Las **cuatro repeticiones son idénticas byte por byte** a sus casos respectivos.
  El primer blueprint 1.0.0 se regeneró y produjo el **GLB idéntico a B0 aprobado**.
- Los diez GLB se reimportaron en Blender y comprobaron inserciones sobre la
  madera exportada. Error máximo de los cuatro nuevos: **.000006723 m**,
  dentro de la tolerancia .0001 m. En toda la matriz, incluida la referencia
  histórica, máximo .000093077 m. [Contactos](export-contacts.json).
- Las consultas de proyección de los cuatro casos nuevos no requirieron
  correcciones. Intentos por caso: 316/316/321/310 de un máximo de 2048;
  todos conservan pool acotado de 8192 muestras.
- **Doce GLB en Godot**: seis copas únicas y sus seis derivados de madera;
  escala, ejes, triángulos y materiales comprobados. **108 capturas reales**,
  nueve por escena, en lotes de dos. Todas no vacías y con al menos 196 píxeles
  de fondo hasta el borde. Revisión visual del asistente sobre las láminas seleccionadas.
- Una cámara común por vista y la misma escala física para todos los modelos,
  incluida la madera desnuda; misma luz y resolución 900×900. Las vistas generales
  se ajustan a la caja conjunta, no a cada silueta. `near/medium/far` usan escalas
  comunes ×1/×2/×5. [Protocolo y métricas](verification.json).
- Generación columnar sin render Blender: **3,341–3,444 s**; GLB
  **492292–494076 bytes**. No se han medido FPS, viento, LOD ni bosque.

Los manifiestos incluyen receta y hash, petición, perfil, semillas, parámetros,
versiones de componentes/adaptador y hashes de fuentes. La generación declara
`external_geometry_inputs=[]`: no usa GLB/Blend previos como entradas.
La referencia B0 interviene como comparación, no como geometría para generar.
[Procedencia seleccionada](generation-provenance.json).

## Reproducción y límites

```sh
PYTHONPATH=src python3 -m treegen generate-blueprint blueprints/arbol_copa_columnar/1.0.0.json --instance presets/blueprints/columnar/pilot.json --output artifacts/blueprints/otro-columnar --no-render
python3 scripts/verify_second_blueprint.py --output artifacts/blueprints/otro-b4 --visual
python3 scripts/second_blueprint_evidence.py --study artifacts/blueprints/otro-b4 --output artifacts/blueprints/evidencia-b4
```

Usar carpetas nuevas. Mismos Blender 5.2.1/Godot 4.7.2 de B2/B3;
generación ≤120 s y pruebas/capturas ≤180 s por subproceso terminable.
Fuera del sandbox cuando este bloquee API loopback, audio o interfaz.
Sin `--visual` no se generan las láminas para el tercer comando.

Resultado local: `artifacts/blueprints/b4-columnar-01/index.html`.
Piloto: `artifacts/blueprints/b4-columnar-01/pilot/tree.glb`.
Fuente del diseño y matriz anteriores al ensayo: [objetivo](../../../blueprints/b4-objetivo.md)
y [peticiones congeladas](frozen-matrix.json).

B4 tiene salida técnica y revisión visual de identidad; falta decisión artística
del usuario antes de promover el tipo. Solo se verifica el perfil de 12 m y
estos cuatro pares de semillas: otras edades, todo el rango editable y otras
arquitecturas siguen sin evaluarse. B5 y la decisión de lote permanecen separados.
