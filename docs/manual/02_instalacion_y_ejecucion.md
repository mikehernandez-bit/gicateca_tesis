# Instalacion y Ejecucion

## Prerrequisitos

| Requisito | Version | Notas |
|-----------|---------|-------|
| Python | 3.13+ | Verificar con `py --version`. Testeado con 3.14.2 |
| Microsoft Word | 2016+ | **Solo Windows**. Requerido para conversion PDF |
| pip | Actualizado | `py -m pip install --upgrade pip` |
| `PYTHONIOENCODING` | `utf-8` | **Requerido en Windows** (ver nota abajo) |

> **⚠️ Windows:** Antes de ejecutar scripts o tests, configurar encoding:
> ```bash
> $env:PYTHONIOENCODING='utf-8'
> ```
> Sin esto, scripts con emojis (ej: `validate_data.py`) fallan con `UnicodeEncodeError: 'charmap' codec`.

**Fuente:** `requirements.txt`, `pyproject.toml`

---

## Pasos de Instalacion

### 1. Clonar el Repositorio

```bash
git clone <url-del-repo>
cd gicateca_tesis
```

### 2. Crear Entorno Virtual

```bash
py -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Contenido de requirements.txt:**
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
jinja2==3.1.4
pydantic==2.10.6
python-docx==1.1.2
python-multipart==0.0.20
docx2pdf==0.1.8
pywin32==308
pytest==8.3.4
jsonschema==4.23.0
```

**Fuente:** `requirements.txt` L1-10

### 4. Ejecutar el Servidor

```bash
py -m uvicorn app.main:app --reload
```

El servidor estara disponible en: `http://127.0.0.1:8000`

**Fuente:** `app/main.py` L46

---

## Variables de Entorno

| Variable | Requerida | Default | Ejemplo | Descripcion |
|----------|-----------|---------|---------|-------------|
| `GICATESIS_API_KEY` | No | (vacio) | `mi-clave-secreta` | Si se define, `/api/v1/*` exige header `X-GICATESIS-KEY` |
| `GICATESIS_CORS_ORIGINS` | No | `http://localhost:3000,http://localhost:5678,http://127.0.0.1:5678` | `http://mi-frontend:3000` | Origenes CORS separados por coma |
| `GICA_DEFAULT_UNI` | No | `unac` | `uni` | Codigo de universidad por defecto |
| `PDF_CACHE_MAX_AGE` | No | `3600` | `7200` | Segundos de cache para PDFs |
| `PDF_PREWARM_ON_STARTUP` | No | `false` | `true` | Si es `true`, genera PDFs al iniciar |
| `PDF_CONVERSION_TIMEOUT` | No | `120` | `300` | Timeout en segundos para Word COM |
| `GICA_VALIDATE_DATA` | No | (vacio) | `1` | Activar validacion de datos en startup |

**Fuentes:**
- `app/main.py` L34 (API_KEY), L49-52 (CORS_ORIGINS)
- `app/core/settings.py` L49 (GICA_DEFAULT_UNI)
- `app/modules/formats/router.py` (PDF_CACHE_MAX_AGE, PDF_PREWARM_ON_STARTUP, PDF_CONVERSION_TIMEOUT)

---

## Como Correr Tests

> Guia detallada: [`17_validacion_y_tests.md`](17_validacion_y_tests.md)  
> Informe QA completo: [`QA_AUDIT.md`](../QA_AUDIT.md)

### Comandos Rapidos

```bash
# Todos los tests (~220 tests, 10 archivos)
python -m pytest tests/ -v

# Tests rapidos (excluir stress tests lentos)
python -m pytest tests/ -v --ignore=tests/test_n8n_stress_scenarios.py

# Tests por modulo
python -m pytest tests/ -k "engine" -v      # Block Engine (renderers, normalizer, registry)
python -m pytest tests/ -k "api" -v         # API endpoints y service
python -m pytest tests/ -k "cover" -v       # View-model de caratula
python -m pytest tests/ -k "catalog" -v     # Reglas de catalogo publico

# Validacion de datos
python scripts/validate_data.py             # Normal
python scripts/validate_data.py --strict    # CI: falla en warnings
python scripts/validate_data.py --uni unac  # Solo UNAC

# Check de encoding
python scripts/check_encoding.py
```

### Estado de Cobertura

| Categoria | Tests Existentes | Modulos Sin Tests |
|-----------|-----------------|-------------------|
| P0 (criticos) | Engine (~140 tests) | generation/, auth, render/* |
| P1 (importantes) | API, view-model, validation (~32 tests) | catalog, formats, PDF, settings |
| P2 (secundarios) | catalog rules, data (~47 tests) | alerts, admin, frontend JS |

Ver la matriz completa en [`QA_AUDIT.md`](../QA_AUDIT.md#bloque-6-matriz-feature-vs-test-coverage).

---

## Verificar Instalacion

1. Navegar a `http://127.0.0.1:8000/` -> Debe mostrar la pagina de inicio.
2. Navegar a `http://127.0.0.1:8000/catalog` -> Debe listar formatos.
3. Navegar a `http://127.0.0.1:8000/docs` -> Swagger UI de FastAPI.
4. Navegar a `http://127.0.0.1:8000/api/v1/formats/version` -> Debe retornar JSON con version del catalogo.
5. Ejecutar `python -m pytest tests/ -v` -> Todos los tests deben pasar (exit code 0).
