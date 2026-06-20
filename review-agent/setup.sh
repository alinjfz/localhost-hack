#!/usr/bin/env bash
set -euo pipefail

echo "This repository ships the review-agent code under src/review_agent."
echo "On the Raspberry Pi, run:"
echo "  cp .env.example .env"
echo "  pip install -e ."
echo "  review-agent"
