# Formatoteca (GicaTesis)

Plataforma de gestion y generacion de formatos de tesis universitarias. **Python + FastAPI + Block Engine DOCX**.

**Version:** 1.0.0

## Ejecutar (local)

```bash
# Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
py -m uvicorn app.main:app --reload
```

Luego abre:
- Home: http://127.0.0.1:8000/
- Catalogo: http://127.0.0.1:8000/catalog
- Referencias: http://127.0.0.1:8000/referencias
- API docs: http://127.0.0.1:8000/docs

---

## Variables de Entorno

| Variable | Requerida | Default | Descripcion |
|----------|-----------|---------|-------------|
| `GICATESIS_API_KEY` | No | (vacio) | Si se define, `/api/v1/*` exige header `X-GICATESIS-KEY` |
| `GICATESIS_CORS_ORIGINS` | No | `http://localhost:3000,...` | Origenes CORS separados por coma |
| `GICA_DEFAULT_UNI` | No | `unac` | Codigo de universidad por defecto |
| `PDF_CACHE_MAX_AGE` | No | `3600` | Segundos de cache para PDFs |
| `PDF_PREWARM_ON_STARTUP` | No | `false` | Si es `true`, genera PDFs al iniciar |
| `PDF_CONVERSION_TIMEOUT` | No | `120` | Timeout en segundos para Word COM |

---

## Reglas de render para integracion con GicaGen

El pipeline de render DOCX/PDF aplica estas reglas para evitar resultados
engañosos o placeholders en el documento final:

1. Caratula:
   - Si el formato trae un placeholder literal de titulo, se usa `values.title`
     (fallback: `project_title`, `projectTitle` o `values.project.title`).
2. Indices:
   - El TOC, indice de tablas e indice de figuras siempre cierran con salto de
     pagina.
3. Indice de abreviaturas:
   - Se renderiza como tabla de 2 columnas (`SIGLA | SIGNIFICADO`), alineada a
     la izquierda y sin numeracion.
   - Formatos aceptados para entrada de abreviaturas:
     - `IA: Inteligencia Artificial`
     - `IA - Inteligencia Artificial`
     - `IA<TAB>Inteligencia Artificial`
4. Imagenes:
   - Si `ruta` es `placeholder`, vacia o no existe, la figura se omite.
   - No se imprime texto de ejemplo ni cajas de reemplazo.
5. Texto IA:
   - Antes de inyectar contenido IA al JSON de render, se limpia markdown
     (`**`, encabezados `#`, tablas con `|`, fences ```), y se eliminan lineas
     tipo `FIGURA DE EJEMPLO` o `[Insertar ...]`.

---

## Estructura del Proyecto

### Motor de Bloques (`app/engine/`)
Pipeline JSON -> Normalizer -> Block[] -> DOCX con 19 tipos de bloque y 12 renderers.
- `normalizer.py` -- JSON -> `List[Block]`
- `registry.py` -- `@register()` + `render_blocks()`
- `primitives.py` -- Helpers DOCX atomicos
- `types.py` -- Tipos Block y BlockRenderer
- `renderers/` -- 12 modulos especializados

### Backend (Python/FastAPI)
- `app/modules/home/` -- Pantalla de inicio
- `app/modules/catalog/` -- Catalogo de formatos (tarjetas + generacion)
- `app/modules/formats/` -- Detalle de formatos, PDF preview, versiones
- `app/modules/references/` -- API y vistas de normas bibliograficas (APA, IEEE, etc.)
- `app/modules/alerts/` -- Sistema de notificaciones
- `app/modules/admin/` -- Panel de administracion
- `app/modules/api/` -- API v1 (formatos, generacion, render)
- `app/modules/generation/` -- Servicio de generacion de documentos

### Frontend (Templates & Static)
- `app/templates/pages/` -- Vistas HTML (Jinja2)
- `app/templates/components/` -- Componentes reutilizables (cover_modal, header, sidebar)
- `app/static/js/` -- Logica de cliente (7 archivos)
- `app/static/css/` -- Estilos

### Datos
- `app/data/unac/` -- Formatos UNAC (informe, maestria, proyecto)
- `app/data/uni/` -- Formatos UNI (informe, posgrado, proyecto)
- `app/data/schemas/` -- JSON Schemas de validacion
- `app/data/references/` -- Normas bibliograficas (APA7, IEEE, ISO690, Vancouver)

### Universidades (`app/universities/`)
- `shared/universal_generator.py` -- Generador unificado para todas las categorias
- `unac/provider.py` -- Configuracion UNAC
- `uni/provider.py` -- Configuracion UNI
- `contracts.py` -- Contrato UniversityProvider

---

## Tests

```bash
py -m pytest tests/ -v
```

## Validacion de datos

```bash
python scripts/validate_data.py
```

## Verificacion de encoding

```bash
python scripts/check_encoding.py
python scripts/check_mojibake.py
```

---

## Documentacion

- [CHANGELOG](docs/CHANGELOG.md)
- [Manual completo](docs/manual/00_indice.md)
- [Guia de integracion GicaGen](docs/GICAGEN_INTEGRATION_GUIDE.md)
- [API de formatos](docs/api/formats-api.md)
- [Contratos DTO](docs/contracts/format-dto.md)
- [Block Engine](docs/manual/16_block_engine.md)
- [Validacion y Tests](docs/manual/17_validacion_y_tests.md)

## Mockup original

Guardado en `ui/mockup/index.html` como referencia visual.
