# Instalación y Ejecución

## Prerrequisitos

| Requisito | Versión | Notas |
|-----------|---------|-------|
| Python | 3.10+ | Verificar con `py --version` |
| Microsoft Word | 2016+ | **Solo Windows**. Requerido para `docx2pdf` |
| pip | Actualizado | `py -m pip install --upgrade pip` |

**Fuente:** `requirements.txt` L1-7

---

## Pasos de Instalación

### 1. Clonar el Repositorio

```bash
git clone <url-del-repo>
cd gicateca_tesis
```

### 2. Crear Entorno Virtual

```bash
py -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Contenido de requirements.txt:**
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
jinja2==3.1.4
pydantic
python-docx
docx2pdf
pywin32
```

**Fuente:** `requirements.txt` L1-7

### 4. Ejecutar el Servidor

```bash
py -m uvicorn app.main:app --reload
```

El servidor estará disponible en: `http://127.0.0.1:8000`

**Fuente:** Comando estándar de uvicorn. La app se define en `app/main.py` L39.

---

## Variables de Entorno (Opcionales)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `PDF_CACHE_MAX_AGE` | `3600` | Segundos de cache para PDFs |
| `PDF_PREWARM_ON_STARTUP` | `false` | Si es `true`, genera PDFs al iniciar |
| `PDF_CONVERSION_TIMEOUT` | `120` | Timeout en segundos para Word COM |

**Fuente:** `app/modules/formats/router.py` L47-49

---

## Verificar Instalación

1. Navegar a `http://127.0.0.1:8000/` → Debe mostrar la página de inicio.
2. Navegar a `http://127.0.0.1:8000/catalog` → Debe listar formatos.
3. Navegar a `http://127.0.0.1:8000/docs` → Swagger UI de FastAPI.
