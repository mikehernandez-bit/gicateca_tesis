# Arquitectura y estructura del proyecto

## 1) Arbol final del repo

```
gicateca_tesis/
|-- app
|   |-- core
|   |   |-- __init__.py
|   |   |-- loaders.py
|   |   |-- paths.py
|   |   |-- registry.py
|   |   |-- seed_loader.py
|   |   |-- templates.py
|   |   `-- university_registry.py
|   |-- data
|   |   |-- unac
|   |   |   |-- informe
|   |   |   |   |-- unac_informe_cual.json
|   |   |   |   `-- unac_informe_cuant.json
|   |   |   |-- maestria
|   |   |   |   |-- unac_maestria_cual.json
|   |   |   |   `-- unac_maestria_cuant.json
|   |   |   |-- proyecto
|   |   |   |   |-- unac_proyecto_cual.json
|   |   |   |   `-- unac_proyecto_cuant.json
|   |   |   `-- alerts.json
|   |   `-- uni
|   |       |-- alerts.json
|   |       `-- formatos.json
|   |-- modules
|   |   |-- admin
|   |   |   |-- __init__.py
|   |   |   |-- router.py
|   |   |   |-- schemas.py
|   |   |   `-- service.py
|   |   |-- alerts
|   |   |   |-- __init__.py
|   |   |   |-- router.py
|   |   |   |-- schemas.py
|   |   |   `-- service.py
|   |   |-- catalog
|   |   |   |-- __init__.py
|   |   |   |-- router.py
|   |   |   |-- schemas.py
|   |   |   `-- service.py
|   |   |-- formats
|   |   |   |-- __init__.py
|   |   |   |-- router.py
|   |   |   |-- schemas.py
|   |   |   `-- service.py
|   |   `-- home
|   |       |-- __init__.py
|   |       |-- router.py
|   |       |-- schemas.py
|   |       `-- service.py
|   |-- static
|   |   |-- assets
|   |   |   |-- figura_ejemplo.png
|   |   |   `-- LogoUNAC.png
|   |   |-- css
|   |   |   `-- extra.css
|   |   `-- js
|   |       |-- catalog.js
|   |       |-- format-viewer.js
|   |       `-- navigation.js
|   |-- templates
|   |   |-- components
|   |   |   |-- header.html
|   |   |   `-- sidebar.html
|   |   |-- pages
|   |   |   |-- admin.html
|   |   |   |-- alerts.html
|   |   |   |-- catalog.html
|   |   |   |-- detail.html
|   |   |   |-- home.html
|   |   |   `-- versions.html
|   |   `-- base.html
|   |-- universities
|   |   |-- unac
|   |   |   |-- centro_formatos
|   |   |   |   |-- __init__.py
|   |   |   |   |-- generador_informe_tesis.py
|   |   |   |   |-- generador_maestria.py
|   |   |   |   `-- generador_proyecto_tesis.py
|   |   |   `-- provider.py
|   |   |-- uni
|   |   |   `-- provider.py
|   |   |-- __init__.py
|   |   |-- contracts.py
|   |   `-- registry.py
|   |-- __init__.py
|   `-- main.py
|-- data
|   `-- seed
|       |-- alerts.sample.json
|       `-- formatos.sample.json
|-- docs
|   |-- ARQUITECTURA_Y_ESTRUCTURA.md
|   |-- CODE_DUMP
|   |   |-- CODE_DUMP_PART_01.md
|   |   `-- INDEX.md
|   |-- GUIA_AGREGAR_FORMATO.md
|   |-- GUIA_AGREGAR_UNIVERSIDAD.md
|   |-- GUIA_ESCALABILIDAD_UNIVERSIDADES.md
|   `-- REPORTE_LEGACY_ONLY_CLEANUP.md
|-- ui
|   `-- mockup
|       |-- index.html
|       `-- README.txt
|-- .gitignore
|-- README.md
|-- REFACTORING_SUMMARY.md
|-- requirements.txt
`-- test_data.py
```

## 2) Para que sirve cada carpeta

- `app/core`: utilidades transversales (paths, loaders, registry, templates).
- `app/modules`: features (routers + services + schemas).
- `app/universities`: plugins por universidad (providers + generadores).
- `app/data`: JSON runtime por universidad y categoria.
- `app/templates` y `app/static`: UI (HTML, CSS, JS, assets).
- `docs`: documentacion y reportes.

## 3) Archivos clave (core / modules / universities)

### Core
- `app/core/paths.py`: paths canonicos del proyecto (app root, data root, docs).
- `app/core/registry.py`: discovery dinamico de providers (plugin-like).
- `app/core/university_registry.py`: wrapper de compatibilidad para imports antiguos.
- `app/core/loaders.py`: discovery de formatos (multi-uni) + carga de JSON.
- `app/core/templates.py`: setup de Jinja2Templates.

### Modules
- `app/modules/catalog/router.py`: endpoint `/catalog` y `/catalog/generate`.
- `app/modules/catalog/service.py`: construccion de catalogo y generacion DOCX por categoria.
- `app/modules/formats/router.py`: endpoints `/formatos/{id}`, `/data`, `/generate`, `/pdf`.
- `app/modules/formats/service.py`: obtencion de formato y generacion DOCX por formato.
- `app/modules/home/router.py`: home y selector de universidad.
- `app/modules/alerts/router.py`: alerts por universidad.

### Universities
- `app/universities/contracts.py`: contrato `UniversityProvider` y `SimpleUniversityProvider`.
- `app/universities/registry.py`: wrapper hacia `app/core/registry.py`.
- `app/universities/unac/provider.py`: provider UNAC con generadores por categoria.
- `app/universities/uni/provider.py`: provider UNI (sin generadores).
- `app/universities/*/centro_formatos/*.py`: generadores DOCX por categoria.

## 4) Donde tocar (debug map)

- Catalogo no lista formatos: revisar `app/core/loaders.py` y `app/modules/catalog/service.py`.
- Detalle de formato falla: revisar `app/modules/formats/router.py` y `app/modules/formats/service.py`.
- Generacion DOCX falla: revisar provider `get_generator_command` y `app/modules/formats/service.py`.
- No detecta nueva universidad: revisar `app/core/registry.py` y `app/universities/<code>/provider.py`.
- No detecta nuevo formato: verificar JSON en `app/data/<uni>/<categoria>/`.
- Encoding incorrecto: revisar `<meta charset>` en `app/templates/base.html` y lectura UTF-8 en loaders.

## 5) Guia: agregar formato (solo JSON)

1) Crear JSON en `app/data/<uni>/<categoria>/`.
2) Mantener naming ASCII en id/slug.
3) Abrir `/catalog` y `/formatos/{id}` para confirmar discovery.

Ver tambien: `docs/GUIA_AGREGAR_FORMATO.md`.

## 6) Guia: agregar universidad

1) Crear `app/universities/<code>/provider.py` con `SimpleUniversityProvider`.
2) Crear data en `app/data/<code>/...`.
3) (Opcional) Crear generadores en `app/universities/<code>/centro_formatos/`.

Ver tambien: `docs/GUIA_AGREGAR_UNIVERSIDAD.md`.

## 7) Flujo principal (request -> docx)

1) Request llega a router (`/catalog` o `/formatos/{id}`).
2) Service llama a `discover_format_files()` (loaders).
3) Loaders usan registry para obtener provider y data_dir.
4) Para generacion, service obtiene `provider.get_generator_command(categoria)`.
5) Se ejecuta generador por categoria con JSON de formato.
6) Se retorna DOCX al cliente.

## 8) Checklist de verificacion

- [ ] `/catalog` lista formatos por discovery.
- [ ] `/formatos/{id}` y `/formatos/{id}/data` funcionan.
- [ ] Generacion DOCX UNAC funciona.
- [ ] Encoding UTF-8 correcto en UI (ej: “Maestría”).
