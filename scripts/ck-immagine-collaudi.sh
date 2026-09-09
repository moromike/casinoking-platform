#!/usr/bin/env bash
# ck-immagine-collaudi.sh — costruisce l'immagine dei collaudi, se serve.
#
# MET-05. I cinque pacchetti che i collaudi pretendono stanno NELL'IMMAGINE, non nel
# lancio. Questo script e' l'unico posto che li mette li'.
#
#   ./scripts/ck-immagine-collaudi.sh            costruisce solo se manca o e' vecchia
#   ./scripts/ck-immagine-collaudi.sh --forza    ricostruisce comunque
#
# QUANDO E' "VECCHIA": quando casinoking-backend:latest e' stato costruito DOPO di lei.
# L'immagine dei collaudi deriva da quella del backend; se il backend cambia e questa no,
# i collaudi girerebbero su una base che non e' piu' quella del prodotto. Il controllo
# costa [GENERATO] circa 0,1 s e non serve ricordarselo: lo fa ck-test.sh a ogni lancio.
set -euo pipefail
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RADICE"
BASE="casinoking-backend:latest"
IMG="casinoking-collaudi:latest"
RICETTA="infra/docker/collaudi.Dockerfile"
FORZA=0; [ "${1:-}" = "--forza" ] && FORZA=1

# La data di nascita si confronta in SECONDI, non come stringa. Docker la restituisce in
# formato RFC3339 e due stringhe RFC3339 si ordinano bene solo se hanno lo stesso formato
# e lo stesso fuso: se un giorno non fosse cosi', il confronto sbaglierebbe in silenzio e
# nella direzione peggiore — "e' aggiornata" mentre non lo e'.
# LE DUE TARGHE. L'immagine porta addosso l'impronta della ricetta con cui e' nata e
# l'identita' dell'immagine di base. Si ricostruisce quando una delle due non corrisponde
# piu' allo stato di adesso — mai per l'ora che segna un orologio.
RICETTA_ORA="$(sha256sum "$RICETTA" | cut -c1-16)"
esiste() { docker image inspect "$1" >/dev/null 2>&1; }
targa()  { docker image inspect -f "{{index .Config.Labels \"$2\"}}" "$1" 2>/dev/null; }
id_di()  { docker image inspect -f '{{.Id}}' "$1" 2>/dev/null; }

if ! docker version >/dev/null 2>&1; then
  echo "[STOP] Non riesco a parlare con Docker: non posso costruire $IMG." >&2
  exit 3
fi
if ! esiste "$BASE"; then
  echo "[STOP] Manca $BASE, che e' la base di $IMG. Lancia prima ./scripts/ck-up.sh" >&2
  exit 1
fi
BASE_ORA="$(id_di "$BASE")"

MOTIVO=""
if [ "$FORZA" = 1 ]; then                             MOTIVO="richiesta esplicita (--forza)"
elif ! esiste "$IMG"; then                            MOTIVO="$IMG non esiste ancora"
elif [ "$(targa "$IMG" ck.ricetta)" != "$RICETTA_ORA" ]; then
                                                      MOTIVO="$RICETTA e' cambiata dopo l'ultima costruzione"
elif [ "$(targa "$IMG" ck.base)" != "$BASE_ORA" ]; then
                                                      MOTIVO="$BASE e' stata ricostruita dopo $IMG"
fi

if [ -z "$MOTIVO" ]; then
  echo "[OK] $IMG e' aggiornata: non ricostruisco."
  exit 0
fi

echo "[COSTRUISCO] $IMG — motivo: $MOTIVO"
docker build -f "$RICETTA" -t "$IMG" \
  --build-arg CK_RICETTA="$RICETTA_ORA" --build-arg CK_BASE="$BASE_ORA" .
echo "[FATTO] $IMG pronta."
