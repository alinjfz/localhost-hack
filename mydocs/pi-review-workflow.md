# Pi Review Workflow

This guide explains how to make the Raspberry Pi review the code after you commit from your Mac.

The key idea is:

- **Macs write code**
- **Gitea stores the repo**
- **The Raspberry Pi reviews pushes**
- **The Pi, not the Mac, runs the review pipeline**

If `/review` is not working on the Pi yet, that usually means the review-agent service is not implemented, not running, or not wired to Caddy correctly. This file is the exact setup path.

## Goal

You want this flow:

1. Edit code on your Mac.
2. Commit and push to Gitea.
3. Gitea sends a webhook to the Pi.
4. The Pi checks out the pushed revision.
5. The Pi runs a lightweight vision model to caption the page.
6. The Pi runs a lightweight code review model to review the diff.
7. The Pi writes `reviews/REVIEW.md`.
8. The Pi serves review output at `/review/`.

The Mac does **not** perform the final review step.

## What Runs Where

### On the Mac

- `mac-harness` CLI
- your editor
- optional local git hooks
- optional local preview while you are working

### On the Raspberry Pi

- Gitea
- Caddy
- review-agent service
- preview server
- Ollama
- vision model
- code review model
- review output storage

## Feasibility

Yes, this is feasible if the Pi uses **lightweight open-source models**.

Recommended Pi models:

- **Vision:** `moondream`
- **Code review:** `qwen2.5-coder:1.5b` or `qwen2.5-coder:3b`

Why this works:

- `moondream` is small enough for Pi use and is good for screenshot captions.
- `qwen2.5-coder:1.5b` is the safest low-RAM review model.
- `qwen2.5-coder:3b` is still lightweight and usually gives better review quality.

If the Pi gets slow, use the `1.5b` code model first.

## Monorepo Layout

Use one repo for everything:

```text
repo/
├── demo-project/
│   ├── landing-page/
│   ├── cli/
│   └── skill/
├── review-agent/
├── reviews/
├── diagnostics/
├── src/
└── mydocs/
```

### Purpose of each folder

- `demo-project/`: the actual app and tools you are building
- `review-agent/`: Pi-side webhook, screenshot, vision, and review pipeline
- `reviews/`: output files written by the Pi
- `src/`: shared helper code
- `mydocs/`: setup and workflow docs

## Required Pi Services

### Gitea

Gitea receives pushes from the Mac and triggers the webhook.

### Caddy

Caddy proxies public URLs to local services on the Pi.

You need these routes:

- `/git/` -> Gitea
- `/webhook` -> review-agent
- `/preview/` -> app preview server
- `/review/` -> review dashboard or review output

### Review Agent

This is the Pi service that performs the review.

It should:

1. Receive webhook events.
2. Verify the webhook secret.
3. Checkout the repository at the pushed commit.
4. Start or update the local preview server.
5. Capture a screenshot.
6. Run the vision caption model.
7. Run the code review model.
8. Write `REVIEW.md`.
9. Save screenshots under `reviews/screenshots/`.

### Ollama

Ollama runs the local open-source models.

Recommended models:

- `moondream` for vision
- `qwen2.5-coder:1.5b` for code review
- `qwen2.5-coder:3b` if the Pi has enough headroom

## Mac Harness

The Mac harness is a CLI that helps you write files and push the monorepo.

Install it on the Mac:

```bash
pip install -e .
```

Useful commands:

```bash
mac-harness init
mac-harness status
mac-harness write demo-project/landing-page/index.html --text "<html>...</html>"
mac-harness write demo-project/cli/setup.py --text 'print("hello")'
git add .
git commit -m "update demo"
git push
```

The harness is only for authoring and organizing files on the Mac. It does **not** replace Pi review.

## Pi Setup Checklist

### 1) Install dependencies

```bash
sudo apt update
sudo apt install -y git wget curl python3-pip python3-venv chromium-browser
```

### 2) Install Ollama

Install Ollama on the Pi using the official installer for your Pi OS release.

Then pull the models:

```bash
ollama pull moondream
ollama pull qwen2.5-coder:1.5b
```

If the Pi is strong enough, you can try:

```bash
ollama pull qwen2.5-coder:3b
```

### 3) Configure Gitea

Use:

- `Database Type`: `SQLite3`
- `Server Domain`: `raspberrypi.local`
- `Gitea HTTP Listen Port`: `9100`
- `Gitea Base URL`: `https://raspberrypi.local/git/`

Create:

- Org: `team`
- Repo: `project`
- Webhook URL: `https://raspberrypi.local/webhook`
- Content type: `application/json`
- Trigger: push events only
- Secret: same value as `WEBHOOK_SECRET`

### 4) Configure Caddy

Your Pi needs reverse proxies for the routes above.

The important one for this workflow is:

```caddyfile
handle /webhook {
    reverse_proxy 127.0.0.1:9102
}
```

If `/review` is broken, it usually means:

- the reverse proxy is missing
- the review-agent is not running
- the review-agent is returning an error

### 5) Configure the review-agent environment

Use an `.env` file on the Pi with values like:

```bash
WEBHOOK_SECRET=your_secret_here
APP_PREVIEW_PORT=9101
REVIEW_AGENT_PORT=9102
DASHBOARD_PORT=9103
REPO_PATH=/home/git/repositories/team/project.git
CHECKOUT_PATH=/tmp/app-preview
REVIEWS_PATH=/home/pi/reviews
VISION_MODEL=moondream
CODE_REVIEW_MODEL=qwen2.5-coder:1.5b
OLLAMA_BASE_URL=http://localhost:11434
```

If you keep everything on the Pi, the review-agent can talk to Ollama locally.

### 6) Run the review-agent

The review-agent is the Pi process that makes `/review` useful.

The finished service should:

- listen on port `9102`
- accept webhooks at `/webhook`
- write reviews into `/home/pi/reviews`
- expose review output under `/review/`

If you installed this repo on the Pi, start it with:

```bash
pip install -e .
review-agent
```

or:

```bash
python -m review_agent
```

## What To Build In `src/review_agent/`

The Pi package now lives under `src/review_agent/` and includes:

- `server.py` for the HTTP handler
- `pipeline.py` for checkout, screenshot, caption, and review logic
- `config.py` for Pi settings
- `__main__.py` for `python -m review_agent`

The core behavior is:

1. `server.py` listens for `/webhook`
2. `pipeline.py` verifies the signature
3. `pipeline.py` checks out the commit
4. `pipeline.py` launches the preview server
5. `pipeline.py` captures the screenshot
6. `pipeline.py` captions the screenshot with `moondream`
7. `pipeline.py` reviews the diff with `qwen2.5-coder:1.5b`
8. `pipeline.py` writes `REVIEW.md` and `REVIEW.html`

## Why `/review` May Not Work Yet

Common reasons:

1. The review-agent service does not exist yet.
2. The review-agent is not running.
3. Caddy is not proxying `/review/` correctly.
4. The Pi cannot read the repo or write to `reviews/`.
5. The code review model is missing.
6. The vision model is missing.
7. The webhook secret does not match.

## Debug Order

When `/review` fails, check in this order:

1. `systemctl status gitea`
2. `systemctl status caddy`
3. `systemctl status review-agent`
4. `curl -k https://raspberrypi.local/webhook`
5. `curl -k https://raspberrypi.local/review/`
6. `ollama list`
7. `ls -la /home/pi/reviews`
8. `journalctl -u review-agent -n 50 --no-pager`

## End-to-End Test

Once the Pi-side service exists, test like this:

1. Modify `demo-project/landing-page/index.html` on your Mac.
2. Commit the change.
3. Push to Gitea.
4. Wait for the webhook.
5. Confirm `REVIEW.md` is written on the Pi.
6. Open `https://raspberrypi.local/review/`.

If that works, the collaboration loop is complete.

## Recommended Minimal Setup

If you want the simplest setup that still works:

- Pi: Gitea + review-agent + `moondream` + `qwen2.5-coder:1.5b`
- Mac: `mac-harness` CLI
- One repo monorepo
- Gitea webhook pointing to Pi only

This is the smallest version that still gives you:

- commit on Mac
- review on Pi
- local vision captions
- local code review
