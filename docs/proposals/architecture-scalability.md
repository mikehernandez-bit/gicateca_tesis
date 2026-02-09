# Propuesta de Arquitectura Escalable: Universidad como Plugin

> **Documento:** Propuesta técnica (solo documentación, sin implementación)  
> **Fecha:** 2026-02-02  
> **Estado:** ✅ Versión final lista para implementación  
> **Basado en:** Análisis del repositorio GicaTesis actual

---

## 1. Resumen Ejecutivo

**Problema actual:**
- Hardcodes de UNI/UNAC en frontend (funciones `resolveUni`, `resolveLogo`, defaults de lugar/año)
- Lógica de decisión por universidad en JavaScript
- Agregar una universidad requiere modificar código JS

**Objetivo:**
- "Universidad como plugin": agregar universidad = crear carpeta + provider + logo, SIN tocar JS/templates
- Backend como fuente única de verdad para defaults, logos y normalización
- Frontend solo renderiza datos ya procesados (view-models)

**Beneficios:**
- Escalabilidad real: ~20 min para agregar universidad nueva
- Cero riesgo de divergencia entre universidades
- Cambios en reglas se hacen en 1 lugar (provider)

---

## 2. Garantía: Agregar Universidad NO Toca JS/Templates

> Esta es una regla fundamental del proyecto.

- ✅ **Agregar universidad** = crear provider + datos + logo
- ❌ **NO modificar** `catalog.js`, `format-viewer.js`, `cover-preview.js`
- ❌ **NO modificar** `catalog.html`, `detail.html`, `cover_modal.html`
- ❌ **NO agregar** condiciones `if (uni === "nueva")` en ningún archivo

---

## 3. Contrato de University Code (`uni_code`)

### Definición

| Propiedad | Valor |
|-----------|-------|
| **Nombre** | `uni_code` |
| **Tipo** | `string` |
| **Formato** | **Minúsculas**, sin espacios, alfanumérico con guiones permitidos |
| **Ejemplos** | `unac`, `uni`, `usmp`, `pucp` |

### Fuente de Verdad

La fuente canónica es `_meta.uni` en cada JSON de formato:

```json
{
    "_meta": {
        "id": "unac-informe-tesis-cual",
        "uni": "unac",  // <-- FUENTE DE VERDAD
        "categoria": "informe"
    }
}
```

### Configuración de DEFAULT_UNI

> **Requisito para implementación:** Crear helper y variable de entorno.

| Elemento | Valor |
|----------|-------|
| **Variable de entorno** | `GICA_DEFAULT_UNI` |
| **Valor por defecto** | `"unac"` (si no está definida) |
| **Ubicación propuesta** | `app/core/settings.py` |
| **Helper propuesto** | `get_default_uni_code() -> str` |

**Comportamiento del Fallback:**

```
1. Leer _meta.uni del formato
   +--- Si existe y es válido → usar ese valor
   `--- Si falta o vacío:
      +--- Emitir WARNING: "Formato sin _meta.uni, usando DEFAULT_UNI"
      `--- Usar get_default_uni_code()
          +--- Leer GICA_DEFAULT_UNI del entorno
          +--- Si no existe → usar "unac"
          `--- Validar que exista en registry
              `--- Si no existe → WARNING adicional + usar "unac"
```

⚠️ **ANTIPATRÓN:** NO inferir `uni_code` desde prefijo de `format_id`.

### Dónde se Usa `uni_code`

| Componente | Uso |
|------------|-----|
| `app/core/registry.py` | Indexa providers por `provider.code` |
| `app/core/loaders.py` | Descubre formatos bajo `app/data/<uni_code>/` |
| `app/universities/<uni_code>/provider.py` | Define `code="<uni_code>"` |
| Templates | `data-uni="{{ format._meta.uni }}"` |

---

## 4. Estrategia Escalable de Logos

### Convención de Nombres

| Elemento | Regla | Ejemplo |
|----------|-------|---------|
| `uni_code` | minúsculas | `unac`, `usmp` |
| Archivo logo | `Logo` + `uni_code.upper()` + `.png` | `LogoUNAC.png` |
| Ruta | `/static/assets/` + archivo | `/static/assets/LogoUNAC.png` |

### Fórmula Exacta

```python
logo_filename = f"Logo{uni_code.upper()}.png"
logo_url = f"/static/assets/{logo_filename}"
```

> **Nota cross-platform:** Se adopta UPPERCASE como estándar para consistencia con Linux/macOS.

### Cadena de Resolución

| Prioridad | Fuente | Descripción |
|-----------|--------|-------------|
| 1 | `data.configuracion.ruta_logo` | Override específico del formato |
| 2 | `provider.default_logo_url` | Default del provider |
| 3 | `/static/assets/LogoGeneric.png` | Fallback genérico |

### Requisito: LogoGeneric.png

> ⚠️ **REQUISITO PARA IMPLEMENTACIÓN**
> 
> Agregar el archivo: `app/static/assets/LogoGeneric.png`
> 
> Este asset es obligatorio para garantizar "cero logos rotos".

**Comportamiento si falta LogoGeneric:**

Si `LogoGeneric.png` no existe durante runtime:
1. Backend **NUNCA** devuelve `null` o string vacío en `logo_url`
2. Fallback mínimo: `provider.default_logo_url`
3. Si todo falla: devolver `/static/assets/LogoGeneric.png` (y el frontend mostrará imagen rota hasta que se agregue)

---

## 5. Diferencia entre `display_name` y `defaults["universidad"]`

| Campo | Propósito | Ejemplo |
|-------|-----------|---------|
| `display_name` | Sigla corta para UI (menús, badges) | `"UNAC"` |
| `defaults["universidad"]` | Nombre largo para carátula | `"UNIVERSIDAD NACIONAL DEL CALLAO"` |

### Regla de Resolución

```python
universidad = (
    data.caratula.universidad       # 1. Valor del formato
    or provider.defaults["universidad"]  # 2. Default del provider
    or provider.display_name        # 3. Fallback a sigla
)
```

---

## 6. Contratos View-Model Propuestos

### GET `/api/formatos/{id}/cover-model`

```json
{
    "logo_url": "/static/assets/LogoUNAC.png",
    "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
    "facultad": "FACULTAD DE...",
    "escuela": "",
    "titulo": "TÍTULO DEL PROYECTO",
    "frase": "Para optar el Título Profesional de",
    "grado": "INGENIERO DE SISTEMAS",
    "lugar": "CALLAO, PERÚ",
    "anio": "2026",
    "autor": "APELLIDO APELLIDO, NOMBRE",
    "asesor": "Mg. NOMBRE APELLIDO"
}
```

---

## 7. Próximos View-Models (Escalabilidad Futura)

> Estos endpoints son **opcionales** y se implementan después de `cover-model`, manteniendo endpoints legacy.

### GET `/api/catalog/view?uni=all|<uni_code>`

**Propósito:** Catálogo sin lógica por universidad en JS.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `items` | array | Lista de formatos |
| `items[].id` | string | format_id |
| `items[].uni_code` | string | Universidad |
| `items[].categoria` | string | Categoría |
| `items[].titulo` | string | Título del formato |
| `items[].descripcion` | string | Descripción corta |
| `items[].tags` | array | Etiquetas |
| `items[].thumbnail_url` | string | (opcional) Miniatura |

### GET `/api/referencias/view?uni=<uni_code>`

**Propósito:** Referencias habilitadas por universidad sin lógica en JS.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `enabled` | array | Lista de IDs de normas habilitadas |
| `default` | string | Norma por defecto |
| `norms` | array | Detalle de cada norma habilitada |
| `norms[].id` | string | ID de la norma |
| `norms[].titulo` | string | Título |
| `norms[].descripcion` | string | Descripción |

---

## 8. Checklist: Agregar Universidad Nueva

### Archivos a Crear

| Paso | Archivo |
|------|---------|
| 1 | `app/universities/<uni_code>/provider.py` |
| 2 | `app/static/assets/Logo<CODE>.png` |
| 3 | `app/data/<uni_code>/` (carpeta) |
| 4 | `app/data/<uni_code>/ejemplo.json` (mínimo 1 formato) |

### Provider Mínimo

```python
from pathlib import Path
from app.core.paths import get_data_dir
from app.universities.contracts import SimpleUniversityProvider

PROVIDER = SimpleUniversityProvider(
    code="usmp",
    display_name="USMP",
    data_dir=get_data_dir("usmp"),
    generator_map={},
    default_logo_url="/static/assets/LogoUSMP.png",
    defaults={
        "universidad": "UNIVERSIDAD DE SAN MARTÍN DE PORRES",
        "lugar": "LIMA, PERÚ",
        "anio": "2026"
    }
)
```

### Qué NO Tocar ❌

- Ningún archivo `.js`
- Ningún archivo `.html`
- `app/core/registry.py`

### Verificación

```bash
py -c "from app.core.registry import list_universities; print(list_universities())"
py -m uvicorn app.main:app --reload
```

---

## 9. Plan por Fases

### Implementación Mínima Recomendada

> Comenzar directamente por Fase 2 para acelerar escalabilidad.

---

### Fase 1: Limpieza JS (OPCIONAL)

Extraer helpers `gica-dom.js`, `gica-api.js`.

**Definition of Done:** Helpers funcionando, mismo resultado visual.

---

### Fase 2: Backend View-Models (PRINCIPAL)

| Tarea | Descripción |
|-------|-------------|
| Extender `contracts.py` | Agregar `defaults`, `default_logo_url` |
| Crear `view_models.py` | `build_cover_view_model()` |
| Crear `settings.py` | `GICA_DEFAULT_UNI`, `get_default_uni_code()` |
| Nuevo endpoint | `GET /api/formatos/{id}/cover-model` |
| Agregar asset | `LogoGeneric.png` |
| Actualizar JS | Consumir view-model, eliminar hardcodes |

**Definition of Done:**
- [ ] Endpoint devuelve JSON con campos resueltos
- [ ] 0 hardcodes UNI/UNAC en JS
- [ ] `LogoGeneric.png` existe
- [ ] Agregar universidad funciona sin tocar JS

---

### Fase 3: Calidad

Tests, JSON Schema, documentación final.

---

## 10. Riesgos y Mitigaciones

| # | Riesgo | Mitigación |
|---|--------|------------|
| 1 | Hardcode en JS | Fase 2 los elimina |
| 2 | Provider rompe catálogo | Validar antes de merge |
| 3 | Logo no encontrado | Fallback a `LogoGeneric.png` |
| 4 | `_meta.uni` ausente | `DEFAULT_UNI` configurable |
| 5 | format_id collision | Verificación en loaders |

---

## 11. Verificación Manual

- [ ] `/catalog` carga sin errores
- [ ] Carátulas → modal abre con logo correcto
- [ ] Universidad muestra nombre largo
- [ ] Referencias carga por universidad
- [ ] Consola sin errores

---

## 12. Estado de Completitud

| Requisito | Estado |
|-----------|--------|
| `uni_code` como fuente de verdad | ✅ |
| No inferir por format_id | ✅ |
| Resolución de logo en backend | ✅ |
| Defaults en provider | ✅ |
| `cover-model` endpoint definido | ✅ |
| Agregar universidad sin tocar JS | ✅ |
| Estrategia docs/changelog | ✅ |
| DEFAULT_UNI configurable | ✅ |
| LogoGeneric.png como requisito | ✅ |
| Próximos view-models documentados | ✅ |

---

> **Recordatorio:** Este documento es una PROPUESTA. Ningún cambio de código ha sido implementado.
