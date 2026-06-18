FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml ./
COPY code_rag_py_mcp ./code_rag_py_mcp
COPY alembic.ini ./
COPY alembic ./alembic
COPY migrations ./migrations

RUN uv sync --no-dev \
    && .venv/bin/python -c "import code_rag_py_mcp"

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 4444

CMD ["code-rag-py-mcp", "--transport", "http", "--host", "0.0.0.0", "--port", "4444"]
