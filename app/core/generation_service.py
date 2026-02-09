"""
Generation Service - Prepares format data for document generation.

This service handles:
1. Loading format definitions
2. Merging user values into placeholders
3. Applying AI-generated or simulated content
4. Excluding instruction/guidance keys from output
5. Orchestrating DOCX/PDF generation via existing generators
"""
from __future__ import annotations

import json
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.core.loaders import load_format_by_id
from app.modules.formats.service import generate_document


# Keys that should NOT appear in the final document
EXCLUDED_KEYS: Set[str] = frozenset({
    "nota", "nota_capitulo", "instruccion", "instruccion_detallada",
    "guia", "ejemplo", "comentario", "observacion", "placeholder",
    "tipo_vista", "vista_previa", "_meta", "version", "descripcion",
})

# Storage for generated artifacts (in-memory with TTL)
_ARTIFACTS_STORE: Dict[str, "GenerationResult"] = {}
_ARTIFACTS_TTL_SECONDS = 3600  # 1 hour


@dataclass
class ArtifactInfo:
    """Info about a generated artifact."""
    type: str
    path: Path
    download_url: str


@dataclass
class GenerationResult:
    """Result of a generation run."""
    project_id: str
    run_id: str
    format_id: str
    status: str
    artifacts: List[ArtifactInfo] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    error: Optional[str] = None


def _generate_run_id() -> str:
    """Generate a unique run ID."""
    return f"gen-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def _get_artifacts_dir() -> Path:
    """Get/create artifacts storage directory."""
    path = Path("outputs") / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cleanup_old_artifacts() -> None:
    """Remove artifacts older than TTL."""
    now = time.time()
    expired = [
        run_id for run_id, result in _ARTIFACTS_STORE.items()
        if now - result.created_at > _ARTIFACTS_TTL_SECONDS
    ]
    for run_id in expired:
        result = _ARTIFACTS_STORE.pop(run_id, None)
        if result:
            for artifact in result.artifacts:
                try:
                    artifact.path.unlink(missing_ok=True)
                except Exception:
                    pass


def _exclude_instruction_keys(obj: Any) -> Any:
    """
    Recursively remove instruction/guidance keys from format data.
    
    Preserves structural keys (titulo, texto) but removes:
    nota, instruccion, guia, ejemplo, etc.
    """
    if isinstance(obj, dict):
        return {
            key: _exclude_instruction_keys(value)
            for key, value in obj.items()
            if key.lower() not in EXCLUDED_KEYS
        }
    elif isinstance(obj, list):
        return [_exclude_instruction_keys(item) for item in obj]
    return obj


def _apply_ai_content(
    data: Dict[str, Any],
    ai_sections: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Apply AI content to the document structure.
    
    ai_sections is a list of {"path": "Section/Subsection", "content": "..."}
    For simulation mode, inserts placeholder if no content provided.
    """
    # Build a map of path -> content for quick lookup
    content_map = {
        section.get("path", ""): section.get("content", "")
        for section in ai_sections
    }
    
    def _apply_to_structure(obj: Any, current_path: str = "") -> Any:
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                child_path = f"{current_path}/{key}" if current_path else key
                
                # Check if this key is a section title
                if key in ("titulo", "text", "texto"):
                    result[key] = value
                    # Look for matching AI content
                    title_val = str(value)
                    for path, content in content_map.items():
                        if path and title_val and path.lower() in title_val.lower():
                            result["_ai_content"] = content
                            break
                else:
                    result[key] = _apply_to_structure(value, child_path)
            
            # Add simulation placeholder if no AI content
            if "titulo" in result and "_ai_content" not in result:
                result["_ai_content"] = "[Contenido generado por IA - simulacion]"
            
            return result
        elif isinstance(obj, list):
            return [_apply_to_structure(item, current_path) for item in obj]
        return obj
    
    return _apply_to_structure(data)


def _merge_values(
    data: Dict[str, Any],
    values: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Merge user-provided values into format placeholders.
    
    Looks for placeholder patterns like "[TITULO]" or "{autor}"
    and replaces with actual values.
    """
    def _replace_placeholders(obj: Any) -> Any:
        if isinstance(obj, str):
            result = obj
            for key, value in values.items():
                # Replace common placeholder patterns
                patterns = [
                    f"[{key.upper()}]",
                    f"[{key}]",
                    f"{{{key}}}",
                    f"<{key}>",
                ]
                for pattern in patterns:
                    if pattern in result:
                        result = result.replace(pattern, str(value))
            return result
        elif isinstance(obj, dict):
            return {k: _replace_placeholders(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_replace_placeholders(item) for item in obj]
        return obj
    
    return _replace_placeholders(data)


def generate_artifacts(
    project_id: str,
    format_id: str,
    values: Optional[Dict[str, Any]] = None,
    ai_result: Optional[Dict[str, Any]] = None,
    mode: str = "simulation",
) -> GenerationResult:
    """
    Generate DOCX and PDF artifacts using the real GicaTesis generators.
    
    Args:
        project_id: Unique project identifier
        format_id: Format to generate (must be publishable)
        values: User-provided values for placeholders
        ai_result: AI-generated content sections
        mode: "simulation" or "production"
    
    Returns:
        GenerationResult with artifact paths and download URLs
    """
    _cleanup_old_artifacts()
    
    run_id = _generate_run_id()
    
    # 1. Load and validate format
    try:
        raw_data = load_format_by_id(format_id)
    except FileNotFoundError:
        return GenerationResult(
            project_id=project_id,
            run_id=run_id,
            format_id=format_id,
            status="error",
            error=f"Format not found: {format_id}",
        )
    
    # Check publishable (check _meta.publish directly on raw data)
    meta = raw_data.get("_meta", {})
    if meta.get("entity") != "format" or not meta.get("publish", False):
        return GenerationResult(
            project_id=project_id,
            run_id=run_id,
            format_id=format_id,
            status="error",
            error="Format is not publishable",
        )
    
    # 2. Exclude instruction keys
    clean_data = _exclude_instruction_keys(raw_data)
    
    # 3. Merge user values
    if values:
        clean_data = _merge_values(clean_data, values)
    
    # 4. Apply AI content (or simulation placeholders)
    ai_sections = []
    if ai_result and isinstance(ai_result.get("sections"), list):
        ai_sections = ai_result["sections"]
    clean_data = _apply_ai_content(clean_data, ai_sections)
    
    # 5. Write merged JSON to temp file
    artifacts_dir = _get_artifacts_dir()
    run_dir = artifacts_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    merged_json_path = run_dir / "merged_input.json"
    merged_json_path.write_text(
        json.dumps(clean_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    # 6. Generate DOCX using existing generator
    try:
        docx_path, _filename = generate_document(format_id)
        # Move to run directory
        final_docx = run_dir / f"{format_id.replace('/', '_')}.docx"
        docx_path.rename(final_docx)
    except Exception as exc:
        return GenerationResult(
            project_id=project_id,
            run_id=run_id,
            format_id=format_id,
            status="error",
            error=f"DOCX generation failed: {exc}",
        )
    
    # 7. Convert to PDF (lazy import to avoid pythoncom dependency at module level)
    final_pdf = run_dir / f"{format_id.replace('/', '_')}.pdf"
    try:
        from app.core.pdf_converter import convert_docx_to_pdf
        convert_docx_to_pdf(str(final_docx), str(final_pdf))
    except Exception as exc:
        # PDF conversion failed but DOCX succeeded
        pass
    
    # 8. Build result
    artifacts = [
        ArtifactInfo(
            type="docx",
            path=final_docx,
            download_url=f"/api/v1/artifacts/{run_id}/docx",
        ),
    ]
    if final_pdf.exists():
        artifacts.append(
            ArtifactInfo(
                type="pdf",
                path=final_pdf,
                download_url=f"/api/v1/artifacts/{run_id}/pdf",
            )
        )
    
    result = GenerationResult(
        project_id=project_id,
        run_id=run_id,
        format_id=format_id,
        status="success",
        artifacts=artifacts,
    )
    
    # Store for later retrieval
    _ARTIFACTS_STORE[run_id] = result
    
    return result


def get_artifact_path(run_id: str, artifact_type: str) -> Optional[Path]:
    """
    Get the path to a generated artifact.
    
    Returns None if not found or expired.
    """
    result = _ARTIFACTS_STORE.get(run_id)
    if not result:
        return None
    
    for artifact in result.artifacts:
        if artifact.type == artifact_type:
            if artifact.path.exists():
                return artifact.path
    
    return None
