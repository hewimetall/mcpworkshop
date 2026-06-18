"""ruvector_embed_as helper function.

Revision ID: 002_code_rag_embed_fn
Revises: 001_code_rag
Create Date: 2026-06-17
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from migration_sql import run_sql_file

revision: str = "002_code_rag_embed_fn"
down_revision: Union[str, None] = "001_code_rag"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_file("002_code_rag_embed_fn.sql")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS ruvector_embed_as(text, text)")
