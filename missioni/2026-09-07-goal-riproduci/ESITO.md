# Esito della corsa GOAL — `ck-riproduci.sh`

Data: 2026-09-08
Stato: **NON VERIFICATO IN INTEGRAZIONE; fermo al dossier obbligatorio**.

## Creato

- `scripts/ck-riproduci.sh`: tredicesimo comando; controlla allowlist chiusa,
  impronta SHA-256 del collaudo e blocco `ESITO` per tutti i dieci artefatti verdi
  e i quattro rossi attesi.
- `missioni/2026-09-07-goal-riproduci/PROPOSTA.md`: proposta non applicata per
  far emettere ai produttori reali il formato richiesto dal contratto.

## Prove di fallimento eseguite davvero

Comando eseguito:

```text
./scripts/ck-riproduci.sh --autotest
```

Output vero:

```text
[OK] Prova A: una riga non mascherata rende rosso l artefatto nominato
[OK] Prova B: collaudo indebolito rende rossa la sua impronta
2/2 prove di fallimento corrette
```

Prova A altera solo `saldo_dopo` dell'artefatto finto `fornitore-sospeso.txt` e
pretende l'errore nominato `ESITO DIVERGENTE`. Prova B altera solo il file di
collaudo finto, lascia invariato l'artefatto e pretende `IMPRONTA DIVERGENTE`.
Entrambe girano in repository temporanei senza Docker.

## Comandi eseguiti

- `bash -n scripts/ck-riproduci.sh` — verde.
- `./scripts/ck-riproduci.sh --autotest` — 2/2 verde.
- `./scripts/ck-riproduci.sh` — rosso atteso prima del rilancio: mancano i dieci
  artefatti verdi depositati e formattati. Nessun comando Docker e nessun
  collaudo di integrazione e' stato quindi eseguito da questo controllore.

## Lasciato aperto e perche'

L'integrazione con i dodici comandi resta non verificata. Oltre al limite Docker
misurato per Codex, i produttori reali non emettono ancora il formato contrattuale:
gli artefatti verdi mancano e quelli rossi di `ck-rosso.sh` non hanno impronta/ESITO.
Correggerli richiede modificare file esistenti nel perimetro protetto. Il mandato
ordina dossier e arresto; la proposta e' in `PROPOSTA.md` e non e' stata applicata.
