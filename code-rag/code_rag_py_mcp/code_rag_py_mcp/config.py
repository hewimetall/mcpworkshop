"""Application configuration from environment and CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = os.getenv("RUVECTOR_EMBED_MODEL", "all-MiniLM-L6-v2")
EMBED_DIM = 384
CODE_RAG_NS = os.getenv("CODE_RAG_NS") or None

DEFAULT_LANE_WEIGHTS = {
    "w_func": 0.6,
    "w_call": 0.2,
    "w_class": 0.2,
    "w_fts": 0.1,
}

LANE_PRESETS: dict[str, dict[str, float]] = {
    "balanced": DEFAULT_LANE_WEIGHTS,
    "func": {"w_func": 0.7, "w_call": 0.15, "w_class": 0.05, "w_fts": 0.1},
    "call": {"w_func": 0.15, "w_call": 0.7, "w_class": 0.05, "w_fts": 0.1},
    "class": {"w_func": 0.15, "w_call": 0.05, "w_class": 0.7, "w_fts": 0.1},
}


def database_url(override: str | None = None) -> str:
    url = override or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env or pass --db-url."
        )
    return url


@dataclass(frozen=True)
class McpSettings:
    transport: str
    host: str
    port: int
    path: str
    db_url: str
    embed_model: str
    default_namespace: str | None

    @classmethod
    def from_env(
        cls,
        *,
        db_url: str | None = None,
        transport: str | None = None,
        host: str | None = None,
        port: int | None = None,
        path: str | None = None,
    ) -> McpSettings:
        return cls(
            transport=(transport or os.getenv("MCP_TRANSPORT", "stdio")).lower(),
            host=host or os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(port or os.getenv("MCP_PORT", "4444")),
            path=path or os.getenv("MCP_PATH", "/mcp"),
            db_url=database_url(db_url),
            embed_model=EMBED_MODEL,
            default_namespace=CODE_RAG_NS,
        )
