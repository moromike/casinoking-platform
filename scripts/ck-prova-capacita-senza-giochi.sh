#!/usr/bin/env bash
# ck-prova-capacita-senza-giochi.sh — il CRITERIO DI PRODOTTO della Fase 8B.
#
# COSA DIMOSTRA: che le capacita' di piattaforma — leggere una partita, validare un
# gettone, e (con CAP-03) liquidare d'ufficio a fine sessione — funzionano quando i
# giochi veri NON CI SONO. E' la sola misura che non si aggira cambiando i collaudi:
# o la piattaforma sa fare quelle cose da sola, o non le sa fare.
#
# Riaccende sempre i giochi, anche se qualcosa va storto.
set -uo pipefail
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="$RADICE/infra/docker/docker-compose.yml"
cd "$RADICE"
ENVFILE="$("$RADICE/scripts/segreti.sh")"
riaccendi(){ CK_GIOCHI_INTERNI=on docker compose -f "$COMPOSE" --env-file "$ENVFILE" up -d backend >/dev/null 2>&1 || true; }
trap riaccendi EXIT

printf '# FASE 8B — LE CAPACITA DI PIATTAFORMA REGGONO SENZA I GIOCHI\n'
printf 'Data: %s\n\n' "$(date '+%Y-%m-%d %H:%M:%S %z')"

printf '[1/3] spengo i giochi interni\n'
CK_GIOCHI_INTERNI=off docker compose -f "$COMPOSE" --env-file "$ENVFILE" up -d backend >/dev/null 2>&1
for _ in $(seq 1 30); do curl -fsS -o /dev/null http://localhost:8000/api/v1/health/ready 2>/dev/null && break; sleep 2; done

printf '\n[2/3] le rotte dei giochi DEVONO essere 404, o la prova non varrebbe niente\n'
fallite=0
for g in mines boxe hi-lo; do
  c="$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:8000/api/v1/games/$g/config")"
  printf '      /games/%-6s/config          -> %s\n' "$g" "$c"
  [[ "$c" == "404" ]] || fallite=1
done
c="$(curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8000/api/v1/games/manichino/launch-token -H 'Content-Type: application/json' -d '{}')"
printf '      /games/manichino/launch-token -> %s  (401 = esiste e chiede le credenziali)\n' "$c"
[[ "$c" == "401" ]] || fallite=1
if [[ "$fallite" -ne 0 ]]; then
  printf '\n[STOP] la configurazione non e quella attesa: la prova non varrebbe niente\n'
  exit 1
fi

printf '\n[3/3] le capacita di piattaforma, a giochi spenti\n'
CK_GIOCHI_INTERNI=off ./scripts/ck-test.sh \
  tests/integration/test_capacita_di_piattaforma.py::test_platform_round_reads_a_cavia_round \
  tests/integration/test_capacita_di_piattaforma.py::test_player_cannot_read_another_players_platform_round \
  tests/integration/test_capacita_di_piattaforma.py::test_missing_platform_round_returns_not_found \
  tests/integration/test_capacita_di_piattaforma.py::test_platform_launch_validation_accepts_valid_token_and_rejects_invalid_cases \
  -v 2>&1 | grep -E "PASSED|FAILED|ERROR|passed|failed"
esito=${PIPESTATUS[0]}

printf '\nNOTA ONESTA: il collaudo di parita con la vecchia lettura di Mines non e in questo\n'
printf 'elenco, e non per debolezza: pretende un round di MINES, che a giochi spenti non si\n'
printf 'puo aprire. Quella parita si prova a giochi accesi, ed e la sola cosa che qui manca.\n'
exit "$esito"
