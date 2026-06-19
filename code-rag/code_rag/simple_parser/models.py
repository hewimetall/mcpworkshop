"""Language-independent data types for code RAG ingest."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass
class CodeUnit:
    qualified_name: str
    module: str
    language: str
    role: str
    symbol: str
    class_chain: list[str]
    path: str
    start_line: int
    end_line: int
    content: str
    calls: list[str]
    embed_text: str
    namespace: str
    doc: str = ""
    package: str | None = None

    @property
    def id(self) -> str:
        return f"{self.path}::{self.qualified_name}"

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "qualified_name": self.qualified_name,
            "module": self.module,
            "language": self.language,
            "role": self.role,
            "symbol": self.symbol,
            "class_chain": self.class_chain,
            "path": self.path,
            "package": self.package,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "calls": self.calls,
            "embed_text": self.embed_text,
            "namespace": self.namespace,
            "doc": self.doc,
        }


@dataclass
class UnitRefs:
    unit_id: str
    qualified_name: str
    path: str
    language: str
    refs: dict[str, str]

    def as_dict(self) -> dict:
        return {
            "unit_id": self.unit_id,
            "qualified_name": self.qualified_name,
            "path": self.path,
            "language": self.language,
            "refs": self.refs,
        }


@dataclass
class Chunk(CodeUnit):
    search_text: str = ""
    content_hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]

    @classmethod
    def from_unit(cls, unit: CodeUnit, search_text: str = "") -> Chunk:
        return cls(
            qualified_name=unit.qualified_name,
            module=unit.module,
            language=unit.language,
            role=unit.role,
            symbol=unit.symbol,
            class_chain=unit.class_chain,
            path=unit.path,
            start_line=unit.start_line,
            end_line=unit.end_line,
            content=unit.content,
            calls=unit.calls,
            embed_text=unit.embed_text,
            namespace=unit.namespace,
            doc=unit.doc,
            package=unit.package,
            search_text=search_text,
        )


def chunk_as_dict(chunk: Chunk) -> dict:
    row = chunk.as_dict()
    row["search_text"] = chunk.search_text
    row["content_hash"] = chunk.content_hash
    return row


def chunk_from_dict(row: dict) -> Chunk:
    return Chunk(
        qualified_name=row["qualified_name"],
        module=row["module"],
        language=row["language"],
        role=row["role"],
        symbol=row["symbol"],
        class_chain=row.get("class_chain") or [],
        path=row["path"],
        start_line=row["start_line"],
        end_line=row["end_line"],
        content=row["content"],
        calls=row.get("calls") or [],
        embed_text=row.get("embed_text", ""),
        namespace=row["namespace"],
        doc=row.get("doc", ""),
        package=row.get("package"),
        search_text=row.get("search_text", ""),
    )
