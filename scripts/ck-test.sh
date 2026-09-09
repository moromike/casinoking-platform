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
# L'immagine si puo' scavalcare: i collaudi di schermo girano su
# casinoking-collaudi-browser:latest, che ha il browser e le sue 25 librerie.
# Il prodotto non le paga.
IMMAGINE="${CK_IMMAGINE:-casinoking-backend:latest}"

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

# LE DUE CORSIE. Fino al 9/09/2026 esisteva solo la prima, e nessuno aveva scritto che
# la seconda esiste: [GENERATO] 249 collaudi su 947 (il 26%) venivano DESELEZIONATI in
# silenzio. Non erano spenti per una libreria mancante — quello e' un altro problema —
# erano esclusi dalla riga di comando, e sarebbero rimasti esclusi anche installando tutto.
#
#   ./scripts/ck-test.sh                  corsia ORDINARIA (quella di sempre)
#   ./scripts/ck-test.sh --corsia-esclusi SOLO i 249: schermo, visivi, carico, distruttivi
#
# Le due corsie non si uniscono in una sola perche' la seconda ha bisogno del browser e
# di un ambiente che puo' mancare: unirle renderebbe il gate rosso per ragioni
# d'ambiente, e un gate rosso per ragioni sbagliate viene disattivato. Ma la seconda NON
# e' facoltativa: il suo esito va dichiarato, e se non gira va scritto perche'.
ESCLUSI_MARCATORI="browser_smoke or visual or stress or destructive"
ARGOMENTI=("$@")
if [[ "${ARGOMENTI[0]:-}" == "--corsia-esclusi" ]]; then
  ARGOMENTI=(-m "$ESCLUSI_MARCATORI" -q "${ARGOMENTI[@]:1}")
elif [[ ${#ARGOMENTI[@]} -eq 0 ]]; then
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
# PERCHE' UN COLLEGAMENTO E NON UNA MODIFICA AI COLLAUDI. I collaudi chiamano
# _find_chromium_executable(), che cerca un chromium DI SISTEMA sul PATH (e, in un
# contenitore Linux, anche in percorsi Windows). Non guarda dove playwright mette il
# proprio. Si poteva "aggiustare" quella funzione: NON SI E' FATTO. In questo progetto
# un motore ha gia' riscritto dei collaudi perche' passassero, ed e' la malattia per cui
# esiste la Fase 9. Si fornisce invece cio' che il collaudo chiede — un chromium sul
# PATH — collegando quello di playwright. Il collaudo resta intatto e la sua pretesa
# resta intatta.
#
# IL BROWSER VIVE IN UN VOLUME, NON NELL'IMMAGINE. Fino all'8/09/2026 i 72 collaudi
# che guardano lo schermo si SALTAVANO tutti con "Chromium executable not available":
# il pacchetto python playwright si installava (riga sotto), il BINARIO del browser no.
# Scaricarlo a ogni corsa sarebbe 115 MB ogni volta; tenerlo in un volume lo scarica
# una volta sola. Trovato chiedendo a pytest il motivo dei salti (-rs) invece di
# supporlo: installare playwright nel contenitore del backend non serviva a niente,
# perche' i collaudi girano in un contenitore usa-e-getta diverso.
# MODALITA' SCHERMO (CK_SCHERMO=1). I collaudi di browser NON possono girare sulla rete
# di compose, e la ragione e' precisa: il frontend e' costruito con l'indirizzo dell'API
# fissato a http://localhost:8000. Dentro un contenitore "localhost" e' il contenitore
# stesso, quindi il browser riceve ERR_CONNECTION_REFUSED e la pagina mostra al giocatore
# "Connessione instabile. Riprova." — misurato l'8/09/2026 con uno screenshot, non dedotto.
# Con la rete dell'host localhost:8000 e' il backend vero e le chiamate riescono.
# NON e' un difetto del prodotto: e' dove gira il browser.
if [ "${CK_SCHERMO:-0}" = "1" ]; then
  RETE="host"
  BASE_API="http://localhost:8000/api/v1"
  BASE_FE="http://localhost:3000"
  BASE_DB="postgresql://casinoking:casinoking@127.0.0.1:56543/casinoking"
  BASE_SITE="http://localhost:3001"
else
  BASE_API="http://backend:8000/api/v1"
  BASE_FE="http://edge:80"
  BASE_DB="postgresql://casinoking:casinoking@postgres:5432/casinoking"
  BASE_SITE="http://frontend-v3:3001"
fi

exec docker run --rm --network "$RETE" \
  -v "$RADICE:/repo" -w /repo \
  -v ck-playwright:/root/.cache/ms-playwright \
  -e PYTHONPATH="/repo/backend" \
  -e CASINOKING_API_BASE_URL="$BASE_API" \
  -e CASINOKING_TEST_DATABASE_URL="$BASE_DB" \
  -e CASINOKING_FRONTEND_BASE_URL="$BASE_FE" \
  -e CASINOKING_PUBLIC_EDGE_BASE_URL="$BASE_FE" \
  -e CASINOKING_SITE_V3_FRONTEND_BASE_URL="$BASE_SITE" \
  -e CK_MANICHINO="${CK_MANICHINO:-1}" \
  -e CK_GIOCHI_INTERNI="${CK_GIOCHI_INTERNI:-on}" \
  -e CK_COLLAUDO_SECRET_KEY="collaudo-test" \
  "$IMMAGINE" \
  sh -c "pip install -q pytest pytest-xdist httpx playwright pillow >/dev/null || echo '[ATTENZIONE] pip install fallito: i collaudi che dipendono da queste librerie si salteranno' >&2; python -m playwright install chromium >/dev/null 2>&1 || echo '[ATTENZIONE] browser non installato: i collaudi di schermo si salteranno' >&2; CHROME=\$(find /root/.cache/ms-playwright -name chrome -path '*chrome-linux*' 2>/dev/null | head -1); [ -n "\$CHROME" ] && "\$CHROME" --version >/dev/null 2>&1 && ln -sf "\$CHROME" /usr/local/bin/chromium || echo '[ATTENZIONE] nessun chromium: i collaudi di schermo si salteranno' >&2; python -m pytest $(printf '%q ' "${ARGOMENTI[@]}") -p no:cacheprovider"
