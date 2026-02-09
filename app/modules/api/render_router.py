"""
Render Router - API endpoints for document rendering using real generators.

These endpoints call the EXACT same pipeline as GicaTesis UI downloads:
- DOCX: formats/service.py:generate_document (external generator scripts)
- PDF: Word COM conversion via pdf_converter.py

POST /api/v1/render/docx - Generate DOCX using real generator
POST /api/v1/render/pdf - Generate PDF using real generator + Word COM

Simulation Mode:
- mode="simulation": Sanitizes JSON (removes notas/guias) and injects AI placeholders
- mode="final": Uses original JSON as-is (default GicaTesis behavior)
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from app.modules.formats import service as formats_service
from app.modules.formats.router import _ensure_pdf_cached, _get_source_mtime
from app.core.loaders import find_format_index
from app.universities.registry import get_provider
from app.core.simulation_preprocessor import (
    build_section_index,
    cleanup_temp_json,
    postprocess_simulation_docx,
    sanitize_definition,
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


def _resolve_generator_command(generator, json_path: Path, output_path: Path) -> Tuple[list, Optional[Path]]:
    """Resolve generator to command and working directory."""
    if isinstance(generator, Path):
        return ["python", str(generator), str(json_path), str(output_path)], generator.parent
    elif isinstance(generator, str):
        gen_path = Path(generator)
        return ["python", str(gen_path), str(json_path), str(output_path)], gen_path.parent if gen_path.is_file() else None
    else:
        # GeneratorCommand tuple (cmd, workdir)
        cmd = generator[0] if isinstance(generator, tuple) else generator
        workdir = generator[1] if isinstance(generator, tuple) and len(generator) > 1 else None
        return [str(cmd), str(json_path), str(output_path)], workdir


def _generate_simulation_docx(
    format_id: str,
    values: Dict[str, Any],
    ai_result: Optional[AIResult],
) -> Tuple[Path, str]:
    """
    Generate DOCX in simulation mode:
    1. Load original format JSON
    2. Sanitize (remove notes/guides)
    3. Inject AI placeholders
    4. Call same generator with sanitized JSON
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
    
    # 1) Sanitize definition: always remove notes/guides keys in simulation.
    sanitized = sanitize_definition(format_data)

    # 2) Build section index from sanitized definition (ordered, path/sectionId).
    section_index = build_section_index(sanitized)
    
    # Merge user values into caratula
    if values and "caratula" in sanitized:
        for key, val in values.items():
            sanitized["caratula"][key] = val
    
    # 3) Write sanitized JSON to temp file for the real generator pipeline.
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
    
    # 4) Resolve generator
    provider = get_provider(item.uni)
    generator = provider.get_generator_command(item.categoria)
    
    # 5) Create output file
    filename = f"{provider.code.upper()}_{item.categoria.upper()}_SIMULACION.docx"
    tmp_docx = tempfile.NamedTemporaryFile(prefix="sim_", suffix=".docx", delete=False)
    output_path = Path(tmp_docx.name)
    tmp_docx.close()
    
    # 6) Execute real generator with sanitized JSON
    cmd, workdir = _resolve_generator_command(generator, sanitized_path, output_path)
    result = subprocess.run(cmd, cwd=str(workdir) if workdir else None, capture_output=True, text=True)
    
    cleanup_temp_json(sanitized_path)
    
    if result.returncode != 0:
        print(f"[SIMULATION ERROR] {result.stderr}")
        raise RuntimeError("Simulation document generation failed.")
    
    if not output_path.exists():
        raise RuntimeError("Generator script executed but did not create DOCX file.")

    # 7) Post-process simulation DOCX:
    #    - insert aiResult content under each heading (path/sectionId mapping)
    #    - remove fixed guide paragraphs from template output.
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
    postprocess_simulation_docx(output_path, section_index=section_index, ai_sections=ai_sections)

    return output_path, filename


@router.post("/docx")
async def render_docx(request: RenderRequest, background_tasks: BackgroundTasks):
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
    background_tasks.add_task(formats_service.cleanup_temp_file, output_path)
    
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
async def render_pdf(request: RenderRequest, background_tasks: BackgroundTasks):
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
            
            # Convert to PDF using same Word COM pipeline
            from app.core.pdf_converter import convert_docx_to_pdf
            
            pdf_path = docx_path.with_suffix(".pdf")
            # Word COM expects filesystem paths as str, not pathlib.Path.
            convert_docx_to_pdf(str(docx_path), str(pdf_path))
            
            # Cleanup DOCX
            background_tasks.add_task(formats_service.cleanup_temp_file, docx_path)
            background_tasks.add_task(formats_service.cleanup_temp_file, pdf_path)
            
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
