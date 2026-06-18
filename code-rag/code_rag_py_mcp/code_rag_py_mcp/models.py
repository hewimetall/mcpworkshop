"""SQLAlchemy ORM models for RuVector code RAG tables."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CodeUnit(Base):
    """Indexed code chunk with multi-lane embeddings."""

    __tablename__ = "code_units"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    qualified_name: Mapped[str] = mapped_column(Text, nullable=False)
    module: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(Text)
    symbol: Mapped[str | None] = mapped_column(Text)
    class_chain: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    path: Mapped[str | None] = mapped_column(Text)
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    namespace: Mapped[str | None] = mapped_column(Text)
    package: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    search_text: Mapped[str | None] = mapped_column(Text)
    calls: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    embed_func_text: Mapped[str | None] = mapped_column(Text)
    embed_call_text: Mapped[str | None] = mapped_column(Text)
    embed_class_text: Mapped[str | None] = mapped_column(Text)
    # vec_* columns use ruvector(384); managed via migrations/*.sql
    content_hash: Mapped[str | None] = mapped_column(Text)
    job_id: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    outgoing_edges: Mapped[list[CodeEdge]] = relationship(
        "CodeEdge",
        back_populates="caller",
        foreign_keys="CodeEdge.caller_id",
        cascade="all, delete-orphan",
    )


class CodeEdge(Base):
    """Call-graph edge from caller unit to callee qualified name."""

    __tablename__ = "code_edges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    caller_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("code_units.id", ondelete="CASCADE"),
        nullable=False,
    )
    callee_qname: Mapped[str] = mapped_column(Text, nullable=False)
    callee_raw: Mapped[str | None] = mapped_column(Text)

    caller: Mapped[CodeUnit] = relationship(
        "CodeUnit",
        back_populates="outgoing_edges",
        foreign_keys=[caller_id],
    )
