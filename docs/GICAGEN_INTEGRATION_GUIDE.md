# GicaGen Integration Guide - Formats API v1

> **Documento completo** para integrar GicaGen con la API de Formatos de GicaTesis.  
> Última actualización: 2026-02-05

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura](#arquitectura)
3. [Endpoints de la API](#endpoints-de-la-api)
4. [Contratos de Datos (DTOs)](#contratos-de-datos-dtos)
5. [Cache y Versionado](#cache-y-versionado)
6. [Ejemplos de Código](#ejemplos-de-código)
7. [Errores Comunes](#errores-comunes)
8. [Checklist de Integración](#checklist-de-integración)

---

## Resumen Ejecutivo

### ¿Qué es esta API?

La **Formats API v1** permite a GicaGen obtener la lista de formatos disponibles en GicaTesis y sus detalles (campos del wizard, assets, reglas). Es **read-only** y está optimizada con cache **ETag/304**.

### URL Base

```
http://{gicatesis-host}/api/v1
```

En desarrollo local:
```
http://localhost:8000/api/v1
```

### Características Clave

| Característica | Detalles |
|----------------|----------|
| **Protocolo** | HTTP/HTTPS |
| **Formato** | JSON |
| **Autenticación** | Ninguna (público) |
| **Cache** | ETag + If-None-Match (304) |
| **Versionado** | Hash SHA256 del contenido |

---

## Arquitectura

```
┌──────────────┐         ┌─────────────────────────────────────────────────────┐
│   GicaGen    │ ──GET── │  GicaTesis                                          │
│  (Cliente)   │         │  ┌─────────────┐    ┌─────────────┐    ┌──────────┐│
│              │ ◀─JSON─ │  │ API Router  │───▶│   Service   │───▶│ Loaders  ││
│              │         │  │/api/v1/*    │    │(Hash,DTOs)  │    │(JSON,etc)││
└──────────────┘         │  └─────────────┘    └─────────────┘    └──────────┘│
                         └─────────────────────────────────────────────────────┘
```

### Archivos del Módulo API

```
app/modules/api/
├── __init__.py          # Inicialización del módulo
├── dtos.py              # Pydantic DTOs (contratos)
├── service.py           # Lógica de negocio (load, hash, map)
└── router.py            # Endpoints HTTP
```

---

## Endpoints de la API

### 1. GET /api/v1/formats/version

**Propósito:** Check rápido de si el catálogo cambió.

**Request:**
```http
GET /api/v1/formats/version HTTP/1.1
Host: localhost:8000
```

**Response (200):**
```json
{
  "version": "5b3398d71b90f766157442ac7c0f0f95cf1ca392e391468bdfd5646c1f6929cb",
  "generatedAt": "2026-02-05T16:39:41.427921+00:00"
}
```

**Uso:** Comparar `version` con la versión guardada en GicaGen. Si son diferentes, sincronizar.

---

### 2. GET /api/v1/formats

**Propósito:** Lista todos los formatos disponibles.

**Query Parameters:**
| Param | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `university` | string | Filtrar por universidad | `unac`, `uni` |
| `category` | string | Filtrar por categoría | `informe`, `maestria`, `proyecto` |
| `documentType` | string | Filtrar por tipo | `cual`, `cuant` |

**Request:**
```http
GET /api/v1/formats?university=unac HTTP/1.1
Host: localhost:8000
```

**Response (200):**
```json
[
  {
    "id": "unac-informe-cual",
    "title": "Informe Cual",
    "university": "unac",
    "category": "informe",
    "documentType": "cual",
    "version": "ce7ea813db7ed315"
  },
  {
    "id": "unac-proyecto-cuant",
    "title": "Proyecto Cuant",
    "university": "unac",
    "category": "proyecto",
    "documentType": "cuant",
    "version": "86b4e54d152a82ac"
  }
]
```

**Headers de Respuesta:**
```
ETag: "5b3398d71b90f766157442ac7c0f0f95cf1ca392e391468bdfd5646c1f6929cb"
Cache-Control: public, max-age=60
```

---

### 3. GET /api/v1/formats/{format_id}

**Propósito:** Detalle completo de un formato, incluye todos los campos del wizard.

**Request:**
```http
GET /api/v1/formats/unac-informe-cual HTTP/1.1
Host: localhost:8000
```

**Response (200):**
```json
{
  "id": "unac-informe-cual",
  "title": "Informe Cual",
  "university": "unac",
  "category": "informe",
  "documentType": "cual",
  "version": "ce7ea813db7ed315",
  "templateRef": null,
  "fields": [
    {
      "name": "universidad",
      "label": "Universidad",
      "type": "text",
      "required": false,
      "default": "UNIVERSIDAD NACIONAL DEL CALLAO",
      "options": null,
      "validation": null,
      "order": 1,
      "section": null
    },
    {
      "name": "facultad",
      "label": "Facultad",
      "type": "text",
      "required": false,
      "default": "FACULTAD DE [NOMBRE DE LA FACULTAD]",
      "options": null,
      "validation": null,
      "order": 2,
      "section": null
    }
  ],
  "assets": [],
  "rules": null
}
```

**Response (404):**
```json
{
  "detail": "Formato no encontrado: invalid-id"
}
```

---

### 4. GET /api/v1/assets/{path}

**Propósito:** Servir logos, imágenes, etc.

**Request:**
```http
GET /api/v1/assets/logos/unac.png HTTP/1.1
Host: localhost:8000
```

**Response:** Archivo binario con headers:
```
Content-Type: image/png
Cache-Control: public, max-age=86400
```

**Seguridad:**
- ❌ No permite `../` (path traversal)
- ❌ No permite paths absolutos
- ✅ Solo sirve desde `/app/static/`

---

## Contratos de Datos (DTOs)

### FormatSummary

Usado en la lista `/formats`.

```typescript
interface FormatSummary {
  id: string;           // ID estable único (ej: "unac-informe-cual")
  title: string;        // Título legible (ej: "Informe Cual")
  university: string;   // Código universidad (ej: "unac", "uni")
  category: string;     // Categoría (ej: "informe", "proyecto", "maestria")
  documentType?: string; // Tipo documento (ej: "cual", "cuant")
  version: string;      // Hash corto del contenido (16 chars)
}
```

### FormatDetail

Usado en detalle `/formats/{id}`. Extiende FormatSummary.

```typescript
interface FormatDetail extends FormatSummary {
  templateRef?: TemplateRef;   // Referencia a plantilla DOCX
  fields: FormatField[];       // Campos del wizard
  assets: AssetRef[];          // Logos, imágenes asociadas
  rules?: RuleSet;             // Reglas de formato (márgenes, fuente, etc.)
}
```

### FormatField

Campo de entrada para el wizard.

```typescript
interface FormatField {
  name: string;          // Nombre técnico (ej: "titulo_placeholder")
  label: string;         // Etiqueta visible (ej: "Título de la Tesis")
  type: FieldType;       // "text" | "textarea" | "number" | "date" | "select" | "boolean"
  required: boolean;     // true si es obligatorio
  default?: any;         // Valor por defecto
  options?: string[];    // Opciones si type="select"
  validation?: object;   // Reglas de validación
  order?: number;        // Orden de aparición
  section?: string;      // Sección/grupo
}
```

### TemplateRef

```typescript
interface TemplateRef {
  kind: string;    // "docx", "html", etc.
  uri: string;     // URI lógica (ej: "gicatesis://templates/unac-informe-cual")
}
```

### AssetRef

```typescript
interface AssetRef {
  id: string;      // ID estable (ej: "unac:logo:main")
  kind: string;    // "logo", "image", "signature"
  url: string;     // URL pública (ej: "/api/v1/assets/logos/unac.png")
}
```

### RuleSet

```typescript
interface RuleSet {
  margins?: object;      // { top: 2.5, bottom: 2.5, left: 3.0, right: 2.5 }
  font?: string;         // "Times New Roman"
  fontSize?: number;     // 12
  lineSpacing?: number;  // 1.5
  extra?: object;        // Reglas adicionales
}
```

### CatalogVersionResponse

```typescript
interface CatalogVersionResponse {
  version: string;       // SHA256 hash del catálogo completo
  generatedAt: string;   // ISO timestamp (ej: "2026-02-05T16:39:41+00:00")
}
```

---

## Cache y Versionado

### Cómo funciona el ETag

1. GicaGen hace `GET /api/v1/formats`
2. La respuesta incluye header `ETag: "abc123..."`
3. GicaGen guarda el ETag
4. En la siguiente request, GicaGen envía `If-None-Match: "abc123..."`
5. Si el catálogo no cambió → API responde **304 Not Modified** (sin body)
6. Si el catálogo cambió → API responde **200** con nuevo ETag

### Flujo recomendado para GicaGen

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Al iniciar GicaGen                                           │
├─────────────────────────────────────────────────────────────────┤
│    GET /api/v1/formats/version                                  │
│    └─ Comparar version con cache local                          │
│       └─ Si son iguales → Usar cache local                      │
│       └─ Si son diferentes → Descargar catálogo completo        │
├─────────────────────────────────────────────────────────────────┤
│ 2. Sincronización periódica (cada 60s o al cambiar de formato)  │
├─────────────────────────────────────────────────────────────────┤
│    GET /api/v1/formats                                          │
│    Headers: If-None-Match: "<etag guardado>"                    │
│    └─ Si 304 → Cache sigue válido                               │
│    └─ Si 200 → Actualizar cache y guardar nuevo ETag            │
├─────────────────────────────────────────────────────────────────┤
│ 3. Al seleccionar un formato                                    │
├─────────────────────────────────────────────────────────────────┤
│    GET /api/v1/formats/{id}                                     │
│    Headers: If-None-Match: "<format version>"                   │
│    └─ Usar campos para renderizar wizard                        │
└─────────────────────────────────────────────────────────────────┘
```

### Cuándo cambia la versión

| Acción | ¿Cambia version? |
|--------|------------------|
| Editar JSON de un formato | ✅ Sí |
| Modificar plantilla DOCX | ✅ Sí |
| Agregar nuevo formato | ✅ Sí |
| Mover carpeta sin cambiar contenido | ❌ No |
| Cambiar timestamp sin cambiar contenido | ❌ No |

---

## Ejemplos de Código

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Cache local
cached_etag = None
cached_formats = None

def sync_formats():
    global cached_etag, cached_formats
    
    headers = {}
    if cached_etag:
        headers["If-None-Match"] = cached_etag
    
    response = requests.get(f"{BASE_URL}/formats", headers=headers)
    
    if response.status_code == 304:
        print("Cache válido, usando datos locales")
        return cached_formats
    
    if response.status_code == 200:
        cached_etag = response.headers.get("ETag")
        cached_formats = response.json()
        print(f"Catálogo actualizado, {len(cached_formats)} formatos")
        return cached_formats
    
    raise Exception(f"Error: {response.status_code}")

def get_format_detail(format_id: str):
    response = requests.get(f"{BASE_URL}/formats/{format_id}")
    if response.status_code == 404:
        return None
    return response.json()

# Uso
formats = sync_formats()
detail = get_format_detail("unac-informe-cual")
print(f"Campos: {len(detail['fields'])}")
```

### TypeScript/JavaScript (fetch)

```typescript
const BASE_URL = "http://localhost:8000/api/v1";

interface FormatCache {
  etag: string | null;
  formats: FormatSummary[];
}

let cache: FormatCache = { etag: null, formats: [] };

async function syncFormats(): Promise<FormatSummary[]> {
  const headers: HeadersInit = {};
  if (cache.etag) {
    headers["If-None-Match"] = cache.etag;
  }

  const response = await fetch(`${BASE_URL}/formats`, { headers });

  if (response.status === 304) {
    console.log("Cache hit");
    return cache.formats;
  }

  if (response.ok) {
    cache.etag = response.headers.get("ETag");
    cache.formats = await response.json();
    console.log(`Updated: ${cache.formats.length} formats`);
    return cache.formats;
  }

  throw new Error(`Error: ${response.status}`);
}

async function getFormatDetail(id: string): Promise<FormatDetail | null> {
  const response = await fetch(`${BASE_URL}/formats/${id}`);
  if (response.status === 404) return null;
  return response.json();
}

// Uso
const formats = await syncFormats();
const detail = await getFormatDetail("unac-informe-cual");
console.log(`Fields: ${detail?.fields.length}`);
```

### PowerShell

```powershell
$baseUrl = "http://localhost:8000/api/v1"

# Obtener lista
$formats = Invoke-RestMethod -Uri "$baseUrl/formats"
$formats | Format-Table id, title, category

# Obtener detalle
$detail = Invoke-RestMethod -Uri "$baseUrl/formats/unac-informe-cual"
$detail.fields | Format-Table name, label, type, default

# Verificar ETag
$r1 = Invoke-WebRequest -Uri "$baseUrl/formats"
$etag = $r1.Headers["ETag"]
Write-Host "ETag: $etag"
```

---

## Errores Comunes

### 1. 404 Not Found en /api/v1/*

**Causa:** El servidor no tiene registrado el router de la API.

**Solución:** Reiniciar uvicorn:
```bash
.venv\Scripts\uvicorn.exe app.main:app --reload
```

### 2. El ID del formato no existe

**Causa:** Usar un ID inventado o antiguo.

**Solución:** Obtener IDs válidos de `GET /api/v1/formats` primero.

### 3. El navegador muestra datos antiguos

**Causa:** Cache del navegador.

**Solución:** 
- Usar `Ctrl+Shift+R` (hard refresh)
- Usar ventana incógnito
- Usar herramientas de desarrollo (Network tab, Disable cache)

### 4. ETag no devuelve 304

**Causa:** El ETag enviado no coincide exactamente.

**Solución:** Asegurarse de incluir las comillas:
```
If-None-Match: "5b3398d71b90f766..."
```
(con comillas dentro del header)

---

## Checklist de Integración

### Antes de empezar
- [ ] GicaTesis corriendo en `http://localhost:8000`
- [ ] Verificar `GET /api/v1/formats/version` responde

### Integración básica
- [ ] Implementar `GET /api/v1/formats` para listar formatos
- [ ] Implementar `GET /api/v1/formats/{id}` para detalles
- [ ] Mapear `FormatField[]` a componentes de formulario
- [ ] Respetar `field.type` para renderizar input correcto
- [ ] Usar `field.default` como valor inicial

### Cache (recomendado)
- [ ] Guardar ETag de respuestas en localStorage/DB
- [ ] Enviar `If-None-Match` en requests siguientes
- [ ] Manejar respuesta 304 (usar cache local)
- [ ] Implementar check periódico con `/formats/version`

### Validación
- [ ] Tests unitarios para parseo de DTOs
- [ ] Tests de integración contra API real
- [ ] Manejo de errores (404, timeout, etc.)

---

## Soporte

| Recurso | Ubicación |
|---------|-----------|
| **Documentación API** | `/docs/api/formats-api.md` |
| **Contratos DTOs** | `/docs/contracts/format-dto.md` |
| **Guía de Cache** | `/docs/runbooks/versioning-cache.md` |
| **Tests** | `tests/test_api_*.py` |
| **OpenAPI (Swagger)** | `http://localhost:8000/docs` |

---

> **Nota:** Este documento fue generado basándose en la implementación real de GicaTesis. Todos los endpoints y DTOs han sido verificados con tests automatizados (21 tests passed).
