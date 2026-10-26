# Diagnóstico tras rechazo del ajuste de grosor

Fecha: 2026-10-26. El usuario rechaza visualmente `fuller-v1`: identifica como
problema las ramillas finas nacidas directamente de madera mucho más gruesa;
prefiere las que nacen de ramas de menor orden. No se cambia geometría en este
diagnóstico ni se considera aprobada la variante.

Comprobación de `parent_branch_id` en `source/manifest.json` de
`artifacts/roble-pintado/rama-muestra-01/`, cruzado con `parent_id` de
`source/base-reference.json`:

| Origen en la muestra | Soportes | Hojas |
| --- | ---: | ---: |
| Primaria 100 | 19 | 114 |
| Secundaria 200 | 5 | 30 |
| Secundaria 201 | 2 | 12 |
| Secundaria 202 | 6 | 36 |
| Total | 32 | 192 |

La receta histórica solo tiene tronco, primarias y secundarias como estructura
de madera; los soportes añaden el siguiente nivel. No hay un nivel intermedio
que conecte los 19 tubos de la primaria con ramas finas. `connection_geometry`
en `src/treegen/foliage_molds.py` usa el radio común de la copa, sin adaptarlo al
grosor de la rama receptora; `make_support` conecta cada muestra a su rama
asignada. Esto confirma el origen directo y el salto de grosor. La naturalidad
es una valoración visual del usuario, no una métrica demostrada por estos datos.

En todo el piloto hay 264 soportes: 8 sobre tronco, 136 sobre primarias y
120 sobre secundarias. La cuestión afecta a la regla, no solo a esta rama.

Eliminar solo los 19 tubos ahorraría 152 tris (13,8 % de los 1104), pero dejaría
114 hojas sin su conexión de madera. Eliminar también sus hojas ahorraría
380 tris (34,4 %, quedan 724), perdiendo 59,4 % de hojas. Ninguna operación
se ha aplicado ni demuestra conservación de copa.

Propuesta pendiente: revisar la jerarquía, favoreciendo follaje conectado a
ramas más finas y evaluando si pocas ramificaciones compartidas pueden sostener
los grupos actuales. No prometer ahorro hasta contar el coste de esas conexiones;
no trasladar hojas, borrar grupos ni integrar al árbol completo sin concretar
el ensayo. La conservación exacta de anclajes del plan vigente necesitaría una
ampliación de alcance para redistribuir grupos.
