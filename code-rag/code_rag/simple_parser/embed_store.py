"""Merge unit embed_text with refs; optional vectorization hook."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from code_rag.simple_parser.models import CodeUnit, UnitRefs

_SKIP_REF_KEYS = frozenset({"mro_source"})


def final_embed_text(unit: CodeUnit, refs: UnitRefs | None) -> str:
    lines = [unit.embed_text]
    if refs:
        for key, val in refs.refs.items():
            if key in _SKIP_REF_KEYS:
                continue
            lines.append(f"ref: {key} | {val}")
    return "\n".join(lines)


def build_call_text(unit: CodeUnit) -> str:
    """Embed lane for call patterns."""
    calls_str = ", ".join(unit.calls[:15]) if unit.calls else "none"
    chain = ".".join(unit.class_chain) if unit.class_chain else ""
    ctx = f"in {chain}" if chain else f"module {unit.module}"
    return (
        f"caller `{unit.symbol}` ({unit.qualified_name}) {ctx} | "
        f"calls: {calls_str}"
    )


def build_class_text(unit: CodeUnit, refs: UnitRefs | None) -> str:
    """Embed lane for class / inheritance context."""
    lines: list[str] = []
    if unit.class_chain:
        lines.append(f"class: {'.'.join(unit.class_chain)}")
    else:
        lines.append(f"module: {unit.module}")
    if refs:
        for key, val in refs.refs.items():
            if key in _SKIP_REF_KEYS:
                continue
            if key in ("mro", "metaclass"):
                lines.append(f"{key}: {val}")
    if not lines:
        lines.append(f"symbol: {unit.symbol}")
    return "\n".join(lines)


def merge_refs_by_id(refs: list[UnitRefs]) -> dict[str, UnitRefs]:
    return {r.unit_id: r for r in refs}


def write_ingest_manifest(
    path: Path,
    *,
    job_id: str,
    file_hashes: dict[str, str],
) -> None:
    path.write_text(
        json.dumps({"job_id": job_id, "files": file_hashes}, indent=2),
        encoding="utf-8",
    )


def file_content_hash(source: bytes) -> str:
    return hashlib.sha256(source).hexdigest()[:16]


class EmbedStore:
    """Prepare texts for RuVector SQL embed on INSERT."""

    def __init__(self, refs_by_id: dict[str, UnitRefs] | None = None) -> None:
        self.refs_by_id = refs_by_id or {}

    def embed_text_for(self, unit: CodeUnit) -> str:
        return final_embed_text(unit, self.refs_by_id.get(unit.id))

    def texts_for_row(self, unit: CodeUnit) -> dict[str, str]:
        refs = self.refs_by_id.get(unit.id)
        return {
            "embed_func_text": final_embed_text(unit, refs),
            "embed_call_text": build_call_text(unit),
            "embed_class_text": build_class_text(unit, refs),
        }

    def prepare_batch(self, units: list[CodeUnit]) -> list[dict]:
        rows = []
        for u in units:
            rows.append(
                {
                    "id": u.id,
                    "qualified_name": u.qualified_name,
                    "embed_text": self.embed_text_for(u),
                    "content": u.content,
                    "namespace": u.namespace,
                }
            )
        return rows
