"""Shared tree-sitter grammar loader."""

from __future__ import annotations

from tree_sitter import Language, Parser


def make_parser(lang_name: str, module_name: str | None = None) -> Parser:
    try:
        from tree_sitter_languages import get_language  # type: ignore[import-untyped]

        return Parser(get_language(lang_name))
    except ImportError:
        if module_name is None:
            raise
        import importlib

        mod = importlib.import_module(module_name)
        return Parser(Language(mod.language()))
