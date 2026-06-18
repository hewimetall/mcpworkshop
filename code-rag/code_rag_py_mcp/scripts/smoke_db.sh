#!/usr/bin/env bash
# Optional integration smoke against live RuVector PostgreSQL.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL not set; skipping DB smoke" >&2
  exit 0
fi

uv run python - <<'PY'
from code_rag_py_mcp.config import McpSettings
from code_rag_py_mcp.store import Store

settings = McpSettings.from_env()
store = Store(settings.db_url, embed_model=settings.embed_model)
with store.session() as session:
    store.load_model(session)
    hits = store.search_units(session, "main", k=1)
print(f"smoke ok: {len(hits)} hit(s)")
PY
