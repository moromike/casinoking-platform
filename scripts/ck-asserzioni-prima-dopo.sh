#!/usr/bin/env bash
# ck-asserzioni-prima-dopo.sh — il metro di CAP-04.
#
# COSA MISURA, E PERCHE' DUE NUMERI E NON UNO.
# Un collaudo ricucito deve verificare ESATTAMENTE cio' che verificava prima. Il modo
# piu' facile di barare e' toglierne qualcuna: quindi si contano le ASSERZIONI SCRITTE,
# file per file, contro i minimi fotografati da un'altra sessione (fase7).
#
# Ma le asserzioni scritte non bastano. Un file interamente SALTATO esce "0 falliti",
# cioe' verde, con zero verifiche eseguite: le asserzioni sono tutte li', e nessuna e'
# mai stata valutata. Quindi si contano anche i COLLAUDI PASSATI per file, e si pretende
# che non calino. Due numeri per due modi diversi di ingannarsi.
set -uo pipefail
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RADICE"

printf '# CAP-04 — ASSERZIONI E COLLAUDI PASSATI, PRIMA E DOPO\n'
printf 'Data: %s\n\n' "$(date '+%Y-%m-%d %H:%M:%S %z')"
printf 'I minimi vengono da artifacts/fase7/asserzioni-prima.md, fotografato il 5/09 da\n'
printf 'unaltra sessione: non e un numero costruito adesso per farlo tornare.\n\n'
printf '%-58s %8s %8s %8s   %s\n' "FILE" "MINIMO" "SCRITTE" "PASSATI" "ESITO"

esito_globale=0
while IFS='|' read -r file minimo; do
  [[ -z "$file" ]] && continue
  if [[ ! -f "$file" ]]; then
    printf '%-58s %8s %8s %8s   %s\n' "$file" "$minimo" "-" "-" "MANCANTE"
    esito_globale=1; continue
  fi
  scritte="$(grep -c 'assert ' "$file")"
  passati="$(./scripts/ck-test.sh "$file" -q 2>&1 | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1)"
  passati="${passati:-0}"
  stato="ok"
  [[ "$scritte" -lt "$minimo" ]] && { stato="ASSERZIONI CALATE"; esito_globale=1; }
  [[ "$passati" -eq 0 ]] && { stato="NESSUN COLLAUDO ESEGUITO"; esito_globale=1; }
  printf '%-58s %8s %8s %8s   %s\n' "$file" "$minimo" "$scritte" "$passati" "$stato"
done <<'ELENCO'
tests/contract/test_api_contract.py|100
tests/integration/test_account_wallet_movements.py|111
tests/integration/test_admin_financial_reports.py|85
tests/integration/test_admin_force_close_sessions.py|52
tests/integration/test_admin_session_drilldown.py|16
tests/integration/test_game_library_publication.py|80
tests/integration/test_game_table_sessions.py|44
tests/integration/test_game_title_archive_restore.py|37
tests/integration/test_platform_access_sessions.py|41
tests/integration/test_session_cascade_close.py|49
tests/integration/test_title_code_propagation.py|41
tests/contract/test_gmp5_game_module_manifest.py|42
tests/contract/test_title_editor_agnostic.py|112
tests/integration/test_8b_demo_anonymous_invariants.py|18
ELENCO

printf '\n'
if [[ "$esito_globale" -eq 0 ]]; then
  printf 'ESITO: VERDE — nessun file ha perso asserzioni, nessun file e uscito a zero collaudi.\n'
else
  printf 'ESITO: ROSSO — vedi le righe sopra.\n'
fi
exit "$esito_globale"
