# Guia de escalabilidad multi-universidad

Esta guia describe como agregar universidades y formatos sin tocar core ni modules.

## 1) Agregar una universidad nueva

1. Crear carpeta en `app/universities/<codigo>/`.
2. Implementar `app/universities/<codigo>/provider.py` y exponer `PROVIDER` (o `get_provider()`).
3. Cumplir el contrato en `app/universities/contracts.py` usando `SimpleUniversityProvider`:
   - `code`: slug ASCII (ej: `unac`, `uni`).
   - `display_name`: nombre visible (puede tener tildes).
   - `data_dir`: `app/data/<code>`.
   - `generator_map`: rutas a generadores por categoria.

Ejemplo minimo:

```python
from pathlib import Path
from app.core.paths import get_data_dir
from app.universities.contracts import SimpleUniversityProvider

BASE_DIR = Path(__file__).resolve().parent / "centro_formatos"

PROVIDER = SimpleUniversityProvider(
    code="xyz",
    display_name="Universidad XYZ",
    data_dir=get_data_dir("xyz"),
    generator_map={
        "informe": BASE_DIR / "generador_informe_tesis.py",
        "maestria": BASE_DIR / "generador_maestria.py",
        "proyecto": BASE_DIR / "generador_proyecto_tesis.py",
    },
)
```

El registry detecta automaticamente `provider.py` sin imports estaticos.

## 2) Agregar un formato nuevo (solo JSON)

Crear un archivo JSON en:

```
app/data/<uni>/<categoria>/
```

Ejemplos:

```
app/data/unac/informe/unac_informe_cual.json
app/data/unac/maestria/unac_maestria_cuant.json
```

No se requiere cambiar JS ni Python. El discovery lo detecta automaticamente.

## 3) Convenciones de nombres

- IDs y slugs: ASCII y en minuscula.
- Titulos visibles: pueden incluir tildes (ej: "Maestria").
- Categoria: nombre de la carpeta inmediata (ej: `informe`, `proyecto`, `maestria`).
- Enfoque: se deriva del nombre del archivo (cual/cuant/general).
- `format_id` global: se normaliza como `<uni>-<categoria>-<enfoque>` o se deriva del filename
  (siempre unico).

## 4) Generadores DOCX

- Se mantienen por categoria (no por formato).
- El core llama al generador segun `get_generator_command(category)`.
- Si una universidad no tiene generador, se lanza:
  `generator not available for category <categoria>`.
