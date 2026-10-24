# Estado del proyecto

Última actualización: 2026-10-23.

## Situación actual

[Sistema de blueprints](plans/sistema-blueprints.md): **B0–B5 cerrado técnicamente**.
Dos tipos registrados y documentados; referencia del primero conservada.
[Guía de uso](docs/uso-blueprints.md), [cierre B5](docs/evidence/blueprints/b5/informe.md).
Solo viejo-09 RF3 está aprobado artísticamente por el usuario como referencia.
Perfiles RF3 nuevos y copa columnar siguen experimentales, aunque verificados.
**RF5: lote de treinta no ejecutado ni promovido al cerrar B5.**

Objetivo v1: treinta robles low-poly reproducibles/exportables a GLB y evaluación
IA para parámetros/reglas/simplificación. Infraestructura F0–F2 verificada;
F4–F6 IA pendientes. F3/bosques, mapa y terreno diferidos.
El [plan v1](plans/v1-generador-arboles.md) conserva ese alcance separado.
[Rediseño de follaje](plans/rediseno-follaje.md): RF3 aprobada; integración B2 y
controles RF4/B3 verificados en matrices acotadas; lote/promoción RF5 pendientes.

## Avances verificados

- B0: referencia RF3 aprobada, congelada y reproducida. 133 archivos auditados,
  105 fuentes recuperables de Git. [Informe](docs/evidence/blueprints/b0/informe.md).
- B1/B2: contratos estrictos, registro, resolución determinista y ejecución
  integrada desde fuentes sin ensayos previos. `roble_copa_ancha` 1.0.0 reproduce
  GLB B0 idéntico y doce vistas Godot idénticas; 70 pruebas.
  [Contrato](docs/contrato-blueprints.md), [B2](docs/evidence/blueprints/b2/informe.md).
- B3 revisada: receta 1.2.0, joven .45 m sin cambiar soportes/raíces; contactos
  contra triángulos reales en float64 y proyección 0.1.1 acotada. 22 éxitos,
  tres rechazos previstos, cuatro repeticiones idénticas, 80 pruebas;
  22 GLB reimportados y 270 capturas reales. Madera/normales/corteza iguales
  a siete Q3; piloto intacto. [Informe](docs/evidence/blueprints/b3-revision/informe.md).
- B4: `arbol_copa_columnar` 1.0.0, 12 m, piloto 4100/controles 4101–4103 y copa 73.
  Reutiliza los tres componentes y ejecutor, sin algoritmo geométrico nuevo.
  Diez generaciones, cuatro repeticiones idénticas, 83 pruebas, 12 GLB Godot
  y 108 capturas. Primer GLB idéntico a B0.
  [Identidad/reutilización](docs/evidence/blueprints/b4/informe.md).
- B5: guía, catálogo y selección histórica explícitos. 85 pruebas y siete
  generaciones CLI en copia sin resultados/evidencia previos; cuatro
  comparaciones exactas, incluida repetición desde manifiesto. Roble/columnar
  idénticos a B0/B4. Alias Q3 y versión explícita idénticos. Sin capturas nuevas.
  [Cierre](docs/evidence/blueprints/b5/informe.md).
- B5 corrigió finalización TreeSpec: inicializar `files_sha256` que no emitía
  el adaptador histórico. Regresión probada; GLB anterior/posterior idéntico.
- Base previa: Q1b y Q2 aprobadas; Q2 normaliza solo Z desde madera y conserva
  X/Y/radios. Q3 aprobada; Q3b rechazada. Fusión/addons comparados, sin ganador
  general ni sustitución del generador propio.
  [Q2](docs/evidence/q2/informe.md), [Q3](docs/evidence/q3/informe.md),
  [fusión](docs/evidence/q3-fusion/informe.md), [addons](docs/evidence/comparacion-addons/informe.md).
- RF2: rama de 144 hojas aprobada el 2026-10-23; RF3 construyó el piloto de
  **9 m, 264 conexiones, 1584 hojas, 10572 triángulos y tres materiales**.
  [RF2](docs/evidence/rediseno-follaje/rf2-densidad/informe.md),
  [RF3](docs/evidence/rediseno-follaje/rf3/informe.md).
- Entorno: Blender 5.2.1 LTS `9e2066aef7ef`, Python Blender 3.13.13,
  orquestación 3.14.4, jsonschema 4.19.2, Pillow 12.1.1 y Godot 4.7.2 `ed1daf0bf`.

## Decisiones vigentes

- Receta/perfil/ejemplar separados; semillas explícitas y componentes registrados.
  CLI exige receta y petición; sin selección “latest”. Inicio rápido: roble 1.0.0
  y viejo-09 aprobado. Recetas 1.0.0/1.1.0/1.2.0 del primero conservadas;
  perfiles nuevos y segundo tipo no promovidos por pasar pruebas técnicas.
- B5 resuelve los alias TreeSpec `presets/{joven,adulto,viejo}.json`: ahora
  idénticos a Q3 `presets/v0.4.0/`. Sus contenidos Q3b previos se conservaron
  byte por byte en `presets/v0.4.1/`; `q3b-cases.json` histórico intacto.
  [Decisión y hashes](docs/evidence/blueprints/b5/defaults-decision.json).
- `generate` y API siguen recibiendo TreeSpec; `generate-blueprint`, receta y
  ejemplar. API solo loopback, un servidor por carpeta, sin reintentos.
  `batch` conserva F2 histórico como predeterminado; no es lote RF3/blueprint.
- Techo blueprint: **12500 triángulos/3 materiales**; TreeSpec conserva 10000.
  RF3: hasta 360 grupos/2160 hojas, 8192 muestras y 2048 intentos antes de mallar.
  Columnar declara máximo 337 grupos; solo 300 comprobados geométricamente en B4.
  Generación ≤120 s; pruebas/capturas ≤180 s por subproceso terminable.
- Conservar geometría actual, incluido tronco; sin reducción de polígonos ni
  tarjetas texturizadas. Optimización futura al integrar en motor, con mediciones
  de rendimiento: menos triángulos por sí solo no demuestra mejora.
- Referencia RF3: moldes Q3 invisibles, seis rombos por conexión, hoja nominal 1 m.
  Joven 1.2.0 usa .45 m con planificación 1 m y soportes conservados. Columnar
  usa .45 m y planificación .45 m. Sin cambios por semilla ni atribución botánica.
- Perfil/ocupación separados: anchura modifica guías X/Y; peso regional reduce
  su cupo sin reasignación. Rechazar colocaciones fuera de altura no renormaliza
  ni recorta madera. Copa vacía se rechaza (≥24 grupos y una región positiva).
- Contactos: distribución 0.1.1 evalúa triángulos reales en float64; conserva
  proyección dentro de .1 mm, corrige fuera con cota de 1 mm. Mayor corrección B3:
  .534 mm. Ruta 0.1.0 histórica conservada. Semiespacios para raíces en tubos.
- Fuentes/contratos históricos reconstruibles; resultados regenerables ignorados,
  evidencia seleccionada y comandos conservados. Git Q3 `fbe87a4`, etiqueta
  `q3-referencia-0.4.0`; fusión `4fa3d8c`.
- No atribuir mejoras IA sin entradas/condiciones reproducibles. Las métricas de
  ocupación o silueta no acreditan naturalidad, rendimiento o aprobación estética.

## Siguiente paso y pendientes

No hay una fase de blueprints en ejecución tras B5. Decisiones separadas:
aprobación artística de perfiles/tipo nuevos y si solicitar/evaluar lote RF5.
No se ha autorizado ni ejecutado ese lote como parte del cierre.
F4–F6 IA siguen pendientes; elegir proveedor/modelo al retomarlas.
F5 conserva normalización Q2 solo Z y radios posiblemente elípticos, y deberá
comparar estructura con/sin regla conservando ≥90 % de longitud; no fue sustituida.

Límites: B4 solo ensaya columna de 12 m/cuatro semillas; intervalos completos y otras
edades no garantizados. Caso 2 m/moldes 3 m técnicamente válido pero visualmente
inadecuado. Extremo de 20 m completa 2021/2048 intentos, cerca del límite de trabajo.
Conexiones superpuestas a Q3, sin soldar ni resolver todas las intersecciones;
hojas angulosas/solapadas. Sin pruebas FPS, viento, LOD ni bosque.

Sin bloqueos técnicos fuera del sandbox. Dentro pueden fallar audio al cerrar
Blender y sockets loopback; ejecución autorizada fuera. Capturas Godot en lotes
de dos escenas, dos dibujos completados por vista.

Referencias locales regenerables: B2 `artifacts/blueprints/b2-acceptance-01/`,
B3 `artifacts/blueprints/b3-controls-05/`, B4 `artifacts/blueprints/b4-columnar-01/`,
B5 `artifacts/blueprints/b5-closure-02/`. Evidencia durable y reproducción en los
informes enlazados; [operación histórica](docs/operacion-historica.md).
