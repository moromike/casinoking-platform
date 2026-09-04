#!/usr/bin/env bash
# ck-test.sh — lancia la suite dentro un contenitore usa-e-getta.
#
# PERCHE' NON SI LANCIA SULLA MACCHINA: la suite e' scritta per Python 3.12 e la
# macchina ha il 3.10; tests/conftest.py:24 usa una sintassi che il 3.10 non
# compila nemmeno. Per anni la procedura canonica e' stata PowerShell su Windows,
# e su Linux non era ricostruibile. Questo script e' la procedura, su Linux.
#
#   ./scripts/ck-test.sh                      # la suite ordinaria
#   ./scripts/ck-test.sh tests/contract -q    # solo una parte
set -euo pipefail

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="$RADICE/infra/docker/docker-compose.yml"
RETE="casinoking_default"
IMMAGINE="casinoking-backend:latest"

if ! docker compose -f "$COMPOSE" ps --status running --quiet backend >/dev/null 2>&1; then
  echo "[STOP] Lo stack non e' in piedi. Lancia prima ./scripts/ck-up.sh" >&2
  exit 1
fi

ARGOMENTI=("$@")
if [[ ${#ARGOMENTI[@]} -eq 0 ]]; then
  ARGOMENTI=(-m "not browser_smoke and not visual and not stress and not destructive" -q)
fi

# PERCHE' PYTHONPATH: l'immagine installa il backend in modo editabile da
# /app/backend, cioe' dal codice copiato dentro l'immagine al momento della
# build. Senza questa variabile i test girerebbero sul codice VECCHIO e un
# modulo nuovo (es. games/manichino) risulterebbe non importabile anche se
# presente nell'albero montato. /repo/backend ha la precedenza e i test
# eseguono il codice della working copy.
#
# PERCHE' CK_MANICHINO: il manichino (cavia contabile) esiste solo se
# l'interruttore arriva dentro il container di test; fuori resta spento.
exec docker run --rm --network "$RETE" \
  -v "$RADICE:/repo" -w /repo \
  -e PYTHONPATH="/repo/backend" \
  -e CASINOKING_API_BASE_URL="http://backend:8000/api/v1" \
  -e CASINOKING_TEST_DATABASE_URL="postgresql://casinoking:casinoking@postgres:5432/casinoking" \
  -e CASINOKING_FRONTEND_BASE_URL="http://edge:80" \
  -e CASINOKING_PUBLIC_EDGE_BASE_URL="http://edge:80" \
  -e CASINOKING_SITE_V3_FRONTEND_BASE_URL="http://frontend-v3:3001" \
  -e CK_MANICHINO="${CK_MANICHINO:-}" \
  "$IMMAGINE" \
  sh -c "pip install -q pytest pytest-xdist httpx playwright pillow 2>/dev/null; python -m pytest $(printf '%q ' "${ARGOMENTI[@]}") -p no:cacheprovider"
