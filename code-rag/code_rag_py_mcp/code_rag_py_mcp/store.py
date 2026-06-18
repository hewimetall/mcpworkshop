"""SQLAlchemy-backed RuVector search store."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.orm import Session, sessionmaker

from code_rag_py_mcp.config import DEFAULT_LANE_WEIGHTS, EMBED_MODEL

_SEARCH_SQL = text("""
WITH q AS (
    SELECT ruvector_embed_as(:query, :model) AS qv
),
ranked AS (
    SELECT
        u.id,
        u.qualified_name,
        u.path,
        u.role,
        u.namespace,
        u.content,
        (u.vec_func <=> q.qv)::double precision AS d_func,
        (u.vec_call <=> q.qv)::double precision AS d_call,
        (u.vec_class <=> q.qv)::double precision AS d_class,
        ts_rank(
            to_tsvector('simple', coalesce(u.search_text, '')),
            plainto_tsquery('simple', :query)
        )::double precision AS ts_score
    FROM code_units u, q
    WHERE (:namespace::text IS NULL OR u.namespace = :namespace)
)
SELECT
    id,
    qualified_name,
    path,
    role,
    namespace,
    content,
    d_func,
    d_call,
    d_class,
    ts_score,
    (
        :w_func * d_func +
        :w_call * d_call +
        :w_class * d_class -
        :w_fts * ts_score
    )::double precision AS score
FROM ranked
ORDER BY score
LIMIT :k
""")

_EXPAND_CALLEES_SQL = text("""
SELECT DISTINCT e.callee_qname, u.id, u.qualified_name, u.path
FROM code_edges e
LEFT JOIN code_units u ON u.qualified_name = e.callee_qname
WHERE e.caller_id = :caller_id
""")

_EXPAND_CALLEES_BATCH_SQL = text("""
SELECT DISTINCT
    e.caller_id,
    e.callee_qname,
    e.callee_raw,
    u.id,
    u.qualified_name,
    u.path
FROM code_edges e
LEFT JOIN code_units u ON u.qualified_name = e.callee_qname
WHERE e.caller_id = ANY(:caller_ids)
""")

_EXPAND_CALLERS_SQL = text("""
SELECT DISTINCT e.caller_id, u.qualified_name, u.path
FROM code_edges e
JOIN code_units u ON u.id = e.caller_id
WHERE e.callee_qname = :callee_qname
""")

_EXPAND_CALLERS_BATCH_SQL = text("""
SELECT DISTINCT
    e.callee_qname,
    e.caller_id,
    u.qualified_name,
    u.path
FROM code_edges e
JOIN code_units u ON u.id = e.caller_id
WHERE e.callee_qname = ANY(:callee_qnames)
""")


@dataclass
class SearchHit:
    id: str
    qualified_name: str
    path: str
    role: str
    namespace: str
    content: str
    score: float
    d_func: float
    d_call: float
    d_class: float
    ts_score: float


class Store:
    def __init__(self, db_url: str, *, embed_model: str = EMBED_MODEL) -> None:
        self.db_url = db_url
        self.embed_model = embed_model
        self._engine: Engine = create_engine(
            db_url,
            pool_size=8,
            max_overflow=0,
            pool_pre_ping=True,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> Engine:
        return self._engine

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()

    def load_model(self, session: Session) -> None:
        session.execute(
            text("SELECT ruvector_load_model(:model)"),
            {"model": self.embed_model},
        )

    def search_units(
        self,
        session: Session,
        query: str,
        *,
        k: int = 10,
        namespace: str | None = None,
        lanes: dict[str, float] | None = None,
    ) -> list[SearchHit]:
        weights = {**DEFAULT_LANE_WEIGHTS, **(lanes or {})}
        params = {
            "query": query,
            "model": self.embed_model,
            "namespace": namespace,
            "k": k,
            **weights,
        }
        rows = session.execute(_SEARCH_SQL, params).mappings().all()
        return [_row_to_search_hit(row) for row in rows]

    def expand_callees_batch(
        self,
        session: Session,
        caller_ids: list[str],
    ) -> list[dict[str, Any]]:
        if not caller_ids:
            return []
        if len(caller_ids) == 1:
            sql, params = _EXPAND_CALLEES_SQL, {"caller_id": caller_ids[0]}
        else:
            sql, params = _EXPAND_CALLEES_BATCH_SQL, {"caller_ids": caller_ids}
        return [dict(row) for row in session.execute(sql, params).mappings().all()]

    def expand_callers_batch(
        self,
        session: Session,
        callee_qnames: list[str],
    ) -> list[dict[str, Any]]:
        if not callee_qnames:
            return []
        if len(callee_qnames) == 1:
            sql, params = _EXPAND_CALLERS_SQL, {"callee_qname": callee_qnames[0]}
        else:
            sql, params = _EXPAND_CALLERS_BATCH_SQL, {"callee_qnames": callee_qnames}
        return [dict(row) for row in session.execute(sql, params).mappings().all()]


def _row_to_search_hit(row: RowMapping) -> SearchHit:
    return SearchHit(
        id=row["id"],
        qualified_name=row["qualified_name"],
        path=row["path"],
        role=row["role"],
        namespace=row["namespace"] or "",
        content=row["content"],
        score=float(row["score"]),
        d_func=float(row["d_func"]),
        d_call=float(row["d_call"]),
        d_class=float(row["d_class"]),
        ts_score=float(row["ts_score"] or 0),
    )
