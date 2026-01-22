# Refactorización Arquitectónica - Separación de Responsabilidades

## 📋 Resumen de cambios

Se ha refactorizado la arquitectura de la aplicación para seguir correctamente el patrón **MVC (Model-View-Controller)** con separación de responsabilidades entre **Router** (orquestación HTTP) y **Service** (lógica de negocio).

---

## ✅ Archivos creados

### 1. `app/core/loaders.py` (NUEVO)
**Responsabilidad**: Funciones compartidas de acceso a datos

```python
- load_json_file(file_path) → Carga y valida archivos JSON
- get_data_dir() → Retorna ruta a directorio de datos
```

**Por qué**: 
- Elimina duplicación de código
- Centraliza la lógica de lectura de archivos
- Ambos módulos (catalog, formats) ahora usan la misma función

---

## 🔄 Archivos refactorizados

### 2. `app/modules/catalog/router.py`
**ANTES**: Router contenía lógica de negocio (`_load_format_from_json`, `_get_formatos_unac`)
**AHORA**: Router solo orquesta HTTP

```python
@router.get("/catalog")
async def get_catalog(request):
    formatos = service.get_all_formatos()  # Delegado al service
    return templates.TemplateResponse(...)
```

**Cambios**:
- ❌ Eliminadas funciones `_load_format_from_json()` y `_get_formatos_unac()`
- ✅ Llamada a `service.get_all_formatos()`
- ✅ Router solo maneja HTTP, no lógica

---

### 3. `app/modules/catalog/service.py`
**ANTES**: Service contenía solo lógica de generación de documentos
**AHORA**: Service contiene toda la lógica de negocio del módulo

```python
def get_all_formatos() -> List[Dict]:
    """Carga los 6 formatos desde JSONs"""
    # Lee todos los JSONs en app/data/unac/
    # Transforma datos
    # Retorna lista de formatos
```

**Cambios**:
- ✅ Nueva función `get_all_formatos()` - Carga y transforma datos
- ✅ Importa de `app.core.loaders` en lugar de reimplementar
- ❌ Eliminadas funciones `_load_format_from_json()` y `_get_formatos_unac()`
- ✅ Mantiene `generate_document()` para generación de documentos

---

### 4. `app/modules/formats/router.py`
**ANTES**: Router contenía lógica de búsqueda (`_load_format_from_json`, `_get_formato`)
**AHORA**: Router solo orquesta HTTP

```python
@router.get("/{format_id}")
async def get_format_detail(format_id: str, request):
    formato = service.get_formato(format_id)  # Delegado al service
    return templates.TemplateResponse(...)
```

**Cambios**:
- ❌ Eliminadas funciones `_load_format_from_json()` y `_get_formato()`
- ✅ Llamada a `service.get_formato(format_id)`
- ✅ Router solo maneja HTTP, no lógica

---

### 5. `app/modules/formats/service.py`
**ANTES**: Service no se usaba (función `get_formato()` nunca era llamada)
**AHORA**: Service contiene la lógica completa

```python
def get_formato(format_id: str) -> Dict:
    """
    Busca un formato específico por ID
    Ejemplo: "unac-proyecto-cual"
    """
    # Parsea el ID
    # Lee el JSON específico
    # Transforma y retorna datos
```

**Cambios**:
- ✅ Implementación completa de `get_formato()`
- ✅ Usa `load_json_file()` y `get_data_dir()` del core
- ✅ Manejo de errores con excepciones

---

## 🎯 Diagrama de flujo - ANTES vs DESPUÉS

### ❌ ANTES (Incorrecto)
```
Cliente HTTP
    ↓
Router (contiene lógica)
    ├─ Abre archivos
    ├─ Lee JSONs
    ├─ Transforma datos
    └─ Retorna a vista
    
Service (no se usa)
    ├─ get_formato() nunca llamado
    └─ Código duplicado aquí
```

### ✅ DESPUÉS (Correcto)
```
Cliente HTTP
    ↓
Router (solo orquesta)
    ↓
Service (contiene lógica)
    ├─ Parsea parámetros
    ├─ Llama core.loaders
    ├─ Transforma datos
    └─ Retorna resultado
    ↓
Core Loaders (código compartido)
    ├─ load_json_file()
    └─ get_data_dir()
```

---

## 📊 Comparativa de Responsabilidades

| Capa | ANTES | DESPUÉS |
|------|-------|---------|
| **Router** | HTTP + Lógica | ✅ Solo HTTP |
| **Service** | Parcial/No usado | ✅ Toda la lógica |
| **Core** | No existía | ✅ Funciones compartidas |
| **Duplicación** | Sí (40+ líneas en 2 routers) | ✅ No (código centralizado) |

---

## 🔧 Cómo funciona ahora

### Flujo de Catalog (Obtener 6 formatos)
```python
# Router recibe GET /catalog
router.get("/catalog"):
    formatos = service.get_all_formatos()  # Llama service
    return template.render(formatos)

# Service contiene la lógica
service.get_all_formatos():
    para cada tipo (informe, maestria, proyecto):
        para cada enfoque (cual, cuant):
            data = loaders.load_json_file()  # Carga JSON
            formatos.append(transformar(data))
    return formatos

# Loaders son compartidos
loaders.load_json_file(path):
    return json.load(path)  # Centralizado
```

### Flujo de Formats (Obtener 1 formato específico)
```python
# Router recibe GET /formatos/unac-proyecto-cual
router.get("/{format_id}"):
    formato = service.get_formato(format_id)  # Llama service
    return template.render(formato)

# Service contiene la lógica
service.get_formato(format_id):
    tipo, enfoque = parsear_id(format_id)
    data = loaders.load_json_file(path)  # Carga JSON
    return transformar(data)

# Loaders son compartidos
loaders.load_json_file(path):
    return json.load(path)  # Mismo código
```

---

## 🚀 Beneficios

| Beneficio | Descripción |
|-----------|-------------|
| **DRY (Don't Repeat Yourself)** | Eliminada duplicación de código en loaders |
| **Mantenibilidad** | Cambios en lógica solo se hacen en un lugar (service) |
| **Testabilidad** | Service puede testearse sin HTTP |
| **Escalabilidad** | Nuevos módulos pueden reutilizar core.loaders |
| **Separación de Responsabilidades** | Router ≠ Service ≠ Data Access |
| **Errores claros** | Service lanza excepciones, Router las maneja |

---

## ✨ Código Limpio

**Antes**:
- 40+ líneas de `_load_format_from_json()` en `catalog/router.py`
- 40+ líneas de `_load_format_from_json()` en `formats/router.py`
- `_get_formato()` en `formats/router.py` sin usar `formats/service.py`
- Total: ~120 líneas duplicadas

**Después**:
- 12 líneas en `app/core/loaders.py` (compartido)
- Cada router: 2-3 llamadas a service
- Total: ~25 líneas de código único

---

## 📝 Nota sobre migración

Los archivos fueron refactorizados pero el comportamiento HTTP es idéntico:
- `/catalog` sigue mostrando 6 formatos
- `/formatos/{format_id}` sigue mostrando detalle
- Los datos JSONs siguen en `app/data/unac/`

---

## 🎓 Lecciones de arquitectura

Esta refactorización demuestra:

1. **Separación de capas**: Router (HTTP), Service (Negocio), Core (Datos)
2. **DRY Principle**: Una sola fuente de verdad para cada lógica
3. **Inyección de dependencias**: Router depende de Service
4. **Manejo de errores**: Service lanza excepciones, Router las traduce
5. **Reutilización de código**: `core.loaders` usado por ambos módulos

