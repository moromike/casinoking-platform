#!/usr/bin/env bash
# segreti.sh — apre il forziere e produce il file d'ambiente per docker compose.
#
# Michele non deve ricordare nessuna password: la chiave sta fuori dal progetto,
# in ~/.config/casinoking/chiave.txt, e gli agenti la leggono da soli. I segreti
# vivono cifrati nel repository.
#
#   ./scripts/segreti.sh            apre il forziere -> stampa il percorso del file
#   ./scripts/segreti.sh --cifra    ricifra il file in chiaro dentro il forziere
set -euo pipefail

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHIAVE="${CASINOKING_CHIAVE:-$HOME/.config/casinoking/chiave.txt}"
FORZIERE="$RADICE/infra/docker/.env.cifrato"
CHIARO="$RADICE/infra/docker/.env"
USCITA="$RADICE/infra/docker/.env.decrypted"

if [[ ! -f "$CHIAVE" ]]; then
  echo "[STOP] Chiave del forziere non trovata: $CHIAVE" >&2
  echo "       Creala con: openssl rand -base64 48 > \"$CHIAVE\" && chmod 600 \"$CHIAVE\"" >&2
  exit 1
fi

if [[ "${1:-}" == "--cifra" ]]; then
  [[ -f "$CHIARO" ]] || { echo "[STOP] Niente da cifrare: $CHIARO non esiste" >&2; exit 1; }
  openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
    -in "$CHIARO" -out "$FORZIERE" -pass "file:$CHIAVE"
  echo "[OK] Forziere aggiornato: $FORZIERE"
  exit 0
fi

if [[ ! -f "$FORZIERE" ]]; then
  echo "[STOP] Forziere non trovato: $FORZIERE" >&2
  echo "       Crealo con: ./scripts/segreti.sh --cifra" >&2
  exit 1
fi

openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -in "$FORZIERE" -out "$USCITA" -pass "file:$CHIAVE"
chmod 600 "$USCITA"
echo "$USCITA"
