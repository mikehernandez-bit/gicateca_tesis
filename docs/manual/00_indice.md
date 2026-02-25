# Indice General de Documentacion

## Rutas Principales del Sistema

| Ruta | Descripcion | Fuente |
|------|-------------|--------|
| `/` | Pagina de inicio | `app/modules/home/router.py` |
| `/catalog` | Catalogo de formatos | `app/modules/catalog/router.py` |
| `/catalog/generate` | Generacion de DOCX | `app/modules/catalog/router.py` |
| `/formatos/{format_id}` | Detalle de formato | `app/modules/formats/router.py` |
| `/formatos/{format_id}/pdf` | Vista previa PDF | `app/modules/formats/router.py` |
| `/formatos/{format_id}/data` | JSON del formato | `app/modules/formats/router.py` |
| `/referencias` | Referencias bibliograficas | `app/modules/references/router.py` |
| `/api/referencias` | API de normas | `app/modules/references/router.py` |
| `/api/referencias/{ref_id}` | Detalle de norma | `app/modules/references/router.py` |
| `/alerts` | Alertas/Notificaciones | `app/modules/alerts/router.py` |
| `/admin` | Panel de administracion | `app/modules/admin/router.py` |
| `/api/v1/formats` | API v1: lista de formatos | `app/modules/api/router.py` |
| `/api/v1/formats/{id}` | API v1: detalle formato | `app/modules/api/router.py` |
| `/api/v1/formats/version` | API v1: version catalogo | `app/modules/api/router.py` |
| `/api/v1/formats/validate` | API v1: validar catalogo | `app/modules/api/router.py` |
| `/api/v1/generate` | API v1: generar documento | `app/modules/api/generation_router.py` |
| `/api/v1/artifacts/{run_id}/docx` | API v1: descargar DOCX | `app/modules/api/generation_router.py` |
| `/api/v1/artifacts/{run_id}/pdf` | API v1: descargar PDF | `app/modules/api/generation_router.py` |
| `/api/v1/render/docx` | API v1: render DOCX directo | `app/modules/api/render_router.py` |
| `/api/v1/render/pdf` | API v1: render PDF directo | `app/modules/api/render_router.py` |
| `/api/v1/assets/{path}` | API v1: assets (logos) | `app/modules/api/router.py` |

---

## Documentos del Manual

1. [Vision General](01_vision_general.md)
2. [Instalacion y Ejecucion](02_instalacion_y_ejecucion.md)
3. [Estructura del Repositorio](03_estructura_del_repo.md)
4. [Arquitectura](04_arquitectura.md)
5. [Modelo de Datos JSON](05_modelo_de_datos_json.md)
6. [Universidades y Providers](06_universidades_y_providers.md)
7. [Catalogo](07_catalogo.md)
8. [Formatos: Detalle y Exportacion](08_formatos_detalle_y_exportacion.md)
9. [Referencias Bibliograficas](09_referencias_bibliograficas.md)
10. [Alertas y Admin](10_alertas_y_admin.md)
11. [Frontend: Templates y JS](11_frontend_templates_y_js.md)
12. [Operacion PDF y Word COM](12_operacion_pdf_y_word_com.md)
13. [Troubleshooting](13_troubleshooting.md)
14. [Contribucion y Estandares](14_contribucion_y_estandares.md)
15. [Glosario](15_glosario.md)
16. [Block Engine](16_block_engine.md)
17. [Validacion y Tests](17_validacion_y_tests.md)

---

## Propuestas

- [Propuesta de arquitectura escalable](../proposals/architecture-scalability.md)

## Diseno Futuro

- [Tablas complejas, citas y orientacion](07_diseno_futuro_formato.md)
