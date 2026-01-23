# REPORTE_FIX_GRID_Y_UTF8_REFERENCIAS

Fecha: 2026-01-23

## 1) Causa del grid vacío
- El endpoint `/api/referencias` fallaba al leer los JSON por problemas de encoding (BOM/UTF-8 mal guardado), lo que dejaba la lista sin items.
- `app/static/js/references.js` no manejaba errores de fetch, por lo que la UI quedaba solo con el header y sin cards.

## 2) Causa del mojibake
- Los JSON de referencias y la configuración por universidad estaban guardados con codificación incorrecta, generando textos tipo “Educaci?n”, “a?o”, “Garc?a”.

## 3) Cambios realizados
- Reemplazo completo y guardado en UTF-8 real (sin BOM) de:
  - `app/data/references/apa7.json`
  - `app/data/references/ieee.json`
  - `app/data/references/iso690.json`
  - `app/data/references/vancouver.json`
  - `app/data/unac/references.json`
  - `app/data/uni/references.json`
- `app/static/js/references.js`: manejo de error al cargar índices + mensaje de fallback.
- `app/templates/pages/references.html`: bump de versión del JS para evitar cache.
- `scripts/check_mojibake.py`: patrones extendidos para detectar cadenas dañadas (“Educaci?n”, “a?o”, etc.).
- `app/templates/base.html`: corrección menor de comentario para evitar texto corrupto.

## 4) Cómo validar
1. Abrir `/referencias?uni=unac` y verificar que aparece el grid con cards (APA7, IEEE, ISO 690, Vancouver).
2. Click “Ver guía” -> se abre el detalle en la misma página (sin recargar).
3. Click “Volver a normas” -> retorna al grid.
4. Verificar textos correctos: “Educación”, “Psicología”, “año”, “sangría”, “García”.
5. APA7: lista con sangría francesa + doble interlineado (clase `.ref-apa7`).
6. IEEE/Vancouver: numeración alineada `[n]` (clases `.ref-numeric`, `.ref-row`).

## 5) Prevención
- Ejecutar: `python scripts/check_mojibake.py`
- Mantener lectura con `encoding="utf-8"` en backend.
- Guardar JSON/HTML/JS en UTF-8 real (sin BOM).