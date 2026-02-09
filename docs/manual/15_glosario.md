# Glosario

## Términos Técnicos

| Término | Definición |
|---------|------------|
| **Cache** | Almacenamiento temporal de archivos generados (DOCX, PDF) para evitar regeneración innecesaria. Ubicación: `app/.cache/`. |
| **Carátula** | Portada institucional del documento académico. Contiene logo, universidad, título, autor, asesor, lugar y fecha. |
| **Categoría** | Tipo de formato dentro de una universidad: `informe`, `proyecto`, `maestria`, `posgrado`. |
| **COM** | Component Object Model. Tecnología de Microsoft para interoperabilidad entre aplicaciones. Usada para controlar Word. |
| **Data-Driven** | Enfoque donde la configuración y estructura se define en archivos de datos (JSON) en lugar de código. |
| **Discovery** | Proceso de escaneo automático de archivos para detectar formatos, providers o normas disponibles. |
| **Enfoque** | Subclasificación del formato: `cual` (cualitativo), `cuant` (cuantitativo), `mixto`. |
| **FastAPI** | Framework web Python para APIs REST. Base del backend de GicaTesis. |
| **Format ID** | Identificador único del formato. Patrón: `{uni}-{categoria}-{enfoque}`. Ejemplo: `unac-informe-cual`. |
| **Generador** | Script Python que lee un JSON y produce un DOCX. Ubicación: `app/universities/{uni}/centro_formatos/`. |
| **HRESULT** | Código de error de Windows COM. El más común es `-2147220995` ("El objeto no está conectado al servidor"). |
| **Jinja2** | Motor de templates usado para renderizar HTML. |
| **Mojibake** | Caracteres corruptos por error de encoding (ej: "é" en lugar de "é"). |
| **PDF Prewarm** | Generación anticipada de PDFs al iniciar el servidor para reducir tiempos de respuesta. |
| **Provider** | Módulo que expone configuración y generadores para una universidad específica. |
| **SHA256** | Algoritmo de hash usado para identificar cambios en archivos y optimizar cache. |
| **STA** | Single-Threaded Apartment. Modelo de threading requerido por Word COM. |
| **Templates** | Archivos HTML con sintaxis Jinja2 para renderizar vistas. Ubicación: `app/templates/`. |
| **TOC** | Table of Contents. Índice generado automáticamente en Word. |
| **Word COM** | Interfaz de automatización de Microsoft Word vía COM. Usada para convertir DOCX a PDF. |

---

## Acrónimos

| Acrónimo | Significado |
|----------|-------------|
| **API** | Application Programming Interface |
| **APA** | American Psychological Association (norma bibliográfica) |
| **CSS** | Cascading Style Sheets |
| **DOCX** | Formato de documento Microsoft Word Open XML |
| **HTML** | HyperText Markup Language |
| **HTTP** | HyperText Transfer Protocol |
| **IEEE** | Institute of Electrical and Electronics Engineers (norma bibliográfica) |
| **ISO** | International Organization for Standardization |
| **JS** | JavaScript |
| **JSON** | JavaScript Object Notation |
| **PDF** | Portable Document Format |
| **REST** | Representational State Transfer |
| **UI** | User Interface |
| **UNAC** | Universidad Nacional del Callao |
| **UNI** | Universidad Nacional de Ingeniería |
| **UTF-8** | Unicode Transformation Format 8-bit |

---

## Rutas Clave

| Ruta | Descripción |
|------|-------------|
| `app/core/` | Núcleo compartido del sistema |
| `app/data/` | Datos JSON por universidad |
| `app/modules/` | Módulos funcionales (catalog, formats, references, etc.) |
| `app/static/` | Archivos estáticos (CSS, JS, assets) |
| `app/templates/` | Templates Jinja2 |
| `app/universities/` | Providers de universidades |
| `app/.cache/` | Cache de DOCX y PDF generados |
| `docs/manual/` | Documentación técnica |
