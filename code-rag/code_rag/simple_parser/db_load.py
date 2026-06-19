"""Load chunks.jsonl and refs.jsonl produced by gen-embedding."""

from __future__ import annotations

import json
from pathlib import Path

from code_rag.simple_parser.models import Chunk, UnitRefs, chunk_from_dict


def load_chunks(path: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(chunk_from_dict(json.loads(line)))
    return chunks


def load_refs(path: Path) -> dict[str, UnitRefs]:
    refs_by_id: dict[str, UnitRefs] = {}
    if not path.is_file():
        return refs_by_id
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            ref = UnitRefs(
                unit_id=row["unit_id"],
                qualified_name=row["qualified_name"],
                path=row["path"],
                language=row["language"],
                refs=row.get("refs") or {},
            )
            refs_by_id[ref.unit_id] = ref
    return refs_by_id
