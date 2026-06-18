"""Code RAG tables, indexes, ruvector extension.

Revision ID: 001_code_rag
Revises:
Create Date: 2026-06-17
"""

from __future__ import annotations

from typing import Sequence, Union

from migration_sql import run_sql_file

revision: str = "001_code_rag"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_file("001_code_rag.sql")


def downgrade() -> None:
    from alembic import op

    op.execute("DROP TABLE IF EXISTS code_edges")
    op.execute("DROP TABLE IF EXISTS code_units")
