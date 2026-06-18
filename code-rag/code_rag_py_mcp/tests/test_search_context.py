"""Tests for search_with_context graph expansion."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from code_rag_py_mcp.search import search_with_context
from code_rag_py_mcp.store import SearchHit


def _hit(
    unit_id: str,
    qname: str,
    *,
    path: str = "/pkg/mod.py",
) -> SearchHit:
    return SearchHit(
        id=unit_id,
        qualified_name=qname,
        path=path,
        role="function",
        namespace="pip",
        content=f"def {qname.split('.')[-1]}(): pass",
        score=0.1,
        d_func=0.1,
        d_call=0.2,
        d_class=0.3,
        ts_score=0.0,
    )


@pytest.fixture
def store() -> MagicMock:
    mock = MagicMock()
    session = MagicMock()
    mock.session.return_value.__enter__ = MagicMock(return_value=session)
    mock.session.return_value.__exit__ = MagicMock(return_value=False)
    return mock


def test_expand_depth_zero_returns_empty_neighbors(store: MagicMock) -> None:
    store.search_units.return_value = [_hit("a::foo", "pkg.foo")]

    result = search_with_context(store, "foo", k=1, expand_depth=0)

    assert len(result.hits) == 1
    assert result.hits[0].callees == []
    assert result.hits[0].callers == []
    store.expand_callees_batch.assert_not_called()
    store.expand_callers_batch.assert_not_called()


def test_depth_one_groups_callees_and_callers_per_hit(store: MagicMock) -> None:
    hit_a = _hit("a::foo", "pkg.foo")
    hit_b = _hit("b::bar", "pkg.bar")
    store.search_units.return_value = [hit_a, hit_b]

    session = store.session.return_value.__enter__.return_value

    def callees_batch(sess, caller_ids: list[str]):
        rows = []
        if "a::foo" in caller_ids:
            rows.append(
                {
                    "caller_id": "a::foo",
                    "callee_qname": "pkg.baz",
                    "callee_raw": "baz",
                    "id": "c::baz",
                    "qualified_name": "pkg.baz",
                    "path": "/pkg/baz.py",
                }
            )
        if "b::bar" in caller_ids:
            rows.append(
                {
                    "caller_id": "b::bar",
                    "callee_qname": "pkg.external",
                    "callee_raw": "external",
                    "id": None,
                    "qualified_name": None,
                    "path": None,
                }
            )
        return rows

    def callers_batch(sess, callee_qnames: list[str]):
        rows = []
        if "pkg.foo" in callee_qnames:
            rows.append(
                {
                    "callee_qname": "pkg.foo",
                    "caller_id": "x::main",
                    "qualified_name": "pkg.main",
                    "path": "/pkg/main.py",
                }
            )
        if "pkg.bar" in callee_qnames:
            rows.append(
                {
                    "callee_qname": "pkg.bar",
                    "caller_id": "y::run",
                    "qualified_name": "pkg.run",
                    "path": "/pkg/run.py",
                }
            )
        return rows

    store.expand_callees_batch.side_effect = callees_batch
    store.expand_callers_batch.side_effect = callers_batch

    result = search_with_context(store, "query", k=2, expand_depth=1)

    assert len(result.hits) == 2
    foo_ctx = result.hits[0]
    assert foo_ctx.hit.id == "a::foo"
    assert len(foo_ctx.callees) == 1
    assert foo_ctx.callees[0].qualified_name == "pkg.baz"
    assert len(foo_ctx.callers) == 1
    assert foo_ctx.callers[0].qualified_name == "pkg.main"

    store.search_units.assert_called_once()
    assert store.search_units.call_args[0][0] is session
