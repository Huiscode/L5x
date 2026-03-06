from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from uuid import uuid4
from xml.etree import ElementTree as ET

from app.models import (
    DiffItem,
    DiffPreviewResponse,
    EditableField,
    ExportPrecheckResponse,
    ParseSummary,
    RelationshipEdge,
    TreeNode,
    ValidationIssue,
)
from app.services.l5x_relationships import extract_relationship_edges
from app.services.l5x_parser import _build_normalized_nodes, _extract_major_revision, _run_integrity_checks

SUPPORTED_FIELD_TAGS = {"Description", "Comment", "LocalizedDescription"}


class SessionNotFoundError(Exception):
    pass


class EditableFieldNotFoundError(Exception):
    pass


@dataclass(slots=True)
class L5xSession:
    session_id: str
    filename: str
    root: ET.Element
    summary: ParseSummary
    nodes: list[TreeNode]
    issues: list[ValidationIssue]
    editable_fields: list[EditableField]
    relationships: list[RelationshipEdge]


class L5xSessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, L5xSession] = {}
        self._lock = Lock()

    def create_session(self, *, filename: str, root: ET.Element, issues: list[ValidationIssue]) -> L5xSession:
        summary = _build_summary(root=root, filename=filename)
        nodes = _build_normalized_nodes(root)
        editable_fields = _extract_editable_fields(root)
        relationships = extract_relationship_edges(root)
        session_id = uuid4().hex
        session = L5xSession(
            session_id=session_id,
            filename=filename,
            root=root,
            summary=summary,
            nodes=nodes,
            issues=issues,
            editable_fields=editable_fields,
            relationships=relationships,
        )

        with self._lock:
            self._sessions[session_id] = session

        return session

    def get_session(self, session_id: str) -> L5xSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' was not found.")
        return session

    def update_field(self, *, session_id: str, target_path: str, updated_value: str) -> L5xSession:
        session = self.get_session(session_id)
        field = next((f for f in session.editable_fields if f.target_path == target_path), None)
        if field is None:
            raise EditableFieldNotFoundError(f"Editable field '{target_path}' was not found.")

        element = _find_element_by_target_path(session.root, target_path)
        if element is None:
            raise EditableFieldNotFoundError(f"XML element for '{target_path}' was not found.")

        field.updated_value = updated_value
        field.validation_state = _validate_text(updated_value)
        element.text = updated_value

        session.nodes = _build_normalized_nodes(session.root)
        session.issues = list(_run_integrity_checks(session.root))
        session.relationships = extract_relationship_edges(session.root)
        return session

    def build_diff(self, session_id: str) -> DiffPreviewResponse:
        session = self.get_session(session_id)
        items = [
            DiffItem(
                target_path=field.target_path,
                field_type=field.field_type,
                old_value=field.original_value,
                new_value=field.updated_value,
            )
            for field in session.editable_fields
            if field.updated_value != field.original_value
        ]

        return DiffPreviewResponse(session_id=session.session_id, total_changes=len(items), items=items)

    def build_export_precheck(self, session_id: str) -> ExportPrecheckResponse:
        session = self.get_session(session_id)
        issues = list(_run_integrity_checks(session.root))
        can_export = not any(issue.severity == "error" for issue in issues)
        diff = self.build_diff(session_id)
        return ExportPrecheckResponse(
            session_id=session.session_id,
            can_export=can_export,
            issues=issues,
            total_changes=diff.total_changes,
        )

    def get_relationships(self, session_id: str) -> list[RelationshipEdge]:
        session = self.get_session(session_id)
        return session.relationships

    def export_xml(self, session_id: str) -> bytes:
        session = self.get_session(session_id)
        precheck = self.build_export_precheck(session_id)
        if not precheck.can_export:
            raise ValueError("Export blocked by integrity pre-check errors.")
        return ET.tostring(session.root, encoding="utf-8", xml_declaration=True)


def _build_summary(*, root: ET.Element, filename: str) -> ParseSummary:
    controller = root.find("Controller")
    software_revision = root.attrib.get("SoftwareRevision")
    major_revision = _extract_major_revision(software_revision)
    return ParseSummary(
        software_revision=software_revision,
        major_revision=major_revision,
        project_name=root.attrib.get("TargetName") or filename,
        controller_name=controller.attrib.get("Name") if controller is not None else None,
        file_size_bytes=0,
    )


def _extract_editable_fields(root: ET.Element) -> list[EditableField]:
    fields: list[EditableField] = []
    counters: dict[str, int] = {}

    def walk(element: ET.Element, path_parts: list[str]) -> None:
        tag = _strip_namespace(element.tag)
        name = element.attrib.get("Name")

        if name:
            key = f"{tag}:{name}"
            index = counters.get(key, 0)
            counters[key] = index + 1
            segment = f"{tag}[Name={name}#{index}]"
        else:
            segment = tag

        current = [*path_parts, segment]

        if tag in SUPPORTED_FIELD_TAGS:
            target_path = "/" + "/".join(current)
            value = element.text or ""
            fields.append(
                EditableField(
                    target_path=target_path,
                    field_type=tag.lower(),
                    locale=element.attrib.get("Lang") or element.attrib.get("Language"),
                    original_value=value,
                    updated_value=value,
                    validation_state=_validate_text(value),
                )
            )

        for child in element:
            walk(child, current)

    walk(root, [])
    return fields


def _validate_text(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return "warning"
    if len(stripped) > 4000:
        return "error"
    return "valid"


def _find_element_by_target_path(root: ET.Element, target_path: str) -> ET.Element | None:
    if not target_path.startswith("/"):
        return None

    parts = [p for p in target_path.split("/") if p]
    if not parts:
        return None

    current = root
    if _strip_namespace(current.tag) != _segment_tag(parts[0]):
        return None

    for segment in parts[1:]:
        tag, name, occurrence = _parse_segment(segment)
        matches: list[ET.Element] = []
        for child in current:
            child_tag = _strip_namespace(child.tag)
            if child_tag != tag:
                continue
            if name is not None and child.attrib.get("Name") != name:
                continue
            matches.append(child)

        if occurrence >= len(matches):
            return None

        current = matches[occurrence]

    return current


def _segment_tag(segment: str) -> str:
    if "[" not in segment:
        return segment
    return segment.split("[", maxsplit=1)[0]


def _parse_segment(segment: str) -> tuple[str, str | None, int]:
    if "[" not in segment or not segment.endswith("]"):
        return segment, None, 0

    tag = segment.split("[", maxsplit=1)[0]
    inner = segment[len(tag) + 1 : -1]

    if inner.startswith("Name=") and "#" in inner:
        name_part, index_part = inner.split("#", maxsplit=1)
        name = name_part.replace("Name=", "", 1)
        if index_part.isdigit():
            return tag, name, int(index_part)
        return tag, name, 0

    return tag, None, 0


def _strip_namespace(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", maxsplit=1)[1]
    return tag


session_store = L5xSessionStore()
