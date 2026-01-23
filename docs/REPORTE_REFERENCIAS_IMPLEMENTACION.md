# REPORTE_REFERENCIAS_IMPLEMENTACION

Fecha: 2026-01-23

## 1) Arbol de archivos creados/actualizados

Nuevos:
- `app/data/references/apa7.json`
- `app/data/references/ieee.json`
- `app/data/references/iso690.json`
- `app/data/references/vancouver.json`
- `app/data/unac/references.json`
- `app/data/uni/references.json`
- `app/modules/references/__init__.py`
- `app/modules/references/router.py`
- `app/modules/references/service.py`
- `app/templates/pages/references.html`
- `app/static/js/references.js`

Actualizados:
- `app/main.py` (registro del router de referencias)
- `app/templates/pages/catalog.html` (boton de referencias abre /referencias, se elimino modal)
- `app/static/js/catalog.js` (se elimino modo referencias y su preview)

## 2) Como agregar una nueva norma (pasos exactos)

1. Crear un JSON global:
   - Archivo: `app/data/references/<id>.json`
   - Debe seguir el schema definido (id, titulo, tags, descripcion, secciones, fuentes).
2. Habilitarla en una universidad:
   - Edita `app/data/<uni>/references.json`
   - Agrega `<id>` en `enabled` y en `order` (segun el orden deseado).
3. Recarga la pagina:
   - `GET /referencias?uni=<uni>`
   - La norma aparece automaticamente sin tocar JS ni backend.

## 3) Como habilitar normas por universidad

Archivo por universidad:
- `app/data/unac/references.json`
- `app/data/uni/references.json`

Campos usados:
- `enabled`: lista de normas visibles
- `order`: orden de despliegue
- `notes`: notas especificas por norma (se muestran arriba del contenido)

Si el archivo no existe, el sistema usa default: todas las normas disponibles.

## 4) Endpoints implementados

- `GET /referencias?uni=<code>`
  - Renderiza la vista dedicada.
- `GET /api/referencias?uni=<code>`
  - Devuelve `{ config, items }` (items = resumen de normas).
- `GET /api/referencias/{ref_id}?uni=<code>`
  - Devuelve la norma completa + `nota_universidad` si aplica.

Fallback:
- Si `uni` no tiene config, se usa default (todas las normas).
- Si el provider no existe, se muestra el codigo en mayusculas.

## 5) Anti-mojibake

Script:
- `python scripts/check_mojibake.py`

Resultado actual:
- OK (sin hallazgos)

## 6) Validacion en navegador (pasos)

1. Catalogo:
   - Click en “Referencias Bibliograficas” -> abre `/referencias?uni=<uni>`.
2. Referencias:
   - Ver listado de 4 normas (APA7, IEEE, ISO 690, Vancouver).
   - Click en cada norma -> carga ejemplos.
3. API:
   - `/api/referencias?uni=unac`
   - `/api/referencias/apa7?uni=unac`

