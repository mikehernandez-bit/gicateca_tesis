# Changelog

## 2026-02-17

### Actualizacion Completa de Documentacion

- **[DOCS]** Sobreescritos 14 archivos de documentacion para reflejar estado real del codigo
- **[DOCS]** Corregida version de `0.1.0` a `1.0.0` en todos los docs
- **[DOCS]** Agregada tabla de variables de entorno (`GICATESIS_API_KEY`, `GICATESIS_CORS_ORIGINS`, `GICA_DEFAULT_UNI`)
- **[DOCS]** Actualizado `requirements.txt` en docs con versiones pinneadas reales
- **[DOCS]** Corregida estructura de providers: `centro_formatos/` reemplazado por `shared/universal_generator.py`
- **[DOCS]** Corregidas categorias UNI: `posgrado` (no `maestria`)
- **[DOCS]** Actualizado arbol de directorio: agregados `engine/`, `shared/`, 7 archivos JS (no 5)
- **[DOCS]** Corregida guia de integracion: autenticacion API key ya no es "Ninguna"
- **[DOCS]** Actualizada lista de tests: 10 archivos (no 2)
- **[DOCS]** Actualizada lista de scripts: 6 archivos (no 4)
- **[DOCS]** Link roto `../proposalsCODEX/` corregido a `../proposals/`
- **[NUEVO]** `docs/manual/16_block_engine.md`: Capitulo del Block Engine (pipeline, renderers, como extender)
- **[DOCS]** Agregados terminos Block Engine al glosario (Block, Normalizer, Renderer, etc.)

## 2026-02-16

### Fase 6: Auditoría Final y Producción

- **[FIX]** Agregado middleware CORS configurable via `GICATESIS_CORS_ORIGINS`
- **[FIX]** Todas las dependencias pinneadas en `requirements.txt` (pydantic==2.10.6, python-docx==1.1.2, etc.)
- **[FIX]** `finales.referencias` agregado a `unac_informe_cuant.json` y `uni_informe_apa.json` (estaban embebidas como capítulo IX en `cuerpo`)
- **[FIX]** `_meta.descripcion` y `_meta.version` agregados a `unac_proyecto_cual.json` y `unac_proyecto_cuant.json`
- **[FIX]** `seed_loader.py` apuntaba a `data/seed/` inexistente → corregido a `app/data/`
- **[FIX]** `anio` con `\n` residual en ambos proyecto UNAC
- **[FIX]** `print()` reemplazado por `logger.warning()` en `image.py` y `logo.py`
- **[FIX]** `set_cell_vertical_alignment()` ahora respeta el parámetro `alignment` (antes siempre era "center")
- **[FIX]** Universidades hardcodeadas extraídas a mapa configurable en `normalizer.py`
- **[FIX]** Bloque `logo` ahora transporta solo `configuracion` + `_meta` en vez del JSON completo
- **[FIX]** `info_table` ahora usa `format_cell_text()` para bold confiable
- **[FIX]** Endpoint `/formatos/{id}/versions` usa `_meta.version` real en vez de datos hardcodeados
- **[FIX]** Imports no usados eliminados de `primitives.py` (`re`, `List`)
- **[FIX]** Logging añadido a `add_styled_note()` en caso de error
- **[NUEVO]** `tests/conftest.py` con fixtures compartidos y sys.path centralizado
- **[NUEVO]** Link a `/referencias` en sidebar
- **[NUEVO]** `pyproject.toml` con configuración de pytest
- **[LIMPIEZA]** Eliminados 17 archivos temporales: `.bak`, scripts `_*.py`, `fix_*.py`, `migrate_*.py`, `tmp_helpers.py`, `debug_loader_v2.py`
- **[DOCS]** CHANGELOG actualizado con Fases 4-6
- **[DOCS]** README principal actualizado (estructura, rutas, engine)
- **[DOCS]** `GICAGEN_INTEGRATION_GUIDE.md` actualizado con endpoints de generation y render

### Fase 5: Stress Tests y Calidad de Datos

- **[NUEVO]** `tests/test_n8n_stress_scenarios.py`: 40 escenarios de estrés para n8n/GicaGen
- **[FIX]** Títulos de tabla duplicados corregidos en 5 archivos JSON
- **[FIX]** `unac_informe_cual.json` reemplazado con estructura cualitativa correcta (6 capítulos)
- **[FIX]** Tablas y figuras restauradas en `unac_informe_cual.json`

### Fase 4: Block Engine + Landscape Fix

- **[NUEVO]** `app/engine/`: Motor de bloques completo (19 tipos, 12 renderers)
  - `normalizer.py`: JSON → Block[] (695 líneas)
  - `registry.py`: Decorador `@register()` + `render_blocks()`
  - `primitives.py`: Helpers DOCX atómicos
  - `types.py`: Tipos Block y BlockRenderer
  - `renderers/`: 12 módulos especializados
- **[FIX]** Páginas en blanco después de tablas landscape (shrink section-break + skip redundant page_break)
- **[REFACTOR]** `universal_generator.py` reescrito de ~1023 a ~95 líneas usando block engine
- **[NUEVO]** `app/modules/generation/`: Módulo de generación para API
- **[NUEVO]** `app/modules/api/generation_router.py`: POST/GET artifacts
- **[NUEVO]** `app/modules/api/render_router.py`: POST render DOCX/PDF

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
