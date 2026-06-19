"""Unit visitor registry by file extension."""

from __future__ import annotations

from pathlib import Path

from code_rag.simple_parser.langs.base import LanguageVisitor
from code_rag.simple_parser.langs.html import HtmlVisitor
from code_rag.simple_parser.langs.javascript import JavaScriptVisitor
from code_rag.simple_parser.langs.python import PythonVisitor
from code_rag.simple_parser.langs.rust import RustVisitor
from code_rag.simple_parser.langs.tsx import TsxVisitor
from code_rag.simple_parser.langs.typescript import TypeScriptVisitor

_VISITORS: list[LanguageVisitor] = [
    PythonVisitor(),
    RustVisitor(),
    JavaScriptVisitor(),
    TypeScriptVisitor(),
    TsxVisitor(),
    HtmlVisitor(),
]

VISITORS_BY_EXT: dict[str, LanguageVisitor] = {}
for v in _VISITORS:
    for ext in v.extensions:
        VISITORS_BY_EXT[ext] = v


def visitor_for(path: Path) -> LanguageVisitor | None:
    return VISITORS_BY_EXT.get(path.suffix.lower())
