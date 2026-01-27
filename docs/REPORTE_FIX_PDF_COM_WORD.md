# REPORTE_FIX_PDF_COM_WORD

Fecha: 2026-01-23

## 1) Causa raíz detectada
- La conversión DOCX->PDF se ejecutaba en hilos arbitrarios del servidor y reutilizaba una instancia COM de Word sin un hilo STA dedicado.
- Bajo concurrencia, Word COM quedaba en estado inválido y lanzaba: **-2147220995 “El objeto no está conectado al servidor”**.

## 2) Cambios realizados
- Nuevo manager robusto de conversión PDF con Word COM:
  - `app/core/pdf_converter.py`
  - Hilo STA dedicado + singleton Word + cola de trabajos
  - Serialización de conversiones (una a la vez)
  - Reintento y reinicio de Word ante com_error
  - Timeout con reinicio forzado
- Integración en endpoint PDF:
  - `app/modules/formats/router.py`
  - Usa `convert_docx_to_pdf` del manager
  - Logs de cache, tiempos de conversión y errores
  - Cache invalida si PDF está vacío
- Script de prueba concurrente:
  - `scripts/test_pdf_concurrency.py`

## 3) Cómo funciona el manager
- **Hilo STA único**: todas las conversiones pasan por el mismo hilo, evitando problemas de COM en threads distintos.
- **Singleton Word**: Word se crea una vez y se reutiliza.
- **Lock + cola**: solo una conversión a la vez.
- **Retry + restart**: si hay com_error o “Object is not connected”, se reinicia Word y se reintenta 1 vez.
- **Timeout**: si una conversión se cuelga, se reinicia Word y se reporta error.

## 4) Cache
- Si el PDF existe y es más nuevo que el origen, se reutiliza.
- Si el PDF está vacío/corrupto, se regenera.
- DOCX se cachea y se reutiliza si está vigente.

## 5) Cómo validar
1) Iniciar servidor.
2) Pedir un PDF: `/formatos/<id>/pdf` y verificar que responde.
3) Segunda solicitud debe ser instantánea (cache hit).
4) Ejecutar prueba concurrente:
   ```
   python scripts/test_pdf_concurrency.py http://127.0.0.1:8000 formatos/unac-informe-cual
   ```

## 6) Limitaciones conocidas
- La automatización de Word en servidor **siempre** es frágil; el manager reduce caídas pero no elimina al 100% los riesgos de Office Automation.
- Se recomienda monitorear logs y reiniciar el servicio si Word queda inestable.
