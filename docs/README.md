# Documentación del Sistema GicaTesis (Formatoteca)

Esta carpeta contiene la documentación técnica completa del sistema **GicaTesis/Formatoteca**.

## Cómo Navegar

El manual técnico está organizado en la carpeta `manual/`. Comienza por el índice:

➡️ **[Índice General](manual/00_indice.md)**

## Requisitos Mínimos

**Fuente:** `requirements.txt` L1-7

- Python 3.10+
- FastAPI 0.115.0
- Uvicorn 0.30.6
- Jinja2 3.1.4
- python-docx
- docx2pdf (requiere Microsoft Word en Windows)
- pywin32

## Ejecutar el Servidor

```bash
py -m uvicorn app.main:app --reload
```

**Fuente:** Servidor corriendo según `app/main.py` L39

## Estructura de la Documentación

| Archivo | Contenido |
|---------|-----------|
| [00_indice.md](manual/00_indice.md) | Índice navegable |
| [01_vision_general.md](manual/01_vision_general.md) | Qué es GicaTesis y flujo de usuario |
| [02_instalacion_y_ejecucion.md](manual/02_instalacion_y_ejecucion.md) | Setup del entorno |
| [03_estructura_del_repo.md](manual/03_estructura_del_repo.md) | Mapa del repositorio |
| [04_arquitectura.md](manual/04_arquitectura.md) | Diagrama y pipeline |
| [05_modelo_de_datos_json.md](manual/05_modelo_de_datos_json.md) | Esquemas JSON |
| [06_universidades_y_providers.md](manual/06_universidades_y_providers.md) | UNAC, UNI, extensibilidad |
| [07_catalogo.md](manual/07_catalogo.md) | Módulo catálogo |
| [08_formatos_detalle_y_exportacion.md](manual/08_formatos_detalle_y_exportacion.md) | Generación DOCX/PDF |
| [09_referencias_bibliograficas.md](manual/09_referencias_bibliograficas.md) | Normas APA, IEEE, etc. |
| [10_alertas_y_admin.md](manual/10_alertas_y_admin.md) | Módulos alerts y admin |
| [11_frontend_templates_y_js.md](manual/11_frontend_templates_y_js.md) | Templates y JS |
| [12_operacion_pdf_y_word_com.md](manual/12_operacion_pdf_y_word_com.md) | Word COM y conversión PDF |
| [13_troubleshooting.md](manual/13_troubleshooting.md) | Problemas comunes |
| [14_contribucion_y_estandares.md](manual/14_contribucion_y_estandares.md) | Cómo contribuir |
| [15_glosario.md](manual/15_glosario.md) | Términos técnicos |

## Propuestas Técnicas

| Archivo | Contenido |
|---------|-----------|
| [architecture-scalability.md](proposals/architecture-scalability.md) | Propuesta: Universidad como Plugin (escalabilidad) |

## Reglas de encoding

- Guardar archivos en UTF-8.
- No usar caracteres de box drawing en docs o codigo.
- No usar emojis en documentacion.
- Ejecutar `python scripts/check_encoding.py` antes de commit.
- Ejecutar `python scripts/check_mojibake.py` antes de commit.

