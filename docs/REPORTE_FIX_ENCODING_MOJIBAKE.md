# REPORTE_FIX_ENCODING_MOJIBAKE

## 1) Diagnostico (origen del bug)
- Se detectaron textos mojibake en UI (Jinja/JS), por ejemplo: "Car\u00c3\u00a1tulas", "\u00c3\u008dndice", "Maestr\u00c3\u00ada/Doc.", "\u00e2\u20ac\u00a2".
- Archivos con texto corrupto:
  - app/templates/pages/catalog.html
  - app/templates/pages/detail.html
  - app/static/js/catalog.js
  - app/static/js/format-viewer.js
  - app/static/js/navigation.js
- Hallazgo tecnico: algunos textos estaban guardados como UTF-8 correcto pero con contenido ya corrompido (double-decoding cp1252/latin-1), incluyendo caracteres de control (U+0081/U+008D) en strings visibles.
- Headers/HTML:
  - app/templates/base.html ya tiene <meta charset="UTF-8">.
  - app/main.py ya fuerza charset=utf-8 via middleware para text/* y application/json.

## 2) Causa raiz
- Mezcla de codificaciones: contenido UTF-8 fue interpretado como cp1252/latin-1 en algun punto (copiado/guardado en entorno con encoding incorrecto), dejando mojibake en archivos fuente.
- El problema no venia de los endpoints en si, sino de textos ya corruptos en templates/JS.

## 3) Cambios aplicados
- Correccion de textos mojibake en templates y JS (UTF-8 real):
  - app/templates/pages/catalog.html
  - app/templates/pages/detail.html
  - app/static/js/catalog.js
  - app/static/js/format-viewer.js
  - app/static/js/navigation.js
- Defensa runtime (solo warning):
  - app/core/loaders.py agrega deteccion de mojibake y log con format_id/path.
- Scripts de prevencion:
  - scripts/check_mojibake.py (escanea y falla si encuentra patrones)
  - scripts/fix_to_utf8.py (convierte a UTF-8 con backup .bak si hay evidencia)
- Documentacion:
  - README.md agrega comando recomendado de verificacion.

## 4) Evidencia antes/despues (ejemplos)
- Antes: "Car\u00c3\u00a1tulas" -> Despues: "Carátulas"
- Antes: "\u00c3\u008dndice" -> Despues: "Índice"
- Antes: "Maestr\u00c3\u00ada/Doc." -> Despues: "Maestría/Doc."
- Antes: "\u00e2\u20ac\u00a2" -> Despues: "•"

## 5) Prevencion
- Ejecutar: `python scripts/check_mojibake.py`
- Si aparece mojibake o archivos no-UTF8, usar: `python scripts/fix_to_utf8.py` (genera .bak).
- Middleware de app/main.py mantiene respuestas HTML/JSON con charset utf-8.

## 6) Verificacion
- check_mojibake: OK (sin hallazgos).
- fix_to_utf8: No se requirio conversion.
- UI: pendiente de verificacion manual en /catalog y /formatos/{id} para validar textos visibles.

## 7) Archivos modificados
- app/templates/pages/catalog.html
- app/templates/pages/detail.html
- app/static/js/catalog.js
- app/static/js/format-viewer.js
- app/static/js/navigation.js
- app/core/loaders.py
- scripts/check_mojibake.py
- scripts/fix_to_utf8.py
- README.md
