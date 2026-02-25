# Diseño Futuro: Tablas Complejas, Citas y Orientación

Este documento describe la estrategia técnica para manejar elementos avanzados en la generación de documentos (DOCX) integrados con flujos de IA (n8n).

## 1. El Problema: Integración con IA y Formatos Complejos
Cuando la IA genera contenido, a menudo produce texto plano o Markdown simple. Sin embargo, para una Tesis profesional, necesitamos:
- **Citas cruzadas dinámicas**: "Ver Figura 3.1" (donde el número 3.1 se genera automáticamente).
- **Tablas apaisadas (Landscape)**: Tablas anchas que requieren girar la hoja solo para esa página.
- **Índices automáticos**: Que Word reconozca las figuras y tablas para generar el índice correctamente.

## 2. Estrategia de Estructura de Datos (JSON)
Para que la IA pueda "controlar" el formato sin saber programar Word, debemos enriquecer el JSON que le pedimos.

### Nuevo Objeto `contenido_complejo`
En lugar de solo strings, permitiremos objetos con tipo:

```json
{
  "cuerpo": [
    {
      "titulo": "III. RESULTADOS",
      "contenido": [
        {
          "tipo": "parrafo",
          "texto": "Como se muestra en la {{REF:tabla_resultados}}, los datos indican..."
        },
        {
          "tipo": "tabla",
          "id": "tabla_resultados",
          "titulo": "Resultados del Análisis Espectroscópico",
          "orientacion": "horizontal",  // <--- CLAVE: Indica Landscape
          "estilo": "APA7",
          "datos": [ ... ]
        },
        {
          "tipo": "figura",
          "id": "fig_grafico_1",
          "titulo": "Distribución de Frecuencias",
          "ruta": "assets/grafico_1.png",
          "ancho_cm": 15
        }
      ]
    }
  ]
}
```

## 3. Implementación Técnica en `universal_generator.py`

### A. Tablas Apaisadas (Landscape)
Word maneja la orientación por **Secciones**. Para poner una tabla en horizontal en medio de un documento vertical, el generador deberá:

1. **Insertar Salto de Sección (Página Siguiente)** antes de la tabla.
2. **Cambiar la orientación** de la nueva sección a `LANDSCAPE`.
3. **Renderizar la tabla**.
4. **Insertar Salto de Sección (Página Siguiente)** después de la tabla.
5. **Cambiar la orientación** de la siguiente sección de vuelta a `PORTRAIT`.

**Lógica Propuesta:**
```python
if item.get('orientacion') == 'horizontal':
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    # ... renderizar tabla ...
    # Restaurar vertical
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    section.orientation = WD_ORIENT.PORTRAIT
```

### B. Referencias Cruzadas y Campos Automáticos (SEQ Fields)
Para que Word actualice los números ("Tabla 1", "Tabla 2") automáticamente, incluso si la IA inserta una nueva tabla al principio:

- **No usar números "duros" en el JSON** (e.g., no escribir "Tabla 3.1").
- **Usar códigos de campo `SEQ` de Word**.

**En el Generador:**
Cuando se encuentra un `titulo` de tabla, insertar un campo Word:
`Figure { SEQ Figure \* ARABIC }`

**En el Texto (Citas):**
El sistema debe pre-procesar el texto buscando `{{REF:id}}` y reemplazarlo por una referencia cruzada al bookmark generado para ese ID. Esto es complejo en `python-docx` puro, pero se puede simular generando un bookmark en la figura y un hyperlink interno en el texto.

**Alternativa Simple para IA:**
Pedirle a la IA que use placeholders genéricos y un paso de post-procesamiento en Python (o Macro) actualice los campos.

## 4. Integración con n8n y Prompts
El flujo en n8n debería ser:

1. **Prompt de Estructura**: "Genera el contenido en JSON. Si una tabla tiene muchas columnas (>5), marca `orientacion: 'horizontal'`. Asigna un `id` único a cada tabla/figura (ej: `tab_presupuesto`) y úsalo para referenciarla en el texto."
2. **Validación JSON**: Un nodo en n8n verifica que el JSON es válido.
3. **Generación DOCX**: GicaGen recibe el JSON, detecta `orientacion: 'horizontal'` y aplica la lógica de secciones descrita arriba.
4. **Resultado**: Un DOCX profesional donde la página gira automáticamente.

## 5. Resumen de Características Necesarias

| Funcionalidad | Estado Actual | Propuesta Futura |
| :--- | :--- | :--- |
| **Tablas Anchas** | Se cortan o salen verticales | **Sección Landscape automática** |
| **Numeración** | Manual en JSON ("Tabla 1...") | **Campos SEQ de Word** (Automático) |
| **Referencias** | Manual ("Ver Tabla 1") | **IDs y Links** ("Ver Tabla X") |
| **Índices** | Estáticos | **Generados por Word** (TOC field) |

---
*Nota: Esta arquitectura permite que la IA se concentre en el contenido, mientras el generador (código) se encarga de la presentación compleja.*
