#!/usr/bin/env bash
# ck-rosso.sh — undicesimo comando del gate: i collaudi sanno diventare rossi?
#
# PERCHE' ESISTE. Un collaudo verde non dice se e' capace di diventare rosso o se
# e' verde perche' non guarda niente. Qui si applica OGNI sabotaggio previsto dal
# contratto (POR-01 importo di un centesimo, POR-03 controllo sul momento, POR-06
# abbozzo del 4 settembre, POR-07 giocatore sospeso), si pretende che il collaudo
# corrispondente FALLISCA, si ripristina, e si esce rossi se anche una sola prova
# resta verde sotto sabotaggio.
#
# REGOLA SUL ROSSO ATTESO. Un'uscita non-zero del collaudo NON e' prova che il
# sabotaggio sia stato smascherato: puo' essere un timeout, un errore di
# infrastruttura, una raccolta fallita, un crash — oppure il fallimento
# COLLATERALE di un altro test dello stesso file, che lascerebbe cieco il
# controllo che il sabotaggio doveva smascherare. Il rosso vale solo se
# nell'output ci sono TUTTI i SEGNI dichiarati per quella prova: le righe
# `FAILED file::nome_del_test` dei nodeid precisi che verificano la cosa
# sabotata. Uscita non-zero senza tutti i segni = ROSSO con scritto "il
# sabotaggio non ha colpito il controllo che doveva colpire"; se la causa e' la
# raccolta dei test o l'infrastruttura, la diagnosi lo dice esplicitamente.
#
# REGOLA SU CIO' CHE MANCA. Se il collaudo di una prova non esiste, lo script
# diventa ROSSO e dice "prova mancante: <sigla>". Non lo salta in silenzio e non
# lo conta come superato: un gate che ignora cio' che manca e' il modo in cui
# "tutti i test sono verdi" diventa una bugia.
#
# REGOLA SUL COLLAUDO GIA' ROSSO. Se il collaudo e' rosso a codice integro, la
# prova-del-rosso non e' dimostrabile: un collaudo sempre rosso non discrimina
# niente. Anche questo e' ROSSO, con la ragione. (Precedente: il controllo
# positivo di ck-prove-rosse-cavia.sh.)
#
# IL RIPRISTINO VIENE PRIMA DI TUTTO. Questo script modifica temporaneamente il
# PERCORSO DEL DENARO. Se si interrompe a meta' lascia il codice sabotato: per
# questo il ripristino sta in un trap EXIT, file per file, per CONTENUTO — mai
# `git checkout .` o `git stash`, che cancellerebbero lavoro non salvato altrui.
# Un ripristino fallito NON passa in silenzio: il fallimento viene registrato,
# gridato a fine corsa, l'uscita e' non-zero e la copia di sicurezza resta dove
# sta, col percorso stampato. A fine corsa si riconfrontano gli SHA256 di TUTTI
# i file tracciati con quelli registrati a inizio corsa — non lo stato git, che
# confronta stringhe e non byte: un file gia' modificato prima e rimasto
# sabotato dopo ha la stessa riga di `git status` ma contenuto diverso.
#
# LO STACK LO GESTISCE LO SCRIPT, NON LA MEMORIA DI NESSUNO. I collaudi girano in
# un contenitore usa-e-getta ma parlano via HTTP col backend dello stack, che
# esegue il codice montato in /app/backend. Se lo stack e' stato avviato da
# UN'ALTRA copia del repository, il sabotaggio scritto in QUESTO worktree non
# arriva a chi lo dovrebbe eseguire. Percio' lo script:
#   1. registra il montaggio iniziale di /app/backend;
#   2. se punta a un altro worktree, ripunta LUI lo stack qui e aspetta che sia
#      sano — non si limita a stampare un comando da lanciare a mano;
#   3. nel trap EXIT rimette lo stack COM'ERA e aspetta che torni sano. Se non
#      ci riesce, lo dice a caratteri cubitali con il comando esatto da lanciare;
#   4. dopo ogni sabotaggio verifica che il marcatore sia visibile DENTRO il
#      contenitore (il file arriva davvero);
#   5. riavvia il contenitore backend dopo ogni modifica e dopo ogni ripristino:
#      il codice caricato dal processo e' quello del file, non quello che uvicorn
#      --reload potrebbe non aver ancora riletto.
set -euo pipefail

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RADICE"
COMPOSE="$RADICE/infra/docker/docker-compose.yml"

ROUTER="backend/app/api/v1/seamless/router.py"

COLLAUDO_POR01="tests/integration/test_seamless_parita_contabile.py"
COLLAUDO_POR03="tests/integration/test_seamless_firma_rigiocata.py"
COLLAUDO_POR06="tests/integration/test_seamless_scrive_davvero.py"
COLLAUDO_POR07="tests/integration/test_seamless_controlli_di_casa.py"

# IL SEGNO DEL ROSSO ATTESO, DICHIARATO PER OGNI PROVA: il NODEID PRECISO del
# test che DEVE fallire sotto quel sabotaggio, cioe' la riga del riepilogo di
# pytest `FAILED file::nome_del_test`. Non basta "un test qualsiasi del file":
# un fallimento collaterale di un altro test lascerebbe cieco il controllo che
# il sabotaggio doveva smascherare — un falso verde strutturale, esattamente
# cio' che questo gate esiste per impedire. Se un file contiene piu' test
# pertinenti, vanno dichiarati TUTTI e pretesi TUTTI. Un errore qualunque
# (timeout, raccolta, crash) non produce la riga FAILED del nodeid e non
# dimostra che il sabotaggio sia stato visto.
#
# POR-01 (importo di un centesimo): test_parita_contabile e' il solo test del
# file e verifica importi e saldi (balance_after dopo reserve+commit).
NODEIDS_POR01=(
  "$COLLAUDO_POR01::test_parita_contabile"
)
# POR-06 (abbozzo del 4 settembre): il sabotaggio finge il successo senza
# scrivere nel registro; TUTTI e quattro i test del file verificano la
# scrittura nel registro (reserve, commit vincita, commit perdita, rollback)
# e devono fallire tutti.
NODEIDS_POR06=(
  "$COLLAUDO_POR06::test_reserve_riuscita_scrive_puntata_sui_conti_giusti"
  "$COLLAUDO_POR06::test_commit_vincita_riuscita_scrive_accredito_sui_conti_giusti"
  "$COLLAUDO_POR06::test_commit_perdita_riuscita_conserva_la_sola_puntata_nel_registro"
  "$COLLAUDO_POR06::test_rollback_riuscito_scrive_rimborso_sui_conti_giusti"
)
# POR-07 (giocatore sospeso): il test che verifica il blocco della sessione
# nuova. Oggi il collaudo e' gia' rosso a codice integro e la prova si ferma
# prima del sabotaggio; il nodeid resta dichiarato per quando sara' verde.
NODEIDS_POR07=(
  "$COLLAUDO_POR07::test_reg02_sospensione_non_blocca_sessione_aperta_ma_blocca_sessione_nuova"
)
# POR-03 (momento della richiesta): il collaudo non esiste ancora. Nessun
# nodeid da dichiarare: se un giorno il file apparisse senza nodeid, il
# giudizio deve restare ROSSO, perche' un sabotaggio senza controllo
# dichiarato non prova niente.
NODEIDS_POR03=()

# Segni che dicono "questo non e' un rosso del collaudo": infrastruttura o
# raccolta. Servono solo per la diagnosi, mai per assolvere.
SEGNI_INFRA='\[STOP\]|Cannot connect to the Docker daemon|error during connect|INTERNALERROR|^ERROR |no tests ran'

ARTEFATTI="artifacts/fase9"

esito=0
rosso() { printf 'ROSSO: %s\n' "$1"; esito=1; }

# --- ripristino: si salva per contenuto, file per file, prima di toccare -------
COPIE="$(mktemp -d)"
TOCCATI=()
SABOTAGGIO_ATTIVO=0
RIPRISTINO_FALLITO=()

salva() { # $1 percorso relativo: copia di sicurezza, una sola volta per file
  local file="$1"
  local nome
  nome="$(printf '%s' "$file" | tr '/' '_')"
  if [[ ! -f "$COPIE/$nome" ]]; then
    cp "$file" "$COPIE/$nome"
    TOCCATI+=("$file")
  fi
}

ripristina_tutto() {
  local file nome
  for file in "${TOCCATI[@]:-}"; do
    [[ -n "$file" ]] || continue
    nome="$(printf '%s' "$file" | tr '/' '_')"
    # Il || non serve ad assolvere: serve solo a far arrivare il trap in fondo.
    # Il fallimento viene REGISTRATO e gridato a fine corsa, e la copia di
    # sicurezza non viene cancellata.
    if ! cp "$COPIE/$nome" "$file"; then
      RIPRISTINO_FALLITO+=("$file")
    fi
  done
}

# --- lo stack: registrato, ripuntato, rimesso com'era nel trap -----------------
ENVFILE=""
CID=""
STACK_DA_RIMETTERE=0
RADICE_INIZIALE=""

container_backend() {
  docker compose -f "$COMPOSE" --env-file "$ENVFILE" ps -q backend 2>/dev/null
}

attendi_sano() { # $1 id contenitore: attende l'healthcheck, o ritorna 1
  local cid="$1" attesa=0
  while [[ "$(docker inspect "$cid" --format '{{.State.Health.Status}}' 2>/dev/null)" != "healthy" ]]; do
    attesa=$((attesa + 3))
    if [[ "$attesa" -gt 120 ]]; then
      return 1
    fi
    sleep 3
  done
  return 0
}

rimetti_stack() { # rimette lo stack sul montaggio iniziale; ritorna 1 se non ci riesce
  [[ "$STACK_DA_RIMETTERE" == "1" ]] || return 0
  local compose_iniziale="$RADICE_INIZIALE/infra/docker/docker-compose.yml"
  local envfile_iniziale="$ENVFILE"
  if [[ -x "$RADICE_INIZIALE/scripts/segreti.sh" ]]; then
    envfile_iniziale="$("$RADICE_INIZIALE/scripts/segreti.sh" 2>/dev/null)" || envfile_iniziale="$ENVFILE"
  fi
  printf 'rimetto lo stack com'\''era: %s\n' "$RADICE_INIZIALE"
  local cid_nuovo=""
  if docker compose -f "$compose_iniziale" --env-file "$envfile_iniziale" up -d backend >/dev/null 2>&1; then
    cid_nuovo="$(docker compose -f "$compose_iniziale" --env-file "$envfile_iniziale" ps -q backend 2>/dev/null)"
    if [[ -n "$cid_nuovo" ]] && attendi_sano "$cid_nuovo"; then
      printf 'stack rimesso su %s e sano.\n' "$RADICE_INIZIALE"
      return 0
    fi
  fi
  printf '\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' >&2
  printf '!! NON SONO RIUSCITO A RIMETTERE LO STACK COM ERA.\n' >&2
  printf '!! Lo stack di %s e'\'\'' fermo o esegue il codice sbagliato.\n' >&2 "$RADICE_INIZIALE"
  printf '!! Rimettilo a mano con:\n' >&2
  printf '!!   docker compose -f "%s" --env-file "%s" up -d backend\n' >&2 "$compose_iniziale" "$envfile_iniziale"
  printf '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n' >&2
  return 1
}

pulisci() {
  # PERCHE' OGNI PASSO E' PROTETTO: il trap EXIT deve arrivare in fondo comunque.
  # Un ripristino interrotto a meta' e' esattamente l'incidente che questo script
  # esiste per non lasciare in giro. Ma "arrivare in fondo" non vuol dire
  # "assolvere": i fallimenti restano registrati e cambiano l'uscita.
  local esito_pulizia=0
  ripristina_tutto
  if [[ "$SABOTAGGIO_ATTIVO" == "1" && -n "$CID" ]]; then
    # Se siamo usciti a sabotaggio applicato, il processo backend potrebbe avere
    # in pancia il codice sabotato: si riavvia per ricaricare i file ripristinati.
    docker restart "$CID" >/dev/null 2>&1 || true
  fi
  rimetti_stack || esito_pulizia=1
  if [[ ${#RIPRISTINO_FALLITO[@]} -gt 0 ]]; then
    printf '\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' >&2
    printf '!! RIPRISTINO FALLITO su questi file:\n' >&2
    printf '!!   %s\n' >&2 "${RIPRISTINO_FALLITO[@]}"
    printf '!! La copia di sicurezza NON viene cancellata. Sta in:\n' >&2
    printf '!!   %s\n' >&2 "$COPIE"
    printf '!! Ripristina a mano, per esempio:\n' >&2
    printf '!!   cp "%s/%s" "%s"\n' >&2 "$COPIE" "$(printf '%s' "${RIPRISTINO_FALLITO[0]}" | tr '/' '_')" "${RIPRISTINO_FALLITO[0]}"
    printf '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n' >&2
    esito_pulizia=1
  else
    rm -rf "$COPIE" || true
  fi
  # Solo la pulizia fallita puo' alzare l'uscita: mai abbassarla.
  if [[ "$esito_pulizia" != "0" ]]; then
    exit "$esito_pulizia"
  fi
}
trap pulisci EXIT

# --- lo stack esegue QUESTO worktree? Se no, ce lo portiamo noi ----------------
ENVFILE="$("$RADICE/scripts/segreti.sh")"
if ! docker compose -f "$COMPOSE" --env-file "$ENVFILE" ps --status running --quiet backend >/dev/null 2>&1; then
  echo "[STOP] Lo stack non e' in piedi. Lancia prima ./scripts/ck-up.sh" >&2
  exit 1
fi

CID="$(container_backend)"
MONTAGGIO_INIZIALE="$(docker inspect "$CID" --format '{{range .Mounts}}{{if eq .Destination "/app/backend"}}{{.Source}}{{end}}{{end}}')"
QUESTO_BACKEND="$(cd "$RADICE/backend" && pwd -P)"
if [[ "$MONTAGGIO_INIZIALE" != "$QUESTO_BACKEND" ]]; then
  RADICE_INIZIALE="$(dirname "$MONTAGGIO_INIZIALE")"
  # LA BANDIERA SI ARMA PRIMA DEL RIPUNTAMENTO, NON DOPO. Se il processo muore
  # fra il `docker compose up` e l'armatura, il trap leggerebbe ancora zero e
  # lascerebbe lo stack di partenza a eseguire il codice di questo ramo, in
  # silenzio. Armandola prima, un'uscita in qualunque punto del ripuntamento
  # scatena un ripristino forse inutile — e un ripristino inutile e' sempre
  # meglio di uno mancato.
  STACK_DA_RIMETTERE=1
  printf 'lo stack esegue %s: lo ripunto su questo worktree.\n' "$MONTAGGIO_INIZIALE"
  docker compose -f "$COMPOSE" --env-file "$ENVFILE" up -d backend >/dev/null
  CID="$(container_backend)"
  if ! attendi_sano "$CID"; then
    echo "[STOP] il backend ripuntato su questo worktree non e' diventato sano entro 120 secondi" >&2
    exit 1
  fi
fi

# PERCHE' LA BANDIERA NON SI ABBASSA MAI DENTRO riavvia_backend: significa "il
# processo backend POTREBBE avere in pancia codice sabotato". Si alza al sabotaggio
# e la abbassa solo chi ha ripristinato i file E riavviato con successo. Se lo
# script muore in mezzo, il trap riavvia il backend sui file ripristinati:
# un processo che continua a eseguire il sabotaggio a file gia' ripristinati
# sarebbe un ripristino finto.
riavvia_backend() {
  docker restart "$CID" >/dev/null
  if ! attendi_sano "$CID"; then
    rosso "il backend non e' tornato sano entro 120 secondi dal riavvio (infrastruttura, non collaudo)"
    return 1
  fi
  return 0
}

lancia_collaudo() { # $1 collaudo, $2 file di output; ritorna il codice di uscita
  local uscita=0
  ./scripts/ck-test.sh "$1" -q >"$2" 2>&1 || uscita=$?
  return "$uscita"
}

# IL GIUDIZIO SUL ROSSO: non basta l'uscita non-zero, e non basta un FAILED
# qualsiasi dello stesso file. Vale solo se TUTTI i nodeid dichiarati per la
# prova compaiono come FAILED: se ne manca anche uno solo, il sabotaggio non
# ha colpito il controllo che doveva colpire.
rosso_del_sabotaggio() { # $1 sigla, $2 file di output, $3.. nodeid attesi
  local sigla="$1" out="$2"
  shift 2
  local nodeid mancanti=() dichiarati=()
  for nodeid in "$@"; do
    [[ -n "$nodeid" ]] && dichiarati+=("$nodeid")
  done
  if [[ ${#dichiarati[@]} -eq 0 ]]; then
    rosso "$sigla: nessun nodeid dichiarato per questa prova — un sabotaggio senza controllo dichiarato non prova niente"
    return 1
  fi
  local riga=""
  riga="$(grep -Ei -m1 "$SEGNI_INFRA" "$out" || true)"
  if [[ -n "$riga" ]]; then
    rosso "$sigla: il collaudo e' fallito, ma non per il sabotaggio — errore di infrastruttura o di raccolta: $riga"
    return 1
  fi
  for nodeid in "${dichiarati[@]}"; do
    if ! grep -qF "FAILED $nodeid" "$out"; then
      mancanti+=("$nodeid")
    fi
  done
  if [[ ${#mancanti[@]} -gt 0 ]]; then
    rosso "$sigla: il sabotaggio non ha colpito il controllo che doveva colpire — FAILED mancante per i nodeid attesi:"
    printf '  %s\n' "${mancanti[@]}"
    tail -5 "$out"
    return 1
  fi
  return 0
}

sostituisci() { # $1 file, $2 sigla, $3 blocco esatto, $4 rimpiazzo; esce 1 se il blocco non c'e'
  python3 - "$1" "$3" "$4" <<'PY'
import sys, pathlib
percorso, blocco, rimpiazzo = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(percorso); t = p.read_text(encoding="utf-8")
n = t.count(blocco)
if n != 1:
    print(f"blocco da sabotare trovato {n} volte (attesa 1) in {percorso}", file=sys.stderr)
    sys.exit(1)
p.write_text(t.replace(blocco, rimpiazzo), encoding="utf-8")
PY
}

marcatore_nel_contenitore() { # $1 sigla, $2 file: il sabotaggio arriva a chi esegue?
  docker exec "$CID" grep -q "SABOTAGGIO-CK-ROSSO: $1" "/app/$2" 2>/dev/null
}

# --- i sabotaggi, uno per impegno ------------------------------------------------
sabotaggio_por01() { # l'importo sbagliato di un centesimo sulla trattenuta
  salva "$ROUTER"
  sostituisci "$ROUTER" "POR-01" \
    'bet_amount=req.amount,' \
    'bet_amount=req.amount + Decimal("0.01"),  # SABOTAGGIO-CK-ROSSO: POR-01'
}

sabotaggio_por06() { # l'abbozzo del 4 settembre: successo senza scrivere niente
  salva "$ROUTER"
  local risposta='    return {"status": "success", "tx_id": req.tx_id, "platform_round_id": "abbozzo", "balance_after": "0.00", "already_exists": False}  # SABOTAGGIO-CK-ROSSO: POR-06'
  sostituisci "$ROUTER" "POR-06" \
    'def reserve_funds(req: ReserveRequest, provider_code: str = Depends(verify_provider_hmac)) -> dict:
' \
    "def reserve_funds(req: ReserveRequest, provider_code: str = Depends(verify_provider_hmac)) -> dict:
$risposta
" || return 1
  sostituisci "$ROUTER" "POR-06" \
    'def commit_funds(req: CommitRequest, provider_code: str = Depends(verify_provider_hmac)) -> dict:
' \
    "def commit_funds(req: CommitRequest, provider_code: str = Depends(verify_provider_hmac)) -> dict:
$risposta
" || return 1
  sostituisci "$ROUTER" "POR-06" \
    'def rollback_funds(req: RollbackRequest, provider_code: str = Depends(verify_provider_hmac)) -> dict:
' \
    "def rollback_funds(req: RollbackRequest, provider_code: str = Depends(verify_provider_hmac)) -> dict:
$risposta
"
}

sabotaggio_por07() { # togli il controllo sul giocatore sospeso all'apertura di sessione nuova
  # Il controllo oggi NON ESISTE nel codice (il collaudo e' rosso a codice integro
  # e la prova si ferma prima di arrivare qui). Il giorno in cui POR-07 sara'
  # implementato e il collaudo verde, questo sabotaggio va definito sul blocco
  # reale — e questa funzione deve fallire finche' il blocco non e' scritto,
  # perche' un sabotaggio che non sa cosa togliere non prova niente.
  printf "sabotaggio POR-07 non definito: il controllo sul giocatore sospeso non e' ancora nel codice\n" >&2
  return 1
}

sabotaggio_por03() { # togli il controllo sul momento della richiesta
  # Come POR-07: il controllo non esiste ancora. Da definire quando POR-03 sara'
  # implementato; fino ad allora fallire e' il comportamento onesto.
  printf "sabotaggio POR-03 non definito: il controllo sul momento non e' ancora nel codice\n" >&2
  return 1
}

# --- la prova del rosso, uguale per tutti ----------------------------------------
prova_del_rosso() { # $1 sigla, $2 collaudo, $3 funzione di sabotaggio, $4 artefatto del rosso, $5.. nodeid attesi
  local sigla="$1" collaudo="$2" sabotaggio="$3" artefatto="$4"
  shift 4
  local out="$COPIE/out-$sigla.txt"

  printf '\n=== %s: %s ===\n' "$sigla" "$collaudo"

  if [[ ! -f "$collaudo" ]]; then
    rosso "prova mancante: $sigla ($collaudo non esiste)"
    return
  fi

  # CONTROLLO POSITIVO: a codice integro il collaudo deve essere verde. Se e'
  # gia' rosso, non puo' dimostrare di saper diventare rosso PER IL SABOTAGGIO.
  if ! lancia_collaudo "$collaudo" "$out"; then
    local riga=""
    riga="$(grep -Ei -m1 "$SEGNI_INFRA" "$out" || true)"
    if [[ -n "$riga" ]]; then
      rosso "$sigla: la baseline non e' partita — errore di infrastruttura o di raccolta, non un rosso del collaudo: $riga"
    else
      rosso "$sigla: il collaudo e' gia' rosso a codice integro — la prova-del-rosso non e' dimostrabile finche' non torna verde"
    fi
    return
  fi
  printf 'baseline: verde, come deve essere.\n'

  if ! "$sabotaggio"; then
    rosso "$sigla: sabotaggio non applicabile (il blocco da togliere non e' stato trovato o non e' definito)"
    ripristina_tutto
    return
  fi
  SABOTAGGIO_ATTIVO=1

  # IL TRABOCCHETTO, VERIFICATO A OGNI PROVA: il marcatore deve essere visibile
  # dentro il contenitore. Se non lo e', il file montato non e' questo worktree e
  # il rosso che seguirebbe non misurerebbe niente.
  if ! marcatore_nel_contenitore "$sigla" "$ROUTER"; then
    rosso "$sigla: il sabotaggio NON arriva al contenitore che esegue il codice"
    ripristina_tutto
    if riavvia_backend; then SABOTAGGIO_ATTIVO=0; fi
    return
  fi

  riavvia_backend || { ripristina_tutto; return; }

  if lancia_collaudo "$collaudo" "$out"; then
    rosso "$sigla: il collaudo e' rimasto VERDE sotto sabotaggio — non sta guardando"
    tail -5 "$out"
  elif rosso_del_sabotaggio "$sigla" "$out" "$@"; then
    printf "ATTESO: sotto sabotaggio il collaudo e' rosso col segno atteso. Il rosso va depositato accanto al verde.\n"
    mkdir -p "$ARTEFATTI"
    cp "$out" "$artefatto"
  fi

  # CONTROPROVA: rimesso a posto il codice, il collaudo deve tornare verde. Senza,
  # un ripristino fallito passerebbe inosservato e falserebbe le prove seguenti.
  ripristina_tutto
  if riavvia_backend; then
    SABOTAGGIO_ATTIVO=0
  else
    return
  fi
  if lancia_collaudo "$collaudo" "$out"; then
    printf "CONTROPROVA: ripristinato, il collaudo e' tornato verde.\n"
  else
    rosso "$sigla: il ripristino non ha riportato il collaudo al verde"
    tail -5 "$out"
  fi
}

# --- il contenuto di TUTTI i file tracciati, prima e dopo ------------------------
# Lo sha256 si registra PRIMA di toccare qualunque file: lo stato git confronta
# stringhe di stato, non byte, e non puo' vedere un file rimasto sabotato.
MANIFEST_SHA="$COPIE/sha256-iniziali.txt"
git ls-files -z | xargs -0 sha256sum > "$MANIFEST_SHA"
STATO_INIZIALE="$(git status --porcelain --untracked-files=no)"

printf '# CK-ROSSO — i collaudi del percorso del denaro sanno diventare rossi?\n'
printf 'Data: %s\n' "$(date '+%Y-%m-%d %H:%M:%S %z')"

prova_del_rosso "POR-01" "$COLLAUDO_POR01" sabotaggio_por01 "$ARTEFATTI/parita-seamless-mines-rosso.txt" "${NODEIDS_POR01[@]}"
prova_del_rosso "POR-06" "$COLLAUDO_POR06" sabotaggio_por06 "$ARTEFATTI/il-collaudo-smaschera-labbozzo.txt" "${NODEIDS_POR06[@]}"
prova_del_rosso "POR-07" "$COLLAUDO_POR07" sabotaggio_por07 "$ARTEFATTI/controlli-di-casa-rosso.txt" "${NODEIDS_POR07[@]}"
prova_del_rosso "POR-03" "$COLLAUDO_POR03" sabotaggio_por03 "$ARTEFATTI/firma-rigiocata-rosso.txt" "${NODEIDS_POR03[@]:-}"

# IL RIPRISTINO SI DIMOSTRA SUL CONTENUTO, NON SULLO STATO: gli sha256 dei file
# tracciati devono essere esattamente quelli di inizio corsa, file per file, e i
# diversi vengono nominati. I file NUOVI (questo script, gli artefatti del rosso)
# non sono tracciati e non contano.
printf '\n=== RIPRISTINO: il contenuto dei file tracciati deve essere identico a inizio corsa ===\n'
DIVERSI="$(sha256sum -c --quiet "$MANIFEST_SHA" 2>/dev/null || true)"
if [[ -n "$DIVERSI" ]]; then
  rosso "il ripristino NON e' completo: contenuto diverso da inizio corsa. NON committare."
  printf '%s\n' "$DIVERSI"
else
  printf 'ripristino confermato: contenuto dei file tracciati identico a inizio corsa.\n'
fi

# Lo stato git resta come controllo AGGIUNTIVO, non come prova.
STATO_FINALE="$(git status --porcelain --untracked-files=no)"
if [[ "$STATO_FINALE" != "$STATO_INIZIALE" ]]; then
  rosso "lo stato git dei file tracciati e' diverso da inizio corsa. NON committare."
  diff <(printf '%s\n' "$STATO_INIZIALE") <(printf '%s\n' "$STATO_FINALE") || true
fi

if [[ "$esito" -eq 0 ]]; then
  printf "\nESITO: VERDE — ogni prova prevista e' diventata rossa sotto il suo sabotaggio.\n"
else
  printf "\nESITO: ROSSO — almeno una prova non si e' dimostrata capace di diventare rossa.\n"
fi
exit "$esito"
