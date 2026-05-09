# Account ACC-1 Endpoint Audit

Documento di audit per decidere se la riorganizzazione Account puo' partire sui
dati attuali o se serve un read model dedicato.

## Stato

- Tipo: audit tecnico UX/API.
- Stato: eseguito; read model Cassa tecnica, statement Cassa business e
  paginazione Storico gioco implementati.
- Ambito: `/wallets`, `/ledger/transactions`, `/games/mines/sessions`,
  nuovo read model `/account/wallet-movements`, nuovo read model
  `/account/statement-movements`.
- Non sostituisce: financial core, `ACCOUNT_WALLET_GAME_HISTORY_REDESIGN_PLAN.md`.

## Sintesi

ACC-1 conferma che la UI Account non deve usare direttamente
`/ledger/transactions` per costruire la Cassa player.

Motivo:

- `/ledger/transactions` espone header tecnici della transazione;
- non espone importo firmato player-friendly;
- non espone `balance_after`;
- non e' paginato;
- il dettaglio `/ledger/transactions/{id}` espone entries contabili utili per
  audit/debug, ma non e' il read model giusto per una Cassa utente.

Decisione:

- mantenere `/ledger/transactions` come endpoint tecnico/diagnostico esistente;
- introdurre un endpoint read-only player-safe per la Cassa:
  `GET /account/wallet-movements?limit=20&cursor=...`;
- introdurre un endpoint read-only business-oriented per la Cassa finale:
  `GET /account/statement-movements?wallet_type=cash&period=last_30_days`;
- introdurre il dettaglio espandibile player-safe:
  `GET /account/statement-movements/{movement_id}`;
- derivare `amount` e `balance_after` dal ledger, senza scrivere saldo e senza
  cambiare wallet/ledger write path.

## Endpoint Audit

### `/wallets`

Esito: utilizzabile per stato wallet.

Espone:

- `wallet_type`;
- `currency_code`;
- `balance_snapshot`;
- `status`;
- `ledger_account_code`.

Uso corretto:

- saldo corrente;
- card wallet;
- confronto visuale con l'ultimo movimento se serve.

Limite:

- non e' uno storico.

### `/ledger/transactions`

Esito: non sufficiente per Cassa player.

Espone:

- `id`;
- `transaction_type`;
- `reference_type`;
- `reference_id`;
- `idempotency_key`;
- `created_at`.

Manca:

- importo firmato per wallet player;
- `wallet_type`;
- `currency_code`;
- `balance_after`;
- paginazione/cursor;
- descrizione player-friendly.

Regola:

- non usare questo endpoint per ricostruire una Cassa user-facing.

### `/ledger/transactions/{id}`

Esito: utile per audit, non per lista Cassa.

Espone entries double-entry:

- `ledger_account_code`;
- `entry_side`;
- `amount`;
- `created_at`.

Limite:

- richiederebbe una chiamata per ogni riga;
- espone dettagli contabili troppo tecnici;
- non contiene `balance_after` gia' pronto.

### `/games/mines/sessions`

Esito: utilizzabile per Storico gioco; paginazione cursor implementata.

Espone:

- round/session id;
- status;
- config Mines;
- bet;
- wallet type;
- safe reveals;
- payout corrente/potenziale;
- access session collegata;
- created/closed timestamps.

Espone ora:

- `limit`;
- cursor opaco;
- `meta.next_cursor`.

Resta fuori scope:

- contratto multi-engine.

Uso corretto:

- tab `Storico gioco`;
- raggruppamento per access session;
- dettaglio round espandibile.

Non usare per:

- saldo;
- ricostruzione balance;
- movimenti deposito/prelievo futuri.

### Accessi

Esito: non pronto come tab player.

Esistono:

- `access_logs`, visibili via backoffice/admin;
- `game_access_sessions`, parzialmente embeddate nello storico Mines.

Manca:

- endpoint player-safe dedicato agli accessi/login;
- decisione su quali campi mostrare al player.

Regola:

- niente tab `Accessi` finche' non esiste endpoint player-safe.

## Nuovo Read Model Cassa

Endpoint:

```text
GET /account/wallet-movements?limit=20&cursor=...
```

Responsabilita':

- leggere solo dati del player autenticato;
- derivare importi dal ledger account collegato al wallet;
- usare importi firmati:
  - credit = aumento saldo player;
  - debit = riduzione saldo player;
- calcolare `balance_after` tramite somma progressiva ledger per wallet;
- restituire cursor opaco;
- non esporre `idempotency_key` nella UI player;
- non modificare wallet, ledger, payout, RNG o settlement.

Uso:

- endpoint tecnico/contabile;
- non deve restare nella UI player dopo CASHIER-3;
- utile per test, diagnostica locale e futuro uso admin/export.

Campi:

```text
id
ledger_transaction_id
transaction_type
reference_type
reference_id
wallet_type
currency_code
direction
amount
balance_after
created_at
```

## Nuovo Read Model Estratto Movimenti

Endpoint:

```text
GET /account/statement-movements
GET /account/statement-movements/{movement_id}
```

Responsabilita':

- leggere solo dati del player autenticato;
- proiettare righe business da ledger e metadati collegati;
- aggregare il gioco per sessione/access session;
- mostrare bonus e adjustment come righe singole;
- tenere cash e bonus separati;
- usare default `wallet_type=cash` e `period=last_30_days`;
- restituire cursor opaco;
- esporre dettaglio round paginato per sessioni gioco;
- esporre dettaglio minimo per bonus/adjustment senza raw admin reason;
- non scrivere dati e non avere storage proprio.

Regola:

- il ledger resta la fonte primaria;
- se lo statement diverge dal ledger, lo statement e' bug.

## Esito ACC-1

- ACC-2 completato: la UI separa Cassa e `Storico gioco`.
- ACC-3 completato: `/games/mines/sessions` supporta `limit` e cursor.
- ACC-4 storico completato: `/account/wallet-movements` resta endpoint tecnico
  e non viene piu' usato dalla UI player.
- CASHIER-1 completato: `/account/statement-movements` espone righe business
  aggregate.
- CASHIER-2 completato: `/account/statement-movements/{movement_id}` espone
  dettaglio player-safe.
- CASHIER-3 completato: la UI Cassa usa lo statement business-oriented e
  sostituisce la card list contabile.
- ACC-5 Accessi resta bloccata finche' non c'e' endpoint player-safe dedicato.

## Verifiche Minime

```powershell
python -m pytest tests/integration/test_account_wallet_movements.py
python -m pytest tests/integration/test_mines_session_history_pagination.py
```
