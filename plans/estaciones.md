# Estaciones — primer roble de otoño

Fecha: 2026-11-01. Ampliación de alcance solicitada por el usuario: comenzar un
sistema reutilizable de estaciones y crear una versión otoñal del roble.
Este es el plan activo para ese trabajo; el abedul queda pendiente de valoración.

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
