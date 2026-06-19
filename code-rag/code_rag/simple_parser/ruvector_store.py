"""Upsert code_units and code_edges into RuVector PostgreSQL."""

from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from code_rag.simple_parser.embed_store import EmbedStore
from code_rag.simple_parser.models import Chunk, UnitRefs

DEFAULT_EMBED_MODEL = os.getenv("RUVECTOR_EMBED_MODEL", "all-MiniLM-L6-v2")

_UPSERT_UNIT = text("""
INSERT INTO code_units (
    id, qualified_name, module, language, role, symbol, class_chain,
    path, start_line, end_line, namespace, package, content, search_text,
    calls, embed_func_text, embed_call_text, embed_class_text,
    vec_func, vec_call, vec_class, content_hash, job_id
) VALUES (
    :id, :qualified_name, :module, :language, :role, :symbol, :class_chain,
    :path, :start_line, :end_line, :namespace, :package, :content, :search_text,
    :calls, :embed_func_text, :embed_call_text, :embed_class_text,
    ruvector_embed_as(:embed_func_text, :model),
    ruvector_embed_as(:embed_call_text, :model),
    ruvector_embed_as(:embed_class_text, :model),
    :content_hash, :job_id
)
ON CONFLICT (id) DO UPDATE SET
    qualified_name = EXCLUDED.qualified_name,
    module = EXCLUDED.module,
    language = EXCLUDED.language,
    role = EXCLUDED.role,
    symbol = EXCLUDED.symbol,
    class_chain = EXCLUDED.class_chain,
    path = EXCLUDED.path,
    start_line = EXCLUDED.start_line,
    end_line = EXCLUDED.end_line,
    namespace = EXCLUDED.namespace,
    package = EXCLUDED.package,
    content = EXCLUDED.content,
    search_text = EXCLUDED.search_text,
    calls = EXCLUDED.calls,
    embed_func_text = EXCLUDED.embed_func_text,
    embed_call_text = EXCLUDED.embed_call_text,
    embed_class_text = EXCLUDED.embed_class_text,
    vec_func = EXCLUDED.vec_func,
    vec_call = EXCLUDED.vec_call,
    vec_class = EXCLUDED.vec_class,
    content_hash = EXCLUDED.content_hash,
    job_id = EXCLUDED.job_id,
    updated_at = now()
""")

_DELETE_EDGES = text("""
DELETE FROM code_edges WHERE caller_id = ANY(:caller_ids)
""")

_INSERT_EDGE = text("""
INSERT INTO code_edges (caller_id, callee_qname, callee_raw)
VALUES (:caller_id, :callee_qname, :callee_raw)
ON CONFLICT (caller_id, callee_qname) DO NOTHING
""")


class RuVectorStore:
    def __init__(self, db_url: str, embed_model: str = DEFAULT_EMBED_MODEL) -> None:
        self.db_url = db_url
        self.embed_model = embed_model
        self._engine: Engine = create_engine(db_url)

    def _unit_params(
        self, chunk: Chunk, texts: dict[str, str], job_id: str
    ) -> dict[str, Any]:
        return {
            "id": chunk.id,
            "qualified_name": chunk.qualified_name,
            "module": chunk.module,
            "language": chunk.language,
            "role": chunk.role,
            "symbol": chunk.symbol,
            "class_chain": chunk.class_chain,
            "path": chunk.path,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "namespace": chunk.namespace,
            "package": chunk.package,
            "content": chunk.content,
            "search_text": chunk.search_text,
            "calls": chunk.calls,
            "embed_func_text": texts["embed_func_text"],
            "embed_call_text": texts["embed_call_text"],
            "embed_class_text": texts["embed_class_text"],
            "content_hash": chunk.content_hash,
            "job_id": job_id,
            "model": self.embed_model,
        }

    def upsert_batch(
        self,
        chunks: list[Chunk],
        *,
        refs_by_id: dict[str, UnitRefs],
        job_id: str,
    ) -> tuple[int, int]:
        if not chunks:
            return 0, 0

        embed_store = EmbedStore(refs_by_id)
        caller_ids = [c.id for c in chunks]
        n_edges = 0

        with self._engine.begin() as conn:
            conn.execute(_DELETE_EDGES, {"caller_ids": caller_ids})

            for chunk in chunks:
                texts = embed_store.texts_for_row(chunk)
                conn.execute(_UPSERT_UNIT, self._unit_params(chunk, texts, job_id))

                for callee in chunk.calls:
                    if not callee:
                        continue
                    conn.execute(
                        _INSERT_EDGE,
                        {
                            "caller_id": chunk.id,
                            "callee_qname": callee,
                            "callee_raw": callee,
                        },
                    )
                    n_edges += 1

        return len(chunks), n_edges
