"""
Universal Generator - GicaTesis
===============================
Genera documentos DOCX para todas las universidades y formatos de tesis.

Arquitectura: Block Engine (Fase 5)
    JSON → normalize() → Block[] → render_blocks() → DOCX

El código de rendering vive ahora en:
    app/engine/normalizer.py   — JSON → Block[]
    app/engine/renderers/      — Block → python-docx
    app/engine/primitives.py   — helpers DOCX atómicos
    app/engine/registry.py     — @register + dispatch

Este archivo conserva únicamente:
    - load_json()               — carga del JSON de entrada
    - generate_document_unified — orquesta el pipeline
    - __main__                  — CLI para subprocess
"""
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path (needed when called via subprocess)
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from docx import Document

# ─────────────────────────────────────────────────────────────
# ENGINE IMPORTS
# ─────────────────────────────────────────────────────────────

# Trigger registration of all 19 block-type renderers
import app.engine.renderers  # noqa: F401

from app.engine.normalizer import normalize
from app.engine.primitives import configure_styles, configure_margins
from app.engine.registry import render_blocks


# ─────────────────────────────────────────────────────────────
# JSON LOADER
# ─────────────────────────────────────────────────────────────

def load_json(path_str: str):
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"JSON not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────────────────────

def generate_document_unified(json_path: str, output_path: str):
    """Genera un DOCX completo a partir de un JSON canónico v2.

    Pipeline:
        1. Carga JSON
        2. configure_styles + configure_margins
        3. normalize(data) → Block[]
        4. render_blocks(doc, blocks) → DOCX in-memory
        5. doc.save(output_path)
    """
    data = load_json(json_path)
    doc = Document()

    # 1. Setup
    configure_styles(doc)
    configure_margins(doc)

    # 2. Normalize → flat block list
    blocks = normalize(data)

    # 3. Render all blocks
    render_blocks(doc, blocks)

    # 4. Save
    doc.save(output_path)
    print(f"[OK] Generated: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        try:
            generate_document_unified(sys.argv[1], sys.argv[2])
        except Exception as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
    else:
        print("Usage: python universal_generator.py <input_json> <output_docx>")

