# F4: lenguaje natural a ejemplares de blueprint

Inicio autorizado el 2026-11-02: «continua con f4». Esta adaptación concreta F4
del plan v1 tras cerrar RF5, blueprints, árboles pintados y transiciones; no
inicia F5/F6.

## Decisión de uso y cambio de alcance

El usuario precisa: **solo Codex abierto en este repositorio**, mediante pedidos
como «créame 10 árboles». Codex interpreta la intención en el chat, prepara
propuestas y usa las herramientas locales. No se integra una API, proveedor
externo ni otro proceso de Codex. Se sustituye expresamente el adaptador de
proveedor previsto en F4 original por un contrato de planes JSON que desacopla
la interpretación del ejecutor. No se necesita nueva cuenta, clave ni interfaz.

La inferencia real es la interpretación de Codex en esta conversación. El origen
`codex-session` es una declaración de procedencia; un archivo no prueba por sí
solo una llamada al modelo. Reproducir respuestas guardadas no es otra inferencia.
No se afirma haber validado una API de modelos ni un proveedor independiente.

## Alcance y contrato

Primera familia evaluada: `roble_copa_ancha@2.2.0`, sin modificar su receta.
Codex selecciona perfiles, propone cambios numéricos de `editable_ranges` y
explica su relación con la petición. Fija semillas explícitas para cada ejemplar.
Rechazar campos desconocidos, duplicados, no finitos, tipos incorrectos y
combinaciones inválidas antes de Blender; validar **todo el lote** primero.
Sin recortar valores, reintentar ni cambiar silenciosamente una propuesta fallida.
Cada plan conserva solicitud, respuestas, receta, semillas, resolución y hashes.
Máximo 30 árboles por plan; directorios nuevos y tiempo acotado por árbol.

La receta conserva presupuestos históricos. F4 exige además **menos de 7000
triángulos y máximo dos materiales** por árbol exportado. La cota previa
conservadora no acredita el conteo tras simplificar madera. Una combinación
admitida por rangos puede fallar en geometría: detener y registrar el fallo.
No se promueven recetas ni se declara aceptación artística automáticamente.

## Evaluación congelada antes de generar

Matriz `configs/verification/f4-v1.json`: joven, adulto, viejo de tronco grueso,
copa densa, copa abierta y ramas asimétricas. Respuestas de Codex en esta sesión:
`configs/language/f4-responses-v1.json`. Base común: perfil adulto de la misma
receta, conservando semillas y cámaras/luz **por pareja**. Las comparaciones de
edad usan el mismo encuadre físico por pareja, no un autoencuadre independiente.
Registrar dirección de parámetros, exportación, repetición exacta e inspección
visual Godot por separado. No atribuir superioridad ni generalización a seis casos.

Variabilidad de uso: combinar perfiles, semillas y cambios permitidos por el
pedido; conservar controles no solicitados. Semillas distintas por sí solas no
prueban variedad artística. No inventar controles botánicos, edades ni especies.

## Pasos y cierre

1. Contrato de plan desacoplado; CLI de preparación y reproducción.
2. Pruebas de entradas, límites, alteraciones y fallos persistidos.
3. Seis pares base/candidato y repetición desde respuestas guardadas.
4. Capturas Godot comunes por pareja; revisión de imágenes reales.
5. Guía permanente para futuros chats e informe con resultados y pendientes.

Estado: **cerrado técnicamente**: 222 pruebas, 28 checks, seis pares, repetición
exacta y 48 capturas Godot revisadas. [Informe](../docs/evidence/f4/lenguaje-01/informe.md).
Aceptación artística del usuario registrada el 2026-11-03: [decisión](../docs/evidence/f4/lenguaje-01/user-acceptance.json). Sin F5/F6, nuevas especies,
estaciones, LOD, bosque, benchmark ni cambios del generador geométrico.
