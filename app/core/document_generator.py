"""
Archivo: app/core/document_generator.py
Proposito:
- Centraliza la resolucion y ejecucion de generadores DOCX.

Responsabilidades:
- Resolver el comando del script generador desde el provider.
- Ejecutar el subprocess que produce el DOCX.
- Limpiar archivos temporales de forma segura.
No hace:
- No define rutas HTTP ni renderiza templates.
- No gestiona cache (eso va en formats/router o un futuro cache_service).

Entradas/Salidas:
- Entradas: format_id, generator command, rutas JSON/output.
- Salidas: (output_path, filename) del DOCX generado.

Dependencias:
- subprocess, tempfile, pathlib, app.core.loaders, app.core.registry.
- app.core.format_builder (para normalize_format_type).

Puntos de extension:
- Agregar hooks pre/post generacion.
- Soportar nuevos tipos de generadores (no solo subprocess).

Donde tocar si falla:
- Revisar resolve_generator_command y ejecucion de subprocess.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

from app.core.loaders import find_format_index
from app.core.registry import get_provider
from app.core.format_builder import normalize_format_type


# ─────────────────────────────────────────────────────────────────────────────
# RESOLUCION DE GENERADORES
# ─────────────────────────────────────────────────────────────────────────────

def resolve_generator_command(
    generator: Union[Path, Sequence[str]],
    json_path: Path,
    output_path: Path,
) -> Tuple[List[str], Optional[Path]]:
    """
    Resuelve el comando del generador y su directorio de trabajo.

    Soporta:
    - list/tuple: se interpreta como comando ya compuesto.
    - Path/str: se interpreta como ruta a script .py.

    Retorna: (cmd_list, workdir_or_None).
    """
    if isinstance(generator, (list, tuple)):
        cmd = [str(part) for part in generator]
        workdir = None
        for part in reversed(generator):
            part_str = str(part)
            if part_str.endswith(".py"):
                workdir = Path(part_str).resolve().parent
                break
        return cmd + [str(json_path), str(output_path)], workdir

    script_path = Path(generator)
    if not script_path.exists():
        raise RuntimeError(f"Generator script not found: {script_path}")
    return [sys.executable, str(script_path), str(json_path), str(output_path)], script_path.parent


# ─────────────────────────────────────────────────────────────────────────────
# GENERACION DE DOCUMENTOS
# ─────────────────────────────────────────────────────────────────────────────

def generate_document_by_id(
    format_id: str,
    section_filter: Optional[str] = None,
    override_json_path: Optional[Path] = None,
) -> Tuple[Path, str]:
    """
    Genera un DOCX para un formato identificado por format_id.

    Permite:
    - section_filter == "planteamiento": filtra solo Capitulo I.
    - override_json_path: usa un JSON preprocesado en lugar del original.

    Retorna: (output_path, filename).
    """
    item = find_format_index(format_id)
    if not item:
        raise ValueError(f"Invalid format ID: {format_id}")

    tipo = item.categoria
    enfoque = item.enfoque

    provider = get_provider(item.uni)
    generator = provider.get_generator_command(tipo)

    json_path = item.path
    if not json_path.exists():
        raise RuntimeError(f"JSON file not found: {json_path}")

    # ─── LOGICA DE OVERRIDE O FILTRADO ───
    path_to_use = json_path
    cleanup_path = False

    if override_json_path:
        path_to_use = override_json_path

    elif section_filter == "planteamiento":
        # 1. Cargamos el JSON original
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 2. Vaciamos todo lo que no sea el cuerpo
        data["preliminares"] = {}
        data["finales"] = {}
        data["matriz_consistencia"] = {}

        if "caratula" in data:
            data["caratula"]["tipo_documento"] = "VISTA PREVIA - CAPITULO I"

        # 3. Nos quedamos SOLO con el bloque que tenga "PLANTEAMIENTO"
        data["cuerpo"] = [
            cap for cap in data.get("cuerpo", [])
            if "PLANTEAMIENTO" in cap.get("titulo", "").upper()
        ]

        # 4. Guardamos el JSON filtrado
        tmp_json = tempfile.NamedTemporaryFile(
            prefix="filtered_", suffix=".json",
            delete=False, mode="w", encoding="utf-8",
        )
        json.dump(data, tmp_json, ensure_ascii=False, indent=2)
        tmp_json.close()

        path_to_use = Path(tmp_json.name)
        cleanup_path = True

    # ─── GENERACION ───
    filename = f"{provider.code.upper()}_{tipo.upper()}_{enfoque.upper()}.docx"
    tmp_file = tempfile.NamedTemporaryFile(
        prefix=f"{provider.code}_", suffix=".docx", delete=False,
    )
    output_path = Path(tmp_file.name)
    tmp_file.close()

    cmd, workdir = resolve_generator_command(generator, path_to_use, output_path)
    result = subprocess.run(
        cmd, cwd=str(workdir) if workdir else None,
        capture_output=True, text=True,
    )

    # Limpiamos el JSON temporal si fue creado por el filtro
    if cleanup_path and path_to_use != json_path and path_to_use != override_json_path:
        try:
            path_to_use.unlink()
        except Exception:
            pass

    if result.returncode != 0:
        print("[ERROR]", result.stderr)
        raise RuntimeError("Document generation failed. Check console for details.")

    if not output_path.exists():
        raise RuntimeError("Generator script executed but did not create DOCX file.")

    return output_path, filename


def generate_document_by_type(
    fmt_type: str,
    sub_type: str,
    uni: str = "unac",
) -> Tuple[Path, str]:
    """
    Genera un DOCX para un formato identificado por tipo/subtipo/universidad.

    Usado por el endpoint POST /catalog/generate.
    Retorna: (output_path, filename).
    """
    fmt_type = normalize_format_type(fmt_type)
    sub_type = (sub_type or "").strip().lower()

    provider = get_provider(uni)
    generator = provider.get_generator_command(fmt_type)

    json_path = provider.get_data_dir() / fmt_type / f"{provider.code}_{fmt_type}_{sub_type}.json"
    if not json_path.exists():
        raise RuntimeError(f"JSON no encontrado: {json_path}")

    filename = f"{provider.code.upper()}_{fmt_type.upper()}_{sub_type.upper()}.docx"
    tmp_file = tempfile.NamedTemporaryFile(
        prefix=f"{provider.code}_", suffix=".docx", delete=False,
    )
    output_path = Path(tmp_file.name)
    tmp_file.close()

    cmd, workdir = resolve_generator_command(generator, json_path, output_path)
    result = subprocess.run(
        cmd, cwd=str(workdir) if workdir else None,
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        print("[ERROR PYTHON]", result.stderr)
        raise RuntimeError("Fallo la generacion interna. Revisa consola.")

    if not output_path.exists():
        raise RuntimeError("El script corrio pero no genero el DOCX")

    return output_path, filename


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────────────────────

def cleanup_temp_file(path: Path) -> None:
    """Elimina un archivo temporal si existe."""
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:
        print(f"[WARN] Could not delete temp file: {exc}")
