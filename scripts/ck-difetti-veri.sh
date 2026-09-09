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
# nome | commit | COLLAUDO PRECISO (file::nome) | FRASE ATTESA nel fallimento | file di prodotto
"D1a-sospeso-apre-partita|4274a74|tests/integration/test_sospensione_rotte_autenticate.py::test_suspended_player_cannot_open_any_authenticated_game|assert 422 == 403|backend/app/api/routes/manichino.py backend/app/api/routes/mines.py backend/app/api/routes/platform_access.py backend/app/modules/platform/rounds/service.py"
"D1b-sospeso-non-incassa|4274a74|tests/integration/test_sospensione_rotte_autenticate.py::test_suspended_mines_player_can_reveal_cashout_and_close_access_session|Account is not active|backend/app/api/routes/manichino.py backend/app/api/routes/mines.py backend/app/api/routes/platform_access.py backend/app/modules/platform/rounds/service.py"
"D2-liquidazione-marcata-vincita|0ec8fcf|tests/integration/test_mines_autoliquidazione_stato_terminale.py::test_mines_autoliquidazione_chiude_il_round_con_stato_terminale|assert 'won' == 'cancelled'|backend/app/modules/games/mines/autoliquidazione.py"
)
# D1 E' SPEZZATO IN DUE perche' il difetto della sospensione bucava in DUE SENSI OPPOSTI:
# il sospeso poteva APRIRE una partita, e non poteva INCASSARNE una gia' aperta. Sono due
# guasti, e ognuno ha il suo collaudo e la sua frase.
#
# D3 (553a872, "stato terminale") E' STATO TOLTO, su rilievo di Antigravity. Motivo: accende
# lo STESSO UNICO collaudo di D2, perche' quel file di collaudo ne contiene uno solo. Tenerlo
# significava contare due volte la stessa prova e chiamarle due. Resta un guasto vero, ma oggi
# NON e' attribuibile separatamente: servirebbe un collaudo che distingua i due difetti.
#
# IL QUARTO GUASTO dell'8/09 — collaudi riscritti per accettare un 500 dove pretendevano un
# 4xx — non e' disfabile: quei collaudi furono scritti PRIMA della riparazione (593f01c).
# E' un difetto di processo, e la sua difesa e' il cricchetto di GAT-04.

TUTTI_I_FILE=$(for g in "${GUASTI[@]}"; do echo "$g" | cut -d'|' -f5; done | tr ' ' '\n' | sort -u)

# Rilievo di Kimi: il ripristino puntava a HEAD. Se qualcuno committa durante la corsa,
# HEAD si sposta e si ripristina allo stato sbagliato. Si fissa il punto di partenza.
PARTENZA="$(git rev-parse HEAD)"
ripristina() { git checkout "$PARTENZA" -- $TUTTI_I_FILE 2>/dev/null || true; }
trap ripristina EXIT INT TERM

sporco=$(git status --porcelain -- $TUTTI_I_FILE)
if [ -n "$sporco" ]; then
  echo "ROSSO: l'albero e' gia' modificato sui file coinvolti. Non parto: non saprei" >&2
  echo "       distinguere un guasto iniettato da una modifica tua." >&2
  exit 2
fi

# collaudo() <selettore> <etichetta> -> 0 verde · 1 rosso · 3 NON PARTITO · 4 NON COMPILA
#
# PERCHE' QUATTRO ESITI. Rilievi di Antigravity, 9/09/2026:
#  - se disfare un guasto rompe un import, pytest stampa "1 error" in fase di raccolta.
#    La stesura precedente lo contava come ROSSO ATTESO: ma il gate non si e' accorto del
#    guasto logico, si e' accorto che il file non compila. Esito separato, e vale zero.
#  - se non si nomina IL collaudo, un altro collaudo dello stesso file che fallisce viene
#    contato come prova superata. Quindi si passa sempre file::nome.
CORSE="artifacts/fase-gate/corse"
# Si azzera a ogni corsa: un output avanzato da una corsa precedente e' una prova falsa
# che sopravvive alla propria scadenza. Trovato il 9/09/2026 dopo aver rinominato le
# etichette: restava sul disco il referto di una prova che non esiste piu'.
rm -rf "$CORSE"; mkdir -p "$CORSE"
collaudo() {
  local sel="$1" etichetta="$2" log="$CORSE/${2}.txt"
  ./scripts/ck-test.sh "$sel" -q > "$log" 2>&1
  local uscita=$?
  grep -qE '[0-9]+ error' "$log" && return 4
  grep -qE '[0-9]+ (passed|failed)' "$log" || return 3
  return $uscita
}

# il rosso deve essere rosso PER IL MOTIVO GIUSTO
motivo_giusto() {  # motivo_giusto <etichetta> <frase attesa>
  grep -qF "$2" "$CORSE/${1}.txt"
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
  # Rilievo di Kimi: si verificava l'albero integro su UN solo collaudo. Se un altro era
  # gia' rosso di suo, il suo "ROSSO ATTESO" non avrebbe provato niente.
  echo | tee -a "$USCITA"
  for g in "${GUASTI[@]}"; do
    nm=$(echo "$g" | cut -d'|' -f1); sel=$(echo "$g" | cut -d'|' -f3)
    printf '   albero integro, %-32s ... ' "$nm" | tee -a "$USCITA"
    collaudo "$sel" "00-integro-$nm"
    case $? in
      0) echo "VERDE ATTESO" | tee -a "$USCITA" ;;
      3|4) echo "NON PARTITO — referto NULLO" | tee -a "$USCITA"; esito=1 ;;
      *) echo "ROSSO INATTESO — gia' rosso senza guasti" | tee -a "$USCITA"; esito=1 ;;
    esac
  done
fi

for g in "${GUASTI[@]}"; do
  nome=$(echo "$g" | cut -d'|' -f1)
  commit=$(echo "$g" | cut -d'|' -f2)
  selettore=$(echo "$g" | cut -d'|' -f3)
  frase=$(echo "$g" | cut -d'|' -f4)
  prodotto=$(echo "$g" | cut -d'|' -f5)

  echo | tee -a "$USCITA"
  echo "## $nome  (disfa $commit)" | tee -a "$USCITA"
  echo "   collaudo:      ${selettore#*::}" | tee -a "$USCITA"
  echo "   frase attesa:  $frase" | tee -a "$USCITA"

  if ! git merge-base --is-ancestor "$commit" HEAD 2>/dev/null; then
    echo "   ROSSO: $commit non e' un antenato di HEAD. Non sto disfando la storia di" | tee -a "$USCITA"
    echo "   questo ramo, e il risultato non varrebbe niente." | tee -a "$USCITA"; esito=1; continue
  fi
  git checkout "${commit}^" -- $prodotto 2>/dev/null || {
    echo "   ROSSO: non riesco a disfare $commit" | tee -a "$USCITA"; esito=1; continue; }
  n_mod=$(git status --porcelain -- $prodotto | wc -l)
  if [ "$n_mod" -eq 0 ]; then
    # Rilievo di Kimi: un'iniezione a vuoto rendeva il collaudo verde, e il verde veniva
    # letto come "buco del gate". Sbagliato: e' un guasto MAI INIETTATO, e va detto cosi'.
    echo "   NESSUNA INIEZIONE — disfare $commit non ha cambiato un solo file." | tee -a "$USCITA"
    echo "   La prova non e' stata eseguita. Esito NON VALIDO." | tee -a "$USCITA"; esito=1; continue
  fi
  echo "   guasto iniettato: $n_mod file di prodotto" | tee -a "$USCITA"

  collaudo "$selettore" "${nome}-guasto"
  case $? in
    0) echo "   VERDE INATTESO — il gate NON si accorge di questo guasto" | tee -a "$USCITA"
       echo "   >>> e' un buco del gate, non un dettaglio" | tee -a "$USCITA"; esito=1 ;;
    3) echo "   NON PARTITO — esito NON VALIDO" | tee -a "$USCITA"; esito=1 ;;
    4) echo "   NON COMPILA — disfare il commit ha rotto un import. Il gate non ha" | tee -a "$USCITA"
       echo "   verificato niente: ha visto un file che non si carica. Esito NON VALIDO." | tee -a "$USCITA"; esito=1 ;;
    *) if motivo_giusto "${nome}-guasto" "$frase"; then
         echo "   ROSSO ATTESO, e per il motivo giusto: \"$frase\"" | tee -a "$USCITA"
       else
         echo "   ROSSO PER IL MOTIVO SBAGLIATO — fallisce, ma non con la frase attesa." | tee -a "$USCITA"
         echo "   Un rosso qualunque non prova che il gate collaudi la logica giusta." | tee -a "$USCITA"; esito=1
       fi ;;
  esac

  ripristina
  if [ $DUE_VERSI -eq 1 ]; then
    collaudo "$selettore" "${nome}-ripristinato"
    case $? in
      0) echo "   dopo il ripristino: VERDE ATTESO  [$(grep -oE '[0-9]+ passed[^,]*' "$CORSE/${nome}-ripristinato.txt" | tail -1)]" | tee -a "$USCITA" ;;
      3|4) echo "   dopo il ripristino: NON VALIDO" | tee -a "$USCITA"; esito=1 ;;
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
