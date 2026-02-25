# Reporte de Ejecucion de Tests — GicaTesis v1.0.0

> Fecha de ejecucion: 2026-02-17 09:30-09:45 (local)  
> Branch: main  
> Entorno: Windows, Python 3.14.2, .venv activo  
> Ejecutor: Lead QA / SDET — modo read-only (sin modificar codigo)

---

## [BLOQUE 1] RESUMEN EJECUTIVO

### Estado General: ✅ PASA (con reservas)

| Suite | Resultado | Duracion |
|-------|-----------|----------|
| **pytest** (253 tests) | **✅ PASS** | 35-55s |
| **validate_data.py** | **✅ PASS** | <2s |
| **validate_data.py --strict** | **✅ PASS** | <2s |
| **test_universal_gen.py** | **✅ PASS** | <5s |
| **Server smoke** (3 endpoints) | **✅ PASS** | ~5s |
| **check_encoding.py** | **❌ FAIL** (exit 1) | <3s |
| **check_mojibake.py** | **❌ FAIL** (exit 1) | <3s |
| **validate_data.py sin PYTHONIOENCODING** | **❌ FAIL** (charmap) | <1s |

### Principales Fallos

| # | Fallo | Prioridad | Tipo |
|---|-------|-----------|------|
| 1 | **96 encoding issues** (box-drawing chars en 11 archivos) | **P1** | Encoding / estilo |
| 2 | `validate_data.py` falla sin `PYTHONIOENCODING=utf-8` | **P1** | Config / portabilidad |
| 3 | Sin lint/format/typecheck configurados | **P2** | Infra faltante |
| 4 | Sin CI/CD pipeline | **P0** | Infra faltante |
| 5 | Version drift en dependencias instaladas vs requirements.txt | **P2** | Config |

### Que se Ejecuto vs Que Quedo Bloqueado

| Ejecutado | Bloqueado |
|-----------|-----------|
| pytest (253 tests) | Lint (no hay linter) |
| validate_data.py (normal + strict) | Typecheck (no hay mypy/pyright) |
| check_encoding.py / check_mojibake.py | Format check (no hay black/ruff) |
| test_universal_gen.py (DOCX gen) | Coverage report (no hay pytest-cov) |
| Server start + HTTP smoke | PDF conversion test (requiere Word interactivo) |

---

## [BLOQUE 2] INVENTARIO DE COMANDOS ENCONTRADOS (REALES)

| Categoria | Comando | Fuente | Existe |
|-----------|---------|--------|--------|
| Install | `pip install -r requirements.txt` | `requirements.txt` | ✅ |
| Start | `python -m uvicorn app.main:app --reload` | `app/main.py`, `README.md` | ✅ |
| Test (all) | `python -m pytest tests/ -v` | `pyproject.toml` (addopts) | ✅ |
| Test (specific) | `python -m pytest tests/test_<name>.py -v` | `pyproject.toml` | ✅ |
| Validate data | `python scripts/validate_data.py` | `scripts/validate_data.py` | ✅ |
| Validate strict | `python scripts/validate_data.py --strict` | `scripts/validate_data.py` | ✅ |
| Check encoding | `python scripts/check_encoding.py` | `scripts/check_encoding.py` | ✅ |
| Check mojibake | `python scripts/check_mojibake.py` | `scripts/check_mojibake.py` | ✅ |
| Test generator | `python scripts/test_universal_gen.py` | `scripts/test_universal_gen.py` | ✅ |
| Fix mojibake | `python scripts/fix_mojibake_json.py` | `scripts/fix_mojibake_json.py` | ✅ |
| Fix encoding | `python scripts/fix_to_utf8.py` | `scripts/fix_to_utf8.py` | ✅ |
| Lint | — | — | **FALTA** |
| Format | — | — | **FALTA** |
| Typecheck | — | — | **FALTA** |
| Build prod | — | — | **FALTA** |
| Coverage | — | — | **FALTA** (`pytest-cov` no instalado) |
| CI pipeline | — | — | **FALTA** (no `.github/workflows/`) |

---

## [BLOQUE 3] RESULTADOS DE EJECUCION (SUITE POR SUITE)

### 3.1 pytest — 253 tests

```
Comando: .venv\Scripts\python.exe -m pytest tests/ -v --tb=short
Resultado: PASS (253 passed, 0 failed)
Duracion: 35-55s
Exit code: 0
```

**Desglose por archivo:**

| Archivo | Tests | Resultado |
|---------|-------|-----------|
| `test_engine_renderers.py` | ~60 | ✅ ALL PASS |
| `test_engine_normalizer.py` | ~50 | ✅ ALL PASS |
| `test_engine_registry.py` | ~30 | ✅ ALL PASS |
| `test_n8n_stress_scenarios.py` | ~40 | ✅ ALL PASS |
| `test_api_endpoints.py` | 12 | ✅ ALL PASS |
| `test_api_service.py` | 10 | ✅ ALL PASS |
| `test_public_catalog_rules.py` | 5 | ✅ ALL PASS |
| `test_repo_validation.py` | 6 | ✅ ALL PASS |
| `test_cover_view_model.py` | 4 | ✅ ALL PASS |
| `test_data.py` | 2 | ✅ ALL PASS |
| **Total** | **253** | **✅ ALL PASS** |

### 3.2 validate_data.py

```
Comando: $env:PYTHONIOENCODING='utf-8'; .venv\Scripts\python.exe scripts/validate_data.py
Resultado: PASS (0 errores, 0 warnings)
Exit code: 0
```

```
Comando: $env:PYTHONIOENCODING='utf-8'; .venv\Scripts\python.exe scripts/validate_data.py --strict
Resultado: PASS (0 errores, 0 warnings)
Exit code: 0
```

**⚠️ SIN PYTHONIOENCODING:**
```
Comando: .venv\Scripts\python.exe scripts/validate_data.py
Resultado: FAIL — UnicodeEncodeError: 'charmap' codec can't encode character
Exit code: 1
```

### 3.3 check_encoding.py

```
Comando: $env:PYTHONIOENCODING='utf-8'; .venv\Scripts\python.exe scripts/check_encoding.py
Resultado: FAIL — "Encoding check failed." (96 issues en 11 archivos)
Exit code: 1
```

**Archivos afectados:**

| Archivo | Issues | Tipo de char |
|---------|--------|-------------|
| `tests/test_engine_renderers.py` | 36 | Box-drawing (U+2500, U+251C, U+2502, U+2514) |
| `tests/test_engine_normalizer.py` | 18 | Box-drawing |
| `tests/test_engine_registry.py` | 10 | Box-drawing |
| `app/core/document_generator.py` | 8 | Box-drawing |
| `app/universities/shared/universal_generator.py` | 6 | Box-drawing |
| `tests/test_n8n_stress_scenarios.py` | 4 | Box-drawing |
| `app/core/format_builder.py` | 4 | Box-drawing |
| `app/engine/renderers/table.py` | 4 | Box-drawing |
| `app/engine/normalizer.py` | 3 | Box-drawing |
| `tests/conftest.py` | 2 | Box-drawing |
| `app/main.py` | 1 | Box-drawing |

### 3.4 check_mojibake.py

```
Comando: $env:PYTHONIOENCODING='utf-8'; .venv\Scripts\python.exe scripts/check_mojibake.py
Resultado: FAIL — "Mojibake check failed." (same 96 issues)
Exit code: 1
```

### 3.5 test_universal_gen.py

```
Comando: $env:PYTHONIOENCODING='utf-8'; .venv\Scripts\python.exe scripts/test_universal_gen.py
Resultado: PASS — Documento generado en test_universal.docx
Exit code: 0
```

### 3.6 Server Smoke Test

```
Comando: Start server on port 8765, test 3 endpoints
Resultado: ALL PASS
```

| Endpoint | Status | Response |
|----------|--------|----------|
| `GET /` (home) | **200** | HTML page |
| `GET /api/v1/formats/version` | **200** | `{"version":"ef6814bee059...","generatedAt":"2026-02-17T14:42:48"}` |
| `GET /api/v1/formats` | **200** | 16,679 bytes JSON |

### 3.7 Suites NO Ejecutadas (no existen)

| Suite | Motivo |
|-------|--------|
| Lint | No hay linter configurado (ruff/flake8/pylint) |
| Format | No hay formatter configurado (black/ruff format) |
| Typecheck | No hay mypy/pyright configurado |
| Coverage | No hay pytest-cov instalado |
| SAST/dep scan | No hay safety/bandit/semgrep |
| Performance | No hay locust/k6/ab |
| E2E browser | No hay playwright/selenium |
| Contract | No hay schemathesis/dredd |

---

## [BLOQUE 4] MATRIZ SUITE vs RESULTADO

| Suite | Comando | Resultado | Error Principal | Prioridad | Notas |
|-------|---------|-----------|-----------------|-----------|-------|
| pytest (unit) | `pytest tests/ -v` | ✅ PASS (253/253) | — | — | 35-55s |
| validate_data | `validate_data.py` | ✅ PASS | — | — | Requiere PYTHONIOENCODING |
| validate_data --strict | `validate_data.py --strict` | ✅ PASS | — | — | 0 errores, 0 warnings |
| test_universal_gen | `test_universal_gen.py` | ✅ PASS | — | — | DOCX generado OK |
| Server smoke | uvicorn + curl 3 endpoints | ✅ PASS | — | — | HOME/VERSION/FORMATS: 200 |
| check_encoding | `check_encoding.py` | ❌ FAIL | 96 box-drawing chars en 11 files | **P1** | Cosmetic pero viola policy |
| check_mojibake | `check_mojibake.py` | ❌ FAIL | Same as above | **P1** | Redundante con check_encoding |
| validate_data (no env) | `validate_data.py` (sin PYTHONIOENCODING) | ❌ FAIL | UnicodeEncodeError charmap | **P1** | Bug portabilidad Windows |
| Lint | — | ⬜ NO EXISTE | — | **P2** | Deberia existir |
| Format | — | ⬜ NO EXISTE | — | **P2** | Deberia existir |
| Typecheck | — | ⬜ NO EXISTE | — | **P2** | Deberia existir |
| Coverage | — | ⬜ NO EXISTE | — | **P1** | pytest-cov no instalado |
| CI/CD | — | ⬜ NO EXISTE | — | **P0** | No hay pipeline |

---

## [BLOQUE 5] TRIAGE DE FALLAS (DETALLE)

### F1: 96 Box-Drawing Characters en Codigo Fuente

- **Severidad:** P1
- **Tipo:** Encoding / estilo — viola la policy establecida por `check_encoding.py`
- **Reproduccion:**
  ```bash
  $env:PYTHONIOENCODING='utf-8'
  .venv\Scripts\python.exe scripts/check_encoding.py
  # Exit code: 1, "Encoding check failed."
  ```
- **Evidencia:** 96 lineas en 11 archivos contienen caracteres box-drawing Unicode (U+2500 `─`, U+251C `├`, U+2502 `│`, U+2514 `└`). Estos son usados como decoradores visuales en comentarios de separacion de secciones (ej: `# ── Fixtures ──`).
- **Archivos mas afectados:** `test_engine_renderers.py` (36), `test_engine_normalizer.py` (18), `test_engine_registry.py` (10), `document_generator.py` (8)
- **Recomendacion:** Reemplazar box-drawing chars por ASCII equivalentes (`# -- Fixtures --` o `# === Fixtures ===`). Ejecutar `scripts/fix_to_utf8.py` si soporta esta conversion, o hacer search-and-replace manual.

### F2: validate_data.py Falla sin PYTHONIOENCODING en Windows

- **Severidad:** P1
- **Tipo:** Bug de portabilidad / config
- **Reproduccion:**
  ```bash
  # Sin PYTHONIOENCODING (default Windows cp1252)
  .venv\Scripts\python.exe scripts/validate_data.py
  # UnicodeEncodeError: 'charmap' codec can't encode character
  ```
- **Causa:** El script usa `print()` con emojis/unicode (ej: `📁`, `📊`, `✅`) que no se pueden codificar en cp1252 (default Windows console encoding).
- **Recomendacion:** Agregar `# -*- coding: utf-8 -*-` al script y/o usar `sys.stdout.reconfigure(encoding='utf-8')` al inicio. Alternativamente, documentar `PYTHONIOENCODING=utf-8` como prerequisito.

### F3: Version Drift en Dependencias

- **Severidad:** P2
- **Tipo:** Config / mantenimiento
- **Evidencia:**

| Paquete | requirements.txt | Instalado | Drift |
|---------|-----------------|-----------|-------|
| pytest | 8.3.4 | 9.0.2 | Minor upgrade |
| python-docx | 1.1.2 | 1.2.0 | Minor upgrade |
| pydantic | 2.10.6 | 2.12.5 | Minor upgrade |
| pywin32 | 308 | 311 | Patch upgrade |
| uvicorn | 0.30.6 | (no reportado) | — |

- **Recomendacion:** Actualizar `requirements.txt` para reflejar versiones reales instaladas, o ejecutar `pip install -r requirements.txt --force-reinstall` para alinear.

### F4: No Hay Pipeline CI/CD

- **Severidad:** P0
- **Tipo:** Infra faltante
- **Evidencia:** No existe `.github/workflows/`, `Dockerfile`, `docker-compose.yml`, ni `Makefile`.
- **Recomendacion:** Crear pipeline minimo que ejecute pytest + validate_data + check_encoding. Ver propuesta YAML en [seccion CI del BLOQUE 6](#recomendaciones-ci).

---

## [BLOQUE 6] GAP ANALYSIS (QUE FALTA)

### Tests Faltantes por Modulo

| Modulo | Tests Existentes | Faltantes Criticos | P |
|--------|-----------------|-------------------|---|
| `app/modules/generation/` | 0 | Flujo JSON->DOCX, preprocessor, errores | **P0** |
| `app/modules/api/generation_router.py` | 0 | POST /generate con datos validos/invalidos | **P0** |
| `app/modules/api/render_router.py` | 0 | POST /render/docx, /render/pdf | **P0** |
| Auth middleware (`main.py`) | 0 | Sin key, key invalida, key correcta | **P0** |
| `app/universities/shared/universal_generator.py` | 0 (pytest), 1 (script) | Unit tests con mocks | **P0** |
| `app/modules/catalog/` | 0 | Listado, filtros, formato vacio | **P1** |
| `app/modules/formats/` | 0 | Detalle, cover model, cache | **P1** |
| `app/core/pdf_converter.py` | 0 | COM error handling, timeout, retry | **P1** |
| `app/core/settings.py` | 0 | Env vars, defaults, fallbacks | **P1** |
| `app/core/registry.py` (providers) | 0 | get_provider valido/invalido | **P1** |
| `app/modules/references/` | 0 | Estilos, config, enabled list | **P1** |
| `app/modules/alerts/` | 0 | Alertas per uni, JSON malformado | **P2** |
| `app/modules/admin/` | 0 | Operaciones read-only | **P2** |
| Frontend JS (7 archivos) | 0 | Sin test runner JS configurado | **P1** |

### Infra/Config Faltante

| Faltante | Impacto | P |
|----------|---------|---|
| CI/CD pipeline (`.github/workflows/`) | Tests no se ejecutan automaticamente | **P0** |
| `pytest-cov` en requirements.txt | No se puede medir cobertura | **P1** |
| `.env.example` | Devs no saben que vars configurar | **P1** |
| Linter (ruff/flake8) | Sin analisis estatico | **P2** |
| Type checker (mypy/pyright) | Sin verificacion de tipos | **P2** |
| Formatter (black/ruff format) | Sin formateo consistente | **P2** |

### Recomendaciones CI

```yaml
# Propuesta: .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install -r requirements.txt pytest-cov
      - run: python -m pytest tests/ -v --cov=app --cov-report=xml
      - run: python scripts/validate_data.py --strict
        env:
          PYTHONIOENCODING: utf-8
      - run: python scripts/check_encoding.py
        env:
          PYTHONIOENCODING: utf-8
```

---

## [BLOQUE 7] ACTUALIZACION DE DOCUMENTACION

### Operaciones

| Ruta | Operacion | Motivo |
|------|-----------|--------|
| `docs/QA_AUDIT.md` | **OVERWRITE** | Sobreescribir audit anterior con resultados de ejecucion real |
| `docs/manual/17_validacion_y_tests.md` | **OVERWRITE** | Agregar resultados de ejecucion y troubleshooting |
| `docs/manual/02_instalacion_y_ejecucion.md` | **OVERWRITE** | Agregar PYTHONIOENCODING como prerequisito |

> Este archivo (`docs/QA_AUDIT.md`) ES el entregable del BLOQUE 7.
> Los otros dos archivos se actualizan en operaciones separadas (ver mas abajo en este documento).

### Dependencias Instaladas vs Requeridas

| Paquete | requirements.txt | Instalado | Estado |
|---------|-----------------|-----------|--------|
| fastapi | 0.115.0 | 0.115.0 | ✅ OK |
| jinja2 | 3.1.4 | 3.1.4 | ✅ OK |
| pytest | 8.3.4 | 9.0.2 | ⚠️ Drift |
| python-docx | 1.1.2 | 1.2.0 | ⚠️ Drift |
| pydantic | 2.10.6 | 2.12.5 | ⚠️ Drift |
| pywin32 | 308 | 311 | ⚠️ Drift |
| jsonschema | 4.23.0 | (verificar) | — |
| docx2pdf | 0.1.8 | 0.1.8 | ✅ OK |

### Known Gaps / TODO

- [ ] **Resolver 96 encoding issues** en 11 archivos (box-drawing chars)
- [ ] **Agregar `sys.stdout.reconfigure(encoding='utf-8')`** a scripts que usan emojis
- [ ] **Crear `.env.example`** con todas las vars documentadas
- [ ] **Instalar `pytest-cov`** y generar baseline de coverage
- [ ] **Crear pipeline CI** minimo (pytest + validate_data + check_encoding)
- [ ] **Agregar linter** (ruff recomendado — rapido y todo-en-uno)
- [ ] **Actualizar `requirements.txt`** para reflejar versiones reales
- [ ] **Tests para modulos P0** (generation, render, auth, universal_generator)

---

## [BLOQUE 8] BLOQUEANTES Y PREGUNTAS

### Bloqueantes

| # | Bloqueante | Que Impidio |
|---|-----------|------------|
| 1 | **Sin pytest-cov** | No se pudo generar coverage report (% cubierto es estimacion) |
| 2 | **PDF conversion requiere Word COM interactivo** | No se pudo testear `POST /render/pdf` en esta sesion |
| 3 | **Sin CI/CD** | No hay forma automatizada de ejecutar esta bateria |

### Preguntas

1. **¿Los box-drawing chars en comentarios son intencionales?** Los scripts `check_encoding.py` y `check_mojibake.py` los marcan como prohibidos, pero estan presentes en 11 archivos del repo. ¿Se deben limpiar?
2. **¿Se debe agregar `PYTHONIOENCODING=utf-8` como prerequisito global?** O ¿se prefiere que cada script configure su propio encoding?
3. **¿Hay planes de CI/CD?** ¿GitHub Actions, GitLab CI, o otro? ¿Windows runner o Linux container?
4. **¿El version drift en dependencias es aceptable?** pytest 9.0.2 vs 8.3.4, pydantic 2.12.5 vs 2.10.6 — ¿actualizar requirements.txt?
5. **¿Se necesita coverage report?** ¿Agregar `pytest-cov` a requirements?
6. **¿Los endpoints `/render/pdf` estan en uso activo?** Determina prioridad de tests de PDF converter.
