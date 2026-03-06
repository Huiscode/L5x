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


class ParseL5xResponse(BaseModel):
    summary: ParseSummary
    nodes: list[TreeNode]
    issues: list[ValidationIssue]
    can_export: bool
