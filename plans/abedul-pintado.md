# Abedul pintado — propuesta inicial

Fecha: 2026-10-26. Nueva especie solicitada por el usuario después del roble y
del pino. Alcance autorizado actual: **pintura y rama aprobadas; árbol completo
integrado y verificado, aceptación artística pendiente**. Aplicar la [política de nuevos árboles](../docs/politica-arboles-optimizados.md).

## Dirección propuesta

Pincelada amplia y mate, coherente con los árboles aprobados. Hojas pequeñas
triangulares/rómbicas, puntiagudas y dentadas, verdes musgo/salvia con acentos
amarillo verdoso contenidos. Corteza blanco marfil con variación gris/beige,
marcas horizontales oscuras discontinuas y nudos escasos. Ramillas finas con
extremos algo caídos y copa ligera con huecos legibles.

La lámina incluye árbol ilustrado, ramilla, hojas aisladas y muestra de corteza
para juzgar la pintura. No define geometría exacta, densidad, escala final de
hoja ni arquitectura de ramificación aprobadas.

## Resultado y siguiente paso

[Propuesta de pintura](../docs/evidence/abedul-pintado/pintura-01/ficha.md)
aprobada; [aceptación y autorización de la rama](../docs/evidence/abedul-pintado/pintura-01/user-acceptance.json).
Atlas RGBA con cuatro ramillas y corteza generados con ImageGen, recursos 0.1.0;
PNG sin retoques, fuente/prompt/procedencia conservados. Rama aislada 0.1.1 con
siete grupos de tres planos cruzados inclinados, 382 tris totales/2 materiales.
Tres pruebas pasan, GLB repetido idéntico y reimportado en Blender/Godot;
35 capturas reales revisadas y visor interactivo preparado.
[Resultado y reproducción](../docs/evidence/abedul-pintado/rama-01/informe.md).

Rama aceptada posteriormente; [aceptación y continuación](../docs/evidence/abedul-pintado/rama-01/user-acceptance.json).
Siguiente paso: valoración del árbol completo, ya implementado como se detalla
al final. No iniciar nuevas edades o fases adicionales por su entrega.

La futura representación deberá usar cruzadas, pintura de estilo manual,
máximo dos materiales y menos de 7000 triángulos totales. La ilustración no
demuestra cumplimiento geométrico, rendimiento ni volumen al girar.

## Continuación autorizada — árbol completo (2026-10-26)

El usuario indica «ok, continua con lo que sigue» después de revisar la rama:
se acepta esa aplicación y se autoriza continuar al abedul completo. Conservar
recursos 0.1.0 y construcción de tres planos inclinados de la rama 0.1.1.

Implementar estructura propia de abedul: tronco esbelto, ramas escalonadas
irregulares, ramificación fina y extremos colgantes. Integrar receta versionada
`abedul_pintado@1.0.0`, componentes explícitos y contrato 1.5, sin reutilizar
la distribución en pisos del pino ni alterar recetas históricas. Primer perfil
adulto de 10 m, parámetros cerrados y piloto/tres controles (6100–6103).

Calcular cota geométrica antes de mallar: tronco/raíces/ramas/láminas, <7000 tris
y dos materiales. Anillos simplificados selectivamente con tolerancia acotada,
extremos/UV conservados y contactos revisados; atlas compartido congelado.
Separar estructura, distribución, representación, adaptación y evaluación.

Verificar contratos, límites, recursos, determinismo, GLB reimportado y
regresiones de roble/pino/columnar al tocar infraestructura común. Revisar
cuatro copas y maderas en Godot con cámaras/luz comunes y varias distancias.
Entregar piloto completo en visor y evidencia seleccionada. La aceptación
de la rama no equivale a aprobación artística del árbol completo.
Sin nuevas edades, viento, LOD, bosque ni benchmark por rutina.

## Resultado de integración

Receta 1.0.0 y contrato 1.5 integrados en catálogo, resolución, CLI y evaluación.
Cuatro casos: piloto/control-01/control-02/control-03 **6278/6278/6278/6254 tris**,
399 grupos, 1197 planos y dos materiales; cota previa 6446. Mismos recursos de
la rama, sin nueva pintura ni retoque por semilla. Simplificación selectiva
de madera a 5 mm; revisión visual de copa y madera en Godot.

155 pruebas pasan, ocho defectos de exportación rechazados, GLB repetido idéntico,
CLI con render también idéntico y regresiones roble/pino/columnar exactas.
80 capturas reales inspeccionadas en cuatro láminas; visor con cuatro semillas.
[Informe y reproducción](../docs/evidence/abedul-pintado/arbol-01/informe.md).
**Árbol completo pendiente de aceptación artística del usuario**; perfil
experimental, sin prometer otras alturas/edades, rendimiento o todos los rangos.
