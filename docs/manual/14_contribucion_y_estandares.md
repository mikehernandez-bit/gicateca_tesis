# Contribucion y Estandares

## Como Contribuir

### 1. Clonar y Configurar

```bash
git clone <url-del-repo>
cd gicateca_tesis
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Crear Branch de Feature

```bash
git checkout -b feature/mi-nueva-funcionalidad
```

### 3. Hacer Cambios

- Seguir los estandares de codigo (ver abajo).
- Agregar fuentes en la documentacion.
- Probar localmente.

### 4. Commit y Push

```bash
git add .
git commit -m "feat: descripcion de la funcionalidad"
git push origin feature/mi-nueva-funcionalidad
```

### 5. Pull Request

- Crear PR hacia `main` o `develop`.
- Describir los cambios.
- Esperar revision.

---

## Estandares de Codigo

### Python

| Regla | Detalle |
|-------|---------|
| Docstrings | Usar formato multilinea al inicio de cada archivo |
| Encoding | UTF-8 para todos los archivos |
| Imports | Agrupar: stdlib, terceros, locales |
| Tipos | Usar type hints cuando sea posible |
| Nombres | snake_case para variables y funciones |

**Ejemplo de docstring de archivo:**

```python
"""
Archivo: app/modules/catalog/router.py
Proposito:
- Define rutas HTTP del catalogo de formatos.

Responsabilidades:
- Registrar endpoints GET /catalog y POST /catalog/generate.
- Delegar logica de negocio a service.py.

No hace:
- No accede directamente a archivos JSON.

Entradas/Salidas:
- Entradas: Request HTTP con query params.
- Salidas: HTMLResponse o FileResponse.

Dependencias:
- fastapi, app.core.templates, app.modules.catalog.service.

Puntos de extension:
- Agregar filtros adicionales.

Donde tocar si falla:
- Revisar service.py y templates/pages/catalog.html.
"""
```

**Fuente:** `app/modules/catalog/router.py` L1-24

### JSON

| Regla | Detalle |
|-------|---------|
| Encoding | UTF-8 (sin BOM) |
| Indentacion | 2 espacios |
| Keys | snake_case en espanol |

### Documentacion

| Regla | Detalle |
|-------|---------|
| Fuentes | Citar archivo y lineas |
| Idioma | Espanol |
| Formato | Markdown |

---

## Agregar un Nuevo Modulo

### Checklist

1. **Crear directorio:**
   ```
   app/modules/nuevo_modulo/
   +-- __init__.py
   +-- router.py
   `-- service.py  (opcional)
   ```

2. **Crear router:**
   ```python
   from fastapi import APIRouter

   router = APIRouter()

   @router.get("/nuevo")
   def nuevo_endpoint():
       return {"status": "ok"}
   ```

3. **Registrar en `main.py`:**
   ```python
   from app.modules.nuevo_modulo import router as nuevo_router

   # En la seccion de includes:
   app.include_router(nuevo_router.router, tags=["NuevoModulo"])
   ```

4. **Crear template** (si aplica):
   ```
   app/templates/pages/nuevo.html
   ```

5. **Documentar:**
   - Agregar seccion en el manual.
   - Citar fuentes.

---

## Scripts de Utilidad

| Script | Proposito |
|--------|-----------|
| `scripts/check_encoding.py` | Verifica encoding de archivos |
| `scripts/check_mojibake.py` | Detecta caracteres corruptos |
| `scripts/fix_mojibake_json.py` | Corrige mojibake en JSON |
| `scripts/fix_to_utf8.py` | Convierte archivos a UTF-8 |
| `scripts/test_universal_gen.py` | Test rapido del generador unificado |
| `scripts/validate_data.py` | Validacion de datos JSON |

**Fuente:** `scripts/` (6 archivos)
