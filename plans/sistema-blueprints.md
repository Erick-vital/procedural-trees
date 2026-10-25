# Plan: sistema de blueprints de árboles

Fecha: 2026-10-23.
Estado: B0–B5 cerradas técnicamente el 2026-10-23. Primer tipo preservado. B3 revisada aprobada por el usuario después del cierre; copa columnar experimental. RF5 ejecutada/verificada y aprobada artísticamente después de B5; rediseño cerrado para la familia ensayada.

## Decisión posterior al cierre B5

El 2026-10-23 el usuario aprueba B3 revisada, incluida la hoja joven de .45 m,
y autoriza ejecutar RF5. [Aprobación](../docs/evidence/blueprints/b3-revision/user-acceptance.json).
La aprobación corresponde a los perfiles/casos B3 revisados; no incluye copa
columnar ni aceptación anticipada de los treinta resultados RF5. B0–B5 y sus
resultados históricos se conservan. La nueva ejecución se rige por
[RF5](rediseno-follaje.md) y `configs/verification/rf5-v1.json`.
[Resultado RF5](../docs/evidence/rediseno-follaje/rf5/informe.md): 30/30 correctos,
regresión de madera, tres repeticiones idénticas y 360 capturas reales Godot.
Sin modificar recetas ni predeterminados. Posteriormente el usuario aprueba el
lote completo: [aceptación RF5](../docs/evidence/rediseno-follaje/rf5/user-acceptance.json).

## 1. Objetivo y decisión de alcance

Ampliación posterior, solicitada por el usuario el 2026-10-23 y verificada el
2026-10-24: [primer intento de pino cónico](blueprint-pino.md), con componentes
específicos y contratos 1.1. Añade un tercer tipo registrado sin reabrir el cierre
B5 ni alterar el roble aprobado. [Resultado](../docs/evidence/blueprints/pino/informe.md).
Aceptación artística pendiente; F4–F6 permanecen fuera de este trabajo.

Crear un sistema mínimo de recetas versionadas para generar familias de árboles,
registrar la generación RF3 como primer blueprint y comprobar la reutilización
creando después un segundo blueprint con una arquitectura visual distinta.

El usuario autorizó ejecutar B0 y aprobó RF3 como referencia del primer tipo el
2026-10-23. Después pidió continuar con la siguiente etapa al terminar B0:
B1 quedó autorizada. Después autorizó B2 para registrar e integrar el primer
blueprint conservando RF3. B0 conservó el piloto; B1 define contratos y B2 ya
genera desde fuentes sin archivos de ensayos. El usuario autoriza continuar B3
el 2026-10-23; después solicita resolver joven/contacto. Revisión implementada
y matriz verificada, con piloto conservado. Después solicita B4: segundo
blueprint autorizado e implementado, sin cambiar componentes de producción.
El usuario solicita B5: documentación, selección segura y cierre implementados.
No se ejecuta lote RF5 ni se promueven perfiles como parte del cierre.

Cambio de alcance propuesto respecto al [rediseño de follaje](rediseno-follaje.md):
pasar de un ensayo de copa sobre un roble a una capa reutilizable de definición
y ejecución de tipos de árbol. El rediseño conserva los contratos y la evidencia
RF0–RF3; sus controles RF4 y su integración RF5 se coordinan con las fases de este
plan para evitar dos implementaciones paralelas. No se declaran completados.
El [plan v1](v1-generador-arboles.md) conserva los experimentos de IA pendientes;
este trabajo no acredita sus fases F4–F6 ni inicia bosque, mapa o terreno.

## 2. Punto de partida comprobado al fijar el plan (histórico)

- Existen presets JSON, `TreeSpec`, derivación de semillas, algoritmos
  versionados, ejecutor CLI/API, manifiestos, evaluación y exportación GLB/Godot.
- No existe una definición integrada de blueprint que seleccione y reúna
  estructura, copa, representación del follaje, apariencia y límites.
- `schemas/tree-spec.schema.json` describe `oak_geometry_nodes` hasta 0.4.1.
  RF3 tiene contrato separado en `schemas/foliage-canopy.schema.json` y parámetros
  en `presets/foliage-canopy.json`; no está integrado en la ejecución normal.
- RF3 usa `src/treegen/foliage_canopy.py`,
  `blender/foliage_canopy_lab.py` y `scripts/verify_foliage_canopy.py`.
  Su preparación depende de referencias, manifiestos y archivos de ensayos
  previos. Esa dependencia debe resolverse antes de ofrecer generación autónoma.
- Referencia RF3: `viejo-09`, madera Q3 0.4.0 conservada,
  `foliage-canopy-0.1.0`, 9 m, 264 conexiones, 1584 hojas,
  10572 triángulos y tres materiales. [Informe RF3](../docs/evidence/rediseno-follaje/rf3/informe.md).
- Galería existente: `artifacts/rediseno-follaje/rf3-acceptance-02/index.html`.
  Modelo existente: `artifacts/rediseno-follaje/rf3-acceptance-02/pilot/tree.glb`.
- El usuario aprobó explícitamente el piloto RF3 como referencia del primer tipo
  el 2026-10-23. [Adopción B0 y hashes](../docs/evidence/blueprints/b0/reference-lock.json).
  La aprobación no demuestra estabilidad entre edades y semillas.
- Los presets principales siguen apuntando a Q3b rechazada. El primer blueprint
  seleccionará explícitamente la base Q3 y el follaje RF3.

## 3. Modelo conceptual

Un blueprint es una receta generativa, no un GLB ni una captura de un ejemplar.

| Concepto | Responsabilidad |
| --- | --- |
| Blueprint | Identidad del tipo, componentes versionados, parámetros predeterminados, rangos y límites |
| Perfil de desarrollo | Ajustes explícitos para joven/adulto/viejo dentro del tipo; solo se publican perfiles comprobados |
| Ejemplar | Blueprint y versión, perfil, semillas y cambios permitidos resueltos para una generación |
| Resultado | Mallas, GLB, vistas, métricas y manifiesto de una ejecución concreta |

Nombre artístico provisional del primero: **Roble estilizado de copa ancha**.
Identificador registrado: `roble_copa_ancha`; primera versión `1.0.0`.
No se afirma equivalencia botánica con una especie real. `viejo-09` será el
ejemplar de referencia inicial, no el nombre de toda la familia.

Cada blueprint declarará:

- Identidad y versiones de esquema y receta; descripción visual y procedencia.
- Regla de estructura: jerarquía, proporciones, longitudes, radios e inclinaciones.
- Regla/perfil de copa y distribución: envolvente, ocupación y soportes.
- Representación del follaje: geometría, escala, agrupación y orientación.
- Apariencia: materiales y paleta, sin modificar la iluminación para compensar cambios.
- Parámetros, unidades, valores predeterminados, rangos y restricciones conjuntas.
- Perfiles de desarrollo disponibles y estado de validación de cada uno.
- Presupuestos geométricos y límites de trabajo y ejecución.

Las semillas pertenecen al ejemplar. Cada prueba de referencia conservará sus
semillas exactas y su derivación; no se reinterpretarán al introducir la capa nueva.

## 4. Arquitectura mínima: propuesta original

Flujo previsto:

`blueprint + perfil + semillas + cambios → especificación resuelta → reglas → Blender → evaluación/GLB → Godot`

- Contratos y resolución sin dependencia de `bpy` en `src/treegen/`.
- Definiciones de datos en una carpeta propuesta `blueprints/`, con referencias
  explícitas a componentes registrados y versionados. No cargar código arbitrario
  desde una receta ni crear un lenguaje de programación de blueprints.
- Separar reglas de estructura, perfil/distribución, soportes y representación;
  conservar Geometry Nodes y Blender donde ya resuelven el trabajo.
- Adaptar el ejecutor compartido, sus fallos y manifiestos; evitar un segundo
  sistema de trabajos. La CLI será la primera entrada; la API existente conservará
  su compatibilidad y solo ampliará su entrada si resulta necesario.
- Registrar en el manifiesto el blueprint original, versión/hash, perfil,
  cambios solicitados, parámetros resueltos, semillas, versiones de componentes,
  hashes de fuentes, entorno y artefactos. Guardar suficiente información para
  repetir un trabajo aunque después cambien los valores predeterminados.
- Mantener esquemas, fuentes y comandos históricos reconstruibles. Una nueva
  interfaz no debe cambiar silenciosamente el significado de `TreeSpec`.
- Versionar los cambios de receta que alteren resultados. Versionar aparte los
  contratos y algoritmos; una edición de descripción no equivale a cambiar geometría.

Esta sección conserva la propuesta original de responsabilidades. Las interfaces
finales y sus comandos reales están en la [guía de uso](../docs/uso-blueprints.md).

## 5. Fases y criterios de salida

### B0. Congelar la referencia y delimitar la migración

1. Identificar entradas, semillas efectivas, fuentes y materiales exactos del
   piloto RF3; registrar hashes y la decisión de adopción de ese resultado.
2. Inventariar dependencias en `artifacts/` y referencias de laboratorio.
   Distinguir evidencia de comparación y entradas necesarias para generar.
3. Fijar qué geometría, normales, transformación y materiales deben conservarse.
   Mantener sin reducción de polígonos la geometría actual del primer tipo.
4. Definir la prueba de equivalencia: hashes de geometría/materiales normalizados
   y comparación visual con cámaras/luz fijas. Un hash binario GLB distinto por
   metadatos no basta para declarar una regresión geométrica.

Salida: referencia reproducible y criterio de conservación explícito. Si falta
un archivo imprescindible, documentarlo y recuperar/reconstruir la referencia
antes de sustituir la ruta de generación.

Resultado: [B0 completada](../docs/evidence/blueprints/b0/informe.md), 133 archivos
auditados, 105 fuentes recuperables desde el commit fijado y reproducción exacta
en firmas normalizadas. Aprobación del usuario vinculada al piloto viejo-09.

### B1. Contrato y resolución de blueprints

1. Diseñar esquema estricto y registro mínimo de componentes, sin construir un
   catálogo genérico de especies ni añadir reglas todavía innecesarias.
2. Definir precedencia: valores del blueprint → perfil → cambios del ejemplar.
   Rechazar campos desconocidos, versiones inexistentes y cambios no permitidos.
3. Validar finitud, unidades, rangos, compatibilidad entre componentes y coste
   máximo antes de abrir Blender. Diferenciar rango aceptado y rango ya probado.
4. Definir semántica de densidad/cantidad y de copa vacía. RF3 exige actualmente
   una región ocupada y al menos 24 grupos; no anunciar densidad cero sin resolver
   ese caso mediante un contrato versionado y su prueba correspondiente.
5. Separar identidad del tipo, perfiles y semillas; evitar duplicar un blueprint
   entero por cada ejemplar o edad.

Salida: carga/resolución determinista y pruebas de errores relevantes, incluida
una combinación individualmente válida pero incompatible o fuera de presupuesto.

Resultado: [contrato B1 implementado](../docs/contrato-blueprints.md), esquemas
estrictos, resolución sin `bpy`, perfiles, semillas separadas y cota conjunta.
Trece pruebas nuevas y 64 totales correctas fuera del sandbox.
Decisión de copa vacía: esta primera combinación la rechaza explícitamente;
RF3 requiere ≥24 grupos, región ocupada y densidad Q3 ≥.125. Su admisión futura
necesita contrato versionado y prueba de integración antes de B3.

### B2. Primer blueprint y generación integrada

1. Registrar `roble_copa_ancha` con base estructural Q3 y representación RF3,
   incluyendo la configuración exacta del piloto como referencia.
2. Incorporar generación de madera y moldes desde datos/fuentes versionados.
   Una ejecución nueva no dependerá de una ruta absoluta a un ensayo anterior
   ni de un `.blend` regenerable no disponible en una copia limpia del proyecto.
3. Reutilizar el ejecutor, límites de tiempo y evaluación, adaptando el presupuesto
   explícito de 12500 sin cambiar el valor histórico de 10000 para trabajos antiguos.
4. Reproducir el piloto desde la nueva entrada; comprobar geometría, normales,
   materiales, altura, raíces de hojas y conexiones, además de repetición.
5. Exportar e importar en Godot y comparar imágenes reales contra B0. Si la
   extracción obliga a cambiar resultados, registrar una revisión y evaluar la
   diferencia; no presentarla como migración equivalente.

Salida: primer blueprint ejecutable, documentado y equivalente al piloto RF3,
con historial reconstruible. Registrar su aceptación visual y alcance.

Resultado: [B2 implementada y verificada](../docs/evidence/blueprints/b2/informe.md).
`roble_copa_ancha` 1.0.0 registrado con único perfil `viejo_referencia`;
generación y repetición desde copia sin `artifacts/` ni `docs/`, GLB idéntico
byte por byte al aprobado y doce vistas Godot idénticas/revisadas. Setenta
pruebas correctas; sin iniciar otros perfiles, casos B3 ni lote.

### B3. Variación del primer tipo y controles RF4

1. Reutilizar los casos RF4: `viejo-00`, `viejo-03`, `adulto-00`, `joven-00`
   y tres semillas reservadas, una por edad, elegidas antes de ajustar.
2. Comprobar cambios aislados de tamaño de hoja, ocupación, perfil y semillas;
   verificar madera base inmutable ante cambios exclusivos de follaje.
3. Ensayar extremos, copa vacía según B1 y combinaciones difíciles de altura,
   escala y presupuesto. Registrar fallos y perfiles aún no admitidos.
4. Revisar estructura sin hojas y copa completa en Godot con cámaras comparables.
   No ajustar en secreto cada semilla ni convertir un caso fallido en éxito.

Salida: matriz de controles y perfiles de desarrollo verificados, con rangos y
limitaciones explícitos. Esta fase cubre los controles RF4 correspondientes;
la integración B2 cubre parte de RF5, pero el lote de treinta sigue separado.

Resultado B3 inicial: [matriz con fallo y límites](../docs/evidence/blueprints/b3/informe.md).
La continuación solicitada resuelve ambos pendientes en la receta 1.2.0:
[revisión verificada](../docs/evidence/blueprints/b3-revision/informe.md).
Hoja joven .45 m con soportes/raíces intactos; distribución 0.1.1 corrige
proyecciones reales, con cota de 1 mm; evaluación float64 sin relajar tolerancia
.1 mm. El fallo de 20 m era falso rechazo de BVH: punto conservado y GLB válido.
22 generaciones, tres rechazos previstos, cuatro repeticiones y 84 invariantes;
matriz `passed=true`, 80 pruebas y regresión Blender. 22 GLB reimportados para
contacto, 28 GLB Godot de matriz y 270 capturas con antes/después comparable.
Piloto idéntico a B0 y madera/normales/corteza conservadas en siete Q3.
Perfiles aún experimentales: revisión visual realizada, aprobación artística
del usuario pendiente. No se acredita todo el rango ni se inicia lote.
B4 se ejecuta después por autorización explícita.

### B4. Segundo blueprint como prueba de reutilización

1. Elegir una identidad visual y referencias coherentes antes de generar.
   Buscar una arquitectura distinguible; cambiar solo color o semilla no basta.
2. Definir silueta, ramificación y organización del follaje objetivo. El nombre
   podrá ser artístico; una atribución a especie real requiere referencias.
3. Intentar expresar el objetivo con componentes existentes. Si faltan reglas,
   añadir únicamente la estrategia necesaria y versionarla, conservando el primer
   blueprint. No prometer que los diez parámetros históricos cubren cualquier árbol.
4. Generar un piloto y al menos tres semillas de control fijadas de antemano,
   con parámetros comunes y sin arreglos individuales ocultos.
5. Evaluar su identidad visual, exportación, repetición y coste. Repetir el
   ejemplar de referencia del primer blueprint tras cualquier cambio compartido.

Salida: segundo blueprint distinguible y reproducible, con componentes reutilizados
identificados, o informe concreto del límite encontrado. Un fallo no exige
desarrollar automáticamente un generador multiespecie completo.

Resultado B4: [segundo blueprint y evaluación](../docs/evidence/blueprints/b4/informe.md).
`arbol_copa_columnar` 1.0.0, objetivo y cuatro semillas fijados antes de generar.
Reutiliza Q3, distribución 0.1.1, seis rombos RF3, contratos, ejecutor y materiales;
sin cambios de código de producción. Tronco esbelto y ramas ascendentes,
comparación visual con madera desnuda y misma semilla del primer tipo.
Cuatro casos de 12 m/11756 triángulos, cuatro repeticiones idénticas, primer
GLB idéntico a B0. Diez generaciones, 83 pruebas, contactos reimportados,
12 GLB Godot y 108 capturas; matriz `passed=true`. Identidad visual revisada,
aprobación artística del usuario pendiente; no se promovieron perfiles/lote.

### B5. Documentación y cierre

1. Documentar comandos reales para listar/seleccionar blueprints y generar,
   validar y repetir ejemplares, según las interfaces finalmente implementadas.
2. Resolver explícitamente los valores predeterminados para que Q3b no sea una
   selección accidental; conservar el acceso a versiones históricas.
3. Enlazar resultados, aceptación y pendientes en `ESTADO.md` y README.
4. Decidir por separado si procede ejecutar el lote de treinta de RF5. El cierre
   del sistema de blueprints no declara ese lote ejecutado ni aceptado.

Salida: dos recetas documentadas, primer tipo preservado, evidencia seleccionada
y ruta de reproducción que no depende de conversaciones o carpetas locales antiguas.

Resultado B5: [documentación y cierre](../docs/evidence/blueprints/b5/informe.md).
README resumido, guía de uso y operación histórica separada. CLI con selección
explícita y sin “latest”; alias TreeSpec ahora Q3 0.4.0 y copias exactas Q3b
anteriores en `presets/v0.4.1/`. Regresión de finalización TreeSpec detectada y
corregida inicializando el registro de artefactos, sin cambiar geometría.
85 pruebas, siete generaciones en copia sin resultados/evidencia previos y
cuatro comparaciones exactas, incluida repetición desde manifiesto. Referencias
B0/B4 intactas. **Decisión RF5: no ejecutarlo al cerrar B5**; requiere una decisión
posterior separada, al igual que la aprobación artística de perfiles/tipos nuevos.

## 6. Verificación, límites y evidencia

- Pruebas unitarias de resolución, validación, versiones y semillas; integración
  Blender/GLB/Godot donde cambie la ejecución o la geometría.
- Revisar números finitos, índices, áreas, materiales, altura, ejes, contactos,
  presupuestos y exclusión de moldes del GLB final. Medir tras realizar instancias.
- Primer blueprint y segundo piloto: hasta 12500 triángulos y tres materiales;
  un cambio de techo se decidirá expresamente antes de generar.
- Mantener para el primer tipo las cotas RF3 de muestras e intentos. Cualquier
  nueva estrategia deberá fijar sus propias cotas antes de ejecutar.
- Generación con límite inicial de 120 s; verificaciones/capturas con 180 s por
  subproceso terminable. Registrar duración y tamaño sin deducir FPS del conteo.
- Comparaciones visuales reales en varias vistas y distancias, con condiciones
  registradas; las métricas de ocupación no sustituyen la aceptación artística.
- Salidas implementadas en `artifacts/blueprints/`; evidencia seleccionada y
  comandos reproducibles en `docs/evidence/blueprints/`, informes B0–B5.
- Registrar procedencia de referencias externas y conservar solo evidencia útil,
  sin grandes salidas regenerables en Git ni copias completas de estados antiguos.

## 7. Fuera del alcance y estado de ejecución

No incluye editor visual, simulación botánica, crecimiento temporal, viento,
LOD, tarjetas texturizadas, bosque, terreno ni conexión a un modelo IA.
Los perfiles de edad son configuraciones artísticas, no una simulación de crecimiento.
No incluye optimización de geometría del árbol actual por el mero hecho de migrarlo.

B0 completada y referencia RF3 aprobada: [informe de conservación y migración](../docs/evidence/blueprints/b0/informe.md).
B1 implementada y verificada: [evidencia](../docs/evidence/blueprints/b1/verification.json).
B2 implementada/verificada: [evidencia](../docs/evidence/blueprints/b2/verification.json).
Primer blueprint registrado e integrado; referencia RF3 conservada. B3
implementada y revisada: los pendientes joven/contacto están resueltos y
verificados. B4 completada con segundo tipo distinguible y componentes
reutilizados. B5 cierra el sistema mínimo y su documentación; dos tipos y
versiones históricas disponibles. Después del cierre B5 se aprueban B3 revisada
y el lote RF5 completo, ejecutado/verificado. La copa columnar sigue pendiente
de aprobación artística. No se cierra el objetivo v1 completo.
