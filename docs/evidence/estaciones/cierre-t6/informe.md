# Cierre T6 — entrega de transiciones

2026-11-02. Solicitado por el usuario: «implementa t6».
**T0–T6 cerradas técnicamente**, candidata estacional 0.1.0 del roble 2.2.0.
[Guía de entrega, archivos y comandos](../../../entrega-transiciones.md).

T6 conserva literalmente T5: proyecto Godot, GLB, calendarios, recursos,
informes y capturas. Valida hashes de fuentes/entradas, catálogo histórico,
proyecto, extremos, 2377 PNG, paquete y decisiones de aprobación.
[Auditoría de cierre e inventario](verification.json).

Nuevo archivo de fuentes/entradas con 266 archivos, extraído en carpeta temporal:
el constructor funciona sin acceso a las rutas del checkout original y produce
manifiesto, proyecto y 16 extremos idénticos. Se valida su contenido y CRC.
Primer intento rechazado por faltar dos texturas históricas requeridas al
validar T1; corregido en `artifacts/estaciones/cierre-t6-02/`.

Galería con cinco fases y secuencias fija/orbital; paquetes y hashes enlazados en
la guía. Los archivos grandes siguen ignorados. No cambia geometría ni shader;
se conserva la revisión visual T5, sin declararla una nueva revisión nativa.
Las 194 pruebas son el resultado previo de T5; el cierre añade la comprobación
real de reconstrucción desde el archivo de fuentes y las auditorías de entrega.

[Decisiones](decisions.json): pintura compatible y calendario del piloto aprobados
en T3; normales .35 aprobadas por delegación en T4. La aceptación artística de
los cuatro casos no se infiere de solicitar T6 y sigue pendiente. Receta/alias
históricos conservados; ninguna fase adicional iniciada. Caída del roble es una
posibilidad que se definirá aparte. Sin benchmark de FPS.
