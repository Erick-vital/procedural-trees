# Política de producción de nuevos árboles

Vigente desde 2026-10-26 por instrucción del usuario. Aplicable a toda nueva
especie y receta de producción que se desarrolle desde esta decisión, incluido
el abedul propuesto. Consolida el enfoque aprobado del roble 2.2.0 y pino 2.3.0.
Es una política de trabajo y aceptación; esta actualización no implementa un
árbol ni modifica validadores, contratos o recetas existentes.

## Representación y pintura

- Representar follaje y ramillas finas mediante grupos de **láminas cruzadas
  fijas en el espacio**, con atlas RGBA compartidos. Diseñar la estructura para
  esta representación desde el inicio; evitar modelar cada hoja o acícula
  individual como representación final y evitar duplicar follaje al sustituirlo.
- Usar **pintura de estilo manual** en follaje y corteza, coherente con la
  dirección artística aprobada. Conservar fuente disponible, recursos finales,
  procedencia y hashes; indicar si se generó o retocó con herramientas. El estilo
  manual no permite atribuir ejecución humana a una imagen generada.
- Presentar primero pintura y una rama representativa para aprobación artística
  del usuario, antes de integrar el árbol completo. Separar concepto, textura
  utilizable y resultado importado en Godot.
- Elegir número, orientación y contorno de las láminas según la especie y su
  volumen. Referencias: dos planos por grupo de pino y tres por grupo de roble;
  no imponer dos si dejan la copa rala ni tres si no aportan presencia visual.
- Compartir atlas y mantener **máximo dos materiales** por árbol: madera y
  follaje. Texturas acotadas, hasta 2048 × 2048 por recurso, con resolución
  justificada por la lectura a las distancias previstas.

## Presupuesto y simplificación

- **Menos de 7000 triángulos por árbol completo: máximo 6999**, sumando tronco,
  raíces, ramas, soportes y láminas. Contar geometría final triangulada del GLB
  reimportado, sin excluir madera oculta ni follaje del presupuesto.
- Diseñar el presupuesto antes de generar y validarlo en la nueva ruta de
  producción. Comprobarlo para todos los perfiles admitidos; una receta no queda
  certificada para todo su rango solo porque pasen el piloto y tres semillas.
  Acotar o rechazar entradas que puedan superar el presupuesto. El techo
  histórico de 12500 no sustituye este criterio para los nuevos árboles.
- Simplificar soportes de las láminas manteniendo el recorte pintado y los UV;
  reducir subdivisiones y caras sin función visible. Revisar superficie
  transparente y solapamientos: ahorrar tris puede aumentar el coste de alfa.
- Usar anillos adaptativos y simplificación selectiva de madera con error
  acotado y registrado. Proteger tronco, ramas que definen la silueta y uniones;
  conservar extremos, tapas y UV necesarios. Incorporar ramillas a la pintura
  cuando mantenga su lectura y contacto, sin dejar follaje flotante visible.
- Las tolerancias de 5 mm del pino y 20 mm en secundarias del roble son
  antecedentes de especies concretas, no valores universales. Elegir y verificar
  tolerancias para cada árbol, sin acumular errores locales inadvertidos.
- Conservar silueta, plenitud, profundidad y carácter. No alcanzar el presupuesto
  vaciando o encogiendo arbitrariamente la copa. Cambios artísticos de volumen
  se evalúan por separado de la simplificación y requieren aprobación.

## Materiales, exportación y evaluación

- Partir de recorte alfa (Alpha Scissor), doble cara, normales, sombras,
  rugosidad, mipmaps y filtrado configurados explícitamente. El pino aprobado
  usa umbral .5; evaluar el umbral adecuado para la nueva pintura en Godot.
  Revisar halos, trazos de canto, costuras, desaparición lejana y sombras.
- Exportar GLB autocontenido con texturas embebidas y conservar fuente Blender
  editable. Verificar conteos, materiales, UV, normales, recursos y anclajes
  sobre la exportación reimportada. Distinguir bounds transparentes y altura
  visible; una cota geométrica por sí sola no certifica contactos ni apariencia.
- Evaluar piloto y al menos tres controles reproducibles, sin retoques por
  semilla. Cubrir edades/tamaños que la receta declare; comparar cambios con
  cámaras y luz comunes, varias orientaciones y distancias, árbol y madera sola.
  Combinar métricas con inspección de imágenes reales Godot y registrar defectos.
- Mantener semillas explícitas y separadas para estructura, distribución y
  pintura cuando corresponda; recetas, recursos y componentes versionados.
  Repetir con recursos congelados y comprobar determinismo y regresiones de
  infraestructura compartida. Generación ≤120 s y subprocesos ≤180 s.
- Registrar triángulos por componente, materiales y texturas. Solo afirmar
  mejoras de rendimiento con medición reproducible en Godot, comparando las
  mismas condiciones e instancias; menos tris no demuestra más FPS. El benchmark
  del pino no acredita rendimiento del abedul ni de futuras especies.
- Distinguir implementado, verificado visualmente y aprobado por el usuario.
  Conservar recetas históricas y documentar cualquier excepción explícitamente
  autorizada. No iniciar LOD, viento, bosques u otras fases por esta política.

## Referencias verificadas

- [Roble 2.2.0](evidence/roble-pintado/integracion-madera-01/informe.md): tres
  láminas por grupo, madera selectiva, dos materiales; cuatro casos de
  3132–6900 triángulos.
- [Pino 2.3.0](evidence/pino-pintado/pp4-laminas/informe.md): dos planos y seis
  triángulos por grupo, madera adaptativa, dos materiales; 4518–4554 triángulos.
- [Benchmark del pino](evidence/pino-pintado/rendimiento-v11/informe.md): protocolo,
  comparación del asset completo y límites de las conclusiones de rendimiento.
