"""Core review pipeline for the Raspberry Pi service."""

from __future__ import annotations

import base64
from dataclasses import dataclass, asdict
from datetime import datetime
from html import escape
import hmac
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import threading
import time
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .config import ReviewSettings, get_settings


@dataclass(slots=True)
class ReviewSummary:
    commit: str
    author: str
    timestamp: str
    repo: str
    branch: str
    message: str
    screenshot_path: str
    caption: str
    code_review: str
    diff_files: list[str]
    diff_text: str
    preview_url: str


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _run(cmd: list[str], *, cwd: str | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def _git(settings: ReviewSettings, *args: str, timeout: int | None = 30) -> str:
    cmd = ["git", "--git-dir", settings.repo_path, *args]
    return _run(cmd, timeout=timeout).stdout.strip()


def extract_payload_fields(payload: dict[str, Any]) -> dict[str, str]:
    head_commit = payload.get("head_commit") or {}
    repository = payload.get("repository") or {}
    pusher = payload.get("pusher") or {}
    branch = (payload.get("ref") or "").split("/")[-1] if payload.get("ref") else "unknown"
    commit = payload.get("after") or head_commit.get("id") or ""
    author = (
        (head_commit.get("author") or {}).get("name")
        or pusher.get("name")
        or payload.get("sender", {}).get("login")
        or "unknown"
    )
    timestamp = head_commit.get("timestamp") or datetime.utcnow().isoformat() + "Z"
    message = head_commit.get("message") or ""
    return {
        "commit": commit,
        "author": author,
        "timestamp": timestamp,
        "repo": repository.get("full_name") or repository.get("name") or "unknown",
        "branch": branch,
        "message": message,
    }


def verify_webhook_secret(secret: str, body: bytes, headers: dict[str, str]) -> bool:
    if not secret:
        return True

    signature = headers.get("x-gitea-signature") or headers.get("X-Gitea-Signature")
    if signature:
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature.strip(), digest)

    token = headers.get("x-webhook-secret") or headers.get("X-Webhook-Secret")
    if token:
        return hmac.compare_digest(token.strip(), secret)

    return False


def prepare_checkout(settings: ReviewSettings, commit: str) -> Path:
    checkout_root = Path(settings.checkout_path)
    _ensure_dir(checkout_root)
    for child in checkout_root.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    archive = subprocess.run(
        ["git", "--git-dir", settings.repo_path, "archive", commit],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["tar", "-x", "-C", str(checkout_root)],
        input=archive.stdout,
        check=True,
        capture_output=True,
    )
    return checkout_root


class PreviewServer:
    def __init__(self, settings: ReviewSettings):
        self.settings = settings
        self._proc: subprocess.Popen[str] | None = None

    def start(self, root: Path) -> None:
        self.stop()
        self._proc = subprocess.Popen(
            [
                "python3",
                "-m",
                "http.server",
                str(self.settings.app_preview_port),
                "--directory",
                str(root),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        time.sleep(1.0)

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None


def capture_screenshot(url: str, output_path: Path) -> None:
    _ensure_dir(output_path.parent)
    browser = shutil.which("chromium-browser") or shutil.which("chromium") or shutil.which("google-chrome")
    if not browser:
        raise RuntimeError("No Chromium browser found for screenshot capture")

    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--window-size=1440,1600",
        f"--screenshot={output_path}",
        url,
    ]
    _run(cmd, timeout=60)


def ollama_generate(base_url: str, model: str, prompt: str, images: list[str] | None = None) -> str:
    payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
    if images:
        payload["images"] = images
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        urljoin(base_url.rstrip("/") + "/", "api/generate"),
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body.get("response", "").strip()


def caption_screenshot(settings: ReviewSettings, screenshot_path: Path) -> str:
    image_b64 = base64.b64encode(screenshot_path.read_bytes()).decode("ascii")
    prompt = (
        "Describe this UI screenshot in 2-4 concise sentences. "
        "List visible UI elements, layout issues, and notable colors if present."
    )
    try:
        return ollama_generate(settings.ollama_base_url, settings.vision_model, prompt, [image_b64])
    except Exception as exc:
        return f"Vision caption unavailable: {exc}"


def get_diff_files(commit: str, settings: ReviewSettings) -> list[str]:
    parent = _git(settings, "rev-list", "--parents", "-n", "1", commit).split()[1:]
    if not parent:
        return []
    diff = _git(settings, "diff", "--name-only", f"{parent[0]}..{commit}")
    return [line for line in diff.splitlines() if line]


def get_diff_text(commit: str, settings: ReviewSettings) -> str:
    parent = _git(settings, "rev-list", "--parents", "-n", "1", commit).split()[1:]
    if not parent:
        return _git(settings, "show", "--format=", commit)
    return _git(settings, "diff", f"{parent[0]}..{commit}", timeout=60)


def review_diff(settings: ReviewSettings, diff_text: str) -> str:
    prompt = (
        "You are an expert code reviewer for an offline Raspberry Pi review agent. "
        "Review this git diff concisely. "
        "Call out bugs, security issues, missing error handling, and accessibility issues. "
        "If there are no issues, say so clearly. Keep it under 300 words.\n\n"
        f"{diff_text}"
    )
    try:
        return ollama_generate(settings.ollama_base_url, settings.code_review_model, prompt)
    except Exception as exc:
        return f"Code review unavailable: {exc}"


def render_review_markdown(summary: ReviewSummary) -> str:
    files = "\n".join(f"- `{path}`" for path in summary.diff_files) if summary.diff_files else "- None"
    return f"""# Review

## Push

- Commit: `{summary.commit}`
- Author: `{summary.author}`
- Timestamp: `{summary.timestamp}`
- Repo: `{summary.repo}`
- Branch: `{summary.branch}`
- Message: {summary.message or "No commit message"}

## Visual Check

- Screenshot: `{summary.screenshot_path}`
- Caption: {summary.caption or "No caption"}
- Preview URL: {summary.preview_url}

## Code Review

{summary.code_review or "No review available"}

## Changed Files

{files}
"""


def render_review_html(summary: ReviewSummary) -> str:
    markdown = render_review_markdown(summary)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Review</title>
    <style>
      body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }}
      pre {{ background: #111; color: #eee; padding: 1rem; overflow: auto; border-radius: 12px; }}
    </style>
  </head>
  <body>
    <h1>Latest Review</h1>
    <p><a href="/review/raw">Raw markdown</a></p>
    <pre>{escape(markdown)}</pre>
  </body>
</html>
"""


class ReviewPipeline:
    def __init__(self, settings: ReviewSettings | None = None):
        self.settings = settings or get_settings()
        self.preview_server = PreviewServer(self.settings)
        self._latest_summary: ReviewSummary | None = None
        self._lock = threading.Lock()

    @property
    def latest_summary(self) -> ReviewSummary | None:
        return self._latest_summary

    def handle_webhook(self, body: bytes, headers: dict[str, str]) -> tuple[int, str]:
        if not verify_webhook_secret(self.settings.webhook_secret, body, headers):
            return 401, "invalid webhook secret"

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return 400, "invalid json payload"

        fields = extract_payload_fields(payload)
        if not fields["commit"]:
            return 400, "missing commit sha"

        try:
            summary = self.run_review(fields, payload)
        except Exception as exc:
            return 500, f"review failed: {exc}"

        self._latest_summary = summary
        return 200, "review complete"

    def run_review(self, fields: dict[str, str], payload: dict[str, Any]) -> ReviewSummary:
        commit = fields["commit"]
        repo_root = prepare_checkout(self.settings, commit)
        preview_root = repo_root
        self.preview_server.start(preview_root)

        preview_url = f"http://127.0.0.1:{self.settings.app_preview_port}/{self.settings.preview_entrypoint}"
        screenshot_dir = Path(self.settings.reviews_path) / "screenshots"
        screenshot_path = screenshot_dir / f"{commit[:12]}.png"
        capture_screenshot(preview_url, screenshot_path)

        caption = caption_screenshot(self.settings, screenshot_path)
        diff_files = get_diff_files(commit, self.settings)
        diff_text = get_diff_text(commit, self.settings)
        code_review = review_diff(self.settings, diff_text)

        summary = ReviewSummary(
            commit=commit,
            author=fields["author"],
            timestamp=fields["timestamp"],
            repo=fields["repo"],
            branch=fields["branch"],
            message=fields["message"],
            screenshot_path=str(screenshot_path),
            caption=caption,
            code_review=code_review,
            diff_files=diff_files,
            diff_text=diff_text,
            preview_url=preview_url,
        )
        self.write_review(summary)
        return summary

    def write_review(self, summary: ReviewSummary) -> None:
        reviews_root = Path(self.settings.reviews_path)
        _ensure_dir(reviews_root)
        markdown = render_review_markdown(summary)
        (reviews_root / "REVIEW.md").write_text(markdown, encoding="utf-8")
        (reviews_root / "REVIEW.html").write_text(render_review_html(summary), encoding="utf-8")

    def as_status(self) -> dict[str, Any]:
        summary = self._latest_summary
        if not summary:
            return {"status": "idle"}
        return {"status": "ready", "latest": asdict(summary)}

    def shutdown(self) -> None:
        self.preview_server.stop()
