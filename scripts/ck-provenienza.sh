#!/usr/bin/env bash
# ck-provenienza.sh — REG-01: verifica la catena di provenienza.
#
# NON si esegue dalla punta del ramo che sta controllando.
# ck-gate.sh estrae questo script da `main` e lancia QUELLA copia contro il ramo:
# altrimenti una versione manomessa deciderebbe se la propria manomissione fosse
# autorizzata, e si assolverebbe da sola.
#
# Uso:  ck-provenienza.sh [--repo <percorso>] [--base <ref>]
#   --repo  la copia di lavoro da esaminare (default: la cartella corrente)
#   --base  la linea di riferimento (default: main)

set -uo pipefail

REPO="$(pwd)"
BASE_REF="main"
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --base) BASE_REF="$2"; shift 2 ;;
    *) echo "argomento sconosciuto: $1" >&2; exit 2 ;;
  esac
done

cd "$REPO" || { echo "ROSSO: cartella non raggiungibile: $REPO" >&2; exit 2; }

esito=0
rosso() { echo "ROSSO: $*"; esito=1; }
nota()  { echo "       $*"; }

git rev-parse --verify "$BASE_REF" >/dev/null 2>&1 \
  || { echo "ROSSO: la linea di riferimento '$BASE_REF' non esiste"; exit 2; }

echo "== Catena di provenienza (REG-01) =="

# --- da quando vale la regola --------------------------------------------------
# Serve una SOGLIA, per la stessa ragione della baseline sulle migrazioni: il lavoro
# fatto PRIMA che REG-01 esistesse non puo' avere una catena, e pretenderla renderebbe
# il gate rosso per sempre su ogni ramo gia' aperto. Trovato ESEGUENDO lo script, non
# leggendolo: al primo lancio ha preteso la catena per nove file toccati nei giorni
# precedenti alla regola.
# La soglia si legge dalla copia FIDATA: spostarla in avanti sul ramo per scavalcare
# un controllo sarebbe l'aggiramento ovvio.
SOGLIA="$(git show "$BASE_REF:scripts/provenienza-soglia.txt" 2>/dev/null \
          | grep -vE '^\s*(#|$)' | head -1 | awk '{print $1}')"
if [ -n "$SOGLIA" ] && git rev-parse --verify "$SOGLIA" >/dev/null 2>&1 \
   && git merge-base --is-ancestor "$SOGLIA" HEAD 2>/dev/null; then
  TRATTO_DA="$SOGLIA"
  echo "   REG-01 in vigore da: $(git rev-parse --short "$SOGLIA")"
else
  TRATTO_DA="$(git merge-base "$BASE_REF" HEAD)"
  echo "   nessuna soglia utilizzabile: si esamina l'intero ramo"
fi
echo "   tratto esaminato: ${TRATTO_DA:0:8}..$(git rev-parse --short HEAD)  (base: $BASE_REF)"

# --- il perimetro si legge dalla copia FIDATA, unita a quella del ramo ---------
# Unione, non sostituzione: aggiungere voci sul ramo vale subito, TOGLIERLE no.
# Una riga tolta sul ramo continua a proteggere finche' la rimozione non e' stata
# fusa in main passando dalla catena. E' il punto: il perimetro non si restringe
# da solo.
PERIM_FILE="scripts/perimetro-protetto.txt"
perimetro="$( { git show "$BASE_REF:$PERIM_FILE" 2>/dev/null; cat "$PERIM_FILE" 2>/dev/null; } \
              | grep -vE '^\s*(#|$)' | sed 's/[[:space:]]*$//' | sort -u )"
if [ -z "$perimetro" ]; then
  rosso "perimetro protetto vuoto o illeggibile ($PERIM_FILE): non si verifica nulla"
  echo "== ESITO: ROSSO =="; exit 1
fi

# --- la baseline si legge SOLO dalla copia fidata ------------------------------
# Qui l'unione sarebbe un buco: basterebbe aggiungere sul ramo la migrazione nuova
# per farla passare per storica.
baseline="$(git show "$BASE_REF:scripts/provenienza-baseline.txt" 2>/dev/null \
            | grep -vE '^\s*(#|$)' | awk '{print $1}' | sort -u)"
# --- avvio: la copia fidata deve esistere PRIMA che il controllo abbia senso -----
# Se la baseline non e' ancora su main, ogni migrazione storica risulta senza catena
# e lo script sputa decine di rossi falsi. Non e' un fallimento del ramo: e' che
# l'impianto non e' ancora installato. Si dice, e ci si ferma: ripiegare sulla copia
# del ramo sarebbe esattamente il comportamento che REG-01 vieta.
BOOTSTRAP_MANCANTE=0
if [ -z "$baseline" ]; then
  BOOTSTRAP_MANCANTE=1
fi

# Restituisce il MODO ("SEMPRE" o "MODIFICA") se il file e' nel perimetro, vuoto se no.
modo_perimetro() {
  local f="$1" voce modo percorso
  while IFS= read -r voce; do
    [ -z "$voce" ] && continue
    modo="${voce%%[[:space:]]*}"
    percorso="${voce#"$modo"}"
    percorso="${percorso#"${percorso%%[![:space:]]*}"}"
    if [ -z "$percorso" ]; then percorso="$modo"; modo="MODIFICA"; fi
    case "$f" in "$percorso"*) echo "$modo"; return 0 ;; esac
  done <<< "$perimetro"
  return 1
}

# --- 1. i file del perimetro toccati nel tratto --------------------------------
toccati="$(git diff --name-status "$TRATTO_DA"..HEAD 2>/dev/null)"
n_protetti=0
while IFS=$'\t' read -r stato f1 f2; do
  [ -z "${stato:-}" ] && continue
  case "$stato" in
    R*) percorsi="$f1 $f2" ;;
    *)  percorsi="$f1" ;;
  esac
  modo=""
  for p in $percorsi; do m="$(modo_perimetro "$p")" && [ -n "$m" ] && modo="$m"; done
  [ -z "$modo" ] && continue
  case "$stato" in
    A)   op="creazione";     bersaglio="$f1" ;;
    M)   op="MODIFICA";      bersaglio="$f1" ;;
    D)   op="CANCELLAZIONE"; bersaglio="$f1" ;;
    R*)  op="RINOMINA";      bersaglio="$f2" ;;
    *)   op="$stato";        bersaglio="$f1" ;;
  esac
  # Creare e' libero dove il modo e' MODIFICA: un file nuovo puo' solo aggiungere
  # controlli, e pretendere una firma per ogni collaudo nuovo blocca il lavoro vero.
  if [ "$stato" = "A" ] && [ "$modo" = "MODIFICA" ]; then
    echo "-- creazione libera: $bersaglio  (modo MODIFICA: solo cambiarlo richiede la catena)"
    continue
  fi
  n_protetti=$((n_protetti+1))
  echo "-- $op: $bersaglio"
  rosso "nessuna catena depositata per '$bersaglio' ($op)"
  nota  "serve missioni/<data>-<nome>/PROPOSTA.md con il testo integrale fra i marcatori,"
  nota  "poi revisione indipendente, poi approvazione FIRMATA, poi l'applicazione."
done <<< "$toccati"

if [ "$n_protetti" -eq 0 ]; then
  echo "   nessun file del perimetro toccato nel tratto."
fi

# --- 2. le migrazioni applicate nel database fuori baseline --------------------
echo "-- migrazioni applicate nel database"
applicate="$(docker compose -f infra/docker/docker-compose.yml exec -T postgres \
             psql -U casinoking -d casinoking -tA \
             -c "SELECT migration_name FROM schema_migrations ORDER BY 1" 2>/dev/null)"
if [ -z "$applicate" ]; then
  nota "database non interrogabile: il controllo sulle migrazioni applicate NON e' stato"
  nota "eseguito. Non e' un via libera: e' un controllo mancante, e va detto."
else
  if [ "$BOOTSTRAP_MANCANTE" -eq 1 ]; then
    rosso "la baseline non esiste su '$BASE_REF': l'impianto REG-01 non e' installato."
    nota  "Le copie fidate (baseline, soglia, perimetro, questo script) devono stare"
    nota  "sulla linea gia' ratificata prima che il controllo possa dire qualcosa."
    nota  "Finche' non ci sono, il controllo sulle migrazioni applicate NON e' eseguito."
    applicate=""
  fi
  fuori=0
  while IFS= read -r m; do
    [ -z "$m" ] && continue
    grep -qxF "$m" <<< "$baseline" && continue
    fuori=$((fuori+1))
    rosso "migrazione '$m' e' APPLICATA nel database, non e' in baseline e non ha catena"
  done <<< "$applicate"
  [ "$fuori" -eq 0 ] && [ "$BOOTSTRAP_MANCANTE" -eq 0 ] \
    && nota "tutte in baseline: nessuna migrazione applicata senza catena."
fi

# --- 3. l'anello che oggi non e' verificabile ----------------------------------
echo "-- approvazione firmata (anello 4)"
if ! git config --get user.signingkey >/dev/null 2>&1; then
  rosso "nessuna chiave di firma configurata: l'anello 4 NON e' verificabile."
  nota  "Senza firma un agente puo' scrivere l'approvazione, attribuirla a Michele e"
  nota  "committarla: su questa macchina i motori committano gia' sotto il suo nome,"
  nota  "quindi l'autore di un commit non prova nulla. Finche' la chiave non esiste,"
  nota  "questo controllo e' dichiarato mancante e il gate resta rosso: e' voluto."
fi

echo "== ESITO: $([ "$esito" -eq 0 ] && echo VERDE || echo ROSSO) =="
exit "$esito"
