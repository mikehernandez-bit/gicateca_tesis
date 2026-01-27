# Formatoteca

Este repositorio es una estructura base en **Python + FastAPI + Jinja2** para una “biblioteca de formatos de tesis”.
La idea es que cada colaborador tome un **módulo** (Catálogo, Detalle, Alertas, etc.) y lo complete mediante Pull Requests.

## Ejecutar (local)
# Windows: 
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
# Visual Code:
pip install -r requirements.txt
python uvicorn app.main:app --reload

Luego abre:
- Home: http://127.0.0.1:8000/
- Catálogo: http://127.0.0.1:8000/catalog
- Alertas: http://127.0.0.1:8000/alerts

---

## Estructura del Proyecto

### Backend (Python/FastAPI)
- `app/modules/home/` -> Pantalla de Inicio.
- `app/modules/catalog/` -> **Controlador del Catálogo.** Gestiona la visualización de tarjetas de normas y carátulas.
- `app/modules/formats/` -> Detalle de formatos específicos.
- `app/modules/referencias/` -> **(Nuevo)** Lógica para la API y vistas de Normas (APA, IEEE, etc.).
- `app/modules/alerts/` -> Sistema de notificaciones.
- `app/modules/admin/` -> Panel de Administración.

### Frontend (Templates & Static)
- `app/templates/pages/` -> Vistas HTML (Jinja2).
    - `catalog.html`: Grid principal de tarjetas con filtros por categoría.
    - `references.html`: Vista de detalle de la norma (Layout optimizado sin sidebar).
- `app/static/js/` -> **Lógica de Cliente (Actualizado):**
    - `catalog.js`: Renderizado limpio de tarjetas (sin tags visuales ni cajas de previsualización), descripciones cortadas al primer punto.
    - `references.js`: Controla el "ScrollSpy" (menú lateral derecho), la navegación de retorno forzada al catálogo y la lógica de desplazamiento suave calibrada (offset de 100px).

- `data/seed/` -> JSON de ejemplo (contenido estático para pruebas sin BD).

---

## Estado Actual del Desarrollo (ChangeLog)

### 1. Módulo Catálogo (`/catalog`)
- **Limpieza Visual:** Se eliminaron los "tags" (círculos azules) y las cajas de previsualización gris de las tarjetas de referencias para una interfaz minimalista.
- **Formato de Texto:** Las descripciones de las normas ahora se recortan automáticamente hasta el primer punto para mantener uniformidad.
- **Navegación:** Los enlaces de "Ver guía" dirigen al usuario a la vista de detalle de referencia manteniendo el contexto.

### 2. Módulo Referencias (`/referencias`)
- **Flujo de Navegación:**
    - El botón "Volver a normas" redirige forzosamente al Catálogo (`/catalog`), eliminando la vista intermedia de lista grid para un flujo más directo.
    - Se ocultó permanentemente el contenedor `refs-grid-view` en el HTML.
- **Layout (Diseño):**
    - Se eliminó la barra lateral izquierda (Sidebar de lista de normas) para dar prioridad al contenido de lectura.
    - Implementación de **CSS Grid** (`1fr` contenido / `320px` menú derecho) para aprovechar mejor el ancho de pantalla.
- **Tabla de Contenidos (ScrollSpy):**
    - Menú lateral derecho ("En esta guía") que se pinta de azul automáticamente según la sección visible al hacer scroll.
    - **Navegación Precisa:** Implementación de lógica de clic con `scrollIntoView` y márgenes calibrados:
        - **Offset:** 100px (para respetar el encabezado fijo y que el título no se tape).
        - **Observer:** Margen de detección `-90px` para una sincronización perfecta al subir y bajar.

---

## Reglas
- No hacer push directo a `main`.

## Verificacion de encoding
- Ejecutar: `python scripts/check_mojibake.py`
  
## Mockup original
Está guardado en `ui/mockup/index.html` como referencia visual.



