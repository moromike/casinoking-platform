#!/usr/bin/env bash
# ck-censimento.sh — conserva il censimento iniziale e sorveglia le specifiche.
#
# LIMITE DICHIARATO: la data di ripubblicazione degli Artifact non e' misurabile
# dal repository. Questo controllo si fonda quindi su una DICHIARAZIONE UMANA nel
# manifesto, perche' gli Artifact vivono su claude.ai e non sono file Git. Lo
# script verifica formato, completezza e coerenza temporale della dichiarazione;
# non finge di aver interrogato claude.ai.
# LIMITE DICHIARATO: la soglia usa la data del committer (`%cs`), che Git
# permette di impostare a piacere con GIT_COMMITTER_DATE; non e' quindi una
# prova temporale infalsificabile, ma soltanto il dato disponibile nel repository.
set -euo pipefail

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RADICE"

CENSIMENTO="tests/integration/test_seamless_censimento.py"
MANIFESTO="scripts/censimento-specifiche.txt"
COMMIT_CENSIMENTO="0bffde3029f54049504f810e547b6657f2170935"
DATA_CENSIMENTO="2026-09-06T00:12:47+02:00"
IMPRONTA_CENSIMENTO="01cfe650dea3a513c759953d714d00b3e1aaf345f1865fe2fb2f03bca6d5f062"

esito=0
rosso() { printf 'ROSSO: %s\n' "$*"; esito=1; }
verde() { printf 'VERDE: %s\n' "$*"; }
nota()  { printf '       %s\n' "$*"; }

printf '== Censimento Fase 9 ==\n'

# PERCHE' UN'IMPRONTA FISSA. Contare righe o asserzioni lascerebbe passare una
# riscrittura che conserva i numeri ma capovolge il senso. L'impronta congela
# invece il censimento esattamente com'era quando fu datato e committato.
if [[ ! -f "$CENSIMENTO" ]]; then
  rosso "$CENSIMENTO manca: il censimento archiviato e' stato cancellato o rinominato"
elif [[ ! -s "$CENSIMENTO" ]]; then
  rosso "$CENSIMENTO e' vuoto: il censimento archiviato e' stato svuotato"
else
  impronta_attuale="$(sha256sum "$CENSIMENTO" | awk '{print $1}')"
  if [[ "$impronta_attuale" != "$IMPRONTA_CENSIMENTO" ]]; then
    rosso "$CENSIMENTO non coincide con il censimento archiviato"
    nota "attesa $IMPRONTA_CENSIMENTO"
    nota "trovata $impronta_attuale"
  elif ! git cat-file -e "$COMMIT_CENSIMENTO:$CENSIMENTO" 2>/dev/null; then
    rosso "il commit che data il censimento non contiene $CENSIMENTO"
  elif [[ "$(git show "$COMMIT_CENSIMENTO:$CENSIMENTO" | sha256sum | awk '{print $1}')" != "$IMPRONTA_CENSIMENTO" ]]; then
    rosso "l'impronta dichiarata non coincide col censimento nel commit di archivio"
  else
    verde "$CENSIMENTO e' datato $DATA_CENSIMENTO e archiviato senza modifiche"
  fi
fi

# L'ultimo codice della fase e' normalmente l'ultimo commit dopo la diramazione
# da main che tocca prodotto o configurazione runtime. Se quel tratto e' vuoto
# (caso normale dopo il merge su main), ripieghiamo sull'ultimo commit di codice
# raggiungibile da HEAD: un controllo permanentemente rosso verrebbe presto
# disattivato e smetterebbe di proteggere proprio le specifiche che sorveglia.
# Test, prove, documenti e verificatori non spostano artificialmente la soglia.
BASE="$(git merge-base main HEAD 2>/dev/null || true)"
COMMIT_CODICE=""
if [[ -z "$BASE" ]]; then
  rosso "non trovo il punto di diramazione fra main e HEAD"
else
  COMMIT_CODICE="$(git log -1 --format='%H' "$BASE..HEAD" -- backend frontend-v3 games infra 2>/dev/null || true)"
  if [[ -z "$COMMIT_CODICE" ]]; then
    COMMIT_CODICE="$(git log -1 --format='%H' HEAD -- backend frontend-v3 games infra 2>/dev/null || true)"
  fi
  if [[ -z "$COMMIT_CODICE" ]]; then
    rosso "non trovo alcun commit di codice raggiungibile da HEAD"
  fi
fi

if [[ ! -f "$MANIFESTO" ]]; then
  rosso "$MANIFESTO manca: le ripubblicazioni dichiarate non sono verificabili"
elif [[ ! -s "$MANIFESTO" ]]; then
  rosso "$MANIFESTO e' vuoto: le ripubblicazioni dichiarate non sono verificabili"
elif [[ -n "$COMMIT_CODICE" ]]; then
  DATA_CODICE="$(git show -s --format='%cs' "$COMMIT_CODICE")"
  nota "ultimo codice della fase: ${COMMIT_CODICE:0:8} del $DATA_CODICE"

  viste_gioco=0
  viste_piattaforma=0
  righe=0
  while IFS='|' read -r nome url data marcatore extra; do
    [[ -z "${nome//[[:space:]]/}" || "$nome" == \#* ]] && continue
    righe=$((righe + 1))

    if [[ -n "${extra:-}" ]]; then
      rosso "$MANIFESTO, riga $righe: troppi campi"
      continue
    fi
    case "$nome" in
      "Che cos'e' un gioco") viste_gioco=$((viste_gioco + 1)) ;;
      "Che cosa fa la piattaforma") viste_piattaforma=$((viste_piattaforma + 1)) ;;
      *) rosso "$MANIFESTO: specifica sconosciuta '$nome'"; continue ;;
    esac
    if [[ ! "$url" =~ ^https://claude\.ai/code/artifact/[0-9a-f-]+$ ]]; then
      rosso "$nome: URL Artifact mancante o non valido"
    fi
    if [[ ! "$data" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || ! date -d "$data" '+%F' >/dev/null 2>&1; then
      rosso "$nome: data dichiarata non valida ('$data')"
    elif [[ "$data" < "$DATA_CODICE" || "$data" == "$DATA_CODICE" ]]; then
      rosso "$nome: ripubblicazione dichiarata il $data, non successiva al codice del $DATA_CODICE"
    else
      verde "$nome: ripubblicazione dichiarata il $data, successiva al codice del $DATA_CODICE"
    fi
    if [[ "$marcatore" == "DA-AGGIORNARE-A-MANO" ]]; then
      nota "$nome usa il segnaposto esplicito DA-AGGIORNARE-A-MANO"
    elif [[ -n "$marcatore" ]]; then
      rosso "$nome: marcatore non riconosciuto ('$marcatore')"
    fi
  done < "$MANIFESTO"

  [[ "$righe" -eq 2 ]] || rosso "$MANIFESTO deve contenere esattamente due specifiche (trovate $righe)"
  [[ "$viste_gioco" -eq 1 ]] || rosso "'Che cos'e' un gioco' deve comparire esattamente una volta"
  [[ "$viste_piattaforma" -eq 1 ]] || rosso "'Che cosa fa la piattaforma' deve comparire esattamente una volta"
fi

if [[ "$esito" -eq 0 ]]; then
  printf '== ESITO: VERDE ==\n'
else
  printf '== ESITO: ROSSO ==\n'
fi
exit "$esito"
