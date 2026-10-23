# Instrucciones del repositorio

## Propósito

Desarrollar un generador procedural de robles low-poly como primer experimento de una infraestructura donde una IA pueda parametrizar, modificar y evaluar algoritmos 3D. El destino inicial de los assets es Godot; la generación se plantea con Python y Blender.

## Al comenzar

- Leer `ESTADO.md` y el plan activo enlazado allí antes de implementar cambios.
- Revisar archivos e instrucciones existentes; no asumir que el plan ya está implementado.
- Comunicarse y documentar en español, salvo identificadores técnicos o convenciones del código.

## Forma de trabajo

- Seguir el plan activo enlazado en `ESTADO.md`. `plans/v1-generador-arboles.md` conserva el marco de infraestructura y fases anteriores; el rediseño de follaje se rige por `plans/rediseno-follaje.md`, solicitado por el usuario. Registrar cambios de alcance expresamente.
- Separar contratos, algoritmos, ejecución, evaluación y adaptadores Blender/Godot.
- Mantener semillas explícitas y registrar versiones, parámetros y procedencia de los resultados.
- Validar entradas y limitar trabajo geométrico y tiempos de ejecución.
- Verificar cambios con pruebas proporcionadas al riesgo. Para geometría, combinar métricas con revisión visual; no declarar validación visual por una prueba sin interfaz.
- No declarar mejoras de la IA sin una comparación con entradas y condiciones reproducibles.
- No guardar credenciales ni salidas voluminosas regenerables en el repositorio. Conservar evidencia seleccionada y rutas de reproducción.
- No implementar fases adicionales solo por actualizar documentación o elaborar planes.

## Política de ESTADO.md

`ESTADO.md` es una síntesis del estado vigente, no una bitácora ni un almacén ilimitado de contexto.

- Mantenerlo en **200 líneas como máximo y 16 KiB (16 384 bytes) como máximo**; ambos límites aplican al archivo completo.
- Incluir: última actualización, fase actual, avances verificados, siguiente paso, bloqueos y decisiones vigentes necesarias para continuar.
- Enlazar planes, decisiones e informes cuando haga falta detalle. Guardar evidencia solo si sirve para reproducir o evaluar un resultado; no volcar conversaciones, logs ni estados anteriores completos.
- Actualizarlo al cerrar una sesión con cambios relevantes de implementación, validación, decisiones o bloqueos. Si nada cambió, no añadir una entrada por rutina.
- Reemplazar información obsoleta y resumir avances ya consolidados. No acumular un historial cronológico ni crear copias de estado para eludir el límite.
- Antes de terminar una actualización, comprobar tamaño y líneas con `wc -lc ESTADO.md`. Si supera cualquiera de los límites, condensarlo antes de finalizar.
- Distinguir trabajo planeado, implementado y verificado. Registrar pruebas pendientes o fallidas sin presentarlas como éxitos.

## Documentación

- `plans/`: alcance, fases, criterios de aceptación y cambios al plan.
- `ESTADO.md`: punto de entrada breve para retomar el trabajo.
- `docs/evidence/`: informes y comparaciones seleccionadas cuando existan resultados.
- Mantener rutas y comandos documentados alineados con los archivos realmente disponibles.
