#!/usr/bin/env bash
# ck-firma-approvazione.sh — l'unico passo della catena che deve farlo una persona.
#
# Deposita la cartella della catena (proposta, tre revisioni, misure, approvazione)
# in un commit FIRMATO. La firma chiede la passphrase: e' la sola cosa, in tutta la
# catena REG-01, che nessun motore AI puo' fare al posto di Michele.
#
# NON applica niente. L'applicazione e' il commit successivo, e la fa Claude.
set -euo pipefail

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CARTELLA="missioni/2026-09-07-campi-obbligatori"
cd "$RADICE"

echo
echo "======================================================================"
echo " APPROVAZIONE FIRMATA — campi obbligatori sulle rotte del denaro"
echo "======================================================================"
echo
echo "Ramo:   $(git branch --show-current)"
echo "Chiave: $(git config --get user.signingkey)"
echo
echo "Cosa stai per firmare (nessun file di prodotto viene toccato ora):"
# Se annulla col Ctrl-C, l'indice torna com'era: un ripensamento non deve
# lasciare file in attesa di un commit che nessuno ha voluto.
trap 'git reset -q -- "$CARTELLA" 2>/dev/null || true' INT TERM
git add -- "$CARTELLA"
git diff --cached --stat -- "$CARTELLA"
echo
echo "I cinque testi autorizzati, per impronta:"
grep -E '^\| `(backend|tests)/' "$CARTELLA/APPROVAZIONE.md" | sed 's/^/   /'
echo
echo "Fra un istante ti verra' chiesta la passphrase della chiave di approvazione."
echo "E' quella che hai scelto tu alle 14:25 di oggi. Se non te la ricorda nessuno,"
echo "e' perche' non la sa nessuno: e' esattamente il punto."
echo
read -rp "Premi Invio per firmare, oppure Ctrl-C per annullare. "

git commit -S -m "Approvazione firmata: i campi obbligatori entrano nel modello delle rotte seamless

Michele autorizza l'applicazione dei cinque blocchi del dossier, per impronta.
Catena REG-01 completa: proposta Claude, tre revisioni indipendenti di Kimi (due
bocciature accolte, poi approvata), misura sullo stack acceso 657->663 verdi e
19->13 rossi senza regressioni, e questa firma.

L'applicazione NON e' in questo commit: e' il passo successivo, e si ferma se un
collaudo verde diventa rosso."

echo
echo "--- verifica della firma ---"
STATO="$(git log -1 --format='%G?')"
FIRMATARIO="$(git log -1 --format='%GS')"
if [ "$STATO" = "G" ]; then
  echo "  VERDE: firma valida, firmatario: $FIRMATARIO"
  echo
  echo "  L'anello 4 di REG-01 e' soddisfatto per questa modifica."
  echo "  Torna da Claude: puo' applicare."
  exit 0
else
  echo "  ROSSO: la firma non risulta valida. Stato git: '$STATO'"
  echo "  Riporta questo output a Claude. Il commit c'e' ma NON vale come approvazione."
  exit 1
fi
