# Formats API v1

API de solo lectura para consumir el catálogo de formatos de GicaTesis desde sistemas externos (GicaGen).

## Base URL

```
/api/v1
```

## Regla de Publicación de Formatos

Un JSON entra al catálogo público solo si cumple:

- `_meta.entity == "format"`
- `_meta.publish == true`

Queda fuera del catálogo público cuando:

- `_meta.entity == "config"`
- `_meta.publish == false`
- El archivo vive en carpeta `configs/`

Notas importantes:

- `GET /formats` y `GET /formats/version` se calculan solo con formatos publicables.
- `GET /formats/{id}` responde `404` para IDs no publicables o de configuración.
- Cambios en configs excluidos (por ejemplo `references_config`) no invalidan la versión pública.

## Endpoints

---

### GET /formats

Lista todos los formatos disponibles.

**Query Parameters:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `university` | string | Filtrar por código de universidad (ej: `unac`, `uni`) |
| `category` | string | Filtrar por categoría |
| `documentType` | string | Filtrar por tipo de documento |

**Response: 200 OK**
```json
[
  {
    "id": "unac-caratula-tesis-cualitativa",
    "title": "Carátula Tesis Cualitativa",
    "university": "unac",
    "category": "general",
    "documentType": "tesis",
    "version": "a1b2c3d4e5f67890"
  }
]
```

**Headers de Respuesta:**
- `ETag: "<catalogVersion>"` — Hash global del catálogo público (solo publicables)
- `Cache-Control: public, max-age=60`

**Cache 304:**
Enviar `If-None-Match: "<catalogVersion>"` para recibir `304 Not Modified` si no hay cambios.

---

### GET /formats/{id}

Obtiene el detalle completo de un formato.

**Response: 200 OK**
```json
{
  "id": "unac-caratula-tesis-cualitativa",
  "title": "Carátula Tesis Cualitativa",
  "university": "unac",
  "category": "general",
  "documentType": "tesis",
  "version": "a1b2c3d4e5f67890",
  "templateRef": {
    "kind": "docx",
    "uri": "gicatesis://templates/unac-caratula-tesis-cualitativa"
  },
  "fields": [
    {
      "name": "titulo",
      "label": "Título",
      "type": "text",
      "required": true,
      "default": null,
      "order": 1
    }
  ],
  "assets": [
    {
      "id": "unac:logo:main",
      "kind": "logo",
      "url": "/api/v1/assets/unac/logo/main"
    }
  ],
  "rules": null,
  "definition": {
    "_meta": {
      "entity": "format",
      "publish": true
    },
    "preliminares": {},
    "cuerpo": {},
    "anexos": {}
  }
}
```

Notas de contrato:
- `fields` se usa para render del wizard.
- `definition` conserva el JSON completo del formato para integraciones externas (n8n/simulacion).
- `definition` puede incluir capitulos, subtitulos, tablas, imagenes y reglas internas del formato.

**Response: 404 Not Found**
```json
{
  "detail": "Formato no encontrado: invalid-id"
}
```

---

### GET /formats/version

Check rápido de la versión actual del catálogo.

La versión se calcula únicamente con formatos publicables.

**Response: 200 OK**
```json
{
  "version": "abc123def456...",
  "generatedAt": "2026-02-05T16:00:00+00:00"
}
```

---

### GET /assets/{path}

Sirve assets (logos, imágenes) de forma segura.

**Seguridad:**
- No permite path traversal (`../`)
- Solo sirve desde directorio `/static`

**Response: 200 OK** — Archivo binario con `Cache-Control: public, max-age=86400`

---

## Comportamiento de Cache

| Escenario | Acción |
|-----------|--------|
| Primera request | Guardar `ETag` de la respuesta |
| Requests siguientes | Enviar `If-None-Match: <ETag guardado>` |
| Si catálogo no cambió | API responde `304` (sin body) |
| Si catálogo cambió | API responde `200` con nuevo `ETag` |

**TTL recomendado en cliente:** 60 segundos + validación con ETag.

---

## Códigos de Estado

| Código | Significado |
|--------|-------------|
| `200` | OK — Datos en body |
| `304` | Not Modified — ETag coincide, usar cache |
| `400` | Bad Request — Path inválido |
| `404` | Not Found — Formato/asset no existe |
