"""HTML visitor — script/style blocks; inline JS delegated in ingest."""

from __future__ import annotations

from tree_sitter import Node, Parser

from simple_parser.langs._grammar import make_parser
from simple_parser.langs.base import LanguageVisitor


class HtmlVisitor(LanguageVisitor):
    language = "html"
    extensions = (".html", ".htm")
    recurse_into_units = False

    def _make_parser(self) -> Parser:
        try:
            return make_parser("html")
        except Exception:
            import tree_sitter_html as tshtml  # type: ignore[import-untyped]
            from tree_sitter import Language

            return Parser(Language(tshtml.language()))

    def accepts(self, node: Node) -> bool:
        return node.type in ("script_element", "style_element")

    def symbol(self, node: Node) -> str:
        start = node.start_point[0] + 1
        tag = "script" if node.type == "script_element" else "style"
        return f"{tag}:inline:{start}"

    def calls_in(self, unit_node: Node) -> list[str]:
        return []

    def role(self, node: Node) -> str:
        return "script" if node.type == "script_element" else "markup"
