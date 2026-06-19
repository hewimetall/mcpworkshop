"""Abstract LanguageRefVisitor for semantic refs (mro, metaclass, …)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from tree_sitter import Node

from code_rag.simple_parser.langs.base import FileContext
from code_rag.simple_parser.models import CodeUnit, UnitRefs


class LanguageRefVisitor(ABC):
    language: str
    extensions: tuple[str, ...]

    @abstractmethod
    def refs_for_units(
        self,
        ctx: FileContext,
        units: list[CodeUnit],
        root: Node,
        *,
        runtime: bool = False,
    ) -> list[UnitRefs]: ...
