from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

from app.models import ParseSummary, TreeNode, ValidationIssue

SUPPORTED_MIN_REVISION = 32
SUPPORTED_MAX_REVISION = 36


@dataclass(slots=True)
class ParseResult:
    summary: ParseSummary
    nodes: list[TreeNode]
    issues: list[ValidationIssue]
    root: ET.Element


class L5xParseError(Exception):
    pass


def parse_l5x_bytes(file_bytes: bytes, filename: str) -> ParseResult:
    issues: list[ValidationIssue] = []
    if not file_bytes:
        raise L5xParseError("Uploaded file is empty.")

    try:
        root = ET.fromstring(file_bytes)
    except ET.ParseError as exc:
        raise L5xParseError(f"Invalid XML: {exc}") from exc

    if root.tag != "RSLogix5000Content":
        raise L5xParseError("Root element must be RSLogix5000Content.")

    software_revision = root.attrib.get("SoftwareRevision")
    major_revision = _extract_major_revision(software_revision)

    if major_revision is None:
        issues.append(
            ValidationIssue(
                code="REVISION_UNKNOWN",
                severity="warning",
                message="SoftwareRevision is missing or could not be parsed.",
                path="/RSLogix5000Content/@SoftwareRevision",
            )
        )
    elif not (SUPPORTED_MIN_REVISION <= major_revision <= SUPPORTED_MAX_REVISION):
        issues.append(
            ValidationIssue(
                code="REVISION_OUT_OF_TARGET",
                severity="warning",
                message=(
                    f"SoftwareRevision major version {major_revision} is outside "
                    f"target v{SUPPORTED_MIN_REVISION}-v{SUPPORTED_MAX_REVISION}."
                ),
                path="/RSLogix5000Content/@SoftwareRevision",
                details={"detected_major_revision": major_revision},
            )
        )

    controller_element = root.find("Controller")
    project_name = root.attrib.get("TargetName") or filename
    controller_name = controller_element.attrib.get("Name") if controller_element is not None else None

    if controller_element is None:
        issues.append(
            ValidationIssue(
                code="CONTROLLER_MISSING",
                severity="error",
                message="Controller element is missing.",
                path="/RSLogix5000Content/Controller",
            )
        )

    tree_nodes = _build_normalized_nodes(root)
    issues.extend(_run_integrity_checks(root))

    summary = ParseSummary(
        software_revision=software_revision,
        major_revision=major_revision,
        project_name=project_name,
        controller_name=controller_name,
        file_size_bytes=len(file_bytes),
    )

    return ParseResult(summary=summary, nodes=tree_nodes, issues=issues, root=root)


def _extract_major_revision(software_revision: str | None) -> int | None:
    if not software_revision:
        return None

    first = software_revision.split(".", maxsplit=1)[0].strip()
    if not first.isdigit():
        return None

    return int(first)


def _build_normalized_nodes(root: ET.Element) -> list[TreeNode]:
    top_nodes: list[TreeNode] = []

    for child in root:
        top_nodes.append(_element_to_node(child, parent_path=PurePosixPath("/RSLogix5000Content")))

    return top_nodes


def _element_to_node(element: ET.Element, parent_path: PurePosixPath) -> TreeNode:
    tag = _strip_namespace(element.tag)
    node_name = element.attrib.get("Name") or tag
    node_path = parent_path / _safe_path_segment(tag, node_name)

    attrs: dict[str, Any] = {
        "tag": tag,
        "text_preview": _preview_text(element.text),
        "attrib": dict(element.attrib),
    }

    children = [_element_to_node(child, node_path) for child in element]

    node_type = _infer_node_type(tag, element.attrib)
    return TreeNode(
        id=str(node_path),
        name=node_name,
        type=node_type,
        path=str(node_path),
        attributes=attrs,
        children=children,
    )


def _strip_namespace(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", maxsplit=1)[1]
    return tag


def _safe_path_segment(tag: str, name: str) -> str:
    safe_name = name.replace("/", "_").replace("\\", "_")
    return f"{tag}[{safe_name}]"


def _infer_node_type(tag: str, attrib: dict[str, str]) -> str:
    if tag == "Tag":
        return "tag"
    if tag == "Program":
        return "program"
    if tag == "Routine":
        return "routine"
    if tag == "Rung":
        return "rung"
    if tag == "AddOnInstructionDefinition":
        return "aoi"
    if tag == "DataType":
        return "udt"
    if "Use" in attrib and tag == "Tags":
        return "tag_collection"
    return tag.lower()


def _preview_text(value: str | None) -> str | None:
    if value is None:
        return None
    compact = " ".join(value.split())
    if not compact:
        return None
    return compact[:200]


def _run_integrity_checks(root: ET.Element) -> Iterable[ValidationIssue]:
    issues: list[ValidationIssue] = []

    _check_required_sections(root, issues)
    _check_duplicate_named_elements(root, "Tag", issues)
    _check_duplicate_named_elements(root, "Program", issues)

    return issues


def _check_required_sections(root: ET.Element, issues: list[ValidationIssue]) -> None:
    controller = root.find("Controller")
    if controller is None:
        return

    for section in ("Tags", "Programs"):
        if controller.find(section) is None:
            issues.append(
                ValidationIssue(
                    code="SECTION_MISSING",
                    severity="warning",
                    message=f"Controller/{section} section is missing.",
                    path=f"/RSLogix5000Content/Controller/{section}",
                )
            )


def _check_duplicate_named_elements(root: ET.Element, element_name: str, issues: list[ValidationIssue]) -> None:
    counts: dict[str, int] = {}
    for elem in root.iter(element_name):
        name = elem.attrib.get("Name")
        if not name:
            continue
        counts[name] = counts.get(name, 0) + 1

    duplicates = {name: count for name, count in counts.items() if count > 1}
    for name, count in duplicates.items():
        issues.append(
            ValidationIssue(
                code="DUPLICATE_NAME",
                severity="warning",
                message=f"Found duplicate {element_name} name '{name}' ({count} occurrences).",
                path=f"//{element_name}[@Name='{name}']",
                details={"count": count, "element": element_name},
            )
        )
