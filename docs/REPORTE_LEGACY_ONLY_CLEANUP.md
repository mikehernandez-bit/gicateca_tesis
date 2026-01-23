# 1) Qué se eliminó (lista completa “spec”)
- app/static/js/format-viewer.js: removidas las rutas de render “spec” (`isSpecFormat`, `buildStructureFromSpec`, `findChapterInSpec`, `getCoverFromSpec`) y las ramas condicionales que las usaban en carátula/índice/capítulos.
- app/static/js/format-viewer.js: eliminado el hidratado de requisitos exclusivo de spec (capítulos desde `data.content.chapters`).
- app/core/loaders.py: eliminado el filtro por carpeta `_spec_backup` (no hay backups spec; discovery queda 100% legacy).
- Búsqueda de `schema_version`, `page_setup`, `legacy_to_spec`, `spec_to_legacy`, `preliminaries`, `isSpecFormat`: sin resultados en código; coincidencias restantes son texto “específicos” en JSONs (no relacionadas a schema).

# 2) Cambios por archivo (qué, por qué)
- app/static/js/format-viewer.js: simplificado a flujo legacy único (carátula/preliminares/cuerpo/finales), removidas funciones spec y duplicados de hidratación; mantiene UI y previews sin cambiar estructura visual.
- app/core/loaders.py: se quitó el filtro `_spec_backup` para eliminar toda referencia “spec” en discovery.
- app/main.py: middleware que fuerza `charset=utf-8` para `text/*`, `application/json` y `application/javascript`, asegurando decodificación correcta de acentos en UI.
- docs/_after_legacy_only_cleanup/*.docx: generación post-limpieza para comparación.
- docs/_after_legacy_only_cleanup/hashes.json: hashes SHA256 de XML internos clave para verificación de igualdad.

# 3) Evidencia de que todo es legacy (ejemplos de JSON keys)
Top-level keys reales por archivo (legacy):
- app/data/unac/informe/unac_informe_cual.json: `caratula`, `preliminares`, `cuerpo`, `finales`, `matriz_consistencia`, `version`, `descripcion`.
- app/data/unac/informe/unac_informe_cuant.json: `caratula`, `preliminares`, `cuerpo`, `finales`, `matriz_consistencia`, `version`, `descripcion`.
- app/data/unac/proyecto/unac_proyecto_cual.json: `configuracion`, `caratula`, `pagina_respeto`, `informacion_basica`, `preliminares`, `cuerpo`, `finales`, `matriz_consistencia`.
- app/data/unac/proyecto/unac_proyecto_cuant.json: `configuracion`, `caratula`, `pagina_respeto`, `informacion_basica`, `preliminares`, `cuerpo`, `finales`, `matriz_consistencia`.
- app/data/unac/maestria/unac_maestria_cual.json: `caratula`, `preliminares`, `cuerpo`, `finales`, `version`, `descripcion`, `informacion_basica`.
- app/data/unac/maestria/unac_maestria_cuant.json: `caratula`, `preliminares`, `cuerpo`, `finales`, `version`, `descripcion`, `informacion_basica`.

No se encontraron claves `schema_version`, `page_setup`, `preliminaries` (spec) en los JSON legacy.

# 4) Fix encoding “Maestr??a” (origen y corrección)
- Origen probable: respuestas de recursos de texto sin `charset`, lo que puede hacer que el navegador interprete UTF-8 como otra codificación (acentos corruptos en UI).
- Corrección aplicada: middleware en app/main.py que fuerza `charset=utf-8` para HTML/JS/JSON.
- Verificación de soporte UTF-8: templates ya incluyen `<meta charset="UTF-8">` y lectura de JSON usa `encoding="utf-8"` en loaders/servicios.

# 5) Verificación DOCX (tabla baseline vs after con OK/DIFF)
Archivos comparados: `word/document.xml`, `word/styles.xml`, `word/numbering.xml`, `word/settings.xml`, `word/_rels/document.xml.rels`, `word/header*.xml`, `word/footer*.xml`.

| Documento | Baseline | After | Resultado |
| --- | --- | --- | --- |
| UNAC_informe_cual.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |
| UNAC_informe_cuant.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |
| UNAC_proyecto_cual.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |
| UNAC_proyecto_cuant.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |
| UNAC_maestria_cual.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |
| UNAC_maestria_cuant.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |

# 6) Checklist final
- [x] Eliminada toda lógica “spec” en frontend y discovery.
- [x] Backend opera solo con schema legacy.
- [x] Encoding UTF-8 garantizado en respuestas HTML/JS/JSON.
- [x] DOCX (6 formatos) idénticos a baseline (hashes OK).
