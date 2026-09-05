#!/usr/bin/env bash
# ck-prove-cavia.sh — deposita in artifacts/fase8/ le prove di PRV-03 e PRV-04-bis.
#
# PERCHE' UNO SCRIPT E NON COMANDI A MANO: chi emette il verdetto deve poter rilanciare
# le stesse prove e confrontare. Una prova che si riproduce solo se ti ricordi i comandi
# non e' una prova, e' un aneddoto.
set -uo pipefail
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RADICE"
mkdir -p artifacts/fase8
DATA="$(date '+%Y-%m-%d %H:%M:%S %z')"

# --- PRV-03: la sequenza completa, e la prova che sa diventare rossa ---------------
{
  printf '# PRV-03 — LA SEQUENZA COMPLETA CONTRO IL TITOLO DI FORNITORE\n'
  printf 'Data: %s\n\n' "$DATA"
  printf 'Il titolo `manichino_test` appartiene al motore `manichino`, che appartiene al\n'
  printf 'fornitore `ck_collaudo`: NON al fornitore interno. Il lancio percorre gettone,\n'
  printf 'sessione d accesso, partita, vincita, quadratura.\n\n'
  printf '## Il catalogo, come lo vede il database\n'
  docker exec casinoking-postgres-1 psql -U casinoking -d casinoking -A -F' | ' -c \
    "SELECT gt.title_code, gt.engine_code, ge.provider_code, gp.status AS provider_status,
            gt.is_test, st.lobby_visibility, st.real_enabled
       FROM game_titles gt
       JOIN game_engines ge ON ge.engine_code = gt.engine_code
       JOIN game_providers gp ON gp.provider_code = ge.provider_code
       LEFT JOIN site_titles st ON st.title_code = gt.title_code AND st.site_code = 'casinoking'
      WHERE gt.title_code = 'manichino_test';"
  printf '\n## La sequenza, e la prova che sa diventare rossa\n'
  printf 'Tre collaudi: la sequenza completa; il titolo reso invisibile che rifa comparire\n'
  printf 'il messaggio; la parita contabile con Mines.\n\n'
  ./scripts/ck-test.sh tests/integration/test_lancio_titolo_provider.py -v 2>&1 \
    | grep -E "PASSED|FAILED|ERROR|passed|failed" | grep -v "^$"
  printf '\n## Il messaggio che non compare piu\n'
  printf 'Cercato in tutta l esecuzione, sulla sequenza completa:\n'
  ./scripts/ck-test.sh tests/integration/test_lancio_titolo_provider.py::test_titolo_provider_collaudo_lancia_e_quadra -q 2>&1 \
    | grep -c "Title is not visible in the player library" \
    | sed 's/^/occorrenze di "Title is not visible in the player library": /'
} > artifacts/fase8/lancio-provider.txt 2>&1

# --- PRV-03: parita' contabile ------------------------------------------------------
{
  printf '# PRV-03 — PARITA CONTABILE FRA IL TITOLO DI FORNITORE E MINES\n'
  printf 'Data: %s\n\n' "$DATA"
  printf 'La stessa prova di MAN-01, un piano piu su: li il manichino era raggiunto per la\n'
  printf 'porta di servizio, qui passa dal catalogo come un fornitore esterno. Si confronta\n'
  printf 'cio che resta nel registro CONTO PER CONTO E LATO PER LATO, non i soli tipi di\n'
  printf 'movimento: due registrazioni contabilmente diverse passerebbero per identiche.\n\n'
  ./scripts/ck-test.sh tests/integration/test_lancio_titolo_provider.py::test_titolo_provider_scrive_come_mines_attraverso_lancio_e_access_session -v 2>&1 \
    | grep -E "PASSED|FAILED|ERROR|passed|failed"
} > artifacts/fase8/parita-provider-mines.txt 2>&1

# --- PRV-04-bis: il fornitore sospeso ferma la partita in corso ---------------------
{
  printf '# PRV-04-bis — SOSPENDERE UN FORNITORE FERMA LE SUE PARTITE, NON IL CASINO\n'
  printf 'Data: %s\n\n' "$DATA"
  printf 'Partita APERTA, poi il fornitore sospeso, poi il tentativo di proseguire: rifiutato.\n'
  printf 'Riattivato, la stessa sequenza riprende. E il contrappeso che rende la prova\n'
  printf 'significativa: mentre `ck_collaudo` e sospeso, un round di Mines continua a\n'
  printf 'funzionare. Senza quel contrappeso "tutto si e fermato" sarebbe un successo.\n\n'
  ./scripts/ck-test.sh tests/integration/test_provider_sospeso_ferma_la_partita.py -v 2>&1 \
    | grep -E "PASSED|FAILED|ERROR|passed|failed"
  printf '\n## Stato del fornitore dopo la prova (deve essere tornato attivo)\n'
  docker exec casinoking-postgres-1 psql -U casinoking -d casinoking -A -F' | ' -c \
    "SELECT provider_code, status FROM game_providers ORDER BY provider_code;"
} > artifacts/fase8/provider-sospeso.txt 2>&1

echo "depositati:"
ls -la artifacts/fase8/lancio-provider.txt artifacts/fase8/parita-provider-mines.txt artifacts/fase8/provider-sospeso.txt
