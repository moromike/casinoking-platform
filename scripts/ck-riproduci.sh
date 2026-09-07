#!/usr/bin/env bash
# ck-riproduci.sh — tredicesimo comando del gate Fase 9.
#
# Rilancia i dodici comandi precedenti e confronta il loro blocco ESITO con gli
# artefatti depositati. Il confronto non e' una fiducia nel testo: ogni artefatto
# dichiara il suo collaudo e l'impronta SHA-256 di quel collaudo e' ricontrollata.
set -euo pipefail

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Questa e' una lista CHIUSA. I nomi non sono configurabili dall'ambiente: un
# campo economico mascherato renderebbe il confronto inutile. Il controllo sotto
# rende esplicito il rifiuto anche se qualcuno altera la lista nel file.
MASCHERATURE=(IDENTIFICATIVO_GENERATO MARCA_TEMPORALE DURATA)
CAMPI_VIETATI=(IMPORTO SALDO VALUTA CODICE_ESITO NOME_CASO)

# artefatto depositato | unico collaudo che lo produce
ARTEFATTI=(
  "artifacts/fase9/parita-seamless-mines.txt|tests/integration/test_seamless_parita_contabile.py"
  "artifacts/fase9/accrediti-rifiutati.txt|tests/integration/test_seamless_accredito_senza_trattenuta.py"
  "artifacts/fase9/concorrenza.txt|tests/integration/test_seamless_accredito_senza_trattenuta.py"
  "artifacts/fase9/firma-rigiocata.txt|tests/integration/test_seamless_firma_rigiocata.py"
  "artifacts/fase9/ordine-invertito.txt|tests/integration/test_seamless_ordine_operazioni.py"
  "artifacts/fase9/fornitore-sospeso.txt|tests/integration/test_seamless_fornitore_sospeso.py"
  "artifacts/fase9/scrive-davvero.txt|tests/integration/test_seamless_scrive_davvero.py"
  "artifacts/fase9/controlli-di-casa.txt|tests/integration/test_seamless_controlli_di_casa.py"
  "artifacts/fase9/rollback-nativo.txt|tests/integration/test_seamless_rollback.py"
  "artifacts/fase9/migrazione-0058.txt|tests/integration/test_migrazione_0058.py"
  "artifacts/fase9/parita-seamless-mines-rosso.txt|tests/integration/test_seamless_parita_contabile.py"
  "artifacts/fase9/il-collaudo-smaschera-labbozzo.txt|tests/integration/test_seamless_scrive_davvero.py"
  "artifacts/fase9/controlli-di-casa-rosso.txt|tests/integration/test_seamless_controlli_di_casa.py"
  "artifacts/fase9/firma-rigiocata-rosso.txt|tests/integration/test_seamless_firma_rigiocata.py"
)

uso() {
  cat <<'EOF'
Uso: ./scripts/ck-riproduci.sh [--autotest|--help]

Rilancia i dodici comandi del gate Fase 9, verifica l'impronta dei collaudi e
confronta i blocchi --- ESITO --- degli artefatti appena rigenerati.
EOF
}

rosso() { printf 'ROSSO: %s\n' "$*" >&2; }

controlla_allowlist() {
  local campo vietato consentito
  for campo in "${MASCHERATURE[@]}"; do
    consentito=0
    case "$campo" in
      IDENTIFICATIVO_GENERATO|MARCA_TEMPORALE|DURATA) consentito=1 ;;
    esac
    if [[ "$consentito" != 1 ]]; then
      rosso "mascheratura non consentita: $campo"
      return 1
    fi
    for vietato in "${CAMPI_VIETATI[@]}"; do
      if [[ "${campo^^}" == *"$vietato"* ]]; then
        rosso "mascheratura vietata: $campo (non si mascherano importi, saldi, valute, codici di esito o nomi dei casi)"
        return 1
      fi
    done
  done
  [[ " ${MASCHERATURE[*]} " == *" IDENTIFICATIVO_GENERATO "* &&
     " ${MASCHERATURE[*]} " == *" MARCA_TEMPORALE "* &&
     " ${MASCHERATURE[*]} " == *" DURATA "* ]] || {
    rosso "allowlist di mascheratura incompleta"
    return 1
  }
}

estrai_esito() {
  local file="$1"
  awk '
    $0 == "--- ESITO ---" { if (aperto++) exit 3; aperto=1; next }
    $0 == "--- FINE ESITO ---" { if (!aperto || chiuso++) exit 3; chiuso=1; exit }
    aperto && !chiuso { print }
    END { if (aperto != 1 || chiuso != 1) exit 3 }
  ' "$file"
}

maschera_esito() {
  # Si sostituiscono soltanto VALORI con etichetta esplicita; non una parola
  # generica come "id", che potrebbe comparire nel nome di un caso.
  sed -E \
    -e 's/(identificativo_generato|id_generato|request_id|tx_id|nonce)=[^[:space:]]+/\1=<IDENTIFICATIVO_GENERATO>/g' \
    -e 's/(timestamp|marca_temporale)=[^[:space:]]+/\1=<MARCA_TEMPORALE>/g' \
    -e 's/(durata|durata_ms|duration)=[0-9]+([.][0-9]+)?(ms|s|secondi)?/\1=<DURATA>/g'
}

leggi_impronta() {
  local artefatto="$1" chiave="$2"
  awk -v chiave="$chiave" '
    $0 == "--- IMPRONTA COLLAUDO ---" { if (aperto++) exit 3; aperto=1; next }
    $0 == "--- FINE IMPRONTA COLLAUDO ---" { if (!aperto || chiuso++) exit 3; chiuso=1; next }
    aperto && !chiuso && index($0, chiave ": ") == 1 { print substr($0, length(chiave) + 3) }
    END { if (aperto != 1 || chiuso != 1) exit 3 }
  ' "$artefatto"
}

verifica_deposito() {
  local artefatto="$1" collaudo_atteso="$2" collaudo impronta impronta_attesa
  [[ -s "$artefatto" ]] || { rosso "artefatto depositato mancante o vuoto: $artefatto"; return 1; }
  collaudo="$(leggi_impronta "$artefatto" file)" || { rosso "impronta del collaudo malformata in $artefatto"; return 1; }
  impronta_attesa="$(leggi_impronta "$artefatto" sha256)" || { rosso "impronta del collaudo malformata in $artefatto"; return 1; }
  [[ "$collaudo" == "$collaudo_atteso" ]] || { rosso "collaudo dichiarato non ammesso in $artefatto: $collaudo"; return 1; }
  [[ "$impronta_attesa" =~ ^[0-9a-f]{64}$ ]] || { rosso "SHA-256 non valida in $artefatto"; return 1; }
  [[ -f "$collaudo" ]] || { rosso "collaudo dichiarato ma assente: $collaudo"; return 1; }
  impronta="$(sha256sum "$collaudo" | awk '{print $1}')"
  [[ "$impronta" == "$impronta_attesa" ]] || {
    rosso "IMPRONTA DIVERGENTE: $artefatto usa $collaudo (attesa $impronta_attesa, trovata $impronta)"
    return 1
  }
  estrai_esito "$artefatto" >/dev/null || { rosso "blocco ESITO mancante o ambiguo in $artefatto"; return 1; }
}

esegui_gate() {
  local numero="$1"; shift
  if ! "$@"; then
    rosso "comando $numero del gate fallito: $*"
    return 1
  fi
}

esegui_dodici_comandi() {
  esegui_gate 1  ./scripts/ck-gate.sh
  esegui_gate 2  ./scripts/ck-test.sh tests/integration/test_seamless_parita_contabile.py -q
  esegui_gate 3  ./scripts/ck-test.sh tests/integration/test_seamless_accredito_senza_trattenuta.py -q
  esegui_gate 4  ./scripts/ck-test.sh tests/integration/test_seamless_firma_rigiocata.py -q
  esegui_gate 5  ./scripts/ck-test.sh tests/integration/test_seamless_ordine_operazioni.py -q
  esegui_gate 6  ./scripts/ck-test.sh tests/integration/test_seamless_fornitore_sospeso.py -q
  esegui_gate 7  ./scripts/ck-test.sh tests/integration/test_seamless_scrive_davvero.py -q
  esegui_gate 8  ./scripts/ck-test.sh tests/integration/test_seamless_controlli_di_casa.py -q
  esegui_gate 9  ./scripts/ck-test.sh tests/integration/test_seamless_rollback.py -q
  esegui_gate 10 ./scripts/ck-test.sh tests/integration/test_migrazione_0058.py -q
  esegui_gate 11 ./scripts/ck-rosso.sh
  esegui_gate 12 ./scripts/ck-provenienza.sh
}

riproduci() {
  local temporanea voce artefatto collaudo deposito nuovo atteso trovato esito=0
  controlla_allowlist || return 1
  cd "$RADICE"
  temporanea="$(mktemp -d)"
  trap 'rm -rf "${temporanea:-}"' RETURN

  # Il deposito viene fotografato PRIMA di rigenerare gli artefatti, che i dodici
  # comandi sovrascrivono nella loro sede canonica.
  for voce in "${ARTEFATTI[@]}"; do
    IFS='|' read -r artefatto collaudo <<< "$voce"
    verifica_deposito "$artefatto" "$collaudo" || { esito=1; continue; }
    mkdir -p "$temporanea/deposito/$(dirname "$artefatto")"
    cp -- "$artefatto" "$temporanea/deposito/$artefatto"
  done
  [[ "$esito" == 0 ]] || return 1

  esegui_dodici_comandi || return 1

  for voce in "${ARTEFATTI[@]}"; do
    IFS='|' read -r artefatto collaudo <<< "$voce"
    deposito="$temporanea/deposito/$artefatto"
    [[ -s "$artefatto" ]] || { rosso "artefatto appena prodotto mancante o vuoto: $artefatto"; esito=1; continue; }
    # Il file appena scritto deve portare l'impronta del collaudo corrente: non
    # confrontare solo ESITO, altrimenti un test indebolito potrebbe imitare il
    # vecchio riassunto.
    verifica_deposito "$artefatto" "$collaudo" || { esito=1; continue; }
    atteso="$(estrai_esito "$deposito" | maschera_esito)" || { rosso "blocco ESITO non leggibile nel deposito $artefatto"; esito=1; continue; }
    trovato="$(estrai_esito "$artefatto" | maschera_esito)" || { rosso "blocco ESITO non leggibile nell'artefatto nuovo $artefatto"; esito=1; continue; }
    if [[ "$atteso" != "$trovato" ]]; then
      rosso "ESITO DIVERGENTE: $artefatto"
      diff -u <(printf '%s\n' "$atteso") <(printf '%s\n' "$trovato") || true
      esito=1
    else
      printf 'VERDE: ESITO riprodotto: %s\n' "$artefatto"
    fi
  done
  [[ "$esito" == 0 ]]
}

autotest() {
  local temporanea repo log uscita corretti=0
  temporanea="$(mktemp -d)"
  trap 'rm -rf "${temporanea:-}"' RETURN

  crea_repo() {
    local destinazione="$1" test file caso
    mkdir -p "$destinazione/scripts" "$destinazione/tests/integration" "$destinazione/artifacts/fase9"
    cp "${BASH_SOURCE[0]}" "$destinazione/scripts/ck-riproduci.sh"
    chmod +x "$destinazione/scripts/ck-riproduci.sh"
    for test in \
      test_seamless_parita_contabile.py test_seamless_accredito_senza_trattenuta.py \
      test_seamless_firma_rigiocata.py test_seamless_ordine_operazioni.py \
      test_seamless_fornitore_sospeso.py test_seamless_scrive_davvero.py \
      test_seamless_controlli_di_casa.py test_seamless_rollback.py test_migrazione_0058.py; do
      printf '# fixture %s\n' "$test" > "$destinazione/tests/integration/$test"
    done
    cat > "$destinazione/scripts/ck-gate.sh" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
    cat > "$destinazione/scripts/ck-rosso.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
scrivi() {
  local file="$1" test="$2" caso="$3" impronta
  impronta="$(sha256sum "$test" | awk '{print $1}')"
  cat > "$file" <<FINE
--- IMPRONTA COLLAUDO ---
file: $test
sha256: $impronta
--- FINE IMPRONTA COLLAUDO ---
--- ESITO ---
caso=$caso
verdetto=ROSSO_ATTESO
importo=10.00 EUR
saldo_prima=100.00 EUR
saldo_dopo=90.00 EUR
id_generato=$RANDOM
timestamp=$(date +%s)
durata_ms=$RANDOM
--- FINE ESITO ---
FINE
}
scrivi artifacts/fase9/parita-seamless-mines-rosso.txt tests/integration/test_seamless_parita_contabile.py parita_rossa
scrivi artifacts/fase9/il-collaudo-smaschera-labbozzo.txt tests/integration/test_seamless_scrive_davvero.py scrittura_rossa
scrivi artifacts/fase9/controlli-di-casa-rosso.txt tests/integration/test_seamless_controlli_di_casa.py controlli_rossi
scrivi artifacts/fase9/firma-rigiocata-rosso.txt tests/integration/test_seamless_firma_rigiocata.py firma_rossa
EOF
    cat > "$destinazione/scripts/ck-provenienza.sh" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
    cat > "$destinazione/scripts/ck-test.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
test="$1"
scrivi() {
  local file="$1" caso="$2" impronta
  impronta="$(sha256sum "$test" | awk '{print $1}')"
  mkdir -p "$(dirname "$file")"
  cat > "$file" <<FINE
--- IMPRONTA COLLAUDO ---
file: $test
sha256: $impronta
--- FINE IMPRONTA COLLAUDO ---
--- ESITO ---
caso=$caso
verdetto=PASS
importo=10.00 EUR
saldo_prima=100.00 EUR
saldo_dopo=90.00 EUR
id_generato=$RANDOM
timestamp=$(date +%s)
durata_ms=$RANDOM
--- FINE ESITO ---
FINE
}
case "$test" in
  *parita_contabile.py) scrivi artifacts/fase9/parita-seamless-mines.txt parita ;;
  *accredito_senza_trattenuta.py) scrivi artifacts/fase9/accrediti-rifiutati.txt accrediti; scrivi artifacts/fase9/concorrenza.txt concorrenza ;;
  *firma_rigiocata.py) scrivi artifacts/fase9/firma-rigiocata.txt firma ;;
  *ordine_operazioni.py) scrivi artifacts/fase9/ordine-invertito.txt ordine ;;
  *fornitore_sospeso.py) scrivi artifacts/fase9/fornitore-sospeso.txt fornitore ;;
  *scrive_davvero.py) scrivi artifacts/fase9/scrive-davvero.txt scrittura ;;
  *controlli_di_casa.py) scrivi artifacts/fase9/controlli-di-casa.txt controlli ;;
  *rollback.py) scrivi artifacts/fase9/rollback-nativo.txt rollback ;;
  *migrazione_0058.py) scrivi artifacts/fase9/migrazione-0058.txt migrazione ;;
  *) exit 2 ;;
esac
EOF
    chmod +x "$destinazione/scripts/ck-gate.sh" "$destinazione/scripts/ck-rosso.sh" "$destinazione/scripts/ck-provenienza.sh" "$destinazione/scripts/ck-test.sh"
    (
      cd "$destinazione"
      ./scripts/ck-test.sh tests/integration/test_seamless_parita_contabile.py -q
      ./scripts/ck-test.sh tests/integration/test_seamless_accredito_senza_trattenuta.py -q
      ./scripts/ck-test.sh tests/integration/test_seamless_firma_rigiocata.py -q
      ./scripts/ck-test.sh tests/integration/test_seamless_ordine_operazioni.py -q
      ./scripts/ck-test.sh tests/integration/test_seamless_fornitore_sospeso.py -q
      ./scripts/ck-test.sh tests/integration/test_seamless_scrive_davvero.py -q
      ./scripts/ck-test.sh tests/integration/test_seamless_controlli_di_casa.py -q
      ./scripts/ck-test.sh tests/integration/test_seamless_rollback.py -q
      ./scripts/ck-test.sh tests/integration/test_migrazione_0058.py -q
      ./scripts/ck-rosso.sh
    )
  }

  repo="$temporanea/prova-a"
  crea_repo "$repo"
  sed -i 's/saldo_dopo=90.00 EUR/saldo_dopo=91.00 EUR/' "$repo/artifacts/fase9/fornitore-sospeso.txt"
  if (cd "$repo" && ./scripts/ck-riproduci.sh) >"$temporanea/prova-a.log" 2>&1; then uscita=0; else uscita=$?; fi
  log="$temporanea/prova-a.log"
  if [[ "$uscita" == 1 ]] && grep -Fq 'ESITO DIVERGENTE: artifacts/fase9/fornitore-sospeso.txt' "$log"; then
    printf '[OK] Prova A: una riga non mascherata rende rosso l artefatto nominato\n'
    corretti=$((corretti + 1))
  else
    printf '[ERRORE] Prova A: uscita=%s\n' "$uscita"; sed -n '1,120p' "$log"
  fi

  repo="$temporanea/prova-b"
  crea_repo "$repo"
  printf '# asserzione indebolita\n' >> "$repo/tests/integration/test_seamless_fornitore_sospeso.py"
  if (cd "$repo" && ./scripts/ck-riproduci.sh) >"$temporanea/prova-b.log" 2>&1; then uscita=0; else uscita=$?; fi
  log="$temporanea/prova-b.log"
  if [[ "$uscita" == 1 ]] && grep -Fq 'IMPRONTA DIVERGENTE: artifacts/fase9/fornitore-sospeso.txt' "$log"; then
    printf '[OK] Prova B: collaudo indebolito rende rossa la sua impronta\n'
    corretti=$((corretti + 1))
  else
    printf '[ERRORE] Prova B: uscita=%s\n' "$uscita"; sed -n '1,120p' "$log"
  fi
  printf '%s/2 prove di fallimento corrette\n' "$corretti"
  [[ "$corretti" -eq 2 ]]
}

case "${1:-}" in
  --help|-h) uso ;;
  --autotest) autotest ;;
  '') riproduci ;;
  *) uso >&2; exit 2 ;;
esac
