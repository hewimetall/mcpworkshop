"""Ref visitor registry by file extension."""

from __future__ import annotations

from pathlib import Path

from code_rag.simple_parser.langs.python_ref import PythonRefVisitor
from code_rag.simple_parser.langs.ref_base import LanguageRefVisitor

_REF_VISITORS: list[LanguageRefVisitor] = [
    PythonRefVisitor(),
]

REFS_BY_EXT: dict[str, LanguageRefVisitor] = {}
for v in _REF_VISITORS:
    for ext in v.extensions:
        REFS_BY_EXT[ext] = v


def ref_visitor_for(path: Path) -> LanguageRefVisitor | None:
    return REFS_BY_EXT.get(path.suffix.lower())
