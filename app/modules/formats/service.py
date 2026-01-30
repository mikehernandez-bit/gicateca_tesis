"""
Archivo: app/modules/formats/service.py
Proposito:
- Implementa logica para obtener formatos y generar DOCX por format_id.

Responsabilidades:
- Construir el detalle de un formato desde el indice.
- Ejecutar generadores por categoria para producir DOCX.
- Aplicar filtros temporales (ej. vista previa de planteamiento).
No hace:
- No define rutas HTTP ni renderiza templates.

Entradas/Salidas:
- Entradas: format_id, filtros opcionales.
- Salidas: dict de formato o rutas de archivos generados.

Dependencias:
- app.core.loaders, app.core.registry, subprocess, tempfile.

Puntos de extension:
- Ajustar filtros de secciones o labels del catalogo.

Donde tocar si falla:
- Revisar find_format_index/load_json_file y ejecucion de generadores.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple, Union

from app.core.loaders import find_format_index, load_json_file
from app.core.registry import get_provider


TIPO_LABELS = {
    "informe": "Informe de Tesis",
    "maestria": "Tesis de Maestr\u00eda",
    "proyecto": "Proyecto de Tesis",
}
ENFOQUE_LABELS = {"cual": "Cualitativo", "cuant": "Cuantitativo"}
TIPO_FILTRO = {
    "informe": "Inv. Formativa",
    "maestria": "Suficiencia",
    "proyecto": "Tesis",
}


def _build_format_title(categoria: str, enfoque: str, raw_title: str, fallback_title: str) -> str:
    """Calcula el titulo visible de un formato."""
    if raw_title:
        return raw_title
    cat_label = TIPO_LABELS.get(categoria)
    enfoque_label = ENFOQUE_LABELS.get(enfoque)
    if cat_label and enfoque_label:
        return f"{cat_label} - {enfoque_label}"
    if cat_label:
        return cat_label
    return fallback_title or categoria.capitalize()


def _build_format_entry(item, data: Dict) -> Dict:
    """Construye el dict de salida para el detalle del formato."""
    raw_title = data.get("titulo") if isinstance(data, dict) else None
    titulo = _build_format_title(item.categoria, item.enfoque, raw_title, item.titulo)
    cat_label = TIPO_LABELS.get(item.categoria, item.categoria.capitalize())
    enfoque_label = ENFOQUE_LABELS.get(item.enfoque)
    resumen = None
    if isinstance(data, dict):
        resumen = data.get("descripcion")
    if not resumen:
        if enfoque_label:
            resumen = f"Plantilla oficial de {cat_label} con enfoque {enfoque_label}"
        else:
            resumen = f"Plantilla oficial de {cat_label}"

    return {
        "id": item.format_id,
        "uni": item.uni.upper(),
        "uni_code": item.uni,
        "tipo": TIPO_FILTRO.get(item.categoria, "Otros"),
        "titulo": titulo,
        "facultad": (data.get("facultad") if isinstance(data, dict) and data.get("facultad") else "Centro de Formatos UNI"),
        "escuela": (data.get("escuela") if isinstance(data, dict) and data.get("escuela") else "Direcci\u00f3n Acad\u00e9mica"),
        "estado": "VIGENTE",
        "version": data.get("version", "1.0.0") if isinstance(data, dict) else "1.0.0",
        "fecha": (data.get("fecha") if isinstance(data, dict) and data.get("fecha") else "2026-01-17"),
        "resumen": resumen,
        "tipo_formato": item.categoria,
        "enfoque": item.enfoque,
    }


def get_formato(format_id: str) -> Optional[Dict]:
    """Retorna el detalle de un formato por ID."""
    item = find_format_index(format_id)
    if not item:
        raise ValueError(f"Format not found: {format_id}")

    # Carga JSON asociado al formato y construye salida.
    try:
        data = item.data if item.data is not None else load_json_file(item.path)
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError(f"Format not found: {format_id}") from exc

    return _build_format_entry(item, data)

def _resolve_generator_command(
    generator: Union[Path, Sequence[str]],
    json_path: Path,
    output_path: Path,
) -> Tuple[list[str], Optional[Path]]:
    """Resuelve el comando del generador y su directorio de trabajo."""
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


def generate_document(format_id: str, section_filter: Optional[str] = None) -> Tuple[Path, str]:
    """
    Genera un DOCX para el formato indicado.
    Permite filtrar secciones (uso interno de vista previa).
    """
    item = find_format_index(format_id)
    if not item:
        raise ValueError(f"Invalid format ID: {format_id}")

    tipo = item.categoria
    enfoque = item.enfoque

    # Usa el provider de la universidad para resolver el generador.
    provider = get_provider(item.uni)
    generator = provider.get_generator_command(tipo)

    json_path = item.path
    if not json_path.exists():
        raise RuntimeError(f"JSON file not found: {json_path}")

    # =========================================================
    # LOGICA DE FILTRADO (SIMPLIFICADA Y AGRESIVA)
    # =========================================================
    path_to_use = json_path

    if section_filter == "planteamiento":
        print(f"[DEBUG] Filtrando SOLO CAP\u00cdTULO I para: {format_id}")

        # 1. Cargamos el JSON original
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 2. LIMPIEZA TOTAL: Vaciamos todo lo que no sea el cuerpo
        data["preliminares"] = {}
        data["finales"] = {}
        data["matriz_consistencia"] = {}

        if "caratula" in data:
            data["caratula"]["tipo_documento"] = "VISTA PREVIA - CAP\u00cdTULO I"

        # 3. FILTRO RAPIDO: Nos quedamos SOLO con el bloque que tenga "PLANTEAMIENTO"
        # Esto elimina cualquier otro capitulo de la lista.
        data["cuerpo"] = [
            cap for cap in data.get("cuerpo", [])
            if "PLANTEAMIENTO" in cap.get("titulo", "").upper()
        ]

        # 4. Guardamos el JSON filtrado
        tmp_json = tempfile.NamedTemporaryFile(prefix="filtered_", suffix=".json", delete=False, mode="w", encoding="utf-8")
        json.dump(data, tmp_json, ensure_ascii=False, indent=2)
        tmp_json.close()

        path_to_use = Path(tmp_json.name)
    # =========================================================

    filename = f"{provider.code.upper()}_{tipo.upper()}_{enfoque.upper()}.docx"
    tmp_file = tempfile.NamedTemporaryFile(prefix=f"{provider.code}_", suffix=".docx", delete=False)
    output_path = Path(tmp_file.name)
    tmp_file.close()

    # Ejecuta el generador externo sin modificar su logica interna.
    cmd, workdir = _resolve_generator_command(generator, path_to_use, output_path)
    result = subprocess.run(cmd, cwd=str(workdir) if workdir else None, capture_output=True, text=True)

    # Debug logs (util si falla)
    # print(f"[DEBUG] Stderr: {result.stderr}")

    # Limpiamos el JSON temporal
    if path_to_use != json_path:
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


def cleanup_temp_file(path: Path) -> None:
    """Elimina un archivo temporal si existe."""
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:
        print(f"[WARN] Could not delete temp file: {exc}")
