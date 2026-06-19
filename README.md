# mcpworkshop

Воркшоп по MCP-серверам для code intelligence и code RAG.

## Как прогнать agent-lsp

1. Создать папку `project`
2. Инициализировать или положить свой проект в `project`
3. Запустить agent-lsp (можно поправить volume mount path до `project`). Учитывайте, что agent (LLM) видит пути хостовой машины и не всегда может верно их конвертировать в пути внутри контейнера
4. Подключить к agent (OpenCode, Cursor и т.д.) URL: `http://127.0.0.1:8888` (или свой socket)
5. Запустить промпт `/agent-lsp:lsp-onboard` (учитывайте, что возможны проблемы при старте LSP)
6. Смотреть за результатом

Docker: [`infra/agent-lsp/compose.yml`](infra/agent-lsp/compose.yml)

Пример `mcp.json`:

```json
{
  "mcpServers": {
    "agent-lsp": {
      "url": "http://127.0.0.1:8888",
      "headers": {
        "Authorization": "Bearer token"
      }
    }
  }
}
```

## Как запустить MCP code-rag

Полный пайплайн:

1. **Индексация** — `gen-embedding` парсит репозиторий → `chunks.jsonl` + `refs.jsonl`
2. **Загрузка в БД** — `load-db` пишет данные в RuVector PostgreSQL
3. **MCP-сервер** — `code-rag-py-mcp` отдаёт поиск по загруженным чанкам

### 1. Запустить MCP-сервер (uv)

```bash
cd code-rag/code_rag_py_mcp
cp .env.example .env   # поправить DATABASE_URL
uv sync
uv run alembic upgrade head
uv run code-rag-py-mcp --transport http --host 0.0.0.0 --port 4444
```

Сервер будет доступен по адресу: `http://127.0.0.1:4444/mcp`

Переменные окружения (`.env`):

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | PostgreSQL с RuVector |
| `RUVECTOR_EMBED_MODEL` | Модель эмбеддингов (по умолчанию `all-MiniLM-L6-v2`) |
| `MCP_TRANSPORT` | `stdio` или `http` |
| `MCP_HOST` / `MCP_PORT` / `MCP_PATH` | HTTP bind (`0.0.0.0`, `4444`, `/mcp`) |
| `CODE_RAG_NS` | Фильтр namespace по умолчанию (опционально) |

### 3. Запустить через Docker Compose

Внешняя БД:

```bash
cd code-rag/code_rag_py_mcp
export DATABASE_URL=postgresql://ruvector:ruvector@192.168.50.2:5432/ruvector_test
docker compose up --build
```

Локальный Postgres (profile `local-db`):

```bash
docker compose --profile local-db up --build
docker compose --profile local-db run --rm migrate
```

### 2. Подготовить данные

Из корня `code-rag/`:

```bash
cd code-rag
uv sync

# проиндексировать репозиторий
uv run gen-embedding --root /path/to/repo -o ./dist

# загрузить в PostgreSQL
export DATABASE_URL=postgresql://ruvector:ruvector@192.168.50.2:5432/ruvector_test
uv run load-db -i ./dist --db-url "$DATABASE_URL"
```

Подробнее: [`code-rag/simple_parser/README.md`](code-rag/simple_parser/README.md)


### 4. Подключить к Cursor / OpenCode

В `~/.cursor/mcp.json` (или аналог):

```json
{
  "mcpServers": {
    "code-rag": {
      "url": "http://127.0.0.1:4444/mcp"
    }
  }
}
```


В opencode (или аналог):
```json
...
  "mcp": {
    "code-rag": {
      "type": "remote",
      "url": "http://127.0.0.1:4444/mcp",
      "enabled": true
    },
  }
...

```
