Status: ACTIVE
Last meaningful update: 2026-05-10

# Account Cashier Movements Redesign Analysis

Documento di analisi per rifare la pagina `Cassa` dopo feedback utente e file
`docs/casinoking_movimenti.xlsx`.

## Stato

- Tipo: analisi UX/API per Cassa player.
- Stato: CASHIER-1/2/3 implementati; CASHIER-4 verifica tecnica completata,
  validazione utente pending.
- Data: 2026-05-09.
- Ambito: movimenti finanziari player, filtri causali, righe espandibili,
  separazione cash/bonus, dettaglio gioco.
- Non sostituisce: financial core, ledger/wallet canonici,
  `docs/ACCOUNT_WALLET_GAME_HISTORY_REDESIGN_PLAN.md`.

## Verdetto Sulla Cassa Attuale

La Cassa implementata in ACC-4 e' tecnicamente utile come primo read model, ma
come esperienza utente e' bocciata.

Motivo:

- mostra eventi ledger quasi grezzi;
- usa card verticali troppo larghe e poco scansionabili;
- non offre prefiltro causali;
- non rispetta il modello mentale di un estratto movimenti;
- per il gioco mostra troppo vicino al singolo evento contabile, mentre il
  player si aspetta una riga di business per sessione.

Quindi la prossima slice non deve essere un polish grafico della card list
attuale. Deve sostituire il pattern con una pagina movimenti vera.

## Input Utente

File letto:

- `docs/casinoking_movimenti.xlsx`

Colonne indicate:

```text
Data
Competenza
Movimento
Descrizione
Codice
Causale
Tipo Movimento
n. *
Dare
Avere
Balance finale
```

Screenshot ricevuto:

- tab causali in alto;
- filtro periodo;
- pulsante ricerca;
- stato vuoto leggibile.

Lo screenshot va preso come riferimento funzionale, non come tema grafico da
copiare.

## Principio Di Prodotto

`Cassa` deve essere l'estratto movimenti finanziario del player.

Non deve essere:

- un dump di `ledger_transactions`;
- uno storico round;
- una vista tecnica da sviluppatore;
- una somma ambigua di cash e bonus.

La riga primaria deve essere una riga di business. Il dettaglio tecnico arriva
solo su espansione.

## Rapporto Con Storico Gioco

`Cassa` e `Storico gioco` non devono raccontare la stessa cosa.

Decisione:

- `Cassa` e' la vista finanziaria: saldo, wallet, causali, giocato, vinto,
  delta, saldo finale e dettaglio contabile essenziale;
- `Storico gioco` resta giustificato solo come vista gameplay/fairness:
  configurazione round, stato, celle rivelate, esito tecnico, riferimenti
  fairness e audit di gioco;
- `Storico gioco` non deve diventare un secondo estratto conto e non deve
  duplicare i saldi della Cassa;
- se nella prossima review non espone informazioni gameplay/fairness realmente
  diverse dalla Cassa, va rinominato/ridisegnato come `Dettaglio gioco` o
  accorpato.

## Prefiltri Causali

Pattern consigliato:

```text
Tutte le causali | Depositi e prelievi | Gioco | Bonus | Rettifiche/Storni
```

Filtro periodo:

```text
Oggi | Ultimi 7 giorni | Ultimi 30 giorni | Mese corrente | Mese precedente | Personalizzato
```

Filtro wallet:

```text
Saldo reale | Bonus
```

Decisione:

- default: `Tutte le causali` + periodo `Ultimi 30 giorni`;
- default wallet: `Saldo reale`, per non mischiare cash e bonus;
- `Tutti` non e' ammesso in CASHIER-1: mischia visivamente wallet con regole
  diverse e aggiunge rumore senza valore prodotto attuale.
- i filtri causali dipendono dal wallet selezionato:
  - con `Saldo reale`, non mostrare `Bonus` perche' restituirebbe una vista
    strutturalmente vuota;
  - con `Bonus`, non mostrare `Depositi e prelievi` finche' deposito/prelievo
    bonus non esiste come prodotto;
  - se un cambio wallet rende invalida la causale corrente, tornare a
    `Tutte le causali`.

## Cash E Bonus

Scelta severa:

- bonus e cash non vanno fusi in un unico saldo;
- il bonus puo' comparire nella Cassa come causale/filtro, ma con badge
  `Bonus` e `balance_after` del wallet bonus;
- il saldo reale resta il wallet `cash`;
- nessuna UI deve mostrare un "saldo finale giocatore" ottenuto sommando cash e
  bonus, finche' non esistono regole prodotto su spendibilita', wagering e
  conversione.

Motivo:

- oggi cash e bonus sono wallet separati;
- bonus grant e admin adjustment sono eventi contabili veri, ma non hanno lo
  stesso significato di deposito/prelievo reale;
- sommare i due valori puo' far credere al player di avere saldo prelevabile
  quando non e' detto.

## Mapping Riga Da Excel

| Colonna Excel | Significato prodotto | Mapping tecnico consigliato |
| --- | --- | --- |
| Data | inizio o data apertura movimento | `started_at` o `created_at` business event |
| Competenza | data di competenza/chiusura | `ended_at`, `closed_at` o ultimo evento ledger |
| Movimento | famiglia movimento | `game`, `deposit`, `withdrawal`, `bonus`, `adjustment`, `reversal` |
| Descrizione | testo leggibile | `Mines`, `Bonifico`, `Carta`, `Bonus`, `Rettifica saldo` |
| Codice | riferimento consultabile | display code derivato da sessione/transazione |
| Causale | causale player-friendly | `Sessione gioco`, `Deposito`, `Prelievo`, `Bonus accreditato`, `Rettifica` |
| Tipo Movimento | engine/provider/strumento | `mines`, futuro `slot`, futuro `card`, `bank_transfer` |
| n. | quantita' eventi nel dettaglio | numero round/spin per gioco, `1` per movimento singolo |
| Dare | uscita/addebito player | importi debit del wallet player |
| Avere | entrata/accredito player | importi credit del wallet player |
| Balance finale | saldo dopo la riga | `balance_after` del wallet coinvolto |

Nota UX:

- in UI player, per righe gioco mostrare `Giocato` / `Vinto` / `Delta`;
- `Delta` e' `Vinto - Giocato`, derivato da `net_amount`;
- per righe non gioco, mantenere `Uscite` / `Entrate`;
- per righe non gioco, mostrare `Delta` come `-`: il delta e' una metrica di
  sessione gioco, non una label generica per bonus, rettifiche o futuri
  depositi/prelievi;
- `Dare` / `Avere` puo' restare come concetto interno o in export/reporting.
- in UI player non usare la label `Competenza`: e' un campo interno del read
  model, non una parola chiara per il giocatore;
- per righe gioco mostrare `Inizio sessione` = `started_at` e `Fine sessione`
  = `competency_at` quando disponibile/diversa, altrimenti `-`;
- per righe non gioco mostrare una sola `Data movimento`;
- mostrare `n.` solo quando il conteggio e' maggiore di 1.

## Riga Primaria Per Tipo Movimento

### Gioco

La riga primaria deve rappresentare una sessione di gioco, non il singolo
ledger event.

Riga:

```text
Inizio sessione: avvio sessione
Fine sessione: chiusura sessione o ultimo evento contabile noto, se disponibile
Movimento: Gioco
Descrizione: Mines
Codice: session code breve
Causale: Sessione gioco
Tipo Movimento: mines
n.: numero round
Giocato: totale puntato
Vinto: totale vinto/stornato
Delta: vinto - giocato
Saldo finale: balance_after dell'ultimo evento wallet della sessione
```

Regola `Saldo finale`:

- mostrare sempre il vero `balance_after` del wallet coinvolto;
- non ricalcolare mai un "saldo della vista" basato sulle sole righe filtrate;
- se la vista e' filtrata, mostrare un disclaimer compatto:
  `Il saldo riflette il wallet, non solo le righe filtrate.`

Motivo:

- se tra due sessioni gioco esiste un deposito, un bonus o una rettifica non
  visibile nel filtro corrente, il saldo puo' saltare correttamente;
- quel salto e' vero, perche' rappresenta il wallet;
- nasconderlo o ricalcolarlo sul filtro sarebbe una contabilita' finta.

Dettaglio espanso:

- round/spin singoli;
- orario round;
- puntata;
- esito;
- vincita/storno;
- configurazione gioco essenziale;
- id tecnici abbreviati.

Regola:

- usare `game_access_sessions.id` come sessione quando presente;
- se manca `access_session_id`, non inventare una sessione fittizia ampia:
  fallback conservativo su singolo round o legacy group dichiarato.

### Deposito

Stato attuale:

- deposito reale non implementato.

Quando arrivera':

- una riga per operazione deposito;
- dettaglio con provider, stato, riferimento pagamento, timestamp;
- nessun impatto wallet fuori dal ledger.

### Prelievo

Stato attuale:

- prelievo reale non implementato.

Quando arrivera':

- una riga per richiesta/operazione prelievo;
- dettaglio con stato richiesta, eventuale annullamento, provider/riferimento;
- se esiste "annulla prelievo in corso", deve essere un flusso dedicato, non un
  bottone statico decorativo.

### Bonus

Stato attuale:

- esiste `bonus_grant` su wallet bonus.

Regola UX:

- visualizzare come movimento separato `Bonus accreditato`;
- non mischiare con saldo cash;
- non esporre raw `admin_actions.reason` al player finche' non esiste un
  `public_reason` o una causale approvata;
- detail minimo: data, importo, codice movimento, wallet bonus.

Gap noto:

- il fix corretto a lungo termine e' aggiungere a `admin_actions` un campo
  `player_visible_note` separato dal `reason` interno;
- non va aggiunto in CASHIER-1.

### Rettifiche E Storni

Stato attuale:

- esiste `admin_adjustment`;
- esiste `void` per chiusure/annullamenti gioco lato admin.

Regola UX:

- mostrare una causale pulita: `Rettifica saldo`, `Storno sessione` o
  `Annullamento round`;
- raw reason interno non va mostrato al player senza campo pubblico dedicato;
- dettaglio con riferimento tecnico abbreviato e impatto saldo.

## Read Model Necessario

L'endpoint attuale:

```text
GET /account/wallet-movements
```

resta endpoint tecnico/read model contabile.

Decisione:

- e' uscito dalla UI player dopo il collegamento di `statement-movements` alla
  nuova Cassa;
- resta disponibile per test, diagnostica locale e futuro uso admin/export;
- non deve convivere in UI con `statement-movements`.

Serve un read model statement-oriented:

```text
GET /account/statement-movements
```

Stato:

- implementato in CASHIER-1;
- backend read-only;
- collegato alla UI player da CASHIER-3.

Regola dura:

- `/account/statement-movements` e' una proiezione read-only su
  `ledger_transactions`, `ledger_entries`, `wallet_accounts`,
  `game_access_sessions`, `platform_rounds` e metadata collegati;
- non scrive;
- non ha storage proprio;
- non ricalcola somme da fonti diverse dal ledger;
- se ledger e statement divergono, il ledger vince e lo statement e' bug.

Query:

```text
category=all|deposits_withdrawals|game|bonus|adjustments
wallet_type=cash|bonus
period=today|last_7_days|last_30_days|current_month|previous_month|custom
date_from=YYYY-MM-DD
date_to=YYYY-MM-DD
limit=20
cursor=...
```

Payload concettuale:

```text
items[]
  id
  movement_family
  movement_label
  description
  code
  causale
  movement_type
  wallet_type
  currency_code
  started_at
  competency_at
  show_competency_at
  detail_count
  show_detail_count
  debit_amount
  credit_amount
  net_amount
  balance_after
  expandable
  contains_adjustments
meta
  next_cursor
  limit
  category
  wallet_type
  period
  balance_disclaimer
```

Endpoint dettaglio:

```text
GET /account/statement-movements/{movement_id}
```

Schema `movement_id`:

```text
game:<access_session_id>
game_round:<platform_round_id>      # solo fallback legacy/no access session
bonus:<admin_action_id>
adjustment:<ledger_transaction_id>
deposit:<deposit_id>                # futuro
withdrawal:<withdrawal_id>          # futuro
```

Regola:

- i nuovi flussi gioco devono usare `game:<access_session_id>`;
- `game_round:<platform_round_id>` serve solo a non perdere righe legacy o
  round avviati fuori da una access session;
- CASHIER-2 deve validare il prefisso prima di cercare il dettaglio.

Payload dettaglio per gioco:

```text
rounds[]  # paginato, limit iniziale 50
  timestamp
  round_code
  bet_amount
  win_amount
  result
  wallet_type
  balance_after
  game_summary
meta
  next_cursor
  limit
```

Regola dettaglio:

- una sessione lunga puo' avere centinaia di round, quindi anche il dettaglio va
  paginato;
- void/storni dentro una sessione restano nel summary economico della sessione
  e attivano `contains_adjustments=true`;
- il dettaglio mostra le rettifiche come righe distinte.

## UI Target

Desktop:

- testata compatta con saldi separati cash/bonus;
- filtro causali a tab;
- filtro periodo e ricerca;
- lista/table compatta con colonne dell'Excel adattate;
- riga cliccabile/espandibile;
- stato vuoto contestuale: "Nessun movimento nel periodo selezionato".

Mobile:

- filtri in riga scrollabile o segmented control;
- periodo sotto;
- righe compatte card-list, non card enormi;
- importo e saldo sempre visibili;
- dettaglio espandibile sotto la riga.

Pattern riga mobile:

```text
Mines                 +12.40 CHIP
Sessione gioco        09/05/2026 18:42
Giocato 10.00         Vinto 22.40
Delta +12.40
Saldo 1,012.40        [Dettaglio]
```

## Cosa Non Fare

- Non rifinire la card list attuale come se fosse il prodotto finale.
- Non usare `/ledger/transactions` direttamente in frontend.
- Non mostrare idempotency key al player.
- Non mostrare raw admin reason come motivazione player-facing.
- Non sommare cash e bonus in un saldo unico.
- Non creare tab Accessi o Depositi/Prelievi come flussi funzionali se i dati
  reali non esistono.

## Sequenza Operativa Consigliata

### CASHIER-1 - Read model statement

Stato: completato.

Backend read-only per `/account/statement-movements`.

Include:

- filtri causale;
- filtri periodo;
- wallet filter;
- default `wallet_type=cash`, `period=last_30_days`;
- righe aggregate gioco per sessione;
- righe singole per bonus/adjustment;
- saldo finale sempre wallet-derived, anche nelle viste filtrate;
- cursor pagination;
- test su cash, bonus, adjustment, game win/loss.

### CASHIER-2 - Detail endpoint

Stato: completato.

Backend read-only per espansione riga.

Include:

- dettaglio round per movimento `game`;
- dettaglio minimo per bonus/adjustment;
- nessun raw internal reason se non player-safe;
- paginazione dettaglio round con `limit=50` e cursor opaco.

### CASHIER-3 - UI Cassa nuova

Stato: completato.

Frontend:

- sostituire la card list attuale;
- implementare prefiltri;
- lista compatta desktop/mobile;
- espansione riga;
- empty/loading/error states.

### CASHIER-4 - QA

Stato: verifica tecnica completata; validazione utente pending.

Verifiche:

- mobile 375px;
- molte righe/paginazione;
- filtro bonus non altera cash;
- sessione gioco mostra una riga primaria e dettaglio round;
- saldo finale per wallet coerente con `/wallets`.
- nelle viste filtrate il saldo mostra il vero `balance_after` del wallet e il
  disclaimer e' presente.

Verifiche tecniche 2026-05-09:

- test integrazione account/Mines/ledger passati;
- build frontend passata;
- backend/frontend Docker ricostruiti e healthy;
- endpoint statement protetto da auth verificato;
- cleanup DB locale test verificato su utenti/title con prefissi test;
- fixture `create_player`/`create_admin_user` aggiornate per cleanup automatico
  di utenti, wallet, ledger, sessioni, round e title test orfani.

## Decisione

Procedere con test, build e verifica locale del flusso CASHIER completo.

Motivo:

- CASHIER-1 ha fissato il read model;
- CASHIER-2 espone il dettaglio espandibile senza duplicare contabilità;
- CASHIER-3 ha rimosso la vecchia card list tecnica dalla Cassa player.
