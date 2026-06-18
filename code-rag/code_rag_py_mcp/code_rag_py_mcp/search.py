"""Search result types and graph expansion."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy.orm import Session

from code_rag_py_mcp.store import SearchHit, Store


@dataclass
class GraphNode:
    qualified_name: str
    path: str | None
    unit_id: str | None
    callee_raw: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HitContext:
    hit: SearchHit
    callees: list[GraphNode]
    callers: list[GraphNode]

    def to_dict(self) -> dict[str, Any]:
        return {
            "hit": asdict(self.hit),
            "callees": [n.to_dict() for n in self.callees],
            "callers": [n.to_dict() for n in self.callers],
        }


@dataclass
class SearchWithContextResult:
    query: str
    hits: list[HitContext]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "hits": [h.to_dict() for h in self.hits],
        }


def search_with_context(
    store: Store,
    query: str,
    *,
    k: int = 10,
    expand_depth: int = 1,
    namespace: str | None = None,
    lanes: dict[str, float] | None = None,
) -> SearchWithContextResult:
    """Return top-k search hits, each with callees/callers up to expand_depth hops."""
    with store.session() as session:
        hits = store.search_units(
            session,
            query,
            k=k,
            namespace=namespace,
            lanes=lanes,
        )
        if expand_depth <= 0:
            contexts = [
                HitContext(hit=hit, callees=[], callers=[]) for hit in hits
            ]
        elif expand_depth == 1:
            contexts = _contexts_depth_one(store, session, hits)
        else:
            contexts = [
                HitContext(
                    hit=hit,
                    callees=_expand_callees(store, session, hit.id, expand_depth),
                    callers=_expand_callers(
                        store, session, hit.qualified_name, expand_depth
                    ),
                )
                for hit in hits
            ]
    return SearchWithContextResult(query=query, hits=contexts)


def _contexts_depth_one(
    store: Store,
    session: Session,
    hits: list[SearchHit],
) -> list[HitContext]:
    callees_by_caller: dict[str, list[GraphNode]] = defaultdict(list)
    callers_by_callee: dict[str, list[GraphNode]] = defaultdict(list)

    if hits:
        callee_rows = store.expand_callees_batch(
            session, [h.id for h in hits]
        )
        for row in callee_rows:
            caller_id = row.get("caller_id") or _infer_single_caller(hits, row)
            if caller_id is None:
                continue
            callees_by_caller[caller_id].append(_callee_row_to_node(row))

        caller_rows = store.expand_callers_batch(
            session, [h.qualified_name for h in hits]
        )
        for row in caller_rows:
            callee_qname = row.get("callee_qname") or _infer_single_callee(hits, row)
            if callee_qname is None:
                continue
            callers_by_callee[callee_qname].append(_caller_row_to_node(row))

    return [
        HitContext(
            hit=hit,
            callees=callees_by_caller.get(hit.id, []),
            callers=callers_by_callee.get(hit.qualified_name, []),
        )
        for hit in hits
    ]


def _infer_single_caller(hits: list[SearchHit], row: dict[str, Any]) -> str | None:
    if len(hits) == 1:
        return hits[0].id
    return None


def _infer_single_callee(hits: list[SearchHit], row: dict[str, Any]) -> str | None:
    if len(hits) == 1:
        return hits[0].qualified_name
    return None


def _callee_row_to_node(row: dict[str, Any]) -> GraphNode:
    return GraphNode(
        qualified_name=row["callee_qname"],
        path=row.get("path"),
        unit_id=row.get("id"),
        callee_raw=row.get("callee_raw"),
    )


def _caller_row_to_node(row: dict[str, Any]) -> GraphNode:
    return GraphNode(
        qualified_name=row["qualified_name"],
        path=row.get("path"),
        unit_id=row.get("caller_id"),
    )


def _expand_callees(
    store: Store,
    session: Session,
    root_id: str,
    depth: int,
) -> list[GraphNode]:
    if depth <= 0:
        return []

    results: list[GraphNode] = []
    seen: set[str] = set()
    frontier: set[str] = {root_id}

    for _ in range(depth):
        if not frontier:
            break
        rows = store.expand_callees_batch(session, list(frontier))
        next_frontier: set[str] = set()
        for row in rows:
            qname = row["callee_qname"]
            if qname in seen:
                continue
            seen.add(qname)
            unit_id = row.get("id")
            results.append(_callee_row_to_node(row))
            if unit_id:
                next_frontier.add(unit_id)
        frontier = next_frontier

    return results


def _expand_callers(
    store: Store,
    session: Session,
    root_qname: str,
    depth: int,
) -> list[GraphNode]:
    if depth <= 0:
        return []

    results: list[GraphNode] = []
    seen: set[str] = set()
    frontier: set[str] = {root_qname}

    for _ in range(depth):
        if not frontier:
            break
        rows = store.expand_callers_batch(session, list(frontier))
        next_frontier: set[str] = set()
        for row in rows:
            qname = row["qualified_name"]
            if qname in seen:
                continue
            seen.add(qname)
            results.append(_caller_row_to_node(row))
            next_frontier.add(qname)
        frontier = next_frontier

    return results
