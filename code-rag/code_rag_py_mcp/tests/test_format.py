"""Tests for response formatting."""

from __future__ import annotations

from code_rag_py_mcp.format import format_hits, snippet
from code_rag_py_mcp.store import SearchHit


def test_snippet_limits_lines() -> None:
    assert snippet("a\nb\nc", lines=2) == "a\nb"


def test_format_hits_empty() -> None:
    assert format_hits([]) == "no results"


def test_format_hits_includes_score() -> None:
    hit = SearchHit(
        id="1",
        qualified_name="pkg.fn",
        path="pkg/mod.py",
        role="function",
        namespace="ns",
        content="def fn(): pass",
        score=0.42,
        d_func=0.1,
        d_call=0.1,
        d_class=0.1,
        ts_score=0.0,
    )
    out = format_hits([hit])
    assert "pkg.fn" in out
    assert "0.4200" in out
