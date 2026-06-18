"""Generic DFS walker and single-parse ingest."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from tree_sitter import Node

from simple_parser.index_policy import (
    INDEXABLE_EXTENSIONS,
    find_site_packages,
    should_index,
)
from simple_parser.langs.base import FileContext, LanguageVisitor
from simple_parser.langs.javascript import JavaScriptVisitor
from simple_parser.langs.ref_registry import ref_visitor_for
from simple_parser.langs.registry import VISITORS_BY_EXT
from simple_parser.models import CodeUnit, UnitRefs


@dataclass
class IngestResult:
    units: list[CodeUnit]
    root: Node
    ctx: FileContext
    refs: list[UnitRefs]


def _dfs(
    node: Node,
    visitor: LanguageVisitor,
    ctx: FileContext,
    units: list[CodeUnit],
    *,
    recurse_into_units: bool,
) -> None:
    if visitor.accepts(node):
        units.append(visitor.make_unit(ctx, node))
        if not recurse_into_units:
            return
    for child in node.children:
        _dfs(child, visitor, ctx, units, recurse_into_units=recurse_into_units)


def _ingest_html_inline_js(
    root: Node,
    ctx: FileContext,
    units: list[CodeUnit],
) -> None:
    """Parse inline script bodies with JavaScriptVisitor."""
    js = JavaScriptVisitor()

    def walk(node: Node) -> None:
        if node.type == "script_element":
            raw = node.text.decode(errors="replace")
            start_line = node.start_point[0] + 1
            sub_path = f"{ctx.path}:inline:{start_line}"
            sub_ctx = FileContext(
                path=sub_path,
                module=ctx.module,
                package=ctx.package,
                namespace=ctx.namespace,
                source=raw.encode(),
            )
            tree = js.parser.parse(sub_ctx.source)
            sub_units: list[CodeUnit] = []
            _dfs(
                tree.root_node,
                js,
                sub_ctx,
                sub_units,
                recurse_into_units=js.recurse_into_units,
            )
            units.extend(sub_units)
        for child in node.children:
            walk(child)

    walk(root)


def ingest_file(
    path: Path,
    visitor: LanguageVisitor,
    ctx: FileContext,
    *,
    recurse_into_units: bool | None = None,
    runtime_refs: bool = False,
) -> IngestResult:
    tree = visitor.parser.parse(ctx.source)
    rec = (
        recurse_into_units
        if recurse_into_units is not None
        else visitor.recurse_into_units
    )
    units: list[CodeUnit] = []
    _dfs(tree.root_node, visitor, ctx, units, recurse_into_units=rec)

    if visitor.language == "html":
        _ingest_html_inline_js(tree.root_node, ctx, units)

    refs: list[UnitRefs] = []
    ref_v = ref_visitor_for(path)
    if ref_v is not None:
        refs = ref_v.refs_for_units(ctx, units, tree.root_node, runtime=runtime_refs)

    return IngestResult(units=units, root=tree.root_node, ctx=ctx, refs=refs)


def walk_file(
    path: Path,
    visitor: LanguageVisitor,
    ctx: FileContext,
    *,
    recurse_into_units: bool | None = None,
) -> list[CodeUnit]:
    return ingest_file(
        path, visitor, ctx, recurse_into_units=recurse_into_units
    ).units


def ingest_repo(
    repo_root: Path,
    *,
    only_packages: set[str] | None = None,
    runtime_refs: bool = False,
) -> Iterator[IngestResult]:
    """ Функция формирования списка загрузки """
    repo_root = repo_root.resolve()
    site_packages = find_site_packages(repo_root)

    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in INDEXABLE_EXTENSIONS:
            continue
        if not should_index(
            path,
            root=repo_root,
            site_packages=site_packages,
            only_packages=only_packages,
            extension=ext,
        ):
            continue
        visitor = VISITORS_BY_EXT.get(ext)
        if visitor is None:
            continue
        ctx = FileContext.build(path, repo_root, site_packages=site_packages)
        yield ingest_file(
            path, visitor, ctx, runtime_refs=runtime_refs
        )


def walk_repo(
    repo_root: Path,
    *,
    only_packages: set[str] | None = None,
) -> Iterator[CodeUnit]:
    for result in ingest_repo(repo_root, only_packages=only_packages):
        yield from result.units
