motore: Codex
modello: gpt-5.6-sol
modalita: scrittura autonoma — PROPOSTA, non applicata
ruolo: proponente
data: 2026-09-07
revisione indipendente: Kimi (verdetto DA CORREGGERE, rilievi recepiti)
sha256: DA-CALCOLARE-DA-ck-provenienza.sh

# Dossier proposto — collegare `ck-censimento.sh` a `ck-gate.sh`

## Perche' serve

Il contratto prescrive che `ck-gate.sh` invochi `ck-censimento.sh` e propaghi il
suo fallimento. La copia attuale di `ck-gate.sh` non contiene quell'invocazione.
Non applico la modifica perche' `ck-gate.sh` e' un file esistente del perimetro
protetto; questo documento deposita soltanto il diff da sottoporre alla catena.

Il diff aggiunge anche l'autotest indispensabile: nel repository finto il
censimento normalmente passa, poi uno scenario lo forza a fallire e pretende
che il gate diventi rosso. Senza questa controprova il collegamento resterebbe
una promessa non misurata.

## Diff proposto, non applicato

Il diff seguente ha hunk `@@` senza numeri di riga: va applicato a mano, non con `git apply`.

```diff
diff --git a/scripts/ck-gate.sh b/scripts/ck-gate.sh
--- a/scripts/ck-gate.sh
+++ b/scripts/ck-gate.sh
@@
   crea_repo() {
@@
     cp "${BASH_SOURCE[0]}" "$destinazione/scripts/ck-gate.sh"
     chmod +x "$destinazione/scripts/ck-gate.sh"
+    printf '#!/usr/bin/env bash\nexit 0\n' > "$destinazione/scripts/ck-censimento.sh"
+    chmod +x "$destinazione/scripts/ck-censimento.sh"
@@
     case "$nome" in
+      censimento)
+        printf '#!/usr/bin/env bash\necho "ROSSO: censimento di prova"\nexit 1\n' \
+          > "$repo/scripts/ck-censimento.sh" ;;
@@
   esegui_scenario verde     0 'VERDE'
+  esegui_scenario censimento 1 'CENSIMENTO: ROSSO'
@@
-  printf '%s/14 scenari corretti\n' "$corretti"
-  [[ "$corretti" -eq 14 ]]
+  printf '%s/15 scenari corretti\n' "$corretti"
+  [[ "$corretti" -eq 15 ]]
@@
 RIGHE=()
 VIOLAZIONI=()
 verde=1
+
+# Il censimento e' parte del gate: un archivio manomesso o una specifica
+# dichiarata troppo vecchia devono rendere rosso anche il comando principale.
+if "$RADICE/scripts/ck-censimento.sh"; then
+  RIGHE+=("CENSIMENTO: VERDE")
+else
+  uscita_censimento=$?
+  RIGHE+=("CENSIMENTO: ROSSO (ck-censimento.sh e' uscito ${uscita_censimento})")
+  VIOLAZIONI+=("ck-censimento.sh ha fallito: eseguire il comando direttamente per il dettaglio")
+  verde=0
+fi
```

## Verifica richiesta dopo l'approvazione

1. `bash -n scripts/ck-gate.sh`
2. `./scripts/ck-gate.sh --autotest`: attesi 15/15 scenari corretti.
3. Forzare temporaneamente `ck-censimento.sh` a uscire non zero nel repository
   finto e verificare la riga `CENSIMENTO: ROSSO` e l'uscita non zero del gate.
