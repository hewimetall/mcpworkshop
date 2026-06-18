"""FastMCP server exposing code RAG search tools."""

from __future__ import annotations

from fastmcp import FastMCP

from code_rag_py_mcp.config import LANE_PRESETS, McpSettings
from code_rag_py_mcp.filters import apply_test_filters
from code_rag_py_mcp.format import format_context_result, format_hits
from code_rag_py_mcp.search import (
    SearchWithContextResult,
    search_with_context as graph_search,
)
from code_rag_py_mcp.store import SearchHit, Store

mcp = FastMCP("code-rag-py-mcp")

_store: Store | None = None
_settings: McpSettings | None = None


def configure(settings: McpSettings) -> None:
    global _settings, _store
    _settings = settings
    _store = Store(settings.db_url, embed_model=settings.embed_model)


def _get_store() -> Store:
    if _store is None:
        raise RuntimeError("MCP server not configured; call configure() first")
    return _store


def _resolve_namespace(namespace: str | None) -> str | None:
    if namespace is not None:
        return namespace
    if _settings is not None:
        return _settings.default_namespace
    return None


def _run_lane_search(
    query: str,
    lane: str,
    k: int,
    namespace: str | None,
    deprioritize_tests: bool,
    exclude_tests: bool,
) -> str:
    store = _get_store()
    fetch_k = k * 3 if (deprioritize_tests or exclude_tests) else k
    with store.session() as session:
        hits = store.search_units(
            session,
            query,
            k=fetch_k,
            namespace=_resolve_namespace(namespace),
            lanes=LANE_PRESETS[lane],
        )
    hits = apply_test_filters(
        hits,
        deprioritize_tests=deprioritize_tests,
        exclude_tests=exclude_tests,
        k=k,
    )
    return format_hits(hits)


@mcp.tool()
def search(
    query: str,
    k: int = 10,
    namespace: str | None = None,
    deprioritize_tests: bool = True,
    exclude_tests: bool = False,
) -> str:
    """Find functions/methods by signature and docstring (func lane)."""
    return _run_lane_search(
        query, "func", k, namespace, deprioritize_tests, exclude_tests
    )


@mcp.tool()
def call_search(
    query: str,
    k: int = 10,
    namespace: str | None = None,
    deprioritize_tests: bool = True,
    exclude_tests: bool = False,
) -> str:
    """Find code by who-it-calls patterns (call lane)."""
    return _run_lane_search(
        query, "call", k, namespace, deprioritize_tests, exclude_tests
    )


@mcp.tool()
def class_search(
    query: str,
    k: int = 10,
    namespace: str | None = None,
    deprioritize_tests: bool = True,
    exclude_tests: bool = False,
) -> str:
    """Find class/module members by inheritance context (class lane)."""
    return _run_lane_search(
        query, "class", k, namespace, deprioritize_tests, exclude_tests
    )


@mcp.tool()
def search_with_context(
    query: str,
    k: int = 10,
    expand_depth: int = 1,
    namespace: str | None = None,
    deprioritize_tests: bool = True,
    exclude_tests: bool = False,
) -> str:
    """Vector search plus callees/callers from code_edges for each hit."""
    store = _get_store()
    fetch_k = k * 3 if (deprioritize_tests or exclude_tests) else k
    result = graph_search(
        store,
        query,
        k=fetch_k,
        expand_depth=expand_depth,
        namespace=_resolve_namespace(namespace),
        lanes=LANE_PRESETS["balanced"],
    )
    if exclude_tests or deprioritize_tests:
        hits = [ctx.hit for ctx in result.hits]
        filtered = apply_test_filters(
            hits,
            deprioritize_tests=deprioritize_tests,
            exclude_tests=exclude_tests,
            k=k,
        )
        keep = {h.id for h in filtered}
        result = SearchWithContextResult(
            query=result.query,
            hits=[ctx for ctx in result.hits if ctx.hit.id in keep],
        )
    return format_context_result(result)


def run_server(settings: McpSettings) -> None:
    configure(settings)
    if settings.transport == "http":
        mcp.run(
            transport="http",
            host=settings.host,
            port=settings.port,
            path=settings.path,
        )
    else:
        mcp.run(transport="stdio")
