"""
Archivo: app/core/pdf_converter.py
Proposito:
- Convertir DOCX a PDF con Word COM de forma estable y reutilizable.

Responsabilidades:
- Mantener una sola instancia de Word (singleton) en un hilo STA dedicado.
- Serializar conversiones con cola + lock.
- Manejar reinicios/reintentos ante com_error (Object not connected).
- Ofrecer timeout y reinicio de Word si se cuelga.

No hace:
- No genera DOCX ni gestiona cache (eso vive en modules/formats).

Entradas/Salidas:
- Entradas: docx_path, pdf_path, timeout.
- Salidas: PDF generado en disco o excepcion controlada.

Dependencias:
- pythoncom, win32com, threading, queue, logging.

Donde tocar si falla:
- Ajustar _convert_with_retry, timeouts o el reinicio de Word.
"""
from __future__ import annotations

import atexit
import logging
import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pythoncom
import win32com.client
import pywintypes

try:
    import win32process  # type: ignore
except Exception:  # pragma: no cover
    win32process = None


logger = logging.getLogger(__name__)

_RETRYABLE_HRESULTS = {
    -2147220995,  # "El objeto no está conectado al servidor"
}


@dataclass
class _Job:
    docx_path: str
    pdf_path: str
    timeout: float
    done: threading.Event
    error: Optional[BaseException] = None


class PdfConversionManager:
    """Manager dedicado a conversiones DOCX->PDF con Word COM."""

    def __init__(self) -> None:
        self._queue: queue.Queue[_Job] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._lock = threading.Lock()
        self._word_app = None
        self._word_pid: Optional[int] = None
        self._restart_requested = False
        self._thread.start()

    def convert(self, docx_path: str, pdf_path: str, timeout: float = 120.0) -> None:
        """Encola y espera la conversion. Lanza excepcion si falla."""
        job = _Job(docx_path=docx_path, pdf_path=pdf_path, timeout=timeout, done=threading.Event())
        self._queue.put(job)

        if not job.done.wait(timeout=timeout):
            # Timeout: reiniciar Word y propagar error
            logger.error("PDF conversion timeout: %s -> %s", docx_path, pdf_path)
            self._force_restart_word(reason="timeout")
            raise TimeoutError("Timeout generando PDF")

        if job.error:
            raise job.error

    def shutdown(self) -> None:
        """Cierra Word si existe."""
        self._force_restart_word(reason="shutdown")

    def _worker(self) -> None:
        pythoncom.CoInitialize()
        logger.info("PDF conversion worker iniciado (STA).")
        try:
            while True:
                job = self._queue.get()
                if job is None:
                    break
                try:
                    self._convert_with_retry(job.docx_path, job.pdf_path)
                except Exception as exc:
                    job.error = exc
                finally:
                    job.done.set()
                    self._queue.task_done()
        finally:
            self._reset_word_app()
            pythoncom.CoUninitialize()

    def _convert_with_retry(self, docx_path: str, pdf_path: str) -> None:
        for attempt in range(2):
            try:
                self._convert_docx_internal(docx_path, pdf_path)
                return
            except Exception as exc:
                hresult = getattr(exc, "hresult", None)
                if isinstance(exc, pywintypes.com_error) and exc.args:
                    # exc.args: (hresult, text, details, arg)
                    if hresult is None:
                        hresult = exc.args[0] if exc.args else None
                logger.warning(
                    "PDF conversion error (attempt %s): %s (hresult=%s)",
                    attempt + 1,
                    exc,
                    hresult,
                )
                if hresult in _RETRYABLE_HRESULTS and attempt == 0:
                    self._force_restart_word(reason="com_error")
                    continue
                if attempt == 0:
                    # reinicio generico una vez
                    self._force_restart_word(reason="generic_error")
                    continue
                raise

    def _convert_docx_internal(self, docx_path: str, pdf_path: str) -> None:
        with self._lock:
            if self._restart_requested:
                self._reset_word_app()
                self._restart_requested = False

            word = self._get_word_app()
            doc = None
            try:
                doc = word.Documents.Open(docx_path, ReadOnly=0, AddToRecentFiles=False)
                doc.Fields.Update()
                for toc in doc.TablesOfContents:
                    toc.Update()
                for tof in doc.TablesOfFigures:
                    tof.Update()
                doc.SaveAs(pdf_path, FileFormat=17)
            finally:
                if doc is not None:
                    doc.Close(False)

    def _get_word_app(self):
        if self._word_app is None:
            self._word_app = win32com.client.DispatchEx("Word.Application")
            self._word_app.Visible = False
            self._word_app.DisplayAlerts = 0
            self._word_pid = self._resolve_word_pid(self._word_app)
            logger.info("Word COM iniciado (pid=%s)", self._word_pid)
        return self._word_app

    def _resolve_word_pid(self, word_app) -> Optional[int]:
        try:
            hwnd = word_app.Hwnd
            if hwnd and win32process:
                _tid, pid = win32process.GetWindowThreadProcessId(hwnd)
                return pid
        except Exception:
            return None
        return None

    def _force_restart_word(self, reason: str) -> None:
        logger.warning("Reiniciando Word COM (reason=%s)", reason)
        self._restart_requested = True
        self._reset_word_app()

    def _reset_word_app(self) -> None:
        if self._word_app is not None:
            try:
                self._word_app.Quit()
            except Exception:
                pass
        if self._word_pid:
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(self._word_pid), "/T", "/F"],
                    check=False,
                    capture_output=True,
                )
            except Exception:
                pass
        self._word_app = None
        self._word_pid = None


_MANAGER: Optional[PdfConversionManager] = None
_MANAGER_LOCK = threading.Lock()


def get_pdf_converter() -> PdfConversionManager:
    global _MANAGER
    if _MANAGER is None:
        with _MANAGER_LOCK:
            if _MANAGER is None:
                _MANAGER = PdfConversionManager()
                atexit.register(_MANAGER.shutdown)
    return _MANAGER


def convert_docx_to_pdf(docx_path: str, pdf_path: str, timeout: float = 120.0) -> None:
    """API publico: convierte docx a pdf usando el manager."""
    return get_pdf_converter().convert(docx_path, pdf_path, timeout=timeout)

