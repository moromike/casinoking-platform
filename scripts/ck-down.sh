#!/usr/bin/env bash
# ck-down.sh — ferma lo stack. Gemello Linux di ck-down.ps1.
set -euo pipefail
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docker compose -f "$RADICE/infra/docker/docker-compose.yml" down
echo "[OK] Stack fermato."
