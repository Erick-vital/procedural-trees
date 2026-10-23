# Contrato experimental RF3: copa completa sobre Q3

Versión `foliage-canopy-0.1.0`, fijada antes de generar candidatos. Piloto único:
viejo-09, semilla estructural 3009 y follaje 17. Se parte de la rama RF2 de
144 hojas aprobada, con rombo opaco nominal de 1 m y conexiones rectas.

- Extraer exactamente toda la madera final Q3 y sus polígonos/sombreado,
  transformación, normalización y corteza. Identificar tronco, primarias y
  secundarias por los canales originales, cotejando sus vértices con la malla
  guardada; máximo 49 ramas. Base inmutable durante RF3.
- Extraer todos los componentes de follaje como moldes: máximo 128 moldes,
  4096 triángulos guía y 16384 vértices. Para viejo-09 hay 89 moldes y 3220
  triángulos; no se exportan ni se conservan como relleno visible.
- Pool fijo de 8192 muestras, proporcional al área. Descartar superficie
  interior respecto a todos los moldes, incluidas otras primarias. Registrar
  intentos, muestras expuestas, áreas y regiones; sin búsquedas ilimitadas.
- Perfil inicial: moldes Q3, escala horizontal 1 alrededor del centro de su
  caja de referencia, Z intacta. Control de perfil: anchura horizontal ×1.12.
  La madera Q3 permanece fija y se vuelven a construir conexiones hacia la guía.
- Partir la superficie en norte/este/sur/oeste respecto a ese centro por eje
  horizontal dominante. Repartir el número global de grupos según las muestras
  expuestas de cada región, con restos mayores e ids de desempate estables.
- Ocupación regional entre 0 y 1: reduce el cupo de esa región, sin reasignar
  su presupuesto ni cambiar los demás cupos. Control inicial: este ×.4.
  Es un diagnóstico espacial; no maximiza porosidad como objetivo estético.
- Cantidad solicitada 24–360 grupos; piloto 264, referencia aritmética de
  24 grupos × once primarias, ahora repartidos globalmente por área expuesta.
  Selección separada por región y progresiva por distancia. Máximo 2048
  intentos de conexión; longitud .05–4 m, inserción sobre su rama Q3 padre.
- Cada conexión conserva la sección triangular RF2: dos anillos, ocho
  triángulos, radio basal .02 m/final .005 m y penetración de raíz .04 m.
  Seis hojas por grupo: las cuatro posiciones RF2 más dos adiciones, mismo
  protocolo por id para raíz, tamaño ±10 %, giro e inclinación ±30°.
- Rechazar grupos que colocan hojas o tubos fuera de Z=0–altura Q3. No mover,
  recortar ni renormalizar la base para acomodar hojas. Trabajo por grupo acotado;
  registrar los rechazos. Las raíces deben quedar dentro de su tubo real.
- Presupuesto previo: `madera_base + grupos × (8 + 6×2) ≤12500`, máximo tres
  materiales. Viejo-09: 5292 + 264×20 =10572; máximo 360 grupos =12492.
  Ocupación regional reducida deja presupuesto sin gastar. Medir exportación.
- Casos: Q3, piloto, repetición, perfil ancho y ocupación este reducida.
  Verificar por separado que cambiar tamaño de hoja conserva conexiones.
- Cámaras RF0 de árbol congeladas, 900×900, más detalle de la rama aprobada;
  mismas luces RF2 por renderizador. Escalas ortográficas 50/25/10 %, sin
  atribuirles distancias físicas de cámara perspectiva. Registrar recortes.
- Contrato, algoritmo, perfil, ensamblado Blender y evaluación separados.
  Generación ≤120 s, verificaciones/capturas ≤180 s por proceso terminable;
  no reintentos automáticos. Fuentes/semillas/artefactos con hashes.
- Evaluación nueva acepta explícitamente hasta 12500; los validadores y
  contratos históricos mantienen 10000 por defecto. RF4/RF5 sin implementar.

Salida revisable: GLB completo, manifiesto, controles de perfil/ocupación y
comparación Godot con Q3. La aceptación artística de copa es independiente de
la aprobación RF2 y de los conteos/cobertura. No se promete rendimiento de juego.
