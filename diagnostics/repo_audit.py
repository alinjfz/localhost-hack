"""Audit the repository for files that no longer belong in the trimmed tree."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

DEFAULT_ALLOWED_FILES = {
    ".env.example",
    ".gitignore",
    "README.md",
    "diagnostics/__init__.py",
    "diagnostics/__main__.py",
    "diagnostics/repo_audit.py",
    "demo-project/README.md",
    "demo-project/cli/setup.py",
    "demo-project/landing-page/index.html",
    "demo-project/skill/SKILL.md",
    "mydocs/the-full-plan.md",
    "pyproject.toml",
    "review-agent/README.md",
    "review-agent/setup.sh",
    "reviews/README.md",
    "src/__init__.py",
    "src/agent/__init__.py",
    "src/agent/config.py",
    "src/agent/memory.py",
    "src/agent/tracer.py",
    "tests/conftest.py",
    "tests/test_repo_audit.py",
    "tests/test_settings.py",
    "tests/test_shared_helpers.py",
}

DEFAULT_IGNORED_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
    "node_modules",
}


def iter_repo_files(root: Path, ignored_parts: Iterable[str] = DEFAULT_IGNORED_PARTS) -> list[str]:
    """Return relative file paths under *root* while skipping common cache folders."""

    ignored = set(ignored_parts)
    files: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored for part in path.parts):
            continue
        files.append(path.relative_to(root).as_posix())

    return sorted(files)


def find_unexpected_files(
    root: Path,
    allowed_files: set[str] = DEFAULT_ALLOWED_FILES,
    ignored_parts: Iterable[str] = DEFAULT_IGNORED_PARTS,
) -> list[str]:
    """Return files that are still present but are not part of the trimmed repo."""

    present = iter_repo_files(root, ignored_parts=ignored_parts)
    return [path for path in present if path not in allowed_files]


def render_report(root: Path) -> str:
    unexpected = find_unexpected_files(root)
    if not unexpected:
        return "Repo audit: clean"

    lines = ["Repo audit: unexpected files found"]
    lines.extend(f"- {path}" for path in unexpected)
    return "\n".join(lines)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = render_report(root)
    print(report)
    return 0 if report == "Repo audit: clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
