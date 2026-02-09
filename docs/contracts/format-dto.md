# Format DTO Contract

Contratos de datos (DTOs) que expone la API de Formatos v1.

## FormatSummary

Usado en listados (`GET /formats`).

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `id` | string | ✅ | ID estable único |
| `title` | string | ✅ | Título legible |
| `university` | string | ✅ | Código de universidad |
| `category` | string | ✅ | Categoría del formato |
| `documentType` | string | ❌ | Tipo de documento |
| `version` | string | ✅ | Hash corto del contenido (16 chars) |

```json
{
  "id": "unac-caratula-tesis-cualitativa",
  "title": "Carátula Tesis Cualitativa",
  "university": "unac",
  "category": "general",
  "documentType": "tesis",
  "version": "a1b2c3d4e5f67890"
}
```

---

## FormatDetail

Usado para detalle (`GET /formats/{id}`). Extiende FormatSummary.

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `templateRef` | TemplateRef | ❌ | Referencia a plantilla |
| `fields` | FormatField[] | ✅ | Campos del wizard |
| `assets` | AssetRef[] | ✅ | Assets asociados |
| `rules` | RuleSet | ❌ | Reglas de formato |
| `definition` | object | ✅ | JSON completo del formato (estructura extendida) |

---

## FormatField

Campo de entrada para el wizard.

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `name` | string | ✅ | Nombre técnico |
| `label` | string | ✅ | Etiqueta visible |
| `type` | enum | ✅ | `text`, `textarea`, `number`, `date`, `select`, `boolean` |
| `required` | boolean | ✅ | Si es obligatorio |
| `default` | any | ❌ | Valor por defecto |
| `options` | string[] | ❌ | Opciones si `type=select` |
| `validation` | object | ❌ | Reglas de validación |
| `order` | int | ❌ | Orden de aparición |
| `section` | string | ❌ | Sección/grupo |

```json
{
  "name": "titulo",
  "label": "Título de la Tesis",
  "type": "text",
  "required": true,
  "default": null,
  "order": 1,
  "section": "datos_generales"
}
```

---

## TemplateRef

Referencia a la plantilla de generación.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `kind` | string | Tipo: `docx`, `html`, etc. |
| `uri` | string | URI lógica estable (no path interno) |

```json
{
  "kind": "docx",
  "uri": "gicatesis://templates/unac-caratula-tesis"
}
```

---

## AssetRef

Referencia a un asset (logo, imagen).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | string | ID estable |
| `kind` | string | `logo`, `image`, `signature` |
| `url` | string | URL pública estable |

```json
{
  "id": "unac:logo:main",
  "kind": "logo",
  "url": "/api/v1/assets/unac/logo/main"
}
```

---

## RuleSet (opcional)

Reglas de formato si existen en la fuente.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `margins` | object | Márgenes en cm |
| `font` | string | Fuente principal |
| `fontSize` | int | Tamaño de fuente |
| `lineSpacing` | float | Interlineado |
| `extra` | object | Reglas adicionales |

---

## Notas de Compatibilidad

- **IDs son estables**: Renombrar carpetas internas NO cambia el ID público.
- **Version es por contenido**: Solo cambia si cambia el JSON o la plantilla.
- **Campos opcionales**: Si un campo es `null`, significa que no existe en la fuente.
- **`fields` vs `definition`**: `fields` es el subset para UI; `definition` es el documento integral para integraciones.
