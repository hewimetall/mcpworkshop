"""TypeScript LanguageVisitor — extends JS patterns."""

from __future__ import annotations

from simple_parser.langs.javascript import JavaScriptVisitor


class TypeScriptVisitor(JavaScriptVisitor):
    language = "typescript"
    extensions = (".ts",)

    def _make_parser(self):
        from tree_sitter import Parser

        try:
            from simple_parser.langs._grammar import make_parser

            return make_parser("typescript")
        except Exception:
            import tree_sitter_typescript as tsts  # type: ignore[import-untyped]
            from tree_sitter import Language

            return Parser(Language(tsts.language_typescript()))
