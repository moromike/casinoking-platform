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
Uso: ./scripts/ck-gate.sh [--autotest|--collaudi-intoccabili|--help]

Controlla albero Git, skip tracciati, risultato pytest, baseline dei test eseguiti
e — se armato con CK_RIPARAZIONE_DA=<commit> — che nessun collaudo sia stato
riscritto durante una riparazione (GAT-04).
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
  # PERCHE' QUESTA FUNZIONE E' LA PARTE PIU' IMPORTANTE DELLO SCRIPT: un gate che
  # non sa dimostrare di accorgersi degli aggiramenti non vale niente. Qui si
  # costruisce un repository finto usa-e-getta e si prova a barare in dodici modi.
  local temporanea corretti=0 motore_pytest uscita
  if python3 -c 'import pytest' >/dev/null 2>&1; then
    motore_pytest="host"
  elif docker image inspect casinoking-backend:latest >/dev/null 2>&1; then
    motore_pytest="docker"
  else
    printf 'ROSSO: autotest impossibile — serve pytest sulla macchina oppure\n' >&2
    printf '       l immagine casinoking-backend:latest. Nessuno dei due presente.\n' >&2
    printf 'Un autotest che SIMULA pytest invece di lanciarlo non prova nulla.\n' >&2
    return 1
  fi
  printf 'autotest: pytest da "%s"\n' "$motore_pytest"
  temporanea="$(mktemp -d)"
  trap 'rm -rf "${temporanea:-}"' EXIT

  scrivi_baseline() {
    # $1 destinazione, $2 comando test, $3 eseguiti, $4 raccolti, $5 sigle ammesse
    printf '{\n  "test_eseguiti_minimo": %s,\n' "$3" > "$1/gate-baseline.json"
    if [[ "$4" != "ASSENTE" ]]; then
      printf '  "test_raccolti_minimo": %s,\n' "$4" >> "$1/gate-baseline.json"
    fi
    printf '  "comando_test": "%s",\n  "ritirati": [%s]\n}\n' "$2" "$5" >> "$1/gate-baseline.json"
  }

  crea_repo() {
    local destinazione="$1" comando="$2"
    mkdir -p "$destinazione/scripts" "$destinazione/tests"
    cp "${BASH_SOURCE[0]}" "$destinazione/scripts/ck-gate.sh"
    chmod +x "$destinazione/scripts/ck-gate.sh"
    printf 'def test_uno():\n    assert True\n\ndef test_due():\n    assert True\n\ndef test_tre():\n    assert True\n' \
      > "$destinazione/tests/test_banali.py"
    scrivi_baseline "$destinazione" "$comando" 3 3 ""
    # CAMBIO DI SPECIFICA DICHIARATO, 9/09/2026. Dal fail-closed di GAT-04 il gate
    # PRETENDE che la missione sia dichiarata: senza, non sa da dove misurare e va in
    # rosso. Il repository finto deve quindi soddisfare la stessa precondizione di uno
    # vero, altrimenti i tre scenari che si aspettano un VERDE fallirebbero per una
    # ragione che non c'entra con cio' che provano (misurato: 14/14 -> 11/14).
    #
    # NON e' "adattare la prova al comportamento rotto": la prova continua a pretendere
    # esattamente cio' che pretendeva prima. E' una precondizione nuova del gate, resa
    # esplicita. Se un domani si volesse provare il gate SENZA missione dichiarata, va
    # aggiunto uno scenario apposta che pretenda il ROSSO.
    printf 'tipo: sviluppo\nda:   HEAD\n' > "$destinazione/.missione"
    git -C "$destinazione" init -q
    git -C "$destinazione" config user.email "ck-gate@example.invalid"
    git -C "$destinazione" config user.name "ck-gate autotest"
    git -C "$destinazione" add .
    git -C "$destinazione" commit -qm "fixture autotest"
  }

  esegui_scenario() {
    local nome="$1" previsto="$2" verifica="$3"
    local repo="$temporanea/$nome" log="$temporanea/$nome.log" comando ambiente=""

    if [[ "$motore_pytest" == "host" ]]; then
      comando="python3 -m pytest -q"
    else
      comando="docker run --rm -v ${repo}:/w -w /w casinoking-backend:latest python -m pytest -q"
    fi
    [[ "$nome" == "uscita" ]] && comando="sh -c 'echo 3 passed in 0.01s; exit 3'"

    crea_repo "$repo" "$comando"

    case "$nome" in
      baseline)   # cancellare un test deve far diventare rosso, non verde
        sed -i '/def test_tre/,+1d' "$repo/tests/test_banali.py"
        git -C "$repo" commit -qam "toglie un test" ;;
      skip)       # skip senza timbro
        printf '\nimport pytest\n\n@pytest.mark.skip\ndef test_muto():\n    assert True\n' >> "$repo/tests/test_banali.py"
        git -C "$repo" commit -qam "skip muto" ;;
      sporco)     # modifica non committata
        printf '\n# non committato\n' >> "$repo/tests/test_banali.py" ;;
      rosso)      # un test che fallisce
        printf '\ndef test_che_fallisce():\n    assert False\n' >> "$repo/tests/test_banali.py"
        git -C "$repo" commit -qam "test rosso" ;;
      manomessa)  # abbasso i minimi e tolgo i test NELLO STESSO commit
        sed -i '/def test_tre/,+1d' "$repo/tests/test_banali.py"
        scrivi_baseline "$repo" "$comando" 2 2 ""
        git -C "$repo" commit -qam "abbassa la baseline e toglie un test insieme" ;;
      modulo)     # una riga in cima spegne il file intero, senza chiocciola
        sed -i '1i import pytest\npytestmark = pytest.mark.skip(reason="spengo tutto")' "$repo/tests/test_banali.py"
        git -C "$repo" commit -qam "silenzia il modulo" ;;
      ambiente)   # provo a imporre il comando dei test dall'ambiente
        ambiente='echo "600 passed in 1s"' ;;
      chiave)     # baseline senza la chiave dei raccolti: il controllo si spegnerebbe
        scrivi_baseline "$repo" "$comando" 3 ASSENTE ""
        git -C "$repo" commit -qam "baseline senza test_raccolti_minimo" ;;
      alias)      # `from pytest import mark` + `@mark.skip`: aggirava l'espressione
        printf '\nfrom pytest import mark\n\n@mark.skip\ndef test_con_alias():\n    assert True\n' >> "$repo/tests/test_banali.py"
        git -C "$repo" commit -qam "skip muto tramite alias di importazione" ;;
      condizionale)  # skipif e pytest.skip() dentro un if: precondizioni, non silenziamenti
        printf '\nimport pytest\n\n@pytest.mark.skipif(False, reason="mai")\ndef test_condizionato():\n    assert True\n\ndef test_con_guardia():\n    if False:\n        pytest.skip("ambiente assente")\n    assert True\n' >> "$repo/tests/test_banali.py"
        scrivi_baseline "$repo" "$comando" 5 5 ""
        git -C "$repo" commit -qam "skip condizionali, legittimi" ;;
      timbro)     # timbro inventato, non dichiarato nella baseline
        printf '\nimport pytest\n\n# IMPEGNO: FAKE-1 me lo sono inventato\n@pytest.mark.skip\ndef test_timbrato():\n    assert True\n' >> "$repo/tests/test_banali.py"
        git -C "$repo" commit -qam "timbro inventato" ;;
      timbro_ok)  # IL PERCORSO LEGITTIMO: timbro dichiarato nella baseline -> verde
        printf '\nimport pytest\n\n# IMPEGNO: BON-05 spostato in m-and-m-games\n@pytest.mark.skip\ndef test_timbrato():\n    assert True\n' >> "$repo/tests/test_banali.py"
        scrivi_baseline "$repo" "$comando" 3 3 '"BON-05"'
        git -C "$repo" commit -qam "skip legittimo, impegno dichiarato" ;;
    esac

    if (cd "$repo" && CK_GATE_TEST_CMD="$ambiente" ./scripts/ck-gate.sh) >"$log" 2>&1; then
      uscita=0
    else
      uscita=$?
    fi

    if [[ "$uscita" == "$previsto" ]] && grep -Fq "$verifica" "$log"; then
      printf '[OK] %s\n' "$nome"
      corretti=$((corretti + 1))
    else
      printf '[ERRORE] %s: uscita=%s attesa=%s cercavo="%s"\n' "$nome" "$uscita" "$previsto" "$verifica"
      sed -n '1,40p' "$log"
    fi
  }

  esegui_scenario verde     0 'VERDE'
  esegui_scenario baseline  1 'BASELINE NON CALATA: ROSSO'
  esegui_scenario skip      1 'NESSUNO SKIP MUTO: ROSSO'
  esegui_scenario sporco    1 'ALBERO PULITO: ROSSO'
  esegui_scenario rosso     1 'SUITE VERDE: ROSSO'
  esegui_scenario manomessa 1 'BASELINE MANOMESSA: ROSSO'
  esegui_scenario modulo    1 'NESSUNO SKIP MUTO: ROSSO'
  esegui_scenario uscita    1 "e' uscito 3"
  esegui_scenario ambiente  1 'COMANDO DEI TEST: ROSSO'
  esegui_scenario chiave    1 'test_raccolti_minimo assente'
  esegui_scenario alias     1 'NESSUNO SKIP MUTO: ROSSO'
  esegui_scenario timbro    1 'impegno non dichiarato'
  esegui_scenario timbro_ok 0 'VERDE'
  esegui_scenario condizionale 0 'VERDE'

  printf '%s/14 scenari corretti\n' "$corretti"
  [[ "$corretti" -eq 14 ]]
}

# ---------------------------------------------------------------------------
# GAT-04 — I COLLAUDI NON SI RISCRIVONO DURANTE UNA RIPARAZIONE
#
# PERCHE' ESISTE. L'8/09/2026 tre collaudi sono stati riscritti DAL MOTORE CHE STAVA
# RIPARANDO, perche' accettassero un 500 dove pretendevano un 4xx. La specifica piegata
# al comportamento rotto: la malattia per cui esiste la Fase 9, ricreata dentro la cura.
# La suite restava verde, e il verde era vero — misurava una specifica peggiorata.
#
# PERCHE' VA ARMATO E NON E' SEMPRE ACCESO. Questo controllo non sa distinguere «sto
# riparando e sto barando» da «sto sviluppando e aggiungo collaudi»: la differenza sta
# nell'intenzione della missione, che nel codice non c'e'. Quindi si arma dichiarandola:
#
#   CK_RIPARAZIONE_DA=<commit di inizio missione> ./scripts/ck-gate.sh
#
# Se non e' armato, stampa NON ARMATO — che NON e' un verde. Un controllo spento che
# stampa verde e' peggio di un controllo assente, perche' rassicura.
#
# L'ECCEZIONE la ratifica Michele, e si scrive dove resta: nel messaggio di commit.
# Un collaudo da cambiare davvero e' una DECISIONE DI SPECIFICA, non un dettaglio di
# riparazione.
collaudi_intoccabili() {
  # FAIL-CLOSED dal 9/09/2026, su rilievo (b) di Codex sol in GAT-06: "l'uso ordinario
  # dipende da chi ricorda di passare CK_RIPARAZIONE_DA. E' una segnalazione, non un
  # cricchetto." Aveva ragione. Ora il riferimento si ricava DA SOLO dal tronco, e il
  # controllo e' sempre acceso: senza intervento umano, un collaudo toccato non puo'
  # produrre verde.
  # DA DOVE SI MISURA. Primo tentativo: il file .missione, che dichiara la missione in
  # corso. Poi la variabile d'ambiente. Poi NIENTE: e senza, il gate e' ROSSO.
  #
  # PERCHE' NON IL TRONCO (provato e scartato il 9/09/2026): ricavare il riferimento dal
  # merge-base con main segnalava 45 file di collaudo — il lavoro legittimo dell'intero
  # ramo. Sarebbe stato rosso sempre, e un controllo sempre rosso viene spento: la stessa
  # malattia del gate sempre rosso che GAT-03 esiste per impedire.
  #
  # PERCHE' FAIL-CLOSED (rilievo (b) di Codex sol, GAT-06): finche' dipendeva da chi si
  # ricordava di passare una variabile, era una segnalazione e non un cricchetto.
  # Dichiarare la missione costa due righe; non dichiararla ferma il gate.
  local ref="${CK_RIPARAZIONE_DA:-}" tipo=""
  if [[ -z "$ref" && -f .missione ]]; then
    tipo="$(grep -oP '^tipo:\s*\K\S+' .missione 2>/dev/null || true)"
    ref="$(grep -oP '^da:\s*\K\S+' .missione 2>/dev/null || true)"
    if [[ "$tipo" != "riparazione" ]]; then
      printf 'COLLAUDI INTOCCABILI: NON APPLICABILE (.missione dichiara tipo=%s)\n' "${tipo:-vuoto}"
      printf '   Il divieto vale nelle missioni di RIPARAZIONE: li il collaudo e la specifica\n'
      printf '   da rispettare, non un dettaglio da adattare.\n'
      return 0
    fi
  fi
  if [[ -z "$ref" ]]; then
    printf 'COLLAUDI INTOCCABILI: ROSSO — nessuna missione dichiarata.\n'
    printf '   Non so da dove misurare, quindi non posso dire che nessuno ha toccato i\n'
    printf '   collaudi. Serve un file .missione con due righe:\n'
    printf '       tipo: riparazione|sviluppo\n'
    printf '       da:   <commit di inizio missione>\n'
    printf '   oppure CK_RIPARAZIONE_DA=<commit>.\n'
    return 1
  fi
  if ! git rev-parse --verify "$ref" >/dev/null 2>&1; then
    printf 'COLLAUDI INTOCCABILI: ROSSO (CK_RIPARAZIONE_DA=%s non e un commit valido)\n' "$ref"
    return 1
  fi
  local toccati
  toccati="$( { git diff --name-only "$ref"; git diff --name-only; git ls-files --others --exclude-standard; } \
    | grep -E '(^|/)tests?/|(^|/)test_[^/]*\.py$|_test\.py$' | sort -u || true )"
  # `|| true` NON e' pigrizia: con `set -e`, grep che non trova NIENTE esce 1 e fa
  # abortire la funzione in silenzio. Cioe' il controllo moriva proprio quando il suo
  # esito era VERDE. Stessa famiglia del difetto di ck-difetti-veri.sh del 9/09.
  if [[ -z "$toccati" ]]; then
    printf 'COLLAUDI INTOCCABILI: VERDE (nessun collaudo toccato da %s)\n' "$ref"
    return 0
  fi
  if git log --format=%B "$ref"..HEAD 2>/dev/null | grep -q 'ECCEZIONE COLLAUDI RATIFICATA DA MICHELE'; then
    printf 'COLLAUDI INTOCCABILI: VERDE con ratifica di Michele (%s collaudi toccati)\n' "$(printf '%s\n' "$toccati" | wc -l)"
    printf '%s\n' "$toccati" | sed 's/^/   /'
    return 0
  fi
  printf 'COLLAUDI INTOCCABILI: ROSSO — collaudi modificati durante una riparazione\n'
  printf '%s\n' "$toccati" | sed 's/^/   /'
  printf '   Un collaudo da cambiare e una DECISIONE DI SPECIFICA: la ratifica Michele,\n'
  printf '   con la riga ECCEZIONE COLLAUDI RATIFICATA DA MICHELE nel messaggio di commit.\n'
  return 1
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
  --collaudi-intoccabili)
    cd "$RADICE"
    collaudi_intoccabili
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

# GAT-04: il controllo sui collaudi entra nella sequenza del gate.
# set +e ESPLICITO: collaudi_intoccabili esce 1 (rosso) o 2 (non armato), e con
# `set -e` un'assegnazione da sostituzione di comando che esce != 0 ABORTISCE lo
# script. Senza questo, il gate usciva 2 SEMPRE e l'autotest crollava da 14/14 a
# 0/14. Preso dal criterio "l'autotest non deve calare" entro un minuto: e' la terza
# volta il 9/09 che lo stesso tipo di errore mi frega, e la prima in cui e' un
# controllo automatico a fermarmi invece di un revisore.
set +e
riga_collaudi="$(collaudi_intoccabili)"
esito_collaudi=$?
set -e
RIGHE+=("$riga_collaudi")
if [[ $esito_collaudi -eq 1 ]]; then
  VIOLAZIONI+=("$riga_collaudi")
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
file_spariti=0
while IFS= read -r percorso; do
  [[ -n "$percorso" ]] || continue
  if [[ -f "$percorso" ]]; then
    FILE_TEST+=("$percorso")
  else
    # Tracciato da git ma non sul disco: qualcuno l'ha cancellato senza committare.
    # E' la firma esatta dell'incidente del 3-4/09/2026 (48 file spariti cosi').
    file_spariti=$((file_spariti + 1))
    VIOLAZIONI+=("File di test tracciato ma sparito dal disco: ${percorso}")
  fi
done < <(git ls-files -- '*test_*.py' '*_test.py' '*conftest.py' 2>/dev/null || true)

# KIMI #4 — Le sigle degli impegni ammesse sono SOLO quelle dichiarate in
# gate-baseline.json. Senza questo riscontro, "# IMPEGNO: FAKE-1" stampato in blocco
# su 65 test e' il gesto dell'incidente con un commento in piu': il timbro sarebbe
# una promessa, non una prova. Cosi' invece serve anche un commit sulla baseline,
# che passa dal controllo del massimo storico ed e' visibile a chi rivede.
SIGLE_AMMESSE="$(grep -oE '"[A-Z]{2,5}-[0-9]+"' "$baseline_file" 2>/dev/null | tr -d '"' | sort -u || true)"

# KIMI #6b — grep: 0 = trovato, 1 = nulla trovato, >=2 = ERRORE (file illeggibile,
# permessi, argomenti). Prima un "|| true" rendeva l'errore indistinguibile da
# "nessuna violazione", cioe' un falso verde su scansione parziale.
GREP_SKIP="$(mktemp)"
esito_grep=0
if [[ ${#FILE_TEST[@]} -gt 0 ]]; then
  # AGY, secondo giro: `from pytest import mark` + `@mark.skip` aggirava tutto,
  # perche' l'espressione presumeva il nome del modulo per esteso. Ora si cerca
  # anche la forma con alias, qualunque assegnazione a pytestmark, e l'importazione
  # stessa di skip/mark da pytest — che e' l'abilitatore, ed e' una riga per file.
  # COSA SI PRETENDE DI DICHIARARE, E PERCHE' SOLO QUESTO.
  # Si cercano gli skip INCONDIZIONATI — quelli che scattano sempre:
  #   @pytest.mark.skip / @mark.skip / @pytest.mark.xfail
  #   pytestmark = pytest.mark.skip(...)   (spegne un file intero)
  #   @unittest.skip
  # NON si pretende un timbro su `skipif`, `@unittest.skipIf` e sulle chiamate
  # `pytest.skip("...")` dentro il corpo di una funzione: sono precondizioni
  # d'ambiente ("Chromium non e' installato"), non silenziamenti. Pretenderlo
  # produrrebbe 69 timbri finti, cioe' il gesto dell'incidente con un commento in piu'.
  # La rete che copre il resto e' il conteggio: uno skip incondizionato scritto in
  # qualunque altra forma fa comunque calare i test ESEGUITI sotto la baseline, e il
  # gate diventa rosso di la'. Le due regole si coprono a vicenda.
  # La classe [^a-zA-Z] dopo skip serve a non prendere skipif.
  grep -HnE 'pytest\.mark\.(skip|xfail)([^a-zA-Z]|$)|@mark\.(skip|xfail)([^a-zA-Z]|$)|pytestmark[[:space:]]*=[^#]*mark\.(skip|xfail)([^a-zA-Z]|$)|unittest\.skip([^a-zA-Z]|$)' \
    "${FILE_TEST[@]}" > "$GREP_SKIP" 2>/dev/null || esito_grep=$?
fi

skip_muti=0
sigle_ignote=0
while IFS=: read -r file riga contenuto; do
  [[ -n "$file" && -n "$riga" ]] || continue
  inizio=$((riga - 2))
  if (( inizio < 1 )); then inizio=1; fi
  timbro="$(sed -n "${inizio},${riga}p" "$file" 2>/dev/null \
    | grep -oE '#[[:space:]]*IMPEGNO:[[:space:]]*[A-Z]{2,5}-[0-9]+' \
    | grep -oE '[A-Z]{2,5}-[0-9]+' | head -n 1 || true)"
  if [[ -z "$timbro" ]]; then
    VIOLAZIONI+=("Skip muto: ${file}:${riga}")
    skip_muti=$((skip_muti + 1))
  elif ! printf '%s\n' "$SIGLE_AMMESSE" | grep -qx "$timbro"; then
    VIOLAZIONI+=("Skip con impegno non dichiarato (${timbro}): ${file}:${riga}")
    sigle_ignote=$((sigle_ignote + 1))
  fi
done < "$GREP_SKIP"
rm -f "$GREP_SKIP"

if [[ "$file_spariti" -gt 0 ]]; then
  RIGHE+=("FILE DI TEST SPARITI: ROSSO (${file_spariti} tracciati da git ma non sul disco)")
  verde=0
fi

if [[ ${#FILE_TEST[@]} -eq 0 ]]; then
  RIGHE+=("NESSUNO SKIP MUTO: ROSSO (nessun file di test tracciato da git)")
  VIOLAZIONI+=("Nessun file di test tracciato: non c'e' niente da controllare")
  verde=0
elif [[ "$esito_grep" -ge 2 ]]; then
  RIGHE+=("NESSUNO SKIP MUTO: ROSSO (la scansione e' fallita, grep esce ${esito_grep})")
  VIOLAZIONI+=("La scansione degli skip non e' andata a buon fine: il risultato non e' attendibile.")
  verde=0
elif [[ "$skip_muti" -eq 0 && "$sigle_ignote" -eq 0 ]]; then
  RIGHE+=("NESSUNO SKIP MUTO: VERDE (0 violazioni, ${#FILE_TEST[@]} file esaminati)")
else
  RIGHE+=("NESSUNO SKIP MUTO: ROSSO (${skip_muti} muti, ${sigle_ignote} con impegno non dichiarato)")
  verde=0
fi

COMANDO_TEST="$(sed -nE 's/.*"comando_test"[[:space:]]*:[[:space:]]*"(.*)".*/\1/p' "$baseline_file" 2>/dev/null | head -n 1)"
[[ -n "$COMANDO_TEST" ]] || COMANDO_TEST="./scripts/ck-test.sh"
# LIMITE RESIDUO, dichiarato invece che nascosto: chi puo' committare puo' cambiare
# "comando_test" nella baseline (o ck-test.sh stesso) e falsare la misura. Non e'
# chiudibile con altro codice — chi controlla il repository controlla il gate. La
# differenza che conta e' che ora resta una traccia in git, mentre la variabile
# d'ambiente non ne lasciava nessuna.
if [[ -n "${CK_GATE_TEST_CMD:-}" ]]; then
  RIGHE+=("COMANDO DEI TEST: ROSSO (qualcuno ha provato a imporlo dall'ambiente)")
  VIOLAZIONI+=("CK_GATE_TEST_CMD era impostato nell'ambiente ed e' stato IGNORATO. Il comando dei test si cambia solo in gate-baseline.json, con un commit.")
  verde=0
fi
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
# DESELECTED, aggiunto il 9/09/2026 su rilievo (c) di Codex sol in GAT-06.
# I non selezionati ESISTONO come collaudi: non venivano contati, quindi si poteva
# zittire un collaudo spostandolo in una categoria esclusa dal filtro senza che il
# cricchetto anti-cancellazione se ne accorgesse. [GENERATO] erano 249 su 947 — il 26%
# della suite — e nessun documento lo diceva.
deselezionati="$(numero_riepilogo deselected "$riepilogo")"

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
  RIGHE+=("SUITE VERDE: VERDE (passed=${passed} failed=${failed} error=${errori} skipped=${skipped} deselezionati=${deselezionati}; exit ${uscita_test})")
fi

# ESEGUITI: gli skipped non contano — e' esattamente il buco da cui si e' passati
# la notte del 3-4/09/2026, silenziando 65 test invece di ripararli.
eseguiti=$((passed + failed + errori))
# RACCOLTI: quanti test ESISTONO. Cancellare un test gia' skippato non abbassa gli
# eseguiti, ma abbassa i raccolti. Servono tutti e due.
# E dal 9/09/2026 comprende i DESELEZIONATI: un collaudo escluso dal filtro esiste
# ancora, e prima usciva dal conteggio: era la terza strada per zittire un collaudo
# senza far calare nessun numero — dopo cancellarlo (raccolti) e saltarlo (eseguiti).
raccolti=$((passed + failed + errori + skipped + deselezionati))
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
    if [[ -z "$minimo_raccolti" ]]; then
      # KIMI #2: prima un default a 0 spegneva in silenzio l'unico controllo
      # anti-cancellazione. Una chiave che manca e' un guasto, non un permesso.
      RIGHE+=("BASELINE NON CALATA: ROSSO (test_raccolti_minimo assente o illeggibile)")
      VIOLAZIONI+=("gate-baseline.json non dichiara test_raccolti_minimo: il controllo anti-cancellazione sarebbe spento.")
      verde=0
      minimo_raccolti=999999999
    fi
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

# KIMI #7 — stato-notte.md e' sovrascritto a ogni esecuzione: il referto di un run
# ROSSO sparirebbe al run successivo, e con lui l'unica traccia leggibile di cosa
# era rotto. Se ne tiene una copia datata. NON e' a prova di manomissione (chi puo'
# scrivere nel repo puo' cancellarla): serve a non perdere le prove per distrazione,
# non a resistere a un avversario. La traccia che resiste e' git log.
# La copia e' un di piu': se la cartella non e' scrivibile (var/ e' creata da docker
# e appartiene a root) NON deve far fallire il gate. Un verdetto giusto che esce con
# il codice sbagliato e' un difetto quanto il contrario.
if mkdir -p var/gate 2>/dev/null; then
  cp stato-notte.md "var/gate/stato-notte-$(date '+%Y%m%d-%H%M%S').md" 2>/dev/null || true
fi

[[ "$verde" -eq 1 ]]
