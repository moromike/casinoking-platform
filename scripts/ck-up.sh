#!/usr/bin/env bash
# ck-up.sh — avvia l'intero stack locale. Gemello Linux di ck-up.ps1.
set -euo pipefail
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="$RADICE/infra/docker/docker-compose.yml"
ENVFILE="$RADICE/infra/docker/.env"
[[ -f "$COMPOSE" ]] || { echo "[STOP] File compose non trovato: $COMPOSE" >&2; exit 1; }
[[ -f "$ENVFILE" ]] || { echo "[STOP] File d'ambiente non trovato: $ENVFILE" >&2; exit 1; }
echo "[INFO] Avvio dello stack con ricostruzione..."
docker compose -f "$COMPOSE" --env-file "$ENVFILE" up -d --build
echo "[INFO] Attendo che i servizi rispondano..."
"$RADICE/scripts/ck-doctor.sh"
