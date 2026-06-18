"""Namespace index on code_units.

Revision ID: 003_code_rag_ns_index
Revises: 002_code_rag_embed_fn
Create Date: 2026-06-17
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from migration_sql import run_sql_file

revision: str = "003_code_rag_ns_index"
down_revision: Union[str, None] = "002_code_rag_embed_fn"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_file("003_code_rag_ns_index.sql")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_units_namespace")
