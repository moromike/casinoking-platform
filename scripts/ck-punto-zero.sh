#!/usr/bin/env bash
# ck-punto-zero.sh — da niente a un sito giocabile, con un comando.
#
# Distrugge il database e lo ricostruisce da zero, poi crea l'amministratore
# tecnico e pubblica la home. Serve a garantire che il punto di partenza sia
# sempre lo stesso: e' cosi' che si e' scoperto (il 4/09/2026) che le migrazioni
# non creavano il titolo giocabile di Mines.
#
#   ./scripts/ck-punto-zero.sh              chiede conferma
#   ./scripts/ck-punto-zero.sh --conferma   non chiede niente
#
# ATTENZIONE: CANCELLA TUTTI I DATI. Fa una copia prima, ma leggila come
# "posso tornare indietro", non come "non e' successo niente".
set -euo pipefail

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="$RADICE/infra/docker/docker-compose.yml"
COPIE="/home/micheleubuntu/Downloads/CasinoKing/governo/backup"

if [[ "${1:-}" != "--conferma" ]]; then
  echo "Questo comando CANCELLA tutti i dati del database locale."
  read -r -p "Scrivi 'azzera' per procedere: " RISPOSTA
  [[ "$RISPOSTA" == "azzera" ]] || { echo "Annullato."; exit 1; }
fi

mkdir -p "$COPIE"
COPIA="$COPIE/punto-zero-prima-$(date +%Y%m%d-%H%M%S).sql"
if docker compose -f "$COMPOSE" ps --status running --quiet postgres >/dev/null 2>&1; then
  echo "[1/5] Copia di sicurezza..."
  docker compose -f "$COMPOSE" exec -T postgres pg_dump -U casinoking -d casinoking > "$COPIA" 2>/dev/null || true
  [[ -s "$COPIA" ]] && echo "      $COPIA" || { rm -f "$COPIA"; echo "      (database vuoto o non raggiungibile: nessuna copia)"; }
else
  echo "[1/5] Stack spento: nessuna copia da fare."
fi

echo "[2/5] Cancello volumi e ricostruisco..."
docker compose -f "$COMPOSE" down -v >/dev/null 2>&1 || true
"$RADICE/scripts/ck-up.sh" >/dev/null

echo "[3/5] Amministratore tecnico..."
ENVFILE="$("$RADICE/scripts/segreti.sh")"
# --env-file serve alla sostituzione nel file compose, NON passa le variabili
# dentro al contenitore: quelle vanno date esplicitamente con -e.
ADMIN_EMAIL="$(grep -E '^LOCAL_ADMIN_EMAIL=' "$ENVFILE" | cut -d= -f2-)"
ADMIN_PASS="$(grep -E '^LOCAL_ADMIN_PASSWORD=' "$ENVFILE" | cut -d= -f2-)"
[[ -n "$ADMIN_EMAIL" && -n "$ADMIN_PASS" ]] || {
  echo "[STOP] LOCAL_ADMIN_EMAIL o LOCAL_ADMIN_PASSWORD mancano nel forziere." >&2; exit 1; }
docker compose -f "$COMPOSE" exec -T \
  -e LOCAL_ADMIN_EMAIL="$ADMIN_EMAIL" -e LOCAL_ADMIN_PASSWORD="$ADMIN_PASS" \
  backend python -m app.tools.bootstrap_local_admin | tail -1

echo "[4/5] Pubblico la home..."
bash "$RADICE/scripts/seed-sito.sh" | tail -1

echo "[5/5] Verifico..."
CODICE="$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000)"
NONPUBB="$(curl -s http://localhost:3000 | grep -ci 'not published' || true)"
if [[ "$CODICE" == "200" && "$NONPUBB" == "0" ]]; then
  echo "[OK] Punto zero raggiunto: http://localhost:3000 e' giocabile."
else
  echo "[STOP] Il sito risponde $CODICE e 'not published' compare $NONPUBB volte." >&2
  exit 1
fi
