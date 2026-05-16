# CasinoKing - Round Reporting Display ID Plan

Stato: design history, non eseguibile senza approvazione CTO esplicita.

## Stato

- Tipo: decision record storico della slice Finance drilldown read-only.
- Stato: implementazione read-only locale avviata il 2026-05-14 e chiusa con Finance Drilldown.
- Dipende da: `docs/NEXT_EXECUTION_DETAILED_CTO_REVIEW_PLAN.md` Step 6.
- Non sostituisce: financial core, ledger, Mines fairness o reporting canonico.

## Problema

Il backoffice Finance deve rendere visibile un identificativo round/spin senza
inventare una nuova identita' scollegata da ledger, round e Mines.

## Decisione

Non creare un nuovo display id in questa slice.

L'identificativo operativo e riconciliabile e' `platform_rounds.id`, gia'
esposto dal detail endpoint Finance come `platform_round_id` per ogni evento
contabile della sessione.

Motivo:

- `platform_rounds.id` e' il boundary platform/game gia' usato da ledger e Mines;
- una sessione finanziaria aggregata puo' contenere piu' round, quindi mostrare
  un solo id in lista sarebbe ambiguo;
- il drill-down per evento evita ambiguita' e non richiede migration.

## Matrice Campi

| Campo UI | Fonte | Note |
| --- | --- | --- |
| Session ID | `game_access_sessions.id` o legacy id | Identifica il gruppo report, non il round. |
| Round ID | `platform_rounds.id` | Identificativo da mostrare nel drill-down. |
| Ledger TX | `ledger_transactions.id` | Transazione contabile collegata all'evento. |
| Tipo | `ledger_transactions.transaction_type` | Bet, win, void, ecc. |
| Wallet | `platform_rounds.wallet_type` | Cash/bonus del round. |
| Game enrichment | `mines_game_rounds` via `platform_round_id` | Solo descrizione accessoria, non fonte contabile. |

## Query Read-Only

Il backend esistente `GET /admin/reports/financial/sessions/{session_id}` usa:

- `platform_rounds.start_ledger_transaction_id`;
- `platform_rounds.settlement_ledger_transaction_id`;
- join read-only su `ledger_transactions`, `ledger_entries`, `ledger_accounts`;
- left join su `mines_game_rounds`.

La UI deve consumare questo endpoint. Non deve scrivere su DB e non deve derivare
round id dal client.

## Test

- Backend: `tests/integration/test_admin_financial_reports.py` verifica gia'
  che il detail ritorni due eventi bet/win con lo stesso `platform_round_id`.
- Frontend: lo smoke Finance deve aprire il drill-down e verificare che il
  `platform_round_id` restituito dall'API sia visibile in UI.

## Fuori Scope

- Display id umano corto persistente.
- Migration storica.
- Nuove colonne ledger.
- Report demo anonimo, perche' demo non scrive `platform_rounds`.
