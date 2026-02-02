# Modelo de Datos JSON

## Ubicación de los Datos

| Ruta | Contenido |
|------|-----------|
| `app/data/{uni}/{categoria}/*.json` | Formatos por universidad/categoría |
| `app/data/references/*.json` | Normas bibliográficas globales |
| `app/data/{uni}/references_config.json` | Configuración de normas por universidad |
| `app/data/{uni}/alerts.json` | Alertas por universidad |

**Fuente:** `app/core/paths.py` L40-48

---

## Esquema de Formato (Ejemplo Real)

Archivo: `app/data/unac/informe/unac_informe_cual.json`

```json
{
  "id": "unac-informe-cual",
  "titulo": "Informe de Tesis - Cualitativo",
  "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
  "facultad": "FACULTAD DE INGENIERÍA ELÉCTRICA Y ELECTRÓNICA",
  "escuela": "ESCUELA PROFESIONAL DE INGENIERÍA ELECTRÓNICA",
  "version": "1.0.0",
  "fecha": "2026-01-17",
  
  "caratula": {
    "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
    "facultad": "FACULTAD DE ...",
    "titulo_placeholder": "TÍTULO DE LA INVESTIGACIÓN",
    "frase_grado": "TESIS PARA OPTAR EL TÍTULO...",
    "grado_objetivo": "INGENIERO ELECTRÓNICO",
    "label_autor": "AUTOR:",
    "autor": "APELLIDOS, Nombres",
    "label_asesor": "ASESOR:",
    "asesor": "Dr. APELLIDOS, Nombres",
    "pais": "CALLAO, PERÚ",
    "fecha": "2026"
  },
  
  "preliminares": {
    "introduccion": {
      "titulo": "INTRODUCCIÓN",
      "contenido": "..."
    }
  },
  
  "cuerpo": [
    {
      "titulo": "CAPÍTULO I: PLANTEAMIENTO DEL PROBLEMA",
      "contenido": [
        {"texto": "1.1. Descripción de la realidad problemática"},
        {"texto": "1.2. Formulación del problema"}
      ]
    }
  ],
  
  "finales": {
    "referencias": {
      "titulo": "REFERENCIAS BIBLIOGRÁFICAS",
      "nota": "Seguir norma APA 7ma edición"
    },
    "anexos": {
      "titulo_seccion": "ANEXOS",
      "nota_general": "Documentos complementarios"
    }
  }
}
```

**Fuente:** Estructura inferida de `app/core/loaders.py` L221-272 y `app/static/js/format-viewer.js` L267-316

---

## Construcción del `format_id`

El `format_id` se normaliza con el patrón: `{uni}-{categoria}-{enfoque}`

Ejemplo: `unac-informe-cual`

**Reglas:**
1. Se extrae el prefijo de universidad del nombre del archivo o del campo `id`.
2. Se normalizan espacios y guiones bajos a guiones.
3. Si no tiene prefijo de universidad, se agrega.

**Fuente:** `app/core/loaders.py` L165-173

```python
def _normalize_format_id(raw_id: str, uni: str) -> str:
    normalized = re.sub(r"[_\s]+", "-", raw_id.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    if not normalized.startswith(f"{uni}-"):
        normalized = f"{uni}-{normalized}"
    return normalized
```

---

## Esquema de Norma de Referencia (Ejemplo Real)

Archivo: `app/data/references/apa7.json`

```json
{
  "id": "apa7",
  "titulo": "APA 7ma Edición",
  "descripcion": "Estándar de la American Psychological Association",
  "tags": ["ciencias sociales", "psicología"],
  "preview": "Autor, A. A. (Año). Título del trabajo...",
  "tipos_fuente": [
    {
      "id": "libro",
      "nombre": "Libro",
      "formato_cita": "(Autor, Año)",
      "formato_referencia": "Autor, A. A. (Año). Título. Editorial."
    }
  ]
}
```

**Fuente:** `app/data/references/apa7.json` (estructura real)

---

## Configuración por Universidad

Archivo: `app/data/unac/references_config.json`

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

Este archivo determina:
- Qué normas están habilitadas para la universidad.
- El orden en que se muestran.
- Notas específicas por norma (si las hay).

**Fuente:** `app/modules/references/service.py` L103-128
