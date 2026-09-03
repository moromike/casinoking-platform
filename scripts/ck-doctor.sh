#!/usr/bin/env bash
# ck-doctor.sh — verifica che lo stack sia davvero sano. Esce 0 solo se lo e'.
set -uo pipefail
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="$RADICE/infra/docker/docker-compose.yml"
API="http://localhost:8000/api/v1/health/ready"   # come la sonda di compose
SITO="http://localhost:3000"

SCADENZA=$(( $(date +%s) + 180 )); API_OK=0; SITO_OK=0; RISPOSTA=""
while (( $(date +%s) < SCADENZA )); do
  if (( ! API_OK )); then
    RISPOSTA="$(curl -fsS "$API" 2>/dev/null || true)"
    [[ "$RISPOSTA" == *'"app":"ok"'* && "$RISPOSTA" == *'"database":"ok"'* \
       && "$RISPOSTA" == *'"redis":"ok"'* ]] && { API_OK=1; echo "[OK] backend, database e cache sani."; }
  fi
  if (( ! SITO_OK )); then
    curl -fsS -o /dev/null "$SITO" 2>/dev/null && { SITO_OK=1; echo "[OK] il sito risponde su $SITO"; }
  fi
  (( API_OK && SITO_OK )) && exit 0
  sleep 3
done
echo "[STOP] Lo stack non e' diventato sano entro 180 secondi." >&2
(( API_OK ))  || echo "       backend non sano. Ultima risposta: ${RISPOSTA:-nessuna}" >&2
(( SITO_OK )) || echo "       il sito non risponde su $SITO" >&2
docker compose -f "$COMPOSE" ps >&2
exit 1
