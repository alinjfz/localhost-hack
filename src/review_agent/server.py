"""Minimal HTTP server for the Pi review-agent."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar

from .config import get_settings
from .pipeline import ReviewPipeline


PIPELINE = ReviewPipeline(get_settings())


class ReviewHandler(BaseHTTPRequestHandler):
    server_version: ClassVar[str] = "review-agent/0.1"

    def _send(self, status: HTTPStatus, body: str, content_type: str = "text/plain; charset=utf-8") -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            payload = json.dumps(PIPELINE.as_status(), indent=2)
            self._send(HTTPStatus.OK, payload, "application/json; charset=utf-8")
            return
        if self.path in {"/", "/review", "/review/"}:
            summary = PIPELINE.latest_summary
            if not summary:
                self._send(HTTPStatus.OK, "No review has been generated yet.")
                return
            from .pipeline import render_review_html

            self._send(HTTPStatus.OK, render_review_html(summary), "text/html; charset=utf-8")
            return
        if self.path in {"/raw", "/review/raw"}:
            summary = PIPELINE.latest_summary
            if not summary:
                self._send(HTTPStatus.OK, "No review has been generated yet.")
                return
            from .pipeline import render_review_markdown

            self._send(HTTPStatus.OK, render_review_markdown(summary))
            return
        self._send(HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/webhook":
            self._send(HTTPStatus.NOT_FOUND, "not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        headers = {k: v for k, v in self.headers.items()}
        status, message = PIPELINE.handle_webhook(body, headers)
        self._send(HTTPStatus(status), message)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> int:
    settings = get_settings()
    server = ThreadingHTTPServer((settings.review_agent_host, settings.review_agent_port), ReviewHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        PIPELINE.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
