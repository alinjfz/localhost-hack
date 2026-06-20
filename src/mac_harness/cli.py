"""Command-line harness for the Mac developers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Iterable


DEFAULT_FILES = {
    "demo-project/landing-page/index.html",
    "demo-project/cli/setup.py",
    "demo-project/skill/SKILL.md",
    "demo-project/README.md",
    "review-agent/README.md",
    "review-agent/setup.sh",
    "reviews/README.md",
    ".env.example",
    "mydocs/README.md",
    "mydocs/the-full-plan.md",
}


@dataclass(frozen=True, slots=True)
class StatusRow:
    path: str
    exists: bool


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def init_workspace(root: Path | None = None) -> list[Path]:
    """Ensure the monorepo scaffold exists for the demo."""

    repo = root or repo_root()
    created: list[Path] = []

    for rel in [
        "demo-project/landing-page",
        "demo-project/cli",
        "demo-project/skill",
        "review-agent",
        "reviews",
    ]:
        (repo / rel).mkdir(parents=True, exist_ok=True)

    files = {
        "demo-project/README.md": dedent(
            """\
            # demo-project

            Monorepo scaffold for the hackathon demo.
            """
        ),
        "demo-project/landing-page/index.html": dedent(
            """\
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <title>Demo Landing Page</title>
              </head>
              <body>
                <main>
                  <h1>Landing page scaffold</h1>
                </main>
              </body>
            </html>
            """
        ),
        "demo-project/cli/setup.py": dedent(
            '''\
            """CLI scaffold for the demo."""

            if __name__ == "__main__":
                print("demo-project CLI scaffold")
            '''
        ),
        "demo-project/skill/SKILL.md": dedent(
            """\
            # Demo Skill

            Placeholder for the Claude Code skill.
            """
        ),
        "review-agent/README.md": dedent(
            """\
            # review-agent

            Raspberry Pi 5 review service scaffold.
            """
        ),
        "review-agent/setup.sh": dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            echo "Review-agent scaffold only for now."
            """
        ),
        "reviews/README.md": dedent(
            """\
            # reviews

            Review output and screenshots will live here.
            """
        ),
    }

    for rel, content in files.items():
        path = repo / rel
        if not path.exists():
            ensure_parent(path)
            path.write_text(content, encoding="utf-8")
            created.append(path)

    return created


def status_rows(root: Path | None = None, files: Iterable[str] = DEFAULT_FILES) -> list[StatusRow]:
    repo = root or repo_root()
    return [StatusRow(path=rel, exists=(repo / rel).exists()) for rel in files]


def write_file(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def _cmd_init(args: argparse.Namespace) -> int:
    created = init_workspace(Path(args.root) if args.root else None)
    if created:
        for path in created:
            print(f"created {path.relative_to(repo_root())}")
    else:
        print("workspace already initialized")
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    rows = status_rows(Path(args.root) if args.root else None)
    for row in rows:
        marker = "ok" if row.exists else "missing"
        print(f"{marker:7} {row.path}")
    missing = sum(not row.exists for row in rows)
    print(f"\n{missing} missing")
    return 0 if missing == 0 else 1


def _cmd_write(args: argparse.Namespace) -> int:
    repo = Path(args.root) if args.root else repo_root()
    target = repo / args.path
    content = Path(args.from_file).read_text(encoding="utf-8") if args.from_file else args.text
    if content is None:
        content = ""
    write_file(target, content)
    print(f"wrote {target.relative_to(repo)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mac-harness", description="Mac-side demo harness")
    parser.add_argument("--root", help="Override repo root", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="Initialize the monorepo scaffold")
    init_parser.set_defaults(func=_cmd_init)

    status_parser = sub.add_parser("status", help="Show scaffold status")
    status_parser.set_defaults(func=_cmd_status)

    write_parser = sub.add_parser("write", help="Write a file in the repo")
    write_parser.add_argument("path", help="Relative path to write")
    write_parser.add_argument("--text", help="Inline content to write", default=None)
    write_parser.add_argument("--from-file", help="Read content from a file", default=None)
    write_parser.set_defaults(func=_cmd_write)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)

