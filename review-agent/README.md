# review-agent

This folder documents the Raspberry Pi 5 service from the plan.

The actual runnable code now lives under [`src/review_agent/`](/Users/ali/Desktop/Codes/localhost-hack/src/review_agent).

## What it provides

- `review-agent` console command
- `python -m review_agent` entrypoint
- `/webhook` POST handler
- `/review` HTML output
- `/review/raw` markdown output
- screenshot capture via Chromium
- local vision captioning through Ollama
- local code review through Ollama

## Pi-first model choice

- Vision: `moondream`
- Code review: `qwen2.5-coder:1.5b`

## Run

After copying the repo to the Pi and setting `.env`:

```bash
pip install -e .
review-agent
```

Or:

```bash
python -m review_agent
```

The Pi should then listen on `REVIEW_AGENT_PORT` and expose the review routes through Caddy.
