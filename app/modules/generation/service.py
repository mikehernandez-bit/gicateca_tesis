"""
Archivo: app/modules/generation/service.py
Proposito:
- Orquesta la generacion de artefactos DOCX/PDF.

Responsabilidades:
- Cargar definiciones de formato.
- Preprocesar datos (sanitizar, merge, AI content).
- Invocar el pipeline de generacion via formats/service.
- Gestionar artefactos temporales con TTL.
No hace:
- No define rutas HTTP.
- No genera DOCX directamente (delega a generadores).

Dependencias:
- app.core.loaders, app.modules.formats.service, app.modules.generation.preprocessor.
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
from app.core.document_generator import generate_document_by_id as generate_document

from app.modules.generation.preprocessor import exclude_instruction_keys, merge_values, apply_ai_content

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
    clean_data = exclude_instruction_keys(raw_data)
    
    # 3. Merge user values
    if values:
        clean_data = merge_values(clean_data, values)
    
    # 4. Apply AI content (or simulation placeholders)
    ai_sections = []
    if ai_result and isinstance(ai_result.get("sections"), list):
        ai_sections = ai_result["sections"]
    clean_data = apply_ai_content(clean_data, ai_sections)
    
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
        docx_path, _filename = generate_document(format_id, override_json_path=merged_json_path)
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
    
    # 7. Convert to PDF
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
