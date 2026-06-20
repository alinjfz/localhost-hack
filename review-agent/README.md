# review-agent

This directory is the Raspberry Pi 5 service from the plan.

It will eventually contain:

- `agent.py` for the FastAPI webhook receiver
- `screenshot.py` for Playwright captures
- `captur_validate.py` for screenshot quality checks
- `vision.py` for Moondream captions
- `code_review.py` for MLX-powered diff review
- `memory.py` for Cognee history
- `tracer.py` for Overmind traces
- `dashboard.py` for the optional review dashboard
- `config.py` for RPi settings
- `setup.sh` for one-command bootstrap

For now this folder documents the target runtime layout and the setup commands in the root README.
