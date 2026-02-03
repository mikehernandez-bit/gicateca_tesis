# Índice General de Documentación

## Rutas Principales del Sistema

| Ruta | Descripción | Fuente |
|------|-------------|--------|
| `/` | Página de inicio | `app/modules/home/router.py` L32-50 |
| `/catalog` | Catálogo de formatos | `app/modules/catalog/router.py` L37-58 |
| `/catalog/generate` | Generación de DOCX | `app/modules/catalog/router.py` L61-83 |
| `/formatos/{format_id}` | Detalle de formato | `app/modules/formats/router.py` L320-336 |
| `/formatos/{format_id}/pdf` | Vista previa PDF | `app/modules/formats/router.py` L380-421 |
| `/formatos/{format_id}/data` | JSON del formato | `app/modules/formats/router.py` L424-437 |
| `/referencias` | Referencias bibliográficas | `app/modules/references/router.py` L45-60 |
| `/api/referencias` | API de normas | `app/modules/references/router.py` L63-68 |
| `/api/referencias/{ref_id}` | Detalle de norma | `app/modules/references/router.py` L71-81 |
| `/alerts` | Alertas/Notificaciones | `app/modules/alerts/router.py` L32-50 |
| `/admin` | Panel de administración | `app/modules/admin/router.py` L33-45 |

---

## Documentos del Manual

1. [Visión General](01_vision_general.md)
2. [Instalación y Ejecución](02_instalacion_y_ejecucion.md)
3. [Estructura del Repositorio](03_estructura_del_repo.md)
4. [Arquitectura](04_arquitectura.md)
5. [Modelo de Datos JSON](05_modelo_de_datos_json.md)
6. [Universidades y Providers](06_universidades_y_providers.md)
7. [Catálogo](07_catalogo.md)
8. [Formatos: Detalle y Exportación](08_formatos_detalle_y_exportacion.md)
9. [Referencias Bibliográficas](09_referencias_bibliograficas.md)
10. [Alertas y Admin](10_alertas_y_admin.md)
11. [Frontend: Templates y JS](11_frontend_templates_y_js.md)
12. [Operación PDF y Word COM](12_operacion_pdf_y_word_com.md)
13. [Troubleshooting](13_troubleshooting.md)
14. [Contribución y Estándares](14_contribucion_y_estandares.md)
15. [Glosario](15_glosario.md)

---

## Propuestas

- [Propuesta de arquitectura escalable](../proposalsCODEX/architecture-scalability.md)

