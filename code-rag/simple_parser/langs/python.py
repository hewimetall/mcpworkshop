"""Python LanguageVisitor — tree-sitter only, no ast.walk."""

from __future__ import annotations

from tree_sitter import Language, Node, Parser, Query, QueryCursor

from simple_parser.langs.base import LanguageVisitor

_FUNCTION = "function_definition"
_DECORATED = "decorated_definition"

_CALL_QUERY_SRC = """
(call
  function: [
    (identifier) @callee
    (attribute attribute: (identifier) @callee)
  ]
)
"""


def _unwrap_decorated(node: Node) -> Node | None:
    for child in node.children:
        if child.type == _FUNCTION:
            return child
    return None


class PythonVisitor(LanguageVisitor):
    language = "python"
    extensions = (".py",)
    recurse_into_units = True

    def _make_parser(self) -> Parser:
        try:
            from tree_sitter_languages import get_language  # type: ignore[import-untyped]

            lang = get_language("python")
        except ImportError:
            import tree_sitter_python as tspython

            lang = Language(tspython.language())
        return Parser(lang)

    def _call_query(self) -> Query:
        if not hasattr(self, "_q"):
            self._q = Query(self.parser.language, _CALL_QUERY_SRC)
        return self._q

    def accepts(self, node: Node) -> bool:
        if node.type == _FUNCTION:
            return True
        if node.type == _DECORATED:
            inner = _unwrap_decorated(node)
            return inner is not None
        return False

    def symbol(self, node: Node) -> str:
        n = _unwrap_decorated(node) if node.type == _DECORATED else node
        if n is None:
            return "<anonymous>"
        name = n.child_by_field_name("name")
        return name.text.decode() if name else "<anonymous>"

    def calls_in(self, unit_node: Node) -> list[str]:
        inner = _unwrap_decorated(unit_node) if unit_node.type == _DECORATED else unit_node
        target = inner if inner is not None else unit_node
        cursor = QueryCursor(self._call_query())
        captures = cursor.captures(target)
        callees = captures.get("callee", [])
        seen: set[str] = set()
        result: list[str] = []
        for n in callees:
            name = n.text.decode()
            if name not in seen:
                seen.add(name)
                result.append(name)
        return result

    def class_chain(self, node: Node) -> list[str]:
        chain: list[str] = []
        current = node.parent
        while current is not None:
            if current.type == "class_definition":
                name = current.child_by_field_name("name")
                if name:
                    chain.append(name.text.decode())
            elif current.type == _DECORATED:
                inner = _unwrap_decorated(current)
                if inner and inner.type == "class_definition":
                    name = inner.child_by_field_name("name")
                    if name:
                        chain.append(name.text.decode())
            current = current.parent
        chain.reverse()
        return chain
