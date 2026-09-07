motore: Codex
modello: gpt-5.6-terra
correzione: il dossier dichiarava `gpt-5.6-sol`. Corretto da Claude l'8/09/2026 sulla
  base del banner della sessione, che riportava `model: gpt-5.6-terra medium`. Un
  dossier che sbaglia il proprio autore non e' un dettaglio: e' la catena che perde
  la tracciabilita' proprio dove serve.
modalita: GOAL — proposta, non applicata
ruolo: proponente
data: 2026-09-08
perimetro: MODIFICA — `ck-rosso.sh` e tutti i `test_seamless_*.py` coinvolti

# Dossier — produttori degli artefatti di riproduzione Fase 9

## Perche' serve

`ck-riproduci.sh` e' stato creato e le sue due prove nel repository finto
dimostrano sia la divergenza non mascherata, sia l'impronta del collaudo
indebolito. L'integrazione reale non puo' pero' ancora partire: i dieci artefatti
verdi del contratto non esistono e i quattro rossi prodotti da `ck-rosso.sh` sono
normali log pytest, privi di entrambi i marcatori obbligatori:

- `--- IMPRONTA COLLAUDO ---` con percorso e SHA-256 del collaudo;
- `--- ESITO ---` con caso, verdetto, importo, saldo prima e saldo dopo.

Non e' lecito sintetizzare quei valori in `ck-riproduci.sh`: renderebbe il
controllore autore della prova che deve solo confrontare. I collaudi che conoscono
i dati devono emettere il loro esito strutturato; il loro hash e' poi legato al
deposito. Questo richiede modificare file di collaudo esistenti e `ck-rosso.sh`,
tutti protetti in modo `MODIFICA`. Per il mandato, deposito la proposta e mi fermo.

## Cosa si propone

1. Aggiungere il nuovo modulo qui sotto, che impone il formato unico e calcola
   l'impronta sui byte del collaudo. Il modulo non inventa importi o saldi: riceve
   esclusivamente quelli che il singolo collaudo ha davvero verificato.
2. Nei nove collaudi del gate, dopo l'asserzione che misura ciascun caso, invocare
   `scrivi_esito(...)` per il rispettivo artefatto del contratto. Il collaudo di
   POR-02 ne emette due (`accrediti-rifiutati.txt`, `concorrenza.txt`).
3. Cambiare `ck-rosso.sh` affinche' aggiunga il medesimo blocco agli artefatti
   rossi solo dopo che ha verificato i nodeid falliti e prima della controprova.
   Ogni blocco deve riferire lo stesso file di collaudo sabotato; il suo verdetto
   stabile e' `ROSSO_ATTESO`.

## Testo proposto — nuovo modulo di supporto

--- INIZIO TESTO PROPOSTO: tests/integration/seamless_esito.py ---
"""Formato canonico dell'artefatto riproducibile Fase 9."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import TextIO


def scrivi_esito(
    output: TextIO,
    *,
    collaudo: str,
    caso: str,
    verdetto: str,
    importo: str,
    saldo_prima: str,
    saldo_dopo: str,
    identificativo_generato: str,
    marca_temporale: str,
    durata: str,
) -> None:
    """Emette il solo formato accettato da ``ck-riproduci.sh``.

    I sei campi economici e di significato restano espliciti. Identificativo,
    tempo e durata sono volutamente separati: il confronto puo' mascherare solo
    questi tre valori etichettati.
    """
    impronta = sha256(Path(collaudo).read_bytes()).hexdigest()
    output.write(
        "--- IMPRONTA COLLAUDO ---\n"
        f"file: {collaudo}\n"
        f"sha256: {impronta}\n"
        "--- FINE IMPRONTA COLLAUDO ---\n"
        "--- ESITO ---\n"
        f"caso={caso}\n"
        f"verdetto={verdetto}\n"
        f"importo={importo}\n"
        f"saldo_prima={saldo_prima}\n"
        f"saldo_dopo={saldo_dopo}\n"
        f"identificativo_generato={identificativo_generato}\n"
        f"marca_temporale={marca_temporale}\n"
        f"durata={durata}\n"
        "--- FINE ESITO ---\n"
    )
--- FINE TESTO PROPOSTO ---

## File protetti da adattare, senza ancora farlo

| File | Artefatto/i | Misura che deve alimentare l'esito |
|---|---|---|
| `tests/integration/test_seamless_parita_contabile.py` | `parita-seamless-mines.txt` | reserve/commit e saldo finale |
| `tests/integration/test_seamless_accredito_senza_trattenuta.py` | `accrediti-rifiutati.txt`, `concorrenza.txt` | rifiuto senza reserve e concorrenza |
| `tests/integration/test_seamless_firma_rigiocata.py` | `firma-rigiocata.txt` | firma e richiesta rigiocata |
| `tests/integration/test_seamless_ordine_operazioni.py` | `ordine-invertito.txt` | ordine dei passaggi |
| `tests/integration/test_seamless_fornitore_sospeso.py` | `fornitore-sospeso.txt` | sospensione fornitore |
| `tests/integration/test_seamless_scrive_davvero.py` | `scrive-davvero.txt` | scritture contabili |
| `tests/integration/test_seamless_controlli_di_casa.py` | `controlli-di-casa.txt` | controlli interni/REG-02 |
| `tests/integration/test_seamless_rollback.py` | `rollback-nativo.txt` | annullamento nativo |
| `tests/integration/test_migrazione_0058.py` | `migrazione-0058.txt` | migrazione 0058 |
| `scripts/ck-rosso.sh` | quattro `*-rosso.txt` | fallimento atteso per POR-01/03/06/07 |

## Cosa rompe e cosa non rompe

Non cambia rotte, migrazioni, adapter, ledger, wallet o semantica dei test. Aggiunge
solo l'emissione dell'evidenza dopo le asserzioni gia' esistenti. Il rischio da
valutare in revisione e' che un collaudo emetta valori non strettamente osservati:
in quel caso l'artefatto sarebbe una dichiarazione e non una misura. Per questo
ogni chiamata dovra' essere accanto all'asserzione che prova i tre valori stabili.

## Collaudi da eseguire dopo la catena

1. I nove comandi pytest #2–#10 del contratto, uno per uno: ciascuno deve produrre
   il proprio artefatto con un solo blocco impronta e un solo blocco ESITO.
2. `./scripts/ck-rosso.sh`: deve produrre quattro artefatti rossi con lo stesso
   formato e conservare le controprove esistenti.
3. `./scripts/ck-riproduci.sh --autotest`: devono restare `2/2 prove di
   fallimento corrette`.
4. `./scripts/ck-riproduci.sh`: quando Docker e depositi sono disponibili, deve
   rilanciare tutti e dodici i comandi e terminare verde solo a confronto riuscito.
