"""Build embed_text and search_text for chunks."""

from __future__ import annotations

from .models import CodeUnit

EMBED_MAX_LEN = 400


def build_embed_text(unit: CodeUnit) -> str:
    """Short signal for embedding: no full body."""
    doc = unit.doc
    signature = unit.content.splitlines()[0].strip() if unit.content else ""
    chain_str = ".".join(unit.class_chain) if unit.class_chain else ""
    context = f"in {chain_str}" if chain_str else f"in {unit.module}"
    lines = [
        f"[{unit.language}] {unit.role} `{unit.symbol}` {context} | path: {unit.path}",
    ]
    if doc:
        lines.append(doc)
    elif signature:
        lines.append(signature)
    calls_str = ", ".join(unit.calls[:10]) if unit.calls else "none"
    lines.append(f"calls: {calls_str}")
    return "\n".join(lines)[:EMBED_MAX_LEN]


def build_search_text(unit: CodeUnit) -> str:
    """BM25-oriented text without refs or full body duplication."""
    lines = [
        f"[namespace:{unit.namespace}]",
        f"qualified_name:{unit.qualified_name}",
        f"module:{unit.module}",
        f"path:{unit.path}",
        f"role:{unit.role}",
    ]
    if unit.package:
        lines.append(f"package:{unit.package}")
    if unit.class_chain:
        lines.append(f"class:{'.'.join(unit.class_chain)}")
    sig = unit.content.splitlines()[0].strip() if unit.content else ""
    if sig:
        lines.append(sig)
    return "\n".join(lines)
