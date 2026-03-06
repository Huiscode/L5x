from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import combinations
from xml.etree import ElementTree as ET

from app.models import RelationshipEdge

TAG_TOKEN_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\b")
INSTRUCTION_RE = re.compile(r"\b([A-Z][A-Z0-9_]*)\(([^)]*)\)")

READ_INSTRUCTIONS = {"XIC", "XIO", "EQU", "NEQ", "LES", "GRT", "LEQ", "GEQ", "ADD", "SUB", "MUL", "DIV"}
WRITE_INSTRUCTIONS = {"OTE", "OTL", "OTU", "MOV", "COP", "CPT"}
IGNORE_TOKENS = {
    "IF",
    "THEN",
    "AND",
    "OR",
    "NOT",
    "TRUE",
    "FALSE",
    "JSR",
    "AFI",
    "TON",
    "TOF",
    "RTO",
}


@dataclass(slots=True)
class _RungContext:
    program: str
    routine: str
    rung_ref: str
    text: str


def extract_relationship_edges(root: ET.Element) -> list[RelationshipEdge]:
    edges: list[RelationshipEdge] = []

    program_names = {
        program.attrib.get("Name")
        for program in root.findall(".//Program")
        if program.attrib.get("Name")
    }
    aoi_types = {
        definition.attrib.get("Name")
        for definition in root.findall(".//AddOnInstructionDefinition")
        if definition.attrib.get("Name")
    }

    tag_type_lookup = _build_tag_type_lookup(root)

    for ctx in _collect_rungs(root):
        tokens = _extract_tag_tokens(ctx.text)
        unique_tokens = sorted(set(tokens))

        for tag in unique_tokens:
            edges.append(
                RelationshipEdge(
                    source_tag=tag,
                    target_tag=tag,
                    relation_type="read_usage",
                    program=ctx.program,
                    routine=ctx.routine,
                    rung_ref=ctx.rung_ref,
                    evidence_excerpt=ctx.text[:220],
                )
            )

        for source, target in combinations(unique_tokens, 2):
            edges.append(
                RelationshipEdge(
                    source_tag=source,
                    target_tag=target,
                    relation_type="same_rung_cooccurrence",
                    program=ctx.program,
                    routine=ctx.routine,
                    rung_ref=ctx.rung_ref,
                    evidence_excerpt=ctx.text[:220],
                )
            )

        instruction_ops = list(INSTRUCTION_RE.finditer(ctx.text))
        for op in instruction_ops:
            opcode = op.group(1)
            args = [arg.strip() for arg in op.group(2).split(",") if arg.strip()]
            arg_tags = [token for arg in args for token in _extract_tag_tokens(arg)]
            if not arg_tags:
                continue

            if opcode in WRITE_INSTRUCTIONS:
                write_tag = arg_tags[-1]
                edges.append(
                    RelationshipEdge(
                        source_tag=write_tag,
                        target_tag=write_tag,
                        relation_type="write_usage",
                        program=ctx.program,
                        routine=ctx.routine,
                        rung_ref=ctx.rung_ref,
                        evidence_excerpt=ctx.text[:220],
                    )
                )
            elif opcode in READ_INSTRUCTIONS:
                for read_tag in arg_tags:
                    edges.append(
                        RelationshipEdge(
                            source_tag=read_tag,
                            target_tag=read_tag,
                            relation_type="read_usage",
                            program=ctx.program,
                            routine=ctx.routine,
                            rung_ref=ctx.rung_ref,
                            evidence_excerpt=ctx.text[:220],
                        )
                    )

        for token in unique_tokens:
            if "." not in token:
                continue

            root_symbol = token.split(".", maxsplit=1)[0]
            if root_symbol in program_names and root_symbol != ctx.program:
                edges.append(
                    RelationshipEdge(
                        source_tag=token,
                        target_tag=root_symbol,
                        relation_type="cross_program_reference",
                        program=ctx.program,
                        routine=ctx.routine,
                        rung_ref=ctx.rung_ref,
                        evidence_excerpt=ctx.text[:220],
                    )
                )

            tag_type = tag_type_lookup.get(root_symbol)
            if tag_type and tag_type in aoi_types:
                edges.append(
                    RelationshipEdge(
                        source_tag=root_symbol,
                        target_tag=token,
                        relation_type="aoi_io_binding",
                        program=ctx.program,
                        routine=ctx.routine,
                        rung_ref=ctx.rung_ref,
                        evidence_excerpt=ctx.text[:220],
                    )
                )

    for tag in root.findall(".//Tag"):
        alias_name = tag.attrib.get("Name")
        alias_for = tag.attrib.get("AliasFor")
        if alias_name and alias_for:
            edges.append(
                RelationshipEdge(
                    source_tag=alias_name,
                    target_tag=alias_for,
                    relation_type="alias_base_mapping",
                    program=None,
                    routine=None,
                    rung_ref=None,
                    evidence_excerpt=None,
                )
            )

    return _dedupe_edges(edges)


def _build_tag_type_lookup(root: ET.Element) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for tag in root.findall(".//Tag"):
        name = tag.attrib.get("Name")
        data_type = tag.attrib.get("DataType")
        if name and data_type:
            lookup[name] = data_type
    return lookup


def _collect_rungs(root: ET.Element) -> list[_RungContext]:
    contexts: list[_RungContext] = []

    for program in root.findall(".//Program"):
        program_name = program.attrib.get("Name", "<unknown_program>")
        for routine in program.findall(".//Routine"):
            routine_name = routine.attrib.get("Name", "<unknown_routine>")
            for rung in routine.findall(".//Rung"):
                rung_number = rung.attrib.get("Number", "?")
                text_elem = rung.find("Text")
                text = (text_elem.text or "").strip() if text_elem is not None else ""
                if not text:
                    continue
                contexts.append(
                    _RungContext(
                        program=program_name,
                        routine=routine_name,
                        rung_ref=f"Rung[{rung_number}]",
                        text=text,
                    )
                )

    return contexts


def _extract_tag_tokens(text: str) -> list[str]:
    tokens = TAG_TOKEN_RE.findall(text)
    normalized: list[str] = []
    for token in tokens:
        upper = token.upper()
        if upper in IGNORE_TOKENS:
            continue
        if token.isdigit():
            continue
        normalized.append(token)
    return normalized


def _dedupe_edges(edges: list[RelationshipEdge]) -> list[RelationshipEdge]:
    deduped: dict[tuple[str, str, str, str | None, str | None, str | None], RelationshipEdge] = {}
    for edge in edges:
        key = (
            edge.source_tag,
            edge.target_tag,
            edge.relation_type,
            edge.program,
            edge.routine,
            edge.rung_ref,
        )
        deduped[key] = edge
    return list(deduped.values())
