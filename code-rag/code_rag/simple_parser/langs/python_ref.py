"""Python RefVisitor — static mro/metaclass from AST; runtime opt-in."""

from __future__ import annotations

import importlib

from tree_sitter import Node

from code_rag.simple_parser.langs.base import FileContext
from code_rag.simple_parser.langs.python import _DECORATED
from code_rag.simple_parser.langs.ref_base import LanguageRefVisitor
from code_rag.simple_parser.models import CodeUnit, UnitRefs

_REF_ROLES = frozenset({"method", "function", "classmethod", "staticmethod"})

_CLASS_TYPES = frozenset({"class_definition"})


def _class_node(node: Node) -> Node | None:
    if node.type == "class_definition":
        return node
    if node.type == _DECORATED:
        for child in node.children:
            if child.type == "class_definition":
                return child
    return None


def find_enclosing_class(root: Node, unit: CodeUnit) -> Node | None:
    """Innermost class whose span contains the unit lines."""
    best: Node | None = None
    best_depth = -1

    def visit(node: Node, depth: int) -> None:
        nonlocal best, best_depth
        cls = _class_node(node)
        if cls is not None:
            start = node.start_point[0] + 1
            end = node.end_point[0] + 1
            if start <= unit.start_line <= end and start <= unit.end_line <= end:
                if depth > best_depth:
                    best = node
                    best_depth = depth
        for child in node.children:
            visit(child, depth + 1)

    visit(root, 0)
    return best


def bases_of(class_node: Node) -> list[str]:
    names: list[str] = []
    supers = class_node.child_by_field_name("superclasses")
    if supers is None:
        for child in class_node.children:
            if child.type == "argument_list":
                supers = child
                break
    if supers is None:
        return names
    for child in supers.children:
        if child.type in ("identifier", "attribute"):
            names.append(child.text.decode())
        elif child.type == "call" and child.child_by_field_name("function"):
            fn = child.child_by_field_name("function")
            if fn:
                names.append(fn.text.decode())
    return names


def metaclass_of(class_node: Node) -> str | None:
    for child in class_node.children:
        if child.type != "argument_list":
            continue
        for arg in child.children:
            if arg.type != "keyword_argument":
                continue
            key = arg.child_by_field_name("name")
            if key and key.text.decode() == "metaclass":
                val = arg.child_by_field_name("value")
                if val:
                    return val.text.decode()
    return None


def static_mro_chain(class_node: Node) -> str:
    bases = bases_of(class_node)
    name = class_node.child_by_field_name("name")
    cls_name = name.text.decode() if name else "?"
    parts = bases + [cls_name, "object"]
    return ", ".join(parts)


def runtime_mro(module: str, class_name: str) -> dict[str, str] | None:
    try:
        mod = importlib.import_module(module)
        cls = getattr(mod, class_name)
        mro = ", ".join(c.__name__ for c in cls.__mro__)
        return {
            "mro": mro,
            "metaclass": type(cls).__name__,
            "mro_source": "runtime",
        }
    except (ImportError, AttributeError, TypeError):
        return None


class PythonRefVisitor(LanguageRefVisitor):
    language = "python"
    extensions = (".py",)

    def refs_for_units(
        self,
        ctx: FileContext,
        units: list[CodeUnit],
        root: Node,
        *,
        runtime: bool = False,
    ) -> list[UnitRefs]:
        out: list[UnitRefs] = []
        for u in units:
            if u.role not in _REF_ROLES or not u.class_chain:
                continue

            if runtime and ctx.namespace == "pip":
                refs = runtime_mro(ctx.module, u.class_chain[-1])
                if refs is None:
                    continue
            else:
                class_node = find_enclosing_class(root, u)
                if class_node is None:
                    continue
                target = _class_node(class_node) or class_node
                meta = metaclass_of(target) or "type"
                refs = {
                    "mro": static_mro_chain(target),
                    "metaclass": meta,
                    "mro_source": "static",
                }

            out.append(
                UnitRefs(
                    unit_id=u.id,
                    qualified_name=u.qualified_name,
                    path=u.path,
                    language=u.language,
                    refs=refs,
                )
            )
        return out
