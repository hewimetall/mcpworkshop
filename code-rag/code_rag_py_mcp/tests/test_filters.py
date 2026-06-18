"""Tests for test-file filtering."""

from __future__ import annotations

from code_rag_py_mcp.filters import apply_test_filters, is_test_hit
from code_rag_py_mcp.store import SearchHit


def _hit(path: str, namespace: str = "pip") -> SearchHit:
    return SearchHit(
        id="x",
        qualified_name="pkg.fn",
        path=path,
        role="function",
        namespace=namespace,
        content="pass",
        score=0.1,
        d_func=0.1,
        d_call=0.1,
        d_class=0.1,
        ts_score=0.0,
    )


def test_is_test_hit_by_path() -> None:
    assert is_test_hit(_hit("pkg/tests/test_foo.py"))
    assert is_test_hit(_hit("tests/test_foo.py"))
    assert not is_test_hit(_hit("pkg/mod.py"))


def test_is_test_hit_by_namespace() -> None:
    assert is_test_hit(_hit("pkg/mod.py", namespace="tests"))


def test_exclude_tests() -> None:
    hits = [_hit("pkg/mod.py"), _hit("pkg/tests/t.py")]
    out = apply_test_filters(hits, deprioritize_tests=True, exclude_tests=True, k=10)
    assert len(out) == 1
    assert out[0].path == "pkg/mod.py"


def test_deprioritize_tests() -> None:
    hits = [_hit("pkg/tests/t.py"), _hit("pkg/mod.py")]
    out = apply_test_filters(hits, deprioritize_tests=True, exclude_tests=False, k=10)
    assert out[0].path == "pkg/mod.py"
    assert out[1].path == "pkg/tests/t.py"
