# Vision General

## Que es GicaTesis/Formatoteca?

**Formatoteca** es un sistema web para gestionar, visualizar y generar documentos academicos (tesis, informes, proyectos) para multiples universidades peruanas (UNAC, UNI). Permite:

1. **Explorar** un catalogo de formatos disponibles.
2. **Previsualizar** caratulas e indices directamente en el navegador.
3. **Descargar** documentos DOCX generados automaticamente.
4. **Ver** normativa de referencias bibliograficas (APA, IEEE, ISO, Vancouver).
5. **Generar** documentos via API para integracion con sistemas externos (GicaGen, n8n).

**Fuente:** `app/main.py` L46: `app = FastAPI(title="Formatoteca", version="1.0.0")`

---

## Enfoque Data-Driven

El sistema NO hardcodea los formatos ni las normas en el codigo Python. En su lugar:

1. **JSON define la estructura** de cada formato (`app/data/{uni}/{categoria}/*.json`).
2. **Block Engine** (`app/engine/`) normaliza el JSON en bloques tipados y los renderiza a DOCX.
3. **Generador unificado** (`app/universities/shared/universal_generator.py`) orquesta la generacion.
4. **Word COM** convierte DOCX a PDF para previsualizaciones.
5. **Cache** almacena PDFs generados para reutilizacion.

```mermaid
flowchart LR
    JSON["JSON (app/data)"] --> Normalizer["Normalizer (engine)"]
    Normalizer --> Blocks["Block[]"]
    Blocks --> Renderers["12 Renderers"]
    Renderers --> DOCX["Archivo DOCX"]
    DOCX --> WordCOM["Word COM"]
    WordCOM --> PDF["PDF Cache"]
    PDF --> UI["Vista Previa Web"]
```

**Fuentes:**
- Block Engine: `app/engine/__init__.py`
- Normalizer: `app/engine/normalizer.py`
- Generador unificado: `app/universities/shared/universal_generator.py`
- Conversion PDF: `app/core/pdf_converter.py`

---

## Flujo de Usuario Tipico

1. **Ingresa a `/catalog`** -> ve listado de formatos.
2. **Selecciona un formato** -> va a `/formatos/{format_id}`.
3. **Previsualiza caratula** (boton "ojo") -> Modal con datos del JSON.
4. **Previsualiza PDF** -> PDF generado en cache.
5. **Descarga DOCX** -> POST a `/formatos/{format_id}/generate`.

**Fuente:** `app/static/js/format-viewer.js` (downloadDocument, openPdfModal, previewCover)
