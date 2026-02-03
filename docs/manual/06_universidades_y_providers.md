# Universidades y Providers

## Providers Actuales

| Código | Nombre | Directorio |
|--------|--------|------------|
| `unac` | UNAC | `app/universities/unac/` |
| `uni` | UNI | `app/universities/uni/` |

**Fuente:** Discovery en `app/core/registry.py` L39-49

---

## Estructura de un Provider

```
app/universities/unac/
├── __init__.py
├── provider.py           # Configuración del provider
└── centro_formatos/      # Generadores DOCX
    ├── generador_informe_tesis.py
    ├── generador_maestria.py
    └── generador_proyecto_tesis.py
```

### Archivo `provider.py` (UNAC)

```python
from pathlib import Path
from app.core.paths import get_data_dir
from app.universities.contracts import SimpleUniversityProvider

BASE_DIR = Path(__file__).resolve().parent / "centro_formatos"

PROVIDER = SimpleUniversityProvider(
    code="unac",
    display_name="UNAC",
    data_dir=get_data_dir("unac"),
    generator_map={
        "informe": BASE_DIR / "generador_informe_tesis.py",
        "maestria": BASE_DIR / "generador_maestria.py",
        "proyecto": BASE_DIR / "generador_proyecto_tesis.py",
    },
)
```

**Fuente:** `app/universities/unac/provider.py` L24-43

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
        """Retorna el script generador para la categoría."""
    
    def list_alerts(self) -> list:
        """Lee alertas desde alerts.json."""
    
    def list_formatos(self) -> list:
        """Lee formatos desde formatos.json (legacy)."""
```

**Fuente:** `app/universities/contracts.py` L35-52

---

## Cómo Agregar una Nueva Universidad

### Checklist

1. **Crear directorio provider:**
   ```
   app/universities/nueva_uni/
   ├── __init__.py
   ├── provider.py
   └── centro_formatos/
       └── generador_informe.py  # (u otros)
   ```

2. **Crear `provider.py`:**
   ```python
   from pathlib import Path
   from app.core.paths import get_data_dir
   from app.universities.contracts import SimpleUniversityProvider

   BASE_DIR = Path(__file__).resolve().parent / "centro_formatos"

   PROVIDER = SimpleUniversityProvider(
       code="nueva_uni",
       display_name="Nueva Universidad",
       data_dir=get_data_dir("nueva_uni"),
       generator_map={
           "informe": BASE_DIR / "generador_informe.py",
       },
   )
   ```

3. **Crear directorio de datos:**
   ```
   app/data/nueva_uni/
   ├── alerts.json          # []
   ├── references_config.json
   └── informe/
       └── nueva_uni_informe_cual.json
   ```

4. **Crear `references_config.json`:**
   ```json
   {
     "university": "nueva_uni",
     "title": "Normas de citación (Nueva Uni)",
     "enabled": ["apa7", "ieee"],
     "order": ["apa7", "ieee"],
     "notes": {}
   }
   ```

5. **Verificar discovery:**
   - El sistema descubre automáticamente providers en `app/universities/*/provider.py`.
   - **Fuente:** `app/core/registry.py` L39-49

---

## Logos de Universidad

Los logos se ubican en `app/static/assets/`:

| Universidad | Logo |
|-------------|------|
| UNAC | `LogoUNAC.png` |
| UNI | `LogoUNI.png` |

La selección del logo en la vista previa de carátula se hace en JavaScript:

```javascript
if (formatId.toLowerCase().startsWith('uni')) {
    logoImg.src = "/static/assets/LogoUNI.png";
} else {
    logoImg.src = "/static/assets/LogoUNAC.png";
}
```

**Fuente:** `app/static/js/format-viewer.js` L121-125
