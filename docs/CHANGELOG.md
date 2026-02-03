# Changelog

## 2026-02-02

### Fase 3: Calidad, Validación y Tests

- **[NUEVO]** `app/data/schemas/format.schema.json`: Schema JSON para validar formatos.
- **[NUEVO]** `app/data/schemas/references_config.schema.json`: Schema para references_config.
- **[NUEVO]** `app/core/validation/`: Módulo de validación con:
  - `issue.py`: Tipo Issue con severidad ERROR/WARN
  - `format_validation.py`: Validador de formatos
  - `references_validation.py`: Validador de references_config
  - `repo_checks.py`: Verificaciones de repositorio (colisiones, providers, assets)
- **[NUEVO]** `scripts/validate_data.py`: CLI para validar datos
- **[NUEVO]** `tests/test_cover_view_model.py`: Tests unitarios de view-model
- **[NUEVO]** `tests/test_repo_validation.py`: Tests de validación
- **[MODIFICADO]** `requirements.txt`: Agregados pytest y jsonschema

### Fase 2: Backend View-Models + Frontend "Tonto"

- `app/core/settings.py`: Configuración `get_default_uni_code()`
- `app/core/view_models.py`: `build_cover_view_model()`
- Endpoint `GET /formatos/{id}/cover-model`
- `app/static/assets/LogoGeneric.png`: Fallback genérico
- Providers UNAC/UNI con `default_logo_url` y `defaults`
- `cover-preview.js`: Sin hardcodes UNI/UNAC

### Fase 1: Limpieza JS

- `gica-dom.js`, `gica-api.js`: Helpers centralizados
- Scripts en orden correcto en `base.html`
