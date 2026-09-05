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

# Il commit contro cui confrontare la forma delle asserzioni. Si passa come primo
# argomento; per difetto il commit precedente a quello attuale.
RIFERIMENTO="${1:-HEAD~1}"

printf '# CAP-04 — ASSERZIONI E COLLAUDI PASSATI, PRIMA E DOPO\n'
printf 'Data: %s\n\n' "$(date '+%Y-%m-%d %H:%M:%S %z')"
printf 'I minimi vengono da artifacts/fase7/asserzioni-prima.md, fotografato il 5/09 da\n'
printf 'unaltra sessione: non e un numero costruito adesso per farlo tornare.\n\n'
# PERCHE' UNA PASSATA SOLA. La prima stesura lanciava ./scripts/ck-test.sh una volta PER
# FILE: ogni invocazione ricostruisce un contenitore e reinstalla le dipendenze, e la
# misura completa richiedeva circa quaranta minuti. Una ricevuta che si ristampa solo in
# quaranta minuti non verra' ristampata da nessuno, e una prova che nessuno rifa' torna a
# essere un'affermazione con una data. Un'invocazione sola, e i collaudi passati per file
# si contano dagli identificativi nell'output.
ESITI="$(mktemp)"
./scripts/ck-test.sh $(grep -oE '^tests/[^|]+' "${BASH_SOURCE[0]}") -v 2>&1 \
  | grep -E "PASSED|FAILED|ERROR" > "$ESITI"

printf '%-58s %8s %8s %8s   %s\n' "FILE" "MINIMO" "SCRITTE" "PASSATI" "ESITO"
esito_globale=0
tot_m=0; tot_s=0; tot_p=0
while IFS='|' read -r file minimo; do
  [[ -z "$file" ]] && continue
  if [[ ! -f "$file" ]]; then
    printf '%-58s %8s %8s %8s   %s\n' "$file" "$minimo" "-" "-" "MANCANTE"
    esito_globale=1; continue
  fi
  scritte="$(grep -c 'assert ' "$file")"
  passati="$(grep -cE "^${file//./\\.}::.*PASSED" "$ESITI")"
  falliti="$(grep -cE "^${file//./\\.}::.*(FAILED|ERROR)" "$ESITI")"
  stato="ok"
  if [[ "$scritte" -lt "$minimo" ]]; then stato="ASSERZIONI CALATE"; esito_globale=1
  elif [[ "$passati" -eq 0 ]]; then stato="NESSUN COLLAUDO ESEGUITO"; esito_globale=1
  elif [[ "$falliti" -gt 0 ]]; then stato="$falliti ROSSI"; esito_globale=1; fi
  tot_m=$((tot_m+minimo)); tot_s=$((tot_s+scritte)); tot_p=$((tot_p+passati))
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
rm -f "$ESITI"
printf '\n%-58s %8s %8s %8s\n' "TOTALE" "$tot_m" "$tot_s" "$tot_p"

# --- IL CONTROLLO CHE MANCAVA, ED E' COSTATO UNA RISERVA ---
# Il 5/09/2026 questo attrezzo ha dato VERDE su un file in cui un confronto esatto fra due
# identificativi era diventato "e' una stringa". Il conteggio non se ne accorge: 16
# asserzioni prima, 16 dopo. L'ha trovato una revisione indipendente leggendo il diff.
#
# COSA FA, E COSA NON FA. Conta quante asserzioni usano un predicato DEBOLE (esiste, non
# e' nullo, e' di questo tipo, contiene) contro quante usano un confronto ESATTO, prima e
# dopo. Non decide: SEGNALA. Un file che guadagna predicati deboli e perde uguaglianze va
# LETTO DA UNA PERSONA. E' un'euristica dichiarata, non una prova — chiamarla prova
# sarebbe ripetere l'errore in una forma nuova.
printf '\n--- PREDICATI DEBOLI: da leggere, non da approvare ---\n'
printf '%-58s %14s %14s\n' "FILE" "DEBOLI p->d" "ESATTE p->d"
# PERCHE' LA LISTA SI RILEGGE QUI. La prima stesura di questo blocco scorreva un array
# che in questo script non esiste: stampava ZERO righe e sembrava "nessun problema". Un
# controllo che non controlla niente e' peggio di nessun controllo, ed e' lo stesso
# difetto che questo blocco esiste per scovare. La lista si ricava dai file di collaudo
# realmente esaminati sopra, cosi' le due sezioni non possono divergere.
for file in $(grep -oE '^tests/[^|]+' "${BASH_SOURCE[0]}"); do
  [[ -f "$file" ]] || continue
  # PERCHE' `| head -1` E NON `|| echo 0`. `grep -c` su zero corrispondenze STAMPA "0" e
  # poi esce con codice 1: la scorciatoia `|| echo 0` aggiungeva un secondo "0" e il
  # confronto aritmetico si rompeva con un errore di sintassi in mezzo alla prova.
  # Successo davvero, sull'ultimo file dell'elenco.
  conta_deboli() { grep -cE 'assert .*(isinstance\(|is not None|is None| in |len\()' "$1" 2>/dev/null | head -1; }
  conta_esatte() { grep -cE 'assert [^=]*==' "$1" 2>/dev/null | head -1; }
  prima_file="$(mktemp)"
  if git show "$RIFERIMENTO:$file" > "$prima_file" 2>/dev/null; then
    d_prima="$(conta_deboli "$prima_file")"; e_prima="$(conta_esatte "$prima_file")"
  else
    d_prima="-"; e_prima="-"
  fi
  rm -f "$prima_file"
  d_dopo="$(conta_deboli "$file")"; e_dopo="$(conta_esatte "$file")"
  # PERCHE' LA CONDIZIONE E' LARGA. La prima stesura segnalava solo chi guadagnava
  # predicati deboli E perdeva uguaglianze insieme. Provandola sul lavoro vero, cinque
  # file avevano PERSO uguaglianze senza guadagnare nulla di debole — e uno di quei cali
  # era un annacquamento vero, trovato da una revisione umana e non da qui. Un calo di
  # confronti esatti va guardato COMUNQUE: puo' essere una ristrutturazione legittima,
  # oppure una verifica che se n'e' andata in punta di piedi. Decide chi legge.
  segnale=""
  if [[ "$d_prima" != "-" ]]; then
    if (( d_dopo > d_prima )); then
      segnale="   <== LEGGERE: piu' predicati deboli"
    elif (( e_dopo < e_prima )); then
      segnale="   <== LEGGERE: meno confronti esatti"
    fi
  fi
  printf '%-58s %6s -> %-4s %6s -> %-4s%s\n' "$file" "$d_prima" "$d_dopo" "$e_prima" "$e_dopo" "$segnale"
done

printf '\n'
if [[ "$esito_globale" -eq 0 ]]; then
  printf 'ESITO: VERDE — nessun file ha perso asserzioni, nessun file e uscito a zero collaudi.\n'
else
  printf 'ESITO: ROSSO — vedi le righe sopra.\n'
fi
exit "$esito_globale"
