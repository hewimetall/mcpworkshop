#!/usr/bin/env python3
"""Workshop loader: simple_parser chunks.jsonl + refs.jsonl -> RuVector DB."""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from rag.db_load import load_chunks, load_refs  # noqa: E402
from rag.ruvector_db import RuVectorStore  # noqa: E402


def resolve_input(path: Path) -> tuple[Path, Path]:
    if path.is_dir():
        chunks_path = path / "chunks.jsonl"
    else:
        chunks_path = path
    refs_path = chunks_path.with_name("refs.jsonl")
    return chunks_path, refs_path


def main() -> None:
    ap = argparse.ArgumentParser(
        description="load simple_parser chunks.jsonl + refs.jsonl into RuVector"
    )
    ap.add_argument("-i", "--input", required=True, type=Path, help="dist/ or chunks.jsonl")
    ap.add_argument("--db-url", required=True, help="PostgreSQL DATABASE_URL")
    args = ap.parse_args()

    chunks_path, refs_path = resolve_input(args.input)
    if not chunks_path.is_file():
        raise SystemExit(f"chunks.jsonl not found: {chunks_path}")

    chunks = load_chunks(chunks_path)
    refs_by_id = load_refs(refs_path)
    job_id = uuid.uuid4().hex[:12]

    print(
        f"loading {len(chunks)} chunks, {len(refs_by_id)} refs "
        f"from {chunks_path} (job_id={job_id})",
        file=sys.stderr,
    )

    store = RuVectorStore(args.db_url)
    n_units, n_edges = store.upsert_batch(chunks, refs_by_id=refs_by_id, job_id=job_id)

    print(f"db: {n_units} units, {n_edges} edges", file=sys.stderr)


if __name__ == "__main__":
    main()
