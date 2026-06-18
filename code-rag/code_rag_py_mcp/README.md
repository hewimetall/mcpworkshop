# Code RAG MCP (Python)

Python rewrite of `code-search-mcp`: FastMCP server with hybrid RuVector search over PostgreSQL.

## Stack

- Python 3.12 + [uv](https://github.com/astral-sh/uv)
- [FastMCP](https://github.com/prefecthq/fastmcp) — MCP tools + stdio/HTTP transport
- SQLAlchemy 2.0 — search store
- Alembic — runs SQL from [`migrations/`](migrations/) (`001` tables, `002` `ruvector_embed_as`, `003` namespace index)

## Quick start

```bash
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run code-rag-py-mcp --transport http --host 0.0.0.0 --port 4444
```

## MCP tools

| Tool | Description |
|------|-------------|
| `search` | Function/docstring lane |
| `call_search` | Call-pattern lane |
| `class_search` | Class/inheritance lane |
| `search_with_context` | Search + call graph neighbors |

## Docker Compose

External DB (default):

```bash
export DATABASE_URL=postgresql://ruvector:ruvector@192.168.50.2:5432/ruvector_test
docker compose --profile external-db up --build
```

Local Postgres (profile `local-db`):

```bash
docker compose --profile local-db up --build
docker compose --profile local-db run --rm migrate
```

## Prerequisites

RuVector PostgreSQL must provide:

- `ruvector` extension (created by `migrations/001_code_rag.sql`)
- `ruvector_embed_as(text, text)` (created by `migrations/002_code_rag_embed_fn.sql`)
- base `ruvector_embed(text, text)` from RuVector extension
- `ruvector_load_model(text)` for warming the embedder

## C4 / Structurizr

Architecture model: [`workspace.dsl`](workspace.dsl)

Target Structurizr workspace: http://192.168.50.2:9080/workspace/2

Validate locally:

```bash
docker run --rm -v "$PWD:/usr/local/structurizr" structurizr/structurizr validate -workspace /usr/local/structurizr/workspace.dsl
```
