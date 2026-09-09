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

**E non e' solo un numero interno:** lo stesso stato finisce nell'estratto conto del
giocatore tradotto in «Vinto», e sommato al totale vinto. Vedi la sezione qui sotto.

Su una piattaforma di gioco **tasso di vincita e RTP non sono statistiche interne**:
sono i numeri che chiede un regolatore.

## QUANTO PESA OGGI: E' ATTIVO, NON LATENTE — l'orchestratore aveva sbagliato

**La prima stesura di questo documento diceva «latente». Era falso, e l'ha smontato Codex
`gpt-5.6-sol` in rivalidazione.** Sta qui invece di essere riscritto in silenzio, perche' il
modo in cui l'errore e' stato fatto e' istruttivo.

**Il consumatore esiste, ed e' il giocatore.** `[LETTO]`
- `backend/app/modules/account/service.py:876` espone lo stato della partita come
  `"result": row["status"]`;
- `frontend-v3/app/ui/player-account-page.tsx:1610-1611` traduce `status === "won"` in
  **«Vinto»**;
- `frontend-v3/app/ui/player-account-page.tsx:1567` fa di piu': somma quell'importo nel
  **totale vinto** (`totalWon`).

`[GENERATO]` **434 rimborsi su 434 sono nello stato `won`**, quindi nell'estratto conto del
giocatore un rimborso appare come **«Vinto»** ed entra nel totale delle vincite.

**Perche' l'errore e' stato fatto, e vale piu' della correzione.** Le controricerche
cercavano `rtp`, `win_rate`, `winrate` e `status = 'won'` — cioe' **chi calcola**. Nessuna
cercava **chi mostra**. Una ricerca che copre una sola forma di consumo e poi conclude
«nessuno lo consuma» e' un'affermazione di assenza costruita male: e' esattamente la regola
8 del metodo applicata male da chi l'ha scritta.

**Non e' un problema futuro.** E' un numero sbagliato che un giocatore vede adesso.

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

**Non nel PASSO 2** — il contratto lo vieta e la ragione regge: tocca dati persistenti e
cambia numeri storici. **Ma la priorita' cambia:** non e' un debito da rimandare, e' un
numero sbagliato mostrato a un giocatore. Codex, in rivalidazione: *«Era giusto non
ripararlo dentro una verifica: serve un passo separato, ratificato, con migrazione e cambio
di specifica; non va pero' rinviato come problema soltanto futuro.»*

La strada che mi sembra giusta:
1. aggiungere a `platform_rounds` uno stato che distingua il rimborso, popolandolo
   all'indietro dai `settlement_kind` che ci sono gia' — nessun dato da inventare;
2. cambiare il collaudo che oggi pretende `won` su un rimborso. **E' un cambio di
   specifica, non una riparazione**, quindi va dichiarato prima e ratificato;
3. riempire `settlement_ledger_transaction_id` anche sulle perdite.

**La decisione e' di Michele:** e' una regola di business — cosa significa «vinta» nei
suoi numeri — non una scelta tecnica.
