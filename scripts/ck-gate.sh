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
    local repo="$temporanea/$nome" log="$temporanea/$nome.log" comando ambiente="" rip_var=""

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
      missione_assente)
        # GAT-04 senza dichiarazione: il gate non sa da dove misurare e DEVE fermarsi.
        rm -f "$repo/.missione"
        git -C "$repo" commit -qam "toglie la dichiarazione di missione" ;;
      riparazione_pulita)
        # missione di riparazione dichiarata e nessun collaudo toccato: verde.
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "dichiara una riparazione" ;;
      riparazione_toccata)
        # LA PROVA CHE CONTA: in riparazione, un collaudo modificato ferma il gate.
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "dichiara una riparazione"
        printf '\ndef test_aggiunto_durante_la_riparazione():\n    assert True\n' >> "$repo/tests/test_banali.py"
        scrivi_baseline "$repo" "$comando" 3 3 ""
        git -C "$repo" commit -qam "tocca un collaudo mentre ripara" ;;
      ratifica)
        # la via legittima: Michele ratifica nel messaggio di commit. Deve passare.
        # Questo scenario esiste perche' la ratifica ERA ROTTA (SIGPIPE) e nessuno se
        # ne sarebbe accorto: un permesso che non funziona si scopre solo usandolo.
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "dichiara una riparazione"
        printf '\ndef test_cambio_di_specifica():\n    assert True\n' >> "$repo/tests/test_banali.py"
        scrivi_baseline "$repo" "$comando" 3 3 ""
        git -C "$repo" commit -qam "cambio di specifica su un collaudo

ECCEZIONE COLLAUDI RATIFICATA DA MICHELE" ;;
      ratifica_solo_per_i_suoi)
        # AGGIRAMENTO di Codex sol, quinto giro: un commit ratificato rendeva verdi anche
        # i collaudi toccati DOPO da commit senza ratifica. Una firma non e' un
        # lasciapassare a tempo indeterminato.
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "dichiara una riparazione"
        printf '\ndef test_ratificato():\n    assert True\n' >> "$repo/tests/test_banali.py"
        scrivi_baseline "$repo" "$comando" 3 3 ""
        git -C "$repo" commit -qam "cambio di specifica ratificato

ECCEZIONE COLLAUDI RATIFICATA DA MICHELE"
        printf 'def test_altro_file():\n    assert True\n' > "$repo/tests/test_secondo.py"
        git -C "$repo" add tests/test_secondo.py
        scrivi_baseline "$repo" "$comando" 4 4 ""
        git -C "$repo" commit -qam "tocca un ALTRO collaudo senza ratifica" ;;
      riferimento_a_due_passi)
        # AGGIRAMENTO di Codex sol, quinto giro: si sposta `da:` in DUE passaggi, con in
        # mezzo un valore invalido, per spezzare la memoria dello spostamento.
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "dichiara una riparazione"
        printf '\ndef test_nascosto():\n    assert True\n' >> "$repo/tests/test_banali.py"
        scrivi_baseline "$repo" "$comando" 3 3 ""
        git -C "$repo" commit -qam "tocca un collaudo"
        printf 'tipo: riparazione\nda:   RIFERIMENTO_INVALIDO\n' > "$repo/.missione"
        git -C "$repo" commit -qam "passaggio invalido"
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "sposta il riferimento in avanti" ;;
      finestra_lunga)
        # AGGIRAMENTO di Codex sol, sesto giro: i due controlli guardavano solo gli ultimi
        # 20 e 30 commit di .missione. Bastava riscrivere .missione abbastanza volte per
        # far uscire dalla finestra il commit che tocca il collaudo, e poi spostare `da:`.
        # Qui si fa esattamente questo, con 31 passaggi: deve restare ROSSO.
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "dichiara una riparazione"
        printf '\ndef test_sepolto():\n    assert True\n' >> "$repo/tests/test_banali.py"
        scrivi_baseline "$repo" "$comando" 3 3 ""
        git -C "$repo" commit -qam "tocca un collaudo"
        for _i in $(seq 1 31); do
          printf 'tipo: riparazione\nda:   RIFERIMENTO_INVALIDO_%s\n' "$_i" > "$repo/.missione"
          git -C "$repo" commit -qam "rumore $_i"
        done
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "sposta il riferimento oltre la finestra" ;;
      missione_nuova_dopo_riparazione)
        # ROSSO FALSO di Antigravity, sesto giro, riprodotto: finita una riparazione se ne
        # dichiara un'altra spostando `da:` in avanti, SENZA aver toccato nessun collaudo.
        # E' il gesto normale di inizio missione e deve essere VERDE. Prima era rosso, e
        # sarebbe scattato alla prima missione vera dopo la Fase GATE.
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "missione 1: dichiara una riparazione"
        printf '\n# riparato qualcosa di prodotto\n' >> "$repo/prodotto.py"
        git -C "$repo" add prodotto.py 2>/dev/null || true
        git -C "$repo" commit -qam "ripara del prodotto, nessun collaudo toccato"
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "missione 2: nuova riparazione" ;;
      collaudo_spostato_fuori)
        # AGGIRAMENTO di Codex gpt-5.6-sol, nono giro: invece di MODIFICARE un collaudo lo
        # si SPOSTA fuori da tests/, cosi' il nome che git mostra non somiglia piu' a un
        # collaudo. Poi si porta avanti `da:`. Deve essere ROSSO.
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "dichiara una riparazione"
        mkdir -p "$repo/altrove"
        git -C "$repo" mv tests/test_banali.py altrove/spostato.py
        git -C "$repo" commit -qm "sposta un collaudo fuori da tests/"
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "sposta il riferimento in avanti" ;;
      tipo_cambiato_dopo)
        # AGGIRAMENTO di Codex sol, quinto giro: tocco il collaudo durante la
        # riparazione, committo, e in un commit SEPARATO dichiaro "sviluppo".
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "dichiara una riparazione"
        printf '\ndef test_furtivo():\n    assert True\n' >> "$repo/tests/test_banali.py"
        scrivi_baseline "$repo" "$comando" 3 3 ""
        git -C "$repo" commit -qam "tocca un collaudo durante la riparazione"
        sed -i 's/^tipo: riparazione/tipo: sviluppo/' "$repo/.missione"
        git -C "$repo" commit -qam "cambia idea: dice che era sviluppo" ;;
      variabile_ignorata)
        # AGGIRAMENTO di Codex sol, quarto giro: CK_RIPARAZIONE_DA=HEAD veniva letta
        # PRIMA di .missione e saltava i controlli anti-manomissione. Nel gate la
        # variabile non deve piu' contare: senza .missione si e' ROSSI comunque.
        rm -f "$repo/.missione"
        git -C "$repo" commit -qam "toglie la dichiarazione"
        rip_var="HEAD" ;;
      riferimento_alla_punta)
        # AGGIRAMENTO di Codex sol, terzo giro: tocco un collaudo, lo committo, POI
        # dichiaro "da: HEAD". Il controllo diceva verde perche' da li' non era stato
        # toccato niente. Un riferimento che coincide con la punta non misura nulla.
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "dichiara una riparazione"
        printf '\ndef test_infilato():\n    assert True\n' >> "$repo/tests/test_banali.py"
        scrivi_baseline "$repo" "$comando" 3 3 ""
        git -C "$repo" commit -qam "tocca un collaudo"
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "sposta il riferimento sulla punta" ;;
      dichiarazione_col_collaudo)
        # L'ALTRO AGGIRAMENTO: dichiaro "sviluppo" e tocco il collaudo NELLO STESSO
        # commit. Cambiare la regola e cio' che la regola giudica, insieme.
        printf 'tipo: riparazione\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        git -C "$repo" commit -qam "dichiara una riparazione"
        printf '\ndef test_insieme():\n    assert True\n' >> "$repo/tests/test_banali.py"
        printf 'tipo: sviluppo\nda:   %s\n' "$(git -C "$repo" rev-parse HEAD)" > "$repo/.missione"
        scrivi_baseline "$repo" "$comando" 3 3 ""
        git -C "$repo" commit -qam "dichiara sviluppo e tocca un collaudo insieme" ;;
      autorizzazione_vecchia)
        # Abbasso i minimi appoggiandomi a un'autorizzazione che parla di ALTRO.
        # E' l'aggiramento con cui Codex sol ha bocciato GAT-06: prima restava verde.
        sed -i '/def test_tre/,+1d' "$repo/tests/test_banali.py"
        printf '{\n  "test_eseguiti_minimo": 1,\n  "test_raccolti_minimo": 1,\n  "comando_test": "%s",\n  "abbassamento_autorizzato": {"campo": "test_raccolti_minimo", "da": 589, "a": 587, "impegno": "BON-05", "perche": "vecchia, per un altro abbassamento"},\n  "ritirati": []\n}\n' "$comando" > "$repo/gate-baseline.json"
        git -C "$repo" commit -qam "abbassa i minimi con un'autorizzazione vecchia" ;;
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

    if (cd "$repo" && CK_GATE_TEST_CMD="$ambiente" CK_RIPARAZIONE_DA="$rip_var" ./scripts/ck-gate.sh) >"$log" 2>&1; then
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
  # I CINQUE NATI IL 9/09/2026. I primi quattro sorvegliano GAT-04, che prima non era
  # coperto da nessuno scenario: un controllo senza scenario e' un controllo di cui
  # nessuno sa se funziona. Il quinto chiude l'aggiramento con cui Codex sol ha bocciato
  # GAT-06 — un'autorizzazione vecchia che spegneva il cricchetto per sempre.
  esegui_scenario missione_assente       1 'nessuna missione dichiarata'
  esegui_scenario riparazione_pulita     0 'VERDE'
  esegui_scenario riparazione_toccata    1 'COLLAUDI INTOCCABILI: ROSSO'
  esegui_scenario ratifica               0 'con ratifica di Michele'
  esegui_scenario autorizzazione_vecchia 1 'BASELINE MANOMESSA'
  # I DUE AGGIRAMENTI DEL TERZO GIRO, sorvegliati perche' non tornino.
  esegui_scenario riferimento_alla_punta     1 'SPOSTATO IN AVANTI'
  esegui_scenario dichiarazione_col_collaudo 1 'NELLO STESSO commit'
  esegui_scenario variabile_ignorata         1 'nessuna missione dichiarata'
  esegui_scenario tipo_cambiato_dopo         1 'COLLAUDI INTOCCABILI: ROSSO'
  esegui_scenario ratifica_solo_per_i_suoi   1 'senza ratifica'
  esegui_scenario riferimento_a_due_passi    1 'SPOSTATO IN AVANTI'
  # L'AGGIRAMENTO DEL SESTO GIRO: fare rumore su .missione finche' il commit colpevole
  # esce dalla finestra che il controllo guardava.
  esegui_scenario finestra_lunga             1 'SPOSTATO IN AVANTI'
  # IL ROSSO FALSO: dichiarare una missione nuova non e' un imbroglio, e deve passare.
  esegui_scenario missione_nuova_dopo_riparazione 0 'VERDE'
  # NONO GIRO: spostare un collaudo fuori da tests/ invece di modificarlo.
  esegui_scenario collaudo_spostato_fuori    1 'COLLAUDI INTOCCABILI: ROSSO'

  printf '%s/28 scenari corretti\n' "$corretti"
  [[ "$corretti" -eq 28 ]]
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
  # UNA PORTA SOLA, E CON LA STORIA DIETRO.
  # Aggiramento di Codex sol, quarto giro: `CK_RIPARAZIONE_DA=HEAD` veniva letta PRIMA
  # di .missione e saltava entrambi i controlli anti-manomissione. Era lo stesso trucco
  # del `da: HEAD`, entrato da un'altra porta.
  # La ragione per cui la variabile non puo' valere quanto il file: il file VIVE IN GIT,
  # quindi si puo' vedere se il riferimento e' stato spostato in avanti o cambiato
  # insieme a un collaudo. Una variabile d'ambiente non ha storia: qualunque valore
  # dichiari, non c'e' modo di sapere se e' stato scelto prima o dopo il fatto.
  # Percio': nel GATE conta solo .missione. La variabile resta utile in
  # `--collaudi-intoccabili`, come strumento di diagnosi, e li' lo dice.
  local ref="" tipo=""
  if [[ "${CK_DIAGNOSI_COLLAUDI:-0}" == "1" && -n "${CK_RIPARAZIONE_DA:-}" ]]; then
    ref="$CK_RIPARAZIONE_DA"
    printf 'COLLAUDI INTOCCABILI: MODO DIAGNOSI (riferimento da variabile, senza storia).\n'
    printf '   Non vale come verdetto: nel gate conta solo il file .missione.\n'
  fi
  if [[ -z "$ref" && -f .missione ]]; then
    tipo="$(grep -oP '^tipo:\s*\K\S+' .missione 2>/dev/null || true)"
    ref="$(grep -oP '^da:\s*\K\S+' .missione 2>/dev/null || true)"
    # DUE CONTROLLI SULLA DICHIARAZIONE STESSA, e vanno fatti PRIMA di guardare il
    # tipo: se si potesse barare cambiando la dichiarazione, guardare il tipo dopo non
    # servirebbe a niente. Entrambi gli aggiramenti sono di Codex sol, terzo giro di
    # GAT-06, e li ha eseguiti davvero prima di scriverli.
    #
    # (a) LA DICHIARAZIONE E IL COLLAUDO NELLO STESSO COMMIT:
    #     git add .missione tests/... && git commit -m 'dichiara sviluppo e tocca un test'
    #     Cambiare la regola e cio' che la regola giudica, insieme, e' riscrivere le
    #     regole durante la partita. Stessa idea dello scenario "manomessa".
    insieme=""
    while IFS= read -r cid; do
      [[ -z "$cid" ]] && continue
      # Il commit INIZIALE di un repository crea per forza tutto insieme: la
      # dichiarazione e i collaudi nascono nello stesso momento, e non e' barare.
      # Si guardano solo i commit che hanno un genitore.
      git rev-parse --verify "${cid}^" >/dev/null 2>&1 || continue
      f="$(git show --name-only --format= "$cid" 2>/dev/null || true)"
      if grep -qE '(^|/)tests?/' <<< "$f"; then insieme+="$cid "; fi
    done <<< "$(git log --format=%H -- .missione 2>/dev/null || true)"
    if [[ -n "$insieme" ]]; then
      printf 'COLLAUDI INTOCCABILI: ROSSO — .missione e un collaudo cambiati NELLO STESSO commit:\n'
      printf '   %s\n' "$insieme"
      printf '   Cambiare la regola e cio che la regola giudica, insieme, e riscrivere le\n'
      printf '   regole durante la partita.\n'
      return 1
    fi
    #
    # (b) IL PUNTO DI PARTENZA SPOSTATO IN AVANTI: si tocca un collaudo, lo si committa,
    #     poi si riscrive `da:` su un commit successivo — e il controllo non vede piu'
    #     niente perche' guarda solo da li' in poi. Se il nuovo `da` discende dal
    #     vecchio, il riferimento e' stato spostato in avanti.
    # SI GUARDANO TUTTI I VALORI PASSATI, non solo l'ultimo.
    # Aggiramento di Codex sol, quinto giro: si sposta `da:` in due passaggi, mettendo in
    # mezzo un valore INVALIDO. Il confronto con la sola versione precedente perdeva la
    # memoria dello spostamento. Ora si confronta con OGNI valore mai dichiarato: se il
    # riferimento di adesso discende da uno qualunque di quelli, e' stato spostato avanti.
    # AGGIRAMENTO di Codex sol, sesto giro, riprodotto: "tutti i valori" era una bugia del
    # commento — il codice diceva `git log -30`, e con 31 modifiche di .missione il
    # riferimento originario usciva dalla finestra e il verde tornava. Stessa cosa al
    # controllo (a), che diceva `-20`. Ora nessuno dei due ha un tetto.
    # PERCHE' NON COSTA NIENTE: [GENERATO] in questo repository UN SOLO commit tocca
    # .missione, e una scansione completa costa meno di 0,01 s. Il tetto non proteggeva da
    # un costo, apriva una porta: bastava fare rumore abbastanza a lungo per uscirne.
    # Lo scenario `finestra_lunga` sorveglia che non torni.
    #
    # FIN DOVE ARRIVA QUESTA MEMORIA, detto con precisione perche' il difetto di partenza
    # era proprio un commento che prometteva piu' di quanto il codice mantenesse.
    # "Tutti i valori mai dichiarati" vuol dire: tutti quelli nella storia RAGGIUNGIBILE
    # da HEAD per questo percorso. Provato il 9/09/2026: cancellare o rinominare .missione
    # NON nasconde niente (i commit visti sono passati da 4 a 6, e il gate e' rimasto
    # rosso). Resta fuori portata una RISCRITTURA della storia o un ramo orfano: li' i
    # vecchi valori diventano irraggiungibili. Rilievo di Codex sol e Antigravity, settimo
    # giro. Non e' riparabile con git come unica fonte, e va nel debito dichiarato: chi
    # riscrive la storia condivisa sta gia' facendo una cosa che si vede.
    if [[ -n "$ref" ]] && git rev-parse --verify "$ref" >/dev/null 2>&1; then
      for c_storia in $(git log --format=%H -- .missione 2>/dev/null || true); do
        da_vecchio="$(git show "${c_storia}:.missione" 2>/dev/null | grep -oP '^da:\s*\K\S+' || true)"
        [[ -z "$da_vecchio" || "$da_vecchio" == "HEAD" || "$da_vecchio" == "$ref" ]] && continue
        git rev-parse --verify "$da_vecchio" >/dev/null 2>&1 || continue
        if git merge-base --is-ancestor "$da_vecchio" "$ref" 2>/dev/null; then
          # SPOSTARE IL RIFERIMENTO IN AVANTI NON E' DI PER SE' UN IMBROGLIO.
          # ROSSO FALSO trovato da Antigravity il 9/09/2026 e RIPRODOTTO — e riprodotto
          # anche sul codice PRIMA di questa riparazione, quindi NON e' stato il taglio
          # del tetto a causarlo: c'era gia', e il tetto lo faceva solo scadere dopo 30
          # commit. Il gesto piu' normale del mondo — finisce una riparazione, ne comincia
          # un'altra e si scrive `da: HEAD` — faceva ROSSO. Cioe' il gate sarebbe diventato
          # rosso alla PROSSIMA missione, per un motivo che non c'entra niente. E un gate
          # rosso per il motivo sbagliato viene disattivato: e' la lezione del 5/09.
          #
          # LA DOMANDA GIUSTA NON E' "il riferimento e' stato spostato" MA "lo spostamento
          # NASCONDE QUALCOSA". Si guarda l'intervallo scavalcato: se li' dentro c'e' un
          # collaudo toccato senza la ratifica di Michele, lo spostamento serviva a
          # nasconderlo ed e' rosso. Se non c'e' niente da nascondere, e' semplicemente una
          # missione nuova, e dev'essere verde.
          nascosti=""
          while IFS= read -r f_nasc; do
            [[ -z "$f_nasc" ]] && continue
            for c_nasc in $(git log --format=%H "$da_vecchio".."$ref" -- "$f_nasc" 2>/dev/null || true); do
              msg_nasc="$(git log -1 --format=%B "$c_nasc" 2>/dev/null || true)"
              grep -q 'ECCEZIONE COLLAUDI RATIFICATA DA MICHELE' <<< "$msg_nasc" || nascosti+="$f_nasc "
            done
          done <<< "$(git diff --name-only --no-renames "$da_vecchio" "$ref" 2>/dev/null | grep -E '(^|/)tests?/|(^|/)test_[^/]*\.py$|_test\.py$' | sort -u || true)"
          if [[ -n "$nascosti" ]]; then
            printf 'COLLAUDI INTOCCABILI: ROSSO — il punto di partenza e stato SPOSTATO IN AVANTI\n'
            printf '   da %s a %s, e cosi facendo NASCONDE dei collaudi toccati senza ratifica:\n' "$da_vecchio" "$ref"
            printf '   %s\n' "$nascosti"
            printf '   (Guardo TUTTI i valori mai dichiarati, non solo il precedente: mettere in\n'
            printf '   mezzo un valore invalido non cancella la memoria dello spostamento.)\n'
            return 1
          fi
        fi
      done
    fi

    # UNA VOLTA RIPARAZIONE, RIPARAZIONE PER TUTTO L'INTERVALLO.
    # Aggiramento di Codex sol, quinto giro: si tocca un collaudo durante una
    # riparazione, si committa, e POI — in un commit SEPARATO, quindi fuori dal controllo
    # "nello stesso commit" — si cambia .missione in "tipo: sviluppo". Il controllo
    # usciva subito con NON APPLICABILE.
    # Il tipo che conta non e' quello di ADESSO: e' quello dichiarato nell'intervallo che
    # si sta giudicando. Se in un qualunque punto dell'intervallo la missione era una
    # riparazione, il divieto vale per tutto l'intervallo. Cambiare idea a posteriori su
    # che lavoro si stava facendo e' la stessa cosa che spostare il traguardo.
    if [[ "$tipo" != "riparazione" && -n "$ref" ]] && git rev-parse --verify "$ref" >/dev/null 2>&1; then
      storia_tipo="$(git show "${ref}:.missione" 2>/dev/null | grep -oP '^tipo:\s*\K\S+' || true)"
      for c in $(git log --format=%H "$ref"..HEAD -- .missione 2>/dev/null || true); do
        t="$(git show "${c}:.missione" 2>/dev/null | grep -oP '^tipo:\s*\K\S+' || true)"
        [[ "$t" == "riparazione" ]] && storia_tipo="riparazione"
      done
      if [[ "$storia_tipo" == "riparazione" ]]; then
        printf 'COLLAUDI INTOCCABILI: la missione era dichiarata RIPARAZIONE dentro questo\n'
        printf '   intervallo, e ora .missione dice "%s". Vale la dichiarazione originale.\n' "${tipo:-vuoto}"
        tipo="riparazione"
      fi
    fi

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
  # IL RIFERIMENTO NON PUO' ESSERE AUTOCERTIFICATO A PIACERE. Aggiramento trovato da
  # Codex sol al terzo giro di GAT-06: si tocca un collaudo, lo si committa, POI si
  # scrive `da: HEAD` — e il controllo dice verde perche' "da li' non e' stato toccato
  # niente". Un riferimento che coincide con la punta non misura nulla.
  if ! git rev-parse --verify "$ref" >/dev/null 2>&1; then
    printf 'COLLAUDI INTOCCABILI: ROSSO (CK_RIPARAZIONE_DA=%s non e un commit valido)\n' "$ref"
    return 1
  fi
  local toccati
  # --no-renames E' LA DIFFERENZA FRA VEDERE E NON VEDERE.
  # AGGIRAMENTO di Codex gpt-5.6-sol, nono giro, riprodotto: si SPOSTA un collaudo fuori
  # da tests/ (git mv tests/integration/X.py backend/qualcosa/Y.py) e poi si porta avanti
  # `da:`. Git riconosce lo spostamento e mostra SOLO il nome di destinazione, che non
  # somiglia a un collaudo: il file spariva dal controllo e il gate diceva VERDE.
  # Con --no-renames lo spostamento e' raccontato come cancellazione + creazione, quindi
  # il nome VECCHIO — quello che sta in tests/ — ricompare e il controllo lo vede.
  # Lo sorveglia lo scenario `collaudo_spostato_fuori`.
  toccati="$( { git diff --name-only --no-renames "$ref"; git diff --name-only --no-renames; git ls-files --others --exclude-standard; } \
    | grep -E '(^|/)tests?/|(^|/)test_[^/]*\.py$|_test\.py$' | sort -u || true )"
  # `|| true` NON e' pigrizia: con `set -e`, grep che non trova NIENTE esce 1 e fa
  # abortire la funzione in silenzio. Cioe' il controllo moriva proprio quando il suo
  # esito era VERDE. Stessa famiglia del difetto di ck-difetti-veri.sh del 9/09.
  if [[ -z "$toccati" ]]; then
    printf 'COLLAUDI INTOCCABILI: VERDE (nessun collaudo toccato da %s)\n' "$ref"
    return 0
  fi
  # NIENTE PIPELINE QUI. Con `set -o pipefail`, `git log | grep -q` puo' risultare falso
  # perche' grep chiude appena trova e git log prende SIGPIPE: la ratifica LEGITTIMA
  # veniva rifiutata. Trovato da Codex sol in GAT-06, ed e' la TERZA volta il 9/09 che
  # lo stesso difetto mi frega — dopo ck-difetti-veri.sh e il controllo dell'assenza.
  # Sapere qual e' il difetto non basta a non rifarlo: serve non scrivere quella forma.
  # LA RATIFICA VALE PER CIO' CHE RATIFICA, NON PER IL FUTURO.
  # Aggiramento di Codex sol, quinto giro: un commit ratificato rendeva verdi anche tutti
  # i collaudi toccati DOPO, da commit senza ratifica. Una firma non e' un lasciapassare
  # a tempo indeterminato: vale per i file di QUEL commit.
  # Percio' si guarda file per file: ogni collaudo toccato deve essere stato toccato solo
  # da commit ratificati. Una modifica non committata non e' ratificabile per definizione.
  non_ratificati=""
  while IFS= read -r file_t; do
    [[ -z "$file_t" ]] && continue
    ok_file=1
    commit_del_file="$(git log --format=%H "$ref"..HEAD -- "$file_t" 2>/dev/null || true)"
    if [[ -z "$commit_del_file" ]]; then
      ok_file=0        # toccato ma non committato: nessuna ratifica possibile
    else
      while IFS= read -r cf; do
        [[ -z "$cf" ]] && continue
        msg="$(git log -1 --format=%B "$cf" 2>/dev/null || true)"
        grep -q 'ECCEZIONE COLLAUDI RATIFICATA DA MICHELE' <<< "$msg" || ok_file=0
      done <<< "$commit_del_file"
    fi
    [[ $ok_file -eq 0 ]] && non_ratificati+="$file_t "
  done <<< "$toccati"

  if [[ -z "$non_ratificati" ]]; then
    printf 'COLLAUDI INTOCCABILI: VERDE con ratifica di Michele (%s collaudi toccati,\n' "$(printf '%s\n' "$toccati" | wc -l)"
    printf '   ognuno solo da commit ratificati)\n'
    printf '%s\n' "$toccati" | sed 's/^/   /'
    return 0
  fi
  printf 'COLLAUDI INTOCCABILI: ROSSO — collaudi modificati durante una riparazione\n'
  printf '   senza ratifica: %s\n' "$non_ratificati"
  printf '   (una firma vale per i file di QUEL commit, non per tutto cio che viene dopo)\n'
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
    export CK_DIAGNOSI_COLLAUDI=1
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
  elif ! grep -qx "$timbro" <<< "$SIGLE_AMMESSE"; then
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
  # PERCHE' I NOMI: l'11/09/2026 il gate e' stato rosso con 3 fallimenti in un giro
  # su quattro, e non diceva quali. L'output di pytest sta in un file temporaneo che
  # il gate cancella: senza i nomi un rosso intermittente non si puo' inseguire.
  VIOLAZIONI+=("Collaudi rossi:" "$(grep -E '^(FAILED|ERROR) ' "$OUTPUT_TEST" || echo '(nessuna riga FAILED/ERROR nell output)')")
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
    # UN'AUTORIZZAZIONE VALE PER L'ABBASSAMENTO CHE DESCRIVE, NON PER SEMPRE.
    # Difetto trovato da Codex sol il 9/09/2026 in GAT-06: bastava che il campo
    # "abbassamento_autorizzato" ESISTESSE — anche vecchio di mesi e per un altro
    # motivo — perche' il confronto col massimo storico fosse spento. Prova sua:
    # ha committato minimi 1/1 con la sola vecchia autorizzazione BON-05 e il gate e'
    # rimasto VERDE. Cioe' il cricchetto si poteva riportare a 1.
    # Ora l'autorizzazione deve dire QUALE campo, DA quanto e A quanto, e i tre valori
    # devono corrispondere all'abbassamento in corso.
    aut_campo="$(sed -nE 's/.*"campo"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' "$baseline_file" | head -n 1)"
    aut_da="$(sed -nE 's/.*"da"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p' "$baseline_file" | head -n 1)"
    aut_a="$(sed -nE 's/.*"a"[[:space:]]*:[[:space:]]*([0-9]+).*/\1/p' "$baseline_file" | head -n 1)"
    abbassato_ese=0; abbassato_rac=0
    [[ "$minimo" -lt "$storico_ese" ]] && abbassato_ese=1
    [[ "$minimo_raccolti" -lt "$storico_rac" ]] && abbassato_rac=1

    autorizzazione_valida=0
    if [[ "$abbassato_ese" -eq 1 && "$aut_campo" == "test_eseguiti_minimo" \
          && "$aut_da" == "$storico_ese" && "$aut_a" == "$minimo" ]]; then
      autorizzazione_valida=1
    fi
    if [[ "$abbassato_rac" -eq 1 && "$aut_campo" == "test_raccolti_minimo" \
          && "$aut_da" == "$storico_rac" && "$aut_a" == "$minimo_raccolti" ]]; then
      autorizzazione_valida=1
    fi
    # se si abbassano ENTRAMBI, una sola autorizzazione non basta
    if [[ "$abbassato_ese" -eq 1 && "$abbassato_rac" -eq 1 ]]; then
      autorizzazione_valida=0
    fi

    if [[ "$autorizzazione_valida" -eq 1 ]]; then
      RIGHE+=("BASELINE ABBASSATA APPOSTA: ${aut_campo} da ${aut_da} a ${aut_a}, autorizzato in gate-baseline.json")
    elif [[ "$abbassato_ese" -eq 1 || "$abbassato_rac" -eq 1 ]]; then
      RIGHE+=("BASELINE MANOMESSA: ROSSO (minimi abbassati: eseguiti ${storico_ese}->${minimo}, raccolti ${storico_rac}->${minimo_raccolti})")
      VIOLAZIONI+=("La baseline e' stata abbassata rispetto al massimo mai committato. Serve un \"abbassamento_autorizzato\" che dichiari campo, da e a CORRISPONDENTI a questo abbassamento: un'autorizzazione vecchia o per un altro campo non vale.")
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
