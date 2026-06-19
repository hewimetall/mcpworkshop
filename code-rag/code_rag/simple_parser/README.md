# simple-parser

Multi-language tree-sitter chunker и загрузчик в RuVector PostgreSQL для code RAG.

Пайплайн:

1. `gen-embedding` — обход репозитория → `chunks.jsonl` + `refs.jsonl`
2. `load-db` — загрузка jsonl в PostgreSQL (таблицы `code_units`, `code_edges`)

## Требования

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Для `load-db`: PostgreSQL с расширением RuVector и миграциями из [`code_rag_py_mcp/migrations/`](../code_rag_py_mcp/migrations/)

## Установка

Из корня `code-rag/` (где лежит `pyproject.toml`):

```bash
cd ../   # из simple_parser/ в code-rag/
uv sync
```

## Запуск

### Локально (`uv run`)

```bash
# из code-rag/
uv run gen-embedding --root ./simple_parser -o ./dist
uv run load-db -i ./dist --db-url "$DATABASE_URL"
```

Из каталога `simple_parser/`:

```bash
uv run --project .. gen-embedding --root . -o ./dist
uv run --project .. load-db -i ./dist --db-url "$DATABASE_URL"
```

### Как tool (`uv tool run`)

```bash
cd /path/to/code-rag

uv tool run --from . gen-embedding --root ./simple_parser -o ./dist
uv tool run --from . load-db -i ./dist --db-url postgresql://user:pass@host:5432/db
```

Постоянная установка в tool-env:

```bash
uv tool install -e .
gen-embedding --root /path/to/repo -o ./dist
load-db -i ./dist --db-url "$DATABASE_URL"
```

## CLI

### `gen-embedding`

```bash
uv run gen-embedding --root <repo> [-o <dist/|chunks.jsonl>]
```

| Флаг | Описание |
|------|----------|
| `--root` | Корень индексируемого репозитория (обязательный) |
| `-o`, `--output` | Папка (`dist/`) или файл `chunks.jsonl`; `refs.jsonl` пишется рядом |

### `load-db`

```bash
uv run load-db -i <dist/|chunks.jsonl> --db-url <postgresql-url>
```

| Флаг | Описание |
|------|----------|
| `-i`, `--input` | Папка с `chunks.jsonl` или путь к файлу (обязательный) |
| `--db-url` | PostgreSQL `DATABASE_URL` (обязательный) |

Переменные окружения (опционально):

- `DATABASE_URL` — можно передать в shell и подставить в `--db-url`
- `RUVECTOR_EMBED_MODEL` — модель для `ruvector_embed_as()` (по умолчанию `all-MiniLM-L6-v2`)

## Выходные файлы

`gen-embedding` создаёт:

- `chunks.jsonl` — чанки кода с `search_text`, `embed_text`, `calls`, метаданными
- `refs.jsonl` — ссылки на MRO, metaclass и прочие ref-поля по `unit_id`

## Связанные компоненты

- [`code_rag_py_mcp`](../code_rag_py_mcp/) — MCP-сервер поиска по загруженным данным
- Миграции БД: `code_rag_py_mcp/migrations/001_code_rag.sql`, `002_code_rag_embed_fn.sql`
