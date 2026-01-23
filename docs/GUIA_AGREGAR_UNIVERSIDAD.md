# Guia para agregar una universidad

## Pasos

1) Crear carpeta `app/universities/<codigo>/`.
2) Crear `app/universities/<codigo>/provider.py` con `PROVIDER`.
3) Crear data runtime en `app/data/<codigo>/...`.
4) (Opcional) Crear generadores en `app/universities/<codigo>/centro_formatos/`.

## Ejemplo de provider

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

## Convenciones

- `code` debe ser ASCII y minuscula.
- `display_name` puede tener tildes.
- Los generadores se registran por categoria (no por formato).
