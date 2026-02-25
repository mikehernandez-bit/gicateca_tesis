"""
Archivo: app/engine/renderers/__init__.py
Proposito:
- Importa todos los módulos de renderers para que sus decoradores @register
  se ejecuten al hacer ``import app.engine.renderers``.

Responsabilidades:
- Trigger de registro automático de TODOS los block types.
No hace:
- No contiene lógica propia.

Donde tocar si falla:
- Si un nuevo renderer no se registra, verificar que está importado aquí.
"""

from app.engine.renderers import (  # noqa: F401
    apa_examples,
    centered_text,
    headings,
    image,
    info_table,
    logo,
    matriz,
    note,
    page_control,
    paragraphs,
    table,
    toc,
)
