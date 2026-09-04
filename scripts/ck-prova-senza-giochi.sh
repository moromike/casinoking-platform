#!/usr/bin/env bash
# ck-prova-senza-giochi.sh — la prova generale dell'estrazione (impegno MAN-04).
#
# COSA DIMOSTRA: che i test di contabilita', sessioni, registro e catalogo restano
# verdi con TUTTI i giochi veri spenti. Se reggono, il giorno in cui i giochi verranno
# portati fuori davvero la suite non crollera' come e' successo il 3-4 settembre 2026,
# quando l'estrazione ha fatto passare i test eseguiti da 572 a 255.
#
# COSA NON DIMOSTRA, e va detto: qui si spengono le ROTTE. Che il codice della
# piattaforma non IMPORTI piu' i moduli dei giochi e' un'altra cosa, e la misura
# tests/contract/test_confine_piattaforma_giochi.py. Spegnere una rotta e' facile;
# districare un import no.
#
#   ./scripts/ck-prova-senza-giochi.sh
#
# Alla fine riaccende i giochi, anche se qualcosa va storto.
set -euo pipefail

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="$RADICE/infra/docker/docker-compose.yml"

riaccendi() {
  echo
  echo "[ripristino] riaccendo i giochi interni"
  CK_GIOCHI_INTERNI=on docker compose -f "$COMPOSE" up -d backend >/dev/null 2>&1 || true
}
trap riaccendi EXIT

echo "[1/3] spengo i giochi interni e riavvio il backend"
CK_GIOCHI_INTERNI=off docker compose -f "$COMPOSE" up -d backend >/dev/null 2>&1
for _ in $(seq 1 30); do
  if curl -fsS -o /dev/null http://localhost:8000/api/v1/health/ready 2>/dev/null; then break; fi
  sleep 2
done

echo "[2/3] le rotte dei giochi devono rispondere 404"
fallite=0
for gioco in mines boxe hi-lo; do
  codice="$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:8000/api/v1/games/$gioco/config")"
  printf '      /games/%-6s/config -> %s\n' "$gioco" "$codice"
  if [[ "$codice" != "404" ]]; then
    echo "      [STOP] i giochi non sono spenti: la prova non varrebbe niente" >&2
    fallite=1
  fi
done
[[ "$fallite" -eq 0 ]] || exit 1

echo "[3/3] la suite, senza un solo gioco vero acceso"
CK_GIOCHI_INTERNI=off "$RADICE/scripts/ck-test.sh"
