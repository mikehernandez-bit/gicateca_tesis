# Universidades y Providers

## Providers Actuales

| Codigo | Nombre | Directorio | Categorias |
|--------|--------|------------|------------|
| `unac` | UNAC | `app/universities/unac/` | informe, maestria, proyecto |
| `uni` | UNI | `app/universities/uni/` | informe, posgrado, proyecto |

**Fuente:** Discovery en `app/core/registry.py`

---

## Estructura de un Provider

```
app/universities/unac/
+-- __init__.py
`-- provider.py           # Configuracion del provider
```

Todos los providers comparten el generador unificado ubicado en:
```
app/universities/shared/
`-- universal_generator.py   # Generador que usa Block Engine
```

### Archivo `provider.py` (UNAC)

```python
from pathlib import Path

from app.core.paths import get_data_dir
from app.universities.contracts import SimpleUniversityProvider

# Carpeta compartida que contiene el generador unificado.
SHARED_DIR = Path(__file__).resolve().parent.parent / "shared"

PROVIDER = SimpleUniversityProvider(
    code="unac",
    display_name="UNAC",
    data_dir=get_data_dir("unac"),
    generator_map={
        "informe": SHARED_DIR / "universal_generator.py",
        "maestria": SHARED_DIR / "universal_generator.py",
        "proyecto": SHARED_DIR / "universal_generator.py",
    },
    # Defaults para view-models de caratula
    default_logo_url="/static/assets/LogoUNAC.png",
    defaults={
        "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
        "lugar": "CALLAO, PERU",
        "anio": "2026",
    },
)
```

**Fuente:** `app/universities/unac/provider.py` L26-51

### Archivo `provider.py` (UNI)

```python
SHARED_DIR = Path(__file__).resolve().parent.parent / "shared"

PROVIDER = SimpleUniversityProvider(
    code="uni",
    display_name="UNI",
    data_dir=get_data_dir("uni"),
    generator_map={
        "informe": SHARED_DIR / "universal_generator.py",
        "maestria": SHARED_DIR / "universal_generator.py",
        "posgrado": SHARED_DIR / "universal_generator.py",
        "proyecto": SHARED_DIR / "universal_generator.py",
    },
    default_logo_url="/static/assets/LogoUNI.png",
    defaults={
        "universidad": "UNIVERSIDAD NACIONAL DE INGENIERIA",
        "lugar": "LIMA - PERU",
        "anio": "2026",
    },
)
```

**Fuente:** `app/universities/uni/provider.py` L34-51

---

## Contrato UniversityProvider

Todo provider debe implementar (o usar `SimpleUniversityProvider`):

```python
class UniversityProvider(Protocol):
    code: str              # "unac", "uni"
    display_name: str      # "UNAC", "UNI"
    data_dir: Path         # app/data/unac
    name: str              # Alias de display_name

    def get_data_dir(self) -> Path:
        """Retorna la carpeta de datos."""

    def get_generator_command(self, category: str) -> GeneratorCommand:
        """Retorna el script generador para la categoria."""

    def list_alerts(self) -> list:
        """Lee alertas desde alerts.json."""

    def list_formatos(self) -> list:
        """Lee formatos legacy desde formatos.json."""
```

**Fuente:** `app/universities/contracts.py` L36-52

### SimpleUniversityProvider (campos adicionales)

| Campo | Tipo | Default | Descripcion |
|-------|------|---------|-------------|
| `code` | str | (requerido) | Codigo de la universidad |
| `display_name` | str | (requerido) | Nombre corto para UI |
| `data_dir` | Path | (requerido) | Carpeta de datos |
| `generator_map` | Dict | (requerido) | Mapa categoria -> generador |
| `name` | str | `display_name` | Alias para templates legacy |
| `default_logo_url` | str | `/static/assets/LogoGeneric.png` | Logo por defecto |
| `defaults` | Dict | `{}` | Valores default para view-models |

### Metodo `get_default(key, fallback)`

```python
def get_default(self, key: str, fallback: str = "") -> str:
    """Obtiene un valor de defaults con fallback."""
    return self.defaults.get(key, fallback)
```

**Fuente:** `app/universities/contracts.py` L55-101

---

## Como Agregar una Nueva Universidad

### Checklist

1. **Crear directorio provider:**
   ```
   app/universities/nueva_uni/
   +-- __init__.py
   `-- provider.py
   ```

2. **Crear `provider.py`:**
   ```python
   from pathlib import Path
   from app.core.paths import get_data_dir
   from app.universities.contracts import SimpleUniversityProvider

   SHARED_DIR = Path(__file__).resolve().parent.parent / "shared"

   PROVIDER = SimpleUniversityProvider(
       code="nueva_uni",
       display_name="Nueva Universidad",
       data_dir=get_data_dir("nueva_uni"),
       generator_map={
           "informe": SHARED_DIR / "universal_generator.py",
       },
       default_logo_url="/static/assets/LogoNUEVA_UNI.png",
       defaults={
           "universidad": "UNIVERSIDAD NUEVA",
           "lugar": "CIUDAD, PERU",
           "anio": "2026",
       },
   )
   ```

3. **Crear directorio de datos:**
   ```
   app/data/nueva_uni/
   +-- alerts.json          # []
   +-- references_config.json
   `-- informe/
       `-- nueva_uni_informe_cual.json
   ```

4. **Crear `references_config.json`:**
   ```json
   {
     "_meta": {
       "entity": "config",
       "publish": false
     },
     "university": "nueva_uni",
     "title": "Normas de citacion (Nueva Uni)",
     "enabled": ["apa7", "ieee"],
     "order": ["apa7", "ieee"],
     "notes": {}
   }
   ```

5. **Marcar formatos publicables con `_meta`:**
   ```json
   {
     "_meta": {
       "entity": "format",
       "publish": true,
       "id": "nueva_uni-informe-cual",
       "uni": "nueva_uni"
     }
   }
   ```

6. **Agregar logo:**
   - Crear `app/static/assets/LogoNUEVA_UNI.png`

7. **Verificar discovery:**
   - El sistema descubre automaticamente providers en `app/universities/*/provider.py`.
   - **NO es necesario tocar** `app/core/registry.py`, ningun `.js` ni ningun `.html`.
   - **Fuente:** `app/core/registry.py`

---

## Logos de Universidad

Los logos se ubican en `app/static/assets/`:

| Universidad | Logo |
|-------------|------|
| UNAC | `LogoUNAC.png` |
| UNI | `LogoUNI.png` |
| Generico | `LogoGeneric.png` |

### Cadena de Resolucion de Logo

| Prioridad | Fuente | Descripcion |
|-----------|--------|-------------|
| 1 | `data.configuracion.ruta_logo` | Override especifico del formato |
| 2 | `provider.default_logo_url` | Default del provider |
| 3 | `/static/assets/LogoGeneric.png` | Fallback generico |

**Fuente:** `app/static/js/cover-preview.js`, `app/core/view_models.py`
