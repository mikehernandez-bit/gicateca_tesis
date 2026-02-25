# Block Engine

## Descripcion

El **Block Engine** es el motor de generacion de documentos DOCX de GicaTesis. Transforma datos JSON estructurados en documentos Word completos usando un pipeline de bloques tipados.

**Ubicacion:** `app/engine/`

**Fuente:** `app/engine/__init__.py`

---

## Pipeline

```
JSON (canonico v2) --> normalizer.py --> Block[] --> registry.py --> Renderers --> DOCX
```

### 1. Normalizer (`normalizer.py`)

Transforma la estructura anidada del JSON canonico v2 en una lista plana de `Block` dicts.

**Orden de secciones:**
1. Caratula
2. Pagina de respeto (solo si existe)
3. Informacion basica (solo si existe)
4. Preliminares (indices, dedicatorias, etc.)
5. Cuerpo (capitulos)
6. Finales (referencias + anexos)
7. Page footer (numeracion de paginas)

**Funciones principales:**

| Funcion | Proposito |
|---------|-----------|
| `normalize(data)` | Punto de entrada. JSON -> `List[Block]` |
| `_normalize_caratula(data)` | Secciones de caratula (logo, titulo, info) |
| `_normalize_pagina_respeto(data)` | Pagina de respeto (UNAC proyecto) |
| `_normalize_informacion_basica(data)` | Info basica (UNAC proyecto/maestria) |
| `_normalize_preliminares(data)` | Indices y secciones preliminares |
| `_normalize_indices(idx)` | Normaliza indices en ambos formatos |
| `_normalize_cuerpo(data)` | Capitulos del cuerpo |
| `_normalize_content_item(item)` | Normaliza un item de contenido |
| `_normalize_content_block(item)` | Contenido compartido de un item |
| `_normalize_finales(data)` | Finales: referencias + anexos |
| `_normalize_referencias(fin)` | Seccion de referencias |
| `_normalize_anexos(data, fin)` | Anexos con logica landscape/matriz |

**Fuente:** `app/engine/normalizer.py` (703 lineas)

---

### 2. Registry (`registry.py`)

Registry central de renderers con patron decorador `@register('tipo')`.

**API:**

```python
from app.engine.registry import register, render_blocks

# Registrar un renderer:
@register("heading")
def render_heading(doc: Document, block: Block) -> None:
    ...

# Renderizar lista de bloques:
render_blocks(doc, blocks)
```

**Funciones:**

| Funcion | Proposito |
|---------|-----------|
| `register(block_type)` | Decorador para registrar un renderer |
| `render_block(doc, block)` | Despacha un block al renderer correspondiente |
| `render_blocks(doc, blocks)` | Renderiza lista de blocks en orden secuencial |
| `list_registered()` | Lista tipos registrados (debugging/tests) |
| `is_registered(block_type)` | Verifica si un tipo tiene renderer |
| `_clear_registry()` | Limpia el registry (SOLO para tests) |

**Comportamiento ante errores:**
- Si un block no tiene renderer registrado: emite warning y continua.
- Si un renderer falla: logea el error y continua con el siguiente.
- No interrumpe la generacion del documento.

**Fuente:** `app/engine/registry.py` (125 lineas)

---

### 3. Types (`types.py`)

Define los tipos fundamentales:

```python
# Un Block es un dict con "type" obligatorio y datos arbitrarios.
Block = Dict[str, Any]
# Ejemplo: {"type": "heading", "text": "CAPITULO I", "level": 1}

class BlockRenderer(Protocol):
    def __call__(self, doc: Document, block: Block) -> None: ...
```

**Fuente:** `app/engine/types.py` (45 lineas)

---

### 4. Primitives (`primitives.py`)

Funciones DOCX atomicas reutilizables por multiples renderers:
- Formateo de fuentes
- Creacion de tablas
- Insercion de imagenes
- Manejo de saltos de pagina/seccion

**Fuente:** `app/engine/primitives.py`

---

## Renderers

Cada renderer maneja un tipo de bloque. Ubicacion: `app/engine/renderers/`.

| Archivo | Tipo(s) de Bloque | Descripcion |
|---------|-------------------|-------------|
| `headings.py` | `heading` | Encabezados (niveles 1-4, estilos Word) |
| `paragraphs.py` | `paragraph`, `paragraph_list` | Parrafos con formato y listas |
| `centered_text.py` | `centered_text` | Texto centrado (titulos, subtitulos) |
| `table.py` | `table` | Tablas complejas con estilos |
| `info_table.py` | `info_table` | Tablas de informacion (clave-valor) |
| `image.py` | `image` | Imagenes con dimensiones y alineacion |
| `logo.py` | `logo` | Logo institucional (resolucion cadena de fallback) |
| `toc.py` | `toc` | Tabla de contenidos (field codes de Word) |
| `note.py` | `note` | Notas y comentarios |
| `apa_examples.py` | `apa_examples` | Ejemplos de formato APA |
| `page_control.py` | `page_break`, `section_break`, `orientation`, `page_footer` | Control de pagina (landscape, breaks, numeracion) |
| `matriz.py` | `matriz` | Matrices de consistencia |

**Registro automatico:** `renderers/__init__.py` importa todos los modulos para que los decoradores `@register()` se ejecuten al iniciar.

**Fuente:** `app/engine/renderers/__init__.py` L16-29

---

## Tipos de Bloque Soportados

Lista completa de 19 tipos de bloque que el normalizer puede producir:

| Tipo | Usado en |
|------|----------|
| `heading` | Titulos de capitulo, seccion, subseccion |
| `paragraph` | Parrafos de texto simples |
| `paragraph_list` | Listas de items |
| `centered_text` | Texto centrado (caratula, dedicatoria) |
| `table` | Tablas con filas y columnas |
| `info_table` | Tablas de informacion basica (clave-valor) |
| `image` | Imagenes incrustadas |
| `logo` | Logo institucional en caratula |
| `toc` | Tabla de contenidos Word |
| `note` | Notas e instrucciones detalladas |
| `apa_examples` | Ejemplos de formato APA |
| `page_break` | Salto de pagina |
| `section_break` | Salto de seccion |
| `orientation` | Cambio de orientacion (portrait/landscape) |
| `page_footer` | Numeracion de paginas |
| `matriz` | Matriz de consistencia |
| `pagina_respeto` | Pagina de respeto (via centered_text) |
| `informacion_basica` | Tabla de info basica (via info_table) |
| `indices` | Indices (via toc) |

---

## Como Agregar un Nuevo Tipo de Bloque

### 1. Crear el renderer

```python
# app/engine/renderers/mi_renderer.py
from docx.document import Document
from app.engine.types import Block
from app.engine.registry import register

@register("mi_tipo")
def render_mi_tipo(doc: Document, block: Block) -> None:
    """Renderer para bloques de tipo 'mi_tipo'."""
    # Leer datos del block
    texto = block.get("text", "")
    # Modificar el documento
    doc.add_paragraph(texto)
```

### 2. Importar en `__init__.py`

```python
# app/engine/renderers/__init__.py
from app.engine.renderers import (
    # ... renderers existentes ...
    mi_renderer,  # <-- agregar
)
```

### 3. Emitir el bloque desde el normalizer

```python
# En normalizer.py, agregar logica para emitir el nuevo tipo:
blocks.append({"type": "mi_tipo", "text": "contenido"})
```

### 4. Agregar test

```python
# tests/test_engine_renderers.py
def test_mi_tipo_basic():
    doc = Document()
    block = {"type": "mi_tipo", "text": "prueba"}
    render_block(doc, block)
    assert doc.paragraphs[0].text == "prueba"
```
