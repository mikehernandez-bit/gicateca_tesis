# Glosario

## Terminos Tecnicos

| Termino | Definicion |
|---------|------------|
| **Artifact** | Archivo generado por el sistema (DOCX, PDF) almacenado temporalmente para descarga via API. |
| **Block** | Diccionario tipado con campo `type` que representa una unidad atomica del documento. Ejemplo: `{"type": "heading", "text": "CAPITULO I", "level": 1}`. |
| **Block Engine** | Motor de generacion de documentos basado en bloques. Pipeline: JSON -> Normalizer -> Block[] -> Renderers -> DOCX. Ubicacion: `app/engine/`. |
| **BlockRenderer** | Protocolo (typing.Protocol) que define la interfaz de un renderer de bloque: `(doc: Document, block: Block) -> None`. |
| **Cache** | Almacenamiento temporal de archivos generados (DOCX, PDF) para evitar regeneracion innecesaria. Ubicacion: `app/.cache/`. |
| **Caratula** | Portada institucional del documento academico. Contiene logo, universidad, titulo, autor, asesor, lugar y fecha. |
| **Categoria** | Tipo de formato dentro de una universidad: `informe`, `proyecto`, `maestria`, `posgrado`. |
| **COM** | Component Object Model. Tecnologia de Microsoft para interoperabilidad entre aplicaciones. Usada para controlar Word. |
| **Data-Driven** | Enfoque donde la configuracion y estructura se define en archivos de datos (JSON) en lugar de codigo. |
| **Discovery** | Proceso de escaneo automatico de archivos para detectar formatos, providers o normas disponibles. |
| **Enfoque** | Subclasificacion del formato: `cual` (cualitativo), `cuant` (cuantitativo), `mixto`. |
| **FastAPI** | Framework web Python para APIs REST. Base del backend de GicaTesis. |
| **Format ID** | Identificador unico del formato. Patron: `{uni}-{categoria}-{enfoque}`. Ejemplo: `unac-informe-cual`. |
| **Generador unificado** | Script `universal_generator.py` compartido en `app/universities/shared/` que usa Block Engine para generar DOCX. |
| **HRESULT** | Codigo de error de Windows COM. El mas comun es `-2147220995` ("El objeto no esta conectado al servidor"). |
| **Jinja2** | Motor de templates usado para renderizar HTML. |
| **Mojibake** | Caracteres corruptos por error de encoding (ej: "e" con tilde corrupta). |
| **Normalizer** | Modulo `app/engine/normalizer.py` que transforma JSON canonico v2 en una lista plana de Blocks. |
| **PDF Prewarm** | Generacion anticipada de PDFs al iniciar el servidor para reducir tiempos de respuesta. |
| **Preprocessor** | Modulo `app/modules/generation/preprocessor.py` que sanitiza, fusiona y prepara JSON antes de generacion. |
| **Provider** | Modulo que expone configuracion y generadores para una universidad especifica. |
| **Renderer** | Funcion registrada con `@register("tipo")` que sabe renderizar un tipo de bloque a DOCX. |
| **SHA256** | Algoritmo de hash usado para identificar cambios en archivos y optimizar cache. |
| **STA** | Single-Threaded Apartment. Modelo de threading requerido por Word COM. |
| **Templates** | Archivos HTML con sintaxis Jinja2 para renderizar vistas. Ubicacion: `app/templates/`. |
| **TOC** | Table of Contents. Indice generado automaticamente en Word. |
| **View-Model** | Estructura de datos derivada que agrega defaults del provider para renderizar caratulas en el frontend. |
| **Word COM** | Interfaz de automatizacion de Microsoft Word via COM. Usada para convertir DOCX a PDF. |

---

## Acronimos

| Acronimo | Significado |
|----------|-------------|
| **API** | Application Programming Interface |
| **APA** | American Psychological Association (norma bibliografica) |
| **CSS** | Cascading Style Sheets |
| **DOCX** | Formato de documento Microsoft Word Open XML |
| **DTO** | Data Transfer Object |
| **HTML** | HyperText Markup Language |
| **HTTP** | HyperText Transfer Protocol |
| **IEEE** | Institute of Electrical and Electronics Engineers (norma bibliografica) |
| **ISO** | International Organization for Standardization |
| **JS** | JavaScript |
| **JSON** | JavaScript Object Notation |
| **PDF** | Portable Document Format |
| **REST** | Representational State Transfer |
| **UI** | User Interface |
| **UNAC** | Universidad Nacional del Callao |
| **UNI** | Universidad Nacional de Ingenieria |
| **UTF-8** | Unicode Transformation Format 8-bit |

---

## Rutas Clave

| Ruta | Descripcion |
|------|-------------|
| `app/core/` | Nucleo compartido del sistema |
| `app/engine/` | Motor de bloques (Block Engine) |
| `app/data/` | Datos JSON por universidad |
| `app/modules/` | Modulos funcionales (catalog, formats, references, api, generation, etc.) |
| `app/static/` | Archivos estaticos (CSS, JS, assets) |
| `app/templates/` | Templates Jinja2 |
| `app/universities/` | Providers de universidades |
| `app/universities/shared/` | Generador unificado compartido |
| `app/.cache/` | Cache de DOCX y PDF generados |
| `docs/manual/` | Documentacion tecnica |
