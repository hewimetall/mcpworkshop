"""Shared tree-sitter grammar loader."""

from __future__ import annotations

import importlib

from tree_sitter import Language, Parser

# (module, language factory attribute)
_GRAMMARS: dict[str, tuple[str, str]] = {
    "python": ("tree_sitter_python", "language"),
    "javascript": ("tree_sitter_javascript", "language"),
    "typescript": ("tree_sitter_typescript", "language_typescript"),
    "tsx": ("tree_sitter_typescript", "language_tsx"),
    "rust": ("tree_sitter_rust", "language"),
    "html": ("tree_sitter_html", "language"),
}


def make_parser(lang_name: str, module_name: str | None = None) -> Parser:
    if module_name is not None:
        mod = importlib.import_module(module_name)
        return Parser(Language(mod.language()))

    spec = _GRAMMARS.get(lang_name)
    if spec is None:
        raise ValueError(f"unknown language: {lang_name}")
    mod_name, attr = spec
    mod = importlib.import_module(mod_name)
    return Parser(Language(getattr(mod, attr)()))
