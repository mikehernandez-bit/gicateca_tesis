# REPORTE_OPTIMIZACION_PDF

## 1) Baseline (antes de cambios)
- Estado: NO ejecutado por error de dependencia.
- Error: ModuleNotFoundError: No module named 'pythoncom'.
- Nota: El endpoint /formatos/{id}/pdf depende de Word COM (pywin32).
- Formatos planeados: unac-informe-cual, unac-maestria-cuant.
- Carpeta baseline creada: docs/_baseline_pdf_speed (sin PDFs por el error).

## 2) Timing despues de cambios
- Estado: NO ejecutado por la misma dependencia faltante (pythoncom).

## 3) Arquitectura de cache
- Cache persistente en:
  - DOCX: app/.cache/docx/<format_id>.docx
  - PDF: app/.cache/pdf/<format_id>.pdf
- Invalida por mtime de:
  - JSON del formato
  - script generador
  - app/modules/formats/service.py
  - app/core/loaders.py
- Manifest opcional por formato:
  - app/.cache/pdf/<format_id>.manifest.json
  - Incluye rutas y mtimes de JSON/generador + paths docx/pdf + sha256_pdf.

## 4) Word COM singleton y lock
- Word se instancia una sola vez por proceso (singleton).
- Se protege conversion con Lock (Word COM no thread-safe).
- En fallo COM se reinicia la instancia para la siguiente conversion.
- atexit cierra Word al salir.

## 5) HTTP cache
- Respuestas PDF agregan Cache-Control, ETag y Last-Modified.
- Si el cliente envia If-None-Match o If-Modified-Since y el cache es valido, responde 304.

## 5.1) Variables de entorno
- PDF_PREWARM_ON_STARTUP: false (default). Si true, precalienta PDFs en startup.
- PDF_CACHE_MAX_AGE: 3600 (default). Max-age para Cache-Control.

## 6) Archivos modificados
- app/modules/formats/router.py
- app/core/paths.py
- app/main.py
- requirements.txt
- .gitignore
- docs/REPORTE_OPTIMIZACION_PDF.md

## 7) Checklist de validacion
- [ ] /formatos/{id}/pdf cold mas rapido que antes (Word reuse + docx cache)
- [ ] /formatos/{id}/pdf warm casi instantaneo (FileResponse)
- [ ] PDF visualmente identico a antes (TOC/TOF/estilos)
- [ ] Manifest generado en app/.cache/pdf
- [ ] Cache-Control, ETag y Last-Modified presentes

## 8) Proxima accion requerida
- Instalar pywin32 en el entorno local y re-ejecutar baseline/after:
  - pip install pywin32
