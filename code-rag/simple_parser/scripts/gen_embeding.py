"""Скрипт: ingest_repo → chunks.jsonl + refs.jsonl (рядом с -o)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from simple_parser.embed_store import EmbedStore
from simple_parser.embed_text import build_search_text
from simple_parser.models import Chunk, chunk_as_dict
from simple_parser.walker import ingest_repo


def main() -> None:
    ap = argparse.ArgumentParser(description="multi-lang tree-sitter chunker")
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        help="папка (dist/) или файл chunks.jsonl; refs.jsonl — рядом",
    )
    args = ap.parse_args()

    out = args.output or Path("chunks.jsonl")
    if out.is_dir() or out.suffix == "":
        out.mkdir(parents=True, exist_ok=True)
        chunks_path = out / "chunks.jsonl"
        refs_path = out / "refs.jsonl"
    else:
        chunks_path = out
        refs_path = out.with_name("refs.jsonl")

    all_chunks: list[Chunk] = []
    all_refs: list[dict] = []

    for result in ingest_repo(args.root):
        # refs считаются вторым проходом по файлу — после всех units
        refs_by_id = {r.unit_id: r for r in result.refs}
        store = EmbedStore(refs_by_id)

        for unit in result.units:
            chunk = Chunk.from_unit(unit, search_text=build_search_text(unit))
            # unit.embed_text уже есть из visitor; здесь добавляем mro/metaclass из refs
            chunk.embed_text = store.embed_text_for(unit)
            all_chunks.append(chunk)

        for r in result.refs:
            all_refs.append(r.as_dict())

    chunks_path.parent.mkdir(parents=True, exist_ok=True)

    with chunks_path.open("w", encoding="utf-8") as f:
        for ch in all_chunks:
            f.write(json.dumps(chunk_as_dict(ch), ensure_ascii=False) + "\n")

    with refs_path.open("w", encoding="utf-8") as f:
        for row in all_refs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"chunks: {len(all_chunks)} -> {chunks_path}", file=sys.stderr)
    print(f"refs: {len(all_refs)} -> {refs_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
