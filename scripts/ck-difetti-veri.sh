#!/usr/bin/env bash
# ck-difetti-veri.sh — GAT-02/GAT-03 del CONTRATTO_FASE_GATE.
#
# LA DOMANDA A CUI RISPONDE: il gate si accorge di quello che e' successo l'8 settembre?
#
# PERCHE' NON SI INVENTANO I GUASTI. I quattro verdi su codice rotto dell'8/09 sono
# storia, e le riparazioni stanno in git, una per commit. Qui si DISFA una riparazione
# vera alla volta — solo i file di PRODOTTO, lasciando il collaudo dov'e' — e si pretende
# che quel collaudo diventi rosso. Un guasto inventato prova che il gate vede cio' che ho
# immaginato io; un guasto vero prova che vede cio' che ci e' davvero successo.
#
# PERCHE' NEI DUE VERSI. Un gate sempre rosso passerebbe la prova "diventa rosso". Quindi
# per ogni guasto si pretendono tre esiti: rosso col guasto, verde dopo il ripristino,
# verde sull'albero integro.
#
# PERCHE' RIPRISTINARE E PULIRE SONO DUE GESTI DIVERSI: lezione gia' pagata il 5/09/2026
# da ck-prove-rosse-cavia.sh — i sabotaggi si sommavano e il referto mentiva. Qui il
# ripristino e' in un trap, e a fine corsa si PRETENDE l'albero pulito.
#
#   ./scripts/ck-difetti-veri.sh              i tre guasti, rosso atteso
#   ./scripts/ck-difetti-veri.sh --due-versi  anche verde dopo ripristino e su albero integro
set -uo pipefail
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RADICE"
DUE_VERSI=0; [ "${1:-}" = "--due-versi" ] && DUE_VERSI=1
USCITA="artifacts/fase-gate/difetti-veri.txt"
mkdir -p artifacts/fase-gate

# --- la tabella dei guasti veri. Aggiungerne uno = aggiungere una riga. ---------------
# nome | commit della riparazione | collaudo che deve arrossare | file di prodotto
GUASTI=(
"D1-sospensione|4274a74|tests/integration/test_sospensione_rotte_autenticate.py|backend/app/api/routes/manichino.py backend/app/api/routes/mines.py backend/app/api/routes/platform_access.py backend/app/modules/platform/rounds/service.py"
"D2-liquidazione-marcata-vincita|0ec8fcf|tests/integration/test_mines_autoliquidazione_stato_terminale.py|backend/app/modules/games/mines/autoliquidazione.py"
"D3-liquidazione-senza-stato-terminale|553a872|tests/integration/test_mines_autoliquidazione_stato_terminale.py|backend/app/modules/games/mines/autoliquidazione.py"
)
# NOTA ONESTA: D3 e' un SOVRAINSIEME di D2 — stesso file, commit precedente. Disfare D3
# toglie anche la riparazione di D2. Dichiarato qui e non nascosto nel referto.
# NOTA ONESTA 2: il contratto parlava di QUATTRO guasti. Il quarto — «tre collaudi
# riscritti per accettare un 500 dove pretendevano un 4xx» — NON e' disfabile: quei
# collaudi furono scritti PRIMA della riparazione (commit 593f01c), quindi non esiste una
# riparazione di prodotto da annullare. E' un difetto di PROCESSO, non di codice, e la sua
# difesa e' il cricchetto di GAT-04, non un'iniezione.

TUTTI_I_FILE=$(for g in "${GUASTI[@]}"; do echo "$g" | cut -d'|' -f4; done | tr ' ' '\n' | sort -u)

ripristina() { git checkout HEAD -- $TUTTI_I_FILE 2>/dev/null || true; }
trap ripristina EXIT INT TERM

sporco=$(git status --porcelain -- $TUTTI_I_FILE)
if [ -n "$sporco" ]; then
  echo "ROSSO: l'albero e' gia' modificato sui file coinvolti. Non parto: non saprei" >&2
  echo "       distinguere un guasto iniettato da una modifica tua." >&2
  exit 2
fi

# collaudo() <file> <etichetta> -> 0 verde · 1 rosso vero · 3 NON PARTITO
#
# PERCHE' TRE ESITI E NON DUE. Se Docker si pianta, ck-test.sh esce diverso da 0 e la
# prima stesura di questo script lo contava come "il gate si e' accorto del guasto":
# un verde per finta costruito dentro l'attrezzo che serve a scovarli. Quindi si
# pretende di VEDERE il riepilogo di pytest: senza quello, il collaudo non e' partito
# e il risultato non vale.
CORSE="artifacts/fase-gate/corse"
mkdir -p "$CORSE"
collaudo() {
  local file="$1" etichetta="$2" log="$CORSE/${2}.txt"
  ./scripts/ck-test.sh "$file" -q > "$log" 2>&1
  local uscita=$?
  if ! grep -qE '[0-9]+ (passed|failed|error)' "$log"; then
    return 3
  fi
  return $uscita
}

esito=0
{
echo "# I guasti veri — il gate si accorge di quello che e' successo l'8 settembre?"
echo
printf '**%s** - commit %s - generato da scripts/ck-difetti-veri.sh%s\n' \
  "$(date '+%d/%m/%Y %H:%M')" "$(git rev-parse --short HEAD)" \
  "$([ $DUE_VERSI -eq 1 ] && echo ' --due-versi')"
echo
} > "$USCITA"

if [ $DUE_VERSI -eq 1 ]; then
  printf 'albero integro, nessuna iniezione ... ' | tee -a "$USCITA"
  collaudo "tests/integration/test_mines_autoliquidazione_stato_terminale.py" "00-albero-integro"
  case $? in
    0) echo "VERDE ATTESO" | tee -a "$USCITA" ;;
    3) echo "NON PARTITO — il collaudo non e' mai stato eseguito. Referto NULLO." | tee -a "$USCITA"; esito=1 ;;
    *) echo "ROSSO INATTESO — fallisce gia' senza guasti" | tee -a "$USCITA"; esito=1 ;;
  esac
fi

for g in "${GUASTI[@]}"; do
  nome=$(echo "$g" | cut -d'|' -f1)
  commit=$(echo "$g" | cut -d'|' -f2)
  test_file=$(echo "$g" | cut -d'|' -f3)
  prodotto=$(echo "$g" | cut -d'|' -f4)

  echo | tee -a "$USCITA"
  echo "## $nome  (disfa $commit: $(git log -1 --format=%s $commit | cut -c1-60))" | tee -a "$USCITA"
  echo "   collaudo che deve arrossare: $test_file" | tee -a "$USCITA"

  git checkout "${commit}^" -- $prodotto 2>/dev/null || {
    echo "   ROSSO: non riesco a disfare $commit" | tee -a "$USCITA"; esito=1; continue; }
  modificati=$(git status --porcelain -- $prodotto | wc -l)
  echo "   guasto iniettato: $modificati file di prodotto riportati indietro" | tee -a "$USCITA"

  collaudo "$test_file" "${nome}-guasto"
  case $? in
    0) echo "   VERDE INATTESO — il gate NON si accorge di questo guasto" | tee -a "$USCITA"
       echo "   >>> e' un buco del gate, non un dettaglio" | tee -a "$USCITA"; esito=1 ;;
    3) echo "   NON PARTITO — il collaudo non e' stato eseguito, questo esito NON VALE" | tee -a "$USCITA"; esito=1 ;;
    *) riep=$(grep -oE '[0-9]+ failed[^,]*' "$CORSE/${nome}-guasto.txt" | tail -1)
       echo "   ROSSO ATTESO — il gate si accorge di $nome  [$riep]" | tee -a "$USCITA" ;;
  esac

  ripristina
  if [ $DUE_VERSI -eq 1 ]; then
    collaudo "$test_file" "${nome}-ripristinato"
    case $? in
      0) riep=$(grep -oE '[0-9]+ passed[^,]*' "$CORSE/${nome}-ripristinato.txt" | tail -1)
         echo "   dopo il ripristino: VERDE ATTESO  [$riep]" | tee -a "$USCITA" ;;
      3) echo "   dopo il ripristino: NON PARTITO — esito NON VALIDO" | tee -a "$USCITA"; esito=1 ;;
      *) echo "   dopo il ripristino: ROSSO INATTESO — il ripristino non e' esatto" | tee -a "$USCITA"; esito=1 ;;
    esac
  fi
done

ripristina
echo | tee -a "$USCITA"
residuo=$(git status --porcelain -- $TUTTI_I_FILE)
if [ -n "$residuo" ]; then
  echo "ROSSO: l'albero NON e' tornato pulito. File ancora modificati:" | tee -a "$USCITA"
  echo "$residuo" | tee -a "$USCITA"; esito=1
else
  echo "albero tornato pulito: nessun file di prodotto modificato" | tee -a "$USCITA"
fi
echo "output di ogni corsa: $CORSE/" | tee -a "$USCITA"
echo "referto: $USCITA"
exit $esito
