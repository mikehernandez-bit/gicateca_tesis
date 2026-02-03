# Operación PDF y Word COM

## Descripción

La conversión DOCX → PDF se realiza usando **Microsoft Word COM** (Component Object Model) en Windows. Esto permite:

1. Actualizar campos (TOC, referencias cruzadas) antes de convertir.
2. Generar PDFs idénticos a como se verían en Word.

**Requisito:** Microsoft Word instalado en el servidor (Windows).

---

## Arquitectura del Conversor

### Singleton con Hilo STA

Word COM requiere ejecutarse en un hilo con COM inicializado (STA - Single-Threaded Apartment). El sistema implementa un **singleton** con cola de trabajos.

**Fuente:** `app/core/pdf_converter.py` L63-219

```python
class PdfConversionManager:
    def __init__(self):
        self._queue = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._lock = threading.Lock()
        self._word_app = None
        self._word_pid = None
        self._restart_requested = False
        self._thread.start()
```

### Flujo de Conversión

1. `convert()` encola un trabajo.
2. El hilo worker lo procesa.
3. `_convert_docx_internal()` abre el documento, actualiza campos, guarda como PDF.
4. El resultado (o error) se devuelve al llamador.

**Fuente:** `app/core/pdf_converter.py` L75-88, L138-156

---

## Manejo de Errores

### Error Típico: "El objeto no está conectado al servidor"

**HRESULT:** `-2147220995`

Este error ocurre cuando:
- Word se cuelga.
- Word se cerró inesperadamente.
- Hay un timeout.

**Fuente:** `app/core/pdf_converter.py` L49-51

```python
_RETRYABLE_HRESULTS = {
    -2147220995,  # "El objeto no está conectado al servidor"
}
```

### Reintentos Automáticos

El sistema reintenta automáticamente ante errores conocidos:

```python
def _convert_with_retry(self, docx_path: str, pdf_path: str):
    for attempt in range(2):
        try:
            self._convert_docx_internal(docx_path, pdf_path)
            return
        except Exception as exc:
            hresult = getattr(exc, "hresult", None)
            if hresult in _RETRYABLE_HRESULTS and attempt == 0:
                self._force_restart_word(reason="com_error")
                continue
            raise
```

**Fuente:** `app/core/pdf_converter.py` L112-136

### Reinicio de Word

Cuando se detecta un error, el sistema:

1. Marca `_restart_requested = True`.
2. Intenta cerrar Word con `Quit()`.
3. Si falla, usa `taskkill` para matar el proceso.
4. Reinicia Word en el próximo trabajo.

**Fuente:** `app/core/pdf_converter.py` L177-198

```python
def _reset_word_app(self):
    if self._word_app is not None:
        try:
            self._word_app.Quit()
        except Exception:
            pass
    if self._word_pid:
        subprocess.run(
            ["taskkill", "/PID", str(self._word_pid), "/T", "/F"],
            check=False,
            capture_output=True,
        )
    self._word_app = None
    self._word_pid = None
```

---

## Timeout

El timeout por defecto es **120 segundos**.

Si se excede, el sistema:
1. Fuerza reinicio de Word.
2. Lanza `TimeoutError`.

**Fuente:** `app/core/pdf_converter.py` L80-84

**Variable de entorno:** `PDF_CONVERSION_TIMEOUT`

**Fuente:** `app/modules/formats/router.py` L49

---

## API Pública

```python
from app.core.pdf_converter import convert_docx_to_pdf

convert_docx_to_pdf(
    docx_path="path/to/file.docx",
    pdf_path="path/to/output.pdf",
    timeout=120.0
)
```

**Fuente:** `app/core/pdf_converter.py` L215-217

---

## Limitaciones Conocidas

| Limitación | Descripción |
|------------|-------------|
| Solo Windows | Requiere Microsoft Word instalado |
| Concurrencia limitada | Un solo hilo procesa conversiones |
| Timeout largo | Documentos complejos pueden tardar |
| Bloqueo de UI Word | Si Word muestra diálogos, puede colgarse |

### Mitigaciones Implementadas

1. **Singleton** evita múltiples instancias de Word.
2. **Lock** serializa conversiones.
3. **Reintentos** ante errores conocidos.
4. **Taskkill** como último recurso.
5. **Timeout configurable**.

**Fuente:** `app/core/pdf_converter.py` L1-219
