# CasinoKing – Documento 05 v3

Wallet, Ledger e fondamenta transazionali definitive

Scopo del documento
Fissare in modo definitivo il modello wallet/ledger della piattaforma CasinoKing, con regole operative codificabili, locking strategy, idempotenza, flussi SQL di riferimento, error handling e riconciliazione. Questo documento sostituisce le ambiguità residue della v2.

## 1. Decisioni finali approvate

- Il saldo wallet è uno snapshot materializzato e non una vista calcolata a runtime.
- La fonte contabile primaria resta il ledger.
- Ogni posting che impatta un wallet aggiorna balance_snapshot nella stessa transazione DB.
- Il modello contabile include un piano dei conti generale tramite ledger_accounts.
- Le scritture sensibili usano idempotency key e row-level locking dove necessario.

## 2. Principio fondamentale: fonte di verità vs snapshot operativo

Il sistema usa due livelli complementari:

- Ledger = verità contabile, auditabile, immutabile o fortemente controllata.
- Wallet snapshot = stato operativo veloce per autorizzare bet, mostrare saldo e ridurre carico query.
- Regola ferrea: ledger e snapshot non possono divergere in un commit riuscito.

## 3. Modello entità v3

| Entità | Ruolo | Note chiave |
| --- | --- | --- |
| ledger_accounts | Piano dei conti generale | conti player, house, promo, game pnl |
| wallet_accounts | Snapshot operativi utente | ogni wallet punta a un ledger_account |
| ledger_transactions | Header transazione | type, reference, idempotency_key, metadata |
| ledger_entries | Posting double-entry | sempre verso ledger_account_id |
| admin_actions | Audit operazioni manuali | mai correzioni silenziose |

## 4. Piano dei conti minimo

- PLAYER_CASH account per ogni player/currency.
- PLAYER_BONUS account per ogni player/currency.
- HOUSE_CASH.
- HOUSE_BONUS.
- PROMO_RESERVE.
- GAME_PNL_MINES.

## 5. Regole di double-entry

- Ogni ledger_transaction deve avere posting bilanciati secondo il modello contabile scelto.
- Ogni ledger_entry usa importo positivo; il verso è espresso da entry_side debit/credit.
- Le entry non puntano al wallet ma al ledger_account.
- wallet_accounts.balance_snapshot viene aggiornato solo per i conti player collegati al wallet.

## 6. Struttura minima raccomandata delle tabelle

ledger_accounts(
id uuid pk,
account_code varchar unique,
account_type varchar,
owner_user_id uuid nullable,
currency_code varchar,
status varchar,
created_at timestamptz
)

wallet_accounts(
id uuid pk,
user_id uuid fk,
ledger_account_id uuid fk unique,
wallet_type varchar,
currency_code varchar,
balance_snapshot numeric(18,6) not null default 0,
status varchar,
created_at timestamptz
)

ledger_transactions(
id uuid pk,
user_id uuid fk,
transaction_type varchar,
reference_type varchar,
reference_id uuid,
idempotency_key varchar unique nullable,
metadata_json jsonb,
created_at timestamptz
)

ledger_entries(
id uuid pk,
transaction_id uuid fk,
ledger_account_id uuid fk,
entry_side varchar check(debit|credit),
amount numeric(18,6) check(amount>0),
created_at timestamptz
)

## 7. Locking strategy

- Per bet, win, cashout e admin adjustment: SELECT ... FOR UPDATE sui wallet_accounts coinvolti e sulla game_session quando applicabile.
- Se l’operazione coinvolge due wallet del player, i lock devono seguire sempre lo stesso ordine logico per evitare deadlock.
- Per cashout e reveal della stessa sessione: lock sulla riga game_sessions prima di qualsiasi posting finanziario.
- Le unique key aiutano, ma non sostituiscono il locking transazionale.

## 8. Idempotenza

- Ogni operazione esterna sensibile deve avere una idempotency_key stabile lato API o generata lato orchestrazione.
- ledger_transactions.idempotency_key deve essere unique.
- Se arriva una richiesta duplicata con stessa chiave e stesso payload logico, il sistema restituisce il risultato già committato.
- Se arriva stessa chiave ma payload diverso, il sistema deve fallire con errore di conflitto idempotenza.

## 9. Flussi canonici codificabili

### 9.1 Signup credit

BEGIN;
-- 1) lock eventuali righe utente già esistenti se necessario
-- 2) create ledger_transaction(type='signup_credit', idempotency_key='signup-<user>')
-- 3) insert ledger_entries:
--    credit PLAYER_CASH 1000
--    debit  HOUSE_CASH   1000   -- oppure PROMO_RESERVE secondo policy
-- 4) update wallet_accounts set balance_snapshot = balance_snapshot + 1000
COMMIT;

### 9.2 Bet

BEGIN;
SELECT * FROM wallet_accounts WHERE id = :player_cash_wallet FOR UPDATE;
SELECT * FROM game_sessions WHERE id = :session_id FOR UPDATE;
-- valida saldo snapshot >= bet_amount
-- create ledger_transaction(type='bet', idempotency_key=:request_key)
-- insert ledger_entries:
--    debit  PLAYER_CASH   :bet_amount
--    credit HOUSE_CASH    :bet_amount   -- o GAME_PNL_MINES holding account
-- update wallet_accounts set balance_snapshot = balance_snapshot - :bet_amount
COMMIT;

### 9.3 Win / cashout

BEGIN;
SELECT * FROM wallet_accounts WHERE id = :player_cash_wallet FOR UPDATE;
SELECT * FROM game_sessions WHERE id = :session_id FOR UPDATE;
-- verifica status=active e cashout valido
-- create ledger_transaction(type='win', idempotency_key=:request_key)
-- insert ledger_entries:
--    debit  HOUSE_CASH    :payout
--    credit PLAYER_CASH   :payout
-- update wallet_accounts set balance_snapshot = balance_snapshot + :payout
-- update game_sessions set status='won', payout_amount=:payout, closed_at=now()
COMMIT;

## 10. Error handling e retry policy

- Qualsiasi eccezione prima del COMMIT invalida completamente posting e snapshot update.
- In caso di unique violation su idempotency_key, l’orchestratore deve recuperare la transaction già esistente e restituire il risultato coerente.
- Mai fare retry cieco senza idempotency key.
- Mai correggere manualmente balance_snapshot senza scrittura contabile associata.

## 11. Edge case espliciti

- Doppio click cashout: un solo commit, il secondo riceve risposta idempotente o conflitto gestito.
- Reveal concorrente e cashout concorrente: lock sessione decide il vincitore logico, l’altra richiesta fallisce con stato invalido.
- Drift rilevato in riconciliazione: aprire incident, non fix diretto.
- Admin adjustment: sempre tramite ledger_transaction + admin_action + audit_event.

## 12. Query di riconciliazione di riferimento

SELECT
wa.id AS wallet_account_id,
wa.balance_snapshot,
COALESCE(SUM(CASE WHEN le.entry_side='credit' THEN le.amount ELSE -le.amount END), 0) AS ledger_balance,
wa.balance_snapshot - COALESCE(SUM(CASE WHEN le.entry_side='credit' THEN le.amount ELSE -le.amount END), 0) AS drift
FROM wallet_accounts wa
JOIN ledger_accounts la ON la.id = wa.ledger_account_id
LEFT JOIN ledger_entries le ON le.ledger_account_id = la.id
GROUP BY wa.id, wa.balance_snapshot;

## 13. Testing minimo obbligatorio

- Integration test: signup_credit, bet, win e admin_adjustment con commit reale su Postgres.
- Concurrency test: doppio cashout simultaneo.
- Concurrency test: start duplicato con stessa idempotency_key.
- Reconciliation test: drift sempre zero dopo ogni scenario nominale.

## 14. Decisione finale

La v3 chiude il modello: wallet snapshot materializzato + piano dei conti completo + posting double-entry + locking + idempotenza. Questo è il riferimento da cui implementare il backend finanziario di CasinoKing.
