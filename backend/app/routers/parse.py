from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.models import (
    DiffPreviewResponse,
    ExportPrecheckResponse,
    ParseL5xResponse,
    RelationshipGraphResponse,
    UpdateEditableFieldRequest,
    UpdateFieldResponse,
)
from app.services.l5x_editor import (
    EditableFieldNotFoundError,
    SessionNotFoundError,
    session_store,
)
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
        parsed = parse_l5x_bytes(payload, filename=file.filename)
    except L5xParseError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    session = session_store.create_session(
        filename=file.filename,
        root=parsed.root,
        issues=parsed.issues,
    )

    can_export = not any(issue.severity == "error" for issue in session.issues)

    return ParseL5xResponse(
        session_id=session.session_id,
        summary=session.summary,
        nodes=session.nodes,
        issues=session.issues,
        editable_fields=session.editable_fields,
        can_export=can_export,
    )


@router.get("/{session_id}/diff", response_model=DiffPreviewResponse)
def get_diff_preview(session_id: str) -> DiffPreviewResponse:
    try:
        return session_store.build_diff(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{session_id}/fields", response_model=UpdateFieldResponse)
def update_editable_field(session_id: str, request: UpdateEditableFieldRequest) -> UpdateFieldResponse:
    try:
        session = session_store.update_field(
            session_id=session_id,
            target_path=request.target_path,
            updated_value=request.updated_value,
        )
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EditableFieldNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    updated = next(field for field in session.editable_fields if field.target_path == request.target_path)
    return UpdateFieldResponse(session_id=session_id, field=updated, diff=session_store.build_diff(session_id))


@router.get("/{session_id}/precheck", response_model=ExportPrecheckResponse)
def get_export_precheck(session_id: str) -> ExportPrecheckResponse:
    try:
        return session_store.build_export_precheck(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{session_id}/relationships", response_model=RelationshipGraphResponse)
def get_relationships(session_id: str) -> RelationshipGraphResponse:
    try:
        edges = session_store.get_relationships(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return RelationshipGraphResponse(session_id=session_id, edges=edges)


@router.get("/{session_id}/export")
def export_l5x(session_id: str) -> Response:
    try:
        xml_bytes = session_store.export_xml(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return Response(
        content=xml_bytes,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{session_id}.L5X"'},
    )
