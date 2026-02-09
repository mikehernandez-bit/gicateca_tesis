# Estructura del Repositorio

## Mapa General

```
gicateca_tesis/
+-- app/                          # Código principal de la aplicación
|   +-- core/                     # Núcleo compartido
|   |   +-- loaders.py            # Discovery y carga de JSON
|   |   +-- paths.py              # Resolución de rutas (cache, data)
|   |   +-- pdf_converter.py      # Conversión DOCX→PDF con Word COM
|   |   +-- registry.py           # Discovery de providers de universidades
|   |   +-- templates.py          # Configuración de Jinja2
|   |   `-- university_registry.py
|   +-- data/                     # Datos JSON por universidad
|   |   +-- references/           # Normas globales (APA, IEEE, etc.)
|   |   +-- unac/                 # Datos UNAC
|   |   |   +-- informe/          # JSON de formatos de informe
|   |   |   +-- maestria/         # JSON de formatos de maestría
|   |   |   +-- proyecto/         # JSON de formatos de proyecto
|   |   |   `-- references_config.json
|   |   `-- uni/                  # Datos UNI
|   +-- modules/                  # Módulos funcionales
|   |   +-- admin/                # Panel de administración
|   |   +-- alerts/               # Sistema de alertas
|   |   +-- catalog/              # Catálogo y generación DOCX
|   |   +-- formats/              # Detalle, PDF y data de formatos
|   |   +-- home/                 # Página de inicio
|   |   `-- references/           # Referencias bibliográficas
|   +-- static/                   # Archivos estáticos
|   |   +-- assets/               # Logos (LogoUNAC.png, LogoUNI.png)
|   |   +-- css/                  # Estilos
|   |   `-- js/                   # JavaScript (catalog.js, format-viewer.js)
|   +-- templates/                # Plantillas Jinja2
|   |   +-- base.html             # Layout base
|   |   +-- components/           # Componentes reutilizables
|   |   `-- pages/                # Páginas (catalog.html, detail.html, etc.)
|   +-- universities/             # Providers de universidades
|   |   +-- contracts.py          # Contrato UniversityProvider
|   |   +-- unac/                 # Provider UNAC
|   |   |   +-- provider.py       # Configuración UNAC
|   |   |   `-- centro_formatos/  # Generadores DOCX
|   |   `-- uni/                  # Provider UNI
|   `-- main.py                   # Punto de entrada FastAPI
+-- docs/                         # Documentación (tú estás aquí)
+-- scripts/                      # Scripts de utilidad
|   +-- check_mojibake.py         # Detecta encoding corrupto
|   +-- fix_mojibake_json.py      # Corrige mojibake
|   +-- fix_to_utf8.py            # Convierte a UTF-8
|   `-- test_pdf_concurrency.py   # Test de concurrencia PDF
+-- tests/                        # Tests
`-- requirements.txt              # Dependencias Python
```

---

## Archivos Clave

### Backend

| Archivo | Propósito | Fuente |
|---------|-----------|--------|
| `app/main.py` | Inicializa FastAPI, registra routers | L28-77 |
| `app/core/loaders.py` | Discovery de formatos JSON | L194-275 |
| `app/core/pdf_converter.py` | Word COM singleton para PDF | L63-219 |
| `app/core/registry.py` | Discovery de providers | L39-106 |
| `app/core/paths.py` | Rutas de cache DOCX/PDF | L56-68 |

### Módulos

| Módulo | Router | Service |
|--------|--------|---------|
| catalog | `router.py` L37-83 | `service.py` L157-256 |
| formats | `router.py` L320-437 | `service.py` L96-213 |
| references | `router.py` L45-81 | `service.py` L131-194 |
| alerts | `router.py` L32-50 | (usa provider.list_alerts) |
| admin | `router.py` L33-45 | (sin service) |
| home | `router.py` L32-50 | (usa provider.list_alerts) |

### Frontend

| Archivo | Propósito | Fuente |
|---------|-----------|--------|
| `app/static/js/format-viewer.js` | Carátula, índice, capítulos, descarga | L1-783 |
| `app/static/js/catalog.js` | Filtros y UI del catálogo | L1-? |
| `app/static/js/references.js` | UI de referencias | L1-? |
| `app/templates/pages/detail.html` | Vista de detalle de formato | ~15KB |
| `app/templates/pages/catalog.html` | Vista de catálogo | ~12KB |

### Datos

| Ruta | Contenido |
|------|-----------|
| `app/data/references/*.json` | Normas globales (apa7, ieee, iso690, vancouver) |
| `app/data/unac/references_config.json` | Config de normas para UNAC |
| `app/data/unac/informe/*.json` | Formatos de informe UNAC |
| `app/data/uni/proyecto/*.json` | Formatos de proyecto UNI |
