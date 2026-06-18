"""TSX LanguageVisitor."""

from __future__ import annotations

from simple_parser.langs.javascript import JavaScriptVisitor


class TsxVisitor(JavaScriptVisitor):
    language = "tsx"
    extensions = (".tsx", ".jsx")

    def _make_parser(self):
        from tree_sitter import Parser

        try:
            from simple_parser.langs._grammar import make_parser

            return make_parser("tsx")
        except Exception:
            import tree_sitter_typescript as tsts  # type: ignore[import-untyped]
            from tree_sitter import Language

            return Parser(Language(tsts.language_tsx()))
