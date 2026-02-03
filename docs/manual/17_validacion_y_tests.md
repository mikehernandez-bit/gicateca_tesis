# Validación y Tests

Esta guía explica cómo ejecutar validaciones y tests en GicaTesis.

## Validación de Datos

El script `validate_data.py` verifica la integridad de los datos en `app/data/`.

### Ejecución Básica

```bash
python scripts/validate_data.py
```

### Opciones

| Opción | Descripción |
|--------|-------------|
| `--strict` | Warnings también cuentan como fallo |
| `--uni CODE` | Validar solo una universidad (ej: `--uni unac`) |
| `--path DIR` | Usar directorio alternativo |

### Qué Valida

1. **Schema de formatos** (`format.schema.json`):
   - `_meta.id` existe y no vacío
   - `_meta.uni` existe y minúsculas

2. **Reglas de negocio**:
   - `_meta.uni` coincide con carpeta (evita errores de asignación)
   - `ruta_logo` tiene formato válido

3. **Verificaciones de repositorio**:
   - Sin colisiones de IDs
   - Providers registrados para cada carpeta
   - Assets requeridos existen (`LogoGeneric.png`)

4. **References config**:
   - `enabled` es array no vacío
   - `default` está en `enabled`

### Códigos de Error Comunes

| Código | Severidad | Descripción |
|--------|-----------|-------------|
| `META_MISSING` | ERROR | Falta campo `_meta` |
| `META_UNI_MISSING` | ERROR | Falta `_meta.uni` |
| `UNI_MISMATCH` | ERROR | `_meta.uni` no coincide con carpeta |
| `ID_COLLISION` | ERROR | ID duplicado en otro formato |
| `ASSET_MISSING` | ERROR | Asset requerido no existe |
| `META_UNI_CASE` | WARN | `_meta.uni` debería ser minúsculas |
| `PROVIDER_MISSING` | WARN | Carpeta sin provider registrado |

---

## Tests

### Ejecutar Tests

```bash
# Todos los tests
python -m pytest tests/ -v

# Tests específicos
python tests/test_cover_view_model.py
python tests/test_repo_validation.py
```

### Tests Disponibles

| Archivo | Cubre |
|---------|-------|
| `test_cover_view_model.py` | View-model UNAC/UNI, fallbacks, normalización logo |
| `test_repo_validation.py` | Schema, reglas, colisiones ID, references_config |

---

## Integración CI/Dev

### Modo Estricto (CI)

```bash
python scripts/validate_data.py --strict
```

Exit code 1 si hay cualquier error o warning.

### Variable de Entorno (Opcional)

```bash
# Activar validación en startup (dev/CI)
GICA_VALIDATE_DATA=1 python -m uvicorn app.main:app
```

---

## Troubleshooting

### "Mi universidad nueva no aparece"

1. Verificar que existe `app/universities/<code>/provider.py` con `PROVIDER`
2. Ejecutar `python scripts/validate_data.py --uni <code>`
3. Revisar que `_meta.uni` coincide con el código de carpeta

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

Cada formato debe tener un `_meta.id` único. Usar prefijos por universidad:
- `unac-informe-tesis`
- `uni-proyecto-maestria`
