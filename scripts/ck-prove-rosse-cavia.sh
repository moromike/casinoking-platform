#!/usr/bin/env bash
# ck-prove-rosse-cavia.sh — PRV-04: toglie UNA difesa alla volta e pretende il rosso.
#
# PERCHE' ESISTE. Un collaudo verde non dice se e' capace di diventare rosso. Quattro
# difese che nessuno ha mai visto cadere sono quattro difese che nessuno ha provato.
# Qui ognuna viene rimossa dal codice, si lancia il collaudo, e si pretende che
# fallisca — e che fallisca su QUELLA difesa e non su un'altra.
#
# PERCHE' RIPRISTINARE E PULIRE SONO DUE GESTI DIVERSI. La prima versione di questo
# script cancellava le copie di sicurezza dentro la funzione di ripristino, che pero'
# viene chiamata dopo OGNI prova: dalla seconda in poi non c'era piu' niente da cui
# ripristinare, i sabotaggi si sommavano, e il referto diceva "tre rossi" mentre
# l'ultima prova cadeva per un sabotaggio precedente mai tolto. Peggio: i file
# restavano sabotati a fine script. Successo il 5/09/2026, e da li' viene la
# CONTROPROVA che ogni prova fa dopo il ripristino.
set -uo pipefail

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RADICE"

LANCIO="backend/app/modules/platform/game_launch/service.py"
VETRINA="backend/app/modules/platform/catalog/library_service.py"
SESSIONI="backend/app/modules/platform/access_sessions/service.py"
COLLAUDO="tests/contract/test_cavia_non_in_produzione.py"
# PERCHE' LA CONTROPROVA NON CONTA I TEST. La prima versione cercava "4 passed" nel
# riepilogo: il giorno in cui al file di contratto si e' aggiunto un collaudo, la
# controprova ha cominciato a gridare "ripristino fallito" su ripristini perfettamente
# riusciti. Un controllo che invecchia al primo test aggiunto e' un controllo che
# insegna a ignorarlo. Adesso si guarda il CODICE DI USCITA: verde e' verde comunque
# siano contati i test.

COPIE="$(mktemp -d)"
salva()      { cp "$LANCIO" "$COPIE/l"; cp "$VETRINA" "$COPIE/v"; cp "$SESSIONI" "$COPIE/s"; }
ripristina() { cp "$COPIE/l" "$LANCIO"; cp "$COPIE/v" "$VETRINA"; cp "$COPIE/s" "$SESSIONI"; }
pulisci()    { ripristina; rm -rf "$COPIE"; }
salva
trap pulisci EXIT

esito=0

prova() {
  local nome="$1" atteso="$2"
  printf '\n=== DIFESA RIMOSSA: %s ===\n' "$nome"
  local uscita
  ./scripts/ck-test.sh "$COLLAUDO" -q 2>&1 | tail -4
  uscita=${PIPESTATUS[0]}
  if [[ "$uscita" -eq 0 ]]; then
    printf 'ERRORE: senza la difesa "%s" il collaudo e VERDE. Non e una difesa.\n' "$nome"
    esito=1
  else
    printf 'ATTESO: rosso senza "%s" — deve cadere %s\n' "$nome" "$atteso"
  fi
  ripristina
  # CONTROPROVA: rimessa la difesa, il collaudo deve tornare verde. Senza, un
  # ripristino fallito passerebbe inosservato e la prova successiva misurerebbe
  # la somma di due sabotaggi invece di uno solo.
  if ./scripts/ck-test.sh "$COLLAUDO" -q >/dev/null 2>&1; then
    printf 'CONTROPROVA: rimessa "%s", il collaudo e tornato verde.\n' "$nome"
  else
    printf 'ERRORE: il ripristino di "%s" non ha funzionato. Le prove seguenti non valgono.\n' "$nome"
    esito=1
  fi
}

togli() { # $1 file, $2 blocco esatto, $3 occorrenze attese
  python3 - "$1" "$2" "$3" <<'PY'
import sys, pathlib
percorso, blocco, attese = sys.argv[1], sys.argv[2], int(sys.argv[3])
p = pathlib.Path(percorso); t = p.read_text(encoding="utf-8")
n = t.count(blocco)
assert n == attese, f"attese {attese} occorrenze in {percorso}, trovate {n}"
p.write_text(t.replace(blocco, ""), encoding="utf-8")
PY
}

printf '# PRV-04 — LE QUATTRO DIFESE SANNO DIVENTARE ROSSE\n'
printf 'Data: %s\n' "$(date '+%Y-%m-%d %H:%M:%S %z')"
printf '\nOgni difesa viene TOLTA dal codice, una alla volta. Il collaudo deve diventare\n'
printf 'rosso, e rosso su QUELLA difesa. Poi la difesa si rimette e si verifica che torni\n'
printf 'verde: una difesa che puo sparire senza che nessuno se ne accorga non e una difesa.\n'

printf '\n=== CONTROLLO POSITIVO: tutte e quattro in piedi ===\n'
./scripts/ck-test.sh "$COLLAUDO" -q 2>&1 | tail -3
if ! ./scripts/ck-test.sh "$COLLAUDO" -q >/dev/null 2>&1; then
  printf 'ERRORE: il collaudo e gia rosso a difese intatte. Le prove che seguono non valgono.\n'
  esito=1
fi

togli "$LANCIO" '    if normalized_game_code == GAME_CODE_MANICHINO and not manichino_attivo():
        raise GameLaunchTokenValidationError("Manichino is not active")
' 2
prova "D1 - l'interruttore" "test_d1_interruttore_..."

togli "$VETRINA" '                  AND gt.is_test = false
' 1
prova "D2 - il marchio di prova in vetrina" "test_d2_vetrina_..."

togli "$LANCIO" '    if ambiente_di_produzione() and title.get("is_test") is True:
        raise GameLaunchTokenValidationError("Test titles cannot be launched in production")
' 1
prova "D3 - l'ambiente sul lancio" "test_d3_lancio_..."

togli "$SESSIONI" '    if ambiente_di_produzione() and title["is_test"] is True:
        raise AccessSessionValidationError("Test titles cannot be launched in production")
' 1
prova "D4 - l'ambiente sulla sessione d'accesso" "test_d4_sessione_accesso_..."

printf '\n=== RIPRISTINO: le quattro difese devono essere tutte al loro posto ===\n'
d1="$(grep -c 'Manichino is not active' "$LANCIO")"
d2="$(grep -c 'AND gt.is_test = false' "$VETRINA")"
d3="$(grep -c 'Test titles cannot be launched in production' "$LANCIO")"
d4="$(grep -c 'Test titles cannot be launched in production' "$SESSIONI")"
printf 'D1 interruttore: %s (attese 2)\nD2 marchio in vetrina: %s (attesa 1)\n' "$d1" "$d2"
printf 'D3 ambiente sul lancio: %s (attesa 1)\nD4 ambiente sulla sessione: %s (attesa 1)\n' "$d3" "$d4"
if [[ "$d1" != "2" || "$d2" != "1" || "$d3" != "1" || "$d4" != "1" ]]; then
  printf 'ERRORE: il codice e rimasto sabotato. NON committare.\n'
  esito=1
fi

if [[ "$esito" -eq 0 ]]; then
  printf '\nESITO: quattro difese, quattro rossi, quattro ritorni al verde.\n'
else
  printf '\nESITO: ALMENO UNA DIFESA NON SERVE A NIENTE, oppure il ripristino e fallito.\n'
fi
exit "$esito"
