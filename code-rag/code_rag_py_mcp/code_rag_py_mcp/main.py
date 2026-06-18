"""CLI entrypoint for code-rag-py-mcp."""

from __future__ import annotations

import argparse

from code_rag_py_mcp.config import McpSettings
from code_rag_py_mcp.mcp_server import run_server


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Code RAG MCP server (Python)")
    p.add_argument(
        "--db-url",
        dest="db_url",
        default=None,
        help="PostgreSQL URL (or DATABASE_URL env)",
    )
    p.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=None,
        help="MCP transport (default: MCP_TRANSPORT or stdio)",
    )
    p.add_argument("--host", default=None, help="HTTP bind host")
    p.add_argument("--port", type=int, default=None, help="HTTP bind port")
    p.add_argument("--path", default=None, help="HTTP MCP path (default /mcp)")
    return p


def main() -> None:
    args = build_parser().parse_args()
    settings = McpSettings.from_env(
        db_url=args.db_url,
        transport=args.transport,
        host=args.host,
        port=args.port,
        path=args.path,
    )
    run_server(settings)


if __name__ == "__main__":
    main()
