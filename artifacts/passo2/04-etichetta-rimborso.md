# PASSO 2, P2-03 — un rimborso e' registrato come una VINCITA

**10/09/2026** `[GENERATO]`. Si misura e si dichiara. **Non si ripara qui:** il
contratto lo vieta, perche' toccare quella funzione cambierebbe i numeri di tutte le
partite gia' chiuse.

## IL FATTO, in una riga

**Un rimborso senza progresso e una vincita vera producono lo stesso stato: `won`.**

```
settlement_kind      | stato_partita | quante
---------------------+---------------+-------
refund_no_progress   | won           |   426
manual_cashout       | won           |   123
```

`[LETTO]` E non e' un incidente: il collaudo lo **pretende**.
`tests/integration/test_boxe_api.py:1284` -> `assert platform_row["status"] == "won"`
dentro un collaudo che si chiama `..._refunds_real_round_...`.

## PERCHE' CONTA — e non e' un dettaglio da informatici

Un rimborso non e' una vincita: il giocatore riprende la sua puntata perche' non e'
successo niente. Se lo stato dice `won`, ogni numero costruito su quello stato nasce
sbagliato. Con i dati di oggi:

| Numero | Se lo si calcola dallo stato | Il vero |
|---|---|---|
| partite vinte | 549 su 571 = **96%** | 123 su 571 = **21,5%** |

Su una piattaforma di gioco **tasso di vincita e RTP non sono statistiche interne**:
sono i numeri che chiede un regolatore.

## QUANTO PESA OGGI: e' LATENTE, non attivo

**Nessun codice, oggi, calcola tasso di vincita o RTP da quello stato.**
CONTRORICERCA: `grep -rn 'rtp|RTP|win_rate|winrate' backend/app/ --include=*.py` ->
solo `rtp_source`, che e' un **puntatore a un documento** di specifica matematica
(`game_runtime_descriptors.py:36-70`), non un calcolo.
CONTRORICERCA: `grep -rn "status = 'won'" backend/app/` -> **2 risultati**, e sono
entrambi **scritture**, non aggregazioni.

**Quindi nessun numero sbagliato sta uscendo da nessuna parte, adesso.** Diventa reale
il giorno in cui qualcuno costruisce un rapporto — e per una piattaforma di gioco quel
giorno arriva insieme a un regolatore.

## L'INFORMAZIONE GIUSTA C'E' GIA', ed e' la buona notizia

`settlement_kind` distingue perfettamente i due casi, ed e' salvato in
`ledger_transactions.metadata_json`. **Non c'e' niente da ricostruire:** i 426 rimborsi
e i 123 incassi veri sono gia' distinguibili con un'interrogazione.

Quello che manca e' che `platform_rounds` non abbia uno stato suo per il rimborso.
`[GENERATO]` gli stati in uso sono **due soli**: `won` (549) e `lost` (22).

## UNA ASIMMETRIA MINORE, trovata strada facendo

`[GENERATO]` Tutte e **22** le partite perse hanno `settlement_ledger_transaction_id`
**vuoto**: dalla partita non si raggiunge il suo movimento contabile.
**Il collegamento pero' esiste al contrario:** tutti e 22 i movimenti `loss` portano
`platform_round_id` nel metadata, e tutti e 22 risolvono a una partita vera.
Quindi la tracciabilita' c'e', ma **a senso unico**. Il primo sospetto — «le perdite non
sono tracciabili» — **era sbagliato**, ed e' stato verificato prima di riportarlo.

## COSA PROPONGO, e in quale passo

**Non nel PASSO 2.** Serve un passo suo, perche' tocca dati persistenti e cambia i
numeri storici. La strada che mi sembra giusta:
1. aggiungere a `platform_rounds` uno stato che distingua il rimborso, popolandolo
   all'indietro dai `settlement_kind` che ci sono gia' — nessun dato da inventare;
2. cambiare il collaudo che oggi pretende `won` su un rimborso. **E' un cambio di
   specifica, non una riparazione**, quindi va dichiarato prima e ratificato;
3. riempire `settlement_ledger_transaction_id` anche sulle perdite.

**La decisione e' di Michele:** e' una regola di business — cosa significa «vinta» nei
suoi numeri — non una scelta tecnica.
