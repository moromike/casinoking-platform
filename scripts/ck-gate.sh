#!/usr/bin/env bash
# ck-gate.sh — impedisce che una suite "verde" nasconda test rimossi o silenziati.
#
# PERCHE' QUESTO GATE E' SEVERO: un test tolto, o reso skip senza un impegno
# tracciabile, non e' una suite piu' affidabile. E' informazione di qualita' persa.
#
#   ./scripts/ck-gate.sh
#   ./scripts/ck-gate.sh --autotest
set -euo pipefail

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

uso() {
  cat <<'EOF'
Uso: ./scripts/ck-gate.sh [--autotest|--help]

Controlla albero Git, skip tracciati, risultato pytest e baseline dei test eseguiti.
EOF
}

numero_riepilogo() {
  local nome="$1"
  local riga="$2"

  if [[ "$riga" =~ ([0-9]+)[[:space:]]+${nome} ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
  else
    printf '0\n'
  fi
}

autotest() {
  local temporanea scenario uscita atteso output corretti=0 motore_pytest
  # PERCHE' QUI NON C'E' UNA SCORCIATOIA: un autotest che simula pytest invece di
  # lanciarlo dimostra solo che il simulatore funziona. Se non c'e' un pytest vero,
  # l'autotest si ferma e lo dice — non finge di essere passato.
  if python3 -c 'import pytest' >/dev/null 2>&1; then
    motore_pytest="host"
  elif docker image inspect casinoking-backend:latest >/dev/null 2>&1; then
    motore_pytest="docker"
  else
    printf 'ROSSO: autotest impossibile — serve pytest sulla macchina oppure\n' >&2
    printf '       l immagine casinoking-backend:latest. Nessuno dei due presente.\n' >&2
    return 1
  fi
  printf 'autotest: pytest da "%s"\n' "$motore_pytest"
  temporanea="$(mktemp -d)"
  # PERCHE' l'autotest non deve mai lasciare un falso repository o un report nel progetto vero.
  trap 'rm -rf "${temporanea:-}"' EXIT

  crea_repo() {
    local destinazione="$1"
    mkdir -p "$destinazione/scripts" "$destinazione/tests"
    cp "${BASH_SOURCE[0]}" "$destinazione/scripts/ck-gate.sh"
    chmod +x "$destinazione/scripts/ck-gate.sh"
    cat > "$destinazione/tests/test_banali.py" <<'EOF'
def test_uno():
    assert True

def test_due():
    assert True

def test_tre():
    assert True
EOF
    cat > "$destinazione/gate-baseline.json" <<'EOF'
{"test_eseguiti_minimo": 3, "test_raccolti_minimo": 3, "filtro_marcatori": "", "aggiornata_il": "2026-09-04", "motivo": "autotest", "ritirati": []}
EOF
    git -C "$destinazione" init -q
    git -C "$destinazione" config user.email "ck-gate@example.invalid"
    git -C "$destinazione" config user.name "ck-gate autotest"
    git -C "$destinazione" add .
    git -C "$destinazione" commit -qm "fixture autotest"
  }

  esegui_scenario() {
    local nome="$1"
    local previsto="$2"
    local verifica="$3"
    local repo="$temporanea/$nome"
    local log="$temporanea/$nome.log"

    crea_repo "$repo"
    case "$nome" in
      baseline)
        sed -i '/def test_tre/,+1d' "$repo/tests/test_banali.py"
        git -C "$repo" add tests/test_banali.py
        git -C "$repo" commit -qm "rimuove test per scenario baseline"
        ;;
      skip)
        cat >> "$repo/tests/test_banali.py" <<'EOF'

import pytest

@pytest.mark.skip
def test_skip_muto():
    assert True
EOF
        git -C "$repo" add tests/test_banali.py
        git -C "$repo" commit -qm "aggiunge skip muto"
        ;;
      sporco)
        printf '\n# modifica non committata\n' >> "$repo/tests/test_banali.py"
        ;;
      rosso)
        cat >> "$repo/tests/test_banali.py" <<'EOF'

def test_che_fallisce():
    assert False
EOF
        git -C "$repo" add tests/test_banali.py
        git -C "$repo" commit -qm "aggiunge un test che fallisce"
        ;;
      modulo)
        # Una riga sola in cima al file, senza chiocciola, spegne tutti i test dentro.
        sed -i '1i import pytest\npytestmark = pytest.mark.skip(reason="spengo tutto")' "$repo/tests/test_banali.py"
        git -C "$repo" add tests/test_banali.py
        git -C "$repo" commit -qm "silenzia il modulo intero"
        ;;
      manomessa)
        # L'AGGIRAMENTO PIU' SUBDOLO: abbasso i minimi e cancello i test nello
        # STESSO commit, cosi' l'albero resta pulito e i minimi nuovi sono rispettati.
        sed -i '/def test_tre/,+1d' "$repo/tests/test_banali.py"
        cat > "$repo/gate-baseline.json" <<'EOF'
{"test_eseguiti_minimo": 2, "test_raccolti_minimo": 2, "filtro_marcatori": "", "aggiornata_il": "2026-09-04", "motivo": "abbassata di nascosto", "ritirati": []}
EOF
        git -C "$repo" add tests/test_banali.py gate-baseline.json
        git -C "$repo" commit -qm "abbassa la baseline e toglie un test, tutto insieme"
        ;;
    esac

    local comando_pytest
    if [[ "$motore_pytest" == "host" ]]; then
      comando_pytest="python3 -m pytest -q"
    else
      comando_pytest="docker run --rm -v ${repo}:/w -w /w casinoking-backend:latest python -m pytest -q"
    fi

    if (cd "$repo" && CK_GATE_TEST_CMD="$comando_pytest" ./scripts/ck-gate.sh) >"$log" 2>&1; then
      uscita=0
    else
      uscita=$?
    fi

    if [[ "$uscita" == "$previsto" ]] && grep -Fq "$verifica" "$log"; then
      printf '[OK] scenario %s\n' "$nome"
      corretti=$((corretti + 1))
    else
      printf '[ERRORE] scenario %s: uscita=%s, attesa=%s, controllo=%s\n' \
        "$nome" "$uscita" "$previsto" "$verifica"
      sed -n '1,120p' "$log"
    fi
  }

  esegui_scenario verde 0 'VERDE'
  esegui_scenario baseline 1 'BASELINE NON CALATA: ROSSO'
  esegui_scenario skip 1 'NESSUNO SKIP MUTO: ROSSO'
  esegui_scenario sporco 1 'ALBERO PULITO: ROSSO'
  esegui_scenario rosso 1 'SUITE VERDE: ROSSO'
  esegui_scenario manomessa 1 'BASELINE MANOMESSA: ROSSO'
  esegui_scenario modulo 1 'NESSUNO SKIP MUTO: ROSSO'

  printf '%s/7 scenari corretti\n' "$corretti"
  [[ "$corretti" -eq 7 ]]
}

case "${1:-}" in
  --help|-h)
    uso
    exit 0
    ;;
  --autotest)
    autotest
    exit $?
    ;;
  '')
    ;;
  *)
    uso >&2
    exit 1
    ;;
esac

cd "$RADICE"
OUTPUT_TEST="$(mktemp)"
trap 'rm -f "$OUTPUT_TEST"' EXIT
RIGHE=()
VIOLAZIONI=()
verde=1

# PERCHE' il gate deve fotografare lo stato prima di scrivere il suo report:
# il report e' una prova del controllo, non una modifica che deve falsarne l'esito.
stato_git="$(git status --porcelain)"
if [[ -z "$stato_git" ]]; then
  RIGHE+=("ALBERO PULITO: VERDE (0 file toccati)")
else
  numero_file="$(printf '%s\n' "$stato_git" | wc -l | tr -d ' ')"
  RIGHE+=("ALBERO PULITO: ROSSO (${numero_file} file toccati)")
  VIOLAZIONI+=("File toccati:" "$stato_git")
  verde=0
fi

# PERCHE' grep E NON ripgrep: `rg` su questa macchina vive dentro ~/.kimi-code/bin/,
# cioe' dipende dall'installazione di un altro motore. Se sparisce, `rg ... || true`
# non trova nulla e il gate stampa "NESSUNO SKIP MUTO: VERDE" — un falso verde dentro
# lo strumento che esiste apposta per impedire i falsi verdi. grep c'e' sempre.
# PERCHE' L'ESPRESSIONE NON RICHIEDE LA CHIOCCIOLA: `pytestmark = pytest.mark.skip(...)`
# a livello di modulo silenzia un FILE INTERO senza mai scrivere "@". Pretendere la
# chiocciola lasciava aperta la scorciatoia piu' economica di tutte: una riga in cima.
# Il prezzo e' qualche falso positivo (una riga di commento che cita pytest.mark.skip
# viene segnalata): sbagliare verso il rosso va bene, verso il verde no.
#
# PERCHE' git ls-files E NON "tests/": esiste anche backend/tests/, e una cartella
# rinominata sfuggirebbe a un percorso cablato. Si guardano TUTTI i file di test
# tracciati, ovunque siano.
FILE_TEST=()
while IFS= read -r percorso; do
  [[ -n "$percorso" ]] && FILE_TEST+=("$percorso")
done < <(git ls-files -- '*test_*.py' '*conftest.py' 2>/dev/null || true)

skip_muti=0
while IFS=: read -r file riga contenuto; do
  [[ -n "$file" ]] || continue
  inizio=$((riga - 2))
  (( inizio < 1 )) && inizio=1
  if ! sed -n "${inizio},${riga}p" "$file" | grep -Eq '#[[:space:]]*IMPEGNO:[[:space:]]*[A-Z]{2,5}-[0-9]+'; then
    VIOLAZIONI+=("Skip muto: ${file}:${riga}")
    skip_muti=$((skip_muti + 1))
  fi
done < <(if [[ ${#FILE_TEST[@]} -gt 0 ]]; then grep -HnE 'pytest\.mark\.(skip|xfail)|pytest\.skip\(|unittest\.skip' "${FILE_TEST[@]}" 2>/dev/null || true; fi)

if [[ ${#FILE_TEST[@]} -eq 0 ]]; then
  RIGHE+=("NESSUNO SKIP MUTO: ROSSO (nessun file di test tracciato da git)")
  VIOLAZIONI+=("Nessun file di test tracciato: non c'e' niente da controllare")
  verde=0
elif [[ "$skip_muti" -eq 0 ]]; then
  RIGHE+=("NESSUNO SKIP MUTO: VERDE (0 violazioni)")
else
  RIGHE+=("NESSUNO SKIP MUTO: ROSSO (${skip_muti} violazioni)")
  verde=0
fi

COMANDO_TEST="${CK_GATE_TEST_CMD:-./scripts/ck-test.sh}"
if bash -c "$COMANDO_TEST" >"$OUTPUT_TEST" 2>&1; then
  uscita_test=0
else
  uscita_test=$?
fi
riepilogo="$(grep -E '([0-9]+[[:space:]]+(passed|failed|error|errors|skipped))' "$OUTPUT_TEST" | tail -n 1 || true)"
passed="$(numero_riepilogo passed "$riepilogo")"
failed="$(numero_riepilogo failed "$riepilogo")"
errori="$(numero_riepilogo 'errors?' "$riepilogo")"
skipped="$(numero_riepilogo skipped "$riepilogo")"

if [[ -z "$riepilogo" ]]; then
  RIGHE+=("SUITE VERDE: ROSSO (riepilogo pytest non interpretabile; exit ${uscita_test})")
  VIOLAZIONI+=("Output pytest senza riepilogo interpretabile:" "$(tail -n 40 "$OUTPUT_TEST")")
  verde=0
elif [[ "$failed" -gt 0 || "$errori" -gt 0 ]]; then
  RIGHE+=("SUITE VERDE: ROSSO (passed=${passed} failed=${failed} error=${errori} skipped=${skipped}; exit ${uscita_test})")
  verde=0
elif [[ "$uscita_test" -ne 0 ]]; then
  # PERCHE': pytest esce !=0 anche senza fallimenti dichiarati — interrotto (2),
  # errore interno (3), uso sbagliato (4), nessun test raccolto (5). Fidarsi solo
  # del riepilogo e ignorare il codice d'uscita e' un falso verde.
  RIGHE+=("SUITE VERDE: ROSSO (nessun fallimento dichiarato ma il comando e' uscito ${uscita_test})")
  VIOLAZIONI+=("Il comando dei test e' uscito ${uscita_test}:" "$(tail -n 20 "$OUTPUT_TEST")")
  verde=0
else
  RIGHE+=("SUITE VERDE: VERDE (passed=${passed} failed=${failed} error=${errori} skipped=${skipped}; exit ${uscita_test})")
fi

# PERCHE' QUESTA FUNZIONE: senza, il gate si aggira in un commit solo — abbasso i
# minimi in gate-baseline.json, cancello i test, committo tutto insieme e l'albero
# risulta pulito. Il numero piu' alto mai committato e' la memoria che lo impedisce.
massimo_storico() {
  local campo="$1" massimo=0 valore commit
  while read -r commit; do
    [[ -n "$commit" ]] || continue
    valore="$(git show "${commit}:gate-baseline.json" 2>/dev/null \
      | sed -nE "s/.*\"${campo}\"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p" | head -n 1)"
    [[ -n "$valore" ]] || continue
    if (( valore > massimo )); then massimo="$valore"; fi
  done < <(git log --format=%H -- gate-baseline.json 2>/dev/null || true)
  printf '%s\n' "$massimo"
}

baseline_file="$RADICE/gate-baseline.json"
# ESEGUITI: gli skipped non contano — e' esattamente il buco da cui si e' passati
# la notte del 3-4/09/2026, silenziando 65 test invece di ripararli.
eseguiti=$((passed + failed + errori))
# RACCOLTI: quanti test ESISTONO. Cancellare un test gia' skippato non abbassa gli
# eseguiti, ma abbassa i raccolti. Servono tutti e due.
raccolti=$((passed + failed + errori + skipped))
if [[ ! -f "$baseline_file" ]]; then
  RIGHE+=("BASELINE NON CALATA: ROSSO (gate-baseline.json mancante; eseguiti=${eseguiti})")
  VIOLAZIONI+=("Baseline mancante: gate-baseline.json")
  verde=0
else
  minimo="$(sed -nE 's/.*"test_eseguiti_minimo"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p' "$baseline_file" | head -n 1)"
  if [[ -z "$minimo" ]]; then
    RIGHE+=("BASELINE NON CALATA: ROSSO (test_eseguiti_minimo non interpretabile; eseguiti=${eseguiti})")
    VIOLAZIONI+=("Baseline non interpretabile: gate-baseline.json")
    verde=0
  else
    minimo_raccolti="$(sed -nE 's/.*"test_raccolti_minimo"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p' "$baseline_file" | head -n 1)"
    : "${minimo_raccolti:=0}"
    storico_ese="$(massimo_storico test_eseguiti_minimo)"
    storico_rac="$(massimo_storico test_raccolti_minimo)"
    if grep -q '"abbassamento_autorizzato"' "$baseline_file"; then
      RIGHE+=("BASELINE ABBASSATA APPOSTA: dichiarato in gate-baseline.json")
    elif [[ "$minimo" -lt "$storico_ese" || "$minimo_raccolti" -lt "$storico_rac" ]]; then
      RIGHE+=("BASELINE MANOMESSA: ROSSO (minimi abbassati: eseguiti ${storico_ese}->${minimo}, raccolti ${storico_rac}->${minimo_raccolti})")
      VIOLAZIONI+=("La baseline e' stata abbassata rispetto al massimo mai committato. Per farlo apposta serve il campo \"abbassamento_autorizzato\" con motivo e impegno.")
      verde=0
    fi
    if [[ "$eseguiti" -lt "$minimo" || "$raccolti" -lt "$minimo_raccolti" ]]; then
      RIGHE+=("BASELINE NON CALATA: ROSSO (eseguiti=${eseguiti}/min ${minimo}, raccolti=${raccolti}/min ${minimo_raccolti})")
      [[ "$eseguiti" -lt "$minimo" ]] && VIOLAZIONI+=("Test eseguiti calati: ${eseguiti} < ${minimo}")
      [[ "$raccolti" -lt "$minimo_raccolti" ]] && VIOLAZIONI+=("Test esistenti calati: ${raccolti} < ${minimo_raccolti} (qualcuno ne ha tolti)")
      verde=0
    else
      RIGHE+=("BASELINE NON CALATA: VERDE (eseguiti=${eseguiti}/min ${minimo}, raccolti=${raccolti}/min ${minimo_raccolti})")
      if [[ "$eseguiti" -gt "$minimo" ]]; then
        RIGHE+=("SUGGERIMENTO BASELINE: eseguiti=${eseguiti} supera minimo=${minimo}; valutare un aumento manuale")
      fi
    fi
  fi
fi

if [[ "$verde" -eq 1 ]]; then
  esito="VERDE"
else
  esito="ROSSO"
fi

contenuto="$esito"
for riga in "${RIGHE[@]}"; do
  contenuto+=$'\n'"$riga"
done
if [[ ${#VIOLAZIONI[@]} -gt 0 ]]; then
  contenuto+=$'\nVIOLAZIONI:'
  for violazione in "${VIOLAZIONI[@]}"; do
    contenuto+=$'\n'"$violazione"
  done
fi

printf '%s\n' "$contenuto"
{
  printf '%s\n' "$contenuto"
  printf 'DATA_ORA: %s\n' "$(date '+%Y-%m-%d %H:%M:%S %z')"
  printf 'UTENTE: %s\n' "$(id -un)"
  printf 'MOTORE: %s\n' "${CK_GATE_MOTORE:-sconosciuto}"
  printf 'COMMIT ULTIMO GIORNO:\n'
  git log --oneline --since='1 day ago' || true
  printf 'FILE TOCCATI:\n'
  if [[ -n "$stato_git" ]]; then
    printf '%s\n' "$stato_git"
  else
    printf '(nessuno)\n'
  fi
} > stato-notte.md

[[ "$verde" -eq 1 ]]
