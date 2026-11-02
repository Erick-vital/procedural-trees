# Estaciones — primer roble de otoño

Fecha: 2026-11-01. Ampliación de alcance solicitada por el usuario: comenzar un
sistema reutilizable de estaciones y crear una versión otoñal del roble.
Plan inicial de ese trabajo; el abedul queda pendiente de valoración.

Continuación vigente de planificación: [transiciones pintadas y normales de copa](transiciones-estacionales.md),
solicitada el 2026-11-01 tras estudiar just-a-simple-tree. T0/T1 autorizadas
posteriormente, implementadas y verificadas; T2 también solicitada y verificada;
T3 aprobada artísticamente y T4 .35 seleccionada por delegación el 2026-11-02;
T5 integrada/verificada como candidata 0.1.0 y T6 cerrada técnicamente;
aceptación artística del conjunto aprobada posteriormente:
[decisión](../docs/evidence/estaciones/cierre-t6/user-acceptance.json). [Entrega](../docs/entrega-transiciones.md). Este documento
conserva antecedentes y resultados del primer otoño.

Primera entrega: variante Godot del roble pintado 2.2.0, con la pintura aprobada,
sin nuevas texturas ni cambios de geometría. Transformación estacional mediante
shader, dos materiales y <7000 tris; copa llena de otoño medio, sin simular caída.
La pintura original, sus alfas y la corteza permanecen en los recursos originales.
La aplicación estacional queda pendiente de aceptación artística del usuario.

Separar motor de color reutilizable (paleta, intensidad, manchas continuas,
semilla explícita) de perfil de especie (material objetivo, tonos, verde residual,
escala de variación y fase admitida). No aplicar otoño de roble automáticamente
a pinos ni afirmar reglas botánicas universales. Este roble es una familia
artística sin identificación taxonómica que certifique una fenología concreta.

Conservar recetas históricas. Empaquetar escena Godot reutilizable y visor con
comparación verano/otoño; GLB base intacto y autocontenido, shader externo necesario
para el otoño. No presentar ese GLB verde como exportación otoñal independiente.
Validar perfil, procedencia, presupuesto real importado, dos materiales, recursos,
determinismo, alfa/sombras y varias vistas/distancias en piloto y tres controles.

Siguientes fases solo tras decidir su alcance: caída por grupos con reglas de
especie, marcescencia, invierno, brotación, atlas estacionales exportables a GLB.
Sin viento, LOD, bosque ni benchmark en esta entrega.

## Primera entrega verificada

Perfil 1.0.0 y escena Godot implementados. Cuatro casos de 3132–6900 tris y dos
materiales, GLB originales exactos, siete pruebas y 19 comprobaciones pasan.
64 capturas reales; piloto, controles y distancias inspeccionados en selección.
Paquete y render repetidos idénticos. [Informe](../docs/evidence/estaciones/roble-otono-01/informe.md).
Siguiente paso: valoración artística de esta variante; caída y otras estaciones
siguen fuera de la implementación actual.

## Comparación desde pintura autorizada — 2026-11-01

El usuario pide conservar el shader como experimento, guardar primero un commit
y hacer el cambio desde pintura para comparar resultados. Punto de restauración
**4187776**, anterior a esta nueva pintura, incluye el estado pendiente del abedul.
Se autoriza una variante experimental aplicada al mismo roble para comparación;
no se adopta en producción ni se atribuye aprobación artística a la nueva pintura.

Editar con ImageGen las cuatro hojas fuente aprobadas: ocres, cobre, dorados,
verdes residuales y detalles secos pintados; conservar disposición y carácter
lobulado. Rehornear las ocho plantillas existentes sin cambiar madera, láminas,
UV o anclajes; registrar cualquier diferencia de contorno/alfa causada por la
nueva pintura. Exportar GLB con atlas embebido y material estándar, sin shader
estacional. Conservar corteza y recursos históricos. Comparar pintura, verano y
shader con igual cámara/luz, primero piloto y luego tres controles; <7000 tris
y dos materiales. Nueva pintura/recurso versionados con prompt y procedencia.

Comparación implementada: pintura/atlas 0.1.0, cuatro GLB otoñales con material
estándar y textura embebida, geometría/UV/normales exactos. Seis pruebas, 26
comprobaciones y 132 capturas Godot; rehorneado RGBA repetido idéntico. Selección
visual revisada; alfa cambia levemente, cobertura de árbol <+.4 % en tres vistas.
[Informe y reproducción](../docs/evidence/estaciones/roble-pintura-01/informe.md).
Shader conservado experimental; pintura/aplicación nuevas pendientes de aceptación.
