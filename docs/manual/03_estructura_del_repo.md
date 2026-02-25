# Estructura del Repositorio

## Mapa General

```
gicateca_tesis/
+-- app/                          # Codigo principal de la aplicacion
|   +-- core/                     # Nucleo compartido
|   |   +-- loaders.py            # Discovery y carga de JSON
|   |   +-- paths.py              # Resolucion de rutas (cache, data)
|   |   +-- pdf_converter.py      # Conversion DOCX->PDF con Word COM
|   |   +-- registry.py           # Discovery de providers de universidades
|   |   +-- settings.py           # Variables de entorno y defaults
|   |   +-- templates.py          # Configuracion de Jinja2
|   |   +-- university_registry.py # Registro de universidades
|   |   +-- view_models.py        # View-models para caratulas
|   |   +-- seed_loader.py        # Loader de datos semilla
|   |   +-- document_generator.py # Generador de documentos
|   |   +-- format_builder.py     # Constructor de formatos
|   |   `-- validation/           # Modulo de validacion
|   |       +-- issue.py          # Tipo Issue con severidad
|   |       +-- format_validation.py # Validador de formatos
|   |       +-- references_validation.py # Validador de refs
|   |       `-- repo_checks.py    # Verificaciones de repositorio
|   +-- engine/                   # Motor de Bloques (Block Engine)
|   |   +-- normalizer.py         # JSON -> Block[]
|   |   +-- registry.py           # @register() + render_blocks()
|   |   +-- primitives.py         # Helpers DOCX atomicos
|   |   +-- types.py              # Tipos Block y BlockRenderer
|   |   `-- renderers/            # 12 renderers especializados
|   |       +-- apa_examples.py   # Ejemplos APA
|   |       +-- centered_text.py  # Texto centrado
|   |       +-- headings.py       # Encabezados
|   |       +-- image.py          # Imagenes
|   |       +-- info_table.py     # Tablas de informacion
|   |       +-- logo.py           # Logo institucional
|   |       +-- matriz.py         # Matrices
|   |       +-- note.py           # Notas
|   |       +-- page_control.py   # Control de pagina (landscape, breaks)
|   |       +-- paragraphs.py     # Parrafos
|   |       +-- table.py          # Tablas
|   |       `-- toc.py            # Tabla de contenidos
|   +-- data/                     # Datos JSON por universidad
|   |   +-- references/           # Normas globales (APA, IEEE, etc.)
|   |   +-- schemas/              # JSON Schemas de validacion
|   |   +-- unac/                 # Datos UNAC
|   |   |   +-- informe/          # JSON de formatos de informe
|   |   |   +-- maestria/         # JSON de formatos de maestria
|   |   |   +-- proyecto/         # JSON de formatos de proyecto
|   |   |   +-- alerts.json       # Alertas UNAC
|   |   |   `-- references_config.json
|   |   `-- uni/                  # Datos UNI
|   |       +-- informe/          # JSON de formatos de informe
|   |       +-- posgrado/         # JSON de formatos de posgrado
|   |       +-- proyecto/         # JSON de formatos de proyecto
|   |       +-- alerts.json       # Alertas UNI
|   |       `-- references_config.json
|   +-- modules/                  # Modulos funcionales
|   |   +-- admin/                # Panel de administracion
|   |   +-- alerts/               # Sistema de alertas
|   |   +-- api/                  # Endpoints API v1
|   |   |   +-- router.py         # Formatos, version, validate, assets
|   |   |   +-- generation_router.py # Generacion y artifacts
|   |   |   +-- render_router.py  # Render directo DOCX/PDF
|   |   |   +-- dtos.py           # Pydantic DTOs (contratos)
|   |   |   `-- service.py        # Logica de negocio API
|   |   +-- catalog/              # Catalogo y generacion DOCX
|   |   +-- formats/              # Detalle, PDF y data de formatos
|   |   +-- generation/           # Orquestacion y preprocesamiento
|   |   |   +-- service.py        # Generacion de artefactos
|   |   |   `-- preprocessor.py   # Sanitizacion/merge/AI
|   |   +-- home/                 # Pagina de inicio
|   |   `-- references/           # Referencias bibliograficas
|   +-- static/                   # Archivos estaticos
|   |   +-- assets/               # Logos (LogoUNAC.png, LogoUNI.png, LogoGeneric.png)
|   |   +-- css/                  # Estilos
|   |   `-- js/                   # JavaScript
|   |       +-- catalog.js        # UI del catalogo
|   |       +-- cover-preview.js  # Modal unificado de caratula
|   |       +-- format-viewer.js  # Vista detalle
|   |       +-- gica-api.js       # Helpers API centralizados
|   |       +-- gica-dom.js       # Helpers DOM centralizados
|   |       +-- navigation.js     # Navegacion
|   |       `-- references.js     # UI de referencias
|   +-- templates/                # Plantillas Jinja2
|   |   +-- base.html             # Layout base
|   |   +-- components/           # Componentes reutilizables
|   |   |   +-- cover_modal.html  # Modal de caratula
|   |   |   +-- header.html       # Header
|   |   |   `-- sidebar.html      # Sidebar/navegacion
|   |   `-- pages/                # Paginas
|   |       +-- admin.html        # Panel admin
|   |       +-- alerts.html       # Alertas
|   |       +-- catalog.html      # Catalogo
|   |       +-- detail.html       # Detalle de formato
|   |       +-- home.html         # Inicio
|   |       +-- references.html   # Referencias
|   |       `-- versions.html     # Versiones
|   +-- universities/             # Providers de universidades
|   |   +-- contracts.py          # Contrato UniversityProvider
|   |   +-- registry.py           # Registry de providers
|   |   +-- shared/               # Generador compartido
|   |   |   `-- universal_generator.py  # Generador unificado (usa Block Engine)
|   |   +-- unac/                 # Provider UNAC
|   |   |   `-- provider.py       # Configuracion UNAC
|   |   `-- uni/                  # Provider UNI
|   |       `-- provider.py       # Configuracion UNI
|   `-- main.py                   # Punto de entrada FastAPI
+-- docs/                         # Documentacion
+-- scripts/                      # Scripts de utilidad
|   +-- check_encoding.py         # Verifica encoding de archivos
|   +-- check_mojibake.py         # Detecta encoding corrupto
|   +-- fix_mojibake_json.py      # Corrige mojibake en JSON
|   +-- fix_to_utf8.py            # Convierte archivos a UTF-8
|   +-- test_universal_gen.py     # Test rapido del generador
|   `-- validate_data.py          # Validacion de datos JSON
+-- tests/                        # Tests automatizados
+-- requirements.txt              # Dependencias Python
`-- pyproject.toml                # Configuracion de pytest
```

---

## Archivos Clave

### Backend

| Archivo | Proposito |
|---------|-----------|
| `app/main.py` | Inicializa FastAPI, registra routers, middleware CORS y API key |
| `app/core/loaders.py` | Discovery de formatos JSON, normalizacion de IDs |
| `app/core/pdf_converter.py` | Word COM singleton para PDF |
| `app/core/registry.py` | Discovery dinamico de providers en `app/universities/*/provider.py` |
| `app/core/paths.py` | Rutas centralizadas (cache DOCX/PDF, data, exports) |
| `app/core/settings.py` | Variables de entorno (`GICA_DEFAULT_UNI`) |
| `app/core/view_models.py` | View-models para caratulas |

### Motor de Bloques

| Archivo | Proposito |
|---------|-----------|
| `app/engine/normalizer.py` | Convierte JSON canonico a lista de bloques tipados |
| `app/engine/registry.py` | Registro de renderers con decorador `@register()` |
| `app/engine/primitives.py` | Funciones DOCX puras (fuentes, tablas, imagenes) |
| `app/engine/types.py` | Definiciones de tipos Block y BlockRenderer |
| `app/engine/renderers/` | 12 renderers especializados por tipo de bloque |

### Modulos

| Modulo | Router | Service |
|--------|--------|---------|
| catalog | `router.py` | `service.py` |
| formats | `router.py` | `service.py` |
| references | `router.py` | `service.py` |
| alerts | `router.py` | (usa provider.list_alerts) |
| admin | `router.py` | (sin service) |
| home | `router.py` | (usa provider.list_alerts) |
| api | `router.py` + `generation_router.py` + `render_router.py` | `service.py` + `dtos.py` |
| generation | (sin router propio) | `service.py` + `preprocessor.py` |

### Frontend

| Archivo | Proposito |
|---------|-----------|
| `app/static/js/format-viewer.js` | Caratula, indice, capitulos, descarga (~30KB) |
| `app/static/js/catalog.js` | Filtros y UI del catalogo (~13KB) |
| `app/static/js/references.js` | UI de referencias (~22KB) |
| `app/static/js/cover-preview.js` | Modal unificado de caratula (~7KB) |
| `app/static/js/gica-api.js` | Helpers API centralizados (~3KB) |
| `app/static/js/gica-dom.js` | Helpers DOM centralizados (~3KB) |
| `app/static/js/navigation.js` | Navegacion (~1KB) |
| `app/templates/pages/detail.html` | Vista de detalle de formato (~12KB) |
| `app/templates/pages/catalog.html` | Vista de catalogo (~10KB) |
| `app/templates/components/cover_modal.html` | Modal de caratula (~5KB) |
| `app/templates/components/header.html` | Header (~1KB) |
| `app/templates/components/sidebar.html` | Sidebar (~3KB) |

### Datos

| Ruta | Contenido |
|------|-----------|
| `app/data/references/*.json` | Normas globales (apa7, ieee, iso690, vancouver) |
| `app/data/unac/references_config.json` | Config de normas para UNAC |
| `app/data/unac/informe/*.json` | Formatos de informe UNAC |
| `app/data/unac/maestria/*.json` | Formatos de maestria UNAC |
| `app/data/unac/proyecto/*.json` | Formatos de proyecto UNAC |
| `app/data/uni/informe/*.json` | Formatos de informe UNI |
| `app/data/uni/posgrado/*.json` | Formatos de posgrado UNI |
| `app/data/uni/proyecto/*.json` | Formatos de proyecto UNI |
| `app/data/schemas/*.json` | JSON Schemas de validacion |
