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
# MET-05 (9/09/2026): l'immagine di difetto NON e' piu' quella del backend, ma una sua
# derivata che ha gia' dentro i cinque pacchetti dei collaudi. Prima si installavano a
# ogni lancio: [GENERATO] 9,66 s su 9,71 s di corsa, per 0,52 s di collaudo vero.
IMMAGINE="${CK_IMMAGINE:-casinoking-collaudi:latest}"

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

# L'IMMAGINE SI COSTRUISCE UNA VOLTA, NON A OGNI LANCIO. Il controllo qui sotto costa
# [GENERATO] 0,27 s: legge due targhe scritte sull'immagine e le confronta con lo stato di
# adesso. Costruisce davvero solo se l'immagine manca, se e' cambiata la sua ricetta, o se
# casinoking-backend:latest e' stata ricostruita.
# Non e' un passo da ricordarsi a mano: un gesto che si puo' dimenticare non e' una difesa.
# Se CK_IMMAGINE e' impostata a mano il chiamante sa cosa sta facendo e non si tocca nulla.
if [ -z "${CK_IMMAGINE:-}" ]; then
  "$RADICE/scripts/ck-immagine-collaudi.sh" >/dev/null || {
    echo "[STOP] Non sono riuscito a preparare $IMMAGINE." >&2
    echo "       Rilancia ./scripts/ck-immagine-collaudi.sh per vedere il motivo." >&2
    exit 5
  }
fi

# DA QUALE ALBERO STA SERVENDO IL CODICE LO STACK ACCESO.
#
# PERCHE' SI CHIEDE AL CONTENITORE E NON SI INDOVINA. Il backend monta una cartella
# dell'host dentro /app/backend: quella cartella E' l'albero il cui codice viene davvero
# eseguito dai collaudi che passano dalla rete. Non e' deducibile da dove ci troviamo:
# e' un fatto che sa solo Docker, e glielo si chiede.
#
# PERCHE' SERVE (9/09/2026, trovato da Codex gpt-5.6-sol e riprodotto): lanciando i
# collaudi da un git worktree, una modifica di prodotto fatta li' NON viene eseguita —
# la rete porta al contenitore, che serve l'albero principale. Misurato: disfando la
# riparazione D2 dentro un worktree, il suo collaudo restava VERDE, mentre sullo stesso
# sabotaggio l'albero principale e' rosso. Un verde falso a un revisore e' peggio di un
# rosso: viene contato come successo.
#
# QUI SI RACCOGLIE SOLTANTO IL DATO. A decidere e' scripts/ck_guardia_albero.py, dentro
# il contenitore, perche' solo pytest sa QUALI collaudi chiedono lo stack. Se il dato non
# si riesce a leggere, resta vuoto e la guardia tace: meglio muta che arbitraria.
ALBERO_STACK="$(docker inspect "$(docker compose -f "$COMPOSE" --env-file "$ENVFILE" ps -q backend 2>/dev/null)" \
  -f '{{range .Mounts}}{{if eq .Destination "/app/backend"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || true)"
ALBERO_STACK="${ALBERO_STACK%/backend}"
# I COLLEGAMENTI SIMBOLICI SI SCIOLGONO QUI, SULL'HOST, non dentro il contenitore.
# Rilievo di Codex sol e Antigravity, ottavo giro: il confronto fra i due percorsi era fra
# stringhe, e chi arrivava all'albero giusto passando per un collegamento veniva fermato
# per sbaglio. Il primo tentativo di riparazione confrontava le cartelle vere DENTRO il
# contenitore: non funziona, perche' li' nessuno dei due percorsi dell'host esiste e la
# risoluzione ricade sul confronto di stringhe. L'unico posto dove i due percorsi sono
# entrambi veri e' questo.
ALBERO_STACK="$(readlink -f "$ALBERO_STACK" 2>/dev/null || echo "$ALBERO_STACK")"
# Si monta la cartella VERA anche dentro il contenitore: Docker rifiuta di montare un
# percorso che passa per un collegamento ("error while creating mount source path"), quindi
# lanciare ck-test.sh attraverso un collegamento non ha mai funzionato. Scoperto provando
# la riparazione del rosso falso, ottavo giro. Una riga, e funziona.
ALBERO_CORRENTE="$(readlink -f "$RADICE" 2>/dev/null || echo "$RADICE")"

# SE NON SI RIESCE A LEGGERLO, SI FERMA. NON si prosegue in silenzio.
# Rilievo di Codex sol e Antigravity, ottavo giro: la guardia era "deliberatamente muta"
# quando il dato mancava. Ma a questo punto dello script sappiamo gia' che Docker risponde
# e che lo stack e' in piedi (i due controlli qui sopra): se adesso il dato torna vuoto,
# non e' una condizione normale da tollerare, e' un'anomalia. Tollerarla significa lasciare
# aperta la porta che questa guardia esiste per chiudere — e "fail-open" e' esattamente il
# nome del difetto per cui esiste la Fase GATE.
if [ -z "$ALBERO_STACK" ]; then
  echo "[STOP] Non riesco a sapere da quale albero il backend sta servendo il codice." >&2
  echo "       Lo stack risulta in piedi, quindi questo e' un guasto, non una condizione" >&2
  echo "       normale. Senza quel dato non posso escludere che i collaudi giudichino il" >&2
  echo "       codice di un altro albero e rispondano verde su codice mai provato." >&2
  echo "       Da guardare: docker inspect del contenitore backend, voce Mounts." >&2
  exit 7
fi

# E NON SI PUO' SPEGNERE DA RIGA DI COMANDO. Sempre ottavo giro: gli argomenti finiscono
# in pytest, quindi bastava aggiungere `-p no:ck_guardia_albero` per zittirla. Una difesa
# che si disattiva con un argomento non e' una difesa.
for _a in "$@"; do
  case "$_a" in
    no:ck_guardia_albero|*ck_guardia_albero*)
      if [ "$_a" != "-p" ]; then
        echo "[STOP] Non si spegne la guardia dell'albero da riga di comando ($_a)." >&2
        echo "       Se ti serve davvero, sistema la causa: lancia dall'albero che ha" >&2
        echo "       acceso lo stack." >&2
        exit 7
      fi ;;
  esac
done

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

# IL COMANDO DENTRO IL CONTENITORE — si VERIFICA, non si installa.
#
# PERCHE' NON "installa se manca". Un lancio che si ripara da solo nasconde il guasto:
# l'immagine resterebbe sbagliata per sempre e ogni corsa pagherebbe la riparazione.
# Qui manca qualcosa => si ferma e dice quale gesto la rimette a posto. Il gesto sta in
# un posto solo (ck-immagine-collaudi.sh), che e' anche l'unico posto dove i pacchetti
# sono nominati per essere installati.
#
# GLI ARGOMENTI NON PASSANO PIU' DA printf %q: si danno a `sh -c` come parametri
# posizionali e si rileggono con "$@". Una riga in meno da citare a mano.
COMANDO='
set -u
if ! python -c "import pytest, xdist, httpx, playwright, PIL" >/dev/null 2>&1; then
  echo "[STOP] Mancano dei pacchetti che i collaudi pretendono." >&2
  echo "       Quali:" >&2
  for m in pytest xdist httpx playwright PIL; do
    python -c "import $m" >/dev/null 2>&1 || echo "         - $m" >&2
  done
  echo "       Rimedio: ./scripts/ck-immagine-collaudi.sh --forza" >&2
  exit 4
fi
# IL BROWSER STA NEL VOLUME ck-playwright, scaricato una volta sola. Qui si controlla
# soltanto che ci sia e che parta: se manca, i collaudi di schermo si salteranno da soli,
# e la corsia ordinaria non li chiede comunque. Nessuno scaricamento a caldo.
CHROME=$(find /root/.cache/ms-playwright -name chrome -path "*chrome-linux*" 2>/dev/null | head -1)
if [ -n "$CHROME" ] && "$CHROME" --version >/dev/null 2>&1; then
  ln -sf "$CHROME" /usr/local/bin/chromium
elif ! command -v chromium >/dev/null 2>&1; then
  echo "[ATTENZIONE] nessun chromium: i collaudi di schermo si salteranno" >&2
fi
exec python -m pytest "$@" -p no:cacheprovider -p ck_guardia_albero
'

exec docker run --rm --network "$RETE" \
  -v "$ALBERO_CORRENTE:/repo" -w /repo \
  -v ck-playwright:/root/.cache/ms-playwright \
  -e PYTHONPATH="/repo/backend:/repo/scripts" \
  -e CK_ALBERO_STACK="$ALBERO_STACK" \
  -e CK_ALBERO_CORRENTE="$ALBERO_CORRENTE" \
  -e CASINOKING_API_BASE_URL="$BASE_API" \
  -e CASINOKING_TEST_DATABASE_URL="$BASE_DB" \
  -e CASINOKING_FRONTEND_BASE_URL="$BASE_FE" \
  -e CASINOKING_PUBLIC_EDGE_BASE_URL="$BASE_FE" \
  -e CASINOKING_SITE_V3_FRONTEND_BASE_URL="$BASE_SITE" \
  -e CK_MANICHINO="${CK_MANICHINO:-1}" \
  -e CK_GIOCHI_INTERNI="${CK_GIOCHI_INTERNI:-on}" \
  -e CK_COLLAUDO_SECRET_KEY="collaudo-test" \
  "$IMMAGINE" \
  sh -c "$COMANDO" ck-test "${ARGOMENTI[@]}"
