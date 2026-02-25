# Validacion y Tests

Esta guia explica como ejecutar validaciones y tests en GicaTesis.

> Ver tambien: [`QA_AUDIT.md`](../QA_AUDIT.md) para el reporte completo de ejecucion de tests.

---

## Prerequisitos para Ejecutar Tests

```bash
# REQUERIDO en Windows — sin esto, scripts con emojis fallan
$env:PYTHONIOENCODING='utf-8'

# Instalar dependencias (incluye pytest)
pip install -r requirements.txt
```

> **⚠️ Nota Windows:** Sin `PYTHONIOENCODING=utf-8`, scripts como `validate_data.py` fallan con `UnicodeEncodeError: 'charmap' codec`.

---

## Validacion de Datos

El script `validate_data.py` verifica la integridad de los datos en `app/data/`.

### Ejecucion Basica

```bash
$env:PYTHONIOENCODING='utf-8'  # Windows
python scripts/validate_data.py
```

### Opciones

| Opcion | Descripcion |
|--------|-------------|
| `--strict` | Warnings tambien cuentan como fallo |
| `--uni CODE` | Validar solo una universidad (ej: `--uni unac`) |
| `--path DIR` | Usar directorio alternativo |

### Que Valida

1. **Schema de formatos** (`format.schema.json`):
   - `_meta.id` existe y no vacio
   - `_meta.uni` existe y minusculas

2. **Reglas de negocio**:
   - `_meta.uni` coincide con carpeta
   - `ruta_logo` tiene formato valido

3. **Verificaciones de repositorio**:
   - Sin colisiones de IDs
   - Providers registrados para cada carpeta
   - Assets requeridos existen (`LogoGeneric.png`)

4. **References config**:
   - `enabled` es array no vacio
   - `default` esta en `enabled`

### Codigos de Error Comunes

| Codigo | Severidad | Descripcion |
|--------|-----------|-------------|
| `META_MISSING` | ERROR | Falta campo `_meta` |
| `META_UNI_MISSING` | ERROR | Falta `_meta.uni` |
| `UNI_MISMATCH` | ERROR | `_meta.uni` no coincide con carpeta |
| `ID_COLLISION` | ERROR | ID duplicado en otro formato |
| `ASSET_MISSING` | ERROR | Asset requerido no existe |
| `META_UNI_CASE` | WARN | `_meta.uni` deberia ser minusculas |
| `PROVIDER_MISSING` | WARN | Carpeta sin provider registrado |

---

## Tests (pytest)

### Ejecutar Tests

```bash
# Todos los tests (253 tests, ~35s)
$env:PYTHONIOENCODING='utf-8'
python -m pytest tests/ -v

# Tests rapidos (excluir stress tests)
python -m pytest tests/ -v --ignore=tests/test_n8n_stress_scenarios.py

# Tests por modulo (keyword match)
python -m pytest tests/ -k "engine" -v
python -m pytest tests/ -k "api" -v
python -m pytest tests/ -k "cover" -v
python -m pytest tests/ -k "catalog" -v
```

### Tests Disponibles

| Archivo | ~Tests | Tipo | Cubre |
|---------|--------|------|-------|
| `test_engine_renderers.py` | 60 | Unit | 19 tipos de bloque (engine) |
| `test_engine_normalizer.py` | 50 | Unit | JSON -> Block[] (engine) |
| `test_engine_registry.py` | 30 | Unit | Registro, despacho, errores (engine) |
| `test_n8n_stress_scenarios.py` | 40 | Integration | 20 escenarios de estres n8n/GicaGen |
| `test_api_endpoints.py` | 12 | Integration | Endpoints HTTP de la API v1 |
| `test_api_service.py` | 10 | Unit | Hash, DTOs, version (API service) |
| `test_public_catalog_rules.py` | 5 | Integration | Reglas catalogo publico |
| `test_repo_validation.py` | 6 | Unit | Schema, reglas, colisiones |
| `test_cover_view_model.py` | 4 | Unit | View-model UNAC/UNI, fallbacks |
| `test_data.py` | 2 | Smoke | Integridad de datos JSON |
| **Total** | **253** | | **Ultima ejecucion: 253 PASS (2026-02-17)** |

**Fuente:** `tests/` (10 archivos + `conftest.py`)

### Fixtures Compartidos (conftest.py)

| Fixture | Scope | Descripcion |
|---------|-------|-------------|
| `project_root` | session | Ruta raiz del proyecto |
| `data_dir` | session | `app/data/` |
| `unac_data_dir` | session | `app/data/unac/` |
| `uni_data_dir` | session | `app/data/uni/` |

---

## Scripts Adicionales

| Script | Proposito | Ultimo resultado (2026-02-17) |
|--------|-----------|-------------------------------|
| `scripts/validate_data.py` | Validacion de datos JSON | ✅ PASS (0 errores, 0 warnings) |
| `scripts/validate_data.py --strict` | Validacion estricta | ✅ PASS |
| `scripts/check_encoding.py` | Detecta chars prohibidos | ❌ FAIL (96 issues en 11 archivos) |
| `scripts/check_mojibake.py` | Detecta mojibake | ❌ FAIL (mismos 96 issues) |
| `scripts/test_universal_gen.py` | Genera DOCX de prueba | ✅ PASS (test_universal.docx generado) |
| `scripts/fix_mojibake_json.py` | Corrige mojibake en JSON | Manual — ejecutar si se detecta mojibake |
| `scripts/fix_to_utf8.py` | Corrige encoding de archivos | Manual — ejecutar si hay archivos no UTF-8 |

---

## Matriz de Cobertura (Resumen)

> Matriz completa en [`QA_AUDIT.md` BLOQUE 6](../QA_AUDIT.md#bloque-6-gap-analysis-que-falta).

| Categoria | Con Tests | Sin Tests | % |
|-----------|-----------|-----------|---|
| P0 (criticos) | 1 (engine) | 4 (gen, render, auth, generator) | ~20% |
| P1 (importantes) | 3 (API, view-model, validation) | 7 (catalog, formats, refs, PDF...) | ~30% |
| P2 (secundarios) | 1 (catalog rules) | 3 (alerts, admin, encoding) | ~25% |
| **Total** | **253 tests** | **~14 modulos sin tests** | **~35%** |

---

## Integracion CI/Dev

### Modo Estricto (CI)

```bash
$env:PYTHONIOENCODING='utf-8'
python scripts/validate_data.py --strict
```

Exit code 1 si hay cualquier error o warning.

### Variable de Entorno (Opcional)

```bash
GICA_VALIDATE_DATA=1 python -m uvicorn app.main:app
```

### CI Propuesto

Ver [`QA_AUDIT.md` BLOQUE 6](../QA_AUDIT.md#recomendaciones-ci) para pipeline YAML propuesto.

---

## Validaciones de render GicaGen -> GicaTesis

Esta capa valida que el documento final no incluya placeholders o markdown
residual cuando llega `ai_result` desde GicaGen.

### Reglas esperadas

1. Caratula:
   - Si el formato trae titulo placeholder, se reemplaza por `values.title`
     (fallback: `project_title`, `projectTitle`, `project.title`).
2. Indice de abreviaturas:
   - Se renderiza como tabla de 2 columnas (`SIGLA | SIGNIFICADO`), alineada a
     la izquierda, sin bullets ni numeracion.
3. Capitulo:
   - El salto se aplica antes de cada capitulo; no se inserta salto justo
     despues del titulo.
4. Imagenes:
   - `ruta == "placeholder"` o ruta inexistente -> imagen omitida.
5. Texto IA:
   - Se limpia markdown y placeholders (`FIGURA DE EJEMPLO`, `[Insertar ...]`)
     antes de inyectar al JSON de render.

### Formato recomendado para abreviaturas

Se aceptan estas variantes por linea:

- `IA: Inteligencia Artificial`
- `IA - Inteligencia Artificial`
- `IA<TAB>Inteligencia Artificial`

---

## Troubleshooting

### "UnicodeEncodeError: 'charmap' codec" (Windows)

**Causa:** Console encoding cp1252 no soporta emojis usados en scripts.
**Solucion:**
```bash
$env:PYTHONIOENCODING='utf-8'
# Luego ejecutar el script normalmente
```

### "Encoding check failed" (96 issues)

**Causa:** Box-drawing characters (U+2500, U+251C, U+2502, U+2514) en comentarios de 11 archivos.
**Estado:** Conocido, pendiente de limpieza. No afecta funcionalidad — son decoradores visuales en comentarios.
**Archivos mas afectados:** `test_engine_renderers.py` (36), `test_engine_normalizer.py` (18), `test_engine_registry.py` (10)

### "Mi universidad nueva no aparece"

1. Verificar que existe `app/universities/<code>/provider.py` con `PROVIDER`
2. Ejecutar `python scripts/validate_data.py --uni <code>`
3. Revisar que `_meta.uni` coincide con el codigo de carpeta

### "Logo no se muestra"

Cadena de fallback:
1. `configuracion.ruta_logo` del formato
2. `provider.default_logo_url` de la universidad
3. `/static/assets/LogoGeneric.png`

Verificar con:
```bash
python scripts/validate_data.py | grep LOGO
```

### "ID duplicado"

Cada formato debe tener un `_meta.id` unico. Usar prefijos por universidad:
- `unac-informe-tesis`
- `uni-proyecto-maestria`
