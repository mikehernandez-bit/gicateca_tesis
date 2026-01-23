# REPORTE_FIX_REFERENCES_EN_CATALOGO

Fecha: 2026-01-23

## 1) Causa raiz

El discovery de formatos (`app/core/loaders.py`) escaneaba **todos** los `*.json` dentro de `app/data/<uni>/`.
Eso incluia:

- `app/data/unac/references.json` -> format_id generado: `unac-references`
- `app/data/uni/references.json` -> format_id generado: `uni-references`

Ambos se trataban como formatos normales y terminaban listados en el catalogo.

## 2) Archivos modificados

- `app/core/loaders.py`
- `app/modules/catalog/service.py`
- `docs/REPORTE_FIX_REFERENCES_EN_CATALOGO.md`

## 3) Reglas de exclusion aplicadas

### Loader (discovery)

Se excluyen rutas que cumplan:
- filename/stem normalizado en: `references`, `referencias`, `bibliografia`, `bibliografica`, `bibliograficas`
- cualquier carpeta en la ruta llamada `references` o `referencias`
- se mantienen exclusiones existentes (`alerts.json`, `*.sample.json`, prefijos "_" o "__")

Archivo: `app/core/loaders.py`

### Catalogo (doble seguridad)

En `build_catalog` se filtran items que cumplan:
- `categoria` en keywords de referencias
- `format_id` contiene `references`/`referencias`
- `path.stem` en keywords
- `titulo` normalizado coincide con keywords

Archivo: `app/modules/catalog/service.py`

## 4) Evidencia (antes / despues)

Antes:
- Aparician cards “References” en Caratulas, Ver Todo y Todos.
- IDs detectados: `unac-references`, `uni-references`.

Despues:
- `discover_format_files()` ya no devuelve items con `references`.
- El catalogo no incluye cards de referencias.

## 5) Checklist final

- [x] References no aparece en Caratulas
- [x] References no aparece en Ver Todo
- [x] References no aparece en Todos
- [x] Acceso rapido “Referencias Bibliograficas” sigue abriendo `/referencias`
- [x] Discovery de formatos reales no se ve afectado

