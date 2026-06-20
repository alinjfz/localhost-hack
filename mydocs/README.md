# Localhost Hackathon Review System

This repository is the working hub for the offline multi-device review workflow in `mydocs/the-full-plan.md`.

It now contains:

- Shared helper code reused by the review-agent:
  - [`src/agent/config.py`](/Users/ali/Desktop/Codes/localhost-hack/src/agent/config.py)
  - [`src/agent/memory.py`](/Users/ali/Desktop/Codes/localhost-hack/src/agent/memory.py)
  - [`src/agent/tracer.py`](/Users/ali/Desktop/Codes/localhost-hack/src/agent/tracer.py)
- Repo diagnostics:
  - [`diagnostics/repo_audit.py`](/Users/ali/Desktop/Codes/localhost-hack/diagnostics/repo_audit.py)
- Plan scaffolds:
  - [`review-agent/README.md`](/Users/ali/Desktop/Codes/localhost-hack/review-agent/README.md)
  - [`review-agent/setup.sh`](/Users/ali/Desktop/Codes/localhost-hack/review-agent/setup.sh)
  - [`demo-project/README.md`](/Users/ali/Desktop/Codes/localhost-hack/demo-project/README.md)
  - [`demo-project/landing-page/index.html`](/Users/ali/Desktop/Codes/localhost-hack/demo-project/landing-page/index.html)
  - [`demo-project/cli/setup.py`](/Users/ali/Desktop/Codes/localhost-hack/demo-project/cli/setup.py)
  - [`demo-project/skill/SKILL.md`](/Users/ali/Desktop/Codes/localhost-hack/demo-project/skill/SKILL.md)
  - [`reviews/README.md`](/Users/ali/Desktop/Codes/localhost-hack/reviews/README.md)

The actual review-agent pipeline now lives in `src/review_agent/` and runs on the Raspberry Pi. This README is the full setup guide for the system the plan describes.

## What The System Does

On every push from the Mac dev machines, Gitea on the Raspberry Pi:

1. Receives the push.
2. Triggers a webhook to the review-agent.
3. The review-agent checks out the pushed code.
4. It serves the demo app locally and captures a Playwright screenshot.
5. It validates the screenshot with Captur.
6. It captions the UI with Moondream via Ollama on the Pi.
7. It sends the code diff to the Pi-local `qwen2.5-coder:1.5b` model.
8. It writes `REVIEW.md` and exposes it at `/review/`.
9. It stores visual and code memory in Cognee.
10. It emits a trace to Overmind.

The demo project itself is:

- `demo-project/landing-page/index.html`
- `demo-project/cli/setup.py`
- `demo-project/skill/SKILL.md`

## Device Roles

### Mac 1

- Hardware: 16 GB unified memory
- Job: frontend work on `demo-project/landing-page/index.html`
- Purpose: author code and push to Gitea

### Mac 2

- Hardware: 24 GB unified memory
- Job: backend/CLI work on `demo-project/cli/setup.py` and `demo-project/skill/SKILL.md`
- Purpose: author code and push to Gitea

### Raspberry Pi 5

- Gitea git server
- App preview server
- Review-agent HTTP service
- Captur quality gate
- Ollama with Moondream captioning and local code review
- Cognee memory store
- Overmind trace endpoint
- Optional Phase 2 review dashboard

## Ports And URLs

These are the ports from the plan.

| Service | Device | Port | Public URL |
| --- | --- | --- | --- |
| Gitea web UI + git HTTP | RPi | 9100 | `https://raspberrypi.local/git/` |
| App preview | RPi | 9101 | `https://raspberrypi.local/preview/` |
| Review-agent webhook/API | RPi | 9102 | `https://raspberrypi.local/webhook` |
| Review dashboard | RPi | 9103 | `https://raspberrypi.local/review/` |
| Overmind trace endpoint | RPi | 9104 | internal only |
| Ollama | RPi | 11434 | `/llm` through Caddy |
| Local code review model | RPi | 11434 | `http://localhost:11434` |

## Setup Order

Follow the order below. The commands are meant to be copy-paste friendly.

1. Prepare the Raspberry Pi 5.
2. Install and configure Caddy.
3. Install and configure Gitea.
4. Clone the repo on both Macs.
5. Start the two MLX inference servers.
6. Configure the Pi review-agent environment.
7. Install review-agent dependencies on the Pi.
8. Start the review-agent.
9. Push a commit from a Mac and verify `reviews/REVIEW.md`.
10. Add the optional dashboard if you have time.

If you specifically want the Pi to do the reviewing, follow [`mydocs/pi-review-workflow.md`](/Users/ali/Desktop/Codes/localhost-hack/mydocs/pi-review-workflow.md).

## Mac Harness CLI

The Macs now use a CLI harness for writing and managing the monorepo scaffold.

Install the repo in editable mode on each Mac:

```bash
pip install -e .
```

Then use:

```bash
mac-harness init
mac-harness status
mac-harness write demo-project/landing-page/index.html --from-file /path/to/new/index.html
mac-harness write demo-project/cli/setup.py --text 'print("hello")'
```

Use `mac-harness init` first if you want the scaffold materialized from the templates.

## Raspberry Pi Setup

### 1) Install OS packages

```bash
sudo apt update
sudo apt install -y git wget curl python3-pip python3-venv chromium-browser
```

### 2) Install Caddy

Use the Pi's existing Caddy instance and internal CA. The site block should include the reverse proxies below.

```caddyfile
{
    local_certs
    email ""
}

http://10.10.0.4, http://raspberrypi.local, http://192.168.0.142 {
    redir https://{host}{uri} permanent
}

https://10.10.0.4, https://raspberrypi.local, https://192.168.0.142 {
    tls internal

    @llm_exact path /llm
    handle @llm_exact {
        redir /llm/ permanent
    }

    handle /llm* {
        reverse_proxy 127.0.0.1:11434
    }

    handle_path /git/* {
        reverse_proxy 127.0.0.1:9100 {
            header_up X-Forwarded-Proto {scheme}
            header_up X-Forwarded-Host {host}
            header_up X-Real-IP {remote_host}
        }
    }

    handle /webhook {
        reverse_proxy 127.0.0.1:9102 {
            header_up X-Forwarded-Proto {scheme}
            header_up X-Real-IP {remote_host}
        }
    }

    handle_path /preview/* {
        reverse_proxy 127.0.0.1:9101
    }

    handle_path /review/* {
        reverse_proxy 127.0.0.1:9103 {
            header_up X-Forwarded-Proto {scheme}
        }
    }
}
```

Reload Caddy:

```bash
sudo systemctl reload caddy
```

### 3) Install Gitea

```bash
sudo adduser --system --shell /bin/bash --group --home /home/git git
wget -O gitea https://dl.gitea.com/gitea/1.26.2/gitea-1.26.2-linux-arm64
chmod +x gitea
sudo mv gitea /usr/local/bin/

sudo mkdir -p /var/lib/gitea/{custom,data,log}
sudo chown -R git:git /var/lib/gitea
sudo mkdir -p /etc/gitea
sudo chown root:git /etc/gitea
sudo chmod 770 /etc/gitea
```

Create the systemd service:

```bash
sudo tee /etc/systemd/system/gitea.service <<'EOF'
[Unit]
Description=Gitea
After=network.target

[Service]
User=git
Group=git
WorkingDirectory=/var/lib/gitea
ExecStart=/usr/local/bin/gitea web --port 9100
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable --now gitea
```

In Gitea first-run setup:

- Database: SQLite
- Server URL: `https://raspberrypi.local/git/`
- Root URL: `https://raspberrypi.local/git/`
- SSH domain: `raspberrypi.local`

Update `/var/lib/gitea/custom/conf/app.ini` if needed:

```ini
[server]
ROOT_URL = https://raspberrypi.local/git/
HTTP_PORT = 9100
DOMAIN = raspberrypi.local
SSH_DOMAIN = raspberrypi.local
```

Restart Gitea:

```bash
sudo systemctl restart gitea
```

Create:

- Org: `team`
- Repo: `project`
- Webhook URL: `https://raspberrypi.local/webhook`
- Content type: `application/json`
- Trigger: push events only
- Secret: match `WEBHOOK_SECRET`

### 4) Review-Agent Environment

Copy the provided example:

```bash
cp .env.example .env
```

The important values are:

```bash
WEBHOOK_SECRET=your_secret_here
APP_PREVIEW_PORT=9101
REVIEW_AGENT_PORT=9102
DASHBOARD_PORT=9103
OVERMIND_PORT=9104
REPO_PATH=/home/git/repositories/team/project.git
CHECKOUT_PATH=/tmp/app-preview
REVIEWS_PATH=/home/pi/reviews
VISION_MODEL=moondream
CODE_REVIEW_URL_PRIMARY=http://mac2_ip:9200/v1
CODE_REVIEW_URL_FALLBACK=http://mac1_ip:9200/v1
CODE_REVIEW_MODEL=mlx-community/Qwen3.5-9B-MLX-8bit
CAPTUR_API_KEY=
```

### 5) Review-Agent Dependencies

```bash
sudo apt install -y python3-pip chromium-browser
pip install fastapi uvicorn playwright ollama cognee httpx python-dotenv
playwright install chromium
```

If you want a dedicated virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn playwright ollama cognee httpx python-dotenv
playwright install chromium
```

### 6) Run the review-agent

When the implementation exists, the process should look like this:

```bash
uvicorn review_agent.agent:app --host 0.0.0.0 --port 9102
```

The code in this repo currently only contains the shared helper modules, so the `review-agent` package still needs to be implemented around them.

## Mac Setup

### 1) Install mlx-lm

```bash
pip install mlx-lm
```

### 2) Start Mac 1

```bash
mlx_lm.server \
  --model mlx-community/Qwen3.5-9B-MLX-4bit \
  --host 0.0.0.0 \
  --port 9200
```

### 3) Start Mac 2

```bash
mlx_lm.server \
  --model mlx-community/Qwen3.5-9B-MLX-8bit \
  --host 0.0.0.0 \
  --port 9200
```

Both servers expose the OpenAI-compatible `/v1/chat/completions` API.

The review-agent should use:

```text
CODE_REVIEW_URL_PRIMARY=http://mac2_ip:9200/v1
CODE_REVIEW_URL_FALLBACK=http://mac1_ip:9200/v1
```

## Demo Project Layout

The plan expects the pushed demo content to live under `demo-project/`.

```text
demo-project/
├── landing-page/
│   └── index.html
├── cli/
│   └── setup.py
└── skill/
    └── SKILL.md
```

Current scaffolds are already present in this repo. Replace them with the actual hackathon content as you build.

## Review Pipeline

The pipeline described in the plan is:

1. Dev pushes code to Gitea.
2. Gitea POSTs to `/webhook`.
3. The review-agent receives the webhook.
4. It checks out the commit into `CHECKOUT_PATH`.
5. It serves the app on `APP_PREVIEW_PORT`.
6. It opens the page with Playwright and saves a screenshot.
7. It validates the screenshot with Captur.
8. It captions the UI with Moondream through Ollama.
9. It stores commit/screenshot/UI-element history in Cognee.
10. It computes a diff and posts it to the primary MLX server.
11. It falls back to the second Mac if the primary fails.
12. It pulls the last few visual states from Cognee for context.
13. It writes `REVIEWS_PATH/REVIEW.md`.
14. It emits an Overmind trace.

## What REVIEW.md Should Contain

The generated review file should include:

- Commit hash
- Author
- Timestamp
- Captur result
- Moondream caption
- UI elements detected
- Code review notes
- Visual history

Example structure:

```md
## Push: a3f91bc by ShawnAlisson at 14:35:02

## Visual Check
Captur: PASS
UI State: Landing page with hero section...
UI Elements: hero-section, navbar, cta-button, footer

## Code Review
- missing alt text
- viewport meta missing

## Visual History
- b2e4a1f ...
- c9d3f2e ...
- a3f91bc ...
```

## Diagnostics

The repo includes a small audit tool so you can confirm the tree matches the current plan stage:

```bash
python3 -m diagnostics
```

If it prints `Repo audit: clean`, the tracked files match the expected scaffold.

## Tests

Run the test suite with:

```bash
pytest -q
```

Current tests cover:

- settings loading from environment
- shared helper no-op behavior when optional dependencies are absent
- repository audit behavior

## Phase 2 Dashboard

The optional dashboard should eventually provide:

- `GET /` for the latest `REVIEW.md`
- `GET /history` for the screenshot timeline
- `POST /query` for natural-language recall
- `GET /screenshot/<commit>` for stored PNGs

It should listen on port `9103` and be proxied at `https://raspberrypi.local/review/`.

## Future Exo Labs Path

After the hackathon, the README can be extended with:

- Exo cluster bootstrap across both Macs
- a split-serve model
- a single `CODE_REVIEW_URL` pointing at the cluster endpoint

The plan intentionally leaves Exo as a future upgrade, not part of the MVP setup.

## Quick Verification Checklist

1. `python3 -m diagnostics` prints `Repo audit: clean`
2. `pytest -q` passes
3. Gitea is reachable at `https://raspberrypi.local/git/`
4. Webhook POSTs arrive at `https://raspberrypi.local/webhook`
5. Mac MLX servers answer on port `9200`
6. The Pi can run Playwright screenshots locally
7. The review-agent writes `REVIEWS_PATH/REVIEW.md`

## Notes On The Shared Helpers

The reusable code in `src/agent/` is intentionally small:

- `config.py` centralizes `.env` values
- `memory.py` wraps Cognee calls
- `tracer.py` wraps Overmind trace emission

The rest of the runtime from the plan belongs in `review-agent/`, which is currently scaffolded but not fully implemented.
