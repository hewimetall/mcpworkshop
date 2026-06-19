"""Abstract LanguageVisitor and FileContext."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from tree_sitter import Node, Parser

from code_rag.simple_parser.embed_text import build_embed_text
from code_rag.simple_parser.index_policy import (
    classify_namespace,
    find_site_packages,
    module_name,
    resolve_package,
)

if TYPE_CHECKING:
    from code_rag.simple_parser.models import CodeUnit


@dataclass
class FileContext:
    path: str
    module: str
    package: str | None
    namespace: str
    source: bytes
    source_lines: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.source_lines:
            self.source_lines = self.source.decode(errors="replace").splitlines()

    @classmethod
    def build(
        cls,
        path: Path,
        repo_root: Path,
        *,
        site_packages: Path | None = None,
        namespace: str | None = None,
    ) -> FileContext:
        source = path.read_bytes()
        rel = path.relative_to(repo_root)
        rel_str = str(rel)
        sp = site_packages if site_packages is not None else find_site_packages(repo_root)
        package = resolve_package(repo_root, path, sp)
        module = module_name(package, rel_str)
        ns = namespace if namespace is not None else classify_namespace(
            path, package, root=repo_root, site_packages=sp
        )
        return cls(
            path=rel_str,
            module=module,
            package=package,
            namespace=ns,
            source=source,
        )


class LanguageVisitor(ABC):
    language: str
    extensions: tuple[str, ...]
    recurse_into_units: bool = False

    _parser: Parser | None = None

    @property
    def parser(self) -> Parser:
        if self._parser is None:
            self._parser = self._make_parser()
        return self._parser

    @abstractmethod
    def _make_parser(self) -> Parser: ...

    @abstractmethod
    def accepts(self, node: Node) -> bool: ...

    @abstractmethod
    def symbol(self, node: Node) -> str: ...

    @abstractmethod
    def calls_in(self, unit_node: Node) -> list[str]: ...

    def class_chain(self, node: Node) -> list[str]:
        chain: list[str] = []
        current = node.parent
        while current is not None:
            if current.type in (
                "class_definition",
                "class_declaration",
                "impl_item",
            ):
                name_node = current.child_by_field_name("name")
                if name_node:
                    chain.append(name_node.text.decode())
            current = current.parent
        chain.reverse()
        return chain

    def role(self, node: Node) -> str:
        t = node.type
        if "impl" in t:
            return "impl"
        if "script" in t:
            return "script"
        if "markup" in t or "html" in t:
            return "markup"
        chain = self.class_chain(node)
        return "method" if chain else "function"

    def qualified_name(self, ctx: FileContext, node: Node) -> str:
        sym = self.symbol(node)
        chain = self.class_chain(node)
        parts = [ctx.module] + chain + [sym]
        return ".".join(p for p in parts if p)

    def build_embed_text(self, unit: CodeUnit) -> str:
        return build_embed_text(unit)

    def doc_for(self, ctx: FileContext, node: Node, content: str) -> str:
        from code_rag.simple_parser.simple_doc import extract_doc

        return extract_doc(self.language, ctx.source_lines, node.start_point[0], content)

    def make_unit(self, ctx: FileContext, node: Node) -> CodeUnit:
        from code_rag.simple_parser.models import CodeUnit

        lines = ctx.source_lines
        start = node.start_point[0]
        end = node.end_point[0]
        content = "\n".join(lines[start : end + 1])
        sym = self.symbol(node)
        chain = self.class_chain(node)
        calls = self.calls_in(node)
        doc = self.doc_for(ctx, node, content)

        unit = CodeUnit(
            qualified_name=self.qualified_name(ctx, node),
            module=ctx.module,
            language=self.language,
            role=self.role(node),
            symbol=sym,
            class_chain=chain,
            path=ctx.path,
            start_line=start + 1,
            end_line=end + 1,
            content=content,
            calls=calls,
            embed_text="",
            namespace=ctx.namespace,
            doc=doc,
            package=ctx.package,
        )
        unit.embed_text = self.build_embed_text(unit)
        return unit
