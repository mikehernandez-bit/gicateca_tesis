# Documentacion del Sistema GicaTesis (Formatoteca)

Esta carpeta contiene la documentacion tecnica completa del sistema **GicaTesis/Formatoteca**.

## Como Navegar

El manual tecnico esta organizado en la carpeta `manual/`. Comienza por el indice:

--> **[Indice General](manual/00_indice.md)**

## Requisitos Minimos

**Fuente:** `requirements.txt`

- Python 3.10+
- FastAPI 0.115.0
- Uvicorn 0.30.6
- Jinja2 3.1.4
- Pydantic 2.10.6
- python-docx 1.1.2
- python-multipart 0.0.20
- docx2pdf 0.1.8 (requiere Microsoft Word en Windows)
- pywin32 308
- pytest 8.3.4
- jsonschema 4.23.0

## Ejecutar el Servidor

```bash
py -m uvicorn app.main:app --reload
```

**Fuente:** Servidor corriendo segun `app/main.py` L46

## Estructura de la Documentacion

| Archivo | Contenido |
|---------|-----------|
| [00_indice.md](manual/00_indice.md) | Indice navegable |
| [01_vision_general.md](manual/01_vision_general.md) | Que es GicaTesis y flujo de usuario |
| [02_instalacion_y_ejecucion.md](manual/02_instalacion_y_ejecucion.md) | Setup del entorno |
| [03_estructura_del_repo.md](manual/03_estructura_del_repo.md) | Mapa del repositorio |
| [04_arquitectura.md](manual/04_arquitectura.md) | Diagrama y pipeline |
| [05_modelo_de_datos_json.md](manual/05_modelo_de_datos_json.md) | Esquemas JSON |
| [06_universidades_y_providers.md](manual/06_universidades_y_providers.md) | UNAC, UNI, extensibilidad |
| [07_catalogo.md](manual/07_catalogo.md) | Modulo catalogo |
| [08_formatos_detalle_y_exportacion.md](manual/08_formatos_detalle_y_exportacion.md) | Generacion DOCX/PDF |
| [09_referencias_bibliograficas.md](manual/09_referencias_bibliograficas.md) | Normas APA, IEEE, etc. |
| [10_alertas_y_admin.md](manual/10_alertas_y_admin.md) | Modulos alerts y admin |
| [11_frontend_templates_y_js.md](manual/11_frontend_templates_y_js.md) | Templates y JS |
| [12_operacion_pdf_y_word_com.md](manual/12_operacion_pdf_y_word_com.md) | Word COM y conversion PDF |
| [13_troubleshooting.md](manual/13_troubleshooting.md) | Problemas comunes |
| [14_contribucion_y_estandares.md](manual/14_contribucion_y_estandares.md) | Como contribuir |
| [15_glosario.md](manual/15_glosario.md) | Terminos tecnicos |
| [16_block_engine.md](manual/16_block_engine.md) | Motor de Bloques (Block Engine) |
| [17_validacion_y_tests.md](manual/17_validacion_y_tests.md) | Validacion y tests |

## Guias Adicionales

| Archivo | Contenido |
|---------|-----------|
| [GICAGEN_INTEGRATION_GUIDE.md](GICAGEN_INTEGRATION_GUIDE.md) | Integracion con GicaGen |
| [formats-api.md](api/formats-api.md) | API de formatos v1 |
| [format-dto.md](contracts/format-dto.md) | Contratos DTO |
| [versioning-cache.md](runbooks/versioning-cache.md) | Cache y versionado |

## Propuestas Tecnicas

| Archivo | Contenido |
|---------|-----------|
| [architecture-scalability.md](proposals/architecture-scalability.md) | Propuesta: Universidad como Plugin (escalabilidad) |

## Reglas de encoding

- Guardar archivos en UTF-8.
- No usar caracteres de box drawing en docs o codigo.
- No usar emojis en documentacion.
- Ejecutar `python scripts/check_encoding.py` antes de commit.
- Ejecutar `python scripts/check_mojibake.py` antes de commit.
