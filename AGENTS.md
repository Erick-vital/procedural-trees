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

## Política para nuevos árboles

- Aplicar [la política de árboles optimizados](docs/politica-arboles-optimizados.md) a toda nueva especie, incluido el abedul propuesto.
- Follaje por grupos de láminas cruzadas fijas, pintura de estilo manual para follaje y corteza, atlas compartidos y máximo dos materiales por árbol.
- Cada árbol completo exportado debe tener **menos de 7000 triángulos (máximo 6999)**, incluida toda su madera y follaje. Diseñar y validar el presupuesto desde el comienzo para los perfiles admitidos.
- Optimizar topología de láminas y madera conservando silueta, plenitud, carácter y conexiones; comprobar transparencias, sombras y aspecto en Godot. Elegir cantidad y forma de láminas según la especie, sin imponer una solución que aplaste la copa.
- Aprobar pintura y rama de muestra antes de integrar el árbol completo; distinguir verificación técnica de aceptación artística del usuario. Medir rendimiento antes de afirmar mejoras de FPS.
- Esta política rige nuevos desarrollos; conservar recetas y contratos históricos. Una excepción requiere decisión explícita del usuario y registro en el plan.

## Política de ESTADO.md

`ESTADO.md` es una síntesis del estado vigente, no una bitácora ni un almacén ilimitado de contexto.

- Mantenerlo en **200 líneas como máximo y 16 KiB (16 384 bytes) como máximo**; ambos límites aplican al archivo completo.
- Incluir: última actualización, fase actual, avances verificados, siguiente paso, bloqueos y decisiones vigentes necesarias para continuar.
- Enlazar planes, decisiones e informes cuando haga falta detalle. Guardar evidencia solo si sirve para reproducir o evaluar un resultado; no volcar conversaciones, logs ni estados anteriores completos.
- Actualizarlo al cerrar una sesión con cambios relevantes de implementación, validación, decisiones o bloqueos. Si nada cambió, no añadir una entrada por rutina.
- Reemplazar información obsoleta y resumir avances ya consolidados. No acumular un historial cronológico ni crear copias de estado para eludir el límite.
- Antes de terminar una actualización, comprobar tamaño y líneas con `wc -lc ESTADO.md`. Si supera cualquiera de los límites, condensarlo antes de finalizar.
- Distinguir trabajo planeado, implementado y verificado. Registrar pruebas pendientes o fallidas sin presentarlas como éxitos.

## Pedidos de árboles desde Codex (F4)

- Mantener la interfaz natural del chat: «créame 10 árboles» autoriza preparar
  y generar el lote con herramientas locales, sin otro proveedor ni proceso de
  Codex. Seguir [el flujo F4](docs/uso-lenguaje-natural.md).
- Traducir la petición a perfiles y cambios permitidos, con semillas explícitas
  y explicación por ejemplar. Usar `plan-blueprints` y `generate-blueprint-plan`
  para validar el lote completo, congelar entradas y repetirlo sin modelo.
- Variar parámetros y semillas según la intención; no inventar controles ni
  modificar recetas históricas. Conservar fallos y revisar visualmente en Godot.
- Distinguir interpretación realizada en el chat de reproducción de respuestas
  guardadas; no afirmar una llamada independiente a un modelo que no ocurrió.

## Documentación

- `plans/`: alcance, fases, criterios de aceptación y cambios al plan.
- `ESTADO.md`: punto de entrada breve para retomar el trabajo.
- `docs/evidence/`: informes y comparaciones seleccionadas cuando existan resultados.
- Mantener rutas y comandos documentados alineados con los archivos realmente disponibles.
