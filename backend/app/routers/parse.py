from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models import ParseL5xResponse
from app.services.l5x_parser import L5xParseError, parse_l5x_bytes

router = APIRouter(prefix="/api/l5x", tags=["l5x"])


@router.post("/parse", response_model=ParseL5xResponse)
async def parse_l5x(file: UploadFile = File(...)) -> ParseL5xResponse:
    if not file.filename or not file.filename.lower().endswith(".l5x"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .L5X files are supported.",
        )

    payload = await file.read()

    try:
        result = parse_l5x_bytes(payload, filename=file.filename)
    except L5xParseError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    can_export = not any(issue.severity == "error" for issue in result.issues)

    return ParseL5xResponse(
        summary=result.summary,
        nodes=result.nodes,
        issues=result.issues,
        can_export=can_export,
    )
