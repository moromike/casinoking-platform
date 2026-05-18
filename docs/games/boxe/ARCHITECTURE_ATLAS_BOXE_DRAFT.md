# BOXE Architecture Atlas Draft

Status: DRAFT
Last meaningful update: 2026-05-18

This draft records the backend foundation produced by `WP-BOXE-2B-SCHEMA-STATE`.
The final atlas remains a Phase 6 deliverable.

## 1. Scope

| Area | Status |
| --- | --- |
| Schema | New BOXE-owned tables only |
| Repository | New BOXE repository module |
| State machine | New pure BOXE state machine |
| API | Out of scope |
| Wallet/ledger | Out of scope |
| Platform shared schema | Not modified |
| Frontend | Out of scope |

## 2. Schema Overview

```text
boxe_sessions
  id PK
  player_id
  access_session_id -> game_access_sessions.id nullable
  table_session_id  -> game_table_sessions.id nullable
  title_code/site_code/status

boxe_rounds
  id PK
  session_id -> boxe_sessions.id
  platform_round_id -> platform_rounds.id nullable unique
  rows_count/difficulty/config snapshot
  status/current_step/safe_picks_count
  bet/multiplier/payout/final payout
  fairness seed/hash/client_seed/nonce/path hash
  start idempotency key/request fingerprint

boxe_picks
  id PK
  round_id -> boxe_rounds.id
  step/row_index/selected_box_index
  safe/outcome math snapshot/rng material
  idempotency key/request fingerprint/response snapshot

boxe_idempotency_keys
  id PK
  optional session_id/round_id owner
  operation/idempotency key/request fingerprint
  response snapshot/TTL
```

## 3. State Machine

Implemented statuses:

| Status | Terminal |
| --- | --- |
| `created` | No |
| `active` | No |
| `row_revealed` | No |
| `cashout_pending` | No |
| `completed_cashout` | Yes |
| `completed_top_row` | Yes |
| `failed_mine` | Yes |
| `expired` | Yes |
| `quarantined` | Yes |

The legal transition table is implemented in
`backend/app/modules/games/boxe/state_machine.py` and mirrors `SPEC.md` section
5.3. Illegal attempts raise `BoxeStateTransitionError`, except terminal replay
cases that intentionally return the terminal state for no-duplicate behavior.

## 4. Repository

`backend/app/modules/games/boxe/repository.py` owns:

| Capability | Method family |
| --- | --- |
| Session CRUD | `create_session` |
| Round CRUD | `create_round`, `get_round`, `update_round_status` |
| Round lock | `lock_round` using `SELECT ... FOR UPDATE` |
| Pick storage | `record_pick`, `get_pick_by_idempotency_key` |
| Idempotency primitive | `save_idempotency_result`, `get_idempotency_result` |

The repository consumes the 2A math module for multiplier ladders and payout
snapshots. It does not call wallet, ledger, API, frontend, or Mines code.

## 5. Concurrency

Concurrency is per-round:

| Race | Primitive |
| --- | --- |
| Two reveals same row | `SELECT ... FOR UPDATE` on `boxe_rounds` |
| Reveal retry | Pick idempotency key lookup |
| Cashout retry | Generic idempotency key lookup |
| Reveal vs cashout | Same round lock decides order |
| Recovery vs player action | Future recovery engine must use the same lock |

## 6. Protected Boundaries

Verified untouched in WP-2B:

| Area | Policy |
| --- | --- |
| Wallet | No imports, no schema, no mutations |
| Ledger | No imports, no schema, no mutations |
| `platform_rounds` | Referenced by nullable FK only |
| `game_access_sessions` | Referenced by nullable FK only |
| `game_table_sessions` | Referenced by nullable FK only |
| Mines | Reference-only reading; no edits/imports |
| Frontend/API | No changes |
