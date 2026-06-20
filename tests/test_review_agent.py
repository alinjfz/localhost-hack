import json
import hmac
import hashlib

from review_agent.pipeline import (
    ReviewSummary,
    extract_payload_fields,
    render_review_markdown,
    verify_webhook_secret,
)


def test_extract_payload_fields_uses_commit_and_author():
    payload = {
        "after": "abc123",
        "ref": "refs/heads/main",
        "repository": {"full_name": "alinjfz/project"},
        "head_commit": {
            "author": {"name": "Ali"},
            "timestamp": "2026-06-20T12:34:56Z",
            "message": "feat: add page",
        },
    }

    fields = extract_payload_fields(payload)

    assert fields["commit"] == "abc123"
    assert fields["author"] == "Ali"
    assert fields["branch"] == "main"
    assert fields["repo"] == "alinjfz/project"


def test_verify_webhook_secret_accepts_valid_signature():
    body = json.dumps({"after": "abc123"}).encode("utf-8")
    secret = "topsecret"
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    assert verify_webhook_secret(secret, body, {"X-Gitea-Signature": digest}) is True


def test_verify_webhook_secret_rejects_invalid_signature():
    body = b"{}"

    assert verify_webhook_secret("topsecret", body, {"X-Gitea-Signature": "wrong"}) is False


def test_render_review_markdown_includes_core_fields():
    summary = ReviewSummary(
        commit="abc123",
        author="Ali",
        timestamp="2026-06-20T12:34:56Z",
        repo="alinjfz/project",
        branch="main",
        message="feat: add page",
        screenshot_path="/tmp/review.png",
        caption="A simple landing page with hero and button.",
        code_review="Looks good.",
        diff_files=["demo-project/landing-page/index.html"],
        diff_text="diff --git a ...",
        preview_url="http://127.0.0.1:9101/demo-project/landing-page/index.html",
    )

    markdown = render_review_markdown(summary)

    assert "abc123" in markdown
    assert "Ali" in markdown
    assert "A simple landing page" in markdown
    assert "Looks good." in markdown
    assert "demo-project/landing-page/index.html" in markdown
