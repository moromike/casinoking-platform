#!/usr/bin/env bash
# controlla-segreti.sh — cancello G4: nessun segreto VERO nei file tracciati.
#
# I segnaposto (change-me...) non bloccano: a quelli pensa il rifiuto all'avvio
# in produzione (SIC-06). Qui si cercano i valori veri, che sono quelli che fanno
# danno se il repository esce di casa.
set -uo pipefail
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RADICE"

NOMI='JWT_SECRET|POSTGRES_PASSWORD|SITE_ACCESS_PASSWORD|MINES_SERVER_SEED|SITE_V3_DRAFT_PREVIEW_SECRET'
ESCLUSI='\.example$|docker-compose\.yml$|controlla-segreti\.sh$|\.md$'

TROVATI="$(git ls-files -z \
  | xargs -0 grep -nIE "(${NOMI})[[:space:]]*[=:][[:space:]]*[\"']?[^\"'[:space:]$}<]" 2>/dev/null \
  | grep -vE "$ESCLUSI" \
  | grep -viE 'change-?me|^[^:]*:[0-9]*:.*=[<]|\$\{|placeholder|example' || true)"

SEGNAPOSTO="$(git ls-files -z \
  | xargs -0 grep -nIE "(${NOMI})[[:space:]]*[=:][[:space:]]*[\"']?change-?me" 2>/dev/null \
  | grep -vE "$ESCLUSI" || true)"

if [[ -n "$SEGNAPOSTO" ]]; then
  echo "[NOTA] Segnaposto nei file tracciati (non bloccano, li ferma SIC-06 all'avvio):"
  echo "$SEGNAPOSTO" | sed 's/^/       /'
fi

if [[ -n "$TROVATI" ]]; then
  echo "[STOP] Segreti con un valore vero in file tracciati:" >&2
  echo "$TROVATI" | sed 's/^/       /' >&2
  exit 1
fi
echo "[OK] Nessun segreto vero nei file tracciati."
