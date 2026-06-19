"""Index policy: skip rules, pip module names, namespace classification."""

from __future__ import annotations

from pathlib import Path

SKIP_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".pytest_cache",
    "dist-info",
    "egg-info",
    ".tox",
    ".mypy_cache",
    "dist",
    "build",
    "target",
    ".eggs",
    "env",
}

SKIP_PACKAGE_PREFIXES = ("pip", "setuptools", "wheel", "pkg_resources")
SKIP_FILE_SUFFIXES = (".pyc", ".pyo", ".exe", ".pem", ".typed")

INDEXABLE_EXTENSIONS = frozenset(
    {".py", ".rs", ".js", ".jsx", ".ts", ".tsx", ".html", ".htm"}
)


def find_site_packages(root: Path) -> Path | None:
    for p in (root, *root.parents):
        if p.name == "site-packages" and p.is_dir():
            return p
    return None


def resolve_package(
    root: Path, file_path: Path, site_packages: Path | None
) -> str | None:
    if site_packages and site_packages in file_path.parents:
        rel = file_path.relative_to(site_packages)
        if rel.parts:
            name = rel.parts[0]
            return name.split("-")[0] if "-" in name else name
    if (root / "__init__.py").is_file():
        return root.name
    return None


def module_name(package: str | None, rel_path: str) -> str:
    """dramatiq/brokers/redis.py → dramatiq.brokers.redis"""
    p = Path(rel_path)
    parts = list(p.parts)
    if parts and parts[-1] == "__init__.py":
        parts = parts[:-1]
    elif parts:
        parts[-1] = Path(parts[-1]).stem

    if package:
        mod = parts if parts and parts[0] == package else [package, *parts]
    else:
        mod = parts
    return ".".join(mod) if mod else (package or "module")


def classify_namespace(
    path: Path,
    package: str | None,
    *,
    root: Path,
    site_packages: Path | None,
) -> str:
    rel = path.as_posix()
    if "/tests/" in rel or rel.startswith("tests/") or "/test_" in rel:
        return "tests"
    if package and (
        (site_packages and site_packages in path.parents)
        or (root / "__init__.py").is_file()
    ):
        return "pip"
    if any(p in ("docs", "doc", "documentation") for p in path.parts):
        return "docs"
    return "code"


def should_index(
    path: Path,
    *,
    root: Path,
    site_packages: Path | None,
    only_packages: set[str] | None,
    extension: str | None = None,
) -> bool:
    if SKIP_DIR_NAMES & set(path.parts):
        return False
    ext = extension if extension is not None else path.suffix.lower()
    if ext not in INDEXABLE_EXTENSIONS:
        return False
    if path.suffix in SKIP_FILE_SUFFIXES:
        return False
    posix = path.as_posix()
    if "/lib64/" in posix or "/licenses/" in posix:
        return False

    if "site-packages" in path.parts:
        idx = path.parts.index("site-packages")
        if idx + 1 < len(path.parts):
            if path.parts[idx + 1].split("-")[0] in SKIP_PACKAGE_PREFIXES:
                return False

    if only_packages and ext == ".py":
        pkg = resolve_package(root, path, site_packages)
        if not pkg or pkg not in only_packages:
            return False
    return True
