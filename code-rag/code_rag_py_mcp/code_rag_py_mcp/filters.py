"""Test-file filtering for search results."""

from __future__ import annotations

from code_rag_py_mcp.store import SearchHit


def is_test_hit(hit: SearchHit) -> bool:
    rel = hit.path.replace("\\", "/")
    return (
        "/tests/" in rel
        or rel.startswith("tests/")
        or "/test_" in rel
        or hit.namespace == "tests"
    )


def apply_test_filters(
    hits: list[SearchHit],
    *,
    deprioritize_tests: bool,
    exclude_tests: bool,
    k: int,
) -> list[SearchHit]:
    if exclude_tests:
        hits = [h for h in hits if not is_test_hit(h)]
    elif deprioritize_tests:
        non_test = [h for h in hits if not is_test_hit(h)]
        tests = [h for h in hits if is_test_hit(h)]
        hits = non_test + tests
    return hits[:k]
