from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["error", "warning", "info"]


class ValidationIssue(BaseModel):
    code: str
    severity: Severity
    message: str
    path: str | None = None
    details: dict[str, Any] | None = None


class ParseSummary(BaseModel):
    software_revision: str | None = None
    major_revision: int | None = None
    project_name: str | None = None
    controller_name: str | None = None
    file_size_bytes: int = 0


class TreeNode(BaseModel):
    id: str
    name: str
    type: str
    path: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    children: list["TreeNode"] = Field(default_factory=list)


class EditableField(BaseModel):
    target_path: str
    field_type: str
    locale: str | None = None
    original_value: str
    updated_value: str
    validation_state: Literal["valid", "warning", "error"] = "valid"


class ParseL5xResponse(BaseModel):
    session_id: str
    summary: ParseSummary
    nodes: list[TreeNode]
    issues: list[ValidationIssue]
    editable_fields: list[EditableField]
    can_export: bool


class UpdateEditableFieldRequest(BaseModel):
    target_path: str
    updated_value: str


class DiffItem(BaseModel):
    target_path: str
    field_type: str
    old_value: str
    new_value: str


class DiffPreviewResponse(BaseModel):
    session_id: str
    total_changes: int
    items: list[DiffItem]


class ExportPrecheckResponse(BaseModel):
    session_id: str
    can_export: bool
    issues: list[ValidationIssue]
    total_changes: int


class UpdateFieldResponse(BaseModel):
    session_id: str
    field: EditableField
    diff: DiffPreviewResponse


RelationshipType = Literal[
    "read_usage",
    "write_usage",
    "same_rung_cooccurrence",
    "cross_program_reference",
    "alias_base_mapping",
    "aoi_io_binding",
]


class RelationshipEdge(BaseModel):
    source_tag: str
    target_tag: str
    relation_type: RelationshipType
    program: str | None = None
    routine: str | None = None
    rung_ref: str | None = None
    evidence_excerpt: str | None = None


class RelationshipGraphResponse(BaseModel):
    session_id: str
    edges: list[RelationshipEdge]
