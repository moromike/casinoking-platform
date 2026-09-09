#!/usr/bin/env bash
# ck-corsia-esclusi.sh — la corsia che il gate NON esegue, ma di cui deve rispondere.
#
# PERCHE' ESISTE. [GENERATO] 9/09/2026: 249 collaudi su 947 — il 26% della suite — erano
# esclusi dal filtro predefinito del gate, e nessun documento lo diceva. Non erano rotti:
# erano invisibili. La differenza fra un verde che significa qualcosa e un verde che
# rassicura sta tutta qui.
#
# PERCHE' NON SONO NEL GATE PRINCIPALE. Hanno bisogno del browser, che su questa macchina
# non c'e'. Metterli nella corsia ordinaria renderebbe il gate rosso per ragioni
# d'ambiente, e un gate rosso per il motivo sbagliato viene disattivato: sarebbe il
# difetto che il gate esiste per impedire.
#
# COSA PRETENDE QUESTO SCRIPT. Non che la corsia sia verde — oggi non lo e'. Pretende che
# i suoi rossi siano ESATTAMENTE quelli dichiarati in gate-baseline.json. Un rosso nuovo
# ferma; un rosso dichiarato che sparisce ferma lo stesso, perche' vuol dire che la lista
# e' vecchia e nessuno l'ha aggiornata.
set -uo pipefail
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RADICE"
BASE="gate-baseline.json"
OUT="artifacts/fase-gate/corsia-esclusi.txt"
mkdir -p artifacts/fase-gate

dichiarati="$(sed -nE 's/.*"il_rosso_noto"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' "$BASE" | head -n 1)"
if [[ -z "$dichiarati" ]]; then
  echo "ROSSO: gate-baseline.json non dichiara 'il_rosso_noto' per la corsia esclusa." >&2
  echo "       Senza la lista dei rossi noti non posso distinguere un guasto nuovo." >&2
  exit 2
fi

./scripts/ck-test.sh --corsia-esclusi > "$OUT" 2>&1
riepilogo="$(grep -E '[0-9]+ (passed|failed|skipped)' "$OUT" | tail -1)"
visti="$(grep -E '^FAILED ' "$OUT" | sed 's/^FAILED //; s/ .*//' | sort -u)"

echo "corsia esclusa: $riepilogo"
echo "rosso dichiarato: $dichiarati"
esito=0

nuovi="$(grep -vxF "$dichiarati" <<< "$visti" || true)"
if [[ -n "$nuovi" ]]; then
  echo "ROSSO — guasti NUOVI, non dichiarati:"; sed 's/^/   /' <<< "$nuovi"; esito=1
fi
if ! grep -qxF "$dichiarati" <<< "$visti"; then
  echo "ROSSO — il rosso dichiarato NON compare piu': o e' stato riparato e la lista va"
  echo "        aggiornata, o non e' stato eseguito. In entrambi i casi la lista mente."
  esito=1
fi

[[ $esito -eq 0 ]] && echo "CORSIA ESCLUSA: VERDE (i rossi sono esattamente quelli dichiarati)"
echo "referto completo: $OUT"
exit $esito
