"""Plain-text formatting for MCP tool responses."""

from __future__ import annotations

from code_rag_py_mcp.search import HitContext, SearchWithContextResult
from code_rag_py_mcp.store import SearchHit


def snippet(content: str, lines: int = 8) -> str:
    return "\n".join(content.splitlines()[:lines])


def format_hits(hits: list[SearchHit]) -> str:
    if not hits:
        return "no results"
    blocks: list[str] = []
    for i, hit in enumerate(hits, 1):
        blocks.append(
            f"{i}. {hit.qualified_name}  score={hit.score:.4f}\n"
            f"   path: {hit.path}  role: {hit.role}  ns: {hit.namespace}\n"
            f"{snippet(hit.content)}"
        )
    return "\n\n".join(blocks)


def format_context(ctx: HitContext) -> str:
    hit = ctx.hit
    lines = [
        f"{hit.qualified_name}  score={hit.score:.4f}",
        f"path: {hit.path}  role: {hit.role}  ns: {hit.namespace}",
        snippet(hit.content),
    ]
    if ctx.callees:
        lines.append(f"callees ({len(ctx.callees)}):")
        for node in ctx.callees:
            lines.append(f"  -> {node.qualified_name}")
    if ctx.callers:
        lines.append(f"callers ({len(ctx.callers)}):")
        for node in ctx.callers:
            lines.append(f"  <- {node.qualified_name}")
    return "\n".join(lines)


def format_context_result(result: SearchWithContextResult) -> str:
    if not result.hits:
        return "no results"
    blocks = [f"{i}. {format_context(ctx)}" for i, ctx in enumerate(result.hits, 1)]
    return "\n\n".join(blocks)
