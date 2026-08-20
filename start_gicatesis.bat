@echo off
setlocal
title GicaTesis Server (:8000)

cd /d "%~dp0"
echo ===================================================
echo   Iniciando GicaTesis en http://127.0.0.1:8000
echo ===================================================

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m uvicorn app.main:app --port 8000 --reload
) else (
    echo [ERROR] No se encontro el entorno virtual .venv en Gicatesis
    pause
)
endlocal
