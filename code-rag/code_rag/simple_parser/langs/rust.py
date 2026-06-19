"""Rust LanguageVisitor."""

from __future__ import annotations

from tree_sitter import Node, Parser, Query, QueryCursor

from code_rag.simple_parser.langs._grammar import make_parser
from code_rag.simple_parser.langs.base import LanguageVisitor

_CALL_QUERY = """
(call_expression
  function: [
    (identifier) @callee
    (field_expression field: (field_identifier) @callee)
    (scoped_identifier name: (identifier) @callee)
  ]
)
"""


class RustVisitor(LanguageVisitor):
    language = "rust"
    extensions = (".rs",)
    recurse_into_units = False

    def _make_parser(self) -> Parser:
        try:
            return make_parser("rust")
        except Exception:
            import tree_sitter_rust as tsrust  # type: ignore[import-untyped]
            from tree_sitter import Language

            return Parser(Language(tsrust.language()))

    def _call_query(self):
        if not hasattr(self, "_q"):
            from tree_sitter import Query

            self._q = Query(self.parser.language, _CALL_QUERY)
        return self._q

    def accepts(self, node: Node) -> bool:
        return node.type == "function_item"

    def symbol(self, node: Node) -> str:
        name = node.child_by_field_name("name")
        return name.text.decode() if name else "<anonymous>"

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

    def class_chain(self, node: Node) -> list[str]:
        chain: list[str] = []
        current = node.parent
        while current is not None:
            if current.type == "impl_item":
                typ = current.child_by_field_name("type")
                if typ:
                    chain.append(typ.text.decode())
            elif current.type in ("struct_item", "enum_item"):
                name = current.child_by_field_name("name")
                if name:
                    chain.append(name.text.decode())
            current = current.parent
        chain.reverse()
        return chain
