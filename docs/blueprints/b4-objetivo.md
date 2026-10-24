# B4: objetivo congelado del segundo blueprint

Fecha: 2026-10-23. Fijado antes de generar el piloto.
Autorización: el usuario solicita continuar B4 del plan de blueprints.
Esto habilita el segundo tipo artístico previsto, conservando el primer tipo.
No inicia B5, especies botánicas, lote RF5, bosque ni optimización geométrica.

## Identidad y referencias

**Árbol estilizado de copa columnar**, identificador `arbol_copa_columnar`.
Referencia de diseño propia: [boceto conceptual](columnar-concepto.svg), creado
para este experimento, sin fotografía ni atribución a especie real.
Referencia de contraste: viejo-09 aprobado, `roble_copa_ancha` 1.0.0,
[adopción B0](../evidence/blueprints/b0/informe.md) y
[vistas reales del primer tipo](../evidence/blueprints/b3-revision/overview.jpg).
El boceto expresa proporciones e intención; no es evidencia de geometría generada.

Objetivo: tronco esbelto y casi recto, ramificación ascendente y copa estrecha,
vertical y con un extremo superior más recogido. Las hojas deben leerse como
follaje facetado y conservar huecos en detalle. No se busca una copa esférica,
una sombrilla ni reproducir exactamente el dibujo.

Primer intento mediante datos existentes: altura 12 m, radio .22 m, curvatura
.025, doce primarias a 18° desde la vertical, profundidad dos, proporción de
longitud .22 y asimetría .12. Moldes Q3 .65 m/densidad .75; 300 conexiones
con seis hojas nominales de .45 m; planificación .45 m; pesos uniformes.
Paleta y propiedades de corteza/hojas idénticas al primer blueprint.
No se cambia el algoritmo ni se aplana una copa ancha con una transformación final.

## Protocolo y salida

- Piloto: semilla estructural 4100. Controles fijados: 4101, 4102 y 4103.
  Semilla de copa común 73. Mismos parámetros y perfil para los cuatro.
- Identidad esperada: anchura/altura de malla final ≤.5 en X y en Y en los
  cuatro casos, acompañada de revisión Godot de estructura desnuda y copa.
  Esta proporción es diagnóstico de la identidad propuesta, no estética automática.
- Comparar también con el primer blueprint usando la misma semilla 4100,
  y con viejo-09 aprobado. Misma paleta, cámaras/luz compartidas por comparación.
- Hasta 12500 triángulos/3 materiales, 8192 muestras y 2048 intentos.
  Cota prevista: 5756 de madera + 6000 de conexiones/hojas = 11756 triángulos.
- Repetir los cuatro casos, verificar GLB y contactos reimportados, escala y
  materiales Godot, y regenerar la referencia del primer tipo. No ajustar
  semillas reservadas después de inspeccionarlas ni presentarlas como nuevas
  reservas en una revisión posterior.
- Si los componentes no expresan esta arquitectura, conservar fallos y limitar
  la ampliación a la estrategia necesaria, con versión y nueva regresión del primero.

Receta y peticiones: `blueprints/arbol_copa_columnar/1.0.0.json` y
`presets/blueprints/columnar/`. Matriz: `configs/verification/b4-v1.json`.
Estado al fijar este objetivo: planeado; resultados pendientes de generar/revisar.
