"""JavaScript LanguageVisitor."""

from __future__ import annotations

from tree_sitter import Node, Parser, Query, QueryCursor

from code_rag.simple_parser.langs._grammar import make_parser
from code_rag.simple_parser.langs.base import LanguageVisitor

_CALL_QUERY = """
(call_expression
  function: [
    (identifier) @callee
    (member_expression property: (property_identifier) @callee)
  ]
)
"""

_UNIT_TYPES = frozenset(
    {
        "function_declaration",
        "method_definition",
        "arrow_function",
        "function_expression",
    }
)


class JavaScriptVisitor(LanguageVisitor):
    language = "javascript"
    extensions = (".js", ".mjs", ".cjs")
    recurse_into_units = True

    def _make_parser(self) -> Parser:
        try:
            return make_parser("javascript")
        except Exception:
            import tree_sitter_javascript as tsjs  # type: ignore[import-untyped]
            from tree_sitter import Language

            return Parser(Language(tsjs.language()))

    def _call_query(self):
        if not hasattr(self, "_q"):
            from tree_sitter import Query

            self._q = Query(self.parser.language, _CALL_QUERY)
        return self._q

    def accepts(self, node: Node) -> bool:
        if node.type in _UNIT_TYPES:
            return True
        if node.type == "lexical_declaration":
            return any(c.type == "arrow_function" for c in node.children)
        return False

    def symbol(self, node: Node) -> str:
        if node.type == "method_definition":
            name = node.child_by_field_name("name")
            return name.text.decode() if name else "<anonymous>"
        if node.type == "function_declaration":
            name = node.child_by_field_name("name")
            return name.text.decode() if name else "<anonymous>"
        if node.type == "lexical_declaration":
            for c in node.children:
                if c.type == "variable_declarator":
                    n = c.child_by_field_name("name")
                    if n:
                        return n.text.decode()
        return "<anonymous>"

    def calls_in(self, unit_node: Node) -> list[str]:
        cursor = QueryCursor(self._call_query())
        captures = cursor.captures(unit_node)
        seen: set[str] = set()
        result: list[str] = []
        for n in captures.get("callee", []):
            t = n.text.decode()
            if t not in seen:
                seen.add(t)
                result.append(t)
        return result
