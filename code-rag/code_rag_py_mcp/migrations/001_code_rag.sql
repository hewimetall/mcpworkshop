-- Code RAG schema for ruvector_test (all-MiniLM-L6-v2, 384 dimensions)

CREATE EXTENSION IF NOT EXISTS ruvector;

CREATE TABLE IF NOT EXISTS code_units (
    id               TEXT PRIMARY KEY,
    qualified_name   TEXT NOT NULL,
    module           TEXT,
    language         TEXT,
    role             TEXT,
    symbol           TEXT,
    class_chain      TEXT[],
    path             TEXT,
    start_line       INT,
    end_line         INT,
    namespace        TEXT,
    package          TEXT,
    content          TEXT NOT NULL,
    search_text      TEXT,
    calls            TEXT[],
    embed_func_text  TEXT,
    embed_call_text  TEXT,
    embed_class_text TEXT,
    vec_func         ruvector(384),
    vec_call         ruvector(384),
    vec_class        ruvector(384),
    content_hash     TEXT,
    job_id           TEXT,
    updated_at       TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS code_edges (
    id           BIGSERIAL PRIMARY KEY,
    caller_id    TEXT NOT NULL REFERENCES code_units(id) ON DELETE CASCADE,
    callee_qname TEXT NOT NULL,
    callee_raw   TEXT,
    UNIQUE (caller_id, callee_qname)
);

CREATE INDEX IF NOT EXISTS idx_units_vec_func ON code_units
    USING hnsw (vec_func ruvector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_units_vec_call ON code_units
    USING hnsw (vec_call ruvector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_units_vec_class ON code_units
    USING hnsw (vec_class ruvector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_units_fts ON code_units
    USING gin (to_tsvector('simple', coalesce(search_text, '')));

CREATE INDEX IF NOT EXISTS idx_edges_caller ON code_edges(caller_id);
CREATE INDEX IF NOT EXISTS idx_edges_callee ON code_edges(callee_qname);
