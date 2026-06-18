"""Load and execute SQL migration files from migrations/."""

from __future__ import annotations

from pathlib import Path

from alembic import op

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def run_sql_file(filename: str) -> None:
    sql = (MIGRATIONS_DIR / filename).read_text(encoding="utf-8")
    op.execute(sql)
