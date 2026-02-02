# Referencias Bibliográficas

## Descripción

El módulo **references** gestiona las normas de citación bibliográfica (APA, IEEE, ISO 690, Vancouver) de forma **data-driven**.

---

## Endpoints

### GET `/referencias`

Renderiza la vista principal de referencias bibliográficas.

**Query Params:**
- `uni` (opcional): Código de universidad (default: `unac`).

**Fuente:** `app/modules/references/router.py` L45-60

### GET `/api/referencias`

Retorna el listado resumido y configuración de normas.

**Response:**
```json
{
  "config": {
    "university": "unac",
    "title": "Normas de citación (UNAC)",
    "enabled": ["apa7", "ieee", "iso690", "vancouver"],
    "order": ["apa7", "ieee", "iso690", "vancouver"],
    "notes": {}
  },
  "items": [
    {"id": "apa7", "titulo": "APA 7ma Edición", "tags": [...], ...}
  ]
}
```

**Fuente:** `app/modules/references/router.py` L63-68

### GET `/api/referencias/{ref_id}`

Retorna la norma completa por ID.

**Response:** Objeto JSON con la estructura completa de la norma.

**Fuente:** `app/modules/references/router.py` L71-81

---

## Estructura de Datos

### Normas Globales

Ubicación: `app/data/references/*.json`

Archivos:
- `apa7.json`
- `ieee.json`
- `iso690.json`
- `vancouver.json`

**Fuente:** Listado de `app/data/references/` (4 archivos)

### Configuración por Universidad

Ubicación: `app/data/{uni}/references_config.json`

Ejemplo (`app/data/unac/references_config.json`):
```json
{
  "university": "unac",
  "title": "Normas de citación (UNAC)",
  "enabled": ["apa7", "ieee", "iso690", "vancouver"],
  "order": ["apa7", "ieee", "iso690", "vancouver"],
  "notes": {}
}
```

**Fuente:** `app/data/unac/references_config.json` L1-7

---

## Servicio

### `build_reference_index(uni)`

Construye el índice resumido de normas para una universidad.

**Proceso:**
1. Lista todas las normas globales disponibles.
2. Carga la configuración de la universidad.
3. Filtra según `enabled` y ordena según `order`.
4. Retorna resumen + config.

**Fuente:** `app/modules/references/service.py` L131-167

### `get_reference_detail(ref_id, uni)`

Retorna la norma completa con nota específica de universidad.

**Fuente:** `app/modules/references/service.py` L170-194

---

## Frontend

### Template: `references.html`

Renderiza la UI de referencias con:
- Lista de normas (tarjetas).
- Detalle expandible por norma.

**Fuente:** `app/templates/pages/references.html` (~4KB)

### JavaScript: `references.js`

Maneja la interacción dinámica:
- Carga de normas via API.
- Expansión/contracción de detalles.
- Filtros por tags.

**Fuente:** `app/static/js/references.js` (~22KB)
