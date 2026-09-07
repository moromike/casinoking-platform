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

# PERCHE' L'ENV-FILE ANCHE QUI: docker compose interpola le variabili del file
# compose PRIMA di eseguire qualunque sottocomando, anche un semplice `ps`. I
# segreti vivono cifrati e il file in chiaro non esiste, quindi senza --env-file
# l'interpolazione fallisce e questo controllo concludeva "lo stack non e' in
# piedi" mentre lo stack era sano. Il 5/09/2026 ha reso ROSSO il gate per un
# motivo che non c'entrava col codice — ed e' il modo in cui un gate perde la
# fiducia di chi lo usa. `ck-up.sh` passava gia' l'env-file: qui mancava.
ENVFILE="$("$RADICE/scripts/segreti.sh")"
# PRIMA SI CHIEDE SE DOCKER RISPONDE, POI SE LO STACK E' ACCESO. Sono due guasti
# diversi e il rimedio e' opposto. Fino al 7/09/2026 c'era un controllo solo, e
# quando un chiamante non poteva PARLARE con Docker questo script rispondeva
# "Lo stack non e' in piedi. Lancia prima ck-up.sh": una diagnosi sbagliata che
# manda a fare la cosa sbagliata. Trovato mandando Codex a lanciare un collaudo
# dal suo ambiente ristretto: lo stack era acceso e in salute, e lo script diceva
# di accenderlo. Un motore ubbidiente avrebbe lanciato ck-up.sh su uno stack gia'
# in piedi invece di dire "io a Docker non ci arrivo".
if ! docker version >/dev/null 2>&1; then
  echo "[STOP] Non riesco a parlare con Docker." >&2
  echo "       Lo stack potrebbe benissimo essere acceso: il problema e' l'accesso." >&2
  echo "       Succede a chi gira in un ambiente ristretto (sandbox di un agente," >&2
  echo "       contenitore senza il socket, utente fuori dal gruppo docker)." >&2
  echo "       NON lanciare ck-up.sh: non e' quello il guasto." >&2
  exit 3
fi
if ! docker compose -f "$COMPOSE" --env-file "$ENVFILE" ps --status running --quiet backend >/dev/null 2>&1; then
  echo "[STOP] Docker risponde, ma lo stack non e' in piedi. Lancia ./scripts/ck-up.sh" >&2
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
# PERCHE' CK_MANICHINO VALE 1 PER DIFETTO: il backend dello stack (docker-compose)
# accende il manichino di default, quindi la suite deve esercitarlo. Con il vecchio
# "${CK_MANICHINO:-}" la variabile arrivava vuota quando non esportata a mano, e i
# test del manichino si SALTAVANO tutti: la suite era verde senza aver mai provato la
# cavia che il backend espone. L'ha pescato Codex in revisione — un falso verde
# operativo. In produzione resta spento comunque (impegno MAN-05).
exec docker run --rm --network "$RETE" \
  -v "$RADICE:/repo" -w /repo \
  -e PYTHONPATH="/repo/backend" \
  -e CASINOKING_API_BASE_URL="http://backend:8000/api/v1" \
  -e CASINOKING_TEST_DATABASE_URL="postgresql://casinoking:casinoking@postgres:5432/casinoking" \
  -e CASINOKING_FRONTEND_BASE_URL="http://edge:80" \
  -e CASINOKING_PUBLIC_EDGE_BASE_URL="http://edge:80" \
  -e CASINOKING_SITE_V3_FRONTEND_BASE_URL="http://frontend-v3:3001" \
  -e CK_MANICHINO="${CK_MANICHINO:-1}" \
  -e CK_GIOCHI_INTERNI="${CK_GIOCHI_INTERNI:-on}" \
  -e CK_COLLAUDO_SECRET_KEY="collaudo-test" \
  "$IMMAGINE" \
  sh -c "pip install -q pytest pytest-xdist httpx playwright pillow 2>/dev/null; python -m pytest $(printf '%q ' "${ARGOMENTI[@]}") -p no:cacheprovider"
