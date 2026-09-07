#!/usr/bin/env bash
# ck-applica-approvato.sh — scrive sui file SOLO i byte che Michele ha firmato.
#
# PERCHE' NON SI COPIA E BASTA. Fra la proposta e l'applicazione passano ore, un
# revisore, e la mano di chi applica. Se chi applica ricopia "la sua versione"
# invece di quella approvata, la firma ha coperto un testo e ne e' entrato un
# altro, e nessuno se ne accorge: la catena diventa una recita.
# Qui i byte si estraggono dal documento FIRMATO, si ricalcola l'impronta, e si
# confronta con quella dell'APPROVAZIONE. Un solo scarto e non si scrive niente.
#
# Uso: ck-applica-approvato.sh <cartella-della-catena> [--prova]
#   --prova  verifica e dice cosa farebbe, senza scrivere
set -euo pipefail

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CARTELLA="${1:?serve la cartella della catena, es. missioni/2026-09-07-campi-obbligatori}"
PROVA="${2:-}"
cd "$RADICE"

PROPOSTA="$CARTELLA/PROPOSTA.md"
APPROVAZIONE="$CARTELLA/APPROVAZIONE.md"
[ -f "$PROPOSTA" ]     || { echo "ROSSO: manca $PROPOSTA"; exit 2; }
[ -f "$APPROVAZIONE" ] || { echo "ROSSO: manca $APPROVAZIONE"; exit 2; }

# --- anello 4: l'approvazione dev'essere firmata ------------------------------
# Si guarda il commit che ha introdotto l'APPROVAZIONE, non l'ultimo commit:
# altrimenti basterebbe firmare qualunque cosa dopo per far passare qualunque
# cosa prima.
COMMIT="$(git log -1 --format=%H -- "$APPROVAZIONE")"
[ -n "$COMMIT" ] || { echo "ROSSO: $APPROVAZIONE non e' mai stata committata."; exit 1; }
STATO="$(git log -1 --format='%G?' "$COMMIT")"
if [ "$STATO" != "G" ]; then
  echo "ROSSO: il commit dell'approvazione ($(git rev-parse --short "$COMMIT")) non ha"
  echo "       una firma valida (stato git: '$STATO'). Non si applica niente."
  exit 1
fi
echo "== approvazione firmata: $(git rev-parse --short "$COMMIT") da $(git log -1 --format='%GS' "$COMMIT")"

python3 - "$PROPOSTA" "$APPROVAZIONE" "$PROVA" <<'PY'
import hashlib, pathlib, re, sys

proposta, approvazione, prova = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]

# le impronte autorizzate, lette dalla tabella dell'APPROVAZIONE firmata
autorizzate = dict(re.findall(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|", approvazione.read_text(), re.M))
if not autorizzate:
    sys.exit("ROSSO: nessuna impronta autorizzata trovata nell'APPROVAZIONE.")

# i blocchi, estratti dai marcatori della PROPOSTA
righe = proposta.read_text().splitlines(keepends=True)
blocchi, ini, nome = [], None, None
for i, r in enumerate(righe):
    if r.startswith("--- INIZIO TESTO PROPOSTO:"):
        nome, ini = r.split(": ", 1)[1].rsplit(" ---", 1)[0].strip(), i + 1
    elif r.startswith("--- FINE TESTO PROPOSTO ---") and ini is not None:
        blocchi.append((nome, "".join(righe[ini:i]))); ini = None

esito, da_scrivere = 0, []
for nome, testo in blocchi:
    calcolata = hashlib.sha256(testo.encode()).hexdigest()
    attesa = autorizzate.get(nome)
    if attesa is None:
        print(f"  ROSSO  {nome}: proposto ma NON autorizzato dalla firma"); esito = 1
    elif attesa != calcolata:
        print(f"  ROSSO  {nome}: i byte non sono quelli firmati")
        print(f"         firmato:  {attesa}")
        print(f"         proposto: {calcolata}"); esito = 1
    else:
        print(f"  verde  {nome}  {calcolata[:16]}...")
        da_scrivere.append((nome, testo))

mancanti = set(autorizzate) - {n for n, _ in blocchi}
for m in sorted(mancanti):
    print(f"  ROSSO  {m}: autorizzato dalla firma ma assente dalla proposta"); esito = 1

if esito:
    sys.exit("\nROSSO: nessun file e' stato scritto.")
if prova == "--prova":
    print(f"\n--prova: {len(da_scrivere)} file sarebbero riscritti. Niente e' stato toccato.")
    sys.exit(0)
for nome, testo in da_scrivere:
    pathlib.Path(nome).write_text(testo)
print(f"\nVERDE: {len(da_scrivere)} file scritti con i byte firmati.")
PY
