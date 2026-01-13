# Formatoteca (Scaffold en Python)

Repositorio base (cascarón) en **Python + FastAPI + Jinja2** para una “biblioteca de formatos de tesis”.
La app ya tiene:
- **Estructura UI** (sidebar, header, páginas)
- **Rutas** (home, catálogo, detalle, historial, alertas, admin)
- **Data de ejemplo** en JSON para mostrar contenido sin base de datos

El objetivo es que el equipo desarrolle en paralelo sin pisarse:
- **Core estable** (estructura + UI base + rutas)
- **Módulos por universidad** (UNAC / UNI) que se editan de forma independiente

---

## Ejecutar en local

### 1) Instalar dependencias
pip install -r requirements.txt

### 2) Iniciar entorno
python -m uvicorn app.main:app --reload
