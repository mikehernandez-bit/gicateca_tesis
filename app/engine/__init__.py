"""
Block-Based Document Engine for GicaTesis.

Arquitectura:
    JSON → Normalizer → Block[] → Engine (render_blocks) → DOCX

Módulos:
    types.py      – Definiciones de Block y BlockRenderer.
    registry.py   – Registry con @register('tipo') y render_block().
    primitives.py – Funciones DOCX puras (futuro, Fase 2).
    normalizer.py – JSON canónico v2 → Block[] (futuro, Fase 3).
    renderers/    – Un archivo por tipo de bloque (futuro, Fase 4).
"""
