"""
Archivo: app/modules/api/render_router.py
Proposito:
- Endpoints API para renderizado de documentos DOCX/PDF.

Responsabilidades:
- POST /api/v1/render/docx: Genera DOCX usando el pipeline real.
- POST /api/v1/render/pdf: Genera PDF usando pipeline real + Word COM.
- Modo simulacion: sanitiza JSON, inyecta contenido AI, genera documento.
- Modo final: usa JSON original tal cual.
No hace:
- No contiene logica de generacion. Delega a formats/service y generation/preprocessor.

Dependencias:
- app.modules.formats.service, app.modules.generation.preprocessor, app.core.loaders.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from app.modules.formats import service as formats_service
from app.modules.formats.router import _ensure_pdf_cached, _get_source_mtime
from app.core.loaders import find_format_index
from app.core.document_generator import cleanup_temp_file
from app.modules.generation.preprocessor import (
    exclude_instruction_keys,
    merge_values,
    apply_ai_content,
    cleanup_temp_json,
)


router = APIRouter(prefix="/api/v1/render", tags=["render"])


# Request/Response Models
class AISection(BaseModel):
    """A section of AI-generated content."""
    sectionId: Optional[str] = Field(default=None, description="Stable section ID from sectionIndex")
    path: Optional[str] = Field(default=None, description="Section path like 'Capitulo I/Introduccion'")
    content: str = Field(..., description="AI-generated content for this section")

    @model_validator(mode="after")
    def validate_locator(self) -> "AISection":
        if not (self.sectionId or self.path):
            raise ValueError("AISection requires at least one locator: path or sectionId")
        return self


class AIResult(BaseModel):
    """AI-generated content result."""
    sections: List[AISection] = Field(default_factory=list)


class RenderRequest(BaseModel):
    """Request to render a document using real generators."""
    formatId: str = Field(..., min_length=1, description="Format ID to render")
    values: Dict[str, Any] = Field(default_factory=dict, description="User values for cover page")
    mode: str = Field(default="simulation", description="Render mode: 'simulation' or 'final'")
    aiResult: Optional[AIResult] = Field(default=None, description="AI-generated content")


def _validate_publishable(format_id: str) -> None:
    """Validate format exists and is publishable."""
    item = find_format_index(format_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Format not found: {format_id}")


def _generate_simulation_docx(
    format_id: str,
    values: Dict[str, Any],
    ai_result: Optional[AIResult],
) -> Tuple[Path, str]:
    """
    Generate DOCX in simulation mode:
    1. Load original format JSON
    2. Sanitize (remove notes/guides)
    3. Merge user values
    4. Inject AI content into JSON
    5. Call formats_service.generate_document with override JSON
    """
    item = find_format_index(format_id)
    if not item:
        raise ValueError(f"Invalid format ID: {format_id}")

    # Load original JSON
    json_path = item.path
    if not json_path.exists():
        raise RuntimeError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        format_data = json.load(f)

    # 1) Sanitize: remove instruction/guide keys
    sanitized = exclude_instruction_keys(format_data)

    # 2) Merge user values
    if values:
        sanitized = merge_values(sanitized, values)

    # 3) Apply AI content
    ai_sections = []
    if ai_result and ai_result.sections:
        ai_sections = [
            {
                "sectionId": s.sectionId,
                "path": s.path,
                "content": s.content,
            }
            for s in ai_result.sections
        ]
    sanitized = apply_ai_content(sanitized, ai_sections)

    # 4) Write processed JSON to temp file
    tmp_json = tempfile.NamedTemporaryFile(
        prefix="sim_",
        suffix=".json",
        delete=False,
        mode="w",
        encoding="utf-8",
    )
    json.dump(sanitized, tmp_json, ensure_ascii=False, indent=2)
    tmp_json.close()
    sanitized_path = Path(tmp_json.name)

    # 5) Generate via the standard pipeline with override JSON
    try:
        output_path, filename = formats_service.generate_document(
            format_id, override_json_path=sanitized_path
        )
    except Exception as e:
        cleanup_temp_json(sanitized_path)
        raise RuntimeError(f"Simulation generation failed: {e}")

    cleanup_temp_json(sanitized_path)

    # Adjust filename for simulation
    sim_filename = filename.replace(".docx", "_SIMULACION.docx")
    return output_path, sim_filename


@router.post("/docx")
def render_docx(request: RenderRequest, background_tasks: BackgroundTasks):
    """
    Generate DOCX using the REAL GicaTesis generator pipeline.

    Mode:
    - "simulation": Removes notes/guides, injects AI placeholders
    - "final": Uses original JSON as-is (same as GicaTesis UI)
    """
    _validate_publishable(request.formatId)

    try:
        if request.mode == "simulation":
            output_path, filename = _generate_simulation_docx(
                request.formatId,
                request.values,
                request.aiResult,
            )
        else:
            # Final mode: use existing pipeline unchanged
            output_path, filename = formats_service.generate_document(request.formatId)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Clean up temp file after response is sent
    background_tasks.add_task(cleanup_temp_file, output_path)

    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "X-Rendered-By": "gicatesis-real-generator",
            "X-Render-Mode": request.mode,
        },
    )


@router.post("/pdf")
def render_pdf(request: RenderRequest, background_tasks: BackgroundTasks):
    """
    Generate PDF using the REAL GicaTesis pipeline.

    Mode:
    - "simulation": First generates simulation DOCX, then converts to PDF
    - "final": Uses cached PDF pipeline (same as GicaTesis UI)
    """
    _validate_publishable(request.formatId)

    try:
        if request.mode == "simulation":
            # Generate simulation DOCX first
            docx_path, docx_filename = _generate_simulation_docx(
                request.formatId,
                request.values,
                request.aiResult,
            )

            if not docx_path.exists():
                raise RuntimeError("DOCX generation returned path but file is missing")


            # Convert to PDF using same Word COM pipeline
            from app.core.pdf_converter import convert_docx_to_pdf

            pdf_path = docx_path.with_suffix(".pdf")
            convert_docx_to_pdf(str(docx_path), str(pdf_path))

            if not pdf_path.exists():
                raise RuntimeError("PDF conversion finished but file is missing")

            # Cleanup DOCX
            background_tasks.add_task(cleanup_temp_file, docx_path)
            background_tasks.add_task(cleanup_temp_file, pdf_path)

            filename = docx_filename.replace(".docx", ".pdf")

            return FileResponse(
                path=str(pdf_path),
                filename=filename,
                media_type="application/pdf",
                headers={
                    "X-Rendered-By": "gicatesis-real-generator",
                    "X-Render-Mode": request.mode,
                },
            )
        else:
            # Final mode: use cached PDF pipeline
            source_mtime = _get_source_mtime(request.formatId)
            pdf_path, docx_path, docx_sha256 = _ensure_pdf_cached(request.formatId, source_mtime)

            item = find_format_index(request.formatId)
            filename = f"{request.formatId.replace('-', '_').upper()}.pdf"
            if item:
                filename = f"{item.uni.upper()}_{item.categoria.upper()}.pdf"

            return FileResponse(
                path=str(pdf_path),
                filename=filename,
                media_type="application/pdf",
                headers={
                    "X-Rendered-By": "gicatesis-real-generator",
                    "X-Render-Mode": request.mode,
                },
            )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {exc}",
        )
