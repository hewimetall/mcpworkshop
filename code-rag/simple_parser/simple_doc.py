"""Simple per-language documentation extraction (no tree-sitter queries)."""

from __future__ import annotations

import ast
import re

_JS_LANGS = frozenset({"javascript", "typescript", "tsx"})


def extract_doc(
    language: str,
    source_lines: list[str],
    start_line: int,
    content: str,
) -> str:
    if language == "python":
        return _doc_python(content)
    if language == "rust":
        return _doc_rust(source_lines, start_line)
    if language in _JS_LANGS:
        return _doc_js_ts(source_lines, start_line)
    return ""


def _doc_python(content: str) -> str:
    try:
        tree = ast.parse(content)
        if tree.body:
            return ast.get_docstring(tree.body[0]) or ""
    except SyntaxError:
        pass
    return ""


def _doc_rust(source_lines: list[str], start_line: int) -> str:
    docs: list[str] = []
    i = start_line - 1
    while i >= 0:
        line = source_lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#["):
            i -= 1
            continue
        if stripped.startswith("///") or stripped.startswith("//!"):
            docs.append(re.sub(r"^[/!]+\s?", "", stripped))
            i -= 1
            continue
        break
    return "\n".join(reversed(docs))


def _doc_js_ts(source_lines: list[str], start_line: int) -> str:
    i = start_line - 1
    while i >= 0 and not source_lines[i].strip():
        i -= 1
    if i < 0:
        return ""

    block = _block_comment_above(source_lines, i)
    if block is not None:
        return block

    lines: list[str] = []
    while i >= 0:
        stripped = source_lines[i].strip()
        if stripped.startswith("//"):
            lines.append(stripped[2:].strip())
            i -= 1
            continue
        if not stripped:
            i -= 1
            continue
        break
    return "\n".join(reversed(lines))


def _block_comment_above(source_lines: list[str], end_idx: int) -> str | None:
    """Return JSDoc-style block immediately above end_idx, or None."""
    i = end_idx
    while i >= 0 and not source_lines[i].strip():
        i -= 1
    if i < 0:
        return None

    close = source_lines[i].strip()
    if not close.endswith("*/"):
        return None

    start = i
    while start >= 0:
        if "/**" in source_lines[start]:
            break
        start -= 1
    if start < 0:
        return None

    block = "\n".join(source_lines[start : i + 1])
    inner = re.sub(r"^/\*\*?", "", block, count=1)
    inner = re.sub(r"\*/\s*$", "", inner)
    lines = []
    for line in inner.splitlines():
        line = re.sub(r"^\s*\*\s?", "", line)
        lines.append(line.rstrip())
    return "\n".join(lines).strip()
