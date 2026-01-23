# REPORTE_UX_REFERENCIAS_GRID_Y_DETALLE

Fecha: 2026-01-23

## 1) Archivos modificados

- `app/templates/pages/references.html`
- `app/static/js/references.js`
- `app/static/css/extra.css`
- `docs/REPORTE_UX_REFERENCIAS_GRID_Y_DETALLE.md`

## 2) Flujo UX (grid -> detalle -> volver)

1) Entrada a `/referencias?uni=<uni>`
   - Se muestra GRID de cards (normas disponibles).
2) Click en card (ej: APA7)
   - Se mantiene la misma pagina.
   - JS carga detalle via `/api/referencias/{id}` y muestra vista detalle.
   - URL se actualiza con `&ref=<id>` usando `history.pushState`.
3) Boton “Volver”
   - Regresa al GRID.
   - URL se limpia a `/referencias?uni=<uni>`.

Deep-link:
- `/referencias?uni=unac&ref=apa7` abre directamente la guia.

## 3) Como agregar una norma nueva

1) Crear JSON global:
   - `app/data/references/<id>.json`
2) Habilitarla en universidad:
   - Editar `app/data/<uni>/references.json`
   - Agregar `<id>` en `enabled` y `order`.
3) Recargar `/referencias`:
   - La card aparece automaticamente.

## 4) Checklist de pruebas

- [x] /referencias abre GRID (no detalle directo).
- [x] Click en una card abre detalle sin recargar pagina.
- [x] Boton Volver regresa al GRID.
- [x] `/referencias?uni=unac&ref=apa7` abre detalle directo.
- [x] Back/forward del navegador respeta grid/detalle.
- [x] Catalogo NO muestra “References” como formato.

