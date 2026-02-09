"""
Generation Router - API endpoints for document generation.

POST /api/v1/generate - Generate DOCX/PDF from format + values
GET /api/v1/artifacts/{runId}/docx - Download generated DOCX
GET /api/v1/artifacts/{runId}/pdf - Download generated PDF
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.generation_service import generate_artifacts, get_artifact_path


router = APIRouter(prefix="/api/v1", tags=["generation"])


class AISection(BaseModel):
    """A section of AI-generated content."""
    path: str = Field(..., description="Section path like 'Resumen' or 'Capitulo I/Introduccion'")
    content: str = Field(..., description="AI-generated content for this section")


class AIResult(BaseModel):
    """AI generation result containing multiple sections."""
    sections: List[AISection] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    """Request to generate DOCX/PDF artifacts."""
    projectId: str = Field(..., min_length=1, description="Project identifier")
    formatId: str = Field(..., min_length=1, description="Format ID (must be publishable)")
    formatVersion: Optional[str] = Field(default=None, description="Optional format version hash")
    mode: str = Field(default="simulation", description="Generation mode: simulation or production")
    values: Dict[str, Any] = Field(default_factory=dict, description="User values for placeholders")
    aiResult: Optional[AIResult] = Field(default=None, description="AI-generated content sections")


class ArtifactResponse(BaseModel):
    """Info about a generated artifact."""
    type: str
    downloadUrl: str


class GenerateResponse(BaseModel):
    """Response from generation endpoint."""
    projectId: str
    runId: str
    status: str
    artifacts: List[ArtifactResponse] = Field(default_factory=list)
    error: Optional[str] = None


@router.post("/generate", response_model=GenerateResponse)
async def generate_document(request: GenerateRequest):
    """
    Generate DOCX and PDF documents using real GicaTesis generators.
    
    The format must be publishable (not a config/reference).
    aiResult sections will be applied to matching document sections.
    If no aiResult is provided, simulation placeholders are inserted.
    
    Instruction/guidance keys (nota, instruccion, guia, etc.) are excluded from output.
    """
    ai_result_dict = None
    if request.aiResult:
        ai_result_dict = {
            "sections": [
                {"path": s.path, "content": s.content}
                for s in request.aiResult.sections
            ]
        }
    
    result = generate_artifacts(
        project_id=request.projectId,
        format_id=request.formatId,
        values=request.values,
        ai_result=ai_result_dict,
        mode=request.mode,
    )
    
    if result.status == "error":
        if "not found" in (result.error or "").lower():
            raise HTTPException(status_code=404, detail=result.error)
        if "not publishable" in (result.error or "").lower():
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=500, detail=result.error or "Generation failed")
    
    return GenerateResponse(
        projectId=result.project_id,
        runId=result.run_id,
        status=result.status,
        artifacts=[
            ArtifactResponse(type=a.type, downloadUrl=a.download_url)
            for a in result.artifacts
        ],
    )


@router.get("/artifacts/{run_id}/docx")
async def download_docx(run_id: str):
    """Download generated DOCX artifact by run ID."""
    path = get_artifact_path(run_id, "docx")
    if not path:
        raise HTTPException(status_code=404, detail="Artifact not found or expired")
    
    return FileResponse(
        path=str(path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=path.name,
    )


@router.get("/artifacts/{run_id}/pdf")
async def download_pdf(run_id: str):
    """Download generated PDF artifact by run ID."""
    path = get_artifact_path(run_id, "pdf")
    if not path:
        raise HTTPException(status_code=404, detail="Artifact not found or expired")
    
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=path.name,
    )
